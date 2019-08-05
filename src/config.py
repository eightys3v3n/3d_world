from enum import Enum, unique


LogFormat = '%(asctime)s: %(processName)-20s:%(filename)-20s:%(funcName)-20s[%(lineno)-3s] %(levelname)-8s %(message)s'
TestingLog = 'test.log'
LogFile = 'main.log'


class Debug:
    class Player:
        PrintHeadingOnChange = False
        PrintPositionOnChange = False


class Game:
    PreventSleep = False


class Player:
    InitialPosition = [0.0, 0.0, 0.0]
    InitialHeading = [90.0, 0.0, 0.0]
    Height = 2 # blocks tall
    MoveSpeed = [4, 4, 4]
    MaxFallSpeed = 30


class WorldGenerator:
    Distance = 4 # chunks
    Processes = 2 # Number of processes generating chunks in parallel.
    WaitTime = 1 # Specifies how long, in seconds, the generator slaves should wait for requests before checking if they should exit.
    RequestQueueSize = 256 # Number of chunks that can be requested before old requests are removed.
    RecentlyRequested = 10 # Number of seconds to store recently requested chunks. This is used to avoid two GenerationSlaves generating the same chunk more than once.
    GarbageCollectionInterval = 1.0 # Once every how many seconds should we clear out the recently requested chunk list.
    MaxRecentChunksStored = 1024 # How many chunks should be stored if the list isn't being cleared quick enough?


class World:
    VoxelSize = 16


class WorldRenderer:
    MaxQueuedChunks = 256
    RendererWaitTime = 1 # Specifies how long, in seconds, the renderer should wait for requests before checking if it should exit.


class WorldDataServer:
    MainConnectionName = 'Main'
    RandomIDLength = 5
    ConnectionWaitTime = 1 # Specifies how long, in seconds, the server should wait for requests before checking if it should exit.
    ChunkSize = 16
    ChunkHexLength = 6 # This is 1-512. It trims a SHA 512 hash to this length to compare and print chunks.
    WorldHeight = 8


@unique
class WorldRequests(Enum):
    # Commands
    FailedReq = 'failure'
    InvalidReq = 'invalid'
    PingReq = 'ping'
    NewClientReq = 'new_client'
    SetChunkReq = 'set_chunk'
    GetChunkReq = 'get_chunk'
    InitChunkReq = 'init_chunk'
    DuplicateInit = 'dupe_init_chunk'
    IsGenerated = 'is_generated'

@unique
class WorldRequestData(Enum):
    # Data fields
    Pong = 'pong'
    NewClientName = 'new_client_name'
    NewClient = 'new_client'
    ChunkPos = 'chunk_pos'
    ChunkData = 'chunk_data'
    Boolean = 'boolean'


@unique
class BlockType(Enum):
    Empty = None
    Grass = 'Grass'

class BlockColour(Enum):
    Grass = (
        # top
        0,255,0,
        0,255,0,
        0,255,0,
        0,255,0,
        # front
        139,69,19,
        139,69,19,
        139,69,19,
        139,69,19,
        # bottom
        139,69,19,
        139,69,19,
        139,69,19,
        139,69,19,
        # left
        139,69,19,
        139,69,19,
        139,69,19,
        139,69,19,
        # back
        139,69,19,
        139,69,19,
        139,69,19,
        139,69,19,
        # right
        139,69,19,
        139,69,19,
        139,69,19,
        139,69,19,
    )
