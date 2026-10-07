from __future__ import annotations

import csv
import io
import struct
from pathlib import Path

import brain_dashboard
from biological_brain.status_summary import FLY_BRAIN_3_STATUS
from dashboard_animation import visual_state


class _Brain:
    this_state = {}
    groups = []
    drives = {
        "hunger": 0.1,
        "fear": 0.2,
        "fatigue": 0.3,
        "curiosity": 0.4,
        "groom": 0.5,
    }
    stimulate = {"lightLevel": 1.0, "temperature": 0.5}
    last_accum = {}
    last_fired = set()
    current_behavior = "idle"
    tick_count = 0


def test_human_made_hero_asset_is_loadable_and_discord_safe():
    path = brain_dashboard.HERO_ASSET_PATH
    with open(path, "rb") as asset:
        data = asset.read()

    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", data[16:24]) == (285, 170)
    assert len(data) < 1_000_000
    loaded = brain_dashboard._load_hero_asset()
    assert loaded is not None
    rgba, width, height = loaded
    assert (width, height) == (285, 170)
    assert any(rgba[index] == 0 for index in range(3, len(rgba), 4))


def test_dashboard_fallback_loads_hero_and_output_stays_below_upload_limit(monkeypatch):
    monkeypatch.setattr(
        brain_dashboard,
        "visual_state",
        lambda *args, **kwargs: {"key": "idle", "frame": None, "effects": []},
    )
    for research in (None, FLY_BRAIN_3_STATUS):
        image = brain_dashboard.render_dashboard(_Brain(), biological_research=research)
        assert (image.width, image.height) == (
            1400, 1760 if research else 1420
        )
        output = io.BytesIO()
        image.save(output, format="PNG")
        encoded = output.getvalue()
        assert encoded.startswith(b"\x89PNG\r\n\x1a\n")
        assert len(encoded) < 18 * 1024 * 1024


def test_source_license_attribution_and_original_are_recorded():
    original = Path("dashboard assests/fly_hero_transparent.png")
    replacement = Path(brain_dashboard.HERO_ASSET_PATH)
    assert original.is_file()
    assert replacement.is_file()

    with open("research/dashboard_asset_replacement_log.csv", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    record = next(row for row in rows if row["asset_id"] == "ASSET_8544FD3D037C")
    assert record["replacement_path"] == replacement.relative_to(Path.cwd()).as_posix()
    assert record["creator"] == "DataBase Center for Life Science (DBCLS)"
    assert record["license"] == "CC BY 4.0"
    assert record["attribution_required"] == "YES"
    assert record["status"] == "REPLACED_VALIDATED"

    licenses = Path("research/dashboard_asset_licenses.md").read_text(encoding="utf-8")
    assert "201902_Drosophila_melanogaster.svg" in licenses
    assert "Creative Commons Attribution 4.0" in licenses
    assert "Drosophila melanogaster, DBCLS, CC BY 4.0" in licenses


def test_commons_fire_overlay_loads_and_renders_in_existing_hero_path():
    path = Path(
        "dashboard assests/fly_behavior_assets_codex_v2/effects/fire_overlay.png"
    ).resolve()
    assert path.is_file()
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", data[16:24]) == (102, 102)
    assert data[24] == 8  # 8-bit PNG
    assert data[25] == 6  # RGBA PNG
    assert len(data) < 20_000

    loaded = brain_dashboard._load_png_asset(str(path))
    assert loaded is not None
    rgba, width, height = loaded
    assert (width, height) == (102, 102)
    assert any(rgba[index] == 0 for index in range(3, len(rgba), 4))
    assert any(rgba[index] > 0 for index in range(3, len(rgba), 4))
    label_pixels = 0
    for y in range(12):
        for x in range(width):
            pixel = (y * width + x) * 4
            if (
                rgba[pixel] > 220
                and rgba[pixel + 1] < 110
                and rgba[pixel + 2] > 130
                and rgba[pixel + 3] > 0
            ):
                label_pixels += 1
    assert label_pixels > 20

    visual = visual_state("idle", visual_override="burn")
    assert visual["key"] == "burn"
    assert Path(visual["effects"][0]).resolve() == path

    # Exercise the current _hero compositor with the real selected effect.
    canvas = brain_dashboard.DashboardImage(575, 540)
    brain_dashboard._hero(canvas, 0, 0, {}, visual)
    rendered_source_pixel = False
    for target_y in range(285):
        source_y = target_y * height // 285
        for target_x in range(285):
            source_x = target_x * width // 285
            source_index = (source_y * width + source_x) * 4
            if rgba[source_index + 3] != 255:
                continue
            target_index = ((245 + target_y) * canvas.width + 145 + target_x) * 3
            assert canvas.pixels[target_index:target_index + 3] == rgba[
                source_index:source_index + 3
            ]
            rendered_source_pixel = True
            break
        if rendered_source_pixel:
            break
    assert rendered_source_pixel

    record_path = Path("research/dashboard_asset_replacement_log.csv")
    with record_path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    record = next(row for row in rows if row["asset_id"] == "ACTIVE_FIRE_OVERLAY_PNG")
    assert Path(record["replacement_path"]).resolve() == path
    assert record["creator"] == "Carl Olsen"
    assert record["license"] == "CC BY 3.0"
    assert record["attribution_required"] == "YES"
    assert record["source_page"] == (
        "https://commons.wikimedia.org/wiki/"
        "File:Flame_-_Carl_Olsen_-_white_-_game-icons.svg"
    )
    assert "recolored" in record["conversion"]
    assert "rasterized" in record["conversion"]
    assert record["status"] == "REPLACED_VALIDATED"
