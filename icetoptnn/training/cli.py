"""
    IceTop-TNN train subcommand
"""

from pathlib import Path;
import random;
import argparse;

import torch;
from torch.utils.data import random_split;
import yaml;

from graphnet.data.dataloader import DataLoader;
from graphnet.data.dataset import SQLiteDataset, EnsembleDataset;
from graphnet.models import StandardModel;
from graphnet.models.data_representation.graphs import EdgelessGraph, NodesAsPulses, KNNGraph;
from graphnet.models.detector import IceCube86;
from graphnet.models.gnn import DynEdge;
from graphnet.models.transformer import ISeeCube;
from graphnet.models.rnn import Node_RNN;
from graphnet.models.task.reconstruction import AzimuthReconstruction, ZenithReconstruction, EnergyReconstruction;
from graphnet.training.loss_functions import MSELoss;

from ..model.demo import DemoModel;
from ..util import load_datasets;
from .training_info import TrainedModelInfo;

# Arguments make these actual arguments or YAML things later!!!
INPUT_FEATURES = [ 'dom_x', 'dom_y', 'dom_z', 'dom_time', 'charge', 'rde', 'pmt_area', 'hlc' ];
INPUT_TRUTH    = [ 'energy' ];

# More hardcoded nonsense!
SPLIT_TRAINING   = 0.7;
SPLIT_VALIDATION = 0.1;
SPLIT_TESTING    = 0.2;

# TODO: change these
DEFAULT_SEED_SPLIT = 1234567;

# more!
BATCH_SIZE = 64;

def apply_arguments(subparsers) -> None:
    """Add arguments to the train subcommand"""

    ap_root_parser = subparsers.add_parser('train', help='train graphnet models',
                                           description=
                                           'Trains a model using GraphNeT. Everything is currently hardcoded.');

    ap_root_parser.add_argument(metavar='output', type=Path, help='output directory', dest='train_output');
    ap_root_parser.add_argument(metavar='datasets', type=Path, help='input dataset', dest='train_datasets',
                                nargs='+');

    ap_root_parser.add_argument('-G', type=int, help='use gpu', dest='train_usegpus',
                                action='append')

    ap_root_parser.add_argument('-e', type=int, help='max epochs', dest='train_maxepochs',
                                default=100);
    ap_root_parser.add_argument('-B', type=int, help='batch size', dest='train_batchsize',
                                default=64);

    ap_root_parser.add_argument('--split-seed', type=int, dest='train_splitseed',
                                help='seed to use when splitting the dataset',
                                default=DEFAULT_SEED_SPLIT);

    ap_root_parser.add_argument('--loader-workers', type=int, dest='train_loaderworkers',
                                help='number of workers to use for each data loader',
                                default = 1);

    return

def main(args: argparse.Namespace) -> None:
    """Train subcommand entry point"""

    # validate args
    if not args.train_output.parent.is_dir():
        raise NotADirectoryError(f'output parent directory "{args.train_output}" is not a directory');
    if args.train_output.is_dir() and len([1 for _ in args.train_output.iterdir()]) > 0:
        raise Exception(f'output directory "{args.train_output}" is not empty');
    if not args.train_output.exists():
        args.train_output.mkdir();

    if len(args.train_datasets) != 1:
        raise Exception(f'The ability to use multiple datasets is currently broken');

    # graph def
    graph_definition = KNNGraph(
        detector = IceCube86(),
        input_feature_names = INPUT_FEATURES,
        node_definition = NodesAsPulses(),
        nb_nearest_neighbours = 20
    );

    # make dataset
    dataset = load_datasets(args.train_datasets, graph_definition, INPUT_FEATURES, INPUT_TRUTH);

    # split dataset
    datasplit_training, datasplit_validation, datasplit_testing = random_split(
        dataset,
        [ SPLIT_TRAINING, SPLIT_VALIDATION, SPLIT_TESTING ],
        torch.Generator().manual_seed(args.train_splitseed)
    );

    loader_training = DataLoader(datasplit_training, batch_size = BATCH_SIZE, shuffle=True,
                                 num_workers=args.train_loaderworkers);
    loader_validation = DataLoader(datasplit_validation, batch_size = BATCH_SIZE, shuffle=False,
                                   num_workers=args.train_loaderworkers);

    # todo: actually implement training
    backbone = DynEdge(
        nb_inputs = len(INPUT_FEATURES),
        nb_neighbours = 20,
        post_processing_layer_sizes = [512, 256],
        readout_layer_sizes = [512, 256],
        global_pooling_schemes = [ 'max', 'mean' ],
        add_global_variables_after_pooling = False,
    );

    model = StandardModel(
        graph_definition = graph_definition,
        backbone = backbone,
        tasks = [
            EnergyReconstruction(
                hidden_size = 256,
                loss_function = MSELoss(),
            )
        ]
    );

    # train
    model.fit(loader_training, loader_validation, max_epochs=20, gpus=args.train_usegpus)

    # create training info structure
    info = TrainedModelInfo();
    info.seed_split = args.train_splitseed;
    info.split_training = SPLIT_TRAINING;
    info.split_validation = SPLIT_VALIDATION;
    info.split_testing = SPLIT_TESTING;
    info.vset_features = INPUT_FEATURES;
    info.vset_truth = INPUT_TRUTH;
    info.datasets = args.train_datasets;

    # save model
    model.save_config(str(args.train_output / 'config.yml'));
    model.save_state_dict(str(args.train_output / 'weights.pth'));
    yaml.dump(info, open(args.train_output / 'model.yml', 'w'));

    return
