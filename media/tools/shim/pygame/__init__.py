"""Minimal pygame stand-in.

Records draw calls into a command buffer instead of rasterising, so GravSim's
real simulation + drawing code can run headless and be re-rendered with PIL.
"""
import math

QUIT = 256
KEYDOWN = 768
KEYUP = 769
MOUSEBUTTONDOWN = 1025
MOUSEBUTTONUP = 1026

# key constants main.py references
for _i, _n in enumerate("abcdefghijklmnopqrstuvwxyz"):
    globals()["K_" + _n] = 97 + _i


class Color(tuple):
    def __new__(cls, *a):
        if len(a) == 1:
            a = tuple(a[0])
        return super().__new__(cls, a)


class Vector2:
    __slots__ = ("x", "y")

    def __init__(self, x=0, y=0):
        if hasattr(x, "__len__"):
            x, y = x[0], x[1]
        self.x, self.y = float(x), float(y)

    def __sub__(self, o):
        return Vector2(self.x - o.x, self.y - o.y)

    def __add__(self, o):
        return Vector2(self.x + o.x, self.y + o.y)

    def __iadd__(self, o):
        self.x += o.x
        self.y += o.y
        return self

    def __iter__(self):
        return iter((self.x, self.y))

    def length(self):
        return math.hypot(self.x, self.y)

    def rotate(self, deg):
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        return Vector2(self.x * c - self.y * s, self.x * s + self.y * c)

    def rotate_ip(self, deg):
        v = self.rotate(deg)
        self.x, self.y = v.x, v.y

    def angle_to(self, o):
        return math.degrees(math.atan2(o.y, o.x) - math.atan2(self.y, self.x))


class Surface:
    """Holds an ordered list of draw commands for the current frame."""

    def __init__(self, size):
        self.size = size
        self.cmds = []
        self.bg = (0, 0, 0)

    def fill(self, color):
        self.bg = tuple(color)
        self.cmds.clear()

    def get_size(self):
        return self.size


class _Draw:
    @staticmethod
    def circle(surface, color, center, radius, width=0):
        surface.cmds.append(("circle", tuple(color), (center[0], center[1]), radius))

    @staticmethod
    def line(surface, color, start, end, width=1):
        surface.cmds.append(("line", tuple(color), tuple(start), tuple(end), width))

    @staticmethod
    def polygon(surface, color, points, width=0):
        surface.cmds.append(("polygon", tuple(color), [tuple(p) for p in points], width))

    @staticmethod
    def rect(surface, color, rect, width=0):
        surface.cmds.append(("rect", tuple(color), tuple(rect), width))


draw = _Draw()


class _Clock:
    def tick(self, fps=0):
        return 0

    def get_fps(self):
        return 0.0


class _Time:
    Clock = _Clock

    @staticmethod
    def get_ticks():
        return 0


time = _Time()


class _Display:
    _surface = None

    @classmethod
    def set_mode(cls, size, *a, **k):
        cls._surface = Surface(size)
        return cls._surface

    @staticmethod
    def set_caption(*a):
        pass

    @staticmethod
    def update(*a):
        pass

    @staticmethod
    def flip(*a):
        pass

    @classmethod
    def get_surface(cls):
        return cls._surface


display = _Display()


class _Event:
    @staticmethod
    def get():
        return []

    @staticmethod
    def pump():
        pass


event = _Event()

_mouse_pos = (0, 0)


class _Mouse:
    @staticmethod
    def get_pos():
        return _mouse_pos

    @staticmethod
    def get_pressed():
        return (0, 0, 0)


mouse = _Mouse()


def set_mouse_pos(x, y):
    global _mouse_pos
    _mouse_pos = (x, y)


def init():
    return (0, 0)


def quit():
    pass
