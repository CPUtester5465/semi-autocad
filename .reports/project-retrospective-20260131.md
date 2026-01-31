# Semi-AutoCAD Project Retrospective

**Date:** 2026-01-31
**Project:** semi-autocad
**Status:** MVP Complete - Quadcopter Frame Assembly

---

## 1. Executive Summary

This report documents the journey from concept to working MVP, capturing decisions, pivots, and establishing patterns for scaling to larger CAD projects.

### What We Built

| Component | Status | Purpose |
|-----------|--------|---------|
| Component Library | ✅ Complete | Parametric drone parts (FC, ESC, motors, battery, props) |
| Assembly System | ✅ Complete | Position components, generate frame around them |
| Neo4j Knowledge Graph | ✅ Configured | Store component specs, mount patterns |
| PNG/STL Export | ✅ Working | Visualization pipeline |
| cq-editor Visualization | ✅ Working | Interactive 3D assembly view |

### Key Insight

**Design components first, then frame around them** - not the reverse.

---

## 2. The Journey: How We Got Here

### Phase 1: Initial Research

**Goal:** Find best MCP servers for Onshape CAD integration.

**Research conducted:**
- 2 dedicated Onshape MCP servers found
- 15+ CAD-specific MCPs evaluated
- 7,400+ Claude Code skills searched (none for CAD)
- Hidden gems explored (Zoo Text-to-CAD, MecAgent, etc.)

**Key finding:** No single MCP covers all Onshape capabilities.

### Phase 2: First Attempt - Frame-First Design

**Approach:** Design frame, then fit components.

**Problem identified by user:**
> "I think we need to first model (or find models for) components and then around them - get result"

**Lesson learned:** Frame-first design is backwards. Real engineering starts with components.

### Phase 3: Stack Decision

**Original plan:** Onshape MCP as primary CAD tool.

**Reality check:** hedless/onshape-mcp limitations:
- ✅ Sketch rectangles, extrude, variables
- ❌ Hole patterns (critical for motor mounts)
- ❌ Fillets/chamfers (stress relief)
- ❌ Circular patterns (4x motor layout)

**Pivot:** CadQuery + cq-editor as primary stack.

| Criteria | Onshape MCP | CadQuery |
|----------|-------------|----------|
| Hole patterns | ❌ | ✅ |
| Full parametric | Limited | ✅ |
| Local execution | ❌ (cloud API) | ✅ |
| No API keys | ❌ | ✅ |
| Visualization | Via Playwright | cq-editor |

### Phase 4: Component-First Implementation

**New workflow:**
```
1. Define components with real dimensions
2. Position in 3D space (assembly)
3. Generate frame geometry AROUND components
4. Verify clearances (prop discs)
5. Export for manufacturing
```

**Scripts created:**
- `components.py` - Parametric component library
- `quadcopter_assembly.py` - Assembly with module imports
- `view_assembly.py` - Standalone visualization (no imports)
- `export_views.py` - PNG/SVG/STL export utilities

### Phase 5: Visualization Challenges

**Issue 1:** SVG exports appeared empty (viewer issue, not content).

**Issue 2:** cq-editor couldn't find module imports when launched from different directory.

**Solution:** Created standalone `view_assembly.py` with all code inline.

**PNG rendering:** trimesh + pyglet works for headless PNG generation.

---

## 3. Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code                               │
│                       (Orchestrator)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │   CadQuery   │  │    Neo4j     │  │  Sequential Thinking   │ │
│  │              │  │   Memory     │  │                        │ │
│  │ - Geometry   │  │              │  │  - Design decisions    │ │
│  │ - Boolean    │  │ - Components │  │  - Problem analysis    │ │
│  │ - Export     │  │ - Patterns   │  │  - Trade-offs          │ │
│  └──────┬───────┘  │ - Designs    │  └────────────────────────┘ │
│         │          └──────┬───────┘                              │
│         ▼                 │                                      │
│  ┌──────────────┐         │                                      │
│  │  cq-editor   │         │                                      │
│  │  (3D View)   │◄────────┘                                      │
│  └──────────────┘   Query component specs                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Output Pipeline                        │   │
│  │  CadQuery → STL → trimesh → PNG                          │   │
│  │          → STEP → Onshape/Slicer                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Neo4j Schema for Persistence

