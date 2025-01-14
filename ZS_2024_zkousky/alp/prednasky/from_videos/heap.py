# Implementace haldy
#
# http://interactivepython.org/runestone/static/pythonds/Trees/BinaryHeapImplementation.html
# Jan Kybic, 2016
 
class MinHeap:
  """ binarni halda __init__ konstruktor """
  def __init__(self):
     self.heap = [] # indexujeme od nuly
 
  def bubble_up(self,i):
    """ probubla prvek i nahoru, zajisti splneni podminek haldy """
    while i>0:
      j=(i-1)//2 # index rodice
      if self.heap[i] >= self.heap[j]:
        break
      self.heap[j],self.heap[i]=self.heap[i],self.heap[j]
      i = j
 
  def insert(self,k):
    """ vloz prvek do haldy """    
    self.heap+=[k]
    self.bubble_up(len(self.heap)-1)
 
  def peek(self):
    """ vrati nejmensi prvek """
    return self.heap[0]
 
  def size(self):
    """ vrati pocet prvku v halde """
    return len(self.heap)
 
  def is_empty(self):
    """ je halda prazdna? """
    return self.size()==0 
 
  def bubble_down(self,i):
     """ probublej prvek dolu """
     n=self.size()
     while 2*i+1 < n:
        j=2*i+1 # zjisti index leveho potomka
        if j+1 < n and self.heap[j] > self.heap[j+1]:
          j+=1
        if self.heap[i]>self.heap[j]:
          self.heap[i],self.heap[j]=self.heap[j],self.heap[i]
        i=j
 
  def pop(self):
    """ odebere nejmensi prvek a uprav haldu """
    element=self.heap[0]
    self.heap[0]=self.heap[-1]
    self.heap.pop() # smaz posledni prvek
    self.bubble_down(0)
    return element
