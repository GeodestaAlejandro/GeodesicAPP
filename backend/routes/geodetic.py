from fastapi import APIRouter, Query
from models import GeodeticCoordinates
from services.conversions import convert_coordinates

router = APIRouter()

@router.post("/")
def convert_geodetic_endpoint(
    coords: GeodeticCoordinates,
    output_system: str = Query(..., description="Sistema de salida"),
    model: str = Query("WGS84", description="Modelo de elipsoide")
):
    try:
        output_coords = convert_coordinates(coords, "geodetic", output_system, model=model)
        return output_coords
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))