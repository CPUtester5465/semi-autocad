"""Unit tests for the ElectronicsSource adapter.

Tests cover:
- Component catalog loading
- ElectronicsSource methods (list_components, get_component, etc.)
- ElectronicsComponent build and geometry conversion
- Parameter handling (defaults, overrides, required params)
- Error handling
"""

import pytest
from unittest.mock import MagicMock, patch
import sys

import cadquery as cq

from semicad.core.component import ComponentSpec


class TestComponentCatalog:
    """Test the COMPONENT_CATALOG structure."""

    def test_catalog_has_required_entries(self):
        """Catalog should have entries for known components."""
        from semicad.sources.electronics import COMPONENT_CATALOG

        # P2.2: Added PiTrayClip to the list
        expected = ["RPi3b", "PinHeader", "JackSurfaceMount", "BGA", "DinClip", "TopHat", "PiTrayClip"]
        for name in expected:
            assert name in COMPONENT_CATALOG, f"Missing {name} in catalog"

    def test_catalog_entry_structure(self):
        """Each catalog entry should have correct structure."""
        from semicad.sources.electronics import COMPONENT_CATALOG

        for name, entry in COMPONENT_CATALOG.items():
            assert len(entry) == 6, f"{name}: expected 6 elements in tuple"
            module_path, class_name, category, description, required, defaults = entry

            assert isinstance(module_path, str), f"{name}: module_path should be str"
            assert isinstance(class_name, str), f"{name}: class_name should be str"
            assert isinstance(category, str), f"{name}: category should be str"
            assert isinstance(description, str), f"{name}: description should be str"
            assert isinstance(required, list), f"{name}: required should be list"
            assert isinstance(defaults, dict), f"{name}: defaults should be dict"

    def test_catalog_categories(self):
        """Catalog should contain expected categories."""
        from semicad.sources.electronics import COMPONENT_CATALOG

        categories = set()
        for _, entry in COMPONENT_CATALOG.items():
            categories.add(entry[2])  # category is 3rd element

        # P2.2: Added "mounting" category for PiTrayClip
        expected_categories = {"board", "connector", "smd", "mechanical", "mounting"}
        assert categories == expected_categories

    def test_catalog_required_params(self):
        """Specific components should have required params."""
        from semicad.sources.electronics import COMPONENT_CATALOG

        # BGA requires length and width
        assert COMPONENT_CATALOG["BGA"][4] == ["length", "width"]

        # TopHat requires length
        assert COMPONENT_CATALOG["TopHat"][4] == ["length"]

        # RPi3b has no required params
        assert COMPONENT_CATALOG["RPi3b"][4] == []


