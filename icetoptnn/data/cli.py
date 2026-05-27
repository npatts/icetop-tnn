"""
    Training data management CLI interface
"""

from argparse import ArgumentParser, Namespace;
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

def apply_arguments(subcommand: ArgumentParser) -> None:
    """Apply arguments to the data subcommand"""
    global ap_root_parser, ap_create_parser;
    
    ap_root_parser = subcommand;
    ap_root_subparsers = subcommand.add_subparsers(title='subcommands', dest='data_subcommand')

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
        if not util.prompt_yn(f'The output directory "{args.data_create_output}" already exists. Continue?'):
            exit(1);

    DataConverter(
        file_reader = I3Reader(gcd_rescue=args.data_create_gcd),
        save_method = ParquetWriter(),
        outdir = args.data_create_output,
        extractors = [ I3GenericExtractor() ]
    )(args.data_create_inputs);

