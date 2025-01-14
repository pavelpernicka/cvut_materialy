sez=[1,2,[3,4,5],[[6,7],8],[9,[10]]]

def nested_sum(x):
    soucet=0
    for i in x:
        if type(i) == type([]):
            s = nested_sum(i)
            soucet+=s
        else:
            soucet+=i
    print("Soucet",x,"je",soucet)
    return soucet

print(nested_sum(sez))
