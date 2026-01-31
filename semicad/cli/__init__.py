"""
Semi-AutoCAD CLI - Main entry point.

Usage:
    python -m semicad [command]
    ./bin/dev [command]
"""

import click
from pathlib import Path

from semicad.core.project import get_project, Project


# Create main CLI group
@click.group()
@click.option("--project", "-p", type=click.Path(exists=True), help="Project root directory")
@click.pass_context
def cli(ctx, project):
    """Semi-AutoCAD - AI-assisted CAD design system."""
    ctx.ensure_object(dict)

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


def main():
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
