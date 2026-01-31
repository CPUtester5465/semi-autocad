#!/usr/bin/env python3
"""
Simple Assembly Viewer for cq-editor
====================================
Self-contained script - no imports needed.
"""

import cadquery as cq
import math

# ============== CONFIGURATION ==============
WHEELBASE = 220        # mm
FC_MOUNT = 30.5        # mm
MOTOR_MOUNT = 16.0     # mm
ARM_LENGTH = WHEELBASE / 2 * 0.707  # ~77.8mm

# ============== FLIGHT CONTROLLER ==============
fc = (
    cq.Workplane("XY")
    .box(36, 36, 4)
    .edges("|Z").fillet(3)
    .faces(">Z").workplane()
    .rect(FC_MOUNT, FC_MOUNT, forConstruction=True)
    .vertices().hole(3.2)
)

# ============== ESC ==============
esc = (
    cq.Workplane("XY")
    .box(36, 36, 6)
    .edges("|Z").fillet(3)
    .faces(">Z").workplane()
    .rect(FC_MOUNT, FC_MOUNT, forConstruction=True)
    .vertices().hole(3.2)
    .translate((0, 0, -12))  # Below FC
)

# ============== MOTOR ==============
def make_motor():
    base = cq.Workplane("XY").cylinder(2, 11)
    stator = cq.Workplane("XY").workplane(offset=2).cylinder(7, 11)
    bell = cq.Workplane("XY").workplane(offset=7).cylinder(8, 13.5)
    shaft = cq.Workplane("XY").workplane(offset=13).cylinder(4, 2.5)
    motor = base.union(stator).union(bell).union(shaft)
    # Add mount holes
    motor = (
        motor.faces("<Z").workplane()
        .rect(MOTOR_MOUNT, MOTOR_MOUNT, forConstruction=True)
        .vertices().hole(3.2)
    )
    return motor

# ============== PROPELLER (clearance disc) ==============
prop = cq.Workplane("XY").cylinder(1, 63.5).faces(">Z").workplane().hole(8)

# ============== BATTERY ==============
battery = (
    cq.Workplane("XY")
    .box(35, 75, 30)
    .edges("|Z").fillet(2)
    .translate((0, 0, 20))  # On top
)

# ============== FRAME ==============
center_size = 42
arm_width = 12
arm_thickness = 4

# Center plate
frame = (
    cq.Workplane("XY")
    .box(center_size, center_size, arm_thickness)
    .edges("|Z").fillet(3)
    .faces(">Z").workplane()
    .rect(FC_MOUNT, FC_MOUNT, forConstruction=True)
    .vertices().hole(3.2)
    .translate((0, 0, -6))  # At motor base level
)

# Add arms and motor mounts
for i in range(4):
    angle = 45 + i * 90
    rad = math.radians(angle)

    # Motor position
    mx = ARM_LENGTH * math.cos(rad)
    my = ARM_LENGTH * math.sin(rad)

    # Arm
    arm_len = ARM_LENGTH - center_size/2 * 0.707
    arm = (
        cq.Workplane("XY")
        .box(arm_len, arm_width, arm_thickness)
        .translate((arm_len/2 + center_size/2 * 0.707, 0, 0))
        .rotate((0,0,0), (0,0,1), angle)
        .translate((0, 0, -6))
    )

    # Motor mount pad
    mount = (
        cq.Workplane("XY")
        .cylinder(arm_thickness, MOTOR_MOUNT/2 + 6)
        .translate((mx, my, -6))
        .faces(">Z").workplane()
        .center(mx, my)
        .rect(MOTOR_MOUNT, MOTOR_MOUNT, forConstruction=True)
        .vertices().hole(3.2)
        .faces(">Z").workplane()
        .center(mx, my)
        .hole(8)
    )

    frame = frame.union(arm).union(mount)

# ============== POSITION MOTORS & PROPS ==============
motors = []
props = []
for i in range(4):
    angle = 45 + i * 90
    rad = math.radians(angle)
    mx = ARM_LENGTH * math.cos(rad)
    my = ARM_LENGTH * math.sin(rad)

    m = make_motor().translate((mx, my, -4))
    motors.append(m)

    p = prop.translate((mx, my, 18))
    props.append(p)

# ============== SHOW IN CQ-EDITOR ==============
show_object(frame, name="Frame", options={"color": "gold", "alpha": 0.9})
show_object(fc, name="Flight Controller", options={"color": "green", "alpha": 0.8})
show_object(esc, name="ESC", options={"color": "blue", "alpha": 0.8})
show_object(battery, name="Battery", options={"color": "orange", "alpha": 0.7})

for i, m in enumerate(motors):
    show_object(m, name=f"Motor_{i+1}", options={"color": "gray", "alpha": 0.9})

for i, p in enumerate(props):
    show_object(p, name=f"Prop_{i+1}", options={"color": "red", "alpha": 0.3})
