def checkPars(x): 
    left = "({["
    right = ")}]"
    stack = []
    for c in x:
        if c in left:
            stack.append(c)
        else:
            for i in range(len(right)):
                if c == right[i]:
                    #we expect left[i] in stack
                    if len(stack)==0:
                        return False
                    lastLeft = stack.pop()
                    if lastLeft != left[i]:
                        return False
    return len(stack) == 0                        
