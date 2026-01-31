#!/usr/bin/env python3
"""
CAD View Export Utility
=======================
Export CadQuery models to PNG images using different backends.

Methods:
1. SVG export (built-in CadQuery) - Fast, 2D orthographic views
2. OCP/vtk (if available) - 3D rendered views
3. trimesh + pyrender - STL to PNG rendering

Usage:
    from export_views import export_png_views, export_svg_views

    result = cq.Workplane("XY").box(10, 10, 10)
    export_svg_views(result, "output/box")
"""

import cadquery as cq
from pathlib import Path
from typing import Union, Optional
import subprocess
import tempfile


def export_svg_views(
    model: cq.Workplane,
    output_prefix: str,
    width: int = 800,
    height: int = 600,
) -> dict[str, Path]:
    """
    Export orthographic SVG views of a CadQuery model.
    Uses built-in CadQuery SVG export - no extra dependencies.

    Args:
        model: CadQuery Workplane to export
        output_prefix: Path prefix for output files (e.g., "output/frame")
        width: SVG width in pixels
        height: SVG height in pixels

    Returns:
        Dict mapping view name to file path
    """
    output_dir = Path(output_prefix).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = Path(output_prefix).name

    views = {
        "top": (0, 0, 1),      # Looking down Z
        "front": (0, -1, 0),   # Looking along Y
        "right": (1, 0, 0),    # Looking along X
        "iso": (1, 1, 1),      # Isometric
    }

    exported = {}

    for view_name, direction in views.items():
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
                }
            )
            exported[view_name] = output_path
            print(f"  Exported: {output_path}")
        except Exception as e:
            print(f"  Failed {view_name}: {e}")

    return exported


def export_stl(model: cq.Workplane, output_path: Union[str, Path]) -> Path:
    """Export model to STL file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(model, str(output_path))
    return output_path


def export_step(model: cq.Workplane, output_path: Union[str, Path]) -> Path:
    """Export model to STEP file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(model, str(output_path))
    return output_path


def stl_to_png_trimesh(
    stl_path: Union[str, Path],
    output_path: Union[str, Path],
    resolution: tuple[int, int] = (800, 600),
) -> Optional[Path]:
    """
    Render STL to PNG using trimesh.
    Requires: pip install trimesh "pyglet<2"

    Args:
        stl_path: Path to STL file
        output_path: Path for output PNG
        resolution: (width, height) in pixels

    Returns:
        Path to PNG file, or None if failed
    """
    try:
        import trimesh

        # Load mesh
        mesh = trimesh.load(str(stl_path))

        # Create scene
        scene = mesh.scene()

        # Render
        png_data = scene.save_image(resolution=list(resolution))

        # Save
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(png_data)

        return output_path

    except ImportError as e:
        print(f"trimesh not available: {e}")
        print("Install with: pip install trimesh 'pyglet<2'")
        return None
    except Exception as e:
        print(f"Rendering failed: {e}")
        return None


def stl_to_png_blender(
    stl_path: Union[str, Path],
    output_path: Union[str, Path],
    resolution: int = 800,
) -> Optional[Path]:
    """
    Render STL to PNG using Blender (if installed).

    Args:
        stl_path: Path to STL file
        output_path: Path for output PNG
        resolution: Image size (square)

    Returns:
        Path to PNG file, or None if failed
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

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
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
        return None


def export_all_formats(
    model: cq.Workplane,
    output_prefix: str,
    png_method: str = "svg",  # "svg", "trimesh", "blender"
) -> dict[str, Path]:
    """
    Export model to all useful formats.

    Args:
        model: CadQuery model
        output_prefix: Base path for outputs (e.g., "output/frame")
        png_method: Method for PNG generation

    Returns:
        Dict of format -> file path
    """
    output_dir = Path(output_prefix).parent
    base_name = Path(output_prefix).name
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    # STEP (for CAD import)
    step_path = output_dir / f"{base_name}.step"
    cq.exporters.export(model, str(step_path))
    results["step"] = step_path
    print(f"Exported STEP: {step_path}")

    # STL (for 3D printing)
    stl_path = output_dir / f"{base_name}.stl"
    cq.exporters.export(model, str(stl_path))
    results["stl"] = stl_path
    print(f"Exported STL: {stl_path}")

    # PNG views
    if png_method == "svg":
        svg_views = export_svg_views(model, output_prefix)
        results["views"] = svg_views
    elif png_method == "trimesh":
        png_path = output_dir / f"{base_name}_render.png"
        result = stl_to_png_trimesh(stl_path, png_path)
        if result:
            results["png"] = result
    elif png_method == "blender":
        png_path = output_dir / f"{base_name}_render.png"
        result = stl_to_png_blender(stl_path, png_path)
        if result:
            results["png"] = result

    return results


# ============== TEST ==============
if __name__ == "__main__":
    print("Testing export utilities...\n")

    # Create test model
    test_model = (
        cq.Workplane("XY")
        .box(20, 30, 10)
        .edges("|Z")
        .fillet(2)
        .faces(">Z")
        .workplane()
        .hole(5)
    )

    output_prefix = Path(__file__).parent.parent / "output" / "test_export"

    print("Exporting SVG views...")
    export_svg_views(test_model, str(output_prefix))

    print("\nExporting STEP and STL...")
    export_step(test_model, output_prefix.with_suffix(".step"))
    export_stl(test_model, output_prefix.with_suffix(".stl"))

    print("\nDone!")
