from pydantic import BaseModel, Field
from typing import Dict, Any, Literal, List
from util.versionstamp import versionstamp, versionid
from util.log import Log
vm = versionstamp()


class Task(BaseModel):
    id: versionid = Field(default_factory=vm)
    name : str 
    description: str 
    log: Log
    event_type: Literal['action', 'material', 'measurement', 'analysis']
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    parameter: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the task")

    class Config:
        arbitrary_types_allowed = True

