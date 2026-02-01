#!/usr/bin/env python3
"""
EnclosureTest Build Script

Generates all output files for manufacturing.

Outputs:
- body.step / body.stl       - Enclosure body
- lid.step / lid.stl         - Enclosure lid
- assembly.step / assembly.stl - Full assembly
- bom.csv / bom.json / bom.md  - Bill of materials

Usage:
    python build.py
    python build.py --variant vented
    python build.py --quality fine
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
from semicad.export import STLQuality, BOM, BOMEntry, export_bom


def generate_bom(config: EnclosureConfig) -> BOM:
    """Generate bill of materials using semicad.export."""
    entries = [
        BOMEntry(
            name="Enclosure Body",
            quantity=1,
            category="Enclosure",
            description=f"{config.width}x{config.height}x{config.body_depth}mm, PETG, 3D Print (FDM)",
        ),
        BOMEntry(
            name="Enclosure Lid",
            quantity=1,
            category="Enclosure",
            description=f"{config.width}x{config.height}x{config.lid_height}mm, {config.lid_style} style, PETG",
        ),
    ]

    # Add hardware based on lid style
    if config.lid_style == "screw":
        entries.append(BOMEntry(
            name="M3x8 Pan Head Screw",
            quantity=4,
            category="Hardware",
            description="Lid mounting",
        ))

    if config.mount_holes:
        entries.append(BOMEntry(
            name=f"M{int(config.mount_hole_diameter)} mounting screw",
            quantity=4,
            category="Hardware",
            description="External mounting",
        ))

    # Build notes with specifications
    notes = f"""Specifications:
- External: {config.width}x{config.height}x{config.depth}mm
- Internal: {config.internal_width:.1f}x{config.internal_height:.1f}x{config.internal_depth:.1f}mm
- Wall thickness: {config.wall_thickness}mm
- Corner radius: {config.corner_radius}mm"""

    return BOM(
        title="enclosure-test",
        entries=entries,
        notes=notes,
    )


def build_project(
    variant: str = "default",
    output_dir: Path | None = None,
    export_all: bool = False,
    quality: STLQuality = STLQuality.NORMAL,
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
            _build_variant(config, variant_dir, name, quality)
    else:
        config = PRESETS.get(variant, CONFIG)
        _build_variant(config, output_dir, variant, quality)


def _build_variant(
    config: EnclosureConfig,
    output_dir: Path,
    name: str,
    quality: STLQuality = STLQuality.NORMAL,
):
    """Build a single variant."""
    print(f"\nConfiguration:")
    print(f"  External: {config.width} x {config.height} x {config.depth} mm")
    print(f"  Wall: {config.wall_thickness}mm")
    print(f"  Lid style: {config.lid_style}")
    print(f"  Quality: {quality.value}")

    # Generate enclosure parts
    print("\nGenerating enclosure...")
    export_enclosure(output_dir, config, quality=quality)

    # Generate assembly
    print("\nGenerating assembly...")
    assembly = create_assembly(config)
    assembly.export(output_dir, quality=quality)

    # Generate BOM using semicad.export (export all formats)
    print("\nGenerating BOM...")
    bom = generate_bom(config)
    export_bom(bom, output_dir / "bom.csv")
    export_bom(bom, output_dir / "bom.json")
    export_bom(bom, output_dir / "bom.md")
    print(f"Exported: bom.csv, bom.json, bom.md")

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
            print(f"  {name:15} - {config.width}x{config.height}x{config.depth}mm, {config.lid_style} lid")
        return

    quality = STLQuality(args.quality)
    build_project(
        variant=args.variant,
        output_dir=args.output,
        export_all=args.export_all,
        quality=quality,
    )


if __name__ == "__main__":
    main()
