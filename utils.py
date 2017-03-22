class Position:
  def __init__(self, x=None, y=None, z=None):
    self.x = x
    self.y = y
    self.z = z


  def __add__(self, o):
    res = Position(0, 0, 0)
    res.x = self.x + o.x
    res.y = self.y + o.y
    res.z = self.z + o.z
    return res


  def __radd__(self, o):
    self.x += o.x
    self.y += o.y
    self.z += o.z


  def __str__(self):
    return "("+str(self.x)+", "+str(self.y)+", "+str(self.z)+")"


  def __repr__(self):
    return self.__str__()