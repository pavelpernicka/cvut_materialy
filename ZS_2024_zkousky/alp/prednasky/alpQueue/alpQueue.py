class ALP_Queue:
    def __init__(self):
        self.items = []

    def put(self, item):
        self.items.insert(0, item)

    def get(self):
        return self.items.pop()

    def isEmpty(self):
        return self.items == []

    def size(self):
        return len(self.items)

