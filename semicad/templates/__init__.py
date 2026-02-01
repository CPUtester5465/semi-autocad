"""
Project Templates - Scaffolding for new sub-projects.

Provides templates for different project types:
- basic: Minimal project with simple geometry
- quadcopter: Drone/quadcopter frame project
- enclosure: Electronics enclosure/box project
"""

import re
from pathlib import Path
from string import Template
from typing import Any

import yaml

# Available templates
TEMPLATES = ["basic", "quadcopter", "enclosure"]


def validate_project_name(name: str) -> tuple[bool, str]:
    """
    Validate project name and return normalized version.

    Args:
        name: Project name to validate

    Returns:
        Tuple of (is_valid, error_message or normalized_name)
    """
    # Check for empty
    if not name:
        return False, "Project name cannot be empty"

    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name):
        return False, (
            f"Invalid project name '{name}'. "
            "Must start with a letter and contain only letters, numbers, hyphens, and underscores."
        )

    # Check length
    if len(name) > 50:
        return False, "Project name must be 50 characters or less"

    return True, name.lower()


def name_to_python_identifier(name: str) -> str:
    """Convert project name to valid Python identifier (for imports)."""
    return name.replace("-", "_").lower()


def name_to_class_name(name: str) -> str:
    """Convert project name to PascalCase class name."""
    parts = re.split(r'[-_]', name)
    return ''.join(part.capitalize() for part in parts)


def get_template(template_name: str) -> dict[str, str]:
    """
    Load a template by name.

    Args:
        template_name: One of 'basic', 'quadcopter', 'enclosure'

    Returns:
        Dictionary mapping filename to template content
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}. Available: {TEMPLATES}")

    if template_name == "basic":
        from semicad.templates.basic import TEMPLATE_FILES
    elif template_name == "quadcopter":
        from semicad.templates.quadcopter import TEMPLATE_FILES
    elif template_name == "enclosure":
        from semicad.templates.enclosure import TEMPLATE_FILES

    return TEMPLATE_FILES


def render_template(content: str, context: dict[str, Any]) -> str:
    """
    Render a template with the given context.

    Uses string.Template for safe substitution.

    Args:
        content: Template content with $variable placeholders
        context: Dictionary of variable values

    Returns:
        Rendered content
    """
    template = Template(content)
    return template.safe_substitute(context)


def _clean_yaml_config(config: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from config to avoid 'null' in YAML output."""
    return {k: v for k, v in config.items() if v is not None}


def update_root_partcad(project_root: Path, project_name: str) -> None:
    """
    Update root partcad.yaml to include the new sub-project as a dependency.

    Args:
        project_root: Root directory of the main project
        project_name: Name of the new sub-project
    """
    partcad_path = project_root / "partcad.yaml"

    # Load existing or create new
    if partcad_path.exists():
        with open(partcad_path) as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {
            "pythonVersion": ">=3.12",
            "partcad": ">=0.7.135",
        }

    # Ensure dependencies section exists
    if "dependencies" not in config:
        config["dependencies"] = {}

    # Add the new project as a local dependency
    config["dependencies"][project_name] = {
        "type": "local",
        "path": f"projects/{project_name}",
    }

    # Clean up None values and write back
    config = _clean_yaml_config(config)
    with open(partcad_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)


