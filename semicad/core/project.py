"""
Project context - Single Responsibility: Manage project state and paths.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


@dataclass
class Project:
    """
    Represents a Semi-AutoCAD project context.

    Manages paths, configuration, and project-specific settings.
    """

    root: Path
    name: str = ""
    config: dict = field(default_factory=dict)

    def __post_init__(self):
        self.root = Path(self.root).resolve()
        if not self.name:
            self.name = self.root.name
        self._load_config()

    def _load_config(self) -> None:
        """Load project configuration from partcad.yaml or pyproject.toml."""
        partcad_file = self.root / "partcad.yaml"
        if partcad_file.exists():
            with open(partcad_file) as f:
                self.config = yaml.safe_load(f) or {}

    @property
    def scripts_dir(self) -> Path:
        return self.root / "scripts"

    @property
    def output_dir(self) -> Path:
        path = self.root / "output"
        path.mkdir(exist_ok=True)
        return path

    @property
    def components_dir(self) -> Path:
        return self.root / "components"

    @property
    def projects_dir(self) -> Path:
        """Directory for sub-projects."""
        return self.root / "projects"

    def get_subproject(self, name: str) -> "Project":
        """Get a sub-project by name."""
        subproject_path = self.projects_dir / name
        if not subproject_path.exists():
            raise ValueError(f"Sub-project not found: {name}")
        return Project(subproject_path)

    def list_subprojects(self) -> list[str]:
        """List available sub-projects."""
        if not self.projects_dir.exists():
            return []
        return [
            p.name for p in self.projects_dir.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        ]


# Global project context
_current_project: Project | None = None


def get_project(path: Path | str | None = None) -> Project:
    """Get or create the current project context."""
    global _current_project

    if path:
        _current_project = Project(Path(path))
    elif _current_project is None:
        # Default to current directory or find project root
        _current_project = Project(Path.cwd())

    return _current_project


def set_project(project: Project) -> None:
    """Set the current project context."""
    global _current_project
    _current_project = project