### Current Schema

```cypher
// Components
(:Component {
  id: string,
  name: string,
  type: "motor" | "fc" | "esc" | "battery",
  weight_g: float,
  ...type-specific properties
})

// Mount patterns (reusable)
(:MountPattern {
  id: string,
  type: "square" | "circular",
  spacing_mm: float,
  hole_diameter_mm: float,
  hole_count: int
})

// Relationships
(:Component)-[:HAS_MOUNT]->(:MountPattern)
```

### Data Currently Stored

| Type | Count | Examples |
|------|-------|----------|
| Motors | 4 | 2207, 2306, 1404, 0802 |
| Flight Controllers | 2 | F405, F722 |
| ESCs | 2 | 45A, 35A 4-in-1 |
| Mount Patterns | 5 | 30.5mm, 20mm, 16mm, 12mm, 9mm |

---

## 5. Scaling to Big Projects

### Challenge: Persistence Across Sessions

Claude Code sessions are ephemeral. How do we maintain context for large, long-running CAD projects?

### Solution: Neo4j as Project Memory

#### 5.1 Extended Schema for Projects

```cypher
// Project container
(:Project {
  id: string,
  name: string,
  description: string,
  created_at: datetime,
  status: "active" | "archived"
})

// Design iterations
(:Design {
  id: string,
  version: string,
  parameters: json,  // All parametric values
  created_at: datetime,
  notes: string
})

// Design decisions (WHY something was done)
(:Decision {
  id: string,
  question: string,
  choice: string,
  reasoning: string,
  alternatives_considered: [string],
  created_at: datetime
})

// File references
(:CADFile {
  id: string,
  path: string,
  format: "step" | "stl" | "py",
  hash: string,
  created_at: datetime
})

// Relationships
(:Project)-[:CONTAINS]->(:Design)
(:Design)-[:USES_COMPONENT]->(:Component)
(:Design)-[:DECIDED_BY]->(:Decision)
(:Design)-[:EXPORTED_AS]->(:CADFile)
(:Design)-[:DERIVED_FROM]->(:Design)  // Version history
```

#### 5.2 Session Continuity Pattern

**At session start:**
```cypher
// Load project context
MATCH (p:Project {name: "quadcopter-v1"})-[:CONTAINS]->(d:Design)
WHERE d.status = "current"
RETURN p, d,
       [(d)-[:USES_COMPONENT]->(c) | c] as components,
       [(d)-[:DECIDED_BY]->(dec) | dec] as decisions
```

**During session:**
```cypher
// Record design decision
CREATE (dec:Decision {
  id: randomUUID(),
  question: "What motor mount pattern to use?",
  choice: "16mm square pattern",
  reasoning: "Standard for 22xx motors, M3 hardware",
  alternatives_considered: ["12mm for 14xx", "19mm for 23xx"],
  created_at: datetime()
})

// Link to current design
MATCH (d:Design {id: $current_design_id})
CREATE (d)-[:DECIDED_BY]->(dec)
```

**At session end:**
```cypher
// Snapshot current state
MATCH (d:Design {id: $current_design_id})
SET d.last_modified = datetime(),
    d.session_notes = $notes
```

#### 5.3 Component Library Growth

```cypher
// Add new component with source
CREATE (c:Component {
  id: "motor-t-motor-f60-2207",
  name: "T-Motor F60 Pro IV 2207",
  type: "motor",
  weight_g: 34.5,
  kv: 1750,
  source: "datasheet",
  source_url: "https://...",
  verified: true
})

// Link to existing mount pattern
MATCH (p:MountPattern {id: "motor-2207"})
CREATE (c)-[:HAS_MOUNT]->(p)
```

#### 5.4 Design Rules Storage

```cypher
// Store learned constraints
CREATE (r:DesignRule {
  id: "prop-clearance-min",
  rule: "Minimum 5mm between prop tips",
  formula: "wheelbase > prop_diameter * 1.41 + 10",
  source: "empirical",
  category: "safety"
})

// Query rules when designing
MATCH (r:DesignRule)
WHERE r.category IN ["safety", "structural"]
RETURN r.rule, r.formula
```

