from checkParsSimple import *

print( checkParsSimple(" a*(a+b) " ) )
print( checkParsSimple(" (1+(a+b))+(2-3) " ) )
print( checkParsSimple(" 1*(a+b " ) )
print( checkParsSimple(" )a+b( " ) )
