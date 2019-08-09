import config, unittest, itertools
from collections import defaultdict
from block import Block
from hashlib import sha3_512


def default_block():
    return Block(config.BlockType.Empty)


class Chunk:
    def __init__(self):
        self.__blocks__ = defaultdict(default_block) # {(x, y, z): Block()}
        self.__generated__ = False


    def __eq__(self, other):
        if not isinstance(other, Chunk): return False
        return self.__blocks__ == other.__blocks__


    def __repr__(self):
        return self.__str__()


    def __str__(self):
        h = sha3_512()
        for p, b in self.__blocks__.items():
            h.update((p, b).__str__().encode())
        h = h.hexdigest()[0:config.WorldDataServer.ChunkHexLength]
        return "Chunk: {}".format(h)


    def __iter__(self):
        """Using `for p, b in Chunk()` will result in p being the position of a given chunk, and b being the block object for that position."""
        for pos, block in self.__blocks__.items():
            yield (pos, block)


    @classmethod
    def all_positions(cls):
        for bx, by, bz in itertools.product(range(config.WorldDataServer.ChunkSize),
                                            range(config.WorldDataServer.WorldHeight),
                                            range(config.WorldDataServer.ChunkSize)):
            yield (bx, by, bz)


    @classmethod
    def all_columns(cls):
        for bx, bz in itertools.product(range(config.WorldDataServer.ChunkSize),
                                        range(config.WorldDataServer.ChunkSize)):
            yield (bx, bz)


    @classmethod
    def __check_position__(cls, bx, by, bz):
        if not 0 <= bx < config.WorldDataServer.ChunkSize:
            raise ValueError("X coordinate must be > 0 and < {}, not {}".format(config.WorldDataServer.ChunkSize, bx))
        if not 0 <= by < config.WorldDataServer.WorldHeight+1:
            raise ValueError("Y coordinate must be > 0 and < {}, not {}".format(config.WorldDataServer.WorldHeight, by))
        if not 0 <= bz < config.WorldDataServer.ChunkSize:
            raise ValueError("Z coordinate must be > 0 and < {}, not {}".format(config.WorldDataServer.ChunkSize, bz))



    def get_block(self, x, y, z):
        Chunk.__check_position__(x, y, z)
        return self.__blocks__[(x, y, z)]


    def set_block(self, x, y, z, block):
        if not self.__generated__:
            self.__generated__ = True

        Chunk.__check_position__(x, y, z)
        if not isinstance(block, Block):
            raise TypeError("Must be a Block object")
        self.__blocks__[(x, y, z)] = block


    def get_column(self, bx, by):
        column = {}
        for (bx1, by1, bz1), b in self:
            if (bx, by) == (bx1, by1):
                column[(bx1, by1, bz1)] = b
        return column


    def is_generated(self):
        return self.__generated__



class TestChunk(unittest.TestCase):
    def test_iterable(self):
        chunk = Chunk()
        chunk.set_block(0, 0, 0, Block(config.BlockType.Grass))
        chunk.set_block(0, 1, 0, Block(config.BlockType.Grass))
        for p, b in chunk:
            self.assertIn(p, ((0, 0, 0), (0, 1, 0)))
            self.assertIsInstance(b, Block)
            self.assertEqual(b, Block(config.BlockType.Grass))

    def test_check_position(self):
        with self.assertRaises(ValueError):
            Chunk.__check_position__(-1, 0, 0)
            Chunk.__check_position__(0, -1, 0)
            Chunk.__check_position__(0, 0, -1)
            Chunk.__check_position__(config.WorldDataServer.ChunkSize, 0, 0)
            Chunk.__check_position__(0, config.WorldDataServer.WorldHeight, 0)
            Chunk.__check_position__(0, 0, config.WorldDataServer.ChunkSize)
        t = None
        try:
            t = (0, 0, 0)
            Chunk.__check_position__(*t)

            t = (1, 0, 0)
            Chunk.__check_position__(*t)

            t = (0, 1, 0)
            Chunk.__check_position__(*t)

            t = (0, 0, 1)
            Chunk.__check_position__(*t)

            t = (config.WorldDataServer.ChunkSize-1, 0, 0)
            Chunk.__check_position__(*t)

            t = (0, config.WorldDataServer.WorldHeight-1, 0)
            Chunk.__check_position__(*t)

            t = (0, 0, config.WorldDataServer.ChunkSize-1)
            Chunk.__check_position__(*t)
        except:
            self.fail("__check_position__ failed the valid position {}".format(t))


    def test_equals(self):
        a = Chunk()
        b = Chunk()
        self.assertEqual(a, b)
        a.__blocks__[(0, 0, 0)] = Block(config.BlockType.Grass)
        self.assertNotEqual(a, b)


    def test_setget(self):
        chunk = Chunk()
        block = Block(config.BlockType.Grass)
        chunk.set_block(0, 0, 0, block)
        res = chunk.get_block(0, 0, 0)
        self.assertEqual(block, res)
        res= chunk.get_block(1, 1, 1)
        self.assertNotEqual(block, res)


    def test_get_column(self):
        orig = config.WorldDataServer.WorldHeight
        config.WorldDataServer.WorldHeight = 3

        try:
            chunk = Chunk()
            r = range(0, config.WorldDataServer.WorldHeight)
            for (x, y, z) in itertools.product(r, r, r):
                chunk.set_block(x, y, z, Block(config.BlockType.Grass))
                column = chunk.get_column(0, 0)

            self.assertEqual(len(column.keys()), config.WorldDataServer.WorldHeight, column.__str__())
            corr = {
                (0, 0, 0): Block(config.BlockType.Grass),
                (0, 0, 1): Block(config.BlockType.Grass),
                (0, 0, 2): Block(config.BlockType.Grass),
            }
            self.assertEqual(column, corr)
        finally:
            config.WorldDataServer.WorldHeight = orig


    def test_all_positions(self):
        all_positions = list(Chunk.all_positions())
        corr = []
        for x in range(config.WorldDataServer.ChunkSize):
            for y in range(config.WorldDataServer.WorldHeight):
                for z in range(config.WorldDataServer.ChunkSize):
                    corr.append((x, y, z))
        self.assertCountEqual(corr, all_positions)
