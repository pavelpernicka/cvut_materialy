from checkPars import *

print(checkPars(" (a+b) ") )
print(checkPars(" (a+b)*[a-b]+{} ") )
print(checkPars(" ( [ ) ] ") )
print(checkPars(" ()[ ") )
print(checkPars(" { a*[1-2]+(3/4)  } ") )
