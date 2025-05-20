from fastapi import APIRouter
from models import ParametricCoordinates
from services.conversions import convert_coordinates

router = APIRouter()

@router.post("/")
def convert_parametric_endpoint(coords: ParametricCoordinates, output_system: str, model: str = "WGS84"):

    output_coords = convert_coordinates(coords, "parametric", output_system, model=model)
    return output_coords