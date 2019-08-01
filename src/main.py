#!/bin/python3

import pyglet
from game import Game


# don't know how to use debugging; also suppose to increase performance when it's off
pyglet.options['debug_gl'] = False


def main():
  window = Game()

  try:
    pyglet.app.run()
  except KeyboardInterrupt:
    pass
  finally:
    window.quit()

if __name__ == "__main__":
  main()
