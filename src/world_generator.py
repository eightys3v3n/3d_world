import multiprocessing as mp


class DefaultGeneration:
    name = "Default"

    @classmethod
    def generate(cls, cx, cy, world_client):
        raise NotImplemented()


class WorldGenerator:
    def __init__(self, world_client, parent_log):
        self.__running__ = mp.Value('b', True)
        self.parent_log = parent_log
        self.log = self.parent_log.getChild("WorldGenerator")
        self.world_client = world_client
        self.chunks_to_generate = mp.Queue(config.WorldGenerator.RequestQueueSize)
        self.recently_requested = {}

        self.generators = []
        for i in range(config.WorldGenerator.Processes):
            world_client = self.world_client.new_client('WorldGenerator({})'.format(i))
            self.generators.append(WorldGenerationSlave(self.__running__, world_client, self.log, self.chunks_to_generate))
        pyglet.clock.schedule_interval(self.garbage_collect_recently_requested, config.WorldGenerator.GarbageCollectionInterval)


    def garbage_collect_recently_requested(self, *args):
        self.log.info("Cleaning recently requested")
        for (cx, cy), t in self.recently_requested.items():
            if time.time() - t >= config.WorldGenerator.RecentlyRequested:
                del self.recently_requested[(cx, cy)]


    def request_chunk(self, cx, cy):
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
        return DefaultGeneration


class WorldGenerationSlave(mp.Process):
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
