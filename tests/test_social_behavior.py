import asyncio
import json

import pytest

from brain_dashboard import render_dashboard
from fly_controller import FlyController
from group_brain import GroupBrain
from social_simulation import MultiFlySimulation


WEIGHTS_PATH = "group_weights.json"


def test_multiple_flies_have_independent_brains_and_state():
    simulation = MultiFlySimulation(WEIGHTS_PATH)
    first = simulation.add_fly(position=(0, 0))
    second = simulation.add_fly(position=(20, 0))

    assert (first, second) == ("fly_01", "fly_02")
    assert simulation.flies[first] is not simulation.flies[second]
    simulation.flies[first].drives["hunger"] = 0.9
    assert simulation.flies[second].drives["hunger"] != 0.9


def test_social_sensing_reports_presence_proximity_activity_and_contact():
    simulation = MultiFlySimulation(WEIGHTS_PATH)
    first = simulation.add_fly(position=(0, 0))
    second = simulation.add_fly(position=(0.5, 0))
    simulation.flies[second].last_accum = {"walkLeft": 10}

    context = simulation._social_context(first)

    assert context["nearby_count"] == 1
    assert context["nearest_fly"] == second
    assert context["proximity"] > 0.9
    assert context["contact"] is True
    assert context["social_activity"] > 0.0
    assert context["approach_tendency"] > 0.0


def test_social_attraction_competes_through_existing_decision_scores():
    simulation = MultiFlySimulation(WEIGHTS_PATH)
    first = simulation.add_fly(position=(0, 0))
    simulation.add_fly(position=(1, 0))
    brain = simulation.flies[first]
    brain.drives.update({"curiosity": 0.8, "mating": 0.9, "fear": 0.0})
    brain.set_social_context(simulation._social_context(first))

    scores, contributions = brain._decision_scores()

    assert scores["approach_social"] > 0.0
    assert contributions["approach_social"]["social_attraction"] > 0.0
    assert brain._select_behavior() in {"approach_social", "follow"}


def test_strong_social_threat_can_select_avoidance_over_attraction():
    simulation = MultiFlySimulation(WEIGHTS_PATH)
    first = simulation.add_fly(position=(0, 0))
    second = simulation.add_fly(position=(1, 0))
    brain = simulation.flies[first]
    brain.drives.update({"fear": 0.9, "mating": 0.8, "curiosity": 0.8})
    simulation.flies[second].drives["fear"] = 1.0
    simulation.flies[second].drives["aversive_valence"] = 1.0
    brain.set_social_context(simulation._social_context(first))

    assert brain._select_behavior() == "avoid_social"
    decision = brain.decision_summary()
    assert decision["competing_scores"]["avoid_social"] > decision["competing_scores"]["approach_social"]


def test_overcrowding_competes_with_social_approach():
    simulation = MultiFlySimulation(WEIGHTS_PATH)
    first = simulation.add_fly(position=(0, 0))
    for index in range(3):
        simulation.add_fly(position=(0.5 + index * 0.2, 0))
    brain = simulation.flies[first]
    brain.set_social_context(simulation._social_context(first))

    assert brain.social_state["overcrowding"] > 0.0
    assert brain._decision_scores()[0]["separate"] > 0.0


def test_social_interaction_is_recorded_in_existing_memory_system():
    simulation = MultiFlySimulation(WEIGHTS_PATH)
    first = simulation.add_fly(position=(0, 0))
    simulation.add_fly(position=(0.5, 0))
    simulation.flies[first].drives.update({"curiosity": 0.9, "mating": 0.9})

    simulation.step()

    events = [event for event in simulation.flies[first].memory.events if event["type"] == "social"]
    assert events
    assert events[-1]["context"]["target"] == "fly_02"
    assert simulation.flies[first].memory.drive_biases()["social_reward"] >= 0.0


def test_social_state_persistence_round_trip(tmp_path):
    simulation = MultiFlySimulation(WEIGHTS_PATH)
    simulation.add_fly(position=(0, 0))
    simulation.add_fly(position=(2, 0))
    simulation.step()
    checkpoint = tmp_path / "social-state.json"

    simulation.save(str(checkpoint))
    restored = MultiFlySimulation.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.agent_count == 2
    assert sorted(restored.flies) == ["fly_01", "fly_02"]
    assert restored.positions["fly_02"] == pytest.approx(simulation.positions["fly_02"])
    assert restored.flies["fly_01"].memory.events


def test_legacy_single_fly_checkpoint_remains_loadable(tmp_path):
    brain = GroupBrain(WEIGHTS_PATH)
    checkpoint = tmp_path / "legacy.json"
    brain.save(str(checkpoint))

    restored = GroupBrain.load(WEIGHTS_PATH, str(checkpoint))

    assert restored.drives["hunger"] == pytest.approx(brain.drives["hunger"])
    assert restored.social_state["nearby_count"] == 0


def test_controller_keeps_single_fly_commands_and_exposes_social_snapshot(tmp_path):
    checkpoint = tmp_path / "fly.json"
    controller = FlyController(WEIGHTS_PATH, str(checkpoint))

    async def exercise():
        snapshot = await controller.step_social()
        assert snapshot["count"] == 1
        assert snapshot["current_fly"] == "fly_01"
        command_snapshot = await controller.stimulate_flag(foodNearby=True)
        assert command_snapshot["behavior"]
        assert command_snapshot["social"]["count"] == 1

    asyncio.run(exercise())


def test_dashboard_renders_social_snapshot_fields(monkeypatch):
    brain = GroupBrain(WEIGHTS_PATH)
    captured = []

    def capture_text(image, x, y, value, *args, **kwargs):
        captured.append(str(value).upper())

    social = {
        "count": 2,
        "current_fly": "fly_01",
        "current": {
            "id": "fly_01",
            "behavior": "approach_social",
            "social": {
                "nearby_count": 1,
                "proximity": 0.8,
                "social_activity": 0.4,
                "contact": True,
                "approach_tendency": 0.7,
                "avoidance_tendency": 0.1,
                "overcrowding": 0.0,
                "following_target": "fly_02",
                "nearby_flies": [{"id": "fly_02", "distance": 1.6}],
            },
            "decision": {
                "drive_contributions": {
                    "approach_social": {"social_attraction": 0.4},
                },
            },
        },
    }
    monkeypatch.setattr("brain_dashboard.DashboardImage.text", capture_text)
    render_dashboard(brain, snapshot={"social": social})

    assert any("FLIES 2" in value for value in captured)
    assert any("CURRENT FLY_01" in value for value in captured)
    assert any("NEARBY 1" in value for value in captured)
    assert any("SOCIAL CONTRIBUTION" in value for value in captured)
