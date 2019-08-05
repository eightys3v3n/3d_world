import logging
import variables
import config
import world_data
import player
import world_generator
import world_renderer
import block
import pdb
from pyglet.gl  import *
from math       import floor
from threading  import Thread
from time       import time
from time       import sleep
from noise      import pnoise2
from variables  import window_width, window_height
import variables
import itertools


class Game(pyglet.window.Window):
  """
  a class that contains the window, world, world rendering, player, event handling, generation
  """
  def __init__(self):
    self.log = logging.getLogger()
    h = logging.StreamHandler()
    fh = logging.FileHandler(config.LogFile)
    f = logging.Formatter(config.LogFormat)
    ff = logging.Formatter(config.LogFormat)
    h.setFormatter(f)
    fh.setFormatter(ff)
    self.log.addHandler(h)
    self.log.addHandler(fh)
    self.log.setLevel(logging.INFO)
    self.log.info("Started logging.")

    # setup the window
    self.log.info("Initializing window...")
    super(Game, self).__init__()                     # initialize the window
    self.set_size(window_width, window_height)       # set the window size
    self.set_exclusive_mouse(False)                  # lock the cursor to this window
    self.set_vsync(variables.vsync)                  # turn off vsync so the framerate isn't limited at your refresh rate
    self.log.info("Initialized window.")

    self.log.info("Setting up key state handler...")
    # setup keyboard event handling
    self.keys = pyglet.window.key.KeyStateHandler()  # allows for a is_this_key_pressed check
    self.push_handlers(self.keys)                    # tells pyglet that it should keep track of when keys are pressed
    self.log.info("Setup key state handler.")

    # setup game
    self.log.info("Setting up world data server...")
    self.world_server = world_data.WorldDataServer(self.log)                       # the world
    self.world_server.start()
    self.world_client = self.world_server.get_main_client()
    self.log.info("Setup world data server.")

    self.log.info("Getting extra world data clients for other processes...")
    generator_world_client = self.world_client.new_client("World Generator")[config.WorldRequestData.NewClient]
    renderer_world_client = self.world_client.new_client("World Renderer")[config.WorldRequestData.NewClient]
    self.log.info("Got extra world data clients for other processes.")

    self.log.info("Creating player...")
    self.player = player.PlayerManager(self.world_client)        # the player and/or perspective
    self.log.info("Created player.")

    self.log.info("Creating and starting world generator...")
    self.world_generator = world_generator.WorldGenerator(generator_world_client, self.log) # generates new chunks
    self.world_generator.start()
    self.log.info("Created and started world generator.")

    self.log.info("Creating and starting world renderer...")
    self.world_renderer = world_renderer.WorldRenderer(renderer_world_client, self.log)          # draws the world
    self.world_renderer.start()
    self.log.info("Created and started world renderer.")

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
    self.log.info("Configured OpenGL.")

    self.loaded_blocks = 0 # how many blocks are currently rendered

    self.focus = False     # whether the mouse is locked or not
    self.debug = False     # whether to start the debugger next frame


    for cx, cy in itertools.product(range(-5, 6), range(-5, 6)):
      self.world_generator.request_chunk(cx, cy)
    # render a reference block
    #b = block.Block(type="grass")              # create a block
    #self.world_render.load_block(b, [0, 0, 0]) # load and draw a block at 0,0,0

    self.fps_display = pyglet.clock.ClockDisplay(color=(1.0, 1.0, 1.0, 0.5))


  def quit(self):
    """
    called when the window is closed
    """
    self.world_generator.stop()
    self.world_server.stop()
    self.world_renderer.stop()


  def prevent_sleep(self,dt):
    """
    prevents pyglet from not updating the screen when the application is idle.
    it makes for weird behaviour if this isn't used.
    """
    pass


  def render_columns(self, x, y, x1, y1):
    count = 0
    positions = list(itertools.product(range(x, x1), range(y, y1)))
    for a, b in positions:
      if not self.world.column_exists(a,b):                       # if the column of blocks at (a,b) is generated
        self.generator.request_column(a, b)
        continue

      column_pos = self.world.get_column_pos(a,b)

      for pos in column_pos:
        if not self.world.get_loaded(pos[0],pos[1],pos[2]): # don't draw if it is already loaded
          if variables.renderer.blocks_drawn_per_frame is None or count <= variables.renderer.blocks_drawn_per_frame:           # stop drawing if count is more than the max blocks drawn per frame

            # load a block; to be drawn from now until cleared.
            self.world_render.load_block(self.world.get_block(*pos), [pos[0], pos[1], pos[2]])

            # flag the block as currently loaded
            self.world.set_loaded(pos[0],pos[1],pos[2],1)
            self.loaded_blocks += 1                       # number of blocks currently loaded
            count += 1                                    # number of blocks loaded this frame




  def generate_view(self):
    """
    Requests chunks in config.WorldGenerator.Distance to be generated.
    """
    current_chunk = self.world_client.abs_block_to_chunk_block(*self.player.standing_on())[0]
    #self.world_generator.request_chunk(*current_chunk)
    print(self.player.standing_on())
    print(current_chunk)
    if not self.world_renderer.is_rendered(*current_chunk):
      self.world_renderer.render_chunk(*current_chunk)

    pyglet.gl.glColor3f(255, 255, 255)
    pyglet.graphics.draw_indexed(4, pyglet.gl.GL_POLYGON,
      [0, 1, 2, 3, 0],
      ('v3f', (0, 0, 0,
               0, 100, 0,
               100, 100, 0,
               100, 0, 0)),
    )

    # my computer glitches out if i render more than ~80,000 blocks.
    # every one else should comment this if statement out.
    #if self.loaded_blocks > 80000:
    #  if not self.slow:
    #    self.slow = True
    #    self.player.player.position = [0.0,0.0,0.0]
    #  print("loaded blocks",self.loaded_blocks)

    #count = 0                               # keeps track of how many blocks were drawn this frame
    #visible = self.player.get_visible()   # the square that should be visible to the player
    #self.world_render.request_columns(*visible)
    #self.world_renderer.draw(self)
