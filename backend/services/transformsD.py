import numpy as np
import math

def calculated_n(a, b):
    n = (a - b) / (a + b)
    return n

def calculated_epsilon(n):
    coefficient = 315 / 512
    epsilon = 0
    for i in range(4, 6):  
        epsilon += coefficient * (n ** i)
    return epsilon

def calculated_delta(n):
    coefficients = [-35/48, 105/256]
    delta = 0
    for i, coef in zip(range(3, 8, 2), coefficients): 
        delta += coef * (n ** i)
    return delta

def calculated_upsilon(n):
    coefficients = [15/16, -15/32, 15/64]
    upsilon = 0
    for i, coef in zip(range(2, 6, 2), coefficients):
        upsilon += coef * (n ** i)
    return upsilon

def calculated_beta(n):
    coefficients = [-3/2, 9/16, -3/32, 9/64]
    beta = 0
    for i, coef in zip(range(1, 7, 2), coefficients):
        beta += coef * (n ** i)
    return beta

def calculated_alpha(n, a, b):
    firt_term = (a + b) / 2
    coefficients = [1/4, 1/64, 1/1024]
    sumAlpha = 1
    for i, coef in zip(range(2, 6, 2), coefficients):
        sumAlpha += coef * (n ** i)
    alpha = firt_term * sumAlpha
    return alpha

def arcMeridianP(alpha, beta, upsilon, delta, epsilon, phi: any):
    # secondTerm = beta * math.sin(2 * phi)
    # thirdTerm = upsilon * math.sin(4 * phi)
    # fourTerm = delta * math.sin(6 * phi)
    # fifthTerm = epsilon * math.sin(8 * phi)
    # gP = alpha * (phi + secondTerm + thirdTerm + fourTerm + fifthTerm)
    # print(secondTerm, thirdTerm, fourTerm, fifthTerm, gP)
    gP = alpha * (phi + beta * math.sin(2 * phi) + upsilon * math.sin(4 * phi) + delta * math.sin(6 * phi) + epsilon * math.sin(8 * phi))
    return gP

def dif_long(longP, longO):
    l = longP - longO
    return l

def calculated_N(arcGp, arcGO, NN, l, t, n2, phi):  
    # Primer término  
    term1 = arcGp - arcGO  
    # Segundo término  
    term2 = (t / 2) * NN * (math.cos(phi)**2)  
    # Tercer término  
    term3 = (l / 24) * NN * (math.cos(phi)**4) * (5 - t**2 + (9 * n2) + (4 * n2**2)) * (l**4)
    # Cuarto término  
    term4 = (l / 720) * NN * (math.cos(phi)**6) * (61 - (58 * t**2) + t**4 + (270 * n2) - (330 * t**2 * n2)) * (l**6)
    # Quinto término  
    term5 = (l / 40320) * NN * (math.cos(phi)**8) * (1385 - (3111 * t**2) + (543 * t**4) - t**6) * (l**8)
    constant = 1000000  
    N = term1 + term2 + term3 + term4 + term5 + constant  
    return N
def calculated_E(NN, l, t, n2, phi):
    # Primer término
    term1 = NN * l * math.cos(phi)
    # Segundo término
    term2 = (l / 6) * NN * (math.cos(phi)**3) * (1 - t**2 + n2) * (l**3)
    # Tercer término
    term3 = (l / 120) * NN * (math.cos(phi)**5) * (5 - (18 * t**2) + t**4 + (14 * n2) - (58 * t**2 * n2)) * (l**5)
    # Cuarto término  
    term4 = (l / 5040) * NN * (math.cos(phi)**7) * (61 - (479 * t**2) + (179 * t**4) - t**6) + (l**7)
    constant = 1000000
    # Sumando todos los términos  
    E = term1 + term2 + term3 + term4 + constant
  
    return E