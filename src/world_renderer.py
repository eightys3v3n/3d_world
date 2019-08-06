import pyglet
from pyglet.gl import *
import multiprocessing as mp
import queue, pyglet, time, unittest, logging
import multiprocessing as mp
import config, world_data
import time


class WorldRenderer(mp.Process):
    def __init__(self, world_client, parent_log):
        super(WorldRenderer, self).__init__()
        self.parent_log = parent_log
        self.log = self.parent_log.getChild("WorldRenderer")
        self.log.setLevel(config.WorldRenderer.LogLevel)
        self.world_client = world_client
        self.chunks_to_render = mp.Queue(config.WorldRenderer.MaxQueuedChunks)
        self.rendered_chunks = {} # (cx, cy): pyglet.graphics.Batch to draw
        self.recently_requested = {} # (cx, cy): time requested
        self.finished_chunks = mp.Queue(maxsize=config.WorldRenderer.MaxFinishedChunks)
        self.__running__ = mp.Value('b', False)


    def start(self, *args, **kwargs):
        super(WorldRenderer, self).start(*args, **kwargs)
        self.__running__.value = True


    def stop(self):
        self.__running__.value = False
        if self.is_alive():
            self.join()


    def render_block_to_batch(self, pos, block, batch):
        indexes, vertices = self.block_vertices(*pos, block)
        colours = self.block_colour(block).value

        data = (len(indexes), GL_QUADS, None, indexes, ("v3f", vertices), ("c3B", colours))
        try:
            assert len(vertices) == len(colours) == 72, "{} != {}".format(len(vertices), len(colours))
            batch.add_indexed(*data)
        except Exception  as e:
            self.log.error(e)
            self.log.debug(data)
            raise Exception(e)


    def render_block_to_data(self, pos, block, batch_data):
        indexes, vertices = self.block_vertices(*pos, block)
        colours = self.block_colour(block).value

        data = (len(indexes), GL_QUADS, None, indexes, ("v3f", vertices), ("c3B", colours))
        batch_data.append(data)


    def is_rendered(self, cx, cy):
        if (cx, cy) in self.rendered_chunks: return True
        return False


    def request_chunk(self, cx, cy, force=False):
        if not force and (cx, cy) in self.recently_requested:
            time_since = time.time() - self.recently_requested[(cx, cy)]
            if time_since < config.WorldRenderer.RecentlyRequestedTimeout:
                self.log.debug("Ignoring chunk ({}, {})".format(cx, cy))
                return
        self.log.info("Requesting chunk ({}, {})".format(cx, cy))
        self.recently_requested[(cx, cy)] = time.time()
        self.chunks_to_render.put((cx, cy))


    def render_chunk(self, cx, cy):
        raise Exception("Can't be used with a multiprocess structure")
        if not self.world_client.is_generated(cx, cy):
            self.log.info("Requested chunk isn't generated ({}, {})".format(cx, cy))
            return

        batch = pyglet.graphics.Batch()
        chunk = self.world_client.get_chunk(cx, cy)
        self.log.info("Rendering chunk ({}, {})".format(cx, cy))
        if config.WorldRequestData.ChunkData not in chunk:
            self.log.warning("Didn't receive chunk data, queuing for later.")
            self.log.debug("Actually received: {}".format(chunk))
            self.request_chunk(cx, cy)
            return
        chunk = chunk[config.WorldRequestData.ChunkData]
        for pos, block in chunk:
            pos = self.world_client.chunk_block_to_abs_block(cx, cy, *pos)
            self.log.debug("Rendering block ({}, {}, {}) of type {}".format(*pos, block))
            self.render_block_to_batch(pos, block, batch)
        self.log.debug("Rendered chunk ({}, {})".format(cx, cy))
        self.rendered_chunks[(cx, cy)] = batch


    def render_chunk_data(self, cx, cy):
        if self.world_client.is_generated(cx, cy):
            batch_data = []

            chunk = self.world_client.get_chunk(cx, cy)
            self.log.debug("Rendering chunk ({}, {})".format(cx, cy))
            if config.WorldRequestData.ChunkData not in chunk:
                self.log.warning("Didn't receive chunk data, queuing for later.")
                self.log.debug("Actually received: {}".format(chunk))
                self.request_chunk(cx, cy)
                return
            chunk = chunk[config.WorldRequestData.ChunkData]

            for pos, block in chunk:
                pos = self.world_client.chunk_block_to_abs_block(cx, cy, *pos)
                self.log.debug("Rendering block ({}, {}, {}) of type {}".format(*pos, block))
                self.render_block_to_data(pos, block, batch_data)
            self.log.debug("Rendered chunk ({}, {})".format(cx, cy))
            self.finished_chunks.put(((cx, cy), batch_data))
        else:
            self.log.info("Requested chunk isn't generated ({}, {})".format(cx, cy))


    def load_finished_chunks(self):
        """Create batches for all the chunks whose data was asynchronously calculated.
        Then add those batches to the list of batches to be drawn."""
        loaded = 0

        while True:
            try:
                (cx, cy), data = self.finished_chunks.get(block=False)
                batch = pyglet.graphics.Batch()
                for block_data in data:
                    batch.add_indexed(*block_data)
                self.rendered_chunks[(cx, cy)] = batch
                loaded += 1
            except queue.Empty: break
        if loaded > 0:
            self.log.info("Loaded {} finished chunks.".format(loaded))


    def timeout_recently_requested(self):
        """Removes all recently made requests that are older than their timeout."""
        for (cx, cy), t in self.recently_requested.items():
            if time.time() - t >= config.WorldRenderer.RecentlyRequestedTimeout:
                del self.recently_requested[(cx, cy)]


    def draw(self):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        for (cx, cy), batch in self.rendered_chunks.items():
            #self.log.info("Drawing chunk ({}, {})".format(cx, cy))
            batch.draw()


    def run(self):
        while self.__running__.value:
            try:
                cx, cy = self.chunks_to_render.get(timeout=config.WorldRenderer.WaitTime)
                self.log.info("Received chunk render request for ({}, {})".format(cx, cy))
                self.render_chunk_data(cx, cy)
            except queue.Empty: pass
            self.timeout_recently_requested()


    def block_colour(self, block):
       return config.BlockColour[block.block_type.value]


    def block_vertices(self, x, y, z, block):
        """Returns the vertices index and the actual screen vertices for a cube, in the correct order."""
        n = config.World.VoxelSize
        x = x*n*2
        y = y*n*2
        z = z*n*2
        return (tuple(range(24)), (
            # top
            x-n,y+n,z+n,
            x+n,y+n,z+n,
            x+n,y+n,z-n,
            x-n,y+n,z-n,
            # front
            x-n,y-n,z+n,
            x+n,y-n,z+n,
            x+n,y+n,z+n,
            x-n,y+n,z+n,
            # bottom
            x-n,y-n,z-n,
            x+n,y-n,z-n,
            x+n,y-n,z+n,
            x-n,y-n,z+n,
            # left
            x-n,y+n,z+n,
            x-n,y+n,z-n,
            x-n,y-n,z-n,
            x-n,y-n,z+n,
            # back
            x-n,y+n,z-n,
            x+n,y+n,z-n,
            x+n,y-n,z-n,
            x-n,y-n,z-n,
            # right
            x+n,y-n,z+n,
            x+n,y-n,z-n,
            x+n,y+n,z-n,
            x+n,y+n,z+n))


class TestWorldRenderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        l = logging.getLogger("TestWorldRenderer")
        fh = logging.FileHandler(config.TestingLog)
        ff = logging.Formatter(config.LogFormat)
        fh.setFormatter(ff)
        l.addHandler(fh)
        l.setLevel(logging.DEBUG)
        cls.log = l


    def setUp(self):
        self.world_server = world_data.WorldDataServer(self.log)
        self.world_client = self.world_server.get_main_client()
        self.renderer = WorldRenderer(self.world_client, self.log)
        self.world_server.start()


    def tearDown(self):
        self.world_server.stop()
        self.world_server.join()


    def test_block_vertices(self):
        # No idea how to test this since they are hardcoded. :/
        pass


    def test_render_chunk(self):
        return
        self.renderer.render_chunk(0, 0)

        for pos, batch in self.renderer.rendered_chunks.items():
            if pos == (0, 0):
                break
        else:
            self.fail("Renderer didn't load chunk (0, 0)")
