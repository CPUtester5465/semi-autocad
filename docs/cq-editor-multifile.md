# CQ-Editor Multi-File Project Setup

This document explains how to make cq-editor work with multi-file structures (importing modules from other files).

---

## The Problem

When you open a script in cq-editor that imports from local modules:

```python
from components import get_component  # ModuleNotFoundError!
```

cq-editor can't find the module because the script's directory isn't in Python's path.

---

## Solutions (Choose One)

### Solution 1: Install as Package (Recommended)

**Best for:** Larger projects, team development, consistent behavior.

1. Create `pyproject.toml` in project root:
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "semicad"
version = "0.1.0"
dependencies = ["cadquery"]

[tool.setuptools.packages.find]
where = ["."]
include = ["scripts*"]
```

2. Create `scripts/__init__.py`:
```python
# Makes scripts/ a Python package
```

3. Install in development mode:
```bash
cd /home/user/cad
pip install -e .
```

4. Use package imports in scripts:
```python
from scripts.components import get_component  # Works everywhere!
```

**Advantage:** Works from any directory, consistent with Python best practices.

---

### Solution 2: CQ-Editor Preference Setting

**Best for:** Quick projects, single-directory scripts.

1. Open cq-editor
2. Go to **Edit → Preferences → Debugger**
3. Check **"Add script dir to path"**
4. Restart cq-editor

Now imports from the same directory will work:
```python
from components import get_component  # Works if in same dir
```

**Limitation:** Only works for files in the same directory as the main script.

---

### Solution 3: PYTHONPATH Environment Variable

**Best for:** Temporary fixes, testing.

```bash
# Set before launching cq-editor
export PYTHONPATH="/home/user/cad/scripts:$PYTHONPATH"
cq-editor /home/user/cad/scripts/quadcopter_assembly.py
```

Or create a launcher script:

```bash
#!/bin/bash
# cq-editor-launcher.sh
export PYTHONPATH="/home/user/cad/scripts:$PYTHONPATH"
cq-editor "$@"
```

---

### Solution 4: sys.path Hack (Not Recommended)

**Best for:** Quick debugging, understanding the problem.

Add at the top of your script:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from components import get_component  # Now works
```

**Limitation:** Modifies global state, can cause issues with module reloading.

---

## Our Project Structure

```
/home/user/cad/
├── pyproject.toml          # Package definition
├── scripts/
│   ├── __init__.py         # Makes it a package
│   ├── components.py       # Component library
│   ├── quadcopter_assembly.py
│   └── export_views.py
└── output/
```

**Import pattern:**
```python
from scripts.components import get_component
from scripts.export_views import export_svg_views
```

---

## Verification

Test imports work from anywhere:
```bash
cd /tmp
python -c "from scripts.components import get_component; print('OK')"
```

Test cq-editor:
```bash
cq-editor /home/user/cad/scripts/quadcopter_assembly.py
# Press F5 - should render without ModuleNotFoundError
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'scripts'"

Package not installed. Run:
```bash
cd /home/user/cad
pip install -e .
```

### "ModuleNotFoundError: No module named 'components'"

Using old import style. Change:
```python
# Old (doesn't work in cq-editor)
from components import get_component

# New (works everywhere)
from scripts.components import get_component
```

### Changes to components.py not reflected

cq-editor caches modules. Either:
1. Restart cq-editor
2. Or: Edit → Preferences → Debugger → Check "Reload CQ" (forces module reload)

---

## Sources

- [CQ-editor Issue #156: ModuleNotFoundError for local files](https://github.com/CadQuery/CQ-editor/issues/156)
- [CQ-editor Issue #347: Importing Python modules](https://github.com/CadQuery/CQ-editor/issues/347)
- [CQ-editor Installation Wiki](https://github.com/CadQuery/CQ-editor/wiki/Installation)
