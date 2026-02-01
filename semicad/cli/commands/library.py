"""
Library commands - Browse and search component libraries.
"""

import json

import click

from semicad.cli import verbose_echo


@click.group()
@click.pass_context
def lib(ctx):
    """Component library operations."""
    pass


@lib.command("list")
@click.option("--source", "-s", help="Filter by source (custom, cq_warehouse, etc.)")
@click.option("--category", "-c", help="Filter by category")
@click.pass_context
def list_libs(ctx, source, category):
    """List available components."""
    from semicad.core.registry import get_registry

    verbose_echo(ctx, "Initializing component registry...")
    registry = get_registry()
    verbose_echo(ctx, f"Registry sources: {registry.sources}")
    json_output = ctx.obj.get("json_output", False)

    # Build data structure
    data = {"sources": {}}

    for src_name in registry.sources:
        if source and src_name != source:
            continue

        components = list(registry.list_from(src_name))
        if category:
            components = [c for c in components if c.category == category]

        # Group by category
        by_category = {}
        for comp in components:
            by_category.setdefault(comp.category, []).append(comp)

        data["sources"][src_name] = {
            cat: [comp.name for comp in comps]
            for cat, comps in sorted(by_category.items())
        }

    if json_output:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo("Component Libraries:")
        click.echo("=" * 50)

        for src_name, categories in data["sources"].items():
            click.echo(f"\n{src_name}:")
            for cat, comps in categories.items():
                click.echo(f"  {cat}:")
                for comp in comps[:10]:  # Limit display
                    click.echo(f"    - {comp}")
                if len(comps) > 10:
                    click.echo(f"    ... and {len(comps) - 10} more")


@lib.command("info")
@click.argument("component")
@click.pass_context
def info(ctx, component):
    """Show detailed info about a component."""
    from semicad.core.registry import get_registry

    verbose_echo(ctx, "Initializing component registry...")
    registry = get_registry()
    verbose_echo(ctx, f"Registry sources: {registry.sources}")
    json_output = ctx.obj.get("json_output", False)

    try:
        # Use get_spec() to avoid requiring params for parametric components
        verbose_echo(ctx, f"Looking up component spec: {component}")
        spec = registry.get_spec(component)
        verbose_echo(ctx, f"Found in source: {spec.source}")

        data = {
            "name": spec.name,
            "source": spec.source,
            "category": spec.category,
            "description": spec.description,
            "full_name": spec.full_name,
            "params": spec.params,
            "metadata": spec.metadata if spec.metadata else None,
        }

        if json_output:
            click.echo(json.dumps(data, indent=2))
        else:
            click.echo(f"Component: {spec.name}")
            click.echo(f"  Source: {spec.source}")
            click.echo(f"  Category: {spec.category}")
            click.echo(f"  Description: {spec.description}")

            if spec.params:
                # Handle structured params (required/defaults) from electronics source
                if "required" in spec.params:
                    required = spec.params["required"]
                    click.echo(f"  Required parameters: {', '.join(required)}")
                if "defaults" in spec.params:
                    defaults = spec.params["defaults"]
                    click.echo("  Default parameters:")
                    for k, v in defaults.items():
                        click.echo(f"    {k}: {v}")
                # Handle simple params dict (from custom/warehouse sources)
                if "required" not in spec.params and "defaults" not in spec.params:
                    click.echo("  Parameters:")
                    for k, v in spec.params.items():
                        click.echo(f"    {k}: {v}")

    except KeyError:
        verbose_echo(ctx, f"Component not found in any source")
        click.echo(f"Component not found: {component}", err=True)
        raise SystemExit(1)


