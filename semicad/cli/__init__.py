"""
Semi-AutoCAD CLI - Main entry point.

Usage:
    python -m semicad [command]
    ./bin/dev [command]
"""

import platform
import sys
from importlib.metadata import PackageNotFoundError, version as get_pkg_version
from pathlib import Path

import click

import semicad
from semicad.core.project import Project, get_project


def verbose_echo(ctx: click.Context, msg: str) -> None:
    """Print debug message if verbose mode is enabled.

    Args:
        ctx: Click context object (may have None obj in tests)
        msg: Message to print when verbose mode is enabled
    """
    if ctx.obj and ctx.obj.get("verbose"):
        click.echo(click.style(f"[verbose] {msg}", dim=True))


def get_ctx_value(ctx: click.Context, key: str, default: object = None) -> object:
    """Safely get a value from the Click context object.

    Handles the case where ctx.obj is None (e.g., in tests).

    Args:
        ctx: Click context object
        key: Key to look up in ctx.obj
        default: Default value if key not found or ctx.obj is None

    Returns:
        The value from ctx.obj[key] or the default
    """
    if ctx.obj is None:
        return default
    return ctx.obj.get(key, default)


# Create main CLI group
@click.group(invoke_without_command=True)
@click.option("--project", "-p", type=click.Path(exists=True), help="Project root directory")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format for scripting")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose debug output")
@click.pass_context
def cli(ctx, project, json_output, verbose):
    """Semi-AutoCAD - AI-assisted CAD design system."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["json_output"] = json_output

    # Show help if no command given
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return

    # Set project context
    if project:
        ctx.obj["project"] = get_project(project)
        if verbose:
            verbose_echo(ctx, f"Project root: {project}")
    else:
        ctx.obj["project"] = get_project(Path.cwd())
        if verbose:
            verbose_echo(ctx, f"Project root: {Path.cwd()}")


# Import and register command groups
from semicad.cli.commands import build, completion, library, partcad_cmd, project as proj_cmd, view

cli.add_command(view.view)
cli.add_command(view.edit)
cli.add_command(build.build)
cli.add_command(build.render)
cli.add_command(build.export)
cli.add_command(library.lib)
cli.add_command(library.search)
cli.add_command(proj_cmd.project)
cli.add_command(proj_cmd.test)
cli.add_command(completion.completion)
cli.add_command(partcad_cmd.partcad)


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


def main() -> None:
    """Entry point for the CLI."""
    import os

    # Determine prog_name for shell completion
    # When invoked via bin/dev, use 'dev' as prog_name for completion
    # When invoked via pip-installed 'semicad', use 'semicad'
    prog_name = None
    if os.environ.get("_DEV_COMPLETE") or os.environ.get("_SEMICAD_COMPLETE"):
        # Completion mode - determine which name to use
        if os.environ.get("_DEV_COMPLETE"):
            prog_name = "dev"
        else:
            prog_name = "semicad"

    cli(obj={}, prog_name=prog_name)


if __name__ == "__main__":
    main()
