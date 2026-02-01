"""
cq_electronics source - Adapts cq_electronics to ComponentSource.

cq_electronics provides electronic components like:
- Raspberry Pi boards
- Connectors (headers, RJ45)
- SMD components (BGA)
- Mechanical (DIN rail, clips)
"""

from dataclasses import dataclass, field
from typing import Iterator, Any
import cadquery as cq

from semicad.core.component import Component, ComponentSpec
from semicad.core.registry import ComponentSource


def _extract_class_constants(obj: Any) -> dict[str, Any]:
    """Extract UPPER_CASE class constants from an object."""
    metadata = {}
    for name in dir(obj):
        if name.isupper() and not name.startswith("_"):
            try:
                value = getattr(obj, name)
                # Only include simple types (numbers, strings, bools)
                if isinstance(value, (int, float, str, bool)):
                    metadata[name] = value
            except Exception:
                pass
    return metadata


@dataclass
class PartInfo:
    """Information about a single part within an assembly."""

    name: str
    color: tuple[float, float, float, float] | None = None  # RGBA 0-1

    @property
    def color_hex(self) -> str | None:
        """Return color as hex string (e.g., '#FF0000')."""
        if self.color is None:
            return None
        r, g, b, _ = self.color
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


@dataclass
class AssemblyInfo:
    """
    Metadata about an assembly structure.

    Preserves part names, colors, and hierarchy that would otherwise
    be lost when converting Assembly to Workplane.
    """

    parts: list[PartInfo] = field(default_factory=list)

    @classmethod
    def from_assembly(cls, asm: cq.Assembly) -> "AssemblyInfo":
        """Extract metadata from a CadQuery Assembly."""
        parts = []
        for name, _ in asm.traverse():
            # Find the child with this name to get its color
            color_tuple = None
            for child in asm.children:
                if child.name == name:
                    if child.color is not None:
                        color_tuple = child.color.toTuple()
                    break
            parts.append(PartInfo(name=name, color=color_tuple))
        return cls(parts=parts)

    @property
    def part_names(self) -> list[str]:
        """List all part names in the assembly."""
        return [p.name for p in self.parts]

    def get_color(self, part_name: str) -> tuple[float, float, float, float] | None:
        """Get the color for a specific part."""
        for p in self.parts:
            if p.name == part_name:
                return p.color
        return None

    def get_color_map(self) -> dict[str, tuple[float, float, float, float]]:
        """Return a mapping of part names to their colors."""
        return {p.name: p.color for p in self.parts if p.color is not None}


# Component catalog: maps short names to import info and metadata
# Format: (module_path, class_name, category, description, required_params, default_params)
COMPONENT_CATALOG = {
    # Raspberry Pi boards
    "RPi3b": (
        "cq_electronics.rpi.rpi3b",
        "RPi3b",
        "board",
        "Raspberry Pi 3B single-board computer",
        [],
        {},
    ),
    # Connectors
    "PinHeader": (
        "cq_electronics.connectors.headers",
        "PinHeader",
        "connector",
        "Through-hole pin header",
        [],
        {"rows": 1, "columns": 1, "above": 7, "below": 3, "simple": True},
    ),
    "JackSurfaceMount": (
        "cq_electronics.connectors.rj45",
        "JackSurfaceMount",
        "connector",
        "RJ45 Ethernet jack (surface mount)",
        [],
        {"length": 21, "simple": True},
    ),
    # SMD components
    "BGA": (
        "cq_electronics.smd.bga",
        "BGA",
        "smd",
        "Ball Grid Array chip package",
        ["length", "width"],
        {"height": 1, "simple": True},
    ),
    # Mechanical
    "DinClip": (
        "cq_electronics.mechanical.din_clip",
        "DinClip",
        "mechanical",
        "DIN rail mounting clip",
        [],
        {},
    ),
    "TopHat": (
        "cq_electronics.mechanical.din_rail",
        "TopHat",
        "mechanical",
        "Top-hat (TH35) DIN rail section",
        ["length"],
        {"depth": 7.5, "slots": True},
    ),
    # Mounting
    "PiTrayClip": (
        "cq_electronics.sourcekit.pitray_clip",
        "PiTrayClip",
        "mounting",
        "Raspberry Pi mounting tray clip for enclosures (76x20x15mm)",
        [],
        {},
    ),
}


