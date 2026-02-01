#!/usr/bin/env python3
"""
Drone Component Library
=======================
Parametric models of common drone components based on real dimensions.
Used for assembly-driven frame design.

Usage:
    from components import FlightController, Motor, ESC, Battery

    fc = FlightController(mount_pattern=30.5)
    motor = Motor(size="2207")
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

import cadquery as cq

if TYPE_CHECKING:
    from collections.abc import Callable

    # show_object is only available in cq-editor runtime
    def show_object(obj: Any, name: str = "") -> None: ...


@dataclass
class MountPattern:
    """Standard mount hole pattern"""
    spacing: float      # mm, hole-to-hole distance
    hole_dia: float     # mm, hole diameter
    pattern: Literal["square", "circular"] = "square"
    hole_count: int = 4


# ============== STANDARD PATTERNS ==============
MOUNT_PATTERNS = {
    "fc_30.5": MountPattern(30.5, 3.0, "square", 4),
    "fc_20": MountPattern(20.0, 2.0, "square", 4),
    "motor_2207": MountPattern(16.0, 3.0, "square", 4),  # 22xx motors
    "motor_1404": MountPattern(12.0, 2.0, "square", 4),  # 14xx motors
    "motor_0802": MountPattern(9.0, 1.6, "square", 4),   # Whoop motors
}


# ============== FLIGHT CONTROLLER ==============
def flight_controller(
    width: float = 36.0,
    length: float = 36.0,
    height: float = 4.0,
    mount_pattern: float = 30.5,
    hole_dia: float = 3.0,
    corner_radius: float = 3.0,
) -> cq.Workplane:
    """
    Create a flight controller model.

    Args:
        width: PCB width in mm
        length: PCB length in mm
        height: PCB + components height in mm
        mount_pattern: Mounting hole spacing in mm (30.5 or 20)
        hole_dia: Mounting hole diameter in mm
        corner_radius: Corner rounding radius

    Returns:
        CadQuery Workplane with FC model
    """
    fc = (
        cq.Workplane("XY")
        .box(width, length, height)
        # Round corners
        .edges("|Z")
        .fillet(corner_radius)
        # Add mount holes
        .faces(">Z")
        .workplane()
        .rect(mount_pattern, mount_pattern, forConstruction=True)
        .vertices()
        .hole(hole_dia)
    )
    return fc


# ============== ESC (4-in-1) ==============
def esc_4in1(
    width: float = 36.0,
    length: float = 36.0,
    height: float = 6.0,
    mount_pattern: float = 30.5,
    hole_dia: float = 3.0,
    corner_radius: float = 3.0,
) -> cq.Workplane:
    """
    Create a 4-in-1 ESC model.
    Same mount pattern as FC, slightly taller due to MOSFETs.
    """
    esc = (
        cq.Workplane("XY")
        .box(width, length, height)
        .edges("|Z")
        .fillet(corner_radius)
        .faces(">Z")
        .workplane()
        .rect(mount_pattern, mount_pattern, forConstruction=True)
        .vertices()
        .hole(hole_dia)
    )
    return esc


# ============== MOTOR ==============
def motor(
    stator_diameter: float = 22.0,
    stator_height: float = 7.0,
    bell_diameter: float = 27.0,
    bell_height: float = 8.0,
    shaft_diameter: float = 5.0,
    shaft_length: float = 4.0,
    mount_pattern: float = 16.0,
    mount_hole_dia: float = 3.0,
    base_thickness: float = 2.0,
) -> cq.Workplane:
    """
    Create a brushless motor model.

    Args:
        stator_diameter: Stator OD in mm (first 2 digits of motor size)
        stator_height: Stator height in mm (last 2 digits of motor size)
        bell_diameter: Outer bell diameter
        bell_height: Bell height including magnets
        shaft_diameter: Motor shaft diameter
        shaft_length: Shaft protrusion above bell
        mount_pattern: Bolt circle diameter for mounting
        mount_hole_dia: Mounting hole diameter
        base_thickness: Motor base plate thickness
    """
    # Base with mount holes
    base = (
        cq.Workplane("XY")
        .cylinder(base_thickness, stator_diameter / 2)
        .faces(">Z")
        .workplane()
        .rect(mount_pattern, mount_pattern, forConstruction=True)
        .vertices()
        .hole(mount_hole_dia)
    )

    # Stator (simplified as cylinder)
    stator = (
        cq.Workplane("XY")
        .workplane(offset=base_thickness)
        .cylinder(stator_height, stator_diameter / 2)
    )

    # Bell (outer rotating part)
    bell = (
        cq.Workplane("XY")
        .workplane(offset=base_thickness + stator_height - 2)  # Overlaps stator slightly
        .cylinder(bell_height, bell_diameter / 2)
    )

    # Shaft
    shaft = (
        cq.Workplane("XY")
        .workplane(offset=base_thickness + stator_height + bell_height - 2)
        .cylinder(shaft_length, shaft_diameter / 2)
    )

    # Combine
    motor_assy = base.union(stator).union(bell).union(shaft)

    return motor_assy


# ============== BATTERY ==============
def battery_lipo(
    cells: int = 4,  # 4S, 6S etc
    capacity: int = 1300,  # mAh
) -> cq.Workplane:
    """
    Create a LiPo battery model based on typical dimensions.

    Common sizes:
    - 4S 1300mAh: ~75 x 35 x 30mm
    - 4S 1550mAh: ~78 x 35 x 35mm
    - 6S 1100mAh: ~70 x 35 x 35mm
    """
    # Estimate dimensions based on capacity and cells
    if cells == 4:
        if capacity <= 1300:
            width, length, height = 35, 75, 30
        elif capacity <= 1550:
            width, length, height = 35, 78, 35
        else:
            width, length, height = 38, 85, 38
    elif cells == 6:
        if capacity <= 1100:
            width, length, height = 35, 70, 35
        else:
            width, length, height = 38, 80, 40
    else:
        # Generic estimate
        width, length, height = 35, 75, 30

    battery = (
        cq.Workplane("XY")
        .box(width, length, height)
        .edges("|Z")
        .fillet(2)  # Slight rounding
    )

    return battery


# ============== PROPELLER (for clearance checking) ==============
def propeller(
    diameter: float = 5.0,  # inches
    hub_diameter: float = 8.0,  # mm
) -> cq.Workplane:
    """
    Create a simplified propeller disc for clearance checking.
    Just a thin disc representing the prop sweep area.
    """
    diameter_mm = diameter * 25.4  # Convert to mm

    prop = (
        cq.Workplane("XY")
        .cylinder(1, diameter_mm / 2)  # 1mm thick disc
        .faces(">Z")
        .workplane()
        .hole(hub_diameter)  # Center hole
    )

    return prop


# ============== COMPONENT PRESETS ==============
# Based on common real-world components

COMPONENTS = {
    # Flight Controllers
    "fc_f405_30x30": {"func": flight_controller, "args": {"width": 36, "length": 36, "height": 4, "mount_pattern": 30.5}},
    "fc_f722_30x30": {"func": flight_controller, "args": {"width": 36, "length": 36, "height": 5, "mount_pattern": 30.5}},
    "fc_f411_20x20": {"func": flight_controller, "args": {"width": 26, "length": 26, "height": 3, "mount_pattern": 20}},

    # ESCs
    "esc_45a_30x30": {"func": esc_4in1, "args": {"width": 36, "length": 36, "height": 6, "mount_pattern": 30.5}},
    "esc_35a_30x30": {"func": esc_4in1, "args": {"width": 36, "length": 36, "height": 5, "mount_pattern": 30.5}},
    "esc_13a_20x20": {"func": esc_4in1, "args": {"width": 26, "length": 26, "height": 4, "mount_pattern": 20}},

    # Motors
    "motor_2207": {"func": motor, "args": {"stator_diameter": 22, "stator_height": 7, "bell_diameter": 27, "mount_pattern": 16}},
    "motor_2306": {"func": motor, "args": {"stator_diameter": 23, "stator_height": 6, "bell_diameter": 28, "mount_pattern": 16}},
    "motor_1404": {"func": motor, "args": {"stator_diameter": 14, "stator_height": 4, "bell_diameter": 18, "mount_pattern": 12, "mount_hole_dia": 2}},
    "motor_0802": {"func": motor, "args": {"stator_diameter": 8, "stator_height": 2, "bell_diameter": 10, "mount_pattern": 9, "mount_hole_dia": 1.6, "shaft_diameter": 1}},

    # Batteries
    "battery_4s_1300": {"func": battery_lipo, "args": {"cells": 4, "capacity": 1300}},
    "battery_4s_1550": {"func": battery_lipo, "args": {"cells": 4, "capacity": 1550}},
    "battery_6s_1100": {"func": battery_lipo, "args": {"cells": 6, "capacity": 1100}},

    # Props
    "prop_5inch": {"func": propeller, "args": {"diameter": 5.0}},
    "prop_3inch": {"func": propeller, "args": {"diameter": 3.0}},
    "prop_31mm": {"func": propeller, "args": {"diameter": 31/25.4}},  # Whoop
}


def get_component(name: str) -> cq.Workplane:
    """Get a component model by name."""
    if name not in COMPONENTS:
        raise ValueError(f"Unknown component: {name}. Available: {list(COMPONENTS.keys())}")

    comp: dict[str, Any] = COMPONENTS[name]
    func = cast("Callable[..., cq.Workplane]", comp["func"])
    return func(**comp["args"])


# ============== TEST / VISUALIZATION ==============
if __name__ == "__main__":
    from pathlib import Path

    output_dir = Path(__file__).parent.parent / "output" / "components"
    output_dir.mkdir(exist_ok=True)

    print("Generating component models...")

    # Generate each component
    for name in ["fc_f405_30x30", "esc_45a_30x30", "motor_2207", "battery_4s_1300", "prop_5inch"]:
        print(f"  {name}...")
        comp = get_component(name)
        cq.exporters.export(comp, str(output_dir / f"{name}.step"))
        cq.exporters.export(comp, str(output_dir / f"{name}.stl"))

    print(f"\nComponents saved to: {output_dir}")

    # For cq-editor visualization
    try:
        show_object(get_component("fc_f405_30x30"), name="Flight Controller")
        show_object(get_component("esc_45a_30x30").translate((0, 0, -10)), name="ESC")
        show_object(get_component("motor_2207").translate((50, 50, 0)), name="Motor")
    except NameError:
        pass
