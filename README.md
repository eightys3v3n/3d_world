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

To profile the application using cProfile, `python main.py profile`
To debug the application use `python main.py debug`

# Stuff to know:
- The controls are WASD and the mouse. Just click in the window to capture the mouse; escape to let the mouse go. Scroll up and down to go faster or slower. Plus and Minus are used to increase and decrease the number of blocks that can be drawn in a single frame. Decrease if the game runs slow or stuttery.
- All the configuration options and settings are in config.py and variables.py.
(variables.py needs to be moved into config.py and I am slowly doing that as I use the values)
- All the different world generation types will be inside generations.py. To change the one being used, return the type you want in the `pick_generation` method. All generation types should follow the `Generation` class as a template.
- For some programming references and explanations, see [references.md](docs/references.md)
