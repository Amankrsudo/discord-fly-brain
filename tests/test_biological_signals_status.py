"""Focused tests for the opt-in 3.0B product integration.

Scope: configuration selection, and conditional rendering of the already-produced
``biological_signals`` on the existing ``/status`` surface. Nothing here tests
3.0D, the GFS demonstration, or any biological model behaviour.

The default product is the 2.0 ``GroupBrain`` path. These tests pin that, and
pin that the opt-in is coarse, explicit, and additive.
"""

import asyncio
import importlib
import os
import sys

import pytest

import fly_controller
from biological_brain import BiologicalMode
from biological_brain.configuration import BIOLOGICAL_CIRCUITS
from fly_controller import FlyController


@pytest.fixture
def reset_biological_circuits():
    """Restore BIOLOGICAL_CIRCUITS after any test that mutates it."""
    saved = dict(BIOLOGICAL_CIRCUITS)
    yield
    BIOLOGICAL_CIRCUITS.clear()
    BIOLOGICAL_CIRCUITS.update(saved)


def _load_fly_bot(env_value):
    """Import fly_bot with ENABLE_BIOLOGICAL_3_0 set to ``env_value``.

    Returns ``(module, circuits_seen_at_import)``. The observed circuit state
    must be captured at import time, because the loader restores
    BIOLOGICAL_CIRCUITS before the caller can assert against it.
    """
    saved = os.environ.get("ENABLE_BIOLOGICAL_3_0")
    if env_value is None:
        os.environ.pop("ENABLE_BIOLOGICAL_3_0", None)
    else:
        os.environ["ENABLE_BIOLOGICAL_3_0"] = env_value
    saved_circuits = dict(BIOLOGICAL_CIRCUITS)
    try:
        for name in list(sys.modules):
            if name == "fly_bot":
                del sys.modules[name]
        module = importlib.import_module("fly_bot")
        return module, dict(BIOLOGICAL_CIRCUITS)
    finally:
        if saved is None:
            os.environ.pop("ENABLE_BIOLOGICAL_3_0", None)
        else:
            os.environ["ENABLE_BIOLOGICAL_3_0"] = saved
        BIOLOGICAL_CIRCUITS.clear()
        BIOLOGICAL_CIRCUITS.update(saved_circuits)


# --- 1, 2. configuration selection -----------------------------------------


def test_default_configuration_preserves_legacy_2_0(reset_biological_circuits):
    """Absent opt-in means the 2.0 path, and no circuit is enabled."""
    module, circuits = _load_fly_bot(None)
    assert module.ENABLE_BIOLOGICAL_3_0 is False
    assert module.fly.biological_brain.mode is BiologicalMode.LEGACY_2_0
    # The opt-in must not leak into the shared circuit defaults.
    assert circuits == {
        "escape": False, "feeding": False, "phototaxis": False,
    }
    # And the controller itself still defaults to LEGACY_2_0 with no opt-in.
    controller = FlyController()
    assert controller.biological_brain.mode is BiologicalMode.LEGACY_2_0


def test_explicit_opt_in_selects_biological_3_0(reset_biological_circuits):
    """Each accepted truthy value selects 3.0B; other values do not."""
    for value, expected in (
        ("1", True), ("true", True), ("TRUE", True), ("yes", True),
        ("on", True), ("  on  ", True),
        ("0", False), ("false", False), ("", False), ("maybe", False),
    ):
        module, circuits = _load_fly_bot(value)
        assert module.ENABLE_BIOLOGICAL_3_0 is expected, value
        if expected:
            assert module.fly.biological_brain.mode is (
                BiologicalMode.BIOLOGICAL_3_0
            ), value
            # The switch is coarse: the escape circuit, and nothing else.
            assert circuits["escape"] is True, value
            assert circuits["feeding"] is False, value
            assert circuits["phototaxis"] is False, value
        else:
            assert module.fly.biological_brain.mode is (
                BiologicalMode.LEGACY_2_0
            ), value
            assert circuits["escape"] is False, value


def test_opt_in_actually_produces_biological_signals(
    reset_biological_circuits,
):
    """The opt-in must yield a real signal dict, not an inert mode."""
    module, _ = _load_fly_bot("1")
    assert module.fly.biological_brain.mode is BiologicalMode.BIOLOGICAL_3_0
    signals = module.fly.biological_brain.step({"lightLevel": 1.0})
    assert set(signals) == {
        "bio_escape_signal", "bio_flight_signal", "bio_threat_signal",
    }
    for value in signals.values():
        assert 0.0 <= value <= 1.0
    # And the controller surfaces it on the snapshot key.
    snapshot = module.fly._snapshot(biological_signals=signals)
    assert snapshot["biological_signals"] is signals


