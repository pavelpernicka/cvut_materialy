#!/usr/bin/env python3
x = list(map(float, input().strip().split()))
y = list(map(float, input().strip().split()))

def fce(x, y):
    #return ((1/2)*(x**2)*((1-y)**2))+((x-2)**3)-(2**y)+x
    return ((0.5*(x*x))*((1-y)*(1-y)))+((x-2)**3)-(2*y)+x

if(len(x) == len(y)):
    max_index = 0
    max_value = None
    lt_zero = 0
    min_index = 0
    min_value = None
    for i in range(len(x)):
        
        result = fce(x[i], y[i])
        result1 = result * (x[i]+2) * (y[i]-2)
        #print(x[i], y[i], result, result1)
        if(result < 0):
            lt_zero += 1
        if(max_value == None or result > max_value):
            max_value = result
            max_index = i
        if(min_value == None or result1 < min_value):
            min_value = result1
            min_index = i
    print(max_index, lt_zero, min_index)
else:
    print("ERROR")
