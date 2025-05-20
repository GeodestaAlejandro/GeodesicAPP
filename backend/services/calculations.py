import numpy as np
from constants import WGS84_A, WGS84_E2

def calculate_N(latitude):
    """ Calcula el radio de curvatura en el primer vertical """
    return WGS84_A / np.sqrt(1 - WGS84_E2 * np.sin(np.radians(latitude))**2)

def calculate_xz_from_latitude(latitude):
    """ Calcula (x, z) en función de latitude """
    N = calculate_N(latitude)
    x = N * np.cos(np.radians(latitude))
    z = N * (1 - WGS84_E2) * np.sin(np.radians(latitude))
    return {"x": x, "z": z}

def calculate_xyz_from_latitude_lambda(latitude, lambda_, h=0):
    """ Calcula (x, y, z) en función de latitude, lambda y altura h """
    N = calculate_N(latitude)
    x = (N + h) * np.cos(np.radians(latitude)) * np.cos(np.radians(lambda_))
    y = (N + h) * np.cos(np.radians(latitude)) * np.sin(np.radians(lambda_))
    z = (N * (1 - WGS84_E2) + h) * np.sin(np.radians(latitude))
    return {"x": x, "y": y, "z": z}