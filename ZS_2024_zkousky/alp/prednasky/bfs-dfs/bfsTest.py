from bfs import bfs

G = {}
G[0] = [1,2,5]
G[1] = [0,2]
G[2] = [0,1,3]
G[3] = [2]

path = bfs(G, 0, 3)
print(path)

path = bfs(G, 5,0)
print(path)
