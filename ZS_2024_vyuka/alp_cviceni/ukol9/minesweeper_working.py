#!/usr/bin/env python3
import os
import sys
import numpy as np
from fractions import Fraction

np.set_printoptions(threshold=sys.maxsize)

def gaussian_elimination(A, b):
    n = len(A)
    # Create the augmented matrix (A | b)
    for i in range(n):
        A[i].append(b[i])
    
    # Perform Gaussian elimination
    for i in range(n):
        # Find the row with the largest pivot
        max_row = i
        max_value = abs(A[i][i])
        for r in range(i + 1, n):
            current_value = abs(A[r][i])
            if current_value > max_value:
                max_row = r
                max_value = current_value
        
        # Swap rows
        A[i], A[max_row] = A[max_row], A[i]
        
        # Normalize the pivot row
        pivot = A[i][i]
        if pivot == 0:
            raise ValueError("Matrix is singular and cannot be solved.")
        for j in range(i, n + 1):
            A[i][j] /= pivot
        
        # Eliminate other rows
        for k in range(n):
            if k == i:
                continue
            factor = A[k][i]
            for j in range(i, n + 1):
                A[k][j] -= factor * A[i][j]
    
    # Extract solution
    x = [row[-1] for row in A]
    return x

def equation_solver(A, b):
    # Convert A and b to Fraction for high precision
    A = np.array(A, dtype=object)
    b = np.array(b, dtype=object)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            A[i, j] = Fraction(A[i, j])
    for i in range(len(b)):
        b[i] = Fraction(b[i])
    
    # Transpose and multiply matrices with high precision
    At = A.T
    AtA = np.dot(At, A)
    Atb = np.dot(At, b)
    
    # Add small identity matrix for numerical stability
    for i in range(AtA.shape[0]):
        AtA[i, i] += Fraction(1, 10**12)
    
    # Convert back to list for Gaussian elimination
    AtA_list = AtA.tolist()
    Atb_list = Atb.tolist()
    
    # Solve using Gaussian elimination
    solution = gaussian_elimination(AtA_list, Atb_list)
    
    # Convert back to floats
    return [float(x) for x in solution]

def solve_minesweeper(grid):
    rows, cols = len(grid), len(grid[0])
    variables = rows * cols
    A = []
    b = []

    def index(r, c):
        return r * cols + c

    # Convert Minesweeper grid to system of equations
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

    # Solve the linear system
    solution = equation_solver(A, b)
    solution = np.array(solution).reshape(rows, cols)
    return solution > 0.5

if len(sys.argv) < 2:
    print("Enter file path")
    sys.exit(1)

filename = sys.argv[1]
mines = []

with open(filename, 'r') as file:
    for line in file:
        mines.append(list(map(int, line.strip().split())))

solution = solve_minesweeper(mines)

for row in solution:
    row_output = ""
    for is_mine in row:
        if is_mine:
            row_output += "X"
        else:
            row_output += "."
    print(row_output)

