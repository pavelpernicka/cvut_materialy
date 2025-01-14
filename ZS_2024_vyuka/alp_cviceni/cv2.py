#!/usr/bin/env python3
L = 0
y = float(input())
R = y

if(y < 0):
    print("Ty pablbe")
    exit()

def fun(x):
    return (x**2)-y

cnt = 0
while True:
    cnt += 1
    M = (L+R)/2
    fL = fun(L)
    fR = fun(R)
    fM = fun(M)
    if (fM > 0 and fR > 0) or (fM <= 0 and fR <= 0):
        R = M
    if (fL <= 0 and fM <= 0) or (fL > 0 and fM > 0):
        L = M
    if(R-L < 1e-10):
        break
print(M)
print("pocet kroku: ", cnt)
"""
y = 700
x = 1
step = 1
while step > 1e-6:
    while (x+step)**2 < y:
        x += step
    step /= 10
print(x)
"""
