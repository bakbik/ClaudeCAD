"""
Jewelry Tree Stand — Realistic Tree Shape
- Organic silhouette: longer lower branches, shorter upper ones
- Curved branches with upward sweep
- Multi-section tapered trunk
- 12 branches across 4 tiers for necklaces/earrings
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

# Trunk — organic multi-section taper
trunk_height = 190
trunk_radii = [18, 15, 12, 10, 8]  # radii at 5 evenly-spaced sections
trunk_section_height = trunk_height / (len(trunk_radii) - 1)

# Branch tiers — each tier: (height, count, azimuth_offset, length, base_radius, tip_radius, bulb_radius, angle)
# Lower tiers: longer, thicker, more horizontal (tree-like silhouette)
# Upper tiers: shorter, thinner, more upward
tiers = [
    # height, count, azimuth_offset, length, base_r, tip_r, bulb_r, upward_angle
    (55,  3,   0, 95, 9, 5.5, 7.5, 25),   # Tier 1: long, thick, spread wide
    (95,  3,  40, 80, 8, 5.0, 7.0, 30),   # Tier 2: medium-long
    (135, 3,  20, 65, 7, 4.5, 6.5, 35),   # Tier 3: medium
    (170, 3,  60, 50, 6, 4.0, 6.0, 42),   # Tier 4: short, thin, angled up
]

# Tree top
top_bulb_radius = 10

# === Base Tray ===
tray = (
    cq.Workplane("XY")
    .circle(tray_diameter / 2)
    .extrude(tray_height)
    .edges("<Z")
    .chamfer(tray_chamfer)
)

tray_inner = (
    cq.Workplane("XY")
    .workplane(offset=tray_height - tray_inner_depth)
    .circle(tray_diameter / 2 - tray_wall)
    .extrude(tray_inner_depth + 1)
)

tray_lip = (
    cq.Workplane("XY")
    .circle(tray_diameter / 2)
    .circle(tray_diameter / 2 - tray_wall)
    .extrude(tray_lip_height)
    .edges(">Z")
    .fillet(1.0)
)

tray_result = tray.union(tray_lip).cut(tray_inner)

# Ring holder bumps
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

# === Organic Trunk ===
# Multi-section loft with varying radii for natural taper
trunk_wp = cq.Workplane("XY").workplane(offset=tray_height)
trunk_wp = trunk_wp.circle(trunk_radii[0])
for i in range(1, len(trunk_radii)):
    trunk_wp = trunk_wp.workplane(offset=trunk_section_height).circle(trunk_radii[i])
trunk = trunk_wp.loft()

# === Curved Branches ===
def make_curved_branch(height, azimuth_deg, length, base_r, tip_r, bulb_r, upward_angle):
    """Create a branch with a gentle upward curve using 3-section loft."""
    # Build the branch along +Z, then rotate into position
    # Use 3 cross-sections to create a subtle curve
    seg = length / 3
    mid_r = (base_r + tip_r) / 2

    branch = (
        cq.Workplane("XY")
        .circle(base_r)
        .workplane(offset=seg)
        .circle(mid_r)
        .workplane(offset=seg)
        .circle(tip_r * 1.1)
        .workplane(offset=seg)
        .circle(tip_r)
        .loft()
    )

    # Bulb at tip
    bulb = (
        cq.Workplane("XY")
        .workplane(offset=length)
        .sphere(bulb_r)
    )
    branch = branch.union(bulb)

    # Rotate: tilt from vertical to the desired upward angle from horizontal
    # (90 - upward_angle) gives the tilt from vertical
    branch = (
        branch
        .rotateAboutCenter((0, 1, 0), -(90 - upward_angle))
        .rotateAboutCenter((0, 0, 1), azimuth_deg)
        .translate((0, 0, tray_height + height))
    )
    return branch


# Build all branches
branches = cq.Workplane("XY").box(0.01, 0.01, 0.01)  # seed object

for tier_h, count, az_offset, length, base_r, tip_r, bulb_r, angle in tiers:
    for i in range(count):
        azimuth = az_offset + i * (360 / count)
        b = make_curved_branch(tier_h, azimuth, length, base_r, tip_r, bulb_r, angle)
        branches = branches.union(b)

# === Tree Top ===
top = (
    cq.Workplane("XY")
    .workplane(offset=tray_height + trunk_height)
    .sphere(top_bulb_radius)
)

# === Combine Everything ===
result = tray_result.union(trunk).union(branches).union(top)
