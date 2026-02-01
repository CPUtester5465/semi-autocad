"""Tests for semicad.core.registry module."""

import pytest
from collections.abc import Iterator
from unittest.mock import MagicMock

import cadquery as cq

from semicad.core.component import Component, ComponentSpec
from semicad.core.registry import (
    CacheStats,
    ComponentRegistry,
    ComponentSource,
    _make_cache_key,
)


class TestMakeCacheKey:
    """Tests for the _make_cache_key function."""

    def test_name_only(self):
        """Test cache key with just a name."""
        key = _make_cache_key("motor", {})
        assert key == "motor"

    def test_with_params(self):
        """Test cache key with parameters."""
        key = _make_cache_key("screw", {"size": "M3", "length": 10})
        # Params should be sorted alphabetically
        assert "length=10" in key
        assert "size='M3'" in key

    def test_deterministic(self):
        """Test that cache keys are deterministic."""
        params = {"b": 2, "a": 1}
        key1 = _make_cache_key("test", params)
        key2 = _make_cache_key("test", {"a": 1, "b": 2})
        assert key1 == key2


class TestCacheStats:
    """Tests for CacheStats dataclass."""

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=80, misses=20, size=50, max_size=100)
        assert stats.hit_rate == 80.0

    def test_hit_rate_zero_total(self):
        """Test hit rate with no requests."""
        stats = CacheStats(hits=0, misses=0, size=0, max_size=100)
        assert stats.hit_rate == 0.0

    def test_hit_rate_all_hits(self):
        """Test hit rate with all cache hits."""
        stats = CacheStats(hits=100, misses=0, size=50, max_size=100)
        assert stats.hit_rate == 100.0


class MockComponent(Component):
    """Mock component for testing."""

    def __init__(self, spec: ComponentSpec):
        super().__init__(spec)
        self._build_count = 0

    def build(self) -> cq.Workplane:
        self._build_count += 1
        return cq.Workplane("XY").box(10, 10, 5)


class MockSource(ComponentSource):
    """Mock component source for testing."""

    def __init__(self, name: str = "mock"):
        self._name = name
        self._components: dict[str, ComponentSpec] = {}

    @property
    def name(self) -> str:
        return self._name

    def add_component(self, name: str, category: str = "test", **kwargs) -> None:
        """Add a component to this mock source."""
        self._components[name] = ComponentSpec(
            name=name,
            source=self._name,
            category=category,
            **kwargs,
        )

    def list_components(self) -> Iterator[ComponentSpec]:
        yield from self._components.values()

    def get_component(self, name: str, **params) -> Component:
        if name not in self._components:
            raise KeyError(f"Component not found: {name}")
        spec = self._components[name]
        # Add params to spec for testing
        spec_with_params = ComponentSpec(
            name=spec.name,
            source=spec.source,
            category=spec.category,
            params=params,
            description=spec.description,
            metadata=spec.metadata,
        )
        return MockComponent(spec_with_params)


class TestComponentSource:
    """Tests for ComponentSource abstract class."""

    def test_search_default_implementation(self):
        """Test the default search implementation."""
        source = MockSource()
        source.add_component("motor_2207", description="Brushless motor")
        source.add_component("fc_board", description="Flight controller")
        source.add_component("esc_30a", description="Motor controller")

        results = list(source.search("motor"))
        assert len(results) == 2  # motor_2207 and esc (motor controller)

    def test_search_case_insensitive(self):
        """Test that search is case insensitive."""
        source = MockSource()
        source.add_component("TestPart", description="A test part")

        results = list(source.search("testpart"))
        assert len(results) == 1

        results = list(source.search("TESTPART"))
        assert len(results) == 1


class TestComponentRegistry:
    """Tests for ComponentRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return ComponentRegistry()

    @pytest.fixture
    def mock_source(self):
        """Create a mock source with some components."""
        source = MockSource("test_source")
        source.add_component("part_a", category="cat1")
        source.add_component("part_b", category="cat2")
        return source

    def test_register_source(self, registry, mock_source):
        """Test registering a component source."""
        registry.register_source(mock_source)

        assert "test_source" in registry.sources
        assert len(registry.sources) == 1

    def test_unregister_source(self, registry, mock_source):
        """Test unregistering a component source."""
        registry.register_source(mock_source)
        registry.unregister_source("test_source")

        assert "test_source" not in registry.sources

    def test_unregister_nonexistent_source(self, registry):
        """Test unregistering a source that doesn't exist."""
        # Should not raise an error
        registry.unregister_source("nonexistent")

    def test_list_all(self, registry, mock_source):
        """Test listing all components."""
        registry.register_source(mock_source)

        components = list(registry.list_all())
        assert len(components) == 2
        names = {c.name for c in components}
        assert names == {"part_a", "part_b"}

    def test_list_from_specific_source(self, registry):
        """Test listing components from a specific source."""
        source1 = MockSource("source1")
        source1.add_component("comp1")
        source2 = MockSource("source2")
        source2.add_component("comp2")

        registry.register_source(source1)
        registry.register_source(source2)

        components = list(registry.list_from("source1"))
        assert len(components) == 1
        assert components[0].name == "comp1"

    def test_list_from_nonexistent_source(self, registry):
        """Test listing from a source that doesn't exist."""
        components = list(registry.list_from("nonexistent"))
        assert components == []

    def test_search_all_sources(self, registry):
        """Test searching across all sources."""
        source1 = MockSource("source1")
        source1.add_component("motor_a")
        source2 = MockSource("source2")
        source2.add_component("motor_b")

        registry.register_source(source1)
        registry.register_source(source2)

        results = list(registry.search("motor"))
        assert len(results) == 2

    def test_search_specific_source(self, registry):
        """Test searching a specific source."""
        source1 = MockSource("source1")
        source1.add_component("motor_a")
        source2 = MockSource("source2")
        source2.add_component("motor_b")

        registry.register_source(source1)
        registry.register_source(source2)

        results = list(registry.search("motor", source="source1"))
        assert len(results) == 1
        assert results[0].name == "motor_a"

    def test_get_by_short_name(self, registry, mock_source):
        """Test getting a component by short name."""
        registry.register_source(mock_source)

        component = registry.get("part_a")
        assert component.name == "part_a"

    def test_get_by_full_name(self, registry, mock_source):
        """Test getting a component by full name."""
        registry.register_source(mock_source)

        component = registry.get("test_source/cat1/part_a")
        assert component.name == "part_a"

    def test_get_not_found(self, registry):
        """Test getting a component that doesn't exist."""
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_get_with_params(self, registry, mock_source):
        """Test getting a component with parameters."""
        registry.register_source(mock_source)

        component = registry.get("part_a", size="M3", length=10)
        assert component.spec.params == {"size": "M3", "length": 10}

    def test_get_spec(self, registry, mock_source):
        """Test getting a component spec without instantiating."""
        registry.register_source(mock_source)

        spec = registry.get_spec("part_a")
        assert spec.name == "part_a"
        assert isinstance(spec, ComponentSpec)

    def test_get_spec_not_found(self, registry):
        """Test getting a spec for a component that doesn't exist."""
        with pytest.raises(KeyError):
            registry.get_spec("nonexistent")