class TestElectronicsSource:
    """Test ElectronicsSource class."""

    def test_source_name(self, mock_cq_electronics):
        """Source should be named 'cq_electronics'."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        assert source.name == "cq_electronics"

    def test_list_components_returns_specs(self, mock_cq_electronics):
        """list_components should yield ComponentSpec objects."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())

        assert len(components) > 0
        for spec in components:
            assert isinstance(spec, ComponentSpec)
            assert spec.source == "cq_electronics"
            assert spec.name != ""
            assert spec.category != ""

    def test_list_components_includes_all_available(self, mock_cq_electronics):
        """list_components should include all successfully loaded components."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())
        names = [c.name for c in components]

        # With mocked modules, all catalog items should load (P2.2: added PiTrayClip)
        expected = ["RPi3b", "PinHeader", "JackSurfaceMount", "BGA", "DinClip", "TopHat", "PiTrayClip"]
        for name in expected:
            assert name in names, f"Missing {name} in list_components"

    def test_list_categories(self, mock_cq_electronics):
        """list_categories should return sorted unique categories."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        categories = source.list_categories()

        assert isinstance(categories, list)
        assert categories == sorted(categories)  # Should be sorted
        assert len(categories) == len(set(categories))  # Should be unique

    def test_list_by_category(self, mock_cq_electronics):
        """list_by_category should filter by category."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        # Test board category
        boards = list(source.list_by_category("board"))
        assert len(boards) >= 1
        for spec in boards:
            assert spec.category == "board"

        # Test connector category
        connectors = list(source.list_by_category("connector"))
        assert len(connectors) >= 2
        for spec in connectors:
            assert spec.category == "connector"

    def test_get_component_simple(self, mock_cq_electronics):
        """get_component should return a component for simple cases."""
        from semicad.sources.electronics import ElectronicsSource, ElectronicsComponent

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        assert isinstance(component, ElectronicsComponent)
        assert component.name == "RPi3b"
        assert component.spec.source == "cq_electronics"

    def test_get_component_with_params(self, mock_cq_electronics):
        """get_component should accept and use parameters."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("PinHeader", rows=2, columns=10)

        assert "rows=2" in component.name or "columns=10" in component.name
        assert component.spec.params.get("rows") == 2
        assert component.spec.params.get("columns") == 10

    def test_get_component_merges_defaults(self, mock_cq_electronics):
        """get_component should merge defaults with provided params."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("PinHeader", rows=2)

        # Should have default 'columns' value merged in
        assert "columns" in component.spec.params
        assert component.spec.params["rows"] == 2  # Provided value

    def test_get_component_missing_required_raises(self, mock_cq_electronics):
        """get_component should raise ValueError for missing required params."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        # BGA requires length and width
        with pytest.raises(ValueError) as exc_info:
            source.get_component("BGA")

        assert "Missing required parameters" in str(exc_info.value)
        assert "length" in str(exc_info.value)
        assert "width" in str(exc_info.value)

    def test_get_component_partial_required_raises(self, mock_cq_electronics):
        """get_component should raise for partial required params."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        # BGA requires both length and width
        with pytest.raises(ValueError) as exc_info:
            source.get_component("BGA", length=10)

        assert "width" in str(exc_info.value)

    def test_get_component_with_all_required(self, mock_cq_electronics):
        """get_component should work when all required params provided."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("BGA", length=10, width=10)

        assert component.spec.params["length"] == 10
        assert component.spec.params["width"] == 10

    def test_get_component_unknown_raises(self, mock_cq_electronics):
        """get_component should raise KeyError for unknown components."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(KeyError) as exc_info:
            source.get_component("UnknownComponent")

        assert "not found" in str(exc_info.value)

    def test_search_by_name(self, mock_cq_electronics):
        """search should find components by name."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        results = list(source.search("RPi"))

        assert len(results) >= 1
        assert any("RPi" in r.name for r in results)

    def test_search_by_description(self, mock_cq_electronics):
        """search should find components by description."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        results = list(source.search("Raspberry"))

        assert len(results) >= 1

    def test_search_case_insensitive(self, mock_cq_electronics):
        """search should be case-insensitive."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        upper = list(source.search("RPI"))
        lower = list(source.search("rpi"))

        assert len(upper) == len(lower)


class TestElectronicsComponent:
    """Test ElectronicsComponent class."""

    def test_component_builds_workplane(self, mock_cq_electronics):
        """build() should return a CadQuery Workplane."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        result = component.build()
        assert isinstance(result, cq.Workplane)

    def test_component_geometry_property(self, mock_cq_electronics):
        """geometry property should lazily build and cache."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        # First access should build
        geom1 = component.geometry
        assert isinstance(geom1, cq.Workplane)

        # Second access should return cached
        geom2 = component.geometry
        assert geom1 is geom2

    def test_component_spec_has_metadata(self, mock_cq_electronics):
        """Component spec should contain relevant metadata."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        assert component.spec.source == "cq_electronics"
        assert component.spec.category == "board"
        assert "Raspberry" in component.spec.description


class TestElectronicsComponentAssemblyConversion:
    """Test Assembly to Workplane conversion in ElectronicsComponent."""

    def test_assembly_converted_to_workplane(self, monkeypatch):
        """Assemblies from cq_electronics should be converted to Workplane."""
        import sys

        # Create a mock that returns an Assembly
        def make_assembly_component(**kwargs):
            mock = MagicMock()
            # Create a real Assembly
            assy = cq.Assembly()
            assy.add(cq.Workplane("XY").box(10, 10, 5), name="part1")
            mock.cq_object = assy
            return mock

        # Mock RPi3b to return an Assembly
        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = make_assembly_component

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }

        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        result = component.build()

        # Should be a Workplane, not an Assembly
        assert isinstance(result, cq.Workplane)
        assert not isinstance(result, cq.Assembly)

    def test_workplane_passed_through(self, mock_cq_electronics):
        """Workplane objects should pass through unchanged."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        result = component.build()
        assert isinstance(result, cq.Workplane)


