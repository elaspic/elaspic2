import importlib
from pathlib import Path
from typing import Optional, Union

import torch
import torch.nn as nn
from kmbio import PDB
from kmtools.structure_tools.types import DomainMutation as Mutation

from elaspic2.core import MutationAnalyzer, StructureTool
from elaspic2.plugins.proteinsolver.protein_data import extract_seq_and_adj, get_mutation_score
from elaspic2.plugins.proteinsolver.types import ProteinSolverData


class ProteinSolver(StructureTool, MutationAnalyzer):
    model: Optional[nn.Module] = None
    device: Optional[torch.device] = None
    is_loaded: bool = False

    @classmethod
    def load_model(cls, model_name="ps_191f05de", device=torch.device("cpu")) -> None:
        # Need to import proteinsolver in order for the torch_geometric.utils.scatter_ monkeypatch
        # to be applied.
        import proteinsolver  # noqa

        state_file = (
            Path(__file__)
            .parent.joinpath("data", model_name, "e53-s1952148-d93703104.state")
            .resolve(strict=True)
            .as_posix()
        )
        module = importlib.import_module(f"elaspic2.plugins.proteinsolver.data.{model_name}.model")
        model = module.Net(  # type: ignore
            x_input_size=21, adj_input_size=2, hidden_size=128, output_size=20
        )
        model.load_state_dict(torch.load(state_file, map_location=device))
        model = model.eval().to(device)
        for param in model.parameters():
            param.requires_grad = False

        cls.model = model
        cls.device = device
        cls.is_loaded = True

    @classmethod
    def build(  # type: ignore[override]
        cls,
        structure_file: Union[Path, str],
        protein_sequence: str,
        ligand_sequence: Optional[str],
        remove_hetatms=True,
    ) -> ProteinSolverData:
        import proteinsolver

        structure = PDB.load(structure_file)
        pdata = extract_seq_and_adj(
            structure,
            [0] if ligand_sequence is None else [0, 1],
            remove_hetatms=remove_hetatms,
        )

        expected_sequence = protein_sequence + (ligand_sequence or "")
        if remove_hetatms:
            expected_sequence = expected_sequence.replace("X", "")
        if pdata.sequence != expected_sequence:
            raise ProteinSolverBuildError(
                f"Parsed sequence does not match provided sequence "
                f"({pdata.sequence} != {protein_sequence} + {ligand_sequence})."
            )

        data = proteinsolver.datasets.protein.row_to_data(pdata)
        data = proteinsolver.datasets.protein.transform_edge_attr(data)

        return data

    @classmethod
    def analyze_mutation(  # type: ignore[override]
        cls, mutation: str, data: ProteinSolverData
    ) -> dict:
        if cls.model is None:
            raise Exception(
                "You need to call `ProteinSolver.load_model()` before evaluating mutations."
            )

        mut = Mutation.from_string(mutation)

        data = data.to(cls.device)  # type: ignore

        score_wt, score_mut = get_mutation_score(
            cls.model, data.x, data.edge_index, data.edge_attr, mut
        )

        return {"score_wt": score_wt, "score_mut": score_mut}


class ProteinSolverBuildError(Exception):
    pass


class ProteinSolverAnalyzeError(Exception):
    pass
