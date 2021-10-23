import numpy as np
"""   FUNCTION LIST:
def white_noise(rho, sr, n, mu=0):
def cr(A, NSD, T, N, T2=0):

"""

"""
parameters: 
rhp - spectral noise density unit/SQRT(Hz)
sr  - sample rate
n   - no of points
mu  - mean value, optional

returns:
n points of noise with spectral noise density of rho
"""


def white_noise(rho, sr, n, mu=0):
    sigma = rho * np.sqrt(sr/2)
    noise = np.random.normal(mu, sigma, n)
    return noise


"""
A - amplitude
NSD - Noise Spectral Density
T - Period of acquisition
T2 - Relaxation rate
N - Number of samples
ret - sigma, sigma2, C
return: STD, C
"""


def cr(A, NSD, T, N, T2=0):
    if T2 == 0:
        C = 1
    else:
        beta = T / (N * T2)  # \delta t/T*_2
        z = np.exp(-beta)
        C = (N ** 3) / 12
        C *= (1 - z ** 2) ** 3
        C *= 1 - z ** (2 * N)
        C *= 1 / ((z ** 2) * ((1 - z ** (2 * N)) ** 2) - (N ** 2) * (z ** (2 * N)) * ((1 - z ** 2) ** 2))

    sigma2 = (12 * C) / (4 * (np.pi ** 2) * ((A / NSD) ** 2) * (T ** 3))
    # print("C= ",C)

    return np.sqrt(sigma2), C