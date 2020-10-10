from pathlib import Path
from typing import List

import numpy as np
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
        protein_aa_list = list(sequence)
        if ligand_sequence is not None:
            ligand_aa_list = list(ligand_sequence)
            combined_aa_list = protein_aa_list + ligand_aa_list
        else:
            ligand_aa_list = None
            combined_aa_list = None
        return ProtBertData(
            protein_sequence=" ".join(protein_aa_list),
            ligand_sequence=" ".join(ligand_aa_list) if ligand_aa_list else None,
            combined_sequence=" ".join(combined_aa_list) if combined_aa_list else None,
        )

    @classmethod
    def analyze_mutation(cls, mutation: str, data: ProtBertData) -> dict:
        protein_aa_list = data.protein_aa_list[:]
        ligand_aa_list = data.ligand_aa_list[:] if data.ligand_aa_list else None
        combined_aa_list = (
            (protein_aa_list + ligand_aa_list) if ligand_aa_list is not None else None
        )

        protein_aa_mut_list = data.protein_aa_list[:]
        assert protein_aa_mut_list[int(mutation[1:-1]) - 1] == mutation[0]
        protein_aa_mut_list[int(mutation[1:-1]) - 1] = mutation[-1]
        combined_aa_mut_list = (
            (protein_aa_mut_list + ligand_aa_list) if ligand_aa_list is not None else None
        )

        sequences = [" ".join(protein_aa_list), " ".join(protein_aa_mut_list)]
        if combined_aa_list is not None:
            sequences += [" ".join(combined_aa_list), " ".join(combined_aa_mut_list)]
        features = cls._get_embeddings(sequences, mutation)

        return features

    @classmethod
    def _get_embeddings(cls, sequences: List[str], mutation: str) -> List[np.ndarray]:
        ids = cls.tokenizer.batch_encode_plus(sequences, add_special_tokens=True, padding="longest")

        input_ids = torch.tensor(ids["input_ids"]).to(cls.device)
        attention_mask = torch.tensor(ids["attention_mask"]).to(cls.device)
        with torch.no_grad():
            embedding = cls.model(input_ids=input_ids, attention_mask=attention_mask)[0]
        embedding = embedding.cpu().numpy()

        features = []
        for seq_num in range(len(embedding)):
            seq_len = (attention_mask[seq_num] == 1).sum()
            seq_emd = embedding[seq_num][1 : seq_len - 1]
            seq_emd_sum = seq_emd.sum(axis=0)
            seq_emd_pos = seq_emd[int(mutation[1:-1]) - 2]
            features.append((seq_emd_sum, seq_emd_pos))

        return features
