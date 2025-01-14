def evalPostfix(x):
    """ x is correct postfix notation """
    stack = []
    for arg in x.split():
        if arg == "+": #last+prev
            stack.append( stack.pop() + stack.pop() )
        elif arg == "-": #prev-last
            stack.append( -stack.pop() + stack.pop() )
        elif arg == "*": #prev*last
            stack.append( stack.pop() * stack.pop() )
        elif arg == "/": #prev/last
            second = stack.pop()
            first = stack.pop()
            stack.append( first / second )
        else:
            stack.append(float(arg))
    return stack.pop()          
