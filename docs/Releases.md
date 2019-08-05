
## Release 807af0b9
### Commit: 807af0b92dc215f83686f01d7fcad8e510f10a70
### Notes:
- Multithread rewrite branch
- DefaultGeneration, 16 block chunks, 1 chunk render distance.
- Large number of chunks are pregenerated on program start to allow for working on the renderer.
- Rendering is done on the main thread; accessing the chunk data from the world data server causes freezes.
