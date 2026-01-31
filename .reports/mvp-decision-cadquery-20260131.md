# MVP Decision Report: CadQuery + cq-editor Stack

**Date:** 2026-01-31
**Project:** semi-autocad
**Goal:** Design quadcopter frame with parametric mount holes

---

## 1. Executive Decision

### Selected Stack

| Component | Solution | Status |
|-----------|----------|--------|
| **Primary CAD Engine** | CadQuery + cq-editor | To install |
| **MCP Server** | cadquery-mcp-server | To install |
| **Knowledge Graph** | Neo4j (neo4j-semicad) | Already configured |
| **Reasoning** | Sequential Thinking | Already configured |
| **Browser Fallback** | Playwright | Already configured |
| **Onshape Integration** | Deferred to Phase 2 | Not needed for MVP |

### Why CadQuery Over Onshape MCP

| Capability | hedless/onshape-mcp | CadQuery |
|------------|---------------------|----------|
| Sketch rectangles | ✅ | ✅ |
| Extrude | ✅ | ✅ |
| Variables | ✅ | ✅ (native Python) |
| **Hole patterns** | ❌ | ✅ |
| **Fillets/chamfers** | ❌ | ✅ |
| **Circular patterns** | ❌ | ✅ |
| **Loft/sweep** | ❌ | ✅ |
| **Boolean operations** | ❌ | ✅ |
| Local execution | ❌ (cloud API) | ✅ |
| No API keys needed | ❌ | ✅ |

**Conclusion:** For quadcopter frame with motor mount holes and structural features, CadQuery provides complete capability while Onshape MCP would require constant Playwright fallback.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code (Orchestrator)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  CadQuery   │  │   Neo4j     │  │ Sequential Thinking │ │
│  │    MCP      │  │   Memory    │  │        MCP          │ │
│  │             │  │             │  │                     │ │
│  │ - Geometry  │  │ - Components│  │ - Design decisions  │ │
│  │ - Features  │  │ - Patterns  │  │ - Problem solving   │ │
│  │ - Export    │  │ - Designs   │  │ - Optimization      │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘ │
│         │                │                                  │
│         ▼                ▼                                  │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │  cq-editor  │  │   Neo4j     │                          │
│  │  (3D View)  │  │  Browser    │                          │
│  │             │  │ :7475       │                          │
│  └─────────────┘  └─────────────┘                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Future: Onshape Integration             │   │
│  │  - Import STEP for CAM/manufacturing                 │   │
│  │  - Collaboration & sharing                           │   │
│  │  - Professional drawings                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Installation Requirements

### 3.1 CadQuery Installation

```bash
# Option A: pip (recommended for MCP integration)
pip install cadquery

# Option B: conda (better dependency management)
conda install -c conda-forge cadquery
```

### 3.2 cq-editor Installation

```bash
# Option A: pip
pip install cq-editor

# Option B: conda (recommended)
conda install -c conda-forge cq-editor

# Option C: Standalone AppImage (Linux)
# Download from: https://github.com/CadQuery/CQ-editor/releases
```

### 3.3 CadQuery MCP Server

```bash
# Clone the MCP server
cd /home/user/cad
git clone https://github.com/rishigundakaram/cadquery-mcp-server.git
cd cadquery-mcp-server
pip install -e .
```

### 3.4 Alternative: mcp-cadquery (HTTP mode with web viewer)

```bash
git clone https://github.com/bertvanbrakel/mcp-cadquery.git
cd mcp-cadquery
pip install -e .
# Includes web-based 3D viewer
```

---

## 4. Configuration Changes

### 4.1 Updated .claude/settings.json

```json
{
  "mcpServers": {
    "cadquery": {
      "command": "python",
      "args": ["-m", "cadquery_mcp_server"],
      "env": {
        "CADQUERY_OUTPUT_DIR": "/home/user/cad/output"
      }
    },
    "neo4j-memory-semicad": {
      "command": "npx",
      "args": ["-y", "@sylweriusz/mcp-neo4j-memory-server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7688",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "semicad2026"
      }
    },
    "neo4j-cypher-semicad": {
      "command": "uvx",
      "args": ["mcp-neo4j-cypher", "--db-url", "bolt://localhost:7688", "--username", "neo4j", "--password", "semicad2026"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

### 4.2 Project Directory Structure

```
/home/user/cad/
├── .claude/
│   ├── settings.json          # MCP configuration
│   └── settings.template.json # Template (no credentials)
├── .reports/
│   ├── mcp-research-20260131.md
│   └── mvp-decision-cadquery-20260131.md
├── cadquery-mcp-server/       # Cloned MCP server
├── scripts/                   # CadQuery scripts
│   └── quadcopter_frame.py
├── output/                    # Generated STEP/STL files
├── components/                # Component definitions
│   └── drone_parts.json
├── CLAUDE.md
├── readme.md
└── .gitignore
```

---

## 5. Neo4j Schema for Drone Components

### 5.1 Node Types

```cypher
// Component base
(:Component {
  id: string,
  name: string,
  type: "motor" | "fc" | "esc" | "battery" | "camera" | "vtx",
  weight_g: float,
  datasheet_url: string
})

