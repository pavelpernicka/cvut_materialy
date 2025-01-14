#!/usr/bin/env python3
import sys
import re

def check(slova, rezezce):
    max_word = None
    used_max = 0
    found_list = []
    for slovo in slova:
        #print("---")
        #print("processing slovo:", slovo)
        covered_map = []
        for pismeno in slovo:
            covered_map.append(False)
        for retezec in retezce:
            p = re.compile(retezec)
            occ = p.finditer(slovo)
            #pos = slovo.find(retezec)
            #for x in occ:
            #print("  found:", x.span())
                #print(slovo, retezec, slovo.find(retezec))
            for x in occ:
                #print(f"  found {retezec}:", x.span())
                pos = x.span()[0]
                if(retezec not in found_list):    
                    found_list.append(retezec)
                for i in range(x.span()[0], x.span()[1]):
                    covered_map[i] = True
                used = 0
                for x in covered_map:
                    if x:
                        used += 1
                #print(covered_map)
                if(used > used_max):
                    used_max = used
                    max_word = slovo
                #print("Used letters:", used)
                #print("Max word:", max_word)
                #print("Used retezce:", len(found_list))
    return max_word, len(found_list)


if(len(sys.argv) > 2):
    slova_filename = sys.argv[1]
    retezce_filename = sys.argv[2]
    with open(slova_filename, "r") as slova_f:
        slova = []
        for slovo in slova_f:
            slovo = slovo.strip()
            slova.append(slovo)
        with open(retezce_filename, "r") as retezce_f:
            retezce = []
            for retezec in retezce_f:
                retezce.append(retezec.strip())
            max_word, used_retezce = check(slova, retezce)
            print(max_word)
            print(used_retezce)
else:
    print("Nedostatek argumentů")
