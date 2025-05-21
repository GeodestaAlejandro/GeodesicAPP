import numpy as np
from pydantic import BaseModel, Field, validator
import re
from typing import Any, Dict, Literal  
  
class EllipsoidAndTypeInput(BaseModel):
    ellipsoid: Literal["WGS84", "GRS80", "WGS72"]
    coordinate_type: Literal["Geodesic", "Geocentric", "Parametric"]

class CoordinateInput(BaseModel):
    ellipsoid: Literal["WGS84", "GRS80", "WGS72"]
    coordinate_type: Literal["Geodesic", "Geocentric", "Parametric"]
    coordinates: Dict[str, Any]

# Modelo de elipsoides y geoides.
class EllipsoidModel:
    def __init__(self, model="WGS84"):
        params = EllipsoidModel.get(model)
        self.a = params("a")
        self.f = params("f")
        self.b = self.a * (1 - self.f)

    @property
    def e2(self):

        """Excentricidad al cuadrado."""
        return self.f * (2 - self.f)

# Ya estan todas las variables por tipo de sistema de coordenada y por una sola variable.
# Funcion gardos a decimales.
def dms_decimal(dms_str = str) -> float:

    pattern = r"(\d+)°(\d+)'([\d.]+)\""
    match = re.match(pattern, dms_str.trip())
    if not match:
        raise ValueError("Las coordenadas deben estar en formato de Grados, Minutos y Segundos ej:4°50'40.23\"")
        grados, minutos, segundos = map(float, match.groups())
        return grados + minutos / 60 + segundos / 3600
        
# Modelos de variables o angulos individuales
class SingleParameter(BaseModel):
    value: float

    @validator("value", pre=True)
    def validate_value(cls, value):
        if cls.__name__ == "latitude":
            if not (-90 <= value <= 90):
                raise ValueError("La latitud phi debe estar entre -90 y 90 grados")
        elif cls.__name__ == "Theta":
            if not (-np.pi / 2 <= value <= np.pi / 2):
                raise ValueError("Theta debe estar entre -π/2 y π/2 radianes")
        elif cls.__name__ == "longitude":
            if not (-180 <= value <= 180):
                raise ValueError("La longitud lambda debe estar entre -180° y 180°")

#  Single parameter geodesic.
class latitudeGeodesic(SingleParameter):
    pass
class longitudeGeodesic(SingleParameter):
    pass

# single parameter geocentrics.
class w(SingleParameter):
    pass
class longitudeGeocentric(SingleParameter):
    pass

#  Single parameter parametric.
class latitudeParametric(SingleParameter):
    pass
class longitudeParametric(SingleParameter):
    pass

# # dos parametros geodesicos 
# class TwoParameters(BaseModel):
#     latitude: float
#     longitude: float
# # dos parametros geocentricos
# class TwoParameters(BaseModel):
#     x: float
#     y: float

# three parameters - coordinates Geodesics
class GeodesicCoordinates(BaseModel):

    latitudeGeodesic: float = Field(..., ge=-90, le=90, descripcion="Latitud en grados")
    longitudeGeodesic: float = Field(..., ge=-180, le=180, descripcion="Longitud en grados")
    orthometricHeight: float = Field(..., ge=0, le=9000)
    unit: str = Field(..., regex="^m$")

    @validator('latitudeGeodesic', 'longitudeGeodesic', pre=True)
    def convertir_a_decimal(cls, v):
        if isinstance(v, float) or isinstance(v, int):
            return float(v)
        if isinstance(v, str) and "°" in v:
            return dms_decimal(v)
        try:
            return float(v)
        except ValueError:
            raise ValueError("La coordenada debe ser decimal o en formato DMS")

#  trhee Parameters - coordinates Geocentric.
class GeocentricCoordinates(BaseModel):

    X: float = Field(..., ge= -6500000,le=65000000, descripcion="Distancia X")
    Y: float = Field(..., ge= -65000000, le=65000000, description="Distancia Y")
    Z: float = Field(..., ge=65000000, le=65000000, description="Distancia de altura")
    unit: str = Field(..., regex="^m$")

    # @validator("X", "Y", "Z")
    # def validate_coordinates(cls, value):
    #     if abs(value) > 1e10:
    #         raise ValueError("Coordenadas geocéntricas fuera de rango")
    #     return value

#  Three Parameter - coordinate Parametrics.
class ParametricCoordinates(BaseModel):

    latitudeParametric: float = Field(..., ge=-90, le=90, descripcion="Laittud Parametrica en grados")
    longitudeParametric: float = Field(..., ge=-180, le=180, descripcion="Longitud Parametrica en grados")
    orthometricHeightParametric: float = Field(..., ge=0, le=9000)
    unit: str = Field(..., regex="^m$")
    
    @validator('latitudeParametric', 'longitudeParametric', pre=True)
    def convertir_a_decimal(cls, v):
        if isinstance(v, float) or isinstance(v, int):
            return float(v)
        if isinstance(v, str) and "°" in v:
            return dms_decimal(v)
        try:
            return float(v)
        except ValueError:
            raise ValueError("La coordenada debe ser decimal o en formato DMS")
