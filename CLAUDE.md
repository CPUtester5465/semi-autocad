# CLAUDE.md

Instructions for Claude Code when working in this repository.

## Project Overview

**semi-autocad** - AI-assisted parametric CAD system using:
- **semicad** - Python CLI and component registry
- **CadQuery** - Parametric 3D modeling engine
- **cq-editor** - 3D visualization GUI
- **cq_warehouse** - Standard parts library (fasteners, bearings)
- **Neo4j** - Persistent component library and design decisions

## Architecture

```
semicad CLI (./bin/dev)
    │
    ├── Core Library (semicad/)
    │   ├── cli/commands/     # Click-based CLI
    │   ├── core/             # Component, Registry, Project
    │   └── sources/          # Component source adapters
    │
    ├── Component Sources
    │   ├── custom (scripts/components.py)
    │   ├── cq_warehouse (fasteners, bearings)
    │   └── cq_electronics (boards, connectors)
    │
    ├── Projects (projects/)
    │   └── quadcopter-5inch/  # MVP project
    │
    └── Output
        ├── STEP files (CAD exchange)
        ├── STL files (3D printing)
        └── BOM (bill of materials)
```

## CLI Commands

```bash
# Core
./bin/dev view [file]       # Open cq-editor
./bin/dev build             # Build root project
./bin/dev export <comp>     # Export component to STEP/STL
./bin/dev render <stl>      # Render STL to PNG
./bin/dev test              # Test all imports

# Library
./bin/dev lib list          # List all components
./bin/dev lib info <comp>   # Component details
./bin/dev lib fasteners     # Show fastener sizes
./bin/dev lib bearings      # Show bearing sizes
./bin/dev search <query>    # Search components

# Projects
./bin/dev project info      # Current project info
./bin/dev project list      # List sub-projects
./bin/dev project build <name>              # Build sub-project
./bin/dev project build <name> --variant X  # Build variant
./bin/dev project view <name>               # Open in cq-editor
./bin/dev project neo4j     # Open Neo4j browser
```

## Project Structure

```
/home/user/cad/
├── bin/dev                    # CLI entry point (bash wrapper)
├── semicad/                   # Core Python library
│   ├── cli/                   # Click CLI
│   │   └── commands/          # view, build, library, project
│   ├── core/                  # Component, Registry, Project
│   └── sources/               # Source adapters (custom, warehouse)
├── scripts/
│   ├── components.py          # Drone component library (16 parts)
│   └── export_views.py        # Export utilities
├── projects/
│   └── quadcopter-5inch/      # MVP sub-project
│       ├── partcad.yaml       # Project manifest
│       ├── config.py          # Configuration (3 variants)
│       ├── frame.py           # Frame generator
│       ├── assembly.py        # Full assembly
│       ├── build.py           # Build script
│       └── output/            # Generated files
├── docs/                      # Documentation
├── .reports/                  # Research and audit reports
└── .claude/                   # MCP configuration
```

## Component Registry

Access components via the registry:

```python
from semicad import get_registry

registry = get_registry()

# Custom drone components
motor = registry.get("motor_2207")
fc = registry.get("fc_f405_30x30")

# cq_warehouse fasteners
screw = registry.get("SocketHeadCapScrew", size="M3-0.5", length=10)

# cq_electronics boards and connectors
rpi = registry.get("RPi3b")
header = registry.get("PinHeader", rows=2, columns=20)
chip = registry.get("BGA", length=10, width=10)

# Access geometry
geometry = motor.geometry  # CadQuery Workplane
```

## cq_electronics Components

Electronic components for enclosure design and PCB integration.

### Available Components

| Name | Category | Required Params | Description |
|------|----------|-----------------|-------------|
| `RPi3b` | board | - | Raspberry Pi 3B |
| `PinHeader` | connector | - | Through-hole pin header |
| `JackSurfaceMount` | connector | - | RJ45 Ethernet jack |
| `BGA` | smd | `length`, `width` | Ball Grid Array package |
| `DinClip` | mechanical | - | DIN rail mounting clip |
| `TopHat` | mechanical | `length` | TH35 DIN rail section |
| `PiTrayClip` | mounting | - | Raspberry Pi mounting tray clip (76x20x15mm) |

### Usage Examples

```python
from semicad import get_registry

registry = get_registry()

# Raspberry Pi 3B (no parameters)
rpi = registry.get("RPi3b")
rpi_geometry = rpi.geometry

# Parametric pin header for GPIO
gpio_header = registry.get("PinHeader", rows=2, columns=20, above=8.5)

# BGA chip (required: length, width)
processor = registry.get("BGA", length=14, width=14, height=1.4)

# DIN rail for industrial enclosures
din_rail = registry.get("TopHat", length=150)
din_clip = registry.get("DinClip")
```

