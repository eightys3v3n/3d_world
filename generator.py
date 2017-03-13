from queue import Queue
from threading import Thread
from noise import snoise2
from block import Block
from world import World
import variables


def map(v,mn,mx,nmn,nmx):
  r = v - mn
  r /= mx - mn
  r *= nmx - nmn
  r += nmn
  return r


class Generator():
  def __init__(self,world):
    self.queue = Queue(variables.max_generation_requests)
    self.world = world
    self.thread = GeneratorThread(self.world,self.queue)
    self.thread.start()


  def request_column(self,x,y):
    self.queue.put((x,y))


  def request_columns(self,x,y,x1,y1):
    for a in range(x,x1):
      for b in range(y,y1):
        self.request_column(a,b)


  def stop(self):
    self.thread.running = False
    self.queue.put((None,None))
    self.thread.join()


class GeneratorThread(Thread):
  def __init__(self,world,queue):
    Thread.__init__(self)
    self.world = world
    self.queue = queue
    self.queue.maxsize = variables.max_generation_requests
    self.running = True


  def generate_height(self,x,y):
    noise = snoise2(x/variables.x_scale,
                    y/variables.y_scale,
                    octaves=5,
                    persistence=0.5)*20
    #noise = map(noise,0,10,variables.z_min,variables.z_max)
    block_height = round(noise)
    return block_height


  def generate_type(self,x,y,z):
    block = Block(position=[x,y,z],type="grass")
    self.world.set_block(x,y,z,block)


  def run(self):
    while self.running:
      x,y = self.queue.get()
      if x != None and y != None:
        h = self.generate_height(x,y)
        for z in range(variables.z_min,h):
          self.generate_type(x,y,z)
        self.queue.task_done()