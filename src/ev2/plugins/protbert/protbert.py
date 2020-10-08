from pathlib import Path

import torch

from ev2.core import MutationAnalyzer, SequenceTool
from ev2.plugins.protbert.types import ProtBertData


class ProtBert(SequenceTool, MutationAnalyzer):
    tokenizer = None
    model = None
    device = None

    @classmethod
    def load_model(cls, model_name="prot_bert_bfd", device=torch.device("cpu")) -> None:
        from transformers import BertModel, BertTokenizer

        data_dir = Path(__file__).parent.joinpath("data", model_name).resolve(strict=True)
        cls.tokenizer = BertTokenizer.from_pretrained(data_dir.as_posix(), do_lower_case=False)
        cls.model = BertModel.from_pretrained(data_dir.as_posix())
        cls.model = cls.model.eval().to(device)
        cls.device = device

    @classmethod
    def build(cls, sequence: str, ligand_sequence: str) -> ProtBertData:
        return ProtBertData(protein_sequence=sequence, ligand_sequence=ligand_sequence)

    @classmethod
    def analyze_mutation(cls, mutation: str, data: ProtBertData) -> dict:
        raise NotImplementedError
