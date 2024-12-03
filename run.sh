#!/bin/bash

# Activate the virtual environment
source myvenv/bin/activate

# Check for the -v flag
if [[ "$1" == "-v" ]]; then
    # Run in foreground (verbose mode)
    shift  # Remove the first argument
    python3 app.py "$@"  # Pass all remaining arguments to app.py
else
    # Run in detached mode
    nohup python3 app.py "$@" > app.log 2>&1 &  # Pass all arguments to app.py
    echo "Application is running in detached mode. Check app.log for details."
fi
