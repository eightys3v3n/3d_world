from enum import Enum, unique


LogFormat = '%(processName)-20s:%(filename)-20s:%(funcName)-20s[%(lineno)-3s] %(levelname)-8s %(message)s'
TestingLog = 'test.log'


class Debug:
    class Player:
        PrintHeadingOnChange = False
        PrintPositionOnChange = False


class Player:
    InitialPosition = [0.0, 0.0, 0.0]
    InitialHeading = [90.0, 0.0, 0.0]
    Height = 2 # blocks tall
    MoveSpeed = [4, 4, 4]
    MaxFallSpeed = 30


class Generator:
    Distance = 1 # chunks


class WorldRenderer:
    MaxQueuedChunks = 256
    RendererWaitTime = 1 # Specifies how long, in seconds, the renderer should wait for requests before checking if it should exit.
    BlockSize = 16


class WorldDataServer:
    MainConnectionName = 'Main'
    RandomIDLength = 5
    ConnectionWaitTime = 1 # Specifies how long, in seconds, the server should wait for requests before checking if it should exit.
    ChunkSize = 16
    ChunkHexLength = 6 # This is 1-512. It trims a SHA 512 hash to this length to compare and print chunks.
    WorldHeight = 1024


@unique
class WorldRequests(Enum):
    # Commands
    FailedReq = 'failure'
    InvalidReq = 'invalid'
    PingReq = 'ping'
    NewClientReq = 'new_client'
    SetChunkReq = 'set_chunk'
    GetChunkReq = 'get_chunk'

@unique
class WorldRequestData(Enum):
    # Data fields
    Pong = 'pong'
    NewClientName = 'new_client_name'
    NewClient = 'new_client'
    ChunkPos = 'chunk_pos'
    ChunkData = 'chunk_data'


@unique
class BlockType(Enum):
    Empty = None
    Grass = 'grass'

class BlockColour(Enum):
    Grass = (
        # top
        0,255,0,0,255,0,
        0,255,0,0,255,0,
        # front
        139,69,19,139,69,19,
        139,69,19,139,69,19,
        # bottom
        139,69,19,139,69,19,
        139,69,19,139,69,19,
        # left
        139,69,19,139,69,19,
        139,69,19,139,69,19,
        # back
        139,69,19,139,69,19,
        139,69,19,139,69,19,
        # right
        139,69,19,139,69,19,
        139,69,19,139,69,19
    )
