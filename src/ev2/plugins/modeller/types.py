from pathlib import Path
from typing import NamedTuple


class ModellerData(NamedTuple):
    root_dir: Path
    structure_file: Path
    use_auth_id: bool
    bioassembly_id: bool
    use_strict_alignment: bool
