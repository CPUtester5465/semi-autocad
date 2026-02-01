"""
Semi-AutoCAD Core Module

Provides abstractions for components, assemblies, and projects.
"""

from .component import Component, ComponentSpec
from .exceptions import (
    ComponentBuildError,
    ComponentError,
    ComponentNotFoundError,
    ExportError,
    ExportFormatError,
    ParameterValidationError,
    ProjectConfigError,
    ProjectError,
    ProjectNotFoundError,
    SemicadError,
    SourceError,
    SourceInitializationError,
    SourceNotAvailableError,
)
from .project import Project
from .registry import CacheStats, ComponentRegistry

__all__ = [
    "CacheStats",
    "Component",
    "ComponentBuildError",
    "ComponentError",
    "ComponentNotFoundError",
    "ComponentRegistry",
    "ComponentSpec",
    "ExportError",
    "ExportFormatError",
    "ParameterValidationError",
    "Project",
    "ProjectConfigError",
    "ProjectError",
    "ProjectNotFoundError",
    "SemicadError",
    "SourceError",
    "SourceInitializationError",
    "SourceNotAvailableError",
]
