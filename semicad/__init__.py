"""
Semi-AutoCAD - AI-assisted CAD design system.

Uses CadQuery for parametric modeling and Neo4j for design memory.
"""

__version__ = "0.1.0"

from semicad.core.component import Component, ComponentSpec
from semicad.core.project import Project, get_project
from semicad.core.registry import ComponentRegistry, get_registry

__all__ = [
    "Component",
    "ComponentRegistry",
    "ComponentSpec",
    "Project",
    "get_project",
    "get_registry",
]
