"""Headless render harness for GravSim (github.com/BentoOre0/GravSim).

Runs the project's real simulation code (Barnes-Hut quadtree, spin/galaxy tool,
momentum-conserving collisions) behind a pygame shim, and re-renders the frames
with PIL so the output is anti-aliased and bloom-lit for portfolio use.
"""
import os
import sys
import time
from collections import deque

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
# Default layout is <repo>/media/tools/, so the GravSim checkout is two levels up.
_DEFAULT_REPO = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
REPO = os.environ.get("GRAVSIM_REPO", _DEFAULT_REPO)


def load_sim(width, height, seed=7):
    """Import GravSim's main.py headlessly at the requested canvas size."""
    os.environ["GRAVSIM_W"] = str(width)
    os.environ["GRAVSIM_H"] = str(height)
    sys.path.insert(0, os.path.join(HERE, "shim"))
    sys.path.insert(0, REPO)
    for mod in ("main", "arrow", "pygame", "screeninfo", "numpy",
                "tkinter", "tkinter.simpledialog"):
        sys.modules.pop(mod, None)
    import random
    random.seed(seed)
    import main
    assert (main.s_width, main.s_height) == (width, height), (main.s_width, main.s_height)
    return main


def step(main):
    """One iteration of main.py's simulation loop (its __main__ block, verbatim order)."""
    main.QT = main.QuadTrees(0, 0, main.s_width, main.s_height)
    main.planet_hash.clear()
    for elem in main.inbound:
        main.QTree_insert(elem)
        main.QTree_point_update(elem)
    main.update_bodies()
    main.handle_collisions()


def live_bodies(main):
    """Bodies the sim would actually blit (Body.draw culls out-of-bounds)."""
    out = []
    for b in main.inbound:
        if b.is_out_of_bounds(main.s_width, main.s_height):
            continue
        if b.mass == 0 or b.radius <= 0:
            continue
        out.append(b)
    return out


def quadtree_rects(main):
    """(bounds, depth) for every node, via the project's own QuadTrees API."""
    rects = []
    stack = deque([(main.QT, 0)])
    while stack:
        node, depth = stack.pop()
        rects.append((node.get_bounds(), depth))
        if not node.leaf:
            for child in node.children:
                stack.append((child, depth + 1))
    return rects


# ---------------------------------------------------------------- rendering

def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


class Renderer:
    """Layered renderer: quadtree behind (crisp), bodies in front (bloomed),
    with optional exponential motion trails."""

    def __init__(self, size, ss=2, backdrop=(3, 4, 9),
                 bloom=((3, 0.8), (10, 0.55), (26, 0.35)),
                 trail_decay=0.0, tree_gain=1.0):
        self.size = size
        self.ss = ss
        self.backdrop = backdrop
        self.bloom = bloom
        self.trail_decay = trail_decay
        self.tree_gain = tree_gain
        self.trail = None

    def _tree_layer(self, main):
        w, h = self.size
        ss = self.ss
        img = Image.new("RGB", (w * ss, h * ss), (0, 0, 0))
        d = ImageDraw.Draw(img)
        rects = quadtree_rects(main)
        maxd = max((dep for _, dep in rects), default=1) or 1
        near, far = (6, 20, 18), (26, 132, 74)
        for (x0, y0, x1, y1), dep in rects:
            t = min(1.0, (dep / maxd) ** 0.8)
            c = _lerp(near, far, t)
            c = tuple(min(255, int(v * self.tree_gain)) for v in c)
            d.rectangle([x0 * ss, y0 * ss, x1 * ss - 1, y1 * ss - 1], outline=c, width=1)
        return img.resize((w, h), Image.LANCZOS) if ss != 1 else img

    def _body_layer(self, main, body_gain=1.0, min_r=0.8):
        w, h = self.size
        ss = self.ss
        img = Image.new("RGB", (w * ss, h * ss), (0, 0, 0))
        d = ImageDraw.Draw(img)
        for b in live_bodies(main):
            r = max(b.radius, min_r) * ss
            cx, cy = b.x * ss, b.y * ss
            col = tuple(min(255, int(v * body_gain)) for v in b.color)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
        return img.resize((w, h), Image.LANCZOS) if ss != 1 else img

    def frame(self, main, show_tree=False, body_gain=1.0, min_r=0.8):
        bodies = self._body_layer(main, body_gain, min_r)

        if self.trail_decay > 0:
            if self.trail is None:
                self.trail = bodies.copy()
            else:
                faded = self.trail.point(lambda v: int(v * self.trail_decay))
                self.trail = ImageChops.lighter(faded, bodies)
            bodies = self.trail.copy()

        lit = bodies
        for radius, weight in self.bloom:
            glow = bodies.filter(ImageFilter.GaussianBlur(radius))
            glow = glow.point(lambda v, _w=weight: int(v * _w))
            lit = ImageChops.add(lit, glow)

        out = Image.new("RGB", self.size, self.backdrop)
        if show_tree:
            out = ImageChops.add(out, self._tree_layer(main))
        return ImageChops.add(out, lit)

    def reset_trails(self):
        self.trail = None


