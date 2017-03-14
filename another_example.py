from time import sleep  # sleep()
import pyglet           # gui library
from pyglet.gl import * # imports all opengl stuff


width  = 800
height = 600


class Window(pyglet.window.Window):
  def __init__(self):
    platform = pyglet.window.get_platform()
    display = platform.get_default_display()
    screen = display.get_default_screen()
    template = pyglet.gl.Config(alpha_size=8)
    try:
      config = screen.get_best_config(template)
    except pyglet.window.NoSuchConfigException:
      template = gl.Config()
      config = screen.get_best_config(template)
    context = config.create_context(None)
    super(Window,self).__init__()

    # set the caption
    self.set_caption("Hello World")

    # set window size
    self.set_size(width,height)

    # toggle mouse cursor
    self.set_mouse_visible(True)


  def on_draw(self):
    # clear window to black
    self.clear()

    # make the camera
    glViewport(0,0,width,height)

    # start changing the way you see things, not where the things actually are
    glMatrixMode(GL_PROJECTION)
    # actually change the mode
    glLoadIdentity()


    glOrtho(0,width,0,height,-1,1)

    # back to changing where things actually are.
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # draw triangle with opengl
    glColor3f(0,0,255)

    pyglet.graphics.draw_indexed(4, pyglet.gl.GL_TRIANGLES,
      [0, 1, 2, 0, 2, 3],
      ('v2i', (799, 599,
               400, 599,
               400, 400,
               799, 400)),
    )


window = Window()
pyglet.app.run()