from pathlib import Path

import pytest

from elaspic2.plugins.rosetta_ddg.functions import parse_cartesian_ddg_file, parse_ddg_monomer_file

TESTS_DIR = Path(__file__).absolute().parent


EXTRA_FEATURES = ["num_rounds"]


@pytest.mark.parametrize(
    "ddg_predictions_file",
    list(TESTS_DIR.joinpath("ddg_monomer").glob("*.out")),
    ids=lambda f: f.name,
)
def test_parse_ddg_monomer_file(ddg_predictions_file):
    result = parse_ddg_monomer_file(ddg_predictions_file)
    assert result
    assert isinstance(result, dict)
    assert all(k.endswith("_wt") or k.endswith("_change") or k in EXTRA_FEATURES for k in result)


@pytest.mark.parametrize(
    "ddg_predictions_file",
    list(TESTS_DIR.joinpath("cartesian_ddg").glob("*.ddg")),
    ids=lambda f: f.name,
)
def test_parse_cartesian_ddg_file(ddg_predictions_file):
    result = parse_cartesian_ddg_file(ddg_predictions_file)
    assert result
    assert isinstance(result, dict)
    assert all(k.endswith("_wt") or k.endswith("_change") or k in EXTRA_FEATURES for k in result)
