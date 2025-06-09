import numpy as np
import math

# Calcula el radio de curvatura en el primer vertical.
def calculate_N(latitude, ellipsoid):
    a = ellipsoid['a']
    f = ellipsoid['f']
    e2 = 2*f - f**2
    return a / np.sqrt(1 - e2 * np.sin(np.radians(latitude))**2)

def calculateRg(latitude, ellipsoid):
    
    a = ellipsoid['a']
    f = ellipsoid['f']
    e2 = 2*f - f**2
    denominator = a * np.sqrt(1 - e2)
    numerator = np.sqrt(1 - e2 * np.cos(latitude)**2)
    Rg = denominator / numerator
    print("Rg", Rg)
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

def latitudeLongitude_to_XYZ(latitude, longitude, orthometricHeight, a, b, e2, ellipsoid, coordinate_type):

# Aqui nombre al primer verticcal N, a Radio Geocentrico Rg, o a "a" de la mimsa forma para ser mas dinamico, aqui estos 3
#  se llaman Rho (p)
    if coordinate_type == "Geodesic":
        # rho aqui es N
        rho_XY = calculate_N(latitude, ellipsoid)
        Z = (rho_XY * (1 - e2) + orthometricHeight) * np.sin(latitude)
    elif coordinate_type == "Geocentric":
        # rho aqui es Rg
        rho_XY = calculateRg(latitude, ellipsoid)
        Z = (rho_XY + orthometricHeight) * np.sin(latitude)
    elif coordinate_type == "Parametric":
        # rho aqui es a o b, depende si es para XY o Z respectivamente.
        rho_XY = a
        rho_Z = b
        Z = rho_Z * np.sin(latitude)
    else:
        raise ValueError("coordinate_type debe ser 'Geodesic' o 'Geocentric' o 'Parametric '")
    X = (rho_XY + orthometricHeight) * np.cos(latitude) * np.cos(longitude)
    Y = (rho_XY + orthometricHeight) * np.cos(latitude) * np.sin(longitude)
    return X, Y, Z
    
    
    