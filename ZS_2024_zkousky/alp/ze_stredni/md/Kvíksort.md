# Kvíksort
```python=
#!/usr/bin/env python3
import time
from random import randint as rand

def rozdel(arr, left, right):
    #zpočátku ji pivot poslední číslo v poli (ovšem není to nutnost)
    i = left #index čísla, které by si vyměňovalo pozici s kontrolovaným číslem
    for j in range(left, right): 
        if arr[j] < arr[right]: #pokud je menší než pivot
            arr[i], arr[j] = arr[j], arr[i] #přehoď kontrolovaný prvek s i
            i += 1
    arr[i], arr[right] = arr[right], arr[i] #přehození pivota s číslem na aktuální pozici (mezi menšími a většími čísly)
    return i #vrať index pivota

#rekurzivní varianta
#klasika
def quicksort(arr, left=0, right=None):
    if right is None:
        right = len(arr) - 1
    
    if left < right:
        #print(arr)
        pivot = rozdel(arr, left, right) #rozdělí pole na větší/menší relativně k pivotu a vrátí jeho index v poli
        quicksort(arr, left, pivot - 1) #reksurzivní volání pro čísla menší než pivot
        quicksort(arr, pivot + 1, right) #rekurzivní volání pro čísla větší než pivot

#rekurzivní varianta
#s polem
"""
def quicksort(arr):
    if len(arr) <= 1: #rozděleno na nejmenší jednotky
        return arr
    else:
        pivot = arr[0] #pivot vlevo
        left = []
        right = []
        for x in arr[1:]: #bez pivot prvku
            if x < pivot: #když je menší vlevo
                left.append(x)
            else: #když je větší vpravo
                right.append(x)
        return quicksort(left) + [pivot] + quicksort(right)
"""

"""
#iterativní varianta
def quicksort(arr):
    zasobnik = [(0, len(arr) - 1)] #prvotní prvek=celá arr
    while len(zasobnik) > 0:
        left, right = zasobnik.pop() #ze zásobníku vystřel poslední náboj a zjisti jeho hodnoty (zásobník napřed nabyde několik prvků podle počtu dělení a potom se jich zbavuje)
        if left < right:
            #pokud je co přehazovat, přehoď prvky před a za pivot a do zásobníku na konec vlož intervaly indexů jednotlivých částí pole
            pivot = rozdel(arr, left, right)
            zasobnik.append((left, pivot - 1))
            zasobnik.append((pivot + 1, right))
"""

count = 100
zadani = [rand(0, 100) for _ in range(count)]
arr = zadani
print(arr)

start = time.time_ns()
quicksort(arr) #quicksort na celém poli
stop = time.time_ns()
print(arr)
print("Duration quicksort: ", stop-start, " ns")```