import logging
from pathlib import Path
from typing import Callable, Union

from kmbio import PDB
from kmtools import py_tools, structure_tools, system_tools

logger = logging.getLogger(__name__)


def run_modeller(structure, alignment, temp_dir: Union[str, Path, Callable]):
    """Run Modeller to create a homology model.

    Args:
        structure: Structure of the template protein.
        alignment_file: Alignment of the target sequence(s) to chain(s) of the template structure.
        temp_dir: Location to use for storing Modeller temporary files and output.

    Returns:
        results: A dictionary of model properties. Of particular interest are the followng:

            `name`: The name of the generated PDB structure.
            `Normalized DOPE score`: DOPE score that should be comparable between structures.
            `GA341 score`: GA341 score that should be comparable between structures.
    """
    import modeller
    from modeller.automodel import assess, automodel, autosched

    if isinstance(structure, (str, Path)):
        structure = PDB.load(structure)

    if callable(temp_dir):
        temp_dir = Path(temp_dir())
    else:
        temp_dir = Path(temp_dir)

    assert len(alignment) == 2
    target_id = alignment[0].id
    template_id = alignment[1].id

    PDB.save(structure, temp_dir.joinpath(f"{template_id}.pdb"))
    alignment_file = temp_dir.joinpath(f"{template_id}-{target_id}.aln")
    structure_tools.write_pir_alignment(alignment, alignment_file)

    # Don't display log messages
    modeller.log.none()

    # Create a new MODELLER environment
    env = modeller.environ()

    # Directories for input atom files
    env.io.atom_files_directory = [str(temp_dir)]
    env.schedule_scale = modeller.physical.values(default=1.0, soft_sphere=0.7)

    # Selected atoms do not feel the neighborhood
    # env.edat.nonbonded_sel_atoms = 2
    env.io.hetatm = True  # read in HETATM records from template PDBs
    env.io.water = True  # read in WATER records (including waters marked as HETATMs)

    a = automodel(
        env,
        # alignment filename
        alnfile=str(alignment_file),
        # codes of the templates
        knowns=(str(template_id)),
        # code of the target
        sequence=str(target_id),
        # wich method for validation should be calculated
        assess_methods=(assess.DOPE, assess.normalized_dope, assess.GA341),
    )
    a.starting_model = 1  # index of the first model
    a.ending_model = 1  # index of the last model

    # Very thorough VTFM optimization:
    a.library_schedule = autosched.slow
    a.max_var_iterations = 300

    # Thorough MD optimization:
    # a.md_level = refine.slow
    a.md_level = None

    # a.repeat_optimization = 2

    # Stop if the objective function is higher than this value
    a.max_molpdf = 2e6

    with py_tools.log_print_statements(logger), system_tools.switch_paths(temp_dir):
        a.make()

    assert len(a.outputs) == 1
    return a.outputs[0]
