"""
Component Sources - Adapters for different component libraries.

Each source adapts a library to the ComponentSource interface,
following the Adapter pattern and Dependency Inversion principle.
"""

from . import custom
from . import warehouse
from . import electronics
from . import partcad_source

__all__ = ["custom", "warehouse", "electronics", "partcad_source"]
