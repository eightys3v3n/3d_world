from pyglet.gl import *
import multiprocessing as mp
import queue, pyglet, time, unittest, logging
import config, world_data


class WorldRenderer(mp.Process):
    def __init__(self, world_client, parent_log):
        super(WorldRenderer, self).__init__()
        self.parent_log = parent_log
        self.log = self.parent_log.getChild("WorldRenderer")
        self.world_client = world_client
        self.chunks_to_render = queue.Queue(config.WorldRenderer.MaxQueuedChunks)
        self.rendered_chunks = []
        self.__running__ = mp.Value('b', True) # Carry over because I planned to make this a seperate process.


    #def start(self, *args, **kwargs):
        """Start the server and log that it has started."""
        #super(WorldRenderer, self).start(*args, **kwargs)
        #self.log.info("WorldRenderer is started.")


    #def stop(self, *args, **kwargs):
        #self.log.info("WorldRenderer is stopping.")
        #self.__running__.value = False


    def chunk_is_rendered(self, x, y):
        for p, _ in self.rendered_chunks:
            if (x, y) == p:
                return True
        return False


    def request_chunk(self, cx, cy):
        if not self.chunk_is_rendered(cx, cy):
            self.log.info("Requesting chunk to be rendered ({}, {})".format(cx, cy))
            self.chunks_to_render.put((cx, cy))


    def render_block_to_batch(self, pos, block, batch):
        indexes, vertices = self.block_vertices(*pos, block)
        colours = self.block_colour(block)
        batch.add_indexed((len(indexes), GL_QUADS, None, indexes, ("v3f", vertices), ("c3B", colours)))


    def render_chunk(self, cx, cy):
        batch = pyglet.graphics.Batch()
        chunk = self.world_client.get_chunk(cx, cy)
        if config.WorldRequestData.ChunkData not in chunk:
            self.log.warning("Didn't receive chunk data, queuing for later.")
            self.log.debug("Actually received: {}".format(chunk))
            self.request_chunk(cx, cy)
            return
        chunk = chunk[config.WorldRequestData.ChunkData]
        for pos, block in chunk:
            self.render_block_to_batch(pos, block, batch)
        self.rendered_chunks.append(((cx, cy), batch))
        self.log.info("Rendered chunk ({}, {})".format(cx, cy))


    def run(self):
        while self.__running__.value:
            try:
                cx, cy = self.chunks_to_render.get(timeout=config.WorldRenderer.RendererWaitTime)
                self.log.info("Got request for chunk ({}, {})".format(cx, cy))
            except queue.Empty: continue

            self.render_chunk(cx, cy)


    def draw(window):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentify()
        for _, batch in self.rendered_chunks:
            batch.draw()


    def block_colour(self, block):
       return config.BlockColour[block.block_type]


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
        self.renderer.render_chunk(0, 0)

        for p, c in self.renderer.rendered_chunks:
            if p == (0, 0):
                break
        else:
            self.fail("Renderer didn't load chunk (0, 0)")
        #for i in range(10):
            #time.sleep(0.200)
