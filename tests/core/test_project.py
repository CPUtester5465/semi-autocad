"""Tests for semicad.core.project module."""

import pytest
from pathlib import Path

from semicad.core.project import Project, get_project, set_project


class TestProject:
    """Tests for Project dataclass."""

    def test_basic_creation(self, tmp_path):
        """Test creating a project with a path."""
        project = Project(root=tmp_path)

        assert project.root == tmp_path.resolve()
        assert project.name == tmp_path.name
        assert project.config == {}

    def test_explicit_name(self, tmp_path):
        """Test creating a project with an explicit name."""
        project = Project(root=tmp_path, name="my-project")

        assert project.name == "my-project"

    def test_root_path_resolved(self, tmp_path):
        """Test that root path is resolved to absolute."""
        # Create a relative path reference
        relative_path = tmp_path / "subdir"
        relative_path.mkdir()

        # Use a path string that isn't absolute
        project = Project(root=str(relative_path))

        assert project.root.is_absolute()
        assert project.root == relative_path.resolve()

    def test_load_config_from_partcad_yaml(self, tmp_path):
        """Test loading configuration from partcad.yaml."""
        config_file = tmp_path / "partcad.yaml"
        config_file.write_text("""
name: test-project
version: 1.0
dependencies:
  - package1
  - package2
""")

        project = Project(root=tmp_path)

        assert project.config["name"] == "test-project"
        assert project.config["version"] == 1.0
        assert len(project.config["dependencies"]) == 2

    def test_load_config_empty_file(self, tmp_path):
        """Test loading from an empty partcad.yaml."""
        config_file = tmp_path / "partcad.yaml"
        config_file.write_text("")

        project = Project(root=tmp_path)

        assert project.config == {}

    def test_load_config_no_file(self, tmp_path):
        """Test that missing config file results in empty config."""
        project = Project(root=tmp_path)

        assert project.config == {}


class TestProjectDirectories:
    """Tests for project directory properties."""

    @pytest.fixture
    def project(self, tmp_path):
        """Create a project for testing."""
        return Project(root=tmp_path)

    def test_scripts_dir(self, project, tmp_path):
        """Test scripts_dir property."""
        expected = tmp_path / "scripts"
        assert project.scripts_dir == expected

    def test_output_dir_creates_if_missing(self, project, tmp_path):
        """Test that output_dir creates the directory if it doesn't exist."""
        output = project.output_dir

        assert output.exists()
        assert output.is_dir()
        assert output == tmp_path / "output"

    def test_output_dir_exists(self, project, tmp_path):
        """Test output_dir when directory already exists."""
        (tmp_path / "output").mkdir()

        output = project.output_dir
        assert output.exists()

    def test_components_dir(self, project, tmp_path):
        """Test components_dir property."""
        expected = tmp_path / "components"
        assert project.components_dir == expected

    def test_projects_dir(self, project, tmp_path):
        """Test projects_dir property."""
        expected = tmp_path / "projects"
        assert project.projects_dir == expected