# --- 3, 4, 5. /status rendering ---------------------------------------------


class _FakeFile:
    name = "dashboard.png"


def _status_content(module, snapshot):
    """Run cmd_status against a stub interaction and return the text sent."""
    sent = {}

    class _Response:
        async def send_message(self, content=None, files=None):
            sent["content"] = content

    class _Interaction:
        response = _Response()

    # cmd_status is a discord.app_commands.Command after decoration; the
    # underlying coroutine is its .callback.
    status = getattr(module.cmd_status, "callback", module.cmd_status)

    async def _go():
        original = module.fly._snapshot
        module.fly._snapshot = lambda *a, **k: snapshot
        try:
            await status(_Interaction())
        finally:
            module.fly._snapshot = original

    asyncio.run(_go())
    return sent.get("content", "")


def test_status_is_unchanged_without_biological_signals(
    reset_biological_circuits,
):
    """With the key absent, /status reads exactly as it did before."""
    module, _ = _load_fly_bot(None)
    base = {
        "behavior": "rest",
        "drives": {
            "hunger": 0.5, "fear": 0.25, "fatigue": 0.1, "curiosity": 0.3,
        },
    }
    without = _status_content(module, dict(base))
    assert without.startswith("behavior: rest")
    assert "3.0B" not in without
    assert "bio_" not in without
    assert "escape=" not in without
    # An empty dict is treated as absent, exactly like the snapshot itself.
    empty = _status_content(module, dict(base, biological_signals={}))
    assert empty == without


def test_status_shows_the_three_signals_when_present(
    reset_biological_circuits,
):
    """The three existing signals are rendered under their existing names."""
    module, _ = _load_fly_bot("1")
    snapshot = {
        "behavior": "rest",
        "drives": {
            "hunger": 0.5, "fear": 0.25, "fatigue": 0.1, "curiosity": 0.3,
        },
        "biological_signals": {
            "bio_escape_signal": 0.25,
            "bio_flight_signal": 0.5,
            "bio_threat_signal": 0.75,
        },
    }
    content = _status_content(module, snapshot)
    # The existing behaviour block is still present and unchanged.
    assert content.startswith("behavior: rest")
    assert "hunger=0.50 fear=0.25 fatigue=0.10 curiosity=0.30" in content
    # The three signals, by their existing names, with their snapshot values.
    assert "3.0B escape-circuit signals" in content
    assert "escape=0.25" in content
    assert "flight=0.50" in content
    assert "threat=0.75" in content
    # Honest labelling: a model output, explicitly not a probability or
    # measurement, and explicitly not the 3.0D GFS model.
    assert "model output" in content
    assert "not probabilities or measurements" in content
    for forbidden in (
        "probability", "decided", "GFS", "giant fiber", "GF activity",
    ):
        assert forbidden not in content.lower(), forbidden
    # A missing individual key must not crash the render.
    partial = _status_content(module, {
        "behavior": "rest",
        "drives": snapshot["drives"],
        "biological_signals": {"bio_threat_signal": 1.0},
    })
    assert "threat=1.00" in partial


def test_status_reads_signals_from_the_snapshot_without_recomputing(
    reset_biological_circuits,
):
    """Values are passed through verbatim; the model is not stepped again."""
    module, _ = _load_fly_bot("1")
    signals = {
        "bio_escape_signal": 0.111,
        "bio_flight_signal": 0.222,
        "bio_threat_signal": 0.333,
    }
    snapshot = {
        "behavior": "rest",
        "drives": {
            "hunger": 0.0, "fear": 0.0, "fatigue": 0.0, "curiosity": 0.0,
        },
        "biological_signals": dict(signals),
    }
    content = _status_content(module, snapshot)
    # Exact round-trip of the snapshot values, to two decimals.
    assert "escape=0.11" in content
    assert "flight=0.22" in content
    assert "threat=0.33" in content
    # The snapshot dict itself is not mutated by the render.
    assert snapshot["biological_signals"] == signals
    # And the biological brain was not stepped to produce these values: a
    # stubbed brain that raises on step() still renders.
    class _Exploding:
        mode = BiologicalMode.BIOLOGICAL_3_0

        def step(self, *a, **k):
            raise AssertionError("cmd_status must not recompute signals")

    module.fly.biological_brain = _Exploding()
    again = _status_content(module, snapshot)
    assert again == content
