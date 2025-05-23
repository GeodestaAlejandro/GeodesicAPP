from typing import Any, Optional
from fastapi import FastAPI, HTTPException  
from fastapi.middleware.cors import CORSMiddleware  
from constants import ELLIPSOID_MODELS  
from models import (EllipsoidAndTypeInput, EllipsoidAndTypeToAnguleInput, GeocentricCoordinates, GeodesicCoordinates, ParametricCoordinates)
from services.ellipsoidMeridian.geoCentricMeridian import xz_lat_geocentric
from services.ellipsoidMeridian.geodesicMeridian import lat_geod_to_xz, xz_to_lat_geod
from services.ellipsoidMeridian.parametricMeridian import theta_parametric_to_xz, xz_to_theta_parametric
  
app = FastAPI(  
    title="Geodesic Calculator",  
    description="API para cálculos geodésicos.",  
    version="0.0.1"  
)  

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]  
)
  
@app.get("/")
def home():
    return {"message": "Geodesic Calculator API"}
  
@app.get("/choose-ellipsoid-type/")
def choose_ellipsoid_type(data: EllipsoidAndTypeInput):
    if data.coordinate_type == "Geodesic":
        fields = ["latitudeGeodesic", "longitudeGeodesic", "orthometricHeight", "unit"]
    elif data.coordinate_type == "Geocentric":
        fields = Optional[Any] = ["X", "Y", "Z", "unit"]
    elif data.coordinate_type == "Parametric":
        fields = ["latitudeParametric", "longitudeParametric", "orthometricHeightParametric", "unit"]
    else:
        raise HTTPException(400, "Tipo de coordenada no válido")
    return {
        "ellipsoid": data.ellipsoid,
        "coordinate_type": data.coordinate_type,
        "expected_fields": fields
    }

@app.post("/validate-coordinates/")
def validate_coordinates(data: EllipsoidAndTypeInput):
    ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)
    if not ellipsoid:
        raise HTTPException(400, "Modelo de elipsoide no válido")
  
    try:
        if data.coordinate_type == "Geodesic":
            coords = GeodesicCoordinates(**data.coordinates)
            result = coords.model_dump()
        elif data.coordinate_type == "Geocentric":
            coords = GeocentricCoordinates(**data.coordinates)
            result = coords.model_dump()
        elif data.coordinate_type == "Parametric":
            coords = ParametricCoordinates(**data.coordinates)
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

@app.post("/calculate_xz_with_angules/")  
def calculate_xz(data: EllipsoidAndTypeInput):  
    ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)  
    if not ellipsoid:  
        raise HTTPException(400, "Modelo de elipsoide no válido")  
      
    try:
        if data.coordinate_type == "Geodesic":  
            coords = GeodesicCoordinates(**data.coordinates)  
            latitudeGeodesic = coords.latitudeGeodesic
            X, Z, Rg = lat_geod_to_xz(latitudeGeodesic, ellipsoid)  
        elif data.coordinate_type == "Geocentric":  
            coords = GeocentricCoordinates(**data.coordinates)
            X = coords.X
            Z = coords.Z
            Rg = (X**2 + Z**2)**0.5  
        elif data.coordinate_type == "Parametric":  
            coords = ParametricCoordinates(**data.coordinates)  
            latitudeParametric = coords.latitudeParametric  
            X, Z, Rg = theta_parametric_to_xz(latitudeParametric, ellipsoid)  
        else:  
            raise HTTPException(400, "Tipo de coordenada no válido")
    except Exception as e:  
        raise HTTPException(400, f"Error de cálculo: {e}")
      
    return {"X": X, "Z": Z, "Rg": Rg}

@app.post("/calculate_angules_with_xz/")  
def calculate_angules(data: EllipsoidAndTypeToAnguleInput):  
    ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)  
    if not ellipsoid:  
        raise HTTPException(400, "Modelo de elipsoide no válido")  
  
    try:  
        coords = GeocentricCoordinates(**data.coordinates)  
        X = coords.X  
        Y = coords.Y  
        Z = coords.Z  
        print(X,Y,Z)
        if X is None or (data.coordinate_type_want in ["Geodesic", "Parametric"] and Y is None) or (data.coordinate_type_want == "Geocentric" and Z is None):
            raise HTTPException(400, "Coordenadas incompletas para el cálculo")
        if data.coordinate_type_want == "Geodesic":  
            latitudeGeodesic = xz_to_lat_geod(X, Y, ellipsoid)  
            if latitudeGeodesic is None:  
                raise HTTPException(400, "Error en el cálculo Geodesic")  
            return latitudeGeodesic  
        elif data.coordinate_type_want == "Geocentric":  
            latitudeGeodesic = xz_lat_geocentric(X, Z, ellipsoid)  
            if latitudeGeodesic is None:  
                raise HTTPException(400, "Error en el cálculo Geocentric")  
            return latitudeGeodesic  
        elif data.coordinate_type_want == "Parametric":  
            latitudeParametric = xz_to_theta_parametric(X, Y, ellipsoid)  
            if latitudeParametric is None:  
                raise HTTPException(400, "Error en el cálculo Parametric")  
            return latitudeParametric  
        else:  
            raise HTTPException(400, "Tipo de coordenada no válido")  
  
    except Exception as e:  
        raise HTTPException(400, f"Error de cálculo: {e}")  

# @app.post("/calculate_angules_with_xz/")  
# def calculate_angules(data: EllipsoidAndTypeToAnguleInput):
#     ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)
#     print(ellipsoid)
#     if not ellipsoid:  
#         raise HTTPException(400, "Modelo de elipsoide no válido")
#     try:
#         if data.coordinate_type_want == "Geodesic":
#             coords =GeocentricCoordinates(**data.coordinates)
#             X = coords.X
#             Y = coords.Y
#             latitudeGeodesic = xz_to_lat_geod(X, Y, ellipsoid)
#             return (latitudeGeodesic)
#         elif data.coordinate_type_want == "Geocentric":
#             coords = GeocentricCoordinates(**data.coordinates)
#             X = coords.X
#             Z = coords.Z
#             Rg = (X**2 + Z**2)**0.5
#             latitudeGeodesic = xz_lat_geocentric(X, Z, ellipsoid)
#             return (latitudeGeodesic)
#         elif data.coordinate_type_want == "Parametric":
#             coords = GeocentricCoordinates(**data.coordinates)
#             X = coords.X
#             Y = coords.Y
#             latitudeParametric = xz_to_theta_parametric(X, Y, ellipsoid)
#             return (latitudeParametric)
#         else:  
#             raise HTTPException(400, "Tipo de coordenada no válido")
#     except Exception as e:  
#         raise HTTPException(400, f"Error de cálculo: {e}")

