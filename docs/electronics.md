# cq_electronics Integration

This document covers the `cq_electronics` component source, which provides electronic components for enclosure design and PCB-integrated assemblies.

## Overview

The `ElectronicsSource` adapter exposes components from the [cq_electronics](https://github.com/gumyr/cq_electronics) library through the semicad registry. Components include:

- **Boards** - Single-board computers (Raspberry Pi)
- **Connectors** - Pin headers, RJ45 jacks
- **SMD** - Surface-mount packages (BGA)
- **Mechanical** - DIN rail components
- **Mounting** - Enclosure mounting clips

## Available Components

| Name | Category | Description | Required Params |
|------|----------|-------------|-----------------|
| `RPi3b` | board | Raspberry Pi 3B single-board computer | - |
| `PinHeader` | connector | Through-hole pin header | - |
| `JackSurfaceMount` | connector | RJ45 Ethernet jack (surface mount) | - |
| `BGA` | smd | Ball Grid Array chip package | `length`, `width` |
| `DinClip` | mechanical | DIN rail mounting clip | - |
| `TopHat` | mechanical | Top-hat (TH35) DIN rail section | `length` |
| `PiTrayClip` | mounting | Raspberry Pi mounting tray clip (76x20x15mm) | - |

## Basic Usage

```python
from semicad import get_registry

registry = get_registry()

# Get a Raspberry Pi 3B
rpi = registry.get("RPi3b")

# Access the CadQuery geometry
geometry = rpi.geometry  # Returns cq.Workplane
```

## Parametric Components

Some components accept parameters to customize their geometry:

### PinHeader

Through-hole pin headers for PCB connections.

```python
# Single row, 10 pins
header_1x10 = registry.get("PinHeader", columns=10)

# Double row, 20 pins (GPIO header)
gpio_header = registry.get("PinHeader", rows=2, columns=20)

# Custom pin heights
tall_header = registry.get("PinHeader", rows=1, columns=8, above=11, below=3)
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rows` | int | 1 | Number of pin rows |
| `columns` | int | 1 | Number of pin columns |
| `above` | float | 7 | Pin height above board (mm) |
| `below` | float | 3 | Pin height below board (mm) |
| `simple` | bool | True | Use simplified geometry |

### BGA (Ball Grid Array)

Surface-mount chip packages.

```python
# 10mm x 10mm BGA package
small_chip = registry.get("BGA", length=10, width=10)

# Large processor package with custom height
processor = registry.get("BGA", length=23, width=23, height=2.1)
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `length` | float | *required* | Package length (mm) |
| `width` | float | *required* | Package width (mm) |
| `height` | float | 1 | Package height (mm) |
| `simple` | bool | True | Use simplified geometry |

### TopHat (DIN Rail)

Standard TH35 DIN rail sections for industrial enclosures.

```python
# 100mm DIN rail section
rail = registry.get("TopHat", length=100)

# Rail without mounting slots
solid_rail = registry.get("TopHat", length=150, slots=False)

# Custom depth (non-standard)
deep_rail = registry.get("TopHat", length=100, depth=15)
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `length` | float | *required* | Rail length (mm) |
| `depth` | float | 7.5 | Rail depth (mm) |
| `slots` | bool | True | Include mounting slots |

### JackSurfaceMount (RJ45)

Surface-mount Ethernet jack.

```python
# Standard RJ45 jack
rj45 = registry.get("JackSurfaceMount")

# Custom length variant
long_jack = registry.get("JackSurfaceMount", length=25)
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `length` | float | 21 | Jack body length (mm) |
| `simple` | bool | True | Use simplified geometry |

### PiTrayClip

Mounting clip for Raspberry Pi boards in enclosures.

```python
# Pi mounting tray clip
clip = registry.get("PiTrayClip")
```

No parameters - fixed 76x20x15mm design.

## Component Metadata

Electronics components expose metadata properties for accessing dimensions, mounting holes, and other design parameters.

### Dimensions

```python
rpi = registry.get("RPi3b")

# Get dimensions as (width, height, thickness)
dims = rpi.dimensions  # (85.0, 56.0, 1.5)
```

### Mounting Holes

```python
rpi = registry.get("RPi3b")

# Get mounting hole locations as [(x, y), ...]
holes = rpi.mounting_holes
# [(24.5, 19.0), (-24.5, -39.0), (-24.5, 19.0), (24.5, -39.0)]
```

### All Metadata

Access all UPPER_CASE class constants:

```python
rpi = registry.get("RPi3b")

# Get all metadata
meta = rpi.metadata
# {'WIDTH': 85, 'HEIGHT': 56, 'THICKNESS': 1.5, 'HOLE_DIAMETER': 2.7, ...}
```

### Raw Instance Access

For advanced use, access the underlying cq_electronics instance:

```python
rpi = registry.get("RPi3b")

# Access raw instance attributes
rpi.raw_instance.hole_points  # Original hole_points attribute
rpi.raw_instance.simple       # Current simple setting
```

## Assembly Structure

Components that are assemblies (like RPi3b) preserve their sub-part structure, allowing access to individual parts and colors.

### Checking for Assembly

```python
rpi = registry.get("RPi3b")

if rpi.has_assembly:
    print("Component has assembly structure")
```

### Listing Parts

```python
rpi = registry.get("RPi3b")

# List all sub-parts
parts = rpi.list_parts()
# ['rpi__pcb_substrate', 'rpi__ethernet_port', 'rpi__usb_port', ...]
```

### Part Colors

```python
rpi = registry.get("RPi3b")

# Get color map (RGBA 0-1 tuples)
colors = rpi.get_color_map()
# {'rpi__pcb_substrate': (0.85, 0.75, 0.55, 1.0), ...}
```

### Extracting Sub-Parts

```python
rpi = registry.get("RPi3b")

# Get specific sub-part geometry
ethernet = rpi.get_part("rpi__ethernet_port")
if ethernet:
    # Position ethernet port separately
    positioned = ethernet.translate((0, 0, 10))
```

### Colored STEP Export

To preserve colors in exports, use the assembly directly:

```python
rpi = registry.get("RPi3b")

# Export with colors preserved
if rpi.has_assembly:
    rpi.assembly.save("rpi_colored.step")
```

## Utility Constants

The electronics module exposes useful constants from cq_electronics.

### Hole Sizes

Standard hole diameters for mounting electronics:

```python
from semicad.sources.electronics import HOLE_SIZES

# Tap hole diameters
HOLE_SIZES["M2R5_TAP_HOLE"]        # 2.15mm (M2.5 tap drill)
HOLE_SIZES["M4_TAP_HOLE"]          # 3.2mm (M4 tap drill)

# Clearance holes
HOLE_SIZES["M4_CLEARANCE_NORMAL"]  # 4.5mm (M4 clearance)

# Countersink
HOLE_SIZES["M4_COUNTERSINK"]       # 9.4mm diameter
HOLE_SIZES["M_COUNTERSINK_ANGLE"]  # 90 degrees
```

### Material Colors

RGB color values for rendering:

```python
from semicad.sources.electronics import COLORS

# PCB colors
COLORS["pcb_substrate_chiffon"]   # PCB substrate
COLORS["solder_mask_green"]       # Green solder mask

# Metal colors
COLORS["gold_plate"]              # Gold-plated contacts
COLORS["tin_plate"]               # Tin-plated surfaces
COLORS["stainless_steel"]         # Stainless steel parts

# Plastic
COLORS["black_plastic"]           # Dark plastic components
```

## Parameter Validation

Parameters are validated before component creation. Invalid parameters raise `ParameterValidationError`.

### Type Validation

```python
# Type error - rows must be int
try:
    header = registry.get("PinHeader", rows="2")  # Should be int
except ParameterValidationError as e:
    print(e)  # "Parameter 'rows' must be int, got str ('2')"
```

### Range Validation

```python
# Range error - rows must be >= 1
try:
    header = registry.get("PinHeader", rows=0)
except ParameterValidationError as e:
    print(e)  # "Parameter 'rows' must be >= 1, got 0"
```

### Unknown Parameters

By default, unknown parameters raise an error:

```python
# Unknown parameter error
try:
    rpi = registry.get("RPi3b", invalid_param=True)
except ParameterValidationError as e:
    print(e)  # "Unknown parameter(s) for RPi3b: ['invalid_param']"
```

Use `strict=False` to silently filter unknown parameters:

```python
# Non-strict mode - unknown params filtered out
rpi = registry.get("RPi3b", strict=False, invalid_param=True)
# Works - invalid_param is silently ignored
```

## Version Compatibility

The adapter checks cq_electronics version on initialization.

### Minimum Version

- **Minimum cq_electronics version:** 0.2.0
- **Tested with:** cadquery 2.5.x

### Version Warning

If an older version is detected, a warning is issued:

```
UserWarning: cq_electronics 0.1.0 may not be compatible.
Minimum recommended: 0.2.0
```

### Error Messages

Component-not-found errors include version info:

```python
try:
    comp = registry.get("NonExistent")
except KeyError as e:
    print(e)
    # "Component not found in cq_electronics: NonExistent (installed: 0.2.0).
    #  Minimum version: 0.2.0"
```

## Integration with Assemblies

Electronics components integrate with the semicad assembly system:

```python
from semicad import get_registry
import cadquery as cq

registry = get_registry()

# Get components
rpi = registry.get("RPi3b")
header = registry.get("PinHeader", rows=2, columns=20)

# Create enclosure base
enclosure = cq.Workplane("XY").box(100, 70, 30)

# Position Raspberry Pi in enclosure
rpi_positioned = rpi.geometry.translate((0, 0, 5))

# For cq-editor visualization
try:
    show_object(enclosure, name="enclosure", options={"alpha": 0.3})
    show_object(rpi_positioned, name="rpi")
except NameError:
    pass
```

## Export Workflow

Export electronics components to STEP/STL for manufacturing:

```python
from semicad import get_registry
import cadquery as cq

registry = get_registry()

# Get component
din_rail = registry.get("TopHat", length=200)

# Export to STEP (CAD exchange)
cq.exporters.export(din_rail.geometry, "din_rail.step")

# Export to STL (3D printing)
cq.exporters.export(din_rail.geometry, "din_rail.stl")
```

Or use the CLI:

```bash
# Export via CLI (if component is registered)
./bin/dev export TopHat --params length=200
```

## Extending the Catalog

To add new cq_electronics components, edit `semicad/sources/electronics.py`:

```python
COMPONENT_CATALOG = {
    # ... existing components ...

    # Add new component
    "NewComponent": (
        "cq_electronics.module.submodule",  # Import path
        "ClassName",                         # Class name
        "category",                          # Category (board, connector, smd, mechanical)
        "Description of the component",      # Description
        ["required_param"],                  # Required parameters (list)
        {"optional_param": default_value},   # Default parameters (dict)
    ),
}
```

## Technical Notes

### Geometry Handling

cq_electronics components may return either `cq.Assembly` or `cq.Workplane` objects. The `ElectronicsSource` adapter automatically converts assemblies:

```python
# Internal conversion logic
if isinstance(cq_obj, cq.Assembly):
    compound = cq_obj.toCompound()
    return cq.Workplane("XY").add(compound)
```

This ensures all components provide a consistent `cq.Workplane` interface.

### Simple Mode

Most components support `simple=True` (default), which generates simplified geometry for faster rendering and smaller file sizes. Set `simple=False` for detailed geometry when needed:

```python
# Detailed geometry (slower)
detailed_rpi = registry.get("RPi3b", simple=False)
```

### Error Handling

Components with required parameters raise `ValueError` if parameters are missing:

```python
# This will raise ValueError
try:
    bga = registry.get("BGA")  # Missing length, width
except ValueError as e:
    print(e)  # "Missing required parameters for BGA: ['length', 'width']"
```

## See Also

- [cq-editor Multi-File Setup](cq-editor-multifile.md) - Visualization patterns
- [cq_electronics GitHub](https://github.com/gumyr/cq_electronics) - Upstream library
- [README.md](../readme.md) - Project overview