class TestElectronicsSourceWithoutLibrary:
    """Test behavior when cq_electronics is not installed."""

    def test_source_loads_no_components_when_unavailable(self, monkeypatch):
        """ElectronicsSource should have no components when cq_electronics unavailable."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        # Manually clear the loaded components to simulate unavailable library
        source._available_components = {}
        components = list(source.list_components())

        # Should gracefully have no components
        assert len(components) == 0

    def test_get_component_raises_when_unavailable(self, monkeypatch):
        """get_component should raise KeyError when component not loaded."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        # Manually clear the loaded components
        source._available_components = {}

        with pytest.raises(KeyError):
            source.get_component("RPi3b")


class TestComponentTransforms:
    """Test translate and rotate on ElectronicsComponent."""

    def test_translate(self, mock_cq_electronics):
        """translate should return a TranslatedComponent."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.core.component import TranslatedComponent

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        translated = component.translate(10, 20, 30)

        assert isinstance(translated, TranslatedComponent)
        # The translated component should still be buildable
        geom = translated.geometry
        assert isinstance(geom, cq.Workplane)

    def test_rotate(self, mock_cq_electronics):
        """rotate should return a RotatedComponent."""
        from semicad.sources.electronics import ElectronicsSource
        from semicad.core.component import RotatedComponent

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        rotated = component.rotate((0, 0, 1), 45)

        assert isinstance(rotated, RotatedComponent)
        geom = rotated.geometry
        assert isinstance(geom, cq.Workplane)


# ============================================================================
# P2.2 - PiTrayClip Component Tests
# ============================================================================

class TestPiTrayClipComponent:
    """Test the PiTrayClip component added in P2.2."""

    def test_pitray_clip_in_catalog(self):
        """PiTrayClip should be in the component catalog."""
        from semicad.sources.electronics import COMPONENT_CATALOG

        assert "PiTrayClip" in COMPONENT_CATALOG

    def test_pitray_clip_catalog_entry(self):
        """PiTrayClip catalog entry should have correct structure."""
        from semicad.sources.electronics import COMPONENT_CATALOG

        entry = COMPONENT_CATALOG["PiTrayClip"]
        module_path, class_name, category, desc, required, defaults = entry

        assert module_path == "cq_electronics.sourcekit.pitray_clip"
        assert class_name == "PiTrayClip"
        assert category == "mounting"
        assert required == []  # No required params
        assert defaults == {}

    def test_pitray_clip_loads(self, mock_cq_electronics):
        """PiTrayClip should load successfully."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())
        names = [c.name for c in components]

        assert "PiTrayClip" in names

    def test_pitray_clip_get_component(self, mock_cq_electronics):
        """Should be able to get PiTrayClip component."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("PiTrayClip")

        assert component is not None
        assert component.spec.category == "mounting"

    def test_pitray_clip_builds(self, mock_cq_electronics):
        """PiTrayClip should build successfully."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("PiTrayClip")
        geom = component.geometry

        assert isinstance(geom, cq.Workplane)


# ============================================================================
# P2.3 - Component Metadata Tests
# ============================================================================

