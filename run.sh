#!/bin/bash

# Activate the virtual environment
source myvenv/bin/activate

# Check for the -v flag
if [[ "$1" == "-v" ]]; then
    # Run in foreground (verbose mode)
    python3 app.py
else
    # Run in detached mode
    nohup python3 app.py > app.log 2>&1 &
    echo "Application is running in detached mode. Check app.log for details."
fi
