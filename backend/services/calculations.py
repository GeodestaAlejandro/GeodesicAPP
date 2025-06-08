import numpy as np
import math

# Calcula el radio de curvatura en el primer vertical.
def calculate_N(latitude, ellipsoid):
    e2 = ellipsoid.e2
    a = ellipsoid.a
    return a / np.sqrt(1 - e2 * np.sin(np.radians(latitude))**2)

# def calculate_Rg(logitudeGeocentric, ellipsoid):
#     e2 = ellipsoid.e2
  
def calculate_Rg(latitude_deg, ellipsoid, h=0):  

    a = ellipsoid.a  
    e2 = ellipsoid.e2  
    lat_rad = np.radians(latitude_deg)  
    sin_lat = np.sin(lat_rad)  
    cos_lat = np.cos(lat_rad)  
      
    N = a / np.sqrt(1 - e2 * sin_lat**2)  
    X = (N + h) * cos_lat  
    Z = (N * (1 - e2) + h) * sin_lat  
      
    Rg = np.sqrt(X**2 + Z**2)  
    return Rg

def geocentricGeodesic_from_parametric(a, b, e2, f, latitudeParametric):
    # Dada beta (latitud paramétrica), calcula phi (latitud geodésica)
    def geodesic_from_parametric(f, latitudeParametric):
        # EJEMPLO DE COMPROBACION DE ECUACIÓN
        # ab = np.divide(a, b)
        # print("a / b =", ab)  
        # print("latitudeeeeee",latitudeParametric)
        # tan_lat_param = math.tan(latitudeParametric)  
        # print("tan(latitudeParametric) =", tan_lat_param)  
        # mult = ab * (tan_lat_param)  
        # print("(a / b) * tan(latitudeParametric) =", mult)  
        # phi = math.atan(mult)
        # print("atan((a / b) * tan(latitudeParametric)) =", phi, "radianes")  
        # print("Resultado en grados =", math.degrees(phi), "°")  
        # return phi
        # return math.atan((a / b) * math.tan(latitudeParametric))
        return math.atan(math.tan(latitudeParametric) / (1 - f))
    # Dada beta (latitud paramétrica), calcula psi (latitud geocéntrica)
    def geocentric_from_parametric(a, b, e2, latitudeParametric):
            return math.atan((1 - e2) * (a / b) * math.tan(latitudeParametric))
        
    phi = geodesic_from_parametric(f, latitudeParametric)
    psi = geocentric_from_parametric(a, b, e2, latitudeParametric)
    return phi, psi

def parametricGeocentric_from_geodesic(e2, f, latitudeGeodesic):
    #  Dada phi (latitud geodésica), calcula beta (latitud paramétrica)
    def parametric_from_geodesic(f, latitudeGeodesic):
        # return math.atan((b / a) * math.tan(latitudeGeodesic))
        return math.atan((1 - f) * math.tan(latitudeGeodesic))  
    # Dada phi (latitud geodésica), calcula psi (latitud geocéntrica)
    def geocentric_from_geodesic(e2, latitudeGeodesic):
        return math.atan((1 - e2) * math.tan(latitudeGeodesic))
    beta = parametric_from_geodesic(f, latitudeGeodesic)
    print("beta",beta)
    psi = geocentric_from_geodesic(e2, latitudeGeodesic)
    return beta, psi

def parametricGeodesic_from_geocentric(a, b, e2, latitudeGeocentric):
    # Dada psi (latitud geocéntrica), calcula phi (latitud geodésica)
    def geodesic_from_geocentric(e2, latitudeGeocentric):
        return math.atan(math.tan(latitudeGeocentric) / (1 - e2))
    # Dada psi (latitud geocéntrica), calcula beta (latitud paramétrica)
    def parametric_from_geocentric(a, b, e2, latitudeGeocentric):
        # al parecer da igual la que se use, siempre dejo las que se asemejen mas al libro del profesor.
        # return math.atan((b / a) * (math.tan(latitudeGeocentric) / (1 - e2)))
        return math.atan((a / b) * (1 - e2) * math.tan(latitudeGeocentric))
    phi = geodesic_from_geocentric(e2, latitudeGeocentric)
    beta = parametric_from_geocentric(a, b, e2, latitudeGeocentric)
    return phi, beta

# Calcula (x, z) en función de latitude.
def calculate_xz_from_latitude(latitude, ellipsoid):
    e2 = ellipsoid.e2
    N = calculate_N(latitude, ellipsoid)
    x = N * np.cos(np.radians(latitude))
    z = N * (1 - e2) * np.sin(np.radians(latitude))
    return {"x": x, "z": z}

# Calcula (x, y, z) en función de latitude, longitude y altura orthometric_height.
def calculate_xyz_from_latitude_longitude(latitude, longitude_, orthometric_height=0, ellipsoid=str):
    N = calculate_N(latitude, ellipsoid)
    e2 = ellipsoid.e2
    x = (N + orthometric_height) * np.cos(np.radians(latitude)) * np.cos(np.radians(longitude_))
    y = (N + orthometric_height) * np.cos(np.radians(latitude)) * np.sin(np.radians(longitude_))
    z = (N * (1 - e2) + orthometric_height) * np.sin(np.radians(latitude))
    return {"x": x, "y": y, "z": z}

# PROBLEMA INVERSO.
# Calculo de (X,Y,Z) sobre la elipse meridiana. Se divide en 3 (Geodesica, Geocentrica y Parametrica).
# 1). (Phi,Lambda, orthoMetric) = (X,Y,Z) - Geodesica.
def calculate_xyz_from_geodesic(latitude, longitude, ellipsoid):
    N = calculate_N(latitude, longitude, ellipsoid)
    e2 = ellipsoid.e2
    x = (N * np.cos(np.radians(latitude)) * np.cos(np.radians(longitude)))
    y = (N * np.cos(np.radians(latitude)) * np.sin(np.radians(longitude)))
    z = (N * np.sqrt(1 - e2 * np.sin(np.radians(latitude))**2))

# # 2). (Rg,W,Lambda) = (X,Y,Z) - Geocentrica.
# def calculate_xyz_from_geocentric(Rg, w, logitudeGeocentric):
