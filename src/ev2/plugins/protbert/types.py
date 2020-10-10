from typing import NamedTuple, Optional


class ProtBertData(NamedTuple):
    protein_sequence: str
    ligand_sequence: Optional[str]
    combined_sequence: Optional[str]
