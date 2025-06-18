"""
### Event

#### Material

A _material_ is an event created by an _action_ that represents a physical material in a phsyical state, materials can feed a new action, and/or feed a measuremnt to yield raw data.

Examples of a material are: Zirconia dopant, Thermo Fischer HCL 0.05%, Intermediate Mixture (of two materials from an action), Anode, Cathode, Coin Cell, etc... 

#### Action

An _action_ is an event performed by an _actor_ that bridges or "generating" material(s). Each _action_ produces a material, even if that material does not get measured. 

Examples of a material are: Procurement, Mix, Heat, Electrode Casting, Elecrolyte Fill, Fabrication, etc...

#### Measurement

A measurement is an event that yields raw data for some _material_. Thus, only _analysis_ events can follow a measurement. A measurement's set of parameters detail the _procedure_ 

Examples of a measurement are: X-ray diffraction, C/10 Coin Cell Cycling, etc...

#### Analysis

An analysis event performed through an _AnalysisMethod_ analyses a _measurement_ or other _analysis_ event. 

### Parameters

Every abstraction in the schema requires a set of parameters that dictacts the logic of the abstraction. The two types of parameter are schematic, i.e represent fields needed to construct the data layer (timestamp or name parameter for example), and some are event scoped, and represent fields a user details to distinguish one event from another (e.g. hcl_mix_temp: 230)
"""

from typing import List, Dict, Any, Literal, Optional, Union, Tuple
from time import time_ns
from src import ingredient
from src.ingredient import Ingredient, UnspecifiedAmountIngredient
from util.versionstamp import versionstamp, versionid
from pydantic import BaseModel
from abc import ABC, abstractmethod
from parameter import Parameter
from src.actor import Actor

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



class BaseEvent(BaseModel, ABC):
    def __init__(
            self,
            name: str,
            upstream: List[Dict[str, versionid]] = None,
            downstream: List[Dict[str, versionid]] = None,
            tags: Optional[List[str]] = None,
            event_type: Literal["action", "material", "measurement", "analysis"] = None,
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
            self.parameters: Parameter = Parameter()
            self.type = event_type
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


class Material(BaseEvent):
    def __init__(
            self,
            name: str,
            upstream: Optional[List[Dict[str, versionid]]] = None,
            downstream: Optional[List[Dict[str, versionid]]] = None,
            tags: Optional[List[str]] = None,
            **contents: Any
        ):
        super().__init__(name, upstream or [], downstream or [], tags, event_type="material")
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


class Action(BaseEvent):
    def __init__(
            self,
            name: str,
            actor: Actor,
            ingredients: List[Ingredient] = [],
            gen_materials: Optional[List[Material]] = [],
            tags: Optional[List[str]] = None,
            **contents,
        ):
        super().__init__(name, event_type="action", tags=tags)
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
        if name is None:
            name = f"{self.name}.{vm()[8:]}"
        generic = Material(name=name)
        generic.add_upstream(self)
        self.gen_materials = [generic]
        self.add_downstream(generic)


        return generic





          
            




