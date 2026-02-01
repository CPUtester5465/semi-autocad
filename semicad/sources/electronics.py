"""
cq_electronics source - Adapts cq_electronics to ComponentSource.

This module provides access to electronic components from the cq_electronics
library through the semicad registry system.

Available component categories:
    - board: Single-board computers (RPi3b)
    - connector: Pin headers, RJ45 jacks (PinHeader, JackSurfaceMount)
    - smd: Surface-mount packages (BGA)
    - mechanical: DIN rail components (TopHat, DinClip)
    - mounting: Enclosure mounting clips (PiTrayClip)

Also exposes utility constants:
    - HOLE_SIZES: Standard hole diameters for mounting electronics
    - COLORS: RGB color values for rendering electronic components

Usage:
    from semicad import get_registry

    registry = get_registry()
    rpi = registry.get("RPi3b")
    header = registry.get("PinHeader", rows=2, columns=20)

See Also:
    - docs/electronics.md for full documentation
    - COMPONENT_CATALOG for available components and parameters
"""

import warnings
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import cadquery as cq

from semicad.core.component import Component, ComponentSpec
from semicad.core.registry import ComponentSource

# Version compatibility (P2.12)
MIN_CQ_ELECTRONICS_VERSION = "0.2.0"
_cq_electronics_version: str | None = None


def _check_version() -> str | None:
    """Check cq_electronics version and warn if incompatible.

    Returns the installed version or None if not installed.
    """
    global _cq_electronics_version
    if _cq_electronics_version is not None:
        return _cq_electronics_version

    try:
        import cq_electronics
        version = getattr(cq_electronics, "__version__", None)
        if version is None:
            # Try importlib.metadata for packages without __version__
            try:
                from importlib.metadata import version as get_version
                version = get_version("cq-electronics")
            except Exception:
                version = "unknown"

        _cq_electronics_version = version

        if version != "unknown":
            from packaging.version import parse
            if parse(version) < parse(MIN_CQ_ELECTRONICS_VERSION):
                warnings.warn(
                    f"cq_electronics {version} may not be compatible. "
                    f"Minimum recommended: {MIN_CQ_ELECTRONICS_VERSION}",
                    UserWarning,
                    stacklevel=3
                )
        return version
    except ImportError:
        return None


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


# Parameter schema definitions for validation
# Format: {"param_name": {"type": type, "min": value, "max": value, "required": bool}}
PARAM_SCHEMAS = {
    "RPi3b": {
        # P2.9: RPi3b supports simple parameter (defaults to True in component)
        "simple": {"type": bool},
    },
    "PinHeader": {
        "rows": {"type": int, "min": 1, "max": 100},
        "columns": {"type": int, "min": 1, "max": 100},
        "above": {"type": (int, float), "min": 0},
        "below": {"type": (int, float), "min": 0},
        "simple": {"type": bool},
    },
    "JackSurfaceMount": {
        "length": {"type": (int, float), "min": 0.1},
        "simple": {"type": bool},
    },
    "BGA": {
        "length": {"type": (int, float), "min": 0.1, "required": True},
        "width": {"type": (int, float), "min": 0.1, "required": True},
        "height": {"type": (int, float), "min": 0.1},
        "simple": {"type": bool},
    },
    "DinClip": {
        # No parameters - fixed design
    },
    "TopHat": {
        "length": {"type": (int, float), "min": 0.1, "required": True},
        "depth": {"type": (int, float), "min": 0.1},
        "slots": {"type": bool},
        # Note: TopHat does NOT support 'simple' parameter
    },
    "PiTrayClip": {
        # No parameters - fixed design
    },
}


class ParameterValidationError(ValueError):
    """Raised when parameter validation fails."""
    pass


