#!/usr/bin/env python3
"""
ClaudeCAD Web Server — Gradio UI for AI-assisted 3D model design.

Usage:
    python server.py
    python server.py --port 7860 --share
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import gradio as gr

DESIGNS_DIR = Path(__file__).parent / "designs"
DESIGNS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def list_designs() -> list[str]:
    """Return sorted list of design files in designs/."""
    exts = {".py", ".stl", ".step", ".glb", ".obj", ".png", ".svg"}
    files = sorted(
        str(p.relative_to(Path(__file__).parent))
        for p in DESIGNS_DIR.iterdir()
        if p.suffix.lower() in exts
    )
    return files if files else ["(no designs yet)"]


def generate_draft_ui(spec_json: str, output_name: str) -> tuple[str, str]:
    """Run generate_draft.py and return (status_message, output_image_path)."""
    if not spec_json.strip():
        return "Please enter a JSON spec.", None

    try:
        spec = json.loads(spec_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}", None

    if not output_name.strip():
        output_name = spec.get("name", "draft").replace(" ", "_").lower()

    output_path = str(DESIGNS_DIR / f"{output_name}_draft.png")

    script = Path(__file__).parent / "scripts" / "generate_draft.py"
    result = subprocess.run(
        [sys.executable, str(script), spec_json, "--output", output_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return f"Error:\n{result.stderr}", None

    return result.stdout.strip(), output_path if os.path.exists(output_path) else None


def render_cad_ui(script_path: str, export_format: str) -> tuple[str, str | None]:
    """Run cad_render.py on a selected design script."""
    if not script_path or script_path == "(no designs yet)":
        return "Select a .py design script first.", None

    if not script_path.endswith(".py"):
        return "Please select a .py CadQuery script.", None

    full_path = Path(__file__).parent / script_path
    if not full_path.exists():
        return f"File not found: {full_path}", None

    script = Path(__file__).parent / "scripts" / "cad_render.py"
    result = subprocess.run(
        [sys.executable, str(script), str(full_path), "--format", export_format],
        capture_output=True,
        text=True,
    )

    output = result.stdout + ("\n" + result.stderr if result.stderr else "")

    # Find a preview image
    base = str(full_path.with_suffix(""))
    preview = None
    for view in ("iso", "front", "top", "right"):
        candidate = f"{base}_{view}.png"
        if os.path.exists(candidate):
            preview = candidate
            break

    return output.strip(), preview


def analyze_model_ui(script_path: str) -> str:
    """Run analyze_model.py on a selected STL/GLB file."""
    if not script_path or script_path == "(no designs yet)":
        return "Select a model file first."

    full_path = Path(__file__).parent / script_path
    if not full_path.exists():
        return f"File not found: {full_path}"

    script = Path(__file__).parent / "scripts" / "analyze_model.py"
    result = subprocess.run(
        [sys.executable, str(script), str(full_path)],
        capture_output=True,
        text=True,
    )
    return (result.stdout + result.stderr).strip()


def refresh_designs() -> gr.Dropdown:
    return gr.Dropdown(choices=list_designs())


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

EXAMPLE_SPEC = json.dumps(
    {
        "name": "Phone Stand",
        "views": ["front", "top", "side"],
        "dimensions": {"width": 80, "height": 120, "depth": 60},
        "features": [
            {"type": "slot", "label": "Phone slot", "position": [40, 90], "size": [15, 6]},
            {"type": "fillet", "label": "Corner R3mm"},
        ],
        "notes": ["Wall thickness: 2mm", "Material: PLA"],
    },
    indent=2,
)


def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="ClaudeCAD",
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
    ) as demo:
        gr.Markdown(
            """
# ClaudeCAD
**AI-assisted 3D model design for 3D printing.**
Generate 2D drafts, render CadQuery models, and analyze existing designs.
"""
        )

        with gr.Tabs():
            # ---- Tab 1: Draft generator ----
            with gr.Tab("2D Draft Generator"):
                gr.Markdown("Generate a dimensioned orthographic draft PNG from a JSON spec.")
                with gr.Row():
                    with gr.Column():
                        spec_input = gr.Textbox(
                            label="JSON Spec",
                            value=EXAMPLE_SPEC,
                            lines=18,
                            max_lines=30,
                        )
                        output_name_input = gr.Textbox(
                            label="Output name (optional)",
                            placeholder="e.g. phone_stand",
                        )
                        gen_btn = gr.Button("Generate Draft", variant="primary")
                    with gr.Column():
                        draft_status = gr.Textbox(label="Status", lines=4, interactive=False)
                        draft_image = gr.Image(label="Draft Preview", type="filepath")

                gen_btn.click(
                    generate_draft_ui,
                    inputs=[spec_input, output_name_input],
                    outputs=[draft_status, draft_image],
                )

            # ---- Tab 2: CAD Renderer ----
            with gr.Tab("CAD Renderer"):
                gr.Markdown("Select a CadQuery `.py` design script to render STL/STEP and preview images.")
                with gr.Row():
                    with gr.Column():
                        design_dd = gr.Dropdown(
                            label="Design script",
                            choices=list_designs(),
                            interactive=True,
                        )
                        format_dd = gr.Dropdown(
                            label="Export format",
                            choices=["stl", "step", "both"],
                            value="stl",
                        )
                        refresh_btn = gr.Button("Refresh list")
                        render_btn = gr.Button("Render", variant="primary")
                    with gr.Column():
                        render_status = gr.Textbox(label="Output", lines=12, interactive=False)
                        render_image = gr.Image(label="Preview (isometric)", type="filepath")

                refresh_btn.click(refresh_designs, outputs=design_dd)
                render_btn.click(
                    render_cad_ui,
                    inputs=[design_dd, format_dd],
                    outputs=[render_status, render_image],
                )

            # ---- Tab 3: Model Analyzer ----
            with gr.Tab("Model Analyzer"):
                gr.Markdown("Analyze an STL/GLB/OBJ model file for statistics (vertices, faces, bounding box, volume).")
                with gr.Row():
                    with gr.Column():
                        analyze_dd = gr.Dropdown(
                            label="Model file",
                            choices=list_designs(),
                            interactive=True,
                        )
                        refresh_btn2 = gr.Button("Refresh list")
                        analyze_btn = gr.Button("Analyze", variant="primary")
                    with gr.Column():
                        analyze_out = gr.Textbox(label="Analysis", lines=20, interactive=False)

                refresh_btn2.click(refresh_designs, outputs=analyze_dd)
                analyze_btn.click(analyze_model_ui, inputs=analyze_dd, outputs=analyze_out)

            # ---- Tab 4: Designs Browser ----
            with gr.Tab("Designs Browser"):
                gr.Markdown("Browse all files in the `designs/` directory.")
                refresh_btn3 = gr.Button("Refresh")
                files_list = gr.Textbox(
                    label="Files",
                    value="\n".join(list_designs()),
                    lines=20,
                    interactive=False,
                )

                def refresh_files():
                    return "\n".join(list_designs())

                refresh_btn3.click(refresh_files, outputs=files_list)

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ClaudeCAD web server")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=7860, help="Port (default: 7860)")
    parser.add_argument("--share", action="store_true", help="Create a public Gradio share link")
    args = parser.parse_args()

    demo = build_ui()
    demo.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        inbrowser=True,
    )


if __name__ == "__main__":
    main()
