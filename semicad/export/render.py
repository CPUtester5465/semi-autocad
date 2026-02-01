"""
Render Module - Generate PNG images from CAD models.

Supports multiple rendering backends:
- SVG export (built-in CadQuery) - Fast 2D orthographic views
- trimesh - 3D rendered views from STL files
- Blender - High-quality renders (requires external Blender installation)
"""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq


@dataclass
class RenderOptions:
    """Options for PNG rendering.

    Attributes:
        width: Image width in pixels.
        height: Image height in pixels.
    """

    width: int = 800
    height: int = 600


# Standard orthographic views
STANDARD_VIEWS = {
    "top": (0, 0, 1),  # Looking down Z
    "bottom": (0, 0, -1),  # Looking up Z
    "front": (0, -1, 0),  # Looking along Y
    "back": (0, 1, 0),  # Looking along -Y
    "right": (1, 0, 0),  # Looking along X
    "left": (-1, 0, 0),  # Looking along -X
    "iso": (1, 1, 1),  # Isometric
    "iso_back": (-1, -1, 1),  # Isometric from back
}


def export_svg_views(
    model: cq.Workplane,
    output_prefix: str | Path,
    views: list[str] | None = None,
    width: int = 800,
    height: int = 600,
) -> dict[str, Path]:
    """
    Export orthographic SVG views of a CadQuery model.

    Uses built-in CadQuery SVG export - no extra dependencies required.

    Args:
        model: CadQuery Workplane to export.
        output_prefix: Path prefix for output files (e.g., "output/frame").
        views: List of view names to export. Default: ["top", "front", "right", "iso"]
        width: SVG width in pixels.
        height: SVG height in pixels.

    Returns:
        Dict mapping view name to file path.

    Example:
        >>> export_svg_views(model, "output/part")
        {'top': Path('output/part_top.svg'), 'front': ...}
        >>> export_svg_views(model, "output/part", views=["iso", "top"])
    """
    output_dir = Path(output_prefix).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = Path(output_prefix).name

    if views is None:
        views = ["top", "front", "right", "iso"]

    exported = {}

    for view_name in views:
        if view_name not in STANDARD_VIEWS:
            print(f"  Unknown view '{view_name}', skipping. Available: {list(STANDARD_VIEWS.keys())}")
            continue

        direction = STANDARD_VIEWS[view_name]
        output_path = output_dir / f"{base_name}_{view_name}.svg"

        try:
            cq.exporters.export(
                model,
                str(output_path),
                exportType="SVG",
                opt={
                    "width": width,
                    "height": height,
                    "projectionDir": direction,
                    "showAxes": False,
                    "showHidden": False,
                },
            )
            exported[view_name] = output_path
        except Exception as e:
            print(f"  Failed {view_name}: {e}")

    return exported


def render_stl_to_png(
    stl_path: str | Path,
    output_path: str | Path,
    width: int = 800,
    height: int = 600,
) -> Path | None:
    """
    Render STL to PNG using trimesh.

    Requires: pip install trimesh "pyglet<2"

    Args:
        stl_path: Path to STL file.
        output_path: Path for output PNG.
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        Path to PNG file, or None if failed.

    Example:
        >>> render_stl_to_png("part.stl", "part.png")
        Path('part.png')
    """
    try:
        import trimesh

        mesh = trimesh.load(str(stl_path))
        scene = mesh.scene()
        png_data = scene.save_image(resolution=[width, height])

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(png_data)

        return output_path

    except ImportError as e:
        print(f"trimesh not available: {e}")
        print("Install with: pip install trimesh 'pyglet<2'")
        return None
    except Exception as e:
        print(f"Rendering failed: {e}")
        return None


def render_stl_to_png_blender(
    stl_path: str | Path,
    output_path: str | Path,
    resolution: int = 800,
) -> Path | None:
    """
    Render STL to PNG using Blender.

    Requires Blender to be installed and available in PATH.

    Args:
        stl_path: Path to STL file.
        output_path: Path for output PNG.
        resolution: Image size (square).

    Returns:
        Path to PNG file, or None if failed.

    Example:
        >>> render_stl_to_png_blender("part.stl", "part.png", resolution=1024)
    """
    stl_path = Path(stl_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if Blender is available
    try:
        subprocess.run(["blender", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Blender not found in PATH")
        return None

    # Blender script for rendering
    blender_script = f'''
import bpy
import math

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import STL
try:
    bpy.ops.wm.stl_import(filepath="{stl_path}")
except:
    bpy.ops.import_mesh.stl(filepath="{stl_path}")

obj = bpy.context.selected_objects[0] if bpy.context.selected_objects else bpy.data.objects[-1]

# Center and scale
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
scale = 1.0 / max(obj.dimensions)
obj.scale = (scale, scale, scale)
obj.location = (0, 0, 0)

# Add camera
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (2, 2, 1.5)
cam.rotation_euler = (math.radians(60), 0, math.radians(45))

# Add light
light_data = bpy.data.lights.new("Light", type='SUN')
light = bpy.data.objects.new("Light", light_data)
bpy.context.scene.collection.objects.link(light)
light.location = (3, 3, 5)

# Render settings
bpy.context.scene.render.resolution_x = {resolution}
bpy.context.scene.render.resolution_y = {resolution}
bpy.context.scene.render.filepath = "{output_path}"
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Render
bpy.ops.render.render(write_still=True)
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(blender_script)
        script_path = f.name

    try:
        result = subprocess.run(
            ["blender", "-b", "-P", script_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        Path(script_path).unlink()

        if output_path.exists():
            return output_path
        else:
            print(f"Blender render failed: {result.stderr}")
            return None

    except Exception as e:
        print(f"Blender render failed: {e}")
        Path(script_path).unlink(missing_ok=True)
        return None


def render_model_to_png(
    model: cq.Workplane,
    output_path: str | Path,
    width: int = 800,
    height: int = 600,
    method: str = "trimesh",
) -> Path | None:
    """
    Render a CadQuery model directly to PNG.

    This exports to a temporary STL, then renders it.

    Args:
        model: CadQuery Workplane to render.
        output_path: Path for output PNG.
        width: Image width in pixels.
        height: Image height in pixels.
        method: Rendering method ("trimesh" or "blender").

    Returns:
        Path to PNG file, or None if failed.

    Example:
        >>> render_model_to_png(model, "preview.png")
    """
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
        stl_path = Path(f.name)

    try:
        # Export to temp STL
        cq.exporters.export(model, str(stl_path))

        # Render based on method
        if method == "blender":
            result = render_stl_to_png_blender(stl_path, output_path, resolution=max(width, height))
        else:
            result = render_stl_to_png(stl_path, output_path, width, height)

        return result
    finally:
        stl_path.unlink(missing_ok=True)
