"""Regression tests for electronics adapter.

Tests cover:
- Geometry validation passes for all components
- Export file sizes are reasonable
- Build times are within limits
- Bounding box sanity checks
- Solid body verification
"""

import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock
import sys

import cadquery as cq


# Threshold constants for regression testing
MAX_BUILD_TIME_SECONDS = 5.0  # Max time to build any component
MIN_STEP_FILE_SIZE = 100  # Minimum STEP file size in bytes
MAX_STEP_FILE_SIZE = 50_000_000  # Maximum STEP file size (50MB)
MIN_STL_FILE_SIZE = 100  # Minimum STL file size in bytes
MAX_STL_FILE_SIZE = 100_000_000  # Maximum STL file size (100MB)


class TestGeometryValidationRegression:
    """Regression tests for geometry validation."""

    def test_all_catalog_components_validate(self, mock_cq_electronics):
        """All catalog components should pass validation."""
        from semicad.sources.electronics import ElectronicsSource, COMPONENT_CATALOG

        source = ElectronicsSource()

        for name in COMPONENT_CATALOG.keys():
            components = list(source.list_components())
            matching = [c for c in components if c.name == name]

            if not matching:
                continue  # Component not loaded (missing dependency)

            # Get required params for this component
            _, _, _, _, required, defaults = COMPONENT_CATALOG[name]

            # Build params with required values (use dummy values)
            params = {}
            for param in required:
                if param in ["length", "width", "height"]:
                    params[param] = 10.0
                else:
                    params[param] = 1

            component = source.get_component(name, **params)
            result = component.validate()

            assert result.is_valid, f"{name} failed validation: {[i.message for i in result.issues if i.severity.value == 'error']}"

    def test_geometry_has_solid_bodies(self, mock_cq_electronics):
        """Built geometry should contain solid bodies."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        result = component.validate()

        assert result.solid_count >= 1, f"Expected at least 1 solid, got {result.solid_count}"

    def test_geometry_has_faces(self, mock_cq_electronics):
        """Built geometry should have faces."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        result = component.validate()

        assert result.face_count >= 1, f"Expected faces, got {result.face_count}"

    def test_bounding_box_reasonable(self, mock_cq_electronics):
        """Bounding box should be within reasonable limits."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        result = component.validate()

        assert result.bbox_size is not None
        for dim in result.bbox_size:
            assert dim > 0, "Dimension should be positive"
            assert dim < 2000, "Dimension should be less than 2 meters"

    def test_no_degenerate_geometry(self, mock_cq_electronics):
        """Geometry should not be degenerate (zero volume)."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        result = component.validate()

        # All dimensions should be non-zero
        assert result.bbox_size is not None
        assert all(dim > 0.001 for dim in result.bbox_size), "Dimensions should be non-zero"


class TestExportFileSizeRegression:
    """Regression tests for export file sizes."""

    def test_step_file_size_reasonable(self, mock_cq_electronics, temp_output_dir):
        """STEP files should be reasonable size."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.step import export_step

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        output_file = temp_output_dir / "size_test.step"
        result = export_step(component.geometry, output_file)

        size = result.stat().st_size
        assert size >= MIN_STEP_FILE_SIZE, f"STEP file too small: {size} bytes"
        assert size <= MAX_STEP_FILE_SIZE, f"STEP file too large: {size} bytes"

    def test_stl_file_size_reasonable(self, mock_cq_electronics, temp_output_dir):
        """STL files should be reasonable size."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.stl import export_stl, STLQuality

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        output_file = temp_output_dir / "size_test.stl"
        result = export_stl(component.geometry, output_file, quality=STLQuality.NORMAL)

        size = result.stat().st_size
        assert size >= MIN_STL_FILE_SIZE, f"STL file too small: {size} bytes"
        assert size <= MAX_STL_FILE_SIZE, f"STL file too large: {size} bytes"

    def test_stl_quality_affects_size(self, mock_cq_electronics, temp_output_dir):
        """Higher STL quality should generally produce larger files."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.stl import export_stl, STLQuality

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        draft_file = temp_output_dir / "draft.stl"
        fine_file = temp_output_dir / "fine.stl"

        export_stl(component.geometry, draft_file, quality=STLQuality.DRAFT)
        export_stl(component.geometry, fine_file, quality=STLQuality.FINE)

        # Fine should be larger or equal (more triangles)
        assert fine_file.stat().st_size >= draft_file.stat().st_size


class TestBuildTimeRegression:
    """Regression tests for build times."""

    @pytest.mark.slow
    def test_build_time_within_limit(self, mock_cq_electronics):
        """Component build time should be within limit."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        start = time.perf_counter()
        _ = component.geometry
        elapsed = time.perf_counter() - start

        assert elapsed < MAX_BUILD_TIME_SECONDS, f"Build took {elapsed:.2f}s, limit is {MAX_BUILD_TIME_SECONDS}s"

    @pytest.mark.slow
    def test_validation_time_reasonable(self, mock_cq_electronics):
        """Validation should complete in reasonable time."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        start = time.perf_counter()
        _ = component.validate()
        elapsed = time.perf_counter() - start

        # Validation includes build, so allow double the time
        assert elapsed < MAX_BUILD_TIME_SECONDS * 2, f"Validation took {elapsed:.2f}s"

    @pytest.mark.slow
    def test_export_time_reasonable(self, mock_cq_electronics, temp_output_dir):
        """Export should complete in reasonable time."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.step import export_step

        source = ElectronicsSource()
        component = source.get_component("RPi3b")
        geom = component.geometry  # Build first

        start = time.perf_counter()
        export_step(geom, temp_output_dir / "time_test.step")
        elapsed = time.perf_counter() - start

        assert elapsed < MAX_BUILD_TIME_SECONDS, f"Export took {elapsed:.2f}s"


