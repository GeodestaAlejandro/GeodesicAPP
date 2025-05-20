import numpy as np
from constants import WGS84_A, WGS84_E2

def calculate_N(phi):
    """ Calcula el radio de curvatura en el primer vertical """
    return WGS84_A / np.sqrt(1 - WGS84_E2 * np.sin(np.radians(phi))**2)

def calculate_xz_from_phi(phi):
    """ Calcula (x, z) en función de phi """
    N = calculate_N(phi)
    x = N * np.cos(np.radians(phi))
    z = N * (1 - WGS84_E2) * np.sin(np.radians(phi))
    return {"x": x, "z": z}

def calculate_xyz_from_phi_lambda(phi, lambda_, h=0):
    """ Calcula (x, y, z) en función de phi, lambda y altura h """
    N = calculate_N(phi)
    x = (N + h) * np.cos(np.radians(phi)) * np.cos(np.radians(lambda_))
    y = (N + h) * np.cos(np.radians(phi)) * np.sin(np.radians(lambda_))
    z = (N * (1 - WGS84_E2) + h) * np.sin(np.radians(phi))
    return {"x": x, "y": y, "z": z}