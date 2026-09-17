"""Small dependency-free PNG dashboard for the fly's group-brain state.

``fly_bot.dashboard_file`` only needs an object with ``save(file, format=
"PNG")``.  Keeping the renderer here avoids making a graphics package a
runtime dependency for the bot.
"""

import struct
import zlib


WIDTH = 900
HEIGHT = 720
THRESHOLD = 22.0


# A compact 5x7 font is sufficient for the short labels used by the dashboard.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "/": ("00001", "00010", "00100", "01000", "10000", "00000", "00000"),
    " ": ("00000",) * 7,
}


class DashboardImage:
    """Minimal image object supporting the Pillow-compatible save call used by the bot."""

    def __init__(self, width, height, color=(12, 18, 32)):
        self.width = width
        self.height = height
        self.pixels = bytearray(color * (width * height))

    def rectangle(self, x, y, width, height, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.width, x + width), min(self.height, y + height)
        for row in range(y0, y1):
            start = (row * self.width + x0) * 3
            self.pixels[start:start + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def text(self, x, y, value, color=(225, 235, 245), scale=1):
        cursor = x
        for char in str(value).upper():
            glyph = FONT.get(char, FONT[" "])
            for row, bits in enumerate(glyph):
                for column, bit in enumerate(bits):
                    if bit == "1":
                        self.rectangle(cursor + column * scale, y + row * scale, scale, scale, color)
            cursor += 6 * scale

    def save(self, file, format=None):
        if format and format.upper() != "PNG":
            raise ValueError("DashboardImage only supports PNG output")
        rows = b"".join(b"\x00" + self.pixels[row * self.width * 3:(row + 1) * self.width * 3]
                        for row in range(self.height))
        def chunk(kind, data):
            return (struct.pack(">I", len(data)) + kind + data +
                    struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))
        png = (b"\x89PNG\r\n\x1a\n" +
               chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)) +
               chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))
        file.write(png)


def _activation_color(value, highlighted):
    if highlighted:
        return (255, 205, 64)
    if value < 0:
        return (73, 82, 130)
    level = min(1.0, value / THRESHOLD)
    return (int(28 + 205 * level), int(75 + 110 * level), int(115 - 65 * level))


def render_dashboard(brain, highlight=None):
    """Render a compact PNG-ready view of a ``GroupBrain`` instance.

    ``highlight`` is the optional iterable of groups fired by the latest
    command/background event, passed unchanged by ``fly_bot.py``.
    """
    image = DashboardImage(WIDTH, HEIGHT)
    fired = set(highlight or ())
    states = getattr(brain, "this_state", {})
    groups = list(getattr(brain, "groups", sorted(states)))
    drives = getattr(brain, "drives", {})

    image.rectangle(0, 0, WIDTH, 78, (20, 41, 68))
    image.text(20, 15, "FLY BRAIN", scale=3)
    image.text(20, 48, "BEHAVIOR: " + str(getattr(brain, "current_behavior", "idle")), scale=2)
    image.text(540, 48, "TICK: " + str(getattr(brain, "tick_count", 0)), scale=2)

    image.text(20, 94, "DRIVES", (125, 210, 255), scale=2)
    for index, name in enumerate(("hunger", "fear", "fatigue", "curiosity", "groom")):
        y = 122 + index * 24
        value = max(0.0, min(1.0, float(drives.get(name, 0.0))))
        image.text(20, y, name, scale=1)
        image.rectangle(95, y, 160, 9, (42, 57, 77))
        image.rectangle(95, y, int(160 * value), 9, (75, 205, 135))
        image.text(265, y, f"{value:.2f}", scale=1)

    image.text(20, 254, "FUNCTIONAL GROUPS", (125, 210, 255), scale=2)
    image.text(500, 258, "YELLOW = RECENTLY FIRED", (255, 205, 64), scale=1)
    columns = 3
    rows_per_column = max(1, (len(groups) + columns - 1) // columns)
    column_width = WIDTH // columns
    for index, group in enumerate(groups):
        column, row = divmod(index, rows_per_column)
        x, y = 12 + column * column_width, 288 + row * 20
        value = float(states.get(group, 0.0))
        is_highlighted = group in fired
        image.rectangle(x, y, column_width - 24, 16, _activation_color(value, is_highlighted))
        image.text(x + 4, y + 4, group, (8, 15, 26) if value >= 0 or is_highlighted else (230, 235, 245))
        image.text(x + column_width - 80, y + 4, f"{value:.1f}", (8, 15, 26) if value >= 0 or is_highlighted else (230, 235, 245))

    image.text(20, HEIGHT - 20, "ACTIVATION COLORS ARE CLAMPED AT FIRE THRESHOLD: 22", (145, 160, 180))
    return image
