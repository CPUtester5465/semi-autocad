"""
cq_electronics source - Adapts cq_electronics to ComponentSource.

cq_electronics provides electronic components like:
- Raspberry Pi boards
- Connectors (headers, RJ45)
- SMD components (BGA)
- Mechanical (DIN rail, clips)
"""

from typing import Iterator, Any
import cadquery as cq

from semicad.core.component import Component, ComponentSpec
from semicad.core.registry import ComponentSource


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
}


class ElectronicsComponent(Component):
    """Component backed by cq_electronics library."""

    def __init__(self, spec: ComponentSpec, component_class: type, params: dict):
        super().__init__(spec)
        self._component_class = component_class
        self._params = params

    def build(self) -> cq.Workplane:
        """Build the component geometry."""
        # Instantiate the cq_electronics component
        instance = self._component_class(**self._params)

        # Get the geometry - cq_object is either Assembly or Workplane
        cq_obj = instance.cq_object

        # Convert Assembly to Workplane if needed
        if isinstance(cq_obj, cq.Assembly):
            compound = cq_obj.toCompound()
            return cq.Workplane("XY").add(compound)
        elif isinstance(cq_obj, cq.Workplane):
            return cq_obj
        else:
            # Fallback: wrap in Workplane
            return cq.Workplane("XY").add(cq_obj)


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
            yield ComponentSpec(
                name=name,
                source=self.name,
                category=category,
                description=desc,
                params=params_info,
            )

    def get_component(self, name: str, **params) -> Component:
        """
        Get an electronics component by name.

        Examples:
            get_component("RPi3b")
            get_component("PinHeader", rows=2, columns=20)
            get_component("BGA", length=10, width=10)
            get_component("TopHat", length=100)
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

        spec = ComponentSpec(
            name=instance_name,
            source=self.name,
            category=category,
            description=desc,
            params=final_params,
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
