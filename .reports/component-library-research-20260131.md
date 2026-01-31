# Component Library Research Report

**Date:** 2026-01-31
**Project:** semi-autocad
**Objective:** Identify best solution for extensive multi-project CAD component library

---

## 1. Executive Summary

### Key Finding

**Don't build a component library from scratch - mature solutions already exist.**

| Solution | Purpose | Maturity |
|----------|---------|----------|
| **cq_warehouse** | Fasteners, bearings, chains, threads | Production-ready |
| **cq-electronics** | Electronic boards and components | Production-ready |
| **PartCAD** | Package manager for CAD projects | Production-ready |

### Recommendation

Integrate existing libraries instead of building from scratch:
- Use **cq_warehouse** for mechanical components (1000+ parts)
- Use **cq-electronics** for electronic components
- Use **PartCAD** for multi-project management
- Use **Neo4j** for design decision memory (our value-add)

---

## 2. Research Methodology

### Sources Searched
- GitHub repositories and documentation
- PyPI package registry
- Hacker News discussions
- ReadTheDocs documentation
- CadQuery community resources

### Search Queries
- "parametric CAD component library open source CadQuery"
- "cq-warehouse cadquery parts library"
- "PartCAD package manager CAD models"
- "cq-electronics cadquery electronic components"
- "build123d vs cadquery parts library"

---

## 3. Detailed Findings

### 3.1 cq_warehouse

**Repository:** https://github.com/gumyr/cq_warehouse
**Documentation:** https://cq-warehouse.readthedocs.io/
**Installation:** `pip install cq-warehouse`

#### Description

cq_warehouse augments CadQuery with parametric parts generated on demand and extensions to the core CadQuery capabilities. Parts can be exported to STEP, STL, and other formats.

#### Available Components

| Category | Components |
|----------|------------|
| **Fasteners** | SocketHeadCapScrew, ButtonHeadCapScrew, CounterSunkScrew, HexBolt, SetScrew, HexNut, SquareNut, Washer, LockWasher |
| **Bearings** | SingleRowDeepGrooveBallBearing, SingleRowCappedDeepGrooveBallBearing |
| **Threads** | IsoThread, AcmeThread, MetricTrapezoidalThread, PlasticBottleThread |
| **Chains** | Chain (inner links with rollers, outer links with pins) |
| **Sprockets** | Parametric sprockets for chain drives |
| **Drafting** | Model-based definition tools |

#### Fastener Standards Supported

**Metric Screws:**
- ISO 4762 (Socket Head Cap Screw)
- ISO 4014 (Hex Head Bolt)
- ISO 7380 (Button Head)
- ISO 10642 (Countersunk)
- DIN 916 (Set Screw)

**Metric Nuts:**
- ISO 4032 (Hex Nut)
- ISO 4035 (Thin Hex Nut)
- ISO 7092 (Flat Washer)
- ISO 7093 (Large Flat Washer)

**Sizes:** M1.6 through M36

**Imperial:** Also supported (UNC, UNF)

#### Usage Example

```python
from cq_warehouse.fastener import SocketHeadCapScrew, HexNut
from cq_warehouse.bearing import SingleRowDeepGrooveBallBearing

# Create M3x10 socket head cap screw
screw = SocketHeadCapScrew(
    size="M3-0.5",
    fastener_type="iso4762",
    length=10,
    simple=True  # Simple threads (faster) or accurate threads
)

# Create 608 bearing (skateboard bearing)
bearing = SingleRowDeepGrooveBallBearing(
    size="M8-22-7",
    bearing_type="SKT"
)

# Create hex nut
nut = HexNut(size="M3-0.5", fastener_type="iso4032")

# Get CadQuery solid
screw_solid = screw.cq_object
bearing_solid = bearing.cq_object
```

#### Key Features

- **Parametric generation:** Parts generated from parameters, not static models
- **Thread options:** Simple (cylinder) or accurate (helical) threads
- **Handedness:** Left and right-hand threads supported
- **Press-fit holes:** `pressFitHole()` method for bearing installation
- **Clearance holes:** `clearanceHole()` method for fastener installation
- **Extensions:** Enhanced CadQuery methods for projecting, embossing, sectioning

