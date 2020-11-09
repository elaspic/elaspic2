from typing import Optional, Tuple

from kmbio import PDB
from kmtools import structure_tools
from kmtools.structure_tools.types import DomainDef


def guess_domain_defs(
    structure: PDB.Structure,
    protein_sequence: str,
    ligand_sequence: Optional[str],
    remove_hetatms: bool = True,
) -> Tuple[Optional[DomainDef], Optional[DomainDef]]:
    protein_domain_def: DomainDef = None
    ligand_domain_def: DomainDef = None
    unknown_residue_marker = "" if remove_hetatms else "X"
    for chain in structure.chains:
        chain_sequence = structure_tools.get_chain_sequence(
            chain, if_unknown="replace", unknown_residue_marker=unknown_residue_marker
        )
        if protein_domain_def is None and chain_sequence == protein_sequence:
            protein_domain_def = DomainDef(chain.parent.id, chain.id, 1, len(chain))
        elif ligand_domain_def is None and chain_sequence == ligand_sequence:
            ligand_domain_def = DomainDef(chain.parent.id, chain.id, 1, len(chain))
    return protein_domain_def, ligand_domain_def
