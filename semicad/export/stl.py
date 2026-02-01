"""
STL Export Module - Export CadQuery models to STL with quality options.

STL (Standard Tessellation Language) files represent 3D surfaces as triangular meshes.
Quality settings control the mesh density vs file size tradeoff.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import cadquery as cq


class STLQuality(Enum):
    """Predefined quality presets for STL export."""

    DRAFT = "draft"  # Fast, rough mesh for quick previews
    NORMAL = "normal"  # Balanced quality/size (default)
    FINE = "fine"  # High quality for detailed parts
    ULTRA = "ultra"  # Maximum quality for precision work


@dataclass
class STLOptions:
    """Options for STL export.

    Attributes:
        tolerance: Linear deflection - max distance between mesh and real surface.
                   Lower values = finer mesh. Units match model units (usually mm).
        angular_tolerance: Angular deflection - max angle (radians) between adjacent
                           triangle normals. Lower values = smoother curves.
        ascii: If True, export ASCII STL (larger but human-readable).
               If False (default), export binary STL (smaller, faster).
    """

    tolerance: float = 0.1
    angular_tolerance: float = 0.1
    ascii: bool = False


# Quality presets mapping
QUALITY_PRESETS: dict[STLQuality, STLOptions] = {
    STLQuality.DRAFT: STLOptions(tolerance=0.5, angular_tolerance=0.5),
    STLQuality.NORMAL: STLOptions(tolerance=0.1, angular_tolerance=0.1),
    STLQuality.FINE: STLOptions(tolerance=0.01, angular_tolerance=0.05),
    STLQuality.ULTRA: STLOptions(tolerance=0.001, angular_tolerance=0.01),
}


def export_stl(
    model: cq.Workplane,
    output_path: str | Path,
    quality: STLQuality = STLQuality.NORMAL,
    tolerance: float | None = None,
    angular_tolerance: float | None = None,
    ascii: bool = False,
) -> Path:
    """
    Export a CadQuery model to STL file.

    Args:
        model: CadQuery Workplane to export.
        output_path: Path for the output STL file.
        quality: Quality preset (DRAFT, NORMAL, FINE, ULTRA).
        tolerance: Override preset's linear tolerance (optional).
        angular_tolerance: Override preset's angular tolerance (optional).
        ascii: If True, write ASCII STL. Default is binary.

    Returns:
        Path to the exported STL file.

    Example:
        >>> from semicad.export import export_stl, STLQuality
        >>> export_stl(model, "part.stl", quality=STLQuality.FINE)
        >>> export_stl(model, "part.stl", tolerance=0.05)  # Custom tolerance
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get base options from preset
    options = QUALITY_PRESETS[quality]

    # Override with explicit values if provided
    tol = tolerance if tolerance is not None else options.tolerance
    ang_tol = angular_tolerance if angular_tolerance is not None else options.angular_tolerance

    # Export using CadQuery
    cq.exporters.export(
        model,
        str(output_path),
        exportType="STL",
        tolerance=tol,
        angularTolerance=ang_tol,
    )

    return output_path


def get_quality_info(quality: STLQuality) -> dict[str, str | float]:
    """Get information about a quality preset.

    Args:
        quality: The quality preset to describe.

    Returns:
        Dict with tolerance values and description.
    """
    options = QUALITY_PRESETS[quality]
    descriptions = {
        STLQuality.DRAFT: "Fast preview, rough mesh. Good for quick checks.",
        STLQuality.NORMAL: "Balanced quality and file size. Good default for 3D printing.",
        STLQuality.FINE: "High quality mesh. Good for detailed parts.",
        STLQuality.ULTRA: "Maximum precision. Large files, smooth surfaces.",
    }

    return {
        "quality": quality.value,
        "tolerance": options.tolerance,
        "angular_tolerance": options.angular_tolerance,
        "description": descriptions[quality],
    }


def list_quality_presets() -> list[dict[str, str | float]]:
    """List all available quality presets with their settings."""
    return [get_quality_info(q) for q in STLQuality]
