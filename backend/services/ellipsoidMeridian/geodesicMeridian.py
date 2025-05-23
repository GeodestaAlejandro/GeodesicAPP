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

# De (X,Z) -> phi: Para φ (geodésica) se necesita iterar, ya que la altura sobre el elipsoide no es conocida directamente.
def xz_to_lat_geod(X, Z, ellipsoid):
    a = ellipsoid['a']
    f = ellipsoid['f']
    e2 = 2 * f - f ** 2
    p = abs(X)
    phi = math.atan2(Z, p)
    prev = 0
    while abs(phi - prev) > 1e-11:
        N = a / math.sqrt(1 - e2 * (math.sin(phi)**2))
        prev = phi
        phi = math.atan2(Z + e2 * N * math.sin(phi), p)
    return math.degrees(phi)