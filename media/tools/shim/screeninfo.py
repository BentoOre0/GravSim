"""screeninfo stand-in: virtual monitor size comes from env vars."""
import os


class Monitor:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.name = "virtual-0"
        self.is_primary = True


def get_monitors():
    # main.py computes s_height = height - 60, so pad the request.
    w = int(os.environ.get("GRAVSIM_W", "1280"))
    h = int(os.environ.get("GRAVSIM_H", "720")) + 60
    return [Monitor(w, h)]
