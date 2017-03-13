from time import sleep  # sleep()
import pyglet           # gui library
from pyglet.gl import * # imports all opengl stuff


# disable/enable error checking for increased/decreased performance
pyglet.options['debug_gl'] = True


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

    # spawn invisible window with settings and resizability with "initial" as the title
    #self.window = pyglet.window.Window(800,600,context=context,visible=False,resizable=True,caption="initial")
    # spawns a fullscreen window
    #window = pyglet.window.Window(context=context,fullscreen=True)

    # load an image from a file stream thing
    #self.image_stream = open("image.png","rb")
    #self.image = pyglet.image.load("image.png",file=self.image_stream)
    # load an image from a file
    self.image = pyglet.resource.image("image.png")
    # get a part of an image
    self.image_part = self.image.get_region(x=100,y=100,width=100,height=100)

    # to break an image into multiple images for drawing animations and such
    #explosion = pyglet.image.load('explosion.png')
    #explosion_seq = pyglet.image.ImageGrid(explosion, 1, 8)

    # a bunch of sprites to draw
    self.batch = pyglet.graphics.Batch()

    # specifying in what order to draw those sprites
    self.first_group = pyglet.graphics.OrderedGroup(0)
    self.second_group = pyglet.graphics.OrderedGroup(1)

    self.sprite1 = pyglet.sprite.Sprite(self.image.get_region(x=200,y=200,width=100,height=100),
                                        batch=self.batch,group=self.first_group)
    # set the origin/anchor/place you are setting the position of in the image
    self.sprite1.anchor_x = self.sprite1.width/2
    self.sprite1.anchor_y = self.sprite1.height/2
    # create a sprite to be drawn at 400,400
    self.sprite2 = pyglet.sprite.Sprite(self.image.get_region(x=400,y=400,width=100,height=100),
                                        batch=self.batch,group=self.second_group,x=300,y=300)
    self.sprite3 = pyglet.sprite.Sprite(self.image.get_region(x=600,y=600,width=100,height=100),
                                        batch=self.batch,group=self.second_group,x=100,y=100)

    self.label = pyglet.text.Label('standard:Hello world',
                              font_name='Times New Roman',
                              font_size=36,
                              x=self.width/2,y=self.height/2,
                              anchor_x='center',anchor_y='center')
    self.html = pyglet.text.HTMLLabel('<font face="Times New Roman" size="10">html:Hello, <i>world</i></font>',
                              x=self.width/2-40, y=self.height/2-40,
                              anchor_x='center', anchor_y='center')
    self.fps = pyglet.clock.ClockDisplay()
    # makes window visible
    self.set_visible()
    # set the caption
    self.set_caption("Hello World")
    # modify window's location
    #x,y = window.get_location()
    #window.set_location(x+20,y+20)
    # set window size
    self.set_size(800,600)
    # sets the windows icon?
    #icon1 = pyglet.image.load('16x16.png')
    #icon2 = pyglet.image.load('32x32.png')
    #window.set_icon(icon1, icon2)
    # set resize limits
    self.set_minimum_size(200,150)
    self.set_maximum_size(1024,768)
    # toggle fullscreen
    #window.set_fullscreen(False)
    # toggle mouse cursor
    self.set_mouse_visible(True)
    # set mouse cursor to image
    #image = pyglet.image.load("cursor.png")
    #cursor = pyglet.window.ImageMouseCursor(image,16,8)
    #window.set_mouse_cursor(cursor)
    # mouse locking/exclusivity
    self.set_exclusive_mouse(False)


  def on_key_press(self,symbol,modifiers):
    if symbol == pyglet.window.key.A:
      print("the 'a' key was pressed")


  def on_key_release(self,symbol,modifiers):
    if symbol == pyglet.window.key.A:
      print("the 'a' key was released")


  def on_mouse_press(self,x,y,button,modifiers):
    if button == pyglet.window.mouse.LEFT:
      print("left mouse button pressed")


  def on_mouse_release(self,x,y,button,modifiers):
    if button == pyglet.window.mouse.LEFT:
      print("left mouse button released")


  # x,y is the current mouse position; dx,dy is the distance the mouse was moved to get to x,y
  def on_mouse_motion(self,x,y,dx,dy):
    pass


  # same as mouse motion but with the mouse buttons and keyboard modifiers
  def on_mouse_drag(self,x,y,dx,dy,buttons,modifiers):
    if buttons & pyglet.window.mouse.LEFT:
      print("dragged left mouse button and keyboard modifiers")
    elif not buttons & pyglet.window.mouse.LEFT:
      print("dragged left mouse button")


  def on_mouse_enter(self,x,y):
    pass


  def on_mouse_exit(self,x,y):
    pass


  def on_draw(self):
    # nicer window clear
    self.clear()

    # opengl window clear
    #glClear(GL_COLOR_BUFFER_BIT)

    # draw image & label
    self.image.blit(0,0)
    #self.image_part.blit(0,0)
    self.batch.draw()
    #self.sprite.draw()
    self.label.draw()
    self.html.draw()
    self.fps.draw()

    # draw triangle with opengl
    #glLoadIdentity()
    #glBegin(GL_TRIANGLES)
    #glVertex2f(0,0)
    #glVertex2f(window.width,0)
    #glVertex2f(window.width,window.height)
    #glEnd()

    # draws a box
    pyglet.gl.glColor3f(0,0,255)
    pyglet.graphics.draw_indexed(4, pyglet.gl.GL_TRIANGLES,
      [0, 1, 2, 0, 2, 3],
      ('v2i', (799, 599,
               400, 599,
               400, 400,
               799, 400)),
    )
    pyglet.gl.glColor3f(255,255,255)


  def on_resize(self,width,height):
    glViewport(0,0,width,height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0,width,0,height,-1,1)
    glMatrixMode(GL_MODELVIEW)
  # prints events
  #window.push_handlers(pyglet.window.event.WindowEventLogger())


# calls this function every 1 second
#def updateStuff(dt):
#  pass
#pyglet.clock.schedule_interval(updateStuff,0.1)

# run this as fast as possible
#pyglet.clock.schedule(updateStuff)

# run this once in 5.0 seconds
#pyglet.clock.schedule_once(updateStuff,5.0)


# animation stuff
#def update(dt):
  # move stuff here
#pyglet.clock.schedule_interval(update,1/60.0)



def screens():
  ret = []
  for screen in display.get_screens():
    ret.append(screen)
  return ret


def print_screens():
  for screen in screens():
    print(screen)

# settings_dir is set to a suitable path to store game data
#settings_dir = pyglet.resource.get_settings_path('snake')

#if not os.path.exists(settings_dir):
  #os.makedirs(settings_dir)
#filename = os.path.join(settings_dir,"settings.ini")

window = Window()
pyglet.app.run()