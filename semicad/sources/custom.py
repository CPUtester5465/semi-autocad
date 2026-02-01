"""
Custom component source - Adapts scripts/components.py to ComponentSource.
"""

from collections.abc import Iterator

import cadquery as cq

from semicad.core.component import Component, ComponentSpec
from semicad.core.registry import ComponentSource


class CustomComponent(Component):
    """Component backed by our custom generator functions."""

    def __init__(self, spec: ComponentSpec, generator: callable, params: dict):
        super().__init__(spec)
        self._generator = generator
        self._params = params

    def build(self) -> cq.Workplane:
        return self._generator(**self._params)


class CustomSource(ComponentSource):
    """
    Source for components defined in scripts/components.py.

    Adapts the existing COMPONENTS dict to our interface.
    """

    def __init__(self):
        # Import the existing components module
        try:
            from scripts.components import COMPONENTS, MOUNT_PATTERNS
            self._components = COMPONENTS
            self._mount_patterns = MOUNT_PATTERNS
        except ImportError:
            self._components = {}
            self._mount_patterns = {}

    @property
    def name(self) -> str:
        return "custom"

    def _categorize(self, name: str) -> str:
        """Determine category from component name."""
        prefixes = {
            "fc_": "flight_controller",
            "esc_": "esc",
            "motor_": "motor",
            "battery_": "battery",
            "prop_": "propeller",
        }
        for prefix, category in prefixes.items():
            if name.startswith(prefix):
                return category
        return "other"

    def list_components(self) -> Iterator[ComponentSpec]:
        """List all custom components."""
        for name, data in self._components.items():
            yield ComponentSpec(
                name=name,
                source=self.name,
                category=self._categorize(name),
                params=data.get("args", {}),
                description=f"Custom {self._categorize(name)} component",
            )

    def get_component(self, name: str, **override_params) -> Component:
        """Get a component by name."""
        if name not in self._components:
            raise KeyError(f"Component not found: {name}")

        data = self._components[name]
        params = {**data.get("args", {}), **override_params}
        spec = ComponentSpec(
            name=name,
            source=self.name,
            category=self._categorize(name),
            params=params,
        )

        return CustomComponent(spec, data["func"], params)

    def list_categories(self) -> list[str]:
        """List available categories."""
        categories = set()
        for name in self._components:
            categories.add(self._categorize(name))
        return sorted(categories)

    def list_by_category(self, category: str) -> Iterator[ComponentSpec]:
        """List components in a specific category."""
        for spec in self.list_components():
            if spec.category == category:
                yield spec
