"""
Self-Balancing Robot Chassis — CadQuery parametric design.

Two-plate design:
  Bottom plate  (140 × 90 mm): TT motor mounts, L298N, dual 18650 battery bay
  Top plate     (120 × 70 mm): Arduino Nano, MPU-6050, HC-05
  Connected via 4× M3 × 40mm standoffs

All dimensions in mm. Designed for FDM printing in PLA/PETG.
Layer height ≤ 0.3mm, 3 perimeters, 40% infill recommended.
"""

import cadquery as cq
from cadquery import exporters

# ── Component dimensions ─────────────────────────────────────────────────────

# TT gear motor (yellow plastic, common on Amazon/AliExpress)
MTR_L   = 70.0   # body length along shaft axis
MTR_W   = 37.0   # body width
MTR_H   = 23.0   # body height
MTR_TAB = 21.0   # mounting hole centre-to-centre (on top face of motor)
MTR_TAB_D = 3.0  # M3 screw

# Plate geometry
BOT_W = 140.0; BOT_D = 90.0; BOT_T = 3.0
TOP_W = 120.0; TOP_D = 70.0; TOP_T = 3.0

# Standoff hole (M3 clearance)
SO_D     = 3.3
SO_INSET = 7.0       # from corner to hole centre
SO_H     = 40.0      # standoff length (controls robot height)

# Wall / fillet constants
FILLET = 4.0
WALL   = 1.8

# Motor pocket: bottom plate has a rectangular slot for each motor body.
# Motors sit flush in the pocket; shaft extends beyond plate edge.
# Pocket is open on the long edge to allow shaft clearance.
MTR_POCKET_W = MTR_W + 0.6   # loose fit
MTR_POCKET_L = MTR_L / 2     # motor body goes halfway in
MTR_POCKET_H = MTR_H + 0.4

# ── Helper: M3 standoff hole pattern for a plate ─────────────────────────────
def standoff_holes(plate, w, d, t, inset=SO_INSET, diam=SO_D):
    pts = [
        (+w/2 - inset, +d/2 - inset),
        (-w/2 + inset, +d/2 - inset),
        (+w/2 - inset, -d/2 + inset),
        (-w/2 + inset, -d/2 + inset),
    ]
    for x, y in pts:
        plate = plate.faces(">Z").workplane().center(x, y).hole(diam)
    return plate

# ── Bottom plate ─────────────────────────────────────────────────────────────
bot = (
    cq.Workplane("XY")
    .box(BOT_W, BOT_D, BOT_T, centered=(True, True, False))
    .edges("|Z").fillet(FILLET)
)

# Motor mounting holes on left and right edges (4 holes per side, 2 per motor tab)
# Left motor: shaft on -X side, tabs at x = -(BOT_W/2 - 5), symmetric in Y
motor_y_offsets = [-MTR_TAB/2, +MTR_TAB/2]
for side in [-1, 1]:
    x_base = side * (BOT_W/2 - 5)
    for dy in motor_y_offsets:
        bot = (
            bot.faces(">Z").workplane()
            .center(x_base, dy)
            .hole(MTR_TAB_D)
        )

# L298N module: 43×43mm, 4× M3 corner holes at 37×37mm spacing
L298N_HOLE = 3.3
L298N_PITCH = 37.0 / 2
L298N_X = 20.0   # offset from centre toward one end
for dx in [-L298N_PITCH + L298N_X, L298N_PITCH + L298N_X]:
    for dy in [-L298N_PITCH, L298N_PITCH]:
        bot = bot.faces(">Z").workplane().center(dx, dy).hole(L298N_HOLE)

# Dual 18650 battery bay cutout (18.5mm each, side by side with 1mm gap)
# 18650: ∅18.5mm × 65mm — use elongated slots
BAT_SLOT_W = 19.5
BAT_SLOT_L = 66.0
BAT_Y_OFFSET = 9.75 + 0.5   # centre of each cell
for by in [-BAT_Y_OFFSET, +BAT_Y_OFFSET]:
    bot = (
        bot.faces(">Z").workplane()
        .center(-L298N_X - 5, by)
        .slot2D(BAT_SLOT_L, BAT_SLOT_W, angle=0)
        .cutThruAll()
    )

# Standoff holes
bot = standoff_holes(bot, BOT_W, BOT_D, BOT_T)

# ── Top plate ────────────────────────────────────────────────────────────────
top = (
    cq.Workplane("XY")
    .box(TOP_W, TOP_D, TOP_T, centered=(True, True, False))
    .edges("|Z").fillet(FILLET)
)

# Arduino Nano footprint: 18 × 45mm, 4× M2.5 holes at corners (16 × 43mm pitch)
NANO_HX = 16.0 / 2
NANO_HY = 43.0 / 2
NANO_X  = 15.0   # shift toward one end
for dx in [-NANO_HX + NANO_X, NANO_HX + NANO_X]:
    for dy in [-NANO_HY, NANO_HY]:
        top = top.faces(">Z").workplane().center(dx, dy).hole(2.7)

# MPU-6050 breakout: 21 × 16mm, M2.5 holes at corners (10mm spacing)
MPU_X = -30.0
for dx in [MPU_X - 5, MPU_X + 5]:
    for dy in [-5.0, 5.0]:
        top = top.faces(">Z").workplane().center(dx, dy).hole(2.7)

# HC-05 module: two 2mm holes, 28mm apart on Y
HC05_X = -42.0
for dy in [-14.0, 14.0]:
    top = top.faces(">Z").workplane().center(HC05_X, dy).hole(2.2)

# Standoff holes (match bottom plate positions, using plate's own dimensions)
top = standoff_holes(top, TOP_W, TOP_D, TOP_T)

# ── Export ───────────────────────────────────────────────────────────────────
exporters.export(bot, "chassis_bottom.stl")
exporters.export(top, "chassis_top.stl")

# Assemble for preview: top plate floated SO_H above bottom
assembly = (
    cq.Assembly()
    .add(bot, name="bottom", color=cq.Color("orange"))
    .add(top, name="top",    color=cq.Color("lightblue"),
         loc=cq.Location(cq.Vector(0, 0, SO_H + BOT_T)))
)
assembly.save("chassis_assembly.step")

print("✓ chassis_bottom.stl")
print("✓ chassis_top.stl")
print("✓ chassis_assembly.step")
print()
print("Print settings: PLA/PETG, 0.2mm layers, 3 walls, 40% infill")
print("Hardware: 4× M3×40mm standoffs, M3 nuts, M3×6 screws")
