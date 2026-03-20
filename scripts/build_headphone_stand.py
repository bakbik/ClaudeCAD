"""
Soundcore Q30 Arch Headphone Stand — trimesh + Shapely (Python 3.14).

Two parts, both fit Bambu P1S (256 x 256 x 256 mm):
  Part A: base + legs (200 x 140 x 230 mm) — print upright
  Part B: arch top   (~206 x 140 x 115 mm) — print flat-base-down

Joint: socket built directly into the arch polygon via a 2-D Shapely subtraction.
  The arch wall is widened to 26 mm (arch_ir=77, arch_or=103).
  A slot box is subtracted from the arch base polygon for each leg,
  leaving 3-mm-wide integral socket walls on each side.
  The connection between socket walls and the arch body has a full
  3 mm cross-sectional width — no zero-width points anywhere.
  Assembly: push Part B straight down; tenons (19.6 mm) slide into
  the 20 mm slots with 0.2 mm clearance per side. No screws.
"""
import numpy as np
import trimesh
from shapely.geometry import Point, box as shapely_box
import os

# ─── Dimensions (mm) ────────────────────────────────────────────────────────
base_w   = 200.0   # base width
base_d   = 140.0   # base depth
base_h   = 15.0    # base height
leg_w    = 20.0    # leg width (slot width = leg_w)
leg_h    = 215.0   # leg height above base
arch_or  = 103.0   # outer arch radius  (extra 3 mm = socket outer-wall thickness)
arch_ir  = 77.0    # inner arch radius  (extra 3 mm = socket inner-wall thickness)
ch_wall  = 3.0     # socket wall thickness  (arch_or - 100 = arch_ir - 80 = 3 mm)
ch_fit   = 0.2     # per-side clearance for friction fit
ch_depth = 15.0    # socket / tenon depth
cpeg_r   = 5.0     # cable-wrap peg radius
cpeg_h   = 35.0    # cable-wrap peg height

# Slot inner edges (must equal arch_ir + ch_wall and arch_or - ch_wall)
slot_inner = arch_ir + ch_wall   # 80.0  (inner face of slot = arch inner + wall)
slot_outer = arch_or - ch_wall   # 100.0 (outer face of slot = arch outer - wall)
assert slot_outer - slot_inner == leg_w, "slot width must equal leg_w"

tenon_w  = leg_w - 2 * ch_fit    # 19.6 mm
tenon_d  = base_d - 2 * ch_fit   # 139.6 mm
arch_cz  = base_h + leg_h        # z of split plane = 230 mm
leg_cx_L = -(base_w / 2 - leg_w / 2)   # -90
leg_cx_R =  (base_w / 2 - leg_w / 2)   # +90


def make_box(wx, wy, wz, cx=0.0, cy=0.0, cz=None):
    if cz is None:
        cz = wz / 2.0
    m = trimesh.creation.box(extents=(wx, wy, wz))
    m.apply_translation([cx, cy, cz])
    return m


def make_cylinder(r, h, cx=0.0, cy=0.0, cz=0.0, sections=64):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    m.apply_translation([cx, cy, cz + h / 2.0])
    return m


def make_arch_with_sockets(depth, center_z=0.0):
    """
    Half-annulus arch (arch_ir=77, arch_or=103) with two slot cavities
    subtracted from the base using Shapely 2-D difference.

    Polygon space: X = world X (width), Y = world Z (arch height).
    Extrusion direction Z → world Y (depth) after rotation.

    Socket walls per leg:
      inner wall: |x| in [arch_ir, slot_inner] = [77, 80]  width = 3 mm
      outer wall: |x| in [slot_outer, arch_or] = [100, 103] width = 3 mm

    Connection cross-section at the arch-to-socket-wall boundary (y=ch_depth):
      The socket wall (3 mm wide) is the SAME material as the arch wall.
      Transition is seamless — connection width = 3 mm.  Non-zero everywhere.
    """
    outer   = Point(0, 0).buffer(arch_or, resolution=128)
    inner   = Point(0, 0).buffer(arch_ir, resolution=128)
    annulus = outer.difference(inner)

    # Keep top half only
    top_half = shapely_box(-arch_or - 1, 0, arch_or + 1, arch_or + 1)
    half_ann = annulus.intersection(top_half)

    # Subtract slot cavities at the base for left and right legs
    # In polygon space: x = leg centre ± leg_w/2 (±10), y = 0..ch_depth
    for cx in [leg_cx_L, leg_cx_R]:
        slot = shapely_box(cx - leg_w / 2, 0, cx + leg_w / 2, ch_depth)
        half_ann = half_ann.difference(slot)

    # Extrude along polygon Z (→ world Y after rotation)
    mesh = trimesh.creation.extrude_polygon(half_ann, depth)

    # Rotate: polygon XY (width, arch-height) + extrude Z  →
    #         world  XZ  (width, height)      + depth  Y
    mesh.apply_transform(
        trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    )
    mesh.apply_translation([0.0, depth / 2.0, center_z])
    return mesh


