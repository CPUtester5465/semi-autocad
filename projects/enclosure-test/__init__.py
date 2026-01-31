"""
EnclosureTest Project

A enclosure project

Usage:
    from projects.enclosure_test import create_assembly, CONFIG

    assembly = create_assembly()
    assembly.export(output_dir)
"""

from .config import CONFIG, PRESETS, EnclosureConfig
from .frame import generate_body, generate_lid, generate_enclosure
from .assembly import create_assembly, EnclosureAssembly

__all__ = [
    "CONFIG",
    "PRESETS",
    "EnclosureConfig",
    "generate_body",
    "generate_lid",
    "generate_enclosure",
    "create_assembly",
    "EnclosureAssembly",
]
