"""
Quadcopter Project Template - Drone/multirotor frame project.

Based on the quadcopter-5inch reference implementation.
"""

TEMPLATE_FILES = {
    "partcad.yaml": '''# $name Quadcopter Project
# $description

name: $name
desc: $description
version: "0.1.0"

# Build configuration
config:
  wheelbase: 220        # mm, motor-to-motor diagonal
  prop_size: 5.0        # inches
  fc_mount: 30.5        # mm, FC/ESC stack mount pattern
  motor_mount: 16.0     # mm, motor bolt pattern
  arm_width: 12         # mm
  arm_thickness: 4      # mm
  material: "carbon_fiber_3k"

# Components used (from semicad registry)
components:
  fc: fc_f405_30x30
  esc: esc_45a_30x30
  motors: motor_2207
  props: prop_5inch
  battery: battery_4s_1300

# Parts defined in this project
parts:
  frame:
    type: cadquery
    path: frame.py
    desc: Main unibody frame plate

# Assembly
assemblies:
  full_assembly:
    type: assy
    path: assembly.assy
    desc: Complete quadcopter with all components

# Manufacturing
manufacturing:
  frame:
    material: "3K Carbon Fiber"
    thickness: "4mm"
    process: "CNC cut"
    finish: "matte"
''',

    "config.py": '''"""
$name_class Configuration

Central configuration for the $name quadcopter build.
"""

from dataclasses import dataclass
from typing import Literal
import math


@dataclass
class QuadConfig:
    """Configuration parameters for the quadcopter."""

    # Frame geometry
    wheelbase: float = 220.0        # mm, motor-to-motor diagonal
    arm_width: float = 12.0         # mm
    arm_thickness: float = 4.0      # mm
    center_size: float = 42.0       # mm, center plate width

    # Mount patterns
    fc_mount: float = 30.5          # mm, FC/ESC stack (30.5x30.5 or 20x20)
    motor_mount: float = 16.0       # mm, motor bolt circle

    # Component specs
    prop_size: float = 5.0          # inches
    motor_size: str = "2207"        # stator diameter x height
    battery_cells: int = 4          # S count
    battery_capacity: int = 1300    # mAh

    # Stack
    stack_standoff: float = 5.0     # mm, standoff between FC and ESC
    stack_total_height: float = 20.0  # mm, total stack height

    # Clearances
    prop_clearance: float = 5.0     # mm, minimum between prop tips
    battery_clearance: float = 2.0  # mm, battery to frame

    @property
    def arm_length(self) -> float:
        """Distance from center to motor mount."""
        return self.wheelbase / 2 * math.cos(math.radians(45))

    @property
    def prop_radius(self) -> float:
        """Propeller radius in mm."""
        return self.prop_size * 25.4 / 2

    @property
    def motor_positions(self) -> list[tuple[float, float]]:
        """XY positions of all 4 motors."""
        return [
            (
                self.arm_length * math.cos(math.radians(45 + i * 90)),
                self.arm_length * math.sin(math.radians(45 + i * 90)),
            )
            for i in range(4)
        ]

    def check_prop_clearance(self) -> tuple[bool, float]:
        """Check if props have adequate clearance."""
        motor_distance = self.wheelbase / math.sqrt(2)
        clearance = motor_distance - 2 * self.prop_radius
        return clearance >= self.prop_clearance, clearance


# Default configuration
CONFIG = QuadConfig()

# Preset configurations
PRESETS = {
    "freestyle": QuadConfig(
        wheelbase=220,
        prop_size=5.0,
        motor_size="2207",
        battery_cells=4,
        battery_capacity=1300,
    ),
    "race": QuadConfig(
        wheelbase=210,
        prop_size=5.0,
        motor_size="2306",
        battery_cells=6,
        battery_capacity=1100,
        arm_width=10,
    ),
    "cinematic": QuadConfig(
        wheelbase=230,
        prop_size=5.0,
        motor_size="2207",
        battery_cells=6,
        battery_capacity=1300,
        arm_width=14,
        arm_thickness=5,
    ),
}
''',

    "frame.py": '''#!/usr/bin/env python3
"""
$name_class Frame Generator

Generates the main carbon fiber frame plate.

Design features:
- Center plate with FC/ESC stack mounting
- 4 arms extending to motor mounts
- Weight-saving cutouts
- Rounded edges for strength

Usage:
    python frame.py              # Export STEP/STL
    cq-editor frame.py           # Interactive view
"""

import cadquery as cq
import math
from pathlib import Path

# Import config
try:
    from config import CONFIG, QuadConfig
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import CONFIG, QuadConfig


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
        arm_start = config.center_size / 2 * 0.707
        arm_actual_length = arm_length - arm_start - 8

        # Create arm
        arm = (
            cq.Workplane("XY")
            .box(arm_actual_length, config.arm_width, t)
            .edges("|Z")
            .fillet(2)
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

    return frame


def export_frame(output_dir: Path, config: QuadConfig = CONFIG):
    """Export frame to STEP and STL."""
    frame = generate_frame(config)

    step_path = output_dir / "frame.step"
    stl_path = output_dir / "frame.stl"

    cq.exporters.export(frame, str(step_path))
    cq.exporters.export(frame, str(stl_path))

    print(f"Exported: {step_path}")
    print(f"Exported: {stl_path}")

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
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    print(f"Generating {CONFIG.wheelbase}mm quadcopter frame...")
    print(f"  Arm length: {CONFIG.arm_length:.1f}mm")
    print(f"  Arm width: {CONFIG.arm_width}mm")
    print(f"  Thickness: {CONFIG.arm_thickness}mm")

    # Check prop clearance
    ok, clearance = CONFIG.check_prop_clearance()
    status = "OK" if ok else "WARNING: TOO CLOSE"
    print(f"  Prop clearance: {clearance:.1f}mm {status}")

    export_frame(output_dir, CONFIG)
''',

    "assembly.py": '''#!/usr/bin/env python3
"""
$name_class Assembly

Positions all components and frame together.

Usage:
    python assembly.py           # Export full assembly
    cq-editor assembly.py        # Interactive visualization
"""

import cadquery as cq
import math
from pathlib import Path
from dataclasses import dataclass

# Add paths for imports
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG, QuadConfig
from frame import generate_frame

# Try to import components (may not be available)
try:
    from components import get_component
    HAS_COMPONENTS = True
except ImportError:
    HAS_COMPONENTS = False


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


def create_placeholder(width: float, height: float, depth: float) -> cq.Workplane:
    """Create a simple box placeholder for missing components."""
    return cq.Workplane("XY").box(width, height, depth)


class QuadcopterAssembly:
    """
    Complete quadcopter assembly manager.

    Handles component positioning, clearance checking, and export.
    """

    def __init__(self, config: QuadConfig = CONFIG):
        self.config = config
        self.components: list[PositionedComponent] = []
        self.frame: cq.Workplane | None = None

    def add_frame(self) -> "QuadcopterAssembly":
        """Add the main frame."""
        self.frame = generate_frame(self.config)
        self.components.append(PositionedComponent(
            name="frame",
            model=self.frame,
            position=(0, 0, 0),
            color="gold",
        ))
        return self

    def add_fc(self, z_offset: float = 8) -> "QuadcopterAssembly":
        """Add flight controller on top of frame."""
        if HAS_COMPONENTS:
            fc = get_component("fc_f405_30x30")
        else:
            fc = create_placeholder(30, 30, 4)
        self.components.append(PositionedComponent(
            name="fc",
            model=fc,
            position=(0, 0, z_offset),
            color="green",
        ))
        return self

    def add_esc(self, z_offset: float = -8) -> "QuadcopterAssembly":
        """Add ESC below frame."""
        if HAS_COMPONENTS:
            esc = get_component("esc_45a_30x30")
        else:
            esc = create_placeholder(30, 30, 4)
        self.components.append(PositionedComponent(
            name="esc",
            model=esc,
            position=(0, 0, z_offset),
            color="blue",
        ))
        return self

    def add_motors(self, z_offset: float = -4) -> "QuadcopterAssembly":
        """Add all 4 motors."""
        if HAS_COMPONENTS:
            motor_model = get_component("motor_2207")
        else:
            motor_model = cq.Workplane("XY").cylinder(15, 11)

        for i, (mx, my) in enumerate(self.config.motor_positions):
            self.components.append(PositionedComponent(
                name=f"motor_{i+1}",
                model=motor_model,
                position=(mx, my, z_offset),
                color="dimgray",
            ))
        return self

    def add_props(self, z_offset: float = 18) -> "QuadcopterAssembly":
        """Add propeller discs for clearance visualization."""
        prop_radius = self.config.prop_radius
        prop_model = cq.Workplane("XY").cylinder(1, prop_radius)

        for i, (mx, my) in enumerate(self.config.motor_positions):
            self.components.append(PositionedComponent(
                name=f"prop_{i+1}",
                model=prop_model,
                position=(mx, my, z_offset),
                color="red",
            ))
        return self

    def build_full(self) -> "QuadcopterAssembly":
        """Build complete assembly with all components."""
        return (
            self.add_frame()
            .add_esc()
            .add_fc()
            .add_motors()
            .add_props()
        )

    def get_combined(self) -> cq.Workplane:
        """Combine all components into single geometry."""
        if not self.components:
            raise ValueError("No components in assembly")

        combined = self.components[0].positioned
        for comp in self.components[1:]:
            combined = combined.union(comp.positioned)
        return combined

    def check_clearances(self) -> dict:
        """Check critical clearances."""
        results = {}

        ok, clearance = self.config.check_prop_clearance()
        results["prop_to_prop"] = {
            "ok": ok,
            "value": clearance,
            "min": self.config.prop_clearance,
            "unit": "mm",
        }

        return results

    def export(self, output_dir: Path):
        """Export assembly to files."""
        output_dir.mkdir(exist_ok=True)

        combined = self.get_combined()
        cq.exporters.export(combined, str(output_dir / "assembly.step"))
        cq.exporters.export(combined, str(output_dir / "assembly.stl"))

        if self.frame:
            cq.exporters.export(self.frame, str(output_dir / "frame.step"))
            cq.exporters.export(self.frame, str(output_dir / "frame.stl"))

        print(f"Exported to {output_dir}")


def create_assembly(config: QuadConfig = CONFIG) -> QuadcopterAssembly:
    """Factory function to create full assembly."""
    return QuadcopterAssembly(config).build_full()


# === Main / cq-editor ===

# Create assembly for visualization
_assembly = create_assembly()

# For cq-editor: show components
try:
    for comp in _assembly.components:
        alpha = 0.3 if "prop" in comp.name else 1.0
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
    print(f"Wheelbase: {CONFIG.wheelbase}mm")
    print(f"Props: {CONFIG.prop_size} inch")
    print(f"Motors: {CONFIG.motor_size}")
    print()

    # Check clearances
    clearances = _assembly.check_clearances()
    print("Clearance Check:")
    for name, data in clearances.items():
        status = "OK" if data["ok"] else "WARNING"
        print(f"  {status} {name}: {data['value']:.1f}mm (min: {data['min']}mm)")
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
- frame.step / frame.stl     - Frame only (for CNC)
- assembly.step / assembly.stl - Full assembly
- bom.txt                     - Bill of materials

Usage:
    python build.py
    python build.py --variant race
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


def generate_bom(config: QuadConfig) -> str:
    """Generate bill of materials."""
    bom = f"""
BILL OF MATERIALS
=================
Project: $name ({config.wheelbase}mm)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

FRAME
-----
- 1x Carbon fiber plate ({config.arm_thickness}mm thick)
  Material: 3K Carbon Fiber
  Process: CNC cut

ELECTRONICS
-----------
- 1x Flight Controller (30.5x30.5mm mount)
- 1x 4-in-1 ESC (30.5x30.5mm mount, 45A)
- 4x Brushless Motor ({config.motor_size}, {config.motor_mount}mm mount)

PROPULSION
----------
- 4x Propeller ({config.prop_size} inch)

POWER
-----
- 1x LiPo Battery ({config.battery_cells}S {config.battery_capacity}mAh)

HARDWARE
--------
- 4x M3x25 Socket Head Screw (stack mounting)
- 4x M3 Nut
- 16x M3x8 Button Head Screw (motor mounting)
- 4x M3 Standoff 20mm (stack spacing)

SPECIFICATIONS
--------------
- Wheelbase: {config.wheelbase}mm
- Arm length: {config.arm_length:.1f}mm
- Prop clearance: {config.check_prop_clearance()[1]:.1f}mm
- Frame weight (est): ~35g
- AUW (est): ~350g
"""
    return bom


def build_project(
    variant: str = "freestyle",
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


def _build_variant(config: QuadConfig, output_dir: Path, name: str):
    """Build a single variant."""
    print(f"\\nConfiguration:")
    print(f"  Wheelbase: {config.wheelbase}mm")
    print(f"  Props: {config.prop_size} inch")
    print(f"  Motors: {config.motor_size}")

    # Check clearances
    ok, clearance = config.check_prop_clearance()
    if not ok:
        print(f"\\nWARNING: Prop clearance is {clearance:.1f}mm (min: {config.prop_clearance}mm)")

    # Generate frame
    print("\\nGenerating frame...")
    frame = export_frame(output_dir, config)

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
    parser = argparse.ArgumentParser(description="Build $name quadcopter project")
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
            print(f"  {name:15} - {config.wheelbase}mm, {config.prop_size}\\" props, {config.motor_size} motors")
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

from .config import CONFIG, PRESETS, QuadConfig
from .frame import generate_frame
from .assembly import create_assembly, QuadcopterAssembly

__all__ = [
    "CONFIG",
    "PRESETS",
    "QuadConfig",
    "generate_frame",
    "create_assembly",
    "QuadcopterAssembly",
]
''',
}
