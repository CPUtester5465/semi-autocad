"""Unit tests for the PartCADSource adapter.

Tests cover:
- PartCADSource initialization
- Component path parsing and normalization
- Component loading and geometry conversion
- Parameter handling
- Search functionality
- Package listing
- Error handling
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys

import cadquery as cq

from semicad.core.component import ComponentSpec


class TestPathParsing:
    """Test path parsing and normalization utilities."""

    def test_normalize_path_with_prefix(self):
        """Paths with // prefix should be normalized."""
        from semicad.sources.partcad_source import _normalize_path

        assert _normalize_path("//pub/std/metric") == "//pub/std/metric"

    def test_normalize_path_without_prefix(self):
        """Paths without // prefix should get it added."""
        from semicad.sources.partcad_source import _normalize_path

        assert _normalize_path("pub/std/metric") == "//pub/std/metric"

    def test_parse_part_path_with_colon(self):
        """Full paths with colon should parse correctly."""
        from semicad.sources.partcad_source import _parse_part_path

        package, part = _parse_part_path("//pub/std/metric/cqwarehouse:fastener/iso4017")
        assert package == "//pub/std/metric/cqwarehouse"
        assert part == "fastener/iso4017"

    def test_parse_part_path_without_prefix(self):
        """Paths without // prefix should still parse."""
        from semicad.sources.partcad_source import _parse_part_path

        package, part = _parse_part_path("pub/std/metric:bolt")
        assert package == "//pub/std/metric"
        assert part == "bolt"

    def test_parse_part_path_without_colon(self):
        """Paths without colon should use root package and keep normalized path."""
        from semicad.sources.partcad_source import _parse_part_path

        package, part = _parse_part_path("//somepath")
        assert package == "//"
        # The normalized path is kept as the part name when no colon separator
        assert part == "//somepath"


class TestPartCADSource:
    """Test PartCADSource class."""

    def test_source_name(self):
        """Source should be named 'partcad'."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        assert source.name == "partcad"

    def test_default_packages(self):
        """Source should have default packages configured."""
        from semicad.sources.partcad_source import PartCADSource, DEFAULT_PACKAGES

        source = PartCADSource()
        assert source._packages == DEFAULT_PACKAGES

    def test_custom_packages(self):
        """Source should accept custom package list."""
        from semicad.sources.partcad_source import PartCADSource

        custom = ["//pub/custom"]
        source = PartCADSource(packages=custom)
        assert source._packages == custom

    def test_lazy_context_initialization(self):
        """Context should not be initialized until needed."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        assert source._context is None
        assert source._initialized is False

    def test_get_category_fastener(self):
        """Fastener-related names should be categorized correctly."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()

        assert source._get_category("fastener/bolt") == "fastener"
        assert source._get_category("fastener/screw") == "fastener"
        assert source._get_category("nut_m3") == "fastener"

    def test_get_category_motor(self):
        """Motor-related names should be categorized correctly."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()

        assert source._get_category("motor_nema17") == "motor"
        assert source._get_category("servo_mg995") == "motor"
        assert source._get_category("stepper_42") == "motor"
        assert source._get_category("nema17") == "motor"

    def test_get_category_bearing(self):
        """Bearing-related names should be categorized correctly."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()

        assert source._get_category("bearing_608") == "bearing"
        assert source._get_category("bushing_bronze") == "bearing"

    def test_get_category_electronics(self):
        """Electronics-related names should be categorized correctly."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()

        assert source._get_category("board_arduino") == "electronics"
        assert source._get_category("pcb_mount") == "electronics"
        assert source._get_category("raspberry_pi") == "electronics"

    def test_get_category_connector(self):
        """Connector-related names should be categorized correctly."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()

        assert source._get_category("connector_usb") == "connector"
        assert source._get_category("header_2x20") == "connector"

    def test_get_category_other(self):
        """Unknown names should be categorized as 'other'."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()

        assert source._get_category("random_part") == "other"
        assert source._get_category("widget") == "other"


