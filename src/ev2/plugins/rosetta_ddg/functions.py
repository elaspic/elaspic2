import logging
import re
from pathlib import Path
from typing import List, Union

import pandas as pd
from kmbio.PDB import Structure
from kmtools import structure_tools, system_tools
from kmtools.structure_tools.types import DomainMutation as Mutation

from elaspic2.core.utils import features_to_differences
from elaspic2.plugins.rosetta_ddg.types import RosettaDDGData

logger = logging.getLogger(__name__)


def relax_structure(self):
    """Not used..."""
    system_command = self.relax_sct.format(weights=self.weights)
    process = system_tools.run(system_command, cwd=self.tempdir)
    cst_file_data = []
    for line in process.stdout:
        if line.startswith("c-alpha"):
            line = line.strip().split()
            cst_file_data.append("AtomPair CA {line[5]} CA {line[7]} HARMONIC {line[9]} {line[12]}")


def to_rosetta_coords(structure: Structure, mutation: Mutation) -> Mutation:
    """Convert mutation to Rosetta coordinates."""
    # Rosetta just joins residues (does not reset residue_idx at chain break)
    residue_idx_offset = 0
    for chain in structure.chains:
        if chain.id == mutation.chain_id:
            break
        residue_idx_offset += len(
            structure_tools.get_chain_sequence(
                chain, if_unknown="replace", unknown_residue_marker=""
            )
        )
    mutation = mutation._replace(residue_id=mutation.residue_id + residue_idx_offset)
    return mutation


def write_mutation_file(mut: Mutation, temp_dir: Path) -> Path:
    """Write a mutation file recognized by Rosetta inside `temp_dir`."""
    mutation_file = temp_dir.joinpath(f"{mut.residue_wt}{mut.residue_id}{mut.residue_mut}.txt")
    with open(mutation_file, "w") as ofh:
        ofh.write("total 1\n" "1\n" f"{mut.residue_wt} {mut.residue_id} {mut.residue_mut}\n")
    return mutation_file


# =============================================================================
# `ddg_monomer` protocol
# =============================================================================


def get_ddg_monomer_file(temp_dir: Path) -> Path:
    return temp_dir.joinpath("ddg_predictions.out")


def parse_ddg_monomer_file(ddg_file: Path) -> dict:
    df = pd.read_csv(ddg_file, sep=" +", engine="python", skip_blank_lines=True)
    df = df.drop("ddG:", axis=1).rename(columns={"description": "mutation", "total": "ddg"})
    assert len(df) == 1
    df = df.rename(columns=lambda c: c + "_change" if c != "ddg" else "dg_change")
    return df.mean().to_dict()


# =============================================================================
# `cartesian_ddg` protocol
# =============================================================================


def get_cartesian_ddg_file(mut: Mutation, temp_dir: Path) -> Path:
    return temp_dir.joinpath(f"{mut.residue_wt}{mut.residue_id}{mut.residue_mut}.ddg")


def parse_cartesian_ddg_file(ddg_file: Path) -> dict:
    rows = []
    with open(ddg_file) as ifh:
        for line in ifh:
            row = {}
            cols = re.split(" +", line)
            while len(cols):
                value: Union[str, float] = cols.pop().strip(": \n")
                try:
                    value = float(value)
                except ValueError:
                    pass
                if len(cols) > 1:
                    key = cols.pop().strip(": \n")
                    row[key] = value
                elif len(cols) == 1:
                    row["round"] = value
                elif len(cols) == 0:
                    row["state"] = value
                else:
                    raise Exception("This should never happen!")
            rows.append(row)
    df = pd.DataFrame(rows)
    df = _merge_cartesian_wt_mut(df)
    df = features_to_differences(df)
    df.drop("round", axis=1, inplace=True)
    df_opt_apart = df[df["state"] == "OPT_APART"].drop("state", axis=1).reset_index(drop=True)
    df_apart = df[df["state"] == "APART"].drop("state", axis=1).reset_index(drop=True)
    df_complex = df[df["state"] == "COMPLEX"].drop("state", axis=1).reset_index(drop=True)
    assert len(df) == (len(df_opt_apart) + len(df_apart) + len(df_complex))
    if df_opt_apart.empty and df_apart.empty:
        return df.mean().to_dict()
    else:
        assert len(df_opt_apart) == len(df_apart) == len(df_complex)
        df_opt_bind = df_complex - df_opt_apart
        df_bind = df_complex - df_apart
        return {
            **df_opt_apart.rename(columns=lambda c: "opt_apart_" + c).mean().to_dict(),
            **df_apart.rename(columns=lambda c: "apart_" + c).mean().to_dict(),
            **df_complex.rename(columns=lambda c: "complex_" + c).mean().to_dict(),
            **df_opt_bind.rename(columns=lambda c: "opt_bind_" + c).mean().to_dict(),
            **df_bind.rename(columns=lambda c: "bind_" + c).mean().to_dict(),
            "num_rounds": len(df_complex),
        }


