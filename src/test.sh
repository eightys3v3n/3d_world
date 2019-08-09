clear; rm test.log; python -m unittest block chunk world_data world_generator world_renderer generations || cat test.log | tail -40
