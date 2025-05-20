from fastapi import APIRouter
from models import GeocentricCoordinates, coordinates
from services.conversions import convert_coordinates

router = APIRouter()

@router.post("/")
def convert_geocentric_endpoint(coords: GeocentricCoordinates, output_system: str, model: str = "WGS84"):

    output_coords = convert_coordinates(coords, "geocentric", output_system, model=model)
    return output_coords