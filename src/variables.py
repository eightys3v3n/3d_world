from utils  import Position
from time   import time
from random import randint


window_width            = 1280
window_height           = 1024
maximum_framerate       = 256
max_generation_requests = 100
vsync                   = True

class player:
    initial_position = [0.0, 0.0, 0.0]
    initial_heading  = [90.0, 0.0, 0.0]
    height = 2
    class debug:
        # Whether to print the players position on player move
        print_player_position = True

        # Whether to print the players heading on change
        print_player_heading = False

class world:
    # Creates a grass block at the player's start position
    create_reference_block = True

class renderer:
    blocks_drawn_per_frame = 1000

cube_size         = 10
field_of_view     = 65.0
mouse_sensitivity = [.2,.2]

# Number of blocks away from player to generate. Generates 40 blocks -x, +x, -z, +z
generate_distance = 10

move_speed    = [0.1, 0.1, 0.1]
max_fall_speed    = 30
player_fall_acc   = Position(x=0.0, y=0.0, z=-5.0)
physics_updates   = 1/30.0

# terrain height generation
class generator:
    # Whether to generate a large area around the player when starting
    generate_reference_area = True

    reference_area = [-50, -50, 50, 50]
    seed = 1123
    x_scale = 400
    y_scale = 400
    z_min = -20
    z_max = 20

    # the amount of detail?
    octaves = 10

    persistence = .5
    lacunarity = 5.0
    repeatx = 1024.0
    repeaty = 1024.0
    base = z_min
    class debug:
        print_requested_columns = True

class debug:
    print_move_speed = True
    # Unload all blocks once this is reached. This was a temporary fix for a crashing bug on my computer. Set to None to never unload all blocks.
    max_blocks              = None

# types of blocks and their colours
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