@lib.command("fasteners")
@click.option("--type", "-t", "fastener_type", default="SocketHeadCapScrew", help="Fastener type")
@click.pass_context
def fasteners(ctx, fastener_type):
    """List available fastener sizes."""
    from semicad.sources.warehouse import WarehouseSource

    verbose_echo(ctx, "Initializing cq_warehouse source...")
    source = WarehouseSource()
    verbose_echo(ctx, f"Querying fastener sizes for: {fastener_type}")
    json_output = ctx.obj.get("json_output", False)

    sizes = source.list_fastener_sizes(fastener_type)
    verbose_echo(ctx, f"Found {len(sizes)} sizes")

    data = {
        "fastener_type": fastener_type,
        "sizes": sizes,
        "example": f'registry.get("{fastener_type}", size="M3-0.5", length=10)',
    }

    if json_output:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Fastener: {fastener_type}")
        click.echo("Available sizes:")

        for size in sizes:
            click.echo(f"  {size}")

        click.echo(f"\nExample usage:")
        click.echo(f'  registry.get("{fastener_type}", size="M3-0.5", length=10)')


@lib.command("bearings")
@click.pass_context
def bearings(ctx):
    """List available bearing sizes."""
    from semicad.sources.warehouse import WarehouseSource

    verbose_echo(ctx, "Initializing cq_warehouse source...")
    source = WarehouseSource()
    verbose_echo(ctx, "Querying bearing sizes...")
    json_output = ctx.obj.get("json_output", False)

    sizes = source.list_bearing_sizes()
    verbose_echo(ctx, f"Found {len(sizes)} bearing sizes")

    data = {
        "type": "Deep Groove Ball Bearings",
        "sizes": sizes,
        "total": len(sizes),
    }

    if json_output:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo("Deep Groove Ball Bearings:")
        click.echo("Available sizes:")

        for size in sizes[:20]:
            click.echo(f"  {size}")

        if len(sizes) > 20:
            click.echo(f"  ... and {len(sizes) - 20} more")


@lib.command("electronics")
@click.pass_context
def electronics(ctx):
    """List all electronics components by category."""
    from semicad.sources.electronics import ElectronicsSource

    source = ElectronicsSource()
    json_output = ctx.obj.get("json_output", False)

    categories = source.list_categories()

    # Build data structure
    data = {"categories": {}}
    for category in categories:
        data["categories"][category] = [
            {
                "name": spec.name,
                "description": spec.description,
                "required_params": spec.params.get("required", []),
                "default_params": spec.params.get("defaults", {}),
            }
            for spec in source.list_by_category(category)
        ]

    if json_output:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo("Electronics Components (cq_electronics):")
        click.echo("=" * 50)

        if not categories:
            click.echo("  No electronics components available.")
            click.echo("  (cq_electronics may not be installed)")
            return

        for category in categories:
            click.echo(f"\n{category}:")
            for spec in source.list_by_category(category):
                # Show required params if any
                required = spec.params.get("required", [])
                if required:
                    params_str = f" (required: {', '.join(required)})"
                else:
                    params_str = ""
                click.echo(f"  - {spec.name}{params_str}")
                if spec.description:
                    click.echo(f"      {spec.description}")

        click.echo("\nUse 'lib boards' or 'lib connectors' for detailed specs.")


