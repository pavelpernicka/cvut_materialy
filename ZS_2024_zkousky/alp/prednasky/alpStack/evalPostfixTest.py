from evalPostfix import *

print( evalPostfix("3 4 *") )
print( evalPostfix("3 4 +") )
print( evalPostfix("3 4 -") )
print( evalPostfix("3 4 /") )
print( evalPostfix("3 4 * 2 - ")) #3*4 -2
print( evalPostfix("3 4 2 - * ")) #3*(4-2)
