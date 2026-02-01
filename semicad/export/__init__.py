"""
Semi-AutoCAD Export Module.

Provides utilities for exporting CAD models to various formats:
- STEP: Exact geometry for CAD interchange
- STL: Tessellated mesh for 3D printing
- PNG: Rendered images for documentation
- BOM: Bill of Materials for manufacturing

Example:
    >>> from semicad.export import export_step, export_stl, STLQuality
    >>> export_step(model, "part.step")
    >>> export_stl(model, "part.stl", quality=STLQuality.FINE)

    >>> from semicad.export import render_stl_to_png, export_svg_views
    >>> render_stl_to_png("part.stl", "preview.png")
    >>> export_svg_views(model, "output/views")

    >>> from semicad.export import generate_bom, export_bom
    >>> bom = generate_bom(components)
    >>> export_bom(bom, "output/bom.csv")
"""

# STEP export
from semicad.export.step import (
    export_step,
    export_step_assembly,
    STEPOptions,
)

# STL export
from semicad.export.stl import (
    export_stl,
    STLQuality,
    STLOptions,
    QUALITY_PRESETS,
    get_quality_info,
    list_quality_presets,
)

# Rendering
from semicad.export.render import (
    export_svg_views,
    render_stl_to_png,
    render_stl_to_png_blender,
    render_model_to_png,
    RenderOptions,
    STANDARD_VIEWS,
)

# BOM generation
from semicad.export.bom import (
    generate_bom,
    export_bom,
    bom_to_csv,
    bom_to_json,
    bom_to_markdown,
    BOM,
    BOMEntry,
)

__all__ = [
    # STEP
    "export_step",
    "export_step_assembly",
    "STEPOptions",
    # STL
    "export_stl",
    "STLQuality",
    "STLOptions",
    "QUALITY_PRESETS",
    "get_quality_info",
    "list_quality_presets",
    # Rendering
    "export_svg_views",
    "render_stl_to_png",
    "render_stl_to_png_blender",
    "render_model_to_png",
    "RenderOptions",
    "STANDARD_VIEWS",
    # BOM
    "generate_bom",
    "export_bom",
    "bom_to_csv",
    "bom_to_json",
    "bom_to_markdown",
    "BOM",
    "BOMEntry",
]
