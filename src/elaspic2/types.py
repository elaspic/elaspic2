from typing import NamedTuple

from elaspic2.plugins.protbert import ProtBertData
from elaspic2.plugins.proteinsolver import ProteinSolverData


class ELASPIC2Data(NamedTuple):
    protbert_data: ProtBertData
    proteinsolver_data: ProteinSolverData
