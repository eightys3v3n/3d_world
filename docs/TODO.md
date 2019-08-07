Improve generation order so it's not always generating NW to SE. Make it radial out from the player.

Add some kind of interface for timing all manner of functions. Then make all the timers configurable in the config.py file.

Break down chunk rendering further so it can be limited by number of blocks per frame. Ideally the config file would specify "only render 200 blocks per frame" to avoid the current stuttering.
This requires creating some kind of queue on the main thread to save chunk data but not use it until next frame.
