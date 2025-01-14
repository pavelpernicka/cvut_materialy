#!/usr/bin/env python3
def decypher_column(n, m, s, numbers, letters):
    x = []
    for i in range(n):
        row = numbers[i * m:(i + 1) * m]
        x.append(row)

    y = []
    for i in range(n):
        row = letters[i * m:(i + 1) * m]
        y.append(row)

    message = []
    for col in range(m):
        row = 0
        while row < n:
            subcolumn = []
            for i in range(row, min(row + s, n)):
                subcolumn.append(x[i][col])
            
            max_value = max(subcolumn)
            max_index = subcolumn.index(max_value) + row
            
            message.append(y[max_index][col])
            row += s
    return ''.join(message)


n, m, s = map(int, input().strip().split())
numbers = list(map(int, input().strip().split()))
letters = input().strip()
result = decypher_column(n, m, s, numbers, letters)
print(result)

