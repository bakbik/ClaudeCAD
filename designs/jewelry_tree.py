"""
Jewelry Tree Stand — Oak Tree Style
- Thick gnarly trunk with irregular taper
- Wide spreading branches forming a broad dome canopy
- Forked branch tips (sub-branches) for earrings
- Root flare buttresses at base
- 13 main branches + sub-forks across 3 tiers
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

# Trunk — gnarly irregular taper (oak-style thick trunk)
trunk_height = 140  # shorter than before — oaks are wide, not tall
# Irregular radii simulate bark knots and natural taper
trunk_sections = [
    # (height_offset, radius) — measured from tray top
    (0,   20),   # wide base
    (15,  18),   # slight narrow
    (35,  19),   # knot/bulge
    (55,  16),   # narrows
    (75,  17),   # another subtle bulge
    (95,  14),   # narrowing toward crown
    (115, 12),   # upper trunk
    (130, 11),   # near crown split
    (140, 10),   # top
]

# Branch tiers — oak canopy: wide dome, lower branches longest
# (height, count, azimuth_offset, length, base_r, tip_r, upward_angle, num_forks)
tiers = [
    (60,  4,   0, 90, 10, 5.0, 20, 2),   # Tier 1: long, thick, spread wide — big oak limbs
    (100, 5,  36, 70,  8, 4.5, 30, 1),   # Tier 2: mid-canopy
    (135, 4,  22, 55,  7, 4.0, 40, 1),   # Tier 3: upper canopy, angled up
]

# Sub-branch (fork) parameters
fork_length = 18
fork_radius = 3.5
fork_tip_radius = 2.5
fork_bulb_radius = 4.5
fork_split_angle = 30  # degrees from parent branch direction

# Main branch tip bulb
branch_bulb_radius = 6.0

# Root flare
num_roots = 5
root_length = 30
root_base_width = 14
root_tip_width = 4
root_height = 25

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
ring_positions = [
    (tray_diameter / 2 - 25, 0),
    (-(tray_diameter / 2 - 25), 0),
    (0, tray_diameter / 2 - 25),
    (0, -(tray_diameter / 2 - 25)),
]
for px, py in ring_positions:
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

# === Gnarly Oak Trunk ===
trunk_wp = cq.Workplane("XY").workplane(offset=tray_height)
trunk_wp = trunk_wp.circle(trunk_sections[0][1])
for i in range(1, len(trunk_sections)):
    h_delta = trunk_sections[i][0] - trunk_sections[i - 1][0]
    trunk_wp = trunk_wp.workplane(offset=h_delta).circle(trunk_sections[i][1])
trunk = trunk_wp.loft()

# === Root Flare / Buttresses ===
roots = cq.Workplane("XY").box(0.01, 0.01, 0.01)  # seed
for i in range(num_roots):
    azimuth = i * (360 / num_roots) + 15  # offset from branches
    # Each root is a tapered box extending from trunk base outward
    root = (
        cq.Workplane("XZ")
        .rect(root_base_width, root_height)
        .workplane(offset=root_length)
        .rect(root_tip_width, 6)
        .loft()
    )
    # Position: rotate around Z, translate to trunk base
    root = (
        root
        .rotateAboutCenter((0, 0, 1), azimuth)
        .translate((0, 0, tray_height))
    )
    roots = roots.union(root)

# === Oak Branches with Forked Tips ===
def make_oak_branch(height, azimuth_deg, length, base_r, tip_r, upward_angle, num_forks):
    """Create an oak branch with optional forked sub-branches at the tip."""
    # Main branch — 4-section loft for organic taper
    seg = length / 4
    r1 = base_r
    r2 = base_r * 0.85
    r3 = (base_r + tip_r) / 2
    r4 = tip_r

    branch = (
        cq.Workplane("XY")
        .circle(r1)
        .workplane(offset=seg)
        .circle(r2)
        .workplane(offset=seg)
        .circle(r3)
        .workplane(offset=seg * 1.2)
        .circle(r4)
        .loft()
    )

    # Bulb at main branch tip
    main_tip_z = seg * 3.2  # total length of loft
    bulb = (
        cq.Workplane("XY")
        .workplane(offset=main_tip_z)
        .sphere(branch_bulb_radius)
    )
    branch = branch.union(bulb)

    # Add forked sub-branches at the tip
    for f in range(num_forks):
        # Alternate fork direction: left/right of branch axis
        fork_azimuth = (f * 120) + 60  # spread forks around the branch tip
        fork_elevation = fork_split_angle

        fork = (
            cq.Workplane("XY")
            .circle(fork_radius)
            .workplane(offset=fork_length)
            .circle(fork_tip_radius)
            .loft()
        )
        fork_bulb = (
            cq.Workplane("XY")
            .workplane(offset=fork_length)
            .sphere(fork_bulb_radius)
        )
        fork = fork.union(fork_bulb)

        # Rotate fork outward from parent branch direction
        fork = (
            fork
            .rotateAboutCenter((0, 1, 0), -fork_elevation)
            .rotateAboutCenter((0, 0, 1), fork_azimuth)
            .translate((0, 0, main_tip_z - 5))  # attach near tip
        )
        branch = branch.union(fork)

    # Rotate entire branch assembly into world position
    branch = (
        branch
        .rotateAboutCenter((0, 1, 0), -(90 - upward_angle))
        .rotateAboutCenter((0, 0, 1), azimuth_deg)
        .translate((0, 0, tray_height + height))
    )
    return branch


# Build all branches
branches = cq.Workplane("XY").box(0.01, 0.01, 0.01)  # seed

for tier_h, count, az_offset, length, base_r, tip_r, angle, forks in tiers:
    for i in range(count):
        azimuth = az_offset + i * (360 / count)
        b = make_oak_branch(tier_h, azimuth, length, base_r, tip_r, angle, forks)
        branches = branches.union(b)

# === Crown Top — small upward branch cluster instead of single bulb ===
crown_branches = cq.Workplane("XY").box(0.01, 0.01, 0.01)
crown_height = trunk_height - 5  # just below trunk top
for i in range(3):
    az = i * 120 + 10
    cb = make_oak_branch(crown_height, az, 35, 6, 3.5, 55, 0)  # short, steep, no forks
    crown_branches = crown_branches.union(cb)

# === Combine Everything ===
result = tray_result.union(trunk).union(roots).union(branches).union(crown_branches)
