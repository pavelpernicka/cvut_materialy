#!/usr/bin/env python3
import math
sum = 0
for n in range(1, 50000):
	sum += ((-1)**n)/((2*n)-1)
print(sum)
check = -(math.pi/4)
print(check)