// Mount patterns
(:MountPattern {
  id: string,
  type: "square" | "circular" | "linear",
  spacing_mm: float,
  hole_diameter_mm: float,
  hole_count: int
})

// Frame designs
(:Frame {
  id: string,
  name: string,
  wheelbase_mm: float,
  arm_count: int,
  weight_g: float,
  created_at: datetime
})

// Parameters
(:Parameter {
  name: string,
  value: float,
  unit: string
})
```

### 5.2 Relationships

```cypher
(:Component)-[:HAS_MOUNT]->(:MountPattern)
(:Frame)-[:USES_COMPONENT]->(:Component)
(:Frame)-[:HAS_PARAMETER]->(:Parameter)
(:Frame)-[:DERIVED_FROM]->(:Frame)
(:Component)-[:COMPATIBLE_WITH]->(:Component)
```

### 5.3 Sample Data: Common Drone Components

```cypher
// Standard FC mount patterns
CREATE (:MountPattern {id: "fc-30.5", type: "square", spacing_mm: 30.5, hole_diameter_mm: 3.0, hole_count: 4})
CREATE (:MountPattern {id: "fc-20", type: "square", spacing_mm: 20.0, hole_diameter_mm: 2.0, hole_count: 4})

// Common motors
CREATE (:Component {id: "motor-2207-1800kv", name: "2207 1800KV Motor", type: "motor", weight_g: 32})
CREATE (:MountPattern {id: "motor-2207", type: "circular", spacing_mm: 16.0, hole_diameter_mm: 3.0, hole_count: 4})

CREATE (:Component {id: "motor-1404-3800kv", name: "1404 3800KV Motor", type: "motor", weight_g: 12})
CREATE (:MountPattern {id: "motor-1404", type: "circular", spacing_mm: 12.0, hole_diameter_mm: 2.0, hole_count: 4})

// Link motors to patterns
MATCH (m:Component {id: "motor-2207-1800kv"}), (p:MountPattern {id: "motor-2207"})
CREATE (m)-[:HAS_MOUNT]->(p)
```

---

## 6. Visualization Workflow

### 6.1 cq-editor Workflow

```
1. Write CadQuery script in cq-editor
2. Press F5 to execute and render
3. 3D view updates in real-time
4. Adjust parameters, re-run
5. Export final design
```

### 6.2 cq-editor Features

| Feature | Description |
|---------|-------------|
| **3D Viewport** | Interactive rotate, zoom, pan |
| **Object Tree** | Inspect parts, faces, edges |
| **Code Editor** | Syntax highlighting, autocomplete |
| **Console** | Python REPL for testing |
| **Variables Panel** | Quick parameter adjustment |
| **Export** | STEP, STL, SVG from GUI |

### 6.3 Alternative: Jupyter Workflow

```bash
pip install jupyter-cadquery
jupyter lab
```

```python
import cadquery as cq
from jupyter_cadquery import show

result = cq.Workplane("XY").box(10, 10, 5)
show(result)  # Interactive 3D in notebook
```

---

## 7. MVP Implementation Plan

### Phase 1: Environment Setup (Day 1)

- [ ] Install CadQuery: `pip install cadquery`
- [ ] Install cq-editor: `pip install cq-editor`
- [ ] Clone cadquery-mcp-server
- [ ] Update `.claude/settings.json`
- [ ] Create output directory
- [ ] Verify cq-editor launches: `cq-editor`

### Phase 2: Component Library (Day 1-2)

- [ ] Create Neo4j schema (run Cypher above)
- [ ] Populate standard mount patterns
- [ ] Add common motor specs
- [ ] Add FC/ESC specs (F405, F722, etc.)
- [ ] Test queries: "Get all 5-inch quad motors"

### Phase 3: First Frame Script (Day 2-3)

Create `/home/user/cad/scripts/quadcopter_frame.py`:

```python
import cadquery as cq

# ============== PARAMETERS ==============
WHEELBASE = 220        # mm, motor to motor diagonal
ARM_COUNT = 4          # X-frame
ARM_WIDTH = 12         # mm
ARM_THICKNESS = 4      # mm
CENTER_SIZE = 40       # mm, center plate
STACK_HOLE_SPACING = 30.5  # mm, FC mount
MOTOR_HOLE_SPACING = 16    # mm, motor mount
MOTOR_HOLE_DIA = 3.0   # mm, M3

# ============== CALCULATIONS ==============
arm_length = (WHEELBASE / 2) - (CENTER_SIZE / 2)
arm_angle = 360 / ARM_COUNT

