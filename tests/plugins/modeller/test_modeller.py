from pathlib import Path

import pytest
import yaml
from kmtools.structure_tools import DomainMutation, DomainTarget

from elaspic2.plugins.modeller import Modeller

TESTS_DIR = Path(__file__).absolute().parent


# --- Load test data ---


def make_kwargs_constructor(obj):
    def kwargs_constructor(loader, node):
        values = loader.construct_mapping(node)
        return obj(**values)

    return kwargs_constructor


yaml.add_constructor("!DomainMutation", make_kwargs_constructor(DomainMutation))
yaml.add_constructor("!DomainTarget", make_kwargs_constructor(DomainTarget))

with Path(__file__).with_suffix(".yaml").open("rt") as fin:
    TEST_DATA = yaml.load(fin, Loader=yaml.FullLoader)


# --- Tests ---


@pytest.mark.parametrize("structure_file, mutations", TEST_DATA["test_modeller_mutate"])
def test_modeller_mutate(structure_file: Path, mutations: DomainMutation):
    structure_file = TESTS_DIR.joinpath(structure_file)
    modeller_data = Modeller.build(structure_file)
    structure_bm, results = Modeller.mutate(mutations, modeller_data)


@pytest.mark.parametrize("structure_file, targets", TEST_DATA["test_create_model"])
def test_create_model(structure_file: Path, targets: DomainTarget):
    structure_file = TESTS_DIR.joinpath(structure_file)
    modeller_data = Modeller.build(structure_file)
    structure_bm, results = Modeller.create_model(targets, modeller_data)


@pytest.mark.parametrize(
    "structure_file, targets, key",
    [
        (structure_file, targets, key)
        for key in [
            "large_structures",
            "different_model_ids",
            "low_quality_model",
            "modified_residues",
            "unknown_residues",
        ]
        for (structure_file, targets) in TEST_DATA["test_create_model-" + key]
    ],
)
def test_create_model_edge_cases(structure_file: Path, targets: DomainTarget, key: str):
    structure_file = TESTS_DIR.joinpath(structure_file)
    modeller_data = Modeller.build(structure_file)
    structure_bm, results = Modeller.create_model(targets, modeller_data)
