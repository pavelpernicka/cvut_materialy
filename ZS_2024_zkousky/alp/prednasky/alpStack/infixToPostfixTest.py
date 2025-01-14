from stack import Stack
from evalPostfix import *
from infixToPostfix import *

print(infixToPostfix("32+4"))
print(infixToPostfix("3*4-2"))
print(infixToPostfix("3*(4-2)"))
print(infixToPostfix("(62-32)*5/9"))
