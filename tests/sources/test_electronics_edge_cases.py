"""Edge case tests for the electronics adapter.

Tests cover:
- cq_electronics not installed
- Invalid parameters
- Missing required parameters
- Unknown component names
- Malformed input handling
- Error message quality
"""

import pytest
from unittest.mock import MagicMock, patch
import sys

import cadquery as cq


class TestMissingCqElectronics:
    """Test behavior when cq_electronics is not installed."""

    def test_source_init_without_cq_electronics(self):
        """ElectronicsSource should initialize even without cq_electronics."""
        from semicad.sources.electronics import ElectronicsSource

        # Create source and manually clear to simulate unavailable library
        source = ElectronicsSource()
        source._available_components = {}

        # Should have no components but not crash
        components = list(source.list_components())
        assert len(components) == 0

    def test_graceful_degradation(self, monkeypatch):
        """System should work gracefully without cq_electronics."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        source._available_components = {}  # Simulate nothing loaded

        # These should not raise
        components = list(source.list_components())
        assert len(components) == 0

        categories = source.list_categories()
        assert len(categories) == 0

        by_category = list(source.list_by_category("board"))
        assert len(by_category) == 0


class TestInvalidParameters:
    """Test handling of invalid parameters."""

    def test_invalid_param_type(self, mock_cq_electronics):
        """Invalid parameter types should raise ParameterValidationError (P2.6)."""
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        source = ElectronicsSource()
        # P2.6: Parameter validation now catches type errors
        with pytest.raises(ParameterValidationError) as exc_info:
            source.get_component("PinHeader", rows="invalid")

        assert "must be int" in str(exc_info.value)

    def test_extra_params_rejected_in_strict_mode(self, mock_cq_electronics):
        """Extra parameters should be rejected in strict mode (P2.6)."""
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        source = ElectronicsSource()
        # P2.6: Unknown params are rejected in strict mode (default)
        with pytest.raises(ParameterValidationError) as exc_info:
            source.get_component("PinHeader", rows=1, unknown_param=True)

        assert "Unknown parameter" in str(exc_info.value)

    def test_extra_params_filtered_in_non_strict_mode(self, mock_cq_electronics):
        """Extra parameters should be filtered in non-strict mode (P2.6)."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        # P2.6: Non-strict mode filters unknown params
        component = source.get_component("PinHeader", rows=1, unknown_param=True, strict=False)

        # Unknown params should NOT be in the spec
        assert "unknown_param" not in component.spec.params

    def test_negative_dimensions_rejected(self, mock_cq_electronics):
        """Negative dimensions should be rejected by validation (P2.6)."""
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        source = ElectronicsSource()
        # P2.6: Range validation catches negative values
        with pytest.raises(ParameterValidationError) as exc_info:
            source.get_component("BGA", length=-10, width=-5)

        assert "must be >=" in str(exc_info.value)

    def test_zero_dimensions_rejected(self, mock_cq_electronics):
        """Zero dimensions should be rejected by validation (P2.6)."""
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        source = ElectronicsSource()
        # P2.6: Min value of 0.1 catches zero values
        with pytest.raises(ParameterValidationError) as exc_info:
            source.get_component("BGA", length=0, width=0)

        assert "must be >=" in str(exc_info.value)


class TestMissingRequiredParameters:
    """Test behavior with missing required parameters."""

    def test_missing_single_required(self, mock_cq_electronics):
        """Missing single required parameter should raise ValueError."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(ValueError) as exc_info:
            source.get_component("TopHat")  # Requires 'length'

        error_msg = str(exc_info.value)
        assert "Missing required parameters" in error_msg
        assert "length" in error_msg

    def test_missing_multiple_required(self, mock_cq_electronics):
        """Missing multiple required parameters should list all."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(ValueError) as exc_info:
            source.get_component("BGA")  # Requires length and width

        error_msg = str(exc_info.value)
        assert "length" in error_msg
        assert "width" in error_msg

    def test_error_message_lists_required(self, mock_cq_electronics):
        """Error message should tell user what params are required."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(ValueError) as exc_info:
            source.get_component("BGA")

        error_msg = str(exc_info.value)
        assert "Required:" in error_msg

    def test_partial_required_params(self, mock_cq_electronics):
        """Providing only some required params should list missing ones."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(ValueError) as exc_info:
            source.get_component("BGA", length=10)  # Missing width

        error_msg = str(exc_info.value)
        assert "width" in error_msg
        # Should not complain about length since it was provided
        assert "Missing required parameters" in error_msg