class ElectronicsComponent(Component):
    """
    Component backed by cq_electronics library.

    Preserves assembly structure when available. Access the original
    assembly via the `assembly` property, or get assembly metadata
    via `assembly_info`.
    """

    def __init__(self, spec: ComponentSpec, component_class: type, params: dict):
        super().__init__(spec)
        self._component_class = component_class
        self._params = params
        self._instance: Any = None
        self._assembly: cq.Assembly | None = None
        self._assembly_info: AssemblyInfo | None = None

    def _ensure_instance(self) -> Any:
        """Ensure the cq_electronics instance exists, creating if needed."""
        if self._instance is None:
            self._instance = self._component_class(**self._params)
        return self._instance

    def build(self) -> cq.Workplane:
        """Build the component geometry."""
        instance = self._ensure_instance()

        # Get the geometry - cq_object is either Assembly or Workplane
        cq_obj = instance.cq_object

        # Convert Assembly to Workplane if needed
        if isinstance(cq_obj, cq.Assembly):
            # Preserve the original assembly and extract metadata
            self._assembly = cq_obj
            self._assembly_info = AssemblyInfo.from_assembly(cq_obj)
            compound = cq_obj.toCompound()
            return cq.Workplane("XY").add(compound)
        elif isinstance(cq_obj, cq.Workplane):
            return cq_obj
        else:
            # Fallback: wrap in Workplane
            return cq.Workplane("XY").add(cq_obj)

    # --- P2.3: Component metadata properties ---

    @property
    def raw_instance(self) -> Any:
        """
        Access the underlying cq_electronics instance.

        This provides direct access to all instance attributes and methods.

        Example:
            rpi = registry.get("RPi3b")
            rpi.raw_instance.hole_points  # [(24.5, 19.0), ...]
            rpi.raw_instance.simple       # True
        """
        return self._ensure_instance()

    @property
    def metadata(self) -> dict[str, Any]:
        """
        Extract component metadata (class constants).

        Returns a dict of UPPER_CASE constants from the component class,
        including dimensions, hole diameters, and other design parameters.

        Example:
            rpi = registry.get("RPi3b")
            rpi.metadata
            # {'WIDTH': 85, 'HEIGHT': 56, 'THICKNESS': 1.5, 'HOLE_DIAMETER': 2.7, ...}
        """
        instance = self._ensure_instance()
        return _extract_class_constants(instance)

    @property
    def mounting_holes(self) -> list[tuple[float, float]] | None:
        """
        Get mounting hole locations if available.

        Returns a list of (x, y) tuples for each mounting hole,
        or None if the component doesn't have mounting holes.

        Example:
            rpi = registry.get("RPi3b")
            rpi.mounting_holes
            # [(24.5, 19.0), (-24.5, -39.0), (-24.5, 19.0), (24.5, -39.0)]
        """
        instance = self._ensure_instance()
        # Check for common attribute names
        if hasattr(instance, "hole_points"):
            return instance.hole_points
        if hasattr(instance, "mounting_holes"):
            return instance.mounting_holes
        return None

    @property
    def dimensions(self) -> tuple[float, float, float] | None:
        """
        Get component dimensions as (width, height, depth/thickness).

        Returns dimensions extracted from component metadata,
        or None if dimensions cannot be determined.

        Example:
            rpi = registry.get("RPi3b")
            rpi.dimensions
            # (85.0, 56.0, 1.5)
        """
        meta = self.metadata
        width = meta.get("WIDTH")
        height = meta.get("HEIGHT")
        # Try various names for depth/thickness
        depth = meta.get("THICKNESS") or meta.get("DEPTH") or meta.get("LENGTH")

        if width is not None and height is not None:
            return (float(width), float(height), float(depth) if depth else 0.0)
        return None

    # --- P2.4: Assembly preservation properties ---

    @property
    def assembly(self) -> cq.Assembly | None:
        """
        Return the original cq.Assembly if the component was built from one.

        This preserves part names, colors, and hierarchy that are lost
        when converting to Workplane.

        Returns None if the component is not assembly-based.
        """
        # Ensure build() has been called to populate _assembly
        if self._geometry is None:
            _ = self.geometry
        return self._assembly

    @property
    def assembly_info(self) -> AssemblyInfo | None:
        """
        Return metadata about the assembly structure.

        Provides access to part names and colors without needing
        to work with the full Assembly object.
        """
        # Ensure build() has been called to populate _assembly_info
        if self._geometry is None:
            _ = self.geometry
        return self._assembly_info

    @property
    def has_assembly(self) -> bool:
        """Check if this component has an underlying assembly."""
        return self.assembly is not None

    def get_part(self, name: str) -> cq.Workplane | None:
        """
        Get a specific sub-part from the assembly by name.

        Args:
            name: The part name (e.g., 'rpi__ethernet_port')

        Returns:
            Workplane containing the part geometry, or None if not found.
        """
        if self.assembly is None:
            return None

        for child in self.assembly.children:
            if child.name == name:
                # child.obj is the actual shape
                if isinstance(child.obj, cq.Workplane):
                    return child.obj
                else:
                    return cq.Workplane("XY").add(child.obj)
        return None

    def get_color_map(self) -> dict[str, tuple[float, float, float, float]]:
        """
        Get a mapping of part names to their RGBA colors.

        Returns:
            Dict mapping part name to (r, g, b, a) tuple with values 0-1.
        """
        if self.assembly_info is None:
            return {}
        return self.assembly_info.get_color_map()

    def list_parts(self) -> list[str]:
        """List all part names in the assembly."""
        if self.assembly_info is None:
            return []
        return self.assembly_info.part_names