### Parameter Defaults

**PinHeader:** `rows=1, columns=1, above=7, below=3, simple=True`
**BGA:** `height=1, simple=True` (length/width required)
**TopHat:** `depth=7.5, slots=True` (length required)

### Component Metadata

Electronics components expose metadata properties:

```python
rpi = registry.get("RPi3b")

# Dimensions as (width, height, thickness)
rpi.dimensions  # (85.0, 56.0, 1.5)

# Mounting hole locations as [(x, y), ...]
rpi.mounting_holes  # [(24.5, 19.0), (-24.5, -39.0), ...]

# All UPPER_CASE class constants
rpi.metadata  # {'WIDTH': 85, 'HEIGHT': 56, 'HOLE_DIAMETER': 2.7, ...}

# Access raw cq_electronics instance
rpi.raw_instance.hole_points
```

### Assembly Preservation

Components that are assemblies preserve their structure:

```python
rpi = registry.get("RPi3b")

# Check if component has assembly
if rpi.has_assembly:
    # List sub-parts
    rpi.list_parts()  # ['rpi__pcb_substrate', 'rpi__ethernet_port', ...]

    # Get part colors (RGBA 0-1)
    rpi.get_color_map()  # {'rpi__pcb_substrate': (0.85, 0.75, 0.55, 1.0)}

    # Get specific sub-part geometry
    ethernet = rpi.get_part("rpi__ethernet_port")

    # Export with colors preserved
    rpi.assembly.save("rpi_colored.step")
```

### Utility Constants

Access standard hole sizes and colors:

```python
from semicad.sources.electronics import HOLE_SIZES, COLORS

# Hole diameters for mounting
HOLE_SIZES["M4_CLEARANCE_NORMAL"]  # 4.5mm
HOLE_SIZES["M2R5_TAP_HOLE"]        # 2.15mm

# Component colors (RGB 0-1)
COLORS["pcb_substrate_chiffon"]    # PCB color
COLORS["solder_mask_green"]        # Solder mask
```

### Limitations

- `simple=True` uses simplified geometry (faster, less detail)
- Components from `cq_electronics` may return `Assembly` objects, which are automatically converted to `Workplane` via `toCompound()`
- Not all cq_electronics components are exposed; catalog can be extended in `semicad/sources/electronics.py`

## Sub-Project Development

Each sub-project in `projects/` should have:

```
projects/<name>/
├── partcad.yaml       # Manifest with config, dependencies
├── config.py          # Parameters and variants
├── frame.py           # Part generators (show_object at module level)
├── assembly.py        # Assembly with positioned components
├── build.py           # CLI build script with argparse
└── output/            # Generated STEP, STL, BOM
```

**Important for cq-editor:** Put `show_object()` at module level (not inside `if __name__`):

```python
# Generate for visualization
_frame = generate_frame()

# For cq-editor
try:
    show_object(_frame, name="Frame")
except NameError:
    pass  # Not in cq-editor

# CLI execution
if __name__ == "__main__":
    # export, print, etc.
```

## Design Workflow

1. **Browse components:** `./bin/dev lib list`, `./bin/dev search motor`
2. **Create sub-project:** Copy from quadcopter-5inch template
3. **Define config:** Set parameters in config.py
4. **Generate parts:** Write CadQuery generators
5. **Position assembly:** Use component registry
6. **Visualize:** `./bin/dev project view <name>`
7. **Build:** `./bin/dev project build <name>`

## Neo4j (Design Memory)

- **URL:** http://localhost:7475
- **Bolt:** bolt://localhost:7688
- **Credentials:** neo4j / semicad2026

Store design decisions and component relationships for cross-session continuity.

## Key Files

| File | Purpose |
|------|---------|
| `scripts/components.py` | 16 drone components (motors, FC, ESC, batteries, props) |
| `semicad/core/registry.py` | Component discovery and loading |
| `semicad/sources/warehouse.py` | cq_warehouse adapter (fasteners, bearings) |
| `semicad/sources/electronics.py` | cq_electronics adapter (boards, connectors) |
| `projects/quadcopter-5inch/build.py` | Example build script with variants |

## Dependency Version Compatibility

| Dependency | Minimum Version | Notes |
|------------|-----------------|-------|
| Python | 3.10 | Required for type hints |
| cadquery | 2.5.0 | Core CAD engine |
| cq_electronics | 0.2.0 | Electronic components (RPi, connectors) |
| cq_warehouse | - | Fasteners and bearings (no minimum) |

The `ElectronicsSource` adapter checks cq_electronics version on initialization and warns if the installed version is below the minimum. Version info is included in error messages for debugging.