def _merge_cartesian_wt_mut(df):
    """Merge ``wt`` and ``mut`` rows into a single row."""
    mut_column = [c for c in df.columns if c.startswith("MUT_")]
    assert len(mut_column) == 1
    mut_column = mut_column[0]
    #
    df_wt_mut = (
        df[df["WT"].notnull()]
        .drop(mut_column, axis=1)
        .merge(
            df[df["WT"].isnull()].drop("WT", axis=1),
            on=["state", "round"],
            suffixes=("_wt", "_mut"),
        )
    )
    assert len(df_wt_mut) == len(df) // 2, (len(df_wt_mut), len(df))
    df_wt_mut = df_wt_mut.rename(columns={"WT": "dg_wt", mut_column: "dg_mut"})
    return df_wt_mut


# =============================================================================
# Shared API for two protocols
# =============================================================================


def read_mutation_ddg(protocol: str, temp_dir: Path, mut: Mutation) -> dict:
    """Read output for a given Rosetta ΔΔG protocol."""
    if protocol == "ddg_monomer":
        ddg_file = get_ddg_monomer_file(temp_dir)
        results = parse_ddg_monomer_file(ddg_file)
    elif protocol == "cartesian_ddg":
        ddg_file = get_cartesian_ddg_file(mut, temp_dir)
        results = parse_cartesian_ddg_file(ddg_file)
    else:
        raise Exception
    return results


# =============================================================================
# System Commands
# =============================================================================


def get_system_command(data: RosettaDDGData, mutation_file: Path) -> str:
    """Generate a Rosetta ΔΔG system command.

    Full description of every argument can be found at:
    https://www.rosettacommons.org/docs/latest/full-options-list


    """
    import pyrosetta.database

    rosetta_db = Path(pyrosetta.database.__path__[0]).resolve().as_posix()

    sc: List[str] = []

    if data.protocol == "ddg_monomer":
        sc += [
            "ddg_monomer.static.linuxgccrelease",
            "-ddg::weight_file soft_rep_design",
            "-ddg::local_opt_only true",
            "-ddg::out ddg_predictions.out",  # this parameter does not work for cartesian_ddg
        ]
    elif data.protocol == "cartesian_ddg":
        sc += [
            "cartesian_ddg.static.linuxgccrelease",
            "-ddg::cartesian",
            "-ddg::bbnbrs 1",
        ]
    else:
        raise Exception

    sc += [
        f"-in:file:s '{data.structure_file}'",
        "-in::file::fullatom",
        f"-database '{rosetta_db}'",
        "-ignore_unrecognized_res true",
        "-ignore_zero_occupancy false",
        "-fa_max_dis 9.0",
        f"-ddg::mut_file '{mutation_file}'",
        f"-ddg::iterations {_get_num_iterations(data)}",
        "-ddg::dump_pdbs true",
        "-ddg::suppress_checkpointing true",
        "-ddg::mean true",
        "-ddg::min true",
        "-ddg::output_silent true",
    ]

    if data.energy_function.startswith("beta"):
        sc += [f"-{data.energy_function}"]
    elif data.energy_function.startswith("talaris"):
        sc += [f"-score:weights {data.energy_function}", "-restore_talaris_behavior"]
    else:
        sc += [f"-score:weights {data.energy_function}"]

    if data.interface:
        sc += [f"-interface_ddg {data.interface}"]

    return " ".join(sc)


def _get_num_iterations(data: RosettaDDGData) -> int:
    if data.quick:
        return 1

    if data.protocol == "ddg_monomer":
        return 50
    elif data.protocol == "cartesian_ddg":
        return 3
    else:
        raise Exception
