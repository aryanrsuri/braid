"""
Author: Aryan Suri
Parameter class for defining ordered tasks of a given event
"""


from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, validator
from util.versionstamp import versionid, versionstamp

vm = versionstamp()

class Parameter(BaseModel, ABC):
    def __init__(self, **data: Any) -> None:
        self.id: versionid = vm()
        super().__init__(**data)

