from alpQueue import ALP_Queue

q = ALP_Queue()
q.put("first")
q.put("2")
q.put(3.0)

while not q.isEmpty():
    print(q.get())
