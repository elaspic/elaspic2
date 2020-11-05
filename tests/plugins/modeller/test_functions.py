import tempfile
from pathlib import Path

import kmbio.PDB
import pytest
from kmtools import structure_tools
from kmtools.structure_tools import DomainTarget

from elaspic2.plugins.modeller import run_modeller

TESTS_DIR = Path(__file__).absolute().parent


@pytest.mark.parametrize(
    "structure_file, targets, num_hetatms",
    [
        (
            TESTS_DIR.joinpath("structures", "1yf4b.pdb"),
            [DomainTarget(0, "B", "CYFQNCPRG", None, None, "CAFQNCPRG")],
            4,
        ),
        (
            TESTS_DIR.joinpath("structures", "1yf4.cif"),
            [
                DomainTarget(
                    0, "A", "LQGIVSWGYGCAQKNKPGVYT-----KV", 187, 209, "LGGGVSWGYGCAQKNKPGVYTKGGGGGV"
                ),
                DomainTarget(0, "B", "CYFQNCPRG", None, None, "CYFQNCPRG"),
            ],
            35,
        ),
    ],
)
def test_run_modeller(structure_file: Path, targets: DomainTarget, num_hetatms: int):
    structure = kmbio.PDB.load(structure_file)
    structure_fm, alignment = structure_tools.prepare_for_modeling(structure, targets)
    with tempfile.TemporaryDirectory() as temp_dir:
        results = run_modeller(structure_fm, alignment, temp_dir)
        structure_bm = kmbio.PDB.load(Path(temp_dir).joinpath(results["name"]))
    # Make sure we have expected model id
    assert [m.id for m in structure_bm] == [0]
    # Make sure we have expected chain id(s)
    num_chains = len(targets) + (1 if num_hetatms > 0 else 0)
    assert len(list(structure_fm[0].chains)) == num_chains
    if num_chains == 1:
        assert [c.id for c in structure_bm[0]] == [" "]
    else:
        assert [c.id for c in structure_bm[0]] == structure_tools.CHAIN_IDS[:num_chains]
    # Make sure we have expected sequence(s)
    for chain, target in zip(structure_bm.chains, targets):
        assert (
            structure_tools.get_chain_sequence(chain, if_unknown="replace")
            == target.target_sequence
        )
    assert len(list(list(structure_fm[0].chains)[-1].residues)) == num_hetatms
    # Make sure we have expected result fields
    for key in ["name", "Normalized DOPE score", "GA341 score"]:
        assert key in results
