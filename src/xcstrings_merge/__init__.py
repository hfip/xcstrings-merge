"""xcstrings-merge - move legacy .strings translations into a String Catalog."""

from .catalog import MergeError, MergeReport, load_catalog, merge, write_catalog
from .strings import decode, load_strings, parse_strings, unescape

__version__ = "0.1.0"

__all__ = [
    "MergeError",
    "MergeReport",
    "decode",
    "load_catalog",
    "load_strings",
    "merge",
    "parse_strings",
    "unescape",
    "write_catalog",
    "__version__",
]
