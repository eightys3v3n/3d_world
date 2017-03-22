from pyglet.gl import *
from math import cos,hypot,degrees,radians,sin,atan2
import variables


class Player:
  def __init__(self):
    self.position = [0.0,0.0,0.0]
    self.heading = [0.0,0.0,0.0]
    self.current_block = [0.0,0.0,0.0]
    self.visible = [0,0,0,0]
    self.height  = variables.player_height


  def move(self,x,y,z):
    hyp = hypot(x,y)
    ang = degrees(atan2(y,x))
    ang = round(ang,4)

    x = round(hyp*cos(radians(ang+self.heading[1])),4)
    y = round(hyp*sin(radians(ang+self.heading[1])),4)

    self.position[0] += x
    self.position[1] += y
    self.position[2] += z


  def look(self,x,y):
    self.heading[0] += x
    self.heading[1] += y

    if self.heading[1] > 360:
      self.heading[1] -= 360
    elif self.heading[1] < 0:
      self.heading[1] += 360

    if self.heading[0] < -90:
      self.heading[0] = -90
    elif self.heading[0] > 90:
      self.heading[0] = 90


class PlayerManager():
  def __init__(self):
    self.player = Player()
    self.flying = True


  def get_position(self):
    return self.player.position


  def look(self,x,y):
    self.player.look(x,y)


  def move(self, x=0.0, y=0.0, z=0.0):
    if abs(x) > variables.move_speed[0]:
      x = variables.move_speed[0] * x/-x
    if abs(y) > variables.move_speed[1]:
      y = variables.move_speed[1] * y/-y
    if abs(z) > variables.move_speed[2]:
      z = variables.move_speed[2] * z/-z

    if self.flying:
      self.player.move(x,y,z)
    else:
      self.player.move(x,y,z)


  def jump(self):
    print("jump not implimented")


  def standing_on(self):
    return self.player.current_block


  def set_standing_on(self, new_block_pos):
    self.player.current_block = new_block_pos
    x = round(self.player.current_block[0]-variables.view_distance)
    x1 = round(self.player.current_block[0]+variables.view_distance)
    y = round(self.player.current_block[1]-variables.view_distance)
    y1 = round(self.player.current_block[1]+variables.view_distance)
    self.player.visible = [x,y,x1,y1]


  def get_visible(self):
    return self.player.visible


  def draw_perspective(self):
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluPerspective(variables.field_of_view, variables.pixel_width/variables.pixel_height, 0.1, 10000.0)
    glRotatef(self.player.heading[0],1,0,0)
    glRotatef(self.player.heading[1],0,1,0)
    glRotatef(self.player.heading[2],0,0,1)
    glTranslatef(self.get_position()[0],-self.get_position()[2],self.get_position()[1])