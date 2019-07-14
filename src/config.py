from enum import Enum, unique


class WorldDataServer:
    MainConnectionName = 'Main'
    RandomIDLength = 5
    ConnectionWaitTime = 1
    ChunkSize = 16
    ChunkHexLength = 6 # This is 1-512. It trims a SHA 512 hash to this length to identify chunks.
    WorldHeight = 1024
    TestingLog = 'test.log'



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
