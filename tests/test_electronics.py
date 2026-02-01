"""Tests for cq_electronics source adapter with assembly preservation."""

import pytest
import cadquery as cq

from semicad.sources.electronics import (
    ElectronicsSource,
    ElectronicsComponent,
    AssemblyInfo,
    PartInfo,
)


@pytest.fixture
def electronics_source():
    """Create an ElectronicsSource instance."""
    return ElectronicsSource()


class TestAssemblyInfo:
    """Tests for AssemblyInfo dataclass."""

    def test_part_info_color_hex(self):
        """Test PartInfo.color_hex conversion."""
        part = PartInfo(name="test", color=(1.0, 0.0, 0.0, 1.0))
        assert part.color_hex == "#ff0000"

        part_green = PartInfo(name="test", color=(0.0, 1.0, 0.0, 1.0))
        assert part_green.color_hex == "#00ff00"

        part_no_color = PartInfo(name="test", color=None)
        assert part_no_color.color_hex is None

    def test_assembly_info_part_names(self):
        """Test AssemblyInfo.part_names property."""
        info = AssemblyInfo(
            parts=[
                PartInfo(name="part1", color=(1.0, 0.0, 0.0, 1.0)),
                PartInfo(name="part2", color=(0.0, 1.0, 0.0, 1.0)),
            ]
        )
        assert info.part_names == ["part1", "part2"]

    def test_assembly_info_get_color(self):
        """Test AssemblyInfo.get_color method."""
        info = AssemblyInfo(
            parts=[
                PartInfo(name="part1", color=(1.0, 0.0, 0.0, 1.0)),
                PartInfo(name="part2", color=None),
            ]
        )
        assert info.get_color("part1") == (1.0, 0.0, 0.0, 1.0)
        assert info.get_color("part2") is None
        assert info.get_color("nonexistent") is None

    def test_assembly_info_get_color_map(self):
        """Test AssemblyInfo.get_color_map method."""
        info = AssemblyInfo(
            parts=[
                PartInfo(name="part1", color=(1.0, 0.0, 0.0, 1.0)),
                PartInfo(name="part2", color=None),
                PartInfo(name="part3", color=(0.0, 0.0, 1.0, 1.0)),
            ]
        )
        color_map = info.get_color_map()
        assert "part1" in color_map
        assert "part2" not in color_map  # None colors excluded
        assert "part3" in color_map


class TestElectronicsComponent:
    """Tests for ElectronicsComponent with assembly preservation."""

    def test_rpi3b_has_assembly(self, electronics_source):
        """Test that RPi3b component preserves assembly."""
        rpi = electronics_source.get_component("RPi3b")
        assert isinstance(rpi, ElectronicsComponent)

        # Geometry should still work
        geometry = rpi.geometry
        assert isinstance(geometry, cq.Workplane)

        # Assembly should be preserved
        assert rpi.has_assembly
        assert rpi.assembly is not None
        assert isinstance(rpi.assembly, cq.Assembly)

    def test_rpi3b_assembly_info(self, electronics_source):
        """Test that assembly info is extracted correctly."""
        rpi = electronics_source.get_component("RPi3b")

        info = rpi.assembly_info
        assert info is not None
        assert isinstance(info, AssemblyInfo)
        assert len(info.parts) > 0

        # Check for expected part names
        part_names = info.part_names
        assert any("pcb" in name for name in part_names)

    def test_rpi3b_list_parts(self, electronics_source):
        """Test listing parts from assembly."""
        rpi = electronics_source.get_component("RPi3b")

        parts = rpi.list_parts()
        assert isinstance(parts, list)
        assert len(parts) > 0

        # RPi3b should have ethernet port
        assert any("ethernet" in p for p in parts)

    def test_rpi3b_get_color_map(self, electronics_source):
        """Test getting color map from assembly."""
        rpi = electronics_source.get_component("RPi3b")

        color_map = rpi.get_color_map()
        assert isinstance(color_map, dict)
        assert len(color_map) > 0

        # Colors should be RGBA tuples
        for name, color in color_map.items():
            assert isinstance(color, tuple)
            assert len(color) == 4
            assert all(0.0 <= c <= 1.0 for c in color)

    def test_rpi3b_get_part(self, electronics_source):
        """Test getting individual parts by name."""
        rpi = electronics_source.get_component("RPi3b")

        # Get a known part
        parts = rpi.list_parts()
        if parts:
            first_part = parts[0]
            part_geom = rpi.get_part(first_part)
            assert part_geom is not None
            assert isinstance(part_geom, cq.Workplane)

        # Non-existent part should return None
        assert rpi.get_part("nonexistent_part") is None

    def test_pin_header_assembly(self, electronics_source):
        """Test PinHeader also preserves assembly."""
        header = electronics_source.get_component(
            "PinHeader", rows=2, columns=10
        )

        # Should have geometry
        geometry = header.geometry
        assert isinstance(geometry, cq.Workplane)

        # Should preserve assembly (if it's an assembly type)
        if header.has_assembly:
            parts = header.list_parts()
            assert len(parts) > 0

    def test_assembly_export_capability(self, electronics_source, tmp_path):
        """Test that preserved assembly can be exported with colors."""
        rpi = electronics_source.get_component("RPi3b")

        assert rpi.has_assembly
        asm = rpi.assembly

        # Should be able to save as STEP (with colors preserved)
        step_file = tmp_path / "rpi_test.step"
        asm.save(str(step_file))
        assert step_file.exists()


class TestElectronicsSource:
    """Tests for ElectronicsSource."""

    def test_get_component_returns_electronics_component(self, electronics_source):
        """Test that get_component returns ElectronicsComponent."""
        rpi = electronics_source.get_component("RPi3b")
        assert isinstance(rpi, ElectronicsComponent)

    def test_list_components(self, electronics_source):
        """Test listing available components."""
        components = list(electronics_source.list_components())
        assert len(components) > 0

        names = [c.name for c in components]
        assert "RPi3b" in names

    def test_list_categories(self, electronics_source):
        """Test listing component categories."""
        categories = electronics_source.list_categories()
        assert "board" in categories
        assert "connector" in categories
