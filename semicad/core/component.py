"""
Component abstraction - Single Responsibility: Define what a component IS.

A Component is any CAD part that can be:
- Generated (parametric)
- Loaded (from file)
- Positioned (in an assembly)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import cadquery as cq

if TYPE_CHECKING:
    from semicad.core.validation import ValidationResult


@dataclass
class ComponentSpec:
    """Specification for a component - metadata without the geometry.

    Attributes:
        name: Short name of the component (e.g., "motor_2207").
        source: Source identifier (e.g., "custom", "cq_warehouse", "partcad").
        category: Component category (e.g., "fastener", "motor", "electronics").
        params: Parameter definitions for parametric components.
        description: Human-readable description of the component.
        metadata: Additional component metadata (dimensions, weight, etc.).
    """

    name: str
    source: str
    category: str
    params: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

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

    def validate(
        self,
        max_dimension: float | None = None,
        min_dimension: float | None = None,
    ) -> "ValidationResult":
        """
        Validate the component geometry.

        Performs checks including:
        - Geometry builds successfully
        - Geometry contains solid bodies
        - OCC shape validity
        - Bounding box sanity checks

        Args:
            max_dimension: Maximum allowed dimension in mm (default: 2000)
            min_dimension: Minimum allowed dimension in mm (default: 0.01)

        Returns:
            ValidationResult with issues and metrics
        """
        from semicad.core.validation import (
            MAX_DIMENSION,
            MIN_DIMENSION,
            IssueSeverity,
            ValidationIssue,
            ValidationResult,
            validate_geometry,
        )

        # Use defaults if not specified
        if max_dimension is None:
            max_dimension = MAX_DIMENSION
        if min_dimension is None:
            min_dimension = MIN_DIMENSION

        try:
            geom = self.geometry  # This triggers build() if needed
            return validate_geometry(
                geom,
                self.name,
                max_dimension=max_dimension,
                min_dimension=min_dimension,
            )
        except Exception as e:
            # Build failed
            return ValidationResult(
                component_name=self.name,
                is_valid=False,
                issues=[ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    code="BUILD_FAILED",
                    message=f"Failed to build geometry: {e}",
                )],
            )

    def translate(self, x: float = 0, y: float = 0, z: float = 0) -> "Component":
        """Return a translated copy of this component."""
        translated = TranslatedComponent(self, x, y, z)
        return translated

    def rotate(
        self, axis: tuple[float, float, float], angle: float
    ) -> "Component":
        """Return a rotated copy of this component.

        Args:
            axis: Rotation axis as (x, y, z) unit vector.
            angle: Rotation angle in degrees.

        Returns:
            New component with rotation applied.
        """
        return RotatedComponent(self, axis, angle)


class TranslatedComponent(Component):
    """Decorator for translated components."""

    def __init__(self, wrapped: Component, x: float, y: float, z: float) -> None:
        super().__init__(wrapped.spec)
        self._wrapped = wrapped
        self._offset: tuple[float, float, float] = (x, y, z)

    def build(self) -> cq.Workplane:
        return self._wrapped.geometry.translate(self._offset)


class RotatedComponent(Component):
    """Decorator for rotated components."""

    def __init__(
        self, wrapped: Component, axis: tuple[float, float, float], angle: float
    ) -> None:
        super().__init__(wrapped.spec)
        self._wrapped = wrapped
        self._axis: tuple[float, float, float] = axis
        self._angle = angle

    def build(self) -> cq.Workplane:
        return self._wrapped.geometry.rotate((0, 0, 0), self._axis, self._angle)
