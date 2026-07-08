"""
    util.py - Misc. utility functions.
"""

import sys;
from pathlib import Path;
import math;

from graphnet.data.dataset import SQLiteDataset, EnsembleDataset
from graphnet.data.dataset.dataset import GraphDefinition;

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

def get_project_root() -> Path:
    """Get the root directory if the IceTop-GNN repository"""

    return Path(sys.argv[0]).resolve().parents[1];

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

def load_datasets(datasets: list[Path], graphdef: GraphDefinition, features: list[str], truth: list[str],
                  pulsemaps: list[str] = [ 'OfflineIceTopHLCTankPulses' ],
                  truth_table: str = 'truth') -> EnsembleDataset:
    """Load a list of datasets and return an ensemble containing them"""

    # validate
    for i in datasets:
        if not i.is_dir():
            raise NotADirectoryError(f'input dataset "{i}" is not a directory');
        if not (i/'merged/events.db').is_file():
            raise FileNotFoundError(f'input dataset "{i}" is not a icetop-tnn dataset');

    # open
    input_datasets = [];
    for i in datasets:
        ds = SQLiteDataset(
            path = str(i.absolute()/'merged/events.db'),
            pulsemaps = pulsemaps,
            truth_table = truth_table,
            features = features,
            truth = truth,
            graph_definition = graphdef
        );

        input_datasets.append(ds);

    # make dataset
    return EnsembleDataset(input_datasets);
