from typing import List, Dict, Any, Literal, Optional, Union, Tuple
from time import time_ns
from util.log import Log
from util.versionstamp import versionstamp, versionid
from abc import ABC, abstractmethod
from src.actor import Actor

vm = versionstamp()

class EventList(List['BaseEvent']):
    def append(self, value: Union['BaseEvent', Dict[str, Any]]) -> None:
        if isinstance(value, BaseEvent):
            super().append(value)
        elif isinstance(value, dict):
            event = BaseEvent.from_dict(value)
            super().append(event)
        else:
            self.log.error("Value must be a BaseEvent or a dict representation of one.")
            raise TypeError("Value must be a BaseEvent or a dict representation of one.")

    def get(self, index: int) -> Union['BaseEvent', Dict[str, Any]]:
        if 0 <= index < len(self):
            return self[index]
        else:
            raise IndexError("Index out of range.")



class BaseEvent(ABC):
    def __init__(
            self,
            name: str,
            upstream: Optional[List[Dict[str, versionid]]] = None, # These will now be BaseEvent instances in internal lists
            downstream: Optional[List[Dict[str, versionid]]] = None, # These will now be BaseEvent instances in internal lists
            tags: Optional[List[str]] = None,
            log: Optional[Log] = None,
            event_type: Optional[Literal["action", "material", "measurement", "analysis"]] = "action",
            id: Optional[versionid] = None, # Add id to init to allow setting it from dict
            created_at: Optional[int] = None, # Add created_at to init
            updated_at: Optional[int] = None, # Add updated_at to init
            **contents: Any, # To capture any extra contents
        ):
            if len(name) < 3:
                raise ValueError("Event name must be at least 3 characters long.")
            if event_type is None or event_type not in ["action", "material", "measurement", "analysis"]:
                raise ValueError("event_type must be one of 'action', 'material', 'measurement', or 'analysis'.")

            self.id = id if id is not None else vm()
            self.name = name
            self.tags = tags or []
            self.created_at = created_at if created_at is not None else time_ns() // 1_000
            self.updated_at = updated_at
            self.history = []
            self._contents = contents # Store generic contents
            self.type = event_type
            self.log = (log or Log(name)).with_context(event=name, event_type=event_type, event_id=self.id)

            # Initialize upstream and downstream as EventList,
            # and use from_dict when adding initial items if they are dicts
            self.upstream = EventList()
            if upstream:
                for item in upstream:
                    # Pass original dictionary if it contains full event data
                    # Otherwise, just pass the ID and type as dict to be handled by add_upstream
                    if isinstance(item, dict) and "event_id" in item and "type" in item:
                        # If `item` is a simple dict like `{'event_id': '...', 'type': '...'}`
                        # and not a full event dict, we still need to add it as a stub.
                        # For now, `add_upstream` expects a BaseEvent object or a full dict.
                        # Let's ensure `add_upstream` correctly handles the format of upstream/downstream lists
                        # which contain dicts with 'event_id' and 'type'.
                        # The `graph` method in Sample expects these to be BaseEvent objects,
                        # so we need to convert them here or ensure they are always BaseEvent objects.
                        # For now, let's assume `upstream` and `downstream` lists passed to init
                        # might contain the minimal dicts from `to_dict` or full event dicts.
                        # The current `add_upstream` logic requires a BaseEvent object or a full event dict.
                        # We will modify `add_upstream/downstream` to handle the stored dicts.
                        self.add_upstream_id(item["event_id"], item.get("type")) # Use a new method to add just ID
                    else:
                        # If it's already a BaseEvent or a full event dict, it will be handled by EventList.append
                        self.upstream.append(item)


            self.downstream = EventList()
            if downstream:
                for item in downstream:
                    if isinstance(item, dict) and "event_id" in item and "type" in item:
                        self.add_downstream_id(item["event_id"], item.get("type"))
                    else:
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
        self.updated_at = time_ns() // 1_000
        # save
        return (self.id, self.name, self.updated_at)

    # New method to add an upstream relationship using just ID and type
    # This is for internal graph representation, not for creating full event objects
    def add_upstream_id(self, event_id: versionid, event_type: Optional[str] = None) -> None:
        # Create a "stub" event object with just id and type for graph purposes
        # This prevents the TypeError from Sample.graph()
        class StubEvent:
            def __init__(self, id, type):
                self.id = id
                self.type = type
        self.upstream.append(StubEvent(event_id, event_type or "unknown"))


    # New method to add a downstream relationship using just ID and type
    def add_downstream_id(self, event_id: versionid, event_type: Optional[str] = None) -> None:
        class StubEvent:
            def __init__(self, id, type):
                self.id = id
                self.type = type
        self.downstream.append(StubEvent(event_id, event_type or "unknown"))


    def add_upstream(self, event: Union['BaseEvent', Dict[str, Any]]) -> None:
        if isinstance(event, BaseEvent):
            self.upstream.append(event)
        elif isinstance(event, dict):
            # If it's a dict, use from_dict to get the actual event object
            event_obj = BaseEvent.from_dict(event)
            self.upstream.append(event_obj)
        else:
            raise TypeError("Upstream event must be a BaseEvent or a dict representation of one.")

    def add_downstream(self, event: Union['BaseEvent', Dict[str, Any]]) -> None:
        if isinstance(event, BaseEvent):
            self.downstream.append(event)
        elif isinstance(event, dict):
            # If it's a dict, use from_dict to get the actual event object
            event_obj = BaseEvent.from_dict(event)
            self.downstream.append(event_obj)
        else:
            raise TypeError("Downstream event must be a BaseEvent or a dict representation of one.")

    @abstractmethod
    def invalid(self) -> bool:
        pass

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "event_type": self.type,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "contents": self._contents,
            # For upstream/downstream, store minimal info to avoid deep recursion and for graph building
            # If you need full event objects, you'd fetch them from a data store based on ID
            "upstream": [{"event_id": e.id, "type": e.type} for e in self.upstream if hasattr(e, 'id') and hasattr(e, 'type')],
            "downstream": [{"event_id": e.id, "type": e.type} for e in self.downstream if hasattr(e, 'id') and hasattr(e, 'type')],
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEvent':
        event_type = data.get("event_type")
        if event_type == "material":
            # Pass all dictionary items as kwargs, Material's __init__ will pick what it needs
            return Material(**data)
        elif event_type == "action":
            # For action, we need to handle actor and ingredients specially if they are dicts
            # This requires Action's __init__ to also accept dicts for actor/ingredients
            # Or, you'll need to reconstruct them here.
            # Let's assume for now that if actor/ingredients are dicts, their respective classes have from_dict
            # or Action's __init__ can handle dicts. If actor is a simple ID, it's fine.
            # For now, let's pass a dummy actor if it's not provided or can't be reconstructed
            actor_data = data.get('actor')
            if actor_data and isinstance(actor_data, dict):
                # Assuming Actor also has a from_dict or its init can take a dict
                actor = Actor(**actor_data) # You'll need to define Actor's __init__ to handle this
            elif actor_data: # If actor is just an ID string
                 actor = Actor(name=f"Actor_{actor_data}") # Create a dummy actor
            else:
                actor = Actor(name="UnknownActor") # Default actor if none provided


            # Ingredients also need to be handled carefully:
            ingredients_data = data.get('ingredients', [])
            ingredients = []
            for ingr_data in ingredients_data:
                if isinstance(ingr_data, dict):
                    # You'll need `Ingredient.from_dict` or similar if ingredient is complex
                    # For now, let's assume it's just material, amount, unit
                    material_data = ingr_data.get('material')
                    if material_data and isinstance(material_data, dict):
                        material = Material.from_dict(material_data)
                    elif material_data and isinstance(material_data, Material):
                        material = material_data
                    else:
                        material = Material(name="UnknownMaterial") # Fallback

                    # Determine ingredient type
                    if ingr_data.get('amount') is None and ingr_data.get('unit') is None:
                        ingredients.append(UnspecifiedAmountIngredient(material=material, name=ingr_data.get('name'), **ingr_data.get('contents',{})))
                    elif ingr_data.get('amount') == 100.0 and ingr_data.get('unit') == "percent":
                        ingredients.append(WholeIngredient(material=material, name=ingr_data.get('name'), **ingr_data.get('contents',{})))
                    else:
                        ingredients.append(Ingredient(material=material, amount=ingr_data.get('amount'), unit=ingr_data.get('unit'), name=ingr_data.get('name'), **ingr_data.get('contents',{})))
                elif isinstance(ingr_data, Ingredient):
                    ingredients.append(ingr_data)

            # Generated materials
            gen_materials = []
            for mat_data in data.get('gen_materials', []):
                if isinstance(mat_data, dict):
                    gen_materials.append(Material.from_dict(mat_data))
                elif isinstance(mat_data, Material):
                    gen_materials.append(mat_data)


            return Action(
                name=data["name"],
                actor=actor,
                ingredients=ingredients,
                gen_materials=gen_materials,
                tags=data.get("tags", []),
                log=data.get("log"), # Pass existing log or create new one
                id=data.get("id"),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
                **data.get("contents", {})
            )

        elif event_type == "measurement":
            material = data.get('material')
            if isinstance(material, dict):
                material = Material.from_dict(material)
            elif not isinstance(material, Material):
                material = None # Or raise error if material is mandatory

            actor = data.get('actor')
            if isinstance(actor, dict):
                actor = Actor(**actor)
            elif not isinstance(actor, Actor):
                actor = None # Or raise error

            return Measurement(
                name=data["name"],
                material=material,
                actor=actor,
                tags=data.get("tags", []),
                log=data.get("log"),
                id=data.get("id"),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
                **data.get("contents", {})
            )
        elif event_type == "analysis":
            actor = data.get('actor')
            if isinstance(actor, dict):
                actor = Actor(**actor)
            elif not isinstance(actor, Actor):
                actor = None # Or raise error

            measurements = []
            for meas_data in data.get('measurements', []):
                if isinstance(meas_data, dict):
                    measurements.append(Measurement.from_dict(meas_data)) # Recursively call from_dict
                elif isinstance(meas_data, Measurement):
                    measurements.append(meas_data)

            upstream_analysis = []
            for an_data in data.get('upstream_analysis', []):
                if isinstance(an_data, dict):
                    upstream_analysis.append(Analysis.from_dict(an_data)) # Recursively call from_dict
                elif isinstance(an_data, Analysis):
                    upstream_analysis.append(an_data)

            return Analysis(
                name=data["name"],
                actor=actor,
                measurements=measurements,
                upstream_analysis=upstream_analysis,
                tags=data.get("tags", []),
                log=data.get("log"),
                id=data.get("id"),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
                **data.get("contents", {})
            )
        else:
            raise ValueError(f"Unknown event_type: {event_type}")


