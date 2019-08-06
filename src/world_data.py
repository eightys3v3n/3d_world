import logging, random, unittest, string, itertools
import multiprocessing as mp
from collections import defaultdict
from chunk import Chunk
from block import Block
import config


# TODO Instead of returning request data from a WorldDataClient, it should set a 'last_response' variable.

class WorldDataClient:
    """An object that connects to the WorldDataServer. Each seperate thread or process requires a seperate instance of this, Not a copy of it. You must use .new_client from the main client to create new instances."""
    def __init__(self, name, pipe, parent_log):
        """Shouldn't be created unless inside WorldDataServer.
        name:  The name of the client (like WorldGenerator, or WorldRenderer)
        pipe:  A pipe connected to the server.
        parent_log: The log of the process that will be using this client."""

        self.name = name
        self.pipe = pipe
        try:
            self.log = parent_log.getChild("WorldDataClient")
            self.log.setLevel(config.WorldDataClient.LogLevel)
        except AttributeError as e:
            raise Exception("Invalid parent logger", e)
        #TODO add some performance metrics tracking the number of requests sent in a minute and time waiting for responses.


    def __send_request__(self, cmd, data=None):
        """Sends requests to the server as well as logging what is sent and received. WAITS until something is received from the server!
        cmd:  An instance of config.WorldRequests that specifies the request type.
        data: A dictionary of config.WorldRequestData keys that contains the data for the request.
        returns the response from the server in the form (instance of config.WorldRequests, dict of config.WorldRequestData keys)"""

        req = (cmd, data)
        self.log.debug("Sending request: {}".format(req))
        self.pipe.send(req)

        res = self.pipe.recv()
        self.log.debug("Server replied to request: {}".format(res))

        return res


    def __handle_fail__(self, req):
        """Handles detecting and logging if the server returns an error. Returns True if there was an error, False otherwise."""
        if req[0] in (config.WorldRequests.FailedReq, config.WorldRequests.InvalidReq, config.WorldRequests.DuplicateInit):
            self.log.warning("Request failed: {}".format(req[0]))
            self.log.debug("Failed request data: {}".format(req[1]))
            return True
        return False


    def ping(self):
        """Just a ping to check the server is still connected.
        Returns {config.WorldRequestData.Pong: 'pong'} if successful, else returns None."""
        req = config.WorldRequests.PingReq
        res = self.__send_request__(req)
        if self.__handle_fail__(res): return None
        else: return res[1]


    def new_client(self, name=None):
        """Requests the server to create another WorldDataClient object that is connected to the server. Will wait until the server responds with a new connected client.
        Returns {config.WorldRequestData.NewClient: WorldDataClient()} if successful, else returns None."""
        req = config.WorldRequests.NewClientReq
        req_data = {'name': name}
        res = self.__send_request__(req, req_data)
        if self.__handle_fail__(res): return None
        else: return res[1]


    def set_chunk(self, cx, cy, chunk):
        """Requests that the server set the chunk data for chunk position (cx, cy). Will wait until the server responds with a success or failure.
        cx: x position of the chunk to set.
        cy: y position of the chunk to set.
        chunk: A Chunk object to put at the specified location.
        Returns False if successful, else returns True."""
        req = config.WorldRequests.SetChunkReq
        req_data = {config.WorldRequestData.ChunkPos: (cx, cy), config.WorldRequestData.ChunkData: chunk}
        res = self.__send_request__(req, req_data)
        return self.__handle_fail__(res)


    def init_chunk(self, cx, cy, chunk):
        """Requests that the server set the chunk data for chunk position (cx, cy) ONLY if the chunk was previously ungenerated. Will wait until the server responds with a success or failure.
        cx: x position of the chunk to set.
        cy: y position of the chunk to set.
        chunk: A Chunk object to put at the specified location.
        Returns False if chunk wasn't already generated and setting the chunk was successful, else returns True."""
        req = config.WorldRequests.InitChunkReq
        req_data = {config.WorldRequestData.ChunkPos: (cx, cy), config.WorldRequestData.ChunkData: chunk}
        res = self.__send_request__(req, req_data)
        return self.__handle_fail__(res)


    def get_chunk(self, cx, cy):
        """Returns a Chunk object for the requested location. Will wait until the server responds with the chunk.
        cx: x position of the chunk to set.
        cy: y position of the chunk to set.
        Returns {config.WorldRequestData.ChunkData: Chunk()} if successful, else returns None"""
        req = config.WorldRequests.GetChunkReq
        req_data = {config.WorldRequestData.ChunkPos: (cx, cy)}
        res = self.__send_request__(req, req_data)
        if self.__handle_fail__(res): return None
        else: return res[1]


    def is_generated(self, cx, cy):
        """Returns True if the chunk has already been generated, False otherwise."""
        req = config.WorldRequests.IsGenerated
        req_data = {config.WorldRequestData.ChunkPos: (cx, cy)}
        res = self.__send_request__(req, req_data)
        if self.__handle_fail__(res): return None
        else: return res[1][config.WorldRequestData.Boolean]


    @classmethod
    def abs_block_to_chunk_block(cls, abx, aby, abz):
        bx = abx % config.WorldDataServer.ChunkSize
        cx = (abx - bx) / config.WorldDataServer.ChunkSize

        by = aby

        bz = abz % config.WorldDataServer.ChunkSize
        cy = (abz - bz) / config.WorldDataServer.ChunkSize

        bx = int(bx)
        cx = int(cx)
        by = int(by)
        bz = int(bz)
        cy = int(cy)
        return ((cx, cy), (bx, by, bz))


    @classmethod
    def chunk_block_to_abs_block(cls, cx, cy, bx, by, bz):
        abx = cx * config.WorldDataServer.ChunkSize + bx
        aby = by
        abz = cy * config.WorldDataServer.ChunkSize + bz
        return (abx, aby, abz)


