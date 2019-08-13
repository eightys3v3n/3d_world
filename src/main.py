#!/bin/python3

import pyglet, cProfile
from game import Game
import sys


def main():
  if len(sys.argv[1:]) > 0:
    if sys.argv[1] == "profile": # Profile the app.
      pyglet.options['debug_gl'] = False
      window = Game()

      try:
        cProfile.runctx('pyglet.app.run()', globals(), locals(), 'main.prof')
      except KeyboardInterrupt: pass
      finally:
        window.on_close()
      return
    elif sys.argv[1] == "debug": # Run in debug mode.
      window = Game()

      try:
        pyglet.app.run()
      except KeyboardInterrupt: pass
      finally:
        window.on_close()

  # Run normally.
  pyglet.options['debug_gl'] = False
  window = Game()

  try:
    pyglet.app.run()
  except KeyboardInterrupt: pass
  finally:
    window.on_close()


if __name__ == "__main__":
  main()
