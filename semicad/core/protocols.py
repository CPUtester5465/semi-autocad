"""Protocols for third-party CAD library integration.

These protocols define the contracts we expect from external libraries,
enabling type checking without requiring library-specific stubs.

This module provides:
- CQObjectProvider: Base protocol for objects with .cq_object attribute
- ParametricPart: Protocol for parts with size enumeration
- AssemblyProvider: Protocol for colored assembly objects
- MountableComponent: Protocol for components with mounting holes

Usage:
    from semicad.core.protocols import CQObjectProvider

    def extract_geometry(obj: CQObjectProvider) -> cq.Workplane:
        return cq.Workplane("XY").add(obj.cq_object)

These protocols allow mypy to type-check code that uses third-party
CAD libraries (cq_warehouse, cq_electronics, etc.) without requiring
type stubs for those libraries.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CQObjectProvider(Protocol):
    """Protocol for objects that provide CadQuery geometry.

    This is the base protocol implemented by most cq_warehouse and
    cq_electronics components. The cq_object property returns either
    a Workplane or an Assembly.

    Implemented by:
        - cq_warehouse.fastener.* (SocketHeadCapScrew, etc.)
        - cq_warehouse.bearing.* (SingleRowDeepGrooveBallBearing, etc.)
        - cq_electronics.rpi.rpi3b.RPi3b
        - cq_electronics.connectors.headers.PinHeader
        - etc.
    """

    @property
    def cq_object(self) -> Any:  # Actually cq.Workplane | cq.Assembly
        """The CadQuery geometry object."""
        ...


@runtime_checkable
class ParametricPart(Protocol):
    """Protocol for parametric parts with size enumeration.

    This protocol is implemented by cq_warehouse fastener classes
    that provide a class method to list available sizes.

    Implemented by:
        - cq_warehouse.fastener.SocketHeadCapScrew
        - cq_warehouse.fastener.HexNut
        - etc.
    """

    @classmethod
    def sizes(cls, fastener_type: str = "") -> list[str]:
        """Return available size strings for this part type.

        Args:
            fastener_type: ISO type string (e.g., "iso4762")

        Returns:
            List of size strings (e.g., ["M2-0.4", "M3-0.5", "M4-0.7"])
        """
        ...

    @property
    def cq_object(self) -> Any:
        """The CadQuery geometry object."""
        ...


@runtime_checkable
class AssemblyProvider(Protocol):
    """Protocol for objects that provide colored assemblies.

    Some cq_electronics components return Assembly objects with
    colored sub-parts. This protocol allows type-safe handling
    of these assemblies while preserving color information.

    Implemented by:
        - cq_electronics.rpi.rpi3b.RPi3b (returns Assembly with colored parts)
    """

    @property
    def cq_object(self) -> Any:  # Actually cq.Assembly
        """The CadQuery assembly with colors."""
        ...


@runtime_checkable
class MountableComponent(Protocol):
    """Protocol for components with mounting holes.

    Many electronic boards expose mounting hole locations for
    enclosure design. This protocol provides type-safe access
    to those locations.

    Implemented by:
        - cq_electronics.rpi.rpi3b.RPi3b
        - Other board components with hole_points attribute
    """

    @property
    def hole_points(self) -> list[tuple[float, float]]:
        """Mounting hole (x, y) positions relative to board center."""
        ...


@runtime_checkable
class DimensionedComponent(Protocol):
    """Protocol for components with known dimensions.

    Components that expose their dimensions via class constants
    can implement this protocol for type-safe dimension access.

    Implemented by:
        - cq_electronics.rpi.rpi3b.RPi3b (WIDTH, HEIGHT, THICKNESS)
        - Other board/enclosure components
    """

    WIDTH: float
    HEIGHT: float


# Type aliases for common patterns
CQGeometry = Any  # cq.Workplane | cq.Assembly | cq.Shape
"""Type alias for CadQuery geometry objects."""

ParamValue = str | int | float | bool
"""Type alias for parameter values."""

ParamDict = dict[str, ParamValue]
"""Type alias for parameter dictionaries."""
