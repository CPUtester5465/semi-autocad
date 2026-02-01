"""
Build commands - Generate and export CAD files.
"""

import click
from pathlib import Path


@click.command()
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.pass_context
def build(ctx, output):
    """Build all project assemblies to STEP/STL."""
    project = ctx.obj["project"]
    output_dir = Path(output) if output else project.output_dir

    click.echo(f"Building project: {project.name}")
    click.echo(f"Output directory: {output_dir}")

    # Find and run build script
    build_script = project.scripts_dir / "quadcopter_assembly.py"
    if build_script.exists():
        import subprocess
        import os

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project.scripts_dir}:{project.root}"

        result = subprocess.run(
            ["python", str(build_script)],
            env=env,
            cwd=str(project.root),
        )

        if result.returncode == 0:
            click.echo("\nBuild complete. Output files:")
            for f in output_dir.glob("*.step"):
                click.echo(f"  {f.name}")
            for f in output_dir.glob("*.stl"):
                click.echo(f"  {f.name}")
    else:
        click.echo("No build script found.", err=True)


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output PNG file")
@click.option("--resolution", "-r", default="1024x768", help="Resolution (WxH)")
@click.option(
    "--method",
    "-m",
    type=click.Choice(["trimesh", "blender"]),
    default="trimesh",
    help="Rendering method",
)
@click.pass_context
def render(ctx, input_file, output, resolution, method):
    """Render STL/STEP to PNG image."""
    from semicad.export import render_stl_to_png, render_stl_to_png_blender

    project = ctx.obj["project"]

    input_path = Path(input_file)
    if output:
        output_path = Path(output)
    else:
        output_path = project.output_dir / f"{input_path.stem}.png"

    width, height = map(int, resolution.split("x"))

    click.echo(f"Rendering {input_path.name} to PNG ({method})...")

    if method == "blender":
        result = render_stl_to_png_blender(input_path, output_path, resolution=max(width, height))
    else:
        result = render_stl_to_png(input_path, output_path, width=width, height=height)

    if result:
        click.echo(f"Saved to: {result}")
    else:
        click.echo("Render failed. Check error messages above.", err=True)
        raise SystemExit(1)


@click.command()
@click.argument("component")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["step", "stl", "both"]),
    default="both",
    help="Export format",
)
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["draft", "normal", "fine", "ultra"]),
    default="normal",
    help="STL mesh quality",
)
@click.option("--tolerance", "-t", type=float, help="Override STL linear tolerance")
@click.option("--angular-tolerance", type=float, help="Override STL angular tolerance")
@click.pass_context
def export(ctx, component, format, output, quality, tolerance, angular_tolerance):
    """Export a component to STEP/STL."""
    from semicad.core.registry import get_registry
    from semicad.export import export_step, export_stl, STLQuality

    project = ctx.obj["project"]
    output_dir = Path(output) if output else project.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = get_registry()

    # Map quality string to enum
    quality_map = {
        "draft": STLQuality.DRAFT,
        "normal": STLQuality.NORMAL,
        "fine": STLQuality.FINE,
        "ultra": STLQuality.ULTRA,
    }
    stl_quality = quality_map[quality]

    click.echo(f"Exporting component: {component}")

    try:
        comp = registry.get(component)
        geometry = comp.geometry

        if format in ("step", "both"):
            step_file = output_dir / f"{comp.name}.step"
            export_step(geometry, step_file)
            click.echo(f"  STEP: {step_file}")

        if format in ("stl", "both"):
            stl_file = output_dir / f"{comp.name}.stl"
            export_stl(
                geometry,
                stl_file,
                quality=stl_quality,
                tolerance=tolerance,
                angular_tolerance=angular_tolerance,
            )
            click.echo(f"  STL: {stl_file} (quality: {quality})")

    except KeyError as e:
        click.echo(f"Component not found: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Export failed: {e}", err=True)
        raise SystemExit(1)
