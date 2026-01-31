#!/usr/bin/env python3
"""
EnclosureTest Build Script

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
Project: enclosure-test
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
        bom += "- 4x M3x8 Pan Head Screw (lid mounting)\n"

    if config.mount_holes:
        bom += f"- 4x M{int(config.mount_hole_diameter)} mounting screws\n"

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
            print(f"\n{'='*50}")
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
    print(f"\nConfiguration:")
    print(f"  External: {config.width} x {config.height} x {config.depth} mm")
    print(f"  Wall: {config.wall_thickness}mm")
    print(f"  Lid style: {config.lid_style}")

    # Generate enclosure parts
    print("\nGenerating enclosure...")
    export_enclosure(output_dir, config)

    # Generate assembly
    print("\nGenerating assembly...")
    assembly = create_assembly(config)
    assembly.export(output_dir)

    # Generate BOM
    print("\nGenerating BOM...")
    bom = generate_bom(config)
    bom_path = output_dir / "bom.txt"
    with open(bom_path, "w") as f:
        f.write(bom)
    print(f"Exported: {bom_path}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Build complete: {name}")
    print(f"Output: {output_dir}")
    print(f"{'='*50}")

    # List output files
    print("\nOutput files:")
    for f in sorted(output_dir.glob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"  {f.name:25} {size:>10,} bytes")


def main():
    parser = argparse.ArgumentParser(description="Build enclosure-test enclosure project")
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
