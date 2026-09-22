import asyncio
import json

import pytest

from experiment_runner import DEFAULT_MAX_STEPS, DEFAULT_MAX_TRIALS, ExperimentRunner
from fly_controller import FlyController
from social_simulation import MultiFlySimulation


WEIGHTS_PATH = "group_weights.json"


def _runner():
    return ExperimentRunner(WEIGHTS_PATH)


def _behavior_observations(sequence):
    return [{"step": index, "agents": [{
        "id": "fly_01", "behavior": behavior,
        "drives": {}, "decision": {"decision_margin": 0.0},
        "social": {"nearby_count": 0, "contact": False},
        "light": {"phototaxis_bias": 0.0},
        "memory": {"habituation": {}, "sensitization": {}},
    }]} for index, behavior in enumerate(sequence)]


def test_experiment_runs_are_deterministic_and_json_serializable():
    runner = _runner()
    first = runner.run_named("phototaxis", steps=8, trials=2, seed=17)
    second = runner.run_named("phototaxis", steps=8, trials=2, seed=17)

    assert first == second
    encoded = runner.to_json(first)
    assert json.loads(encoded) == first
    assert first["version"] == 1
    assert first["trials"][0]["fly_ids"] == ["fly_01"]


def test_habituation_experiment_records_actual_habituation():
    result = _runner().run_named("habituation", steps=8, seed=1)
    memory = result["trials"][0]["summary"]["memory_changes"]

    assert result["summary"]["total_steps"] == 8
    assert memory["habituation"].get("touch", 0.0) > 0.0
    assert result["trials"][0]["observations"][-1]["agents"][0]["memory"]["events"] >= 8


def test_sensitization_experiment_records_actual_sensitization():
    result = _runner().run_named("sensitization", steps=6, seed=2)
    sensitization = result["trials"][0]["summary"]["memory_changes"]["sensitization"]

    assert sensitization.get("threat", 0.0) > 0.0
    assert result["summary"]["behavior_counts"]


def test_phototaxis_experiment_reports_real_light_response():
    result = _runner().run_named("phototaxis", steps=6, seed=3)
    phototaxis = result["summary"]["phototaxis"]
    observations = result["trials"][0]["observations"]

    assert phototaxis["min_bias"] <= phototaxis["max_bias"]
    assert any(agent["light"]["intensity"] == 0.2
               for agent in observations[0]["agents"])
    assert any(agent["light"]["intensity"] == 0.9
               for observation in observations
               for agent in observation["agents"])


def test_competing_drives_experiment_collects_decision_and_drive_metrics():
    result = _runner().run_named("competing_drives", steps=10, seed=4)
    summary = result["summary"]

    assert summary["drive_statistics"]["hunger"]["mean"] >= 0.0
    assert summary["mean_decision_margin"] >= 0.0
    assert "behavior_counts" in summary
    assert "transition_count" in summary


def test_social_experiment_collects_social_metrics_for_multiple_flies():
    result = _runner().run_named("social", steps=6, seed=5)
    summary = result["summary"]

    assert result["trials"][0]["fly_ids"] == ["fly_01", "fly_02"]
    assert summary["social_interactions"]["nearby_steps"] > 0
    assert "contact_steps" in summary["social_interactions"]
    assert result["trials"][0]["observations"][0]["agents"][0]["social"]["nearby_count"] == 1


def test_behavior_transitions_and_response_latency_are_actual_observations():
    runner = _runner()
    result = runner.run(
        "latency",
        {"steps": 5, "stimuli": [{"dangerOdor": True}] * 5},
        trials=1,
        seed=6,
    )
    trial = result["trials"][0]

    assert isinstance(trial["transitions"], list)
    assert set(trial["first_response_steps"]).issubset({"fly_01"})
    assert result["summary"]["mean_response_latency"] is None or \
        result["summary"]["mean_response_latency"] >= 0


def test_limits_are_bounded_and_named_experiments_are_explicit():
    runner = _runner()
    result = runner.run_named("social", steps=999, trials=999, seed=7)

    assert result["configuration"]["steps"] == DEFAULT_MAX_STEPS
    assert len(result["trials"]) == DEFAULT_MAX_TRIALS
    with pytest.raises(ValueError):
        runner.run_named("not-a-real-experiment")


