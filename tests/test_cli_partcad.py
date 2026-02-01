"""CLI tests for PartCAD commands.

Tests cover:
- partcad search command
- partcad list command
- partcad info command
- partcad sizes command
- partcad render command
- partcad install command
- JSON output format
- Error handling
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from semicad.cli import cli


# The module path where PartCADSource is imported in the CLI
PARTCAD_SOURCE_PATH = "semicad.sources.partcad_source.PartCADSource"


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_partcad_source():
    """Mock PartCADSource for CLI tests."""
    from semicad.core.component import ComponentSpec

    mock_source = MagicMock()
    mock_source.name = "partcad"

    # Setup search results
    mock_source.search.return_value = iter([
        ComponentSpec(
            name="fastener/hex_bolt",
            source="partcad",
            category="fastener",
            description="Hex head bolt",
            metadata={"partcad_path": "//pub/test:fastener/hex_bolt"},
        )
    ])

    # Setup list_packages
    mock_source.list_packages.return_value = ["//pub/std", "//pub/electromechanics"]

    # Setup list_parts_in_package
    mock_source.list_parts_in_package.return_value = ["fastener/bolt", "fastener/nut"]

    # Setup get_part_info
    mock_source.get_part_info.return_value = {
        "path": "//pub/test:bolt",
        "name": "bolt",
        "type": "cadquery",
        "description": "Test bolt",
        "parameters": {
            "size": {"type": "string", "enum": ["M3", "M4", "M5"], "default": "M3"},
            "length": {"type": "int", "default": 10},
        },
        "aliases": [],
        "manufacturable": True,
    }

    # Setup get_available_sizes
    mock_source.get_available_sizes.return_value = ["M3", "M4", "M5"]

    return mock_source


class TestPartCADHelp:
    """Test help output for partcad commands."""

    def test_partcad_help(self, runner):
        """partcad --help should show available commands."""
        result = runner.invoke(cli, ["partcad", "--help"])

        assert result.exit_code == 0
        assert "search" in result.output
        assert "list" in result.output
        assert "info" in result.output
        assert "sizes" in result.output
        assert "render" in result.output
        assert "install" in result.output

    def test_search_help(self, runner):
        """partcad search --help should show options."""
        result = runner.invoke(cli, ["partcad", "search", "--help"])

        assert result.exit_code == 0
        assert "QUERY" in result.output
        assert "--limit" in result.output

    def test_list_help(self, runner):
        """partcad list --help should show options."""
        result = runner.invoke(cli, ["partcad", "list", "--help"])

        assert result.exit_code == 0
        assert "PACKAGE" in result.output

    def test_info_help(self, runner):
        """partcad info --help should show options."""
        result = runner.invoke(cli, ["partcad", "info", "--help"])

        assert result.exit_code == 0
        assert "PATH" in result.output

    def test_sizes_help(self, runner):
        """partcad sizes --help should show options."""
        result = runner.invoke(cli, ["partcad", "sizes", "--help"])

        assert result.exit_code == 0
        assert "PATH" in result.output
        assert "--param" in result.output

    def test_render_help(self, runner):
        """partcad render --help should show options."""
        result = runner.invoke(cli, ["partcad", "render", "--help"])

        assert result.exit_code == 0
        assert "PATH" in result.output
        assert "--output" in result.output
        assert "--format" in result.output
        assert "--size" in result.output


class TestSearchCommand:
    """Test partcad search command."""

    def test_search_basic(self, runner, mock_partcad_source):
        """search should find matching parts."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["partcad", "search", "bolt"])

            assert result.exit_code == 0
            assert "hex_bolt" in result.output or "Found" in result.output

    def test_search_json_output(self, runner, mock_partcad_source):
        """search with --json should output JSON."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["--json", "partcad", "search", "bolt"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "query" in data
            assert "results" in data

    def test_search_with_limit(self, runner, mock_partcad_source):
        """search with --limit should limit results."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["partcad", "search", "bolt", "--limit", "5"])

            assert result.exit_code == 0


class TestListCommand:
    """Test partcad list command."""

    def test_list_packages(self, runner, mock_partcad_source):
        """list without argument should show packages."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["partcad", "list"])

            assert result.exit_code == 0
            assert "//pub/std" in result.output or "packages" in result.output.lower()

    def test_list_parts_in_package(self, runner, mock_partcad_source):
        """list with package should show parts."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["partcad", "list", "//pub/test"])

            assert result.exit_code == 0

    def test_list_json_output(self, runner, mock_partcad_source):
        """list with --json should output JSON."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["--json", "partcad", "list"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "packages" in data


class TestInfoCommand:
    """Test partcad info command."""

    def test_info_basic(self, runner, mock_partcad_source):
        """info should show part details."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["partcad", "info", "//pub/test:bolt"])

            assert result.exit_code == 0
            assert "bolt" in result.output or "Part" in result.output

    def test_info_json_output(self, runner, mock_partcad_source):
        """info with --json should output JSON."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["--json", "partcad", "info", "//pub/test:bolt"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "path" in data
            assert "parameters" in data


class TestSizesCommand:
    """Test partcad sizes command."""

    def test_sizes_basic(self, runner, mock_partcad_source):
        """sizes should show available options."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["partcad", "sizes", "//pub/test:bolt"])

            assert result.exit_code == 0
            assert "M3" in result.output or "Available" in result.output

    def test_sizes_custom_param(self, runner, mock_partcad_source):
        """sizes with --param should show that parameter's options."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["partcad", "sizes", "//pub/test:bolt", "--param", "length"])

            assert result.exit_code == 0

    def test_sizes_json_output(self, runner, mock_partcad_source):
        """sizes with --json should output JSON."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["--json", "partcad", "sizes", "//pub/test:bolt"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "values" in data


class TestRenderCommand:
    """Test partcad render command."""

    def test_render_help_shows_formats(self, runner):
        """render help should show supported formats."""
        result = runner.invoke(cli, ["partcad", "render", "--help"])

        assert result.exit_code == 0
        assert "png" in result.output
        assert "stl" in result.output
        assert "step" in result.output


class TestInstallCommand:
    """Test partcad install command."""

    def test_install_help(self, runner):
        """install help should show usage."""
        result = runner.invoke(cli, ["partcad", "install", "--help"])

        assert result.exit_code == 0
        assert "PACKAGE" in result.output


class TestErrorHandling:
    """Test error handling in CLI commands."""

    def test_search_import_error(self, runner):
        """search should handle missing PartCAD gracefully."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.side_effect = ImportError("PartCAD not installed")

            result = runner.invoke(cli, ["partcad", "search", "bolt"])

            assert result.exit_code != 0
            assert "not available" in result.output.lower() or "error" in result.output.lower()

    def test_info_not_found(self, runner, mock_partcad_source):
        """info should handle missing part gracefully."""
        mock_partcad_source.get_part_info.side_effect = KeyError("Part not found")

        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["partcad", "info", "nonexistent"])

            assert result.exit_code != 0


class TestVerboseOutput:
    """Test verbose output mode."""

    def test_search_verbose(self, runner, mock_partcad_source):
        """search with --verbose should show debug info."""
        with patch(PARTCAD_SOURCE_PATH) as MockSource:
            MockSource.return_value = mock_partcad_source

            result = runner.invoke(cli, ["--verbose", "partcad", "search", "bolt"])

            # Verbose output should include debug messages
            assert result.exit_code == 0