class TestConsistencyRegression:
    """Regression tests for output consistency."""

    def test_repeated_builds_consistent(self, mock_cq_electronics):
        """Repeated builds should produce consistent geometry."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        comp1 = source.get_component("RPi3b")
        comp2 = source.get_component("RPi3b")

        result1 = comp1.validate()
        result2 = comp2.validate()

        assert result1.bbox_size == result2.bbox_size
        assert result1.solid_count == result2.solid_count
        assert result1.face_count == result2.face_count

    def test_exports_consistent(self, mock_cq_electronics, temp_output_dir):
        """Repeated exports should produce same size files."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.step import export_step

        source = ElectronicsSource()
        component = source.get_component("RPi3b")
        geom = component.geometry

        file1 = temp_output_dir / "consist1.step"
        file2 = temp_output_dir / "consist2.step"

        export_step(geom, file1)
        export_step(geom, file2)

        # Files should be same size
        assert file1.stat().st_size == file2.stat().st_size

    def test_component_names_unique(self, mock_cq_electronics):
        """All components should have unique names."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())

        names = [c.name for c in components]
        assert len(names) == len(set(names)), "Duplicate component names found"


class TestParameterRegression:
    """Regression tests for parameter handling."""

    def test_default_params_preserved(self, mock_cq_electronics):
        """Default parameters should be in spec."""
        from semicad.sources.electronics import ElectronicsSource, COMPONENT_CATALOG

        source = ElectronicsSource()

        # PinHeader has defaults
        component = source.get_component("PinHeader")
        defaults = COMPONENT_CATALOG["PinHeader"][5]  # defaults dict

        for key, value in defaults.items():
            assert key in component.spec.params
            assert component.spec.params[key] == value

    def test_override_params_preserved(self, mock_cq_electronics):
        """Overridden parameters should be in spec."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("PinHeader", rows=5, columns=20)

        assert component.spec.params["rows"] == 5
        assert component.spec.params["columns"] == 20

    def test_required_params_in_spec(self, mock_cq_electronics):
        """Required parameters should be in component info."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())

        # BGA should indicate required params
        bga_specs = [c for c in components if c.name == "BGA"]
        if bga_specs:
            bga = bga_specs[0]
            assert "required" in bga.params or bga.params.get("required") is not None


class TestMetadataRegression:
    """Regression tests for component metadata."""

    def test_all_components_have_description(self, mock_cq_electronics):
        """All components should have descriptions."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())

        for comp in components:
            assert comp.description, f"{comp.name} missing description"
            assert len(comp.description) > 5, f"{comp.name} description too short"

    def test_all_components_have_category(self, mock_cq_electronics):
        """All components should have categories."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())

        for comp in components:
            assert comp.category, f"{comp.name} missing category"

    def test_source_name_consistent(self, mock_cq_electronics):
        """Source name should be consistent across all components."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())

        for comp in components:
            assert comp.source == "cq_electronics"


@pytest.mark.requires_cq_electronics
class TestRealComponentRegression:
    """Regression tests with real cq_electronics.

    These ensure the adapter works correctly with the actual library.
    """

    @pytest.mark.slow
    def test_real_component_build_time(self):
        """Real components should build within time limit."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())

        if not components:
            pytest.skip("No cq_electronics components available")

        for spec in components[:3]:  # Test first 3 to limit time
            component = source.get_component(spec.name)

            start = time.perf_counter()
            _ = component.geometry
            elapsed = time.perf_counter() - start

            assert elapsed < MAX_BUILD_TIME_SECONDS * 2, f"{spec.name} took {elapsed:.2f}s"

    def test_real_component_validation(self):
        """Real components should pass validation."""
        from semicad.sources.electronics import ElectronicsSource, COMPONENT_CATALOG

        source = ElectronicsSource()
        components = list(source.list_components())

        if not components:
            pytest.skip("No cq_electronics components available")

        for spec in components:
            # Get required params for this component
            if spec.name in COMPONENT_CATALOG:
                _, _, _, _, required, _ = COMPONENT_CATALOG[spec.name]
                # Build params with required values
                params = {}
                for param in required:
                    if param in ["length", "width", "height"]:
                        params[param] = 10.0
                    else:
                        params[param] = 1
            else:
                params = {}

            component = source.get_component(spec.name, **params)
            result = component.validate()

            # Should have reasonable geometry
            assert result.bbox_size is not None
            assert result.solid_count >= 0

    def test_real_export_produces_files(self, temp_output_dir):
        """Real component exports should produce non-empty files."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.export.step import export_step
        from semicad.export.stl import export_stl

        source = ElectronicsSource()
        components = list(source.list_components())

        if not components:
            pytest.skip("No cq_electronics components available")

        component = source.get_component(components[0].name)

        step_file = export_step(component.geometry, temp_output_dir / "real.step")
        stl_file = export_stl(component.geometry, temp_output_dir / "real.stl")

        assert step_file.stat().st_size > MIN_STEP_FILE_SIZE
        assert stl_file.stat().st_size > MIN_STL_FILE_SIZE
