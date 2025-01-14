#!/usr/bin/env python3

def faktorial(n):
    fact = n
    for i in range(1, n):
        fact = fact * i
    return fact
    
def is_prime(n):
    for i in range(2, n):
        if n % i == 0:
            return False
    return True

def sexy_prime(count):
    arr = []
    for i in range (0, count):
        if is_prime(i) and is_prime(i+6):
            arr.append((i, i+6))
    return arr

def is_perfect_number(n):
    suma = 0
    for i in range(1, n):
        if(n % i == 0):
            suma += i
    if(suma == n):
        return True
    return False

def perfect_numbers(count):
    arr = []
    for i in range(count):
        if(is_perfect_number(i)):
            arr.append(i)
    return(arr)

#print(perfect_numbers(1000000000))

def caesar(string, shift):
    shift = shift % 26
    meze = ((65, 90), (97, 122)) # A-Z, a-z
    string  = [*string]
    for pozice, znak in enumerate(string):
        for mez in meze:
            old_ord = ord(znak)
            if old_ord >= mez[0] and old_ord <= mez[1]:
                new_ord = old_ord + shift
                if(new_ord > mez[1]):
                    new_ord = new_ord - mez[1] + mez[0]
                elif(new_ord < mez[0]):
                    new_ord = mez[1] - (mez[0] - new_ord) + 1
                string[pozice] = chr(new_ord)
    return("".join(string))
            

retezec = input()
shift = int(input())
print(caesar(retezec, shift))
