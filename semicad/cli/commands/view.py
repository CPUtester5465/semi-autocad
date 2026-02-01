"""
View commands - Open files in cq-editor.
"""

import os
import subprocess
from pathlib import Path

import click

from semicad.cli import verbose_echo


@click.command()
@click.argument("file", required=False, type=click.Path())
@click.pass_context
def view(ctx: click.Context, file: str | None) -> None:
    """Open a file in cq-editor for visualization."""
    project = ctx.obj["project"]

    # Default to assembly_viewer.py
    if not file:
        file_path = project.scripts_dir / "assembly_viewer.py"
        verbose_echo(ctx, f"No file specified, using default: {file_path}")
    else:
        file_path = Path(file)
        if not file_path.is_absolute():
            file_path = project.root / file_path
        verbose_echo(ctx, f"Resolved file path: {file_path}")

    if not file_path.exists():
        click.echo(f"File not found: {file_path}", err=True)
        raise SystemExit(1)

    # Set up PYTHONPATH for imports
    env = os.environ.copy()
    pythonpath = f"{project.scripts_dir}:{project.root}"
    if "PYTHONPATH" in env:
        pythonpath += f":{env['PYTHONPATH']}"
    env["PYTHONPATH"] = pythonpath

    verbose_echo(ctx, f"PYTHONPATH: {pythonpath}")

    click.echo("Opening cq-editor...")
    click.echo(f"  File: {file_path}")
    click.echo("  Press F5 to render")

    verbose_echo(ctx, f"Running: cq-editor {file_path}")

    try:
        subprocess.run(["cq-editor", str(file_path)], env=env, check=False)
    except FileNotFoundError:
        click.echo("cq-editor not found. Install with: pip install cq-editor", err=True)
        raise SystemExit(1) from None


@click.command()
@click.argument("file", required=False, type=click.Path())
@click.pass_context
def edit(ctx: click.Context, file: str | None) -> None:
    """Open a file in the default editor."""
    project = ctx.obj["project"]

    if not file:
        file_path = project.scripts_dir / "assembly_viewer.py"
        verbose_echo(ctx, f"No file specified, using default: {file_path}")
    else:
        file_path = Path(file)
        if not file_path.is_absolute():
            file_path = project.root / file_path
        verbose_echo(ctx, f"Resolved file path: {file_path}")

    editor = os.environ.get("EDITOR", "nano")
    verbose_echo(ctx, f"Using editor: {editor}")
    verbose_echo(ctx, f"Running: {editor} {file_path}")
    subprocess.run([editor, str(file_path)], check=False)