#    for a in range(x, x1):
#      for b in range(y, y1):
#        if self.world.column_exists(a,b):                       # if the column of blocks at (a,b) is generated
#          column_pos = self.world.get_column_pos(a,b)
#
#          for pos in column_pos:
#            if not self.world.get_loaded(pos[0],pos[1],pos[2]): # don't draw if it is already loaded
#              if count <= variables.renderer.blocks_drawn_per_frame:           # stop drawing if count is more than the max blocks drawn per frame

                # load a block; to be drawn from now until cleared.
#                self.world_render.load_block(self.world.get_block(*pos), [pos[0], pos[1], pos[2]])

                # flag the block as currently loaded
#                self.world.set_loaded(pos[0],pos[1],pos[2],1)
#                self.loaded_blocks += 1                       # number of blocks currently loaded
#                count += 1                                    # number of blocks loaded this frame

#        else:
          # generate the column if it isn't already
#          self.generator.request_column(a, b)

    # unloads all blocks once max_blocks are rendered.
    # again only to fix a bug on my computer, everyone else comment this out.
    #if variables.debug.max_blocks is not None and self.loaded_blocks >= variables.debug.max_blocks:
    #  print("unloading all loaded blocks to avoid graphics glitch on my pc")
    #  raise NotImplemented()
      # This feature was removed with the new world renderer
      #self.world_render.unload_all()
      #self.world.unload_all()
      #self.loaded_blocks = 0
    #self.world_render.load_blocks(blocks)


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
      variables.move_speed[0] -= 0.1
      variables.move_speed[1] -= 0.1
      variables.move_speed[2] -= 0.1
    elif scroll_y > 0:
      variables.move_speed[0] += 0.1
      variables.move_speed[1] += 0.1
      variables.move_speed[2] += 0.1

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

    elif symbol == pyglet.window.key.D and modifiers & pyglet.window.key.MOD_ALT:
      self.set_exclusive_mouse(False)
      self.focus = False
      self.debug = True

    elif symbol == pyglet.window.key.G:
      if config.WorldGenerator.Distance <= 2:
        config.WorldGenerator.Distance = 10
      else:
        config.WorldGenerator.Distance = 1


  def on_draw(self):
    pyglet.clock.tick()

    if self.debug:
      self.debug = False
      pdb.set_trace()

    self.check_user_input()

    self.clear()
    #glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    self.generate_view()
    self.player.draw_perspective()
    self.world_renderer.draw()

    glTranslatef(0, 1000, 0)
    self.fps_display.draw()
