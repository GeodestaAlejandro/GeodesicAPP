from fastapi import APIRouter
from constants import ELLIPSOID_MODELS
from fastapi.responses import StreamingResponse
from models import (EllipsoidAndTypeInput, EllipsoidAndTypeToAnguleInput, CartesianCoordinates, GeodesicCoordinates, ParametricCoordinates, dms_decimal)
from services.ellipsoidMeridian.geoCentricMeridian import xz_lat_geocentric
from services.ellipsoidMeridian.geodesicMeridian import lat_geod_to_xz, xz_to_lat_geod
from services.ellipsoidMeridian.parametricMeridian import theta_parametric_to_xz, xz_to_theta_parametric
from services.plotting.meridianPlotting import plot_meridian_ellipse_and_points, xz_ellipse_from_lat

router = APIRouter()

@router.post("/plot-ellipse-with-coordLatitude/")
async def plot_ellipse_coord(input: EllipsoidAndTypeInput):
    ellipsoid = ELLIPSOID_MODELS[input.ellipsoid]
    a = ellipsoid["a"]
    b = a * (1 - ellipsoid["f"])
  
    if input.coordinate_type == "Geodesic":
        coords = GeodesicCoordinates(**input.coordinates)
        if coords.latitudeGeodesic is None:
            raise ValueError("Debe proporcionar 'latitudeGeodesic' (decimal o DMS)")
        angle = coords.latitudeGeodesic
        x, z, N = lat_geod_to_xz(angle, ellipsoid)
    elif input.coordinate_type == "Geocentric":
        coords = CartesianCoordinates(**input.coordinates)
        if coords.X is None or coords.Z is None:
            raise ValueError("Debe proporcionar 'X' y 'Z' para coordenadas geocéntricas")
        x = coords.X  
        z = coords.Z  
        N = None  
    elif input.coordinate_type == "Parametric":  
        coords = ParametricCoordinates(**input.coordinates)  
        if coords.latitudeParametric is None:  
            raise ValueError("Debe proporcionar 'latitudeParametric' (decimal o DMS)")  
        angle = coords.latitudeParametric  
        x, z = theta_parametric_to_xz(angle, ellipsoid)  
        N = None  
    else:  
        raise ValueError("El tipo de coordenada no es válido")  
  
    if input.coordinate_type in ["Geodesic", "Parametric"]:
        label = f"{input.coordinate_type} ({angle:.6f}°)"
    else:  
        label = f"{input.coordinate_type} (X={x:.1f},Z={z:.1f})"
  
    
    points = [(x, z)]
    labels = [label]
    print("X,Z",x,z)
    buf = plot_meridian_ellipse_and_points(a, b, points, labels)  
    return StreamingResponse(buf, media_type="image/png") 

# Falta verificar si los datos si se estan verificando bien con coords...
@router.post("/plot-ellipse-with-XZ/")
async def plot_ellipse(input: dict):
    coords = CartesianCoordinates(**data.coordinates)
    X = input['coordinates']['X']
    Z = input['coordinates']['Z']
    ellipsoid = ELLIPSOID_MODELS.get(input['ellipsoid'])  
    a = ellipsoid['a']
    b = a * (1 - ellipsoid['f'])
  
    lat_geoc = xz_lat_geocentric(X, Z)  
    lat_geod = xz_to_lat_geod(X, Z, ellipsoid)  
    lat_param = xz_to_theta_parametric(X, Z, ellipsoid)  
  
    points = [  
        xz_ellipse_from_lat(a, b, lat_geoc),
        xz_ellipse_from_lat(a, b, lat_geod),
        xz_ellipse_from_lat(a, b, lat_param)
    ]  
    labels = [  
        f'Geocéntrica ({lat_geoc:.2f}°)',  
        f'Geodésica ({lat_geod:.2f}°)',  
        f'Paramétrica ({lat_param:.2f}°)'  
    ]  
  
    buf = plot_meridian_ellipse_and_points(a, b, points, labels)  
    return StreamingResponse(buf, media_type="image/png")