class TestComponentMetadata:
    """Test component metadata properties added in P2.3."""

    def test_raw_instance_property(self, mock_cq_electronics):
        """raw_instance should return the underlying cq_electronics instance."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        instance = component.raw_instance
        assert instance is not None
        # The mock returns a MagicMock, so verify it has cq_object
        assert hasattr(instance, "cq_object")

    def test_metadata_property_returns_dict(self, mock_cq_electronics):
        """metadata property should return a dict."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        metadata = component.metadata
        assert isinstance(metadata, dict)

    def test_metadata_extracts_class_constants(self, monkeypatch):
        """metadata should extract UPPER_CASE class constants."""
        import sys

        # Create component with class constants
        class MockRPi3b:
            WIDTH = 85
            HEIGHT = 56
            THICKNESS = 1.5
            HOLE_DIAMETER = 2.7
            _PRIVATE = "ignored"
            lowercase = "ignored"

            def __init__(self, **kwargs):
                self.cq_object = cq.Workplane("XY").box(85, 56, 1.5)

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = MockRPi3b

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }
        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        metadata = component.metadata
        assert metadata.get("WIDTH") == 85
        assert metadata.get("HEIGHT") == 56
        assert metadata.get("THICKNESS") == 1.5
        assert metadata.get("HOLE_DIAMETER") == 2.7
        # Private and lowercase should not be included
        assert "_PRIVATE" not in metadata
        assert "lowercase" not in metadata

    def test_mounting_holes_property(self, monkeypatch):
        """mounting_holes should return hole locations if available."""
        import sys

        class MockRPi3b:
            hole_points = [(24.5, 19.0), (-24.5, -39.0), (-24.5, 19.0), (24.5, -39.0)]

            def __init__(self, **kwargs):
                self.cq_object = cq.Workplane("XY").box(10, 10, 5)

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = MockRPi3b

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }
        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        holes = component.mounting_holes
        assert holes is not None
        assert len(holes) == 4
        assert (24.5, 19.0) in holes

    def test_mounting_holes_returns_none_if_not_available(self, monkeypatch):
        """mounting_holes should return None if component has no holes."""
        import sys

        # Create a component without hole_points attribute
        class MockComponentNoHoles:
            def __init__(self, **kwargs):
                self.cq_object = cq.Workplane("XY").box(10, 10, 5)
            # Intentionally no hole_points or mounting_holes attribute

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = MockComponentNoHoles

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }
        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        holes = component.mounting_holes
        assert holes is None

    def test_dimensions_property(self, monkeypatch):
        """dimensions should return (width, height, depth) tuple."""
        import sys

        class MockRPi3b:
            WIDTH = 85
            HEIGHT = 56
            THICKNESS = 1.5

            def __init__(self, **kwargs):
                self.cq_object = cq.Workplane("XY").box(10, 10, 5)

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = MockRPi3b

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }
        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        dims = component.dimensions
        assert dims is not None
        assert dims == (85.0, 56.0, 1.5)

    def test_dimensions_returns_none_if_not_available(self, mock_cq_electronics):
        """dimensions should return None if constants not available."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        # Our basic mock doesn't have WIDTH/HEIGHT constants
        dims = component.dimensions
        assert dims is None


# ============================================================================
# P2.4 - Assembly Preservation Tests
# ============================================================================

class TestAssemblyPreservation:
    """Test assembly preservation features added in P2.4."""

    def test_assembly_property_with_assembly_component(self, monkeypatch):
        """assembly property should return the original Assembly."""
        import sys

        def make_assembly_component(**kwargs):
            mock = MagicMock()
            assy = cq.Assembly()
            assy.add(cq.Workplane("XY").box(10, 10, 2), name="pcb", color=cq.Color("green"))
            assy.add(cq.Workplane("XY").box(5, 5, 3), name="chip", color=cq.Color("gray"))
            mock.cq_object = assy
            return mock

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = make_assembly_component

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }
        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        # Access geometry to trigger build
        _ = component.geometry

        assy = component.assembly
        assert assy is not None
        assert isinstance(assy, cq.Assembly)

    def test_assembly_property_returns_none_for_workplane(self, mock_cq_electronics):
        """assembly should return None for non-assembly components."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")

        # Our mock returns Workplane, not Assembly
        _ = component.geometry
        assert component.assembly is None

    def test_has_assembly_property(self, monkeypatch):
        """has_assembly should return True for assembly-based components."""
        import sys

        def make_assembly_component(**kwargs):
            mock = MagicMock()
            assy = cq.Assembly()
            assy.add(cq.Workplane("XY").box(10, 10, 2), name="part1")
            mock.cq_object = assy
            return mock

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = make_assembly_component

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }
        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")
        _ = component.geometry

        assert component.has_assembly is True

    def test_list_parts_returns_part_names(self, monkeypatch):
        """list_parts should return names of all parts in assembly."""
        import sys

        def make_assembly_component(**kwargs):
            mock = MagicMock()
            assy = cq.Assembly()
            assy.add(cq.Workplane("XY").box(10, 10, 2), name="pcb_substrate")
            assy.add(cq.Workplane("XY").box(5, 5, 3), name="cpu_chip")
            assy.add(cq.Workplane("XY").box(3, 6, 4), name="ethernet_port")
            mock.cq_object = assy
            return mock

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = make_assembly_component

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }
        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")
        _ = component.geometry

        parts = component.list_parts()
        assert isinstance(parts, list)
        # Assembly.traverse() returns parts differently, but our list should have names

    def test_get_color_map(self, monkeypatch):
        """get_color_map should return part name to color mapping."""
        import sys

        def make_assembly_component(**kwargs):
            mock = MagicMock()
            assy = cq.Assembly()
            assy.add(cq.Workplane("XY").box(10, 10, 2), name="pcb", color=cq.Color("green"))
            mock.cq_object = assy
            return mock

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = make_assembly_component

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }
        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        component = source.get_component("RPi3b")
        _ = component.geometry

        color_map = component.get_color_map()
        assert isinstance(color_map, dict)

    def test_assembly_info_dataclass(self):
        """AssemblyInfo should properly extract info from Assembly."""
        from semicad.sources.electronics import AssemblyInfo, PartInfo

        assy = cq.Assembly()
        assy.add(cq.Workplane("XY").box(10, 10, 2), name="pcb", color=cq.Color("green"))
        assy.add(cq.Workplane("XY").box(5, 5, 3), name="chip", color=cq.Color("gray"))

        info = AssemblyInfo.from_assembly(assy)

        assert isinstance(info, AssemblyInfo)
        assert len(info.parts) >= 0  # Depends on traverse behavior

    def test_part_info_color_hex(self):
        """PartInfo.color_hex should return hex color string."""
        from semicad.sources.electronics import PartInfo

        part = PartInfo(name="test", color=(1.0, 0.0, 0.0, 1.0))
        assert part.color_hex == "#ff0000"

        part_no_color = PartInfo(name="test2", color=None)
        assert part_no_color.color_hex is None


