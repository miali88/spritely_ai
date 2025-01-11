#!/bin/bash

# Geclt the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Use the virtual environment's Python
PYTHON_PATH="$DIR/venv/bin/python3"

# Run the Python script with the --from-shortcut flag
"$PYTHON_PATH" "$DIR/instant_spritely.py" --from-shortcut