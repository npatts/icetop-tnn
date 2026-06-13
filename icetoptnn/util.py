"""
    util.py - Misc. utility functions.
"""

import sys;
import pathlib;
import math;

# KNOWN_EXTENSIONS = [ '.i3', '.i3.gz', '.i3.bz2', '.root', '.h5' ];
# SKIPPED_EXTENSIONS = [ '.root', '.h5' ];
I3FILE_EXTENSIONS = [ '.i3', '.i3.gz', '.i3.bz2' ];

STORAGE_SUFFIXES = [ 'K', 'M', 'G', 'T' ];

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

def parse_storage(string: str) -> int:
    """Parse a storage string into an integer representing the number of bytes it represents"""

    amount = 0;
    index = 0;
    magnitude = 0;
    base = 1000;

    # find end of number part
    for c in string:
        if c.isdigit() or c == '.':
            index += 1;
        else:
            break;

    # parse amount
    amount = float(string[:index]);

    # apply suffixes
    for c in string[index:]:
        if c == 'B':
            continue;
        elif c == 'i':
            base = 1024;
        elif c in STORAGE_SUFFIXES:
            magnitude = STORAGE_SUFFIXES.index(c) + 1;
        else:
            raise(Exception(f"Unknown storage suffix \"{c}\""));
    
    # math
    return math.ceil(amount * pow(base, magnitude));

