from pyglet.gl import *
import config
from math import cos,hypot,degrees,radians,sin,atan2
import variables, utils
from variables import window_height, window_width, cube_size


def legacy_get_abs_block_pos(player_pos):
  x = -player_pos[0]/config.World.VoxelSize/2
  y = -player_pos[1]/config.World.VoxelSize/2
  z = player_pos[2]/config.World.VoxelSize/2
  x = round(x)
  y = round(y)
  z = round(z)
  return (x, y, z)


def legacy_get_top_block_height(world_client, abx, aby):
  """Returns the height of the top most block at the given absolute block position in the world."""
  (cx, cy), (bx, by) = WorldDataClient.abs_block_to_chunk_block(abx, aby)
  chunk = world_client.get_chunk(cx, cy)
  column = chunk.get_column(bx, by)
  column = list(column.items())
  column.sort(reverse=True)
  return column[0][2]


class Player:
  def __init__(self):
    self.position = variables.player.initial_position
    self.current_block = [0, 0, 0]
    self.heading = variables.player.initial_heading
    self.visible = [0, 0, 0, 0]
    self.height  = variables.player.height


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
  def __init__(self, world):
    self.player = Player()
    self.world = world
    self._flying = True
    self.velocity = utils.Position(0, 0, 0)
    self.can_jump = True
    self.prev = utils.Position(0, 0, 0)


  def flying(self, status=None):
    if status is None:
      status = not self._flying

    if status:
      self.velocity.z = 0
      self._flying = True

    else:
      self._flying = False


  def get_position(self):
    return self.player.position


  def look(self,x,y):
    self.player.look(x,y)

    if variables.player.debug.print_player_heading:
      self.print_heading()


  def move(self, x=0.0, y=0.0, z=0.0):
    if not x and not y and not z:
      return

    if abs(x) > variables.move_speed[0]:
      x = variables.move_speed[0] * x/-x
    if abs(y) > variables.move_speed[1]:
      y = variables.move_speed[1] * y/-y
    if abs(z) > variables.max_fall_speed:
      z = variables.max_fall_speed * z/-z

    if self._flying:
      self.player.move(x,y,z)
    else:
      self.player.move(x,y,z)

    if variables.player.debug.print_player_position:
      self.print_position()
      self.print_standing_on()


  def print_heading(self):
    x = round(self.player.heading[0], 4)
    y = round(self.player.heading[1], 4)

    s = 'Player heading: {:0< 6.4f}, {:0> 6.4f}'.format(x, y)
    print(s)


  def print_position(self):
    x = round(self.player.position[0] / cube_size, 4)
    y = round(self.player.position[1] / cube_size, 4)
    z = round(self.player.position[2] / cube_size, 4)

    s = 'Player Position: {:0< 6.4f}, {:0^ 6.4f}, {:0> 6.4f}'.format(x, y, z)
    print(s)


  def print_standing_on(self):
    x = round(self.standing_on()[0], 4)
    y = round(self.standing_on()[1], 4)
    z = round(self.standing_on()[2], 4)

    s = 'Player standing on: {:0< 6.4f}, {:0^ 6.4f}, {:0> 6.4f}'.format(x, y, z)
    print(s)


  def jump(self):
    if self.can_jump:
      self.velocity.z += 7
      self.can_jump = False
      print("jump")

    else:
      print("can't jump")

    self.print_position()


  def standing_on(self):
    return [self.player.current_block[0],
            self.player.current_block[2],
            self.player.current_block[1],]


  def set_standing_on(self, new_block_pos):
    """Returns a rectangle of what should be drawn."""
    self.player.current_block = new_block_pos
    #self.player.visible = [x,y,x1,y1]


  def get_visible(self):
    return self.player.visible


  def update_physics(self, dt):
    """
    suppose to make the player fall to the ground if they aren't flying
    """
    self.set_standing_on(legacy_get_abs_block_pos(self.player.position))

    if not self._flying:
      # get the highest block in the x,z that the player is in.
      # should actually be 'get the highest block below the player'
      top_block_height = legacy_get_top_block_height(self.world_client, *self.standing_on())

      if top_block_height != None:                          # if there is a block in x, z
        if self.standing_on()[2] > top_block_height+self.player.height:    # if the player is above the top block
          print("Falling!")
          self.velocity += variables.player_fall_acc
          self.can_jump = False
          #self.move(variables.fall_speed.x, variables.fall_speed.y, variables.fall_speed.z)     # should move the player down

        elif self.standing_on()[2] == top_block_height+self.player.height:
          if self.velocity.z < 0:
            print("standing on the ground, resetting down velocity")
            self.velocity.z = 0
          self.can_jump = True

        else:
          print("standing in the ground, raising to surface")
          self.can_jump = True
          self.player.move(0, 0, cube_size*2)
          self.velocity.z = 0

    if self.prev != self.velocity:
      self.prev = self.velocity
      print("velocity ", self.velocity)

    self.move(self.velocity.x, self.velocity.y, self.velocity.z)


  def draw_perspective(self):
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluPerspective(config.Player.FOV, config.Window.Width/config.Window.Height, 0.1, 10000.0)
    glRotatef(self.player.heading[0],1,0,0)
    glRotatef(self.player.heading[1],0,1,0)
    glRotatef(self.player.heading[2],0,0,1)
    glTranslatef(self.get_position()[0],-self.get_position()[2],self.get_position()[1])