# --- Event Subclasses (Material, Action, Measurement, Analysis) ---
# Ensure these are defined below BaseEvent or imported.
# Assuming they are in the same file for now.

class Material(BaseEvent):
    def __init__(
            self,
            name: str,
            upstream: Optional[List[Dict[str, versionid]]] = None,
            downstream: Optional[List[Dict[str, versionid]]] = None,
            tags: Optional[List[str]] = None,
            log: Optional[Log] = None,
            created_at: Optional[int] = None, # Added created_at
            updated_at: Optional[int] = None, # Added updated_at
            **contents: Any
        ):
        super().__init__(name, upstream, downstream, tags, event_type="material", log=log,
                         created_at=created_at, updated_at=updated_at, **contents)
        self.id = vm()  

    def invalid(self):
        if any(getattr(event, 'type', None) not in ["action"] for event in self.upstream):
            return True
        if any(getattr(event, 'type', None) not in ["action", "measurement"] for event in self.downstream):
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
        return f"<Ingredient ** {self.name} ** {self.material.name} ** {self.amount} {self.unit if self.unit else 'units'}>"

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
            ingredients: Optional[List[Union[Ingredient, Dict[str, Any]]]] = None, 
            gen_materials: Optional[List[Union[Material, Dict[str, Any]]]] = None,
            tags: Optional[List[str]] = None,
            log: Optional[Log] = None,
            created_at: Optional[int] = None,
            updated_at: Optional[int] = None,
            **contents,
        ):
        super().__init__(name, tags=tags, event_type="action", log=log,
                         , created_at=created_at, updated_at=updated_at, **contents)

        self.id = vm()  
        self.actor = actor 
        self.ingredients = []
        self.gen_materials = []
        self.log = (log or Log(name)).with_context(
            action_name=name,
            action_id=self.id,
        )

        for ingredient in ingredients or []:
            self.add_ingredient(ingredient)
        for material in gen_materials or []:
            self.add_gen_material(material)

    def add_ingredient(self, ingredient: Union[Ingredient, Material, Dict[str, Any]]) -> None:
        if isinstance(ingredient, Material):
            ingredient = UnspecifiedAmountIngredient(material=ingredient)
            self.add_upstream(ingredient.material) # Correctly add the material upstream
            ingredient.material.add_downstream(self)
            self.ingredients.append(ingredient)
        elif isinstance(ingredient, Ingredient):
            self.add_upstream(ingredient.material)
            ingredient.material.add_downstream(self)
            self.ingredients.append(ingredient)
        elif isinstance(ingredient, dict):
            self.log.debug("Adding ingredient from dict representation.")
            raise TypeError("Please pass Ingredient or Material objects to add_ingredient, not raw dicts.")
        else:
            raise TypeError("Ingredient must be an Ingredient or Material instance.")


    def add_gen_material(self, material: Union[Material, Dict[str, Any]]) -> None:
        if isinstance(material, dict):
            material_obj = Material.from_dict(material) 
            self.add_downstream(material_obj)
            material_obj.add_upstream(self)
            # FIXME: Check if material_obj is already in gen_materials
            self.gen_materials.append(material_obj)
        elif isinstance(material, Material):
            if material in self.gen_materials:
                pass # Already added
            self.add_downstream(material)
            material.add_upstream(self)
            self.gen_materials.append(material)
        else:
            self.log.error("Generated material must be a Material instance or a dict representation.")
            raise TypeError("Generated material must be a Material instance or a dict representation.")


    def generate_generic_material(self, name: Optional[str] = None) -> Material:
        if len(self.gen_materials) > 0:
            raise ValueError("Cannot generate a generic material when there are already generated materials.")

        generated_name = name
        if generated_name is None:
            if len(self.ingredients) > 0:
                ingredient_names = "".join(ingredient.name for ingredient in self.ingredients)
                generated_name = f"{self.name}.{ingredient_names}:{vm()}"
            else:
                generated_name = f"{self.name}.NI:{vm()}"

        generic = Material(name=generated_name)
        generic.add_upstream(self) 
        self.add_downstream(generic)
        self.gen_materials = [generic]
        return generic

    def invalid(self) -> bool:
        if any(getattr(event, 'type', None) not in ["material"] for event in self.upstream):
            return True
        if any(getattr(event, 'type', None) not in ["material", "measurement"] for event in self.downstream):
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
            created_at: Optional[int] = None,
            updated_at: Optional[int] = None,
            **contents: Any,
            ):
        super(Measurement, self).__init__(
                name=name, tags=tags, event_type="measurement", log=log, created_at=created_at, updated_at=updated_at, **contents
        )
        self.id = vm()
        self._material = None
        self._actor = None
        self.log = (log or Log(name)).with_context(
        # _contents is handled by super().__init__ now

        if material:
            self.material = material
        if actor:
            self.actor = actor 

    def invalid(self) -> bool:
        """
        A measurement event is invalid if its upstream contains anything but a material, or if its downstream contains anything but an analysis event.
        """
        if any(getattr(event, 'type', None) not in ["material"] for event in self.upstream):
            return True
        if any(getattr(event, 'type', None) not in ["analysis"] for event in self.downstream):
            return True
        return False

    @property
    def material(self) -> Optional[Material]:
        return self._material

    @material.setter
    def material(self, material_obj: Material):
        if not isinstance(material_obj, Material):
            raise TypeError("Material must be a Material instance.")
        if self._material is not None:
            raise ValueError("Material is already set.")
        self._material = material_obj
        self.add_upstream(material_obj) # Add as upstream BaseEvent
        material_obj.add_downstream(self) # Link the material back

    @property
    def actor(self) -> Optional[Actor]:
        return self._actor

    @actor.setter
    def actor(self, actor_obj: Actor):
        if not isinstance(actor_obj, Actor):
            self.log.error("Actor must be an Actor instance.")
            raise TypeError("Actor must be an Actor instance.")
        self._actor = actor_obj

class Analysis(BaseEvent):
    def __init__(
            self,
            name: str,
            actor: Optional[Actor] = None,
            measurements: Optional[List[Union['Measurement', Dict[str, Any]]]] = None,
            upstream_analysis: Optional[List[Union['Analysis', Dict[str, Any]]]] = None,
            tags: Optional[List[str]] = None,
            log: Optional[Log] = None,
            created_at: Optional[int] = None,
            updated_at: Optional[int] = None,
            **contents: Any,
            ):
        super(Analysis, self).__init__(
                name=name, tags=tags, event_type="analysis", log=log,
                created_at=created_at, updated_at=updated_at, **contents
                )

        self.id = vm()
        self._measurements = []
        self._upstream_analysis = []
        self._actor = None
        # _contents handled by super

        if actor:
            self.actor = actor # Use setter
        for measurement in measurements or []:
            self.add_measurement(measurement)
        for analysis in upstream_analysis or []:
            self.add_upstream_analysis(analysis)


    @property
    def actor(self) -> Optional[Actor]:
        return self._actor

    @actor.setter
    def actor(self, actor_obj: Actor):
        if not isinstance(actor_obj, Actor):
            raise TypeError("Actor must be an Actor instance.")
        self._actor = actor_obj

    def add_measurement(self, measurement: Union[Measurement, Dict[str, Any]]) -> None:
        if isinstance(measurement, dict):
            measurement_obj = Measurement.from_dict(measurement)
        elif isinstance(measurement, Measurement):
            measurement_obj = measurement
        else:
            raise TypeError("Measurement must be a Measurement instance or a dict representation.")

        if measurement_obj in self._measurements:
            return
        measurement_obj.add_downstream(self)
        self.add_upstream(measurement_obj)
        self._measurements.append(measurement_obj)

    def add_upstream_analysis(self, analysis: Union['Analysis', Dict[str, Any]]) -> None:
        if isinstance(analysis, dict):
            analysis_obj = Analysis.from_dict(analysis)
        elif isinstance(analysis, Analysis):
            analysis_obj = analysis
        else:
            raise TypeError("Upstream analysis must be an Analysis instance or a dict representation.")

        if analysis_obj in self._upstream_analysis:
            return
        analysis_obj.add_downstream(self)
        self.add_upstream(analysis_obj)
        self._upstream_analysis.append(analysis_obj)

    def invalid(self) -> bool:
        """
        An analysis event is invalid if its upstream contains anything but a measurement or analysis event, or if its downstream contains anything but an analysis event.
        """
        if len(self._upstream_analysis) == 0 and len(self._measurements) == 0:
            return True
        if self._actor is None:
            return True
        if any(getattr(event, 'type', None) not in ["measurement", "analysis"] for event in self.upstream):
            return True
        if any(getattr(event, 'type', None) not in ["analysis"] for event in self.downstream):
            return True
        return False
