from typing import List, TypeVar

import pandas as pd


def get_sequence_features(aa_sequence: str, mutations: List[str]):
    pass


def get_structure_features(aa_sequence: str):
    pass


T = TypeVar("T", dict, pd.DataFrame)


def features_to_differences(data: T, keep_wt: bool = True) -> T:
    data = data.copy()
    for key in data:
        key_wt = key[: -len("_mut")] + "_wt"
        key_change = key[: -len("_mut")] + "_change"
        if key.endswith("_mut") and key_wt in data:
            data[key_change] = data[key] - data[key_wt]
            del data[key]
            if not keep_wt:
                del data[key_wt]
    return data
