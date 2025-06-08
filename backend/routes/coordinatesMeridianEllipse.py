from fastapi import APIRouter, HTTPException
from typing import Optional
from constants import ELLIPSOID_MODELS
from fastapi.responses import StreamingResponse
from models import (EllipsoidAndTypeInput, EllipsoidAndTypeToAnguleInput, CartesianCoordinates, GeodesicCoordinates, ParametricCoordinates, dms_decimal)
from services.ellipsoidMeridian.geoCentricMeridian import xz_lat_geocentric
from services.ellipsoidMeridian.geodesicMeridian import lat_geod_to_xz, xz_to_lat_geod
from services.ellipsoidMeridian.parametricMeridian import theta_parametric_to_xz, xz_to_theta_parametric
from services.plotting.meridianPlotting import plot_meridian_ellipse_and_points, xz_ellipse_from_lat

router = APIRouter()

@router.post("/calculate_xz_with_angules/")
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
            coords = CartesianCoordinates(**data.coordinates)
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

@router.post("/calculate_angules_with_xz/")
def calculate_angules(data: EllipsoidAndTypeToAnguleInput):
    ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)
    if not ellipsoid:
        raise HTTPException(400, "Modelo de elipsoide no válido")
  
    try:
        coords = CartesianCoordinates(**data.coordinates)  
        X = coords.X
        Y = Optional[coords.Y]
        Z = coords.Z
        print(X,Y,Z)
        if X is None or (data.coordinate_type_want in ["Geodesic", "Parametric"] and Y is None) or (data.coordinate_type_want == "Geocentric" and Z is None):
            raise HTTPException(400, "Coordenadas incompletas para el cálculo")
        if data.coordinate_type_want == "Geodesic":  
            latitudeGeodesic = xz_to_lat_geod(X, Z, ellipsoid)  
            if latitudeGeodesic is None:  
                raise HTTPException(400, "Error en el cálculo Geodesic")  
            return {"Latitud Geodesica (angle)": latitudeGeodesic}
        elif data.coordinate_type_want == "Geocentric":
            latitudeGeocentric = xz_lat_geocentric(X, Z)
            if latitudeGeocentric is None:
                raise HTTPException(400, "Error en el cálculo Geocentric")
            return {"Latitud Geocentrica (W)": latitudeGeocentric}
        elif data.coordinate_type_want == "Parametric":
            latitudeParametric = xz_to_theta_parametric(X, Z, ellipsoid)
            if latitudeParametric is None:
                raise HTTPException(400, "Error en el cálculo Parametric")
            return {"Latitud Parametrica (Omega)": latitudeParametric}
        else:
            raise HTTPException(400, "Tipo de coordenada no válido")
          
    except Exception as e:
        raise HTTPException(400, f"Error de cálculo: {e}")
