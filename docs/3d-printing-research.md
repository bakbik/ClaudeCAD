# Research: 3D Printing Skills & MCPs for Claude

## Context
Research into existing Claude Code skills, MCP servers, and tools for 3D printing — covering CAD design, print optimization, slicer integration, and printer control. The ClaudeCAD repo is currently a blank-slate project (just a README).

---

## CAD Design MCP Servers & Skills

### 1. CadQuery MCP Server
- Exposes CadQuery (Python parametric CAD on OpenCASCADE kernel) via MCP
- Tools: `verify_cad_query`, `generate_cad_query`; exports STL/STEP/SVG
- Source: [LobeHub - CadQuery MCP](https://lobehub.com/mcp/rishigundakaram-cadquery-mcp-server)

### 2. Claude CAD MCP Plugin (PyPI: `claude-cad`)
- MCP plugin using CadQuery for parametric 3D model generation
- Exports STEP, STL, and other formats
- Source: [claude-cad on PyPI](https://pypi.org/project/claude-cad/)

### 3. BuildCAD AI MCP Server
- Free MCP server for conversational CAD design
- Tools to list designs, read CAD code, render multi-view PNGs
- Works in Claude, Cursor, Windsurf, Claude Code
- Source: [BuildCAD AI](https://buildcad.ai/mcp)

### 4. OpenSCAD 3D Modeler (Claude Code Skill)
- Claude Code skill integrating OpenSCAD for parametric 3D modeling
- Automated syntax validation, multi-angle previews, STL export
- Source: [MCPMarket - OpenSCAD](https://mcpmarket.com/tools/skills/openscad-3d-modeler) / [FastMCP](https://fastmcp.me/skills/details/1958/openscad)

### 5. OpenSCAD Agent
- Claude Code-powered 3D modeling agent with iterative design loop
- Natural language → OpenSCAD code → PNG preview → refinement
- Geometry validation (non-manifold checks, printability)
- Source: [GitHub - openscad-agent](https://github.com/iancanderson/openscad-agent)

### 6. FreeCad MCP
- Connects FreeCAD to Claude via MCP for prompt-assisted 3D design
- Source: [GitHub - freecad_mcp](https://github.com/bonninr/freecad_mcp)

### 7. SolidWorks MCP Server
- Controls SolidWorks, generates VBA scripts, automates CAD workflows
- Exports STEP, IGES, STL, PDF, DXF, DWG
- Source: [LobeHub - SolidWorks MCP](https://lobehub.com/mcp/espocorp-mcp-server-solidworks)

### 8. AutoCAD MCP Server
- 8 consolidated tools over MCP for AutoCAD LT (drawing, entity, layer, etc.)
- Source: [GitHub - autocad-mcp](https://github.com/puran-water/autocad-mcp)

### 9. Blender MCP
- Natural language control of Blender for 3D modeling
- Source: [blender-mcp.com](https://blender-mcp.com/)

---

## 3D Printer Control & Print Optimization

### 10. MCP 3D Printer Server (DMontgomery40)
- **Most comprehensive** — connects to OctoPrint, Klipper/Moonraker, Duet, Repetier, Bambu, Prusa, Creality
- STL manipulation (scale, rotate, merge vertices, center, lay flat)
- Slicer integration (OrcaSlicer, PrusaSlicer, Cura CLI) for G-code generation
- `process_and_print_stl` pipeline: modify → slice → print in one command
- Print monitoring, temperature control, file management
- Source: [GitHub - mcp-3D-printer-server](https://github.com/DMontgomery40/mcp-3D-printer-server) / [Docker](https://hub.docker.com/r/mcp/3d-printer)

### 11. Kiln (codeofaxel)
- 273 MCP tools + 107 CLI commands for printer fleet management
- Supports OctoPrint, Moonraker, Bambu Lab, Prusa Link, Elegoo
- Search models, slice STL, queue prints, manage fleets
- Source: [GitHub - Kiln](https://github.com/codeofaxel/Kiln)

### 12. OctoEverywhere MCP Server
- Cloud MCP for live printer status, webcam snapshots, print control
- Works with OctoPrint, Klipper, Moonraker, Bambu, Creality, Prusa, Elegoo, etc.
- Source: [OctoEverywhere Blog](https://blog.octoeverywhere.com/setup-cloud-mcp-for-your-3d-printer/)

---

## Claude Code Skills for 3D Printing

### 13. CadQuery Conversational Skill (Nicolas Chourrout)
- Turns natural language into parametric CadQuery scripts
- 3-checkpoint workflow: base shape → features → final cleanup with previews
- Self-review pipeline: generates STL, renders 4-view preview, self-checks
- Encodes FDM best practices (wall thickness, hole clearance, overhang limits, material-specific tolerances)
- Source: [Medium Article](https://medium.com/@nchourrout/i-taught-claude-to-design-3d-printable-parts-heres-how-675f644af78a)

### 14. Claude-3D-Playground
- Open a directory in Claude Code, describe a part, get CadQuery → STL
- Source: [GitHub - claude-3d-playground](https://github.com/ivanearisty/claude-3d-playground)

### 15. Paramancer
- Conversational parametric 3D modeling with iterative refinement
- Source: [Indie Hackers - Paramancer](https://www.indiehackers.com/post/paramancer-claude-code-for-iterative-3d-modelling-a2fd56d177)

---

## Autonomous Design & Optimization

### 16. CDS (Cognitive Design Systems) + Claude
- Autonomous engineering design workflow
- AI agent explores/optimizes 50+ design variants (vs. 3-5 manually)
- Runs simulations, evaluates performance, refines geometry
- Source: [3D Adept](https://3dadept.com/how-cds-uses-claude-to-demonstrate-an-autonomous-engineering-design-workflow/)

---

## Related Repos

### 17. ClaudeCAD (niklasmh)
- "Claude 3.5 Aided Design" — use Claude to enhance modeling for 3D printing
- Source: [GitHub - ClaudeCAD](https://github.com/niklasmh/ClaudeCAD)

---

## Key Takeaways

| Category | Best Options |
|---|---|
| **CAD Design (code-based)** | CadQuery MCP, OpenSCAD Skill/Agent, BuildCAD AI |
| **CAD Design (GUI-based)** | FreeCAD MCP, SolidWorks MCP, AutoCAD MCP, Blender MCP |
| **Printer Control** | DMontgomery40 MCP 3D Printer Server, Kiln, OctoEverywhere |
| **Slicing/G-code** | DMontgomery40 (OrcaSlicer/PrusaSlicer/Cura integration) |
| **Print Optimization** | CadQuery Skill (FDM best practices), CDS autonomous optimization |
| **End-to-end Workflow** | DMontgomery40 (modify → slice → print), Kiln (fleet management) |

### Technology Choices
- **CadQuery** (Python + OpenCASCADE) is the preferred programmatic CAD approach — pip-installable, Pythonic API, real CAD kernel
- **OpenSCAD** is a lighter alternative, good for simpler parts, but struggles with complex nested boolean operations
- **MCP** is the standard integration pattern — all major tools now expose MCP interfaces
