# ClaudeCAD — AI-Assisted 3D Model Design Agent

An AI agent that guides you from idea → 2D draft → 3D model, choosing between parametric CAD (CadQuery) and AI mesh generation (Meshy AI) based on your design type.

## Quick Start

```bash
pip install -r requirements.txt
/cad-agent design a phone stand for iPhone 15
```

## Setup

### Requirements
- Python 3.10+
- `pip install -r requirements.txt`

### Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `MESHY_API_KEY` | Meshy AI API key for mesh generation | For organic/freeform shapes |

```bash
export MESHY_API_KEY=your_key_here
```

**Getting a Meshy API key**: Sign up at [meshy.ai](https://www.meshy.ai), go to API → Generate Key. Pro tier required (starts at ~$20/mo). For development/testing, use the free test key: `msy_dummy_api_key_for_test_mode_12345678` (returns sample outputs, no credits used).

**Free alternative for mesh generation**: [TRELLIS 3D](https://trellis3d.co) — upload an image or enter a text prompt manually, download the result as GLB/STL, then place it in `designs/`.

## How It Works

Invoke via Claude Code:
```
/cad-agent <your request>
```

The agent runs through 5 phases:

1. **Input parsing** — accepts text, image paths, or 3D file paths (STL, 3MF, STEP, SLDPRT, OBJ, GLB)
2. **Requirements gathering** — identifies the object category and asks targeted questions
3. **2D draft** — generates a dimensioned orthographic sketch PNG for your review
4. **Approach decision** — chooses CadQuery (parametric) or Meshy AI (mesh) based on shape type
5. **Model generation** — produces STL/STEP (CAD) or GLB/STL (mesh) in `designs/`

## Scripts

| Script | Purpose | Usage |
|---|---|---|
| `scripts/analyze_model.py` | Parse 3D files → JSON stats | `python scripts/analyze_model.py model.stl` |
| `scripts/generate_draft.py` | JSON spec → dimensioned PNG | `python scripts/generate_draft.py '<json>' --output out.png` |
| `scripts/cad_render.py` | CadQuery script → STL + preview | `python scripts/cad_render.py design.py --format both` |
| `scripts/mesh_generate.py` | Meshy AI API → GLB/STL | `python scripts/mesh_generate.py --prompt "..." --output out.glb` |

## Design Conventions

- All dimensions in **millimeters**
- CadQuery scripts store the final shape in a variable named `result`
- Output files land in `designs/<name>.*`
- FDM print rules applied automatically: wall thickness ≥ 0.8mm, overhangs ≤ 45°, fillets on bottom edges

## Project Structure

```
ClaudeCAD/
├── .claude/skills/cad-agent/SKILL.md   # Claude Code skill
├── scripts/
│   ├── analyze_model.py
│   ├── generate_draft.py
│   ├── cad_render.py
│   └── mesh_generate.py
├── designs/                             # Generated outputs
├── requirements.txt
└── CLAUDE.md
```
