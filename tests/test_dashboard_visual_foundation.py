from pathlib import Path

import brain_dashboard


def test_field_notebook_palette_spacing_and_font_assets():
    assert brain_dashboard.BG == (11, 17, 16)
    assert brain_dashboard.PANEL == (17, 26, 24)
    assert brain_dashboard.PANEL_ALT == (21, 33, 30)
    assert brain_dashboard.TEXT == (228, 236, 231)
    assert brain_dashboard.MUTED == (158, 173, 165)
    assert brain_dashboard.DIVIDER == (42, 57, 52)
    assert brain_dashboard.GREEN == (95, 175, 143)
    assert brain_dashboard.BLUE == (92, 158, 170)
    assert brain_dashboard.ORANGE == (211, 154, 82)
    assert brain_dashboard.PURPLE == (164, 119, 155)
    assert brain_dashboard.METER_TRACK == (38, 52, 47)
    assert (
        brain_dashboard.SPACE_8,
        brain_dashboard.SPACE_12,
        brain_dashboard.SPACE_16,
        brain_dashboard.SPACE_24,
    ) == (8, 12, 16, 24)
    assert brain_dashboard.CORNER_RADIUS == 12
    assert Path(brain_dashboard.FONT_REGULAR_PATH).is_file()
    assert Path(brain_dashboard.FONT_SEMIBOLD_PATH).is_file()
    assert (Path(brain_dashboard.FONT_DIRECTORY) / "OFL.txt").is_file()


def test_dashboard_image_draws_rounded_card_and_source_sans_text():
    image = brain_dashboard.DashboardImage(100, 70)
    image.rounded_rectangle(10, 10, 60, 40, brain_dashboard.PANEL)
    image.text(20, 25, "VALUE 12.34", brain_dashboard.TEXT)

    assert image.pixels[0:3] == bytes(brain_dashboard.BG)
    center = (45 * image.width + 60) * 3
    assert image.pixels[center:center + 3] == bytes(brain_dashboard.PANEL)
    assert any(
        image.pixels[index:index + 3] != bytes(brain_dashboard.BG)
        for index in range(0, len(image.pixels), 3)
    )


def test_dashboard_canvas_and_cards_have_no_white_surface():
    image = brain_dashboard.DashboardImage(100, 70)
    image.rounded_rectangle(10, 10, 60, 40, brain_dashboard.PANEL)

    assert image.pixels[0:3] == bytes.fromhex("0B1110")
    assert bytes.fromhex("FFFFFF") not in image.pixels
    assert bytes(brain_dashboard.PANEL) in image.pixels