class TestPartCADComponent:
    """Test PartCADComponent class."""

    def test_component_stores_path(self):
        """Component should store the PartCAD path."""
        from semicad.sources.partcad_source import PartCADComponent
        from semicad.core.component import ComponentSpec

        spec = ComponentSpec(
            name="test_part",
            source="partcad",
            category="fastener",
            description="Test part",
        )
        component = PartCADComponent(spec, "//pub/test:part", {"size": "M3"})

        assert component.partcad_path == "//pub/test:part"

    def test_component_stores_params(self):
        """Component should store parameters."""
        from semicad.sources.partcad_source import PartCADComponent
        from semicad.core.component import ComponentSpec

        spec = ComponentSpec(
            name="test_part",
            source="partcad",
            category="fastener",
            description="Test part",
        )
        params = {"size": "M3", "length": 10}
        component = PartCADComponent(spec, "//pub/test:part", params)

        assert component.parameters == params

    def test_component_params_copy(self):
        """parameters property should return a copy."""
        from semicad.sources.partcad_source import PartCADComponent
        from semicad.core.component import ComponentSpec

        spec = ComponentSpec(
            name="test_part",
            source="partcad",
            category="fastener",
            description="Test part",
        )
        params = {"size": "M3"}
        component = PartCADComponent(spec, "//pub/test:part", params)

        # Modifying returned params shouldn't affect original
        returned = component.parameters
        returned["new_key"] = "value"

        assert "new_key" not in component._params

    def test_component_lazy_context(self):
        """Component should not initialize context until build."""
        from semicad.sources.partcad_source import PartCADComponent
        from semicad.core.component import ComponentSpec

        spec = ComponentSpec(
            name="test_part",
            source="partcad",
            category="fastener",
            description="Test part",
        )
        component = PartCADComponent(spec, "//pub/test:part", None)

        assert component._context is None


