from typing import NamedTuple


class ProtBertData(NamedTuple):
    protein_sequence: str
    ligand_sequence: str
