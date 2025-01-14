#!/usr/bin/env python3
a=int(input())
b=int(input())

if a > b:
    increment = -1
else:
    increment = 1

suma = 0
for i in range(a, b+increment, increment):
    mocnina = i**4
    if mocnina >= 100 and mocnina <= 100000:
        suma += i**4

print(suma)
