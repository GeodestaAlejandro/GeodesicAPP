import math

# De phi -> (X,Z)
def lat_geod_to_xz(latitudeGeodesic_deg, ellipsoid):
    a = ellipsoid['a']
    f = ellipsoid['f']
    e2 = 2 * f - f ** 2
    phi = math.radians(latitudeGeodesic_deg)
    operation = math.sqrt(1 - e2 * (math.sin(phi)) ** 2)
    print(operation)
    N = a / math.sqrt(1 - e2 * (math.sin(phi)) ** 2)
    X = N * math.cos(phi)
    Z = N * (1 - e2) * math.sin(phi)
    return X, Z, N

# De (X,Z) -> phi
def xz_to_lat_geod(X, Z, ellipsoid):  
    a = ellipsoid['a']  
    f = ellipsoid['f']  
    b = a * (1 - f)  
    ratio = (a / b) * (Z / X)  
    phi_rad = math.atan(ratio)  
    latitudeGeodesic_deg = math.degrees(phi_rad)  
    return latitudeGeodesic_deg