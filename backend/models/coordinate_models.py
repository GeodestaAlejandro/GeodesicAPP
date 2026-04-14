from pydantic import BaseModel
from typing import Literal

class CoordinateInput(BaseModel):
    type: Literal["geodetic", "ecef", "parametric"]
    values: dict
