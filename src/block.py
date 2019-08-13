import config, unittest


class Block():
  """A single voxel in the world and it's type."""
  def __init__(self, block_type=None):
    if not isinstance(block_type, config.BlockType):
      raise ValueError("Invalid block type {}".format(block_type))
    self.block_type = block_type

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    return str("A block of type {}".format(self.block_type))

  def __eq__(self, other):
    if not isinstance(other, Block): return False
    return self.block_type == other.block_type


class TestBlock(unittest.TestCase):
  def test_equals(self):
    a = Block(config.BlockType.Grass)
    b = Block(config.BlockType.Empty)
    self.assertNotEqual(a, b)
    b = Block(config.BlockType.Grass)
    self.assertEqual(a, b)
