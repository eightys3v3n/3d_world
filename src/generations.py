from chunk import Chunk
from block import Block
from world_data import WorldDataClient
import unittest
import config
import noise


def pick_generation(cx, cy, world_client):
    return PerlinHeight


def translate(num, min_in, max_in, min_out, max_out):
    """Given a num in the range(min_in, max_in), translate it to the range(min_out, max_out)."""
    ret = num - min_in
    ret /= max_in - min_in
    ret *= max_out - min_out
    ret += min_out
    return ret


class Generation:
    def __init__(self, parent_log):
        raise NotImplementedError()


    def generate(self, cx, cy, world_client):
        """This generates the chunk at cx, cy and returns it."""
        raise NotImplementedError()


class PerlinHeight(Generation):
    """This generation type uses perlin noise to decide on the height of the ground. It then creates a grass only world."""
    X_SCALE = 400
    Z_SCALE = 400
    OCTAVES = 5
    PERSISTENCE = 0.5
    MULTIPLIER = 10


    @classmethod
    def column_height(cls, abx, abz):
        n = noise.snoise3(abx / cls.X_SCALE,
                          abz / cls.Z_SCALE,
                          config.WorldGenerator.Seed,
                          octaves=cls.OCTAVES,
                          persistence=cls.PERSISTENCE)
        n *= cls.MULTIPLIER
        n = translate(n, 0, cls.MULTIPLIER, 0, config.WorldDataServer.WorldHeight)
        height = round(n)
        return height


    @classmethod
    def column_heights(cls, cx, cy):
        column_heights = {}
        for bx, bz in Chunk.all_columns():
            abx, _, abz = WorldDataClient.chunk_block_to_abs_block(cx, cy, bx, 0, bz)
            h = cls.column_height(abx, abz)
            if h > config.WorldDataServer.WorldHeight:
                print("Generator returned an invalid world height.")
            column_heights[(bx, bz)] = h
        return column_heights


    @classmethod
    def generate(cls, cx, cy, world_client):
        chunk = Chunk()
        column_heights = cls.column_heights(cx, cy)

        for bx, bz in chunk.all_columns():
            for by in range(0, column_heights[bx, bz]):
                chunk.set_block(bx, by, bz, Block(config.BlockType.Grass))
        return chunk


class Flat(Generation):
    HEIGHT = 4


    @classmethod
    def generate(cls, cx, cy, world_client):
        chunk = Chunk()
        for bx, bz in chunk.all_columns():
            for by in range(cls.HEIGHT):
                chunk.set_block(bx, by, bz, Block(config.BlockType.Grass))
        return chunk



class TestTranslate(unittest.TestCase):
    def test_translate(self):
        tests = [
            ((0, 0, 4, 0, 40), 0),
            ((1, 0, 4, 0, 40), 10),
            ((2, 0, 4, 0, 40), 20),
            ((3, 0, 4, 0, 40), 30),
            ((4, 0, 4, 0, 40), 40),

            ((0, 0, 10, 0, 100), 0),
            ((1, 0, 10, 0, 100), 10),
            ((5, 0, 10, 0, 100), 50),
            ((9, 0, 10, 0, 100), 90),
            ((10, 0, 10, 0, 100), 100),
            ]

        for inp, corr in tests:
            ret = translate(*inp)
            self.assertEqual(corr, ret, "Test failed: {}\nShould be {}, not {}.".format(inp, corr, ret))