def remove_from_partcad(project_root: Path, project_name: str) -> bool:
    """
    Remove a sub-project dependency from root partcad.yaml.

    Args:
        project_root: Root directory of the main project
        project_name: Name of the sub-project to remove

    Returns:
        True if the entry was found and removed, False if not found
    """
    partcad_path = project_root / "partcad.yaml"

    if not partcad_path.exists():
        return False

    with open(partcad_path) as f:
        config = yaml.safe_load(f) or {}

    # Check if project exists in dependencies
    if "dependencies" not in config:
        return False

    if project_name not in config["dependencies"]:
        return False

    # Remove the dependency
    del config["dependencies"][project_name]

    # Clean up None values and write back
    config = _clean_yaml_config(config)
    with open(partcad_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

    return True


def remove_project(
    name: str,
    project_root: Path,
) -> tuple[bool, bool]:
    """
    Remove a sub-project completely.

    Args:
        name: Project name to remove
        project_root: Root directory of the main project

    Returns:
        Tuple of (directory_removed, partcad_entry_removed)

    Raises:
        ValueError: If project name is invalid
    """
    import shutil

    # Validate name
    is_valid, result = validate_project_name(name)
    if not is_valid:
        raise ValueError(result)

    normalized_name = result
    projects_dir = project_root / "projects"
    project_dir = projects_dir / normalized_name

    # Remove directory if it exists
    dir_removed = False
    if project_dir.exists():
        shutil.rmtree(project_dir)
        dir_removed = True

    # Remove from partcad.yaml
    partcad_removed = remove_from_partcad(project_root, normalized_name)

    return dir_removed, partcad_removed


def sync_partcad(project_root: Path) -> list[str]:
    """
    Remove stale entries from partcad.yaml that point to non-existent projects.

    Args:
        project_root: Root directory of the main project

    Returns:
        List of project names that were removed
    """
    partcad_path = project_root / "partcad.yaml"

    if not partcad_path.exists():
        return []

    with open(partcad_path) as f:
        config = yaml.safe_load(f) or {}

    if "dependencies" not in config:
        return []

    project_root / "projects"
    removed = []

    # Find local dependencies that point to non-existent directories
    to_remove = []
    for name, dep in config["dependencies"].items():
        if isinstance(dep, dict) and dep.get("type") == "local":
            dep_path = dep.get("path", "")
            if dep_path.startswith("projects/"):
                full_path = project_root / dep_path
                if not full_path.exists():
                    to_remove.append(name)

    # Remove stale entries
    for name in to_remove:
        del config["dependencies"][name]
        removed.append(name)

    if removed:
        config = _clean_yaml_config(config)
        with open(partcad_path, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

    return removed


def scaffold_project(
    name: str,
    template_name: str,
    project_root: Path,
    description: str = "",
) -> Path:
    """
    Scaffold a new sub-project from a template.

    Args:
        name: Project name (e.g., 'drone-7inch')
        template_name: Template to use ('basic', 'quadcopter', 'enclosure')
        project_root: Root directory of the main project
        description: Optional project description

    Returns:
        Path to the created project directory

    Raises:
        ValueError: If project name is invalid or project already exists
    """
    # Validate name
    is_valid, result = validate_project_name(name)
    if not is_valid:
        raise ValueError(result)

    normalized_name = result

    # Check if project already exists
    projects_dir = project_root / "projects"
    project_dir = projects_dir / normalized_name

    if project_dir.exists():
        raise ValueError(f"Project '{normalized_name}' already exists at {project_dir}")

    # Create projects directory if needed
    projects_dir.mkdir(exist_ok=True)

    # Load template
    template_files = get_template(template_name)

    # Build context for template substitution
    context = {
        "name": normalized_name,
        "name_underscore": name_to_python_identifier(normalized_name),
        "name_class": name_to_class_name(normalized_name),
        "description": description or f"A {template_name} project",
    }

    # Create project directory
    project_dir.mkdir()

    # Render and write each template file
    for filename, content in template_files.items():
        rendered = render_template(content, context)
        file_path = project_dir / filename
        with open(file_path, "w") as f:
            f.write(rendered)

    # Update root partcad.yaml
    update_root_partcad(project_root, normalized_name)

    return project_dir


__all__ = [
    "TEMPLATES",
    "get_template",
    "name_to_class_name",
    "name_to_python_identifier",
    "remove_from_partcad",
    "remove_project",
    "render_template",
    "scaffold_project",
    "sync_partcad",
    "update_root_partcad",
    "validate_project_name",
]
