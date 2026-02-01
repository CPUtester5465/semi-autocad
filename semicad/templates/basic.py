"""
Basic Project Template - Minimal project structure.

A simple starting point for custom CAD projects.
"""

TEMPLATE_FILES = {
    "partcad.yaml": '''# $name Project
# $description

name: $name
desc: $description
version: "0.1.0"

# Build configuration
config:
  width: 100          # mm
  height: 50          # mm
  depth: 30           # mm
  thickness: 3        # mm

# Parts defined in this project
parts:
  main:
    type: cadquery
    path: frame.py
    desc: Main part geometry

# Assembly
assemblies:
  full_assembly:
    type: assy
    path: assembly.assy
    desc: Complete assembly
''',

    "config.py": '''"""
$name_class Configuration

Central configuration for the $name project.
"""

from dataclasses import dataclass


@dataclass
class Config:
    """Configuration parameters for the project."""

    # Geometry
    width: float = 100.0       # mm
    height: float = 50.0       # mm
    depth: float = 30.0        # mm
    thickness: float = 3.0     # mm

    # Features
    fillet_radius: float = 2.0  # mm, edge fillet


# Default configuration
CONFIG = Config()

# Preset configurations (variants)
PRESETS = {
    "default": Config(),
    "small": Config(
        width=50,
        height=25,
        depth=15,
    ),
    "large": Config(
        width=200,
        height=100,
        depth=60,
        thickness=5,
    ),
}
''',

    "frame.py": '''#!/usr/bin/env python3
"""
$name_class Main Geometry

Generates the main part geometry.

Usage:
    python frame.py              # Export STEP/STL
    cq-editor frame.py           # Interactive view
"""

import cadquery as cq
from pathlib import Path

# Import config
try:
    from config import CONFIG, Config
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import CONFIG, Config


def generate_part(config: Config = CONFIG) -> cq.Workplane:
    """
    Generate the main part geometry.

    Args:
        config: Config with geometry parameters

    Returns:
        CadQuery Workplane with part geometry
    """
    # Create base box
    part = (
        cq.Workplane("XY")
        .box(config.width, config.height, config.depth)
        .edges("|Z")
        .fillet(config.fillet_radius)
    )

    return part


def export_part(output_dir: Path, config: Config = CONFIG, quality: str = "normal"):
    """Export part to STEP and STL using semicad.export module.

    Args:
        output_dir: Directory for output files
        config: Configuration parameters
        quality: STL quality preset (draft, normal, fine, ultra)
    """
    from semicad.export import export_step, export_stl, STLQuality

    part = generate_part(config)

    quality_map = {
        "draft": STLQuality.DRAFT,
        "normal": STLQuality.NORMAL,
        "fine": STLQuality.FINE,
        "ultra": STLQuality.ULTRA,
    }
    stl_quality = quality_map.get(quality, STLQuality.NORMAL)

    step_path = output_dir / "part.step"
    stl_path = output_dir / "part.stl"

    export_step(part, step_path)
    export_stl(part, stl_path, quality=stl_quality)

    print(f"Exported: {step_path}")
    print(f"Exported: {stl_path} (quality: {quality})")

    return part


# === Main / cq-editor ===

# Generate part for visualization
_part = generate_part(CONFIG)

# For cq-editor: show_object is only available in cq-editor context
try:
    show_object(_part, name="Part", options={"color": "steelblue"})
except NameError:
    pass  # Not running in cq-editor

# CLI execution
if __name__ == "__main__":
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    print(f"Generating $name part...")
    print(f"  Width: {CONFIG.width}mm")
    print(f"  Height: {CONFIG.height}mm")
    print(f"  Depth: {CONFIG.depth}mm")

    export_part(output_dir, CONFIG)
''',

    "assembly.py": '''#!/usr/bin/env python3
"""
$name_class Assembly

Positions all components together.

Usage:
    python assembly.py           # Export full assembly
    cq-editor assembly.py        # Interactive visualization
"""

import cadquery as cq
from pathlib import Path
from dataclasses import dataclass

# Add paths for imports
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG, Config
from frame import generate_part


@dataclass
class PositionedComponent:
    """A component with its position in the assembly."""
    name: str
    model: cq.Workplane
    position: tuple[float, float, float]
    color: str = "gray"

    @property
    def positioned(self) -> cq.Workplane:
        """Return the model translated to its position."""
        return self.model.translate(self.position)


class Assembly:
    """
    Complete assembly manager.

    Handles component positioning and export.
    """

    def __init__(self, config: Config = CONFIG):
        self.config = config
        self.components: list[PositionedComponent] = []

    def add_main_part(self) -> "Assembly":
        """Add the main part."""
        part = generate_part(self.config)
        self.components.append(PositionedComponent(
            name="main_part",
            model=part,
            position=(0, 0, 0),
            color="steelblue",
        ))
        return self

    def build_full(self) -> "Assembly":
        """Build complete assembly with all components."""
        return self.add_main_part()

    def get_combined(self) -> cq.Workplane:
        """Combine all components into single geometry."""
        if not self.components:
            raise ValueError("No components in assembly")

        combined = self.components[0].positioned
        for comp in self.components[1:]:
            combined = combined.union(comp.positioned)
        return combined

    def export(self, output_dir: Path, quality: str = "normal"):
        """Export assembly to files using semicad.export module.

        Args:
            output_dir: Directory for output files
            quality: STL quality preset (draft, normal, fine, ultra)
        """
        from semicad.export import export_step, export_stl, STLQuality

        output_dir.mkdir(exist_ok=True)

        quality_map = {
            "draft": STLQuality.DRAFT,
            "normal": STLQuality.NORMAL,
            "fine": STLQuality.FINE,
            "ultra": STLQuality.ULTRA,
        }
        stl_quality = quality_map.get(quality, STLQuality.NORMAL)

        combined = self.get_combined()

        export_step(combined, output_dir / "assembly.step")
        export_stl(combined, output_dir / "assembly.stl", quality=stl_quality)

        print(f"Exported to {output_dir} (quality: {quality})")


def create_assembly(config: Config = CONFIG) -> Assembly:
    """Factory function to create full assembly."""
    return Assembly(config).build_full()


# === Main / cq-editor ===

# Create assembly for visualization
_assembly = create_assembly()

# For cq-editor: show components
try:
    for comp in _assembly.components:
        show_object(
            comp.positioned,
            name=comp.name,
            options={"color": comp.color}
        )
except NameError:
    pass  # Not running in cq-editor

# CLI execution
if __name__ == "__main__":
    output_dir = Path(__file__).parent / "output"

    print("Building $name_class Assembly")
    print("=" * 40)
    print(f"Width: {CONFIG.width}mm")
    print(f"Height: {CONFIG.height}mm")
    print(f"Depth: {CONFIG.depth}mm")
    print()

    _assembly.export(output_dir)

    print("\\nTo visualize:")
    print(f"  cq-editor {__file__}")
''',

    "build.py": '''#!/usr/bin/env python3
"""
$name_class Build Script

Generates all output files for manufacturing and visualization.

Outputs:
- part.step / part.stl      - Main part (for CNC/3D print)
- assembly.step / assembly.stl - Full assembly
- bom.csv                    - Bill of materials

Usage:
    python build.py
    python build.py --variant small
    python build.py --quality fine
    python build.py --export-all
"""

import argparse
from pathlib import Path
import sys

# Setup paths
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(project_dir.parent.parent))
sys.path.insert(0, str(project_dir.parent.parent / "scripts"))

from config import CONFIG, PRESETS, Config
from frame import generate_part, export_part
from assembly import create_assembly


def generate_bom(config: Config, output_dir: Path):
    """Generate bill of materials using semicad.export module."""
    from semicad.export import BOM, BOMEntry, export_bom

    bom = BOM(
        title="$name Bill of Materials",
        entries=[
            BOMEntry(
                name="Main Part",
                quantity=1,
                category="structure",
                source="custom",
                description=f"{config.width}x{config.height}x{config.depth}mm",
                params=f"thickness={config.thickness}mm",
            ),
        ],
        notes=f"Generated for $name project",
    )

    # Export in multiple formats
    export_bom(bom, output_dir / "bom.csv")
    export_bom(bom, output_dir / "bom.json")

    print(f"Exported: {output_dir / 'bom.csv'}")
    print(f"Exported: {output_dir / 'bom.json'}")

    return bom


def build_project(
    variant: str = "default",
    output_dir: Path | None = None,
    export_all: bool = False,
    quality: str = "normal",
):
    """
    Build all project outputs.

    Args:
        variant: Configuration preset name
        output_dir: Output directory (default: project/output)
        export_all: Export all variants
        quality: STL mesh quality (draft, normal, fine, ultra)
    """
    if output_dir is None:
        output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)

    if export_all:
        for name, config in PRESETS.items():
            print(f"\\n{'='*50}")
            print(f"Building variant: {name}")
            print(f"{'='*50}")
            variant_dir = output_dir / name
            variant_dir.mkdir(exist_ok=True)
            _build_variant(config, variant_dir, name, quality)
    else:
        config = PRESETS.get(variant, CONFIG)
        _build_variant(config, output_dir, variant, quality)


def _build_variant(config: Config, output_dir: Path, name: str, quality: str):
    """Build a single variant."""
    print(f"\\nConfiguration:")
    print(f"  Width: {config.width}mm")
    print(f"  Height: {config.height}mm")
    print(f"  Depth: {config.depth}mm")
    print(f"  Quality: {quality}")

    # Generate part
    print("\\nGenerating part...")
    export_part(output_dir, config, quality=quality)

    # Generate assembly
    print("\\nGenerating assembly...")
    assembly = create_assembly(config)
    assembly.export(output_dir, quality=quality)

    # Generate BOM
    print("\\nGenerating BOM...")
    generate_bom(config, output_dir)

    # Summary
    print(f"\\n{'='*50}")
    print(f"Build complete: {name}")
    print(f"Output: {output_dir}")
    print(f"{'='*50}")

    # List output files
    print("\\nOutput files:")
    for f in sorted(output_dir.glob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"  {f.name:25} {size:>10,} bytes")


def main():
    parser = argparse.ArgumentParser(description="Build $name project")
    parser.add_argument(
        "--variant", "-v",
        choices=list(PRESETS.keys()),
        default="default",
        help="Configuration variant"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output directory"
    )
    parser.add_argument(
        "--quality", "-q",
        choices=["draft", "normal", "fine", "ultra"],
        default="normal",
        help="STL mesh quality"
    )
    parser.add_argument(
        "--export-all",
        action="store_true",
        help="Export all variants"
    )
    parser.add_argument(
        "--list-variants",
        action="store_true",
        help="List available variants"
    )

    args = parser.parse_args()

    if args.list_variants:
        print("Available variants:")
        for name, config in PRESETS.items():
            print(f"  {name:15} - {config.width}x{config.height}x{config.depth}mm")
        return

    build_project(
        variant=args.variant,
        output_dir=args.output,
        export_all=args.export_all,
        quality=args.quality,
    )


if __name__ == "__main__":
    main()
''',

    "__init__.py": '''"""
$name_class Project

$description

Usage:
    from projects.$name_underscore import create_assembly, CONFIG

    assembly = create_assembly()
    assembly.export(output_dir)
"""

from .config import CONFIG, PRESETS, Config
from .frame import generate_part
from .assembly import create_assembly, Assembly

__all__ = [
    "CONFIG",
    "PRESETS",
    "Config",
    "generate_part",
    "create_assembly",
    "Assembly",
]
''',
}
