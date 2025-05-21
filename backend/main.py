from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.constants import COORDINATES_TYPE, ELLIPSOID_MODELS
from backend.models import CoordinateInput, EllipsoidAndTypeInput, GeocentricCoordinates, GeodesicCoordinates, ParametricCoordinates, TypeData
from backend.routes.calculations import router as calculations_router
from backend.services.conversions import EllipsoidModel

app = FastAPI(
    title="Geodesic Calculator",
    description="API para cálculos geodésicos.",
    version="0.0.1"
)

origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Geodesic Calculator API"}

@app.post("/choose-ellipsoid-type/")  
def choose_ellipsoid_type(data: EllipsoidAndTypeInput):  

    if data.coordinate_type == "Geodesic":  
        fields = ["latitudeGeodesic", "longitudeGeodesic", "orthometricHeight", "unit"]  
    elif data.coordinate_type == "Geocentric":  
        fields = ["X", "Y", "Z", "unit"]  
    elif data.coordinate_type == "Parametric":  
        fields = ["latitudeParametric", "longitudeParametric", "orthometricHeightParametric", "unit"]  
  
    return {  
        "ellipsoid": data.ellipsoid,  
        "coordinate_type": data.coordinate_type,  
        "expected_fields": fields  
    }  

@app.post("/validate-coordinates/")  
def validate_coordinates(data: CoordinateInput):  
    ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)  
    if not ellipsoid:  
        raise HTTPException(400, "Modelo de elipsoide no válido")  
  
    if data.coordinate_type == "Geodesic":  
        coords = GeodesicCoordinates(**data.coordinates)  
        # result = process_geodesic(coords, ellipsoid)  
    elif data.coordinate_type == "Geocentric":  
        coords = GeocentricCoordinates(**data.coordinates)  
        # result = process_geocentric(coords, ellipsoid)  
    elif data.coordinate_type == "Parametric":  
        coords = ParametricCoordinates(**data.coordinates)  
        # result = process_parametric(coords, ellipsoid)  
    else:  
        raise HTTPException(400, "Tipo de coordenada no válido")  
    return {"result"}  
