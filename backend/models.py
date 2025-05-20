import numpy as np
from pydantic import BaseModel, Field, validator
import re

# Ya estan todas las variables por tipo de sistema de coordenada y por una sola variable y 
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

class latitude(SingleParameter):
    pass

# class W(SingleParameter):
#     pass

class Theta(SingleParameter):
    pass

class longitude(SingleParameter):
    pass
# dos parametros geodesicos 
class TwoParameters(BaseModel):
    latitude: float
    longitude: float
# dos parametros geocentricos
class TwoParameters(BaseModel):
    x: float
    y: float

# three parameters
class GeodesicCoordinates(BaseModel):

    latitude: float = Field(..., ge=-90, le=90, descripcion="Laittud en grados")
    longitude: float = Field(..., ge=-180, le=180, descripcion="Longitud en grados")
    orthometric_height: float = Field(..., ge=0, le=9000)
    unit: str = Field(..., regex="^m$")

    @validator('latitud', 'longitud', pre=True)
    def convertir_a_decimal(cls, v):
        if isinstance(v, float) or isinstance(v, int):
            return float(v)
        if isinstance(v, str) and "°" in v:
            return dms_decimal(v)
        try:
            return float(v)
        except ValueError:
            raise ValueError("La coordenada debe ser decimal o en formato DMS")

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

class ParametricCoordinates(BaseModel):
    latitudeParametric: float = Field(..., ge=-90, le=90, descripcion="Laittud Parametrica en grados")
    longitudeParametric: float = Field(..., ge=-180, le=180, descripcion="Longitud Parametrica en grados")
    orthometric_heightParametric: float = Field(..., ge=0, le=9000)
    unit: str = Field(..., regex="^m$")
