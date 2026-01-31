# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**semi-autocad** - A system for semi-automatic CAD operations using Claude Code as orchestrator, CadQuery for parametric modeling, and Neo4j for persistent memory/knowledge graph.

**Current MVP:** Quadcopter frame design with parametric mount holes.

## Architecture

```
Claude Code (Orchestrator)
    │
    ├── MCP Servers
    │   ├── cadquery - Parametric CAD engine (primary)
    │   ├── neo4j-memory-semicad (bolt://localhost:7688) - Component library
    │   ├── neo4j-cypher-semicad - Direct Cypher queries
    │   ├── sequential-thinking - Complex design reasoning
    │   └── playwright - Browser automation (Onshape fallback)
    │
    ├── Local Tools
    │   └── cq-editor - 3D visualization GUI
    │
    └── Future: Onshape Integration
        ├── Import STEP for CAM/manufacturing
        ├── Collaboration & sharing
        └── Professional drawings
```

## MCP Configuration

Project uses local `.claude/settings.json`:

| MCP Server | Purpose | Status |
|------------|---------|--------|
| cadquery | Parametric CAD modeling | To configure |
| neo4j-memory-semicad | Component knowledge graph | Configured |
| neo4j-cypher-semicad | Direct Cypher queries | Configured |
| sequential-thinking | Design reasoning | Configured |
| playwright | Browser automation | Configured |

### Neo4j Instance
- **Container**: `neo4j-semicad`
- **Bolt**: `bolt://localhost:7688`
- **Browser**: `http://localhost:7475`
- **Credentials**: `neo4j` / `semicad2026`

## Project Structure

```
/home/user/cad/
├── scripts/           # CadQuery parametric scripts
├── output/            # Generated STEP/STL files
├── components/        # Component definitions
├── .reports/          # Research and decision reports
└── .claude/           # MCP configuration
```

## Workflow

1. **Define components** in Neo4j (motors, FC, ESC with mount patterns)
2. **Query requirements** via neo4j-memory-semicad
3. **Generate geometry** via CadQuery MCP
4. **Visualize** in cq-editor
5. **Export** STEP/STL for manufacturing
6. **Store successful designs** back to Neo4j

## Key Commands

```bash
# Launch visualization
cq-editor

# Run CadQuery script
python scripts/quadcopter_frame.py

# View Neo4j
open http://localhost:7475
```

## Component Library (Neo4j)

Standard patterns stored in knowledge graph:
- FC mount: 30.5mm, 20mm square patterns
- Motor mounts: Various circular patterns (12mm, 16mm, 19mm)
- Hardware: M2, M3 clearance holes

Query example:
```cypher
MATCH (m:Component {type: "motor"})-[:HAS_MOUNT]->(p:MountPattern)
WHERE m.name CONTAINS "2207"
RETURN m.name, p.spacing_mm, p.hole_diameter_mm
```

## Reports

- `.reports/mcp-research-20260131.md` - Full MCP ecosystem research
- `.reports/mvp-decision-cadquery-20260131.md` - Stack decision rationale

## External Resources

- CadQuery Docs: https://cadquery.readthedocs.io/
- cq-editor: https://github.com/CadQuery/CQ-editor
- Onshape API (future): https://onshape-public.github.io/docs/
