import importlib
from pathlib import Path

import torch

from ev2.core import MutationAnalyzer, SequenceTool
from ev2.plugins.proteinsolver.types import ProteinSolverData


class ProteinSolver(SequenceTool, MutationAnalyzer):
    model = None
    device = None

    @classmethod
    def load_model(cls, model_name="191f05de", device=torch.device("cpu")) -> None:
        import proteinsolver  # noqa

        state_file = (
            Path(__file__)
            .parent.joinpath("data", model_name, "e53-s1952148-d93703104.state")
            .resolve(strict=True)
            .as_posix()
        )
        module = importlib.import_module(f"ev2.plugins.proteinsolver.data.{model_name}.model")
        net = module.Net(x_input_size=21, adj_input_size=2, hidden_size=128, output_size=20)
        net.load_state_dict(torch.load(state_file, map_location=device))
        net = net.eval().to(device)
        cls.model = net
        cls.device = device

    @classmethod
    def build(cls, sequence: str, ligand_sequence: str) -> ProteinSolverData:
        return ProteinSolverData(protein_sequence=sequence, ligand_sequence=ligand_sequence)

    @classmethod
    def analyze_mutation(cls, mutation: str, data: ProteinSolverData) -> dict:
        raise NotImplementedError
