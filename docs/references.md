## Positions:
### Chunk:Block
A chunk:block position is composed of a (cx, cy) for the chunk's x and y position. As well as a (bx, by, bz) for a block inside that chunk. The block positions are relative to the chunks SW corner and increase to the NE. by is the up and down, bx and bz are north/south and east/west.
### Absolute Block
An absolute block position (abx, aby, abz) is a block's position relative to the (0, 0, 0) block in the world.
### Examples
- Chunk:Block of this converts to Absolute Block of this; if the ChunkSize is 16 blocks.
- (0, 0):(1, 1, 1) -> (1, 1, 1)
- (1, 1):(0, 0, 0) -> (16, 0, 16)
