"""
PartCAD source - Adapts PartCAD package manager to ComponentSource.

PartCAD is a package manager for CAD models providing access to:
- Standard fasteners (ISO/DIN standards)
- Mechanical components
- Electronic enclosures
- Community-contributed parts

Note: PartCAD CLI has compatibility issues with current Click version,
so we use the Python API exclusively.
"""

import logging
from collections.abc import Iterator
from typing import Any

import cadquery as cq

from semicad.core.component import Component, ComponentSpec
from semicad.core.registry import ComponentSource

logger = logging.getLogger(__name__)


# Default packages to index for component discovery
DEFAULT_PACKAGES = [
    "//pub/std/metric/cqwarehouse",
    "//pub/std/metric/m",
    "//pub/std/metric/nema",
    "//pub/std/imperial",
    "//pub/electromechanics",
    "//pub/electronics",
    "//pub/robotics",
]


def _normalize_path(path: str) -> str:
    """Normalize a PartCAD path to canonical form."""
    # Remove leading // if present, we'll add it back
    if path.startswith("//"):
        path = path[2:]
    return f"//{path}"


def _parse_part_path(path: str) -> tuple[str, str]:
    """
    Parse a PartCAD part path into package and part name.

    Args:
        path: Full path like "//pub/std/metric/cqwarehouse:fastener/iso4017"
              or short form like "pub/std/metric/cqwarehouse:fastener/iso4017"

    Returns:
        Tuple of (package_path, part_name)
    """
    path = _normalize_path(path)

    if ":" in path:
        package, part = path.rsplit(":", 1)
        return package, part

    # No colon - assume it's just a part name in root
    return "//", path


