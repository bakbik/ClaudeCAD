# ClaudeCAD

AI-assisted CAD design for 3D printing, powered by Claude and CadQuery.

## Features

- **Conversational CAD Design**: Describe a part in natural language, get a parametric CadQuery model
- **FDM Print Optimization**: Built-in rules for wall thickness, overhangs, clearances, and material-specific tolerances
- **Multi-View Previews**: Automatic SVG renders (front, top, right, isometric) for design review
- **STL/STEP Export**: Production-ready file export for slicing and printing
- **Iterative Refinement**: Modify designs with natural language ("make it 5mm taller", "add a hole on the left")

## Quick Start

```bash
# Install dependencies
pip install cadquery

# Design a part (using Claude Code with the cad-design skill)
# Claude will generate a script in designs/ and render previews

# Manual render
python3 scripts/cad_render.py designs/example_phone_stand.py
```

## Project Structure

```
.claude/skills/cad-design.md  — Claude Code skill for CAD design
scripts/cad_render.py          — Render + export helper
designs/                       — CadQuery scripts and outputs (.stl, .svg)
```

## Research

See `.claude/plans/` for research notes on 3D printing MCPs and Claude skills ecosystem.