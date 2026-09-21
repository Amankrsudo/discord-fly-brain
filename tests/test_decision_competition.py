import json

import pytest

from group_brain import DECISION_BEHAVIORS, GroupBrain


WEIGHTS_PATH = "group_weights.json"


def _brain():
    return GroupBrain(WEIGHTS_PATH)


def test_competing_scores_are_bounded_and_exposed():
    brain = _brain()
    brain.drives.update({
        "hunger": 1.0,
        "fear": 1.0,
        "fatigue": 1.0,
        "curiosity": 1.0,
        "groom": 1.0,
        "mating": 1.0,
        "positive_valence": 1.0,
        "aversive_valence": 1.0,
    })
    brain.light_state["phototaxis_bias"] = -1.0
    brain.last_accum = {
        "startle": 1000,
        "flight": 1000,
        "feed": 1000,
        "groom": 1000,
        "walkLeft": 1000,
        "walkRight": 1000,
    }

    scores, _ = brain._decision_scores(has_nearby_food=True)
    assert set(scores) == set(DECISION_BEHAVIORS)
    assert all(0.0 <= score <= 1.0 for score in scores.values())

    brain._select_behavior(has_nearby_food=True)
    decision = brain.decision_summary()
    assert set(decision["competing_scores"]) == set(DECISION_BEHAVIORS)
    assert 0.0 <= decision["winning_score"] <= 1.0
    assert 0.0 <= decision["runner_up_score"] <= 1.0
    assert decision["decision_margin"] >= 0.0


def test_strong_hunger_can_beat_mild_fear_when_food_is_nearby():
    brain = _brain()
    brain.drives.update({"hunger": 0.95, "fear": 0.25, "curiosity": 0.1})
    brain.stimulate["foodNearby"] = True

    assert brain._select_behavior(has_nearby_food=True) == "feed"


def test_strong_fear_and_flight_signal_override_food_seeking():
    brain = _brain()
    brain.drives.update({"hunger": 1.0, "fear": 0.95, "aversive_valence": 0.8})
    brain.stimulate["foodNearby"] = True
    brain.last_accum = {"feed": 20, "flight": 15}

    assert brain._select_behavior(has_nearby_food=True) == "fly"
    assert brain.decision_summary()["competing_scores"]["fly"] > \
        brain.decision_summary()["competing_scores"]["feed"]


def test_fatigue_competes_with_exploration_and_prioritizes_rest():
    brain = _brain()
    brain.drives.update({"fatigue": 0.95, "curiosity": 0.9})
    brain.last_accum = {"walkLeft": 5, "walkRight": 5}

    assert brain._select_behavior() == "rest"


def test_food_memory_increases_feed_competition_score():
    without_memory = _brain()
    without_memory.drives["hunger"] = 0.6
    without_memory.stimulate["foodNearby"] = True
    baseline = without_memory._decision_scores(has_nearby_food=True)[0]["feed"]

    with_memory = _brain()
    with_memory.drives["hunger"] = 0.6
    with_memory.stimulate["foodNearby"] = True
    with_memory.memory.record_event("food", valence=1.0, intensity=1.0)
    remembered = with_memory._decision_scores(has_nearby_food=True)[0]["feed"]

    assert remembered > baseline


def test_phototaxis_and_light_memory_participate_in_competition():
    brain = _brain()
    brain.drives["curiosity"] = 0.7
    brain.light_state["phototaxis_bias"] = 0.8
    before = brain._decision_scores()[0]["phototaxis"]
    brain.memory.record_event("light", valence=1.0, intensity=1.0)
    after = brain._decision_scores()[0]["phototaxis"]

    assert after > before
    assert brain._decision_scores()[0]["phototaxis"] > \
        brain._decision_scores()[0]["idle"]


def test_positive_valence_strengthens_reward_seeking():
    brain = _brain()
    brain.drives["hunger"] = 0.6
    baseline = brain._decision_scores(has_nearby_food=True)[0]["feed"]
    brain.drives["positive_valence"] = 0.9

    assert brain._decision_scores(has_nearby_food=True)[0]["feed"] > baseline


def test_aversive_valence_strengthens_avoidance():
    brain = _brain()
    baseline = brain._decision_scores()[0]["fly"]
    brain.drives["aversive_valence"] = 0.9

    assert brain._decision_scores()[0]["fly"] > baseline


def test_decision_margin_matches_top_competitors():
    brain = _brain()
    brain.last_accum = {"startle": 30}
    brain._select_behavior()
    decision = brain.decision_summary()
    scores = decision["competing_scores"]
    ranked = sorted(scores.values(), reverse=True)

    assert decision["winning_score"] == pytest.approx(ranked[0])
    assert decision["runner_up_score"] == pytest.approx(ranked[1])
    assert decision["decision_margin"] == pytest.approx(ranked[0] - ranked[1])


def test_hysteresis_retains_close_current_behavior():
    brain = _brain()
    brain.current_behavior = "idle"
    brain.last_accum = {"walkLeft": 0.4}

    selected = brain._select_behavior()

    assert brain.decision_summary()["winning_behavior"] == "walk"
    assert selected == "idle"


def test_substantially_stronger_competitor_switches_behavior():
    brain = _brain()
    brain.current_behavior = "feed"
    brain.drives.update({"fear": 0.9, "aversive_valence": 0.8})
    brain.last_accum = {"flight": 15}

    assert brain._select_behavior() == "fly"


def test_mating_memory_contributes_to_approach_scores():
    brain = _brain()
    brain.memory.record_event("mate", valence=1.0, intensity=1.0)
    biases = brain.memory.drive_biases()
    brain.drives["mating"] = biases["mating"]

    contributions = brain._decision_scores()[1]
    assert biases["mating"] > 0.0
    assert contributions["explore"]["mating"] > 0.0


def test_decision_and_new_drive_state_round_trip(tmp_path):
    brain = _brain()
    brain.current_behavior = "feed"
    brain.drives["mating"] = 0.4
    checkpoint = tmp_path / "decision-state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.current_behavior == "feed"
    assert restored.drives["mating"] == pytest.approx(0.4)
    assert restored.decision_summary()["current_behavior"] == "idle"


def test_old_checkpoint_without_mating_or_decision_state_loads(tmp_path):
    checkpoint = tmp_path / "old-state.json"
    checkpoint.write_text(json.dumps({
        "drives": {"hunger": 0.7, "fear": 0.2},
        "current_behavior": "idle",
    }))

    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.drives["hunger"] == 0.7
    assert restored.drives["mating"] == 0.0
    assert restored.decision_summary()["current_behavior"] == "idle"
