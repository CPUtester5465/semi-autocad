# Code Security Audit Report - 2026-02-01

## Executive Summary

This audit reviewed the semi-autocad codebase for security vulnerabilities, code quality issues, and architectural concerns. The codebase is generally well-structured with appropriate use of design patterns. Several findings require attention, ranging from informational notes to medium-severity security issues.

**Overall Risk Level: LOW-MEDIUM**

---

## Findings Summary

| Severity | Count | Description |
|----------|-------|-------------|
| HIGH | 0 | Critical security vulnerabilities |
| MEDIUM | 3 | Security issues requiring attention |
| LOW | 5 | Minor issues and code quality concerns |
| INFO | 6 | Best practice recommendations |

---

## MEDIUM Severity Findings

### M1. Hardcoded Credentials in project.py

**Location:** `semicad/cli/commands/project.py:413-415`

**Issue:** Neo4j database credentials are hardcoded and displayed to users.

```python
click.echo("  User: neo4j")
click.echo("  Pass: semicad2026")
```

**Risk:** Credentials exposed in source code and CLI output. If this repository is made public or Neo4j is exposed to a network, unauthorized access is possible.

**Recommendation:**
- Move credentials to environment variables or a configuration file
- Use `.env` file with `python-dotenv`
- Add credential files to `.gitignore`

---

### M2. Subprocess Command Injection Risk (Blender Script)

**Location:** `semicad/export/render.py:189-232`

**Issue:** The `render_stl_to_png_blender()` function constructs a Python script as a string with f-string interpolation of file paths.

```python
blender_script = f'''
...
bpy.ops.wm.stl_import(filepath="{stl_path}")
...
bpy.context.scene.render.filepath = "{output_path}"
'''
```

**Risk:** If `stl_path` or `output_path` contain quotes or escape sequences, the generated Python script could malfunction or execute unintended code within Blender's Python environment.

**Recommendation:**
- Use `json.dumps()` to properly escape path strings
- Or pass paths via Blender command line arguments: `--python-expr`
- Or use environment variables accessible from the Blender script

---

### M3. EDITOR Environment Variable Command Injection

**Location:** `semicad/cli/commands/view.py:72-75`

**Issue:** The `edit` command reads the `EDITOR` environment variable and passes it directly to `subprocess.run()`.

```python
editor = os.environ.get("EDITOR", "nano")
subprocess.run([editor, str(file)])
```

**Risk:** While subprocess.run with a list prevents shell injection, a malicious EDITOR value could still execute arbitrary binaries. This is a minor risk since EDITOR is user-controlled environment variable.

**Recommendation:**
- Validate EDITOR against a whitelist of known editors
- Or document that this is intentional behavior

---

## LOW Severity Findings

### L1. Silent Exception Swallowing

**Location:** `semicad/core/registry.py:280-293`

**Issue:** Default source initialization silently catches and ignores all exceptions.

```python
try:
    registry.register_source(custom.CustomSource())
except Exception:
    pass  # Custom source not available
```

**Risk:** Legitimate configuration errors are hidden, making debugging difficult.

**Recommendation:** Log warnings for caught exceptions, distinguishing between expected ImportError and unexpected errors.

---

### L2. YAML Loading Without Schema Validation

**Location:** `semicad/core/project.py:29-34`, `semicad/templates/__init__.py:117-119`

**Issue:** YAML files are loaded with `yaml.safe_load()` (which is safe) but without schema validation.

```python
with open(partcad_file) as f:
    self.config = yaml.safe_load(f) or {}
```

**Risk:** Malformed YAML could cause unexpected behavior if keys are missing or have wrong types.

**Recommendation:** Add schema validation using `jsonschema` or `pydantic` for configuration files.

---

### L3. Path Traversal Not Fully Validated

**Location:** `semicad/cli/commands/project.py:310-316`

**Issue:** Sub-project paths are constructed from user input without full path traversal protection.

```python
subproject_dir = proj.projects_dir / subproject
if not subproject_dir.exists():
    click.echo(f"Sub-project not found: {subproject}", err=True)
```

**Risk:** While Click's Path type provides some protection, explicit validation that resolved paths stay within the projects directory would be more robust.

**Recommendation:** Add explicit check that resolved path is within projects_dir:
```python
if not subproject_dir.resolve().is_relative_to(proj.projects_dir.resolve()):
    raise ValueError("Invalid subproject path")
```

---

### L4. Unbounded Cache Size Default

**Location:** `semicad/core/registry.py:79`

**Issue:** Default cache size is 128, but there's no warning if memory usage grows large.

```python
DEFAULT_CACHE_SIZE = 128
```

**Risk:** With complex CAD geometries, 128 cached components could consume significant memory.

**Recommendation:** Add memory monitoring or make cache size configurable via environment variable.

---

### L5. Template Rendering with safe_substitute

**Location:** `semicad/templates/__init__.py:97-98`

