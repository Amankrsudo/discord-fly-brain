import math

import pytest

from diagnostics import format_diagnostics, get_brain_diagnostics, validate_brain_state
from group_brain import GroupBrain


def _make_brain():
    return GroupBrain.load("group_weights.json", "fly_state.json")


def _valid_brain_state():
    brain = _make_brain()
    brain.drives = {
        "hunger": 0.5,
        "fear": 0.2,
        "fatigue": 0.3,
        "curiosity": 0.4,
        "groom": 0.1,
    }
    brain.this_state = {"A": 1.0, "B": 2.0}
    brain.last_fired = {"A"}
    brain.groups = ["A", "B"]
    return brain


def test_get_brain_diagnostics_returns_expected_keys():
    brain = _make_brain()
    result = get_brain_diagnostics(brain)

    assert set(result.keys()) == {
        "tick_count",
        "current_behavior",
        "hunger",
        "fear",
        "fatigue",
        "curiosity",
        "grooming",
        "number_of_neural_groups",
        "number_of_active_groups",
        "number_of_recently_fired_groups",
    }

    assert isinstance(result["tick_count"], int)
    assert isinstance(result["current_behavior"], str)
    assert isinstance(result["hunger"], float)
    assert isinstance(result["fear"], float)
    assert isinstance(result["fatigue"], float)
    assert isinstance(result["curiosity"], float)
    assert isinstance(result["grooming"], float)
    assert isinstance(result["number_of_neural_groups"], int)
    assert isinstance(result["number_of_active_groups"], int)
    assert isinstance(result["number_of_recently_fired_groups"], int)


def test_format_diagnostics_is_string_and_contains_main_fields():
    brain = _make_brain()
    text = format_diagnostics(brain)

    assert isinstance(text, str)
    assert "Fly Brain Diagnostics" in text
    assert "tick_count:" in text
    assert "current_behavior:" in text
    assert "hunger:" in text
    assert "fear:" in text
    assert "fatigue:" in text
    assert "curiosity:" in text
    assert "grooming:" in text


def test_get_brain_diagnostics_is_read_only_and_uses_real_state():
    brain = _make_brain()
    before = brain.drives.copy()
    before_groups = len(brain.groups)

    result = get_brain_diagnostics(brain)

    assert brain.drives == before
    assert len(brain.groups) == before_groups
    assert math.isfinite(float(result["hunger"]))
    assert math.isfinite(float(result["fear"]))
    assert math.isfinite(float(result["fatigue"]))
    assert math.isfinite(float(result["curiosity"]))
    assert math.isfinite(float(result["grooming"]))


def test_validate_brain_state_missing_drives_dictionary():
    class NoDrivesBrain:
        this_state = {"A": 1.0}
        last_fired = {"A"}
        groups = ["A"]

    warnings = validate_brain_state(NoDrivesBrain())
    assert "missing drives dictionary." in warnings


def test_validate_brain_state_missing_hunger():
    brain = _valid_brain_state()
    brain.drives.pop("hunger")

    warnings = validate_brain_state(brain)
    assert "missing drive value: hunger." in warnings


def test_validate_brain_state_missing_fear():
    brain = _valid_brain_state()
    brain.drives.pop("fear")

    warnings = validate_brain_state(brain)
    assert "missing drive value: fear." in warnings


def test_validate_brain_state_missing_fatigue():
    brain = _valid_brain_state()
    brain.drives.pop("fatigue")

    warnings = validate_brain_state(brain)
    assert "missing drive value: fatigue." in warnings


def test_validate_brain_state_missing_curiosity():
    brain = _valid_brain_state()
    brain.drives.pop("curiosity")

    warnings = validate_brain_state(brain)
    assert "missing drive value: curiosity." in warnings


def test_validate_brain_state_missing_groom():
    brain = _valid_brain_state()
    brain.drives.pop("groom")

    warnings = validate_brain_state(brain)
    assert "missing drive value: groom." in warnings


def test_validate_brain_state_nan_drive_value():
    brain = _valid_brain_state()
    brain.drives["hunger"] = float("nan")

    warnings = validate_brain_state(brain)
    assert any("drive value is not finite: hunger=" in warning for warning in warnings)


def test_validate_brain_state_infinite_drive_value():
    brain = _valid_brain_state()
    brain.drives["fear"] = float("inf")

    warnings = validate_brain_state(brain)
    assert any("drive value is not finite: fear=" in warning for warning in warnings)


def test_validate_brain_state_drive_below_zero():
    brain = _valid_brain_state()
    brain.drives["fatigue"] = -0.1

    warnings = validate_brain_state(brain)
    assert any("drive value out of range: fatigue=" in warning for warning in warnings)


def test_validate_brain_state_drive_above_one():
    brain = _valid_brain_state()
    brain.drives["curiosity"] = 1.1

    warnings = validate_brain_state(brain)
    assert any("drive value out of range: curiosity=" in warning for warning in warnings)


def test_validate_brain_state_missing_this_state():
    brain = _valid_brain_state()
    delattr(brain, "this_state")

    warnings = validate_brain_state(brain)
    assert "missing this_state." in warnings


def test_validate_brain_state_this_state_is_not_dictionary():
    brain = _valid_brain_state()
    brain.this_state = [1, 2, 3]

    warnings = validate_brain_state(brain)
    assert "this_state is not a dictionary." in warnings


def test_validate_brain_state_non_finite_value_inside_this_state():
    brain = _valid_brain_state()
    brain.this_state["A"] = float("nan")

    warnings = validate_brain_state(brain)
    assert any("non-finite group value in this_state: A=" in warning for warning in warnings)


def test_validate_brain_state_missing_last_fired():
    brain = _valid_brain_state()
    delattr(brain, "last_fired")

    warnings = validate_brain_state(brain)
    assert "missing last_fired." in warnings


def test_validate_brain_state_non_string_value_inside_last_fired():
    brain = _valid_brain_state()
    brain.last_fired = {1, "A"}

    warnings = validate_brain_state(brain)
    assert any("last_fired contains a non-string entry" in warning for warning in warnings)


def test_validate_brain_state_groups_is_not_a_list():
    brain = _valid_brain_state()
    brain.groups = {"A", "B"}

    warnings = validate_brain_state(brain)
    assert "groups is missing or not a list." in warnings


@pytest.mark.parametrize(
    "bad_value, label",
    [
        (float("nan"), "NaN"),
        (float("inf"), "infinite"),
    ],
)
def test_validate_brain_state_nan_and_infinite_values_for_any_drive(bad_value, label):
    brain = _valid_brain_state()
    brain.drives["fear"] = bad_value
    warnings = validate_brain_state(brain)
    assert any(f"drive value is not finite: fear={bad_value!r}." in warning for warning in warnings)
