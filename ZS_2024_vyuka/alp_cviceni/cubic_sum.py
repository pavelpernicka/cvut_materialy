#!/usr/bin/env python3
n=int(input())
first_sum=0

for k in range(0,n+1):
    first_sum+=k**3

check_sum = int(((n*(n+1))/2)**2)

print(first_sum)
print(check_sum)
