import math  

# De Theta a (X,Z).
def theta_parametric_to_xz(theta_deg, ellipsoid):  

    a = ellipsoid['a']  
    f = ellipsoid['f']  
    b = a * (1 - f)  
    theta_rad = math.radians(theta_deg)  
    X = a * math.cos(theta_rad)  
    Z = b * math.sin(theta_rad)  
    return X, Z

# De (X,Z) a Theta: Para ω (paramétrica) debes conocer la excentricidad e. Las dos funciones son correctas, chat prefiere la segunda.
# def xz_to_theta_parametric(X, Z, ellipsoid):
#     a = ellipsoid['a']
#     f = ellipsoid['f']
#     b = a * (1 - f)
#     theta_rad = math.atan2(a * Z, b * X)
#     theta_deg = math.degrees(theta_rad)
#     return theta_deg

def xz_to_theta_parametric(X, Z, ellipsoid):
    f = ellipsoid['f']
    e2 = 2 * f - f ** 2
    return math.degrees(math.atan2(Z, (1 - e2) * X))