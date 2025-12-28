import argparse
import json
import time
import itertools
import numpy as np

import open3d as o3d

MASTER = (100, 100, 100)  # X, Y, Z

def parse_items(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # supports either: [ [20,20,20], ... ] OR { "items": [ ... ] }
    if isinstance(data, dict) and "items" in data:
        data = data["items"]

    if not isinstance(data, list):
        raise ValueError("JSON must be a list OR a dict with key 'items'.")

    items = []
    for i, it in enumerate(data):
        if isinstance(it, (list, tuple)) and len(it) == 3:
            dims = it
        elif isinstance(it, dict):
            # try common keys
            for k in ["dimensions", "dims", "size", "whd", "lwh"]:
                if k in it and isinstance(it[k], (list, tuple)) and len(it[k]) == 3:
                    dims = it[k]
                    break
            else:
                raise ValueError(f"Item {i} dict has no dimension key: {it}")
        else:
            raise ValueError(f"Item {i} has unsupported format: {it}")

        dx, dy, dz = [int(np.ceil(float(x))) for x in dims]
        items.append({"id": i, "dims": (dx, dy, dz)})

    return items

def unique_orientations(dims):
    return list({tuple(p) for p in set(itertools.permutations(dims, 3))})

def find_best_placement(heightmap, item_dims):
    max_x, max_y, max_z = MASTER
    best = None

    for (dx, dy, dz) in unique_orientations(item_dims):
        if dx > max_x or dy > max_y or dz > max_z:
            continue

        for x in range(0, max_x - dx + 1):
            for y in range(0, max_y - dy + 1):
                region = heightmap[x:x+dx, y:y+dy]
                base_z = int(region.max())

                # must be fully supported
                if not np.all(region == base_z):
                    continue

                # must fit in Z
                if base_z + dz > max_z:
                    continue

                new_max = int(max(heightmap.max(), base_z + dz))

                # heuristic: lower base, then lower final height, then closer to origin
                score = (base_z, new_max, x + y)

                if best is None or score < best["score"]:
                    best = {"x": x, "y": y, "z": base_z, "dx": dx, "dy": dy, "dz": dz, "score": score}

    return best

def place_item(heightmap, placement):
    x, y, z = placement["x"], placement["y"], placement["z"]
    dx, dy, dz = placement["dx"], placement["dy"], placement["dz"]
    heightmap[x:x+dx, y:y+dy] = z + dz

def make_master_wireframe():
    aabb = o3d.geometry.AxisAlignedBoundingBox(min_bound=(0, 0, 0), max_bound=MASTER)
    ls = o3d.geometry.LineSet.create_from_axis_aligned_bounding_box(aabb)
    ls.paint_uniform_color([0.1, 0.1, 0.1])
    return ls

def make_box_mesh(dx, dy, dz, x, y, z, color):
    box = o3d.geometry.TriangleMesh.create_box(width=float(dx), height=float(dy), depth=float(dz))
    box.compute_vertex_normals()
    box.paint_uniform_color(color)
    box.translate((float(x), float(y), float(z)))
    return box

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=str, default="Item List.json", help="Path to Item List.json")
    ap.add_argument("--save_out", type=str, default="placements_out.json", help="Output placements JSON")
    ap.add_argument("--step_delay", type=float, default=0.8, help="Seconds between placements")
    args = ap.parse_args()

    items = parse_items(args.json)

    # big first packing generally better
    items.sort(key=lambda it: it["dims"][0] * it["dims"][1] * it["dims"][2], reverse=True)

    heightmap = np.zeros((MASTER[0], MASTER[1]), dtype=np.int32)

    placements = []
    unplaced = []

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="3D Packing (Press close to end)", width=1280, height=720)

    master_wire = make_master_wireframe()
    frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=10, origin=[0, 0, 0])
    vis.add_geometry(master_wire)
    vis.add_geometry(frame)

    palette = [
        [0.80, 0.20, 0.20],
        [0.20, 0.60, 0.20],
        [0.20, 0.30, 0.80],
        [0.80, 0.60, 0.20],
        [0.60, 0.20, 0.80],
        [0.20, 0.70, 0.70],
    ]

    print("\nPacking into Master Box 100x100x100 ...\n")

    for idx, it in enumerate(items):
        dims = it["dims"]
        best = find_best_placement(heightmap, dims)

        if best is None:
            unplaced.append(it)
            print(f"[FAIL] Item {it['id']} dims={dims} could not be placed (support rule).")
            continue

        place_item(heightmap, best)

        record = {
            "id": it["id"],
            "original_dims": list(dims),
            "placed_dims": [best["dx"], best["dy"], best["dz"]],
            "position_xyz": [best["x"], best["y"], best["z"]],
        }
        placements.append(record)

        print(f"[OK] {idx+1:02d}/{len(items)} Item {it['id']} at {record['position_xyz']} dims={record['placed_dims']}")

        color = palette[idx % len(palette)]
        box = make_box_mesh(best["dx"], best["dy"], best["dz"], best["x"], best["y"], best["z"], color)
        vis.add_geometry(box)
        vis.poll_events()
        vis.update_renderer()
        time.sleep(args.step_delay)

    used_vol = sum(p["placed_dims"][0] * p["placed_dims"][1] * p["placed_dims"][2] for p in placements)
    master_vol = MASTER[0] * MASTER[1] * MASTER[2]
    utilization = used_vol / master_vol

    print("\n" + "=" * 70)
    print(f"Placed items: {len(placements)} / {len(items)}")
    print(f"Unplaced items: {len(unplaced)}")
    print(f"Volume utilization: {utilization*100:.2f}%")
    print(f"Final max height used (Z): {int(heightmap.max())}")
    print("=" * 70)

    out = {
        "master_box": list(MASTER),
        "placements": placements,
        "unplaced": [{"id": u["id"], "dims": list(u["dims"])} for u in unplaced],
        "utilization": utilization,
        "max_height_z": int(heightmap.max()),
    }
    with open(args.save_out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"\nSaved placements to: {args.save_out}")
    print("\n[VIS] Close the window when you are done recording.")
    vis.run()
    vis.destroy_window()

if __name__ == "__main__":
    main()
