import argparse;
import sys;

from .training import cli as training_cli;
from .util import get_project_root;

def main() -> None:
    """IceTop-TNN entry point"""

    # Root command/arguments
    ap_root_parser = argparse.ArgumentParser(description='IceTop-TNN command line interface');
    ap_root_subparsers = ap_root_parser.add_subparsers(title='subcommands', dest='subcommand');

    ap_root_parser.add_argument('-v', help='increase verbosity', dest='verbosity',
                                default=0,
                                action='count');
    ap_root_parser.add_argument('--env', type=str, help='override environment.txt path', dest='environment_path',
                                default=get_project_root()/'environment.txt')


    # Datagen command/arguments
    ap_datagen_parser = ap_root_subparsers.add_parser('data', help='training data management');

    # Trainer command/arguments
    training_cli.apply_arguments(ap_root_subparsers.add_parser('train', help='model training'));

    # Parse arguments
    args = ap_root_parser.parse_args();

    # Hand off to subcommands
    match args.subcommand:
        case 'data':
            print('error: not implemented', file=sys.stderr);
        case 'train':
            training_cli.main(args);
        case _:
            # Print help if no subcommand specified
            print('error: no subcommand specified', file=sys.stderr);
            ap_root_parser.print_help();
            exit(1);

main();
exit(0);

