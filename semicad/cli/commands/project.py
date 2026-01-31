"""
Project commands - Project management and testing.
"""

import click

from semicad.templates import (
    TEMPLATES,
    scaffold_project,
    validate_project_name,
    remove_project,
    sync_partcad,
)


@click.group()
def project():
    """Project management commands."""
    pass


@project.command("new")
@click.argument("name")
@click.option(
    "--template", "-t",
    type=click.Choice(TEMPLATES),
    default="basic",
    help="Project template to use"
)
@click.option(
    "--description", "-d",
    default="",
    help="Project description"
)
@click.pass_context
def new_project(ctx, name, template, description):
    """Create a new sub-project from a template.

    NAME is the project name (e.g., 'drone-7inch', 'controller-box').

    Examples:

        ./bin/dev project new my-widget

        ./bin/dev project new drone-7inch --template quadcopter

        ./bin/dev project new sensor-box --template enclosure -d "Weatherproof sensor housing"
    """
    proj = ctx.obj["project"]

    # Validate name
    is_valid, result = validate_project_name(name)
    if not is_valid:
        click.echo(f"Error: {result}", err=True)
        raise SystemExit(1)

    normalized_name = result

    # Check if already exists
    project_dir = proj.projects_dir / normalized_name
    if project_dir.exists():
        click.echo(f"Error: Project '{normalized_name}' already exists at {project_dir}", err=True)
        raise SystemExit(1)

    # Create the project
    click.echo(f"Creating new project: {normalized_name}")
    click.echo(f"  Template: {template}")
    click.echo(f"  Location: {project_dir}")
    click.echo()

    try:
        created_dir = scaffold_project(
            name=name,
            template_name=template,
            project_root=proj.root,
            description=description,
        )

        click.echo("Created files:")
        for f in sorted(created_dir.iterdir()):
            click.echo(f"  - {f.name}")

        click.echo()
        click.echo("Project created successfully!")
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  1. Edit configuration: projects/{normalized_name}/config.py")
        click.echo(f"  2. View in cq-editor:  ./bin/dev project view {normalized_name}")
        click.echo(f"  3. Build outputs:      ./bin/dev project build {normalized_name}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error creating project: {e}", err=True)
        raise SystemExit(1)


@project.command("remove")
@click.argument("name")
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Skip confirmation prompt"
)
@click.pass_context
def remove_project_cmd(ctx, name, force):
    """Remove a sub-project completely.

    This will delete the project directory and remove the entry from partcad.yaml.

    Examples:

        ./bin/dev project remove my-widget

        ./bin/dev project remove old-project --force
    """
    proj = ctx.obj["project"]

    # Validate name
    is_valid, result = validate_project_name(name)
    if not is_valid:
        click.echo(f"Error: {result}", err=True)
        raise SystemExit(1)

    normalized_name = result
    project_dir = proj.projects_dir / normalized_name

    # Check what exists
    dir_exists = project_dir.exists()

    if not dir_exists:
        click.echo(f"Project directory not found: {project_dir}")
        click.echo("Checking for stale partcad.yaml entry...")

        # Try to remove just the partcad entry
        from semicad.templates import remove_from_partcad
        if remove_from_partcad(proj.root, normalized_name):
            click.echo(f"Removed stale entry '{normalized_name}' from partcad.yaml")
        else:
            click.echo(f"No entry found for '{normalized_name}' in partcad.yaml")
        return

    # Confirm deletion
    if not force:
        # List files that will be deleted
        files = list(project_dir.iterdir())
        click.echo(f"This will permanently delete project '{normalized_name}':")
        click.echo(f"  Directory: {project_dir}")
        click.echo(f"  Files: {len(files)} items")
        for f in sorted(files)[:10]:
            click.echo(f"    - {f.name}")
        if len(files) > 10:
            click.echo(f"    ... and {len(files) - 10} more")
        click.echo()

        if not click.confirm("Are you sure you want to delete this project?"):
            click.echo("Cancelled.")
            return

    # Perform removal
    try:
        dir_removed, partcad_removed = remove_project(
            name=name,
            project_root=proj.root,
        )

        click.echo(f"Project '{normalized_name}' removed:")
        click.echo(f"  Directory deleted: {'yes' if dir_removed else 'no'}")
        click.echo(f"  partcad.yaml updated: {'yes' if partcad_removed else 'no'}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error removing project: {e}", err=True)
        raise SystemExit(1)


@project.command("sync")
@click.pass_context
def sync_projects(ctx):
    """Sync partcad.yaml with actual project directories.

    Removes entries from partcad.yaml that point to non-existent project directories.
    This is useful for cleaning up after manual deletions.

    Examples:

        ./bin/dev project sync
    """
    proj = ctx.obj["project"]

    click.echo("Syncing partcad.yaml with project directories...")

    removed = sync_partcad(proj.root)

    if removed:
        click.echo(f"Removed {len(removed)} stale entries:")
        for name in removed:
            click.echo(f"  - {name}")
    else:
        click.echo("No stale entries found. partcad.yaml is in sync.")


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
