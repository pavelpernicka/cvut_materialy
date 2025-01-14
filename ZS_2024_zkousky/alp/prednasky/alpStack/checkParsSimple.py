def checkParsSimple(x):
    stack = []
    for c in x:
        if c=="(":
            stack.append(c)
        elif c == ")":
            if len(stack) == 0:
                return False
            leftPar = stack.pop()
            if leftPar != "(":
                return False
    return len(stack) == 0

print( checkParsSimple(" a*(a+b) " ) )
print( checkParsSimple(" (1+(a+b))+(2-3) " ) )
print( checkParsSimple(" 1*(a+b " ) )
print( checkParsSimple(" )a+b( " ) )
