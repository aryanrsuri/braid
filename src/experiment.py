from src.task import Task
from time import time_ns
from src.event import Material, Action, Measurement, Analysis
from typing import List, Optional, Dict, Any, Literal, Union, TYPE_CHECKING
from src.lab import Lab, Project
from abc import ABC
from enum import Enum
from util.versionstamp import versionid, versionstamp
from util.log import Log
from util.status import Status
vm = versionstamp()

if TYPE_CHECKING:
    from src.sample import Sample 

class Experiment:
    def __init__(
        self,
        name: str,
        log: Log,
        lab: Lab,
        project: Project,
        status: Status = Status.PENDING,
        description: Optional[str] = None,
        tags: List[str] = [],
        samples: List['Sample'] = [],
        tasks: List[Task] = [],
        **contents: Any
        ):

        self.id = vm()
        self.name = name
        self.log = (log or Log(name)).with_context(
            experiment_name=name,
            experiment_id=self.id,
            samples=[sample.id for sample in samples] if samples else [],
            tasks=[task.id for task in tasks] if tasks else []
        )
        self._contents = contents
        self.description = description or ""
        self.created_at = time_ns() // 1_000
        self.updated_at = None
        self.status = status
        self.tags = tags or []
        self.samples = samples or []
        self.tasks = tasks or []
        self.lab = lab
        self.project = project
        self.save()

    def save(self):
        self.updated_at = time_ns() // 1_000
        self.log.info(f"Experiment {self.name} saved with status {self.status.value}")
        # TODO: Implement once DB connection is created

    def to_dict(self, include_samples: bool = True, include_tasks: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "contents": self._contents
        }
        if include_samples:
            data["samples"] = [sample.to_dict() for sample in self.samples]
        if include_tasks:
            data["tasks"] = [task.to_dict() for task in self.tasks]
        return data

    def __repr__(self):
        return f"Experiment(name={self.name}, id={self.id}, created_at={self.created_at})"

    def create_sample(self, description: str = "", tags: List[str] = [], **contents: Any) -> 'Sample':
        from src.sample import Sample
        sample = Sample(description=description, tags=tags, log=self.log, experiment=self, **contents)
        self.samples.append(sample)
        self.log.info(f"Sample {sample.name} created in experiment {self.name}")
        return sample

