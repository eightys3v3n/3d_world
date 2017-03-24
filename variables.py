from utils  import Position
from time   import time
from random import randint


window_width            = 800
window_height           = 600
maximum_framerate       = 256
max_generation_requests = 100
blocks_per_frame        = 300

cube_size         = 10
field_of_view     = 65.0
mouse_sensitivity = [.2,.2]
view_distance     = 10
player_height     = 2

move_speed    = [2,2,3]
max_fall_speed    = 30
player_fall_acc   = Position(x=0.0, y=0.0, z=-3.0)
physics_updates   = 1/10.0

seed              = randint(0,10000000)

# terrain height generation
x_scale = 70
y_scale = 70
z_min = -20
z_max = 20
octaves = 10
persistence = .5
lacunarity = 2.0
repeatx = 1024.0
repeaty = 1024.0
base = z_min

block = {
  "grass":1,
  "stone":2
  }

block_colour = {
  block["grass"]:(
    # top
    0,255,0,0,255,0,
    0,255,0,0,255,0,
    # front
    139,69,19,139,69,19,
    139,69,19,139,69,19,
    # bottom
    139,69,19,139,69,19,
    139,69,19,139,69,19,
    # left
    139,69,19,139,69,19,
    139,69,19,139,69,19,
    # back
    139,69,19,139,69,19,
    139,69,19,139,69,19,
    # right
    139,69,19,139,69,19,
    139,69,19,139,69,19
    ),
  block["stone"]:(
    # top
    175,175,175,175,175,175,
    175,175,175,175,175,175,
    # front
    175,175,175,175,175,175,
    175,175,175,175,175,175,
    # bottom
    175,175,175,175,175,175,
    175,175,175,175,175,175,
    # left
    175,175,175,175,175,175,
    175,175,175,175,175,175,
    # back
    175,175,175,175,175,175,
    175,175,175,175,175,175,
    # right
    175,175,175,175,175,175,
    175,175,175,175,175,175
    )
}