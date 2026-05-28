"""
    Training data management CLI interface
"""

from argparse import ArgumentParser, Namespace;
from os import pardir, system
import sys;
from tempfile import TemporaryDirectory;
from pathlib import Path;

from graphnet.data.dataconverter import DataConverter;
from graphnet.data.readers import I3Reader;
from graphnet.data.writers import ParquetWriter;
from graphnet.data.extractors.icecube.i3genericextractor import I3GenericExtractor;

from .. import environment, util;

ap_root_parser:   ArgumentParser;
ap_create_parser: ArgumentParser;

def apply_arguments(subparsers) -> None:
    """Apply arguments to the data subcommand"""
    global ap_root_parser, ap_create_parser;
    
    ap_root_parser = subparsers.add_parser('data', help='generate graphnet datasets',
                                           description=
                                           'Generates GraphNeT datasets. All input directories are treated as '
                                           'a single input dataset. The generated datasets will be outputted to '
                                           'the output directory.');
    ap_root_subparsers = ap_root_parser.add_subparsers(title='subcommands', dest='data_subcommand')

    ap_create_parser = ap_root_subparsers.add_parser('create',
                                                     help='create datasets from raw icecube events')
    ap_create_parser.add_argument(metavar='output', type=Path, help='output directory', dest='data_create_output',
                                  default='./data/')
    ap_create_parser.add_argument(metavar='input', type=Path, help='input directories', dest='data_create_inputs', nargs='+',
                                  default='./data.i3')
    ap_create_parser.add_argument('-G', type=Path, dest='data_create_gcd',
                                  help='default gcd file, defaults to a non-existent placeholder',
                                  default='/@/invalid/no-gcd-specified');

    return

def main(args: Namespace) -> None:
    """Data subcommand entry point"""
    global ap_root_parser;

    match args.data_subcommand:
        case 'create':
            sub_create(args);
        case _:
            print('error: no subcommand specified', file=sys.stderr);
            ap_root_parser.print_help();
            exit(1);

def sub_create(args: Namespace) -> None:
    # Validate arguments
    for file in args.data_create_inputs:
        if not file.exists():
            print(f'error: input "{file}" does not exist', file=sys.stderr);
            exit(1);
        if not file.is_dir():
            print(f'error: input "{file}" is not a directory', file=sys.stderr);
            exit(1);

    if args.data_create_output.exists():
        if not args.data_create_output.is_dir():
            print(f'error: output "{args.data_create_output}" is not a directory');
            exit(1);
    elif not args.data_create_output.parent.exists():
        print(f'error: "{args.data_create_output.parent}" is not a directory');
    else:
        args.data_create_output.mkdir(parents=False);

    if sum(1 for _ in args.data_create_output.iterdir()) != 0:
        if not util.prompt_yn(f'The output directory "{args.data_create_output}" already exists. Continue?'):
            exit(1);

    # Path path, str extension, str layout
    events: list[tuple[Path, str, str]] = []

    # str layout -> Path path, str extension
    gcds: dict[str, tuple[Path, str]] = {}

    # TODO(npatts): Don't hardcode this
    # Find event files
    for root in args.data_create_inputs:
        for dir, _, files in root.walk():
            for file in files:
                name: str;
                ext: str;
                if file.endswith('.i3.gz'):
                    ext = 'gz';
                    name = file[:-6];
                elif file.endswith('.i3.bz2'):
                    ext = 'bz2';
                    name = file[:-7];
                elif file.endswith('.root') or file.endswith('.h5'): # ignore whatever these are
                    continue
                else:
                    raise Exception(f'Unexpected file extension on {file}');

                # split into components by the delimiter _
                comps: list[str] = name.split('_');

                match comps:
                    case ['Level3', layout, 'GCD']:
                        gcds[layout] = (dir/file, ext);
                    case ['Level3', 'IC86.2012', 'SIBYLL2.1', composition, layout, event]:
                        events.append((dir/file, ext, layout));
                    case ['Level3', 'IC86.2012', 'SIBYLL2.1', composition, 'thinned', layout, event]:
                        pass; # skip thinned
                    case ['Level3', 'IC86.2012', 'SIBYLL2.1', composition, layout, _, _]: # what are these? the second to last is probably energy? what's the last thing?
                        events.append((dir/file, ext, layout));
                    case ['Level3', 'IC86.2012', 'SIBYLL2.1', composition, 'thinned', layout, _, _ ]:
                        pass; # skip thinned
                    case _:
                        raise Exception(f'Unrecognized file name pattern {file}');

    # "Validate" events
    for path, _, layout in events:
        if not layout in gcds:
            raise Exception(f'No GCD for layout {layout} (event path: {path})');

    # Feedback
    print(f'Got {len(events)} events');

    with TemporaryDirectory() as merged:
        # Create layout directories
        for layout, (path, ext) in gcds.items():
            (Path(merged)/layout).mkdir();
            (Path(merged)/layout/f'layout.gcd.i3.{ext}').symlink_to(path);

        # Populate layout directories
        seq = 0;
        for path, ext, layout in events:
            (Path(merged)/layout/f'{seq}.i3.{ext}').symlink_to(path);
            seq += 1;

        system(f'ls -la {merged}');

        DataConverter(
            file_reader = I3Reader(gcd_rescue=str(args.data_create_gcd)),
            save_method = ParquetWriter(),
            outdir = str(args.data_create_output),
            extractors = [ I3GenericExtractor() ]
        )([merged]);

