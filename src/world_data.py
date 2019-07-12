import logging, random, unittest
import multiprocessing as mp
from collections import defaultdict
import config


class WorldDataClient:
    def __init__(self, name, pipe, parent_log):
        self.name = name
        self.pipe = pipe
        try:
            self.log = parent_log.getChild("WorldDataClient")
        except AttributeError as e:
            raise Exception("Invalid parent logger")


    def send_request(self, cmd, **data):
        req = (cmd, data)
        self.pipe.send(req)
        return self.pipe.recv()


    def ping(self):
        res = self.send_request(config.WorldRequests.PingReq)
        self.log.info("Server replied to request: {}".format(res[1]))



class WorldDataServer(mp.Process):
    """A world data request takes the form of a tuple, (command, data_dict)"""
    def __init__(self, parent_log, log_level=logging.INFO):
        super(WorldDataServer, self).__init__()

        self.__running__ = mp.Value('b', True)
        self.__main_pipe_pub__, self.__main_pipe__ = mp.Pipe(True)
        self.__world_data__ = defaultdict(lambda: Chunk())
        self.__connections__ = {self.__main_pipe__: config.WorldDataServer.MainConnectionName,}
        self.parent_log = parent_log

        self.log = logging.getLogger('WorldDataServer')

        self.__handler__ = logging.StreamHandler()
        self.__formatter__ = logging.Formatter('%(asctime)s %(processName)-6s %(filename)s:%(funcName)s[%(lineno)s] %(levelname)-8s %(message)s')
        self.__handler__.setFormatter(self.__formatter__)
        self.log.addHandler(self.__handler__)
        self.log.setLevel(log_level)


    def get_main_client(self):
        return WorldDataClient(config.WorldDataServer.MainConnectionName, self.__main_pipe_pub__, self.parent_log)


    def random_cli_id(self):
        letters = string.ascii_lowercase
        id = ''.join(random.choice(letters) for i in range(config.WorldDataServer.RandomIDLength))
        return id


    def new_client(self, parent_log, name=None):
        if name is None:
            name = self.random_cli_id

        __new_pipe__, new_pipe = mp.Pipe(duplex)
        self.__connections__[__new_pipe__] = name
        new_cli = WorldDataClient(name, pipe, parent_log)

        self.log.info("Created a new client '{}'".format(name))

        return new_cli


    def handle_request(self, cli, req):
        cli_name = self.__connections__[cli]

        if req[0] not in config.WorldRequests:
            self.log.warning("Invalid request from client '{}'".format(cli_name, req[0]))
            self.log.debug("Invalid request contents: {}".format(req))
            return

        # Switch statement for all supported commands.
        response = [None, None] # [responding_to_request, response_data]
        if req[0] == config.WorldRequests.PingReq:
            self.log.info("Received Ping request from client '{}'".format(cli_name))
            response[0] = req[0]
            response[1] = {config.WorldRequestData.Pong: 'pong'}

        elif req[0] == config.WorldRequests.NewClientReq:
            self.log.info("Received New Client request from client '{}'".format(cli_name))
            if req[1] is not None:
                name = req[1][config.WorldRequestData.NewClienName]
            else:
                name = None
            new_cli = self.new_cli(name=name)
            response[0] = config.WorldRequests.NewClientReq
            response[1] = {config.WorldRequestData.NewClient: new_cli}

        self.log.debug("Replying with: {}".format(response))
        cli.send(tuple(response))


    def run(self):
        while self.__running__.value:
            ready = mp.connection.wait(self.__connections__.keys(), timeout=config.WorldDataServer.ConnectionWaitTime)
            for cli in ready:
                name = self.__connections__[cli]
                try:
                    req = cli.recv()
                except EOFError as e:
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
        l = logging.getLogger("Testing")
        h = logging.StreamHandler()
        f = logging.Formatter('%(processName)-20s:%(filename)s:%(funcName)s[%(lineno)s] %(levelname)-8s %(message)s')
        h.setFormatter(f)
        l.addHandler(h)
        l.setLevel(logging.DEBUG)
        self.log = l

        self.world_server = WorldDataServer(self.log)
        self.world_client = self.world_server.get_main_client()
        self.world_server.start()


    def tearDown(self):
        self.world_server.__running__.value = False
        print("Closing world server")
        self.world_server.join()

    def test_ping(self):
        self.world_client.ping()
