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

    with TemporaryDirectory() as merged:
        seq = 0;
        for dir in args.data_create_inputs:
            (Path(merged)/str(seq)).symlink_to(Path(dir))
            seq += 1;

        system(f'ls -la {merged}')

        DataConverter(
            file_reader = I3Reader(gcd_rescue=str(args.data_create_gcd)),
            save_method = ParquetWriter(),
            outdir = str(args.data_create_output),
            extractors = [ I3GenericExtractor() ]
        )([merged]);

