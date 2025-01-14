#Jan Kybic
from stack import Stack
from evalPostfix import *

def infixToPostfix(s):
  """ converts an infix to postfix expression """
  result=""  # output string
  op=Stack() # operator stack
  i=0        # index to 's'
  while i<len(s):
    if s[i] in "0123456789":
      while i<len(s) and s[i] in  "0123456789":
        result+=s[i]
        i+=1
      result+=" "
      continue   
    if s[i]=='(':
      op.push(s[i])
    elif s[i]==')':
      top=op.pop()
      while top!='(': 
        result+=top+" "
        top=op.pop()    
    else: # s[i] is +,-,*,/
      while not op.is_empty() and not higher_prec(s[i],op.peek()):
        result+=op.pop()+" "
      op.push(s[i])
    i+=1           
  while not op.is_empty():
     result+=op.pop()+" "
  return result

def higher_prec(a,b):
  """ does operator 'a' have a higher precedence than the stack top element 'b' """
  return ((a in "*/") and (b in "+-")) or (b=="(")
