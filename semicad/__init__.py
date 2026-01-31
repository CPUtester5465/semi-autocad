"""
Semi-AutoCAD - AI-assisted CAD design system.

Uses CadQuery for parametric modeling and Neo4j for design memory.
"""

__version__ = "0.1.0"

from semicad.core.component import Component, ComponentSpec
from semicad.core.registry import get_registry, ComponentRegistry
from semicad.core.project import get_project, Project

__all__ = [
    "Component",
    "ComponentSpec",
    "ComponentRegistry",
    "get_registry",
    "Project",
    "get_project",
]
