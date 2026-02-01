"""
Custom exception hierarchy for semicad.

Provides specific exception types for different error conditions,
enabling better error handling and more informative error messages.

Exception Hierarchy:
    SemicadError (base)
    ├── ComponentError
    │   ├── ComponentNotFoundError
    │   ├── ComponentBuildError
    │   └── ParameterValidationError
    ├── SourceError
    │   ├── SourceNotAvailableError
    │   └── SourceInitializationError
    ├── ProjectError
    │   ├── ProjectNotFoundError
    │   └── ProjectConfigError
    └── ExportError
        └── ExportFormatError
"""

from typing import Any


class SemicadError(Exception):
    """Base exception for all semicad errors.

    Attributes:
        message: Human-readable error message.
        context: Optional dictionary with additional error context.
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with context if available."""
        if not self.context:
            return self.message
        context_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
        return f"{self.message} ({context_str})"


# =============================================================================
# Component Errors
# =============================================================================


class ComponentError(SemicadError):
    """Base exception for component-related errors."""

    pass


class ComponentNotFoundError(ComponentError):
    """Raised when a component cannot be found in any registered source.

    Attributes:
        component_name: The name of the component that was not found.
        searched_sources: List of source names that were searched.
    """

    def __init__(
        self,
        component_name: str,
        searched_sources: list[str] | None = None,
    ) -> None:
        self.component_name = component_name
        self.searched_sources = searched_sources or []
        context: dict[str, Any] = {"component": component_name}
        if searched_sources:
            context["searched_sources"] = searched_sources
        super().__init__(f"Component not found: {component_name}", context)


class ComponentBuildError(ComponentError):
    """Raised when a component fails to build its geometry.

    Attributes:
        component_name: The name of the component that failed to build.
        original_error: The underlying exception that caused the build failure.
    """

    def __init__(
        self,
        component_name: str,
        original_error: Exception | None = None,
    ) -> None:
        self.component_name = component_name
        self.original_error = original_error
        context: dict[str, Any] = {"component": component_name}
        if original_error:
            context["original_error"] = type(original_error).__name__
        message = f"Failed to build component: {component_name}"
        if original_error:
            message += f" - {original_error}"
        super().__init__(message, context)


class ParameterValidationError(ComponentError):
    """Raised when component parameters fail validation.

    Attributes:
        component_name: The name of the component.
        parameter_name: The name of the invalid parameter.
        parameter_value: The invalid value that was provided.
        valid_values: Optional list/description of valid values.
    """

    def __init__(
        self,
        component_name: str,
        parameter_name: str,
        parameter_value: Any,
        valid_values: list[Any] | str | None = None,
    ) -> None:
        self.component_name = component_name
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.valid_values = valid_values
        context = {
            "component": component_name,
            "parameter": parameter_name,
            "value": parameter_value,
        }
        if valid_values:
            context["valid_values"] = valid_values
        message = (
            f"Invalid parameter '{parameter_name}' for component '{component_name}': "
            f"got {parameter_value!r}"
        )
        if valid_values:
            if isinstance(valid_values, list):
                message += f", valid values: {valid_values}"
            else:
                message += f", {valid_values}"
        super().__init__(message, context)


# =============================================================================
# Source Errors
# =============================================================================


class SourceError(SemicadError):
    """Base exception for component source errors."""

    pass


class SourceNotAvailableError(SourceError):
    """Raised when a required source is not available.

    Attributes:
        source_name: The name of the unavailable source.
        required_package: The package that needs to be installed.
    """

    def __init__(
        self,
        source_name: str,
        required_package: str | None = None,
    ) -> None:
        self.source_name = source_name
        self.required_package = required_package
        context: dict[str, Any] = {"source": source_name}
        if required_package:
            context["required_package"] = required_package
        message = f"Source not available: {source_name}"
        if required_package:
            message += f". Install with: pip install {required_package}"
        super().__init__(message, context)


class SourceInitializationError(SourceError):
    """Raised when a source fails to initialize.

    Attributes:
        source_name: The name of the source that failed.
        original_error: The underlying exception.
    """

    def __init__(
        self,
        source_name: str,
        original_error: Exception | None = None,
    ) -> None:
        self.source_name = source_name
        self.original_error = original_error
        context: dict[str, Any] = {"source": source_name}
        if original_error:
            context["original_error"] = type(original_error).__name__
        message = f"Failed to initialize source: {source_name}"
        if original_error:
            message += f" - {original_error}"
        super().__init__(message, context)


# =============================================================================
# Project Errors
# =============================================================================


class ProjectError(SemicadError):
    """Base exception for project-related errors."""

    pass


class ProjectNotFoundError(ProjectError):
    """Raised when a project or sub-project cannot be found.

    Attributes:
        project_name: The name of the project.
        project_path: The path that was checked.
    """

    def __init__(
        self,
        project_name: str,
        project_path: str | None = None,
    ) -> None:
        self.project_name = project_name
        self.project_path = project_path
        context: dict[str, Any] = {"project": project_name}
        if project_path:
            context["path"] = project_path
        super().__init__(f"Project not found: {project_name}", context)


class ProjectConfigError(ProjectError):
    """Raised when project configuration is invalid.

    Attributes:
        project_name: The name of the project.
        config_file: The configuration file with issues.
        details: Description of the configuration problem.
    """

    def __init__(
        self,
        project_name: str,
        config_file: str,
        details: str,
    ) -> None:
        self.project_name = project_name
        self.config_file = config_file
        self.details = details
        context = {
            "project": project_name,
            "config_file": config_file,
        }
        super().__init__(f"Invalid project configuration: {details}", context)


# =============================================================================
# Export Errors
# =============================================================================


class ExportError(SemicadError):
    """Base exception for export-related errors."""

    pass


class ExportFormatError(ExportError):
    """Raised when export to a specific format fails.

    Attributes:
        format_name: The export format (e.g., "STEP", "STL").
        component_name: The component being exported.
        output_path: The target output path.
    """

    def __init__(
        self,
        format_name: str,
        component_name: str,
        output_path: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        self.format_name = format_name
        self.component_name = component_name
        self.output_path = output_path
        self.original_error = original_error
        context: dict[str, Any] = {
            "format": format_name,
            "component": component_name,
        }
        if output_path:
            context["output_path"] = output_path
        if original_error:
            context["original_error"] = type(original_error).__name__
        message = f"Failed to export '{component_name}' to {format_name}"
        if original_error:
            message += f": {original_error}"
        super().__init__(message, context)