---

### 3.2 cq-electronics

**Repository:** https://github.com/sethfischer/cq-electronics
**Documentation:** https://cq-electronics.readthedocs.io/
**Installation:** `pip install cq-electronics`

#### Description

Pure CadQuery models of various electronic boards and components. Models are representations suitable for mechanical design (enclosures, mounts) rather than electrically accurate.

#### Available Components

| Category | Components |
|----------|------------|
| **Single Board Computers** | Raspberry Pi 3 Model B, Raspberry Pi Zero |
| **Connectors** | Pin headers (male/female), RJ45, USB |
| **Mounting** | DIN rail clips, DIN rails |
| **SMD Packages** | BGA, QFP, SOIC footprints |
| **Accessories** | Sourcekit PiTray Clip |

#### Usage Example

```python
from cq_electronics.rpi import RaspberryPi3B
from cq_electronics.connectors import PinHeader

# Create Raspberry Pi 3 Model B
rpi = RaspberryPi3B()

# Create 40-pin header
header = PinHeader(rows=2, cols=20, pitch=2.54)

# Get dimensions for enclosure design
rpi_dims = rpi.bounding_box()
```

#### Limitations

- Smaller library compared to cq_warehouse
- Focus on representation, not electrical accuracy
- Limited microcontroller selection (no Arduino, ESP32 yet)

---

### 3.3 PartCAD - Package Manager for CAD

**Repository:** https://github.com/partcad/partcad
**Website:** https://partcad.org/
**Documentation:** https://partcad.readthedocs.io/
**Installation:** `pip install partcad partcad-cli`

#### Description

PartCAD is the **first package manager for CAD models**. It manages parts, assemblies, and entire projects with Git-based versioning. Think "npm for hardware."

#### Key Concepts

| Concept | Description |
|---------|-------------|
| **Package** | A collection of parts and assemblies (like npm package) |
| **Part** | Individual component (CadQuery, build123d, OpenSCAD, or STEP file) |
| **Assembly** | YAML file describing how parts fit together |
| **Import** | Reference parts from other packages |

#### Features

**Project Management:**
- `partcad.yaml` configuration file
- Package dependencies and imports
- Version control friendly

**Multi-Format Support:**
- CadQuery scripts (.py)
- build123d scripts (.py)
- OpenSCAD scripts (.scad)
- STEP files (.step)
- STL files (.stl)
- BREP files (.brep)

**Assembly System:**
- YAML-based assembly definitions (.assy files)
- Automatic bill-of-materials generation
- Transform/position parts in assemblies

**Export & Rendering:**
- Export to STEP, STL, 3MF, OBJ, GLTF
- Render PNG images
- Generate documentation

**AI Integration (Experimental):**
- AI-assisted design modifications
- Natural language to CAD

#### CLI Commands

```bash
# Project management
pc init                          # Initialize new package
pc install                       # Install dependencies
pc list parts                    # List all parts
pc list assemblies               # List all assemblies

# Import parts from other packages
pc add cq-warehouse              # Add cq_warehouse as dependency
pc import part <file>            # Import existing part

# Visualization
pc inspect <part>                # View part in 3D
pc render <part> --format png    # Render to image

# Export
pc export <part> --format step   # Export to STEP
pc convert <file> --to stl       # Convert formats

# Assembly
pc inspect <assembly.assy>       # View assembly
pc render <assembly.assy>        # Render assembly
```

#### Example: partcad.yaml

```yaml
name: quadcopter-frame
version: 0.1.0
desc: 5-inch freestyle quadcopter frame

# Import external packages
import:
  cq-warehouse:
    type: git
    url: https://github.com/gumyr/cq_warehouse

# Define parts
parts:
  frame:
    type: cadquery
    path: parts/frame.py

  motor-mount:
    type: cadquery
    path: parts/motor_mount.py

# Define assemblies
assemblies:
  quadcopter:
    type: assy
    path: assemblies/quadcopter.assy
```

