"""
Enclosure Project Template - Electronics enclosure/box project.

For creating enclosures with lids, mounting holes, and ventilation.
"""

TEMPLATE_FILES = {
    "partcad.yaml": '''# $name Enclosure Project
# $description

name: $name
desc: $description
version: "0.1.0"

# Build configuration
config:
  # Outer dimensions
  width: 100          # mm, external width
  height: 60          # mm, external height
  depth: 40           # mm, external depth

  # Wall properties
  wall_thickness: 2.5   # mm
  corner_radius: 3      # mm

  # Lid
  lid_style: "snap"     # snap, screw, slide
  lid_clearance: 0.2    # mm, gap for fit

  # Material
  material: "PETG"

# Parts defined in this project
parts:
  enclosure:
    type: cadquery
    path: frame.py
    desc: Main enclosure body
  lid:
    type: cadquery
    path: frame.py
    desc: Enclosure lid

# Assembly
assemblies:
  full_assembly:
    type: assy
    path: assembly.assy
    desc: Complete enclosure with lid

# Manufacturing
manufacturing:
  enclosure:
    material: "PETG"
    process: "3D Print (FDM)"
    infill: "20%"
    layer_height: "0.2mm"
''',

    "config.py": '''"""
$name_class Configuration

Central configuration for the $name enclosure.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class EnclosureConfig:
    """Configuration parameters for the enclosure."""

    # External dimensions
    width: float = 100.0        # mm
    height: float = 60.0        # mm
    depth: float = 40.0         # mm

    # Wall properties
    wall_thickness: float = 2.5  # mm
    corner_radius: float = 3.0   # mm

    # Lid configuration
    lid_style: Literal["snap", "screw", "slide"] = "snap"
    lid_height: float = 8.0      # mm, height of lid portion
    lid_clearance: float = 0.2   # mm, gap for fit
    lid_lip: float = 2.0         # mm, overlap lip

    # Mounting
    mount_holes: bool = True
    mount_hole_diameter: float = 4.0  # mm (M4)
    mount_inset: float = 8.0     # mm from corners

    # Ventilation
    vent_holes: bool = False
    vent_diameter: float = 5.0   # mm
    vent_spacing: float = 8.0    # mm

    # Features
    screw_bosses: bool = True
    screw_boss_diameter: float = 8.0  # mm
    screw_hole_diameter: float = 2.5  # mm (M3 tap)

    @property
    def internal_width(self) -> float:
        """Internal cavity width."""
        return self.width - 2 * self.wall_thickness

    @property
    def internal_height(self) -> float:
        """Internal cavity height."""
        return self.height - 2 * self.wall_thickness

    @property
    def internal_depth(self) -> float:
        """Internal cavity depth (body only, not lid)."""
        return self.depth - self.wall_thickness - self.lid_height

    @property
    def body_depth(self) -> float:
        """Depth of the body (without lid)."""
        return self.depth - self.lid_height


# Default configuration
CONFIG = EnclosureConfig()

# Preset configurations
PRESETS = {
    "default": EnclosureConfig(),
    "small": EnclosureConfig(
        width=60,
        height=40,
        depth=25,
        wall_thickness=2.0,
    ),
    "large": EnclosureConfig(
        width=150,
        height=100,
        depth=60,
        wall_thickness=3.0,
        corner_radius=5.0,
    ),
    "vented": EnclosureConfig(
        vent_holes=True,
        vent_diameter=4.0,
        vent_spacing=6.0,
    ),
    "screw_lid": EnclosureConfig(
        lid_style="screw",
        lid_height=10.0,
    ),
}
''',

    "frame.py": '''#!/usr/bin/env python3
"""
$name_class Enclosure Generator

Generates the enclosure body and lid.

Design features:
- Hollow box with configurable wall thickness
- Multiple lid styles (snap, screw, slide)
- Optional mounting holes and ventilation
- Corner screw bosses

Usage:
    python frame.py              # Export STEP/STL
    cq-editor frame.py           # Interactive view
"""

import cadquery as cq
from pathlib import Path

# Import config
try:
    from config import CONFIG, EnclosureConfig
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import CONFIG, EnclosureConfig


def generate_body(config: EnclosureConfig = CONFIG) -> cq.Workplane:
    """
    Generate the enclosure body (without lid).

    Args:
        config: EnclosureConfig with enclosure parameters

    Returns:
        CadQuery Workplane with body geometry
    """
    w = config.width
    h = config.height
    d = config.body_depth
    t = config.wall_thickness
    r = config.corner_radius

    # Create outer shell
    body = (
        cq.Workplane("XY")
        .box(w, h, d)
        .edges("|Z")
        .fillet(r)
    )

    # Hollow out the interior
    body = (
        body
        .faces(">Z")
        .workplane()
        .rect(w - 2*t, h - 2*t)
        .cutBlind(-(d - t))
    )

    # Add lid lip (inner wall for lid to sit on)
    lip = config.lid_lip
    body = (
        body
        .faces(">Z")
        .workplane()
        .rect(w - 2*t - 2*lip, h - 2*t - 2*lip)
        .extrude(-lip)
    )

    # Add screw bosses in corners
    if config.screw_bosses:
        boss_r = config.screw_boss_diameter / 2
        hole_r = config.screw_hole_diameter / 2
        inset = config.mount_inset

        boss_positions = [
            (w/2 - inset, h/2 - inset),
            (-w/2 + inset, h/2 - inset),
            (w/2 - inset, -h/2 + inset),
            (-w/2 + inset, -h/2 + inset),
        ]

        for x, y in boss_positions:
            # Add boss cylinder
            boss = (
                cq.Workplane("XY")
                .center(x, y)
                .circle(boss_r)
                .extrude(d - t)
                .translate((0, 0, -d/2 + t))
            )
            body = body.union(boss)

            # Add screw hole
            body = (
                body
                .faces(">Z")
                .workplane()
                .center(x, y)
                .hole(hole_r * 2, d - t)
            )

    # Add mounting holes on bottom
    if config.mount_holes:
        inset = config.mount_inset
        hole_d = config.mount_hole_diameter

        mount_positions = [
            (w/2 - inset, h/2 - inset),
            (-w/2 + inset, h/2 - inset),
            (w/2 - inset, -h/2 + inset),
            (-w/2 + inset, -h/2 + inset),
        ]

        body = (
            body
            .faces("<Z")
            .workplane()
            .pushPoints(mount_positions)
            .hole(hole_d)
        )

    return body


def generate_lid(config: EnclosureConfig = CONFIG) -> cq.Workplane:
    """
    Generate the enclosure lid.

    Args:
        config: EnclosureConfig with enclosure parameters

    Returns:
        CadQuery Workplane with lid geometry
    """
    w = config.width
    h = config.height
    d = config.lid_height
    t = config.wall_thickness
    r = config.corner_radius
    lip = config.lid_lip
    clearance = config.lid_clearance

    # Create lid outer shell
    lid = (
        cq.Workplane("XY")
        .box(w, h, d)
        .edges("|Z")
        .fillet(r)
    )

    # Add inner lip that fits inside body
    lip_width = w - 2*t - 2*lip - clearance
    lip_height = h - 2*t - 2*lip - clearance
    lip_depth = lip - clearance

    inner_lip = (
        cq.Workplane("XY")
        .box(lip_width, lip_height, lip_depth)
        .translate((0, 0, -d/2 - lip_depth/2))
    )
    lid = lid.union(inner_lip)

    # Add screw holes if screw style
    if config.lid_style == "screw" and config.screw_bosses:
        hole_r = config.screw_hole_diameter / 2 + 0.5  # Clearance hole
        inset = config.mount_inset

        hole_positions = [
            (w/2 - inset, h/2 - inset),
            (-w/2 + inset, h/2 - inset),
            (w/2 - inset, -h/2 + inset),
            (-w/2 + inset, -h/2 + inset),
        ]

        lid = (
            lid
            .faces(">Z")
            .workplane()
            .pushPoints(hole_positions)
            .hole(hole_r * 2)
        )

    return lid


def generate_enclosure(config: EnclosureConfig = CONFIG) -> tuple[cq.Workplane, cq.Workplane]:
    """Generate both body and lid."""
    return generate_body(config), generate_lid(config)


def export_enclosure(output_dir: Path, config: EnclosureConfig = CONFIG):
    """Export enclosure parts to STEP and STL."""
    body, lid = generate_enclosure(config)

    # Export body
    cq.exporters.export(body, str(output_dir / "body.step"))
    cq.exporters.export(body, str(output_dir / "body.stl"))
    print(f"Exported: {output_dir / 'body.step'}")
    print(f"Exported: {output_dir / 'body.stl'}")

    # Export lid
    cq.exporters.export(lid, str(output_dir / "lid.step"))
    cq.exporters.export(lid, str(output_dir / "lid.stl"))
    print(f"Exported: {output_dir / 'lid.step'}")
    print(f"Exported: {output_dir / 'lid.stl'}")

    return body, lid


# === Main / cq-editor ===

# Generate parts for visualization
_body = generate_body(CONFIG)
_lid = generate_lid(CONFIG)

# Position lid above body for visualization
_lid_positioned = _lid.translate((0, 0, CONFIG.body_depth/2 + CONFIG.lid_height/2 + 5))

# For cq-editor: show_object is only available in cq-editor context
try:
    show_object(_body, name="Body", options={"color": "steelblue"})
    show_object(_lid_positioned, name="Lid", options={"color": "lightblue", "alpha": 0.8})
except NameError:
    pass  # Not running in cq-editor

# CLI execution
if __name__ == "__main__":
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    print(f"Generating $name enclosure...")
    print(f"  External: {CONFIG.width} x {CONFIG.height} x {CONFIG.depth} mm")
    print(f"  Internal: {CONFIG.internal_width:.1f} x {CONFIG.internal_height:.1f} x {CONFIG.internal_depth:.1f} mm")
    print(f"  Wall thickness: {CONFIG.wall_thickness}mm")
    print(f"  Lid style: {CONFIG.lid_style}")

    export_enclosure(output_dir, CONFIG)
''',

    "assembly.py": '''#!/usr/bin/env python3
"""
$name_class Assembly

Positions enclosure body and lid together.

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
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG, EnclosureConfig
from frame import generate_body, generate_lid


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


class EnclosureAssembly:
    """
    Complete enclosure assembly manager.

    Handles component positioning and export.
    """

    def __init__(self, config: EnclosureConfig = CONFIG):
        self.config = config
        self.components: list[PositionedComponent] = []
        self.body: cq.Workplane | None = None
        self.lid: cq.Workplane | None = None

    def add_body(self) -> "EnclosureAssembly":
        """Add the enclosure body."""
        self.body = generate_body(self.config)
        self.components.append(PositionedComponent(
            name="body",
            model=self.body,
            position=(0, 0, 0),
            color="steelblue",
        ))
        return self

    def add_lid(self, open_position: bool = False) -> "EnclosureAssembly":
        """Add the lid, optionally in open position."""
        self.lid = generate_lid(self.config)

        if open_position:
            # Position lid above body with gap
            z_offset = self.config.body_depth/2 + self.config.lid_height/2 + 10
        else:
            # Position lid closed on body
            z_offset = self.config.body_depth/2 + self.config.lid_height/2 - self.config.lid_lip

        self.components.append(PositionedComponent(
            name="lid",
            model=self.lid,
            position=(0, 0, z_offset),
            color="lightblue",
        ))
        return self

    def build_full(self, open_lid: bool = True) -> "EnclosureAssembly":
        """Build complete assembly."""
        return self.add_body().add_lid(open_position=open_lid)

    def get_combined(self) -> cq.Workplane:
        """Combine all components into single geometry."""
        if not self.components:
            raise ValueError("No components in assembly")

        combined = self.components[0].positioned
        for comp in self.components[1:]:
            combined = combined.union(comp.positioned)
        return combined

    def export(self, output_dir: Path):
        """Export assembly and individual parts to files."""
        output_dir.mkdir(exist_ok=True)

        # Export combined assembly
        combined = self.get_combined()
        cq.exporters.export(combined, str(output_dir / "assembly.step"))
        cq.exporters.export(combined, str(output_dir / "assembly.stl"))

        # Export individual parts
        if self.body:
            cq.exporters.export(self.body, str(output_dir / "body.step"))
            cq.exporters.export(self.body, str(output_dir / "body.stl"))

        if self.lid:
            cq.exporters.export(self.lid, str(output_dir / "lid.step"))
            cq.exporters.export(self.lid, str(output_dir / "lid.stl"))

        print(f"Exported to {output_dir}")


def create_assembly(config: EnclosureConfig = CONFIG) -> EnclosureAssembly:
    """Factory function to create full assembly."""
    return EnclosureAssembly(config).build_full()


# === Main / cq-editor ===

# Create assembly for visualization
_assembly = create_assembly()

# For cq-editor: show components
try:
    for comp in _assembly.components:
        alpha = 0.8 if comp.name == "lid" else 1.0
        show_object(
            comp.positioned,
            name=comp.name,
            options={"color": comp.color, "alpha": alpha}
        )
except NameError:
    pass  # Not running in cq-editor

# CLI execution
if __name__ == "__main__":
    output_dir = Path(__file__).parent / "output"

    print("Building $name_class Assembly")
    print("=" * 40)
    print(f"External: {CONFIG.width} x {CONFIG.height} x {CONFIG.depth} mm")
    print(f"Wall thickness: {CONFIG.wall_thickness}mm")
    print(f"Lid style: {CONFIG.lid_style}")
    print()

    _assembly.export(output_dir)

    print("\\nTo visualize:")
    print(f"  cq-editor {__file__}")
''',

    "build.py": '''#!/usr/bin/env python3
"""
$name_class Build Script

Generates all output files for manufacturing.

Outputs:
- body.step / body.stl       - Enclosure body
- lid.step / lid.stl         - Enclosure lid
- assembly.step / assembly.stl - Full assembly
- bom.txt                     - Bill of materials

Usage:
    python build.py
    python build.py --variant vented
    python build.py --export-all
"""

import argparse
from pathlib import Path
from datetime import datetime
import sys

# Setup paths
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(project_dir.parent.parent))

from config import CONFIG, PRESETS, EnclosureConfig
from frame import export_enclosure
from assembly import create_assembly


def generate_bom(config: EnclosureConfig) -> str:
    """Generate bill of materials."""
    bom = f"""
BILL OF MATERIALS
=================
Project: $name
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

ENCLOSURE
---------
- 1x Body
  Dimensions: {config.width} x {config.height} x {config.body_depth} mm
  Material: PETG
  Process: 3D Print (FDM)

- 1x Lid
  Dimensions: {config.width} x {config.height} x {config.lid_height} mm
  Style: {config.lid_style}
  Material: PETG

HARDWARE
--------
"""
    if config.lid_style == "screw":
        bom += "- 4x M3x8 Pan Head Screw (lid mounting)\\n"

    if config.mount_holes:
        bom += f"- 4x M{int(config.mount_hole_diameter)} mounting screws\\n"

    bom += f"""
SPECIFICATIONS
--------------
- External: {config.width} x {config.height} x {config.depth} mm
- Internal: {config.internal_width:.1f} x {config.internal_height:.1f} x {config.internal_depth:.1f} mm
- Wall thickness: {config.wall_thickness}mm
- Corner radius: {config.corner_radius}mm
"""
    return bom


def build_project(
    variant: str = "default",
    output_dir: Path | None = None,
    export_all: bool = False,
):
    """Build all project outputs."""
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
            _build_variant(config, variant_dir, name)
    else:
        config = PRESETS.get(variant, CONFIG)
        _build_variant(config, output_dir, variant)


def _build_variant(config: EnclosureConfig, output_dir: Path, name: str):
    """Build a single variant."""
    print(f"\\nConfiguration:")
    print(f"  External: {config.width} x {config.height} x {config.depth} mm")
    print(f"  Wall: {config.wall_thickness}mm")
    print(f"  Lid style: {config.lid_style}")

    # Generate enclosure parts
    print("\\nGenerating enclosure...")
    export_enclosure(output_dir, config)

    # Generate assembly
    print("\\nGenerating assembly...")
    assembly = create_assembly(config)
    assembly.export(output_dir)

    # Generate BOM
    print("\\nGenerating BOM...")
    bom = generate_bom(config)
    bom_path = output_dir / "bom.txt"
    with open(bom_path, "w") as f:
        f.write(bom)
    print(f"Exported: {bom_path}")

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
    parser = argparse.ArgumentParser(description="Build $name enclosure project")
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
            print(f"  {name:15} - {config.width}x{config.height}x{config.depth}mm, {config.lid_style} lid")
        return

    build_project(
        variant=args.variant,
        output_dir=args.output,
        export_all=args.export_all,
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

from .config import CONFIG, PRESETS, EnclosureConfig
from .frame import generate_body, generate_lid, generate_enclosure
from .assembly import create_assembly, EnclosureAssembly

__all__ = [
    "CONFIG",
    "PRESETS",
    "EnclosureConfig",
    "generate_body",
    "generate_lid",
    "generate_enclosure",
    "create_assembly",
    "EnclosureAssembly",
]
''',
}
