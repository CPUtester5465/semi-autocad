#!/usr/bin/env python3
"""
EnclosureTest Enclosure Generator

Generates the enclosure body and lid.

Design features:
- Hollow box with configurable wall thickness
- Multiple lid styles (snap, screw, slide)
- Optional mounting holes and ventilation
- Corner screw bosses

Usage:
    python frame.py              # Export STEP/STL
    python frame.py --quality fine
    cq-editor frame.py           # Interactive view
"""

import cadquery as cq
from pathlib import Path
import sys

# Setup paths for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG, EnclosureConfig
from semicad.export import export_step, export_stl, STLQuality


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


def export_enclosure(
    output_dir: Path,
    config: EnclosureConfig = CONFIG,
    quality: STLQuality = STLQuality.NORMAL,
):
    """Export enclosure parts to STEP and STL.

    Args:
        output_dir: Directory to write files
        config: Enclosure configuration
        quality: STL mesh quality
    """
    body, lid = generate_enclosure(config)

    # Export body
    export_step(body, output_dir / "body.step")
    export_stl(body, output_dir / "body.stl", quality=quality)
    print(f"Exported: {output_dir / 'body.step'}")
    print(f"Exported: {output_dir / 'body.stl'} (quality: {quality.value})")

    # Export lid
    export_step(lid, output_dir / "lid.step")
    export_stl(lid, output_dir / "lid.stl", quality=quality)
    print(f"Exported: {output_dir / 'lid.step'}")
    print(f"Exported: {output_dir / 'lid.stl'} (quality: {quality.value})")

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
    import argparse

    parser = argparse.ArgumentParser(description="Generate enclosure parts")
    parser.add_argument(
        "--quality", "-q",
        choices=["draft", "normal", "fine", "ultra"],
        default="normal",
        help="STL mesh quality"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(__file__).parent / "output",
        help="Output directory"
    )
    args = parser.parse_args()

    args.output.mkdir(exist_ok=True)
    quality = STLQuality(args.quality)

    print(f"Generating enclosure-test enclosure...")
    print(f"  External: {CONFIG.width} x {CONFIG.height} x {CONFIG.depth} mm")
    print(f"  Internal: {CONFIG.internal_width:.1f} x {CONFIG.internal_height:.1f} x {CONFIG.internal_depth:.1f} mm")
    print(f"  Wall thickness: {CONFIG.wall_thickness}mm")
    print(f"  Lid style: {CONFIG.lid_style}")
    print(f"  Quality: {quality.value}")

    export_enclosure(args.output, CONFIG, quality=quality)
