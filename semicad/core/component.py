"""
Component abstraction - Single Responsibility: Define what a component IS.

A Component is any CAD part that can be:
- Generated (parametric)
- Loaded (from file)
- Positioned (in an assembly)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
import cadquery as cq


@dataclass
class ComponentSpec:
    """Specification for a component - metadata without the geometry."""
    name: str
    source: str  # e.g., "custom", "cq_warehouse", "partcad"
    category: str  # e.g., "fastener", "motor", "electronics"
    params: dict = field(default_factory=dict)
    description: str = ""

    @property
    def full_name(self) -> str:
        """Fully qualified name: source/category/name"""
        return f"{self.source}/{self.category}/{self.name}"


@runtime_checkable
class ComponentProvider(Protocol):
    """Protocol for anything that can provide a CadQuery object."""

    def build(self) -> cq.Workplane:
        """Build and return the CadQuery geometry."""
        ...


class Component(ABC):
    """
    Abstract base for all components.

    Liskov Substitution: Any Component subclass can be used wherever
    Component is expected.
    """

    def __init__(self, spec: ComponentSpec):
        self._spec = spec
        self._geometry: cq.Workplane | None = None

    @property
    def spec(self) -> ComponentSpec:
        return self._spec

    @property
    def name(self) -> str:
        return self._spec.name

    @abstractmethod
    def build(self) -> cq.Workplane:
        """Build the component geometry. Must be implemented by subclasses."""
        pass

    @property
    def geometry(self) -> cq.Workplane:
        """Lazy-load geometry on first access."""
        if self._geometry is None:
            self._geometry = self.build()
        return self._geometry

    def translate(self, x: float = 0, y: float = 0, z: float = 0) -> "Component":
        """Return a translated copy of this component."""
        translated = TranslatedComponent(self, x, y, z)
        return translated

    def rotate(self, axis: tuple, angle: float) -> "Component":
        """Return a rotated copy of this component."""
        return RotatedComponent(self, axis, angle)


class TranslatedComponent(Component):
    """Decorator for translated components."""

    def __init__(self, wrapped: Component, x: float, y: float, z: float):
        super().__init__(wrapped.spec)
        self._wrapped = wrapped
        self._offset = (x, y, z)

    def build(self) -> cq.Workplane:
        return self._wrapped.geometry.translate(self._offset)


class RotatedComponent(Component):
    """Decorator for rotated components."""

    def __init__(self, wrapped: Component, axis: tuple, angle: float):
        super().__init__(wrapped.spec)
        self._wrapped = wrapped
        self._axis = axis
        self._angle = angle

    def build(self) -> cq.Workplane:
        return self._wrapped.geometry.rotate((0, 0, 0), self._axis, self._angle)