#### Example: Assembly File (quadcopter.assy)

```yaml
links:
  - part: frame
    location: [[0, 0, 0], [0, 0, 1], 0]

  - part: cq-warehouse:SocketHeadCapScrew
    params:
      size: M3-0.5
      length: 10
    location: [[15, 15, 5], [0, 0, 1], 0]

  - part: motor-mount
    name: motor_fl
    location: [[77, 77, 0], [0, 0, 1], 45]
```

#### Why PartCAD is a Game-Changer

1. **Package reuse:** Import cq_warehouse and get 1000+ parts instantly
2. **Version control:** Git-friendly YAML configs, not binary blobs
3. **Assembly management:** YAML-based, human-readable assemblies
4. **Multi-project:** Each project is a package, can import from others
5. **Format agnostic:** Mix CadQuery, OpenSCAD, STEP in same project
6. **CLI + Python API:** Use from terminal or in scripts

---

### 3.4 build123d + bd_warehouse

**Repository:** https://github.com/gumyr/build123d
**Parts Library:** bd_warehouse (same author as cq_warehouse)

#### Description

build123d is a Python CAD framework derived from CadQuery but with a more "pythonic" API using context managers instead of method chaining.

#### Key Differences from CadQuery

| Aspect | CadQuery | build123d |
|--------|----------|-----------|
| Style | Method chaining (fluent) | Context managers (with blocks) |
| Debugging | Harder (chain breaks) | Easier (insert print anywhere) |
| Extensibility | Monkey patching | Standard class inheritance |
| Selectors | String-based | Enum-based |

#### Example Comparison

```python
# CadQuery style
result = (
    cq.Workplane("XY")
    .box(10, 10, 5)
    .faces(">Z")
    .hole(3)
)

# build123d style
with BuildPart() as part:
    Box(10, 10, 5)
    with Locations((0, 0, 5)):
        Hole(3)
result = part.part
```

#### bd_warehouse

Same components as cq_warehouse but for build123d:
- Fasteners
- Bearings
- Threads
- Chains/Sprockets

#### Recommendation

For this project, **stick with CadQuery + cq_warehouse** because:
1. cq_warehouse is more mature
2. More community resources
3. cq-editor optimized for CadQuery
4. Can always convert between them if needed

---

### 3.5 Other Libraries Discovered

#### cq-queryabolt
- Quick nutcatches, screw holes, countersinks
- Standards-compliant hole generation
- https://github.com/mmalecki/cq-queryabolt

#### CQ_Gears
- Involute profile gear generator
- Spur, helical, bevel gears
- https://github.com/meadiode/cq_gears

#### cq-gridfinity
- Gridfinity storage system components
- Baseplates, boxes, dividers
- https://github.com/smkent/cq-gridfinity

#### KiCad Packages3D Generator
- Generate 3D models for KiCad components
- STEP and VRML output
- https://gitlab.com/kicad/libraries/kicad-packages3D-generator

---

## 4. Architecture Comparison

### Option A: Build From Scratch (Original Plan)

```
/home/user/cad/
├── core/
│   ├── components/
│   │   ├── electronics.py      # Write ourselves
│   │   ├── fasteners.py        # Write ourselves
│   │   ├── bearings.py         # Write ourselves
│   │   └── ...                 # Months of work
│   └── specs/
│       └── *.yaml              # Maintain ourselves
└── projects/
```

**Pros:**
- Full control
- Exactly what we need

**Cons:**
- Reinventing the wheel
- Months of development
- No community support
- Must maintain ourselves

---

### Option B: Use Existing Libraries (Recommended)

```
/home/user/cad/
├── partcad.yaml                # PartCAD project config
│
├── parts/                      # Our custom parts only
│   └── *.py                    # CadQuery scripts
│
├── assemblies/                 # Assembly definitions
│   └── *.assy                  # YAML assembly files
│
├── output/                     # Generated files
│
└── .neo4j/                     # Our value-add
    └── design_decisions        # Decision tracking
```

