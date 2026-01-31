# CQ-Editor Multi-File Project Setup

How to make cq-editor work with multi-file structures (importing modules from other files).

---

## The Problem

When you open a script in cq-editor that imports from local modules:

```python
from components import get_component  # ModuleNotFoundError!
```

cq-editor can't find the module because the script's directory isn't in Python's path.

---

## Our Solution: CLI + Package Install

We use a combination approach:

### 1. Package Installation

The project is installed as an editable package:

```bash
pip install -e .
```

This allows imports like:
```python
from scripts.components import get_component
from semicad import get_registry
```

### 2. CLI with PYTHONPATH

The `./bin/dev` CLI sets PYTHONPATH automatically:

```bash
# Opens cq-editor with correct paths
./bin/dev view scripts/components.py

# For sub-projects
./bin/dev project view quadcopter-5inch
./bin/dev project view quadcopter-5inch -f frame.py
```

---

## Key Pattern for cq-editor Scripts

**Important:** Put `show_object()` at module level, not inside `if __name__`:

```python
#!/usr/bin/env python3
"""My CAD Script"""

import cadquery as cq
from scripts.components import get_component

# === Generate geometry ===
motor = get_component("motor_2207")
frame = cq.Workplane("XY").box(100, 100, 4)

# === For cq-editor (at module level!) ===
try:
    show_object(frame, name="Frame", options={"color": "gold"})
    show_object(motor, name="Motor", options={"color": "gray"})
except NameError:
    pass  # Not running in cq-editor

# === CLI execution ===
if __name__ == "__main__":
    import cadquery as cq
    cq.exporters.export(frame, "output/frame.step")
    print("Exported frame.step")
```

**Why?** cq-editor executes the entire script but `show_object` only exists in the cq-editor context. The try/except allows the same script to work both in cq-editor and from command line.

---

## Project Structure

```
/home/user/cad/
├── bin/dev                     # CLI (sets PYTHONPATH)
├── pyproject.toml              # Package definition
├── semicad/                    # Core library
│   ├── cli/                    # CLI commands
│   ├── core/                   # Component, Registry
│   └── sources/                # Source adapters
├── scripts/
│   ├── __init__.py             # Package marker
│   └── components.py           # Component library
└── projects/
    └── quadcopter-5inch/       # Sub-project
        ├── frame.py            # Part (cq-editor compatible)
        ├── assembly.py         # Assembly (cq-editor compatible)
        └── build.py            # Build script (CLI only)
```

---

## Quick Reference

### Open in cq-editor

```bash
# Root scripts
./bin/dev view scripts/components.py

# Sub-project files
./bin/dev project view quadcopter-5inch
./bin/dev project view quadcopter-5inch -f frame.py
```

### Import Patterns

```python
# From scripts/
from scripts.components import get_component, motor, flight_controller

# From semicad library
from semicad import get_registry
from semicad.core.component import Component

# Within a sub-project (e.g., in projects/quadcopter-5inch/assembly.py)
from config import CONFIG        # Local to project
from frame import generate_frame # Local to project
from scripts.components import get_component  # From root
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'scripts'"

Package not installed:
```bash
cd /home/user/cad
pip install -e .
```

### "ModuleNotFoundError: No module named 'semicad'"

Same fix - reinstall:
```bash
pip install -e .
```

### Changes not reflected in cq-editor

cq-editor caches modules. Options:
1. Restart cq-editor
2. Edit → Preferences → Debugger → Check "Reload CQ"

### Empty viewport after F5

1. Check console (bottom panel) for errors
2. Ensure `show_object()` is at module level (not inside `if __name__`)
3. Zoom out - model might be small

### Can't find local imports in sub-project

Sub-projects need path setup. Use the CLI:
```bash
./bin/dev project view quadcopter-5inch -f assembly.py
```

Or add to your script:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

---

## Sources

- [CQ-editor Issue #156: ModuleNotFoundError](https://github.com/CadQuery/CQ-editor/issues/156)
- [CQ-editor Issue #347: Importing modules](https://github.com/CadQuery/CQ-editor/issues/347)
