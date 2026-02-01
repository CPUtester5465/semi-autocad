"""Integration tests for electronics adapter with the component registry.

Tests cover:
- Registry integration (registry.get() for electronics)
- Search functionality across sources
- BOM generation with electronics
- Export to STEP/STL
- Transform operations
- Geometry validation
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

import cadquery as cq


class TestRegistryElectronicsIntegration:
    """Test electronics components via the registry."""

    def test_electronics_source_registered(self, mock_cq_electronics):
        """Electronics source should be registered in the registry."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        assert "cq_electronics" in registry.sources

    def test_registry_get_electronics_short_name(self, mock_cq_electronics):
        """registry.get() should work with short names for electronics."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        component = registry.get("RPi3b")
        assert component is not None
        assert "RPi" in component.name

    def test_registry_get_electronics_full_name(self, mock_cq_electronics):
        """registry.get() should work with full names."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        component = registry.get("cq_electronics/board/RPi3b")
        assert component is not None

    def test_registry_get_with_params(self, mock_cq_electronics):
        """registry.get() should pass parameters to electronics components."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        component = registry.get("PinHeader", rows=2, columns=20)
        assert component.spec.params.get("rows") == 2
        assert component.spec.params.get("columns") == 20

    def test_registry_list_all_includes_electronics(self, mock_cq_electronics):
        """list_all should include electronics components."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        all_components = list(registry.list_all())
        electronics = [c for c in all_components if c.source == "cq_electronics"]

        assert len(electronics) > 0

    def test_registry_list_from_electronics(self, mock_cq_electronics):
        """list_from should work for electronics source."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        electronics = list(registry.list_from("cq_electronics"))
        assert len(electronics) > 0
        for spec in electronics:
            assert spec.source == "cq_electronics"

    def test_registry_search_finds_electronics(self, mock_cq_electronics):
        """search should find electronics components."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        results = list(registry.search("Raspberry"))
        assert len(results) >= 1

    def test_registry_search_with_source_filter(self, mock_cq_electronics):
        """search with source filter should only search that source."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        results = list(registry.search("header", source="cq_electronics"))
        for spec in results:
            assert spec.source == "cq_electronics"


class TestElectronicsExportIntegration:
    """Test exporting electronics components."""

    def test_export_to_step(self, mock_cq_electronics, temp_output_dir):
        """Electronics components should export to STEP."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.step import export_step

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        output_file = temp_output_dir / "rpi3b.step"
        result = export_step(component.geometry, output_file)

        assert result.exists()
        assert result.stat().st_size > 0

    def test_export_to_stl(self, mock_cq_electronics, temp_output_dir):
        """Electronics components should export to STL."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.stl import export_stl, STLQuality

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        output_file = temp_output_dir / "rpi3b.stl"
        result = export_stl(component.geometry, output_file, quality=STLQuality.NORMAL)

        assert result.exists()
        assert result.stat().st_size > 0

    def test_export_multiple_formats(self, mock_cq_electronics, temp_output_dir):
        """Same component should export to multiple formats."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.step import export_step
        from semicad.export.stl import export_stl

        source = ElectronicsSource()
        component = source.get_component("PinHeader", rows=1, columns=10)

        step_file = export_step(component.geometry, temp_output_dir / "header.step")
        stl_file = export_stl(component.geometry, temp_output_dir / "header.stl")

        assert step_file.exists()
        assert stl_file.exists()


class TestElectronicsValidationIntegration:
    """Test geometry validation for electronics components."""

    def test_component_validates_successfully(self, mock_cq_electronics):
        """Electronics components should pass validation."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        result = component.validate()

        assert result.is_valid
        assert not result.has_errors

    def test_validation_returns_metrics(self, mock_cq_electronics):
        """Validation should return geometry metrics."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        result = component.validate()

        assert result.bbox_size is not None
        assert result.solid_count >= 1

    def test_validation_with_custom_thresholds(self, mock_cq_electronics):
        """Validation should respect custom thresholds."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        # Very small max_dimension should trigger warning
        result = component.validate(max_dimension=1.0)

        assert result.has_warnings or not result.is_valid


class TestElectronicsTransformIntegration:
    """Test transform operations with electronics components."""

    def test_translate_preserves_geometry(self, mock_cq_electronics):
        """Translated component should still be valid."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")
        translated = component.translate(100, 50, 25)

        result = translated.validate()
        assert result.is_valid

    def test_rotate_preserves_geometry(self, mock_cq_electronics):
        """Rotated component should still be valid."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")
        rotated = component.rotate((0, 0, 1), 90)

        result = rotated.validate()
        assert result.is_valid

    def test_chained_transforms(self, mock_cq_electronics):
        """Chained transforms should work correctly."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        transformed = component.translate(10, 0, 0).rotate((0, 0, 1), 45)

        result = transformed.validate()
        assert result.is_valid

    def test_translated_component_exports(self, mock_cq_electronics, temp_output_dir):
        """Translated components should export successfully."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.step import export_step

        source = ElectronicsSource()
        component = source.get_component("RPi3b")
        translated = component.translate(50, 50, 0)

        output_file = temp_output_dir / "translated.step"
        result = export_step(translated.geometry, output_file)

        assert result.exists()


class TestMultipleElectronicsComponents:
    """Test working with multiple electronics components."""

    def test_multiple_components_independent(self, mock_cq_electronics):
        """Multiple component instances should be independent."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        comp1 = source.get_component("PinHeader", rows=1, columns=5)
        comp2 = source.get_component("PinHeader", rows=2, columns=10)

        # Should have different params
        assert comp1.spec.params["rows"] != comp2.spec.params["rows"]
        assert comp1.spec.params["columns"] != comp2.spec.params["columns"]

    def test_components_from_different_categories(self, mock_cq_electronics):
        """Should be able to get components from different categories."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        board = source.get_component("RPi3b")
        connector = source.get_component("PinHeader")
        mechanical = source.get_component("DinClip")

        assert board.spec.category == "board"
        assert connector.spec.category == "connector"
        assert mechanical.spec.category == "mechanical"


@pytest.mark.requires_cq_electronics
class TestRealElectronicsComponents:
    """Tests that require real cq_electronics installed.

    These tests verify behavior with the actual library.
    Skip with: pytest -m "not requires_cq_electronics"
    """

    def test_real_rpi3b_loads(self):
        """Real RPi3b should load successfully."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        if "RPi3b" not in [c.name for c in source.list_components()]:
            pytest.skip("RPi3b not available in cq_electronics")

        component = source.get_component("RPi3b")
        geom = component.geometry

        assert isinstance(geom, cq.Workplane)

    def test_real_component_validates(self):
        """Real components should pass validation."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())

        if not components:
            pytest.skip("No cq_electronics components available")

        component = source.get_component(components[0].name)
        result = component.validate()

        assert result.is_valid

    def test_real_component_exports(self, temp_output_dir):
        """Real components should export successfully."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.step import export_step

        source = ElectronicsSource()
        components = list(source.list_components())

        if not components:
            pytest.skip("No cq_electronics components available")

        component = source.get_component(components[0].name)
        output_file = temp_output_dir / "real_component.step"

        result = export_step(component.geometry, output_file)
        assert result.exists()
        assert result.stat().st_size > 100  # Should be a reasonable file size
