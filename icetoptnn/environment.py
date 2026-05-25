"""
    environment.py - IceTop-TNN environment.txt interface
"""

import pathlib;
from typing import overload;

state = {};

# TODO: this does no validation whatsoever and doesn't handle quotes
def reload(path: pathlib.Path) -> None:
    """Reload the environment.txt file from the specified path"""
    global state;

    # clear state
    state = {};

    # read in environment.txt
    for line in path.read_text().split("\n"):
        line = line.strip();
        if line == '':
            continue;

        (name, _, value) = line.partition('=');
        state[name] = value;

    return;

@overload
def get(key: str) -> str|None: pass;
@overload
def get(key: str, default: str) -> str: pass;
def get(key: str, default: str|None = None) -> str|None:
    """Get an environment value"""

    return state[key] if key in state else default;
