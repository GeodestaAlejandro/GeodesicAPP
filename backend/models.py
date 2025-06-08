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
    latitudeGeodesic: Optional[float] = Field(None, ge=-90, le=90)  
    longitudeGeodesic: Optional[float] = Field(None, ge=-180, le=180)  
    orthometricHeight: Optional[float] = Field(None, ge=0, le=9000)  
    unit: Optional[str] = Field(None, pattern="^m$")  
  
    @validator('latitudeGeodesic', 'longitudeGeodesic', pre=True)  
    def parse_dms_or_decimal(cls, v):  
        if isinstance(v, (float, int)):  
            return float(v)  
        if isinstance(v, str) and "°" in v:  
            return dms_decimal(v)  
        try:  
            return float(v)  
        except Exception:  
            raise ValueError("La coordenada debe ser decimal o en formato DMS")  
  
class CartesianCoordinates(BaseModel):
    X: Optional[float] = Field(None)
    Y: Optional[float] = Field(None)
    Z: Optional[float] = Field(None)
    
class GeocentricCoordinates(BaseModel):
    latitudeGeocentric: Optional[float] = Field(None, ge=-90.0, le=90.0,)
    longitudeGeocentric: Optional[float] = Field(None, ge=-180.0, le=180.0,)
    orthometricHeight: Optional[float] = Field(None, ge=-500.0, le=10000.0, )
    
    @validator('latitudeGeocentric', 'longitudeGeocentric', pre=True)  
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
    latitudeParametric: Optional[float] = Field(None, ge=-90, le=90)  
    longitudeParametric: Optional[float] = Field(None, ge=-180, le=180)  
    orthometricHeightParametric: Optional[float] = Field(None, ge=0, le=9000)  
    unit: Optional[str] = Field(None, pattern="^m$")  
  
    @validator('latitudeParametric', 'longitudeParametric', pre=True)
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
    coordinate_type: Literal["Geodesic", "Geocentric", "Parametric"]
    coordinates: Dict[str, Any]

class EllipsoidAndTypeToAnguleInput(BaseModel):
    ellipsoid: Literal["WGS84", "GRS80", "WGS72"]
    coordinate_type_want: Literal["Geodesic", "Geocentric", "Parametric"]
    coordinates: Dict[str, Any]

    
