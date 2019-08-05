import unittest, logging
from time import sleep, time
from queue import Empty as QueueEmpty
import multiprocessing as mp
from world_data import WorldDataServer, WorldDataClient
import config
from block import Block
from chunk import Chunk


class DefaultGeneration:
    name = "Default"

    @classmethod
    def generate(cls, cx, cy, world_client):
        print("Only giving grass blocks in chunk")
        chunk = Chunk()
        for pos in chunk.all_positions():
            if pos[1] < config.WorldDataServer.WorldHeight / 2:
                chunk.set_block(*pos, Block(config.BlockType.Grass))
        return chunk


class WorldGenerator:
    """Controls WorldGeneratorSlaves and handles requesting chunks. An instance of this is held by the main game thread."""
    def __init__(self, world_client, parent_log):
        """Parameters:
            world_client (WorldDataClient): An instance of WorldDataClient that can be used to access the world data.
            parent_log (logging.Logger): The logger that the calling function uses.
        """
        self.__running__ = mp.Value('b', True) # Used to stop any running threads.
        self.parent_log = parent_log
        self.log = self.parent_log.getChild("WorldGenerator")
        self.world_client = world_client # Used to access the world data
        self.chunks_to_generate = mp.Queue(config.WorldGenerator.RequestQueueSize) # A queue of chunks to generate.
        self.recently_requested = {} # dict[(cx, cy)] = time.time(); A list of chunks that have been recently requested and the time requested. These won't be requested again until removed.

        self.generators = []
        for i in range(config.WorldGenerator.Processes):
            response = self.world_client.new_client('WorldGenerator({})'.format(i))
            world_client = response[config.WorldRequestData.NewClient]
            assert isinstance(world_client, WorldDataClient), ""
            self.generators.append(WorldGenerationSlave(self.__running__, world_client, self.log, self.chunks_to_generate))


    def start(self):
        for g in self.generators:
            g.start()


    def stop(self):
        self.__running__.value = False
        for g in self.generators:
            if g.is_alive():
                g.join()


    def garbage_collect_recently_requested(self, *args):
        """Remove any chunk positions in recently_requested that are older than config.WorldGenerator.RecentlyRequested.

        Parameters: Ignores all arguments"""
        self.log.info("Cleaning recently requested")
        for (cx, cy), t in self.recently_requested.items():
            if time() - t >= config.WorldGenerator.RecentlyRequested:
                del self.recently_requested[(cx, cy)]


    def request_chunk(self, cx, cy):
        """If a chunk has not been recently requested (config.WorldGenerator.RecentlyRequested) then request it to be generated.
        Also calls garbage_collect_recently_requested if the size is above maximum.

        Parameters:
            cx (int): The chunk x coordinate of the request
            cy (int): The chunk y coordinate of the request
        """
        if (cx, cy) in self.recently_requested: return
        if len(self.recently_requested) > config.WorldGenerator.MaxRecentChunksStored:
            self.log.warning("Had to clean up recently_requested on main process because size is {}".format(len(self.recently_requested)))
            self.garbage_collect_recently_requested()
        self.recently_requested[(cx, cy)] = time()
        self.chunks_to_generate.put((cx, cy))


    @classmethod
    def pick_generation(cls, cx, cy):
        """To be used in future to pick biomes or such. Currently just gets the DefaultGeneration class."""
        return DefaultGeneration


class WorldGenerationSlave(mp.Process):
    """A slave that is created by WorldGenerator. This class actually does the generation of chunks in separate processes."""
    def __init__(self, running, world_client, parent_log, chunks_to_generate):
        super(WorldGenerationSlave, self).__init__()
        self.chunks_to_generate = chunks_to_generate
        self.world_client = world_client
        self.parent_log = parent_log
        self.__running__ = running


    def run(self):
        while self.__running__.value:
            try:
                (cx, cy) = self.chunks_to_generate.get(timeout=config.WorldGenerator.WaitTime)
            except QueueEmpty: continue

            if self.world_client.is_generated(cx, cy): continue
            generation_type = WorldGenerator.pick_generation(cx, cy)
            chunk = generation_type.generate(cx, cy, self.world_client)
            self.world_client.init_chunk(cx, cy, chunk)


class TestWorldGeneration(unittest.TestCase):
    def setUp(self):
        l = logging.getLogger("TestWorldRenderer")
        fh = logging.FileHandler(config.TestingLog)
        ff = logging.Formatter(config.LogFormat)
        fh.setFormatter(ff)
        l.addHandler(fh)
        l.setLevel(logging.DEBUG)
        self.log = l

        self.world_data = WorldDataServer(self.log)
        self.world_data.start()
        self.world_client = self.world_data.get_main_client()
        self.world_generator = WorldGenerator(self.world_client, self.log)


    def tearDown(self):
        self.world_data.stop()
        self.world_generator.stop()


    def test_request_chunk(self):
        self.world_generator.request_chunk(0, 0)
        self.assertTrue((0, 0) in self.world_generator.recently_requested.keys())
        self.assertEqual((0, 0), self.world_generator.chunks_to_generate.get())


    def test_slave_pickup(self):
        self.world_generator.start()
        self.world_generator.request_chunk(0, 0)
        sleep(1)
        self.assertTrue(self.world_generator.chunks_to_generate.empty())
        self.assertTrue(self.world_client.is_generated(0, 0))

