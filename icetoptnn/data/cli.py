"""
    Training data management CLI interface
"""

from argparse import ArgumentParser, Namespace;
from os import get_exec_path, pardir, system
from tempfile import TemporaryDirectory;
from pathlib import Path;
import functools;
import sys;
import gzip;

from icecube import dataclasses, icetray, dataio;
import icecube.frame_object_diff.segments as frame_object_diff;

from graphnet.data.dataconverter import DataConverter;
from graphnet.data.extractors.icecube import I3FeatureExtractorIceCube86, I3TruthExtractor;
from graphnet.data.readers import I3Reader;
from graphnet.data.writers import SQLiteWriter;

from ..util import I3FILE_EXTENSIONS, prompt_yn, validate_ext;
from .      import input as tnninput

ap_root_parser:   ArgumentParser;
ap_create_parser: ArgumentParser;

class EventFiles:
    """IceTop event files"""

    layout: str;
    """The GCD layout to use"""

    paths: list[Path];
    """Paths to the files to use"""

class TrackedGCD:
    """
        A single* IceTop GCD file

        *single does not include base files in frame diffs
    """

    path: Path;
    """Path to the GCD file"""

    refcount: int = 0;
    """Number if event file groups referencing this GCD"""

# All events
events: list[EventFiles] = [];

# All GCDs located by the current create op
gcds: dict[str, TrackedGCD] = {};

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
    ap_create_parser.add_argument('-G', type=Path, dest='data_create_recoverygcd',
                                  help='Use the specified GCD as a placeholder if a event has no associated GCD');

    ap_create_parser.add_argument('-C', dest='data_create_htcondor',
                                  action='store_true',
                                  help='Set the script to use HTCondor.');
    ap_create_parser.add_argument('-W', type=int, dest='data_create_workers',
                                  help='Number of workers to use.',
                                  default=1);

    return

def main(args: Namespace) -> None:
    """`data` subcommand entry point"""
    global ap_root_parser;

    match args.data_subcommand:
        case 'create':
            sub_create(args); # TODO: All of this is probably going to have to get split into a different file ATP
        case _:
            print('error: no subcommand specified', file=sys.stderr);
            ap_root_parser.print_help();
            exit(1);

def sub_create(args: Namespace) -> None:
    """`data create` subcommand entry point"""

    # Validate arguments
    for file in args.data_create_inputs:
        if not file.exists():
            raise FileNotFoundError(f'error: input "{file}" does not exist');

    if args.data_create_output.exists():
        if not args.data_create_output.is_dir():
            raise NotADirectoryError(f'output "{args.data_create_output}" is not a directory');
    elif not args.data_create_output.parent.exists():
        raise FileNotFoundError(f'"{args.data_create_output.parent}" is not a directory');
    else:
        args.data_create_output.mkdir(parents=False);

    if args.data_create_recoverygcd is not None and not args.data_create_recoverygcd.exists():
        raise FileNotFoundError(f'placeholder gcd "{args.data_create_recoverygcd}" does not exist');

    if sum(1 for _ in args.data_create_output.iterdir()) != 0:
        if not prompt_yn(f'The output directory "{args.data_create_output}" already exists. This WILL cause problems. Continue?'):
            exit(1);

    # TODO(npatts): Don't hardcode this
    # Find event files
    for root in args.data_create_inputs:
        # Input file system
        if root.suffix != '.yml':
            raise NotADirectoryError(f"Input \"{root}\" is not an input definition");

        definition = tnninput.read_input_definition(root);
        for file_set in definition.get_files():
            match file_set.resource:
                case tnninput.InputResourceType.EVENT:
                    take_events(file_set.layout, file_set.files);

                case tnninput.InputResourceType.GCD:
                    if len(file_set.files) != 1:
                        raise Exception(f"Length of GCD file set must be 1, got {len(file_set.files)}");

                    take_gcd(file_set.layout, file_set.files[0]);

    # "Validate" i3file path and check for unneeded gcdfiles
    for group in events:
        # link to recovery gcd if we don't have one already
        # TODO(npatts): this is bad. the recovery gcd will be processed multiple times in the uncompress step if it isn't a complete gcd.
        if not group.layout in gcds:
            if args.data_create_recoverygcd is not None:
                # TODO: npatts ????-??-??: HANDLE ALL EXTENSIONS IN THE FILE
                #       npatts 2026-06-12: What did she mean by this?
                _, ext = validate_ext(args.data_create_recoverygcd.name, I3FILE_EXTENSIONS);
                take_gcd(group.layout, args.data_create_recoverygcd)
            else:
                raise Exception(f'No GCD for layout {group.layout}');

        # increment layout refcount
        gcds[group.layout].refcount += 1;

    # Remove GCDs that we don't need
    for name, gcd in list(gcds.items()):
        if gcd.refcount == 0:
            del gcds[name];

    # TODO: Deduplicate file paths?

    # Get going
    if args.data_create_htcondor:
        execute_remote(args);
    else:
        execute_local(args);

