#!/usr/bin/env python3
import sys

if(len(sys.argv) > 2):
    file_path = sys.argv[1]
    postfix = sys.argv[2]
    #print(f"Otevírám soubor: {file_path}")
    #print(f"Hledám postfix: {postfix}")
    count = 0
    min_word = None
    with open(file_path, "r") as file:
        for line in file:
            text = line.strip()
            found_postfix = text[-len(postfix):]
            #print(found_postfix)
            if(found_postfix==postfix):
                count += 1
                #print(text)
                if(min_word==None or len(text) < len(min_word)):
                    min_word = text
                    #print(f"update: {min_word}, {len(min_word)}")
        print(count)
        print(min_word)
else:
    print("Nedostatek argumentů")
