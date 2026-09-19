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