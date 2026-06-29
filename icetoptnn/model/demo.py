"""
    Test model to check that IceTop-TNN works
"""

import torch;
from torch_geometric.data import Data

from graphnet.models import Model;

class DemoModel(Model):
    def __init__(self,
                 input_dim : int = 5,
                 output_dim : int = 10):

        super().__init__()
        self._layer = torch.nn.Linear(input_dim, output_dim)

    def forward(self, data: Data) -> torch.Tensor:
        x = data.x
        return self._layer(x)
