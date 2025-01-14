m=[[12,-7,3, 26],
   [4 ,5,-6, -5],
   [-7 ,8,9, 21]]

def maximum(m, s):
    maximum_index = s
    max_value = abs(m[s][s])
    for j in range(s+1,len(m)):
        if abs(m[j][s])>max_value:
            max_value = abs(m[j][s])
            maximum_index = j
    return maximum_index

def set(m, s):
    ind = maximum(m, s)
    if ind!=s:
        m[ind],m[s] = m[s],m[ind]

def do_line(m,s):
    set(m,s)
    if m[s][s]!=0:
        div = m[s][s]
        for j in range(len(m[s])):
            m[s][j]=m[s][j]/div
        print("Krok 1")
        for i in m:
            print(*i,sep='\t')

        for r in range(len(m)):
            if r!=s:
                x = m[r][s]
                for j in range(len(m[r])):
                    m[r][j]=m[r][j]-x*m[s][j]
        print("Krok 2")
        for i in m:
            print(*i,sep='\t')
        print()
        return True
    else:
        return False

def Gauss_elim(m):
    for s in range(len(m)):
        if not do_line(m,s):
            return False
    return True

from fractions import Fraction

m_fraction = [list(map(Fraction,v)) for v in m]

Gauss_elim(m)

for i in m:
    print(*i,sep='\t')

print("Zlomky - Fraction")

Gauss_elim(m_fraction)

for i in m_fraction:
    print(*i,sep='\t')
