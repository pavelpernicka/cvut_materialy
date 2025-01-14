#!/usr/bin/env python3
import sys

def find_path(autobusy, start, stop):
    path = []
    startpoints = [] # linka, index
    needed_lines = []
    autobusy1 = {}
    for linka, zastavky in autobusy:
        #print(f"{linka}: {zastavky}")
        autobusy1[linka] = []
        for i, zastavka in enumerate(zastavky):
            autobusy1[linka].append(zastavka)
            if(zastavka == start):
                startpoints.append((linka, i))
            if(zastavka == stop):
                if(linka not in needed_lines):
                    needed_lines.append(linka)
    #print(startpoints)
    if(len(startpoints) == 0):
        return([])
    #print(needed_lines)
    cost = 10000000000000000000000
    for start_line, start_index in startpoints:
        if(len(needed_lines) == 1): # no prestup
            for direction in [1, -1]:
                found = False
                tmp_path = []
                position = start_index
                tmp_cost = 0
                #print("dir:", direction)
                while not found:
                    tmp_path.append(autobusy1[start_line][position])
                    #print("checking:", autobusy1[start_line][position])
                    if(autobusy1[start_line][position] == stop):
                        #print("found station:", tmp_path, cost)
                        found = True
                    else:
                        position = position + direction
                        tmp_cost += 1
                        if(position >= len(autobusy1[start_line])):
                            break
                        if(position < 0):
                            break
                if(found and (tmp_cost < cost)):
                    cost = tmp_cost
                    path.append((start_line, tmp_path))
                    #print(path)
        else: # prestup needed
            return []
    return path


file_linky = sys.argv[1]
with open(file_linky, "r") as file:
    autobusy = []
    for radek in file:
        linka_list = radek.strip().split()
        linka_number = int(linka_list[0])
        linka_stations = linka_list[1:]
        path = []
        for i in range(1, len(linka_stations)):
            path.append((linka_stations[i-1], linka_stations[i]))
        #path.append((linka_stations[len(linka_stations)-1], linka_stations[0]))
        autobusy.append((linka_number, linka_stations))
    
    start = sys.argv[2]
    stop = sys.argv[3]
    found = find_path(autobusy, start, stop)
    if(len(found) > 0):
        for linka, zastavky in found:
            print(f"{linka}", end="")
            x = 0
            for zastavka in zastavky:
                x += 1
                print("", zastavka, end="")
            print()

    else:
        print("NOSOLUTION")

        