class ElectronicsSource(ComponentSource):
    """
    Source for cq_electronics components.

    Provides access to:
    - Raspberry Pi boards (RPi3b)
    - Connectors (PinHeader, JackSurfaceMount)
    - SMD components (BGA)
    - Mechanical parts (DinClip, TopHat/DIN rail)
    """

    def __init__(self):
        self._available_components: dict[str, tuple] = {}
        self._load_components()

    @property
    def name(self) -> str:
        return "cq_electronics"

    def _load_components(self) -> None:
        """Load available components from cq_electronics."""
        for name, (module_path, class_name, category, desc, required, defaults) in COMPONENT_CATALOG.items():
            try:
                # Try to import the module and class
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                self._available_components[name] = (cls, category, desc, required, defaults)
            except (ImportError, AttributeError):
                # Component not available, skip it
                pass

    def list_components(self) -> Iterator[ComponentSpec]:
        """List all available electronic components."""
        for name, (cls, category, desc, required, defaults) in self._available_components.items():
            params_info = {}
            if required:
                params_info["required"] = required
            if defaults:
                params_info["defaults"] = defaults

            # Extract class-level metadata (constants)
            class_metadata = _extract_class_constants(cls)

            yield ComponentSpec(
                name=name,
                source=self.name,
                category=category,
                description=desc,
                params=params_info,
                metadata=class_metadata,
            )

    def get_component(self, name: str, **params) -> ElectronicsComponent:
        """
        Get an electronics component by name.

        The returned ElectronicsComponent preserves the original assembly
        structure, allowing access to:
        - Original cq.Assembly via `.assembly` property
        - Part names via `.list_parts()`
        - Part colors via `.get_color_map()`
        - Individual sub-parts via `.get_part(name)`

        Examples:
            # Basic usage
            rpi = get_component("RPi3b")
            geometry = rpi.geometry  # Workplane (for positioning)

            # Access assembly structure
            if rpi.has_assembly:
                print(rpi.list_parts())  # ['rpi__pcb_substrate', ...]
                print(rpi.get_color_map())  # {'rpi__pcb_substrate': (0.85, ...)}
                ethernet = rpi.get_part("rpi__ethernet_port")

            # For colored STEP export, use .assembly directly
            rpi.assembly.save("rpi.step")
        """
        if name not in self._available_components:
            raise KeyError(f"Component not found in cq_electronics: {name}")

        cls, category, desc, required, defaults = self._available_components[name]

        # Check required parameters
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(
                f"Missing required parameters for {name}: {missing}. "
                f"Required: {required}"
            )

        # Merge defaults with provided params
        final_params = {**defaults, **params}

        # Build spec with final params
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
        instance_name = f"{name}_{param_str}" if param_str else name

        # Extract class-level metadata (constants)
        class_metadata = _extract_class_constants(cls)

        spec = ComponentSpec(
            name=instance_name,
            source=self.name,
            category=category,
            description=desc,
            params=final_params,
            metadata=class_metadata,
        )

        return ElectronicsComponent(spec, cls, final_params)

    def list_categories(self) -> list[str]:
        """List available component categories."""
        categories = set()
        for _, (_, category, _, _, _) in self._available_components.items():
            categories.add(category)
        return sorted(categories)

    def list_by_category(self, category: str) -> Iterator[ComponentSpec]:
        """List components in a specific category."""
        for spec in self.list_components():
            if spec.category == category:
                yield spec
