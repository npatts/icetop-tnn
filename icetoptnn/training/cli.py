"""
    IceTop-TNN train subcommand
"""

import argparse;

from graphnet.models import StandardModel;
from graphnet.models.data_representation.graphs import EdgelessGraph;
from graphnet.models.detector.icecube import IceCubeUpgrade;
from graphnet.models.transformer import ISeeCube;
from graphnet.models.task.reconstruction import AzimuthReconstruction, ZenithReconstruction
from graphnet.training.loss_functions import MSELoss;

def apply_arguments(subcommand) -> None:
    """Add arguments to the train subcommand"""
    
    return

def main(args: argparse.Namespace) -> None:
    """Train subcommand entry point"""

    # todo: actually implement training
    backbone = ISeeCube();
    
    model = StandardModel(
        graph_definition = EdgelessGraph(detector = IceCubeUpgrade()),
        backbone = backbone,
        tasks = [
            AzimuthReconstruction(1, loss_function = MSELoss()),
            ZenithReconstruction(1, loss_function = MSELoss())
        ]
    )

    return
