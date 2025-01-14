f=open("mat.txt")
pole=[]
for l in f:
    pole.append(list(map(int,l.split())))

for i in pole:
    print(*i, sep='\t')

import copy
pole2=copy.deepcopy(pole)

pole[0][0]=-10
print("pole2")
for r in pole2:
    print(*r)
print("pole")
for r in pole:
    print(*r)
