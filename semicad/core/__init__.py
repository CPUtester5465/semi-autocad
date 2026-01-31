"""
Semi-AutoCAD Core Module

Provides abstractions for components, assemblies, and projects.
"""

from .component import Component, ComponentSpec
from .registry import ComponentRegistry
from .project import Project

__all__ = ["Component", "ComponentSpec", "ComponentRegistry", "Project"]
