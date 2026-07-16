import math as m;

import torch as t;
from torch import nn;
from torch_geometric import nn as geonn;
from torch_geometric import utils as geoutil;
from torch_geometric.data import Data, feature_store;

from graphnet.models import Model;
from graphnet.models.utils import array_to_sequence;

class IceTopTNNTransformer(Model):
    input_length: int;
    """Number of input features"""

    output_length: int;
    """Number of outputs"""

    positional_encoding_features: tuple[int, int, int];
    """Index into the feature vector(?) with the x, y, and z coordinates of the DOM"""

    positional_encoding_length: int;
    """Dimension of a single part of the positional encoding"""

    positional_encoding_constant: int;
    """The constant used to define the positional encoding. 10000 in the transformer paper"""

    transformer_length: int;
    """Dimension of the transformer part"""

    _encoded_token_dim: int;
    """Dimension of a token with the added position vector, 3l + features - 3"""

    def __init__(self,
                 input_length: int,
                 output_length: int,
                 positional_encoding_features: tuple[int, int, int],
                 positional_encoding_length: int = 2,
                 positional_encoding_constant: int = 10000,
                 transformer_length: int = 16):

        super().__init__()

        self.input_length = input_length;
        self.output_length = output_length;
        self.positional_encoding_features = positional_encoding_features;
        self.positional_encoding_length = positional_encoding_length;
        self.positional_encoding_constant = positional_encoding_constant;
        self.transformer_length = transformer_length;

        self._encoded_token_dim = self.input_length - 3 + 3 * self.positional_encoding_length;

        for f in iter(positional_encoding_features):
            print(f)

        self.linear1 = nn.Linear(self._encoded_token_dim, self._encoded_token_dim)
        self.relu1 = nn.ReLU()
        self.linear2 = nn.Linear(self._encoded_token_dim, self._encoded_token_dim)
        self.relu2 = nn.ReLU()
        self.linear3 = nn.Linear(self._encoded_token_dim, self._encoded_token_dim)
        self.relu3 = nn.ReLU()
        self.readout = nn.Linear(self._encoded_token_dim, self.output_length);


    def forward(self, data: Data) -> t.Tensor:
        # notes to self:
        # data.x     - energy for each pulse, variable length (depends on doms in events)
        # data.index - which event in the batch each data.x value corresponds to

        # dump input data
        x = data.x;
        batch = data.batch;
        self._dump('input(x)', x)
        self._dump('input(batch)', batch)

        # convert x into a set of transformer embeddings
        x = self._embedding(x)
        self._dump('embedding', x)

        # pad all batches to equal length. i was going to implement this myself but i spotted it in gn.m.util
        x, seq_mask, seq_lengths = array_to_sequence(x, batch, 0)
        self._dump('sequence', x)

        # dummy remove this
        x = self.linear1(x);
        self._dump('linear1', x)

        x = self.relu1(x);
        self._dump('relu1', x)

        x = self.linear2(x);
        self._dump('linear2', x)

        x = self.relu2(x);
        self._dump('relu2', x)

        x = self.linear3(x);
        self._dump('linear3', x)

        x = self.relu3(x);
        self._dump('relu3', x)

        x = self.readout(x);
        self._dump('readout', x)

        # get the average of the outputs for each dom
        x = t.mean(x, 1);
        self._dump('squeeze', x)

        # combine outputs for each batch
        # i found this in dynedge, i think i'm using it right???
        # https://pytorch-geometric.readthedocs.io/en/latest/modules/utils.html#torch_geometric.utils.scatter
        # https://pytorch-scatter.readthedocs.io/en/latest/functions/scatter.html
        # x = geoutil.scatter(x, batch, 0, reduce='mean')
        # self._dump('scatter', x)

        return x

    def _embedding(self, x: t.Tensor) -> t.Tensor:
        """Create an embedding for a single DOM"""

        # build encoding
        parts = [];
        for part in range(0, 3):
            # column with feature values
            col = x[:,self.positional_encoding_features[part]]
            
            # build encoding for column
            for i in range(0, self.positional_encoding_length):
                # alternate between sine and cosine
                func = [t.sin, t.cos][i % 2];

                # apply encoding
                col = func(t.div(
                    col, 
                    m.pow(self.positional_encoding_constant, 2 * (i // 2) / self.transformer_length)
                ))

                # add to the things
                parts.append(col)

        # make back into tensor [3len, inputs]
        parts = t.stack(parts, dim=1)

        # get everything not in the positional encoding
        x = t.take_along_dim(
            x,
            t.tensor([[
                v for v 
                   in range(0, self.input_length)
                   if not v in self.positional_encoding_features
            ]]),
            dim=1
        )

        # combine back to make the encoding
        x = t.cat([parts, x], dim=1)

        return x

    def _dump(self, name: str, x: t.Tensor):
        """Vomit huge amounts of data onto the screen for debugging"""

        print(name)
        print(x)
        print(x.size())
