# MCP & Plugin Configuration Research for Onshape CAD Integration

**Date:** 2026-01-31 (Updated)
**Project:** semi-autocad
**Objective:** Identify optimal MCP servers, Claude Code plugins, and skills for seamless Onshape CAD integration

---

## 1. Executive Summary

This comprehensive research identified **2 dedicated Onshape MCP servers**, **15+ CAD-specific MCP servers**, **7,400+ Claude Code skills**, and numerous hidden gems for CAD automation. The research spans MCP servers, skills/plugins, Onshape App Store, workflow automation, file format tools, and adjacent domain integrations.

### Recommended Stack

| Component | Recommended Solution | Status |
|-----------|---------------------|--------|
| **Onshape MCP** | [hedless/onshape-mcp](https://github.com/hedless/onshape-mcp) | Ready to use |
| **Parametric CAD** | [CadQuery MCP](https://github.com/rishigundakaram/cadquery-mcp-server) | Ready to use |
| **Knowledge Graph** | neo4j-memory-semicad | Already configured |
| **Browser Automation** | playwright | Already configured |
| **3D Visualization** | [Blender MCP](https://github.com/ahujasid/blender-mcp) | Optional |
| **Game Engine** | [Unity MCP](https://github.com/CoderGamester/mcp-unity) | Optional |
| **Electronics** | [KiCad MCP](https://github.com/mixelpixx/KiCAD-MCP-Server) | Optional |
| **FEA Simulation** | [FEA-MCP](https://mcp.so/server/FEA-MCP/GreatApo) | Optional |

### Key Finding

**Critical Gap:** No dedicated CAD/engineering skills exist in major skill registries (VoltAgent 172+ skills, Anthropic official, awesome-claude-code). Custom skill development is required for CAD-specific workflows.

---

## 2. MCP Servers Found

### 2.1 Onshape-Specific MCP Servers

#### Primary Recommendation: hedless/onshape-mcp

| Attribute | Details |
|-----------|---------|
| **GitHub** | [github.com/hedless/onshape-mcp](https://github.com/hedless/onshape-mcp) |
| **Language** | Python 3.10+ |
| **Tools** | 13 comprehensive tools |
| **Tests** | 93 unit tests |
| **License** | MIT |

**Available Tools:**
- `list_documents` - Filter by type (all, owned, created, shared)
- `search_documents` - Query-based document search
- `get_document` - Retrieve detailed document information
- `get_document_summary` - Comprehensive overview
- `find_part_studios` - Locate Part Studios
- `get_elements` - Retrieve workspace elements by type
- `get_parts` - Extract parts from Part Studio
- `get_assembly` - Access assembly structure
- `create_sketch_rectangle` - Parametric rectangles on standard planes
- `create_extrude` - Generate extrude features
- `get_variables` - Access variable tables
- `set_variable` - Update/create parametric variables
- `get_features` - List all Part Studio features

**Installation:**
```bash
git clone https://github.com/hedless/onshape-mcp.git
cd onshape-mcp
python -m venv venv
source venv/bin/activate
pip install -e .

export ONSHAPE_ACCESS_KEY="your_key"
export ONSHAPE_SECRET_KEY="your_key"
```

**Claude Code Configuration:**
```json
{
  "mcpServers": {
    "onshape": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "onshape_mcp"],
      "env": {
        "ONSHAPE_ACCESS_KEY": "your_key",
        "ONSHAPE_SECRET_KEY": "your_key"
      }
    }
  }
}
```

#### Alternative: BLamy/onshape-mcp

| Attribute | Details |
|-----------|---------|
| **GitHub** | [github.com/BLamy/onshape-mcp](https://github.com/BLamy/onshape-mcp) |
| **Language** | TypeScript |
| **Status** | Early stage (11 stars) |
| **Install** | `npm install onshape-mcp-server` |

### 2.2 General CAD MCP Servers

Based on [Snyk's analysis](https://snyk.io/articles/9-mcp-servers-for-computer-aided-drafting-cad-with-ai/):

| Server | Platform | Stars | Key Feature | GitHub |
|--------|----------|-------|-------------|--------|
| **CAD-MCP** | AutoCAD, GstarCAD, ZWCAD | 98 | Universal translator | [daobataotie/CAD-MCP](https://github.com/daobataotie/CAD-MCP) |
| **Easy-MCP-AutoCad** | AutoCAD | 64 | SQLite database integration | [zh19980811/Easy-MCP-AutoCad](https://github.com/zh19980811/Easy-MCP-AutoCad) |
| **autocad-mcp** | AutoCAD | 59 | P&ID + ISA 5.1 symbols | [puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp) |
| **fusion360-mcp-server** | Fusion 360 | 26 | Comprehensive 3D modeling | [ArchimedesCrypto/fusion360-mcp-server](https://github.com/ArchimedesCrypto/fusion360-mcp-server) |
| **freecad-mcp** | FreeCAD | 165 | Parts library access | [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) |
| **freecad_mcp** | FreeCAD | 68 | Direct script execution | [bonninr/freecad_mcp](https://github.com/bonninr/freecad_mcp) |
| **mcp-server-solidworks** | SolidWorks | 14 | Intelligent LLM bridging | [eyfel/mcp-server-solidworks](https://github.com/eyfel/mcp-server-solidworks) |
| **multiCAD-mcp** | Multiple CAD | - | COM-based architecture | [AnCode666/multiCAD-mcp](https://github.com/AnCode666/multiCAD-mcp) |

### 2.3 Game Engine MCP Servers (Visualization)

#### Unity MCP (38 Tools)

| Attribute | Details |
|-----------|---------|
| **GitHub** | [CoderGamester/mcp-unity](https://github.com/CoderGamester/mcp-unity) |
| **Stars** | High activity |
| **Features** | Asset creation, scene control, ProBuilder, build automation |
| **Academic** | Published in SA Technical Communications '25 |

**Tools include:** `execute_menu_item`, `select_gameobject`, `update_gameobject`, `update_component`, script generation, material creation, shader updates.

**Use Cases:**
- XR/AR/VR visualization of CAD models
- Real-time design iteration
- Interactive prototyping

#### Unreal Engine MCP

| Attribute | Details |
|-----------|---------|
| **GitHub** | [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp) |
| **Features** | Actor creation, Blueprint classes, Remote Control API |
| **CAD Import** | Via [Datasmith](https://www.unrealengine.com/en-US/datasmith) plugins |

### 2.4 Electronics/PCB MCP Server (KiCad)

| Attribute | Details |
|-----------|---------|
| **GitHub** | [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) |
| **Tools** | 64 tools (12 direct + 47 routed in 7 categories) |
| **Features** | JLCPCB API integration (100k+ parts), BOM management, DRC |

**Categories:** board, component, export, drc, schematic, library, routing

**Why it matters for semi-autocad:** Mechanical-electrical integration for enclosures, mounting, and thermal management.

### 2.5 FEA/Simulation MCP Servers

| Server | Platform | Key Feature |
|--------|----------|-------------|
| **FEA-MCP** | LUSAS, ETABS | Unified API for FEA software |
| **Abaqus MCP** | Abaqus/CAE | GUI automation, Python scripts |

Reference: [FEA-MCP Server](https://mcp.so/server/FEA-MCP/GreatApo)

### 2.6 BIM/Architecture MCP Servers

| Server | Platform | Use Case |
|--------|----------|----------|
| **revit-mcp** | Autodesk Revit | BIM modeling, cost estimation |
| **archicad-mcp** | ArchiCAD | Architectural design |
| **openbim-mcp** | IFC files | Building data extraction |
| **bonsai-blender-ifc** | Blender+IFC | Open BIM workflows |

### 2.7 Parametric CAD MCP Servers

#### CadQuery MCP Server

| Attribute | Details |
|-----------|---------|
| **GitHub** | [rishigundakaram/cadquery-mcp-server](https://github.com/rishigundakaram/cadquery-mcp-server) |
| **Engine** | OpenCASCADE (OCCT) |
| **Export** | STL, STEP, SVG |

**Alternative:** [bertvanbrakel/mcp-cadquery](https://github.com/bertvanbrakel/mcp-cadquery) - HTTP/SSE mode with web frontend

---

## 3. Claude Code Skills & Plugins (Expanded)

### 3.1 Skill Registry Overview

| Registry | Total Skills | CAD/Engineering Skills | Link |
|----------|-------------|----------------------|------|
| **claude-plugins.dev** | 7,453+ | None dedicated | [claude-plugins.dev](https://claude-plugins.dev/) |
| **VoltAgent/awesome-agent-skills** | 172+ | CloudAI-X/threejs-skills only | [GitHub](https://github.com/VoltAgent/awesome-agent-skills) |
| **Anthropic Official** | 50+ | None | [github.com/anthropics/skills](https://github.com/anthropics/skills) |
| **awesome-skills.com** | 70+ | None dedicated | [awesome-skills.com](https://awesome-skills.com/) |

**Critical Finding:** No dedicated CAD/engineering/3D modeling skills exist in major registries. This represents a significant gap and opportunity.

### 3.2 CAD-Adjacent Skills Found

| Skill | Description | Source |
|-------|-------------|--------|
| **CAD Model Compare** | 3D model evaluation via boolean operations, GLB visualization | [mcpmarket.com](https://mcpmarket.com/tools/skills/cad-model-compare) |
| **build123d CAD Modeling** | Python CAD design capabilities | [mcpmarket.com](https://mcpmarket.com/tools/skills/build123d-cad-modeling) |
| **Three.js Skills** | 3D elements and interactive experiences | CloudAI-X/threejs-skills |
| **Calculator MCP** | Advanced math, derivatives, integrals, matrix operations | [mcpmarket.com](https://mcpmarket.com/server/calculator-3) |

### 3.3 Engineering-Adjacent Skills

| Skill/Plugin | Description | Source |
|--------------|-------------|--------|
| **cc-devops-skills** | IaC code generation, validation | [akin-ozer](https://github.com/akin-ozer) |
| **claude-skills-engineering** | DevOps, testing, git workflows | [djacobsmeyer](https://github.com/djacobsmeyer/claude-skills-engineering) |
| **Trail of Bits Security** | 20+ security skills (code analysis) | VoltAgent registry |
| **obra/superpowers** | 20+ skills: TDD, debugging, collaboration | [obra/superpowers](https://github.com/obra/superpowers) |

### 3.4 Major Skill Registries Explored

#### Official Anthropic Skills Categories
- Document creation (docx, pdf, pptx, xlsx)
- Creative/design (algorithmic-art, canvas-design)
- Branding (brand-guidelines, internal-comms)
- Meta (skill-creator)

#### VoltAgent Official Skills
- Vercel: React, deployment, React Native
- Cloudflare: Workers, AI agents, MCP servers
- Supabase: PostgreSQL best practices
- Google Labs: Design management
- Hugging Face: ML workflows, model training
- Stripe: Integration, SDK upgrades
- Expo: App design, deployment
- Sentry: Code review, bug identification

### 3.5 Awesome Lists for Claude Code

| List | Focus | Link |
|------|-------|------|
| **hesreallyhim/awesome-claude-code** | Skills, hooks, slash-commands, plugins | [GitHub](https://github.com/hesreallyhim/awesome-claude-code) |
| **travisvn/awesome-claude-skills** | Skills and workflows | [GitHub](https://github.com/travisvn/awesome-claude-skills) |
| **jqueryscript/awesome-claude-code** | Tools, integrations, frameworks | [GitHub](https://github.com/jqueryscript/awesome-claude-code) |
| **ccplugins/awesome-claude-code-plugins** | Slash commands, subagents, hooks | [GitHub](https://github.com/ccplugins/awesome-claude-code-plugins) |
| **ComposioHQ/awesome-claude-skills** | Practical skills, Skill Seekers tool | [GitHub](https://github.com/ComposioHQ/awesome-claude-skills) |

### 3.6 Custom Skill Development Resources

| Resource | Description | Link |
|----------|-------------|------|
| **Claude Code Skill Factory** | Production-ready skill toolkit | [alirezarezvani/claude-code-skill-factory](https://github.com/alirezarezvani/claude-code-skill-factory) |
| **Skill Structure Docs** | Official skill creation guide | [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) |
| **Skill Seekers** | Auto-convert docs to skills | ComposioHQ |

**Skill Structure:**
```
skill-name/
├── SKILL.md          # YAML frontmatter + instructions
├── scripts/          # Optional executable code
├── templates/        # Optional templates
└── resources/        # Optional assets
```

### 3.7 Plugin System Architecture

**Plugin Structure:**
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json       # Plugin metadata
├── commands/             # Slash commands
├── agents/               # Specialized agents
├── skills/               # Agent Skills
├── hooks/                # Event handlers
├── .mcp.json             # External tool configuration
└── README.md             # Documentation
```

**LSP Integration:** Plugins can provide Language Server Protocol servers for real-time code intelligence.

---

## 4. Onshape App Store Ecosystem (NEW)

### 4.1 Key Apps for Automation

| App | Category | Key Feature |
|-----|----------|-------------|
| **CAM Studio** | Manufacturing | Native 5-axis milling, G-code generation (Jan 2025) |
| **Intact** | Simulation | Structural, thermal, modal analysis |
| **Simscape Multibody** | Simulation | MathWorks integration, Simulink |
| **Render Studio Advanced** | Visualization | Volumes, photorealistic rendering |
| **Cadasio** | Documentation | Interactive technical docs, auto-sync |
| **Swift Calcs** | Engineering | Calculation platform driving Onshape variables |
| **ESPRIT** | CAM | Wire-EDM, 5-axis features |
| **OnCreate3D** | CAM | Full-cloud CAM |

### 4.2 Onshape AI Advisor (October 2025)

| Feature | Description |
|---------|-------------|
| **Natural Language** | Ask design questions conversationally |
| **Context-Aware** | Understands current design state |
| **Powered By** | Amazon Bedrock |
| **Access** | Embedded directly in design workspace |

**Roadmap:**
- FeatureScript Optimization (AI suggestions)
- AI Quick Render (natural language → renderings)
- AI Agents (automated routine tasks)
- Generative AI for geometry creation

Reference: [Onshape AI Advisor](https://www.onshape.com/en/features/ai-advisor)

### 4.3 2025 Onshape Updates

17 updates released in 2025, top features:
- CAM Studio
- Assembly Mirror
- AI Advisor
- Query Variables
- Configurable Variable Studios

---

## 5. FeatureScript Development Tools (NEW)

### 5.1 Built-in IDE Features

| Feature | Description |
|---------|-------------|
| **Feature Studio** | Integrated IDE within Onshape |
| **Code Snippets** | Auto-completion |
| **Inline Docs** | Hover documentation |
| **Monitoring** | Real-time Part Studio monitoring |
| **Profiling** | Performance timing per code line |

### 5.2 Debugging Tools

| Tool | Purpose |
|------|---------|
| `print`, `println`, `printTimer` | Console output |
| `debug` | Highlight entities in graphics |
| Static Analysis | Parse errors, semantic warnings |
| Runtime Exceptions | Division by zero, undefined refs |
| Profiler | Timing data (>0.1ms resolution) |

### 5.3 FeatureScript Resources

| Resource | Link |
|----------|------|
| **Official Docs** | [cad.onshape.com/FsDoc/](https://cad.onshape.com/FsDoc/) |
| **Debugging Guide** | [cad.onshape.com/FsDoc/debugging-in-feature-studios.html](https://cad.onshape.com/FsDoc/debugging-in-feature-studios.html) |
| **CADSharp Tutorials** | [cadsharp.com/onshape-featurescript-video-tutorials](https://www.cadsharp.com/onshape-featurescript-video-tutorials/) |
| **dcowden/featurescript** | Curated list on [GitHub](https://github.com/dcowden/featurescript) |
| **FRCDesign.org** | [frcdesign.org/resources/featurescripts](https://www.frcdesign.org/resources/featurescripts/) |

---

## 6. Workflow Automation (NEW)

### 6.1 n8n Integration

n8n can connect to Onshape via HTTP Request node to REST API.

**Key Onshape Webhook Events:**
- `onshape.revision.created`
- `onshape.model.lifecycle.createversion`
- `onshape.model.translation.complete`
- `onshape.workflow.transition`

**Use Cases:**
- Sync released designs to PLM/ERP
- Auto-export on version save
- Notification on workflow transitions

### 6.2 GitHub Actions for CAD

**Potential Workflows:**
1. STEP file validation on PR
2. STL mesh quality checks
3. Design rule verification
4. Auto-documentation generation

**Tools to Integrate:**
- PythonOCC for STEP validation
- PyMeshLab for STL checks
- NIST STEP File Analyzer

### 6.3 Onshape Webhook Integration

| Event | Use Case |
|-------|----------|
| Release created | Auto-export STEP/PDF |
| Version saved | Backup to cloud storage |
| Translation complete | Trigger downstream processes |

Reference: [Onshape Webhooks](https://onshape-public.github.io/docs/app-dev/webhook/)

---

## 7. File Format Tools (NEW)

### 7.1 STEP File Tools

| Tool | Type | Key Feature |
|------|------|-------------|
| **NIST STEP Analyzer** | Validator | PMI analysis, format errors |
| **PythonOCC** | Python library | Full OCCT bindings |
| **steputils** | Python library | STEP DOM manipulation |
| **python-step-parser** | Python library | SQLite normalization |
| **Open STEP Viewer** | Viewer | BRep analysis |

### 7.2 STL Mesh Repair

| Tool | Type | Key Feature |
|------|------|-------------|
| **PyMeshLab** | Python library | MeshLab filters via pybind11 |
| **PyMeshFix** | Python library | Hole repair |
| **MeshLib SDK** | SDK | 1-click repair, commercial |
| **FreeCAD Mesh Module** | GUI/Python | Evaluate & Repair |

### 7.3 CAD Version Control & Diff

| Tool | Focus | Key Feature |
|------|-------|-------------|
| **Onshape (native)** | Cloud CAD | Git-style branching/merging |
| **Zoo Diff Viewer** | GitHub | Chrome extension, 3D diff |
| **Anchorpoint** | Desktop | Git LFS, thumbnails |
| **Thangs Sync** | Cloud | 30+ format support |
| **CADLAB.io** | PCB | Git for hardware |

---

## 8. Adjacent Domain MCPs (NEW)

### 8.1 Open Source PLM Integration

| PLM | Language | Key Feature | Link |
|-----|----------|-------------|------|
| **OdooPLM** | Python | Odoo integration, CAD upload | [SourceForge](https://sourceforge.net/projects/openerpplm/) |
| **DocDokuPLM** | Java | Cloud-native, Kubernetes | [GitHub](https://github.com/docdoku/docdoku-plm) |
| **Dokuly** | Python | Fast, easy setup | [GitHub](https://github.com/Dokuly-PLM/dokuly) |
| **nanoPLM** | Python | FreeCAD native | [GitHub](https://github.com/alekssadowski95/nanoPLM) |
| **InvenTree** | Python | Part/BOM management, API | [inventree.org](https://inventree.org/) |

### 8.2 Robotics/Simulation Pipeline

| Tool | Purpose | Link |
|------|---------|------|
| **onshape-to-robot** | URDF/SDF/MuJoCo export | [Rhoban](https://github.com/Rhoban/onshape-to-robot) |
| **onshape-robotics-toolkit** | URDF + visualization | [neurobionics](https://github.com/neurobionics/onshape-robotics-toolkit) |
| **ExportURDF** | Unified CAD→URDF | [david-dorf](https://github.com/david-dorf/ExportURDF) |

### 8.3 Computational Geometry Libraries

| Library | Language | Kernel | Link |
|---------|----------|--------|------|
| **PythonOCC** | Python | OCCT | [dev.opencascade.org](https://dev.opencascade.org/project/pythonocc) |
| **pyOCCT** | Python | OCCT 7+ | [GitHub](https://github.com/trelau/pyOCCT) |
| **CadQuery** | Python | OCCT | [GitHub](https://github.com/CadQuery/cadquery) |
| **build123d** | Python | OCCT | [build123d.readthedocs.io](https://build123d.readthedocs.io/) |
| **TiGL** | C++/Python | OCCT | [dlr-sc.github.io/tigl](https://dlr-sc.github.io/tigl/) |
| **libfive** | C/C++ | Custom | [libfive.com](https://libfive.com/) |

---

## 9. Hidden Gems Section (Expanded)

### 9.1 Zoo/KittyCAD Text-to-CAD (Game-Changer)

| Attribute | Details |
|-----------|---------|
| **Website** | [zoo.dev/text-to-cad](https://zoo.dev/text-to-cad) |
| **Key Innovation** | Generates **B-Rep surfaces** (not meshes!) |
| **Export** | STL, PLY, OBJ, STEP, GLTF, GLB, FBX |
| **KCL Language** | Human-readable CAD code, version control friendly |

### 9.2 MecAgent - AI CAD Copilot

| Attribute | Details |
|-----------|---------|
| **Website** | [mecagent.com](https://mecagent.com/) |
| **Platforms** | SolidWorks, CATIA, Inventor, Fusion 360, Creo |
| **Funding** | $3M raised |
| **Feature** | Contextual part generation from assembly context |

### 9.3 Adam AI - AI-Powered CAD Agent

| Attribute | Details |
|-----------|---------|
| **Website** | [adam.new](https://adam.new/) |
| **Launch** | January 24, 2025 |
| **Funding** | $4.1M seed |

### 9.4 MIT VideoCAD Dataset

41,000+ examples of CAD modeling from videos. AI learns to operate CAD software like humans.

Reference: [MIT News](https://news.mit.edu/2025/new-ai-agent-learns-use-cad-create-3d-objects-sketches-1119)

### 9.5 FlowsCad - Visual Feedback Loop

| Attribute | Details |
|-----------|---------|
| **GitHub** | [dexmac221/FlowsCad](https://github.com/dexmac221/FlowsCad) |
| **Innovation** | Render-analyze-refine autonomous design cycles |

### 9.6 OpenSCAD Studio

| Attribute | Details |
|-----------|---------|
| **GitHub** | [zacharyfmarion/openscad-studio](https://github.com/zacharyfmarion/openscad-studio) |
| **Features** | AI copilot, live 3D preview, SVG mode |

### 9.7 Undocumented FeatureScript Functions

| Function | Description |
|----------|-------------|
| `opExtendSheetBody` | Extend sheet bodies |
| `opEdgeChange` | Negative offset sheet edges |
| `getRemainderPatternTransform` | Enable feature pattern selection |

### 9.8 Siemens NX Python Automation

NX Open API supports Python (NX 10+) with 90% design time reduction reported.

Reference: [dennisklappe.nl](https://dennisklappe.nl/academic-work/nxopen-python-automation)

### 9.9 International CAD Tools

| Tool | Origin | Key Feature |
|------|--------|-------------|
| **ZWCAD** | China | VBA, ZRX, LISP APIs |
| **GstarCAD** | China | AutoCAD compatible |
| **ActCAD** | India | Multi-language (German, Japanese) |
| **WSCAD ELECTRIX** | Germany | Electrical CAD, AR support |

---

## 10. Gaps & Custom Development Needed (Updated)

### 10.1 Critical Gaps Identified

| Gap | Impact | Priority |
|-----|--------|----------|
| **No CAD Skills in Registries** | Must build custom skills | HIGH |
| **No FeatureScript Generation MCP** | Cannot create custom features via Claude | HIGH |
| **No Onshape Drawing MCP** | Drawing API undocumented | MEDIUM |
| **No unified CAD skills standard** | Fragmented ecosystem | MEDIUM |
| **No real-time collaborative MCP** | Use Playwright as fallback | LOW |

### 10.2 Recommended Custom Development

#### 1. Onshape Skills Package (Priority: HIGH)
Create custom skills for:
- Sketch operations (constraints, dimensions)
- Feature creation (extrude, revolve, fillet)
- Assembly operations (mates, patterns)
- Drawing generation
- FeatureScript code generation

#### 2. FeatureScript MCP Server (Priority: HIGH)
- Input: Natural language description
- Output: FeatureScript code
- Validation: Syntax checking before deployment

#### 3. Design Decision Logger (Priority: MEDIUM)
- Capture Claude's reasoning during design
- Store in Neo4j with relationships
- Enable "why was this designed this way?" queries

#### 4. Webhook Integration Server (Priority: MEDIUM)
- Listen to Onshape events (release, version, translation)
- Trigger Claude Code workflows
- Auto-export on release

#### 5. Visual Feedback Loop Integration (Priority: LOW)
- Playwright screenshots of Onshape viewport
- Claude analyzes and suggests improvements
- Iterative design refinement

---

## 11. Recommended Configurations

### 11.1 Minimal Configuration

```json
{
  "mcpServers": {
    "onshape": {
      "command": "python",
      "args": ["-m", "onshape_mcp"],
      "env": {
        "ONSHAPE_ACCESS_KEY": "${ONSHAPE_ACCESS_KEY}",
        "ONSHAPE_SECRET_KEY": "${ONSHAPE_SECRET_KEY}"
      }
    },
    "neo4j-memory-semicad": { "// existing": "..." },
    "playwright": { "// existing": "..." }
  }
}
```

### 11.2 Full-Featured Configuration

```json
{
  "mcpServers": {
    "onshape": {
      "command": "python",
      "args": ["-m", "onshape_mcp"],
      "env": {
        "ONSHAPE_ACCESS_KEY": "${ONSHAPE_ACCESS_KEY}",
        "ONSHAPE_SECRET_KEY": "${ONSHAPE_SECRET_KEY}"
      }
    },
    "cadquery": {
      "command": "python",
      "args": ["-m", "cadquery_mcp"]
    },
    "blender": {
      "command": "python",
      "args": ["-m", "blender_mcp"]
    },
    "openscad": {
      "command": "python",
      "args": ["src/main.py"]
    },
    "unity": {
      "command": "node",
      "args": ["path/to/mcp-unity/build/index.js"]
    },
    "kicad": {
      "command": "python",
      "args": ["-m", "kicad_mcp"]
    },
    "neo4j-memory-semicad": { "// existing": "..." },
    "neo4j-cypher-semicad": { "// existing": "..." },
    "playwright": { "// existing": "..." },
    "sequential-thinking": { "// existing": "..." }
  }
}
```

### 11.3 Custom Skills Directory Structure

```
.claude/skills/
├── onshape-sketch/
│   └── SKILL.md
├── onshape-features/
│   └── SKILL.md
├── onshape-assembly/
│   └── SKILL.md
├── featurescript-generator/
│   ├── SKILL.md
│   └── scripts/
│       └── validate.py
└── cad-design-patterns/
    └── SKILL.md
```

---

## 12. Next Steps

### Immediate (This Week)

1. **Install hedless/onshape-mcp**
2. **Generate Onshape API Keys** at [dev-portal.onshape.com](https://dev-portal.onshape.com/)
3. **Test basic workflow:** list documents → create sketch → extrude
4. **Create first custom skill:** onshape-sketch operations

### Short-term (Next 2 Weeks)

1. **Evaluate Zoo Text-to-CAD** - Test B-Rep generation quality
2. **Integrate CadQuery MCP** - Local prototyping pipeline
3. **Design Knowledge Graph Schema** - Parts, decisions, constraints
4. **Build FeatureScript skill** - Code generation + validation

### Medium-term (Next Month)

1. **Build complete Onshape skills package**
2. **Implement webhook automation**
3. **Create visual feedback loop with Playwright**
4. **Evaluate Unity MCP for visualization**

---

## 13. References

### Official Documentation
- [Onshape API Docs](https://onshape-public.github.io/docs/)
- [Onshape Developer Portal](https://dev-portal.onshape.com/)
- [FeatureScript Docs](https://cad.onshape.com/FsDoc/)
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)

### GitHub Repositories - MCP Servers
- [hedless/onshape-mcp](https://github.com/hedless/onshape-mcp)
- [BLamy/onshape-mcp](https://github.com/BLamy/onshape-mcp)
- [rishigundakaram/cadquery-mcp-server](https://github.com/rishigundakaram/cadquery-mcp-server)
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)
- [CoderGamester/mcp-unity](https://github.com/CoderGamester/mcp-unity)
- [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server)
- [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp)

### GitHub Repositories - Skills & Plugins
- [anthropics/skills](https://github.com/anthropics/skills)
- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)
- [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)
- [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills)
- [alirezarezvani/claude-code-skill-factory](https://github.com/alirezarezvani/claude-code-skill-factory)

### GitHub Repositories - CAD Tools
- [CodeToCAD/CodeToCAD](https://github.com/CodeToCAD/CodeToCAD)
- [kyle-tennison/onpy](https://github.com/kyle-tennison/onpy)
- [neurobionics/onshape-robotics-toolkit](https://github.com/neurobionics/onshape-robotics-toolkit)
- [dcowden/featurescript](https://github.com/dcowden/featurescript)
- [KittyCAD](https://github.com/kittycad)
- [CadQuery/cadquery](https://github.com/CadQuery/cadquery)

### Research Papers
- [CAD-MLLM: Multimodality-Conditioned CAD Generation](https://cad-mllm.github.io/)
- [CAD-Llama: LLMs for Parametric 3D (CVPR 2025)](https://openaccess.thecvf.com/content/CVPR2025/papers/Li_CAD-Llama_Leveraging_Large_Language_Models_for_Computer-Aided_Design_Parametric_3D_CVPR_2025_paper.pdf)
- [LLMs for CAD: A Survey (arXiv 2025)](https://arxiv.org/html/2505.08137v1)
- [MIT VideoCAD Dataset](https://news.mit.edu/2025/new-ai-agent-learns-use-cad-create-3d-objects-sketches-1119)

### Community Resources
- [Snyk: 9 MCP Servers for CAD](https://snyk.io/articles/9-mcp-servers-for-computer-aided-drafting-cad-with-ai/)
- [claude-plugins.dev](https://claude-plugins.dev/)
- [awesome-skills.com](https://awesome-skills.com/)
- [Onshape Forum](https://forum.onshape.com/)
- [Onshape AI Advisor](https://www.onshape.com/en/features/ai-advisor)

---

*Report generated by Claude Code for semi-autocad project*
*Last updated: 2026-01-31*
