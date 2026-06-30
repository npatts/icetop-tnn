"""
    IceTop-TNN train subcommand
"""

from pathlib import Path;
import argparse;

import torch;

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

def apply_arguments(subparsers) -> None:
    """Add arguments to the train subcommand"""

    ap_root_parser = subparsers.add_parser('train', help='train graphnet models',
                                           description=
                                           'Trains a model using GraphNeT. Everything is currently hardcoded.');

    ap_root_parser.add_argument(metavar='output', type=Path, help='output directory', dest='train_output');
    ap_root_parser.add_argument(metavar='datasets', type=Path, help='input dataset', dest='train_datasets',
                                nargs='+');

    ap_root_parser.add_argument('-G', type=int, help='use gpu', dest='train_usegpus',
                                nargs='+')

    return

def main(args: argparse.Namespace) -> None:
    """Train subcommand entry point"""

    # Arguments make these actual arguments or YAML things later!!!
    INPUT_FEATURES = [ 'dom_x', 'dom_y', 'dom_z', 'dom_time', 'charge', 'rde', 'pmt_area', 'hlc' ];

    # validate args
    if not args.train_output.parent.is_dir():
        raise NotADirectoryError(f'output parent directory "{args.train_output}" is not a directory');
    if args.train_output.is_dir() and len(args.train_output.iterdir()) > 0:
        raise Exception(f'output directory "{args.train_output}" is not empty');

    input_datasets = [];
    for i in args.train_datasets:
        if not i.is_dir():
            raise NotADirectoryError(f'input dataset "{i}" is not a directory');
        if not (i/'merged/events.db').is_file():
            raise FileNotFoundError(f'input dataset "{i}" is not a icetop-tnn dataset');

    # graph def
    graph_definition = KNNGraph(
        detector = IceCube86(),
        input_feature_names = INPUT_FEATURES,
        node_definition = NodesAsPulses(),
        nb_nearest_neighbours = 20
    );

    # set up dataset list
    for i in args.train_datasets:
        ds = SQLiteDataset(
            path = str(i.absolute()/'merged/events.db'),
            pulsemaps=[ 'OfflineIceTopHLCTankPulses' ],
            truth_table = 'truth',
            features = INPUT_FEATURES,
            truth = [ 'energy' ],
            graph_definition = graph_definition
        );

        input_datasets.append(ds);

    # make ensemble
    dataset = EnsembleDataset(input_datasets);
    input_datasets[0].config.selection = {
        'train': '2000 random events',
        'test':  '5000 random events'
    };

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

    loader = DataLoader(
        input_datasets[0]['train'],
        batch_size=16
    );

    # train
    model.fit(loader, max_epochs=20, gpus=args.train_usegpus)

    # log result to model output
    result = model.predict_as_dataframe(input_datasets[0]['validation']);
    (args.train_output / 'logs/' ).mkdir();
    result.to_csv(str(args.train_output / 'logs/loss.csv'));

    return
