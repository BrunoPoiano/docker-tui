#!/bin/bash

SCRIPT_PATH=$(realpath docker-tui.py)

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "Error: Script not found at $SCRIPT_PATH"
  exit 1
fi

chmod +x "$SCRIPT_PATH"

sudo ln -sf $SCRIPT_PATH "/usr/local/bin/docker-tui"

echo "Symbolic link created. You can now run your script using the command: docker-tui"
