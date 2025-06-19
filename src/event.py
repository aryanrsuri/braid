from typing import List, Dict, Any, Literal, Optional, Union, Tuple
from time import time_ns
from util.log import Log
from util.versionstamp import versionstamp, versionid
from abc import ABC, abstractmethod
from src.actor import Actor

"""
TODO:
- Implement a `view` class for all given event types, which will allow us to view events in a more structured way.
- Implement a `logger` class to handle logging of events.
- Implement the `save` method to persist events to the DB
- Implement `to_dict` and `from_dict` methods for serialization and deserialization.
"""



vm = versionstamp()

class EventList(List['BaseEvent']):
    def append(self, value: Union['BaseEvent', Dict[str, Any]]) -> None:
        if isinstance(value, BaseEvent):
            super().append(value)
        elif isinstance(value, dict):
            event = BaseEvent(**value)
            super().append(event)
        else:
            raise TypeError("Value must be a BaseEvent or a dict representation of one.")

    def get(self, index: int) -> Union['BaseEvent', Dict[str, Any]]:
        # TODO: Implement a `view` class for all given event types
        if 0 <= index < len(self):
            return self[index]
        else:
            raise IndexError("Index out of range.")



class BaseEvent(ABC):
    def __init__(
            self,
            name: str,
            upstream: Optional[List[Dict[str, versionid]]] = None,
            downstream: Optional[List[Dict[str, versionid]]] = None,
            tags: Optional[List[str]] = None,
            log: Optional[Log] = None,
            event_type: Optional[Literal["action", "material", "measurement", "analysis"]] = "action",
        ):
            if len(name) < 3:
                raise ValueError("Event name must be at least 3 characters long.")
            if event_type is None or event_type not in ["action", "material", "measurement", "analysis"]:
                raise ValueError("event_type must be one of 'action', 'material', 'measurement', or 'analysis'.")

            self.id = vm()
            self.name = name
            self.upstream = EventList()
            self.downstream = EventList()
            self.tags = tags or []
            self.created_at = time_ns() // 1_000
            self.updated_at = None
            self.history = []
            self._contents = {}
            self.type = event_type
            self.log = (log or Log(name)).with_context(event=name, event_type=event_type, event_id=self.id)
            for item in upstream or []:
                self.upstream.append(item)
            for item in downstream or []:
                self.downstream.append(item)


    def __hash__(self):
        return hash(self.name + str(self.id))

    def __eq__(self, other):
        if isinstance(other, BaseEvent):
            return self.id == other.id
        return False

    def __repr__(self):
        return f"<{self.type} ** {self.name} ** {self.id}>"

    def save(self) -> Tuple[versionid, str, int]:
        # TODO: Implement once the `view` class is implemented
        self.updated_at = time_ns() // 1_000
        # save 

        return (self.id, self.name, self.updated_at)

    def add_upstream(self, event: Union['BaseEvent', Dict[str, Any]]) -> None:
        if isinstance(event, BaseEvent):
            self.upstream.append(event)
        elif isinstance(event, dict):
            event_obj = BaseEvent(**event)
            self.upstream.append(event_obj)
        else:
            raise TypeError("Upstream event must be a BaseEvent or a dict representation of one.")

    def add_downstream(self, event: Union['BaseEvent', Dict[str, Any]]) -> None:
        if isinstance(event, BaseEvent):
            self.downstream.append(event)
        elif isinstance(event, dict):
            event_obj = BaseEvent(**event)
            self.downstream.append(event_obj)
        else:
            raise TypeError("Downstream event must be a BaseEvent or a dict representation of one.")

    @abstractmethod
    def invalid(self) -> bool:
        pass


class Material(BaseEvent):
    def __init__(
            self,
            name: str,
            upstream: Optional[List[Dict[str, versionid]]] = None,
            downstream: Optional[List[Dict[str, versionid]]] = None,
            tags: Optional[List[str]] = None,
            log: Optional[Log] = None,
            **contents: Any
        ):
        super().__init__(name, upstream or [], downstream or [], tags, event_type="material", log=log)
        self._contents = contents

    def invalid(self):
        """
        A material event is invalid if anything but action even is in the upstream, or anything but action and measurement events are in the downstream
        """
        if any(event.type not in ["action"] for event in self.upstream):
            return True
        if any(event.type not in ["action", "measurement"] for event in self.downstream):
            return True
        return False


class Ingredient():
    def __init__(
            self,
            material: Material,
            amount: Optional[float],
            unit: Optional[str],
            name: Optional[str] = None,
            **contents,
            ):
        # Inherit material name if ingredient name is not provided
        if name is None:
            name = material.name
        self.name = name
        self.material = material
        self.amount = amount
        self.unit = unit
        self._contents = contents

    def __repr__(self) -> str:
        return f"<Ingredient ** {self.name} ** {self.material} ** {self.amount} {self.unit if self.unit else 'units'}>"

class UnspecifiedAmountIngredient(Ingredient):
    def __init__(self, material: Material, name: Optional[str] = None, **contents):
        super().__init__(material=material, amount=None, unit=None, name=name, **contents)

class WholeIngredient(Ingredient):
    def __init__(self, material: Material, name: Optional[str] = None, **contents):
        super().__init__(material=material, amount=100.0, unit="percent", name=name, **contents)