class WorldDataServer(mp.Process):
    """A server in a seperate process that handles all access to the world data. This class could be used to cache different sections of the world or to load between the filesystem and RAM. Currently it just stores the entire world in RAM using a dictionary of Chunk objects."""
    def __init__(self, parent_log):
        """parent_log: The logging.getLogger() object that will be the parent for this log."""
        super(WorldDataServer, self).__init__()

        self.__running__ = mp.Value('b', True)
        self.__main_pipe_pub__, self.__main_pipe__ = mp.Pipe(True)
        self.__chunks__ = defaultdict(lambda: Chunk())
        self.__connections__ = {self.__main_pipe__: config.WorldDataServer.MainConnectionName,}
        self.parent_log = parent_log

        #self.log = logging.getLogger('WorldDataServer')
        self.log = parent_log.getChild('WorldDataServer')
        self.log.setLevel(config.WorldDataServer.LogLevel)

        #self.__handler__ = logging.StreamHandler()

        # DON'T DELETE ME. This is the format I want for the main log.
        #self.__formatter__ = logging.Formatter('%(asctime)s %(processName)-6s %(filename)s:%(funcName)s[%(lineno)s] %(levelname)-8s %(message)s')

        #self.__handler__.setFormatter(self.__formatter__)
        #self.log.addHandler(self.__handler__)
        #self.log.setLevel(log_level)
        self.log.info("WorldDataServer is ready.")


    def start(self, *args, **kwargs):
        """Start the server and log that it has started."""
        super(WorldDataServer, self).start(*args, **kwargs)
        self.log.info("WorldDataServer is started.")


    def stop(self, *args, **kwargs):
        self.log.info("WorldDataServer is stopping.")
        self.__running__.value = False
        self.join()
        self.log.info("WorldDataServer stopped.")


    def set_chunk(self, cx, cy, chunk):
        """Change the chunk data at a specified location."""
        if not isinstance(chunk, Chunk):
            raise TypeError("Must be Chunk, not {}".format(type(chunk)))
        self.__chunks__[(cx, cy)] = chunk


    def get_chunk(self, cx, cy):
        """Get the chunk data at a specified location"""
        return self.__chunks__[(cx, cy)]


    def get_main_client(self):
        """Return the main client to the starting process."""
        return WorldDataClient(config.WorldDataServer.MainConnectionName, self.__main_pipe_pub__, self.parent_log)


    def random_cli_id(self):
        """Create a random client ID for new_client if a name isn't specified."""
        letters = string.ascii_lowercase
        id = ''.join(random.choice(letters) for i in range(config.WorldDataServer.RandomIDLength))
        return id


    def new_client(self, parent_log, name=None):
        """Creates a new WorldDataClient that is connected to this server.
        parent_log: The logging.getLogger() object of the process that is going to use this client.
        name: Something useful to identify the client in the logs (like WorldGenerator or WorldRenderer)
        Returns the new client"""
        if name is None:
            name = self.random_cli_id()
        if name in self.__connections__.values():
            new_name = name + self.random_cli_id()
            self.log.info("Client ID '{}' already connected. Changing to '{}'".format(name, new_name))
            name = new_name

        __new_pipe__, new_pipe = mp.Pipe(True)
        self.__connections__[__new_pipe__] = name
        new_cli = WorldDataClient(name, new_pipe, parent_log)

        self.log.info("Created a new client '{}'".format(name))

        return new_cli


    def handle_request(self, cli, req):
        """Figures out what was requested, does it, and responds to the client.
        cli: The pipe object that is in self.__connections__ to communicate with the client/
        req: The request received from the client in the form (instance of config.WorldRequests, dict of config.WorldRequestData keys)"""
        cli_name = self.__connections__[cli]
        response = [None, None] # [responding_to_request, response_data]

        if not isinstance(req[0], config.WorldRequests):
            self.log.warning("Invalid request from client '{}'".format(cli_name, req[0]))
            self.log.debug("Invalid request contents: {}".format(req))
            response[0] = config.WorldRequests.InvalidReq

        elif req[0] is config.WorldRequests.PingReq:
            self.log.info("Received Ping request from client '{}'".format(cli_name))
            response[0] = req[0]
            response[1] = {config.WorldRequestData.Pong: 'pong'}

        elif req[0] == config.WorldRequests.NewClientReq:
            self.log.info("Received New Client request from client '{}'".format(cli_name))
            if req[1] is not None and config.WorldRequestData.NewClientName in req[1]:
                name = req[1][config.WorldRequestData.NewClientName]
            else:
                name = None
            try:
                new_cli = self.new_client(self.parent_log, name=name)
                response[0] = req[0]
                response[1] = {config.WorldRequestData.NewClient: new_cli}
            except Exception as e:
                self.log.warning("Failed to get new client.")
                self.log.debug(e)
                response[0] = config.WorldRequests.FailedReq

        elif req[0] == config.WorldRequests.SetChunkReq:
            self.log.info("Received Set Chunk request from client '{}'".format(cli_name))

            cx, cy = req[1][config.WorldRequestData.ChunkPos]
            chunk_data = req[1][config.WorldRequestData.ChunkData]

            try:
                self.set_chunk(cx, cy, chunk_data)
                response[0] = req[0]
            except Exception as e:
                self.log.warning("Failed to set chunk data.")
                self.log.debug(e)
                response[0] = config.WorldRequests.FailedReq

        elif req[0] == config.WorldRequests.GetChunkReq:
            self.log.info("Receiuved Get Chunk request from client '{}'".format(cli_name))

            cx, cy = req[1][config.WorldRequestData.ChunkPos]

            try:
                chunk = self.get_chunk(cx, cy)
                response[0] = req[0]
                response[1] = {config.WorldRequestData.ChunkData: chunk}
            except Exception as e:
                self.log.warning("Failed to get chunk data.")
                self.log.debug(e)
                response[0] = config.WorldRequests.FailedReq

        elif req[0] == config.WorldRequests.InitChunkReq:
            self.log.info("Received Init Chunk request from client '{}'".format(cli_name))

            cx, cy = req[1][config.WorldRequestData.ChunkPos]
            if not self.get_chunk(cx, cy).is_generated():
                chunk_data = req[1][config.WorldRequestData.ChunkData]

                try:
                    self.set_chunk(cx, cy, chunk_data)
                    response[0] = req[0]
                except Exception as e:
                    self.log.warning("Failed to set chunk data.")
                    self.log.debug(e)
                    response[0] = config.WorldRequests.FailedReq
            else:
                self.log.warning("A chunk was initialized twice")
                self.log.debug("Chunk: ({}, {})".format(cx, cy))
                response[0] = config.WorldRequests.DuplicateInit

        elif req[0] == config.WorldRequests.IsGenerated:
            self.log.info("Received Is Generated request from client '{}'".format(cli_name))

            cx, cy = req[1][config.WorldRequestData.ChunkPos]
            try:
                if self.get_chunk(cx, cy).is_generated():
                    response[1] = {config.WorldRequestData.Boolean: True}
                else:
                    response[1] = {config.WorldRequestData.Boolean: False}
                response[0] = config.WorldRequests.IsGenerated
            except Exception as e:
                self.log.warning("Failed to check if chunk is generated.")
                self.log.debug("Chunk: ({}, {})".format(cx, cy))
                response[0] = config.WorldRequests.FailedReq


        self.log.debug("Replying with: {}".format(response))
        cli.send(tuple(response))


    def run(self):
        """The main loop for the WorldDataServer. It waits for messages from clients, then passes the requests to handle_requests. Since this is not multithreaded or multiprocessed all world modifications happen syncronously."""
        while self.__running__.value:
            ready = mp.connection.wait(self.__connections__.keys(), timeout=config.WorldDataServer.ConnectionWaitTime)
            for cli in ready:
                name = self.__connections__[cli]
                try:
                    req = cli.recv()
                except EOFError:
                    if name == config.WorldDataServer.MainConnectionName:
                        self.log.info("WorldDataServer: Main connection closed, exiting.")
                        self.running = False
                        break
                    else:
                        del self.__connections__[cli]
                        self.log.info("WorldDataServer: Client closed connection, '{}'".format(name))
                        continue
                self.handle_request(cli, req)