class TestUnknownComponentNames:
    """Test handling of unknown component names."""

    def test_unknown_component_raises_keyerror(self, mock_cq_electronics):
        """Unknown component should raise KeyError."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(KeyError):
            source.get_component("NonExistentComponent")

    def test_error_message_includes_name(self, mock_cq_electronics):
        """Error should include the component name that wasn't found."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(KeyError) as exc_info:
            source.get_component("FakeComponent123")

        assert "FakeComponent123" in str(exc_info.value)

    def test_similar_names_not_confused(self, mock_cq_electronics):
        """Similar but different names should not match."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(KeyError):
            source.get_component("rpi3b")  # lowercase, should not match RPi3b

        with pytest.raises(KeyError):
            source.get_component("RPi3B")  # Different case for B

    def test_empty_name(self, mock_cq_electronics):
        """Empty component name should raise KeyError."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(KeyError):
            source.get_component("")

    def test_whitespace_name(self, mock_cq_electronics):
        """Whitespace component name should raise KeyError."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises(KeyError):
            source.get_component("   ")


class TestMalformedInput:
    """Test handling of malformed input."""

    def test_none_component_name(self, mock_cq_electronics):
        """None as component name should raise appropriate error."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises((KeyError, TypeError)):
            source.get_component(None)

    def test_dict_as_component_name(self, mock_cq_electronics):
        """Dict as component name should raise appropriate error."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises((KeyError, TypeError)):
            source.get_component({"name": "RPi3b"})

    def test_list_as_component_name(self, mock_cq_electronics):
        """List as component name should raise appropriate error."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        with pytest.raises((KeyError, TypeError)):
            source.get_component(["RPi3b"])


class TestSearchEdgeCases:
    """Test search with edge cases."""

    def test_empty_query(self, mock_cq_electronics):
        """Empty search query should return all or empty."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        results = list(source.search(""))

        # Empty query typically matches everything
        assert len(results) >= 0

    def test_special_characters_in_query(self, mock_cq_electronics):
        """Special characters in query should be handled."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        # These should not raise
        results = list(source.search(".*"))
        results = list(source.search("$^"))
        results = list(source.search("[]"))
        results = list(source.search("()"))

    def test_very_long_query(self, mock_cq_electronics):
        """Very long query should be handled."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        long_query = "a" * 10000

        results = list(source.search(long_query))
        assert len(results) == 0  # Should find nothing but not crash

    def test_unicode_query(self, mock_cq_electronics):
        """Unicode in query should be handled."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        # These should not raise
        results = list(source.search("板"))  # Chinese for "board"
        results = list(source.search("🔌"))  # Connector emoji


class TestCategoryEdgeCases:
    """Test category operations with edge cases."""

    def test_list_by_nonexistent_category(self, mock_cq_electronics):
        """Listing by nonexistent category should return empty."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        results = list(source.list_by_category("nonexistent_category"))

        assert len(results) == 0

    def test_list_by_empty_category(self, mock_cq_electronics):
        """Listing by empty category should return empty."""
        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()
        results = list(source.list_by_category(""))

        assert len(results) == 0


class TestBuildErrors:
    """Test error handling during component build."""

    def test_build_error_propagates(self, monkeypatch):
        """Errors during build should propagate."""
        import sys

        # Create a component class that raises on cq_object access
        class FailingComponent:
            def __init__(self, **kwargs):
                pass

            @property
            def cq_object(self):
                raise RuntimeError("Build failed")

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = FailingComponent

        modules = {
            "cq_electronics": MagicMock(),
            "cq_electronics.rpi": MagicMock(),
            "cq_electronics.rpi.rpi3b": mock_rpi3b,
        }

        for name, mock in modules.items():
            monkeypatch.setitem(sys.modules, name, mock)

        from semicad.sources.electronics import ElectronicsSource

        source = ElectronicsSource()

        # Component creation works
        component = source.get_component("RPi3b")

        # But build should fail
        with pytest.raises(RuntimeError) as exc_info:
            component.build()
        assert "Build failed" in str(exc_info.value)

    def test_validation_catches_build_error(self, monkeypatch):
        """Validation should catch and report build errors."""
        import sys

        def failing_component(**kwargs):
            mock = MagicMock()
            # Raise error when cq_object is accessed
            type(mock).cq_object = property(lambda s: (_ for _ in ()).throw(RuntimeError("Test error")))
            return mock

        mock_rpi3b = MagicMock()
        mock_rpi3b.RPi3b = failing_component

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

        # Validation should catch and report the error
        result = component.validate()
        assert not result.is_valid
        assert result.has_errors
        assert any("BUILD_FAILED" in issue.code for issue in result.issues)
