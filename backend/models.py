from pydantic import BaseModel, Field, validator
import re

# Funcion gardos a decimales.
def dms_decimal(dms_str = str) -> float:

    pattern = r"(\d+)°(\d+)'([\d.]+)\""
    match = re.match(pattern, dms_str.trip())
    if not match:
        raise ValueError("Las coordenadas deben estar en formato de Grados, Minutos y Segundos ej:4°50'40.23\"")
        grados, minutos, segundos = map(float, match.groups())
        return grados + minutos / 60 + segundos / 3600
    
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
        
# Modelos de variables o angulos 
# class SingleParameter(BaseModel):
#     value: float

#     @validator("value")
#     def validate_value(cls, value):
#         if cls.__name__ == "Phi":
#             if not (-90 <= value <= 90):
#                 raise ValueError("Phi debe estar entre -90 y 90 grados")
#         elif cls.__name__ == "W":
#             # Validaciones específicas para W
#             pass
#         elif cls.__name__ == "Theta":
#             if not (-np.pi / 2 <= value <= np.pi / 2):
#                 raise ValueError("Theta debe estar entre -π/2 y π/2 radianes")
#         return value


# class Phi(SingleParameter):
#     pass


# class W(SingleParameter):
#     pass


# class Theta(SingleParameter):
#     pass


class TwoParameters(BaseModel):
    phi: float
    lambda_: float


class ThreeParameters(BaseModel):
    phi: float
    lambda_: float
    height: float

class GeocentricCoordinates(BaseModel):
    X: float
    Y: float
    Z: float

    @validator("X", "Y", "Z")
    def validate_coordinates(cls, value):
        if abs(value) > 1e10:
            raise ValueError("Coordenadas geocéntricas fuera de rango")
        return value



class ParametricCoordinates(BaseModel):
    phi: float
    lambda_: float
    h: float

    # @validator("phi")
    # def validate_phi(cls, value):
    #     if not (-np.pi / 2 <= value <= np.pi / 2):  # Radianes válidos para latitud
    #         raise ValueError("Phi debe estar entre -π/2 y π/2 radianes")
    #     return value

    # @validator("lambda_")
    # def validate_lambda(cls, value):
    #     if not (-np.pi <= value <= np.pi):  # Radianes válidos para longitud
    #         raise ValueError("Lambda debe estar entre -π y π radianes")
    #     return value

    @validator("h")
    def validate_h(cls, value):
        if value < 0:
            raise ValueError("Altura no puede ser negativa")
        return value

class coordinates(BaseModel):
    latitude: float
    longitude: float
    orthometric_height: float
