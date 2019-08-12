import pyglet
from pyglet.gl import *
from enum import Enum


class Colour(Enum):

    White = (1.0, 1.0, 1.0)
    Red = (1.0, 0.0, 0.0)
    Green = (0.0, 1.0, 0.0)
    Blue = (0.0, 0.0, 1.0)

    Requested = (1.0, 0.0, 0.0)
    Rendered = (0.0, 1.0, 0.0)


class Camera:
    MAX_ZOOM_LEVEL = 0.175
    MIN_ZOOM_LEVEL = 0.01
    ZOOM_STEP = 0.5

    def __init__(self, window, x=0.0, y=0.0, zoom=0.4):
        self.window = window
        self.x = x
        self.y = y
        self.zoom = zoom


    def zoom_in(self):
        self.zoom = min(self.zoom / Camera.ZOOM_STEP, Camera.MAX_ZOOM_LEVEL)


    def zoom_out(self):
        self.zoom = max(self.zoom * Camera.ZOOM_STEP, Camera.MIN_ZOOM_LEVEL)


    def world_projection(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        width_ratio = self.window.width / self.window.height
        gluOrtho2D(
            width_ratio / -self.zoom,
            width_ratio / self.zoom,
            width_ratio / -self.zoom,
            width_ratio / self.zoom)


class Square:

    def __init__(self, x, y, colour):
        self.x = x
        self.y = y
        self.colour = colour


    def draw(self):
        #glScalef(1.0, 1.0, 1.0)
        #glTranslatef(self.x, self.y, 0.0)
        glBegin(GL_POLYGON)
        glColor3f(*Colour.White.value)
        glVertex2f(self.x-0.5, self.y-0.5)
        glColor3f(*Colour.White.value)
        glVertex2f(self.x+0.5, self.y-0.5)
        glColor3f(*Colour.White.value)
        glVertex2f(self.x+0.5, self.y+0.5)
        glColor3f(*Colour.White.value)
        glVertex2f(self.x-0.5, self.y+0.5)
        glEnd()


class World:

    def __init__(self, renderer):
        self.renderer = renderer
        self.world_data = {} # (x, y): cube


    def set_square_colour(self, x, y, colour):
        self.world_data[(x, y)].colour = colour


    def add_square(self, x, y, colour=Colour.White):
        if (x, y) not in self.world_data:
            self.world_data[(x, y)] = Square(x, y, colour)


    def tick(self):
        for x, y in self.renderer.requested:
            self.add_square(x, y)
            self.set_square_colour(x, y, Colour.Requested)
        for x, y in self.renderer.rendered_chunks.keys():
            self.add_square(x, y)
            self.set_square_colour(x, y, Colour.Rendered)


    def draw(self):
        for _, square in self.world_data.items():
            square.draw()


class RendererGui(pyglet.window.Window):

    def __init__(self, world_renderer):
        super(RendererGui, self).__init__()
        self.set_size(250, 250)
        self.set_caption("World Renderer Status")

        self.world = World(world_renderer)
        self.camera = Camera(self)
        pyglet.clock.set_fps_limit(30)

        pyglet.clock.schedule_interval(self.update, 1/60.0)


    def update(self, dt): pass


    def quit(self):
        self.close()


    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if scroll_y > 0:
            print("Scroll up")
            self.camera.zoom_in()
        elif scroll_y < 0:
            self.camera.zoom_out()

        print("self.camera.zoom: {}".format(self.camera.zoom))


    def on_draw(self):
        self.clear()

        self.camera.world_projection()
        self.world.tick()
        self.world.draw()

        pyglet.clock.tick()
