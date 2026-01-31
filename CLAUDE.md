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

# Access geometry
geometry = motor.geometry  # CadQuery Workplane
```

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
| `semicad/sources/warehouse.py` | cq_warehouse adapter |
| `projects/quadcopter-5inch/build.py` | Example build script with variants |
