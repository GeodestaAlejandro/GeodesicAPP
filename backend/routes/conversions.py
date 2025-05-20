from fastapi import APIRouter, HTTPException
from models import GeocentricCoordinates, GeodeticCoordinates, ParametricCoordinates
from conversions import convert_coordinates

router = APIRouter()

@router.post("/")
def convert(input_system: str, output_system: str, model: str = "WGS84", input_coords: dict = None):
  
    try:
        if input_system == "geodetic":
            coords = GeodeticCoordinates(**input_coords)
        elif input_system == "geocentric":
            coords = GeocentricCoordinates(**input_coords)
        elif input_system == "parametric":
            coords = ParametricCoordinates(**input_coords)
        else:
            raise ValueError("Sistema de coordenadas de entrada no válido")
        
        result = convert_coordinates(coords, input_system, output_system, model)
        return {"converted_coordinates": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
