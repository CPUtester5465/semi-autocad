"""
Component Registry - Single Responsibility: Find and retrieve components.

Open/Closed: New sources can be added without modifying this class.
Dependency Inversion: Depends on ComponentSource abstraction, not concrete sources.
"""

from typing import Callable, Iterator
from .component import Component, ComponentSpec


class ComponentSource:
    """
    Abstract interface for component sources.

    Interface Segregation: Only requires what's needed for discovery and loading.
    """

    @property
    def name(self) -> str:
        """Source identifier (e.g., 'cq_warehouse', 'custom')."""
        raise NotImplementedError

    def list_components(self) -> Iterator[ComponentSpec]:
        """Yield all available component specs from this source."""
        raise NotImplementedError

    def get_component(self, name: str, **params) -> Component:
        """Load a component by name with optional parameters."""
        raise NotImplementedError

    def search(self, query: str) -> Iterator[ComponentSpec]:
        """Search components by name/description."""
        query_lower = query.lower()
        for spec in self.list_components():
            if query_lower in spec.name.lower() or query_lower in spec.description.lower():
                yield spec


class ComponentRegistry:
    """
    Central registry for all component sources.

    Single Responsibility: Aggregates multiple sources into unified interface.
    """

    def __init__(self):
        self._sources: dict[str, ComponentSource] = {}

    def register_source(self, source: ComponentSource) -> None:
        """Register a new component source."""
        self._sources[source.name] = source

    def unregister_source(self, name: str) -> None:
        """Remove a component source."""
        self._sources.pop(name, None)

    @property
    def sources(self) -> list[str]:
        """List registered source names."""
        return list(self._sources.keys())

    def list_all(self) -> Iterator[ComponentSpec]:
        """List components from all sources."""
        for source in self._sources.values():
            yield from source.list_components()

    def list_from(self, source_name: str) -> Iterator[ComponentSpec]:
        """List components from a specific source."""
        if source_name in self._sources:
            yield from self._sources[source_name].list_components()

    def search(self, query: str, source: str | None = None) -> Iterator[ComponentSpec]:
        """Search components across all or specific source."""
        if source and source in self._sources:
            yield from self._sources[source].search(query)
        else:
            for src in self._sources.values():
                yield from src.search(query)

    def get(self, full_name: str, **params) -> Component:
        """
        Get component by full name (source/category/name) or short name.

        Examples:
            registry.get("custom/motor/motor_2207")
            registry.get("motor_2207")  # searches all sources
        """
        parts = full_name.split("/")

        if len(parts) >= 3:
            # Full name: source/category/name
            source_name = parts[0]
            component_name = parts[-1]
            if source_name in self._sources:
                return self._sources[source_name].get_component(component_name, **params)

        # Short name: search all sources
        for source in self._sources.values():
            try:
                return source.get_component(full_name, **params)
            except (KeyError, ValueError):
                continue

        raise KeyError(f"Component not found: {full_name}")


# Global registry instance
_registry: ComponentRegistry | None = None


def get_registry() -> ComponentRegistry:
    """Get or create the global component registry."""
    global _registry
    if _registry is None:
        _registry = ComponentRegistry()
        _init_default_sources(_registry)
    return _registry


def _init_default_sources(registry: ComponentRegistry) -> None:
    """Initialize registry with default sources."""
    # Import here to avoid circular imports
    from semicad.sources import custom, warehouse

    try:
        registry.register_source(custom.CustomSource())
    except Exception:
        pass  # Custom source not available

    try:
        registry.register_source(warehouse.WarehouseSource())
    except Exception:
        pass  # cq_warehouse not installed
