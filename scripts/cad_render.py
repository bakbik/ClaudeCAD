#!/usr/bin/env python3
"""
CadQuery render and export script for ClaudeCAD.

Usage:
    python3 scripts/cad_render.py designs/my_part.py [--no-preview] [--format stl|step|both]

Executes a CadQuery script, exports STL/STEP, and generates a multi-view PNG preview.
The script must define a variable called `result` containing the CadQuery Workplane or Shape.
"""

import argparse
import importlib.util
import math
import os
import struct
import sys


def load_cad_script(script_path: str):
    """Load and execute a CadQuery script, returning the `result` object."""
    spec = importlib.util.spec_from_file_location("cad_script", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "result"):
        print("Error: Script must define a 'result' variable with the CadQuery object.")
        sys.exit(1)

    return module.result


def export_stl(result, output_path: str):
    """Export CadQuery result to STL."""
    import cadquery as cq
    cq.exporters.export(result, output_path, exportType="STL")
    print(f"STL exported: {output_path}")


def export_step(result, output_path: str):
    """Export CadQuery result to STEP."""
    import cadquery as cq
    cq.exporters.export(result, output_path, exportType="STEP")
    print(f"STEP exported: {output_path}")


def export_svg_view(result, output_path: str, direction: tuple, label: str, width=800, height=800):
    """Export a single SVG view of the CadQuery result."""
    import cadquery as cq
    cq.exporters.export(
        result,
        output_path,
        exportType="SVG",
        opt={
            "projectionDir": direction,
            "showAxes": False,
            "marginLeft": 10,
            "marginTop": 10,
            "showHidden": False,
            "strokeColor": (30, 30, 30),
            "hiddenColor": (200, 200, 200),
            "width": width,
            "height": height,
        },
    )


def svg_to_png(svg_path: str, png_path: str, width=800, height=800):
    """Convert SVG to PNG using cairosvg if available."""
    try:
        import cairosvg
        cairosvg.svg2png(
            url=svg_path,
            write_to=png_path,
            output_width=width,
            output_height=height,
        )
        return True
    except ImportError:
        return False


def generate_preview(result, base_path: str):
    """Generate multi-view SVG previews and PNG conversions."""
    # CadQuery SVG exporter: projectionDir is the camera look-at direction.
    # The exporter flips Z in the 2D projection, so use negative Z
    # components to get an upright view.
    views = {
        "front": (0, -1, 0.01),
        "top": (0, 0, -1),
        "right": (-1, 0, 0.01),
        "iso": (-1, -1.2, 0.5),
    }

    svg_paths = []
    png_paths = []
    for name, direction in views.items():
        svg_path = f"{base_path}_{name}.svg"
        export_svg_view(result, svg_path, direction, name)
        svg_paths.append(svg_path)
        print(f"SVG preview ({name}): {svg_path}")

        # Auto-convert to PNG if cairosvg is available
        png_path = f"{base_path}_{name}.png"
        if svg_to_png(svg_path, png_path):
            png_paths.append(png_path)
            print(f"PNG preview ({name}): {png_path}")

    return svg_paths


def get_model_stats(result) -> dict:
    """Get basic stats about the model (bounding box, volume)."""
    try:
        bb = result.val().BoundingBox()
        stats = {
            "size_x": round(bb.xlen, 2),
            "size_y": round(bb.ylen, 2),
            "size_z": round(bb.zlen, 2),
        }
    except Exception:
        stats = {"size_x": "?", "size_y": "?", "size_z": "?"}

    return stats


def validate_printability(result) -> list:
    """Basic printability checks."""
    warnings = []
    try:
        bb = result.val().BoundingBox()
        # Check if any dimension is extremely thin
        dims = [bb.xlen, bb.ylen, bb.zlen]
        for i, d in enumerate(dims):
            axis = ["X", "Y", "Z"][i]
            if d < 0.4:
                warnings.append(f"WARNING: {axis} dimension is {d:.2f}mm — too thin for most printers")
            elif d < 0.8:
                warnings.append(f"CAUTION: {axis} dimension is {d:.2f}mm — may be fragile")

        # Check for very large parts
        for i, d in enumerate(dims):
            axis = ["X", "Y", "Z"][i]
            if d > 250:
                warnings.append(f"WARNING: {axis} dimension is {d:.0f}mm — may exceed build volume")

    except Exception as e:
        warnings.append(f"Could not validate: {e}")

    return warnings


def main():
    parser = argparse.ArgumentParser(description="CadQuery render and export for ClaudeCAD")
    parser.add_argument("script", help="Path to the CadQuery Python script")
    parser.add_argument("--no-preview", action="store_true", help="Skip preview generation")
    parser.add_argument("--format", choices=["stl", "step", "both"], default="stl",
                        help="Export format (default: stl)")
    args = parser.parse_args()

    script_path = args.script
    if not os.path.exists(script_path):
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    base_path = os.path.splitext(script_path)[0]

    print(f"Loading CadQuery script: {script_path}")
    result = load_cad_script(script_path)
    print("Script loaded successfully.")

    # Model stats
    stats = get_model_stats(result)
    print(f"Model size: {stats['size_x']} x {stats['size_y']} x {stats['size_z']} mm")

    # Printability checks
    warnings = validate_printability(result)
    for w in warnings:
        print(f"  {w}")

    # Export
    if args.format in ("stl", "both"):
        export_stl(result, f"{base_path}.stl")
    if args.format in ("step", "both"):
        export_step(result, f"{base_path}.step")

    # Preview
    if not args.no_preview:
        svg_paths = generate_preview(result, base_path)

    print("\nDone!")


if __name__ == "__main__":
    main()
