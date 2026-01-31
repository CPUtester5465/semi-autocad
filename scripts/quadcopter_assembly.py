#!/usr/bin/env python3
"""
Quadcopter Assembly-Driven Design
=================================
Design frame AROUND components, not the other way around.

Workflow:
1. Position components in 3D space
2. Calculate required frame geometry
3. Generate frame that connects everything
4. Verify clearances

Usage:
    python quadcopter_assembly.py

Or open in cq-editor for interactive visualization.
"""

import cadquery as cq
from pathlib import Path
import math

# Import our component library
from components import get_component, flight_controller, esc_4in1, motor, propeller, battery_lipo


# ============== QUAD CONFIGURATION ==============
class QuadConfig:
    """Configuration for a specific quadcopter build."""

    def __init__(
        self,
        name: str = "220mm 5inch",
        wheelbase: float = 220,       # mm, motor to motor diagonal
        prop_size: float = 5.0,       # inches
        fc_mount: float = 30.5,       # mm, FC mount pattern
        motor_mount: float = 16.0,    # mm, motor mount pattern
        stack_height: float = 25,     # mm, total FC+ESC stack with standoffs
        battery_position: str = "top", # "top" or "bottom"
    ):
        self.name = name
        self.wheelbase = wheelbase
        self.prop_size = prop_size
        self.fc_mount = fc_mount
        self.motor_mount = motor_mount
        self.stack_height = stack_height
        self.battery_position = battery_position

        # Derived dimensions
        self.arm_length = wheelbase / 2 * 0.707  # Distance from center to motor
        self.prop_radius = prop_size * 25.4 / 2   # Prop radius in mm

        # Minimum clearance between props (typically 3-5mm)
        self.prop_clearance = 5  # mm


# ============== PREDEFINED CONFIGURATIONS ==============
CONFIGS = {
    "5inch_freestyle": QuadConfig(
        name="5inch Freestyle",
        wheelbase=220,
        prop_size=5.0,
        fc_mount=30.5,
        motor_mount=16.0,
        stack_height=25,
    ),
    "3inch_cinewhoop": QuadConfig(
        name="3inch Cinewhoop",
        wheelbase=140,
        prop_size=3.0,
        fc_mount=20.0,
        motor_mount=12.0,
        stack_height=20,
    ),
    "toothpick": QuadConfig(
        name="3inch Toothpick",
        wheelbase=140,
        prop_size=3.0,
        fc_mount=20.0,
        motor_mount=12.0,
        stack_height=15,
    ),
}


