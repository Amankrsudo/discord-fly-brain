import json

import pytest

from group_brain import GroupBrain
from memory import MemorySystem
from social_simulation import MultiFlySimulation

WEIGHTS_PATH = "group_weights.json"


def test_corrupt_json_raises_with_path_named(tmp_path):
    checkpoint = tmp_path / "corrupt.json"
    checkpoint.write_text('{"drives": {"hunger": 0.5}, "this_state": {')

    with pytest.raises(ValueError) as exc_info:
        GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert checkpoint.name in str(exc_info.value)
    assert str(checkpoint) in str(exc_info.value)


def test_top_level_non_dict_returns_fresh_brain(tmp_path):
    checkpoint = tmp_path / "list.json"
    checkpoint.write_text(json.dumps([{"drives": {"hunger": 0.5}}]))

    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.drives["hunger"] == 0.3
    assert restored.current_behavior == "idle"
    assert restored.memory.events == []


def test_memory_not_dict_returns_fresh_memory_but_preserves_brain_state(tmp_path):
    checkpoint = tmp_path / "bad_memory.json"
    checkpoint.write_text(json.dumps({
        "drives": {"hunger": 0.7, "fear": 0.2},
        "memory": ["not", "a", "dict"],
    }))

    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.drives["hunger"] == 0.7
    assert restored.drives["fear"] == 0.2
    assert restored.memory.events == []


def test_memory_system_from_dict_rejects_non_dict():
    assert MemorySystem.from_dict(None).events == []
    assert MemorySystem.from_dict([]).events == []
    assert MemorySystem.from_dict("string").events == []
    assert MemorySystem.from_dict(42).events == []


def test_multifly_top_level_non_dict_returns_empty_simulation(tmp_path):
    checkpoint = tmp_path / "list.json"
    checkpoint.write_text(json.dumps([{"id": "fly_01"}]))

    restored = MultiFlySimulation.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.agent_count == 0


def test_multifly_agents_not_list_treated_as_empty(tmp_path):
    checkpoint = tmp_path / "agents_dict.json"
    checkpoint.write_text(json.dumps({
        "version": 1,
        "next_id": 2,
        "agents": {"fly_01": {"id": "fly_01"}},
    }))

    restored = MultiFlySimulation.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.agent_count == 0


def test_multifly_corrupt_json_raises_with_path_named(tmp_path):
    checkpoint = tmp_path / "corrupt.json"
    checkpoint.write_text('{"version": 1, "agents": [')

    with pytest.raises(ValueError) as exc_info:
        MultiFlySimulation.load(WEIGHTS_PATH, str(checkpoint))

    assert checkpoint.name in str(exc_info.value)
    assert str(checkpoint) in str(exc_info.value)