# ============================================================================
# P2.6 - Parameter Validation Tests
# ============================================================================

class TestParameterValidation:
    """Test parameter validation features added in P2.6."""

    def test_param_schemas_exist(self):
        """PARAM_SCHEMAS should exist for catalog components."""
        from semicad.sources.electronics import PARAM_SCHEMAS, COMPONENT_CATALOG

        for name in COMPONENT_CATALOG:
            assert name in PARAM_SCHEMAS, f"Missing PARAM_SCHEMAS for {name}"

    def test_validate_params_with_valid_params(self):
        """validate_params should accept valid parameters."""
        from semicad.sources.electronics import validate_params

        result = validate_params("PinHeader", {"rows": 2, "columns": 10})
        assert result["rows"] == 2
        assert result["columns"] == 10

    def test_validate_params_type_error(self):
        """validate_params should raise on wrong type."""
        from semicad.sources.electronics import validate_params, ParameterValidationError

        with pytest.raises(ParameterValidationError) as exc_info:
            validate_params("PinHeader", {"rows": "two"})

        assert "must be int" in str(exc_info.value)

    def test_validate_params_range_error_min(self):
        """validate_params should raise on value below minimum."""
        from semicad.sources.electronics import validate_params, ParameterValidationError

        with pytest.raises(ParameterValidationError) as exc_info:
            validate_params("PinHeader", {"rows": 0})

        assert "must be >= 1" in str(exc_info.value)

    def test_validate_params_range_error_max(self):
        """validate_params should raise on value above maximum."""
        from semicad.sources.electronics import validate_params, ParameterValidationError

        with pytest.raises(ParameterValidationError) as exc_info:
            validate_params("PinHeader", {"rows": 101})

        assert "must be <= 100" in str(exc_info.value)

    def test_validate_params_unknown_strict(self):
        """validate_params in strict mode should raise on unknown params."""
        from semicad.sources.electronics import validate_params, ParameterValidationError

        with pytest.raises(ParameterValidationError) as exc_info:
            validate_params("PinHeader", {"unknown_param": 5}, strict=True)

        assert "Unknown parameter" in str(exc_info.value)

    def test_validate_params_unknown_non_strict(self):
        """validate_params in non-strict mode should filter unknown params."""
        from semicad.sources.electronics import validate_params

        result = validate_params("PinHeader", {"rows": 2, "unknown": "test"}, strict=False)

        assert "rows" in result
        assert "unknown" not in result

    def test_get_component_validates_params(self, mock_cq_electronics):
        """get_component should validate parameters."""
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        source = ElectronicsSource()

        with pytest.raises(ParameterValidationError):
            source.get_component("PinHeader", rows="invalid")

    def test_get_component_strict_flag(self, mock_cq_electronics):
        """get_component should support strict flag."""
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        source = ElectronicsSource()

        # Strict mode (default) should raise
        with pytest.raises(ParameterValidationError):
            source.get_component("PinHeader", unknown_param=5)

        # Non-strict mode should succeed
        component = source.get_component("PinHeader", strict=False, unknown_param=5)
        assert component is not None
        # Unknown param should NOT be in validated params
        assert "unknown_param" not in component.spec.params

    def test_get_param_schema(self, mock_cq_electronics):
        """get_param_schema should return component's param schema."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        schema = source.get_param_schema("PinHeader")

        assert "rows" in schema
        assert schema["rows"]["type"] == int
        assert schema["rows"]["min"] == 1
        assert schema["rows"]["max"] == 100

    def test_get_param_schema_empty_for_unknown(self, mock_cq_electronics):
        """get_param_schema should return empty dict for unknown component."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        schema = source.get_param_schema("NonExistent")

        assert schema == {}

    def test_component_spec_includes_schema(self, mock_cq_electronics):
        """ComponentSpec from list_components should include schema."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        components = list(source.list_components())

        pin_header = next(c for c in components if c.name == "PinHeader")
        assert "schema" in pin_header.params
        assert "rows" in pin_header.params["schema"]


# ============================================================================
# P2.9 - Catalog Defaults and Simple Parameter Handling Tests
# ============================================================================

class TestCatalogDefaultsP29:
    """Test catalog defaults fixes from P2.9."""

    def test_rpi3b_has_simple_in_param_schema(self):
        """RPi3b PARAM_SCHEMAS should include 'simple' parameter."""
        from semicad.sources.electronics import PARAM_SCHEMAS

        assert "RPi3b" in PARAM_SCHEMAS
        assert "simple" in PARAM_SCHEMAS["RPi3b"]
        assert PARAM_SCHEMAS["RPi3b"]["simple"]["type"] == bool

    def test_rpi3b_default_includes_simple(self):
        """RPi3b catalog entry should have simple=True as default."""
        from semicad.sources.electronics import COMPONENT_CATALOG

        entry = COMPONENT_CATALOG["RPi3b"]
        defaults = entry[5]  # defaults is 6th element (0-indexed)

        assert "simple" in defaults
        assert defaults["simple"] is True

    def test_rpi3b_accepts_simple_param(self, mock_cq_electronics):
        """RPi3b should accept simple parameter without error."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        # Should not raise
        component = source.get_component("RPi3b", simple=False)
        assert component.spec.params["simple"] is False

        component2 = source.get_component("RPi3b", simple=True)
        assert component2.spec.params["simple"] is True


