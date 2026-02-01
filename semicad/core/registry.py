"""
Component Registry - Single Responsibility: Find and retrieve components.

Open/Closed: New sources can be added without modifying this class.
Dependency Inversion: Depends on ComponentSource abstraction, not concrete sources.
"""

from collections import OrderedDict
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from .component import Component, ComponentSpec


def _make_cache_key(name: str, params: dict[str, Any]) -> str:
    """Generate a deterministic cache key from component name and parameters."""
    if not params:
        return name
    # Sort params for deterministic key generation
    sorted_items = sorted(params.items())
    params_str = ",".join(f"{k}={v!r}" for k, v in sorted_items)
    return f"{name}:{params_str}"


@dataclass
class CacheStats:
    """Statistics about component cache usage."""
    hits: int
    misses: int
    size: int
    max_size: int

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


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

    def get_component(self, name: str, **params: Any) -> Component:
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

    Features:
    - Component caching with LRU eviction for repeated `get()` calls
    - Cache is keyed by component name and parameters
    - Translated/rotated components are not cached (they wrap originals)
    """

    DEFAULT_CACHE_SIZE = 128

    def __init__(self, cache_size: int | None = None):
        self._sources: dict[str, ComponentSource] = {}
        self._cache: OrderedDict[str, Component] = OrderedDict()
        self._cache_max_size = cache_size if cache_size is not None else self.DEFAULT_CACHE_SIZE
        self._cache_hits = 0
        self._cache_misses = 0

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

    def get_spec(self, name: str) -> ComponentSpec:
        """
        Get component spec without instantiating (no params required).

        This is useful for getting metadata about parametric components
        that require parameters to instantiate.

        Args:
            name: Component name (short or full)

        Returns:
            ComponentSpec with component metadata

        Raises:
            KeyError: If component not found
        """
        parts = name.split("/")

        # Handle full name: source/category/name
        if len(parts) >= 3:
            source_name = parts[0]
            component_name = parts[-1]
            if source_name in self._sources:
                for spec in self._sources[source_name].list_components():
                    if spec.name == component_name:
                        return spec

        # Short name: search all sources
        for source in self._sources.values():
            for spec in source.list_components():
                if spec.name == name:
                    return spec

        raise KeyError(f"Component not found: {name}")

    def get(self, full_name: str, use_cache: bool = True, **params: Any) -> Component:
        """
        Get component by full name (source/category/name) or short name.

        Args:
            full_name: Component name (e.g., "motor_2207" or "custom/motor/motor_2207")
            use_cache: If True, return cached instance if available (default: True)
            **params: Component parameters (e.g., size="M3-0.5", length=10)

        Returns:
            Component instance (may be cached if use_cache=True)

        Examples:
            registry.get("custom/motor/motor_2207")
            registry.get("motor_2207")  # searches all sources
            registry.get("SocketHeadCapScrew", size="M3-0.5", length=10)
            registry.get("motor_2207", use_cache=False)  # force new instance

        Raises:
            KeyError: If component not found in any source
            ValueError: If component found but missing required parameters
            ParameterValidationError: If parameter validation fails
        """
        cache_key = _make_cache_key(full_name, params)

        # Check cache first
        if use_cache and cache_key in self._cache:
            self._cache_hits += 1
            # Move to end for LRU ordering
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        self._cache_misses += 1
        component = self._get_uncached(full_name, **params)

        # Store in cache
        if use_cache:
            self._cache[cache_key] = component
            self._cache.move_to_end(cache_key)
            # Evict oldest if over capacity
            while len(self._cache) > self._cache_max_size:
                self._cache.popitem(last=False)

        return component

    def _get_uncached(self, full_name: str, **params: Any) -> Component:
        """Internal method to fetch component without cache."""
        parts = full_name.split("/")

        if len(parts) >= 3:
            # Full name: source/category/name
            source_name = parts[0]
            component_name = parts[-1]
            if source_name in self._sources:
                return self._sources[source_name].get_component(component_name, **params)

        # Short name: search all sources
        # Track ValueError to distinguish "not found" from "found but missing params"
        last_value_error: ValueError | None = None

        for source in self._sources.values():
            try:
                return source.get_component(full_name, **params)
            except KeyError:
                # Component not in this source, try next
                continue
            except ValueError as e:
                # Check if it's a parameter validation error - these should propagate immediately
                # We check the class name to avoid importing the specific exception
                if type(e).__name__ == "ParameterValidationError":
                    raise
                # Other ValueErrors (e.g., missing required params) indicate the
                # component was found but params were wrong - save error
                last_value_error = e
                continue

        # If we got a ValueError, the component exists but needs params
        if last_value_error is not None:
            raise last_value_error

        raise KeyError(f"Component not found: {full_name}")

    def clear_cache(self) -> int:
        """
        Clear all cached components.

        Returns:
            Number of items that were cleared
        """
        count = len(self._cache)
        self._cache.clear()
        return count

    def cache_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats with hits, misses, size, and max_size
        """
        return CacheStats(
            hits=self._cache_hits,
            misses=self._cache_misses,
            size=len(self._cache),
            max_size=self._cache_max_size,
        )


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
    """Initialize registry with default sources.

    Sources are loaded on a best-effort basis. If a source's dependencies
    are not installed, that source is silently skipped. This allows the
    registry to work with any subset of optional dependencies.

    Sources are registered in order:
    1. custom - Always available (built-in components)
    2. warehouse - Requires cq_warehouse (fasteners, bearings)
    3. electronics - Requires cq_electronics (boards, connectors)
    4. partcad - Requires partcad (package manager)
    """
    # Import here to avoid circular imports
    from semicad.sources import custom, electronics, partcad_source, warehouse

    try:
        registry.register_source(custom.CustomSource())
    except (ImportError, OSError, RuntimeError) as e:
        # ImportError: dependency missing
        # OSError: file access issues
        # RuntimeError: initialization failed
        import logging

        logging.debug("Custom source not available: %s", e)

    try:
        registry.register_source(warehouse.WarehouseSource())
    except ImportError:
        pass  # cq_warehouse not installed (expected if not using fasteners)
    except (OSError, RuntimeError) as e:
        import logging

        logging.debug("Warehouse source initialization failed: %s", e)

    try:
        registry.register_source(electronics.ElectronicsSource())
    except ImportError:
        pass  # cq_electronics not installed (expected if not using electronics)
    except (OSError, RuntimeError) as e:
        import logging

        logging.debug("Electronics source initialization failed: %s", e)

    try:
        registry.register_source(partcad_source.PartCADSource())
    except ImportError:
        pass  # PartCAD not installed (expected if not using package manager)
    except (OSError, RuntimeError) as e:
        import logging

        logging.debug("PartCAD source initialization failed: %s", e)
