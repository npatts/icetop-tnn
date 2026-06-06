"""
    Training data management CLI interface
"""

from argparse import ArgumentParser, Namespace;
from os import pardir, system
from tempfile import TemporaryDirectory;
from pathlib import Path;
import sys;
import gzip;

from icecube import dataclasses, icetray, dataio;
import icecube.frame_object_diff.segments as frame_object_diff;

from graphnet.data.dataconverter import DataConverter;
from graphnet.data.extractors.icecube import I3TruthExtractor
from graphnet.data.readers import I3Reader;
from graphnet.data.writers import ParquetWriter;
from graphnet.data.extractors.icecube.i3genericextractor import I3FeatureExtractor;

from .diff_inflate import GCDDecompressor;
from .. import environment, util;

ap_root_parser:   ArgumentParser;
ap_create_parser: ArgumentParser;

KNOWN_EXTENSIONS = [ '.i3', '.i3.gz', '.i3.bz2', '.root', '.h5' ];
SKIPPED_EXTENSIONS = [ '.root', '.h5' ];
I3FILE_EXTENSIONS = [ '.i3', '.i3.gz', '.i3.bz2' ];

class SubDataset:
    """IceTop sub-dataset"""

    # Composition
    composition: str;

    # Energy levels
    energy_min: float;
    energy_max: float;

    # Events
    # (Path path, str extension, str layout)
    i3files: list[tuple[Path, str, str]] = [];

class TrackedGCD:
    """
        A single* IceTop GCD file

        *single does not include base files in frame diffs
    """

    # File path
    path: Path;

    # File extension
    extension: str;

    # Number of i3files referencing this GCD
    refcount: int = 0;

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

    return

def main(args: Namespace) -> None:
    """`data` subcommand entry point"""
    global ap_root_parser;

    match args.data_subcommand:
        case 'create':
            sub_create(args);
        case _:
            print('error: no subcommand specified', file=sys.stderr);
            ap_root_parser.print_help();
            exit(1);

def sub_create(args: Namespace) -> None:
    """`data create` subcommand entry point"""

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
        exit(1);
    else:
        args.data_create_output.mkdir(parents=False);

    if args.data_create_recoverygcd is not None and not args.data_create_recoverygcd.exists():
        print(f'error: placeholder gcd "{args.data_create_recoverygcd}" does not exist');
        exit(1);

    if sum(1 for _ in args.data_create_output.iterdir()) != 0:
        if not util.prompt_yn(f'The output directory "{args.data_create_output}" already exists. Continue?'):
            exit(1);

    subdatasets: dict[str, SubDataset] = {}

    # str layout -> Path path, str extension
    gcds: dict[str, TrackedGCD] = {}

    # TODO(npatts): Don't hardcode this
    # Find event files
    for root in args.data_create_inputs:
        for dir, _, files in root.walk():
            for file in files:
                (name, ext) = get_ext(file, KNOWN_EXTENSIONS);
                if ext in SKIPPED_EXTENSIONS:
                    continue;

                match name.split('_'):
                    case ['Level3', layout, 'GCD']:
                        take_gcd(gcds, layout, dir/file, ext);
                    case ['Level3', 'IC86.2012', 'SIBYLL2.1', composition, layout, event]:
                        take_event(subdatasets, dir.parent.name, dir/file, ext, layout, composition, float(dir.name));
                    case ['Level3', 'IC86.2012', 'SIBYLL2.1', composition, 'thinned', layout, event]:
                        pass;
                    case ['Level3', 'IC86.2012', 'SIBYLL2.1', composition, layout, energyraw, energylevelevent]:
                        if energyraw[0] != 'E': raise Exception(f'Unrecognized file name pattern {file}');
                        take_event(subdatasets, dir.name, dir/file, ext, layout, composition, float(energyraw[1:]));
                    case ['Level3', 'IC86.2012', 'SIBYLL2.1', composition, 'thinned', layout, _, _ ]:
                        pass; # skip thinned
                    case _:
                        raise Exception(f'Unrecognized file name pattern {file}');

    # Remove any sub-datasets we don't want.
    for name, sds in list(subdatasets.items()):
        # Remove low/high energy sets, just in case we missed one.
        if sds.energy_min < 5.0 or sds.energy_max > 8.0: del subdatasets[name];

    for name, ds in subdatasets.items():
        print(name);
        print(ds.composition);
        print(ds.energy_min, ds.energy_max);

    # "Validate" i3file path and check for unneeded gcdfiles
    for sds_name, sds in subdatasets.items():
        for path, _, layout in sds.i3files:
            # link to recovery gcd if we don't have one already
            # TODO(npatts): this is bad. the recovery gcd will be processed multiple times in the uncompress step if it isn't a complete gcd.
            if not layout in gcds:
                if args.data_create_recoverygcd is not None:
                    _, ext = get_ext(args.data_create_recoverygcd.name, I3FILE_EXTENSIONS);

                    take_gcd(gcds, layout, args.data_create_recoverygcd, ext)
                else:
                    raise Exception(f'No GCD for layout {layout} (event path: {path})');

            # increment refcount
            gcds[layout].refcount += 1;

    # Remove GCDs that we don't need
    for name, gcd in list(gcds.items()):
        if gcd.refcount == 0:
            del gcds[name];

    # Feedback
    # print(f'Got {len(events)} events');

    with TemporaryDirectory(prefix='icetop-tnn-datagen.') as merged:
        # Create layout directories
        for layout, trackedgcd in gcds.items():
            (Path(merged)/layout).mkdir();
            decompress_gcd(trackedgcd.path, Path(merged)/layout/f'layout.gcd{trackedgcd.extension}');

        # Populate layout directories
        seq = 0;
        for sds_name, sds in subdatasets.items():
            for path, ext, layout in sds.i3files:
                bind(Path(merged)/layout/f'{seq}{ext}', path)
                seq += 1;

        system(f'ls -la {merged}');

        input()

        try:
            # Hand off to GraphNeT
            DataConverter(
                file_reader = I3Reader(gcd_rescue='/@/invalid/gcd-not-linked-you-should-never-see-this-something-is-very-very-wrong'),
                save_method = ParquetWriter(),
                outdir = str(args.data_create_output),
                extractors = [ I3FeatureExtractor() ]
            )([merged]);
        except Exception as e:
            print(e);
            input();
            raise e;

