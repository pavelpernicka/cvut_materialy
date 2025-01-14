#!/usr/bin/env python3
import math
 
words = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000,
    "million": 1000000, "billion": 1000000000, "trillion": 1000000000000,
    "quadrillion": 1000000000000000
}
 
def find_key_by_value(dictionary, value_to_find):
    for key, value in dictionary.items():
        if value == value_to_find:
            return key
    return None
 
def find_value(dictionary, value):
    if value in dictionary:
        return dictionary[value]
    else:
        return None
 
def trojice_to_text(trojice):
    slova = []
    cislo = int(trojice)
    if(cislo >= 100):
        slova.append(find_key_by_value(words, int(trojice[0])))
        slova.append(find_key_by_value(words, 100))
    if(cislo % 100 > 20):
        desitky = cislo % 100 // 10 * 10
        jednotky = cislo % 10
        des = find_key_by_value(words, desitky)
        jedn = find_key_by_value(words, jednotky)
        if des:
            slova.append(des)
        if jedn:
            slova.append(jedn)
    else:
        cis = find_key_by_value(words, cislo % 100)
        if cis:
            slova.append(cis)
    return slova
 
def number_to_text(number):
    slova = []
    for i in range(1, math.ceil(len(number) / 3)+1):
        ind_from = len(number)-(i*3)
        if(ind_from < 0):
            ind_from = 0
        ind_to = len(number)-((i-1)*3)
        trojice = number[ind_from:ind_to]
        #print(trojice)
        rad = 10 ** ((i-1)*3)
        trojice_arr = trojice_to_text(trojice)
        #print(trojice_arr)
        if(rad > 1 and len(trojice_arr) > 0):
            slova.append(find_key_by_value(words, rad))
        slova.extend(reversed(trojice_arr))
    return " ".join(reversed(slova)).strip()
 
def text_to_number(slova):
    if len(slova) == 0:
        return "ERROR"
    slova_arr = slova.split()
    cislo = 0
    temp = 0
    last_large_number = None
    last = None

    for i in range(len(slova_arr)):
        word = slova_arr[i]
        this = find_value(words, word)
        if this is None:
            return "ERROR"
        if this >= 100:
            if last is not None and last >= 10 and last < 20 and (i == len(slova_arr)-1) and this == 100: # wtf asi protichůdné požadavky BRUTE (nineteen hundred fifteen -> 1915, seventeen hundred -> ERROR); chápu to tak, že číslo když má teen násobítko, musí mít nějaká další řády
                return "ERROR"
            if temp == 0:
                return "ERROR"
            if this >= 1000:
                if last_large_number is not None and this >= last_large_number:
                    return "ERROR"
                cislo += temp * this
                temp = 0
                last_large_number = this
                last = None
            else:
                temp *= this
                last = this
        else:
            if last is not None and last < 10 and this >= 10:
                return "ERROR"
            if last is not None and ((last >= 10 and last < 20) or (last < 10 and this < 10)):
                return "ERROR"
            temp += this
            last = this
    
    cislo += temp
    return str(cislo)

 
def main(vstup):
    if vstup.isnumeric():
        out = number_to_text(vstup)
    else:
        out = text_to_number(vstup)
    return out
 
def test_main():
    test_cases = [
        ("315010075284157375", "three hundred fifteen quadrillion ten trillion seventy five billion two hundred eighty four million one hundred fifty seven thousand three hundred seventy five"),
        ("1002003004005006", "one quadrillion two trillion three billion four million five thousand six"),
        ("one hundred twenty", "120"),
        ("two hundred fifty seven thousand three hundred seventy five", "257375"),
        ("1v2", "ERROR"),
        ("one quadrillion million six", "ERROR"),
        ("one million two quadrillion six", "ERROR"),
        ("eleven hundred one twenty", "ERROR"),
        ("1", "one"),
        ("999999999999999999", "nine hundred ninety nine quadrillion nine hundred ninety nine trillion nine hundred ninety nine billion nine hundred ninety nine million nine hundred ninety nine thousand nine hundred ninety nine"),
        ("seventeen five", "ERROR"),
        ("one twenty", "ERROR"),
        ("twenty five ten", "ERROR"),
        ("nineteen hundred fifteen", "1915"),
        ("20000000004", "twenty billion four"),
        ("one two", "ERROR"),
        ("ten four", "ERROR"),
        ("seventeen hundred", "ERROR"),
        ("eleven thousand", "11000"),
        ("100000610000001", "one hundred trillion six hundred ten million one")
    ]
    
    for i, (input_value, expected_output) in enumerate(test_cases):
        actual_output = main(input_value)
        if actual_output == expected_output:
            print(f"Test {i + 1}: Pro vstup '{input_value}' - úspěšně prošel.")
        else:
            print(f"Test {i + 1}: Pro vstup '{input_value}' - selhal. Očekávaný výsledek: '{expected_output}', ale dostal: '{actual_output}'.")
 
#test_main()
print(main(input()))
