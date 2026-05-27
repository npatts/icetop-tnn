import argparse;
import sys;
import pathlib;

from .training import cli as training_cli;
from .data import cli as data_cli;
from . import util;
from . import environment;

def main() -> None:
    """IceTop-TNN entry point"""

    # Root command/arguments
    ap_root_parser = argparse.ArgumentParser(description='IceTop-TNN command line interface');
    ap_root_subparsers = ap_root_parser.add_subparsers(title='subcommands', dest='subcommand');

    ap_root_parser.add_argument('-v', help='increase verbosity', dest='verbosity',
                                default=0,
                                action='count');
    ap_root_parser.add_argument('--env', type=str, help='override environment.txt path', dest='environment_path',
                                default=util.get_project_root()/'environment.txt')

    # Datagen command/arguments
    data_cli.apply_arguments(ap_root_subparsers);

    # Trainer command/arguments
    training_cli.apply_arguments(ap_root_subparsers);

    # Parse arguments
    args = ap_root_parser.parse_args();

    # Load environment.txt
    environment.reload(pathlib.Path(args.environment_path).resolve());

    # Hand off to subcommands
    match args.subcommand:
        case 'data':
            data_cli.main(args);
        case 'train':
            training_cli.main(args);
        case _:
            # Print help if no subcommand specified
            print('error: no subcommand specified', file=sys.stderr);
            ap_root_parser.print_help();
            exit(1);

main();
exit(0);

