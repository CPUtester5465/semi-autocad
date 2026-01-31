"""
Library commands - Browse and search component libraries.
"""

import click


@click.group()
def lib():
    """Component library operations."""
    pass


@lib.command("list")
@click.option("--source", "-s", help="Filter by source (custom, cq_warehouse, etc.)")
@click.option("--category", "-c", help="Filter by category")
def list_libs(source, category):
    """List available components."""
    from semicad.core.registry import get_registry

    registry = get_registry()

    click.echo("Component Libraries:")
    click.echo("=" * 50)

    for src_name in registry.sources:
        if source and src_name != source:
            continue

        click.echo(f"\n{src_name}:")

        components = list(registry.list_from(src_name))
        if category:
            components = [c for c in components if c.category == category]

        # Group by category
        by_category = {}
        for comp in components:
            by_category.setdefault(comp.category, []).append(comp)

        for cat, comps in sorted(by_category.items()):
            click.echo(f"  {cat}:")
            for comp in comps[:10]:  # Limit display
                click.echo(f"    - {comp.name}")
            if len(comps) > 10:
                click.echo(f"    ... and {len(comps) - 10} more")


@lib.command("info")
@click.argument("component")
def info(component):
    """Show detailed info about a component."""
    from semicad.core.registry import get_registry

    registry = get_registry()

    try:
        comp = registry.get(component)
        spec = comp.spec

        click.echo(f"Component: {spec.name}")
        click.echo(f"  Source: {spec.source}")
        click.echo(f"  Category: {spec.category}")
        click.echo(f"  Description: {spec.description}")

        if spec.params:
            click.echo("  Parameters:")
            for k, v in spec.params.items():
                click.echo(f"    {k}: {v}")

    except KeyError:
        click.echo(f"Component not found: {component}", err=True)
        raise SystemExit(1)


@lib.command("fasteners")
@click.option("--type", "-t", "fastener_type", default="SocketHeadCapScrew", help="Fastener type")
def fasteners(fastener_type):
    """List available fastener sizes."""
    from semicad.sources.warehouse import WarehouseSource

    source = WarehouseSource()

    click.echo(f"Fastener: {fastener_type}")
    click.echo("Available sizes:")

    sizes = source.list_fastener_sizes(fastener_type)
    for size in sizes:
        click.echo(f"  {size}")

    click.echo(f"\nExample usage:")
    click.echo(f'  registry.get("{fastener_type}", size="M3-0.5", length=10)')


@lib.command("bearings")
def bearings():
    """List available bearing sizes."""
    from semicad.sources.warehouse import WarehouseSource

    source = WarehouseSource()

    click.echo("Deep Groove Ball Bearings:")
    click.echo("Available sizes:")

    sizes = source.list_bearing_sizes()
    for size in sizes[:20]:
        click.echo(f"  {size}")

    if len(sizes) > 20:
        click.echo(f"  ... and {len(sizes) - 20} more")


@click.command()
@click.argument("query")
@click.option("--source", "-s", help="Search specific source only")
def search(query, source):
    """Search for components by name or description."""
    from semicad.core.registry import get_registry

    registry = get_registry()

    click.echo(f"Searching for: {query}")
    click.echo("-" * 40)

    results = list(registry.search(query, source))

    if not results:
        click.echo("No components found.")
        return

    for spec in results[:20]:
        click.echo(f"  [{spec.source}] {spec.name}")
        if spec.description:
            click.echo(f"      {spec.description}")

    if len(results) > 20:
        click.echo(f"\n  ... and {len(results) - 20} more results")
