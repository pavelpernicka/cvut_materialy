class State:
    def __init__(self,x, parent = None):
        self.x = x[:]
        self.parent = parent
        self.action = None
 
    def expand(self):
        result = []
        #Vx
        for i in range( len(self.x) ):
            if self.x[i] > 0:
                child = State(self.x, self)
                child.x[i] = 0
                child.action = "V" + str(i)
                result.append( child )
        #Nx:
        for i in range(len(self.x)):
            if self.x[i] < V[i]:
                child = State(self.x, self)
                child.x[i] = V[i]
                child.action = "N" + str(i)
                result.append( child )
        #iPj
        for i in range(len(self.x)):
            for j in range(len(self.x)):
                if i == j:
                    continue
                else:
                    if self.x[j] != V[j]:
                        child = State(self.x, self)
                        vol = self.x[i] + self.x[j]
                        over = vol - V[j]
                        if over < 0:
                            over = 0
                        child.x[j] = vol - over
                        child.x[i] = over
                        child.action = str(i) + "P" + str(j)
                        result.append(child)
        return result
 
V = [5,3,4,2]
 
start = State([5,0,0,1])
res = start.expand()
 
Q = [ start ]
known = {}
known[ str(start.x) ] = 1
 
while len(Q) > 0:
    actual = Q.pop()
 
    if actual.x == [4,0]:
        print("HURA")
        path = []
        while actual != None:
            path.append( actual.action )
            actual = actual.parent
        p2 = path[::-1]
        print(p2[1:])
        break
 
    for child in actual.expand():
        if not str(child.x) in known:
            Q.insert(0, child)
            known[ str(child.x) ] = True
