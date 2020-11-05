import logging
import tempfile
from pathlib import Path
from typing import List, Tuple, TypeVar, Union

import kmbio.PDB
from kmbio.PDB import Atom, Chain, Model, Residue, Structure
from kmbio.PDB.io.loaders import guess_pdb_type
from kmtools import structure_tools
from kmtools.structure_tools import (
    AAA_DICT,
    RESIDUE_ATOM_NAMES,
    RESIDUE_MAPPING_TO_CANONICAL,
    DomainMutation,
    DomainTarget,
)

import elaspic2

logger = logging.getLogger(__name__)


ToolOutput = TypeVar("ToolOutput")


class ToolBase:
    @classmethod
    def get_temp_dir(cls, *unique_ids) -> Path:
        temp_dir = (
            Path(tempfile.mkdtemp())
            .joinpath(elaspic2.__name__, cls.__name__, *unique_ids)
            .resolve()
        )
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir


# #############################################################################
# Sequence
# #############################################################################


class SequenceTool(ToolBase):
    @classmethod
    def build(cls, sequence: str = None, **kwargs) -> ToolOutput:
        raise NotImplementedError


# #############################################################################
# Structure
# #############################################################################


class StructureTool(ToolBase):
    @staticmethod
    def process_structure(
        structure_file: Union[str, Path, Structure], use_auth_id=False, bioassembly_id=True
    ) -> Structure:
        """
        Args:
            structure_file: Structure to process.
            use_auth_id: Whether to look at the AUTH chain id in an mmCIF file.
                If `use_auth_id` is False and `structure_file` does not point to a PDB file,
                we expect that all residues in a chain that is not `chain_is_hetatm` will
                be polymer residues.
            bioassembly_id: ID of the biological assembly that we should generate.
        """
        if isinstance(structure_file, (str, Path)):
            unique_id = Path(structure_file).stem.partition(".")[0].rpartition("?")[-1]
            structure = kmbio.PDB.load(
                structure_file, use_auth_id=use_auth_id, bioassembly_id=bioassembly_id
            )
            pdb_type = guess_pdb_type(structure_file)
            add_hetatm_chain = use_auth_id or pdb_type == "pdb"
        else:
            unique_id = structure_file.id
            structure = structure_file
            # Don't know if the structure came from a PDB or an mmCIF file, so allow to be safe.
            add_hetatm_chain = True
        p_structure = Structure(unique_id)
        h_chain = Chain("Z")
        h_k = 0
        for i, model in enumerate(structure.models):
            p_model = Model(i)
            for j, chain in enumerate(model.chains):
                p_chain = Chain(chain.id)
                chain_is_hetatm = structure_tools.chain_is_hetatm(chain)
                for k, residue in enumerate(chain.residues):
                    if (
                        chain_is_hetatm
                        or residue.resname in AAA_DICT
                        or residue.resname in ["DG", "DC", "DT", "DA", "DU"]
                        or residue.resname in ["G", "C", "T", "A", "U"]
                    ):
                        p_residue = Residue(
                            (residue.id[0], k + 1, residue.id[2]),
                            residue.resname,
                            residue.segid,
                            children=list(residue.atoms),
                        )
                    elif residue.resname in RESIDUE_MAPPING_TO_CANONICAL:
                        resname = RESIDUE_MAPPING_TO_CANONICAL[residue.resname]
                        p_residue = Residue((" ", k + 1, " "), resname, residue.segid)
                        residue_atom_names = RESIDUE_ATOM_NAMES[resname]
                        for l, atom in enumerate(residue.atoms):
                            if atom.name in residue_atom_names:
                                p_atom = Atom(
                                    atom.name,
                                    atom.coord,
                                    atom.bfactor,
                                    atom.occupancy,
                                    atom.altloc,
                                    atom.fullname,
                                    atom.serial_number,
                                    element=atom.element,
                                )
                                p_residue.add(p_atom)
                            else:
                                logger.warning(
                                    f"Removing atom '{atom.name}' from model '{model.id}', "
                                    f"chain '{chain.id}', residue '{residue.resname}' "
                                    f"{residue.id}."
                                )
                    else:
                        if not add_hetatm_chain:
                            logger.warning(
                                f"Skipping strange residue '{residue.resname}' {residue.id} "
                                "inside a polymer chain of an mmCIF file. "
                                "Maybe we are working with a PDB file instead? "
                                "Specify `use_auth_id=True` to silence."
                            )
                            continue
                        h_residue = Residue(
                            (residue.id[0], h_k + 1, residue.id[2]),
                            residue.resname,
                            residue.segid,
                            children=list(residue.atoms),
                        )
                        h_chain.add(h_residue)
                        h_k += 1
                        continue
                    p_chain.add(p_residue)
                p_model.add(p_chain)
            p_structure.add(p_model)
        if list(h_chain.residues):
            assert add_hetatm_chain
            p_structure[0].add(h_chain)
        return p_structure

    @classmethod
    def build(cls, structure: Union[str, Path, Structure], **kwargs) -> ToolOutput:
        raise NotImplementedError


class ResidueAnalyzer:
    @classmethod
    def analyze_residue(cls, mutation: str, data: ToolOutput) -> dict:
        raise NotImplementedError


class MutationAnalyzer:
    @classmethod
    def analyze_mutation(cls, mutation: str, data: ToolOutput) -> dict:
        raise NotImplementedError


class Mutator:
    @classmethod
    def mutate(cls, mutations: List[DomainMutation], data: ToolOutput) -> Tuple[Structure, dict]:
        raise NotImplementedError


class HomologyModeler:
    @classmethod
    def create_model(cls, targets: List[DomainTarget], data: ToolOutput) -> Tuple[Structure, dict]:
        raise NotImplementedError
