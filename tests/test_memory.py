import json

import pytest

from group_brain import GroupBrain
from memory import MemorySystem

WEIGHTS_PATH = "group_weights.json"


def test_memory_creation_and_decay():
    memory = MemorySystem()
    memory.record_event("food", valence=1.0, intensity=0.8, context={"source": "feed"})

    assert len(memory.events) == 1
    assert memory.events[0]["strength"] > 0.0

    memory.decay(dt=0.5)
    assert memory.events[0]["strength"] < 1.0


def test_recent_memories_are_stronger_than_old_memories():
    memory = MemorySystem()
    now = 1000.0
    memory.record_event("food", valence=1.0, intensity=1.0, context={"source": "feed"}, timestamp=now - 60)
    memory.record_event("threat", valence=-1.0, intensity=1.0, context={"source": "scare"}, timestamp=now)

    recent = memory.recent_strength("threat", now=now)
    old = memory.recent_strength("food", now=now)
    assert recent > old


def test_habituation_from_repeated_harmless_stimuli():
    memory = MemorySystem()
    for _ in range(6):
        memory.record_event("light", valence=0.0, intensity=0.5, context={"source": "ambient"})

    assert memory.habituation_factor("light") > 0.0


def test_sensitization_from_repeated_threats():
    memory = MemorySystem()
    for _ in range(6):
        memory.record_event("threat", valence=-1.0, intensity=0.8, context={"source": "scare"})

    assert memory.sensitization_factor("threat") > 0.0


def test_associative_learning_strengthens_reward_and_threat_links():
    memory = MemorySystem()
    now = 1000.0
    for _ in range(5):
        memory.record_event("food", valence=1.0, intensity=1.0, context={"source": "feed"}, timestamp=now)
        memory.record_event("scare", valence=-1.0, intensity=1.0, context={"source": "scare"}, timestamp=now)

    assert memory.association_strength("food", "reward", now=now) > 0.0
    assert memory.association_strength("scare", "threat", now=now) > 0.0


def test_positive_valence_creates_only_positive_association():
    memory = MemorySystem()
    memory.record_event("food", valence=1.0, intensity=1.0)

    assert memory.associations["food"]["reward"] > 0.0
    assert "threat" not in memory.associations["food"]


def test_negative_valence_creates_only_negative_association():
    memory = MemorySystem()
    memory.record_event("scare", valence=-1.0, intensity=1.0)

    assert memory.associations["scare"]["threat"] > 0.0
    assert "reward" not in memory.associations["scare"]


def test_zero_valence_creates_no_association():
    memory = MemorySystem()
    memory.record_event("ambient", valence=0.0, intensity=1.0)

    assert "ambient" not in memory.associations
    assert "reward" not in memory.associations
    assert "threat" not in memory.associations


def test_neutral_event_does_not_change_either_association_direction():
    memory = MemorySystem()
    memory.record_event("food", valence=1.0, intensity=1.0)
    memory.record_event("scare", valence=-1.0, intensity=1.0)
    before_reward = memory.associations["food"]["reward"]
    before_threat = memory.associations["scare"]["threat"]

    memory.record_event("ambient", valence=0.0, intensity=1.0)

    assert memory.associations["food"]["reward"] == before_reward
    assert memory.associations["scare"]["threat"] == before_threat
    assert "ambient" not in memory.associations


def test_reward_memories_influence_feeding_related_drive():
    brain = GroupBrain(WEIGHTS_PATH)
    brain.memory.record_event("food", valence=1.0, intensity=1.0, context={"source": "feed"})
    brain.memory.record_event("food", valence=1.0, intensity=1.0, context={"source": "feed"})

    biases = brain.memory.drive_biases()
    assert biases["hunger"] > 0.0


def test_threat_memories_influence_fear_related_drive():
    brain = GroupBrain(WEIGHTS_PATH)
    for _ in range(4):
        brain.memory.record_event("threat", valence=-1.0, intensity=1.0, context={"source": "shock"})

    biases = brain.memory.drive_biases()
    assert biases["fear"] > 0.0


def test_old_checkpoint_without_memory_data_still_loads():
    brain = GroupBrain(WEIGHTS_PATH)
    checkpoint = "tests/_tmp_old_state.json"
    with open(checkpoint, "w") as handle:
        json.dump({"drives": {"hunger": 0.7, "fear": 0.2}}, handle)
    try:
        restored = GroupBrain.load(WEIGHTS_PATH, checkpoint)
        assert restored.drives["hunger"] == 0.7
        assert restored.drives["fear"] == 0.2
        assert restored.memory is not None
    finally:
        import os
        if os.path.exists(checkpoint):
            os.remove(checkpoint)


def test_memory_persistence_reload_round_trip(tmp_path):
    brain = GroupBrain(WEIGHTS_PATH)
    brain.memory.record_event("food", valence=1.0, intensity=0.9, context={"source": "feed"})
    checkpoint = tmp_path / "memory_state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.memory is not None
    assert restored.memory.recent_strength("food") > 0.0


