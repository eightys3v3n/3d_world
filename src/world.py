import pyglet
from pyglet.gl import *
from math import ceil
import variables


class World:
  def __init__(self):
    self.world = {}


  def block_exists(self,x,y,z):
    if x not in self.world:
      self.world[x] = {}
      return False
    if y not in self.world[x]:
      self.world[x][y] = {}
      return False
    if z not in self.world[x][y]:
      return False
    return True


  def column_exists(self,x,y):
    if x not in self.world:
      return False
    if y not in self.world[x]:
      return False
    for z in self.world[x][y]:
      if not self.block_exists(x,y,z):
        return False
    return True


  def set_block(self,x,y,z,block):
    if x not in self.world:
      self.world[x] = {}
    if y not in self.world[x]:
      self.world[x][y] = {}

    self.world[x][y][z] = block
    return False


  def set_loaded(self,x,y,z,v):
    if x not in self.world:
      return None
    if y not in self.world[x]:
      return None

    self.world[x][y][z].loaded = v


  def get_loaded(self,x,y,z):
    if x not in self.world:
      return None
    if y not in self.world[x]:
      return None

    return self.world[x][y][z].loaded


  def unload_all(self):
    for x in self.world:
      for y in self.world[x]:
        for z in self.world[x][y]:
          self.set_loaded(x,y,z,0)


  def get_block(self,x,y,z):
    if not self.block_exists(x,y,z):
      return None
    return self.world[x][y][z]


  def get_block_pos_at(self,position):
    x = -position[0]/variables.cube_size/2
    y = -position[1]/variables.cube_size/2
    z = position[2]/variables.cube_size/2
    x = round(x)
    y = round(y)
    z = round(z)
    return [x,y,z]


  def get_top_block_height(self,x,y):
    if not self.column_exists(x,y):
      return None
    top = None
    for z in self.world[x][y]:
      if top == None:
        top = z
      elif z >= top:
        top = z
    return top


  def get_column(self,x,y):
    blocks = []
    if x not in self.world:
      return None
    if y not in self.world[x]:
      return None
    for z in self.world[x][y]:
      blocks.append(self.world[x][y][z])
    return blocks


  def get_column_pos(self,x,y):
    blocks = []
    if x not in self.world:
      return None
    if y not in self.world[x]:
      return None
    for z in self.world[x][y]:
      blocks.append([x,y,z])
    return blocks


class WorldRender():
  def __init__(self):
    self.batch = pyglet.graphics.Batch()


  def block_vertices(self, block, position):
    n = variables.cube_size
    x = position[0]*n*2
    y = position[2]*n*2
    z = position[1]*n*2
    return (
    # top
    x-n,y+n,z+n,
    x+n,y+n,z+n,
    x+n,y+n,z-n,
    x-n,y+n,z-n,
    # front
    x-n,y-n,z+n,
    x+n,y-n,z+n,
    x+n,y+n,z+n,
    x-n,y+n,z+n,
    # bottom
    x-n,y-n,z-n,
    x+n,y-n,z-n,
    x+n,y-n,z+n,
    x-n,y-n,z+n,
    # left
    x-n,y+n,z+n,
    x-n,y+n,z-n,
    x-n,y-n,z-n,
    x-n,y-n,z+n,
    # back
    x-n,y+n,z-n,
    x+n,y+n,z-n,
    x+n,y-n,z-n,
    x-n,y-n,z-n,
    # right
    x+n,y-n,z+n,
    x+n,y-n,z-n,
    x+n,y+n,z-n,
    x+n,y+n,z+n)


  def block_colour(self,block):
    return variables.block_colour[variables.block[block.type]]


  def unload_all(self):
    self.batch = pyglet.graphics.Batch()


  def load_block(self, block, position):
    a = self.block_vertices(block, position)
    c = self.block_colour(block)

    self.batch.add_indexed(24,GL_QUADS,None,
      [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
      ("v3f",a),
      ("c3B",c))


  def load_blocks(self, blocks, positions):
    if len(position) != len(blocks):
      raise Exception("need exactly a position for every block")

    for i in range(0, len(position)):
      self.load_block(blocks[i], position[i])


  def draw(self):
    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    self.batch.draw()
