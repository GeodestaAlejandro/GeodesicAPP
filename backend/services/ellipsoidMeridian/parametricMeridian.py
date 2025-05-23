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

# De (X,Z) a Theta.
def xz_to_theta_parametric(X, Z, ellipsoid):  
    a = ellipsoid['a']  
    f = ellipsoid['f']  
    b = a * (1 - f)  
    theta_rad = math.atan2(a * Z, b * X)  
    theta_deg = math.degrees(theta_rad)  
    return theta_deg  