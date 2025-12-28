import os
import numpy as np
import trimesh
import open3d as o3d

FILES = ["CUBE.obj", "CYLINDER.obj", "TEAPOT.obj"]
MESH_DIR = "meshes"

EDGES = np.array([
    [0,1],[1,2],[2,3],[3,0],
    [4,5],[5,6],[6,7],[7,4],
    [0,4],[1,5],[2,6],[3,7]
], dtype=np.int32)

def load_trimesh(path):
    tm = trimesh.load(path, force="mesh")
    if isinstance(tm, trimesh.Scene):
        tm = trimesh.util.concatenate(tuple(tm.dump()))
    return tm

def lineset_from_corners(corners):
    ls = o3d.geometry.LineSet(
        points=o3d.utility.Vector3dVector(corners.astype(np.float64)),
        lines=o3d.utility.Vector2iVector(EDGES)
    )
    ls.paint_uniform_color([1, 0, 0])  # red
    return ls

def build_geometries(obj_path):
    # trimesh OBB (tight-ish)
    tm = load_trimesh(obj_path)
    box = tm.bounding_box_oriented
    ext = np.array(box.primitive.extents, dtype=float)
    vol = float(np.prod(ext))
    L, W, H = sorted(ext.tolist(), reverse=True)

    print("\n" + "=" * 60)
    print(f"File: {os.path.basename(obj_path)}")
    print(f"OBB extents: {ext[0]:.4f} x {ext[1]:.4f} x {ext[2]:.4f}")
    print(f"Dimensions (L x W x H): {L:.4f} x {W:.4f} x {H:.4f}")
    print(f"Volume: {vol:.6f}")
    print("=" * 60)

    # open3d mesh + OBB lines
    mesh = o3d.io.read_triangle_mesh(obj_path)
    mesh.compute_vertex_normals()
    mesh.paint_uniform_color([0.7, 0.7, 0.7])

    corners = np.asarray(box.vertices)  # (8,3)
    obb_ls = lineset_from_corners(corners)

    frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.25, origin=[0, 0, 0])
    return [mesh, obb_ls, frame]

def main():
    # Prepare file paths
    paths = []
    for f in FILES:
        p = os.path.join(MESH_DIR, f)
        if not os.path.exists(p):
            print(f"[SKIP] Not found: {p}")
        else:
            paths.append(p)

    if not paths:
        raise SystemExit("No OBJ files found in meshes/")

    idx = {"i": 0}  # mutable for callbacks

    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window(window_name="OBB Viewer (Press N for Next, Q/Esc to Quit)", width=1280, height=720)

    def load_current():
        vis.clear_geometries()
        geoms = build_geometries(paths[idx["i"]])
        for g in geoms:
            vis.add_geometry(g)
        vis.reset_view_point(True)
        vis.update_renderer()

    def on_next(v):
        idx["i"] = (idx["i"] + 1) % len(paths)
        load_current()
        return False

    def on_prev(v):
        idx["i"] = (idx["i"] - 1) % len(paths)
        load_current()
        return False

    # N = next, P = prev
    vis.register_key_callback(ord("N"), on_next)
    vis.register_key_callback(ord("P"), on_prev)

    print("\nViewer Controls:")
    print("  - Press N = Next object")
    print("  - Press P = Previous object")
    print("  - Close window / press Q or Esc = Exit\n")

    load_current()
    vis.run()
    vis.destroy_window()

if __name__ == "__main__":
    main()
