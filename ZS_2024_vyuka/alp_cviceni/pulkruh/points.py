#!/usr/bin/env python3
import math
def find_teziste(body):
    sum_x = 0
    sum_y = 0
    for bod in body:
        sum_x += bod[0]
        sum_y += bod[1]
    x = sum_x/len(body)
    y = sum_y/len(body)
    return(x, y)

def find_nearest(body, teziste):
    shortest = math.inf
    found = (0, 0)
    ind_found = 0
    for index, i in enumerate(body):
        distance = math.sqrt(((teziste[0]-i[0])**2) + ((teziste[1]-i[1])**2))
        #print(i, distance)
        if(distance < shortest):
            shortest = distance
            found = i
            ind_found = index
    return ind_found, found

def find_kruznice(body, pocet_bodu):
    for index, bod in enumerate(body):
        distance = math.sqrt(((bod[0])**2) + ((bod[1])**2))
        cnt = 0
        for x in body:
            x_distance = math.sqrt(((x[0])**2) + ((x[1])**2))
            if(x_distance <= distance):
                cnt += 1
        if(cnt == pocet_bodu):
            #print("found: ", bod, cnt)
            return index, bod
    return(0, body[0])

vstup = input()
souradnice = list(map(float, vstup.strip().split()))
body = []
if(len(souradnice) > 1):
    for i in range(0, len(souradnice)-1, 2):
        body.append((souradnice[i], souradnice[i+1]))
    #print(body)
    teziste_coords = find_teziste(body)
    #print("teziste: ", teziste_coords)
    index_nearest, nearest = find_nearest(body, teziste_coords)
    #print("nearest: ", nearest)
    pocet_bodu = int(len(body)/2)
    index_kruznice, bod_na_kruznici = find_kruznice(body, pocet_bodu)
    #print("bod na kruznici: ", bod_na_kruznici)
    print(index_nearest, index_kruznice)
else:
    print("Not enough coords entered")

