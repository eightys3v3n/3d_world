import multiprocessing as mp
import unittest


class DefaultGeneration:
    name = "Default"

    @classmethod
    def generate(cls, cx, cy, world_client):
        raise NotImplemented()


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
        self.recently_requested = {} # A list of chunks that have been recently requested and the time requested. These won't be requested again until removed.

        self.generators = []
        for i in range(config.WorldGenerator.Processes):
            world_client = self.world_client.new_client('WorldGenerator({})'.format(i))
            self.generators.append(WorldGenerationSlave(self.__running__, world_client, self.log, self.chunks_to_generate))
        pyglet.clock.schedule_interval(self.garbage_collect_recently_requested, config.WorldGenerator.GarbageCollectionInterval)


    def garbage_collect_recently_requested(self, *args):
        """Remove any chunk positions in recently_requested that are older than config.WorldGenerator.RecentlyRequested.

        Parameters: Ignores all arguments"""
        self.log.info("Cleaning recently requested")
        for (cx, cy), t in self.recently_requested.items():
            if time.time() - t >= config.WorldGenerator.RecentlyRequested:
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
        self.recently_requested[(cx, cy)] = time.time()
        self.chunks_to_generate.put((cx, cy))


    def start(self):
        for g in self.generators:
            g.start()


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
            (cx, cy) = self.chunks_to_generate.get()
            if self.world_client.is_generated(x, y): continue
            generation_type = WorldGenerator.pick_generation(cx, cy)
            chunk = generation_type.generate(cx, cy)
            self.world_client.init_chunk(cx, cy)


class TestWorldGeneration(unittest.TestCase):
    def test_request_chunk(self):
        self.fail()
