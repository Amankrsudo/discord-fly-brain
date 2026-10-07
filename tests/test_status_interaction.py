import asyncio

import pytest

import fly_bot


def _status_callback():
    return getattr(fly_bot.cmd_status, "callback", fly_bot.cmd_status)


def test_status_defers_before_dashboard_then_sends_one_followup(monkeypatch):
    events = []
    snapshot = {
        "behavior": "rest",
        "drives": {
            "hunger": 0.5,
            "fear": 0.25,
            "fatigue": 0.1,
            "curiosity": 0.3,
        },
    }
    attached_file = type("FakeFile", (), {"filename": "brain.png"})()

    class FakeBrain:
        def habituation_report(self):
            return {}

    class FakeFly:
        lock = asyncio.Lock()
        brain = FakeBrain()

        def _snapshot(self):
            return snapshot

    class FakeResponse:
        async def defer(self, **kwargs):
            events.append(("defer", kwargs))

        async def send_message(self, **kwargs):
            raise AssertionError("/status must not send a second initial response")

    class FakeFollowup:
        async def send(self, **kwargs):
            events.append(("followup", kwargs))

    class FakeInteraction:
        response = FakeResponse()
        followup = FakeFollowup()

    def fake_dashboard_file(**kwargs):
        events.append(("render", kwargs))
        return attached_file

    monkeypatch.setattr(fly_bot, "fly", FakeFly())
    monkeypatch.setattr(fly_bot, "dashboard_file", fake_dashboard_file)

    asyncio.run(_status_callback()(FakeInteraction()))

    assert [event[0] for event in events] == ["defer", "render", "followup"]
    assert events[0] == ("defer", {"thinking": True})
    assert events[1][1]["brain_snapshot"] is snapshot
    assert events[2][1]["content"] == (
        "behavior: rest  |  hunger=0.50 fear=0.25 fatigue=0.10 curiosity=0.30"
    )
    assert events[2][1]["files"] == [attached_file]
    assert events[2][1]["files"][0].filename == "brain.png"


def test_status_render_error_completes_deferred_interaction(monkeypatch):
    events = []

    class FakeBrain:
        def habituation_report(self):
            return {}

    class FakeFly:
        lock = asyncio.Lock()
        brain = FakeBrain()

        def _snapshot(self):
            return {
                "behavior": "idle",
                "drives": {
                    "hunger": 0.0,
                    "fear": 0.0,
                    "fatigue": 0.0,
                    "curiosity": 0.0,
                },
            }

    class FakeResponse:
        async def defer(self, **kwargs):
            events.append("defer")

        async def send_message(self, **kwargs):
            raise AssertionError("/status must not send a second initial response")

    class FakeFollowup:
        async def send(self, **kwargs):
            events.append(("followup", kwargs))

    class FakeInteraction:
        response = FakeResponse()
        followup = FakeFollowup()

    def failed_dashboard_file(**kwargs):
        events.append("render")
        raise RuntimeError("render failed")

    monkeypatch.setattr(fly_bot, "fly", FakeFly())
    monkeypatch.setattr(fly_bot, "dashboard_file", failed_dashboard_file)

    with pytest.raises(RuntimeError, match="render failed"):
        asyncio.run(_status_callback()(FakeInteraction()))

    assert events[0:2] == ["defer", "render"]
    assert events[2][0] == "followup"
    assert events[2][1]["ephemeral"] is True
    assert "Unable to render the dashboard" in events[2][1]["content"]
