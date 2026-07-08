"""
    IceTop-TNN eval subcommand
"""

import argparse;
from pathlib import Path;

import torch;
from torch.nn.modules import instancenorm
from torch.utils.data import random_split;
import yaml;

from graphnet.data.dataset.dataset import GraphDefinition
from graphnet.data.dataloader import DataLoader;
from graphnet.models import Model, StandardModel;
from graphnet.models.data_representation.graphs import graph_definition
from graphnet.utilities.config import ModelConfig

from ..training.training_info import TrainedModelInfo;
from ..util import load_datasets;

def apply_arguments(subparsers) -> None:
    """Add arguments to the eval subcommand"""

    ap_root_parser = subparsers.add_parser('eval', help='evaluate graphnet models',
                                           description='Evaluates a model using GraphNeT');

    ap_root_parser.add_argument(metavar='output', type=Path, dest='eval_output',
                                help='output directory');
    ap_root_parser.add_argument(metavar='model', type=Path, dest='eval_model',
                                help='model directory');

    ap_root_parser.add_argument('-G', type=int, help='use gpu', dest='eval_usegpus',
                                action='append');

    return;

def main(args: argparse.Namespace) -> None:
    """Evaluate a model"""

    # validate args
    if not args.eval_output.parent.is_dir():
        raise NotADirectoryError(f'{args.eval_output.parent} is not a directory');
    if args.eval_output.exists() and not args.eval_output.is_dir():
        raise NotADirectoryError(f'{args.eval_output} is not a directory');
    if args.eval_output.is_dir() and len([ent for ent in args.eval_output.iterdir()]):
        raise Exception(f'{args.eval_output} exists and is not empty');

    if not args.eval_model.is_dir():
        raise NotADirectoryError(f'{args.eval_model} is not a directory');
    if not (args.eval_model/'config.yml').is_file():
        raise FileNotFoundError(f'{args.eval_model} has no config.yml');
    if not (args.eval_model/'weights.pth').is_file():
        raise FileNotFoundError(f'{args.eval_model} has no weights.pth');
    if not (args.eval_model/'model.yml').is_file():
        raise FileNotFoundError(f'{args.eval_model} has no model.yml');

    # load model info
    model_info = yaml.load(open(args.eval_model/'model.yml'), yaml.Loader);
    if not isinstance(model_info, TrainedModelInfo):
        raise TypeError(f'Model file is unexpected type {type(model_info)}');

    # load model
    model_config = ModelConfig.load(str(args.eval_model/'config.yml'));
    model = Model.from_config(model_config, trust=True); # super secure :)
    graph_definition = GraphDefinition.from_config(model_config.arguments['graph_definition']);

    if not isinstance(model, StandardModel):
        raise TypeError('Model is not a StandardModel instance');

    # load dataset
    dataset = load_datasets(model_info.datasets, graph_definition,
                            model_info.vset_features, model_info.vset_truth)

    # split dataset
    _, _, datasplit_testing = random_split(
        dataset,
        [ model_info.split_training, model_info.split_validation, model_info.split_testing ],
        torch.Generator().manual_seed(model_info.seed_split)
    );

    loader = DataLoader(datasplit_testing, batch_size=64);

    # predict
    results = model.predict_as_dataframe(
        loader,
        additional_attributes=['event_no'] + model.target_labels,
        gpus=args.eval_usegpus
    );

    # save output
    if not args.eval_output.exists():
        args.eval_output.mkdir();

    results.to_csv(str(args.eval_output/'results.csv'));

    return
