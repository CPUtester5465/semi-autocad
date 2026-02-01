"""Shell completion support for semicad CLI."""

import click
from click.shell_completion import get_completion_class


SHELLS = ["bash", "zsh", "fish"]


@click.group()
def completion():
    """Shell completion utilities.

    Enable tab-completion for commands and arguments.

    \b
    Quick setup:
        # Bash
        ./bin/dev completion show bash >> ~/.bashrc

        # Zsh
        ./bin/dev completion show zsh >> ~/.zshrc

        # Fish
        ./bin/dev completion show fish > ~/.config/fish/completions/dev.fish
    """
    pass


@completion.command("show")
@click.argument("shell", type=click.Choice(SHELLS))
@click.option(
    "--prog-name",
    default=None,
    help="Override the program name (default: dev)",
)
def show(shell, prog_name):
    """Output shell completion script.

    \b
    Examples:
        # Add to your shell config
        ./bin/dev completion show bash >> ~/.bashrc
        ./bin/dev completion show zsh >> ~/.zshrc

        # Or source directly (for testing)
        eval "$(./bin/dev completion show bash)"
    """
    from semicad.cli import cli

    # Default prog_name to 'dev' since that's the common wrapper
    if prog_name is None:
        prog_name = "dev"

    # Get the completion class for the shell
    comp_cls = get_completion_class(shell)
    if comp_cls is None:
        raise click.ClickException(f"Unsupported shell: {shell}")

    # Generate the completion script
    # The env var will be _<PROG_NAME>_COMPLETE in uppercase
    env_var = f"_{prog_name.upper()}_COMPLETE"
    comp = comp_cls(cli, {}, prog_name, env_var)

    click.echo(comp.source())


@completion.command("install")
@click.argument("shell", type=click.Choice(SHELLS))
def install(shell):
    """Show instructions for installing completion.

    \b
    Prints the commands needed to enable completion for your shell.
    """
    instructions = {
        "bash": """\
# Add to ~/.bashrc:
eval "$(./bin/dev completion show bash)"

# Or append permanently:
./bin/dev completion show bash >> ~/.bashrc
source ~/.bashrc""",
        "zsh": """\
# Add to ~/.zshrc:
eval "$(./bin/dev completion show zsh)"

# Or append permanently:
./bin/dev completion show zsh >> ~/.zshrc
source ~/.zshrc""",
        "fish": """\
# Save to fish completions directory:
./bin/dev completion show fish > ~/.config/fish/completions/dev.fish""",
    }

    click.echo(f"To enable {shell} completion:\n")
    click.echo(instructions[shell])
