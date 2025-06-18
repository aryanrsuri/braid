from util.versionstamp import versionstamp, versionid
from src.event import Material
from pydantic import BaseModel
from typing import Optional, Union
from enum import Enum


class Ingredient(BaseModel):
    def __init__(
            self,
            material: Material,
            amount: float,
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
        return f"<Ingredient ** {self.name} ** {self.material} ** {self.amount} {self.unit.value if self.unit else 'units'}>"

# TODO Derived classes for shortcuts, e.g. WholeIngredient or UnspecifiedIngredient
        
class UnspecifiedAmountIngredient(Ingredient):
    def __init__(self, material: Material, name: Optional[str] = None, **contents):
        super().__init__(material=material, amount=None, unit=None, name=name, **contents)

class WholeIngredient(Ingredient):
    def __init__(self, material: Material, name: Optional[str] = None, **contents):
        super().__init__(material=material, amount=100.0, unit="percent", name=name, **contents)

