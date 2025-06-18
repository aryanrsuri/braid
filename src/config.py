from typing import List, Optional
from pydantic import BaseModel, Field
from src.view import BaseView
from src.ingredient import Ingredient
from src.event import Material
from util.versionstamp import versionstamp
from time import time_ns
"""
The configuration class defines the lab administrative settings and labels:
- **lab_name**: The name of the lab.
- users
- groups
- roles + description

"""

vm = versionstamp()
class Lab(BaseModel):
    def __init__(
            self,
            lab_name: str,
            lab_code: str,
            lab_location: str,
            description: str = "",
            views: Optional[List[BaseView]] = [],
            **contents,
            ):

        self.lab_name = lab_name
        self.lab_code = lab_code
        self.lab_location = lab_location
        self.id = vm()
        self.created_at = time_ns() / 1_000
        self.updated_at = None
        self.description = description
        self._contents = contents
        self.save()

    def save(self):
        # TODO: Implement once DB connection is created
        self.updated_at = time_ns() // 1_000

    def sample_material_name(self, sample: Experiment):
        name: str = f"{lab_code}.{lab_location[0:3]}.:


