"""CLI e2e tests for electronics adapter commands.

Tests cover P2.5 - Fix CLI commands for parametric components:
- lib info with parametric components (should NOT require params)
- lib validate with --param options
- parse_validate_param helper function
- registry.get_spec() method
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import sys


class TestParseValidateParam:
    """Test the parse_validate_param helper function."""

    def test_empty_input(self):
        """Empty input should return empty dict."""
        from semicad.cli.commands.library import parse_validate_param

        result = parse_validate_param([])
        assert result == {}

        result = parse_validate_param(None)
        assert result == {}

    def test_single_param(self):
        """Single KEY=VALUE should parse correctly."""
        from semicad.cli.commands.library import parse_validate_param

        result = parse_validate_param(["rows=2"])
        assert result == {"rows": 2}

    def test_multiple_params(self):
        """Multiple KEY=VALUE pairs should all parse."""
        from semicad.cli.commands.library import parse_validate_param

        result = parse_validate_param(["rows=2", "columns=10", "above=7.5"])
        assert result == {"rows": 2, "columns": 10, "above": 7.5}

    def test_integer_conversion(self):
        """Integer values should be converted to int."""
        from semicad.cli.commands.library import parse_validate_param

        result = parse_validate_param(["count=42"])
        assert result["count"] == 42
        assert isinstance(result["count"], int)

    def test_float_conversion(self):
        """Float values should be converted to float."""
        from semicad.cli.commands.library import parse_validate_param

        result = parse_validate_param(["length=10.5"])
        assert result["length"] == 10.5
        assert isinstance(result["length"], float)

    def test_boolean_true_values(self):
        """True-like string values should convert to True."""
        from semicad.cli.commands.library import parse_validate_param

        # Note: "1" is parsed as int before reaching boolean check
        for value in ["true", "True", "TRUE", "yes", "Yes"]:
            result = parse_validate_param([f"flag={value}"])
            assert result["flag"] is True, f"Failed for {value}"

    def test_boolean_false_values(self):
        """False-like string values should convert to False."""
        from semicad.cli.commands.library import parse_validate_param

        # Note: "0" is parsed as int before reaching boolean check
        for value in ["false", "False", "FALSE", "no", "No"]:
            result = parse_validate_param([f"flag={value}"])
            assert result["flag"] is False, f"Failed for {value}"

    def test_numeric_one_and_zero_are_integers(self):
        """'1' and '0' should be parsed as integers, not booleans."""
        from semicad.cli.commands.library import parse_validate_param

        result = parse_validate_param(["val=1"])
        assert result["val"] == 1
        assert isinstance(result["val"], int)

        result = parse_validate_param(["val=0"])
        assert result["val"] == 0
        assert isinstance(result["val"], int)

    def test_string_values(self):
        """Non-numeric values should remain as strings."""
        from semicad.cli.commands.library import parse_validate_param

        result = parse_validate_param(["name=test_value"])
        assert result["name"] == "test_value"
        assert isinstance(result["name"], str)

    def test_invalid_format_raises(self):
        """Invalid format (no =) should raise BadParameter."""
        import click
        from semicad.cli.commands.library import parse_validate_param

        with pytest.raises(click.BadParameter) as exc_info:
            parse_validate_param(["invalid_no_equals"])

        assert "Invalid parameter format" in str(exc_info.value)

    def test_equals_in_value(self):
        """Values containing = should be preserved."""
        from semicad.cli.commands.library import parse_validate_param

        result = parse_validate_param(["expr=a=b"])
        assert result["expr"] == "a=b"


class TestRegistryGetSpec:
    """Test registry.get_spec() method added in P2.5."""

    def test_get_spec_simple_component(self, mock_cq_electronics):
        """get_spec should return spec for simple components."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        spec = registry.get_spec("RPi3b")

        assert spec is not None
        assert spec.name == "RPi3b"
        assert spec.source == "cq_electronics"

    def test_get_spec_parametric_component(self, mock_cq_electronics):
        """get_spec should work for parametric components without params."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        # BGA requires length and width, but get_spec should NOT require them
        spec = registry.get_spec("BGA")

        assert spec is not None
        assert spec.name == "BGA"
        assert "required" in spec.params
        assert "length" in spec.params["required"]
        assert "width" in spec.params["required"]

    def test_get_spec_full_name(self, mock_cq_electronics):
        """get_spec should work with full name (source/category/name)."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        spec = registry.get_spec("cq_electronics/board/RPi3b")

        assert spec is not None
        assert spec.name == "RPi3b"

    def test_get_spec_not_found_raises(self, mock_cq_electronics):
        """get_spec should raise KeyError for unknown component."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        with pytest.raises(KeyError) as exc_info:
            registry.get_spec("NonExistentComponent")

        assert "not found" in str(exc_info.value)


class TestLibInfoCommand:
    """Test lib info CLI command."""

    def test_lib_info_simple_component(self, mock_cq_electronics):
        """lib info should show info for simple components."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["info", "RPi3b"])

        assert result.exit_code == 0
        assert "RPi3b" in result.output
        assert "cq_electronics" in result.output

    def test_lib_info_parametric_component(self, mock_cq_electronics):
        """lib info should work for parametric components without params."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["info", "BGA"])

        # Should succeed without requiring parameters
        assert result.exit_code == 0
        assert "BGA" in result.output
        # Should show required parameters
        assert "Required parameters" in result.output or "required" in result.output.lower()

    def test_lib_info_shows_defaults(self, mock_cq_electronics):
        """lib info should show default parameter values."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["info", "PinHeader"])

        assert result.exit_code == 0
        # Should show defaults
        assert "Default" in result.output or "default" in result.output.lower()

    def test_lib_info_not_found(self, mock_cq_electronics):
        """lib info should error for unknown component."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["info", "NonExistentComponent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestLibValidateCommand:
    """Test lib validate CLI command."""

    def test_lib_validate_simple_component(self, mock_cq_electronics):
        """lib validate should work for simple components."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["validate", "RPi3b"])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_lib_validate_with_params(self, mock_cq_electronics):
        """lib validate should accept --param options."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, [
            "validate", "BGA",
            "-p", "length=10",
            "-p", "width=10"
        ])

        assert result.exit_code == 0
        assert "Parameters" in result.output or "valid" in result.output.lower()

    def test_lib_validate_missing_required_params(self, mock_cq_electronics):
        """lib validate should show helpful error for missing params."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["validate", "BGA"])

        # Should fail
        assert result.exit_code == 1
        # Should show helpful message about required params
        assert "required" in result.output.lower() or "missing" in result.output.lower()

    def test_lib_validate_shows_metrics(self, mock_cq_electronics):
        """lib validate should show geometry metrics."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["validate", "RPi3b"])

        assert result.exit_code == 0
        # Should show bounding box or solid count
        assert "Bounding box" in result.output or "Solids" in result.output

    def test_lib_validate_verbose(self, mock_cq_electronics):
        """lib validate with verbose context should show extra details."""
        from semicad.cli import cli

        runner = CliRunner()
        # Use full CLI invocation with --verbose flag before subcommand
        result = runner.invoke(cli, ["--verbose", "lib", "validate", "RPi3b"])

        assert result.exit_code == 0

    def test_lib_validate_not_found(self, mock_cq_electronics):
        """lib validate should error for unknown component."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["validate", "NonExistentComponent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestLibListCommand:
    """Test lib list CLI command."""

    def test_lib_list_shows_electronics(self, mock_cq_electronics):
        """lib list should show electronics components."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["list"])

        assert result.exit_code == 0
        assert "cq_electronics" in result.output

    def test_lib_list_filter_by_source(self, mock_cq_electronics):
        """lib list --source should filter by source."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["list", "-s", "cq_electronics"])

        assert result.exit_code == 0
        assert "cq_electronics" in result.output

    def test_lib_list_filter_by_category(self, mock_cq_electronics):
        """lib list --category should filter by category."""
        from semicad.cli.commands.library import lib

        runner = CliRunner()
        result = runner.invoke(lib, ["list", "-c", "board"])

        assert result.exit_code == 0
        # Should show board category components


class TestSearchCommand:
    """Test search CLI command."""

    def test_search_finds_components(self, mock_cq_electronics):
        """search should find components by name."""
        from semicad.cli.commands.library import search

        runner = CliRunner()
        result = runner.invoke(search, ["RPi"])

        assert result.exit_code == 0
        assert "RPi" in result.output

    def test_search_by_description(self, mock_cq_electronics):
        """search should find components by description."""
        from semicad.cli.commands.library import search

        runner = CliRunner()
        result = runner.invoke(search, ["Raspberry"])

        assert result.exit_code == 0

    def test_search_no_results(self, mock_cq_electronics):
        """search should handle no results gracefully."""
        from semicad.cli.commands.library import search

        runner = CliRunner()
        result = runner.invoke(search, ["xyznonexistent123"])

        assert result.exit_code == 0
        assert "No components found" in result.output


class TestRegistryGetWithValidation:
    """Test registry.get() with parameter validation (P2.6)."""

    def test_registry_get_propagates_validation_error(self, mock_cq_electronics):
        """registry.get() should propagate ParameterValidationError."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource, ParameterValidationError

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        with pytest.raises(ParameterValidationError):
            registry.get("PinHeader", rows="invalid")

    def test_registry_get_propagates_missing_required(self, mock_cq_electronics):
        """registry.get() should propagate ValueError for missing required."""
        from semicad.core.registry import ComponentRegistry
        from semicad.sources.electronics import ElectronicsSource

        registry = ComponentRegistry()
        registry.register_source(ElectronicsSource())

        with pytest.raises(ValueError) as exc_info:
            registry.get("BGA")

        assert "Missing required parameters" in str(exc_info.value)
