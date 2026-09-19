import time

from group_brain import GroupBrain, OVERLOAD_SECONDS


def test_overload_maxes_real_internal_state_and_recovers(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(time, "time", lambda: now[0])
    brain = GroupBrain("group_weights.json")

    brain.trigger_overload()

    assert brain.current_behavior == "overload"
    assert all(brain.drives[name] == 1.0 for name in (
        "fear", "positive_valence", "aversive_valence", "fatigue"))

    now[0] += OVERLOAD_SECONDS + 0.1
    brain.tick()

    assert brain.drives["fear"] < 1.0
    assert brain.drives["positive_valence"] < 1.0
    assert brain.drives["aversive_valence"] < 1.0
    assert brain.drives["fatigue"] < 1.0