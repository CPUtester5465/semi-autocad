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
# BOM generation
from semicad.export.bom import (
    BOM,
    BOMEntry,
    bom_to_csv,
    bom_to_json,
    bom_to_markdown,
    export_bom,
    generate_bom,
)

# Rendering
from semicad.export.render import (
    STANDARD_VIEWS,
    RenderOptions,
    export_svg_views,
    render_model_to_png,
    render_stl_to_png,
    render_stl_to_png_blender,
)
from semicad.export.step import (
    STEPOptions,
    export_step,
    export_step_assembly,
)

# STL export
from semicad.export.stl import (
    QUALITY_PRESETS,
    STLOptions,
    STLQuality,
    export_stl,
    get_quality_info,
    list_quality_presets,
)

__all__ = [
    "BOM",
    "QUALITY_PRESETS",
    "STANDARD_VIEWS",
    "BOMEntry",
    "RenderOptions",
    "STEPOptions",
    "STLOptions",
    "STLQuality",
    "bom_to_csv",
    "bom_to_json",
    "bom_to_markdown",
    "export_bom",
    # STEP
    "export_step",
    "export_step_assembly",
    # STL
    "export_stl",
    # Rendering
    "export_svg_views",
    # BOM
    "generate_bom",
    "get_quality_info",
    "list_quality_presets",
    "render_model_to_png",
    "render_stl_to_png",
    "render_stl_to_png_blender",
]
