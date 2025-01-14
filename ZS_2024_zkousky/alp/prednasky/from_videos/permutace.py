def printPermutation(prefix, items) :
    if len(items) == 0:
        print (prefix, end = " ") # print on one line
    for i in range (len( items )) :
        printPermutation(prefix + items [ i ] , items [: i ]+ items [ i +1:])

y = ["a", "b", "c", "d"]
printPermutation(" ", y)