class Action(BaseEvent):
    def __init__(
            self,
            name: str,
            actor: Actor,
            ingredients: List[Ingredient] = [],
            gen_materials: Optional[List[Material]] = [],
            tags: Optional[List[str]] = None,
            log: Optional[Log] = None,
            **contents,
        ):
        super().__init__(name, event_type="action", tags=tags, log=log)
        self._contents = contents
        self.actor = actor
        self.ingredients = []
        self.gen_materials = []
        for ingredient in ingredients:
            self.add_ingredient(ingredient)
        for material in gen_materials or []:
            self.add_gen_material(material)
    def add_ingredient(self, ingredient: Ingredient | Material) -> None:
        if isinstance(ingredient, Material):
            ingredient = UnspecifiedAmountIngredient(material=ingredient)
        elif isinstance(ingredient, Ingredient):
            self.add_upstream(ingredient.material)
            ingredient.material.add_downstream(self)
            self.ingredients.append(ingredient)
        else:
            raise TypeError("Ingredient must be an Ingredient or Material instance.")


    def add_gen_material(self, material: Material) -> None:
        if not isinstance(material, Material):
            raise TypeError("Generated material must be a Material instance.")
        if material in self.gen_materials:
            pass
        self.add_downstream(material)
        material.add_upstream(self)
        self.gen_materials.append(material)

    def generate_generic_material(self, name: Optional[str] = None) -> Material:
        if len(self.gen_materials) > 0:
            raise ValueError("Cannot generate a generic material when there are already generated materials.")
        """
        TODO: A Lab view (view over the whole lab) which houses the experiments->sample->material should generate
        the material name based on an intelligent naming scheme, e.g. "ExperimentName.MaterialName:versionstamp".

        For now this method generates a material name based on the action name and list of ingredients
        """
        generated_name = name
        if generated_name is None:
            if len(self.ingredients) > 0:
                ingredient_names = "".join(ingredient.name for ingredient in self.ingredients)
                # Is this name too long?
                generated_name = f"{self.name}.{ingredient_names}:{vm()}"
            else:
                generated_name = f"{self.name}.NI:{vm()}"

        generic = Material(name=generated_name)
        generic.add_upstream(self)
        self.gen_materials = [generic]
        self.add_downstream(generic)
        return generic

    def invalid(self) -> bool:
        """
        An action event is invalid if its upstream contains anything but a material, or if its downstream contains anything but a material or measurement event, or if It is not linked to any generated materials nor ingredients.
        """
        if any(event.type not in ["material"] for event in self.upstream):
            return True
        if any(event.type not in ["material", "measurement"] for event in self.downstream):
            return True
        if len(self.gen_materials) == 0 and len(self.ingredients) == 0:
            return True
        return False

class Measurement(BaseEvent):
    def __init__(
            self,
            name: str,
            material: Optional[Material] = None,
            actor: Optional[Actor] = None,
            tags: Optional[List[str]] = None,
            log: Optional[Log] = None,
            **contents: Any,
            ):
        super(Measurement, self).__init__(
                name=name, tags=tags, event_type="measurement", log=log, **contents
        )
        self._material = None
        self._actor = None
        if material:
            self.material = material
        if actor:
            self.actor = actor
        self._contents = contents

    def invalid(self) -> bool:
        """
        A measurement event is invalid if its upstream contains anything but a material, or if its downstream contains anything but an analysis event.
        """
        if any(event.type not in ["material"] for event in self.upstream):
            return True
        if any(event.type not in ["analysis"] for event in self.downstream):
            return True
        return False

    def set_material(self, material: Material):
        if not isinstance(material, Material):
            raise TypeError("Material must be a Material instance.")
        if self._material is not None:
            raise ValueError("Materials is already set.")
        self._material = material
        self.material.add_downstream(self)
        self.add_upstream(material)


    def set_actor(self, actor: Actor):
        if not isinstance(actor, Actor):
            raise TypeError("Actor must be an Actor instance.")
        self._actor = actor
        self.actorid = actor.id


class Analysis(BaseEvent):
    def __init__(
            self,
            name: str,
            actor: Optional[Actor] = None,
            measurements: Optional[List[Measurement]] = None,
            upstream_analysis: Optional[List["Analysis"]] = None,
            tags: Optional[List[str]] = None,
            **contents: Any,
            ):
        super(Analysis, self).__init__(
                name=name, tags=tags, event_type="analysis", **contents
                )
        
        # self.actorid = None
        self._measurements = []
        self._upstream_analysis = []
        self._actor = None
        self._contents = contents

        if actor:
            self.actor = actor
        for measurement in measurements or []:
            self.add_measurement(measurement)

        for analysis in upstream_analysis or []:
            self.add_upstream_analysis(analysis)


    def add_measurement(self, measurement: Measurement) -> None:
        if not isinstance(measurement, Measurement):
            raise TypeError("Measurement must be a Measurement instance.")
        if measurement in self._measurements:
            return
        measurement.add_downstream(self)
        self.add_upstream(measurement)
        self._measurements.append(measurement)

    def add_upstream_analysis(self, analysis: 'Analysis') -> None:
        if not isinstance(analysis, Analysis):
            raise TypeError("Upstream analysis must be an Analysis instance.")
        if analysis in self._upstream_analysis:
            return
        analysis.add_downstream(self)
        self.add_upstream(analysis)
        self._upstream_analysis.append(analysis)

    def invalid(self) -> bool:
        """
        An analysis event is invalid if its upstream contains anything but a measurement or analysis event, or if its downstream contains anything but an analysis event.
        """
        if len(self._upstream_analysis) == 0 and len(self._measurements) == 0:
            return True
        if self._actor is None:
            return True
        if any(event.type not in ["measurement", "analysis"] for event in self.upstream):
            return True
        if any(event.type not in ["analysis"] for event in self.downstream):
            return True
        return False


