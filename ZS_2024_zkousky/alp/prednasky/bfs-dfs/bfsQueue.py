from gnode import *
from queue import Queue

def bfs(graph, start, goal):
    #graph as list of neighbors
    #start,goal are names of vertices
    q = Queue()
    q.put( GNode(start) )
    known = {}
    known[ start ] = True
    while not q.empty():
        node = q.get()
        if node.name == goal:
            path = traverse(node)
            return path[::-1]
        if not node.name in graph:
            continue
        for neighbor in graph[node.name]:
            if not neighbor in known:
                known[neighbor] = True
                q.put( GNode(neighbor, node) )
    return []

                
        
            
