import os.path as op
import tempfile
from pathlib import Path
from typing import List, Tuple, Union

import kmbio.PDB
from kmbio.PDB import Structure
from kmtools import structure_tools
from kmtools.structure_tools import DomainMutation, DomainTarget

from elaspic2.core import HomologyModeler, Mutator, StructureTool
from elaspic2.plugins.modeller.functions import run_modeller
from elaspic2.plugins.modeller.types import ModellerData


class ModellerError(Exception):
    pass


class Modeller(StructureTool, Mutator, HomologyModeler):
    @classmethod
    def build(
        cls,
        structure: Union[str, Path, Structure],
        use_auth_id=False,
        bioassembly_id=True,
        use_strict_alignment=True,
    ) -> ModellerData:
        """Prepare Modeller input data.

        Args:
            structure: A `Structure` object or a string or Path that is understood by
                `kmbio.PDB.load`. The structure should ideally be provided in mmCIF format.
        """
        structure = cls.process_structure(
            structure, use_auth_id=use_auth_id, bioassembly_id=bioassembly_id
        )
        unique_id = structure.id
        root_dir = cls.get_temp_dir(unique_id)
        structure_file = op.join(root_dir, unique_id + ".pdb")
        kmbio.PDB.save(structure, structure_file)
        return ModellerData(
            root_dir, structure_file, use_auth_id, bioassembly_id, use_strict_alignment
        )

    @classmethod
    def mutate(cls, mutations: List[DomainMutation], data: ModellerData) -> Tuple[Structure, dict]:
        structure = kmbio.PDB.load(data.structure_file)
        target_map = structure_tools.get_target_map(structure)
        for mutation in mutations:
            id_ = (mutation.model_id, mutation.chain_id)
            target_map[id_] = structure_tools.mutation_to_target(mutation, target_map[id_])
        return cls.create_model(list(target_map.values()), data)

    @classmethod
    def create_model(
        cls, targets: List[DomainTarget], data: ModellerData
    ) -> Tuple[Structure, dict]:
        import _modeller

        structure = kmbio.PDB.load(data.structure_file)
        structure_fm, alignment = structure_tools.prepare_for_modeling(
            structure, targets, strict=data.use_strict_alignment
        )
        temp_dir = tempfile.mkdtemp(dir=data.root_dir.as_posix())
        try:
            results = run_modeller(structure_fm, alignment, temp_dir)
        except _modeller.ModellerError as e:
            raise ModellerError(f"Modeller crashed with an error: '{str(e)}'")
        if results["failure"] is not None:
            raise ModellerError(f"Modeller finished with an error: '{results['failure']}'")
        structure_bm = kmbio.PDB.load(Path(temp_dir).joinpath(results["name"]))
        return structure_bm, {**results, "temp_dir": temp_dir}
