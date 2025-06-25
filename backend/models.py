import re  
from typing import Any, Dict, Literal, Optional  
from pydantic import BaseModel, Field, root_validator, validator  
  
def dms_decimal(dms_str: str) -> float:
    pattern = r"\s*([+-]?\d+)°\s*(\d+)'[\s]*([\d.]+)\""  
    match = re.match(pattern, dms_str.strip())
    if not match:
        raise ValueError("Las coordenadas deben estar en formato Grados, Minutos y Segundos, ej: 4°50'40.23\"")
    grados, minutos, segundos = map(float, match.groups())
    return grados + minutos / 60 + segundos / 3600
  
class GeodesicCoordinates(BaseModel):  
    latitude: Optional[float] = Field(None, ge=-90, le=90)  
    longitude: Optional[float] = Field(None, ge=-180, le=180)  
    orthometricHeight: Optional[float] = Field(None, ge=0, le=9000)
      
    @validator('latitude', 'longitude', pre=True)
    def parse_dms_or_decimal(cls, v):
        if isinstance(v, (float, int)):
            return float(v)
        if isinstance(v, str) and "°" in v:
            return dms_decimal(v)
        try:
            return float(v)
        except Exception:
            raise ValueError("La coordenada debe ser decimal o en formato DMS")

class GausKruger(BaseModel):
    nort_m: Optional[float] = Field(None, ge=1000000)
    east_m: Optional[float] = Field(None, ge=1000000)

class geocentricCardCoord(BaseModel):
    X: Optional[float] = Field(None, ge=-6_500_000, le=6_500_000)
    Y: Optional[float] = Field(None, ge=-6_500_000, le=6_500_000)
    Z: Optional[float] = Field(None, ge=-6_500_000, le=6_500_000)
  
    @validator('X', 'Y', 'Z', pre=True)
    def parse_numeric(cls, v):
        if isinstance(v, (float, int)):
            return float(v)
        try:
            return float(v)
        except Exception:
            raise ValueError("Cada coordenada debe ser un número válido (float o int)")
        
class GeocentricAngles(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0,)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0,)
    orthometricHeight: Optional[float] = Field(None, ge=-500.0, le=10000.0, )
    
    @validator('latitude', 'longitude', pre=True)
    def parse_dms_or_decimal(cls, v):
        if isinstance(v, (float, int)):
            return float(v)
        if isinstance(v, str) and "°" in v:
            return dms_decimal(v)
        try:
            return float(v)  
        except Exception:  
            raise ValueError("La coordenada debe ser decimal o en formato DMS")
    
class ParametricCoordinates(BaseModel):  
    latitude: Optional[float] = Field(None, ge=-90, le=90)  
    longitude: Optional[float] = Field(None, ge=-180, le=180)  
    orthometricHeight: Optional[float] = Field(None, ge=0, le=9000)  
    unit: Optional[str] = Field(None, pattern="^m$")  
  
    @validator('latitude', 'longitude', pre=True)
    def parse_dms_or_decimal(cls, v):
        if isinstance(v, (float, int)):
            return float(v)
        if isinstance(v, str) and "°" in v:
            return dms_decimal(v)
        try:
            return float(v)
        except Exception:
            raise ValueError("La coordenada debe ser decimal o en formato DMS")
  
class EllipsoidAndTypeInput(BaseModel):
    ellipsoid: Literal["WGS84", "GRS80", "WGS72"]
    coordinate_type: Literal["Geodesic", "Geocentric", "Parametric", "Cartesian", "GausKruger"]
    system_reference: Optional[str] = Literal["magnaOrigins", "bogotaDatum"]
    coordinates: Dict[str, Any]

class EllipsoidAndTypeToAnguleInput(BaseModel):
    ellipsoid: Literal["WGS84", "GRS80", "WGS72"]
    coordinate_type_want: Literal["Geodesic", "Geocentric", "Parametric", "Cartesian", "GausKruger"]
    coordinates: Dict[str, Any]

    
