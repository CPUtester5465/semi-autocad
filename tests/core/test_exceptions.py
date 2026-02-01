"""Tests for semicad.core.exceptions module."""

import pytest

from semicad.core.exceptions import (
    SemicadError,
    ComponentError,
    ComponentNotFoundError,
    ComponentBuildError,
    ParameterValidationError,
    SourceError,
    SourceNotAvailableError,
    SourceInitializationError,
    ProjectError,
    ProjectNotFoundError,
    ProjectConfigError,
    ExportError,
    ExportFormatError,
)


class TestSemicadError:
    """Tests for base SemicadError."""

    def test_basic_message(self):
        """Test basic error creation."""
        error = SemicadError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.context == {}

    def test_with_context(self):
        """Test error with context dictionary."""
        error = SemicadError(
            "Operation failed",
            context={"operation": "build", "component": "test"}
        )

        assert "operation='build'" in str(error)
        assert "component='test'" in str(error)
        assert error.context["operation"] == "build"

    def test_exception_inheritance(self):
        """Test that SemicadError is an Exception."""
        error = SemicadError("test")
        assert isinstance(error, Exception)


class TestComponentErrors:
    """Tests for component-related exceptions."""

    def test_component_not_found_basic(self):
        """Test ComponentNotFoundError with just a name."""
        error = ComponentNotFoundError("motor_2207")

        assert error.component_name == "motor_2207"
        assert "motor_2207" in str(error)
        assert isinstance(error, ComponentError)
        assert isinstance(error, SemicadError)

    def test_component_not_found_with_sources(self):
        """Test ComponentNotFoundError with searched sources."""
        error = ComponentNotFoundError(
            "motor_2207",
            searched_sources=["custom", "warehouse", "electronics"]
        )

        assert error.searched_sources == ["custom", "warehouse", "electronics"]
        assert error.context["searched_sources"] == ["custom", "warehouse", "electronics"]

    def test_component_build_error_basic(self):
        """Test ComponentBuildError with just a name."""
        error = ComponentBuildError("broken_part")

        assert error.component_name == "broken_part"
        assert error.original_error is None
        assert "broken_part" in str(error)

    def test_component_build_error_with_cause(self):
        """Test ComponentBuildError with original error."""
        original = ValueError("Invalid geometry")
        error = ComponentBuildError("broken_part", original_error=original)

        assert error.original_error is original
        assert "ValueError" in error.context["original_error"]
        assert "Invalid geometry" in str(error)

    def test_parameter_validation_error_basic(self):
        """Test ParameterValidationError with required fields."""
        error = ParameterValidationError(
            component_name="screw",
            parameter_name="size",
            parameter_value="invalid"
        )

        assert error.component_name == "screw"
        assert error.parameter_name == "size"
        assert error.parameter_value == "invalid"
        assert "size" in str(error)
        assert "screw" in str(error)
        assert "invalid" in str(error)

    def test_parameter_validation_error_with_valid_values_list(self):
        """Test ParameterValidationError with list of valid values."""
        error = ParameterValidationError(
            component_name="screw",
            parameter_name="size",
            parameter_value="M99",
            valid_values=["M3", "M4", "M5", "M6"]
        )

        assert error.valid_values == ["M3", "M4", "M5", "M6"]
        assert "M3" in str(error)

    def test_parameter_validation_error_with_valid_values_string(self):
        """Test ParameterValidationError with string description."""
        error = ParameterValidationError(
            component_name="motor",
            parameter_name="power",
            parameter_value=-100,
            valid_values="must be positive"
        )

        assert "must be positive" in str(error)


class TestSourceErrors:
    """Tests for source-related exceptions."""

    def test_source_not_available_basic(self):
        """Test SourceNotAvailableError with just name."""
        error = SourceNotAvailableError("cq_warehouse")

        assert error.source_name == "cq_warehouse"
        assert "cq_warehouse" in str(error)
        assert isinstance(error, SourceError)

    def test_source_not_available_with_package(self):
        """Test SourceNotAvailableError with required package."""
        error = SourceNotAvailableError(
            "electronics",
            required_package="cq-electronics>=0.2.0"
        )

        assert error.required_package == "cq-electronics>=0.2.0"
        assert "pip install" in str(error)
        assert "cq-electronics>=0.2.0" in str(error)

    def test_source_initialization_error_basic(self):
        """Test SourceInitializationError with just name."""
        error = SourceInitializationError("partcad")

        assert error.source_name == "partcad"
        assert error.original_error is None

    def test_source_initialization_error_with_cause(self):
        """Test SourceInitializationError with original error."""
        original = RuntimeError("Failed to connect")
        error = SourceInitializationError("partcad", original_error=original)

        assert error.original_error is original
        assert "Failed to connect" in str(error)


