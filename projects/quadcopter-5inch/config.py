"""
Quadcopter 5-inch Configuration
===============================
Central configuration for the 220mm freestyle quad build.
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
        # Distance between adjacent motor centers
        motor_distance = self.wheelbase / math.sqrt(2)
        # Clearance = distance - 2 * prop_radius
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
