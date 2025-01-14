#!/usr/bin/env python3
import copy, time
def numAlive(a, r, c):
    neigh = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]
    count = 0
    for n in neigh:
        ro, co = n
        radek = r + ro
        sloupec = c + co
        count += a[radek%len(a)][sloupec%len(a[0])] #preteceni
    return count

def life(a):
    #a is 2d array
    newa = copy.deepcopy(a)
    for r in range(len(a)):
        for c in range(len(a[r])):
            n = numAlive(a,r,c)
            if n == 3:
                newa[r][c] = 1
            elif a[r][c] == 1 and n == 2:
                newa[r][c] = 1
            else:
                newa[r][c] = 0
    return newa

def pm(a):
    for r in range(len(a)):
        for c in range(len(a[r])):
            val = "*"
            if a[r][c] == 0:
                val = "."
            print(val,end=" ")
        print()
    

    
a = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
     [0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
     [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
   ]

while True:
    pm(a)
    print()
    a = life(a)
    time.sleep(0.3)
