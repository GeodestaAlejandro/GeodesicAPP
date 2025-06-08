from fastapi import APIRouter, HTTPException
import math
from constants import ELLIPSOID_MODELS
from models import EllipsoidAndTypeInput
from services.validations import validate_coordinates
from services.calculations import geocentricGeodesic_from_parametric, parametricGeocentric_from_geodesic, parametricGeodesic_from_geocentric

router = APIRouter()

@router.post("/calculate_angles/")
def calculateAngules(data: EllipsoidAndTypeInput):
    coordinates = validate_coordinates(data)
    # print(coordinates)
    ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)
    if not ellipsoid:  
        raise HTTPException(400, "Modelo de elipsoide no válido")

    a = ellipsoid['a']
    b = float(a * (1 - ellipsoid["f"]))
    f = ellipsoid['f']
    e2 = 2 * f - f ** 2
    try: 
        result = {}
        if data.coordinate_type == "Geodesic":
            # print(coordinates['coordinates']['latitudeGeodesic'])
            latitudeGeodesic = math.radians(coordinates['coordinates']['latitudeGeodesic'])
            if latitudeGeodesic is None:
                raise HTTPException(400, "Falta la latitud geodesica")
            beta, psi = parametricGeocentric_from_geodesic(a, b, e2, latitudeGeodesic)
            result["latitudeParametric"] = math.degrees(beta)
            result["latitudeGeocentric"] = math.degrees(psi)

        elif data.coordinate_type == "Geocentric":
            # print(coordinates['coordinates']['latitudeGeocentric'])
            latitudeGeocentric = math.radians(coordinates['coordinates']['latitudeGeocentric'])
            if latitudeGeocentric is None:
                raise HTTPException(400, "Falta la latitud geocentrica")
            beta, phi = parametricGeodesic_from_geocentric(a, b, e2, latitudeGeocentric)
            result["latitudeParametric"] = math.degrees(beta)
            result["latitudeGeodesic"] = math.degrees(phi)

        elif data.coordinate_type == "Parametric":
            # print(coordinates['coordinates']['latitudeParametric'])
            latitudeParametric = math.radians(coordinates['coordinates']['latitudeParametric'])
            if latitudeParametric is None:
                raise HTTPException(400, "Falta la latitud paramétrica")
            phi, psi = geocentricGeodesic_from_parametric(a, b, e2, latitudeParametric)
            result["latitudeGeodesic"] = math.degrees(phi)
            result["latitudeGeocentric"] = math.degrees(psi)
        else:
            raise HTTPException(400, "Tipo de coordenada no válido")

    except Exception as e:
        raise HTTPException(400, f"Error de cálculo: {e}")

    return result