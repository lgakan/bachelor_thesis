#!/bin/bash

python -m venv venv

UNIX_ACTIVATE=venv/bin/activate
WIN_ACTIVATE=venv/Scripts/activate

if [ -f "$UNIX_ACTIVATE" ]; then
  echo "Running build system on UNIX-based system."
  . venv/bin/activate
elif [ -f "$WIN_ACTIVATE" ]; then
  echo "Running build system on Windows."
  venv/Scripts/activate
else
  echo "VENV run failed."
  return 1
fi

python -m pip install -r requirements.txt
