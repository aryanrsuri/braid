from pydantic import BaseModel
from abc import ABC

class BaseView(BaseModel, ABC):
    def __init__(self, **data) -> None:
        super().__init__(**data)

