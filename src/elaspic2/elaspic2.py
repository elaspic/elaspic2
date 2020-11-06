import importlib.resources
from pathlib import Path
from typing import Dict, Union

import lightgbm as lgb
import numpy as np
import pandas as pd
import torch
import json

import elaspic2.data
from elaspic2.plugins.protbert import ProtBert
from elaspic2.plugins.proteinsolver import ProteinSolver
from elaspic2.types import ELASPIC2Data


class ELASPIC2:
    def __init__(self, device: torch.device = torch.device("cpu")):
        self.device = device

        self.pca_columns = self._load_pca_models()
        self.pca_models = self._load_pca_models()

        self.lgb_columns = self._load_lgb_columns()
        self.lgb_models = self._load_lgb_models()

        if not ProtBert.is_loaded:
            ProtBert.load_model(device=device)

        if not ProteinSolver.is_loaded:
            ProteinSolver.load_model(device=device)

    @staticmethod
    def _load_pca_models():
        pca_models = {"core": [], "interface": []}
        with importlib.resources.path(elaspic2.data, "pca") as pca_data_path:
            for pca_file in sorted(pca_data_path.glob("*.pickle")):
                coi = "core" if "-core-" in pca_file.name else "interface"
                pca_models[coi].append(torch.load(pca_file))
        return pca_models

    @staticmethod
    def _load_lgb_models():
        lgb_models = {"core": [], "interface": []}
        with importlib.resources.path(elaspic2.data, "lgb") as lgb_data_path:
            for lgb_file in sorted(lgb_data_path.glob("*.txt")):
                coi = "core" if "-core-" in lgb_file.name else "interface"
                lgb_models[coi].append(lgb.Booster(model_file=lgb_file.as_posix()))
        return lgb_models

    @staticmethod
    def _load_pca_columns():
        pca_columns = {}
        with importlib.resources.path(elaspic2.data, "pca") as lgb_data_path:
            for coi in ["core", "interface"]:
                json_file = lgb_data_path.joinpath(f"pca-columns-{coi}.json")
                with json_file.open("rt") as fin:
                    pca_columns[coi] = json.load(fin)
        return pca_columns

    @staticmethod
    def _load_lgb_columns():
        feature_columns = {}
        with importlib.resources.path(elaspic2.data, "lgb") as lgb_data_path:
            for coi in ["core", "interface"]:
                json_file = lgb_data_path.joinpath(f"feature-columns-{coi}.json")
                with json_file.open("rt") as fin:
                    feature_columns[coi] = json.load(fin)
        return feature_columns

    def build(
        self,
        structure_file: Union[Path, str],
        protein_sequence: str,
        ligand_sequence: str,
        remove_hetatms=True,
    ) -> ELASPIC2Data:
        protbert_data = ProtBert.build(
            protein_sequence,
            ligand_sequence,
            remove_hetatms,
        )
        proteinsolver_data = ProteinSolver.build(
            structure_file,
            protein_sequence,
            ligand_sequence,
            remove_hetatms,
        )
        data = ELASPIC2Data(protbert_data, proteinsolver_data)
        return data

    def analyze_mutation(self, mutation: str, data: ELASPIC2Data) -> Dict:
        if "_" not in mutation:
            mutation = f"A_{mutation}"

        protbert_result = ProtBert.analyze_mutation(mutation, data.protbert_data)
        proteinsolver_result = ProteinSolver.analyze_mutation(mutation, data.proteinsolver_data)
        return {
            **{f"protbert_{key}": value for key, value in protbert_result.items()},
            **{f"proteinsolver_{key}": value for key, value in proteinsolver_result.items()},
        }

    def predict_mutation_effect(self, analyze_mutation_results: pd.DataFrame) -> np.ndarray:
        coi = (
            "core"
            if "protbert_core2interface_features_residue_change" not in analyze_mutation_results
            else "interface"
        )

        n_components = 10
        pca_columns = self.pca_columns[coi]
        pca_models = self.pca_models[coi]
        lgb_columns = self.lgb_columns[coi]
        lgb_models = self.lgb_models[coi]

        analyze_mutation_results = analyze_mutation_results.copy()
        for split_idx, (pca_model, lgb_model) in enumerate(zip(pca_models, lgb_models)):
            for column in pca_columns:
                values = np.vstack(analyze_mutation_results[column].values)
                values_out = pca_model.transform(values)
                for i in range(n_components):
                    new_column = f"{column}_{i}_pc"
                    analyze_mutation_results[new_column] = values_out[:, i]

            analyze_mutation_results[f"ddg_pred_{split_idx}"] = lgb_model.predict(
                analyze_mutation_results[lgb_columns]
            )

        analyze_mutation_results["ddg_pred"] = analyze_mutation_results[
            [f"ddg_pred_{split_idx}" for split_idx in range(len(self.lgb_models))]
        ].mean(axis=1)

        return analyze_mutation_results["ddg_pred"].values