def validate_params(component_name: str, params: dict, strict: bool = True) -> dict:
    """
    Validate parameters for a component and return filtered params.

    Args:
        component_name: Name of the component being validated
        params: Parameters provided by the user
        strict: If True, raise error on unknown params; if False, filter them out

    Returns:
        Validated and filtered parameters dict

    Raises:
        ParameterValidationError: When validation fails with clear error message
    """
    schema = PARAM_SCHEMAS.get(component_name, {})
    validated_params = {}
    errors = []

    # Check for unknown parameters
    known_params = set(schema.keys())
    provided_params = set(params.keys())
    unknown_params = provided_params - known_params

    if unknown_params and strict:
        errors.append(
            f"Unknown parameter(s) for {component_name}: {sorted(unknown_params)}. "
            f"Valid parameters: {sorted(known_params) if known_params else 'none'}"
        )
        # In non-strict mode, unknown params are simply filtered out

    # Validate each provided parameter
    for param_name, value in params.items():
        if param_name in unknown_params:
            continue  # Skip unknown params

        param_schema = schema.get(param_name, {})
        expected_type = param_schema.get("type")
        min_val = param_schema.get("min")
        max_val = param_schema.get("max")

        # Type checking
        if expected_type is not None:
            # Handle tuple of types (e.g., (int, float))
            if isinstance(expected_type, tuple):
                if not isinstance(value, expected_type):
                    type_names = " or ".join(t.__name__ for t in expected_type)
                    errors.append(
                        f"Parameter '{param_name}' must be {type_names}, "
                        f"got {type(value).__name__} ({value!r})"
                    )
                    continue
            elif not isinstance(value, expected_type):
                errors.append(
                    f"Parameter '{param_name}' must be {expected_type.__name__}, "
                    f"got {type(value).__name__} ({value!r})"
                )
                continue

        # Range checking for numeric types
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if min_val is not None and value < min_val:
                errors.append(
                    f"Parameter '{param_name}' must be >= {min_val}, got {value}"
                )
                continue
            if max_val is not None and value > max_val:
                errors.append(
                    f"Parameter '{param_name}' must be <= {max_val}, got {value}"
                )
                continue

        validated_params[param_name] = value

    if errors:
        raise ParameterValidationError(
            f"Invalid parameters for {component_name}:\n  - " + "\n  - ".join(errors)
        )

    return validated_params


# Hole sizes from cq_electronics.fasteners module
# These are standard metric hole diameters for mounting electronics
HOLE_SIZES: dict[str, float] = {}
try:
    from cq_electronics import fasteners as _fasteners
    HOLE_SIZES = {
        "M2R5_TAP_HOLE": _fasteners.M2R5_TAP_HOLE_DIAMETER,
        "M4_TAP_HOLE": _fasteners.M4_TAP_HOLE_DIAMETER,
        "M4_CLEARANCE_NORMAL": _fasteners.M4_CLEARANCE_NORMAL_DIAMETER,
        "M4_COUNTERSINK": _fasteners.M4_COUNTERSINK_DIAMETER,
        "M_COUNTERSINK_ANGLE": _fasteners.M_COUNTERSINK_ANGLE,
    }
except ImportError:
    pass  # cq_electronics.fasteners not available

# Colors from cq_electronics.materials module
# RGB values for rendering electronic components
COLORS: dict[str, list[float]] = {}
try:
    from cq_electronics import materials as _materials
    COLORS = dict(_materials.COLORS)
except ImportError:
    pass  # cq_electronics.materials not available


# Component catalog: maps short names to import info and metadata
#
# Format: (module_path, class_name, category, description, required_params, default_params)
#
# To add a new component:
#   "ComponentName": (
#       "cq_electronics.module.submodule",  # Full import path
#       "ClassName",                         # Class to import
#       "category",                          # One of: board, connector, smd, mechanical
#       "Component description",             # Human-readable description
#       ["required_param"],                  # List of required parameter names
#       {"param": default_value},            # Dict of optional params with defaults
#   ),
#
COMPONENT_CATALOG = {
    # Raspberry Pi boards
    "RPi3b": (
        "cq_electronics.rpi.rpi3b",
        "RPi3b",
        "board",
        "Raspberry Pi 3B single-board computer",
        [],
        {"simple": True},  # P2.9: Explicitly set default
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
        {},  # No parameters
    ),
    "TopHat": (
        "cq_electronics.mechanical.din_rail",
        "TopHat",
        "mechanical",
        "Top-hat (TH35) DIN rail section",
        ["length"],
        {"depth": 7.5, "slots": True},  # Note: no 'simple' - not supported
    ),
    # Mounting
    "PiTrayClip": (
        "cq_electronics.sourcekit.pitray_clip",
        "PiTrayClip",
        "mounting",
        "Raspberry Pi mounting tray clip for enclosures (76x20x15mm)",
        [],
        {},  # No parameters
    ),
}


