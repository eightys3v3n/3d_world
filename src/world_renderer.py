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
        self.world_client = world_client
        self.chunks_to_render = mp.Queue(config.WorldRenderer.MaxQueuedChunks)
        self.rendered_chunks = {}
        self.rendered_chunks_to_add = mp.Queue(config.WorldRenderer.MaxQueuedChunks)
        self.__running__ = mp.Value('b', True) # Carry over because I planned to make this a seperate process.
        self.last_chunk = ((None, None), 0) # Is ((cx, cy), time.time())


    def start(self, *args, **kwargs):
        """Start the server and log that it has started."""
        super(WorldRenderer, self).start(*args, **kwargs)
        self.log.info("WorldRenderer is started.")


    def stop(self, *args, **kwargs):
        self.log.info("WorldRenderer is stopping.")
        self.__running__.value = False
        self.join()
        self.log.info("WorldRenderer stopped.")


    def chunk_is_rendered(self, x, y):
        for p, _ in self.rendered_chunks:
            if (x, y) == p:
                return True
        return False


    def request_chunk(self, cx, cy):
        if (cx, cy) != self.last_chunk[0] or time.time() - self.last_chunk[1] > 2:
            if not self.chunk_is_rendered(cx, cy):
                self.log.info("Requesting chunk to be rendered ({}, {})".format(cx, cy))
                self.chunks_to_render.put((cx, cy))
                self.last_chunk = ((cx, cy), time.time())



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


    def render_block_to_batch_data(self, pos, block, batch_data):
        indexes, vertices = self.block_vertices(*pos, block)
        colours = self.block_colour(block).value

        data = (len(indexes), GL_QUADS, None, indexes, ("v3f", vertices), ("c3B", colours))
        batch_data.append(data)


    def is_rendered(self, cx, cy):
        if (cx, cy) in self.rendered_chunks: return True
        return False


    def render_chunk(self, cx, cy):
        if not self.world_client.is_generated(cx, cy):
            self.log.info("Requested chunk isn't generated ({}, {})".format(cx, cy))
            return

        batch = pyglet.graphics.Batch()
        chunk = self.world_client.get_chunk(cx, cy)
        self.log.debug("Rendering chunk ({}, {})".format(cx, cy))
        if config.WorldRequestData.ChunkData not in chunk:
            self.log.warning("Didn't receive chunk data, queuing for later.")
            self.log.debug("Actually received: {}".format(chunk))
            self.request_chunk(cx, cy)
            return
        chunk = chunk[config.WorldRequestData.ChunkData]
        for pos, block in chunk:
            #self.log.debug("Rendering block ({}, {}, {}) of type {}".format(*pos, block))
            self.render_block_to_batch(pos, block, batch)
        self.log.debug("Rendered chunk ({}, {})".format(cx, cy))
        self.rendered_chunks[(cx, cy)] = batch


    def run(self):
        while self.__running__.value:
            try:
                cx, cy = self.chunks_to_render.get(timeout=config.WorldRenderer.RendererWaitTime)
                self.log.info("Got request for chunk ({}, {})".format(cx, cy))
            except queue.Empty: continue

            self.render_chunk(cx, cy)


    def draw(self):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        for (cx, cy), batch in self.rendered_chunks.items():
            #self.log.info("Drawing chunk ({}, {})".format(cx, cy))
            batch.draw()


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


    def test_request_chunk(self):
        return
        self.renderer.render_chunk(0, 0)

        for p, c in self.renderer.rendered_chunks:
            if p == (0, 0):
                break
        else:
            self.fail("Renderer didn't load chunk (0, 0)")
        #for i in range(10):
            #time.sleep(0.200)

    def test_rendered_chunk(self):
        self.log.info("test_rendered_chunk")
        self.renderer.start()
        self.renderer.request_chunk(0, 0)
        time.sleep(1)
        self.renderer.download_rendered_chunks()
        self.assertTrue(len(self.renderer.rendered_chunks) == 1)
