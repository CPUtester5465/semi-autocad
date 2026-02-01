"""
PartCAD commands - Browse and install parts from the PartCAD package manager.

Note: The PartCAD CLI (`pc` command) has version compatibility issues with
the current Click version. These commands use the PartCAD Python API directly.
"""

import json

import click

from semicad.cli import verbose_echo


@click.group()
@click.pass_context
def partcad(ctx):
    """PartCAD package manager operations.

    Access parts from the PartCAD public index including:
    - Standard fasteners (ISO/DIN)
    - Mechanical components
    - Electronic enclosures
    - Community-contributed parts

    First access may require network to fetch packages.
    """
    pass


@partcad.command("search")
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Maximum results to show")
@click.pass_context
def search_parts(ctx, query, limit):
    """Search for parts in the PartCAD index.

    Examples:
        partcad search "bolt"
        partcad search "servo" --limit 10
        partcad search "hex"
    """
    verbose_echo(ctx, f"Searching PartCAD for: {query}")
    json_output = ctx.obj.get("json_output", False)

    try:
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        results = list(source.search(query))[:limit]

        if json_output:
            data = {
                "query": query,
                "count": len(results),
                "results": [
                    {
                        "name": r.name,
                        "path": r.metadata.get("partcad_path", "") if r.metadata else "",
                        "description": r.description,
                        "category": r.category,
                    }
                    for r in results
                ],
            }
            click.echo(json.dumps(data, indent=2))
        else:
            if not results:
                click.echo(f"No parts found matching: {query}")
                return

            click.echo(f"Found {len(results)} parts matching '{query}':\n")

            for spec in results:
                path = spec.metadata.get("partcad_path", "") if spec.metadata else ""
                click.echo(f"  {spec.name}")
                click.echo(f"    Path: {path}")
                click.echo(f"    Category: {spec.category}")
                if spec.description:
                    click.echo(f"    Description: {spec.description}")
                click.echo()

    except ImportError as e:
        click.echo(f"PartCAD not available: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        verbose_echo(ctx, f"Error: {e}")
        click.echo(f"Search failed: {e}", err=True)
        raise SystemExit(1)


@partcad.command("list")
@click.argument("package", required=False)
@click.option("--recursive", "-r", is_flag=True, help="List all parts recursively")
@click.pass_context
def list_parts(ctx, package, recursive):
    """List parts in a PartCAD package.

    Without arguments, lists top-level packages.
    With a package path, lists parts in that package.

    Examples:
        partcad list                              # List top-level packages
        partcad list //pub/std/metric/cqwarehouse # List parts in package
        partcad list pub/std/metric               # List subpackages
    """
    verbose_echo(ctx, f"Listing PartCAD package: {package or '(root)'}")
    json_output = ctx.obj.get("json_output", False)

    try:
        from semicad.sources.partcad_source import PartCADSource, _normalize_path

        source = PartCADSource()

        if package is None:
            # List top-level packages
            packages = source.list_packages()

            if json_output:
                click.echo(json.dumps({"packages": packages}, indent=2))
            else:
                click.echo("PartCAD Top-Level Packages:\n")
                for pkg in packages:
                    click.echo(f"  {pkg}")
                click.echo(f"\nTotal: {len(packages)} packages")
        else:
            # List parts in specific package
            package = _normalize_path(package)
            parts = source.list_parts_in_package(package)

            if json_output:
                click.echo(json.dumps({"package": package, "parts": parts}, indent=2))
            else:
                click.echo(f"Parts in {package}:\n")
                for part in parts[:50]:  # Limit display
                    click.echo(f"  {part}")
                if len(parts) > 50:
                    click.echo(f"  ... and {len(parts) - 50} more")
                click.echo(f"\nTotal: {len(parts)} parts")

    except ImportError as e:
        click.echo(f"PartCAD not available: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        verbose_echo(ctx, f"Error: {e}")
        click.echo(f"List failed: {e}", err=True)
        raise SystemExit(1)


@partcad.command("info")
@click.argument("path")
@click.pass_context
def part_info(ctx, path):
    """Show detailed info about a PartCAD part.

    Examples:
        partcad info //pub/std/metric/cqwarehouse:fastener/iso4017
        partcad info "fastener/hexhead-iso4017"
    """
    verbose_echo(ctx, f"Getting info for: {path}")
    json_output = ctx.obj.get("json_output", False)

    try:
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        info = source.get_part_info(path)

        if json_output:
            click.echo(json.dumps(info, indent=2))
        else:
            click.echo(f"Part: {info['name']}")
            click.echo(f"  Path: {info['path']}")
            click.echo(f"  Type: {info['type']}")

            if info.get("description"):
                click.echo(f"  Description: {info['description']}")

            if info.get("aliases"):
                click.echo(f"  Aliases: {', '.join(info['aliases'])}")

            if info.get("manufacturable"):
                click.echo("  Manufacturable: Yes")

            params = info.get("parameters", {})
            if params:
                click.echo("\n  Parameters:")
                for name, param in params.items():
                    if isinstance(param, dict):
                        ptype = param.get("type", "unknown")
                        default = param.get("default", "none")

                        if "enum" in param:
                            options = param["enum"]
                            if len(options) > 5:
                                opts_str = f"{options[:5]} ... ({len(options)} total)"
                            else:
                                opts_str = str(options)
                            click.echo(f"    {name}: {ptype} = {default}")
                            click.echo(f"      Options: {opts_str}")
                        else:
                            click.echo(f"    {name}: {ptype} = {default}")
                    else:
                        click.echo(f"    {name}: {param}")

    except KeyError as e:
        click.echo(f"Part not found: {path}", err=True)
        raise SystemExit(1)
    except ImportError as e:
        click.echo(f"PartCAD not available: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        verbose_echo(ctx, f"Error: {e}")
        click.echo(f"Info failed: {e}", err=True)
        raise SystemExit(1)


@partcad.command("install")
@click.argument("package")
@click.pass_context
def install_package(ctx, package):
    """Pre-fetch a PartCAD package for offline use.

    This downloads the package to the local PartCAD cache.
    Useful for preparing parts before going offline.

    Examples:
        partcad install pub/electromechanics/towerpro
        partcad install //pub/std/metric
    """
    verbose_echo(ctx, f"Installing package: {package}")
    json_output = ctx.obj.get("json_output", False)

    try:
        from semicad.sources.partcad_source import _normalize_path
        import partcad

        package = _normalize_path(package)

        click.echo(f"Fetching package: {package}")
        click.echo("This may take a moment on first access...")

        ctx_pc = partcad.init(".")
        project = ctx_pc.get_project(package)

        if project is None:
            click.echo(f"Package not found: {package}", err=True)
            raise SystemExit(1)

        # List parts to trigger any lazy loading
        parts = list(project.parts.keys()) if hasattr(project, 'parts') else []
        children = project.get_child_project_names() if hasattr(project, 'get_child_project_names') else []

        result = {
            "package": package,
            "status": "installed",
            "parts_count": len(parts),
            "subpackages_count": len(children),
        }

        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"\nPackage installed: {package}")
            click.echo(f"  Parts: {len(parts)}")
            click.echo(f"  Subpackages: {len(children)}")

            if children:
                click.echo("\n  Subpackages:")
                for child in children[:10]:
                    click.echo(f"    {child}")
                if len(children) > 10:
                    click.echo(f"    ... and {len(children) - 10} more")

    except ImportError as e:
        click.echo(f"PartCAD not available: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        verbose_echo(ctx, f"Error: {e}")
        click.echo(f"Install failed: {e}", err=True)
        raise SystemExit(1)


@partcad.command("render")
@click.argument("path")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", "fmt", default="png", type=click.Choice(["png", "stl", "step"]), help="Output format")
@click.option("--size", "-s", help="Part parameters as 'key=value' pairs", multiple=True)
@click.pass_context
def render_part(ctx, path, output, fmt, size):
    """Render or export a PartCAD part.

    Examples:
        partcad render //pub/std/metric/cqwarehouse:fastener/iso4017
        partcad render //pub/std/metric/cqwarehouse:fastener/iso4017 -o bolt.stl -f stl
        partcad render //pub/std/metric/cqwarehouse:fastener/hexhead-iso4017 --size="size=M10-1.5" --size="length=30"
    """
    verbose_echo(ctx, f"Rendering part: {path}")

    # Parse size parameters
    params = {}
    for s in size:
        if "=" in s:
            key, value = s.split("=", 1)
            # Try to convert to int/float if possible
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass  # Keep as string
            params[key] = value

    try:
        from semicad.sources.partcad_source import PartCADSource
        import cadquery as cq

        source = PartCADSource()
        component = source.get_component(path, **params)
        geometry = component.geometry

        # Generate default output filename if not provided
        if output is None:
            part_name = path.split(":")[-1].replace("/", "_") if ":" in path else path
            output = f"{part_name}.{fmt}"

        if fmt == "stl":
            cq.exporters.export(geometry, output)
            click.echo(f"Exported STL to: {output}")
        elif fmt == "step":
            cq.exporters.export(geometry, output)
            click.echo(f"Exported STEP to: {output}")
        elif fmt == "png":
            # Use semicad's render if available
            try:
                from semicad.cli.commands.build import _render_to_png
                _render_to_png(geometry, output)
                click.echo(f"Rendered PNG to: {output}")
            except (ImportError, AttributeError):
                # Fallback - just export STEP and note
                step_output = output.replace(".png", ".step")
                cq.exporters.export(geometry, step_output)
                click.echo(f"PNG rendering not available. Exported STEP to: {step_output}")

    except KeyError as e:
        click.echo(f"Part not found: {path}", err=True)
        raise SystemExit(1)
    except ImportError as e:
        click.echo(f"PartCAD not available: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        verbose_echo(ctx, f"Error: {e}")
        click.echo(f"Render failed: {e}", err=True)
        raise SystemExit(1)


@partcad.command("sizes")
@click.argument("path")
@click.option("--param", "-p", default="size", help="Parameter name to show options for")
@click.pass_context
def show_sizes(ctx, path, param):
    """Show available sizes/options for a parametric part.

    Examples:
        partcad sizes //pub/std/metric/cqwarehouse:fastener/hexhead-iso4017
        partcad sizes //pub/std/metric/cqwarehouse:fastener/hexhead-iso4017 --param length
    """
    verbose_echo(ctx, f"Getting sizes for: {path}")
    json_output = ctx.obj.get("json_output", False)

    try:
        from semicad.sources.partcad_source import PartCADSource

        source = PartCADSource()
        sizes = source.get_available_sizes(path, param)
        info = source.get_part_info(path)
        params = info.get("parameters", {})

        if json_output:
            click.echo(json.dumps({"path": path, "param": param, "values": sizes}, indent=2))
        else:
            click.echo(f"Part: {path}")
            click.echo(f"Parameter: {param}")

            if param in params:
                param_info = params[param]
                if isinstance(param_info, dict):
                    click.echo(f"  Type: {param_info.get('type', 'unknown')}")
                    click.echo(f"  Default: {param_info.get('default', 'none')}")

            click.echo(f"\nAvailable values ({len(sizes)} options):")
            for s in sizes[:30]:
                click.echo(f"  {s}")
            if len(sizes) > 30:
                click.echo(f"  ... and {len(sizes) - 30} more")

    except KeyError as e:
        click.echo(f"Part not found: {path}", err=True)
        raise SystemExit(1)
    except ImportError as e:
        click.echo(f"PartCAD not available: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        verbose_echo(ctx, f"Error: {e}")
        click.echo(f"Failed to get sizes: {e}", err=True)
        raise SystemExit(1)