class TestProjectErrors:
    """Tests for project-related exceptions."""

    def test_project_not_found_basic(self):
        """Test ProjectNotFoundError with just name."""
        error = ProjectNotFoundError("quadcopter")

        assert error.project_name == "quadcopter"
        assert "quadcopter" in str(error)
        assert isinstance(error, ProjectError)

    def test_project_not_found_with_path(self):
        """Test ProjectNotFoundError with path."""
        error = ProjectNotFoundError(
            "quadcopter",
            project_path="/home/user/projects/quadcopter"
        )

        assert error.project_path == "/home/user/projects/quadcopter"
        assert error.context["path"] == "/home/user/projects/quadcopter"

    def test_project_config_error(self):
        """Test ProjectConfigError."""
        error = ProjectConfigError(
            project_name="broken-project",
            config_file="partcad.yaml",
            details="Invalid YAML syntax at line 5"
        )

        assert error.project_name == "broken-project"
        assert error.config_file == "partcad.yaml"
        assert error.details == "Invalid YAML syntax at line 5"
        assert "Invalid YAML syntax" in str(error)


class TestExportErrors:
    """Tests for export-related exceptions."""

    def test_export_format_error_basic(self):
        """Test ExportFormatError with required fields."""
        error = ExportFormatError(
            format_name="STEP",
            component_name="broken_part"
        )

        assert error.format_name == "STEP"
        assert error.component_name == "broken_part"
        assert "STEP" in str(error)
        assert "broken_part" in str(error)
        assert isinstance(error, ExportError)

    def test_export_format_error_with_path(self):
        """Test ExportFormatError with output path."""
        error = ExportFormatError(
            format_name="STL",
            component_name="part",
            output_path="/tmp/output/part.stl"
        )

        assert error.output_path == "/tmp/output/part.stl"
        assert error.context["output_path"] == "/tmp/output/part.stl"

    def test_export_format_error_with_cause(self):
        """Test ExportFormatError with original error."""
        original = IOError("Disk full")
        error = ExportFormatError(
            format_name="STEP",
            component_name="large_part",
            original_error=original
        )

        assert error.original_error is original
        assert "Disk full" in str(error)


class TestExceptionHierarchy:
    """Tests for exception hierarchy and isinstance checks."""

    def test_all_exceptions_inherit_from_semicad_error(self):
        """Test that all custom exceptions inherit from SemicadError."""
        exceptions = [
            ComponentError("test"),
            ComponentNotFoundError("test"),
            ComponentBuildError("test"),
            ParameterValidationError("comp", "param", "val"),
            SourceError("test"),
            SourceNotAvailableError("test"),
            SourceInitializationError("test"),
            ProjectError("test"),
            ProjectNotFoundError("test"),
            ProjectConfigError("proj", "file", "details"),
            ExportError("test"),
            ExportFormatError("fmt", "comp"),
        ]

        for exc in exceptions:
            assert isinstance(exc, SemicadError), f"{type(exc).__name__} should inherit from SemicadError"

    def test_component_errors_catchable_by_parent(self):
        """Test that component errors can be caught by ComponentError."""
        errors = [
            ComponentNotFoundError("test"),
            ComponentBuildError("test"),
            ParameterValidationError("comp", "param", "val"),
        ]

        for error in errors:
            try:
                raise error
            except ComponentError:
                pass  # Should be caught
            except Exception:
                pytest.fail(f"{type(error).__name__} not caught by ComponentError")

    def test_exception_chaining(self):
        """Test that exceptions can be chained with 'from'."""
        try:
            try:
                raise ValueError("original error")
            except ValueError as e:
                raise ComponentBuildError("part", original_error=e) from e
        except ComponentBuildError as error:
            assert error.__cause__ is not None
            assert isinstance(error.__cause__, ValueError)
