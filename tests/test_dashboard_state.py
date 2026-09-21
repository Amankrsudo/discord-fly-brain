import brain_dashboard


class _Brain:
    this_state = {}
    groups = []
    drives = {
        "hunger": 0.1,
        "fear": 0.2,
        "fatigue": 0.3,
        "curiosity": 0.4,
        "groom": 0.5,
        "positive_valence": 0.67,
        "aversive_valence": 0.78,
    }
    stimulate = {"lightLevel": 1.0, "temperature": 0.5}
    last_accum = {}
    last_fired = set()
    current_behavior = "idle"
    tick_count = 0


def test_dashboard_reads_live_valence_values(monkeypatch):
    captured = []

    def capture_meter(image, x, y, name, value, color):
        captured.append((name, value))

    monkeypatch.setattr(brain_dashboard, "_meter", capture_meter)
    brain_dashboard.render_dashboard(_Brain())

    assert ("REWARD", 0.67) in captured
    assert ("AVERSIVE", 0.78) in captured


def test_dashboard_labels_existing_valence_state(monkeypatch):
    captured = []

    def capture_text(image, x, y, value, *args, **kwargs):
        captured.append(str(value).upper())

    monkeypatch.setattr(brain_dashboard.DashboardImage, "text", capture_text)
    brain_dashboard.render_dashboard(_Brain())

    assert "VALENCE AVERSIVE" in captured


def _dashboard_snapshot(margin=0.05):
    return {
        "stimuli": {
            "lightLevel": 0.2,
            "temperature": 0.8,
            "foodNearby": True,
            "dangerOdor": False,
            "nociception": False,
        },
        "light_state": {
            "intensity": 0.2,
            "preferred": 0.6,
            "phototaxis_bias": 0.42,
        },
        "light_memory": {"reward": 0.31, "threat": 0.04, "habituation": 0.12},
        "threat_signal": 0.18,
        "memory": {
            "events": [{"type": "food", "valence": 1.0, "strength": 0.84}],
            "associations": {
                "reward": {"food": 1.4},
                "threat": {"scare": 0.6},
            },
            "habituation": {"light": 0.12},
            "sensitization": {"scare": 0.2},
        },
        "decision": {
            "current_behavior": "feed",
            "winning_behavior": "feed",
            "winning_score": 0.82,
            "runner_up_behavior": "fly",
            "runner_up_score": 0.61,
            "decision_margin": margin,
            "competing_scores": {"feed": 0.82, "fly": 0.61, "explore": 0.39, "idle": 0.21},
            "drive_contributions": {
                "feed": {"hunger": 0.31, "food_memory": 0.18, "fear": -0.07, "fatigue": -0.02},
            },
        },
    }


def test_dashboard_renders_snapshot_state_panels(monkeypatch):
    captured = []

    def capture_text(image, x, y, value, *args, **kwargs):
        captured.append(str(value).upper())

    monkeypatch.setattr(brain_dashboard.DashboardImage, "text", capture_text)
    brain_dashboard.render_dashboard(_Brain(), snapshot=_dashboard_snapshot())

    assert "MATING" in captured
    assert any("FOOD 1.40" in value for value in captured)
    assert any("POSITIVE: FOOD" in value for value in captured)
    assert any("NEGATIVE: SCARE" in value for value in captured)
    assert "BELOW PREFERENCE" in captured
    assert "PHOTOTAXIS" in captured
    assert any("RUNNER FLY" in value for value in captured)
    assert "CONFLICT" in captured
    assert any("WHY HUNGER" in value for value in captured)


def test_dashboard_uses_confidence_from_actual_decision_margin(monkeypatch):
    captured = []

    def capture_text(image, x, y, value, *args, **kwargs):
        captured.append(str(value).upper())

    monkeypatch.setattr(brain_dashboard.DashboardImage, "text", capture_text)
    brain_dashboard.render_dashboard(_Brain(), snapshot=_dashboard_snapshot(margin=0.42))

    assert "CONFIDENT" in captured


def test_dashboard_legacy_brain_without_snapshot_still_renders():
    image = brain_dashboard.render_dashboard(_Brain())

    assert image.width == 1400
    assert image.height == 1420
    assert any(image.pixels)