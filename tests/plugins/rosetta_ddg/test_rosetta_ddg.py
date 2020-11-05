import os
import subprocess
import unittest.mock
from pathlib import Path

import pytest

from elaspic2.plugins.rosetta_ddg import RosettaDDG

TESTS_DIR = Path(__file__).absolute().parent


@pytest.mark.parametrize(
    "structure, mutation, is_correct",
    [
        # (TESTS_DIR.joinpath("structures").joinpath("1SBN.pdb"), "I_R38K", True),  # TODO: Fix
        (TESTS_DIR.joinpath("structures").joinpath("2JEL.pdb"), "P_A81S", False),
        (TESTS_DIR.joinpath("structures").joinpath("2JEL.pdb"), "P_A82S", True),
        (TESTS_DIR.joinpath("structures").joinpath("1ekg.cif"), "A_D15G", True),
        (TESTS_DIR.joinpath("structures").joinpath("1t7hb.pdb"), "B_S4Y", True),
        (TESTS_DIR.joinpath("structures").joinpath("1t7h.cif"), "B_S4Y", True),
        (TESTS_DIR.joinpath("structures").joinpath("1yf4b.pdb"), "B_Q4N", True),
    ],
)
def test_correct_residue(structure: Path, mutation: str, is_correct: bool):
    data = RosettaDDG.build(
        structure,
        protocol="cartesian_ddg",
        energy_function="beta_cart",
        interface=False,
        quick=True,
    )

    class ResidueMatchError(Exception):
        pass

    class ResidueMismatchError(Exception):
        pass

    def subprocess_run(*args, **kwargs):
        for key in ["stdout", "stderr", "timeout", "check", "bufsize"]:
            if key in kwargs:
                kwargs.pop(key)
        proc = subprocess.Popen(
            *args, **kwargs, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        for line in proc.stdout:
            if "ERROR: Assertion `pose.residue(resnum).name1() == wt` failed" in line:
                raise ResidueMismatchError
            if "protocols.relax.FastRelax" in line:
                raise ResidueMatchError
        raise Exception("Unexpected result.")

    with unittest.mock.patch(
        "elaspic2.plugins.rosetta_ddg.rosetta_ddg.subprocess.run", subprocess_run
    ):
        with pytest.raises(ResidueMatchError if is_correct else ResidueMismatchError):
            RosettaDDG.analyze_mutation(mutation, data)


@pytest.mark.skipif(os.getenv("SKIP_SLOW_TESTS") is not None, reason="Skipping slow tests")
@pytest.mark.parametrize(
    "structure, mutation, protocol, energy_function, interface",
    [
        (
            structure,
            mutation,
            protocol,
            energy_function + ("_cart" if "cartesian" in protocol else ""),
            interface,
        )
        for structure, mutation in [
            # (TESTS_DIR.joinpath("structures").joinpath("1ekg.cif"), "A-D15G"),
            # (TESTS_DIR.joinpath("structures").joinpath("1t7hb.pdb"), "B-S4Y")
            (TESTS_DIR.joinpath("structures").joinpath("1t7h.cif"), "B_S4Y")
            # (TESTS_DIR.joinpath("structures").joinpath("1yf4b.pdb"), "B-Q4N")
        ]
        for protocol in ["ddg_monomer", "cartesian_ddg"]
        for energy_function in [
            "beta",
            "beta_nov16",
            # "beta_july15",  # throws an error
            "talaris2014",
            "talaris2013",
            "score12",
            "soft_rep_design",
        ]
        for interface in [1, 0]
        if (protocol, energy_function) != ("cartesian_ddg", "soft_rep_design")
        and (protocol != "ddg_monomer" or interface == 0)
    ],
)
def test_parameter_grid(structure, mutation, protocol, energy_function, interface):
    """Make sure `RosettaDDG.analyze_mutation` works with every combination of parameters."""
    data = RosettaDDG.build(
        structure,
        protocol=protocol,
        energy_function=energy_function,
        interface=interface,
        quick=True,
    )
    results = RosettaDDG.analyze_mutation(mutation, data)
    print(results)
