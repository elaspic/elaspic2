import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import lightgbm as lgb
import numpy as np
import pandas as pd
import torch
from kmbio import PDB
from kmtools import structure_tools

import elaspic2.data
from elaspic2.plugins.protbert import ProtBert
from elaspic2.plugins.proteinsolver import ProteinSolver
from elaspic2.types import COI, ELASPIC2Data
from elaspic2.utils import guess_domain_defs

try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources


class ELASPIC2:
    def __init__(self, device: torch.device = torch.device("cpu")):
        self.device = device

        self.pca_columns = self._load_pca_columns()
        self.pca_models = self._load_pca_models()

        self.lgb_columns = self._load_lgb_columns()
        self.lgb_models = self._load_lgb_models()

        if not ProtBert.is_loaded:
            ProtBert.load_model(device=device)

        if not ProteinSolver.is_loaded:
            ProteinSolver.load_model(device=device)

    @staticmethod
    def _load_pca_models():
        pca_models = {COI.CORE: {}, COI.INTERFACE: {}}
        with importlib_resources.path(elaspic2.data, "pca") as pca_data_path:
            for pca_file in sorted(pca_data_path.glob("*.pickle")):
                coi = COI.CORE if "-core" in pca_file.name else COI.INTERFACE
                pca_models[coi][pca_file.stem] = torch.load(pca_file)
        return pca_models

    @staticmethod
    def _load_lgb_models():
        lgb_models = {COI.CORE: [], COI.INTERFACE: []}
        with importlib_resources.path(elaspic2.data, "lgb") as lgb_data_path:
            for lgb_file in sorted(lgb_data_path.glob("*.txt")):
                coi = COI.CORE if "-core" in lgb_file.name else COI.INTERFACE
                lgb_models[coi].append(lgb.Booster(model_file=lgb_file.as_posix()))
        return lgb_models

    @staticmethod
    def _load_pca_columns():
        pca_columns = {}
        with importlib_resources.path(elaspic2.data, "pca") as lgb_data_path:
            for coi in COI:
                json_file = lgb_data_path.joinpath(f"pca-columns-{coi.value}.json")
                with json_file.open("rt") as fin:
                    pca_columns[coi] = json.load(fin)
        return pca_columns

    @staticmethod
    def _load_lgb_columns():
        feature_columns = {}
        with importlib_resources.path(elaspic2.data, "lgb") as lgb_data_path:
            for coi in COI:
                json_file = lgb_data_path.joinpath(f"feature-columns-{coi.value}.json")
                with json_file.open("rt") as fin:
                    feature_columns[coi] = json.load(fin)
        return feature_columns

    def build(
        self,
        structure_file: Union[Path, str],
        protein_sequence: str,
        ligand_sequence: Optional[str],
        remove_hetatms=True,
    ) -> ELASPIC2Data:
        structure = PDB.load(structure_file)
        protein_domain_def, ligand_domain_def = guess_domain_defs(
            structure, protein_sequence, ligand_sequence, remove_hetatms=remove_hetatms
        )
        if protein_domain_def is None or (
            ligand_sequence is not None and ligand_domain_def is None
        ):
            raise ValueError(
                "Cound not find protein and / or ligand sequence in the provided structure file."
            )

        domain_defs = (
            [protein_domain_def]
            if ligand_sequence is None
            else [protein_domain_def, ligand_domain_def]
        )
        structure_new = structure_tools.extract_domain(
            structure, domain_defs, remove_hetatms=remove_hetatms
        )

        with tempfile.NamedTemporaryFile(suffix=".pdb") as pdb_file_obj:
            PDB.save(structure_new, pdb_file_obj.name)
            protbert_data = ProtBert.build(protein_sequence, ligand_sequence, remove_hetatms)
            proteinsolver_data = ProteinSolver.build(
                pdb_file_obj.name, protein_sequence, ligand_sequence, remove_hetatms
            )

        data = ELASPIC2Data(ligand_sequence is not None, protbert_data, proteinsolver_data)
        return data

    def analyze_mutation(self, mutation: str, data: ELASPIC2Data) -> Dict:
        if "_" not in mutation:
            mutation = f"A_{mutation}"

        coi = COI.INTERFACE if data.is_interface else COI.CORE
        protbert_result = ProtBert.analyze_mutation(mutation, data.protbert_data)
        proteinsolver_result = ProteinSolver.analyze_mutation(mutation, data.proteinsolver_data)
        return {
            **{f"protbert_{coi.value}_{key}": value for key, value in protbert_result.items()},
            **{
                f"proteinsolver_{coi.value}_{key}": value
                for key, value in proteinsolver_result.items()
            },
        }

    def predict_mutation_effect(
        self,
        mutation_stability_features: List[Dict],
        mutation_affinity_features: Optional[List[Dict]] = None,
    ) -> np.ndarray:
        coi = COI.INTERFACE if mutation_affinity_features is not None else COI.CORE
        pca_models = self.pca_models[coi]
        lgb_models = self.lgb_models[coi]
        feature_columns = self.lgb_columns[coi]

        if mutation_affinity_features is None:
            mutation_features = mutation_stability_features
        else:
            mutation_features = [
                {**stability_features, **affinity_features}
                for stability_features, affinity_features in zip(
                    mutation_stability_features, mutation_affinity_features
                )
            ]

        mutation_features_df = pd.DataFrame(mutation_features)
        mutation_features_df, pca_columns = self._add_feature_deltas(mutation_features_df)

        n_components = 10
        for split_idx, lgb_model in enumerate(lgb_models):
            for column in pca_columns:
                pca_model = pca_models[f"pca-{column}-{coi.value}"]
                values = np.vstack(mutation_features_df[column].values)
                values_out = pca_model.transform(values)
                for i in range(n_components):
                    new_column = f"{column}_{i}_pc"
                    mutation_features_df[new_column] = values_out[:, i]

            mutation_features_df[f"ddg_pred_{split_idx}"] = lgb_model.predict(
                mutation_features_df[feature_columns]
            )

        mutation_features_df["ddg_pred"] = mutation_features_df[
            [f"ddg_pred_{split_idx}" for split_idx in range(len(lgb_models))]
        ].mean(axis=1)

        return mutation_features_df["ddg_pred"].values

    @staticmethod
    def _add_feature_deltas(input_df):
        def assign_delta(input_df, column, column_ref, column_change):
            value_sample = input_df[column].iloc[0]
            if isinstance(value_sample, (list, np.ndarray)):
                input_df[column_change] = input_df[column].apply(np.array) - input_df[
                    column_ref
                ].apply(np.array)
                return input_df, True
            else:
                input_df[column_change] = input_df[column] - input_df[column_ref]
                return input_df, False

        pca_columns = []
        for column in sorted(input_df):
            if column.endswith("_mut") and "_core2interface_" not in column:
                column_ref = column[:-4] + "_wt"
                column_change = column[:-4] + "_change"
                input_df, is_array = assign_delta(input_df, column, column_ref, column_change)
                if is_array:
                    pca_columns.extend([column_ref, column_change])

        for column in sorted(input_df):
            if "_interface_" in column and not column.endswith("_mut"):
                column_ref = column.replace("_interface_", "_core_")
                column_change = column.replace("_interface_", "_core2interface_")
                input_df, is_array = assign_delta(input_df, column, column_ref, column_change)
                if is_array:
                    pca_columns.extend([column_change])

        return input_df, pca_columns
