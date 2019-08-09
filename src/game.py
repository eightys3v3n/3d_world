import logging
import sys
import variables
import config
import world_data
import player
import world_generator
import block
import math
import os
import pdb
from pyglet.gl  import *
from threading  import Thread
from time       import time
from time       import sleep
from noise      import pnoise2
from world_renderer import WorldRenderer
import variables
import itertools


class Game(pyglet.window.Window):
  """
  a class that contains the window, world, world rendering, player, event handling, generation
  """
  def __init__(self):
    self.log = logging.getLogger()
    h = logging.StreamHandler()
    h.setLevel(config.Game.ConsoleLogLevel)
    fh = logging.FileHandler(config.LogFile)
    f = logging.Formatter(config.LogFormat)
    ff = logging.Formatter(config.LogFormat)
    h.setFormatter(f)
    fh.setFormatter(ff)
    self.log.addHandler(h)
    self.log.addHandler(fh)
    self.log.info("Started logging.")

    # setup the window
    self.log.info("Initializing window...")
    super(Game, self).__init__(resizable=True)                     # initialize the window
    #if config.Window.Width is not None and config.Window.Height is not None:
      #self.set_size(config.Window.Width, config.Window.Height)       # set the window size
    self.set_exclusive_mouse(False)                  # lock the cursor to this window
    self.set_vsync(variables.vsync)                  # turn off vsync so the framerate isn't limited at your refresh rate
    self.log.info("Initialized window.")

    self.log.info("Setting up key state handler...")
    # setup keyboard event handling
    self.keys = pyglet.window.key.KeyStateHandler()  # allows for a is_this_key_pressed check
    self.push_handlers(self.keys)                    # tells pyglet that it should keep track of when keys are pressed
    self.log.info("Setup key state handler.")

    if sys.platform == 'linux':
      os.nice(2)
    # setup game
    self.log.info("Setting up world data server...")
    self.world_server = world_data.WorldDataServer(self.log)                       # the world
    self.world_server.start()
    self.world_client = self.world_server.get_main_client()
    self.log.info("Setup world data server.")
    if sys.platform == 'linux':
      os.nice(0)

    self.log.info("Getting extra world data clients for other processes...")
    generator_world_client = self.world_client.new_client("World Generator")[config.WorldRequestData.NewClient]
    renderer_world_client = self.world_client.new_client("World Renderer")[config.WorldRequestData.NewClient]
    self.log.info("Got extra world data clients for other processes.")

    self.log.info("Creating player...")
    self.player = player.PlayerManager(self.world_client)        # the player and/or perspective
    self.log.info("Created player.")

    self.log.info("Creating and starting world generator...")
    if sys.platform == 'linux':
      os.nice(10)
    self.world_generator = world_generator.WorldGenerator(generator_world_client, self.log) # generates new chunks
    self.world_generator.start()
    self.log.info("Created and started world generator.")

    self.log.info("Creating and starting world renderer...")
    if sys.platform == 'linux':
      os.nice(8)
    self.world_renderer = WorldRenderer(renderer_world_client, self.log)          # draws the world
    self.world_renderer.start()
    self.log.info("Created and started world renderer.")

    if sys.platform == 'linux':
      os.nice(0)
    pyglet.clock.set_fps_limit(variables.maximum_framerate)      # set the maximum framerate
    if config.Game.PreventSleep:
      pyglet.clock.schedule_interval(self.prevent_sleep, 1.0/60.0) # this prevents the application from 'smartly' sleeping when idle

    pyglet.clock.schedule_interval(self.player.update_physics, variables.physics_updates)

    self.log.info("Configuring OpenGL...")
    glEnable(GL_DEPTH_TEST) # gpu can tell when stuff is infront or behind
    glDepthFunc(GL_LESS)    # anything closer should be drawn
    glEnable(GL_CULL_FACE)  # don't draw faces that are behind something
    glFrontFace(GL_CCW)     # used to determine the 'front' of a 2d shape
    glCullFace(GL_BACK)     # remove the backs of faces
    glDepthRange(0, 1)      # Show as much depth wise as possible
    glEnable(GL_DEPTH_CLAMP)
    self.log.info("Configured OpenGL.")

    self.loaded_blocks = 0 # how many blocks are currently rendered

    self.focus = False     # whether the mouse is locked or not
    self.debug = False     # whether to start the debugger next frame


    # Pre-generate a bunch of blocks and wait for them to finish so as to not clutter the logs.
    #for cx, cy in itertools.product(range(-5, 6), range(-5, 6)):
    #  self.world_generator.request_chunk(cx, cy)

    self.fps_display = pyglet.clock.ClockDisplay(color=(1.0, 1.0, 1.0, 1.0))
    self.log.info("Started.")

    self.times = []
    if config.Debug.Game.FPS_SPAM:
      self.fps = {}

    if config.WorldGenerator.InitialDistance > 0:
      print("Generating initial radius of {}.".format(config.WorldGenerator.InitialDistance))
      self.generate_radius(0, 0, config.WorldGenerator.InitialDistance)

    if config.WorldRenderer.InitialDistance > 0:
      print("Rendering initial radius of {}.".format(config.WorldRenderer.InitialDistance))
      self.generate_radius(0, 0, config.WorldRenderer.InitialDistance)


  def generate_radius(self, cx, cy, radius):
    r = range(-radius, radius+1)
    for ox, oy in itertools.product(r, r):
      x = ox + cx
      y = oy + cy
      self.world_generator.request_chunk(x, y)


  def render_radius(self, cx, cy, radius):
    r = range(-radius, radius+1)
    for ox, oy in itertools.product(r, r):
      x = ox + cx
      y = oy + cy
      self.world_renderer.request_chunk(x, y)


  def quit(self):
    """
    called when the window is closed
    """
    self.world_generator.stop()
    self.world_server.stop()
    self.world_renderer.stop()

    if len(self.times) > 0:
      average = round(sum(self.times) / len(self.times), 5)
      print("Average load_finished_chunks time: {}".format(average))


  def prevent_sleep(self,dt):
    """
    prevents pyglet from not updating the screen when the application is idle.
    it makes for weird behaviour if this isn't used.
    """
    pass


  def generate_view(self):
    """
    Requests chunks in config.WorldGenerator.Distance to be generated.
    """

    if config.Debug.Game.TimeRenderingChunks:
      before = time()

    self.world_renderer.render_queued()

    if config.Debug.Game.TimeRenderingChunks:
      after = time()
      res = round(after - before, 5)
      if res >= 0.0005:
        print("Took {:.4} seconds to load_finished_chunks.".format(round(after - before, 4)))
        self.times.append(res)

    current_chunk = self.world_client.abs_block_to_chunk_block(*self.player.standing_on())[0]

    # Generate all the chunks in the generation distance.
    self.generate_radius(*current_chunk, config.WorldGenerator.Distance)
    self.render_radius(*current_chunk, config.WorldRenderer.Distance)


  def check_user_input(self):
    """
    check for keys that are currently pressed and act accordingly
    """
    x = 0.0
    y = 0.0
    z = 0.0

    # player movement
    if self.keys[pyglet.window.key.LEFT] or self.keys[pyglet.window.key.A]:
      x += variables.move_speed[0]
      #self.log.debug("Moving left.")
    if self.keys[pyglet.window.key.RIGHT] or self.keys[pyglet.window.key.D]:
      x -= variables.move_speed[0]
      #self.log.debug("Moving right.")

    if self.keys[pyglet.window.key.UP] or self.keys[pyglet.window.key.W]:
      y += variables.move_speed[2]
      #self.log.debug("Moving forward.")
    if self.keys[pyglet.window.key.DOWN] or self.keys[pyglet.window.key.S]:
      y -= variables.move_speed[2]
      #self.log.debug("Moving backward.")
    if self.keys[pyglet.window.key.SPACE]:
      z += variables.move_speed[1]
      #self.log.debug("Moving up")
    if self.keys[pyglet.window.key.LSHIFT]:
      z -= variables.move_speed[1]
      #self.log.debug("Moving down")

    # only try to move the player if a button was pressed
    if x or y or z:
      if not self.player._flying:
        self.player.move(x,0,z)
        if y > 0:
          self.player.jump()
      else:
        self.player.move(x,y,z)


  def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
    if scroll_y < 0:
      variables.move_speed[0] -= 1
      variables.move_speed[1] -= 1
      variables.move_speed[2] -= 1
    elif scroll_y > 0:
      variables.move_speed[0] += 1
      variables.move_speed[1] += 1
      variables.move_speed[2] += 1

    for i, m in enumerate(variables.move_speed):
      if m < 0:
        variables.move_speed[i] = 0.001

    if variables.debug.print_move_speed:
      print("New move speed: {}, {}, {}".format(round(variables.move_speed[0], 4), round(variables.move_speed[1], 4), round(variables.move_speed[2], 4)))


  def on_mouse_press(self, x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
      if not self.focus:
        self.log.debug("Taking focus.")
        self.set_exclusive_mouse(True)
        self.focus = True


  def on_mouse_motion(self,x,y,dx,dy):
    if self.focus:
      self.player.look(-dy*variables.mouse_sensitivity[0],dx*variables.mouse_sensitivity[1])


  def on_key_press(self,symbol,modifiers):
    if symbol == pyglet.window.key.F:
      self.player.flying()

    elif symbol == pyglet.window.key.ESCAPE:
      self.log.debug("Dropping focus.")
      self.focus = False
      self.set_exclusive_mouse(False)

    elif symbol == pyglet.window.key.PLUS:
      config.WorldRenderer.MaxBlocksPerFrame += 10
      print("MaxBlocksPerFrame: {}".format(config.WorldRenderer.MaxBlocksPerFrame))

    elif symbol == pyglet.window.key.MINUS:
      config.WorldRenderer.MaxBlocksPerFrame = max(0, config.WorldRenderer.MaxBlocksPerFrame - 10)
      print("MaxBlocksPerFrame: {}".format(config.WorldRenderer.MaxBlocksPerFrame))


    elif symbol == pyglet.window.key.D and modifiers & pyglet.window.key.MOD_ALT:
      self.set_exclusive_mouse(False)
      self.focus = False
      self.debug = True

    elif symbol == pyglet.window.key.G:
      if config.WorldGenerator.Distance <= 2:
        config.WorldGenerator.Distance = 10
      else:
        config.WorldGenerator.Distance = 1

  def on_resize(self, width, height):
    config.Window.Width = width
    config.Window.Height = height
    super(Game, self).on_resize(width, height)
    print("Resizing window: {}, {}".format(config.Window.Width, config.Window.Height))


  def on_draw(self):
    dt = pyglet.clock.tick()


    if __debug__ and config.Debug.Game.FPS_SPAM:
      offset = 10000
      if dt > 0:
        self.fps[round(time()*offset)] = 1.0 / dt / 100
        #self.fps.append(pyglet.clock.get_fps()) # actually calculating the framerate seems to be more accurate.
        while time() - list(self.fps.keys())[0]/offset >= config.Debug.Game.FPS_SPAM_SPAN: del self.fps[list(self.fps.keys())[0]]
        if len(self.fps) > 0:
          avgerage = round(sum(self.fps.values()) / len(self.fps), 2)
          print("Average FPS: {}".format(avgerage))
          minimum = round(min(self.fps.values()), 2)
          print("Minimum FPS: {}".format(minimum))


    if __debug__ and self.debug:
      self.debug = False
      pdb.set_trace()

    self.check_user_input()

    self.clear()
    #glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    self.player.draw_perspective(config.Window.Width, config.Window.Height)
    self.generate_view()
    self.world_renderer.draw()

    glTranslatef(0, 1000, 0)
    self.fps_display.draw()
