def sumRecursivelyWithStack(x): #x is list
    result = 0
    stack = [ x ]
    while len(stack) > 0:
        a = stack.pop() #a is array
        if len(a) == 0:
            break
        result += a.pop() #a.pop = last item of a
        stack.append(a)
    return result

a = [1,2]
print( sumRecursivelyWithStack(a) )

a = [i for i in range(1100) ]
print( sumRecursivelyWithStack(a) )
