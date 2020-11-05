from pathlib import Path
from typing import NamedTuple, Optional


class RosettaDDGData(NamedTuple):
    unique_id: str
    root_dir: Path
    structure_file: str
    protocol: str = "cartesian_ddg"
    energy_function: str = "beta_nov16_cart"
    # Calculate the ΔΔG of binding for the specified interface
    interface: Optional[int] = None
    #: Run the quickest mode available
    quick: bool = False
