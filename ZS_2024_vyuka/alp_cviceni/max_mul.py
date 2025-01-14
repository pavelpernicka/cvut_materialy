#!/usr/bin/env python3
nums = list(map(int, input().split()))
nums.append(1)

index, delka, suma = 0, 0, 0
prev_index, prev_delka, prev_suma = 0, 0, 0

    
for i, cislo in enumerate(nums):
    if cislo % 3 == 0:
        if delka == 0:
            index = i
        delka += 1
        suma += cislo
    else:
        if delka > 0:
            #print(f"konec posloupnosti: {index} {delka} {suma}")
            if (prev_delka < delka) or (prev_delka == delka and prev_suma < suma):
                prev_delka, prev_suma, prev_index = delka, suma, index
            index, delka, suma = 0, 0, 0
#print(f"nejlepsi: {prev_index} {prev_delka} {prev_suma}")
print(f"{prev_index} {prev_delka} {prev_suma}")
