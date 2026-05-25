"""
    util.py - Misc. utility functions.
"""

import sys;
import pathlib;

def get_project_root() -> pathlib.Path:
    """Get the root directory if the IceTop-GNN repository"""
    return pathlib.Path(sys.argv[0]).resolve().parents[1];

