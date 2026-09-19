import asyncio
import os

from dashboard_animation import visual_state
import fly_bot
from fly_bot import VISUAL_COMMAND_OVERRIDES


EXPECTED_VISUALS = {
    "feed": "feed", "love": "happy", "burn": "burn", "freeze": "freeze",
    "shock": "shock", "scare": "scare", "hurt": "hurt", "mate": "mate",
    "takeoff": "takeoff", "land": "land", "sleep": "sleep", "wake": "idle",
    "happy": "happy", "confused": "confused",
}


def test_commands_use_their_explicit_visual_intent():
    assert VISUAL_COMMAND_OVERRIDES == EXPECTED_VISUALS
    for command, expected in EXPECTED_VISUALS.items():
        visual = visual_state("phototaxis", {"temperature": 0.9, "nociception": True}, 0,
                              visual_override=VISUAL_COMMAND_OVERRIDES[command])
        assert visual["key"] == expected
        assert visual["frame"] and os.path.isfile(visual["frame"])


def test_command_effect_overlays_are_preserved_only_for_their_commands():
    assert os.path.basename(visual_state("idle", visual_override="burn")["effects"][0]) == "fire_overlay.png"
    assert os.path.basename(visual_state("idle", visual_override="freeze")["effects"][0]) == "ice_overlay.png"
    assert os.path.basename(visual_state("idle", visual_override="shock")["effects"][0]) == "shock_overlay.png"
    assert visual_state("shock", {"nociception": True}, visual_override="hurt")["effects"] == []


def test_reply_preserves_brain_snapshot_and_passes_visual_intent():
    class FakeBrain:
        def note_first(self, key, description):
            pass

        def log_event(self, description):
            pass

    class FakeFly:
        def __init__(self):
            self.lock = asyncio.Lock()
            self.brain = FakeBrain()

    class FakeFollowup:
        async def send(self, **kwargs):
            self.kwargs = kwargs

    class FakeInteraction:
        def __init__(self):
            self.followup = FakeFollowup()

    captured = []

    def fake_dashboard_file(**kwargs):
        captured.append(kwargs)
        return object()

    original_fly, original_dashboard_file = fly_bot.fly, fly_bot.dashboard_file
    fly_bot.fly, fly_bot.dashboard_file = FakeFly(), fake_dashboard_file
    try:
        async def verify(command, arc, expected_behavior, expected_intent):
            snapshot = {
                "behavior": arc[-1], "behavior_arc": arc, "fired": ["NOCI"],
                "stimuli": {"nociception": True, "temperature": 0.9},
            }
            await fly_bot._reply(FakeInteraction(), command, snapshot)
            assert captured[-1]["behavior"] == expected_behavior
            assert captured[-1]["visual_override"] == expected_intent
            assert captured[-1]["stimuli"] == snapshot["stimuli"]
            assert snapshot["behavior_arc"] == arc

        async def run():
            for command, intent in EXPECTED_VISUALS.items():
                await verify(command, ["idle", "fly", "idle"], "fly", intent)
            await verify("wind", ["idle", "fly", "idle"], "fly", None)
            await verify("wind", ["idle", "startle", "idle"], "startle", None)
            await verify("wind", ["idle", "idle"], "idle", None)

        asyncio.run(run())
    finally:
        fly_bot.fly, fly_bot.dashboard_file = original_fly, original_dashboard_file
