import variables
import world
import player
import generator
import block
from pyglet.gl import *
from math import floor
from threading import Thread
from time import time
from time import sleep
from noise import pnoise2


class Game(pyglet.window.Window):
  """
  a class that contains the window, world, world rendering, player, event handling, generation
  """
  def __init__(self):
    super(Game,self).__init__()                                     # initialize the window
    self.set_size(variables.pixel_width, variables.pixel_height)      # set the window size
    self.set_exclusive_mouse(False)                                    # lock the cursor to this window
    self.set_vsync(False)                                             # turn off vsync so the framerate isn't limited at your refresh rate
    self.keys = pyglet.window.key.KeyStateHandler()                   # allows for a is_this_key_pressed check
    self.push_handlers(self.keys)                                     # tells pyglet that it should keep track of when keys are pressed
    self.world = world.World()                                        # the world
    self.player = player.PlayerManager()                              # the player and/or perspective
    self.world_render = world.WorldRender()                           # draws the world
    self.generator = generator.Generator(self.world)                  # generates new chunks

    pyglet.clock.set_fps_limit(256)                                   # set the maximum framerate
    pyglet.clock.schedule_interval(self.prevent_sleep, 1.0/60.0)      # this prevents the application from 'smartly' sleeping when idle
    #pyglet.clock.schedule_interval(self.reload_view,1.0)

    glEnable(GL_DEPTH_TEST)   # gpu can tell when stuff is infront or behind
    glDepthFunc(GL_LESS)      # anything closer should be drawn
    glEnable(GL_CULL_FACE)    # don't draw faces that are behind something
    glFrontFace(GL_CCW)       # used to determine the 'front' of a 2d shape
    glCullFace(GL_BACK)       # remove the backs of faces

    b = block.Block(type="grass")               # create a block
    self.world_render.load_block(b, [0, 0, 0])  # load and draw a block at 0,0,0
    # this block is rendered but Not actually part of the world. It is for frame of reference

    self.loaded_blocks = 0  # how many blocks are currently rendered
    #self.slow = False

    self.focus = False      # whether the mouse is locked or not
    self.debug = False      # whether to start the debugger next frame


  def quit(self):
    """
    called when the window is closed
    """
    self.generator.stop()


  def prevent_sleep(self,dt):
    """
    prevents pyglet from not updating the screen when the application is idle.
    it makes for weird behaviour if this isn't used.
    """
    pass


  def reload_view(self,dt):
    """
    clear the rendered world
    re-draw all the blocks in the view distance of the player
    """

    # my computer glitches out if i render more than ~80,000 blocks.
    # every one else should comment this if statement out.
    #if self.loaded_blocks > 80000:
    #  if not self.slow:
    #    self.slow = True
    #    self.player.player.position = [0.0,0.0,0.0]
    #  print("loaded blocks",self.loaded_blocks)

    count = 0                               # keeps track of how many blocks were drawn this frame
    x,y,x1,y1 = self.player.get_visible()   # the square that should be visible to the player
    for a in range(x,x1):
      for b in range(y,y1):
        if self.world.column_exists(a,b):                       # if the column of blocks at (a,b) is generated
          column_pos = self.world.get_column_pos(a,b)

          for pos in column_pos:
            if not self.world.get_loaded(pos[0],pos[1],pos[2]): # don'y draw if it is already loaded
              if count <= variables.blocks_per_frame:           # stop drawing if count is more than the max blocks drawn per frame

                # load a block; to be drawn from now until cleared.
                self.world_render.load_block(self.world.get_block(pos[0],pos[1],pos[2]), [pos[0], pos[1], pos[2]])

                # flag the block as currently loaded
                self.world.set_loaded(pos[0],pos[1],pos[2],1)
                self.loaded_blocks += 1                       # number of blocks currently loaded
                count += 1                                    # number of blocks loaded this frame

        else:
          # generate the column if it isn't already
          self.generator.request_column(a,b)

    # unloads all blocks once 80,000 are rendered.
    # again only to fix a bug on my computer, everyone else comment this out.
    if self.loaded_blocks >= 80000:
      print("unloading all loaded blocks to avoid graphics glitch on my pc")
      self.world_render.unload_all()
      self.world.unload_all()
      self.loaded_blocks = 0
    #self.world_render.load_blocks(blocks)


  def check_user_input(self):
    """
    check for keys that are currently pressed and act accordingly
    """
    x = 0.0
    y = 0.0
    z = 0.0
    if self.keys[pyglet.window.key.LEFT] or self.keys[pyglet.window.key.A]:
      x += variables.move_speed[0]
    if self.keys[pyglet.window.key.RIGHT] or self.keys[pyglet.window.key.D]:
      x -= variables.move_speed[0]
    if self.keys[pyglet.window.key.UP] or self.keys[pyglet.window.key.W]:
      y += variables.move_speed[1]
    if self.keys[pyglet.window.key.DOWN] or self.keys[pyglet.window.key.S]:
      y -= variables.move_speed[1]
    if self.keys[pyglet.window.key.SPACE]:
      z += variables.move_speed[2]
    if self.keys[pyglet.window.key.LSHIFT]:
      z -= variables.move_speed[2]

    # only move the player if a button was pressed
    if x or y or z:
      if not self.player._flying:
        self.player.move(x,y,0)
        if z > 0:
          self.player.jump()
      else:
        self.player.move(x,y,z)


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


  def on_mouse_press(self, x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
      if not self.focus:
        self.set_exclusive_mouse(True)
        self.focus = True


  def on_mouse_motion(self,x,y,dx,dy):
    if self.focus:
      self.player.look(-dy*variables.mouse_sensitivity[0],dx*variables.mouse_sensitivity[1])


  def on_key_press(self,symbol,modifiers):
    if symbol == pyglet.window.key.F:
      self.player.flying()

    elif symbol == pyglet.window.key.ESCAPE:
      self.focus = False
      self.set_exclusive_mouse(False)

    elif symbol == pyglet.window.key.D and modifiers & pyglet.window.key.MOD_ALT:
      self.set_exclusive_mouse(False)
      self.focus = False
      self.debug = True


  def on_draw(self):
    if self.debug:
      pdb.set_trace()

    self.reload_view(None)
    self.player.update_physics(self.world)
    self.check_user_input()

    self.clear()
    #glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    self.player.draw_perspective()
    self.world_render.draw()