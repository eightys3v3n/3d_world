class Block():
  def __init__(self,position=[None,None,None],type=None):
    self.position = position
    self.type = type
    self.loaded = False


  def __str__(self):
    return str(self.position[0])+","+str(self.position[1])+","+str(self.position[2])+",type:"+str(self.type)