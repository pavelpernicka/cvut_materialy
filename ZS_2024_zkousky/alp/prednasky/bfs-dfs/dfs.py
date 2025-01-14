from gnode import *

def dfs(graph, start, goal):
    #graph as list of neighbors
    #start,goal are names of vertices
    stack = [ GNode(start) ]
    known = {}
    known[ start ] = True
    while len(queue) > 0:
        node = stack.pop()
        if node.name == goal:
            path = traverse(node)
            return path[::-1]
        if not node.name in graph:
            continue
        for neighbor in graph[node.name]:
            if not neighbor in known:
                known[neighbor] = True
                stack.append(GNode(neighbor, node) )
    return []

                
        
            
