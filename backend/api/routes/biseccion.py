from fastapi import APIRouter, HTTPException
import math
from services.transformsI import calculated_lat, calculatedI_alpha, calculatedI_beta, calculatedI_delta, calculatedI_epsilon, calculatedI_upsilon, dif_east_m, dif_nort_m, latP, calculated_long
from services.calculations import calculate_N
from constants import BOGOTA_DATUM_ORIGINS, ELLIPSOID_MODELS, MAGNA_ORIGINS
from models import EllipsoidAndTypeInput
from services.transformsD import arcMeridianP, calculated_E, calculated_N, calculated_alpha, calculated_beta, calculated_delta, calculated_n, calculated_epsilon, calculated_upsilon, dif_long
from services.validations import validate_coordinates

router = APIRouter()

@router.post("/transform_SGK_to_Geodesic/")
def transformGeodesic(data: EllipsoidAndTypeInput):
    coordinates = validate_coordinates(data)
    system_reference = MAGNA_ORIGINS.get(data.system_reference)
    if not system_reference:
        raise HTTPException(400, "Sistema de referencia no valido")
    if data.system_reference == "Bogotá_MAGNA":
        nort_mO = MAGNA_ORIGINS["Bogotá_MAGNA"].get("nort_m", 1000000)
        east_mO = MAGNA_ORIGINS["Bogotá_MAGNA"].get("east_m", None)
        longO = MAGNA_ORIGINS["Bogotá_MAGNA"].get("longitude", None)
    elif data.system_reference == "BOGOTA_DATUM_ORIGINS":
        nort_mO = BOGOTA_DATUM_ORIGINS["Bogotá_BOGOTA"].get("nort_m", None)
        east_mO = BOGOTA_DATUM_ORIGINS["Bogotá_BOGOTA"].get("east_m", None)
    elif data.system_reference == "Oeste_Oeste_MAGNA":
        longO = MAGNA_ORIGINS[" Oeste_Oeste_MAGNA"].get("longitude", None)
    ellipsoid = ELLIPSOID_MODELS.get(data.ellipsoid)
    if not ellipsoid:
        raise HTTPException(400, "Modelo de elipsoide no válido")
    
    a = ellipsoid['a']
    b = float(a * (1 - ellipsoid["f"]))
    f = ellipsoid['f']
    e2 = 2 * f - f ** 2
    e22 = e2 / (1 - e2)
    nort_mP = coordinates['coordinates']['nort_m']
    east_mP = coordinates['coordinates']['east_m']

    if nort_mP and east_mP is None:
        raise HTTPException(400, "Falta norte y este ")
    
    # primer calculo
    n = calculated_n(a, b)
    epsilon = calculatedI_epsilon(n)
    delta = calculatedI_delta(n)
    upsilon = calculatedI_upsilon(n)
    beta = calculatedI_beta(n)
    alpha = calculatedI_alpha(n, a, b)
    delta_nort = dif_nort_m(nort_mP, nort_mO)
    delta_east = dif_east_m(east_mP, east_mO)
    latPSubf = latP(delta_nort, alpha, beta, upsilon, delta, epsilon)
    NN = calculate_N(latPSubf, ellipsoid)
    tSubf = math.tan(latPSubf)
    n2 = e22 * (math.cos(latPSubf) ** 2)
    long = calculated_long(delta_east, NN, latPSubf, tSubf, longO, n2)
    lat = calculated_lat(delta_east, NN, latPSubf, tSubf, n2)
    return lat, long

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
    
    a = ellipsoid['a']
    b = float(a * (1 - ellipsoid["f"]))
    f = ellipsoid['f']
    e2 = 2 * f - f ** 2
    e22 = e2 / (1 - e2)
    phi = latitude = math.radians(coordinates['coordinates']['latitude'])
    longP = longitude = math.radians(coordinates['coordinates']['longitude'])
    # print("phi", phi, "lonP", longP)
    # print("a", a, "f", f, "e2", e2)
    longO = math.radians(longO)
    latO = math.radians(latO)
    if latitude and longitude is None:
        raise HTTPException(400, "Falta la latitud y longitud ")
    
    n = calculated_n(a, b)
    print(n)
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
    print(arcGp)
    # Calculo de N, E.
    N = calculated_N(arcGp, arcGO, NN, l, t, n2, phi)
    E = calculated_E(NN, l, t, n2, phi)
    return N, E
# "arcGp", arcGp, "n",n, "elpsilon",epsilon, "delta",delta, "upsilon",upsilon, "beta",beta, "alpha",alpha
