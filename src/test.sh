clear; rm test.log; python -m unittest block chunk world_data world_generator world_renderer || cat test.log | tail -40
