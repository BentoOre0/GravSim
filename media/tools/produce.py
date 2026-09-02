"""Regenerate the GravSim portfolio media set.

Runs GravSim's own simulation code (main.py: Barnes-Hut quadtree, spin() galaxy
tool, momentum-conserving merging) headlessly via the shim/ package, and
re-renders the frames with PIL.

    python3 produce.py [name ...]      # default: all
"""
import os
import sys
import time

import scenes
import studio

# Default output is the media/ directory this tools/ folder lives in.
OUT = os.environ.get("GRAVSIM_OUT",
                     os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def stamp(name, t0):
    mb = os.path.getsize(os.path.join(OUT, name)) / 1e6
    print(f"  -> {name:32} {mb:5.2f} MB  ({time.time() - t0:.0f}s)", flush=True)


def quadtree_gif():
    """Hero loop: quadtree subdividing around a collapsing galaxy."""
    t0 = time.time()
    W, H = 800, 500
    m, _ = scenes.build(W, H, seed=9, G=0.30, theta=0.5, max_radius=1,
                        plan=[dict(cx=400, cy=250, r=225, n=700, spin=1.0)])
    scenes.zero_momentum(m)
    r = studio.Renderer((W, H), ss=2, tree_gain=1.6, bloom=((2, 0.7), (7, 0.45)))
    frames = []
    for _ in range(60):
        studio.step(m)
        frames.append(r.frame(m, show_tree=True))
    studio.save_gif(frames, os.path.join(OUT, "quadtree-subdivision.gif"),
                    duration=70, colors=64)
    stamp("quadtree-subdivision.gif", t0)


def quadtree_detail():
    """Hi-res still: recursive subdivision, one body per leaf cell."""
    t0 = time.time()
    W, H = 1800, 1125
    m, _ = scenes.build(W, H, seed=9, G=0.30, theta=0.5, max_radius=1,
                        plan=[dict(cx=900, cy=562, r=505, n=900, spin=1.0)])
    scenes.zero_momentum(m)
    for _ in range(8):
        studio.step(m)
    r = studio.Renderer((W, H), ss=2, tree_gain=1.6, bloom=((3, 0.7), (9, 0.5)))
    r.frame(m, show_tree=True, min_r=1.3).save(os.path.join(OUT, "quadtree-detail.png"))
    stamp("quadtree-detail.png", t0)


def galaxy_trails():
    """Long exposure: 140 steps of orbital paths accumulated on one canvas."""
    t0 = time.time()
    W, H = 1600, 1000
    m, _ = scenes.build(W, H, seed=12, G=0.16, theta=0.5, max_radius=1,
                        plan=[dict(cx=800, cy=500, r=430, n=2400, spin=1.0)])
    scenes.zero_momentum(m)
    studio.long_exposure(m, (W, H), steps=140, ss=2, trail_gain=0.035, settle=3) \
        .save(os.path.join(OUT, "galaxy-long-exposure.png"))
    stamp("galaxy-long-exposure.png", t0)


def planets():
    """Two frames of the merge cascade: many worlds, then fewer bigger ones."""
    t0 = time.time()
    W, H = 1600, 1000
    m, _ = scenes.build(W, H, seed=4, G=0.30, theta=0.5, max_radius=4,
                        plan=[dict(cx=800, cy=500, r=390, n=2600, spin=1.0)])
    scenes.zero_momentum(m)
    r = studio.Renderer((W, H), ss=2, bloom=((3, 0.5), (9, 0.4), (24, 0.3)))
    done = 0
    for name, n in (("planets-coalescence.png", 34), ("planets-late.png", 46)):
        while done < n:
            studio.step(m)
            done += 1
        r.frame(m, min_r=1.1, body_gain=0.55).save(os.path.join(OUT, name))
        stamp(name, t0)


def planets_closeup():
    """Portrait of large merged worlds (bigger seed bodies, max_radius=8)."""
    t0 = time.time()
    W, H = 1600, 1000
    m, _ = scenes.build(W, H, seed=21, G=0.28, theta=0.5, max_radius=8,
                        plan=[dict(cx=800, cy=500, r=330, n=1500, spin=1.0)])
    scenes.zero_momentum(m)
    for _ in range(30):
        studio.step(m)
    r = studio.Renderer((W, H), ss=2, bloom=((4, 0.5), (12, 0.4), (30, 0.3)))
    r.frame(m, min_r=1.4, body_gain=0.55).save(os.path.join(OUT, "planets-closeup.png"))
    stamp("planets-closeup.png", t0)


def galaxy_gif():
    """Loop: rotating galaxy coalescing into planets, with short motion trails."""
    t0 = time.time()
    W, H = 720, 450
    m, _ = scenes.build(W, H, seed=12, G=0.16, theta=0.5, max_radius=2,
                        plan=[dict(cx=360, cy=225, r=195, n=1400, spin=1.0)])
    scenes.zero_momentum(m)
    r = studio.Renderer((W, H), ss=2, trail_decay=0.55,
                        bloom=((3, 0.5), (10, 0.38), (24, 0.26)))
    frames = []
    for _ in range(44):
        studio.step(m)
        frames.append(r.frame(m, min_r=1.0, body_gain=0.75))
    studio.save_gif(frames, os.path.join(OUT, "galaxy-formation.gif"),
                    duration=75, colors=128)
    stamp("galaxy-formation.gif", t0)


TARGETS = {
    "quadtree-gif": quadtree_gif,
    "quadtree-detail": quadtree_detail,
    "galaxy-trails": galaxy_trails,
    "planets": planets,
    "planets-closeup": planets_closeup,
    "galaxy-gif": galaxy_gif,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or list(TARGETS)
    for i, n in enumerate(names, 1):
        print(f"[{i}/{len(names)}] {n}", flush=True)
        TARGETS[n]()
    print("\nOutput:", OUT)
