"""
Semi-AutoCAD CLI - Main entry point.

Usage:
    python -m semicad [command]
    ./bin/dev [command]
"""

import click
import platform
import sys
from importlib.metadata import version as get_pkg_version, PackageNotFoundError
from pathlib import Path

from semicad.core.project import get_project, Project
import semicad


# Create main CLI group
@click.group(invoke_without_command=True)
@click.option("--project", "-p", type=click.Path(exists=True), help="Project root directory")
@click.pass_context
def cli(ctx, project):
    """Semi-AutoCAD - AI-assisted CAD design system."""
    ctx.ensure_object(dict)

    # Show help if no command given
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return

    # Set project context
    if project:
        ctx.obj["project"] = get_project(project)
    else:
        ctx.obj["project"] = get_project(Path.cwd())


# Import and register command groups
from semicad.cli.commands import view, build, library, project as proj_cmd

cli.add_command(view.view)
cli.add_command(view.edit)
cli.add_command(build.build)
cli.add_command(build.render)
cli.add_command(build.export)
cli.add_command(library.lib)
cli.add_command(library.search)
cli.add_command(proj_cmd.project)
cli.add_command(proj_cmd.test)


# Quick aliases
@cli.command("v")
@click.argument("file", required=False)
@click.pass_context
def v_alias(ctx, file):
    """Alias for 'view'."""
    ctx.invoke(view.view, file=file)


@cli.command("b")
@click.pass_context
def b_alias(ctx):
    """Alias for 'build'."""
    ctx.invoke(build.build)


@cli.command("l")
@click.pass_context
def l_alias(ctx):
    """Alias for 'lib list'."""
    ctx.invoke(library.list_libs)


def _get_version(package_name: str) -> str | None:
    """Get version of a package, or None if not installed."""
    try:
        return get_pkg_version(package_name)
    except PackageNotFoundError:
        return None


@cli.command()
def version():
    """Show version information for semicad and dependencies."""
    # Core info
    click.echo(f"semicad {semicad.__version__}")
    click.echo(f"Python {sys.version.split()[0]} ({platform.system()} {platform.machine()})")
    click.echo()

    # Core dependencies
    click.echo("Dependencies:")
    core_packages = [
        ("cadquery", "cadquery"),
        ("OCP", "cadquery-ocp"),
        ("click", "click"),
        ("pyyaml", "pyyaml"),
    ]
    for display_name, pkg_name in core_packages:
        ver = _get_version(pkg_name)
        status = ver if ver else "not installed"
        click.echo(f"  {display_name:<16} {status}")

    click.echo()

    # Optional dependencies
    click.echo("Optional:")
    optional_packages = [
        ("cq-editor", "cq-editor"),
        ("cq-warehouse", "cq-warehouse"),
        ("cq-electronics", "cq-electronics"),
        ("partcad", "partcad"),
        ("trimesh", "trimesh"),
    ]
    for display_name, pkg_name in optional_packages:
        ver = _get_version(pkg_name)
        status = ver if ver else "not installed"
        click.echo(f"  {display_name:<16} {status}")


def main():
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
