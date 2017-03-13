import os,sys,queue,traceback
from time import sleep
import generator,world,player


statuses = {}


def func_name():
  return traceback.extract_stack(None,2)[0][2]


def World_Test():
  if func_name() in statuses:
    return False

  return None

  statuses[func_name()] = True
  return False


def Generator_Test():
  if func_name() in statuses:
    return False

  w = world.World()
  q = queue.Queue()
  g = generator.Generator(w,q)
  sleep(0.1)

  if not g.thread.is_alive():
    print("generator thread didn't start in time")
    return True

  q.put((0,0,0))
  sleep(0.1)

  if not q.empty():
    print("generator didn't empty the queue in time")
    return True

  if not w.block_exists(0,0,0):
    print("generator didn't generate a block in time")
    return True

  g.stop()

  statuses[func_name()] = True
  return False


def Player_Test():
  if func_name() in statuses:
    return False

  p = player.Player()
  p.move(1,0,0)
  if p.position != [1.0,0.0,0.0]:
    print("player moved incorrectly in x")
    return True

  p.position = [0.0,0.0,0.0]
  p.move(0,1,0)
  if p.position != [0.0,1.0,0.0]:
    print("player moved incorrectly in y")
    return True

  p.position = [0.0,0.0,0.0]
  p.move(0,0,1)
  if p.position != [0.0,0.0,1.0]:
    print("player moved incorrectly in z")
    return True

  p.position = [0.0,0.0,0.0]
  p.move(1,1,0)
  if p.position != [1.0,1.0,0.0]:
    print("player moved incorrectly in x,y",p.position)
    return True

  p.position = [0.0,0.0,0.0]
  p.heading = [0.0,45.0,0.0]
  p.move(1,1,1)
  p.position[2] = round(p.position[2],3)
  if p.position != [0.0,1.0,1.414]:
    print("player moved incorrectly in x,z",p.position)
    return True

  p.position = [0.0,0.0,0.0]
  p.heading = [0.0,45.0,0.0]
  p.move(1,1,0)
  p.position[0] = round(p.position[0],3)
  p.position[2] = round(p.position[2],3)
  if p.position != [0.707,1.0,0.707]:
    print("player moved incorrectly for 1,1,0 @ 45",p.position)
    return True

  p.position = [0.0,0.0,0.0]
  p.heading = [0.0,10.0,0.0]
  p.move(1,1,1)
  p.position[0] = round(p.position[0],3)
  p.position[2] = round(p.position[2],3)
  if p.position != [0.811,1.0,1.159]:
    print("player moved incorrectly for 1,1,1 @ 10",p.position)
    return True

  p.heading = [0.0,0.0,0.0]
  p.look(1,0)
  if p.heading != [1.0,0.0,0.0]:
    print("player looked incorrectly for 1,0",p.heading)
    return True

  p.heading = [0.0,0.0,0.0]
  p.look(3,8)
  if p.heading != [3.0,8.0,0.0]:
    print("player looked incorrectly for 3,8",p.heading)
    return True

  p.heading = [0.0,0.0,0.0]
  p.look(180,370)
  if p.heading != [90.0,10.0,0.0]:
    print("player looked incorrectly for 180,370",p.heading)
    return True

  statuses[func_name()] = True
  return False


def PlayerManager_Test():
  if func_name() in statuses:
    return False

  p = player.PlayerManager()

  p.player.position = [0.0,0.0,0.0]
  if p.get_position() != [0.0,0.0,0.0]:
    print("get position returned wrong for 0,0,0",p.get_position())
    return True

  p.player.heading = [0.0,0.0,0.0]
  p.look(10,1)
  if p.player.heading != [10.0,1.0,0.0]:
    print("player manager looked wrong for 10,1",p.player.heading)
    return True

  p.player.position = [0.0,0.0,0.0]
  p.player.heading = [0.0,0.0,0.0]
  p.move(1,2)
  if p.get_position() != [1.0,0.0,2.0]:
    print("player manager moved wrong for 1,2",p.get_position())
    return True

  p.player.position = [0.0,0.0,0.0]
  p.player.heading = [10.0,0.0,0.0]
  p.move(1,2)
  if p.get_position() != [1.0,0.0,2.0]:
    print("player manager moved wrong for 1,2 @ 10,0",p.get_position())
    return True

  statuses[func_name()] = True
  return False


def _Test():
  if func_name() in statuses:
    return False

  # test

  statuses[func_name()] = True
  return False