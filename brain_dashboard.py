"""Dependency-light, live Field Notebook renderer for the Discord fly brain."""

import os
import struct
import zlib

from PIL import Image, ImageDraw, ImageFont

from dashboard_animation import visual_state


WIDTH, HEIGHT = 1400, 1420
FIRE_THRESHOLD = 22.0

# Dark Field Notebook presentation tokens. Existing panel positions and
# dimensions remain unchanged in Phase 1.
BG = (11, 17, 16)               # #0B1110
PANEL = (17, 26, 24)            # #111A18
PANEL_ALT = (21, 33, 30)        # #15211E
TEXT = (228, 236, 231)          # #E4ECE7
MUTED = (158, 173, 165)         # #9EADA5
DIVIDER = (42, 57, 52)           # #2A3934
GREEN = (95, 175, 143)           # #5FAF8F
BLUE = (92, 158, 170)            # #5C9EAA
ORANGE = (211, 154, 82)          # #D39A52
PURPLE = (164, 119, 155)         # #A4779B
METER_TRACK = (38, 52, 47)       # #26342F
CYAN, CYAN_DIM = BLUE, DIVIDER
MAGENTA = PURPLE
CORNER_RADIUS = 12
SPACE_8, SPACE_12, SPACE_16, SPACE_24 = 8, 12, 16, 24
SPACING_SCALE = (SPACE_8, SPACE_12, SPACE_16, SPACE_24)
FONT_DIRECTORY = os.path.join(os.path.dirname(__file__), "dashboard assests", "fonts")
FONT_REGULAR_PATH = os.path.join(FONT_DIRECTORY, "SourceSans3-Regular.ttf")
FONT_SEMIBOLD_PATH = os.path.join(FONT_DIRECTORY, "SourceSans3-Semibold.ttf")
HERO_ASSET_PATH = os.path.join(os.path.dirname(__file__), "dashboard assests", "fly_hero_human_commons_ccby.png")
_HERO_ASSET = None



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

    def rounded_rectangle(self, x, y, width, height, fill, outline=DIVIDER,
                          radius=CORNER_RADIUS):
        x, y, width, height = int(x), int(y), int(width), int(height)
        if width <= 0 or height <= 0:
            return
        radius = max(0, min(int(radius), width // 2, height // 2))
        card = Image.new("RGB", (width, height), fill)
        ImageDraw.Draw(card).rounded_rectangle(
            (0, 0, width - 1, height - 1), radius=radius,
            fill=fill, outline=outline, width=1,
        )
        left, top = max(0, x), max(0, y)
        right, bottom = min(self.width, x + width), min(self.height, y + height)
        if left >= right or top >= bottom:
            return
        source = card.crop((left - x, top - y, right - x, bottom - y)).tobytes()
        row_size = (right - left) * 3
        for row in range(bottom - top):
            target = ((top + row) * self.width + left) * 3
            self.pixels[target:target + row_size] = source[row * row_size:(row + 1) * row_size]

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
        value = str(value).upper()[:limit]
        if not value:
            return
        font_size = {1: 12, 2: 18, 3: 24}.get(scale, max(12, int(12 * scale)))
        font_path = FONT_SEMIBOLD_PATH if scale > 1 else FONT_REGULAR_PATH
        font = ImageFont.truetype(font_path, font_size)
        digit_advance = max(font.getlength(digit) for digit in "0123456789")
        advances = [digit_advance if char.isdecimal() else font.getlength(char) for char in value]
        mask = Image.new("L", (max(1, int(sum(advances)) + 4), font_size + 8), 0)
        draw = ImageDraw.Draw(mask)
        cursor = 1
        for char, advance in zip(value, advances):
            glyph_advance = font.getlength(char)
            glyph_x = cursor + (advance - glyph_advance) / 2 if char.isdecimal() else cursor
            draw.text((glyph_x, 1), char, font=font, fill=255)
            cursor += advance
        x, y = int(x), int(y)
        for mask_y in range(mask.height):
            target_y = y + mask_y
            if target_y < 0 or target_y >= self.height:
                continue
            for mask_x in range(mask.width):
                alpha = mask.getpixel((mask_x, mask_y))
                target_x = x + mask_x
                if not alpha or target_x < 0 or target_x >= self.width:
                    continue
                target = (target_y * self.width + target_x) * 3
                inverse = 255 - alpha
                for channel in range(3):
                    self.pixels[target + channel] = (
                        color[channel] * alpha + self.pixels[target + channel] * inverse
                    ) // 255

    def save(self, file, format=None):
        if format and format.upper() != "PNG":
            raise ValueError("DashboardImage only supports PNG output")
        rows = b"".join(b"\x00" + self.pixels[y * self.width * 3:(y + 1) * self.width * 3] for y in range(self.height))
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        file.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def _panel(image, x, y, width, height, title, accent=CYAN):
    image.rounded_rectangle(x, y, width, height, PANEL, DIVIDER, CORNER_RADIUS)
    image.text(x + SPACE_16, y + SPACE_12, title, accent, 2)


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
    if group.startswith("DN") or group.startswith("MN"): return ORANGE
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
    image.rectangle(x + 92, y, 136, 10, METER_TRACK)
    image.rectangle(x + 93, y + 1, int(134 * value), 8, color)
    image.text(x + 238, y, f"{value:.2f}", color, 1)


def _signed_meter(image, x, y, name, value, color):
    value = max(-1.0, min(1.0, float(value)))
    image.text(x, y, name, TEXT, 1)
    image.rectangle(x + 92, y, 136, 10, METER_TRACK)
    center = x + 160
    image.line(center, y, center, y + 10, MUTED)
    length = int(66 * abs(value))
    if value >= 0:
        image.rectangle(center, y + 1, length, 8, color)
    else:
        image.rectangle(center - length, y + 1, length, 8, color)
    image.text(x + 238, y, f"{value:+.2f}", color, 1)


def _snapshot_memory(brain, snapshot):
    memory = snapshot.get("memory") if isinstance(snapshot, dict) else None
    if isinstance(memory, dict):
        return memory
    summary = getattr(brain, "memory_summary", None)
    return summary(limit=4) if callable(summary) else {}


def _snapshot_decision(brain, snapshot):
    decision = snapshot.get("decision") if isinstance(snapshot, dict) else None
    if isinstance(decision, dict):
        return decision
    summary = getattr(brain, "decision_summary", None)
    return summary() if callable(summary) else {}


def _snapshot_light(brain, snapshot):
    light = snapshot.get("light_state") if isinstance(snapshot, dict) else None
    if isinstance(light, dict):
        return light
    return dict(getattr(brain, "light_state", {}))


def _snapshot_social(brain, snapshot):
    social = snapshot.get("social") if isinstance(snapshot, dict) else None
    if isinstance(social, dict):
        return social
    context = dict(getattr(brain, "social_state", {}))
    return {
        "count": 1,
        "current_fly": "fly_01",
        "current": {"id": "fly_01", "behavior": getattr(brain, "current_behavior", "idle"),
                     "social": context, "decision": getattr(brain, "decision_summary", lambda: {})()},
        "agents": [{"id": "fly_01", "behavior": getattr(brain, "current_behavior", "idle"),
                    "social": context}],
    }


def _association_label(associations, category):
    values = associations.get(category, {}) if isinstance(associations, dict) else {}
    if not values:
        return "NONE"
    key, value = max(values.items(), key=lambda item: float(item[1]))
    return f"{key.upper()} {float(value):.2f}"


def _memory_panel(image, x, y, width, height, brain, snapshot):
    _panel(image, x, y, width, height, "MEMORY", PURPLE)
    memory = _snapshot_memory(brain, snapshot)
    events = memory.get("events", []) if isinstance(memory, dict) else []
    image.text(x + 18, y + 48, "RECENT", CYAN, 1)
    if events:
        for index, event in enumerate(events[:3]):
            label = f"{event.get('type', 'UNKNOWN')} {event.get('valence', 0.0):+.2f} S{event.get('strength', 0.0):.2f}"
            image.text(x + 18, y + 67 + index * 18, label, TEXT, 1, 43)
    else:
        image.text(x + 18, y + 67, "NO RECENT MEMORIES", MUTED, 1)
    associations = memory.get("associations", {}) if isinstance(memory, dict) else {}
    image.text(x + 18, y + 128, "POSITIVE: " + _association_label(associations, "reward"), GREEN, 1, 55)
    image.text(x + 18, y + 149, "NEGATIVE: " + _association_label(associations, "threat"), MAGENTA, 1, 55)
    habituation = memory.get("habituation", {}) if isinstance(memory, dict) else {}
    sensitization = memory.get("sensitization", {}) if isinstance(memory, dict) else {}
    image.text(x + 18, y + 183, "HAB " + str(len(habituation)) + "  SENS " + str(len(sensitization)), PURPLE, 1)


def _sensory_panel(image, x, y, width, height, brain, snapshot, stimuli):
    _panel(image, x, y, width, height, "SENSORY / LIGHT", BLUE)
    light = _snapshot_light(brain, snapshot)
    intensity = float(light.get("intensity", stimuli.get("lightLevel", 0.0)))
    preferred = float(light.get("preferred", 0.6))
    phototaxis = float(light.get("phototaxis_bias", 0.0))
    relation = "NEAR PREFERENCE"
    if intensity < preferred - 0.08:
        relation = "BELOW PREFERENCE"
    elif intensity > preferred + 0.08:
        relation = "ABOVE PREFERENCE"
    _meter(image, x + 18, y + 48, "LIGHT", intensity, BLUE)
    _meter(image, x + 18, y + 68, "PREFERRED", preferred, CYAN)
    _signed_meter(image, x + 18, y + 88, "PHOTOTAXIS", phototaxis, ORANGE)
    light_bias = snapshot.get("light_memory", {})
    if not light_bias and hasattr(brain, "memory"):
        light_bias = brain.memory.light_association_bias()
    image.text(x + 18, y + 110, relation, ORANGE, 1, 49)
    image.text(x + 18, y + 131, "LIGHT REWARD " + f"{light_bias.get('reward', 0.0):.2f}", GREEN, 1)
    image.text(x + 18, y + 149, "LIGHT THREAT " + f"{light_bias.get('threat', 0.0):.2f}", MAGENTA, 1)
    temperature = stimuli.get("temperature", 0.5)
    thermal = "WARM" if temperature > 0.65 else "COOL" if temperature < 0.35 else "NEUTRAL"
    threat = snapshot.get("threat_signal", 0.0)
    food = "CONTACT" if stimuli.get("foodContact") else "NEARBY" if stimuli.get("foodNearby") else "NONE"
    danger = "YES" if stimuli.get("dangerOdor") else "NO"
    pain = "YES" if stimuli.get("nociception") else "NO"
    image.text(x + 18, y + 171, "THERMAL " + thermal, ORANGE, 1)
    image.text(x + 18, y + 189, "FOOD " + food + " DANGER " + danger + " PAIN " + pain, TEXT, 1, 55)
    image.text(x + 210, y + 171, "THREAT " + f"{float(threat):.2f}", MAGENTA, 1)


def _decision_panel(image, x, y, width, height, brain, snapshot):
    _panel(image, x, y, width, height, "DECISION COMPETITION", GREEN)
    decision = _snapshot_decision(brain, snapshot)
    current = str(decision.get("current_behavior", getattr(brain, "current_behavior", "idle"))).upper()
    winning = float(decision.get("winning_score", 0.0))
    runner = str(decision.get("runner_up_behavior", "NONE")).upper()
    runner_score = float(decision.get("runner_up_score", 0.0))
    margin = float(decision.get("decision_margin", 0.0))
    confidence = "CONFLICT" if margin < 0.12 else "CONFIDENT"
    confidence_color = MAGENTA if confidence == "CONFLICT" else GREEN
    image.text(x + 18, y + 46, current, confidence_color, 2, 13)
    image.text(x + 150, y + 51, f"SCORE {winning:.2f}", TEXT, 1)
    image.text(x + 18, y + 70, "RUNNER " + runner + f" {runner_score:.2f}", MUTED, 1, 39)
    image.text(x + 225, y + 70, confidence, confidence_color, 1)
    image.text(x + 18, y + 88, "MARGIN " + f"{margin:.2f}", CYAN, 1)
    scores = decision.get("competing_scores", {}) if isinstance(decision, dict) else {}
    ranked = sorted(scores.items(), key=lambda item: (-float(item[1]), item[0]))[:4]
    for index, (name, score) in enumerate(ranked):
        bar_y = y + 108 + index * 18
        value = max(0.0, min(1.0, float(score)))
        image.text(x + 18, bar_y, name.upper(), TEXT, 1, 12)
        image.rectangle(x + 94, bar_y, 170, 8, METER_TRACK)
        image.rectangle(x + 95, bar_y + 1, int(168 * value), 6, GREEN if name.upper() == current else BLUE)
        image.text(x + 272, bar_y, f"{value:.2f}", GREEN if name.upper() == current else MUTED, 1)
    parts = decision.get("drive_contributions", {}).get(current.lower(), {})
    if parts:
        strongest = sorted(parts.items(), key=lambda item: -abs(float(item[1])))[:2]
        summary = "WHY " + " ".join(f"{key.upper()} {float(value):+.2f}" for key, value in strongest)
        image.text(x + 18, y + 190, summary, ORANGE, 1, 48)


def _social_panel(image, x, y, width, height, brain, snapshot):
    _panel(image, x, y, width, height, "SOCIAL FIELD", MAGENTA)
    social = _snapshot_social(brain, snapshot)
    current = social.get("current") or {}
    context = current.get("social", {})
    image.text(x + 18, y + 46, "FLIES " + str(social.get("count", 1)), CYAN, 1)
    image.text(x + 160, y + 46, "CURRENT " + str(social.get("current_fly", "fly_01")).upper(), GREEN, 1)
    image.text(x + 360, y + 46, "BEHAVIOR " + str(current.get("behavior", "idle")).upper(), ORANGE, 1, 22)
    nearby = context.get("nearby_flies", [])
    image.text(x + 18, y + 70, "NEARBY " + str(context.get("nearby_count", len(nearby))), TEXT, 1)
    image.text(x + 160, y + 70, "PROXIMITY " + f"{float(context.get('proximity', 0.0)):.2f}", BLUE, 1)
    image.text(x + 340, y + 70, "ACTIVITY " + f"{float(context.get('social_activity', 0.0)):.2f}", ORANGE, 1)
    image.text(x + 520, y + 70, "CONTACT " + ("YES" if context.get("contact") else "NO"), GREEN, 1)
    image.text(x + 18, y + 94, "APPROACH " + f"{float(context.get('approach_tendency', 0.0)):.2f}", GREEN, 1)
    image.text(x + 190, y + 94, "AVOID " + f"{float(context.get('avoidance_tendency', 0.0)):.2f}", MAGENTA, 1)
    image.text(x + 340, y + 94, "CROWD " + f"{float(context.get('overcrowding', 0.0)):.2f}", PURPLE, 1)
    image.text(x + 520, y + 94, "FOLLOW " + str(context.get("following_target") or "NONE").upper(), CYAN, 1, 18)
    if nearby:
        entries = "  ".join(f"{item.get('id', '?')}:{float(item.get('distance', 0.0)):.1f}"
                            for item in nearby[:6])
        image.text(x + 18, y + 120, "NEIGHBORS " + entries, TEXT, 1, 100)
    else:
        image.text(x + 18, y + 120, "NEIGHBORS NONE", MUTED, 1)
    decision = current.get("decision", {})
    parts = decision.get("drive_contributions", {}).get(str(current.get("behavior", "")).lower(), {})
    social_parts = [(key, value) for key, value in parts.items()
                    if "social" in key or "follow" in key or "crowd" in key]
    summary = "SOCIAL CONTRIBUTION " + " ".join(f"{key.upper()} {float(value):+.2f}"
                                                for key, value in social_parts[:3])
    image.text(x + 18, y + 148, summary if social_parts else "SOCIAL CONTRIBUTION NONE", ORANGE, 1, 110)


_BIOLOGICAL_SECTIONS = {
    "BIOLOGICAL CIRCUIT", "ANATOMY VERIFIED", "LITERATURE",
    "MODEL-DERIVED", "UNRESOLVED / ASSUMPTION",
}


def _biological_panel(image, x, y, width, height, research):
    """Render the stored Fly Brain 3.0 research summary as a static panel.

    The values are presentation-only research outputs, never live simulation
    state, so the panel is drawn verbatim from the supplied summary text.
    """
    _panel(image, x, y, width, height, "FLY BRAIN 3.0", PURPLE)
    lines = [line.strip() for line in str(research).splitlines() if line.strip()]
    line_y = y + 46
    for line in lines:
        structural = line in _BIOLOGICAL_SECTIONS or line.startswith("MODEL OUTPUTS")
        image.text(x + 18, line_y, line, ORANGE if structural else TEXT, 1, 200)
        line_y += 20


def _hero(image, x, y, states, visual, tick=0):
    image.rectangle(x + 10, y + 40, 555, 500, PANEL_ALT)
    for xx in range(x + 25, x + 565, 44): image.line(xx, y + 45, xx, y + 535, DIVIDER)
    for yy in range(y + 60, y + 535, 36): image.line(x + 15, yy, x + 565, yy, DIVIDER)
    image.text(x + 25, y + 52, "LIVE FUNCTIONAL MAP", CYAN, 1)
    cx, cy = x + 285, y + 170
    for prefix, dx, dy, color in (("OLF", -90, -10, MAGENTA), ("VIS", 90, -10, BLUE), ("CX", -35, 55, ORANGE), ("MB", 55, 55, GREEN), ("SEZ", 0, 95, PURPLE)):
        level = max((max(0.0, states.get(group, 0.0)) for group in states if group.startswith(prefix)), default=0.0)
        radius = 23 + int(min(1.0, level / FIRE_THRESHOLD) * 14)
        image.ellipse(cx + dx, cy + dy, radius, radius - 5, color, CYAN_DIM)
        image.text(cx + dx - 10, cy + dy - 3, prefix, TEXT, 1)
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
        image.ellipse(cx - 96, y + 370, 38, 32, (158, 119, 80), ORANGE)
        image.ellipse(cx - 45, y + 374, 57, 37, (139, 105, 75), ORANGE)
        image.ellipse(cx + 27, y + 380, 82, 30, (120, 94, 69), ORANGE)
    for effect_path in visual.get("effects", []):
        effect_asset = _load_visual_asset(effect_path)
        if effect_asset:
            rgba, source_width, source_height = effect_asset
            image.composite_rgba(rgba, source_width, source_height, x + 145, y + 245, 285, 285)
    image.text(x + 25, y + 218, "VISUAL: " + visual.get("key", "idle").upper(), ORANGE, 1)
    image.text(x + 35, y + 92, "OLF", MAGENTA, 1); image.text(x + 510, y + 92, "VIS", BLUE, 1); image.text(x + 35, y + 145, "CX", ORANGE, 1); image.text(x + 510, y + 145, "MB", GREEN, 1); image.text(x + 35, y + 195, "SEZ", PURPLE, 1)


def render_dashboard(brain, highlight=None, stimulus_snapshot=None, behavior_snapshot=None,
                     visual_override=None, snapshot=None, biological_research=None):
    """Render a live GroupBrain state; the result supports ``.save(..., 'PNG')``."""
    # The biological research panel is a static, opt-in appendix. It only
    # extends the canvas when the 3.0B layer is on, so the default 2.0
    # dashboard keeps its exact 1400x1420 geometry.
    canvas_height = 1760 if biological_research else HEIGHT
    image = DashboardImage(WIDTH, canvas_height)
    snapshot = snapshot if isinstance(snapshot, dict) else {}
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

    _panel(image, 20, 18, 340, 88, "FLY BRAIN", ORANGE); image.text(42, 61, "LIVE NEURAL SIMULATION", CYAN, 1)
    _panel(image, 375, 18, 510, 88, "CURRENT BEHAVIOR"); image.text(580, 58, behavior, GREEN if behavior in ("IDLE", "REST") else ORANGE, 3, 15); image.text(397, 84, "SENSE  PROCESS  DECIDE  ACT", MUTED, 1)
    _panel(image, 900, 18, 480, 88, "SYSTEM"); image.text(922, 57, "TICK: " + str(tick), CYAN, 2); image.text(1120, 57, "LIVE", GREEN, 2); image.text(922, 82, "BEHAVIOR: " + behavior, MUTED, 1, 34)

    _panel(image, 20, 124, 280, 590, "DRIVES AND STATE")
    for index, (name, key, color) in enumerate((("HUNGER", "hunger", MAGENTA), ("FEAR", "fear", PURPLE), ("FATIGUE", "fatigue", BLUE), ("CURIOSITY", "curiosity", ORANGE), ("GROOMING", "groom", GREEN), ("MATING", "mating", ORANGE), ("REWARD", "positive_valence", GREEN), ("AVERSIVE", "aversive_valence", MAGENTA))): _meter(image, 40, 168 + index * 36, name, drives.get(key, 0), color)
    positive = float(drives.get("positive_valence", 0.0))
    aversive = float(drives.get("aversive_valence", 0.0))
    valence_label = "REWARDING" if positive > aversive else "AVERSIVE" if aversive > positive else "NEUTRAL"
    valence_color = GREEN if valence_label == "REWARDING" else MAGENTA if valence_label == "AVERSIVE" else MUTED
    image.text(40, 447, "VALENCE " + valence_label, valence_color, 1)
    image.line(38, 465, 282, 465, CYAN_DIM); image.text(40, 480, "LIVE INPUTS", CYAN, 1)
    inputs = (("LIGHT", stimuli.get("lightLevel", "N/A")), ("TEMP", stimuli.get("temperature", "N/A")), ("WIND", stimuli.get("windStrength", 0.0) if stimuli.get("wind") else 0.0), ("FOOD", 1.0 if stimuli.get("foodContact") or stimuli.get("foodNearby") else 0.0), ("THREAT", 1.0 if stimuli.get("dangerOdor") or stimuli.get("nociception") else 0.0))
    for index, (name, value) in enumerate(inputs): image.text(40, 503 + index * 24, name, MUTED, 1); image.text(160, 503 + index * 24, f"{value:.2f}" if isinstance(value, (int, float)) else "N/A", TEXT, 1)
    image.text(40, 635, "STIMULUS", CYAN, 1); image.text(40, 655, _stimulus(stimuli, fired), ORANGE, 1, 30)

    _panel(image, 315, 124, 575, 590, "NEURAL FIELD"); _hero(image, 315, 124, states, visual, tick)
    for index, action in enumerate(("IDLE", "WALK", "FEED", "GROOM", "SCARE", "BURN", "SHOCK", "SLEEP")):
        x, active = 330 + index * 67, action == behavior or (action == "SLEEP" and behavior == "REST")
        image.rectangle(x, 665, 60, 28, PANEL_ALT if active else PANEL); image.line(x, 665, x + 60, 665, GREEN if active else CYAN_DIM); image.text(x + 4, 676, action, GREEN if active else MUTED, 1, 9)

    _panel(image, 905, 124, 475, 590, "NEURAL ACTIVITY")
    active = sorted(groups, key=lambda group: (group not in fired, -max(0.0, states.get(group, 0.0))))[:8]
    image.text(1125, 145, "TOP ACTIVE", CYAN, 1)
    for index, group in enumerate(active):
        value, color = states.get(group, 0.0), _color(group); intensity = max(0, min(1, max(0, value) / FIRE_THRESHOLD)); y = 170 + index * 20
        image.text(925, y, group, ORANGE if group in fired else TEXT, 1, 17); image.rectangle(1037, y, 175, 8, METER_TRACK); image.rectangle(1038, y + 1, int(173 * intensity), 6, ORANGE if group in fired else color); image.text(1218, y, f"{value:.1f}", ORANGE if group in fired else MUTED, 1)
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

    _memory_panel(image, 20, 970, 500, 220, brain, snapshot)
    _sensory_panel(image, 535, 970, 390, 220, brain, snapshot, stimuli)
    _decision_panel(image, 940, 970, 440, 220, brain, snapshot)
    _social_panel(image, 20, 1210, 1360, 180, brain, snapshot)
    if biological_research:
        _biological_panel(image, 20, 1420, 1360, 300, biological_research)
        footer_y = 1735
    else:
        footer_y = 1405
    image.text(20, footer_y, "DROSOPHILA SIMULATION / OBSERVE - EXPERIMENT - UNDERSTAND", MUTED, 1)
    return image
