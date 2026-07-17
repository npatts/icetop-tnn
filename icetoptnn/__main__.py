import argparse;
import sys;
import os;
import pathlib;
import tempfile;

from .evaluation import cli as evaluation_cli;
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
                                default=os.getenv('ICETOPTNN_ENVIRONMENT_PATH') or util.get_project_root()/'environment.txt')

    # Working directory
    ap_root_parser.add_argument('--workdir', type=pathlib.Path, dest='workdir',
                                help='switch to directory before starting. uses temporary directory if set to /:tmp:/', 
                                default=os.getcwd())

    # Condor configuration arguments
    ap_root_parser.add_argument('--condor-scratch', type=pathlib.Path, dest='condor_scratchdir',
                                help='Directory to store files for running DAGs. Should be a shared FS.');
    ap_root_parser.add_argument('--condor-base', type=pathlib.Path, dest='condor_basedir',
                                help='Directory to store condor submit files by default',
                                default=util.get_project_root()/'private/condor/')
    ap_root_parser.add_argument('--condor-stdout', type=pathlib.Path, dest='condor_stdoutdir',
                                help='HTCondor submmission stdout directory')
    ap_root_parser.add_argument('--condor-stderr', type=pathlib.Path, dest='condor_stderrdir',
                                help='HTCondor submmission stderr directory')
    ap_root_parser.add_argument('--condor-logdir', type=pathlib.Path, dest='condor_logdir',
                                help='HTCondor submmission log directory')
    ap_root_parser.add_argument('--condor-submitdir', type=pathlib.Path, dest='condor_submitdir',
                                help='HTCondor submmission file directory')

    # Datagen command/arguments
    data_cli.apply_arguments(ap_root_subparsers);

    # Trainer command/arguments
    training_cli.apply_arguments(ap_root_subparsers);

    # Evaluation command/arguments
    evaluation_cli.apply_arguments(ap_root_subparsers)

    # Parse arguments
    args = ap_root_parser.parse_args();

    # Load environment.txt
    environment.reload(pathlib.Path(args.environment_path).resolve());

    # Apply envtxt based defaults
    if args.condor_scratchdir is None:
        scratch_dir = environment.get('CONDOR_SCRATCH_DIR');
        if scratch_dir is None:
            raise Exception('CONDOR_SCRATCH_DIR is not set and a scratch dir was not provided with --condor-scratch');

        args.condor_scratchdir = pathlib.Path(scratch_dir);

    # Default condor submit dir paths
    if args.condor_stdoutdir is None:
        args.condor_stdoutdir = args.condor_basedir / 'stdout/'
    if args.condor_stderrdir is None:
        args.condor_stderrdir = args.condor_basedir / 'stderr/'
    if args.condor_logdir is None:
        args.condor_logdir = args.condor_basedir / 'log/'
    if args.condor_submitdir is None:
        args.condor_submitdir = args.condor_basedir / 'submit/'

    # Validate arguments
    if not args.condor_scratchdir.exists():
        raise FileNotFoundError(f'Scratch directory "{args.condor_scratchdir}" does not exist');

    # Switch to new working directory
    if args.workdir == pathlib.Path('/:tmp:/'):
        args.workdir = tempfile.mkdtemp(prefix='icetoptnn-workdir.');

    os.chdir(args.workdir);

    # Hand off to subcommands
    match args.subcommand:
        case 'data':
            data_cli.main(args);
        case 'train':
            training_cli.main(args);
        case 'eval':
            evaluation_cli.main(args);
        case _:
            # Print help if no subcommand specified
            print('error: no subcommand specified', file=sys.stderr);
            ap_root_parser.print_help();
            exit(1);

main();
exit(0);

