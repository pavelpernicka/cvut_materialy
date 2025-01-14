# Jan Kybic 
from stack import Stack
from evalPostfix import *
from infixToPostfix import *

def evalInfix(s):
  return evalPostfix(infixToPostfix(s))

print(evalInfix("32+4"))
print(evalInfix("3*4-2"))
print(evalInfix("3*(4-2)"))
print(evalInfix("(62-32)*5/9"))