class TestPartCADSourceWithMockedContext:
    """Test PartCADSource with mocked PartCAD context."""

    @pytest.fixture
    def mock_partcad(self):
        """Mock the partcad module."""
        mock_context = MagicMock()
        mock_project = MagicMock()
        mock_project.parts = {
            "fastener/bolt_m3": {"type": "cadquery"},
            "fastener/nut_m3": {"type": "cadquery"},
        }
        mock_project.get_child_project_names.return_value = []

        mock_context.get_project.return_value = mock_project
        mock_context.get_part.return_value = MagicMock(config={"type": "cadquery"})

        with patch("semicad.sources.partcad_source.PartCADSource._get_context") as mock_get_ctx:
            mock_get_ctx.return_value = mock_context
            yield mock_context

    def test_list_parts_in_package(self, mock_partcad):
        """list_parts_in_package should return part names."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        parts = source.list_parts_in_package("//pub/test")

        assert "fastener/bolt_m3" in parts
        assert "fastener/nut_m3" in parts

    def test_get_part_info(self, mock_partcad):
        """get_part_info should return part metadata."""
        from semicad.sources.partcad_source import PartCADSource

        # Setup mock to return proper part info
        mock_part = MagicMock()
        mock_part.config = {
            "type": "cadquery",
            "name": "bolt_m3",
            "desc": "M3 bolt",
            "parameters": {"size": {"type": "string", "default": "M3"}},
        }
        mock_partcad.get_part.return_value = mock_part

        source = PartCADSource()
        # Manually add to indexed parts for lookup
        source._indexed_parts["//pub/test:bolt_m3"] = {
            "name": "bolt_m3",
            "package": "//pub/test",
            "config": mock_part.config,
        }
        source._initialized = True

        info = source.get_part_info("//pub/test:bolt_m3")

        assert info["name"] == "bolt_m3"
        assert info["type"] == "cadquery"
        assert "parameters" in info

    def test_get_available_sizes(self, mock_partcad):
        """get_available_sizes should return enum values."""
        from semicad.sources.partcad_source import PartCADSource

        # Setup mock with enum parameter
        mock_part = MagicMock()
        mock_part.config = {
            "type": "cadquery",
            "name": "bolt",
            "parameters": {
                "size": {
                    "type": "string",
                    "enum": ["M3", "M4", "M5"],
                    "default": "M3",
                }
            },
        }
        mock_partcad.get_part.return_value = mock_part

        source = PartCADSource()
        source._indexed_parts["//pub/test:bolt"] = {
            "name": "bolt",
            "package": "//pub/test",
            "config": mock_part.config,
        }
        source._initialized = True

        sizes = source.get_available_sizes("//pub/test:bolt")

        assert sizes == ["M3", "M4", "M5"]


class TestSearchFunctionality:
    """Test search functionality."""

    @pytest.fixture
    def source_with_parts(self):
        """Create a source with pre-indexed parts."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        source._indexed_parts = {
            "//pub/test:fastener/hex_bolt": {
                "name": "fastener/hex_bolt",
                "package": "//pub/test",
                "config": {},
            },
            "//pub/test:fastener/socket_screw": {
                "name": "fastener/socket_screw",
                "package": "//pub/test",
                "config": {},
            },
            "//pub/test:motor/nema17": {
                "name": "motor/nema17",
                "package": "//pub/test",
                "config": {},
            },
        }
        source._initialized = True
        return source

    def test_search_by_name(self, source_with_parts):
        """Search should find parts by name."""
        results = list(source_with_parts.search("hex"))

        assert len(results) == 1
        assert results[0].name == "fastener/hex_bolt"

    def test_search_by_category(self, source_with_parts):
        """Search should find parts by category keyword."""
        results = list(source_with_parts.search("fastener"))

        assert len(results) == 2

    def test_search_case_insensitive(self, source_with_parts):
        """Search should be case insensitive."""
        results = list(source_with_parts.search("HEX"))

        assert len(results) == 1

    def test_search_no_results(self, source_with_parts):
        """Search with no matches should return empty."""
        results = list(source_with_parts.search("nonexistent"))

        assert len(results) == 0


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_get_component_not_found(self):
        """get_component should raise KeyError for unknown parts."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        source._initialized = True  # Skip indexing
        source._indexed_parts = {}

        with pytest.raises(KeyError):
            source.get_component("nonexistent_part")

    def test_get_part_info_not_found(self):
        """get_part_info should raise KeyError for unknown parts."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        source._initialized = True
        source._indexed_parts = {}

        with pytest.raises(KeyError):
            source.get_part_info("nonexistent")


class TestComponentSpecGeneration:
    """Test ComponentSpec generation from indexed parts."""

    def test_list_components_returns_specs(self):
        """list_components should yield ComponentSpec objects."""
        from semicad.sources.partcad_source import PartCADSource
        from semicad.core.component import ComponentSpec

        source = PartCADSource()
        source._indexed_parts = {
            "//pub/test:bolt": {
                "name": "bolt",
                "package": "//pub/test",
                "config": {"parameters": {"size": {"default": "M3"}}},
            }
        }
        source._initialized = True

        specs = list(source.list_components())

        assert len(specs) == 1
        assert isinstance(specs[0], ComponentSpec)
        assert specs[0].name == "bolt"
        assert specs[0].source == "partcad"

    def test_spec_includes_metadata(self):
        """ComponentSpec should include partcad_path in metadata."""
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        source._indexed_parts = {
            "//pub/test:bolt": {
                "name": "bolt",
                "package": "//pub/test",
                "config": {},
            }
        }
        source._initialized = True

        specs = list(source.list_components())

        assert specs[0].metadata["partcad_path"] == "//pub/test:bolt"
        assert specs[0].metadata["package"] == "//pub/test"


class TestIntegrationWithRegistry:
    """Test integration with the component registry."""

    def test_source_registered(self):
        """PartCAD source should be registered in the global registry."""
        from semicad.core.registry import get_registry

        registry = get_registry()
        assert "partcad" in registry.sources
