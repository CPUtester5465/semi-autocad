"""
Semi-AutoCAD Core Module

Provides abstractions for components, assemblies, and projects.
"""

from .component import Component, ComponentSpec
from .registry import CacheStats, ComponentRegistry
from .project import Project

__all__ = ["CacheStats", "Component", "ComponentSpec", "ComponentRegistry", "Project"]
