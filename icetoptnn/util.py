"""
    util.py - Misc. utility functions.
"""

import sys;
import pathlib;

# KNOWN_EXTENSIONS = [ '.i3', '.i3.gz', '.i3.bz2', '.root', '.h5' ];
# SKIPPED_EXTENSIONS = [ '.root', '.h5' ];
I3FILE_EXTENSIONS = [ '.i3', '.i3.gz', '.i3.bz2' ];

def get_ext(name: str, allowed: list[str]) -> tuple[str, str, bool]:
    """Split a file into it's name and extension using a list of allowed extensions"""

    for ext in sorted(allowed, key=lambda a: -len(a)):
        if (name.endswith(ext)):
            return (name[:-len(ext)], ext, True);

    return (name, "", False);

def validate_ext(name: str, allowed: list[str]) -> tuple[str, str]:
    """
        Split a file into it's name and extension using a list of allowed extensions and raise an error
        if a valid extension is not found
    """
    
    name, ext, found = get_ext(name, allowed)
    if not found:
        raise Exception(f'Unexpected file extension on {name} (want {allowed})');

    return (name, ext);

def get_project_root() -> pathlib.Path:
    """Get the root directory if the IceTop-GNN repository"""

    return pathlib.Path(sys.argv[0]).resolve().parents[1];

def prompt_yn(prompt: str) -> bool:
    """Display a yes/no prompt to the user"""

    while True:
        print(prompt + ' (y/n): ', file=sys.stderr, end='');

        match input().lower():
            case 'y': return True;
            case 'n': return False;
            case  _:  continue;
