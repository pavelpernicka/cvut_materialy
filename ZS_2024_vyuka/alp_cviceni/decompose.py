#!/usr/bin/env python3

def generate_permutations(numbers):
    if len(numbers) == 0:
        return []
    if len(numbers) == 1:
        return [numbers]
    permutations = []
    stack = [([], numbers)]
    while stack:
        path, remaining = stack.pop()
        if not remaining:
            permutations.append(path)
        else:
            for i in range(len(remaining)):
                stack.append((path + [remaining[i]], remaining[:i] + remaining[i + 1:]))
    return permutations

def find(index, current_expression, current_value, last_value, used_numbers, target, numbers): # rekurzivně budu postupne sestavovat výraz a testovat
    # ukonceni rekurze
    if current_value == target and used_numbers:
        return True, current_expression

    # nelze poskladat jen z daných čísel
    if index == len(numbers):
        return False, ""
    num = numbers[index]
    
    # reskoc aktualni
    found, expression = find(index + 1, current_expression, current_value, last_value, used_numbers, target, numbers)
    if found:
        return True, expression
        
    # hledam moznosti ve dvou větvích pro každou operaci
    # rekurzivne pro +
    found, expression = find(
        index + 1,
        current_expression + " + " + str(num),
        current_value + num,
        num,
        True,
        target,
        numbers
    )
    if found: # chci testovat hned
        return True, expression

    # pro mínus -
    found, expression = find(
        index + 1,
        current_expression + " * " + str(num),
        current_value - last_value + last_value * num,
        last_value * num,
        True,
        target,
        numbers
    )
    if found:
        return True, expression
    return False, ""

def get_decomposition(numbers, target):
    result = find(0, "", 0, 0, False, target, numbers)[1] or "NEEXISTUJE" # start rekurze
    if(result.startswith(" + ")):
        result = result[3:]
    return result


numbers = list(map(int, input().strip().split()))
vysledek = int(input().strip())
result = get_decomposition(numbers, vysledek)
print(result)
