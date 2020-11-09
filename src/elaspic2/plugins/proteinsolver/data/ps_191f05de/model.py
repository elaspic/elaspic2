import atexit
import copy
import csv
import time
import warnings

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.modules.container import ModuleList
from torch_geometric.nn.inits import reset
from torch_geometric.utils import scatter_, to_dense_adj


class EdgeConvMod(torch.nn.Module):
    def __init__(self, nn, aggr="max"):
        super().__init__()
        self.nn = nn
        self.aggr = aggr
        self.reset_parameters()

    def reset_parameters(self):
        reset(self.nn)

    def forward(self, x, edge_index, edge_attr=None):
        """"""
        row, col = edge_index
        x = x.unsqueeze(-1) if x.dim() == 1 else x

        # TODO: Try -x[col] instead of x[col] - x[row]
        if edge_attr is None:
            out = torch.cat([x[row], x[col]], dim=-1)
        else:
            out = torch.cat([x[row], x[col], edge_attr], dim=-1)
        out = self.nn(out)
        x = scatter_(self.aggr, out, row, dim_size=x.size(0))

        return x, out

    def __repr__(self):
        return "{}(nn={})".format(self.__class__.__name__, self.nn)


class EdgeConvBatch(nn.Module):
    def __init__(self, gnn, hidden_size, batch_norm=True, dropout=0.2):
        super().__init__()

        self.gnn = gnn

        x_post_modules = []
        edge_attr_post_modules = []

        if batch_norm is not None:
            x_post_modules.append(nn.LayerNorm(hidden_size))
            edge_attr_post_modules.append(nn.LayerNorm(hidden_size))

        if dropout:
            x_post_modules.append(nn.Dropout(dropout))
            edge_attr_post_modules.append(nn.Dropout(dropout))

        self.x_postprocess = nn.Sequential(*x_post_modules)
        self.edge_attr_postprocess = nn.Sequential(*edge_attr_post_modules)

    def forward(self, x, edge_index, edge_attr=None):
        x, edge_attr = self.gnn(x, edge_index, edge_attr)
        x = self.x_postprocess(x)
        edge_attr = self.edge_attr_postprocess(edge_attr)
        return x, edge_attr


def get_graph_conv_layer(input_size, hidden_size, output_size):
    mlp = nn.Sequential(
        #
        nn.Linear(input_size, hidden_size),
        nn.ReLU(),
        nn.Linear(hidden_size, output_size),
    )
    gnn = EdgeConvMod(nn=mlp, aggr="add")
    graph_conv = EdgeConvBatch(gnn, output_size, batch_norm=True, dropout=0.2)
    return graph_conv


