import pyglet
from queue import Queue, Full
from threading import Thread
from pyglet.gl import *
from math import ceil
import variables
import itertools


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
  def __init__(self, world, generator):
    self.world = world
    self.generator = generator
    self.batch = pyglet.graphics.Batch()
    self.render_queue = Queue(variables.render.max_render_requests)
    self.requested_recently = []
    self.pending_queue = Queue(variables.render.max_pending)
    self.prepared = Queue(variables.render.max_rendered_requests)
    self.thread = WorldRenderThread(self.world, self.generator, self.render_queue, self.pending_queue, self.prepared)
    self.thread.start()
    pyglet.clock.schedule_interval(self.clear_requested_recently, 1/2)

  def clear_requested_recently(self, dt):
    self.requested_recently = []

  def request_columns(self, x1, y1, x2, y2):
    for x, y in itertools.product(range(x1, x2), range(y1, y2)):
      if (x, y) not in self.requested_recently:
        try:
          self.render_queue.put((x, y), timeout=0.5)
          self.requested_recently.append((x, y))
        except Full as e:
          print(e)
          print("Render queue was full, so didn't add requested columns.")
          return
    try:
      self.render_queue.put(self.pending_queue.get(), timeout=0.5)
      self.pending_queue.task_done()
    except Full as e: pass


  def stop(self):
    self.thread.running = False
    self.render_queue.put((None, None))
    self.thread.join()


  def unload_all(self):
    self.batch = pyglet.graphics.Batch()


  def draw(self):
    drawn = 0

    while not self.prepared.empty() and drawn < variables.render.max_drawn_per_frame:
      self.batch.add_indexed(*self.prepared.get())
      self.prepared.task_done()
      drawn += 1

    if variables.render.debug.print_render_requests:
      print("Number of render requests: {}".format(self.render_queue.qsize()))
    if variables.render.debug.print_pending_requests:
      print("Number of pending requests: {}".format(self.pending_queue.qsize()))
    if variables.render.debug.print_rendered_requests:
      print("Number of rendered requests: {}".format(self.prepared.qsize()))

    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    self.batch.draw()


class WorldRenderThread(Thread):
  def __init__(self, world, generator, render_queue, pending_queue, prepared):
    Thread.__init__(self)
    self.world = world
    self.generator = generator
    self.queue = render_queue
    self.prepared = prepared
    self.pending = pending_queue
    self.running = True


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



  def load_block(self, block, position):
    a = self.block_vertices(block, position)
    c = self.block_colour(block)

    self.prepared.put((24, GL_QUADS, None,
      [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
      ("v3f",a),
      ("c3B",c)))


  def load_blocks(self, blocks, positions):
    if len(position) != len(blocks):
      raise Exception("need exactly a position for every block")

    for i in range(0, len(position)):
      self.load_block(blocks[i], position[i])


  def run(self):
    while self.running:

      if self.queue.empty() and not self.pending.empty():
        try:
          self.queue.put(self.pending.get(), timeout=0.1)
        except Full as e:
          print(e)
        self.pending.task_done()

      pos = self.queue.get()
      if pos is (None, None):
        return

      if not self.world.column_exists(*pos):
        self.generator.request_column(*pos)
        #print("Requested column, trying again next time.")
        try:
          self.pending.put(pos, timeout=0.5)
        except Full as e:
          print(e)
          print("Queue was full so I couldn't schedule this column to be checked later.")
      else:
        column_blocks = self.world.get_column_pos(*pos)
        for column_block in column_blocks:
          if not self.world.get_loaded(*column_block):
            self.load_block(self.world.get_block(*column_block), column_block)

            self.world.set_loaded(*column_block, 1)
      self.queue.task_done()

