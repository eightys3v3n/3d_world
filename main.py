import pyglet,math
from sys import exit
from pyglet.gl import *
from math import floor
from threading import Thread
from time import time
from time import sleep
from noise import pnoise2
import variables,world,player,generator,block


# increase performance
pyglet.options['debug_gl'] = False


class Window(pyglet.window.Window):
  def __init__(self):
    # initialize the window
    super(Window,self).__init__()
    self.set_size(variables.pixel_width,variables.pixel_height)
    self.set_exclusive_mouse(True)
    self.set_vsync(False)

    # allows for a is_this_key_pressed check
    self.keys = pyglet.window.key.KeyStateHandler()
    self.push_handlers(self.keys)

    self.world = world.World()
    self.player = player.PlayerManager()
    self.world_render = world.WorldRender()
    self.generator = generator.Generator(self.world)

    pyglet.clock.set_fps_limit(256)
    pyglet.clock.schedule_interval(self.prevent_sleep,1.0/60.0)
    #pyglet.clock.schedule_interval(self.reload_view,1.0)

    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    glEnable(GL_CULL_FACE)
    glFrontFace(GL_CCW)
    glCullFace(GL_BACK)

    b = block.Block(position=[0,0,0],type="grass")
    self.world_render.load_block(b)
    self.loaded_blocks = 0
    self.slow = False


  def quit(self):
    self.generator.stop()


  # this is just to stop pyglet from sleeping the program
  def prevent_sleep(self,dt):
    pass


  def reload_view(self,dt):
    if self.loaded_blocks > 80000:
      if not self.slow:
        self.slow = True
        self.player.player.position = [0.0,0.0,0.0]
      print("loaded blocks",self.loaded_blocks)
    count = 0
    x,y,x1,y1 = self.player.get_visible()
    for a in range(x,x1):
      for b in range(y,y1):
        if self.world.column_exists(a,b):
          column_pos = self.world.get_column_pos(a,b)
          for pos in column_pos:
            if not self.world.get_loaded(pos[0],pos[1],pos[2]):
              if count <= variables.blocks_per_frame:
                self.world_render.load_block(self.world.get_block(pos[0],pos[1],pos[2]))
                self.world.set_loaded(pos[0],pos[1],pos[2],1)
                self.loaded_blocks += 1
                count += 1
        else:
          self.generator.request_column(a,b)
    if self.loaded_blocks >= 80000:
      print("unloading all loaded blocks to avoid graphics glitch on my pc")
      self.world_render.unload_all()
      self.world.unload_all()
      self.loaded_blocks = 0
    #self.world_render.load_blocks(blocks)


  def check_user_input(self):
    x = 0.0
    y = 0.0
    z = 0.0
    if self.keys[pyglet.window.key.LEFT] or self.keys[pyglet.window.key.A]:
      x += variables.move_speed[0]
    if self.keys[pyglet.window.key.RIGHT] or self.keys[pyglet.window.key.D]:
      x += -variables.move_speed[0]
    if self.keys[pyglet.window.key.UP] or self.keys[pyglet.window.key.W]:
      y += variables.move_speed[1]
    if self.keys[pyglet.window.key.DOWN] or self.keys[pyglet.window.key.S]:
      y += -variables.move_speed[1]
    if self.keys[pyglet.window.key.SPACE]:
      z += -variables.move_speed[2]
    if self.keys[pyglet.window.key.LSHIFT]:
      z += variables.move_speed[2]
    if x or y or z:
      self.player.move(x,y,z)
      current = self.world.get_block_pos_at(self.player.get_position())
      #print("standing on",current)
      if current != self.player.standing_on():
        self.player.set_standing_on(current)


  def player_physics(self):
    if not self.player.flying:
      top_block_height = self.world.get_top_block_height(self.player.standing_on()[0],self.player.standing_on()[1])
      if top_block_height != None:
        if self.player.standing_on()[2] > top_block_height:
          print("falling")
          self.player.move(0,0,-variables.fall_speed[2])


  def on_mouse_scroll(self,x,y,scroll_x,scroll_y):
    if scroll_y < 0:
      variables.move_speed[0] -= 0.5
      variables.move_speed[1] -= 0.5
      variables.move_speed[2] -= 0.5
    elif scroll_y > 0:
      variables.move_speed[0] += 0.5
      variables.move_speed[1] += 0.5
      variables.move_speed[2] += 0.5

    for i in range(len(variables.move_speed)):
      if variables.move_speed[i] <= 0:
        variables.move_speed[i] = 0.01


  def on_mouse_motion(self,x,y,dx,dy):
    self.player.look(-dy*variables.mouse_sensitivity[0],dx*variables.mouse_sensitivity[1])

  def on_key_press(self,symbol,modifiers):
    if symbol == pyglet.window.key.F:
      self.player.flying = not self.player.flying


  def on_draw(self):
    self.reload_view(None)
    self.player_physics()
    self.check_user_input()

    self.clear()
    #glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    self.player.draw_perspective()
    self.world_render.draw()


def main():
  window = Window()
  pyglet.app.run()
  window.quit()


if __name__ == "__main__":
  main()