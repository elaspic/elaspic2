import logging
import os.path as op
import shlex
import subprocess
from contextlib import closing
from pathlib import Path
from typing import Union

import kmbio.PDB
from kmbio.PDB import Structure
from kmtools import py_tools
from kmtools.structure_tools.types import DomainMutation as Mutation

from elaspic2.core.interface import MutationAnalyzer, StructureTool
from elaspic2.plugins.rosetta_ddg.functions import (
    get_system_command,
    read_mutation_ddg,
    to_rosetta_coords,
    write_mutation_file,
)
from elaspic2.plugins.rosetta_ddg.types import RosettaDDGData

logger = logging.getLogger(__name__)


class RosettaDDG(StructureTool, MutationAnalyzer):
    @classmethod
    def build(cls, structure: Union[str, Path, Structure], **kwargs) -> RosettaDDGData:
        if isinstance(structure, (str, Path)):
            unique_id = Path(structure).stem
            structure = kmbio.PDB.load(structure)
        else:
            unique_id = structure.id
        root_dir = cls.get_temp_dir(unique_id)
        structure_file = op.join(root_dir, unique_id + ".pdb")
        kmbio.PDB.save(structure, structure_file)
        return RosettaDDGData(unique_id, root_dir, structure_file, **kwargs)

    @classmethod
    def analyze_mutation(cls, mutation: str, data: RosettaDDGData, timeout: int = None) -> dict:
        if "cartesian" in data.protocol and not data.energy_function.endswith("_cart"):
            raise Exception("Using a cartesian ddG protocol without a cartesian energy function!")
        elif "cartesian" not in data.protocol and data.energy_function.endswith("_cart"):
            raise Exception("Using a non-cartesian ddG protocol with a cartesian energy function!")

        structure = kmbio.PDB.load(data.structure_file)
        mut = Mutation.from_string(mutation)
        mut = to_rosetta_coords(structure, mut)
        temp_dir = data.root_dir.joinpath(str(mut))
        temp_dir.mkdir()

        mutation_file = write_mutation_file(mut, temp_dir)
        system_command = get_system_command(data, mutation_file)

        logger.debug(system_command)
        with closing(py_tools.LogPipe(logger.debug)) as log_pipe:
            cp = subprocess.run(
                shlex.split(system_command),
                stdout=log_pipe,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=temp_dir,
                timeout=timeout,
                check=True,
            )
        if cp.stderr.strip():
            logger.info("Error messages:\n%s", cp.stderr.strip())
        # system_tools.execute(system_command, cwd=temp_dir)
        results = read_mutation_ddg(data.protocol, temp_dir, mut)
        return results
