from typing import Tuple

import torch
import torch.nn as nn
from kmtools import structure_tools
from kmtools.structure_tools.types import DomainMutation as Mutation


def extract_seq_and_adj(structure, chain_idxs, remove_hetatms=False):
    from proteinsolver.utils import ProteinData

    domain, result_df = get_interaction_dataset_wdistances(
        structure, 0, chain_idxs, r_cutoff=12, remove_hetatms=remove_hetatms
    )
    domain_sequence = structure_tools.get_chain_sequence(
        domain, if_unknown="replace", unknown_residue_marker=("" if remove_hetatms else "X")
    )
    assert max(result_df["residue_idx_1"].values) < len(domain_sequence)
    assert max(result_df["residue_idx_2"].values) < len(domain_sequence)
    data = ProteinData(
        domain_sequence,
        result_df["residue_idx_1"].values,
        result_df["residue_idx_2"].values,
        result_df["distance"].values,
    )
    return data


def get_interaction_dataset_wdistances(
    structure, model_id, chain_idxs, r_cutoff=12, remove_hetatms=False
):
    domain_defs = []
    for chain_idx in chain_idxs:
        chain = list(structure[0])[chain_idx]
        num_residues = len(list(chain.residues))
        domain_def = structure_tools.DomainDef(model_id, chain.id, 1, num_residues)
        domain_defs.append(domain_def)

    domain_structure = structure_tools.extract_domain(
        structure, domain_defs, remove_hetatms=remove_hetatms
    )
    distances_core = structure_tools.get_distances(
        domain_structure.to_dataframe(), r_cutoff, groupby="residue"
    )
    assert (distances_core["residue_idx_1"] <= distances_core["residue_idx_2"]).all()
    return domain_structure, distances_core


def get_mutation_score(
    net: nn.Module,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    edge_attr: torch.Tensor,
    mutation: Mutation,
    num_categories: int = 20,
) -> Tuple[float, float]:
    import proteinsolver

    x = x.clone()

    wt_aa_idx = (
        proteinsolver.utils.seq_to_tensor(mutation.residue_wt.encode("ascii")).astype(int).item()
    )
    mutation_idx = int(mutation.residue_id) - 1
    mut_aa_idx = (
        proteinsolver.utils.seq_to_tensor(mutation.residue_mut.encode("ascii")).astype(int).item()
    )
    assert wt_aa_idx != mut_aa_idx

    x[mutation_idx] = num_categories

    with torch.no_grad():
        output = net(x, edge_index, edge_attr)
        output = torch.softmax(output, dim=1)

    score_wt = output[mutation_idx][wt_aa_idx].item()
    score_mut = output[mutation_idx][mut_aa_idx].item()

    return score_wt, score_mut