class TestWorldDataServer(unittest.TestCase):
    def setUp(self):
        l = logging.getLogger("TestWorldDataServer")
        #h = logging.StreamHandler()
        fh = logging.FileHandler(config.TestingLog)
        #f = logging.Formatter('%(filename)s:%(funcName)s[%(lineno)s] %(message)s')
        ff = logging.Formatter(config.LogFormat)
        fh.setFormatter(ff)
        #h.setFormatter(f)
        l.addHandler(fh)
        #l.addHandler(h)
        l.setLevel(logging.DEBUG)
        self.log = l

        self.world_server = WorldDataServer(self.log)
        self.world_client = self.world_server.get_main_client()
        self.world_server.start()

    def tearDown(self):
        self.world_server.stop()
        self.world_server.join()

    def test_ping(self):
        res = self.world_client.ping()
        self.assertIn(config.WorldRequestData.Pong, res)

    def test_new_client(self):
        cli = self.world_client.new_client()
        self.assertIsNotNone(cli[config.WorldRequestData.NewClient])
        cli = cli[config.WorldRequestData.NewClient]
        res = cli.ping()
        self.assertIn(config.WorldRequestData.Pong, res)

    def test_setget_chunk(self):
        # Create a chunk with a non-default blocks
        chunk = Chunk()
        chunk.set_block(0, 0, 0, Block(config.BlockType.Grass))

        # Ensure that the block the server sets the chunk without error.
        res = self.world_client.set_chunk(0, 0, chunk)
        self.assertFalse(res)

        # Ensure the chunk it gives back to us is the same one we but in.
        res = self.world_client.get_chunk(0, 0)[config.WorldRequestData.ChunkData]
        self.assertIsNotNone(res, "get_chunk failed")
        self.assertEqual(chunk, res)

    def test_init_chunk(self):
        chunk = Chunk()
        chunk.set_block(0, 0, 0, Block(config.BlockType.Grass))
        res = self.world_client.init_chunk(0, 0, chunk)
        self.assertFalse(res)

        res = self.world_client.init_chunk(0, 0, chunk)
        self.assertTrue(res)

    def test_is_generated(self):
        res = self.world_client.is_generated(0, 0)
        self.assertFalse(res, "World Client says an ungenerated chunk is already generated.")

        chunk = Chunk()
        chunk.set_block(0, 0, 0, Block(config.BlockType.Grass))
        res = self.world_client.init_chunk(0, 0, chunk)
        self.assertFalse(res, "Couldn't init the chunk.")

        res = self.world_client.is_generated(0, 0)
        self.assertTrue(res)


class TestWorldDataClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        M = config.WorldDataServer.ChunkSize
        cls.tests = {
            ((0, 0), (0, 0, 0)): (0, 0, 0),
            ((0, 0), (1, 0, 0)): (1, 0, 0),
            ((0, 0), (0, 0, 1)): (0, 0, 1),
            ((0, 0), (2, 0, 3)): (2, 0, 3),

            ((1, 0), (0, 0, 0)): (M, 0, 0),
            ((1, 0), (1, 0, 0)): (M+1, 0, 0),
            ((1, 0), (0, 0, 1)): (M, 0, 1),
            ((1, 0), (2, 0, 3)): (M+2, 0, 3),

            ((0, 1), (0, 0, 0)): (0, 0, M),
            ((0, 1), (1, 0, 0)): (1, 0, M),
            ((0, 1), (0, 0, 1)): (0, 0, M+1),
            ((0, 1), (2, 0, 3)): (2, 0, M+3),

            ((0, -1), (0, 0, 0)): (0, 0, -M),
            ((0, -1), (1, 0, 0)): (1, 0, -M),
            ((0, -1), (0, 0, 1)): (0, 0, -M+1),
            ((0, -1), (2, 0, 3)): (2, 0, -M+3),

            ((-1, 0), (0, 0, 0)): (-M, 0, 0),
            ((-1, 0), (1, 0, 0)): (-M+1, 0, 0),
            ((-1, 0), (0, 0, 1)): (-M, 0, 1),
            ((-1, 0), (2, 0, 3)): (-M+2, 0, 3),

            ((2, 3), (0, 0, 0)): (2*M, 0, 3*M),
            ((2, 3), (1, 0, 0)): (2*M+1, 0, 3*M),
            ((2, 3), (0, 0, 1)): (2*M, 0, 3*M+1),
            ((2, 3), (2, 0, 3)): (2*M+2, 0, 3*M+3),

            ((-2, -3), (0, 0, 0)): (-2*M, 0, -3*M),
            ((-2, -3), (1, 0, 0)): (-2*M+1, 0, -3*M),
            ((-2, -3), (0, 0, 1)): (-2*M, 0, -3*M+1),
            ((-2, -3), (2, 0, 3)): (-2*M+2, 0, -3*M+3),
        }

    def test_abs_block_to_chunk_block(self):
        for i, (corr, test) in enumerate(self.tests.items()):
            res = WorldDataClient.abs_block_to_chunk_block(*test)
            self.assertEqual(corr, res, "Test {}: Should be {}, but was {}".format(i, corr, res))


    def test_chunk_block_to_abs_block(self):
        for i, (test, corr) in enumerate(self.tests.items()):
            try:
                res = WorldDataClient.chunk_block_to_abs_block(*test[0], *test[1])
            except Exception as e:
                print(test)
                raise Exception(e)
            self.assertEqual(corr, res, "Test {}: Should be {}, but was {}".format(i, corr, res))
