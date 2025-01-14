#!/usr/bin/env python3
import sys

def letter_list(text):
    ldict = {}
    for letter in text:
        if(letter in ldict):
            ldict[letter] += 1
        else:
            ldict[letter] = 1
    return(ldict)

if(len(sys.argv) > 1):
    filename = sys.argv[1]
    with open(filename, "r") as file:
        prev_dicts = []
        dvojice = []
        for line in file:
            word = line.strip().replace(" ", "")
            letters = letter_list(word)
            prev_dicts.append(letters)
            #print(h)
        for d in range(len(prev_dicts)):
            for h in range(d+1, len(prev_dicts)):
                if(prev_dicts[d] == prev_dicts[h]):
                    dvojice.append((d, h))
        if(len(dvojice)==0):
            print("None")
        else:
            for x, y in dvojice:
                print(f"{x} {y}")
else:
    print("Chcu víc argumentů")
