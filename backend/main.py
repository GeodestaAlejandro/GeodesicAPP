from typing import Any, Optional
from fastapi import FastAPI, HTTPException  
from fastapi.middleware.cors import CORSMiddleware
from routes.plotEllipse import router as plotEllipse_router
from routes.coordinatesMeridianEllipse import router as coordinatesMeridianEllipse_router
from routes.coordinatesEllipsoid import router as coordinatesEllipsoid_router
from routes.biseccion import router as biseccion_router
from models import (EllipsoidAndTypeInput)
  
app = FastAPI(
    title="Geodesic Calculator",
    description="API para cálculos geodésicos.",
    version="0.0.1"
)

app.include_router(plotEllipse_router)
app.include_router(coordinatesMeridianEllipse_router)
app.include_router(coordinatesEllipsoid_router)
app.include_router(biseccion_router)

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

# @app.post("/validate-coordinates/")
# def validate_coordinates(data: EllipsoidAndTypeInput):
#     ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)
#     if not ellipsoid:
#         raise HTTPException(400, "Modelo de elipsoide no válido")
  
#     try:
#         if data.coordinate_type == "Geodesic":
#             coords = GeodesicCoordinates(**data.coordinates)
#             result = coords.model_dump()
#         elif data.coordinate_type == "Geocentric":
#             coords = CartesianCooordenates(**data.coordinates)
#             result = coords.model_dump()
#         elif data.coordinate_type == "Parametric":
#             coords = ParametricCoordinates(**data.coordinates)
#             result = coords.model_dump()
#         else:
#             raise HTTPException(400, "Tipo de coordenada no válido")
#     except Exception as e:
#         raise HTTPException(400, f"Error de validación: {e}")
  
#     return {
#         "ellipsoid": data.ellipsoid,
#         "coordinate_type": data.coordinate_type,
#         "coordinates": result
#     }