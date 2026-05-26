"""
    util.py - Misc. utility functions.
"""

import sys;
import pathlib;

def get_project_root() -> pathlib.Path:
    """Get the root directory if the IceTop-GNN repository"""
    return pathlib.Path(sys.argv[0]).resolve().parents[1];

def prompt_yn(prompt: str) -> bool:
    while True:
        print(prompt + ' (y/n): ', file=sys.stderr, end='');

        match input().lower():
            case 'y': return True;
            case 'n': return False;
            case  _:  continue;
