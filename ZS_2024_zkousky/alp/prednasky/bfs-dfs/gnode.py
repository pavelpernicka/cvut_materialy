class GNode:
    def __init__(self, name, parent = None):
        self.name = name
        self.parent = parent

def traverse(node):
    result = []
    while node != None:
        result.append(node.name)
        node = node.parent
    return result    
