# Example usage for world_data.py

## Start the server.
### Create a logger (see [logging](logging.md))
### Start the server
```
world_server = WorldDataServer(parent_log)
main_world_client = world_server.get_main_client()
world_server.start()
```
`main_world_client` is now the leaping off point for creating new clients or using the WorldDataServer if you only want one client. It is a WorldDataClient object that is connected to the newly started WorldDataServer object.

## Usage
A WorldDataClient can use these methods to communicate with the server.
ping:        Just for testing or ensuring the server is still connected.
new_client:  Returns another client for other processes or threads to use.
set_chunk:   Sets a specified chunk's Chunk object.
get_chunk:   Returns a specified chunk's Chunk object.
