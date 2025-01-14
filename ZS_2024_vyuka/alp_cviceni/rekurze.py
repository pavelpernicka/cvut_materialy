#!/usr/bin/env python3

def faktorial(n):
    if(n == 0 or n== 1):
        return 1
    return n*faktorial(n-1)

def binom(n, k):
    if(k==1 or (n==k)):
        return 1
    if(k==1 or (n==k-1)):
        return n
    return binom(n-1, k) + binom(n-1, k-1)

def fibonacci(n):
    if(n==0 or n==1):
        return 1
    return fibonacci(n-1) + fibonacci(n-2)

MEM = {}
def fibonacci2(n):
    if(n in MEM):
        return MEM[n]
    if(n==0 or n==1):
        MEM[n] = 1
        return MEM[n]
    val = fibonacci2(n-1) + fibonacci2(n-2)
    MEM[n] = val
    return val

def flatten(x):
    res = []
    for value in x:
        if(type(value) == list):
            res += flatten(value)
        else:
            res.append(value)
    return res

def rotate(x):
    xu = []
    orig_pocet_radku = len(x[0])
    orig_pocet_sloupcu = len(x)
    for i in reversed(range(orig_pocet_radku)):
        mat = []
        for j in range(orig_pocet_sloupcu):
            mat.append(x[j][i])
        xu.append(mat)
    return xu


"""
for i in range(10):
    print(i, faktorial(i))
"""
"""
for i in range(70):
    print(i, fibonacci2(i))
"""

#print(flatten([1, [1, 2], [[1, [2]], [1, 2]]]))

matrix = [["A", "B", "C", "D"], ["E", "F", "G", "H"]]
print(matrix)
print(rotate(matrix))
