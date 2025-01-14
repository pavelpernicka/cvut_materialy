#!/usr/bin/env python3
import sys

def largest_submatrix(matrix):
    rows = len(matrix)
    cols = len(matrix[0])
    max_area = 0
    top_left = (0, 0)
    bottom_right = (0, 0)

    # matice na histogram (doc)
    hist = [[0] * cols for _ in range(rows)]
    #print(hist)

    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] < 0:
                if i > 0:
                    hist[i][j] = hist[i - 1][j] + 1
                else:
                    hist[i][j] = 1                
            else:
                hist[i][j] = 0

    # projdu histogram po řádcích, najdu největší souvislou část
    for i in range(rows):
        stack = []
        left = [-1] * cols
        right = [cols] * cols

        # leva strana
        for j in range(cols):
            while stack and hist[i][stack[-1]] >= hist[i][j]:
                stack.pop()
            left[j] = stack[-1] if stack else -1
            stack.append(j)

        # prava strana
        stack = [] # musim resetnout
        for j in range(cols - 1, -1, -1): # pozpatku
            while stack and hist[i][stack[-1]] >= hist[i][j]:
                stack.pop()
            right[j] = stack[-1] if stack else cols
            stack.append(j)

        for j in range(cols): # aktualizace max. matice
            height = hist[i][j]
            width = right[j] - left[j] - 1
            area = height * width
            if area > max_area:
                max_area = area
                top_left = (i - height + 1, left[j] + 1)
                bottom_right = (i, right[j] - 1)

    return top_left, bottom_right

if len(sys.argv) != 2:
    print("No file argument given")
else:
    file_path = sys.argv[1]
    with open(file_path, 'r') as file:
        matrix = [list(map(int, line.split())) for line in file]
    (r1, s1), (r2, s2) = largest_submatrix(matrix)
    print(r1, s1)
    print(r2, s2)
