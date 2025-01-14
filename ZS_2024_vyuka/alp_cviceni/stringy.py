#!/usr/bin/env python3
def find(string, substring):
    for i in range(len(string)):
        char = string[i]
        found = False
        for j in range(len(substring)):
            substr_char = substring[j]
            new_index = i + j
            if(new_index < len(string)):
                char = string[new_index]
            else:
                break
            #print(f"Comparing {char} vs. {substr_char}")
            if(char == substr_char):
                #print("found same character")
                found = True
            else:
                found = False
                break
    if found:
        return i
    else:
        return False
        
"""
def find1(text, word):
    if len(text) == 0 or len(word) == 0:
        return False
    for r in range(len(text)-len(word)+1):
"""

def replace(text, word, new):
    start_index = find(text, word)
    if(start_index):
        text_pred = text[:start_index]
        text_za = text[(start_index + len(word)):]
        return text_pred + new + text_za
    else:
        return False

def maximum(arr):
    if len(arr) == 0:
        return None
    nej = arr[0]
    for x in range(1, len(arr)):
        if(arr[x] > nej):
            nej = arr[x]
    return nej
        
def second_max(arr):
    first_max = maximum(arr)
    if(first_max == None):
        return None
    cmp = arr[0]
    for x in range(0, len(arr)):
        if(arr[x] != first_max):
            cmp = arr[x]
            
    return cmp
x = [7, 7, 7, 0, 9]
resp = second_max(x)
print(f"Maximum: {resp}")