# ============== ASSEMBLY CLASS ==============
class QuadcopterAssembly:
    """
    Manages component placement and frame generation.
    """

    def __init__(self, config: QuadConfig):
        self.config = config
        self.components = {}  # name -> (model, position, rotation)
        self.frame = None

    def add_fc(self, z_offset: float = 0):
        """Add flight controller to assembly."""
        if self.config.fc_mount == 30.5:
            fc = get_component("fc_f405_30x30")
        else:
            fc = get_component("fc_f411_20x20")

        self.components["fc"] = {
            "model": fc,
            "position": (0, 0, z_offset),
            "color": "green",
        }
        return self

    def add_esc(self, z_offset: float = -10):
        """Add ESC below FC."""
        if self.config.fc_mount == 30.5:
            esc = get_component("esc_45a_30x30")
        else:
            esc = get_component("esc_13a_20x20")

        self.components["esc"] = {
            "model": esc,
            "position": (0, 0, z_offset),
            "color": "blue",
        }
        return self

    def add_motors(self, z_offset: float = -5):
        """Add 4 motors at calculated positions."""
        arm_length = self.config.arm_length

        # Motor positions (45° from X axis for X-frame)
        positions = [
            (arm_length * math.cos(math.radians(45 + i * 90)),
             arm_length * math.sin(math.radians(45 + i * 90)),
             z_offset)
            for i in range(4)
        ]

        if self.config.motor_mount == 16.0:
            motor_model = get_component("motor_2207")
        elif self.config.motor_mount == 12.0:
            motor_model = get_component("motor_1404")
        else:
            motor_model = get_component("motor_0802")

        for i, pos in enumerate(positions):
            self.components[f"motor_{i+1}"] = {
                "model": motor_model,
                "position": pos,
                "color": "gray",
            }
        return self

    def add_props(self, z_offset: float = 15):
        """Add prop discs for clearance visualization."""
        arm_length = self.config.arm_length

        positions = [
            (arm_length * math.cos(math.radians(45 + i * 90)),
             arm_length * math.sin(math.radians(45 + i * 90)),
             z_offset)
            for i in range(4)
        ]

        prop = propeller(self.config.prop_size)

        for i, pos in enumerate(positions):
            self.components[f"prop_{i+1}"] = {
                "model": prop,
                "position": pos,
                "color": "red",
            }
        return self

    def add_battery(self, z_offset: float = 30):
        """Add battery."""
        battery = get_component("battery_4s_1300")

        self.components["battery"] = {
            "model": battery,
            "position": (0, 0, z_offset),
            "color": "orange",
        }
        return self

    def get_assembly(self) -> cq.Workplane:
        """
        Combine all components into a single assembly.
        Returns CadQuery Workplane with all parts positioned.
        """
        if not self.components:
            raise ValueError("No components added to assembly")

        # Start with first component
        first_name = list(self.components.keys())[0]
        first_comp = self.components[first_name]
        assembly = first_comp["model"].translate(first_comp["position"])

        # Add remaining components
        for name, comp in list(self.components.items())[1:]:
            positioned = comp["model"].translate(comp["position"])
            assembly = assembly.union(positioned)

        return assembly

    def get_component_models(self) -> dict:
        """Get individual positioned components for visualization."""
        result = {}
        for name, comp in self.components.items():
            result[name] = comp["model"].translate(comp["position"])
        return result

    def generate_frame(self) -> cq.Workplane:
        """
        Generate frame geometry based on component positions.
        The frame connects all motors and provides mounting for FC/ESC stack.
        """
        cfg = self.config
        arm_length = cfg.arm_length

        # Frame parameters (derived from components)
        center_size = cfg.fc_mount + 10  # Slightly larger than mount pattern
        arm_width = 12
        arm_thickness = 4

        # Center plate with FC mount holes
        center = (
            cq.Workplane("XY")
            .box(center_size, center_size, arm_thickness)
            .edges("|Z")
            .fillet(3)
            # FC/ESC mount holes
            .faces(">Z")
            .workplane()
            .rect(cfg.fc_mount, cfg.fc_mount, forConstruction=True)
            .vertices()
            .hole(3.2)
        )

        # Generate arms
        frame = center

        for i in range(4):
            angle = 45 + i * 90  # X-frame orientation

            # Calculate arm endpoint
            arm_end_x = arm_length * math.cos(math.radians(angle))
            arm_end_y = arm_length * math.sin(math.radians(angle))

            # Create arm as box, then rotate
            arm_actual_length = arm_length - center_size / 2 * 0.707

            arm = (
                cq.Workplane("XY")
                .box(arm_actual_length, arm_width, arm_thickness)
                # Position to extend from center edge
                .translate((arm_actual_length / 2 + center_size / 2 * 0.707, 0, 0))
                # Rotate to correct angle
                .rotate((0, 0, 0), (0, 0, 1), angle)
            )

            # Add motor mount at end of arm
            motor_mount = (
                cq.Workplane("XY")
                .cylinder(arm_thickness, cfg.motor_mount / 2 + 5)  # Circular mount pad
                .translate((arm_end_x, arm_end_y, 0))
                # Motor mount holes
                .faces(">Z")
                .workplane()
                .center(arm_end_x, arm_end_y)
                .rect(cfg.motor_mount, cfg.motor_mount, forConstruction=True)
                .vertices()
                .hole(3.2)
                # Center hole for motor shaft
                .faces(">Z")
                .workplane()
                .center(arm_end_x, arm_end_y)
                .hole(8)
            )

            frame = frame.union(arm).union(motor_mount)

        self.frame = frame
        return frame


# ============== MAIN ==============
def create_quad_assembly(config_name: str = "5inch_freestyle") -> tuple:
    """
    Create a complete quadcopter assembly.

    Returns:
        (assembly, frame, components_dict)
    """
    config = CONFIGS.get(config_name, CONFIGS["5inch_freestyle"])

    # Create assembly
    quad = QuadcopterAssembly(config)

    # Add components at appropriate Z positions
    quad.add_esc(z_offset=-8)       # ESC at bottom of stack
    quad.add_fc(z_offset=0)          # FC above ESC
    quad.add_motors(z_offset=-6)     # Motors at frame level
    quad.add_props(z_offset=20)      # Props above motors
    quad.add_battery(z_offset=15)    # Battery on top

    # Generate frame
    frame = quad.generate_frame()

    return quad, frame, quad.get_component_models()


if __name__ == "__main__":
    from pathlib import Path

    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    print("Creating 5-inch freestyle quadcopter assembly...\n")

    quad, frame, components = create_quad_assembly("5inch_freestyle")

    print(f"Configuration: {quad.config.name}")
    print(f"  Wheelbase: {quad.config.wheelbase}mm")
    print(f"  Prop size: {quad.config.prop_size} inch")
    print(f"  Arm length: {quad.config.arm_length:.1f}mm")
    print(f"  Components: {list(components.keys())}")

    # Export frame
    frame_path = output_dir / "quad_frame_assembly.step"
    cq.exporters.export(frame, str(frame_path))
    print(f"\nFrame exported: {frame_path}")

    # Export STL
    stl_path = output_dir / "quad_frame_assembly.stl"
    cq.exporters.export(frame, str(stl_path))
    print(f"STL exported: {stl_path}")

    # For cq-editor: show components and frame separately
    try:
        # Show frame
        show_object(frame, name="Frame", options={"color": "yellow"})

        # Show each component
        for name, model in components.items():
            color = quad.components[name].get("color", "gray")
            show_object(model, name=name, options={"color": color})

    except NameError:
        # Not running in cq-editor
        pass

    print("\nOpen in cq-editor to visualize:")
    print(f"  cq-editor {__file__}")
