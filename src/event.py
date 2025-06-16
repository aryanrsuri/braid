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

from typing import List, Dict, Any, Literal, Optional, Union
from time import time_ns
# from bson import ObjectId
from util.versionstamp import versionstamp, versionid
from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod
from parameter import Parameter

vm = versionstamp()

class EventList(list):
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
            self.updated_at = self.created_at
            self.history = []
            self.contents = []
            self.parameters: Parameter = Parameter()
            self.event_type = event_type
            for item in upstream or []:
                self.upstream.append(item)
            for item in downstream or []:
                self.downstream.append(item)
            print(f"Event ID: {self.event_id}")



        

          
            




