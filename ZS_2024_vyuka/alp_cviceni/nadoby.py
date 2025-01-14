#!/usr/bin/env python3
VOLUME = [5, 3, 2]

class State:
    def __init__(self, water = [0, 0, 0]):
        self.water = water[:]
        self.action = "INIT"
    
    def expand(self):
        result = []
        # Nx: nalej
        for x in range(3):
            if(self.water[x] < VOLUME[x]):
                s = State(self.water)
                s.water[x] = VOLUME[x]
                s.action = f"N{x}"
                result.append(s)
        # Vx: vylej
        for x in range(3):
            if(self.water[x] > 0):
                s = State(self.water)
                s.water[x] = 0
                s.action = f"V{x}"
                result.append(s)
        # xPy: přelej z x do y
        """
        for x in range(3):
            for y in range(3):
                if(x != y):
                    if(self.water[x] > 0 and self.water[y] < VOLUME[y]):
                        s = State(self.water)
                        s.water[y] = s.water[y] + s.water[x]
                        s.water[x] = s.water[y] % VOLUME[y]
                        if(s.water[y] > VOLUME[y]):
                            s.water[y] = VOLUME[y]
                        s.action = f"{x}P{y}"
                        result.append(s)
        """
        for y in range(3):
            for x in range(3):
                if x != y:
                    s = State(self.water)
                    if VOLUME[y] > s.water[y] and s.water[x] != 0:
                        deficit = VOLUME[y] - s.water[y]
                        if s.water[x] >= deficit:
                            s.water[y] = VOLUME[y]
                            s.water[x] = s.water[x] - deficit
                        if s.water[x] < deficit:
                            s.water[y] = s.water[y] + s.water[x]
                            s.water[x] = 0
 
                        s.action = str(x) + "P" + str(y)
                        result.append(s)
        return result
    
    def __repr__(self):
        return f"State(action={self.action}, water={self.water})"

def bfs(start, stop):
    queue = [start]
    isKnown = {}
    isKnown[str(start.water)] = None # lifehack
    while len(queue) > 0:
        actual = queue.pop(0)
        new_states = actual.expand() # bude list of State instances
        if(actual.water == stop.water):
            path = []
            while actual != None:
                path.append(actual.action + str(actual.water))
                actual = isKnown [str(actual.water)]
            return path # Cesta nalezena
        for state in new_states:
            if not str(state.water) in isKnown:
                isKnown[str(state.water)] = actual
                queue.append(state)

def test():
    s = State([3, 0, 2])
    end = State([0, 2, 1])
    print(bfs(s, end))

test()
