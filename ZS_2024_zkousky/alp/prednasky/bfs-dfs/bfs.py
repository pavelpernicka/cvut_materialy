from gnode import *

def bfs(graph, start, goal):
    #graph as list of neighbors
    #start,goal are names of vertices
    queue = [ GNode(start) ]
    known = {}
    known[ start ] = True
    while len(queue) > 0:
        node = queue.pop(0)
        if node.name == goal:
            path = traverse(node)
            return path[::-1]
        if not node.name in graph:
            continue
        for neighbor in graph[node.name]:
            if not neighbor in known:
                known[neighbor] = True
                queue.append(GNode(neighbor, node) )
    return []

                
        
            
