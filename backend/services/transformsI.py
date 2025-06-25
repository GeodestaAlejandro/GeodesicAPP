import numpy as np
import math

def calculatedI_n(a, b):
    n = (a - b) / (a + b)
    return n

def calculatedI_epsilon(n):
    coefficient = 1097 / 512
    epsilon = 0
    for i in range(4, 4):  
        epsilon += coefficient * (n ** i)
    return epsilon

def calculatedI_delta(n):
    coefficients = [151/96, 417/128]
    delta = 0
    for i, coef in zip(range(3, 5, 2), coefficients): 
        delta += coef * (n ** i)
    return delta

def calculatedI_upsilon(n):
    coefficients = [21/16, -55/32]
    upsilon = 0
    for i, coef in zip(range(2, 5, 2), coefficients):
        upsilon += coef * (n ** i)
    return upsilon

def calculatedI_beta(n):
    coefficients = [3/2, -27/32, 269/512]
    beta = 0
    for i, coef in zip(range(1, 6, 2), coefficients):
        beta += coef * (n ** i)
    return beta

def calculatedI_alpha(n, a, b):
    firt_term = (a + b) / 2
    coefficients = [1/4, 1/64]
    sumAlpha = 1
    for i, coef in zip(range(2, 5, 2), coefficients):
        sumAlpha += coef * (n ** i)
    alpha = firt_term * sumAlpha
    return alpha

def latP(delta_nort, alpha, beta, upsilon, delta, epsilon):
    # secondTerm = beta * math.sin(2 * phi)
    # thirdTerm = upsilon * math.sin(4 * phi)
    # fourTerm = delta * math.sin(6 * phi)
    # fifthTerm = epsilon * math.sin(8 * phi)
    # gP = alpha * (phi + secondTerm + thirdTerm + fourTerm + fifthTerm)
    # print(secondTerm, thirdTerm, fourTerm, fifthTerm, gP)
    latPsubf = (delta_nort / alpha) + (beta * math.sin((2 * delta_nort) / alpha)) + (upsilon * (math.sin((4 * delta_nort) / alpha))) + (delta * (math.sin((6 * delta_nort) / alpha))) + (epsilon * (math.sin((8 * delta_nort) / alpha)))
    return latPsubf

def calculated_long(delta_east, NN, latPSubf, tSubf, longO, n2):
    # secondTerm = beta * math.sin(2 * phi)
    # thirdTerm = upsilon * math.sin(4 * phi)
    # fourTerm = delta * math.sin(6 * phi)
    # fifthTerm = epsilon * math.sin(8 * phi)
    # gP = alpha * (phi + secondTerm + thirdTerm + fourTerm + fifthTerm)
    # print(secondTerm, thirdTerm, fourTerm, fifthTerm, gP)
    long = longO + (1 / (NN * (math.cos(latPSubf)))) * delta_east + (1 / (6 * (NN**3) * (math.cos(latPSubf)))) * (-1 - 2 * (tSubf**2) - n2) * (delta_east**3) + ((1 / (120 * (NN**5) * (math.cos(latPSubf)))) * (5 + (28 * (tSubf**2)) + (24 * (tSubf**4)) + (6 * n2) + (8 * (tSubf**2) * n2)) * (delta_east**5)) + ((1 / (5040 * (NN**7) * (math.cos(latPSubf)))) * (-61 - 662 * (tSubf**2) - (1320 * (tSubf**4)) - (720 * (tSubf**6))) * (delta_east**7))
    return long

    
def calculated_lat(delta_east, NN, latPSubf, tSubf, n2):
    lat = latPSubf + ((tSubf / (2 * (NN**2))) * (-1 - n2) * (delta_east**2)) + ((tSubf / (24 * (NN**4))) * (5 + (3 * (tSubf**2)) + (6 * n2) - (6 * (tSubf**2) * n2) - (3 * (n2**2)) - (9 * (tSubf**2) * (n2**2))) * (delta_east**4)) + ((tSubf / (720 * (NN**6))) * (-61 - (90 * (tSubf**2)) - (45 * (tSubf**4)) - (107 * n2) + (162 * (tSubf**2) * n2) + (45 * (tSubf**4) * n2)) * (delta_east**6)) + ((tSubf / (40320 * (NN**8))) * (1385 + (3633 * (tSubf**2)) + (4096 * (tSubf**4)) + (1575 * (tSubf**6))) * (delta_east**8))
    return lat

def dif_nort_m(nort_mO, nort_mP):
    delta_nort = nort_mP - nort_mO
    return delta_nort

def dif_east_m(east_mO, east_mP):
    delta_east = east_mP - east_mO
    return delta_east