class TestSubprojects:
    """Tests for sub-project management."""

    @pytest.fixture
    def project_with_subprojects(self, tmp_path):
        """Create a project with sub-projects."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create sub-projects
        (projects_dir / "subproject1").mkdir()
        (projects_dir / "subproject2").mkdir()
        (projects_dir / ".hidden").mkdir()  # Should be ignored

        return Project(root=tmp_path)

    def test_list_subprojects(self, project_with_subprojects):
        """Test listing available sub-projects."""
        subprojects = project_with_subprojects.list_subprojects()

        assert len(subprojects) == 2
        assert "subproject1" in subprojects
        assert "subproject2" in subprojects
        assert ".hidden" not in subprojects

    def test_list_subprojects_no_projects_dir(self, tmp_path):
        """Test listing when projects directory doesn't exist."""
        project = Project(root=tmp_path)

        subprojects = project.list_subprojects()
        assert subprojects == []

    def test_get_subproject(self, project_with_subprojects):
        """Test getting a sub-project by name."""
        subproject = project_with_subprojects.get_subproject("subproject1")

        assert isinstance(subproject, Project)
        assert subproject.name == "subproject1"

    def test_get_subproject_not_found(self, project_with_subprojects):
        """Test getting a non-existent sub-project."""
        with pytest.raises(ValueError, match="Sub-project not found"):
            project_with_subprojects.get_subproject("nonexistent")

    def test_subproject_has_own_config(self, tmp_path):
        """Test that sub-projects can have their own configuration."""
        # Setup
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        subproject_dir = projects_dir / "sub1"
        subproject_dir.mkdir()

        # Add config to sub-project
        (subproject_dir / "partcad.yaml").write_text("variant: custom")

        project = Project(root=tmp_path)
        subproject = project.get_subproject("sub1")

        assert subproject.config.get("variant") == "custom"


class TestGlobalProjectContext:
    """Tests for global project context functions."""

    def setup_method(self):
        """Reset global state before each test."""
        import semicad.core.project as proj_module
        proj_module._current_project = None

    def test_get_project_creates_default(self, tmp_path, monkeypatch):
        """Test that get_project creates a project from cwd."""
        monkeypatch.chdir(tmp_path)

        project = get_project()

        assert project.root == tmp_path

    def test_get_project_with_path(self, tmp_path):
        """Test get_project with explicit path."""
        project = get_project(path=tmp_path)

        assert project.root == tmp_path

    def test_get_project_returns_cached(self, tmp_path):
        """Test that get_project returns the same instance."""
        project1 = get_project(path=tmp_path)
        project2 = get_project()

        assert project1 is project2

    def test_get_project_path_overrides_cached(self, tmp_path):
        """Test that providing a path creates a new project."""
        other_dir = tmp_path / "other"
        other_dir.mkdir()

        project1 = get_project(path=tmp_path)
        project2 = get_project(path=other_dir)

        assert project1 is not project2
        assert project2.root == other_dir

    def test_set_project(self, tmp_path):
        """Test setting the current project."""
        project = Project(root=tmp_path)
        set_project(project)

        current = get_project()
        assert current is project

    def test_get_project_with_string_path(self, tmp_path):
        """Test get_project with string path."""
        project = get_project(path=str(tmp_path))

        assert project.root == tmp_path


class TestProjectEdgeCases:
    """Tests for edge cases and error handling."""

    def test_project_with_nested_path(self, tmp_path):
        """Test project with deeply nested path."""
        deep_path = tmp_path / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)

        project = Project(root=deep_path)
        assert project.root == deep_path

    def test_project_preserves_symlinks(self, tmp_path):
        """Test that project resolves symlinks in path."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()

        link_dir = tmp_path / "link"
        try:
            link_dir.symlink_to(real_dir)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        project = Project(root=link_dir)
        # resolve() follows symlinks
        assert project.root == real_dir

    def test_unicode_project_name(self, tmp_path):
        """Test project with unicode characters in name."""
        unicode_dir = tmp_path / "项目_プロジェクト"
        unicode_dir.mkdir()

        project = Project(root=unicode_dir)
        assert project.name == "项目_プロジェクト"

    def test_config_with_complex_yaml(self, tmp_path):
        """Test loading complex YAML configuration."""
        config_file = tmp_path / "partcad.yaml"
        config_file.write_text("""
project:
  name: complex-project
  variants:
    standard:
      motor: 2207
      prop: 5x4.5
    racing:
      motor: 2306
      prop: 5x4.3
  dependencies:
    - name: fasteners
      version: ">=1.0"
""")

        project = Project(root=tmp_path)

        assert project.config["project"]["name"] == "complex-project"
        assert "standard" in project.config["project"]["variants"]
        assert project.config["project"]["variants"]["racing"]["motor"] == 2306
