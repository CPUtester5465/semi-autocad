# Semi-AutoCAD

AI-assisted CAD design system using Claude Code as orchestrator, CadQuery for parametric modeling, and Neo4j for persistent design memory.

## Quick Start

```bash
# Install dependencies
pip install -e ".[all]"

# Test installation
./bin/dev test

# Open assembly viewer
./bin/dev view

# Build frame files
./bin/dev build

# Browse components
./bin/dev lib list
```

## Architecture

```
Claude Code (Orchestrator)
    ├── semicad CLI ───► Component registry, project management
    ├── CadQuery ──────► Parametric modeling, cq-editor visualization
    ├── cq_warehouse ──► Fasteners, bearings, standard parts
    ├── Neo4j ─────────► Design decisions, component relationships
    └── Export ────────► STEP, STL, PNG
```

## Project Structure

```
├── bin/dev                 # CLI entry point
├── semicad/                # Core Python library
│   ├── cli/                # Click-based CLI
│   │   └── commands/       # view, build, library, project
│   ├── core/               # Component, Registry, Project abstractions
│   └── sources/            # Adapters for cq_warehouse, custom components
├── scripts/
│   ├── components.py       # Drone component library (16 components)
│   ├── assembly_viewer.py  # Main assembly for cq-editor
│   └── quadcopter_assembly.py  # Build script
├── projects/               # Sub-projects (e.g., quadcopter-5inch)
├── output/                 # Generated STEP/STL/PNG files
├── docs/                   # Documentation
└── .reports/               # Research and decision reports
```

## CLI Commands

### Core Commands
| Command | Description |
|---------|-------------|
| `./bin/dev view [file]` | Open in cq-editor |
| `./bin/dev build` | Generate STEP/STL files |
| `./bin/dev export <component>` | Export single component |
| `./bin/dev render <stl>` | Render STL to PNG |
| `./bin/dev test` | Test all imports |

### Library Commands
| Command | Description |
|---------|-------------|
| `./bin/dev lib list` | List all components |
| `./bin/dev lib info <name>` | Component details |
| `./bin/dev lib fasteners` | Show fastener sizes |
| `./bin/dev lib bearings` | Show bearing sizes |
| `./bin/dev search <query>` | Search components |

### Project Commands
| Command | Description |
|---------|-------------|
| `./bin/dev project info` | Show current project |
| `./bin/dev project list` | List sub-projects |
| `./bin/dev project neo4j` | Open Neo4j browser |

## Component Sources

| Source | Components | Description |
|--------|------------|-------------|
| `custom` | 16 | Drone parts (motors, FC, ESC, batteries, props) |
| `cq_warehouse` | 1000+ | Fasteners, bearings, chains, sprockets |
| `cq_electronics` | 7 | Electronic boards, connectors, SMD, mechanical, mounting |

## cq_electronics Components

Electronic component library for enclosure design and PCB integration.

### Available Components

| Name | Category | Description | Required Params |
|------|----------|-------------|-----------------|
| `RPi3b` | board | Raspberry Pi 3B SBC | - |
| `PinHeader` | connector | Through-hole pin header | - |
| `JackSurfaceMount` | connector | RJ45 Ethernet jack | - |
| `BGA` | smd | Ball Grid Array package | `length`, `width` |
| `DinClip` | mechanical | DIN rail mounting clip | - |
| `TopHat` | mechanical | TH35 DIN rail section | `length` |
| `PiTrayClip` | mounting | Raspberry Pi mounting tray clip | - |

### Electronics Usage

```python
from semicad import get_registry

registry = get_registry()

# Get Raspberry Pi board
rpi = registry.get("RPi3b")

# Parametric pin header (2x20 GPIO header)
header = registry.get("PinHeader", rows=2, columns=20)

# BGA chip package (required: length, width)
chip = registry.get("BGA", length=10, width=10, height=1.2)

# DIN rail section
rail = registry.get("TopHat", length=100)

# Access geometry for positioning
geometry = rpi.geometry  # CadQuery Workplane
```

### Parameter Reference

**PinHeader** (all optional):
- `rows`: Number of rows (default: 1)
- `columns`: Number of columns (default: 1)
- `above`: Pin height above board in mm (default: 7)
- `below`: Pin height below board in mm (default: 3)
- `simple`: Use simplified geometry (default: True)

**BGA** (length/width required):
- `length`: Package length in mm (required)
- `width`: Package width in mm (required)
- `height`: Package height in mm (default: 1)
- `simple`: Use simplified geometry (default: True)

**TopHat** (length required):
- `length`: Rail length in mm (required)
- `depth`: Rail depth in mm (default: 7.5)
- `slots`: Include mounting slots (default: True)

## Usage in Code

```python
from semicad import get_registry

# Get a component
registry = get_registry()
motor = registry.get("motor_2207")
screw = registry.get("SocketHeadCapScrew", size="M3-0.5", length=10)

# Access geometry
geometry = motor.geometry  # CadQuery Workplane

# Position components
motor_positioned = motor.translate(50, 50, 0)
```

## Neo4j Database

- **URL:** http://localhost:7475
- **Bolt:** bolt://localhost:7688
- **Credentials:** neo4j / semicad2026

## Documentation

- [cq_electronics Integration](/docs/electronics.md)
- [CQ-Editor Multi-File Setup](/docs/cq-editor-multifile.md)
- [MCP Research](/.reports/mcp-research-20260131.md)
- [Stack Decision](/.reports/mvp-decision-cadquery-20260131.md)
- [Component Library Research](/.reports/component-library-research-20260131.md)
- [CAD Task Flows](/.reports/cad-task-flows-20260131.md)
