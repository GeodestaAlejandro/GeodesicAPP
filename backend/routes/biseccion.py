from fastapi import APIRouter, HTTPException
import math
from services.calculations import calculate_N
from constants import ELLIPSOID_MODELS, MAGNA_ORIGINS
from models import EllipsoidAndTypeInput
from services.transforms import arcMeridianP, calculated_E, calculated_N, calculated_alpha, calculated_beta, calculated_delta, calculated_n, calculated_epsilon, calculated_upsilon, dif_long
from services.validations import validate_coordinates

router = APIRouter()

@router.post("/transform_geodesic_to_SGK/")
def transformGeodesic(data: EllipsoidAndTypeInput):
    coordinates = validate_coordinates(data)
    system_reference = MAGNA_ORIGINS.get(data.system_reference)
    if not system_reference:
        raise HTTPException(400, "Sistema de referencia no valido")
    if data.system_reference == "Bogotá_MAGNA":
        latO = MAGNA_ORIGINS["Bogotá_MAGNA"].get("latitude", None)
        longO = MAGNA_ORIGINS["Bogotá_MAGNA"].get("longitude", None)
    elif data.system_reference == "BOGOTA_DATUM_ORIGINS":
        longO = MAGNA_ORIGINS["Este_Central_MAGNA"].get("longitude", None)
    elif data.system_reference == "Oeste_Oeste_MAGNA":
        longO = MAGNA_ORIGINS[" Oeste_Oeste_MAGNA"].get("longitude", None)
    ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)
    if not ellipsoid:
        raise HTTPException(400, "Modelo de elipsoide no válido")
    
    result = {}
    a = ellipsoid['a']
    b = float(a * (1 - ellipsoid["f"]))
    f = ellipsoid['f']
    e2 = 2 * f - f ** 2
    e22 = e2 / (1 - e2)
    coordinate_type = data.coordinate_type
    phi = latitude = math.radians(coordinates['coordinates']['latitude'])
    longP = longitude = math.radians(coordinates['coordinates']['longitude'])
    longO = math.radians(longO)
    latO = math.radians(latO)
    orthometricHeight = coordinates['coordinates']['orthometricHeight']
    if latitude and longitude is None:
        raise HTTPException(400, "Falta la latitud y longitud ")
    
    n = calculated_n(a, b)
    print("a", a, "->", "b", b)
    # Primer calculo de arco meridiano
    epsilon = calculated_epsilon(n)
    delta = calculated_delta(n)
    upsilon = calculated_upsilon(n)
    beta = calculated_beta(n)
    alpha = calculated_alpha(n, a, b)
    arcGp = arcMeridianP(alpha, beta, upsilon, delta, epsilon, phi)
    arcGO = arcMeridianP(alpha, beta, upsilon, delta, epsilon, latO)
    # calculo demas variables l, t, n, N
    l = dif_long(longP, longO)
    t = math.tan(phi)
    n2 = e22 * (math.cos(phi) ** 2)
    NN = calculate_N(latitude, ellipsoid)
    # Calculo de N, E.
    N = calculated_N(arcGp, arcGO, NN, l, t, n2, phi)
    E = calculated_E(NN, l, t, n2, phi)
    return N, E
# "arcGp", arcGp, "n",n, "elpsilon",epsilon, "delta",delta, "upsilon",upsilon, "beta",beta, "alpha",alpha
