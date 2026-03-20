"""
Quick visual sketch of the arch headphone stand design.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Arc, FancyArrowPatch
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(12, 7), facecolor="#1a1a2e")
fig.suptitle("Soundcore Q30 — Arch Headphone Stand", color="white", fontsize=14,
             fontfamily="monospace", fontweight="bold", y=0.97)

# ── FRONT VIEW ──────────────────────────────────────────────────────────────
ax = axes[0]
ax.set_facecolor("#1a1a2e")
ax.set_xlim(-30, 230)
ax.set_ylim(-30, 290)
ax.set_aspect("equal")
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
for sp in ax.spines.values():
    sp.set_edgecolor("#404060")
ax.set_title("FRONT VIEW", color="white", fontsize=9, fontfamily="monospace")

# Base
base = mpatches.FancyBboxPatch((0, 0), 200, 15,
    boxstyle="round,pad=1", linewidth=1.5,
    edgecolor="#e0e0e0", facecolor="#2a2a4a")
ax.add_patch(base)

# Left leg
left_leg = mpatches.Rectangle((0, 15), 20, 215,
    linewidth=1.5, edgecolor="#e0e0e0", facecolor="#2a2a4a")
ax.add_patch(left_leg)

# Right leg
right_leg = mpatches.Rectangle((180, 15), 20, 215,
    linewidth=1.5, edgecolor="#e0e0e0", facecolor="#2a2a4a")
ax.add_patch(right_leg)

# Arch top (semicircle)
arch_center_x = 100
arch_center_y = 230
arch_radius = 100  # outer
arch_inner_radius = 80

theta = np.linspace(0, np.pi, 100)
# Outer arch
ox = arch_center_x + arch_radius * np.cos(theta)
oy = arch_center_y + arch_radius * np.sin(theta)
# Inner arch
ix = arch_center_x + arch_inner_radius * np.cos(theta[::-1])
iy = arch_center_y + arch_inner_radius * np.sin(theta[::-1])

arch_x = np.concatenate([ox, ix])
arch_y = np.concatenate([oy, iy])
ax.fill(arch_x, arch_y, facecolor="#2a2a4a", edgecolor="#e0e0e0", linewidth=1.5, zorder=3)

# Cable wrap peg on right side of base
peg = mpatches.FancyBboxPatch((185, 15), 10, 35,
    boxstyle="round,pad=1", linewidth=1, linestyle="--",
    edgecolor="#4fc3f7", facecolor="#1a2a3a")
ax.add_patch(peg)
ax.text(215, 33, "cable\nwrap peg", color="#4fc3f7", fontsize=6.5,
        fontfamily="monospace", ha="left", va="center")

# Foot recesses (4 circles)
for fx, fy in [(12, 7), (188, 7)]:
    foot = plt.Circle((fx, fy), 5, linewidth=1, linestyle="--",
                       edgecolor="#aed581", facecolor="#1a1a2e")
    ax.add_patch(foot)
ax.text(100, 3, "rubber foot recesses ×4", color="#aed581",
        fontsize=6, fontfamily="monospace", ha="center", va="center")

# Headphones ghost (to show fit)
hband_x = [60, 60, 65, 135, 140, 140]
hband_y = [195, 230, 240, 240, 230, 195]
ax.plot(hband_x, hband_y, color="#f0c040", linewidth=1.5, linestyle=":", alpha=0.6, zorder=5)
# Ear cups
left_cup = plt.Circle((58, 185), 22, linewidth=1, linestyle=":",
                        edgecolor="#f0c040", facecolor="none", alpha=0.5)
right_cup = plt.Circle((142, 185), 22, linewidth=1, linestyle=":",
                         edgecolor="#f0c040", facecolor="none", alpha=0.5)
ax.add_patch(left_cup)
ax.add_patch(right_cup)
ax.text(100, 155, "Q30 (ghost)", color="#f0c040", fontsize=6,
        fontfamily="monospace", ha="center", alpha=0.7)

# Dimension arrows
def arrow(ax, x1, y1, x2, y2, label, lx=None, ly=None, color="#f0c040"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="<->", color=color, lw=0.9))
    lx = lx if lx is not None else (x1+x2)/2
    ly = ly if ly is not None else (y1+y2)/2
    ax.text(lx, ly, label, color=color, fontsize=6.5, ha="center",
            va="center", fontfamily="monospace",
            bbox=dict(facecolor="#1a1a2e", edgecolor="none", pad=1))

arrow(ax, 0, -18, 200, -18, "200mm", ly=-18)
arrow(ax, -18, 0, -18, 15, "15mm", lx=-25)
arrow(ax, -18, 15, -18, 260, "245mm (arch height)", lx=-25)
arrow(ax, 20, 230, 180, 230, "160mm inner width", ly=225)

ax.set_xlim(-50, 250)

# ── SIDE VIEW ───────────────────────────────────────────────────────────────
ax2 = axes[1]
ax2.set_facecolor("#1a1a2e")
ax2.set_aspect("equal")
ax2.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
for sp in ax2.spines.values():
    sp.set_edgecolor("#404060")
ax2.set_title("SIDE VIEW", color="white", fontsize=9, fontfamily="monospace")

# Base side
base2 = mpatches.FancyBboxPatch((0, 0), 140, 15,
    boxstyle="round,pad=1", linewidth=1.5,
    edgecolor="#e0e0e0", facecolor="#2a2a4a")
ax2.add_patch(base2)

# Arch leg (side: just a vertical bar from base)
leg2 = mpatches.Rectangle((60, 15), 20, 215,
    linewidth=1.5, edgecolor="#e0e0e0", facecolor="#2a2a4a")
ax2.add_patch(leg2)

# Arch top side profile (a ring/tube cross-section)
arch_top = plt.Circle((70, 230), 20, linewidth=1.5,
                        edgecolor="#e0e0e0", facecolor="#2a2a4a")
arch_inner = plt.Circle((70, 230), 10, linewidth=1,
                          edgecolor="#4fc3f7", facecolor="#1a1a2e", linestyle="--")
ax2.add_patch(arch_top)
ax2.add_patch(arch_inner)
ax2.text(100, 230, "Ø20mm\ntube", color="#4fc3f7", fontsize=6.5,
         fontfamily="monospace", ha="left", va="center")

# Cable peg side
peg2 = mpatches.FancyBboxPatch((120, 15), 8, 35,
    boxstyle="round,pad=0.5", linewidth=1, linestyle="--",
    edgecolor="#4fc3f7", facecolor="#1a2a3a")
ax2.add_patch(peg2)

arrow(ax2, 0, -18, 140, -18, "140mm depth", ly=-18)
arrow(ax2, -18, 0, -18, 260, "260mm total height", lx=-30)
arrow(ax2, 0, 7, 60, 7, "60mm", ly=3)

ax2.set_xlim(-50, 170)
ax2.set_ylim(-30, 290)

# Notes
notes = "Arch inner clearance: 160×180mm  |  Wall: 3mm  |  No supports needed  |  PLA / Bambu P1S"
fig.text(0.5, 0.01, notes, color="#b0bec5", fontsize=7,
         ha="center", fontfamily="monospace", style="italic")

plt.tight_layout(rect=[0, 0.04, 1, 0.95])
fig.savefig("designs/headphone_stand_sketch.png", dpi=150,
            bbox_inches="tight", facecolor="#1a1a2e")
print("Saved: designs/headphone_stand_sketch.png")
