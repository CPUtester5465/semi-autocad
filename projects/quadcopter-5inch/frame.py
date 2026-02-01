#!/usr/bin/env python3
"""
Quadcopter Frame Generator
==========================
Generates the main carbon fiber frame plate.

Design features:
- Center plate with FC/ESC stack mounting
- 4 arms extending to motor mounts
- Weight-saving cutouts
- Rounded edges for strength

Usage:
    python frame.py              # Export STEP/STL
    python frame.py --quality fine
    cq-editor frame.py           # Interactive view
"""

import cadquery as cq
import math
from pathlib import Path
import sys

# Setup paths for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG, QuadConfig
from semicad.export import export_step, export_stl, STLQuality


def generate_frame(config: QuadConfig = CONFIG) -> cq.Workplane:
    """
    Generate the quadcopter frame geometry.

    Args:
        config: QuadConfig with frame parameters

    Returns:
        CadQuery Workplane with frame geometry
    """
    arm_length = config.arm_length
    t = config.arm_thickness

    # === Center Plate ===
    center = (
        cq.Workplane("XY")
        .box(config.center_size, config.center_size, t)
        .edges("|Z")
        .fillet(4)
        # FC/ESC mount holes (M3)
        .faces(">Z")
        .workplane()
        .rect(config.fc_mount, config.fc_mount, forConstruction=True)
        .vertices()
        .hole(3.2)
        # Center weight-reduction hole
        .faces(">Z")
        .workplane()
        .hole(12)
    )

    frame = center

    # === Arms ===
    for i in range(4):
        angle = 45 + i * 90  # X-frame layout

        # Motor position
        mx = arm_length * math.cos(math.radians(angle))
        my = arm_length * math.sin(math.radians(angle))

        # Arm extends from center edge to motor
        arm_start = config.center_size / 2 * 0.707  # Distance to corner
        arm_actual_length = arm_length - arm_start - 8  # Leave room for motor mount

        # Create arm
        arm = (
            cq.Workplane("XY")
            .box(arm_actual_length, config.arm_width, t)
            .edges("|Z")
            .fillet(2)
            # Position: start at center edge, extend outward
            .translate((arm_actual_length / 2 + arm_start + 4, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )

        # Motor mount pad (circular)
        motor_pad_radius = config.motor_mount / 2 + 6
        motor_mount = (
            cq.Workplane("XY")
            .cylinder(t, motor_pad_radius)
            .translate((mx, my, 0))
            # Motor bolt holes (M3)
            .faces(">Z")
            .workplane()
            .pushPoints([
                (mx + config.motor_mount/2 * math.cos(math.radians(a)),
                 my + config.motor_mount/2 * math.sin(math.radians(a)))
                for a in [0, 90, 180, 270]
            ])
            .hole(3.2)
            # Center shaft hole
            .faces(">Z")
            .workplane()
            .center(mx, my)
            .hole(10)
        )

        frame = frame.union(arm).union(motor_mount)

    # === Weight Reduction ===
    # Add lightening holes in arms (optional)
    # for i in range(4):
    #     angle = 45 + i * 90
    #     hole_dist = arm_length * 0.6
    #     hx = hole_dist * math.cos(math.radians(angle))
    #     hy = hole_dist * math.sin(math.radians(angle))
    #     frame = frame.faces(">Z").workplane().center(hx, hy).hole(6)

    return frame


def generate_frame_with_chamfers(config: QuadConfig = CONFIG) -> cq.Workplane:
    """Generate frame with chamfered edges for easier CNC."""
    frame = generate_frame(config)
    # Chamfer top and bottom edges
    frame = frame.edges(">Z or <Z").chamfer(0.5)
    return frame


# === Export Functions ===
def export_frame(
    output_dir: Path,
    config: QuadConfig = CONFIG,
    quality: STLQuality = STLQuality.NORMAL,
):
    """Export frame to STEP and STL.

    Args:
        output_dir: Directory to write files
        config: Frame configuration
        quality: STL mesh quality (draft, normal, fine, ultra)
    """
    frame = generate_frame(config)

    step_path = output_dir / "frame.step"
    stl_path = output_dir / "frame.stl"

    export_step(frame, step_path)
    export_stl(frame, stl_path, quality=quality)

    print(f"Exported: {step_path}")
    print(f"Exported: {stl_path} (quality: {quality.value})")

    return frame


# === Main / cq-editor ===

# Generate frame for visualization
_frame = generate_frame(CONFIG)

# For cq-editor: show_object is only available in cq-editor context
try:
    show_object(_frame, name="Frame", options={"color": "gold"})
except NameError:
    pass  # Not running in cq-editor

# CLI execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate quadcopter frame")
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

    print(f"Generating {CONFIG.wheelbase}mm quadcopter frame...")
    print(f"  Arm length: {CONFIG.arm_length:.1f}mm")
    print(f"  Arm width: {CONFIG.arm_width}mm")
    print(f"  Thickness: {CONFIG.arm_thickness}mm")
    print(f"  Quality: {quality.value}")

    # Check prop clearance
    ok, clearance = CONFIG.check_prop_clearance()
    print(f"  Prop clearance: {clearance:.1f}mm {'✓' if ok else '⚠ TOO CLOSE'}")

    export_frame(args.output, CONFIG, quality=quality)
