#!/usr/bin/env python3
"""
generate_draft.py — Generate a dimensioned 2D orthographic sketch PNG from a JSON spec.

Usage:
    python generate_draft.py '<json_spec>' --output designs/draft.png

JSON spec format:
{
  "name": "Phone Case",
  "views": ["front", "top", "side"],
  "dimensions": {"width": 75, "height": 160, "depth": 12},
  "features": [
    {"type": "hole",   "label": "Camera cutout", "position": [60, 20], "size": [30, 30]},
    {"type": "slot",   "label": "USB-C port",    "position": [37, 158], "size": [10, 4]},
    {"type": "fillet", "label": "Corner R3mm"}
  ],
  "notes": ["Wall thickness: 1.5mm", "Material: PLA"]
}
"""

import sys
import json
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch


# --- Drawing style constants ---
BG_COLOR = "#1a1a2e"
LINE_COLOR = "#e0e0e0"
DIM_COLOR = "#f0c040"
FEATURE_COLOR = "#4fc3f7"
FILLET_COLOR = "#aed581"
NOTE_COLOR = "#b0bec5"
TITLE_COLOR = "#ffffff"
FACE_COLOR = "#2a2a4a"
FACE_ALPHA = 0.8


def _draw_dim_arrow(ax, x1, y1, x2, y2, label, offset=0.06, fontsize=7):
    """Draw a dimension arrow with a centered label."""
    ax.annotate(
        "",
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="<->", color=DIM_COLOR, lw=0.8),
    )
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mx, my + offset, label, color=DIM_COLOR, fontsize=fontsize,
            ha="center", va="bottom", fontfamily="monospace")


def _draw_view(ax, view_name: str, dims: dict, features: list, scale: float):
    """Draw one orthographic view."""
    w = dims.get("width", 50)
    h = dims.get("height", 50)
    d = dims.get("depth", 20)

    if view_name == "front":
        vw, vh, xlabel, ylabel = w, h, "width", "height"
    elif view_name == "top":
        vw, vh, xlabel, ylabel = w, d, "width", "depth"
    else:  # side
        vw, vh, xlabel, ylabel = d, h, "depth", "height"

    margin = max(vw, vh) * 0.25
    ax.set_xlim(-margin, vw + margin)
    ax.set_ylim(-margin, vh + margin)
    ax.set_aspect("equal")
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for spine in ax.spines.values():
        spine.set_edgecolor("#404060")

    # Main body rectangle
    rect = mpatches.FancyBboxPatch(
        (0, 0), vw, vh,
        boxstyle="round,pad=0",
        linewidth=1.2, edgecolor=LINE_COLOR,
        facecolor=FACE_COLOR, alpha=FACE_ALPHA,
        zorder=2,
    )
    ax.add_patch(rect)

    # Draw features
    for feat in features:
        ftype = feat.get("type", "").lower()
        label = feat.get("label", "")
        pos = feat.get("position", None)
        size = feat.get("size", None)

        if ftype in ("hole", "cutout", "slot") and pos and size and view_name == "front":
            fx, fy = pos[0] * vw / w, pos[1] * vh / h
            fw = size[0] * vw / w
            fh = size[1] * vh / h
            color = FEATURE_COLOR
            frect = mpatches.Rectangle(
                (fx - fw / 2, fy - fh / 2), fw, fh,
                linewidth=0.8, edgecolor=color, facecolor=BG_COLOR,
                linestyle="--", zorder=3,
            )
            ax.add_patch(frect)
            ax.text(fx, fy, label, color=color, fontsize=5.5,
                    ha="center", va="center", fontfamily="monospace", zorder=4)

        elif ftype == "fillet" and view_name == "front":
            ax.text(vw * 0.08, vh * 0.08, f"⌒ {label}", color=FILLET_COLOR,
                    fontsize=5.5, ha="left", va="bottom", fontfamily="monospace", zorder=4)

    # Dimension arrows
    dim_offset = max(vw, vh) * 0.08
    _draw_dim_arrow(ax, 0, -dim_offset, vw, -dim_offset,
                    f"{vw:.1f}mm ({xlabel})", offset=dim_offset * 0.3)
    _draw_dim_arrow(ax, -dim_offset, 0, -dim_offset, vh,
                    f"{vh:.1f}mm\n({ylabel})", offset=0)

    # View label
    ax.set_title(view_name.upper(), color=TITLE_COLOR, fontsize=8,
                 fontfamily="monospace", pad=4)


def generate_draft(spec: dict, output_path: str):
    name = spec.get("name", "Design Draft")
    views = spec.get("views", ["front", "top", "side"])
    dims = spec.get("dimensions", {"width": 50, "height": 50, "depth": 20})
    features = spec.get("features", [])
    notes = spec.get("notes", [])

    n_views = len(views)
    fig_w = 4 * n_views
    fig_h = 5.5

    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=BG_COLOR)
    fig.suptitle(name, color=TITLE_COLOR, fontsize=11,
                 fontfamily="monospace", y=0.97, fontweight="bold")

    max_dim = max(dims.get("width", 50), dims.get("height", 50), dims.get("depth", 20))
    scale = 1.0  # normalized; actual mm values shown as annotations

    axes = []
    for i, view_name in enumerate(views):
        ax = fig.add_subplot(1, n_views, i + 1)
        _draw_view(ax, view_name, dims, features, scale)
        axes.append(ax)

    # Notes section
    if notes:
        notes_text = "  |  ".join(notes)
        fig.text(0.5, 0.02, notes_text, color=NOTE_COLOR, fontsize=6.5,
                 ha="center", va="bottom", fontfamily="monospace",
                 style="italic")

    plt.tight_layout(rect=[0, 0.05, 1, 0.94])

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"Draft saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", help="JSON spec string")
    parser.add_argument("--output", default="designs/draft.png", help="Output PNG path")
    args = parser.parse_args()

    try:
        spec = json.loads(args.spec)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON spec: {e}", file=sys.stderr)
        sys.exit(1)

    generate_draft(spec, args.output)
