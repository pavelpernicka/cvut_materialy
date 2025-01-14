#!/usr/bin/env python3
import sys

class State:
    def __init__(self, tubes, empty_tube_index):
        self.tubes = [tube[:] for tube in tubes]
        self.empty_tube_index = empty_tube_index
        self.action = ""

    def expand(self):
        result = []
        for i in range(len(self.tubes)):
            if not self.tubes[i]:
                continue
            ball = self.tubes[i][-1]
            for j in range(len(self.tubes)):
                if i != j and (not self.tubes[j] or (len(self.tubes[j]) < max_items and self.tubes[j][-1] == ball)):
                    new_tubes = [tube[:] for tube in self.tubes]
                    new_tubes[j].append(new_tubes[i].pop())
                    s = State(new_tubes, i if len(new_tubes[i]) == 0 else self.empty_tube_index)
                    s.action = chr(65 + i) + chr(65 + j)
                    result.append(s)
        return result
    
    def __repr__(self):
        return "".join(self.tubes)

def is_sorted(tubes):
    for i, tube in enumerate(tubes[:-1]):
        if len(tube) != len(tubes[0]) or any(ball != i + 1 for ball in tube):
            return False
    return True

def bfs(start):
    queue = [start]
    visited = {start: None}

    while queue:
        current = queue.pop(0)

        if is_sorted(current.tubes):
            path = []
            while current:
                if current.action:
                    path.append(current.action)
                current = visited[current]
            return path[::-1]

        for neighbor in current.expand():
            if neighbor not in visited:
                visited[neighbor] = current
                queue.append(neighbor)
    return None

if len(sys.argv) > 1:
    input_file = sys.argv[1]
    with open(input_file, "r") as file:
        tubes = [list(map(int, line.strip().split())) for line in file]
        empty_tube_index = len(tubes)
        max_items = max(len(tube) for tube in tubes)
        tubes.append([])
        start_state = State(tubes, empty_tube_index)
        solution = bfs(start_state)
        if solution:
            print(" ".join(solution))
        else:
            print("NOSOLUTION")
else:
    print("No filename entered")