class TestRegistryCache:
    """Tests for registry caching behavior."""

    @pytest.fixture
    def registry(self):
        """Create a registry with a small cache for testing."""
        return ComponentRegistry(cache_size=3)

    @pytest.fixture
    def mock_source(self):
        """Create a mock source."""
        source = MockSource()
        source.add_component("comp1")
        source.add_component("comp2")
        source.add_component("comp3")
        source.add_component("comp4")
        return source

    def test_cache_hit(self, registry, mock_source):
        """Test that cached components are returned."""
        registry.register_source(mock_source)

        comp1 = registry.get("comp1")
        comp2 = registry.get("comp1")

        # Should be the same instance
        assert comp1 is comp2

        stats = registry.cache_stats()
        assert stats.hits == 1
        assert stats.misses == 1

    def test_cache_miss(self, registry, mock_source):
        """Test cache miss tracking."""
        registry.register_source(mock_source)

        registry.get("comp1")
        registry.get("comp2")

        stats = registry.cache_stats()
        assert stats.misses == 2
        assert stats.hits == 0

    def test_cache_eviction(self, registry, mock_source):
        """Test LRU cache eviction."""
        registry.register_source(mock_source)

        # Fill cache (size 3)
        registry.get("comp1")
        registry.get("comp2")
        registry.get("comp3")

        # This should evict comp1
        registry.get("comp4")

        stats = registry.cache_stats()
        assert stats.size == 3  # Still at max size

        # Accessing comp1 again should be a miss
        initial_misses = stats.misses
        registry.get("comp1")
        stats = registry.cache_stats()
        assert stats.misses == initial_misses + 1

    def test_cache_bypass(self, registry, mock_source):
        """Test bypassing cache with use_cache=False."""
        registry.register_source(mock_source)

        comp1 = registry.get("comp1")
        comp2 = registry.get("comp1", use_cache=False)

        # Should be different instances
        assert comp1 is not comp2

    def test_cache_params_differentiation(self, registry, mock_source):
        """Test that different params create different cache entries."""
        registry.register_source(mock_source)

        comp1 = registry.get("comp1", size="M3")
        comp2 = registry.get("comp1", size="M4")

        # Should be different instances due to different params
        assert comp1 is not comp2

        stats = registry.cache_stats()
        assert stats.misses == 2  # Two different cache entries

    def test_clear_cache(self, registry, mock_source):
        """Test clearing the cache."""
        registry.register_source(mock_source)

        registry.get("comp1")
        registry.get("comp2")

        cleared = registry.clear_cache()
        assert cleared == 2

        stats = registry.cache_stats()
        assert stats.size == 0

    def test_cache_stats(self, registry, mock_source):
        """Test cache statistics reporting."""
        registry.register_source(mock_source)

        registry.get("comp1")
        registry.get("comp1")
        registry.get("comp2")

        stats = registry.cache_stats()
        assert stats.hits == 1
        assert stats.misses == 2
        assert stats.size == 2
        assert stats.max_size == 3
        assert stats.hit_rate == pytest.approx(33.33, rel=0.1)


class TestRegistryErrorHandling:
    """Tests for registry error handling."""

    @pytest.fixture
    def registry(self):
        return ComponentRegistry()

    def test_value_error_propagation(self, registry):
        """Test that ValueError from source is propagated."""
        source = MockSource()
        source.add_component("param_required")

        # Override get_component to raise ValueError
        original_get = source.get_component
        def get_with_validation(name, **params):
            if name == "param_required" and "size" not in params:
                raise ValueError("Required parameter 'size' not provided")
            return original_get(name, **params)

        source.get_component = get_with_validation
        registry.register_source(source)

        with pytest.raises(ValueError, match="size"):
            registry.get("param_required")

    def test_multiple_sources_searched(self, registry):
        """Test that all sources are searched for short names."""
        source1 = MockSource("source1")
        source2 = MockSource("source2")
        source2.add_component("unique_part")

        registry.register_source(source1)
        registry.register_source(source2)

        # Should find it in source2
        component = registry.get("unique_part")
        assert component.name == "unique_part"
