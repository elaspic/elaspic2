from typing import NamedTuple

import torch


class ProteinSolverData(NamedTuple):
    x: torch.Tensor
    edge_index: torch.Tensor
    edge_attr: torch.Tensor
