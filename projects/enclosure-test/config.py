"""
EnclosureTest Configuration

Central configuration for the enclosure-test enclosure.
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
