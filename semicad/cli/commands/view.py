"""
View commands - Open files in cq-editor.
"""

import click
import subprocess
import os
from pathlib import Path


@click.command()
@click.argument("file", required=False, type=click.Path())
@click.pass_context
def view(ctx, file):
    """Open a file in cq-editor for visualization."""
    project = ctx.obj["project"]

    # Default to assembly_viewer.py
    if not file:
        file = project.scripts_dir / "assembly_viewer.py"
    else:
        file = Path(file)
        if not file.is_absolute():
            file = project.root / file

    if not file.exists():
        click.echo(f"File not found: {file}", err=True)
        raise SystemExit(1)

    # Set up PYTHONPATH for imports
    env = os.environ.copy()
    pythonpath = f"{project.scripts_dir}:{project.root}"
    if "PYTHONPATH" in env:
        pythonpath += f":{env['PYTHONPATH']}"
    env["PYTHONPATH"] = pythonpath

    click.echo(f"Opening cq-editor...")
    click.echo(f"  File: {file}")
    click.echo(f"  Press F5 to render")

    try:
        subprocess.run(["cq-editor", str(file)], env=env)
    except FileNotFoundError:
        click.echo("cq-editor not found. Install with: pip install cq-editor", err=True)
        raise SystemExit(1)


@click.command()
@click.argument("file", required=False, type=click.Path())
@click.pass_context
def edit(ctx, file):
    """Open a file in the default editor."""
    project = ctx.obj["project"]

    if not file:
        file = project.scripts_dir / "assembly_viewer.py"
    else:
        file = Path(file)
        if not file.is_absolute():
            file = project.root / file

    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(file)])