# ============== CENTER PLATE ==============
center = (
    cq.Workplane("XY")
    .box(CENTER_SIZE, CENTER_SIZE, ARM_THICKNESS)
    # FC mount holes
    .faces(">Z")
    .rect(STACK_HOLE_SPACING, STACK_HOLE_SPACING, forConstruction=True)
    .vertices()
    .hole(3.2)  # M3 clearance
)

# ============== ARMS ==============
arm = (
    cq.Workplane("XY")
    .box(arm_length, ARM_WIDTH, ARM_THICKNESS)
    .translate((arm_length/2 + CENTER_SIZE/2, 0, 0))
    # Motor mount holes
    .faces(">Z")
    .workplane()
    .center(arm_length/2 + CENTER_SIZE/2, 0)
    .rect(MOTOR_HOLE_SPACING, MOTOR_HOLE_SPACING, forConstruction=True)
    .vertices()
    .hole(MOTOR_HOLE_DIA)
)

# ============== COMBINE ==============
frame = center
for i in range(ARM_COUNT):
    rotated_arm = arm.rotate((0,0,0), (0,0,1), i * arm_angle)
    frame = frame.union(rotated_arm)

# ============== EXPORT ==============
cq.exporters.export(frame, "/home/user/cad/output/quad_frame_220.step")
cq.exporters.export(frame, "/home/user/cad/output/quad_frame_220.stl")

# For cq-editor visualization
show_object(frame, name="Quadcopter Frame 220mm")
```

### Phase 4: Iterate & Validate (Day 3+)

- [ ] Open script in cq-editor
- [ ] Adjust parameters for different sizes (180, 250, 300mm)
- [ ] Add fillets for stress relief
- [ ] Add weight reduction cutouts
- [ ] Export successful designs
- [ ] Store design parameters in Neo4j

---

## 8. CadQuery Quick Reference

### Basic Operations

```python
import cadquery as cq

# Box
box = cq.Workplane("XY").box(10, 20, 5)

# Cylinder
cyl = cq.Workplane("XY").cylinder(10, 5)

# Hole
with_hole = box.faces(">Z").hole(3)

# Fillet
filleted = box.edges("|Z").fillet(1)

# Pattern (rectangular)
pattern = (cq.Workplane("XY")
    .rect(20, 20, forConstruction=True)
    .vertices()
    .hole(3))

# Pattern (circular)
circular = (cq.Workplane("XY")
    .polarArray(radius=10, startAngle=0, angle=360, count=4)
    .hole(3))

# Boolean union
combined = part1.union(part2)

# Export
cq.exporters.export(result, "output.step")
cq.exporters.export(result, "output.stl")
```

### Face Selectors

| Selector | Meaning |
|----------|---------|
| `>Z` | Top face (max Z) |
| `<Z` | Bottom face (min Z) |
| `>X` | Right face |
| `<X` | Left face |
| `\|Z` | Edges parallel to Z |
| `#Z` | Faces perpendicular to Z |

---

## 9. Future Onshape Integration Path

### When to Add Onshape

| Trigger | Action |
|---------|--------|
| Need CAM for CNC | Import STEP to Onshape, use CAM Studio |
| Need collaboration | Push design to Onshape document |
| Need 2D drawings | Use Onshape Drawing tools |
| Need simulation | Use Onshape Intact app |

### Integration Method

```
CadQuery → STEP file → Onshape Import → Refine → Manufacture
```

### Onshape MCP (Future)

When ready, add hedless/onshape-mcp for:
- Variable synchronization (CadQuery params ↔ Onshape variables)
- Document management
- Version tracking

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| CadQuery learning curve | Extensive docs, cq-editor helps |
| MCP server issues | Can run CadQuery standalone |
| Complex geometry limits | Fall back to Onshape UI via Playwright |
| No live collaboration | Export STEP, share via Onshape |

### Fallback Options

1. **If CadQuery MCP fails:** Run scripts directly in cq-editor
2. **If geometry too complex:** Use Onshape + Playwright
3. **If need quick prototype:** Zoo Text-to-CAD → STEP → refine

---

## 11. Success Criteria for MVP

- [ ] 220mm X-frame generated via CadQuery
- [ ] Correct FC mount holes (30.5mm pattern)
- [ ] Correct motor mount holes (16mm pattern)
- [ ] Exported STEP file imports cleanly to slicer
- [ ] Parameters stored in Neo4j
- [ ] Design reproducible by changing variables

---

## 12. Next Actions

### Immediate (Today)

1. Run installation commands from Section 3
2. Update `.claude/settings.json` with CadQuery MCP
3. Create `/home/user/cad/scripts/` and `/home/user/cad/output/` directories
4. Test cq-editor launches

### Tomorrow

1. Populate Neo4j with component data
2. Create first frame script
3. Generate 220mm frame
4. Iterate on design

---

*Report generated by Claude Code for semi-autocad project*
*Decision: CadQuery + cq-editor as primary CAD stack for MVP*
