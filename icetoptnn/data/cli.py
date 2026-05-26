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
                                                     help='create a dataset from raw icecube events')
    ap_create_parser.add_argument(metavar='output', type=Path, help='output file path', dest='data_create_output',
                                  default='./data.parquet')
    ap_create_parser.add_argument(metavar='input', type=Path, help='input file path', dest='data_create_inputs', nargs='+',
                                  default='./data.i3')

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
            print(f'error: input file "{file}" does not exist', file=sys.stderr);
            exit(1);

    if args.data_create_output.is_dir():
        print(f'error: output file "{args.data_create_output}" is a directory', file=sys.stderr);
        exit(1);

    if args.data_create_output.exists():
        if not util.prompt_yn(f'The output file "{args.data_create_output}" already exists. Replace it?'):
            exit(1);

    # todo
    with TemporaryDirectory() as workdir:
        converter = DataConverter(
            file_reader = I3Reader(),
            save_method = ParquetWriter(),
            outdir = workdir,
            extractors = [ I3GenericExtractor() ]
        );

        converter.merge_files();

        print(workdir);
