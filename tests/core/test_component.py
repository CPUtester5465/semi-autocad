"""Tests for semicad.core.component module."""

import pytest
import cadquery as cq

from semicad.core.component import (
    Component,
    ComponentSpec,
    ComponentProvider,
    TranslatedComponent,
    RotatedComponent,
)


class TestComponentSpec:
    """Tests for ComponentSpec dataclass."""

    def test_basic_creation(self):
        """Test creating a ComponentSpec with required fields."""
        spec = ComponentSpec(
            name="test_part",
            source="custom",
            category="test",
        )
        assert spec.name == "test_part"
        assert spec.source == "custom"
        assert spec.category == "test"
        assert spec.params == {}
        assert spec.description == ""
        assert spec.metadata == {}

    def test_full_name(self):
        """Test that full_name returns source/category/name."""
        spec = ComponentSpec(
            name="motor_2207",
            source="custom",
            category="motor",
        )
        assert spec.full_name == "custom/motor/motor_2207"

    def test_with_params_and_metadata(self):
        """Test creating spec with params and metadata."""
        spec = ComponentSpec(
            name="screw",
            source="warehouse",
            category="fastener",
            params={"size": "M3-0.5", "length": 10},
            description="A simple screw",
            metadata={"weight": 0.5, "material": "steel"},
        )
        assert spec.params == {"size": "M3-0.5", "length": 10}
        assert spec.description == "A simple screw"
        assert spec.metadata["weight"] == 0.5


class ConcreteComponent(Component):
    """A concrete implementation of Component for testing."""

    def __init__(self, spec: ComponentSpec, geometry: cq.Workplane | None = None):
        super().__init__(spec)
        self._test_geometry = geometry or cq.Workplane("XY").box(10, 10, 5)

    def build(self) -> cq.Workplane:
        return self._test_geometry


class TestComponent:
    """Tests for Component abstract base class."""

    @pytest.fixture
    def sample_spec(self):
        """Create a sample ComponentSpec for testing."""
        return ComponentSpec(
            name="test_component",
            source="test",
            category="test",
        )

    @pytest.fixture
    def sample_component(self, sample_spec):
        """Create a sample component for testing."""
        return ConcreteComponent(sample_spec)

    def test_spec_property(self, sample_component, sample_spec):
        """Test that spec property returns the correct spec."""
        assert sample_component.spec == sample_spec

    def test_name_property(self, sample_component):
        """Test that name property returns component name."""
        assert sample_component.name == "test_component"

    def test_geometry_lazy_loading(self, sample_component):
        """Test that geometry is lazy-loaded on first access."""
        # Before accessing geometry, _geometry should be None
        assert sample_component._geometry is None

        # Access geometry triggers build()
        geom = sample_component.geometry
        assert geom is not None
        assert isinstance(geom, cq.Workplane)

        # Second access should return cached geometry
        geom2 = sample_component.geometry
        assert geom is geom2

    def test_translate(self, sample_component):
        """Test translate method returns TranslatedComponent."""
        translated = sample_component.translate(10, 20, 30)

        assert isinstance(translated, TranslatedComponent)
        assert translated.name == sample_component.name

    def test_rotate(self, sample_component):
        """Test rotate method returns RotatedComponent."""
        rotated = sample_component.rotate((0, 0, 1), 45)

        assert isinstance(rotated, RotatedComponent)
        assert rotated.name == sample_component.name


class TestTranslatedComponent:
    """Tests for TranslatedComponent decorator."""

    @pytest.fixture
    def base_component(self):
        """Create a base component for wrapping."""
        spec = ComponentSpec(name="base", source="test", category="test")
        return ConcreteComponent(spec)

    def test_translated_component_creation(self, base_component):
        """Test creating a translated component."""
        translated = TranslatedComponent(base_component, 10, 20, 30)

        assert translated._offset == (10, 20, 30)
        assert translated.name == base_component.name

    def test_translated_geometry(self, base_component):
        """Test that translation is applied to geometry."""
        translated = TranslatedComponent(base_component, 100, 0, 0)
        geom = translated.geometry

        # The geometry should be translated
        bbox = geom.val().BoundingBox()
        # Original box is centered at origin (10x10x5)
        # After translation by 100 in X, center should be at ~100
        assert bbox.xmin > 90  # Should be well past origin


class TestRotatedComponent:
    """Tests for RotatedComponent decorator."""

    @pytest.fixture
    def base_component(self):
        """Create a base component for wrapping."""
        spec = ComponentSpec(name="base", source="test", category="test")
        return ConcreteComponent(spec)

    def test_rotated_component_creation(self, base_component):
        """Test creating a rotated component."""
        rotated = RotatedComponent(base_component, (0, 0, 1), 90)

        assert rotated._axis == (0, 0, 1)
        assert rotated._angle == 90
        assert rotated.name == base_component.name

    def test_rotated_geometry(self, base_component):
        """Test that rotation is applied to geometry."""
        # Create a non-symmetric component to verify rotation
        spec = ComponentSpec(name="rect", source="test", category="test")
        rect_component = ConcreteComponent(
            spec,
            geometry=cq.Workplane("XY").box(20, 10, 5)  # Longer in X
        )

        rotated = RotatedComponent(rect_component, (0, 0, 1), 90)
        geom = rotated.geometry

        bbox = geom.val().BoundingBox()
        # After 90-degree rotation around Z, X and Y dimensions should swap
        x_size = bbox.xmax - bbox.xmin
        y_size = bbox.ymax - bbox.ymin

        # After rotation, should be longer in Y (was longer in X)
        assert y_size > x_size


class TestComponentProvider:
    """Tests for ComponentProvider protocol."""

    def test_component_is_provider(self):
        """Test that Component instances satisfy ComponentProvider protocol."""
        spec = ComponentSpec(name="test", source="test", category="test")
        component = ConcreteComponent(spec)

        assert isinstance(component, ComponentProvider)

    def test_any_object_with_build_is_provider(self):
        """Test that any object with build() method is a provider."""
        class CustomProvider:
            def build(self) -> cq.Workplane:
                return cq.Workplane("XY").box(5, 5, 5)

        provider = CustomProvider()
        assert isinstance(provider, ComponentProvider)


class TestComponentChaining:
    """Tests for chaining transformations."""

    def test_translate_then_rotate(self):
        """Test chaining translate and rotate."""
        spec = ComponentSpec(name="test", source="test", category="test")
        component = ConcreteComponent(spec)

        transformed = component.translate(10, 0, 0).rotate((0, 0, 1), 90)

        assert isinstance(transformed, RotatedComponent)
        # The chain should work and produce valid geometry
        geom = transformed.geometry
        assert geom is not None

    def test_multiple_translations(self):
        """Test chaining multiple translations."""
        spec = ComponentSpec(name="test", source="test", category="test")
        component = ConcreteComponent(spec)

        transformed = component.translate(10, 0, 0).translate(0, 20, 0)

        geom = transformed.geometry
        bbox = geom.val().BoundingBox()

        # Should be translated by (10, 20, 0) total
        center_x = (bbox.xmin + bbox.xmax) / 2
        center_y = (bbox.ymin + bbox.ymax) / 2

        assert abs(center_x - 10) < 0.01
        assert abs(center_y - 20) < 0.01
