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
@click.pass_context
def render(ctx, input_file, output, resolution):
    """Render STL/STEP to PNG image."""
    project = ctx.obj["project"]

    input_path = Path(input_file)
    if output:
        output_path = Path(output)
    else:
        output_path = project.output_dir / f"{input_path.stem}.png"

    width, height = map(int, resolution.split("x"))

    click.echo(f"Rendering {input_path.name} to PNG...")

    try:
        import trimesh

        mesh = trimesh.load(str(input_path))
        scene = mesh.scene()
        png = scene.save_image(resolution=[width, height])

        with open(output_path, "wb") as f:
            f.write(png)

        click.echo(f"Saved to: {output_path}")

    except ImportError:
        click.echo("trimesh not installed. Run: pip install trimesh", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Render failed: {e}", err=True)
        raise SystemExit(1)


@click.command()
@click.argument("component")
@click.option("--format", "-f", type=click.Choice(["step", "stl", "both"]), default="both")
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.pass_context
def export(ctx, component, format, output):
    """Export a component to STEP/STL."""
    from semicad.core.registry import get_registry
    import cadquery as cq

    project = ctx.obj["project"]
    output_dir = Path(output) if output else project.output_dir
    registry = get_registry()

    click.echo(f"Exporting component: {component}")

    try:
        comp = registry.get(component)
        geometry = comp.geometry

        if format in ("step", "both"):
            step_file = output_dir / f"{comp.name}.step"
            cq.exporters.export(geometry, str(step_file))
            click.echo(f"  STEP: {step_file}")

        if format in ("stl", "both"):
            stl_file = output_dir / f"{comp.name}.stl"
            cq.exporters.export(geometry, str(stl_file))
            click.echo(f"  STL: {stl_file}")

    except KeyError as e:
        click.echo(f"Component not found: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Export failed: {e}", err=True)
        raise SystemExit(1)
