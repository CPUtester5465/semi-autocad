"""
Build commands - Generate and export CAD files.
"""

from pathlib import Path

import click

from semicad.cli import verbose_echo


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
    verbose_echo(ctx, f"Looking for build script: {build_script}")

    if build_script.exists():
        import os
        import subprocess

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project.scripts_dir}:{project.root}"

        verbose_echo(ctx, f"PYTHONPATH: {env['PYTHONPATH']}")
        verbose_echo(ctx, f"Working directory: {project.root}")
        verbose_echo(ctx, f"Running: python {build_script}")

        result = subprocess.run(
            ["python", str(build_script)],
            env=env,
            cwd=str(project.root),
        )

        verbose_echo(ctx, f"Build script exit code: {result.returncode}")

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

    verbose_echo(ctx, f"Input file: {input_path}")
    verbose_echo(ctx, f"Output file: {output_path}")
    verbose_echo(ctx, f"Resolution: {width}x{height}")
    verbose_echo(ctx, f"Method: {method}")

    click.echo(f"Rendering {input_path.name} to PNG ({method})...")

    if method == "blender":
        verbose_echo(ctx, f"Using Blender renderer with resolution={max(width, height)}")
        result = render_stl_to_png_blender(input_path, output_path, resolution=max(width, height))
    else:
        verbose_echo(ctx, f"Using trimesh renderer with width={width}, height={height}")
        result = render_stl_to_png(input_path, output_path, width=width, height=height)

    if result:
        click.echo(f"Saved to: {result}")
        verbose_echo(ctx, "Render completed successfully")
    else:
        click.echo("Render failed. Check error messages above.", err=True)
        raise SystemExit(1)


def parse_param(ctx, param, value):
    """Parse KEY=VALUE parameter pairs into a dictionary."""
    if not value:
        return {}
    params = {}
    for item in value:
        if "=" not in item:
            raise click.BadParameter(f"Invalid parameter format: {item}. Use KEY=VALUE")
        key, val = item.split("=", 1)
        # Try to convert to appropriate type
        try:
            # Try int first
            params[key] = int(val)
        except ValueError:
            try:
                # Then float
                params[key] = float(val)
            except ValueError:
                # Handle booleans
                if val.lower() in ("true", "yes", "1"):
                    params[key] = True
                elif val.lower() in ("false", "no", "0"):
                    params[key] = False
                else:
                    # Keep as string
                    params[key] = val
    return params


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
@click.option(
    "--param", "-p",
    multiple=True,
    help="Component parameter as KEY=VALUE (can be repeated)",
)
@click.pass_context
def export(ctx, component, format, output, quality, tolerance, angular_tolerance, param):
    """
    Export a component to STEP/STL.

    For parametric components, use --param to specify required parameters:

        ./bin/dev export BGA --param length=10 --param width=10

    Or use the short form:

        ./bin/dev export BGA -p length=10 -p width=10
    """
    from semicad.core.registry import get_registry
    from semicad.export import STLQuality, export_step, export_stl

    project = ctx.obj["project"]
    output_dir = Path(output) if output else project.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    verbose_echo(ctx, f"Output directory: {output_dir}")
    verbose_echo(ctx, "Initializing component registry...")

    registry = get_registry()

    verbose_echo(ctx, f"Registry sources: {registry.sources}")

    # Parse component parameters
    comp_params = parse_param(ctx, None, param)

    # Map quality string to enum
    quality_map = {
        "draft": STLQuality.DRAFT,
        "normal": STLQuality.NORMAL,
        "fine": STLQuality.FINE,
        "ultra": STLQuality.ULTRA,
    }
    stl_quality = quality_map[quality]

    verbose_echo(ctx, f"STL quality: {quality} -> {stl_quality}")
    if tolerance:
        verbose_echo(ctx, f"Linear tolerance override: {tolerance}")
    if angular_tolerance:
        verbose_echo(ctx, f"Angular tolerance override: {angular_tolerance}")

    click.echo(f"Exporting component: {component}")
    if comp_params:
        click.echo(f"  Parameters: {comp_params}")

    try:
        verbose_echo(ctx, f"Looking up component: {component}")
        if comp_params:
            verbose_echo(ctx, f"With parameters: {comp_params}")
        comp = registry.get(component, **comp_params)
        verbose_echo(ctx, f"Found component: {comp.name} (source: {comp.spec.source})")
        verbose_echo(ctx, "Generating geometry...")
        geometry = comp.geometry
        verbose_echo(ctx, "Geometry generated successfully")

        if format in ("step", "both"):
            step_file = output_dir / f"{comp.name}.step"
            verbose_echo(ctx, f"Exporting STEP to: {step_file}")
            export_step(geometry, step_file)
            click.echo(f"  STEP: {step_file}")

        if format in ("stl", "both"):
            stl_file = output_dir / f"{comp.name}.stl"
            verbose_echo(ctx, f"Exporting STL to: {stl_file}")
            export_stl(
                geometry,
                stl_file,
                quality=stl_quality,
                tolerance=tolerance,
                angular_tolerance=angular_tolerance,
            )
            click.echo(f"  STL: {stl_file} (quality: {quality})")

    except KeyError as e:
        verbose_echo(ctx, "Component lookup failed in all sources")
        click.echo(f"Component not found: {e}", err=True)
        raise SystemExit(1)
    except ValueError as e:
        # Handle missing required parameters with helpful message
        click.echo(f"Parameter error: {e}", err=True)
        # Try to show available info about the component
        try:
            spec = registry.get_spec(component)
            if spec.params and "required" in spec.params:
                click.echo(f"\nRequired parameters for {component}: {spec.params['required']}")
                click.echo("\nExample:")
                example_params = " ".join(f"-p {p}=<value>" for p in spec.params["required"])
                click.echo(f"  ./bin/dev export {component} {example_params}")
        except KeyError:
            pass
        raise SystemExit(1)
    except Exception as e:
        verbose_echo(ctx, f"Exception type: {type(e).__name__}")
        click.echo(f"Export failed: {e}", err=True)
        raise SystemExit(1)
