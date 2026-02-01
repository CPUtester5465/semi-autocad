"""
BOM (Bill of Materials) Generation Module.

Generate structured lists of components from assemblies or component collections.
Supports multiple output formats: CSV, JSON, Markdown.
"""

import csv
import json
from collections import Counter
from dataclasses import dataclass, field, asdict
from io import StringIO
from pathlib import Path
from typing import Union, Sequence

from semicad.core.component import Component, ComponentSpec


@dataclass
class BOMEntry:
    """A single entry in the Bill of Materials.

    Attributes:
        name: Component name.
        quantity: Number of this component in the assembly.
        category: Component category (e.g., "fastener", "motor").
        source: Component source (e.g., "custom", "cq_warehouse").
        description: Component description.
        params: Component parameters as formatted string.
    """

    name: str
    quantity: int
    category: str = ""
    source: str = ""
    description: str = ""
    params: str = ""


@dataclass
class BOM:
    """Bill of Materials for an assembly.

    Attributes:
        title: Name/title for this BOM.
        entries: List of BOM entries.
        notes: Optional notes about the BOM.
    """

    title: str = "Bill of Materials"
    entries: list[BOMEntry] = field(default_factory=list)
    notes: str = ""

    @property
    def total_parts(self) -> int:
        """Total number of parts (sum of quantities)."""
        return sum(e.quantity for e in self.entries)

    @property
    def unique_parts(self) -> int:
        """Number of unique part types."""
        return len(self.entries)


def generate_bom(
    components: Sequence[Component | ComponentSpec],
    title: str = "Bill of Materials",
) -> BOM:
    """
    Generate a Bill of Materials from a list of components.

    Counts duplicate components and groups them.

    Args:
        components: List of Component or ComponentSpec objects.
        title: Title for the BOM.

    Returns:
        BOM object with entries.

    Example:
        >>> from semicad import get_registry
        >>> registry = get_registry()
        >>> parts = [registry.get("motor_2207") for _ in range(4)]
        >>> bom = generate_bom(parts, title="Quadcopter BOM")
        >>> print(bom.total_parts)
        4
    """
    # Count components by name
    name_counts: Counter[str] = Counter()
    component_specs: dict[str, ComponentSpec] = {}

    for comp in components:
        if isinstance(comp, Component):
            spec = comp.spec
        else:
            spec = comp

        name_counts[spec.name] += 1
        component_specs[spec.name] = spec

    # Build BOM entries
    entries = []
    for name, count in sorted(name_counts.items()):
        spec = component_specs[name]
        params_str = ", ".join(f"{k}={v}" for k, v in spec.params.items()) if spec.params else ""

        entries.append(
            BOMEntry(
                name=name,
                quantity=count,
                category=spec.category,
                source=spec.source,
                description=spec.description,
                params=params_str,
            )
        )

    return BOM(title=title, entries=entries)


def bom_to_csv(bom: BOM, output_path: Union[str, Path] | None = None) -> str:
    """
    Export BOM to CSV format.

    Args:
        bom: BOM object to export.
        output_path: Optional file path. If provided, writes to file.

    Returns:
        CSV string.

    Example:
        >>> csv_str = bom_to_csv(bom)
        >>> bom_to_csv(bom, "output/bom.csv")
    """
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Name", "Quantity", "Category", "Source", "Description", "Parameters"])

    # Entries
    for entry in bom.entries:
        writer.writerow(
            [
                entry.name,
                entry.quantity,
                entry.category,
                entry.source,
                entry.description,
                entry.params,
            ]
        )

    # Summary
    writer.writerow([])
    writer.writerow(["Total Parts", bom.total_parts])
    writer.writerow(["Unique Parts", bom.unique_parts])

    csv_string = output.getvalue()

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(csv_string)

    return csv_string


def bom_to_json(bom: BOM, output_path: Union[str, Path] | None = None, indent: int = 2) -> str:
    """
    Export BOM to JSON format.

    Args:
        bom: BOM object to export.
        output_path: Optional file path. If provided, writes to file.
        indent: JSON indentation (default 2).

    Returns:
        JSON string.

    Example:
        >>> json_str = bom_to_json(bom)
        >>> bom_to_json(bom, "output/bom.json")
    """
    data = {
        "title": bom.title,
        "total_parts": bom.total_parts,
        "unique_parts": bom.unique_parts,
        "notes": bom.notes,
        "entries": [asdict(e) for e in bom.entries],
    }

    json_string = json.dumps(data, indent=indent)

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_string)

    return json_string


def bom_to_markdown(bom: BOM, output_path: Union[str, Path] | None = None) -> str:
    """
    Export BOM to Markdown table format.

    Args:
        bom: BOM object to export.
        output_path: Optional file path. If provided, writes to file.

    Returns:
        Markdown string.

    Example:
        >>> md_str = bom_to_markdown(bom)
        >>> bom_to_markdown(bom, "output/BOM.md")
    """
    lines = [
        f"# {bom.title}",
        "",
        "| Name | Qty | Category | Source | Description |",
        "|------|-----|----------|--------|-------------|",
    ]

    for entry in bom.entries:
        lines.append(
            f"| {entry.name} | {entry.quantity} | {entry.category} | {entry.source} | {entry.description} |"
        )

    lines.extend(
        [
            "",
            f"**Total Parts:** {bom.total_parts}",
            f"**Unique Parts:** {bom.unique_parts}",
        ]
    )

    if bom.notes:
        lines.extend(["", "## Notes", "", bom.notes])

    md_string = "\n".join(lines)

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md_string)

    return md_string


def export_bom(
    bom: BOM,
    output_path: Union[str, Path],
    format: str | None = None,
) -> Path:
    """
    Export BOM to file, auto-detecting format from extension.

    Args:
        bom: BOM object to export.
        output_path: Output file path.
        format: Force format ("csv", "json", "md"). Auto-detected if None.

    Returns:
        Path to exported file.

    Example:
        >>> export_bom(bom, "output/bom.csv")
        >>> export_bom(bom, "output/parts.json")
        >>> export_bom(bom, "output/BOM.md")
    """
    path = Path(output_path)

    if format is None:
        ext = path.suffix.lower()
        format_map = {".csv": "csv", ".json": "json", ".md": "md", ".markdown": "md"}
        format = format_map.get(ext, "csv")

    if format == "json":
        bom_to_json(bom, path)
    elif format == "md":
        bom_to_markdown(bom, path)
    else:
        bom_to_csv(bom, path)

    return path
