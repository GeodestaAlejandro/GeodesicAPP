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

def decimal_a_dms(decimal, tipo='lat'):  
    # Extraer grados, minutos, segundos absolutos  
    grados = int(decimal)  
    minutos_dec = abs((decimal - grados) * 60)  
    minutos = int(minutos_dec)  
    segundos = (minutos_dec - minutos) * 60  
  
    # Determinar sufijo según signo y tipo de coordenada  
    if tipo == 'lat':  
        sufijo = 'N' if decimal >= 0 else 'S'  
    else:  
        sufijo = 'E' if decimal >= 0 else 'W'  
  
    # Formato con símbolos grados, minutos, segundos y sufijo  
    return f"{abs(grados)}°{abs(minutos)}'{abs(segundos):.4f}\" {sufijo}"

def geocentricGeodesic_from_parametric(a, b, e2, f, latitude):
    # Dada beta (latitud paramétrica), calcula phi (latitud geodésica)
    def geodesic_from_parametric(f, latitude):
        # EJEMPLO DE COMPROBACION DE ECUACIÓN
        # ab = np.divide(a, b)
        # print("a / b =", ab)  
        # print("latitudeeeeee",latitude)
        # tan_lat_param = math.tan(latitude)  
        # print("tan(latitude) =", tan_lat_param)  
        # mult = ab * (tan_lat_param)  
        # print("(a / b) * tan(latitude) =", mult)  
        # phi = math.atan(mult)
        # print("atan((a / b) * tan(latitude)) =", phi, "radianes")
        # print("Resultado en grados =", math.degrees(phi), "°")
        # return phi
        # return math.atan((a / b) * math.tan(latitude))
        return math.atan(math.tan(latitude) / (1 - f))
    # Dada beta (latitud paramétrica), calcula psi (latitud geocéntrica)
    def geocentric_from_parametric(a, b, e2, latitude):
            return math.atan((1 - e2) * (a / b) * math.tan(latitude))
        
    phi = geodesic_from_parametric(f, latitude)
    psi = geocentric_from_parametric(a, b, e2, latitude)
    return phi, psi

def parametricGeocentric_from_geodesic(e2, f, latitude):
    #  Dada phi (latitud geodésica), calcula beta (latitud paramétrica)
    def parametric_from_geodesic(f, latitude):
        # return math.atan((b / a) * math.tan(latitude))
        return math.atan((1 - f) * math.tan(latitude))  
    # Dada phi (latitud geodésica), calcula psi (latitud geocéntrica)
    def geocentric_from_geodesic(e2, latitude):
        return math.atan((1 - e2) * math.tan(latitude))
    beta = parametric_from_geodesic(f, latitude)
    print("beta",beta)
    psi = geocentric_from_geodesic(e2, latitude)
    return beta, psi

def parametricGeodesic_from_geocentric(a, b, e2, latitude):
    # Dada psi (latitud geocéntrica), calcula phi (latitud geodésica)
    def geodesic_from_geocentric(e2, latitude):
        return math.atan(math.tan(latitude) / (1 - e2))
    # Dada psi (latitud geocéntrica), calcula beta (latitud paramétrica)
    def parametric_from_geocentric(a, b, e2, latitude):
        # al parecer da igual la que se use, siempre dejo las que se asemejen mas al libro del profesor.
        # return math.atan((b / a) * (math.tan(latitude) / (1 - e2)))
        return math.atan((a / b) * (1 - e2) * math.tan(latitude))
    phi = geodesic_from_geocentric(e2, latitude)
    beta = parametric_from_geocentric(a, b, e2, latitude)
    return phi, beta

# def XYZ_to_latitudeLongitude(X, Y, Z, a, b, e2, ellipsoid):
    
#     e22 = e2 / (1 - e2)
    
#     V = np.atan((Z * a) / (np.sqrt(X**2 + Y**2) * b))
    
#     phi = np.atan((Z + (e22 * b * (np.sin(V))**3)) / (np.sqrt(X**2 + Y**2) - (e2 * a * (np.cos(V))**3)))
    
#     N = calculate_N(phi, ellipsoid)
    
#     lammbda = np.atan( Y / X )

#     orthometricHeight = (np.sqrt(X**2 + Y**2) / np.cos(phi)) - N
    
#     return phi, lammbda, orthometricHeight

def XYZ_to_latitudeLongitude(X, Y, Z, e2, ellipsoid):
    
     # Magnitud de la proyección en el plano XY  
    vp = np.sqrt(X**2 + Y**2)
    # Longitud geodésica  
    lon = np.arctan2(Y, X)
    print("lon", lon)
    # Latitud inicial (método de Bowring)
    secondTerm = e2 / (1 - e2)
    phi = np.atan((Z / vp) * (1 + secondTerm))
    # Ahora se calcula an base a estos datos ya calculados con phiSub0.
    N_sub1 = calculate_N(phi, ellipsoid)
    eps = 1e-12
    phi_prev = 0
    diff = abs(phi - phi_prev)
    h = 0
  
    while diff > eps:
        h = vp / np.cos(phi) - N_sub1
        phi_prev = phi
        product = e2 * N_sub1 * np.sin(phi_prev)
        phi = np.arctan((Z + product) / vp)
        diff = abs(phi - phi_prev)

    print("phi", math.degrees(phi))
    lat = "lat"
    lot = "lon"
    phi = decimal_a_dms(math.degrees(phi), lat)
    lon = decimal_a_dms(math.degrees(lon), lot)
    return phi, lon, h

# revisada
def latitudeLongitude_to_XYZ(latitude, longitude, orthometricHeight, a, b, e2, ellipsoid, coordinate_type):
    # Aqui nombre al primer verticcal N, a Radio Geocentrico Rg, o a "a" de la mimsa forma para ser mas dinamico, aqui estos 3
    #  se llaman Rho (p)
    if coordinate_type == "Geodesic":
        # rho aqui es N
        rho_XY = calculate_N(latitude, ellipsoid)
        Z = (rho_XY * (1 - e2) + orthometricHeight) * np.sin(latitude)
        Za = (rho_XY * (1 - e2) + orthometricHeight) * np.sin(latitude)
        print("diferencia entre ztas", Z, Za)
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

    
    