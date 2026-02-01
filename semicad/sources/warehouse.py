"""
cq_warehouse source - Adapts cq_warehouse to ComponentSource.

cq_warehouse provides parametric fasteners, bearings, chains, etc.
"""

from collections.abc import Iterator
from typing import Any

import cadquery as cq

from semicad.core.component import Component, ComponentSpec
from semicad.core.registry import ComponentSource

# Map cq_warehouse classes to our categories
FASTENER_CLASSES = {
    "SocketHeadCapScrew": ("iso4762", "Socket head cap screw (ISO 4762)"),
    "ButtonHeadScrew": ("iso7380_1", "Button head screw (ISO 7380-1)"),
    "CounterSunkScrew": ("iso10642", "Countersunk screw (ISO 10642)"),
    "HexHeadScrew": ("iso4014", "Hex head screw (ISO 4014)"),
    "HexNut": ("iso4032", "Hex nut (ISO 4032)"),
    "HexNutWithFlange": ("iso4161", "Hex nut with flange"),
    "SetScrew": ("iso4026", "Set screw (ISO 4026)"),
}


class WarehouseFastener(Component):
    """Component backed by cq_warehouse fastener."""

    def __init__(
        self,
        spec: ComponentSpec,
        fastener_class: type[Any],
        fastener_type: str,
        size: str,
        length: float | None = None,
    ) -> None:
        super().__init__(spec)
        self._fastener_class = fastener_class
        self._fastener_type = fastener_type
        self._size = size
        self._length = length

    def build(self) -> cq.Workplane:
        if self._length:
            fastener = self._fastener_class(
                size=self._size,
                length=self._length,
                fastener_type=self._fastener_type,
            )
        else:
            fastener = self._fastener_class(
                size=self._size,
                fastener_type=self._fastener_type,
            )
        return fastener.cq_object  # type: ignore[no-any-return]


class WarehouseBearing(Component):
    """Component backed by cq_warehouse bearing."""

    def __init__(
        self,
        spec: ComponentSpec,
        bearing_class: type[Any],
        size: str,
    ) -> None:
        super().__init__(spec)
        self._bearing_class = bearing_class
        self._size = size

    def build(self) -> cq.Workplane:
        bearing = self._bearing_class(size=self._size)
        return bearing.cq_object  # type: ignore[no-any-return]


class WarehouseSource(ComponentSource):
    """
    Source for cq_warehouse components.

    Provides access to:
    - Fasteners (screws, nuts, bolts)
    - Bearings
    - Chains and sprockets
    """

    def __init__(self) -> None:
        self._fasteners: dict[str, tuple[type[Any], str, str]] = {}
        self._bearings: dict[str, type[Any]] = {}
        self._load_fasteners()
        self._load_bearings()

    @property
    def name(self) -> str:
        return "cq_warehouse"

    def _load_fasteners(self) -> None:
        """Load fastener classes from cq_warehouse."""
        try:
            from cq_warehouse import fastener as f
            for class_name, (default_type, desc) in FASTENER_CLASSES.items():
                if hasattr(f, class_name):
                    cls = getattr(f, class_name)
                    self._fasteners[class_name] = (cls, default_type, desc)
        except ImportError:
            pass

    def _load_bearings(self) -> None:
        """Load bearing classes from cq_warehouse."""
        try:
            from cq_warehouse.bearing import SingleRowDeepGrooveBallBearing
            self._bearings["SingleRowDeepGrooveBallBearing"] = SingleRowDeepGrooveBallBearing
        except ImportError:
            pass

    def list_components(self) -> Iterator[ComponentSpec]:
        """List available component types (not individual sizes)."""
        for class_name, (_cls, default_type, desc) in self._fasteners.items():
            yield ComponentSpec(
                name=class_name,
                source=self.name,
                category="fastener",
                description=desc,
                params={"fastener_type": default_type},
            )

        for class_name, _cls in self._bearings.items():
            yield ComponentSpec(
                name=class_name,
                source=self.name,
                category="bearing",
                description="Deep groove ball bearing",
            )

    def list_fastener_sizes(self, fastener_type: str = "SocketHeadCapScrew", iso_type: str = "iso4762") -> list[str]:
        """List available sizes for a fastener type."""
        if fastener_type in self._fasteners:
            cls, _, _ = self._fasteners[fastener_type]
            sizes: list[str] = cls.sizes(iso_type)
            return sizes
        return []

    def list_bearing_sizes(self) -> list[str]:
        """List available bearing sizes."""
        if "SingleRowDeepGrooveBallBearing" in self._bearings:
            sizes: list[str] = self._bearings["SingleRowDeepGrooveBallBearing"].sizes()
            return sizes
        return []

    def get_component(self, name: str, **params: Any) -> Component:
        """
        Get a fastener or bearing component.

        Examples:
            get_component("SocketHeadCapScrew", size="M3-0.5", length=10)
            get_component("SingleRowDeepGrooveBallBearing", size="M8-22-7")
        """
        # Check if it's a fastener
        if name in self._fasteners:
            cls, default_type, desc = self._fasteners[name]
            size = params.get("size", "M3-0.5")
            length = params.get("length")
            fastener_type = params.get("fastener_type", default_type)

            spec = ComponentSpec(
                name=f"{name}_{size}_{length}mm" if length else f"{name}_{size}",
                source=self.name,
                category="fastener",
                description=desc,
                params={"size": size, "length": length, "fastener_type": fastener_type},
            )
            return WarehouseFastener(spec, cls, fastener_type, size, length)

        # Check if it's a bearing
        if name in self._bearings:
            cls = self._bearings[name]
            size = params.get("size", "M8-22-7")

            spec = ComponentSpec(
                name=f"{name}_{size}",
                source=self.name,
                category="bearing",
                description="Deep groove ball bearing",
                params={"size": size},
            )
            return WarehouseBearing(spec, cls, size)

        raise KeyError(f"Component not found in cq_warehouse: {name}")

    def get_screw(self, size: str, length: float, screw_type: str = "SocketHeadCapScrew") -> Component:
        """Convenience method to get a screw."""
        return self.get_component(screw_type, size=size, length=length)

    def get_nut(self, size: str, nut_type: str = "HexNut") -> Component:
        """Convenience method to get a nut."""
        return self.get_component(nut_type, size=size)

    def get_bearing(self, size: str) -> Component:
        """Convenience method to get a bearing."""
        return self.get_component("SingleRowDeepGrooveBallBearing", size=size)