### 5.5 Multi-Session Workflow

```
Session 1: Research & Component Selection
├── Store components in Neo4j
├── Record selection decisions
└── Export: component_selection.md

Session 2: Frame Design
├── Load components from Neo4j
├── Generate frame geometry
├── Store design parameters
└── Export: frame_v1.step

Session 3: Iteration
├── Load previous design
├── Query: "Why was 220mm wheelbase chosen?"
├── Modify parameters
├── Store as new version
└── Export: frame_v2.step

Session 4: Manufacturing Prep
├── Load final design
├── Generate manufacturing files
├── Store export history
└── Export: frame_final.stl, .gcode
```

---

## 6. Lessons Learned

### What Worked

| Practice | Benefit |
|----------|---------|
| Component-first design | Natural workflow, correct clearances |
| Neo4j for component specs | Queryable, persistent, relational |
| CadQuery for parametric | Full control, Python ecosystem |
| cq-editor for visualization | Interactive, immediate feedback |
| Standalone scripts | No import issues in cq-editor |

### What Didn't Work

| Issue | Resolution |
|-------|------------|
| Frame-first design | Pivot to component-first |
| Onshape MCP limitations | Use CadQuery instead |
| SVG viewer issues | Use PNG via trimesh |
| Module imports in cq-editor | Standalone scripts |

### Key Principles Established

1. **Model what exists, design what's needed**
   - Components are constraints, frame is solution

2. **Persist decisions, not just geometry**
   - Future sessions need to know WHY

3. **Parametric over hardcoded**
   - Change wheelbase → everything updates

4. **Visualize early and often**
   - cq-editor catches issues before export

5. **Export multiple formats**
   - STEP for CAD, STL for printing, PNG for review

---

## 7. Next Steps

### Immediate

- [ ] Store current design in Neo4j with all parameters
- [ ] Add more components to library (cameras, VTX, receivers)
- [ ] Create 3-inch and 7-inch frame variants

### Short-term

- [ ] Implement design version history in Neo4j
- [ ] Add design rule validation (prop clearance, etc.)
- [ ] Create component search/recommendation queries

### Medium-term

- [ ] Integrate with Onshape for collaboration/CAM
- [ ] Add FEA simulation for stress analysis
- [ ] Create web viewer for design sharing

---

## 8. File Reference

### Scripts

| File | Purpose |
|------|---------|
| `scripts/components.py` | Parametric component library |
| `scripts/quadcopter_assembly.py` | Full assembly with imports |
| `scripts/view_assembly.py` | Standalone cq-editor visualization |
| `scripts/quadcopter_frame.py` | Simple frame generator |
| `scripts/export_views.py` | PNG/SVG/STL export utilities |

### Output

| File | Format | Purpose |
|------|--------|---------|
| `output/quad_frame_assembly.step` | STEP | CAD import |
| `output/quad_frame_assembly.stl` | STL | 3D printing |
| `output/quad_frame_render.png` | PNG | Preview |
| `output/components/*.stl` | STL | Individual parts |

### Reports

| File | Content |
|------|---------|
| `mcp-research-20260131.md` | Full MCP ecosystem research |
| `mvp-decision-cadquery-20260131.md` | Stack decision rationale |
| `project-retrospective-20260131.md` | This document |

---

## 9. Commands Quick Reference

```bash
# Visualize assembly
cq-editor scripts/view_assembly.py

# Generate frame
python scripts/quadcopter_assembly.py

# Render PNG
python -c "
from scripts.export_views import stl_to_png_trimesh
stl_to_png_trimesh('output/quad_frame_assembly.stl', 'output/render.png')
"

# Query Neo4j for components
# (in Claude Code session)
MATCH (c:Component)-[:HAS_MOUNT]->(m:MountPattern)
RETURN c.name, m.spacing_mm
```

---

*Report generated by Claude Code for semi-autocad project*
*Retrospective covering 2026-01-31 development session*
