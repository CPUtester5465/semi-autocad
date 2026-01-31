#!/usr/bin/env python3
"""
EnclosureTest Assembly

Positions enclosure body and lid together.

Usage:
    python assembly.py           # Export full assembly
    cq-editor assembly.py        # Interactive visualization
"""

import cadquery as cq
from pathlib import Path
from dataclasses import dataclass

# Add paths for imports
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG, EnclosureConfig
from frame import generate_body, generate_lid


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


class EnclosureAssembly:
    """
    Complete enclosure assembly manager.

    Handles component positioning and export.
    """

    def __init__(self, config: EnclosureConfig = CONFIG):
        self.config = config
        self.components: list[PositionedComponent] = []
        self.body: cq.Workplane | None = None
        self.lid: cq.Workplane | None = None

    def add_body(self) -> "EnclosureAssembly":
        """Add the enclosure body."""
        self.body = generate_body(self.config)
        self.components.append(PositionedComponent(
            name="body",
            model=self.body,
            position=(0, 0, 0),
            color="steelblue",
        ))
        return self

    def add_lid(self, open_position: bool = False) -> "EnclosureAssembly":
        """Add the lid, optionally in open position."""
        self.lid = generate_lid(self.config)

        if open_position:
            # Position lid above body with gap
            z_offset = self.config.body_depth/2 + self.config.lid_height/2 + 10
        else:
            # Position lid closed on body
            z_offset = self.config.body_depth/2 + self.config.lid_height/2 - self.config.lid_lip

        self.components.append(PositionedComponent(
            name="lid",
            model=self.lid,
            position=(0, 0, z_offset),
            color="lightblue",
        ))
        return self

    def build_full(self, open_lid: bool = True) -> "EnclosureAssembly":
        """Build complete assembly."""
        return self.add_body().add_lid(open_position=open_lid)

    def get_combined(self) -> cq.Workplane:
        """Combine all components into single geometry."""
        if not self.components:
            raise ValueError("No components in assembly")

        combined = self.components[0].positioned
        for comp in self.components[1:]:
            combined = combined.union(comp.positioned)
        return combined

    def export(self, output_dir: Path):
        """Export assembly and individual parts to files."""
        output_dir.mkdir(exist_ok=True)

        # Export combined assembly
        combined = self.get_combined()
        cq.exporters.export(combined, str(output_dir / "assembly.step"))
        cq.exporters.export(combined, str(output_dir / "assembly.stl"))

        # Export individual parts
        if self.body:
            cq.exporters.export(self.body, str(output_dir / "body.step"))
            cq.exporters.export(self.body, str(output_dir / "body.stl"))

        if self.lid:
            cq.exporters.export(self.lid, str(output_dir / "lid.step"))
            cq.exporters.export(self.lid, str(output_dir / "lid.stl"))

        print(f"Exported to {output_dir}")


def create_assembly(config: EnclosureConfig = CONFIG) -> EnclosureAssembly:
    """Factory function to create full assembly."""
    return EnclosureAssembly(config).build_full()


# === Main / cq-editor ===

# Create assembly for visualization
_assembly = create_assembly()

# For cq-editor: show components
try:
    for comp in _assembly.components:
        alpha = 0.8 if comp.name == "lid" else 1.0
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

    print("Building EnclosureTest Assembly")
    print("=" * 40)
    print(f"External: {CONFIG.width} x {CONFIG.height} x {CONFIG.depth} mm")
    print(f"Wall thickness: {CONFIG.wall_thickness}mm")
    print(f"Lid style: {CONFIG.lid_style}")
    print()

    _assembly.export(output_dir)

    print("\nTo visualize:")
    print(f"  cq-editor {__file__}")
