#!/bin/python3

import pyglet, cProfile
from game import Game


# don't know how to use debugging; also suppose to increase performance when it's off
pyglet.options['debug_gl'] = False


def main():
  window = Game()

  try:

    cProfile.runctx('pyglet.app.run()', globals(), locals(), 'main.prof')
    #pyglet.app.run()
  except KeyboardInterrupt:
    pass
  finally:
    window.on_close()

if __name__ == "__main__":
  main()