**Issue:** Using `safe_substitute` silently ignores undefined variables.

```python
template = Template(content)
return template.safe_substitute(context)
```

**Risk:** Template variables that aren't provided are left as `$variable` in output, which could cause syntax errors in generated Python files.

**Recommendation:** Use `substitute()` and catch KeyError, or validate all expected variables are provided.

---

## INFORMATIONAL Findings

### I1. No Input Validation on Component Parameters

**Location:** `semicad/sources/warehouse.py:135-173`

**Issue:** The warehouse source accepts arbitrary parameters without type validation.

```python
def get_component(self, name: str, **params) -> Component:
    size = params.get("size", "M3-0.5")
    length = params.get("length")
```

**Note:** While the electronics source has parameter validation (PARAM_SCHEMAS), the warehouse source does not. Invalid parameters will cause errors at build time rather than validation time.

---

### I2. No Rate Limiting on Subprocess Calls

**Location:** `semicad/cli/commands/build.py:37-41`, `semicad/cli/commands/project.py:463`

**Issue:** CLI commands that invoke subprocess have no rate limiting.

**Note:** Could potentially be used to spawn many processes if invoked in a loop, but this is a CLI tool with local execution.

---

### I3. Global Singleton Pattern Usage

**Locations:**
- `semicad/core/registry.py:262-272` (`_registry` global)
- `semicad/core/project.py:72-86` (`_current_project` global)

**Issue:** Global singletons can make testing and concurrent usage difficult.

**Note:** Acceptable for CLI applications but limits reusability as a library.

---

### I4. No Timeout on Subprocess Calls

**Location:** `semicad/cli/commands/project.py:463`

**Issue:** Build scripts are run without timeout (except Blender which has 60s timeout).

```python
result = subprocess.run(cmd, cwd=str(subproject_dir))
```

**Note:** A runaway build script could hang indefinitely.

---

### I5. Debug Information in Error Messages

**Location:** Various CLI commands

**Issue:** Error messages include full file paths and stack traces.

**Note:** Appropriate for development CLI but may leak sensitive path information in production logs.

---

### I6. Missing __all__ Exports

**Location:** Several modules

**Issue:** Many modules don't define `__all__`, making it unclear what the public API is.

**Note:** The templates module correctly defines `__all__` at line 331-343, but other modules do not.

---

## Positive Security Observations

1. **yaml.safe_load()** is used consistently for YAML parsing (not `yaml.load()`)
2. **subprocess.run()** uses list arguments, preventing shell injection
3. **Path validation** exists for project names via `validate_project_name()`
4. **Parameter validation** exists for electronics components with schemas
5. **Click's built-in validation** is used for many CLI arguments
6. **No eval/exec** of user input found anywhere in the codebase

---

## Dependency Review

| Package | Version | Notes |
|---------|---------|-------|
| cadquery | unpinned | Core dependency, should pin major version |
| click | >=8.0 | Good minimum version |
| pyyaml | unpinned | Uses safe_load correctly |
| cq-electronics | >=0.2.0 | Version check implemented |

**Recommendations:**
- Add upper bounds on major versions to prevent breaking changes
- Consider using `poetry` or `pip-tools` for reproducible installs
- Add a `requirements-lock.txt` for deterministic builds

---

## Code Quality Observations

### Strengths
- Clean separation of concerns (CLI, core, sources, export)
- Consistent use of type hints (Python 3.10+)
- Good docstrings throughout
- Design patterns used appropriately (Adapter, Registry, Decorator)
- Parameter validation with clear error messages (electronics source)

### Areas for Improvement
- Test coverage could not be assessed (no pytest results)
- Some code duplication in parameter parsing (`parse_param` appears twice)
- Magic strings could be constants (e.g., "custom", "cq_warehouse")

---

## Recommendations Priority Matrix

| Priority | Finding | Effort |
|----------|---------|--------|
| HIGH | M1 - Remove hardcoded credentials | Low |
| HIGH | M2 - Fix Blender script injection | Medium |
| MEDIUM | L1 - Improve exception logging | Low |
| MEDIUM | L3 - Add path traversal checks | Low |
| LOW | L2 - Add YAML schema validation | Medium |
| LOW | I1 - Add warehouse param validation | Medium |

---

## Conclusion

The semi-autocad codebase demonstrates good security practices overall, with proper use of `yaml.safe_load()`, list-based subprocess calls, and input validation on project names. The main areas requiring attention are:

1. Removal of hardcoded credentials
2. Proper escaping in dynamically generated Blender scripts
3. Enhanced exception handling for better debugging

The architecture is sound and follows SOLID principles. The CLI is well-structured with Click, and the component registry provides clean abstraction over multiple component sources.

**Report prepared by:** Claude Code Audit
**Date:** 2026-02-01
**Files reviewed:** 25+ Python files across semicad/, scripts/, and projects/
