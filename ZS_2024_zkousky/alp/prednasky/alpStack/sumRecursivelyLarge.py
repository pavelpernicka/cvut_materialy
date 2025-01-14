def sumRecursively(x): #x is list
    if len(x) == 0:
        return 0
    if len(x) == 1:  #basic case
        return x[0]                   
    return sumRecursively(x[:-1]) + x[-1]

a = [i for i in range(1100) ]
print( sumRecursively(a) )