**External (pip installed):**
- cq_warehouse (fasteners, bearings, threads)
- cq-electronics (boards, connectors)
- partcad (project management)

**Pros:**
- 1000+ parts immediately available
- Community maintained
- Focus on our unique value-add
- Standard interfaces

**Cons:**
- Dependency on external projects
- May need to contribute upstream for missing parts

---

## 5. Recommended Implementation

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code                               │
│                       (Orchestrator)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXTERNAL LIBRARIES (pip install)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ cq_warehouse │  │cq-electronics│  │      PartCAD         │   │
│  │              │  │              │  │                      │   │
│  │ - Fasteners  │  │ - RPi        │  │ - Project mgmt       │   │
│  │ - Bearings   │  │ - Connectors │  │ - Assembly YAML      │   │
│  │ - Threads    │  │ - DIN rail   │  │ - Import/Export      │   │
│  │ - Chains     │  │              │  │ - Versioning         │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  OUR VALUE-ADD                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │    Neo4j     │  │   bin/dev    │  │   Custom Parts       │   │
│  │              │  │     CLI      │  │                      │   │
│  │ - Decisions  │  │              │  │ - Domain-specific    │   │
│  │ - History    │  │ - Wraps pc   │  │ - Not in libraries   │   │
│  │ - Relations  │  │ - Neo4j ops  │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  VISUALIZATION                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              cq-editor / PartCAD inspect                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Installation

```bash
# Core libraries
pip install cadquery cq-editor
pip install cq-warehouse
pip install cq-electronics
pip install partcad partcad-cli

# Our existing
pip install -e .  # Install our project
```

### Project Structure

```
/home/user/cad/
├── partcad.yaml              # PartCAD package definition
│
├── parts/                    # Custom CadQuery parts
│   ├── drone_frame.py
│   ├── motor_mount.py
│   └── camera_mount.py
│
├── assemblies/               # PartCAD assembly files
│   ├── quadcopter-220.assy
│   ├── quadcopter-180.assy
│   └── robot-arm.assy
│
├── bin/
│   └── dev                   # Enhanced CLI
│
├── core/                     # Our utilities
│   └── neo4j/
│       ├── schema.py
│       └── queries.py
│
├── output/                   # Generated files
│   ├── quadcopter-220/
│   └── robot-arm/
│
├── docs/
├── .reports/
└── .claude/
```

### Example: partcad.yaml

```yaml
name: semi-autocad
version: 0.1.0
desc: AI-assisted CAD system with Claude Code

# Import external libraries
import:
  warehouse:
    type: pypi
    package: cq-warehouse

  electronics:
    type: pypi
    package: cq-electronics

# Our custom parts
parts:
  drone-frame-220:
    type: cadquery
    path: parts/drone_frame.py
    parameters:
      wheelbase: 220

  motor-mount-2207:
    type: cadquery
    path: parts/motor_mount.py
    parameters:
      motor_size: 2207

# Assemblies
assemblies:
  quadcopter-220:
    type: assy
    path: assemblies/quadcopter-220.assy
```

### Example: Assembly Using cq_warehouse Parts

```yaml
# assemblies/quadcopter-220.assy
links:
  # Our custom frame
  - part: drone-frame-220
    name: frame
    location: [[0, 0, 0], [0, 0, 1], 0]

  # cq_warehouse screws for FC mount
  - part: warehouse:SocketHeadCapScrew
    name: fc_screw_1
    params:
      size: M3-0.5
      fastener_type: iso4762
      length: 8
    location: [[15.25, 15.25, 5], [0, 0, 1], 0]

  - part: warehouse:SocketHeadCapScrew
    name: fc_screw_2
    params:
      size: M3-0.5
      fastener_type: iso4762
      length: 8
    location: [[-15.25, 15.25, 5], [0, 0, 1], 0]

  # ... more screws, nuts, etc.
```

### CLI Enhancement

