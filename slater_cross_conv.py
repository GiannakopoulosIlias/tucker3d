
import numpy as np
import time
from math import pi
from core import *
import timeit


np.random.seed(1)

N = 2**9
M = 2*N-1
print 'N= %s' % N

eps = 1e-7
print 'Accuracy: %s' % eps

a = -5.
b = abs(a)
h = (b-a)/(N-1)


h=(b-a)/(N-1)

newton_const = 1./(4*pi)* h**3

x = np.zeros(N)
for i in xrange(N):
    x[i] = a + i*h

def slater_func((i,j,k)):
    return np.exp(-(x[i]**2 + x[j]**2 + x[k]**2)**0.5)


def newton_func((i,j,k)):
    return newton_const * 1./((x[i])**2 + (x[j])**2 + (x[k])**2)**0.5

print 'WARNING!'
print 'Very slow part (cross approximation of Slater and Newton funs).'
print 'It does not influence cross-conv time performance.'
print 'Will be updated soon.'
print 'In process...'
slater = cross(slater_func, N, eps, delta_add = 1e-5)
newton = cross(newton_func, N, eps, delta_add = 1e-5)
newton = lr_circulant(newton)

start = time.time()
start_conv = time.time()
conv = cross_conv(newton, slater, eps, (4,4,4))
end_conv = time.time()
print 'Cross-conv Time: %s' % (end_conv - start_conv)

