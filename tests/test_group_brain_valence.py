import json

import pytest

from group_brain import FIRE_THRESHOLD, GroupBrain


WEIGHTS_PATH = "group_weights.json"


def _brain():
    return GroupBrain(WEIGHTS_PATH)


def test_threat_and_pain_groups_feed_fear_and_aversive_pathways():
    with open(WEIGHTS_PATH) as weights_file:
        weights = json.load(weights_file)

    for source in ("VIS_LC", "NOCI", "THERMO_WARM", "OLF_ORN_DANGER"):
        assert weights[source]["DRIVE_FEAR"] > 0
        assert weights[source]["MB_DAN_PUN"] > 0


def test_drive_fear_firing_increases_fear_once_and_then_fear_decays():
    brain = _brain()
    brain.this_state["DRIVE_FEAR"] = FIRE_THRESHOLD + 1
    brain.threat_signal = 1.0

    brain._run_connectome()
    fear_after_event = brain.drives["fear"]
    assert fear_after_event == pytest.approx(0.18 * (23 / FIRE_THRESHOLD))

    for _ in range(10):
        brain.tick()

    assert brain.drives["fear"] < fear_after_event


def test_single_shock_does_not_create_runaway_fear():
    brain = _brain()
    fear_values = []

    for _ in range(4):
        brain.external_stimulate("NOCI")
        brain.tick()
        fear_values.append(brain.drives["fear"])
    for _ in range(20):
        brain.tick()
        fear_values.append(brain.drives["fear"])

    assert max(fear_values) <= 1.0
    assert fear_values[-1] < max(fear_values)


def _run_scare(brain, count=1):
    for _ in range(count):
        for _ in range(3):
            brain.external_stimulate("VIS_LC")
            brain.tick()
        for _ in range(3):
            brain.tick()
    return brain


def test_one_scare_produces_noticeable_fear():
    brain = _run_scare(_brain())
    assert brain.drives["fear"] > 0.1


def test_three_rapid_scares_exceed_one_scare():
    one = _run_scare(_brain()).drives["fear"]
    three = _run_scare(_brain(), count=3).drives["fear"]
    assert three > one


def test_fear_recovers_gradually_after_stimulation_stops():
    brain = _run_scare(_brain(), count=3)
    fear_before = brain.drives["fear"]
    for _ in range(10):
        brain.tick()
    assert 0.0 < brain.drives["fear"] < fear_before


def _run_flag_stimulus(group, scale, ticks=6):
    brain = _brain()
    for _ in range(ticks):
        brain.external_stimulate(group, scale)
        brain.tick()
    return brain


def test_extreme_stimuli_are_stronger_than_scare():
    scare = _run_scare(_brain()).drives["fear"]
    shock = _run_flag_stimulus("NOCI", 1.0, 4).drives["fear"]
    burn = _run_flag_stimulus("THERMO_WARM", 0.8).drives["fear"]
    freeze = _run_flag_stimulus("THERMO_COOL", 0.8).drives["fear"]
    assert shock > scare
    assert burn > scare
    assert freeze > scare


def test_shock_updates_both_valences_and_biases_flight():
    brain = _run_flag_stimulus("NOCI", 1.0, 4)
    assert brain.drives["fear"] > 0.0
    assert brain.drives["aversive_valence"] > 0.0
    assert brain.drives["positive_valence"] == 0.0
    brain.last_accum["flight"] = 9
    assert brain._select_behavior() == "fly"


def test_reward_persists_and_decays_after_feeding():
    brain = _brain()
    brain.stimulate["foodContact"] = True
    for _ in range(6):
        brain.tick()
    reward_after_feed = brain.drives["positive_valence"]
    assert reward_after_feed > 0.0
    brain.stimulate["foodContact"] = False
    brain.tick()
    assert 0.0 < brain.drives["positive_valence"] < reward_after_feed


def test_repeated_extreme_stimuli_remain_bounded():
    brain = _brain()
    for _ in range(20):
        for _ in range(4):
            brain.external_stimulate("NOCI")
            brain.tick()
        for _ in range(2):
            brain.tick()
    assert all(0.0 <= brain.drives[name] <= 1.0
               for name in ("fear", "positive_valence", "aversive_valence"))


def test_reward_and_punishment_update_bounded_decaying_valence():
    brain = _brain()
    brain.this_state["MB_DAN_REW"] = FIRE_THRESHOLD + 1
    brain._run_connectome()
    assert brain.drives["positive_valence"] == pytest.approx(0.12 * (23 / FIRE_THRESHOLD))

    brain.this_state["MB_DAN_PUN"] = FIRE_THRESHOLD + 1
    brain._run_connectome()
    assert brain.drives["aversive_valence"] == pytest.approx(0.16 * (23 / FIRE_THRESHOLD))
    assert brain.drives["positive_valence"] < 0.12

    for _ in range(20):
        brain.tick()

    assert 0.0 <= brain.drives["positive_valence"] < 0.12
    assert 0.0 <= brain.drives["aversive_valence"] < 0.12


