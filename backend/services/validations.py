from fastapi import HTTPException
from constants import ELLIPSOID_MODELS
from models import (EllipsoidAndTypeInput, geocentricCardCoord, GeodesicCoordinates, ParametricCoordinates, GausKruger)

# en proceso, no funciona aun 
# def Ellipsoid(ellipsoid):
#     if not ellipsoid:
#         raise HTTPException(400, "Modelo de elipsoide no valido")

def validate_coordinates(data: EllipsoidAndTypeInput):
    ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)
    if not ellipsoid:
        raise HTTPException(400, "Modelo de elipsoide no válido")
  
    try:
        if data.coordinate_type == "Geodesic":
            coords = GeodesicCoordinates(**data.coordinates)
            result = coords.model_dump()
        elif data.coordinate_type == "Geocentric":
            coords = geocentricCardCoord(**data.coordinates)
            result = coords.model_dump()
        elif data.coordinate_type == "Parametric":
            coords = ParametricCoordinates(**data.coordinates)
            result = coords.model_dump()
        elif data.coordinate_type == "Cartesian":
            coords = geocentricCardCoord(**data.coordinates)
            result = coords.model_dump()
        elif data.coordinate_type == "GausKruger":
            coords = GausKruger(**data.coordinates)
            result = coords.model_dump()
        else:
            raise HTTPException(400, "Tipo de coordenada no válido")
    except Exception as e:
        raise HTTPException(400, f"Error de validación: {e}")
  
    return {
            "ellipsoid": data.ellipsoid,
            "coordinate_type": data.coordinate_type,
            "coordinates": result
    }