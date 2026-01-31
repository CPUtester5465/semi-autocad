#!/usr/bin/env python3
"""
Parametric Quadcopter Frame Generator
=====================================
Generates a simple X-frame quadcopter with:
- Center plate with FC/ESC mount holes
- 4 arms with motor mount holes
- Configurable for different sizes

Usage:
    python quadcopter_frame.py

Or open in cq-editor for interactive visualization.
"""

import cadquery as cq
from pathlib import Path

# ============== PARAMETERS ==============
# Change these to customize your frame

# Frame size
WHEELBASE = 220          # mm, motor to motor diagonal
ARM_COUNT = 4            # Number of arms (4 = X-frame)

# Arm dimensions
ARM_WIDTH = 12           # mm
ARM_THICKNESS = 3        # mm (same as center for flush design)

# Center plate
CENTER_SIZE = 40         # mm, center plate width/length
CENTER_THICKNESS = 3     # mm (match arm thickness)

# FC/ESC stack mount (30.5mm standard)
STACK_HOLE_SPACING = 30.5   # mm
STACK_HOLE_DIA = 3.2        # mm (M3 clearance)

# Motor mount (16mm for 22xx motors)
MOTOR_HOLE_SPACING = 16     # mm, bolt circle diameter
MOTOR_HOLE_DIA = 3.2        # mm (M3 clearance)
MOTOR_CENTER_HOLE = 8       # mm, center shaft clearance

# Design features
FILLET_RADIUS = 2        # mm, edge fillets
WEIGHT_REDUCTION = True  # Add lightening holes

# ============== CALCULATIONS ==============
arm_length = (WHEELBASE * 0.707 / 2) - (CENTER_SIZE / 2)  # 0.707 = cos(45°)
arm_angle = 360 / ARM_COUNT

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============== CENTER PLATE ==============
print(f"Creating center plate: {CENTER_SIZE}x{CENTER_SIZE}x{CENTER_THICKNESS}mm")

center = (
    cq.Workplane("XY")
    .box(CENTER_SIZE, CENTER_SIZE, CENTER_THICKNESS)
    # FC/ESC mount holes (30.5mm pattern)
    .faces(">Z")
    .workplane()
    .rect(STACK_HOLE_SPACING, STACK_HOLE_SPACING, forConstruction=True)
    .vertices()
    .hole(STACK_HOLE_DIA)
)

# Add corner fillets to center plate
center = center.edges("|Z").fillet(FILLET_RADIUS)

# ============== SINGLE ARM ==============
print(f"Creating arm: {arm_length}x{ARM_WIDTH}x{ARM_THICKNESS}mm")

# Create arm extending in +X direction
arm = (
    cq.Workplane("XY")
    .box(arm_length, ARM_WIDTH, ARM_THICKNESS)
    # Position arm flush with center plate (no Z offset since same thickness)
    .translate((arm_length/2 + CENTER_SIZE/2, 0, 0))
)

# Add motor mount holes at end of arm
motor_mount_center_x = arm_length + CENTER_SIZE/2
arm = (
    arm
    .faces(">Z")
    .workplane()
    .center(motor_mount_center_x, 0)
    # Center hole for motor shaft
    .hole(MOTOR_CENTER_HOLE)
)

# Add 4 motor mount holes in square pattern
arm = (
    arm
    .faces(">Z")
    .workplane()
    .center(motor_mount_center_x, 0)
    .rect(MOTOR_HOLE_SPACING, MOTOR_HOLE_SPACING, forConstruction=True)
    .vertices()
    .hole(MOTOR_HOLE_DIA)
)

# Note: Fillets applied after boolean union to avoid geometry errors

# ============== WEIGHT REDUCTION (optional) ==============
# Disabled for MVP - can add lightening holes later
# if WEIGHT_REDUCTION and arm_length > 30:
#     slot_length = arm_length - 25
#     slot_width = ARM_WIDTH - 6
#     if slot_length > 10 and slot_width > 3:
#         slot_center_x = CENTER_SIZE/2 + 12 + slot_length/2
#         arm = arm.faces(">Z").workplane().center(slot_center_x, 0)
#         arm = arm.slot2D(slot_length, slot_width, angle=0).cutThruAll()

# ============== COMBINE ARMS ==============
print(f"Combining {ARM_COUNT} arms at {arm_angle}° intervals")

frame = center
for i in range(ARM_COUNT):
    angle = i * arm_angle + 45  # Start at 45° for X-frame
    rotated_arm = arm.rotate((0, 0, 0), (0, 0, 1), angle)
    frame = frame.union(rotated_arm)

# ============== EXPORT ==============
step_file = OUTPUT_DIR / f"quad_frame_{WHEELBASE}mm.step"
stl_file = OUTPUT_DIR / f"quad_frame_{WHEELBASE}mm.stl"

print(f"\nExporting to:")
print(f"  STEP: {step_file}")
print(f"  STL:  {stl_file}")

cq.exporters.export(frame, str(step_file))
cq.exporters.export(frame, str(stl_file))

print(f"\n✓ Frame complete!")
print(f"  Wheelbase: {WHEELBASE}mm")
print(f"  Arms: {ARM_COUNT}x {arm_length:.1f}mm")
print(f"  Stack mount: {STACK_HOLE_SPACING}mm pattern")
print(f"  Motor mount: {MOTOR_HOLE_SPACING}mm pattern")

# ============== CQ-EDITOR VISUALIZATION ==============
# This line makes the model visible in cq-editor
# Comment out if running as standalone script
try:
    show_object(frame, name=f"Quadcopter Frame {WHEELBASE}mm")
except NameError:
    # show_object not available when running standalone
    pass
