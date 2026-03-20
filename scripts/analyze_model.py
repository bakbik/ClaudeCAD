#!/usr/bin/env python3
"""
analyze_model.py — Parse 3D model files and return metadata as JSON.

Supports: STL, 3MF, OBJ, PLY, GLB/GLTF (via trimesh)
         STEP, SLDPRT (via CadQuery fallback)

Usage:
    python analyze_model.py <file_path>
    python analyze_model.py model.stl
"""

import sys
import json
import os


def analyze_with_trimesh(file_path: str) -> dict:
    import trimesh
    mesh = trimesh.load(file_path, force="mesh")

    # Handle scenes (GLB files with multiple meshes)
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(list(mesh.geometry.values()))

    extents = mesh.bounding_box.extents.tolist()
    return {
        "file": file_path,
        "format": os.path.splitext(file_path)[1].lower().lstrip("."),
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "bounding_box_mm": {
            "width": round(extents[0], 2),
            "depth": round(extents[1], 2),
            "height": round(extents[2], 2),
        },
        "volume_mm3": round(float(mesh.volume), 2) if mesh.is_watertight else None,
        "is_watertight": bool(mesh.is_watertight),
        "center_of_mass": [round(float(v), 2) for v in mesh.center_mass],
        "surface_area_mm2": round(float(mesh.area), 2),
    }


def analyze_with_cadquery(file_path: str) -> dict:
    import cadquery as cq
    shape = cq.importers.importStep(file_path)
    bb = shape.val().BoundingBox()
    return {
        "file": file_path,
        "format": os.path.splitext(file_path)[1].lower().lstrip("."),
        "vertices": None,
        "faces": None,
        "bounding_box_mm": {
            "width": round(bb.xmax - bb.xmin, 2),
            "depth": round(bb.ymax - bb.ymin, 2),
            "height": round(bb.zmax - bb.zmin, 2),
        },
        "volume_mm3": None,
        "is_watertight": None,
        "center_of_mass": None,
        "surface_area_mm2": None,
        "note": "Parsed via CadQuery (STEP/SLDPRT) — mesh stats not available",
    }


def analyze(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    ext = os.path.splitext(file_path)[1].lower()
    step_formats = {".step", ".stp", ".sldprt", ".sldasm"}

    if ext in step_formats:
        try:
            return analyze_with_cadquery(file_path)
        except Exception as e:
            return {"error": f"CadQuery parse failed: {e}", "file": file_path}

    try:
        return analyze_with_trimesh(file_path)
    except Exception as e:
        # Try CadQuery as fallback for any format
        if ext in step_formats:
            try:
                return analyze_with_cadquery(file_path)
            except Exception:
                pass
        return {"error": f"Parse failed: {e}", "file": file_path}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_model.py <file_path>", file=sys.stderr)
        sys.exit(1)

    result = analyze(sys.argv[1])
    print(json.dumps(result, indent=2))
