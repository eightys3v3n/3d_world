from chunk import Chunk
from block import Block
import config


def pick_generation(cx, cy, world_client):
    return DefaultGeneration


class DefaultGeneration:
    name = "Default"

    @classmethod
    def generate(cls, cx, cy, world_client):
        print("Only giving grass blocks in chunk")
        chunk = Chunk()
        for pos in chunk.all_positions():
            if pos[1] < config.WorldDataServer.WorldHeight / 2:
                chunk.set_block(*pos, Block(config.BlockType.Grass))
        return chunk

