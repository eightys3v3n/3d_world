from enum import Enum, unique
import logging
import random
0

LogFormat = '%(asctime)s: %(processName)-20s:%(filename)-20s:%(funcName)-20s[%(lineno)-3s] %(levelname)-8s %(message)s'
TestingLog = 'test.log'
LogFile = 'main.log'


class Debug:
    class Game:
        FPS_SPAM = False # This will track the current FPS for Every Frame, then print the running average over the last N seconds.
        FPS_SPAM_SPAN = 3 # How many seconds of FPS readings every frame to keep.
        TimeRenderingChunks = False # Whether to print how long it took to load the finished chunks onto the screen. This times the current largest cause of stuttering.

    class Player:
        PrintHeadingOnChange = False
        PrintPositionOnChange = False


class Window:
    Width = None
    Height = None


class OpenGL:
    pass

class Game:
    ViewDistance = 2  # radius of chunks to render and generate. Not the actual visible distance
    InitialGeneration = 0 # radius of chunks around (0, 0) to render when starting the game.
    PreventSleep = True
    ConsoleLogLevel = logging.ERROR # This doesn't work for some reason. Need to do more reading on the man page.


class Player:
    InitialPosition = [0.0, 0.0, 0.0]
    InitialHeading = [90.0, 0.0, 0.0]
    Height = 2 # blocks tall
    FOV = 70.0
    MoveSpeed = [4, 4, 4]
    MaxFallSpeed = 30


class WorldGenerator:
    LogLevel = logging.INFO
    Distance = Game.ViewDistance + 1 # radius of chunks to generate around the player.
    InitialDistance = Game.InitialGeneration # radius of chunks to generate when starting the game.
    Processes = 2 # Number of processes generating chunks in parallel.
    WaitTime = 1 # Specifies how long, in seconds, the generator slaves should wait for requests before checking if they should exit.
    RequestQueueSize = 1024 # Number of chunks that can be requested before old requests are removed.
    RecentlyRequested = 10 # Number of seconds to store recently requested chunks. This is used to avoid two GenerationSlaves generating the same chunk more than once.
    GarbageCollectionInterval = 1.0 # Once every how many seconds should we clear out the recently requested chunk list.
    MaxRecentChunksStored = 4096 # How many chunks should be stored if the list isn't being cleared quick enough?
    Seed = random.random()


class World:
    VoxelSize = 16 # How many Pixels is a Voxel.


class WorldRenderer:
    class BatchAddModes(Enum):
        Indexed = 'indexed' # Slower but I think it draws the points in order?
        Nonindexed = 'nonindexed' # Faster but doesn't draw them in order?

    Distance = Game.ViewDistance # Radius of chunks to render around the player.
    InitialDistance = Game.InitialGeneration
    LogLevel = logging.INFO
    MaxQueuedChunks = 1024
    MaxFinishedChunks = 16 # This should be low enough that there is no noticable delay when drawing. It will then stop the renderer for that frame. It is essentially the main bottle neck in speed of rendering chunks, how many can we deal with on the main thread in a single frame without stuttering issues.
    WaitTime = 1 # Specifies how long, in seconds, the renderer should wait for requests before checking if it should exit.
    RecentlyRequestedTimeout = 4 # How long (seconds) to wait until a chunk can be requested to be rendered again.
    TrashChunksOnFullFinishedQueue = 1 # Throw out the data for this many chunks if the finished data queue is full. This is intended to ensure that chunks being rendered are not too old and unneeded.
    MaxBlocksPerFrame = 200 # Max number of blocks to add to the pyglet batch every frame. This results in a chunk being rendered over many frames to stop stuttering issues.
    BatchAddMode = BatchAddModes.Nonindexed # Which call to use when adding to pyglet.graphics.Batch.
    PutFinishedChunkTimeout = 2


class WorldDataServer:
    LogLevel = logging.WARNING
    MainConnectionName = 'Main'
    RandomIDLength = 5
    ConnectionWaitTime = 1 # Specifies how long, in seconds, the server should wait for requests before checking if it should exit.
    ChunkSize = 16
    ChunkHexLength = 6 # This is 1-512. It trims a SHA 512 hash to this length to compare and print chunks.
    WorldHeight = 256


class WorldDataClient:
    LogLevel = logging.WARNING


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
