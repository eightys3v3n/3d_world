#!/bin/bash

VENV="../3d_world_venv"

[[ -d $VENV ]] && . $VENV/bin/activate || echo "No venv detected at " $VENV # Activate the virtual environment if there is one.

alias run='rm -f main.log; clear; python -O main.py' # Run the application to play test.
alias debug='rm -f main.log; clear; python main.py' # Run the application with intent to debug it.
alias test='rm -f test.log; clear; python -m unittest *.py' # Run all the non-exhaustive tests.
alias profile='rm -f main.prof main.log; clear; python main.py profile && python -m snakeviz main.prof' # Profile the application and view the profile info with snakeviz.
