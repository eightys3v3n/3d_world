from enum import Enum, unique


class WorldDataServer:
    MainConnectionName = 'Main'
    RandomIDLength = 5
    ConnectionWaitTime = 1


@unique
class WorldRequests(Enum):
    # Commands
    PingReq = 'ping'
    NewClientReq = 'new_client'

@unique
class WorldRequestData(Enum):
    # Data fields
    Pong = 'pong'
    NewClientName = 'new_client_name'
    NewClient = 'new_client'
