import json
import argparse
import os
import plotly.graph_objects as go

MASTER = (100, 100, 100)

EDGES = [
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7)
]

# 12 triangles for a cuboid (8 vertices)
FACES = [
    (0,1,2),(0,2,3),  # bottom
    (4,5,6),(4,6,7),  # top
    (0,1,5),(0,5,4),  # side
    (1,2,6),(1,6,5),  # side
    (2,3,7),(2,7,6),  # side
    (3,0,4),(3,4,7)   # side
]

def cuboid_vertices(x,y,z, dx,dy,dz):
    # 8 corners
    return [
        (x,     y,     z),
        (x+dx,  y,     z),
        (x+dx,  y+dy,  z),
        (x,     y+dy,  z),
        (x,     y,     z+dz),
        (x+dx,  y,     z+dz),
        (x+dx,  y+dy,  z+dz),
        (x,     y+dy,  z+dz),
    ]

def master_wireframe():
    x0,y0,z0 = 0,0,0
    x1,y1,z1 = MASTER
    v = cuboid_vertices(x0,y0,z0, x1,y1,z1)
    xs, ys, zs = [], [], []
    for a,b in EDGES:
        xs += [v[a][0], v[b][0], None]
        ys += [v[a][1], v[b][1], None]
        zs += [v[a][2], v[b][2], None]
    return go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", name="Master Box")

def box_mesh_trace(placement, color):
    x,y,z = placement["position_xyz"]
    dx,dy,dz = placement["placed_dims"]
    verts = cuboid_vertices(x,y,z, dx,dy,dz)

    X = [p[0] for p in verts]
    Y = [p[1] for p in verts]
    Z = [p[2] for p in verts]

    I = [a for (a,b,c) in FACES]
    J = [b for (a,b,c) in FACES]
    K = [c for (a,b,c) in FACES]

    return go.Mesh3d(
        x=X, y=Y, z=Z,
        i=I, j=J, k=K,
        opacity=0.75,
        name=f"Item {placement['id']}",
        color=color
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--placements", type=str, default="placements_out.json", help="placements_out.json path")
    ap.add_argument("--out", type=str, default="packing_animation.html", help="output html")
    args = ap.parse_args()

    if not os.path.exists(args.placements):
        raise SystemExit(f"placements file not found: {args.placements}")

    with open(args.placements, "r", encoding="utf-8") as f:
        data = json.load(f)

    placements = data["placements"]

    # colors for 20 items (simple)
    colors = [
        "#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00",
        "#a65628","#f781bf","#999999","#66c2a5","#fc8d62",
        "#8da0cb","#e78ac3","#a6d854","#ffd92f","#e5c494",
        "#b3b3b3","#1b9e77","#d95f02","#7570b3","#e7298a"
    ]

    base = [master_wireframe()]

    frames = []
    for t in range(1, len(placements)+1):
        traces = [master_wireframe()]
        for i in range(t):
            traces.append(box_mesh_trace(placements[i], colors[i % len(colors)]))
        frames.append(go.Frame(data=traces, name=str(t)))

    fig = go.Figure(
        data=frames[0].data,
        frames=frames
    )

    fig.update_layout(
        title="3D Packing Animation (Step-by-step)",
        scene=dict(
            xaxis=dict(range=[0, MASTER[0]], title="X"),
            yaxis=dict(range=[0, MASTER[1]], title="Y"),
            zaxis=dict(range=[0, MASTER[2]], title="Z"),
            aspectmode="cube"
        ),
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=1.05,
            x=0.02,
            xanchor="left",
            buttons=[
                dict(label="Play",
                     method="animate",
                     args=[None, {"frame": {"duration": 600, "redraw": True},
                                  "fromcurrent": True}]),
                dict(label="Pause",
                     method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate"}])
            ]
        )],
        sliders=[dict(
            steps=[dict(method="animate", args=[[str(k)], {"mode":"immediate", "frame":{"duration":0, "redraw":True}}],
                        label=str(k)) for k in range(1, len(placements)+1)],
            x=0.1, y=0.02, len=0.85
        )]
    )

    fig.write_html(args.out, auto_open=True)
    print(f"Saved animation to: {args.out}")

if __name__ == "__main__":
    main()
