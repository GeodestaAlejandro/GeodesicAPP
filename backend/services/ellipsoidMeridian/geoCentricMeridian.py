import math  

# De W -> (X,Z)
def lat_geocentric_to_xz(W_deg, ellipsoid):
    a = ellipsoid['a']
    f = ellipsoid['f']
    b = a * (1 - f)
    W_rad = math.radians(W_deg)
    X = a * math.cos(W_rad)
    Z = b * math.sin(W_rad)
    Rg = math.sqrt(X**2 + Z**2)
    return X, Z, Rg

# De (X,Z) -> W:  Para W (geocéntrica) basta con X y Z.
def xz_lat_geocentric(X, Z):
    return math.degrees(math.atan2(Z, X))