#!/usr/bin/env python3
"""
Quadcopter 5-inch Build Script
==============================
Generates all output files for manufacturing and visualization.

Outputs:
- frame.step / frame.stl     - Frame only (for CNC)
- assembly.step / assembly.stl - Full assembly
- bom.csv / bom.json / bom.md  - Bill of materials

Usage:
    python build.py
    python build.py --variant race
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
sys.path.insert(0, str(project_dir.parent.parent / "scripts"))

from config import CONFIG, PRESETS, QuadConfig
from frame import generate_frame, export_frame
from assembly import create_assembly
from semicad.export import STLQuality, BOM, BOMEntry, export_bom


def generate_bom(config: QuadConfig) -> BOM:
    """Generate bill of materials using semicad.export."""
    entries = [
        # Frame
        BOMEntry(
            name=f"Carbon fiber plate ({config.arm_thickness}mm)",
            quantity=1,
            category="Frame",
            description="3K Carbon Fiber, CNC cut",
        ),
        # Electronics
        BOMEntry(
            name="Flight Controller",
            quantity=1,
            category="Electronics",
            description="30.5x30.5mm mount",
        ),
        BOMEntry(
            name="4-in-1 ESC",
            quantity=1,
            category="Electronics",
            description="30.5x30.5mm mount, 45A",
        ),
        BOMEntry(
            name=f"Brushless Motor {config.motor_size}",
            quantity=4,
            category="Electronics",
            description=f"{config.motor_mount}mm mount pattern",
        ),
        # Propulsion
        BOMEntry(
            name=f"Propeller {config.prop_size} inch",
            quantity=4,
            category="Propulsion",
        ),
        # Power
        BOMEntry(
            name=f"LiPo Battery {config.battery_cells}S {config.battery_capacity}mAh",
            quantity=1,
            category="Power",
        ),
        # Hardware
        BOMEntry(
            name="M3x25 Socket Head Screw",
            quantity=4,
            category="Hardware",
            description="Stack mounting",
        ),
        BOMEntry(
            name="M3 Nut",
            quantity=4,
            category="Hardware",
        ),
        BOMEntry(
            name="M3x8 Button Head Screw",
            quantity=16,
            category="Hardware",
            description="Motor mounting",
        ),
        BOMEntry(
            name="M3 Standoff 20mm",
            quantity=4,
            category="Hardware",
            description="Stack spacing",
        ),
    ]

    # Build notes with specifications
    notes = f"""Specifications:
- Wheelbase: {config.wheelbase}mm
- Arm length: {config.arm_length:.1f}mm
- Prop clearance: {config.check_prop_clearance()[1]:.1f}mm
- Frame weight (est): ~35g
- AUW (est): ~350g"""

    return BOM(
        title=f"Quadcopter 5-inch ({config.wheelbase}mm)",
        entries=entries,
        notes=notes,
    )


def build_project(
    variant: str = "freestyle",
    output_dir: Path | None = None,
    export_all: bool = False,
    quality: STLQuality = STLQuality.NORMAL,
):
    """
    Build all project outputs.

    Args:
        variant: Configuration preset name
        output_dir: Output directory (default: project/output)
        export_all: Export all variants
        quality: STL mesh quality
    """
    if output_dir is None:
        output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)

    if export_all:
        # Build all variants
        for name, config in PRESETS.items():
            print(f"\n{'='*50}")
            print(f"Building variant: {name}")
            print(f"{'='*50}")
            variant_dir = output_dir / name
            variant_dir.mkdir(exist_ok=True)
            _build_variant(config, variant_dir, name, quality)
    else:
        # Build single variant
        config = PRESETS.get(variant, CONFIG)
        _build_variant(config, output_dir, variant, quality)


def _build_variant(
    config: QuadConfig,
    output_dir: Path,
    name: str,
    quality: STLQuality = STLQuality.NORMAL,
):
    """Build a single variant."""
    print(f"\nConfiguration:")
    print(f"  Wheelbase: {config.wheelbase}mm")
    print(f"  Props: {config.prop_size} inch")
    print(f"  Motors: {config.motor_size}")
    print(f"  Quality: {quality.value}")

    # Check clearances
    ok, clearance = config.check_prop_clearance()
    if not ok:
        print(f"\n⚠ WARNING: Prop clearance is {clearance:.1f}mm (min: {config.prop_clearance}mm)")

    # Generate frame
    print("\nGenerating frame...")
    frame = export_frame(output_dir, config, quality=quality)

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
    parser = argparse.ArgumentParser(description="Build quadcopter 5-inch project")
    parser.add_argument(
        "--variant", "-v",
        choices=list(PRESETS.keys()),
        default="freestyle",
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
            print(f"  {name:15} - {config.wheelbase}mm, {config.prop_size}\" props, {config.motor_size} motors")
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
