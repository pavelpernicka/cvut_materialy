tycky = [ [20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1], [], [] ]

def hanoi(n, ze, do, pom):
    if n>0:
        hanoi(n-1, ze, pom, do)
        t = tycky[ze].pop()
        if (len(tycky[do])==0 or tycky[do][-1]>t):
            tycky[do].append(t)
        else:
            print("ERROR - Chyba davame vesti kruh na mensi")
        print("0=", tycky[0], "1=", tycky[1], "2=", tycky[2])
        hanoi(n-1, pom, do, ze)

print("0=", tycky[0], "1=", tycky[1], "2=", tycky[2])
hanoi(len(tycky[0]), 0, 2, 1)
