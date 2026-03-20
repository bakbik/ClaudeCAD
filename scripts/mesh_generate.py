#!/usr/bin/env python3
"""
mesh_generate.py — Generate a 3D mesh using free HuggingFace Spaces.

No API key or account required. Uses the gradio_client library to call
publicly hosted inference spaces:

  - TRELLIS  (Microsoft) — image-to-3D, high quality GLB output
  - Hunyuan3D-2 (Tencent) — text-to-3D and image-to-3D

Backend is auto-selected based on input:
  - Image provided  → TRELLIS (best quality)
  - Text only       → Hunyuan3D-2

Usage:
    python mesh_generate.py --prompt "a decorative oak tree, low-poly"
    python mesh_generate.py --prompt "phone stand" --image reference.png
    python mesh_generate.py --prompt "..." --backend hunyuan
    python mesh_generate.py --prompt "..." --backend trellis --image ref.png

Output: GLB file (can be converted to STL via trimesh)
"""

import sys
import os
import argparse
import json
import tempfile
import shutil


# --- HuggingFace Space IDs ---
TRELLIS_SPACE   = "JeffreyXiang/TRELLIS"
HUNYUAN_SPACE   = "tencent/Hunyuan3D-2"


def _gradio_client(space_id: str):
    """Return a Gradio client for the given HF Space ID."""
    try:
        from gradio_client import Client
    except ImportError:
        print("gradio_client not installed. Run: pip install gradio_client", file=sys.stderr)
        sys.exit(1)
    print(f"Connecting to HuggingFace Space: {space_id} ...")
    return Client(space_id)


# ---------------------------------------------------------------------------
# TRELLIS backend — image-to-3D
# ---------------------------------------------------------------------------

def generate_trellis(image_path: str, output_path: str,
                     simplify: float = 0.95, texture_size: int = 1024) -> str:
    """
    Call the TRELLIS HuggingFace Space to convert an image to a 3D GLB.
    TRELLIS is image-to-3D only; a prompt is not used.

    Returns path to the downloaded GLB file.
    """
    client = _gradio_client(TRELLIS_SPACE)

    print("Preprocessing image...")
    # Step 1: preprocess the image (background removal + centering)
    preprocessed = client.predict(
        image=image_path,
        api_name="/preprocess_image",
    )

    print("Generating 3D model with TRELLIS (this may take 1–3 minutes)...")
    # Step 2: image → 3D (returns a tuple; first element is the GLB path on the Space)
    result = client.predict(
        image=preprocessed,
        multiimages=[],
        seed=42,
        randomize_seed=True,
        ss_guidance_strength=7.5,
        ss_sampling_steps=12,
        slat_guidance_strength=3.0,
        slat_sampling_steps=12,
        multiimage_algo="stochastic",
        api_name="/image_to_3d",
    )

    print("Extracting GLB...")
    # Step 3: extract GLB from the result
    glb_result = client.predict(
        mesh_simplify=simplify,
        texture_size=texture_size,
        api_name="/extract_glb",
    )

    # glb_result is typically a file path string or a dict with a 'value' key
    glb_src = glb_result if isinstance(glb_result, str) else glb_result.get("value", glb_result)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    shutil.copy(glb_src, output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ TRELLIS GLB saved: {output_path} ({size_kb:.1f} KB)")
    return output_path


# ---------------------------------------------------------------------------
# Hunyuan3D-2 backend — text-to-3D and image-to-3D
# ---------------------------------------------------------------------------

def generate_hunyuan(prompt: str, output_path: str,
                     image_path: str | None = None,
                     steps: int = 20, guidance: float = 7.5) -> str:
    """
    Call the Hunyuan3D-2 HuggingFace Space to generate a 3D model.
    Supports both text-to-3D (prompt only) and image+text-to-3D.

    Returns path to the downloaded GLB file.
    """
    client = _gradio_client(HUNYUAN_SPACE)

    print(f"Generating 3D model with Hunyuan3D-2 ({'image+text' if image_path else 'text'}-to-3D)...")
    print(f"  Prompt: {prompt}")

    if image_path:
        # Image + text conditioned generation
        result = client.predict(
            image=image_path,
            text=prompt,
            steps=steps,
            guidance_scale=guidance,
            seed=42,
            api_name="/generation_all",
        )
    else:
        # Text-only generation
        result = client.predict(
            text=prompt,
            steps=steps,
            guidance_scale=guidance,
            seed=42,
            api_name="/text_to_3d",
        )

    # Result is typically a file path to the GLB, or a dict
    glb_src = result if isinstance(result, str) else (
        result[0] if isinstance(result, (list, tuple)) else result.get("value", str(result))
    )

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    shutil.copy(glb_src, output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ Hunyuan3D-2 GLB saved: {output_path} ({size_kb:.1f} KB)")
    return output_path


# ---------------------------------------------------------------------------
# STL conversion helper
# ---------------------------------------------------------------------------

def glb_to_stl(glb_path: str, stl_path: str) -> str:
    """Convert a GLB file to STL using trimesh."""
    try:
        import trimesh
        mesh = trimesh.load(glb_path)
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(list(mesh.geometry.values()))
        mesh.export(stl_path)
        size_kb = os.path.getsize(stl_path) / 1024
        print(f"✅ STL saved: {stl_path} ({size_kb:.1f} KB)")
        return stl_path
    except Exception as e:
        print(f"⚠️  STL conversion failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a 3D mesh using free HuggingFace Spaces (no API key needed)"
    )
    parser.add_argument("--prompt", required=True,
                        help="Text description of the 3D model")
    parser.add_argument("--image", default=None,
                        help="Reference image path (for image-to-3D; auto-selects TRELLIS)")
    parser.add_argument("--output", default="designs/model.glb",
                        help="Output GLB file path")
    parser.add_argument("--backend", choices=["auto", "trellis", "hunyuan"], default="auto",
                        help="Generation backend (default: auto — TRELLIS if image, else Hunyuan3D-2)")
    parser.add_argument("--also-stl", action="store_true",
                        help="Also convert output to STL via trimesh")
    parser.add_argument("--simplify", type=float, default=0.95,
                        help="TRELLIS mesh simplification ratio (0–1, default 0.95)")
    parser.add_argument("--steps", type=int, default=20,
                        help="Hunyuan3D-2 diffusion steps (default 20)")
    args = parser.parse_args()

    # Auto-select backend
    backend = args.backend
    if backend == "auto":
        backend = "trellis" if args.image else "hunyuan"

    print(f"Backend: {backend.upper()}")

    glb_path = args.output
    if not glb_path.endswith(".glb"):
        glb_path = os.path.splitext(glb_path)[0] + ".glb"

    if backend == "trellis":
        if not args.image:
            print("⚠️  TRELLIS is image-to-3D only. Please provide --image <path>.", file=sys.stderr)
            print("   Falling back to Hunyuan3D-2 for text-to-3D...", file=sys.stderr)
            backend = "hunyuan"

    if backend == "trellis":
        generate_trellis(args.image, glb_path, simplify=args.simplify)
    else:
        generate_hunyuan(args.prompt, glb_path, image_path=args.image, steps=args.steps)

    stl_path = None
    if args.also_stl:
        stl_path = os.path.splitext(glb_path)[0] + ".stl"
        stl_path = glb_to_stl(glb_path, stl_path)

    print(json.dumps({
        "backend": backend,
        "glb": glb_path,
        "stl": stl_path,
        "prompt": args.prompt,
        "image": args.image,
    }))


if __name__ == "__main__":
    main()
