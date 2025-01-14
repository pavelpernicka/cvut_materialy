def print_pole(m):
    for i in m:
        for j in i:
            c='.'
            if j==1:
                c='X'
            elif j==2:
                c='O'
            print(c,end='')
        print()
        
dir_r=[ 1, 1, 1, 0]
dir_s=[-1, 0, 1, 1]
def check_winner(m):
    winner=0
    fail=True
    for r in range(len(m)):
        for s in range(len(m[r])):
            if m[r][s]!=0:
                for dir in range(4):
                    if r+4*dir_r[dir]>=0 and r+4*dir_r[dir]<len(m):
                        if s+4*dir_s[dir]>=0 and s+4*dir_s[dir]<len(m[r]):
                            fail=False
                            for j in range(1,5):
                                if m[r][s]!=m[r+j*dir_r[dir]][s+j*dir_s[dir]]:
                                    fail=True
                                    break
                    if not fail:
                        winner=m[r][s]
                        break
            if not fail:
                break
        if not fail:
            break
    return winner


size=20
pole=[ [0]*size for i in range(size)]

end=False
sign=1
while not end:
    print_pole(pole)
    good_move=False
    while not good_move:
        s=input()
        move = list(map(int,s.split()))
        if move[0]>=0 and move[0]<size and move[1]>=0 and move[1]<size:
            if pole[move[0]][move[1]]==0:
                good_move=True
            else:
                print("Obsazeno")
        else:
            print("Mimo hraci plochu")

    pole[move[0]][move[1]]=sign

    winner = check_winner(pole)
    end = (winner!=0)

    sign=3-sign

print_pole(pole)
if winner==1:
    print("Vyhral krizek")
elif winner==2:
    print("Vyhralo kolecko")

