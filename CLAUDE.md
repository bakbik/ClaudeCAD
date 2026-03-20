# ClaudeCAD

AI-assisted CAD design for 3D printing, powered by Claude and CadQuery.

## Skills

- **cad-design** (`.claude/skills/cad-design.md`): Conversational 3D part design with FDM print optimization. Generates CadQuery Python scripts, renders multi-view SVG previews, and exports STL files.

## Project Structure

```
.claude/skills/cad-design.md  — Claude Code skill for CAD design
scripts/cad_render.py          — Render + export helper (SVG previews, STL/STEP export)
designs/                       — CadQuery scripts and generated outputs
```

## Workflow

1. Describe a part to Claude
2. Claude generates a CadQuery script in `designs/`
3. Run `python3 scripts/cad_render.py designs/<name>.py` to render previews and export STL
4. Iterate on the design with natural language feedback

## Dependencies

- Python 3.10+
- `cadquery` (`pip install cadquery`)

## Design Conventions

- All dimensions in millimeters
- CadQuery scripts must define a `result` variable
- FDM print rules are applied automatically (see skill for details)
- Bottom edges use chamfers (not fillets) for build plate adhesion
- Default clearances: +0.3mm per side for clearance fits