class MyEdgeConv(torch.nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.nn = nn.Sequential(
            #
            nn.Linear(hidden_size * 3, hidden_size * 2),
            nn.ReLU(),
            nn.Linear(hidden_size * 2, hidden_size),
        )
        self.reset_parameters()

    def reset_parameters(self):
        reset(self.nn)

    def forward(self, x, edge_index, edge_attr=None):
        """"""
        row, col = edge_index
        x = x.unsqueeze(-1) if x.dim() == 1 else x

        # TODO: Try -x[col] instead of x[col] - x[row]
        if edge_attr is None:
            out = torch.cat([x[row], x[col]], dim=-1)
        else:
            out = torch.cat([x[row], x[col], edge_attr], dim=-1)
        edge_attr_out = self.nn(out)

        return edge_attr_out

    def __repr__(self):
        return "{}(nn={})".format(self.__class__.__name__, self.nn)


class MyAttn(torch.nn.Module):
    def __init__(self, hidden_size, num_heads):
        super().__init__()
        self.attn = nn.MultiheadAttention(hidden_size, num_heads)
        self.reset_parameters()

    def reset_parameters(self):
        reset(self.attn)

    def forward(self, x, edge_index, edge_attr, batch):
        """"""
        query = x.unsqueeze(0)
        key = to_dense_adj(edge_index, batch=batch, edge_attr=edge_attr).squeeze(0)

        adjacency = to_dense_adj(edge_index, batch=batch).squeeze(0)
        key_padding_mask = adjacency == 0
        key_padding_mask[torch.eye(key_padding_mask.size(0)).to(torch.bool)] = 0
        #         attn_mask = torch.zeros_like(key)
        #         attn_mask[mask] = -float("inf")

        x_out, _ = self.attn(query, key, key, key_padding_mask=key_padding_mask)
        #         x_out = torch.where(torch.isnan(x_out), torch.zeros_like(x_out), x_out)
        x_out = x_out.squeeze(0)
        assert (x_out == x_out).all().item()
        assert x.shape == x_out.shape, (x.shape, x_out.shape)
        return x_out

    def __repr__(self):
        return "{}(nn={})".format(self.__class__.__name__, self.nn)


class Net(nn.Module):
    def __init__(self, x_input_size, adj_input_size, hidden_size, output_size):
        super().__init__()

        self.embed_x = nn.Sequential(
            nn.Embedding(x_input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            # nn.ReLU(),
        )
        self.embed_adj = (
            nn.Sequential(
                nn.Linear(adj_input_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size),
                nn.LayerNorm(hidden_size),
                # nn.ELU(),
            )
            if adj_input_size
            else None
        )
        self.graph_conv_0 = get_graph_conv_layer(
            (2 + bool(adj_input_size)) * hidden_size, 2 * hidden_size, hidden_size
        )

        N = 3
        graph_conv = get_graph_conv_layer(3 * hidden_size, 2 * hidden_size, hidden_size)
        self.graph_conv = _get_clones(graph_conv, N)

        self.linear_out = nn.Linear(hidden_size, output_size)

    def forward(self, x, edge_index, edge_attr):

        x = self.embed_x(x)
        # edge_index, _ = add_self_loops(edge_index)  # We should remove self loops in this case!
        edge_attr = self.embed_adj(edge_attr) if edge_attr is not None else None

        x_out, edge_attr_out = self.graph_conv_0(x, edge_index, edge_attr)
        x = x + x_out
        edge_attr = (edge_attr + edge_attr_out) if edge_attr is not None else edge_attr_out

        for i in range(3):
            x = F.relu(x)
            edge_attr = F.relu(edge_attr)
            x_out, edge_attr_out = self.graph_conv[i](x, edge_index, edge_attr)
            x = x + x_out
            edge_attr = edge_attr + edge_attr_out

        x = self.linear_out(x)

        return x


def _get_clones(module, N):
    return ModuleList([copy.deepcopy(module) for i in range(N)])


def to_fixed_width(lst, precision=None):
    lst = [round(l, precision) if isinstance(l, float) else l for l in lst]
    return [f"{l: <18}" for l in lst]


class Stats:
    epoch: int
    step: int
    batch_size: int
    echo: bool
    total_loss: float
    num_correct_preds: int
    num_preds: int
    num_correct_preds_missing: int
    num_preds_missing: int
    num_correct_preds_missing_valid: int
    num_preds_missing_valid: int
    start_time: float

    def __init__(self, *, epoch=0, step=0, batch_size=1, filename=None, echo=True, tb_writer=None):
        self.epoch = epoch
        self.step = step
        self.batch_size = batch_size
        self.echo = echo
        self.tb_writer = tb_writer
        self.reset_parameters()

        if filename:
            self.filehandle = open(filename, "wt", newline="")
            self.writer = csv.DictWriter(self.filehandle, list(self.stats.keys()), dialect="unix")
            self.writer.writeheader()
            atexit.register(self.filehandle.close)
        else:
            self.filehandle = None
            self.writer = None

    def reset_parameters(self):
        self.num_steps = 0
        self.total_loss = 0
        self.num_correct_preds = 0
        self.num_preds = 0
        self.num_correct_preds_missing = 0
        self.num_preds_missing = 0
        self.num_correct_preds_missing_valid = 0
        self.num_preds_missing_valid = 0
        self.start_time = time.perf_counter()

    @property
    def header(self):
        return "".join(to_fixed_width(self.stats.keys()))

    @property
    def row(self):
        return "".join(to_fixed_width(self.stats.values(), 4))

    @property
    def stats(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return {
                "epoch": self.epoch,
                "step": self.step,
                "datapoint": self.datapoint,
                "avg_loss": np.float64(1) * self.total_loss / self.num_steps,
                "accuracy": np.float64(1) * self.num_correct_preds / self.num_preds,
                "accuracy_m": np.float64(1)
                * self.num_correct_preds_missing
                / self.num_preds_missing,
                "accuracy_mv": self.accuracy_mv,
                "time_elapsed": time.perf_counter() - self.start_time,
            }

    @property
    def accuracy_mv(self):
        return np.float64(1) * self.num_correct_preds_missing_valid / self.num_preds_missing_valid

    @property
    def datapoint(self):
        return self.step * self.batch_size

    def write_header(self):
        if self.echo:
            print(self.header)
        if self.writer is not None:
            self.writer.writeheader()

    def write_row(self):
        if self.echo:
            print(self.row, end="\r")
        if self.writer is not None:
            self.writer.writerow(self.stats)
        if self.tb_writer is not None:
            stats = self.stats
            datapoint = stats.pop("datapoint")
            for key, value in stats.items():
                self.tb_writer.add_scalar(key, value, datapoint)
            self.tb_writer.flush()
