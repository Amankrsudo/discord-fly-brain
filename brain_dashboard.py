"""Dependency-free, live sci-fi HUD renderer for the Discord fly brain."""

import os
import struct
import zlib

from dashboard_animation import visual_state


WIDTH, HEIGHT = 1400, 1000
FIRE_THRESHOLD = 22.0
BG, PANEL, PANEL_ALT = (4, 10, 18), (7, 20, 31), (9, 28, 42)
CYAN, CYAN_DIM, TEXT, MUTED = (51, 222, 255), (19, 108, 137), (207, 235, 247), (108, 157, 178)
MAGENTA, ORANGE, GREEN, BLUE, PURPLE = (255, 70, 168), (255, 171, 58), (56, 235, 164), (83, 141, 255), (181, 103, 255)
HERO_ASSET_PATH = os.path.join(os.path.dirname(__file__), "dashboard assests", "fly_hero_transparent.png")
_HERO_ASSET = None


FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"), "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"), "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"), "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"), "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"), "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"), "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"), "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"), "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"), "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"), "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"), "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"), "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"), "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"), "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"), "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"), "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"), "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"), "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"), "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"), ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "/": ("00001", "00010", "00100", "01000", "10000", "00000", "00000"), ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    " ": ("00000",) * 7,
}


class DashboardImage:
    """Small RGB canvas with the ``save(buffer, format='PNG')`` API the bot needs."""
    def __init__(self, width=WIDTH, height=HEIGHT, color=BG):
        self.width, self.height = width, height
        self.pixels = bytearray(color * (width * height))

    def pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i:i + 3] = bytes(color)

    def rectangle(self, x, y, width, height, color):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.width, int(x + width)), min(self.height, int(y + height))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.width + x0) * 3
            self.pixels[i:i + len(row)] = row

    def line(self, x0, y0, x1, y1, color, width=1):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        error = dx + dy
        while True:
            self.rectangle(x0 - width // 2, y0 - width // 2, width, width, color)
            if x0 == x1 and y0 == y1:
                return
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def ellipse(self, cx, cy, rx, ry, color, outline=None):
        for y in range(max(0, int(cy - ry)), min(self.height, int(cy + ry) + 1)):
            for x in range(max(0, int(cx - rx)), min(self.width, int(cx + rx) + 1)):
                distance = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if distance <= 1:
                    self.pixel(x, y, color)
                elif outline and distance <= 1.05:
                    self.pixel(x, y, outline)

    def composite_rgba(self, rgba, source_width, source_height, x, y, width, height):
        """Nearest-neighbour alpha composite for the supplied transparent hero PNG."""
        for target_y in range(max(0, y), min(self.height, y + height)):
            source_y = min(source_height - 1, (target_y - y) * source_height // height)
            for target_x in range(max(0, x), min(self.width, x + width)):
                source_x = min(source_width - 1, (target_x - x) * source_width // width)
                source = (source_y * source_width + source_x) * 4
                alpha = rgba[source + 3]
                if not alpha:
                    continue
                target = (target_y * self.width + target_x) * 3
                if alpha == 255:
                    self.pixels[target:target + 3] = rgba[source:source + 3]
                    continue
                inverse = 255 - alpha
                for channel in range(3):
                    self.pixels[target + channel] = (rgba[source + channel] * alpha + self.pixels[target + channel] * inverse) // 255

    def text(self, x, y, value, color=TEXT, scale=1, limit=None):
        for index, char in enumerate(str(value).upper()[:limit]):
            for row, bits in enumerate(FONT.get(char, FONT[" "])):
                for column, bit in enumerate(bits):
                    if bit == "1":
                        self.rectangle(x + index * 6 * scale + column * scale, y + row * scale, scale, scale, color)

    def save(self, file, format=None):
        if format and format.upper() != "PNG":
            raise ValueError("DashboardImage only supports PNG output")
        rows = b"".join(b"\x00" + self.pixels[y * self.width * 3:(y + 1) * self.width * 3] for y in range(self.height))
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        file.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def _panel(image, x, y, width, height, title, accent=CYAN):
    cut = 12
    image.rectangle(x, y, width, height, PANEL)
    for a, b, c, d in ((x + cut, y, x + width - cut, y), (x + width, y + cut, x + width, y + height - cut), (x + width - cut, y + height, x + cut, y + height), (x, y + height - cut, x, y + cut)):
        image.line(a, b, c, d, CYAN_DIM)
    for a, b, c, d in ((x, y + cut, x + cut, y), (x + width - cut, y, x + width, y + cut), (x + width, y + height - cut, x + width - cut, y + height), (x + cut, y + height, x, y + height - cut)):
        image.line(a, b, c, d, accent)
    image.text(x + 18, y + 15, title, accent, 2)


def _paeth(left, above, upper_left):
    estimate = left + above - upper_left
    left_distance, above_distance, upper_left_distance = abs(estimate - left), abs(estimate - above), abs(estimate - upper_left)
    return left if left_distance <= above_distance and left_distance <= upper_left_distance else above if above_distance <= upper_left_distance else upper_left


def _load_png_asset(path):
    """Load the supplied 8-bit RGBA PNG using only the standard library."""
    try:
        data = open(path, "rb").read()
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        offset, idat = 8, bytearray()
        width = height = bit_depth = color_type = interlace = None
        while offset < len(data):
            size = struct.unpack(">I", data[offset:offset + 4])[0]
            kind, payload = data[offset + 4:offset + 8], data[offset + 8:offset + 8 + size]
            offset += 12 + size
            if kind == b"IHDR":
                width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", payload)
            elif kind == b"IDAT":
                idat.extend(payload)
            elif kind == b"IEND":
                break
        if bit_depth != 8 or color_type != 6 or interlace != 0:
            return None
        raw, row_bytes, previous, decoded = zlib.decompress(idat), width * 4, bytearray(width * 4), bytearray()
        position = 0
        for _ in range(height):
            filter_type, row = raw[position], bytearray(raw[position + 1:position + 1 + row_bytes])
            position += row_bytes + 1
            for index in range(row_bytes):
                left = row[index - 4] if index >= 4 else 0
                above, upper_left = previous[index], previous[index - 4] if index >= 4 else 0
                if filter_type == 1:
                    row[index] = (row[index] + left) & 255
                elif filter_type == 2:
                    row[index] = (row[index] + above) & 255
                elif filter_type == 3:
                    row[index] = (row[index] + ((left + above) // 2)) & 255
                elif filter_type == 4:
                    row[index] = (row[index] + _paeth(left, above, upper_left)) & 255
                elif filter_type != 0:
                    return None
            decoded.extend(row)
            previous = row
        return decoded, width, height
    except (OSError, ValueError, zlib.error, struct.error):
        return None


def _gif_lzw_decode(data, minimum_code_size, expected):
    clear, end = 1 << minimum_code_size, (1 << minimum_code_size) + 1
    code_size, next_code = minimum_code_size + 1, end + 1
    table = {index: bytes((index,)) for index in range(clear)}
    output, bit_position, previous = bytearray(), 0, None

    def read_code():
        nonlocal bit_position
        value = 0
        for bit in range(code_size):
            offset = bit_position + bit
            if offset // 8 >= len(data):
                return None
            value |= ((data[offset // 8] >> (offset % 8)) & 1) << bit
        bit_position += code_size
        return value

    while len(output) < expected:
        code = read_code()
        if code is None or code == end:
            break
        if code == clear:
            table = {index: bytes((index,)) for index in range(clear)}
            code_size, next_code, previous = minimum_code_size + 1, end + 1, None
            continue
        if code in table:
            entry = table[code]
        elif code == next_code and previous is not None:
            entry = previous + previous[:1]
        else:
            return None
        output.extend(entry)
        if previous is not None:
            table[next_code] = previous + entry[:1]
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
        previous = entry
    return bytes(output[:expected]) if len(output) >= expected else None


def _load_gif_asset(path, frame_index=0):
    """Decode one GIF frame into the same RGBA tuple used by PNG assets."""
    try:
        data = open(path, "rb").read()
        if data[:6] not in (b"GIF87a", b"GIF89a"):
            return None
        width, height, packed, background, _ = struct.unpack_from("<HHBBB", data, 6)
        global_table = None
        offset = 13
        if packed & 0x80:
            size = 3 * (1 << ((packed & 0x07) + 1))
            global_table, offset = data[offset:offset + size], offset + size
        canvas = bytearray(width * height * 4)
        previous_canvas = None
        transparent = None
        disposal = 0
        frames = []

        def color(table, index):
            start = index * 3
            return tuple(table[start:start + 3]) if table and start + 3 <= len(table) else (0, 0, 0)

        while offset < len(data) and data[offset] != 0x3B:
            marker = data[offset]
            offset += 1
            if marker == 0x21:
                label = data[offset]
                offset += 1
                if label == 0xF9:
                    block_size = data[offset]
                    packed_gce, _, transparent_index = struct.unpack_from("<BBB", data, offset + 1)
                    disposal = (packed_gce >> 2) & 0x07
                    transparent = transparent_index if packed_gce & 1 else None
                    offset += block_size + 2
                else:
                    while offset < len(data):
                        block_size = data[offset]
                        offset += 1
                        if not block_size:
                            break
                        offset += block_size
            elif marker == 0x2C:
                left, top, frame_width, frame_height, packed_image = struct.unpack_from("<HHHHB", data, offset)
                offset += 9
                local_table = None
                if packed_image & 0x80:
                    size = 3 * (1 << ((packed_image & 0x07) + 1))
                    local_table, offset = data[offset:offset + size], offset + size
                minimum_code_size = data[offset]
                offset += 1
                compressed = bytearray()
                while offset < len(data):
                    block_size = data[offset]
                    offset += 1
                    if not block_size:
                        break
                    compressed.extend(data[offset:offset + block_size])
                    offset += block_size
                pixels = _gif_lzw_decode(compressed, minimum_code_size, frame_width * frame_height)
                if pixels is None:
                    return None
                if disposal == 3:
                    previous_canvas = bytes(canvas)
                table = local_table or global_table
                rows = list(range(frame_height))
                if packed_image & 0x40:
                    rows = (list(range(0, frame_height, 8)) + list(range(4, frame_height, 8)) +
                            list(range(2, frame_height, 4)) + list(range(1, frame_height, 2)))
                for source_row, row in enumerate(rows):
                    for column in range(frame_width):
                        target_x, target_y = left + column, top + row
                        if target_x >= width or target_y >= height:
                            continue
                        pixel_index = pixels[source_row * frame_width + column]
                        if pixel_index == transparent:
                            continue
                        target = (target_y * width + target_x) * 4
                        canvas[target:target + 4] = bytes((*color(table, pixel_index), 255))
                frames.append((bytes(canvas), width, height))
                if disposal == 2:
                    for row in range(top, min(height, top + frame_height)):
                        start = (row * width + left) * 4
                        end = (row * width + min(width, left + frame_width)) * 4
                        canvas[start:end] = b"\0" * (end - start)
                elif disposal == 3 and previous_canvas is not None:
                    canvas = bytearray(previous_canvas)
                transparent, disposal, previous_canvas = None, 0, None
            else:
                return None
        return frames[frame_index % len(frames)] if frames else None
    except (OSError, IndexError, ValueError, struct.error):
        return None


def _load_visual_asset(path, frame_index=0):
    if path and path.lower().endswith(".gif"):
        return _load_gif_asset(path, frame_index)
    return _load_png_asset(path) if path else None


def _load_hero_asset():
    global _HERO_ASSET
    if _HERO_ASSET is None:
        _HERO_ASSET = _load_png_asset(HERO_ASSET_PATH)
    return _HERO_ASSET


def _color(group):
    if group.startswith("VIS"): return BLUE
    if group.startswith("OLF"): return MAGENTA
    if group.startswith("CX"): return ORANGE
    if group.startswith("MB"): return GREEN
    if group.startswith("SEZ"): return PURPLE
    if group.startswith("DN") or group.startswith("MN"): return (255, 143, 112)
    return CYAN


def _stimulus(stimulate, fired):
    names = []
    if stimulate.get("touch"): names.append("TOUCH")
    if stimulate.get("foodContact"): names.append("FOOD CONTACT")
    elif stimulate.get("foodNearby"): names.append("FOOD NEARBY")
    if stimulate.get("dangerOdor"): names.append("DANGER ODOR")
    if stimulate.get("wind"): names.append("WIND")
    temp = stimulate.get("temperature", 0.5)
    if temp > .65: names.append("WARM")
    elif temp < .35: names.append("COOL")
    if stimulate.get("nociception"): names.append("PAIN")
    if names: return " / ".join(names)
    for group, name in (("NOCI", "RECENT SHOCK"), ("VIS_LC", "RECENT SCARE"), ("THERMO_WARM", "RECENT BURN"), ("THERMO_COOL", "RECENT FREEZE"), ("GUS_GRN_SWEET", "RECENT FEED")):
        if group in fired: return name
    return "NO ACTIVE FLAG"


def _flow(brain, fired):
    for source in sorted(fired):
        for target in getattr(brain, "weights", {}).get(source, {}):
            if target in fired:
                return source + " - " + target
    return "RECENT FIRED: " + ", ".join(sorted(fired)[:4]) if fired else "NO RECENT THRESHOLD CROSSINGS"


def _meter(image, x, y, name, value, color):
    value = max(0.0, min(1.0, float(value)))
    image.text(x, y, name, TEXT, 1)
    image.rectangle(x + 92, y, 136, 10, (18, 37, 54))
    image.rectangle(x + 93, y + 1, int(134 * value), 8, color)
    image.text(x + 238, y, f"{value:.2f}", color, 1)


def _hero(image, x, y, states, visual, tick=0):
    image.rectangle(x + 10, y + 40, 555, 500, (5, 16, 26))
    for xx in range(x + 25, x + 565, 44): image.line(xx, y + 45, xx, y + 535, (8, 43, 58))
    for yy in range(y + 60, y + 535, 36): image.line(x + 15, yy, x + 565, yy, (8, 43, 58))
    image.text(x + 25, y + 52, "LIVE FUNCTIONAL MAP", CYAN, 1)
    cx, cy = x + 285, y + 170
    for prefix, dx, dy, color in (("OLF", -90, -10, MAGENTA), ("VIS", 90, -10, BLUE), ("CX", -35, 55, ORANGE), ("MB", 55, 55, GREEN), ("SEZ", 0, 95, PURPLE)):
        level = max((max(0.0, states.get(group, 0.0)) for group in states if group.startswith(prefix)), default=0.0)
        radius = 23 + int(min(1.0, level / FIRE_THRESHOLD) * 14)
        image.ellipse(cx + dx, cy + dy, radius, radius - 5, color, CYAN_DIM)
        image.text(cx + dx - 10, cy + dy - 3, prefix, BG, 1)
    frame_asset = _load_visual_asset(visual.get("frame"), tick)
    hero_asset = frame_asset or _load_hero_asset()
    if hero_asset:
        rgba, source_width, source_height = hero_asset
        target_width = target_height = 285
        scale = min(target_width / source_width, target_height / source_height)
        display_width = max(1, int(source_width * scale))
        display_height = max(1, int(source_height * scale))
        display_x = x + 145 + (target_width - display_width) // 2
        display_y = y + 245 + (target_height - display_height) // 2
        image.composite_rgba(rgba, source_width, source_height,
                              display_x, display_y, display_width, display_height)
    else:
        # Graceful fallback if the optional visual asset is unavailable.
        image.ellipse(cx - 96, y + 370, 38, 32, (136, 86, 52), ORANGE)
        image.ellipse(cx - 45, y + 374, 57, 37, (103, 69, 48), ORANGE)
        image.ellipse(cx + 27, y + 380, 82, 30, (87, 56, 43), ORANGE)
    for effect_path in visual.get("effects", []):
        effect_asset = _load_visual_asset(effect_path)
        if effect_asset:
            rgba, source_width, source_height = effect_asset
            image.composite_rgba(rgba, source_width, source_height, x + 145, y + 245, 285, 285)
    image.text(x + 25, y + 218, "VISUAL: " + visual.get("key", "idle").upper(), ORANGE, 1)
    image.text(x + 35, y + 92, "OLF", MAGENTA, 1); image.text(x + 510, y + 92, "VIS", BLUE, 1); image.text(x + 35, y + 145, "CX", ORANGE, 1); image.text(x + 510, y + 145, "MB", GREEN, 1); image.text(x + 35, y + 195, "SEZ", PURPLE, 1)


def render_dashboard(brain, highlight=None, stimulus_snapshot=None, behavior_snapshot=None,
                     visual_override=None):
    """Render a live GroupBrain state; the result supports ``.save(..., 'PNG')``."""
    image = DashboardImage()
    states, drives = dict(getattr(brain, "this_state", {})), dict(getattr(brain, "drives", {}))
    groups, stimuli = list(getattr(brain, "groups", sorted(states))), dict(getattr(brain, "stimulate", {}))
    motor = dict(getattr(brain, "last_accum", {}))
    fired = set(highlight if highlight is not None else getattr(brain, "last_fired", set()))
    behavior, tick = str(getattr(brain, "current_behavior", "idle")).upper(), getattr(brain, "tick_count", 0)
    # Command bursts can contain a real short-lived behavior (for example,
    # flight) that has settled before Discord receives the PNG.  The
    # controller's recorded behavior arc is still GroupBrain output, not a
    # command-derived animation instruction.
    visual = visual_state(behavior_snapshot or behavior,
                          stimulus_snapshot if stimulus_snapshot is not None else stimuli, tick,
                          visual_override=visual_override)
    for xx in range(0, WIDTH, 70): image.line(xx, 0, xx, HEIGHT, (5, 24, 35))
    for yy in range(0, HEIGHT, 56): image.line(0, yy, WIDTH, yy, (5, 24, 35))

    _panel(image, 20, 18, 340, 88, "FLY BRAIN", ORANGE); image.text(42, 61, "LIVE NEURAL SIMULATION", CYAN, 1)
    _panel(image, 375, 18, 510, 88, "CURRENT BEHAVIOR"); image.text(580, 58, behavior, GREEN if behavior in ("IDLE", "REST") else ORANGE, 3, 15); image.text(397, 84, "SENSE  PROCESS  DECIDE  ACT", MUTED, 1)
    _panel(image, 900, 18, 480, 88, "SYSTEM"); image.text(922, 57, "TICK: " + str(tick), CYAN, 2); image.text(1120, 57, "LIVE", GREEN, 2); image.text(922, 82, "BEHAVIOR: " + behavior, MUTED, 1, 34)

    _panel(image, 20, 124, 280, 590, "DRIVES AND STATE")
    for index, (name, key, color) in enumerate((("HUNGER", "hunger", MAGENTA), ("FEAR", "fear", PURPLE), ("FATIGUE", "fatigue", BLUE), ("CURIOSITY", "curiosity", ORANGE), ("GROOMING", "groom", GREEN), ("REWARD", "positive_valence", GREEN), ("AVERSIVE", "aversive_valence", MAGENTA))): _meter(image, 40, 172 + index * 48, name, drives.get(key, 0), color)
    image.line(38, 515, 282, 515, CYAN_DIM); image.text(40, 532, "LIVE INPUTS", CYAN, 1)
    inputs = (("LIGHT", stimuli.get("lightLevel", "N/A")), ("TEMP", stimuli.get("temperature", "N/A")), ("WIND", stimuli.get("windStrength", 0.0) if stimuli.get("wind") else 0.0), ("FOOD", 1.0 if stimuli.get("foodContact") or stimuli.get("foodNearby") else 0.0), ("THREAT", 1.0 if stimuli.get("dangerOdor") or stimuli.get("nociception") else 0.0))
    for index, (name, value) in enumerate(inputs): image.text(40, 558 + index * 29, name, MUTED, 1); image.text(160, 558 + index * 29, f"{value:.2f}" if isinstance(value, (int, float)) else "N/A", TEXT, 1)
    image.text(40, 680, "STIMULUS", CYAN, 1); image.text(40, 700, _stimulus(stimuli, fired), ORANGE, 1, 30)

    _panel(image, 315, 124, 575, 590, "NEURAL FIELD"); _hero(image, 315, 124, states, visual, tick)
    for index, action in enumerate(("IDLE", "WALK", "FEED", "GROOM", "SCARE", "BURN", "SHOCK", "SLEEP")):
        x, active = 330 + index * 67, action == behavior or (action == "SLEEP" and behavior == "REST")
        image.rectangle(x, 665, 60, 28, PANEL_ALT if active else (5, 15, 24)); image.line(x, 665, x + 60, 665, GREEN if active else CYAN_DIM); image.text(x + 4, 676, action, GREEN if active else MUTED, 1, 9)

    _panel(image, 905, 124, 475, 590, "NEURAL ACTIVITY")
    active = sorted(groups, key=lambda group: (group not in fired, -max(0.0, states.get(group, 0.0))))[:8]
    image.text(1125, 145, "TOP ACTIVE", CYAN, 1)
    for index, group in enumerate(active):
        value, color = states.get(group, 0.0), _color(group); intensity = max(0, min(1, max(0, value) / FIRE_THRESHOLD)); y = 170 + index * 20
        image.text(925, y, group, ORANGE if group in fired else TEXT, 1, 17); image.rectangle(1037, y, 175, 8, (20, 34, 53)); image.rectangle(1038, y + 1, int(173 * intensity), 6, ORANGE if group in fired else color); image.text(1218, y, f"{value:.1f}", ORANGE if group in fired else MUTED, 1)
    image.line(923, 340, 1360, 340, CYAN_DIM); image.text(925, 353, "MOTOR OUTPUT", CYAN, 1)
    output = "  ".join(f"{name}:{value:.1f}" for name, value in sorted(motor.items()) if value > 0) or "NO ACTIVE MOTOR READOUT"; image.text(925, 374, output, TEXT, 1, 65)
    image.text(925, 398, "RECENT FIRED", ORANGE, 1); image.text(925, 418, ", ".join(sorted(fired)[:6]) or "NONE", ORANGE if fired else MUTED, 1, 65)
    image.line(923, 440, 1360, 440, CYAN_DIM); image.text(925, 452, "FUNCTIONAL GROUP MATRIX", CYAN, 1)
    rows = max(1, (len(groups) + 2) // 3)
    for index, group in enumerate(groups):
        column, row = divmod(index, rows); x, y, value = 925 + column * 145, 474 + row * 11, states.get(group, 0.0)
        image.text(x, y, group, ORANGE if group in fired else _color(group), 1, 14); image.text(x + 87, y, f"{value:.0f}", TEXT if value >= 0 else MUTED, 1, 5)

    _panel(image, 20, 732, 820, 220, "NEURAL FLOW AND EVENT TRACE"); image.text(44, 775, _flow(brain, fired), ORANGE if fired else MUTED, 2, 57); image.text(44, 810, "CURRENT STIMULUS: " + _stimulus(stimuli, fired), CYAN, 1, 90); image.text(44, 842, "RECENT EVENTS", CYAN, 1)
    history = list(getattr(brain, "history", []))[-4:]
    if history:
        for index, event in enumerate(reversed(history)): image.text(44, 862 + index * 18, f"T{event.get('tick', '?')}: {event.get('event', '')}", TEXT, 1, 110)
    else: image.text(44, 862, "NO RECORDED EVENTS", MUTED, 1)
    _panel(image, 855, 732, 525, 220, "LIVE READOUT"); image.text(878, 776, "ACTIVE GROUPS: " + str(sum(1 for value in states.values() if value > 0)), GREEN, 1); image.text(878, 802, "FIRING GROUPS: " + str(len(fired)), ORANGE, 1); image.text(878, 828, "HABITUATION: " + str(len(getattr(brain, "habituation", {}))) + " PATHWAYS", PURPLE, 1); image.text(878, 870, "LIVE DATA ONLY - NO SYNTHETIC METRICS", MUTED, 1)
    image.text(20, 975, "DROSOPHILA SIMULATION / OBSERVE - EXPERIMENT - UNDERSTAND", CYAN_DIM, 1)
    return image