def save_gif(frames, path, duration=70, loop=0, colors=64):
    """One shared adaptive palette, no dithering, no per-frame disposal - all
    three keep the LZW stream compressible, which matters a lot for web use."""
    sample = frames[::max(1, len(frames) // 12)]
    strip = Image.new("RGB", (frames[0].width, frames[0].height * len(sample)))
    for i, f in enumerate(sample):
        strip.paste(f, (0, i * frames[0].height))
    pal = strip.quantize(colors=colors, method=Image.MEDIANCUT)
    out = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    out[0].save(path, save_all=True, append_images=out[1:], duration=duration,
                loop=loop, optimize=True, disposal=1)
    return path


class Progress:
    def __init__(self, total, label):
        self.total, self.label, self.t0 = total, label, time.time()

    def tick(self, i):
        if i % 10 == 0 or i == self.total - 1:
            el = time.time() - self.t0
            print(f"  {self.label}: {i + 1}/{self.total}  ({el:.1f}s)", flush=True)


def long_exposure(main, size, steps, ss=2, trail_gain=0.10, backdrop=(3, 4, 9),
                  bloom=((3, 0.5), (10, 0.4), (26, 0.3)), min_r=0.9,
                  max_seg=90, settle=0):
    """Accumulate many simulation steps onto one canvas -> continuous orbital
    streaks. Each step draws a segment from each body's previous position to its
    current one, so trails are smooth rather than dashed. Bloom is applied once."""
    w, h = size
    acc = Image.new("RGB", (w * ss, h * ss), (0, 0, 0))
    for _ in range(settle):
        step(main)
    prev = {id(b): (b.x, b.y) for b in live_bodies(main)}
    for _ in range(steps):
        step(main)
        layer = Image.new("RGB", (w * ss, h * ss), (0, 0, 0))
        d = ImageDraw.Draw(layer)
        nxt = {}
        for b in live_bodies(main):
            k = id(b)
            nxt[k] = (b.x, b.y)
            col = tuple(max(1, int(v * trail_gain)) for v in b.color)
            r = max(b.radius, min_r) * ss
            x1, y1 = b.x * ss, b.y * ss
            p0 = prev.get(k)
            if p0 is not None:
                x0, y0 = p0[0] * ss, p0[1] * ss
                if (x1 - x0) ** 2 + (y1 - y0) ** 2 < (max_seg * ss) ** 2:
                    d.line([x0, y0, x1, y1], fill=col, width=max(1, min(int(2 * r), int(3 * ss))))
            d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=col)
        acc = ImageChops.add(acc, layer)
        prev = nxt
    img = acc.resize((w, h), Image.LANCZOS) if ss != 1 else acc
    lit = img
    for radius, weight in bloom:
        glow = img.filter(ImageFilter.GaussianBlur(radius))
        lit = ImageChops.add(lit, glow.point(lambda v, _w=weight: int(v * _w)))
    return ImageChops.add(Image.new("RGB", size, backdrop), lit)
