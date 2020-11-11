__version__ = "0.1.3"
__all__ = ["core", "utils", "plugins"]

from kmbio.PDB.core import Atom

Atom.get_coord = lambda self: self.coord

from . import *
from .types import ELASPIC2Data
from .elaspic2 import ELASPIC2
