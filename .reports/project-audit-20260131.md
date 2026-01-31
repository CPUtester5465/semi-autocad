# Project Audit - 2026-01-31

## Current State Summary

### Working
- ✅ `semicad` CLI with Click-based commands
- ✅ Component registry (custom + cq_warehouse)
- ✅ `projects/quadcopter-5inch/` - fully functional MVP project
- ✅ cq-editor visualization working
- ✅ STEP/STL export working
- ✅ BOM generation working
- ✅ All imports passing (`./bin/dev test`)

### Directory Structure
```
/home/user/cad/
├── bin/dev                 ✅ CLI entry point
├── semicad/                ✅ Core library
│   ├── cli/commands/       ✅ view, build, library, project
│   ├── core/               ✅ Component, Registry, Project
│   ├── sources/            ✅ custom, warehouse adapters
│   └── export/             ⚠️ EMPTY - not implemented
├── scripts/                ⚠️ REDUNDANT FILES
├── projects/quadcopter-5inch/  ✅ MVP project
├── output/                 ⚠️ OLD FILES - should clean
├── screenshots/            ❌ DELETE - old images
└── [config files]
```

---

## Issues to Fix

### 1. CLAUDE.md Outdated
**Problem:** Doesn't reflect new architecture
**Fix:** Update with new CLI commands, project structure, semicad library

### 2. Redundant Files in scripts/
| File | Status | Action |
|------|--------|--------|
| `components.py` | ✅ KEEP | Core component library |
| `__init__.py` | ✅ KEEP | Package marker |
| `assembly_viewer.py` | ⚠️ REDUNDANT | Replaced by projects/*/assembly.py |
| `quadcopter_assembly.py` | ⚠️ REDUNDANT | Replaced by projects/quadcopter-5inch/ |
| `export_views.py` | ⚠️ MAYBE KEEP | Could move to semicad/export/ |

### 3. Old Output Files
**Location:** `/home/user/cad/output/`
**Action:** Delete old files, use `projects/*/output/` instead
```
- quad_frame_220mm.step/stl (old)
- quad_frame_assembly.step/stl (old)
- test_export* (old tests)
- motor_2207.step (moved to project)
```

### 4. Screenshots Directory
**Location:** `/home/user/cad/screenshots/`
**Content:** Old images (image.png, image copy.png)
**Action:** DELETE - not needed

### 5. .gitignore Incomplete
**Missing:**
```
__pycache__/
*.egg-info/
output/
*.pyc
.DS_Store
```

### 6. Empty semicad/export/ Module
**Status:** Directory exists but empty
**Should contain:**
- step.py - STEP export utilities
- stl.py - STL export utilities
- render.py - PNG rendering
- bom.py - BOM generation

---

## Missing Features

### CLI Commands Not Implemented
| Command | Priority | Description |
|---------|----------|-------------|
| `project new <name>` | HIGH | Scaffold new sub-project |
| `project use <name>` | MEDIUM | Switch active project |
| `component new <name>` | MEDIUM | Scaffold component generator |
| `memory add` | LOW | Record design decision to Neo4j |
| `memory search` | LOW | Query design patterns |

### Code Gaps
1. **No project scaffolding** - must manually create project files
2. **No clearance checking CLI** - only in assembly.py
3. **No drawing generation** - 2D drawings not implemented
4. **cq_electronics source** - adapter not written (only warehouse)

---

## Cleanup Actions

### Immediate (Do Now)
```bash
# 1. Remove old screenshots
rm -rf screenshots/

# 2. Clean old output files
rm -rf output/quad_frame* output/test_export* output/components/

# 3. Remove redundant scripts
rm scripts/assembly_viewer.py scripts/quadcopter_assembly.py

# 4. Update .gitignore
```

### Soon (This Session)
1. Update CLAUDE.md with current architecture
2. Move export_views.py utilities to semicad/export/
3. Update .gitignore

### Later
1. Implement `project new` scaffolding
2. Add cq_electronics source adapter
3. Implement design memory CLI commands

---

## File Inventory After Cleanup

### Keep
```
bin/dev
semicad/**
scripts/components.py
scripts/__init__.py
projects/quadcopter-5inch/**
docs/
.reports/
.claude/
pyproject.toml
partcad.yaml
readme.md
CLAUDE.md
.gitignore
```

### Delete
```
screenshots/
output/quad_frame*
output/test_export*
output/components/
scripts/assembly_viewer.py
scripts/quadcopter_assembly.py
```

### Move
```
scripts/export_views.py → semicad/export/views.py (optional)
```
