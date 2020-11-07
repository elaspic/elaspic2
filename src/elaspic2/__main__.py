from typing import Any, Dict, List

import fire
import torch
from tqdm import tqdm

import elaspic2 as el2


def run(
    *,
    protein_structure: str,
    protein_sequence: str,
    mutations: str,
    ligand_sequence: str = None,
    device="cpu",
) -> List[Dict[str, Any]]:
    """Predict the effect of mutations on protein folding and protein-protein interaction.

    Args:
        protein_structure: The structure of the protein to be mutated.
        protein_sequence: The sequence of the protein to be mutated.
            Should map to chain A in `protein_structure`.
        mutations: One or more mutations to be evaluated.
            Multiple mutations should be separated with a ','.
        ligand_sequence: The sequence of the ligand that is interacting with the protein
            to be mutated. Should map to chain B in `protein_structure.`
        device: Device to use for evaluating mutations. Use "cuda" or "cuda:N" to use
            the first or Nth GPU.

    Returns:
        Stability (and affinity) predictions for every mutation.
    """
    mutation_list = mutations.replace(".", ",").split(",")

    model = el2.ELASPIC2(device=torch.device(device))

    mutation_stability_features = calculate_stability(
        model, protein_structure, protein_sequence, mutation_list
    )
    results_core = combine_results_core(model, mutation_list, mutation_stability_features)

    def assert_mutations_match(rcore, rinterface):
        assert rcore["mutation"] == rinterface["mutation"]
        return True

    if ligand_sequence:
        mutation_affinity_features = calculate_affinity(
            model,
            protein_structure,
            protein_sequence,
            mutation_list,
            ligand_sequence,
            mutation_stability_features,
        )
        results_interface = combine_results_interface(
            model, mutation_list, mutation_stability_features, mutation_affinity_features
        )
        assert len(results_core) == len(results_interface)
        results = [
            {**rcore, **rinterface}
            for (rcore, rinterface) in zip(results_core, results_interface)
            if assert_mutations_match(rcore, rinterface)
        ]
    else:
        results = results_core

    return results


def calculate_stability(model, protein_structure, protein_sequence, mutation_list):
    protein_stability_features = model.build(
        structure_file=protein_structure,
        protein_sequence=protein_sequence,
        ligand_sequence=None,
        remove_hetatms=True,
    )

    mutation_stability_features = list(
        tqdm(
            (model.analyze_mutation(mut, protein_stability_features) for mut in mutation_list),
            total=len(mutation_list),
            desc="stability",
        )
    )

    return mutation_stability_features


def combine_results_core(model, mutation_list, mutation_stability_features):
    protbert_core_list = [
        f["protbert_core_score_wt"] - f["protbert_core_score_mut"]
        for f in mutation_stability_features
    ]

    proteinsolver_core_list = [
        f["proteinsolver_core_score_wt"] - f["proteinsolver_core_score_mut"]
        for f in mutation_stability_features
    ]

    el2core_list = model.predict_mutation_effect(mutation_stability_features).tolist()

    assert (
        len(mutation_list)
        == len(protbert_core_list)
        == len(proteinsolver_core_list)
        == len(el2core_list)
    )

    results_core = [
        {
            "mutation": mutation,
            "protbert_core": protbert_core,
            "proteinsolver_core": proteinsolver_core,
            "el2core": el2core,
        }
        for (mutation, protbert_core, proteinsolver_core, el2core) in zip(
            mutation_list, protbert_core_list, proteinsolver_core_list, el2core_list
        )
    ]

    return results_core


def calculate_affinity(
    model,
    protein_structure,
    protein_sequence,
    mutation_list,
    ligand_sequence,
    mutation_stability_features,
):
    protein_affinity_features = model.build(
        structure_file=protein_structure,
        protein_sequence=protein_sequence,
        ligand_sequence=ligand_sequence,
        remove_hetatms=True,
    )

    mutation_affinity_features = list(
        tqdm(
            (model.analyze_mutation(mut, protein_affinity_features) for mut in mutation_list),
            total=len(mutation_list),
            desc="affinity",
        )
    )

    return mutation_affinity_features


def combine_results_interface(
    model, mutation_list, mutation_stability_features, mutation_affinity_features
):
    protbert_interface_list = [
        f["protbert_interface_score_wt"] - f["protbert_interface_score_mut"]
        for f in mutation_affinity_features
    ]

    proteinsolver_interface_list = [
        f["proteinsolver_interface_score_wt"] - f["proteinsolver_interface_score_mut"]
        for f in mutation_affinity_features
    ]

    el2interface_list = model.predict_mutation_effect(
        mutation_stability_features, mutation_affinity_features
    )

    results_interface = [
        {
            "mutation": mutation,
            "protbert_interface": protbert_interface,
            "proteinsolver_interface": proteinsolver_interface,
            "el2interface": el2interface,
        }
        for (mutation, protbert_interface, proteinsolver_interface, el2interface) in zip(
            mutation_list, protbert_interface_list, proteinsolver_interface_list, el2interface_list
        )
    ]

    return results_interface


def main():
    fire.Fire(run, name="elaspic2")


if __name__ == "__main__":
    main()
