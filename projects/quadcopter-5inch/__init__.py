"""
Quadcopter 5-inch Project
=========================
A 220mm wheelbase FPV freestyle quadcopter frame.

Usage:
    from projects.quadcopter_5inch import create_assembly, CONFIG

    assembly = create_assembly()
    assembly.export(output_dir)
"""

from .config import CONFIG, PRESETS, QuadConfig
from .frame import generate_frame
from .assembly import create_assembly, QuadcopterAssembly

__all__ = [
    "CONFIG",
    "PRESETS",
    "QuadConfig",
    "generate_frame",
    "create_assembly",
    "QuadcopterAssembly",
]