def test_food_contact_reduces_hunger_and_reaches_reward_pathway():
    brain = _brain()
    brain.drives["hunger"] = 0.5
    brain.stimulate["foodContact"] = True

    hunger_before = brain.drives["hunger"]
    for _ in range(10):
        brain.tick()

    assert brain.drives["hunger"] < hunger_before
    assert brain.drives["positive_valence"] > 0.0


def test_high_fear_suppresses_approach_behaviors_and_biases_flight():
    brain = _brain()
    brain.drives["fear"] = 0.8
    brain.last_accum = {"feed": 20, "groom": 20, "walkLeft": 20, "walkRight": 0, "flight": 0}
    assert brain._select_behavior(has_nearby_food=True) == "idle"

    brain.last_accum["flight"] = 9
    assert brain._select_behavior() == "fly"


def test_hunger_and_nearby_food_can_select_feed_without_feed_motor_output():
    brain = _brain()
    brain.drives["hunger"] = 0.8
    brain.stimulate["foodNearby"] = True

    assert brain._select_behavior(has_nearby_food=True) == "feed"


def test_valence_state_round_trips_through_checkpoint(tmp_path):
    brain = _brain()
    brain.drives["positive_valence"] = 0.4
    brain.drives["aversive_valence"] = 0.3
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.drives["positive_valence"] == 0.4
    assert restored.drives["aversive_valence"] == 0.3


def test_old_checkpoint_without_valence_keys_remains_loadable(tmp_path):
    checkpoint = tmp_path / "old-state.json"
    checkpoint.write_text(json.dumps({"drives": {"hunger": 0.7, "fear": 0.2}}))

    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.drives["hunger"] == 0.7
    assert restored.drives["positive_valence"] == 0.0
    assert restored.drives["aversive_valence"] == 0.0


def test_checkpoint_preserves_ambient_stimulus_state(tmp_path):
    brain = _brain()
    brain.stimulate["lightLevel"] = 0.0
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.stimulate["lightLevel"] == 0.0


def test_checkpoint_preserves_tick_count(tmp_path):
    brain = _brain()
    brain.tick_count = 42
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.tick_count == 42


def test_checkpoint_preserves_this_state_and_next_state_values(tmp_path):
    brain = _brain()
    group = next(iter(brain.this_state))
    brain.this_state[group] = 5.0
    brain.next_state[group] = 7.0
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.this_state[group] == 5.0
    assert restored.next_state[group] == 7.0


def test_checkpoint_preserves_cooldown_until(tmp_path):
    brain = _brain()
    brain.cooldown_until["feed"] = 1e9
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.cooldown_until.get("feed") == 1e9


def test_checkpoint_preserves_habituation(tmp_path):
    brain = _brain()
    brain.habituation["light"] = 0.5
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.habituation.get("light") == 0.5


def test_checkpoint_preserves_history(tmp_path):
    brain = _brain()
    brain.history = [{"tick": 1, "event": "stim"}]
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.history == [{"tick": 1, "event": "stim"}]


def test_checkpoint_preserves_first_seen(tmp_path):
    brain = _brain()
    brain.first_seen = {"A", "B"}
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.first_seen == {"A", "B"}


def test_checkpoint_preserves_idle_since(tmp_path):
    brain = _brain()
    brain.idle_since = 1000.0
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.idle_since == 1000.0


def test_checkpoint_preserves_longest_idle_seconds(tmp_path):
    brain = _brain()
    brain.longest_idle_seconds = 9.5
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.longest_idle_seconds == 9.5


def test_checkpoint_preserves_fear_event_cooldown(tmp_path):
    brain = _brain()
    brain.fear_event_cooldown = 7
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.fear_event_cooldown == 7


def test_checkpoint_preserves_multiple_stimulate_fields(tmp_path):
    brain = _brain()
    brain.stimulate["foodNearby"] = True
    brain.stimulate["windStrength"] = 0.7
    brain.stimulate["temperature"] = 0.3
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.stimulate["foodNearby"] is True
    assert restored.stimulate["windStrength"] == 0.7
    assert restored.stimulate["temperature"] == 0.3


def test_checkpoint_preserves_groupbrain_social_state(tmp_path):
    brain = _brain()
    brain.social_state["nearby_count"] = 3
    brain.social_state["contact"] = True
    checkpoint = tmp_path / "state.json"

    brain.save(str(checkpoint))
    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.social_state["nearby_count"] == 3
    assert restored.social_state["contact"] is True