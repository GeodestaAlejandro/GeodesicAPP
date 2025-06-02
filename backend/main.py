from typing import Any, Optional
from fastapi import FastAPI, HTTPException  
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse  
from constants import ELLIPSOID_MODELS  
from models import (EllipsoidAndTypeInput, EllipsoidAndTypeToAnguleInput, GeocentricCoordinates, GeodesicCoordinates, ParametricCoordinates, dms_decimal)
from services.ellipsoidMeridian.geoCentricMeridian import lat_geocentric_to_xz, xz_lat_geocentric
from services.ellipsoidMeridian.geodesicMeridian import lat_geod_to_xz, xz_to_lat_geod
from services.ellipsoidMeridian.parametricMeridian import theta_parametric_to_xz, xz_to_theta_parametric
from services.plotting.meridianPlotting import plot_meridian_ellipse_and_points, xz_ellipse_from_lat
  
app = FastAPI(  
    title="Geodesic Calculator",  
    description="API para cálculos geodésicos.",  
    version="0.0.1"  
)

@app.post("/plot-ellipse-coord/")  
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
        coords = GeocentricCoordinates(**input.coordinates)
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


@app.post("/plot-ellipse/")
async def plot_ellipse(input: dict):
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
            latitudeGeocentric = xz_lat_geocentric(X, Z, ellipsoid)
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
#   
    except Exception as e:  
        raise HTTPException(400, f"Error de cálculo: {e}")  
