#!/usr/bin/env python3
def get_matrix(numbers, n, m):
    matrix = []
    for i in range(n):
        row = numbers[i * m:(i + 1) * m]
        matrix.append(row)
    return matrix

def main(n, m, s, numbers, message):
    #numbers = list(map(int, numbers.strip().split()))
    x = get_matrix(numbers, n, m)
    y = get_matrix(message, n, m)

    #print(x)
    #print(y)

    offset = 0
    neigh = [(0,0), (0,1), (0,-1), (1,0), (-1,0)] 
    res = ""
    for offset in range(0, m, s):
        for start in range(0, n, s):
            #print("checking submatrix: ", start, start+s) 
            max_value = None
            max_character = None
            maxindex = 0

            for a in range(start, start+s):
                for b in range(offset, offset+s):
                    #print("checking number: ", a, b)
                    hodnota = 0
                    minx = start
                    maxx = start + s -1
                    miny = offset
                    maxy = offset + s - 1
                    #print("bbox:", minx, maxx, miny, maxy)
                    for offx, offy in neigh:
                        coordy = b+offy
                        coordx = a+offx
                        #print()
                        if(coordx > maxx):
                            coordx = minx
                        if(coordx < minx):
                            coordx = maxx
                        if(coordy > maxy):
                            coordy = miny
                        if(coordy < miny):
                            coordy = maxy
                        #print("   counting", coordx, coordy, str(x[coordx][coordy]))
                        hodnota += x[coordx][coordy]
                    #print("total:", hodnota)
                    if max_value == None or hodnota > max_value:
                        max_value = hodnota
                        max_character = y[a][b]
                        maxindex = (a,b)
            res += max_character
            #print("found:", max_character, "at:", maxindex)
        #print("konec radku")
    print(res)

n, m, s = map(int, input().strip().split())
numbers = list(map(int, input().strip().split()))
message = input()

main(n, m, s, numbers, message)
#main(6, 6, 3, "2 1 6 3 6 2 4 3 8 1 4 6 7 9 10 18 12 3 8 1 4 1 16 2 3 2 5 10 11 10 9 5 10 5 16 1", "abcdefghijklmnkpdrstuvwxabcd2fohijkl")

