from copy import deepcopy
from time import time_ns
from typing import Any, Optional, Dict, List
from util.versionstamp import versionstamp
from enum import Enum

vm = versionstamp()

class ActorStatus(Enum):
    OCCUPIED = "occupied",
    LOCKED = "locked",
    IDLE = "idle",
    ERROR = "error",


class BaseActor:
    def __init__(
            self,
            name: str,
            description: str,
            tags: Optional[List[str]] = None,
            status: ActorStatus = ActorStatus.IDLE,
            **contents: Any
            ):
        self.id = vm()
        self.name = name
        self.status = status
        self.tags = [] if tags is None else tags
        self.description = description
        self._contents = contents
        self.created_at = time_ns() // 1_000
        # Updated by the database on `save`
        self.updated_at = None
        self._versioning = [{
                "v": 1,
                "description": "ver: 1",
                "created_at": time_ns() // 1_000,
                }]

    def current_version(self):
        return self._versioning[-1]["v"]

    def version(self, description: str):
        self._versioning.append({
            "v": self.current_version() + 1,
            "description": description,
            "created_at": time_ns() // 1_000,
        })

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value[0],
            "tags": self.tags,
            "description": self.description,
            "contents": deepcopy(self._contents),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "versioning": deepcopy(self._versioning),
        }

    def from_dict(self):
        return BaseActor(
            name=self.name,
            description=self.description,
            tags=self.tags,
            status=self.status,
            **deepcopy(self._contents)
        )

    def save(self):
        self.updated_at = time_ns() // 1_000
        # View handles the save
        # from src.view import View
        # View.add(entry=self, "update")

        raise NotImplementedError("Save method should be implemented in the subclass.")


class Actor(BaseActor):
    def __init__(
            self,
            name: str,
            description: str,
            tags: Optional[List[str]] = None,
            status: ActorStatus = ActorStatus.IDLE,
            **contents: Any
            ):
        super().__init__(name, description, tags, status, **contents)





