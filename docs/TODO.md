## Remind-mes
- Change the Player.draw_perspective back to not taking a width and height.


## Features
- Improve generation order so it's not always generating NW to SE. Make it radial out from the player.
- Add some kind of interface for timing all manner of functions. Then make all the timers configurable in the config.py file.


## Changes
- Change log messages in WorldDataServer and WorldDataClient to use the names assigned randomly.
- Make renderer throw out the queue more often so chunks rendered are more relevent.


## Bugs
- Chunks are still being re-rendered in some cases when rendering a single chunk takes too long.


## Done:
- Make window resizable.
- Break down chunk rendering further so it can be limited by number of blocks per frame. Ideally the config file would specify "only render 200 blocks per frame" to avoid the current stuttering.