def test_light_intensity_and_preferred_light_bounds():
    brain = GroupBrain(WEIGHTS_PATH)
    brain.stimulate["lightLevel"] = 1.5
    brain._update_light_state()
    assert 0.0 <= brain.light_state["intensity"] <= 1.0
    brain.light_state["preferred"] = 2.0
    brain._update_light_state()
    assert 0.0 <= brain.light_state["preferred"] <= 1.0


def test_positive_phototaxis_when_light_is_below_preferred():
    brain = GroupBrain(WEIGHTS_PATH)
    brain.stimulate["lightLevel"] = 0.2
    brain.light_state["preferred"] = 0.6
    brain._update_light_state()
    assert brain.light_state["phototaxis_bias"] > 0.0


def test_negative_phototaxis_when_light_above_preferred():
    brain = GroupBrain(WEIGHTS_PATH)
    brain.stimulate["lightLevel"] = 0.9
    brain.light_state["preferred"] = 0.2
    brain._update_light_state()
    assert brain.light_state["phototaxis_bias"] < 0.0


def test_neutral_response_near_preferred_light():
    brain = GroupBrain(WEIGHTS_PATH)
    brain.stimulate["lightLevel"] = 0.6
    brain.light_state["preferred"] = 0.6
    brain._update_light_state()
    assert abs(brain.light_state["phototaxis_bias"]) < 0.2


def test_light_reward_association_increases_positive_phototaxis():
    brain = GroupBrain(WEIGHTS_PATH)
    brain.memory.record_event("light", valence=1.0, intensity=0.7, context={"source": "feed"})
    brain.stimulate["lightLevel"] = 0.2
    brain.light_state["preferred"] = 0.6
    brain._update_light_state()
    assert brain.light_state["phototaxis_bias"] > 0.3


def test_light_threat_association_increases_avoidance():
    brain = GroupBrain(WEIGHTS_PATH)
    brain.memory.record_event("light", valence=-1.0, intensity=0.9, context={"source": "scare"})
    brain.stimulate["lightLevel"] = 0.8
    brain.light_state["preferred"] = 0.2
    brain._update_light_state()
    assert brain.light_state["phototaxis_bias"] < -0.2


def test_habituation_reduces_repeated_harmless_light_response():
    brain = GroupBrain(WEIGHTS_PATH)
    for _ in range(8):
        brain.memory.record_event("light", valence=0.0, intensity=0.5, context={"source": "ambient"})
    bias = brain.memory.light_association_bias()
    assert bias["habituation"] > 0.0


def test_memory_decay_affects_light_response():
    brain = GroupBrain(WEIGHTS_PATH)
    brain.memory.record_event("light", valence=1.0, intensity=0.7, context={"source": "feed"}, timestamp=0)
    before = brain.memory.light_association_bias(now=0)
    brain.memory.decay(dt=50.0, now=50.0)
    after = brain.memory.light_association_bias(now=50.0)
    assert after["reward"] <= before["reward"]


def test_internal_hunger_and_fear_prime_light_bias():
    brain = GroupBrain(WEIGHTS_PATH)
    brain.drives["hunger"] = 0.9
    brain.drives["fear"] = 0.2
    brain.stimulate["lightLevel"] = 0.2
    brain.light_state["preferred"] = 0.6
    brain._update_light_state()
    assert brain.light_state["phototaxis_bias"] > 0.0

    brain.drives["fear"] = 0.9
    brain.drives["hunger"] = 0.1
    brain.memory.record_event("light", valence=-1.0, intensity=0.9, context={"source": "scare"})
    brain._update_light_state()
    assert brain.light_state["phototaxis_bias"] < 0.0


def test_light_state_persistence_round_trip(tmp_path):
    brain = GroupBrain(WEIGHTS_PATH)
    brain.light_state["preferred"] = 0.75
    brain.light_state["phototaxis_bias"] = 0.42
    checkpoint = tmp_path / "light_state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.light_state["preferred"] == pytest.approx(0.75)
    assert restored.light_state["phototaxis_bias"] == pytest.approx(0.42)


def test_old_state_without_light_state_still_loads():
    checkpoint = "tests/_tmp_old_light_state.json"
    with open(checkpoint, "w") as handle:
        json.dump({"drives": {"hunger": 0.3, "fear": 0.1}}, handle)
    try:
        restored = GroupBrain.load(WEIGHTS_PATH, checkpoint)
        assert 0.0 <= restored.light_state["preferred"] <= 1.0
        assert 0.0 <= restored.light_state["intensity"] <= 1.0
    finally:
        import os
        if os.path.exists(checkpoint):
            os.remove(checkpoint)


def test_memory_from_dict_accepts_future_version_and_loads_state():
    data = {
        "version": 99,
        "events": [{"type": "food", "valence": 1.0}],
        "associations": {"food": {"reward": 0.5}},
        "habituation": {"light": 0.1},
        "sensitization": {"scare": 0.2},
    }
    memory = MemorySystem.from_dict(data)

    assert len(memory.events) == 1
    assert memory.associations == {"food": {"reward": 0.5}}
    assert memory.habituation == {"light": 0.1}
    assert memory.sensitization == {"scare": 0.2}


def test_memory_from_dict_treats_missing_version_as_current():
    memory = MemorySystem.from_dict({"events": [{"type": "food", "valence": 1.0}]})

    assert len(memory.events) == 1
