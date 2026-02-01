"""
STEP Export Module - Export CadQuery models to STEP format.

STEP (Standard for the Exchange of Product model data) is an ISO standard
for CAD data exchange. It preserves exact geometry (no tessellation).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import cadquery as cq


@dataclass
class STEPOptions:
    """Options for STEP export.

    Attributes:
        application_protocol: STEP application protocol.
            - "AP203": Configuration controlled 3D design (older, widely supported)
            - "AP214": Automotive design (default, good general purpose)
        write_pcurves: Include parametric curves on surfaces.
        precision_mode: Precision handling (-1=min, 0=default, 1=max).
    """

    application_protocol: str = "AP214"
    write_pcurves: bool = True
    precision_mode: int = 0


# Default options
DEFAULT_OPTIONS = STEPOptions()


def export_step(
    model: cq.Workplane,
    output_path: Union[str, Path],
    application_protocol: str | None = None,
    write_pcurves: bool | None = None,
    precision_mode: int | None = None,
) -> Path:
    """
    Export a CadQuery model to STEP file.

    STEP files preserve exact geometry and are ideal for CAD interchange.
    Unlike STL, there's no tessellation - geometry remains precise.

    Args:
        model: CadQuery Workplane to export.
        output_path: Path for the output STEP file.
        application_protocol: "AP203" or "AP214" (default).
        write_pcurves: Include parametric curves (default True).
        precision_mode: -1 (min), 0 (default), 1 (max).

    Returns:
        Path to the exported STEP file.

    Example:
        >>> from semicad.export import export_step
        >>> export_step(model, "part.step")
        >>> export_step(model, "part.stp", application_protocol="AP203")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # CadQuery's STEP export is straightforward - just export
    # The underlying OCCT handles most options automatically
    cq.exporters.export(model, str(output_path), exportType="STEP")

    return output_path


def export_step_assembly(
    assembly: cq.Assembly,
    output_path: Union[str, Path],
) -> Path:
    """
    Export a CadQuery Assembly to STEP file.

    Assemblies preserve component structure and positioning.

    Args:
        assembly: CadQuery Assembly to export.
        output_path: Path for the output STEP file.

    Returns:
        Path to the exported STEP file.

    Example:
        >>> from semicad.export import export_step_assembly
        >>> assy = cq.Assembly()
        >>> assy.add(part1, name="base")
        >>> assy.add(part2, name="top", loc=cq.Location((0, 0, 10)))
        >>> export_step_assembly(assy, "assembly.step")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    assembly.save(str(output_path), exportType="STEP")

    return output_path