class ElectronicsComponent(Component):
    """
    Component backed by cq_electronics library.

    Wraps cq_electronics objects and normalizes their geometry output to
    cq.Workplane for consistent handling across the semicad system.

    Preserves assembly structure when available. Access the original
    assembly via the `assembly` property, or get assembly metadata
    via `assembly_info`.

    Attributes:
        spec: ComponentSpec with name, source, category, and parameters.
        geometry: CadQuery Workplane (lazy-built on first access).
        assembly: Original cq.Assembly if component is assembly-based.
        metadata: Dict of UPPER_CASE constants from the component class.
        mounting_holes: List of (x, y) mounting hole locations.
        dimensions: Tuple of (width, height, depth) if available.
    """

    def __init__(self, spec: ComponentSpec, component_class: type, params: dict):
        """
        Initialize an electronics component.

        Args:
            spec: Component specification with metadata.
            component_class: The cq_electronics class to instantiate.
            params: Parameters to pass to the component constructor.
        """
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
        """
        Build the component geometry.

        Instantiates the cq_electronics component and converts the result
        to a CadQuery Workplane. Handles both Assembly and Workplane outputs.
        Preserves the original Assembly for later access via `.assembly`.

        Returns:
            CadQuery Workplane containing the component geometry.
        """
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
    Source adapter for cq_electronics components.

    Implements the ComponentSource interface to provide access to electronic
    components through the semicad registry.

    Available categories:
        - board: Single-board computers (RPi3b)
        - connector: Pin headers, RJ45 jacks (PinHeader, JackSurfaceMount)
        - smd: Surface-mount packages (BGA)
        - mechanical: DIN rail parts (DinClip, TopHat)
        - mounting: Enclosure clips (PiTrayClip)

    Components are loaded dynamically from cq_electronics at initialization.
    If cq_electronics is not installed, this source provides no components.

    Version compatibility:
        - Minimum cq_electronics version: 0.2.0
        - Tested with cadquery 2.5.x

    Example:
        source = ElectronicsSource()
        rpi = source.get_component("RPi3b")
        header = source.get_component("PinHeader", rows=2, columns=20)
    """

    def __init__(self):
        """Initialize the electronics source, loading available components."""
        self._available_components: dict[str, tuple] = {}
        self._version = _check_version()
        self._load_components()

    @property
    def name(self) -> str:
        """Source identifier used in component specs."""
        return "cq_electronics"

    def _load_components(self) -> None:
        """
        Load available components from cq_electronics.

        Iterates through COMPONENT_CATALOG and attempts to import each
        component. Components that fail to import are silently skipped,
        allowing graceful degradation if cq_electronics is partial or missing.
        """
        for name, catalog_entry in COMPONENT_CATALOG.items():
            module_path, class_name, category, desc, required, defaults = catalog_entry
            try:
                # Try to import the module and class
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                self._available_components[name] = (cls, category, desc, required, defaults)
            except (ImportError, AttributeError):
                # Component not available, skip it
                pass

    def list_components(self) -> Iterator[ComponentSpec]:
        """
        List all available electronic components.

        Yields:
            ComponentSpec for each available component with metadata
            including required and default parameters.
        """
        for name, (cls, category, desc, required, defaults) in self._available_components.items():
            params_info = {}
            if required:
                params_info["required"] = required
            if defaults:
                params_info["defaults"] = defaults
            # Include parameter schema for documentation
            if PARAM_SCHEMAS.get(name):
                params_info["schema"] = PARAM_SCHEMAS[name]

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

    def get_component(self, name: str, strict: bool = True, **params) -> ElectronicsComponent:
        """
        Get an electronics component by name.

        The returned ElectronicsComponent preserves the original assembly
        structure, allowing access to:
        - Original cq.Assembly via `.assembly` property
        - Part names via `.list_parts()`
        - Part colors via `.get_color_map()`
        - Individual sub-parts via `.get_part(name)`

        Args:
            name: Component name (e.g., "RPi3b", "PinHeader", "BGA").
            strict: If True (default), raise error on unknown params.
                    If False, unknown params are silently filtered out.
            **params: Component parameters. Required params must be provided;
                optional params use defaults from COMPONENT_CATALOG.

        Returns:
            ElectronicsComponent with the requested configuration.

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

        Raises:
            KeyError: If component not found
            ValueError: If missing required parameters
            ParameterValidationError: If parameter validation fails
        """
        if name not in self._available_components:
            version_info = f" (installed: {self._version})" if self._version else " (not installed)"
            raise KeyError(
                f"Component not found in cq_electronics: {name}{version_info}. "
                f"Minimum version: {MIN_CQ_ELECTRONICS_VERSION}"
            )

        cls, category, desc, required, defaults = self._available_components[name]

        # Check required parameters first (before validation)
        missing = [p for p in required if p not in params]
        if missing:
            schema = PARAM_SCHEMAS.get(name, {})
            schema_info = []
            for p in required:
                p_schema = schema.get(p, {})
                p_type = p_schema.get("type")
                if p_type:
                    if isinstance(p_type, tuple):
                        type_name = " or ".join(t.__name__ for t in p_type)
                    else:
                        type_name = p_type.__name__
                    schema_info.append(f"{p}: {type_name}")
                else:
                    schema_info.append(p)
            raise ValueError(
                f"Missing required parameters for {name}: {missing}. "
                f"Required: [{', '.join(schema_info)}]"
            )

        # Validate user-provided parameters (P2.6 + P2.9: validates and rejects unknown params)
        validated_params = validate_params(name, params, strict=strict)

        # Merge defaults with validated params (validated params override defaults)
        final_params = {**defaults, **validated_params}

        # Build spec with validated params only (not defaults, for cleaner naming)
        param_str = "_".join(f"{k}={v}" for k, v in sorted(validated_params.items()) if v is not None)
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
        """
        List available component categories.

        Returns:
            Sorted list of category names (e.g., ["board", "connector", "mechanical", "smd"]).
        """
        categories = set()
        for _, (_, category, _, _, _) in self._available_components.items():
            categories.add(category)
        return sorted(categories)

    def list_by_category(self, category: str) -> Iterator[ComponentSpec]:
        """
        List components in a specific category.

        Args:
            category: Category name (board, connector, smd, mechanical).

        Yields:
            ComponentSpec for each component in the specified category.
        """
        for spec in self.list_components():
            if spec.category == category:
                yield spec

    def get_param_schema(self, name: str) -> dict:
        """
        Get the parameter schema for a component.

        Returns a dict mapping parameter names to their constraints:
        - type: Expected type(s)
        - min: Minimum value (for numeric types)
        - max: Maximum value (for numeric types)
        - required: Whether the parameter is required

        Args:
            name: Component name

        Returns:
            Parameter schema dict, or empty dict if no schema defined
        """
        return PARAM_SCHEMAS.get(name, {})

    def get_board_info(self, name: str) -> dict[str, Any]:
        """
        Get detailed info about a board component.

        Returns dict with dimensions, mounting holes, etc.
        """
        if name not in self._available_components:
            raise KeyError(f"Board not found: {name}")

        cls, category, desc, _required, _defaults = self._available_components[name]
        if category != "board":
            raise ValueError(f"{name} is not a board (category: {category})")

        info = {
            "name": name,
            "description": desc,
            "category": category,
        }

        # Extract dimension constants from class
        for attr in ["WIDTH", "HEIGHT", "THICKNESS"]:
            if hasattr(cls, attr):
                info[attr.lower()] = getattr(cls, attr)

        # Extract hole info
        for attr in ["HOLE_DIAMETER", "HOLE_CENTERS_LONG", "HOLE_OFFSET_FROM_EDGE"]:
            if hasattr(cls, attr):
                info[attr.lower()] = getattr(cls, attr)

        return info

    def list_boards(self) -> list[dict[str, Any]]:
        """List all board components with their dimensions."""
        boards = []
        for spec in self.list_by_category("board"):
            try:
                info = self.get_board_info(spec.name)
                boards.append(info)
            except (KeyError, ValueError):
                pass
        return boards

    def get_connector_info(self, name: str) -> dict[str, Any]:
        """
        Get detailed info about a connector component.

        Returns dict with parameters, pitch, etc.
        """
        if name not in self._available_components:
            raise KeyError(f"Connector not found: {name}")

        cls, category, desc, required, defaults = self._available_components[name]
        if category != "connector":
            raise ValueError(f"{name} is not a connector (category: {category})")

        info = {
            "name": name,
            "description": desc,
            "category": category,
            "required_params": required,
            "default_params": defaults,
        }

        # Extract relevant constants from class
        for attr in ["PITCH", "PIN_WIDTH", "BASE_HEIGHT", "LENGTH_MAGNETIC", "LENGTH_NON_MAGNETIC"]:
            if hasattr(cls, attr):
                info[attr.lower()] = getattr(cls, attr)

        return info

    def list_connectors(self) -> list[dict[str, Any]]:
        """List all connector components with their specs."""
        connectors = []
        for spec in self.list_by_category("connector"):
            try:
                info = self.get_connector_info(spec.name)
                connectors.append(info)
            except (KeyError, ValueError):
                pass
        return connectors

    # --- P2.11: Utility constants ---

    @property
    def hole_sizes(self) -> dict[str, float]:
        """
        Standard hole diameters for mounting electronics.

        Returns dict with keys like:
        - M2R5_TAP_HOLE: 2.15mm (M2.5 tap drill)
        - M4_TAP_HOLE: 3.2mm (M4 tap drill)
        - M4_CLEARANCE_NORMAL: 4.5mm (M4 clearance hole)
        - M4_COUNTERSINK: 9.4mm (M4 countersink diameter)
        - M_COUNTERSINK_ANGLE: 90 degrees
        """
        return HOLE_SIZES

    @property
    def colors(self) -> dict[str, list[float]]:
        """
        RGB color values for rendering electronic components.

        Returns dict with keys like:
        - black_plastic: dark plastic components
        - gold_plate: gold-plated contacts
        - pcb_substrate_chiffon: PCB substrate color
        - solder_mask_green: green PCB solder mask
        - stainless_steel: stainless steel parts
        - tin_plate: tin-plated surfaces
        """
        return COLORS
