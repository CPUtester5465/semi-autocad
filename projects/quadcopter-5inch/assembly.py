#!/usr/bin/env python3
"""
Quadcopter Assembly
===================
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
from components import get_component


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
        fc = get_component("fc_f405_30x30")
        self.components.append(PositionedComponent(
            name="fc",
            model=fc,
            position=(0, 0, z_offset),
            color="green",
        ))
        return self

    def add_esc(self, z_offset: float = -8) -> "QuadcopterAssembly":
        """Add ESC below frame."""
        esc = get_component("esc_45a_30x30")
        self.components.append(PositionedComponent(
            name="esc",
            model=esc,
            position=(0, 0, z_offset),
            color="blue",
        ))
        return self

    def add_motors(self, z_offset: float = -4) -> "QuadcopterAssembly":
        """Add all 4 motors."""
        motor_model = get_component("motor_2207")

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
        prop_model = get_component("prop_5inch")

        for i, (mx, my) in enumerate(self.config.motor_positions):
            self.components.append(PositionedComponent(
                name=f"prop_{i+1}",
                model=prop_model,
                position=(mx, my, z_offset),
                color="red",
            ))
        return self

    def add_battery(self, z_offset: float = 20) -> "QuadcopterAssembly":
        """Add battery on top."""
        battery = get_component("battery_4s_1300")
        self.components.append(PositionedComponent(
            name="battery",
            model=battery,
            position=(0, 0, z_offset),
            color="orange",
        ))
        return self

    def add_fasteners(self) -> "QuadcopterAssembly":
        """Add mounting screws (from cq_warehouse)."""
        try:
            from semicad.sources.warehouse import WarehouseSource
            warehouse = WarehouseSource()

            # FC/ESC stack screws (M3x25)
            screw = warehouse.get_screw("M3-0.5", 25)
            screw_model = screw.geometry

            for x, y in [(15.25, 15.25), (-15.25, 15.25),
                         (15.25, -15.25), (-15.25, -15.25)]:
                self.components.append(PositionedComponent(
                    name=f"screw_stack_{x}_{y}",
                    model=screw_model,
                    position=(x, y, 15),
                    color="silver",
                ))
        except Exception as e:
            print(f"Note: Could not add fasteners: {e}")

        return self

    def build_full(self) -> "QuadcopterAssembly":
        """Build complete assembly with all components."""
        return (
            self.add_frame()
            .add_esc()
            .add_fc()
            .add_motors()
            .add_props()
            .add_battery()
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

        # Prop clearance
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

        # Export combined assembly
        combined = self.get_combined()
        cq.exporters.export(combined, str(output_dir / "assembly.step"))
        cq.exporters.export(combined, str(output_dir / "assembly.stl"))

        # Export frame only
        if self.frame:
            cq.exporters.export(self.frame, str(output_dir / "frame.step"))
            cq.exporters.export(self.frame, str(output_dir / "frame.stl"))

        print(f"Exported to {output_dir}")

    def show_in_editor(self):
        """Display in cq-editor (call from script)."""
        for comp in self.components:
            alpha = 0.3 if "prop" in comp.name else 1.0
            show_object(
                comp.positioned,
                name=comp.name,
                options={"color": comp.color, "alpha": alpha}
            )


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

    print("Building Quadcopter 5-inch Assembly")
    print("=" * 40)
    print(f"Wheelbase: {CONFIG.wheelbase}mm")
    print(f"Props: {CONFIG.prop_size} inch")
    print(f"Motors: {CONFIG.motor_size}")
    print()

    # Check clearances
    clearances = _assembly.check_clearances()
    print("Clearance Check:")
    for name, data in clearances.items():
        status = "✓" if data["ok"] else "⚠"
        print(f"  {status} {name}: {data['value']:.1f}mm (min: {data['min']}mm)")
    print()

    # Export
    _assembly.export(output_dir)

    print("\nTo visualize:")
    print(f"  cq-editor {__file__}")