@lib.command("boards")
@click.pass_context
def boards(ctx):
    """List available board components with dimensions."""
    from semicad.sources.electronics import ElectronicsSource

    source = ElectronicsSource()
    json_output = ctx.obj.get("json_output", False)

    board_list = source.list_boards()

    if json_output:
        data = {
            "boards": board_list,
            "total": len(board_list),
            "example": 'registry.get("RPi3b")',
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo("Electronic Boards:")
        click.echo("=" * 50)

        if not board_list:
            click.echo("  No boards available.")
            return

        for board in board_list:
            click.echo(f"\n{board['name']}:")
            click.echo(f"  {board.get('description', '')}")

            # Dimensions
            width = board.get("width")
            height = board.get("height")
            thickness = board.get("thickness")
            if width and height:
                dims = f"  Dimensions: {width} x {height}"
                if thickness:
                    dims += f" x {thickness}"
                dims += " mm"
                click.echo(dims)

            # Mounting holes
            hole_dia = board.get("hole_diameter")
            if hole_dia:
                click.echo(f"  Mounting holes: M{hole_dia:.1f}")

            hole_spacing = board.get("hole_centers_long")
            hole_offset = board.get("hole_offset_from_edge")
            if hole_spacing and hole_offset:
                click.echo(f"  Hole spacing: {hole_spacing}mm (long), offset {hole_offset}mm from edge")

        click.echo(f"\nExample usage:")
        click.echo('  registry.get("RPi3b")')


@lib.command("connectors")
@click.pass_context
def connectors(ctx):
    """List available connector components with specs."""
    from semicad.sources.electronics import ElectronicsSource

    source = ElectronicsSource()
    json_output = ctx.obj.get("json_output", False)

    connector_list = source.list_connectors()

    if json_output:
        data = {
            "connectors": connector_list,
            "total": len(connector_list),
            "examples": [
                'registry.get("PinHeader", rows=2, columns=20)',
                'registry.get("JackSurfaceMount")',
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo("Electronic Connectors:")
        click.echo("=" * 50)

        if not connector_list:
            click.echo("  No connectors available.")
            return

        for conn in connector_list:
            click.echo(f"\n{conn['name']}:")
            click.echo(f"  {conn.get('description', '')}")

            # Show pitch if available
            pitch = conn.get("pitch")
            if pitch:
                click.echo(f"  Pitch: {pitch}mm")

            # Show required params
            required = conn.get("required_params", [])
            if required:
                click.echo(f"  Required params: {', '.join(required)}")

            # Show defaults
            defaults = conn.get("default_params", {})
            if defaults:
                defaults_str = ", ".join(f"{k}={v}" for k, v in defaults.items())
                click.echo(f"  Defaults: {defaults_str}")

        click.echo(f"\nExample usage:")
        click.echo('  registry.get("PinHeader", rows=2, columns=20)')
        click.echo('  registry.get("JackSurfaceMount")')


@click.command()
@click.argument("query")
@click.option("--source", "-s", help="Search specific source only")
@click.pass_context
def search(ctx, query, source):
    """Search for components by name or description."""
    from semicad.core.registry import get_registry

    verbose_echo(ctx, "Initializing component registry...")
    registry = get_registry()
    verbose_echo(ctx, f"Registry sources: {registry.sources}")
    json_output = ctx.obj.get("json_output", False)

    if source:
        verbose_echo(ctx, f"Filtering by source: {source}")

    verbose_echo(ctx, f"Executing search query: '{query}'")
    results = list(registry.search(query, source))
    verbose_echo(ctx, f"Search returned {len(results)} results")

    data = {
        "query": query,
        "source_filter": source,
        "total": len(results),
        "results": [
            {
                "name": spec.name,
                "source": spec.source,
                "category": spec.category,
                "description": spec.description,
                "full_name": spec.full_name,
            }
            for spec in results
        ],
    }

    if json_output:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Searching for: {query}")
        click.echo("-" * 40)

        if not results:
            click.echo("No components found.")
            return

        for spec in results[:20]:
            click.echo(f"  [{spec.source}] {spec.name}")
            if spec.description:
                click.echo(f"      {spec.description}")

        if len(results) > 20:
            click.echo(f"\n  ... and {len(results) - 20} more results")


def parse_validate_param(value):
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
            params[key] = int(val)
        except ValueError:
            try:
                params[key] = float(val)
            except ValueError:
                if val.lower() in ("true", "yes", "1"):
                    params[key] = True
                elif val.lower() in ("false", "no", "0"):
                    params[key] = False
                else:
                    params[key] = val
    return params


@lib.command("validate")
@click.argument("component")
@click.option("--max-size", type=float, default=2000.0, help="Max dimension warning threshold (mm)")
@click.option("--min-size", type=float, default=0.01, help="Min dimension warning threshold (mm)")
@click.option(
    "--param", "-p",
    multiple=True,
    help="Component parameter as KEY=VALUE (can be repeated)",
)
@click.pass_context
def validate(ctx, component, max_size, min_size, param):
    """
    Validate component geometry.

    Checks:
    - Geometry is valid (no self-intersections)
    - Bounding box reasonable
    - Has expected features (solids, faces)

    For parametric components, use --param to specify required parameters:

        ./bin/dev lib validate BGA --param length=10 --param width=10

    Example:
        ./bin/dev lib validate motor_2207

    Use global --verbose flag for detailed issue output:
        ./bin/dev -v lib validate motor_2207
    """
    from semicad.core.registry import get_registry
    from semicad.core.validation import IssueSeverity

    verbose = ctx.obj.get("verbose", False)

    verbose_echo(ctx, "Initializing component registry...")
    registry = get_registry()
    verbose_echo(ctx, f"Registry sources: {registry.sources}")
    json_output = ctx.obj.get("json_output", False)

    # Parse component parameters
    comp_params = parse_validate_param(param)

    try:
        verbose_echo(ctx, f"Looking up component: {component}")
        if comp_params:
            verbose_echo(ctx, f"With parameters: {comp_params}")
        comp = registry.get(component, **comp_params)
        verbose_echo(ctx, f"Found in source: {comp.spec.source}")
    except KeyError:
        verbose_echo(ctx, f"Component not found in any source")
        click.echo(f"Component not found: {component}", err=True)
        raise SystemExit(1)
    except ValueError as e:
        # Handle missing required parameters with helpful message
        click.echo(f"Parameter error: {e}", err=True)
        try:
            spec = registry.get_spec(component)
            if spec.params and "required" in spec.params:
                click.echo(f"\nRequired parameters for {component}: {spec.params['required']}")
                click.echo(f"\nExample:")
                example_params = " ".join(f"-p {p}=<value>" for p in spec.params["required"])
                click.echo(f"  ./bin/dev lib validate {component} {example_params}")
        except KeyError:
            pass
        raise SystemExit(1)

    # Run validation
    verbose_echo(ctx, f"Running validation with max_size={max_size}, min_size={min_size}")
    result = comp.validate(max_dimension=max_size, min_dimension=min_size)
    verbose_echo(ctx, f"Validation complete: is_valid={result.is_valid}")

    # Build JSON data
    data = {
        "component": component,
        "params": comp_params if comp_params else None,
        "is_valid": result.is_valid,
        "metrics": {
            "bbox_size": list(result.bbox_size) if result.bbox_size else None,
            "solid_count": result.solid_count,
            "face_count": result.face_count,
        },
        "issues": [
            {
                "severity": issue.severity.value,
                "code": issue.code,
                "message": issue.message,
                "details": issue.details,
            }
            for issue in result.issues
        ],
        "summary": {
            "error_count": result.error_count,
            "warning_count": result.warning_count,
        },
    }

    if json_output:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"\nValidating: {component}")
        if comp_params:
            click.echo(f"Parameters: {comp_params}")
        click.echo("=" * 50)

        # Display results
        if result.is_valid:
            click.echo(click.style("\n\u2713 Geometry is valid", fg="green"))
        else:
            click.echo(click.style("\n\u2717 Validation failed", fg="red"))

        # Show metrics
        if result.bbox_size:
            x, y, z = result.bbox_size
            click.echo(f"  Bounding box: {x:.1f} x {y:.1f} x {z:.1f} mm")

        if result.solid_count > 0:
            click.echo(f"  Solids: {result.solid_count}")

        if result.face_count > 0:
            click.echo(f"  Faces: {result.face_count}")

        # Show issues
        if result.issues:
            click.echo("\nIssues:")
            for issue in result.issues:
                if issue.severity == IssueSeverity.ERROR:
                    prefix = click.style("  \u2717 ERROR", fg="red")
                elif issue.severity == IssueSeverity.WARNING:
                    prefix = click.style("  \u26a0 WARNING", fg="yellow")
                else:
                    prefix = click.style("  \u2139 INFO", fg="blue")

                click.echo(f"{prefix}: {issue.code} - {issue.message}")

                if verbose and issue.details:
                    for k, v in issue.details.items():
                        click.echo(f"      {k}: {v}")

        # Summary
        click.echo("")
        if result.error_count > 0 or result.warning_count > 0:
            summary_parts = []
            if result.error_count > 0:
                summary_parts.append(click.style(f"{result.error_count} error(s)", fg="red"))
            if result.warning_count > 0:
                summary_parts.append(click.style(f"{result.warning_count} warning(s)", fg="yellow"))
            click.echo(", ".join(summary_parts))
        else:
            click.echo(click.style("No issues found.", fg="green"))

    # Exit with error if validation failed
    if not result.is_valid:
        raise SystemExit(1)
