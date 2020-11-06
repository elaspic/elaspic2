from enum import Enum
from typing import NamedTuple

from elaspic2.plugins.protbert import ProtBertData
from elaspic2.plugins.proteinsolver import ProteinSolverData


class ELASPIC2Data(NamedTuple):
    is_interface: bool
    protbert_data: ProtBertData
    proteinsolver_data: ProteinSolverData


class COI(Enum):
    CORE = "core"
    INTERFACE = "interface"
