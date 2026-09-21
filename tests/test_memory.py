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