def take_event(subdatasets: dict[str, SubDataset], name: str,
               path: Path, extension: str, layout: str,
               composition: str, energy: float) -> None:
    """Track an event file"""

    # Add new sub-dataset if one does not already exist.
    if not name in subdatasets:
        newds = SubDataset()
        newds.composition = composition;
        newds.energy_min = energy;
        newds.energy_max = energy;
        subdatasets[name] = newds;

        print(f'Registered sub-dataset {name} {{ .c = {composition}, .emin = .emax = {energy} }}');

    # Add the event to the sub-dataset
    if subdatasets[name].composition != composition: raise Exception(f'{subdatasets[name].composition} != {composition}');

    subdatasets[name].i3files.append((path, extension, layout));
    subdatasets[name].energy_min = min(subdatasets[name].energy_min, energy);
    subdatasets[name].energy_max = max(subdatasets[name].energy_max, energy);

def take_gcd(trackedgcds: dict[str, TrackedGCD], name: str,
             path: Path, extension: str) -> None:
    """Track a GCD file"""

    if name in trackedgcds:
        raise Exception(f'Duplicate GCD file: "{trackedgcds[name].path}" "{path}"');

    newgcd = TrackedGCD();
    newgcd.path = path;
    newgcd.extension = extension;
    trackedgcds[name] = newgcd;


def bind(path: Path, target: Path) -> None:
    """Add a file to the datagen directory""";

    if path.name.endswith('.i3'): # GraphNeT ignores i3files unless they're compressed.
        with gzip.open(path.parent/(path.name+'.gz'), 'wb', 9) as out:
            with open(target, 'rb') as src:
                out.write(src.read());
    else:
        path.symlink_to(target.absolute());

def get_ext(name: str, allowed: list[str]) -> tuple[str, str]:
    """Split a file into it's name and extension using a list of allowed extensions"""

    for ext in sorted(allowed, key=lambda a: -len(a)):
        if (name.endswith(ext)):
            return (name[:-len(ext)], ext);

    raise Exception(f'Unexpected file extension on {name} (want {allowed})');

def decompress_gcd(path: Path, output: Path) -> None:
    """Decompress a GCD file compressed with frame_object_diff"""

    # Decompress diffs with IceTray
    tray = icetray.I3Tray();
    tray.Add('I3Reader', Filename=path.as_posix());
    tray.Add('Dump');
    tray.Add(frame_object_diff.uncompress) # TODO(npatts): in the future, i would like this to use something custom that can reroute file paths from one prefix to another (eg /data to ~/Documents/data)
                                           #               until then, if using compressed gcds, it will not be possible to run datagen outside of icecube servers
    # tray.Add(GCDDecompressor);
    tray.Add('Dump');
    tray.Add('I3Writer', Filename=output.as_posix());
    tray.Execute();

    return
