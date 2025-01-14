#!/usr/bin/env python3
import os, sys
import numpy as np
np.set_printoptions(threshold=sys.maxsize)

def gaussian_elimination(A, b):
    n = len(A)
    # vytvořím rozšířenou matice (A | b)
    for i in range(n):
        A[i].append(b[i])
    
    # eliminace
    for i in range(n):
        # najdu řádek s největším koeficientem 
        max_row = i
        max_value = abs(A[i][i])
        for r in range(i+1, n):
            current_value = abs(A[r][i])
            if current_value > max_value:
                max_row = r
                max_value = current_value

        # prohození řádků
        A[i], A[max_row] = A[max_row], A[i]
        
        # chcu dásáhnout toho, aby prvek na diagonále by 1 a bylo možné dostat řešení
        diagonala = A[i][i]
        if diagonala == 0:
            raise ValueError("Matice je singulární a nelze ji vyřešit.")
        for j in range(i, n + 1):
            A[i][j] /= diagonala
        
        # eleminace řádků potom
        for k in range(n):
            if k == i:
                continue
            nas = A[k][i]
            for j in range(i, n + 1):
                A[k][j] -= nas * A[i][j]
    
    # získání výsledku pomocí substituce
    x = [row[-1] for row in A]
    return x

def equation_solver(A, b):
    A = np.array(A, dtype=float) # kvůli řádkovým úprávám použiju floaty
    b = np.array(b, dtype=float)
    
    At = A.T # vytvoření transponované matice k A
    AtA = At @ A # maticové násobení
    Atb = At @ b
    
    AtA += 1e-12 * np.eye(AtA.shape[0], dtype=float) # posunu hodnoty o jednotkovou matici * malé číslo kvůli numerické stabilitě

    AtA_list = AtA.tolist()
    Atb_list = Atb.tolist()
    solution = gaussian_elimination(AtA_list, Atb_list)
    return solution

def solve_minesweeper(grid):
    rows, cols = len(grid), len(grid[0])
    variables = rows * cols
    A = []
    b = []

    def index(r, c):
        return r * cols + c

    # převedu na problém řešení soustavy rovnic protože muluji lineární algebru
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 0:
                continue
            
            neighbors = [
                (r + dr, c + dc)
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if (0 <= r + dr < rows) and (0 <= c + dc < cols)
            ]
            equation = [0] * variables
            for nr, nc in neighbors:
                equation[index(nr, nc)] = 1
            A.append(equation)
            b.append(grid[r][c])

    #solution = equation_solver(A, b)
    solution1 = np.linalg.lstsq(A, b, rcond=None)[0]
    #print(np.array(solution).reshape(rows, cols))
    #solution = np.array(solution).reshape(rows, cols)
    solution1 = np.array(solution1).reshape(rows, cols)
    #print(solution)
    #print(solution1)
    return solution1 > 0.5

if len(sys.argv) < 2:
    print("Enter file path")
    sys.exit(1)

filename = sys.argv[1]
mines = []

with open(filename, 'r') as file:
    for line in file:
        mines.append(list(map(int, line.strip().split())))

#print("Mines array:", mines)
solution = solve_minesweeper(mines)

for row in solution:
    row_output = ""
    for is_mine in row:
        if is_mine:
            row_output += "X"
        else:
            row_output += "."
    print(row_output)