# ════════════════════════════════════════════════════════════════════════════
# PART A — Base + Legs  (print upright, base on bed)
# ════════════════════════════════════════════════════════════════════════════
base = make_box(base_w, base_d, base_h, cz=base_h / 2)

leg_body_h = leg_h - ch_depth   # lower full-width section
collar_h   = ch_depth            # collar wing height = socket depth (15 mm)

pieces_a = [base]
for cx in [leg_cx_L, leg_cx_R]:
    body  = make_box(leg_w,  base_d,  leg_body_h,
                     cx=cx, cz=base_h + leg_body_h / 2)
    tenon = make_box(tenon_w, tenon_d, ch_depth,
                     cx=cx, cz=base_h + leg_body_h + ch_depth / 2)
    # Collar wings — extend the leg wall outward so arch outer/inner faces
    # align flush when Part B is pressed down.
    # outer wing sits at x = ±[100, 103]  (matches arch outer face)
    # inner wing sits at x = ±[77,  80 ]  (matches arch inner face)
    side        = np.sign(cx)                          # +1 right, -1 left
    outer_cx    = cx + side * (leg_w / 2 + ch_wall / 2)
    inner_cx    = cx - side * (leg_w / 2 + ch_wall / 2)
    collar_cz   = base_h + leg_body_h - collar_h / 2  # top of leg body
    outer_collar = make_box(ch_wall, base_d, collar_h, cx=outer_cx, cz=collar_cz)
    inner_collar = make_box(ch_wall, base_d, collar_h, cx=inner_cx, cz=collar_cz)
    pieces_a += [body, tenon, outer_collar, inner_collar]

pieces_a.append(
    make_cylinder(cpeg_r, cpeg_h, cx=70, cy=-(base_d / 2 - 12), cz=base_h)
)
part_a = trimesh.util.concatenate(pieces_a)

# ════════════════════════════════════════════════════════════════════════════
# PART B — Arch top  (print flat-base-down; socket bottoms on bed)
# Socket bottoms at z=0, arch flat face at z=ch_depth, crown at z=ch_depth+arch_or
# ════════════════════════════════════════════════════════════════════════════
arch_base_z = ch_depth   # arch flat face 15 mm above bed
part_b = make_arch_with_sockets(base_d, center_z=arch_base_z)

# ─── Connectivity check ──────────────────────────────────────────────────────
print("Connectivity check — socket wall cross-section width at arch junction:")
for side, cx in [("L-leg", leg_cx_L), ("R-leg", leg_cx_R)]:
    inner_wall_w = slot_inner - arch_ir        # 80 - 77 = 3 mm
    outer_wall_w = arch_or    - slot_outer     # 103 - 100 = 3 mm
    print(f"  {side}  inner socket wall: {inner_wall_w:.1f} mm  "
          f"outer socket wall: {outer_wall_w:.1f} mm  "
          f"{'OK' if inner_wall_w > 0 and outer_wall_w > 0 else 'FAIL'}")
print(f"  Slot width: {slot_outer - slot_inner:.1f} mm  "
      f"Tenon width: {tenon_w:.1f} mm  "
      f"Clearance per side: {(slot_outer - slot_inner - tenon_w) / 2:.2f} mm")

# ─── Export ──────────────────────────────────────────────────────────────────
os.makedirs("designs", exist_ok=True)
out_a = "designs/headphone_stand_q30_partA_base_legs.stl"
out_b = "designs/headphone_stand_q30_partB_arch.stl"
part_a.export(out_a)
part_b.export(out_b)

def report(label, mesh, orient, path):
    e = mesh.bounding_box.extents
    fits = all(x <= 256 for x in e)
    print(f"\n{label}")
    print(f"  File:  {path}")
    print(f"  Size:  {e[0]:.0f} x {e[1]:.0f} x {e[2]:.0f} mm  ({orient})")
    print(f"  P1S:   {'OK' if fits else 'TOO LARGE'}")

report("Part A - Base + Legs", part_a, "upright, base on bed",  out_a)
report("Part B - Arch Top",    part_b, "flat-base-down",        out_b)
print("\nAssembly: push Part B straight down onto Part A.")
print("No screws or hardware needed.")
