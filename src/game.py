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
from minimap import Minimap
import variables
import itertools


class Game(pyglet.window.Window):
  """The main game class."""
  def __init__(self):
    self.setup_logger()

    # Setup the window
    self.log.info("Initializing window...")
    super(Game, self).__init__(resizable=True)                     # initialize the window
    if config.Window.Width is not None and config.Window.Height is not None:
      self.set_size(config.Window.Width, config.Window.Height)       # set the window size
    self.set_exclusive_mouse(False)                  # don't lock the cursor to this window to start with.
    self.set_vsync(variables.vsync)                  # turn off vsync so the framerate isn't limited at your refresh rate. Doesn't work on my computer anyways so I have it off.
    self.log.info("Initialized window.")

    # setup keyboard event handling so we can ask if a key is currently pressed rather than only knowing when a key is pressed.
    self.log.info("Setting up key state handler...")
    self.keys = pyglet.window.key.KeyStateHandler()  # allows for a is_this_key_pressed check
    self.push_handlers(self.keys)                    # tells pyglet that it should keep track of when keys are pressed
    self.log.info("Setup key state handler.")

    # Setup the world data storange.
    if sys.platform == 'linux': # Set the niceness a little lower on Linux so the main thread runs smooth at all times.
      os.nice(2)
    self.log.info("Setting up world data server...")
    self.world_server = world_data.WorldDataServer(self.log) # Stores the world data.
    self.world_server.start() # Start the server.
    self.world_client = self.world_server.get_main_client() # Get the client that is used by the main thread and to create more clients.
    self.log.info("Setup world data server.")
    if sys.platform == 'linux': # Set the niceness back to normal.
      os.nice(0)

    # Create some more clients for the various processes we will start.
    self.log.info("Getting extra world data clients for other processes...")
    generator_world_client = self.world_client.new_client("World Generator")[config.WorldRequestData.NewClient]
    renderer_world_client = self.world_client.new_client("World Renderer")[config.WorldRequestData.NewClient]
    self.log.info("Got extra world data clients for other processes.")

    # Create the player object.
    self.log.info("Creating player...")
    self.player = player.PlayerManager(self.world_client)        # the player and/or perspective
    self.log.info("Created player.")

    # Create and start the world generator process.
    self.log.info("Creating and starting world generator...")
    if sys.platform == 'linux':
      os.nice(10)
    self.world_generator = world_generator.WorldGenerator(generator_world_client, self.log) # generates new chunks
    self.world_generator.start()
    self.log.info("Created and started world generator.")

    # Create and start the world renderer process.
    self.log.info("Creating and starting world renderer...")
    if sys.platform == 'linux':
      os.nice(8)
    self.world_renderer = WorldRenderer(renderer_world_client, self.log)          # draws the world
    self.world_renderer.start()
    self.log.info("Created and started world renderer.")

    # Create a second window using PyGame for debugging or whatever it currently does.
    if config.Game.Minimap:
      self.minimap = Minimap(self.world_renderer, self.world_generator, self.world_client)

    if sys.platform == 'linux':
      os.nice(0)

    #pyglet.clock.set_fps_limit(variables.maximum_framerate)      # set the maximum framerate
    # Removed in recent pyglet? This needs to be fixed or looked into

    # PyGlet does this weird thing where the on_draw method is only called if something happens. So if you don't press keys, the game appears to be running at 1 FPS. This prevents that and makes sure the game runs at least 60 FPS. Decreasing this number doesn't seem to make the game run faster.
    if config.Game.PreventSleep:
      pyglet.clock.schedule_interval(self.prevent_sleep, 1.0/60.0) # this prevents the application from 'smartly' sleeping when idle

    # Initially set all the GL flags and what not. There are cases where this needs to be set every frame (like having two PyGlet windows. That's why the Minimap is written in PyGame.
    self.log.info("Configuring OpenGL...")
    glEnable(GL_DEPTH_TEST) # gpu can tell when stuff is infront or behind
    glDepthFunc(GL_LEQUAL)    # anything closer should be drawn
    glEnable(GL_CULL_FACE)  # don't draw faces that are behind something
    glFrontFace(GL_CCW)     # used to determine the 'front' of a 2d shape
    glCullFace(GL_BACK)     # remove the backs of faces
    glDepthRange(0, 1)      # Show as much depth wise as possible
    self.log.info("Configured OpenGL.")

    self.focus = False     # whether the mouse is locked or not
    self.debug = False     # whether to start the debugger next frame


    # Pre-generate a bunch of blocks and wait for them to finish so as to not clutter the logs.
    #for cx, cy in itertools.product(range(-5, 6), range(-5, 6)):
    #  self.world_generator.request_chunk(cx, cy)

    self.log.info("Started.")

    self.times = []
    if config.Debug.Game.FPS_SPAM: # Create the fps dictionary if we want to spam the current FPS to the console.
      self.fps = {}

    # Generate and attempt to render an initial distance if the config file says so. This happens before drawing.
    if config.WorldGenerator.InitialDistance > 0:
      print("Generating initial radius of {}.".format(config.WorldGenerator.InitialDistance))
      self.generate_radius(0, 0, config.WorldGenerator.InitialDistance)

    if config.WorldRenderer.InitialDistance > 0:
      print("Rendering initial radius of {}.".format(config.WorldRenderer.InitialDistance))
      self.generate_radius(0, 0, config.WorldRenderer.InitialDistance)


  def setup_logger(self):
    # Create the logger.
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


  def generate_radius(self, cx, cy, radius):
    """Request to generate all the chunks in a radius around (cx, cy)."""
    r = range(-radius, radius+1)
    for ox, oy in itertools.product(r, r):
      x = ox + cx
      y = oy + cy
      self.world_generator.request_chunk(x, y)


  def render_radius(self, cx, cy, radius):
    """Request to render all the chunks in a radius around (cx, cy)."""
    r = range(-radius, radius+1)
    for ox, oy in itertools.product(r, r):
      x = ox + cx
      y = oy + cy
      if not self.world_renderer.is_rendered(x, y):
        self.world_renderer.request_chunk(x, y)


  def prevent_sleep(self,dt):
    """
    prevents pyglet from not updating the screen when the application is idle.
    it makes for weird behaviour if this isn't used.
    """
    pass


  def generate_view_sequence(self, cx, cy, view_distance):
    """This is intended to return the sequence to request chunks. However right now just the radius functions are being used instead. So if you want to generate things furthest to closest, this would be for that. But it's not used right now."""
    seq = []
    for distance in range(view_distance):
      if distance == 0:
        seq.append((cx, cy))
        continue;

    for length in range(distance):
      if length == 0:
        seq.append((cx-distance, cy))
        seq.append((cx+distance, cy))
      else:
        seq.append((cx+distance, cy-length))
        seq.append((cx-distance, cy-length))
        seq.append((cx+distance, cy+length))
        seq.append((cx-distance, cy+length))

    for height in range(distance):
      if height == 0:
        seq.append((cx, cy-distance))
        seq.append((cx, cy+distance))
      else:
        seq.append((cx-height, cy+distance))
        seq.append((cx-height, cy-distance))
        seq.append((cx+height, cy+distance))
        seq.append((cx+height, cy-distance))
    return seq


  def generate_view(self):
    """
    Requests chunks to be generated, rendered, and continue rendering any pre-calculated chunks.
    """

    if config.Debug.Game.TimeRenderingChunks:
      before = time()

    self.world_renderer.render_queued() # Actually draw any chunks that were pre-calculated.

    if config.Debug.Game.TimeRenderingChunks:
      after = time()
      res = round(after - before, 5)
      if res >= 0.0005:
        print("Took {:.4} seconds to load_finished_chunks.".format(round(after - before, 4)))
        self.times.append(res)

    cx, cy = self.world_client.abs_block_to_chunk_block(*self.player.standing_on())[0] # Get the chunk the player is in.

    # Generate all the chunks in the generation distance.
    self.generate_radius(cx, cy, config.WorldGenerator.Distance)
    self.render_radius(cx, cy, config.WorldRenderer.Distance)
    # Using a funky pattern because why not.
    #for x, y in self.generate_view_sequence(cx, cy, config.WorldGenerator.Distance):
      #self.world_generator.request_chunk(x, y)
    #for x, y in self.generate_view_sequence(cx, cy, config.WorldRenderer.Distance):
      #self.world_renderer.request_chunk(x, y)


  def check_user_input(self):
    """
    Check for keys that are currently pressed and act accordingly. This is not for when a key is pressed for the first time. This is only if you want to know when a key is held down. See on_key_press() and on_key_release().
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
      self.player.move(x,y,z)


  def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
    """Is called when the scroll wheel is used."""
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
    """Is called when a mouse button is pressed."""
    if button == pyglet.window.mouse.LEFT:
      if not self.focus:
        self.log.debug("Taking focus.")
        self.set_exclusive_mouse(True)
        self.focus = True


  def on_mouse_motion(self,x,y,dx,dy):
    """Is called when the mouse moves in the window."""
    if self.focus:
      self.player.look(-dy*variables.mouse_sensitivity[0],dx*variables.mouse_sensitivity[1])


  def on_key_press(self,symbol,modifiers):
    """Is called when a key is pressed; and only when a key is pressed down, not called repeatedly when the key is held. See check_user_input() for held keys."""
    #if symbol == pyglet.window.key.F:
      #self.player.flying()

    if symbol == pyglet.window.key.ESCAPE: # Let the mouse out of the window.
      self.log.debug("Dropping focus.")
      self.focus = False
      self.set_exclusive_mouse(False)

    elif symbol == pyglet.window.key.PLUS: # Increase the number of blocks drawn per frame.
      config.WorldRenderer.MaxBlocksPerFrame += 10
      print("MaxBlocksPerFrame: {}".format(config.WorldRenderer.MaxBlocksPerFrame))

    elif symbol == pyglet.window.key.MINUS: # Decrease the number of blocks drawn per frame.
      config.WorldRenderer.MaxBlocksPerFrame = max(0, config.WorldRenderer.MaxBlocksPerFrame - 10)
      print("MaxBlocksPerFrame: {}".format(config.WorldRenderer.MaxBlocksPerFrame))

    elif symbol == pyglet.window.key.D and modifiers & pyglet.window.key.MOD_ALT: # Open the debugger on the beginning of the next frame.
      self.set_exclusive_mouse(False)
      self.focus = False
      self.debug = True

    elif symbol == pyglet.window.key.O: # Return the chunk the player is standing in and whether it has been requested to be rendered.
      cx, cy = self.world_client.abs_block_to_chunk_block(*self.player.standing_on())[0]
      print("Chunk {}, {}".format(cx, cy))
      if (cx, cy) in self.world_renderer.requested:
        print("Chunk is in requested")


  def on_resize(self, width, height):
    """Called when window is resized."""
    config.Window.Width = width
    config.Window.Height = height
    super(Game, self).on_resize(width, height)
    print("Resizing window: {}, {}".format(config.Window.Width, config.Window.Height))


  def on_close(self):
    """Called when the game closes or is killed with C-c on the command line."""
    self.close()
    self.world_generator.stop()
    self.world_server.stop()
    self.world_renderer.stop()
    if config.Game.Minimap:
      self.minimap.close()

    if len(self.times) > 0:
      average = round(sum(self.times) / len(self.times), 5)
      print("Average load_finished_chunks time: {}".format(average))



  def on_draw(self):
    """Called every frame."""

    # Print the FPS spam if it's enabled.
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

    # if the debug flag is set, start the debugger; only when the app isn't running with the -O flag.
    if __debug__ and self.debug:
      self.debug = False
      pdb.set_trace()

    self.check_user_input()

    self.clear() # Clear the screen
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST) # Maybe change OpenGL settings to look nicer???

    self.player.draw_perspective() # Set the FOV, move the player 'camera', and looking direction.
    self.generate_view() # Do all the generating of chunks and rendering of chunks.

    self.world_renderer.draw() # Draw the world.

    # Update the second window if it's enabled.
    if config.Game.Minimap:
      self.minimap.update()
      self.minimap.draw()