```bash
# bin/dev commands
./bin/dev projects              # List PartCAD projects
./bin/dev new <name>            # Create new project (pc init wrapper)
./bin/dev parts                 # List all parts (pc list parts)
./bin/dev view <part>           # Inspect part (pc inspect)
./bin/dev build <assembly>      # Build assembly (pc render)
./bin/dev export <assembly>     # Export STEP/STL
./bin/dev decisions             # Show Neo4j decisions
./bin/dev decide "<question>"   # Record decision
```

---

## 6. Migration Plan

### Phase 1: Install Libraries

```bash
pip install cq-warehouse cq-electronics partcad partcad-cli
```

### Phase 2: Initialize PartCAD

```bash
cd /home/user/cad
pc init
```

### Phase 3: Migrate Quadcopter

1. Move `scripts/components.py` custom parts to `parts/`
2. Create `assemblies/quadcopter-220.assy`
3. Reference cq_warehouse fasteners instead of custom

### Phase 4: Update CLI

Enhance `bin/dev` to wrap PartCAD commands with Neo4j integration.

### Phase 5: Test

```bash
pc list parts           # Should show cq_warehouse + our parts
pc inspect quadcopter-220.assy  # Should render assembly
```

---

## 7. What We Still Build

Even with external libraries, we add value:

| Component | Purpose |
|-----------|---------|
| **Neo4j Integration** | Track design decisions across sessions |
| **bin/dev CLI** | Unified interface wrapping PartCAD + Neo4j |
| **Domain Parts** | Drone-specific parts not in libraries |
| **CLAUDE.md** | Instructions for Claude Code integration |
| **MCP Tools** | Optional: MCP server for PartCAD commands |

---

## 8. Comparison: Build vs Buy

| Aspect | Build From Scratch | Use Libraries |
|--------|-------------------|---------------|
| Time to MVP | Months | Days |
| Fasteners | Write ourselves | 1000+ ready |
| Bearings | Write ourselves | Ready |
| Electronics | Write ourselves | RPi, connectors ready |
| Multi-project | Build system | PartCAD ready |
| Maintenance | All on us | Community |
| Customization | Full control | Contribute upstream |
| Learning curve | Learn CadQuery | Learn CadQuery + PartCAD |

**Verdict:** Use libraries. Focus our effort on the unique value-add (Neo4j decisions, Claude Code integration).

---

## 9. References

### Primary Libraries

- **cq_warehouse:** https://github.com/gumyr/cq_warehouse
- **cq-electronics:** https://github.com/sethfischer/cq-electronics
- **PartCAD:** https://github.com/partcad/partcad
- **build123d:** https://github.com/gumyr/build123d

### Documentation

- cq_warehouse docs: https://cq-warehouse.readthedocs.io/
- cq-electronics docs: https://cq-electronics.readthedocs.io/
- PartCAD docs: https://partcad.readthedocs.io/
- CadQuery docs: https://cadquery.readthedocs.io/

### Community Resources

- Awesome CadQuery: https://github.com/CadQuery/awesome-cadquery
- Awesome build123d: https://github.com/phillipthelen/awesome-build123d
- CadQuery Google Group: https://groups.google.com/g/cadquery

### Additional Libraries

- cq-queryabolt: https://github.com/mmalecki/cq-queryabolt
- CQ_Gears: https://github.com/meadiode/cq_gears
- cq-gridfinity: https://github.com/smkent/cq-gridfinity

---

## 10. Conclusion

The research reveals that building an extensive component library from scratch would be reinventing the wheel. Mature, well-maintained libraries already exist:

1. **cq_warehouse** provides 1000+ mechanical parts
2. **cq-electronics** provides electronic components
3. **PartCAD** solves multi-project management

Our value-add should focus on:
- Neo4j integration for design decision memory
- Claude Code orchestration
- Domain-specific parts not covered by libraries
- Unified CLI experience

**Recommended next step:** Install libraries and migrate quadcopter project to PartCAD format.

---

*Report generated by Claude Code for semi-autocad project*
*Research conducted: 2026-01-31*
