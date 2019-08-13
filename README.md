# 3D World
This is a project created so I can experiment with and learn about multiprocessing, pyglet, and world generation in Python.  

Currently it has a working world generator (think Minecraft) using Perlin or Simplex noise.
The world generator, world renderer, and world data storage are all running in separate processes.
I would have used threads, except I have read that threads in Python are not the same as in other languages.
In Python only one thread can have the interpreter lock at a time, thus it's not really multithreaded in the same way C++ is.  

# Get this running:
```
pip install -r requirements.txt
cd src/
python main.py
```

# Stuff to know:
- The controls are WASD and the mouse. Just click in the window to capture the mouse; escape to let the mouse go. Scroll up and down to go faster or slower. Plus and Minus are used to increase and decrease the number of blocks that can be drawn in a single frame. Decrease if the game runs slow or stuttery.
- All the configuration options and settings are in config.py and variables.py.
(variables.py needs to be moved into config.py and I am slowly doing that as I use the values)
- All the different world generation types will be inside generations.py. To change the one being used, return the type you want in the `pick_generation` method. All generation types should follow the `Generation` class as a template.

# References:
## Positions:
### Chunk:Block
A chunk:block position is composed of a (cx, cy) for the chunk's x and y position. As well as a (bx, by, bz) for a block inside that chunk. The block positions are relative to the chunks SW corner and increase to the NE. by is the up and down, bx and bz are north/south and east/west.
### Absolute Block
An absolute block position (abx, aby, abz) is a block's position relative to the (0, 0, 0) block in the world.
### Examples
- Chunk:Block of this converts to Absolute Block of this; if the ChunkSize is 16 blocks.
- (0, 0):(1, 1, 1) -> (1, 1, 1)
- (1, 1):(0, 0, 0) -> (16, 0, 16)
