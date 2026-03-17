"""
Jewelry Tree Stand
- Large size: ~160mm tray, ~230mm tall
- 8 branches at varying heights for necklaces/earrings
- Wide tray base for bracelets and rings
- FDM-optimized for PLA on Bambu P1S (256x256x256mm)
"""
import cadquery as cq
import math

# === Parameters ===
# Base tray
tray_diameter = 160
tray_height = 8
tray_wall = 3.0
tray_lip_height = 12
tray_inner_depth = 6
tray_chamfer = 1.0

# Trunk
trunk_base_radius = 16
trunk_top_radius = 10
trunk_height = 200
trunk_segments = 36

# Branches (8 total, in 3 tiers)
branch_length = 80
branch_radius = 8
branch_tip_radius = 5
branch_tip_bulb = 7.0  # knob at end to hold jewelry
branch_upward_angle = 35  # degrees from horizontal (FDM safe, well under 45° overhang)

# Tier heights (from base of trunk)
tier_1_height = 80   # 2 branches
tier_2_height = 130  # 3 branches
tier_3_height = 175  # 3 branches

# Tree top
top_bulb_radius = 12

# === Base Tray ===
# Outer tray shell
tray = (
    cq.Workplane("XY")
    .circle(tray_diameter / 2)
    .extrude(tray_height)
    .edges("<Z")
    .chamfer(tray_chamfer)
)

# Hollow out the tray interior (ring/bracelet dish)
tray_inner = (
    cq.Workplane("XY")
    .workplane(offset=tray_height - tray_inner_depth)
    .circle(tray_diameter / 2 - tray_wall)
    .extrude(tray_inner_depth + 1)
)

# Tray lip
tray_lip = (
    cq.Workplane("XY")
    .circle(tray_diameter / 2)
    .circle(tray_diameter / 2 - tray_wall)
    .extrude(tray_lip_height)
    .edges(">Z")
    .fillet(1.0)
)

tray_result = tray.union(tray_lip).cut(tray_inner)

# Ring holder bumps inside the tray (short cylinders to drape rings over)
ring_holder_positions = [
    (tray_diameter / 2 - 25, 0),
    (-(tray_diameter / 2 - 25), 0),
    (0, tray_diameter / 2 - 25),
    (0, -(tray_diameter / 2 - 25)),
]

for px, py in ring_holder_positions:
    bump = (
        cq.Workplane("XY")
        .workplane(offset=tray_height - tray_inner_depth)
        .center(px, py)
        .circle(4)
        .extrude(8)
        .edges(">Z")
        .fillet(2.5)
    )
    tray_result = tray_result.union(bump)

# === Trunk ===
# Tapered trunk using a loft between two circles
trunk = (
    cq.Workplane("XY")
    .workplane(offset=tray_height)
    .circle(trunk_base_radius)
    .workplane(offset=trunk_height)
    .circle(trunk_top_radius)
    .loft()
)

# === Branches ===
def make_branch(height, angle_deg, azimuth_deg, length, radius):
    """Create a single branch angled upward from the trunk."""
    # Branch as a tapered cylinder pointing in +X, then rotated
    branch = (
        cq.Workplane("XY")
        .circle(radius)
        .workplane(offset=length)
        .circle(branch_tip_radius)
        .loft()
    )
    # Bulb at tip to prevent jewelry from sliding off
    bulb = (
        cq.Workplane("XY")
        .workplane(offset=length)
        .sphere(branch_tip_bulb)
    )
    branch = branch.union(bulb)

    # Rotate to point outward and upward
    branch = (
        branch
        .rotateAboutCenter((0, 1, 0), -(90 - branch_upward_angle))
        .rotateAboutCenter((0, 0, 1), azimuth_deg)
        .translate((0, 0, tray_height + height))
    )
    return branch

# Define branch positions: (height, azimuth_angle)
branches_config = [
    # Tier 1: 2 branches, opposite sides
    (tier_1_height, 0),
    (tier_1_height, 180),
    # Tier 2: 3 branches, evenly spaced offset from tier 1
    (tier_2_height, 60),
    (tier_2_height, 180),
    (tier_2_height, 300),
    # Tier 3: 3 branches, offset from tier 2
    (tier_3_height, 30),
    (tier_3_height, 150),
    (tier_3_height, 270),
]

branches = cq.Workplane("XY").box(0.01, 0.01, 0.01)  # seed object for union
for height, azimuth in branches_config:
    b = make_branch(height, branch_upward_angle, azimuth, branch_length, branch_radius)
    branches = branches.union(b)

# === Tree Top ===
top = (
    cq.Workplane("XY")
    .workplane(offset=tray_height + trunk_height)
    .sphere(top_bulb_radius)
)

# === Combine Everything ===
result = tray_result.union(trunk).union(branches).union(top)
