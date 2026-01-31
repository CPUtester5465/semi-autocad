# CAD Task Flow Analysis

## Current Directory Issues

### Files to Remove (Redundant/Unused)
| Path | Reason |
|------|--------|
| `backups/` | Neo4j backup from unrelated project (peakfitness) |
| `supabase/` | Leftover temp folder, not used |
| `cadquery-mcp-server/` | Cloned repo, not integrated |
| `components/` | Empty directory (use scripts/components.py) |
| `templates/` | Empty directory |
| `cq-launch.sh` | Redundant with bin/dev |
| `scripts/view_assembly.py` | Self-contained duplicate of assembly_viewer.py |
| `scripts/quadcopter_frame.py` | Older version, replaced by quadcopter_assembly.py |

### Files to Keep
| Path | Purpose |
|------|---------|
| `semicad/` | Core library + CLI |
| `scripts/components.py` | Drone component library |
| `scripts/assembly_viewer.py` | Main cq-editor viewer |
| `scripts/quadcopter_assembly.py` | Build script |
| `scripts/export_views.py` | Export utilities |
| `.reports/` | Research documentation |
| `docs/` | User documentation |
| `output/` | Generated files |
| `projects/` | Sub-project directories |

---

## CAD Task Flows

### 1. Component Design Flow
**Goal:** Create a new parametric component

```
[Browse existing] → [Design params] → [Write generator] → [Test in cq-editor] → [Add to registry]
```

**CLI Implementation:**
```bash
# Browse what exists
./bin/dev lib list
./bin/dev search "motor"

# View example component
./bin/dev lib info motor_2207

# Create new component (edit scripts/components.py)
./bin/dev edit scripts/components.py

# Test in cq-editor
./bin/dev view scripts/components.py

# Export for verification
./bin/dev export my_new_component
```

**Missing Commands:**
- `./bin/dev new component <name>` - scaffold new component
- `./bin/dev validate <component>` - check geometry validity

---

### 2. Assembly Design Flow
**Goal:** Create assembly from components

```
[Select components] → [Define positions] → [Check clearances] → [Export assembly]
```

**CLI Implementation:**
```bash
# List available components
./bin/dev lib list

# Create/edit assembly script
./bin/dev edit scripts/my_assembly.py

# View in cq-editor
./bin/dev view scripts/my_assembly.py

# Build to STEP/STL
./bin/dev build

# Render preview
./bin/dev render output/assembly.stl
```

**Missing Commands:**
- `./bin/dev assembly new <name>` - scaffold assembly
- `./bin/dev assembly add <component> --pos x,y,z` - add component to assembly
- `./bin/dev clearance check` - check component interference

---

### 3. Library Browsing Flow
**Goal:** Find right component for the job

```
[Search by type] → [Filter by specs] → [View details] → [Get params] → [Use in design]
```

**CLI Implementation:**
```bash
# Search across all sources
./bin/dev search "screw M3"

# List by category
./bin/dev lib list --category fastener

# View fastener sizes
./bin/dev lib fasteners --type SocketHeadCapScrew

# Get component info
./bin/dev lib info SocketHeadCapScrew

# Use in code:
# from semicad import get_registry
# screw = get_registry().get("SocketHeadCapScrew", size="M3-0.5", length=10)
```

**Missing Commands:**
- `./bin/dev lib filter --min-size 10 --max-size 20` - filter by parameters
- `./bin/dev lib compare comp1 comp2` - compare two components

---

### 4. Export/Manufacturing Flow
**Goal:** Prepare files for manufacturing

```
[Build assembly] → [Export STEP] → [Export STL] → [Generate drawings] → [Render previews]
```

**CLI Implementation:**
```bash
# Build all
./bin/dev build

# Export specific component
./bin/dev export motor_2207 --format both

# Render to PNG
./bin/dev render output/assembly.stl --resolution 1920x1080

# (Future) Generate drawings
./bin/dev drawing generate output/assembly.step
```

**Missing Commands:**
- `./bin/dev export --all` - export all components
- `./bin/dev drawing <file>` - generate 2D drawings
- `./bin/dev bom generate` - bill of materials

---

### 5. Project Management Flow
**Goal:** Manage multiple CAD projects

```
[Create project] → [Add components] → [Build variants] → [Track versions]
```

**CLI Implementation:**
```bash
# Show current project
./bin/dev project info

# List sub-projects
./bin/dev project list

# (Future) Create new sub-project
./bin/dev project new drone-7inch

# (Future) Switch project context
./bin/dev project use drone-7inch
```

**Missing Commands:**
- `./bin/dev project new <name>` - create sub-project
- `./bin/dev project use <name>` - switch context
- `./bin/dev project clone <name> <new-name>` - copy project

---

### 6. Design Memory Flow (Neo4j)
**Goal:** Track design decisions and patterns

```
[Record decision] → [Link to components] → [Query patterns] → [Reuse knowledge]
```

**CLI Implementation:**
```bash
# Open Neo4j browser
./bin/dev project neo4j

# (Future) Record design decision
./bin/dev memory add "chose M3 screws for weight" --tags motors,fasteners

# (Future) Query patterns
./bin/dev memory search "motor mount"
```

**Missing Commands:**
- `./bin/dev memory add <note>` - record decision
- `./bin/dev memory search <query>` - find patterns
- `./bin/dev memory link <comp1> <comp2> --rel "mounts_with"`

---

## Recommended CLI Structure

```
semicad
├── view [file]           # Open cq-editor
├── edit [file]           # Open editor
├── build                 # Build project
├── export <comp>         # Export component
├── render <file>         # Render to PNG
│
├── lib                   # Library commands
│   ├── list              # List components
│   ├── info <comp>       # Component details
│   ├── search <query>    # Search components
│   ├── fasteners         # Fastener sizes
│   └── bearings          # Bearing sizes
│
├── project               # Project commands
│   ├── info              # Show project
│   ├── list              # List sub-projects
│   ├── new <name>        # Create project
│   ├── use <name>        # Switch project
│   └── neo4j             # Open Neo4j
│
├── component             # Component commands (NEW)
│   ├── new <name>        # Scaffold component
│   ├── validate <name>   # Check geometry
│   └── test <name>       # Test component
│
├── assembly              # Assembly commands (NEW)
│   ├── new <name>        # Scaffold assembly
│   ├── add <comp>        # Add component
│   └── check             # Check clearances
│
└── memory                # Design memory (NEW)
    ├── add <note>        # Record decision
    ├── search <query>    # Query patterns
    └── export            # Export to markdown
```

## Priority Implementation

### Phase 1 (Current - Done)
- [x] Basic CLI structure
- [x] Library browsing
- [x] Component registry
- [x] Build/export commands

### Phase 2 (Next)
- [ ] Project new/use commands
- [ ] Component scaffolding
- [ ] Assembly scaffolding

### Phase 3 (Future)
- [ ] Design memory integration
- [ ] Drawing generation
- [ ] BOM generation
- [ ] Clearance checking
