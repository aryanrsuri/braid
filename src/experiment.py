from pydantic import BaseModel
from abc import ABC


class BaseExperiment(BaseModel, ABC):
    pass
