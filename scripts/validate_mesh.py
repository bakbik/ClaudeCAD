#!/usr/bin/env python3
"""
STL mesh validation for ClaudeCAD.

Usage:
    python3 scripts/validate_mesh.py designs/my_part.stl

Checks:
- File readable and valid STL format
- Triangle count and bounding box
- Watertight (every edge shared by exactly 2 triangles)
- Manifold (no non-manifold edges or vertices)
- No degenerate triangles (zero-area faces)
"""

import struct
import sys
from collections import defaultdict


def read_binary_stl(path: str) -> list:
    """Read a binary STL file and return list of triangles (normal, v1, v2, v3)."""
    triangles = []
    with open(path, "rb") as f:
        header = f.read(80)
        num_triangles = struct.unpack("<I", f.read(4))[0]
        for _ in range(num_triangles):
            data = struct.unpack("<12fH", f.read(50))
            normal = data[0:3]
            v1 = data[3:6]
            v2 = data[6:9]
            v3 = data[9:12]
            triangles.append((normal, v1, v2, v3))
    return triangles


def read_ascii_stl(path: str) -> list:
    """Read an ASCII STL file and return list of triangles."""
    triangles = []
    with open(path, "r") as f:
        lines = f.readlines()

    normal = None
    vertices = []
    for line in lines:
        line = line.strip()
        if line.startswith("facet normal"):
            parts = line.split()
            normal = (float(parts[2]), float(parts[3]), float(parts[4]))
            vertices = []
        elif line.startswith("vertex"):
            parts = line.split()
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif line.startswith("endfacet"):
            if len(vertices) == 3 and normal is not None:
                triangles.append((normal, vertices[0], vertices[1], vertices[2]))
    return triangles


def read_stl(path: str) -> list:
    """Read an STL file (auto-detect binary vs ASCII)."""
    with open(path, "rb") as f:
        header = f.read(80)
    if b"solid" in header[:10]:
        # Could be ASCII — try it, fall back to binary
        try:
            triangles = read_ascii_stl(path)
            if triangles:
                return triangles
        except Exception:
            pass
    return read_binary_stl(path)


def round_vertex(v, decimals=4):
    """Round vertex coords to avoid floating point edge-matching issues."""
    return tuple(round(c, decimals) for c in v)


def make_edge(v1, v2):
    """Create a canonical edge (sorted tuple of vertices)."""
    return tuple(sorted([v1, v2]))


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def magnitude(v):
    return (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5


def validate(path: str) -> dict:
    """Validate an STL mesh and return a report dict."""
    triangles = read_stl(path)
    report = {
        "file": path,
        "triangles": len(triangles),
        "errors": [],
        "warnings": [],
    }

    if not triangles:
        report["errors"].append("No triangles found in STL file")
        return report

    # Bounding box
    all_verts = []
    for _, v1, v2, v3 in triangles:
        all_verts.extend([v1, v2, v3])

    xs = [v[0] for v in all_verts]
    ys = [v[1] for v in all_verts]
    zs = [v[2] for v in all_verts]
    report["bbox"] = {
        "x": (round(min(xs), 2), round(max(xs), 2)),
        "y": (round(min(ys), 2), round(max(ys), 2)),
        "z": (round(min(zs), 2), round(max(zs), 2)),
    }
    report["size"] = {
        "x": round(max(xs) - min(xs), 2),
        "y": round(max(ys) - min(ys), 2),
        "z": round(max(zs) - min(zs), 2),
    }

    # Edge analysis for watertight / manifold checks
    edge_count = defaultdict(int)
    degenerate = 0

    for _, v1, v2, v3 in triangles:
        rv1 = round_vertex(v1)
        rv2 = round_vertex(v2)
        rv3 = round_vertex(v3)

        # Degenerate triangle check
        area_vec = cross(sub(rv2, rv1), sub(rv3, rv1))
        area = magnitude(area_vec) / 2.0
        if area < 1e-10:
            degenerate += 1
            continue

        edges = [make_edge(rv1, rv2), make_edge(rv2, rv3), make_edge(rv3, rv1)]
        for e in edges:
            edge_count[e] += 1

    if degenerate > 0:
        report["warnings"].append(f"{degenerate} degenerate (zero-area) triangles")

    # Watertight check: every edge shared by exactly 2 triangles
    boundary_edges = sum(1 for c in edge_count.values() if c == 1)
    non_manifold_edges = sum(1 for c in edge_count.values() if c > 2)

    report["total_edges"] = len(edge_count)
    report["boundary_edges"] = boundary_edges
    report["non_manifold_edges"] = non_manifold_edges

    if boundary_edges > 0:
        report["errors"].append(
            f"NOT watertight: {boundary_edges} boundary edges (holes in mesh)"
        )
    if non_manifold_edges > 0:
        report["errors"].append(
            f"Non-manifold: {non_manifold_edges} edges shared by >2 triangles"
        )

    report["watertight"] = boundary_edges == 0
    report["manifold"] = non_manifold_edges == 0
    report["valid"] = report["watertight"] and report["manifold"] and len(report["errors"]) == 0

    return report


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/validate_mesh.py <stl_file>")
        sys.exit(1)

    path = sys.argv[1]
    report = validate(path)

    print(f"File: {report['file']}")
    print(f"Triangles: {report['triangles']}")

    if "size" in report:
        s = report["size"]
        print(f"Size: {s['x']} x {s['y']} x {s['z']} mm")

    print(f"Watertight: {'YES' if report.get('watertight') else 'NO'}")
    print(f"Manifold: {'YES' if report.get('manifold') else 'NO'}")
    print(f"Valid: {'YES' if report.get('valid') else 'NO'}")

    for w in report.get("warnings", []):
        print(f"  WARNING: {w}")
    for e in report.get("errors", []):
        print(f"  ERROR: {e}")

    sys.exit(0 if report.get("valid") else 1)


if __name__ == "__main__":
    main()