def test_controller_runs_experiment_without_changing_normal_state(tmp_path):
    controller = FlyController(WEIGHTS_PATH, str(tmp_path / "fly.json"))
    before = controller.brain.tick_count

    async def exercise():
        result = await controller.run_experiment("habituation", steps=4, trials=1, seed=8)
        assert result["summary"]["total_steps"] == 4
        assert controller.brain.tick_count == before

    asyncio.run(exercise())


def test_per_fly_momentary_reset_preserves_non_target_stimulus():
    runner = _runner()
    simulation = MultiFlySimulation(WEIGHTS_PATH)
    first = simulation.add_fly(position=(0, 0))
    second = simulation.add_fly(position=(2, 0))
    brains = simulation.flies
    brains[second].stimulate["touch"] = True
    stimulus = {"flies": {first: {"foodNearby": True}}}

    runner._apply_stimulus(brains, stimulus)
    simulation.step()
    runner._reset_momentary(brains, stimulus)

    assert brains[first].stimulate["foodNearby"] is False
    assert brains[second].stimulate["touch"] is True


def test_behavior_durations_capture_consecutive_runs_and_flush_final_run():
    runner = _runner()
    sequence = ["idle", "idle", "feed", "feed", "feed", "idle", "idle"]
    observations = _behavior_observations(sequence)

    durations = runner._behavior_durations(observations)
    summary = runner._summarize_trial(
        observations,
        [{"step": 2, "fly_id": "fly_01", "from": "idle", "to": "feed"},
         {"step": 5, "fly_id": "fly_01", "from": "feed", "to": "idle"}],
        {},
    )

    assert durations == {"fly_01": {"feed": [3], "idle": [2, 2]}}
    assert summary["behavior_counts"] == {"feed": 3, "idle": 4}
    assert summary["behavior_durations"] != summary["behavior_counts"]
    assert summary["transition_count"] == 2


def test_behavior_duration_aggregation_keeps_runs_separate_across_trials():
    runner = _runner()
    first = {"fly_01": {"idle": [2], "feed": [3]}}
    second = {"fly_01": {"idle": [1], "feed": [2]}}

    merged = runner._merge_behavior_durations([first, second])

    assert merged == {"fly_01": {"feed": [3, 2], "idle": [2, 1]}}
    assert merged["fly_01"]["idle"] != [3]


def _multi_fly_observations(sequence_by_fly):
    observations = []
    for step, behaviors in enumerate(sequence_by_fly):
        agents = []
        for fly_id, behavior in behaviors:
            agents.append({
                "id": fly_id, "behavior": behavior,
                "drives": {}, "decision": {"decision_margin": 0.0},
                "social": {"nearby_count": 0, "contact": False},
                "light": {"phototaxis_bias": 0.0},
                "memory": {"habituation": {}, "sensitization": {}},
            })
        observations.append({"step": step, "agents": agents})
    return observations


def test_behavior_durations_are_independent_across_multiple_flies():
    runner = _runner()
    # fly_01: idle, idle, feed, feed, walk  (final run flushed at end)
    # fly_02: walk, walk, walk, idle         (final run flushed at end)
    sequence = [
        [("fly_01", "idle"),  ("fly_02", "walk")],
        [("fly_01", "idle"),  ("fly_02", "walk")],
        [("fly_01", "feed"), ("fly_02", "walk")],
        [("fly_01", "feed"), ("fly_02", "idle")],
        [("fly_01", "walk"), ("fly_02", "idle")],
    ]
    observations = _multi_fly_observations(sequence)

    durations = runner._behavior_durations(observations)

    assert durations == {
        "fly_01": {"feed": [2], "idle": [2], "walk": [1]},
        "fly_02": {"walk": [3], "idle": [2]},
    }
    # Durations are run lengths, not per-step counts (which would be 5 each).
    assert durations["fly_01"]["walk"] == [1]
    assert durations["fly_02"]["walk"] == [3]


def test_behavior_durations_never_equal_behavior_counts_for_runs():
    runner = _runner()
    sequence = ["feed", "feed", "feed", "feed", "idle"]
    observations = _behavior_observations(sequence)

    durations = runner._behavior_durations(observations)

    assert durations == {"fly_01": {"feed": [4], "idle": [1]}}
    # Counts would be {"feed": 4, "idle": 1}; durations are run-length lists.
    assert durations["fly_01"]["feed"] == [4]
    assert durations["fly_01"]["feed"] != [1, 1, 1, 1]
