#!/usr/bin/env python3

def calc_poly(arr, x):
    final = 0
    for pozice, clen in enumerate(arr):
        final += clen*(x**pozice)
    return final
    
def sum_poly(arr1, arr2):
    result = [0] * max(len(arr1), len(arr2))
    for i in range(len(arr1)):
        result[i] += arr1[i]
    for i in range(len(arr2)):
        result[i] += arr2[i]
    return result
    
def multiply_poly(arr1, arr2):
    result = [0] * (len(arr1) + len(arr2) - 1)
    for i in range(len(arr1)):
        for j in range(len(arr2)):
            result[i+j] += arr1[i] * arr2[j]
    return result
    
def print_matrix(matrix):
    for radek in matrix:
        for prvek in radek:
            print(prvek, end=" ")
        print("")

def str2matrix(string, radky, sloupce):
    strarr = list(map(int, string.split()))
    arr = []
    tmpmat = []
    for i in strarr:
        if(len(tmpmat) <= sloupce):
            tmpmat.append(i)
        if(len(tmpmat) == sloupce):
            arr.append(tmpmat)
            tmpmat = []
    return arr
    
string = "3 4 5 6 7 8"
print(str2matrix(string, 3, 2))
