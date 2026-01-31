"""
Project commands - Project management and testing.
"""

import click


@click.group()
def project():
    """Project management commands."""
    pass


@project.command("info")
@click.pass_context
def info(ctx):
    """Show current project information."""
    proj = ctx.obj["project"]

    click.echo(f"Project: {proj.name}")
    click.echo(f"  Root: {proj.root}")
    click.echo(f"  Scripts: {proj.scripts_dir}")
    click.echo(f"  Output: {proj.output_dir}")

    subprojects = proj.list_subprojects()
    if subprojects:
        click.echo(f"  Sub-projects:")
        for sp in subprojects:
            click.echo(f"    - {sp}")


@project.command("list")
@click.pass_context
def list_projects(ctx):
    """List sub-projects."""
    proj = ctx.obj["project"]

    subprojects = proj.list_subprojects()
    if not subprojects:
        click.echo("No sub-projects found.")
        return

    click.echo("Sub-projects:")
    for sp in subprojects:
        click.echo(f"  - {sp}")


@project.command("neo4j")
def neo4j():
    """Open Neo4j browser."""
    import webbrowser

    url = "http://localhost:7475"
    click.echo(f"Opening Neo4j browser: {url}")
    click.echo("  User: neo4j")
    click.echo("  Pass: semicad2026")

    webbrowser.open(url)


@project.command("build")
@click.argument("subproject")
@click.option("--variant", "-v", default="freestyle", help="Build variant")
@click.option("--all-variants", is_flag=True, help="Build all variants")
@click.pass_context
def build_subproject(ctx, subproject, variant, all_variants):
    """Build a sub-project."""
    import subprocess
    import sys

    proj = ctx.obj["project"]
    subproject_dir = proj.projects_dir / subproject

    if not subproject_dir.exists():
        click.echo(f"Sub-project not found: {subproject}", err=True)
        click.echo(f"Available: {proj.list_subprojects()}")
        raise SystemExit(1)

    build_script = subproject_dir / "build.py"
    if not build_script.exists():
        click.echo(f"No build.py found in {subproject}", err=True)
        raise SystemExit(1)

    click.echo(f"Building sub-project: {subproject}")
    click.echo("=" * 50)

    # Run build script
    cmd = [sys.executable, str(build_script)]
    if all_variants:
        cmd.append("--export-all")
    else:
        cmd.extend(["--variant", variant])

    result = subprocess.run(cmd, cwd=str(subproject_dir))

    if result.returncode != 0:
        raise SystemExit(result.returncode)


@project.command("view")
@click.argument("subproject")
@click.option("--file", "-f", default="assembly.py", help="File to open")
@click.pass_context
def view_subproject(ctx, subproject, file):
    """Open sub-project in cq-editor."""
    import subprocess
    import os

    proj = ctx.obj["project"]
    subproject_dir = proj.projects_dir / subproject

    if not subproject_dir.exists():
        click.echo(f"Sub-project not found: {subproject}", err=True)
        raise SystemExit(1)

    target_file = subproject_dir / file
    if not target_file.exists():
        click.echo(f"File not found: {target_file}", err=True)
        raise SystemExit(1)

    # Set up environment
    env = os.environ.copy()
    pythonpath = f"{subproject_dir}:{proj.scripts_dir}:{proj.root}"
    if "PYTHONPATH" in env:
        pythonpath += f":{env['PYTHONPATH']}"
    env["PYTHONPATH"] = pythonpath

    click.echo(f"Opening cq-editor: {target_file}")
    subprocess.run(["cq-editor", str(target_file)], env=env)


@click.command()
@click.pass_context
def test(ctx):
    """Test all imports and dependencies."""
    proj = ctx.obj["project"]

    click.echo("Testing Semi-AutoCAD installation...")
    click.echo("=" * 50)

    errors = []

    # Test CadQuery
    click.echo("\n[1/5] CadQuery...")
    try:
        import cadquery as cq
        click.echo(f"  OK - version {cq.__version__ if hasattr(cq, '__version__') else 'unknown'}")
    except ImportError as e:
        click.echo(f"  FAIL - {e}")
        errors.append("cadquery")

    # Test cq_warehouse
    click.echo("\n[2/5] cq_warehouse...")
    try:
        from cq_warehouse.fastener import SocketHeadCapScrew
        from cq_warehouse.bearing import SingleRowDeepGrooveBallBearing
        click.echo("  OK - fasteners, bearings available")
    except ImportError as e:
        click.echo(f"  FAIL - {e}")
        errors.append("cq_warehouse")

    # Test cq_electronics
    click.echo("\n[3/5] cq_electronics...")
    try:
        from cq_electronics.rpi.rpi3b import RPi3b
        rpi = RPi3b()
        click.echo(f"  OK - RPi3b ({rpi.WIDTH}x{rpi.HEIGHT}mm)")
    except ImportError as e:
        click.echo(f"  FAIL - {e}")
        errors.append("cq_electronics")

    # Test PartCAD
    click.echo("\n[4/5] PartCAD...")
    try:
        import partcad as pc
        ctx_pc = pc.init(str(proj.root))
        click.echo("  OK - context initialized")
    except Exception as e:
        click.echo(f"  WARN - {e}")

    # Test custom components
    click.echo("\n[5/5] Custom components...")
    try:
        from scripts.components import COMPONENTS
        click.echo(f"  OK - {len(COMPONENTS)} components loaded")
    except ImportError as e:
        click.echo(f"  FAIL - {e}")
        errors.append("custom_components")

    # Summary
    click.echo("\n" + "=" * 50)
    if errors:
        click.echo(f"FAILED: {', '.join(errors)}")
        raise SystemExit(1)
    else:
        click.echo("All tests passed!")
