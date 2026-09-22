import json

import pytest

from group_brain import GroupBrain

WEIGHTS_PATH = "group_weights.json"


def _fresh_drives():
    return GroupBrain(WEIGHTS_PATH).drives


def test_loaded_drives_are_clamped_to_zero_one():
    checkpoint = {"drives": {"hunger": 1.5, "fear": -0.4}}
    restored = GroupBrain.from_state_dict(WEIGHTS_PATH, checkpoint)

    assert restored.drives["hunger"] == 1.0
    assert restored.drives["fear"] == 0.0


def test_loaded_drives_replace_non_finite_with_defaults():
    defaults = _fresh_drives()
    checkpoint = {"drives": {
        "curiosity": "high", "fatigue": float("inf"),
        "groom": float("nan"), "mating": True, "positive_valence": False,
    }}
    restored = GroupBrain.from_state_dict(WEIGHTS_PATH, checkpoint)

    assert restored.drives["curiosity"] == defaults["curiosity"]
    assert restored.drives["fatigue"] == defaults["fatigue"]
    assert restored.drives["groom"] == defaults["groom"]
    assert restored.drives["mating"] == defaults["mating"]
    assert restored.drives["positive_valence"] == defaults["positive_valence"]


def test_loaded_drives_preserve_unknown_keys():
    checkpoint = {"drives": {"hunger": 0.5, "custom": 0.9}}
    restored = GroupBrain.from_state_dict(WEIGHTS_PATH, checkpoint)

    assert restored.drives["hunger"] == 0.5
    assert restored.drives["custom"] == 0.9


def test_loaded_overload_until_time_rejects_non_finite():
    for bad in ("soon", float("inf"), float("nan"), [1.0]):
        restored = GroupBrain.from_state_dict(WEIGHTS_PATH,
                                              {"overload_until_time": bad})
        assert restored.is_overloaded() is False


def test_loaded_overload_until_time_preserves_finite_future_timestamp():
    restored = GroupBrain.from_state_dict(WEIGHTS_PATH,
                                          {"overload_until_time": 1e18})
    assert restored.is_overloaded() is True


def test_loaded_this_state_rejects_non_finite_and_drops_unknown_groups():
    brain = GroupBrain(WEIGHTS_PATH)
    known = next(iter(brain.this_state))
    checkpoint = {"this_state": {known: float("nan"), "Z": 5.0}}
    restored = GroupBrain.from_state_dict(WEIGHTS_PATH, checkpoint)

    assert restored.this_state[known] == 0.0
    assert "Z" not in restored.this_state


def test_loaded_next_state_rejects_non_finite():
    brain = GroupBrain(WEIGHTS_PATH)
    known = next(iter(brain.next_state))
    checkpoint = {"next_state": {known: "x"}}
    restored = GroupBrain.from_state_dict(WEIGHTS_PATH, checkpoint)

    assert restored.next_state[known] == 0.0


def test_loaded_cooldown_until_drops_invalid_entries():
    checkpoint = {"cooldown_until": {"feed": "soon", "fly": 1e18}}
    restored = GroupBrain.from_state_dict(WEIGHTS_PATH, checkpoint)

    assert "feed" not in restored.cooldown_until
    assert restored.cooldown_until["fly"] == 1e18


def test_loaded_cooldown_until_replaces_non_dict():
    for bad in ([1, 2], "string", 42, None):
        restored = GroupBrain.from_state_dict(WEIGHTS_PATH,
                                              {"cooldown_until": bad})
        assert restored.cooldown_until == {}


def test_loaded_habituation_clamps_negative_and_drops_non_finite():
    checkpoint = {"habituation": {"light": -0.5, "touch": float("nan")}}
    restored = GroupBrain.from_state_dict(WEIGHTS_PATH, checkpoint)

    assert restored.habituation["light"] == 0.0
    assert "touch" not in restored.habituation