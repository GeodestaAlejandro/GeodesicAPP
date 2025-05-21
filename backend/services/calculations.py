import numpy as np

# Calcula el radio de curvatura en el primer vertical.
def calculate_N(latitude, ellipsoid):
    e2 = ellipsoid.e2
    a = ellipsoid.a
    return a / np.sqrt(1 - e2 * np.sin(np.radians(latitude))**2)

def calculate_Rg(logitudeGeocentric, ellipsoid):
    e2 = ellipsoid.e2

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

# 2). (Rg,W,Lambda) = (X,Y,Z) - Geocentrica.
def calculate_xyz_from_geocentric(Rg, w, logitudeGeocentric):
