__version__ = "0.1.0"
__all__ = ["core", "plugins"]

from kmbio.PDB.core import Atom

Atom.get_coord = lambda self: self.coord

from . import *