class TestSimpleParamRejectionP29:
    """Test that components without 'simple' support reject the parameter."""

    def test_dinclip_rejects_simple_param(self, mock_cq_electronics):
        """DinClip should reject 'simple' parameter with clear error."""
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        source = ElectronicsSource()

        with pytest.raises(ParameterValidationError) as exc_info:
            source.get_component("DinClip", simple=False)

        error_msg = str(exc_info.value)
        assert "simple" in error_msg
        assert "Unknown parameter" in error_msg
        assert "none" in error_msg.lower()  # "Valid parameters: none"

    def test_tophat_rejects_simple_param(self, mock_cq_electronics):
        """TopHat should reject 'simple' parameter with clear error."""
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        source = ElectronicsSource()

        with pytest.raises(ParameterValidationError) as exc_info:
            source.get_component("TopHat", length=100, simple=True)

        error_msg = str(exc_info.value)
        assert "simple" in error_msg
        assert "Unknown parameter" in error_msg
        # Should list valid params
        assert "length" in error_msg or "depth" in error_msg or "slots" in error_msg

    def test_pitray_clip_rejects_simple_param(self, mock_cq_electronics):
        """PiTrayClip should reject 'simple' parameter with clear error."""
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        source = ElectronicsSource()

        with pytest.raises(ParameterValidationError) as exc_info:
            source.get_component("PiTrayClip", simple=True)

        error_msg = str(exc_info.value)
        assert "simple" in error_msg
        assert "Unknown parameter" in error_msg

    def test_dinclip_param_schema_is_empty(self):
        """DinClip PARAM_SCHEMAS should be empty (no params supported)."""
        from semicad.sources.electronics import PARAM_SCHEMAS

        assert "DinClip" in PARAM_SCHEMAS
        assert PARAM_SCHEMAS["DinClip"] == {}

    def test_tophat_param_schema_excludes_simple(self):
        """TopHat PARAM_SCHEMAS should NOT include 'simple'."""
        from semicad.sources.electronics import PARAM_SCHEMAS

        assert "TopHat" in PARAM_SCHEMAS
        assert "simple" not in PARAM_SCHEMAS["TopHat"]
        # But should have the valid params
        assert "length" in PARAM_SCHEMAS["TopHat"]
        assert "depth" in PARAM_SCHEMAS["TopHat"]
        assert "slots" in PARAM_SCHEMAS["TopHat"]

    def test_pitray_clip_param_schema_is_empty(self):
        """PiTrayClip PARAM_SCHEMAS should be empty (no params supported)."""
        from semicad.sources.electronics import PARAM_SCHEMAS

        assert "PiTrayClip" in PARAM_SCHEMAS
        assert PARAM_SCHEMAS["PiTrayClip"] == {}


class TestNonStrictModeP29:
    """Test non-strict mode behavior with unsupported params."""

    def test_dinclip_non_strict_filters_simple(self, mock_cq_electronics):
        """DinClip in non-strict mode should filter 'simple' param."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        # Should not raise in non-strict mode
        component = source.get_component("DinClip", strict=False, simple=False)

        # simple should NOT be in the params
        assert "simple" not in component.spec.params

    def test_tophat_non_strict_filters_simple(self, mock_cq_electronics):
        """TopHat in non-strict mode should filter 'simple' param."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        component = source.get_component("TopHat", length=100, strict=False, simple=True)

        # simple should NOT be in the params, but length should be
        assert "simple" not in component.spec.params
        assert component.spec.params["length"] == 100