def take_events(layout: str, files: list[Path]) -> None:
    """Track an event group"""

    group = EventFiles();
    group.layout = layout;
    group.paths = files;
    events.append(group);

def take_gcd(name: str, file: Path) -> None:
    """Track a GCD file"""

    if not file.exists() or file.is_dir():
        raise FileNotFoundError(f"GCD file \"{file}\" is not a file");

    if name in gcds:
        raise Exception(f'Duplicate GCD file: "{gcds[name].path}" "{file}"');
    
    newgcd = TrackedGCD();
    newgcd.path = file;
    gcds[name] = newgcd;

def bind(path: Path, target: Path) -> None:
    """Add a file to the datagen directory""";

    if path.name.endswith('.i3'): # GraphNeT ignores i3files unless they're compressed.
        with gzip.open(path.parent/(path.name+'.gz'), 'wb', 9) as out:
            with open(target, 'rb') as src:
                out.write(src.read());
    else:
        path.symlink_to(target.absolute());

def decompress_gcd(path: Path, output: Path) -> None:
    """Decompress a GCD file compressed with frame_object_diff"""

    # Decompress diffs with IceTray
    tray = icetray.I3Tray();
    tray.Add('I3Reader', Filename=path.as_posix());
    tray.Add('Dump');
    tray.Add(frame_object_diff.uncompress) # TODO(npatts): in the future, i would like this to use something custom that can reroute file paths from one prefix to another (eg /data to ~/Documents/data)
                                           #               until then, if using compressed gcds, it will not be possible to run datagen outside of icecube servers
    tray.Add('Dump');
    tray.Add('I3Writer', Filename=output.as_posix());
    tray.Execute();

    return

def execute_remote(args: Namespace):
    """Run the data generator on a Condor cluster"""

    

    pass;

def execute_local(args: Namespace):
    """Run the data generator locally."""

    # Run the data generator
    with TemporaryDirectory(prefix='icetop-tnn-datagen.') as merged:
        # Create layout directories
        for layout, trackedgcd in gcds.items():
            _, ext = validate_ext(trackedgcd.path.name, I3FILE_EXTENSIONS);

            (Path(merged)/layout).mkdir();
            decompress_gcd(trackedgcd.path, Path(merged)/layout/f'layout.gcd{ext}');

        # Populate layout directories
        seq = 0;
        for group in events:
            for path in group.paths:
                bind(Path(merged)/group.layout/f'{seq}--{path.name}', path);
                seq += 1;

        try:
            # Hand off to GraphNeT
            converter = DataConverter(
                file_reader = I3Reader(gcd_rescue='/@/invalid/gcd-not-linked-you-should-never-see-this-something-is-very-very-wrong'),
                save_method = SQLiteWriter(merged_database_name='events'), # events.db :roaches_beetles:
                outdir = str(args.data_create_output),
                extractors = [ 
                    I3TruthExtractor(ice_top = True), # TODO: ice_top should be a datagen argument
                    I3FeatureExtractorIceCube86("OfflineIceTopHLCTankPulses") # Should we be using SLC instead?
                ],
                num_workers=args.data_create_workers
            );

            # Let it rip
            converter([merged])

            # Merge generated databases
            # GraphNeT claims there's a database_name argument, but there actually isn't. It uses
            # the merged_database_name argument on the converter constructor instead. (outputs to events.sqlite)
            converter.merge_files(
                files = [ str(f) for f in args.data_create_output.iterdir() ],
                output_dir = str(args.data_create_output),
                remove_originals = True
            );

            input()
        except Exception as e:
            print(e);
            input();
            raise e;