class PartCADComponent(Component):
    """Component backed by a PartCAD part."""

    def __init__(
        self,
        spec: ComponentSpec,
        partcad_path: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(spec)
        self._partcad_path = partcad_path
        self._params = params or {}
        self._context: Any = None

    def _get_context(self):
        """Lazy-load PartCAD context."""
        if self._context is None:
            import partcad
            self._context = partcad.init(".")
        return self._context

    def build(self) -> cq.Workplane:
        """Build CadQuery geometry from PartCAD part."""
        ctx = self._get_context()

        # Get the solid from PartCAD
        if self._params:
            solid = ctx.get_part_cadquery(self._partcad_path, self._params)
        else:
            solid = ctx.get_part_cadquery(self._partcad_path)

        # Wrap the Solid in a Workplane for semicad compatibility
        return cq.Workplane("XY").newObject([solid])

    @property
    def partcad_path(self) -> str:
        """Return the PartCAD path for this component."""
        return self._partcad_path

    @property
    def parameters(self) -> dict[str, Any]:
        """Return the parameters used for this component."""
        return self._params.copy()


class PartCADSource(ComponentSource):
    """
    Source for PartCAD package manager components.

    Provides access to the PartCAD public index containing:
    - Standard fasteners (bolts, screws, nuts)
    - Mechanical components (bearings, motors, servos)
    - Electronic components
    - Community-contributed parts

    Components are fetched on-demand and cached by PartCAD.
    First access may require network to clone package repositories.
    """

    def __init__(self, packages: list[str] | None = None) -> None:
        """
        Initialize PartCAD source.

        Args:
            packages: List of package paths to index. Defaults to common packages.
        """
        self._packages = packages or DEFAULT_PACKAGES
        self._context: Any = None
        self._indexed_parts: dict[str, dict[str, Any]] = {}  # path -> config
        self._initialized = False

    @property
    def name(self) -> str:
        return "partcad"

    def _get_context(self) -> Any:
        """Lazy-load PartCAD context."""
        if self._context is None:
            try:
                import partcad
                self._context = partcad.init(".")
            except Exception as e:
                logger.warning(f"Failed to initialize PartCAD context: {e}")
                raise
        return self._context

    def _ensure_indexed(self) -> None:
        """Index available parts from configured packages."""
        if self._initialized:
            return

        try:
            ctx = self._get_context()

            for package_path in self._packages:
                try:
                    project = ctx.get_project(package_path)
                    if project and hasattr(project, 'parts'):
                        for part_name, part_config in project.parts.items():
                            full_path = f"{package_path}:{part_name}"
                            self._indexed_parts[full_path] = {
                                "name": part_name,
                                "package": package_path,
                                "config": part_config if isinstance(part_config, dict) else {},
                            }
                except Exception as e:
                    logger.debug(f"Failed to index package {package_path}: {e}")
                    continue

            self._initialized = True

        except Exception as e:
            logger.warning(f"Failed to index PartCAD packages: {e}")
            self._initialized = True  # Don't retry on error

    def _get_category(self, part_name: str) -> str:
        """Infer category from part name."""
        part_lower = part_name.lower()

        if any(x in part_lower for x in ["fastener", "screw", "bolt", "nut"]):
            return "fastener"
        if any(x in part_lower for x in ["bearing", "bushing"]):
            return "bearing"
        if any(x in part_lower for x in ["motor", "servo", "stepper"]):
            return "motor"
        if any(x in part_lower for x in ["nema"]):
            return "motor"
        if any(x in part_lower for x in ["board", "pcb", "arduino", "raspberry"]):
            return "electronics"
        if any(x in part_lower for x in ["connector", "header", "socket"]):
            return "connector"

        return "other"

    def _get_description(self, part_name: str, config: dict[str, Any]) -> str:
        """Get description from part config or generate one."""
        if "desc" in config:
            return config["desc"]

        # Generate description from name
        name = part_name.replace("/", " - ").replace("-", " ").replace("_", " ")
        return name.title()

    def list_components(self) -> Iterator[ComponentSpec]:
        """Yield all available component specs from indexed packages."""
        self._ensure_indexed()

        for full_path, info in self._indexed_parts.items():
            part_name = info["name"]
            config = info.get("config", {})

            # Extract parameters if available
            params = {}
            if "parameters" in config:
                params = {
                    k: v.get("default")
                    for k, v in config["parameters"].items()
                    if isinstance(v, dict) and "default" in v
                }

            yield ComponentSpec(
                name=part_name,
                source=self.name,
                category=self._get_category(part_name),
                description=self._get_description(part_name, config),
                params=params,
                metadata={
                    "partcad_path": full_path,
                    "package": info["package"],
                    "parameters": config.get("parameters", {}),
                },
            )

    def get_component(self, name: str, **params: Any) -> Component:
        """
        Get a PartCAD component by name or path.

        Args:
            name: Part name or full PartCAD path
            **params: Parameters for parametric parts (e.g., size="M3-0.5", length=10)

        Returns:
            Component instance

        Raises:
            KeyError: If component not found
            ValueError: If required parameters are missing
        """
        self._ensure_indexed()

        # First, check if name is a full path
        full_path = None
        part_config = {}

        if ":" in name or name.startswith("//"):
            # Full path provided
            normalized = _normalize_path(name)
            if ":" not in normalized:
                # Just package path, not valid for get_component
                raise KeyError(f"Invalid PartCAD path (missing part name): {name}")
            full_path = normalized

            # Try to get config from index
            if full_path in self._indexed_parts:
                part_config = self._indexed_parts[full_path].get("config", {})
        else:
            # Short name - search in indexed parts
            for path, info in self._indexed_parts.items():
                if info["name"] == name or info["name"].endswith(f"/{name}"):
                    full_path = path
                    part_config = info.get("config", {})
                    break

        if full_path is None:
            raise KeyError(f"Component not found in PartCAD: {name}")

        # Verify the part exists by trying to get it
        try:
            ctx = self._get_context()
            part = ctx.get_part(full_path)
            if part is None:
                raise KeyError(f"PartCAD returned None for: {full_path}")
        except Exception as e:
            raise KeyError(f"Failed to load PartCAD part {full_path}: {e}") from e

        # Build the spec
        package, part_name = _parse_part_path(full_path)

        spec = ComponentSpec(
            name=part_name,
            source=self.name,
            category=self._get_category(part_name),
            description=self._get_description(part_name, part_config),
            params=params,
            metadata={
                "partcad_path": full_path,
                "package": package,
                "parameters": part_config.get("parameters", {}),
            },
        )

        return PartCADComponent(spec, full_path, params if params else None)

    def search(self, query: str) -> Iterator[ComponentSpec]:
        """Search components by name or description."""
        self._ensure_indexed()

        query_lower = query.lower()

        for spec in self.list_components():
            if (query_lower in spec.name.lower() or
                query_lower in spec.description.lower() or
                (spec.metadata and query_lower in spec.metadata.get("partcad_path", "").lower())):
                yield spec

    def list_packages(self) -> list[str]:
        """List available top-level packages."""
        try:
            ctx = self._get_context()
            pub = ctx.get_project("//pub")
            if pub:
                return pub.get_child_project_names()
        except Exception as e:
            logger.debug(f"Failed to list packages: {e}")
        return []

    def list_parts_in_package(self, package_path: str) -> list[str]:
        """List parts in a specific package."""
        try:
            ctx = self._get_context()
            package_path = _normalize_path(package_path)
            project = ctx.get_project(package_path)
            if project and hasattr(project, 'parts'):
                return list(project.parts.keys())
        except Exception as e:
            logger.debug(f"Failed to list parts in {package_path}: {e}")
        return []

    def get_part_info(self, path: str) -> dict[str, Any]:
        """
        Get detailed information about a part.

        Args:
            path: Full PartCAD path or short name

        Returns:
            Dictionary with part metadata including parameters, description, etc.
        """
        self._ensure_indexed()

        # Normalize path
        if ":" in path or path.startswith("//"):
            full_path = _normalize_path(path)
        else:
            # Search for short name
            full_path = None
            for p, info in self._indexed_parts.items():
                if info["name"] == path or info["name"].endswith(f"/{path}"):
                    full_path = p
                    break

            if full_path is None:
                raise KeyError(f"Part not found: {path}")

        try:
            ctx = self._get_context()
            part = ctx.get_part(full_path)
            if part is None:
                raise KeyError(f"Part not found: {full_path}")

            config = part.config if hasattr(part, 'config') else {}

            return {
                "path": full_path,
                "name": config.get("name", full_path.split(":")[-1]),
                "type": config.get("type", "unknown"),
                "description": config.get("desc", ""),
                "parameters": config.get("parameters", {}),
                "aliases": config.get("aliases", []),
                "manufacturable": config.get("manufacturable", False),
            }
        except Exception as e:
            raise KeyError(f"Failed to get part info for {path}: {e}") from e

    def get_available_sizes(self, path: str, param_name: str = "size") -> list[str]:
        """
        Get available sizes/options for a parametric part.

        Args:
            path: PartCAD path
            param_name: Parameter name to get options for (default: "size")

        Returns:
            List of available values for the parameter
        """
        info = self.get_part_info(path)
        params = info.get("parameters", {})

        if param_name in params:
            param = params[param_name]
            if isinstance(param, dict):
                if "enum" in param:
                    return param["enum"]
                elif "min" in param and "max" in param:
                    return [f"{param['min']} to {param['max']}"]

        return []
