import sys
import tests

def Test():
  statuses = []

  # runs every function in the tests file
  for i in dir(tests):
    item = getattr(tests,i)
    # only call functions that end in _Test
    if i[-5:] == "_Test" and callable(item):
      # don't run test if already passed
      if i in statuses:
        continue

      ret = item()
      if ret == False:
        print("\033[92m"+i+" passed\033[0m")
        statuses.append(i)

      elif ret == None:
        print("\033[90m"+i+" has no test\033[0m")

      else:
        print("\033[91m"+i+" failed\033[0m")
        sys.exit(2)

  sys.exit(0)


if __name__ == '__main__':
  Test()