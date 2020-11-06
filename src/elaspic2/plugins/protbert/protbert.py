import importlib.resources
import logging
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import torch
from kmtools.structure_tools.types import DomainMutation as Mutation

import elaspic2.plugins.protbert.data
from elaspic2.core import MutationAnalyzer, SequenceTool
from elaspic2.plugins.protbert.types import ProtBertData

logger = logging.getLogger(__name__)


class ProtBert(SequenceTool, MutationAnalyzer):
    tokenizer = None
    model = None
    model_lm = None
    device = None
    is_loaded: bool = False

    @classmethod
    def load_model(cls, model_name="prot_bert_bfd", device=torch.device("cpu")) -> None:
        from transformers import BertForMaskedLM, BertModel, BertTokenizer, logging

        @contextmanager
        def hide_warning():
            try:
                logging.set_verbosity_error()
                yield
            finally:
                logging.set_verbosity_warning()

        with importlib.resources.path(elaspic2.plugins.protbert.data, "prot_bert_bfd") as data_dir:
            cls._download_model_data(data_dir)
            cls.tokenizer = BertTokenizer.from_pretrained(data_dir.as_posix(), do_lower_case=False)
            cls.model = BertModel.from_pretrained(data_dir.as_posix())
            with hide_warning():
                cls.model_lm = BertForMaskedLM.from_pretrained(data_dir.as_posix())

        cls.model = cls.model.eval().to(device)
        cls.model_lm = cls.model_lm.eval().to(device)
        cls.device = device
        cls.is_loaded = True

    @staticmethod
    def _download_model_data(data_dir: Path):
        tag = f"v{elaspic2.__version__}"
        url = (
            f"https://gitlab.com/elaspic/elaspic-v2/-/raw/{tag}/src/elaspic2/"
            "plugins/protbert/data/prot_bert_bfd/pytorch_model.bin"
        )
        protbert_model_file = data_dir.joinpath("pytorch_model.bin")
        if not protbert_model_file.is_file():
            logger.info("Downloading ProtBert model files. This may take several minutes...")
            urllib.request.urlretrieve(url, protbert_model_file)

    @classmethod
    def build(  # type: ignore[override]
        cls, sequence: str, ligand_sequence: str, remove_hetatms=True
    ) -> ProtBertData:
        if ligand_sequence is not None:
            sequence += ligand_sequence
        if remove_hetatms:
            sequence = sequence.replace("X", "")
        return ProtBertData(sequence=sequence)

    @classmethod
    def analyze_mutation(cls, mutation: str, data: ProtBertData) -> dict:  # type: ignore[override]

        mut = Mutation.from_string(mutation)

        if data.sequence[int(mut.residue_id) - 1] != mut.residue_wt:
            raise ProtBertAnalyzeError(
                f"Mutation does not match sequence ({mut}, {data.sequence})."
            )

        scores_dict = cls._get_scores(data, mut)
        features_dict = cls._get_features(data, mut)

        return {**scores_dict, **features_dict}

    @classmethod
    def _get_scores(cls, data: ProtBertData, mut: Mutation) -> dict:
        if cls.tokenizer is None or cls.model is None:
            raise Exception("Call `ProtBert.load_model()` before using this class.")

        from transformers import pipeline

        unmasker = pipeline("fill-mask", model=cls.model_lm, tokenizer=cls.tokenizer, topk=30)
        aa_list = list(data.sequence)
        assert aa_list[int(mut.residue_id) - 1] == mut.residue_wt
        aa_list[int(mut.residue_id) - 1] = "[MASK]"
        scores = unmasker(" ".join(aa_list))
        score_wt = next((s["score"] for s in scores if s["token_str"] == mut.residue_wt))
        score_mut = next((s["score"] for s in scores if s["token_str"] == mut.residue_mut))
        return {"score_wt": score_wt, "score_mut": score_mut}

    @classmethod
    def _get_features(cls, data: ProtBertData, mut: Mutation) -> dict:
        if cls.tokenizer is None or cls.model is None:
            raise Exception("Call `ProtBert.load_model()` before using this class.")

        mut_idx = int(mut.residue_id) - 1

        aa_wt_list = list(data.sequence)
        aa_mut_list = aa_wt_list[:]
        aa_mut_list[mut_idx] = mut.residue_mut
        assert aa_wt_list[mut_idx] == mut.residue_wt
        assert aa_mut_list[mut_idx] == mut.residue_mut

        encoded_input_wt = cls.tokenizer(" ".join(list(aa_wt_list)), return_tensors="pt")
        output_wt, output_cls_wt = cls.model(**encoded_input_wt)

        encoded_input_mut = cls.tokenizer(" ".join(list(aa_mut_list)), return_tensors="pt")
        output_mut, output_cls_mut = cls.model(**encoded_input_mut)

        return {
            "features_residue_wt": output_wt[:, mut_idx].squeeze().data.cpu().numpy().tolist(),
            "features_protein_wt": output_wt.mean(dim=1).squeeze().data.cpu().numpy().tolist(),
            "features_residue_mut": output_mut[:, mut_idx].squeeze().data.cpu().numpy().tolist(),
            "features_protein_mut": output_mut.mean(dim=1).squeeze().data.cpu().numpy().tolist(),
        }


class ProtBertBuildError(Exception):
    pass


class ProtBertAnalyzeError(Exception):
    pass
