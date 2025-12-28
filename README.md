# 3D OBB + 3D Packing (3D Tetris)

This repo contains solutions for:

- **Part 1:** Compute Oriented Bounding Box (OBB) for OBJ meshes and report dimensions + volume.
- **Part 2:** Pack 20 items into a **100×100×100** master box with **no overlap** and **gravity/support** constraints, plus visualization.

---

## Setup

```bash
pip install numpy trimesh open3d plotly
Part 1 — OBB
Place meshes in meshes/:

CUBE.obj

CYLINDER.obj

TEAPOT.obj

Run:

bash
python part1_obb.py
Part 2 — Packing
Run:

bash
python part2_packing.py --json "Item List.json"
If OpenGL/Open3D viewer issues occur, generate browser visualization:

bash
python part2_plotly.py --placements placements_out.json --out packing_animation.html

Outputs

placements_out.json — final placements
packing_animation.html — step-by-step animation







