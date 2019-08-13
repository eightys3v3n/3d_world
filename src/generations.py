from chunk import Chunk
from block import Block
from world_data import WorldDataClient
import unittest
import config
import noise
import time


"""All the generation types, their logic, and the method that returns the generation type to use for any given chunk.
Change this file to change how the world generates or what generation type is used."""


def pick_generation(cx, cy, world_client):
    """This is run for every chunk that is generated. So if you want an entire world of SimplexHeight, always return SimplexHeight. If you want to do something with biomes, store and retrieve the biome from world_client and return the correct world generation class."""
    if cx > 0:
        return SimplexHeight
    else:
        return PerlinHeight


def translate(num, min_in, max_in, min_out, max_out):
    """Given a num in the range(min_in, max_in), translate it to the range(min_out, max_out).
    Example:
        translate(1, 1, 10, 1, 100) == 1
        translate(2, 1, 10, 1, 100) == 20"""
    ret = num - min_in
    ret /= max_in - min_in
    ret *= max_out - min_out
    ret += min_out
    return ret


class Generation:
    """All world generators must be static. IE every method must have the @classmethod. This allows multiple
    generation threads to use it at the same time with no funny consequences."""

    # For the noise algorithms.
    X_SCALE = None # Think "stretch the noise over the x axis this amount. So lots of hills close together or further apart.
    Y_SCALE = None # Same as X_SCALE but for the y axis.
    OCTAVES = None # Imagine 1 creates big rolling hills, 2 creates little hills on those hills, and so on. I think.
    PERSISTENCE = None # No idea.
    MULTIPLIER = None # Just multiply the resulting noise value [0:1] by this number. No idea what this does either.
    DEPTH = None # Generate this many of the top most blocks. This is for performance when testing worlds.

    def __init__(self, parent_log):
        raise NotImplementedError()


    @classmethod
    def generate(self, cx, cy, world_client):
        """This generates the Chunk() at cx, cy and returns it. To access the already generated world data, use world_client."""
        raise NotImplementedError()

class SimplexHeight(Generation):
    """This generation type uses simplex noise to decide on the height of the ground. It then creates a grass only world. See the Generation docstring for documentation on the noise algorithm variables."""
    X_SCALE = 400
    Z_SCALE = 400
    OCTAVES = 4
    PERSISTENCE = 0.5
    MULTIPLIER = 10
    DEPTH = 5 # How many blocks deep to go


    @classmethod
    def column_height(cls, abx, abz):
        """Returns the height of the top block in this column."""
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
        """Gets all the column heights for the chunk."""
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
            lowest = max(0, column_heights[bx, bz]-PerlinHeight.DEPTH)
            for by in range(lowest, column_heights[bx, bz]):
                chunk.set_block(bx, by, bz, Block(config.BlockType.Grass))
        return chunk




class PerlinHeight(Generation):
    """This generation type uses perlin noise to decide on the height of the ground. It then creates a grass only world."""
    X_SCALE = 600
    Z_SCALE = 600
    OCTAVES = 4
    PERSISTENCE = 0.5
    MULTIPLIER = 10
    DEPTH = 5 # How many blocks deep to go


    @classmethod
    def column_height(cls, abx, abz):
        """Returns the height of the top block in this column."""
        n = noise.pnoise3(abx / cls.X_SCALE,
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
        """Gets all the column heights for the chunk."""
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
            lowest = max(0, column_heights[bx, bz]-PerlinHeight.DEPTH)
            for by in range(lowest, column_heights[bx, bz]):
                chunk.set_block(bx, by, bz, Block(config.BlockType.Grass))
        return chunk


class Flat(Generation):
    """Generates a flat world HEIGHT deep made of grass."""
    HEIGHT = 4 # How many blocks deep should we generate.


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

