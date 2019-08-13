import pyglet
from pyglet.gl import *
import multiprocessing as mp
import queue, pyglet, time, unittest, logging
import multiprocessing as mp
import config, world_data
import time


class RenderedBatch:
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self.complete = False


class WorldRenderer(mp.Process):
    """Handles the rendering and storing of screen data. Also how voxels are drawn and what not. The seperate process handles actually getting the chunk from the WorldDataServer and creating the vertex/colour arrays to be sent to the GPU."""

    def __init__(self, world_client, parent_log):
        super(WorldRenderer, self).__init__()
        self.parent_log = parent_log
        self.log = self.parent_log.getChild("WorldRenderer")
        self.log.setLevel(config.WorldRenderer.LogLevel)

        self.world_client = world_client

        self.chunks_to_render = mp.Queue(config.WorldRenderer.MaxQueuedChunks) # (cx, cy): Chunks that are requested to be rendered.
        self.rendered_chunks = {} # (cx, cy): pyglet.graphics.Batch to draw
        self.requested = [] # (cx, cy): Chunks that have been requested and aren't drawn yet.
        self.finished_chunks = mp.Queue(maxsize=config.WorldRenderer.MaxFinishedChunks) # ((cx, cy), chunk_data): Chunks that have been pre-calculated but have yet to be saved to the GPU for drawing.
        self.rendering_chunk = None # ((cx, cy), render_data): The chunk that is being drawn over more than one frame.
        self.pending_chunks = [] # (cx, cy): Chunks that were attempted but something happened (like it wasn't generated yet).
        self.__running__ = mp.Value('b', False)


    def start(self, *args, **kwargs):
        """Start the pre-calculation process."""
        super(WorldRenderer, self).start(*args, **kwargs)
        self.__running__.value = True


    def stop(self):
        """Stop the pre-calculation process."""
        self.__running__.value = False
        while not self.chunks_to_render.empty():
            try:
                self.chunks_to_render.get(block=False)
            except queue.Empty: pass
        while not self.finished_chunks.empty():
            try:
                self.finished_chunks.get(block=False)
            except queue.Empty: pass


    def render_block_to_data(self, pos, block, batch_data):
        """Calculates the vertice data and colour for a given Block object and it's absolute position in the world.
        Adds this data to the batch_Data array."""
        indexes, vertices = self.block_vertices(*pos, block)
        colours = self.block_colour(block).value

        if config.WorldRenderer.BatchAddMode == config.WorldRenderer.BatchAddModes.Indexed:
            data = (len(indexes), GL_QUADS, None, indexes, ("v3f", vertices), ("c3B", colours))
        elif config.WorldRenderer.BatchAddMode == config.WorldRenderer.BatchAddModes.Nonindexed:
            data = (len(indexes), GL_QUADS, None, ("v3f", vertices), ("c3B", colours))
        batch_data.append(data)


    def is_rendered(self, cx, cy):
        """True if the chunk is currently being drawn, False otherwise."""
        if (cx, cy) in self.rendered_chunks: return True
        return False


    def request_chunk(self, cx, cy, force=False):
        """Put in a request for a chunk to be rendered.
        Parameters:
            force (boolean): False means never rerender a chunk."""
        if (cx, cy) in self.requested and not force:
            self.log.debug("Ignoring already requested chunk ({}, {}).".format(cx, cy))
            return

        self.log.info("Requesting chunk ({}, {})".format(cx, cy))
        try:
            self.chunks_to_render.put((cx, cy), block=False)
            self.requested.append((cx, cy))
        except queue.Full:
            self.log.warning("Dropping request for chunk ({}, {}) because render queue is full.".format(cx, cy))


    def calc_chunk_render_data(self, cx, cy):
        """Get all the data necessary to create all the rendering data (vertices, colours, the chunk data...).
        Add that data to the finished_chunks queue so the main thread can draw it."""
        if self.world_client.is_generated(cx, cy):
            batch_data = []

            chunk = self.world_client.get_chunk(cx, cy)
            self.log.debug("Calculating render data for chunk ({}, {})".format(cx, cy))
            if config.WorldRequestData.ChunkData not in chunk:
                self.log.warning("Didn't receive chunk data, queuing for later.")
                self.log.debug("Actually received: {}".format(chunk))
                self.request_chunk(cx, cy)
                return
            chunk = chunk[config.WorldRequestData.ChunkData]

            for pos, block in chunk:
                pos = self.world_client.chunk_block_to_abs_block(cx, cy, *pos)
                self.render_block_to_data(pos, block, batch_data)

            try:
                self.finished_chunks.put([(cx, cy), batch_data], timeout=config.WorldRenderer.PutFinishedChunkTimeout)
                return False

            except queue.Full:
                self.log.warning("Failed to put finished chunk into queue ({}, {}).".format(cx, cy))
                return True
        else:
            self.log.info("Requested chunk isn't generated ({}, {})".format(cx, cy))
            return True


    def render_block(self, render_data, batch):
        """Add the given render_data to the given RenderedBatch object. This is what takes so long and must be done on the main thread. pyglet.graphics.Batch() can't be passed through a multiprocessing.Queue()."""
        batch.batch.add(*render_data)


    def continue_rendering(self, max_blocks):
        """Try to resume rendering the rendering_chunk, but only draw max_blocks.

        Returns the number of blocks rendered."""
        rendered_blocks = 0

        if self.rendering_chunk is None: return 0

        if self.rendering_chunk[0] in self.rendered_chunks:
            batch = self.rendered_chunks[self.rendering_chunk[0]]
            if batch.complete: # Delete the previous batch and start creating a new one. (re-render a chunk)
                batch = RenderedBatch()
                self.rendered_chunks[self.rendering_chunk[0]] = batch
                self.log.debug("Creating new batch for chunk ({}, {}).".format(*self.rendering_chunk[0]))
            else:
                self.log.debug("Adding to previous batch for chunk ({}, {}).".format(*self.rendering_chunk[0]))
        else:
            batch = RenderedBatch()
            self.rendered_chunks[self.rendering_chunk[0]] = batch
            self.log.debug("Creating new batch for chunk ({}, {}).".format(*self.rendering_chunk[0]))

        for block_render_data in self.rendering_chunk[1]:
            if rendered_blocks >= max_blocks:
                batch.complete = False
                self.log.debug("Leaving chunk ({}, {}) incomplete.".format(*self.rendering_chunk[0]))
                break

            self.render_block(block_render_data, batch)
            self.rendering_chunk[1] = self.rendering_chunk[1][1:]
            rendered_blocks += 1
        else:
            batch.complete = True
            self.log.debug("Finished rendering chunk ({}, {}).".format(*self.rendering_chunk[0]))

        if len(self.rendering_chunk[1]) == 0:
            self.rendering_chunk = None

        return rendered_blocks


    def render_queued(self):
        """Render some of the pre_calculated chunks onto the screen by putting them into a batch to be drawn.
        Tries to finish the incompletely rendered chunk before getting another pre-calculated chunk. Will only put config.WorldRenderer.MaxBlocksPerFrame blocks into a batch to be drawn every frame."""
        if self.finished_chunks.full():
            self.log.warning("Throwing out some finished chunks from render queue.")
            for i in range(config.WorldRenderer.TrashChunksOnFullFinishedQueue):
                try:
                    (cx, cy), _ = self.finished_chunks.get(block=False)
                    self.requested.remove((cx, cy))
                    if (cx, cy) in self.rendered_chunks:
                        del self.rendered_chunks[(cx, cy)]
                except queue.Empty: break

        rendered_blocks = self.continue_rendering(config.WorldRenderer.MaxBlocksPerFrame)

        if rendered_blocks < config.WorldRenderer.MaxBlocksPerFrame:
            try:
                self.rendering_chunk = self.finished_chunks.get(block=False)
                self.log.info("Finished rendering chunk ({}, {}).".format(*self.rendering_chunk[0]))
                self.requested.remove(self.rendering_chunk[0])
            except queue.Empty: pass
            self.continue_rendering(config.WorldRenderer.MaxBlocksPerFrame - rendered_blocks)


    def draw(self):
        """Actually draw all the rendered chunks."""

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        for (cx, cy), batch in self.rendered_chunks.items():
            #self.log.info("Drawing chunk ({}, {})".format(cx, cy))
            batch.batch.draw()


    def run(self):
        """What the renderer process runs in the background. Receives chunk requests, gets the chunk data, pre-calculates vertex and colour arrays, sends the results to the main thread."""
        while self.__running__.value:
            try:
                cx, cy = self.chunks_to_render.get(timeout=config.WorldRenderer.WaitTime)
                self.log.debug("Received chunk render request for ({}, {})".format(cx, cy))
                if self.calc_chunk_render_data(cx, cy):
                    self.log.info("Saving chunk to pending because render failed ({}, {})".format(cx, cy))
                    self.pending_chunks.append((cx, cy))

                for cx, cy in self.pending_chunks:
                    if not self.calc_chunk_render_data(cx, cy):
                        self.log.info("Finished pending chunk ({}, {}).".format(cx, cy))
                        self.pending_chunks.remove((cx, cy))
            except queue.Empty: pass


    def block_colour(self, block):
        """Get the block colour array for a given block."""
       return config.BlockColour[block.block_type.value]


    def block_vertices(self, x, y, z, block):
        """Returns the vertices index and the actual screen vertices for a cube, in the correct order (CCW right now based on OpenGL config."""
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
        #self.world_server.join()


    def test_block_vertices(self):
        # No idea how to test this since they are hardcoded. :/
        pass


    def DISABLED_test_render_chunk(self):
        return
        self.renderer.render_chunk(0, 0)

        for pos, batch in self.renderer.rendered_chunks.items():
            if pos == (0, 0):
                break
        else:
            self.fail("Renderer didn't load chunk (0, 0)")
