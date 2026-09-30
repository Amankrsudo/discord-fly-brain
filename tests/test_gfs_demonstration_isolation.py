"""Focused regression tests: the GFS demonstration must NOT be a behaviour path.

3.0D-8I classified the GFS numerical demonstration as a developer/research
fixture rather than a product integration, and removed it from the four
behaviour command paths. These tests lock that in.

The reason is biological, not cosmetic. The GFS adapter is driven by a DECLARED
NUMERICAL FIXTURE: its gap-junction conductance is the unresolved 3.0D-7U value
and it inherits 3.0D-8G's unresolved 80 uS vs 0.08 uS conflict, under which no
finite DLMn motor event is produced. Executing it from a behaviour command would
present a solver fixture as a response to a user action -- which is precisely
what the adapter's own provenance strings forbid, and what von Reyn et al.
2017 (PMID 28641115) rules out, since GF activity depends on the integration of
looming features that `/scare` does not supply.
"""

import ast
import asyncio
import inspect

import pytest

import fly_controller
import gfs_demonstration
from biological_brain.configuration import (
    GFS_DEMONSTRATION_FIXTURE_PROVENANCE,
    BiologicalMode,
    GFSNumericalDemonstrationConfig,
)
from gfs_demonstration import (
    GF_EVENT_FIXTURE_PROVENANCE,
    GFS_DEMONSTRATION_SNAPSHOT_KEY,
    build_gap_conductance,
    build_gf_event,
    run_gfs_numerical_demonstration,
)

#: The four behaviour command paths that must never reach the GFS adapter.
BEHAVIOUR_PATHS = ("set_ambient", "stimulate_flag", "trigger_group", "overload")


def _enabled_config():
    """A VALID, ENABLED demonstration config, as an operator would supply it."""
    return GFSNumericalDemonstrationConfig(
        gap_conductance_value=1.0,
        gap_conductance_unit="nS",
        gap_conductance_provenance=GFS_DEMONSTRATION_FIXTURE_PROVENANCE,
        enabled=True,
    )


def _controller(checkpoint_path=None, **overrides):
    kwargs = dict(overrides)
    if checkpoint_path is not None:
        kwargs["checkpoint_path"] = checkpoint_path
    return fly_controller.FlyController(**kwargs)


# --- the adapter is gone from every behaviour path --------------------------


def test_controller_does_not_import_the_gfs_adapter():
    """The controller must not even import it, so it cannot call it."""
    imported = []
    for node in ast.walk(ast.parse(inspect.getsource(fly_controller))):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    joined = " ".join(imported)
    assert "gfs_demonstration" not in joined
    for name in (
        "run_gfs_numerical_demonstration", "GFS_DEMONSTRATION_SNAPSHOT_KEY",
        "build_gap_conductance", "build_gf_event",
    ):
        assert name not in joined, name
    # The controller exposes no GFS execution method at all.
    for attribute in dir(fly_controller.FlyController):
        assert "gfs_demonstration_payload" not in attribute
    # The snapshot key constant is not referenced by the controller either.
    assert GFS_DEMONSTRATION_SNAPSHOT_KEY not in inspect.getsource(
        fly_controller
    )


def test_none_of_the_four_behaviour_paths_invokes_the_adapter():
    """set_ambient, stimulate_flag, trigger_group and overload are clean."""
    source = inspect.getsource(fly_controller)
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    for function in cls.body:
        if function.name not in BEHAVIOUR_PATHS:
            continue
        body = ast.get_source_segment(source, function) or ""
        for banned in (
            "gfs_demonstration_payload", "run_gfs_numerical_demonstration",
            "GFSCircuit", "GFS_DEMONSTRATION_SNAPSHOT_KEY",
            "build_gap_conductance", "build_gf_event",
        ):
            assert banned not in body, (function.name, banned)
    # Nothing anywhere in the file constructs a GFSCircuit or publishes the key.
    for banned in ("GFSCircuit(", "GFS_DEMONSTRATION_SNAPSHOT_KEY"):
        assert banned not in source, banned


def test_scare_does_not_invoke_the_adapter_even_when_enabled(tmp_path):
    """`/scare` must be identical whether the demonstration is on or off."""
    # Separate checkpoint files, so both controllers start from the same fresh
    # state. Without this the first run's save() would make the second run's
    # drives differ, and the comparison would prove nothing.
    disabled_snapshot = asyncio.run(
        _controller(str(tmp_path / "off.json")).trigger_group("VIS_LC", 3)
    )
    enabled_controller = _controller(
        str(tmp_path / "on.json"),
        gfs_demonstration_config=_enabled_config(),
    )
    assert enabled_controller.gfs_demonstration_config.enabled is True
    enabled_snapshot = asyncio.run(
        enabled_controller.trigger_group("VIS_LC", 3)
    )

    # Identical: the enabled configuration changes nothing about /scare.
    assert set(enabled_snapshot) == set(disabled_snapshot)
    assert GFS_DEMONSTRATION_SNAPSHOT_KEY not in enabled_snapshot
    assert enabled_snapshot["stimuli"] == disabled_snapshot["stimuli"]
    assert enabled_snapshot["biological_signals"] == (
        disabled_snapshot["biological_signals"]
    )
    assert enabled_snapshot["behavior"] == disabled_snapshot["behavior"]
    # The 2.0 brain uses wall-clock cooldowns, so the numeric drives differ
    # slightly between any two runs. Only the STRUCTURE is asserted here; the
    # exact comparisons above are the ones that must be exact.
    assert set(enabled_snapshot["drives"]) == set(disabled_snapshot["drives"])
    # And the existing /scare semantics are intact: VIS_LC is a 2.0 weighted
    # group injection that places no looming stimulus key.
    stimuli = enabled_snapshot["stimuli"]
    for looming_key in ("loomingLeft", "loomingRight", "loomingFront"):
        assert looming_key not in stimuli
    assert "VIS_LC" not in stimuli
    assert stimuli.get("lightLevel") == 1.0
    assert stimuli.get("temperature") == 0.5


def test_no_gfscircuit_is_constructed_on_any_behaviour_path():
    """Structural proof: the controller cannot build a circuit, so it cannot."""
    source = inspect.getsource(fly_controller)
    # The PARAMETER name gfs_demonstration_config deliberately remains (it is
    # the hook a future research surface uses, and the opt-in a test sets), so
    # the check is on what the controller can actually DO, not on the word.
    assert "GFSCircuit" not in source
    assert "run_gfs_numerical_demonstration" not in source
    assert "GFS_DEMONSTRATION_SNAPSHOT_KEY" not in source
    assert "escape_behavior_from_circuit" not in source
    assert "gf_action_selection" not in source
    # And the controller imports nothing from the adapter module (asserted by
    # AST in the companion test above).
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any("gfs_demonstration" in name for name in imported)


def test_other_behaviour_paths_are_also_clean_when_enabled(tmp_path):
    """stimulate_flag, set_ambient and overload ignore the demonstration too."""
    controller = _controller(
        str(tmp_path / "on.json"),
        gfs_demonstration_config=_enabled_config(),
    )
    assert controller.gfs_demonstration_config.enabled is True

    disabled = _controller(str(tmp_path / "off.json"))
    # stimulate_flag
    enabled_wind = asyncio.run(controller.stimulate_flag(wind=True, windStrength=0.5))
    disabled_wind = asyncio.run(disabled.stimulate_flag(wind=True, windStrength=0.5))
    assert set(enabled_wind) == set(disabled_wind)
    assert GFS_DEMONSTRATION_SNAPSHOT_KEY not in enabled_wind
    # set_ambient
    enabled_ambient = asyncio.run(controller.set_ambient(lightLevel=0.3))
    disabled_ambient = asyncio.run(disabled.set_ambient(lightLevel=0.3))
    assert set(enabled_ambient) == set(disabled_ambient)
    assert GFS_DEMONSTRATION_SNAPSHOT_KEY not in enabled_ambient
    # overload
    enabled_overload = asyncio.run(controller.overload())
    disabled_overload = asyncio.run(disabled.overload())
    assert set(enabled_overload) == set(disabled_overload)
    assert GFS_DEMONSTRATION_SNAPSHOT_KEY not in enabled_overload


# --- defaults and legacy behaviour are unchanged ----------------------------


def test_defaults_and_legacy_mode_are_unchanged():
    controller = _controller()
    # LEGACY_2_0 remains the default biological mode.
    assert controller.biological_brain.mode is BiologicalMode.LEGACY_2_0
    # The demonstration config defaults to explicitly disabled.
    assert isinstance(
        controller.gfs_demonstration_config, GFSNumericalDemonstrationConfig
    )
    assert controller.gfs_demonstration_config.enabled is False
    # BIOLOGICAL_CIRCUITS defaults are untouched.
    import biological_brain.configuration as cfg

    assert cfg.BIOLOGICAL_CIRCUITS == {
        "escape": False, "feeding": False, "phototaxis": False,
    }
    assert cfg.BiologicalMode.LEGACY_2_0.value == "legacy_2_0"


# --- the adapter remains an independent developer/research fixture ---------


def test_the_adapter_is_still_independently_usable():
    """The retained fixture is testable on its own, with no controller."""
    # Disabled: builds nothing at all.
    disabled = GFSNumericalDemonstrationConfig(
        gap_conductance_value=None,
        gap_conductance_unit=None,
        gap_conductance_provenance=None,
    )
    assert run_gfs_numerical_demonstration(disabled) == {}

    # Enabled: the fixture pieces are constructible in isolation, and neither
    # requires a FlyController.
    config = _enabled_config()
    conductance = build_gap_conductance(config)
    assert conductance.value == pytest.approx(1.0)
    assert conductance.unit == "nS"
    assert conductance.is_default is False
    event = build_gf_event(config)
    assert event.provenance == GF_EVENT_FIXTURE_PROVENANCE
    # The module still exists and still publishes the key, for a future
    # research surface; only the controller wiring was removed.
    assert gfs_demonstration.gfs_demonstration_scope_note()
    assert GFS_DEMONSTRATION_SNAPSHOT_KEY == "gfs_3d"


def test_adapter_invariants_remain_intact():
    """Every guard the adapter carries survives the unwiring."""
    import inspect as _inspect

    from biological_brain.dynamics.gfs_circuit import GFEventSource, GFSCircuit

    # 1. Explicit conductance required, and no implicit default anywhere.
    parameters = _inspect.signature(GFSCircuit.__init__).parameters
    assert parameters["gap_conductance"].default is _inspect.Parameter.empty
    with pytest.raises(TypeError):
        GFSCircuit()
    with pytest.raises(TypeError):
        GFSNumericalDemonstrationConfig()

    # 2. Conductance is never a default and is the declared fixture.
    conductance = build_gap_conductance(_enabled_config())
    assert conductance.is_default is False
    assert (
        conductance.provenance == GFS_DEMONSTRATION_FIXTURE_PROVENANCE
    )

    # 3. The event is a numerical solver fixture, never a visual stimulus.
    event = build_gf_event(_enabled_config())
    assert event.source is GFEventSource.DIRECT_NUMERICAL_STIMULUS
    # FUTURE_SENSORY_COUPLING would assert a sensory bridge that does not
    # exist, so it must never be the source here.
    assert event.source is not GFEventSource.FUTURE_SENSORY_COUPLING
    assert event.is_visual_stimulus is False
    assert "NOT a visual stimulus" in event.provenance
    assert "NOT a measured biological event" in event.provenance


    # 4. No 8L sensory coupling anywhere in the adapter's code.
    tokens = set()
    with open(gfs_demonstration.__file__, encoding="utf-8") as handle:
        for node in ast.walk(ast.parse(handle.read())):
            if isinstance(node, ast.Name):
                tokens.add(node.id.lower())
            elif isinstance(node, ast.Attribute):
                tokens.add(node.attr.lower())
            elif isinstance(node, ast.Constant):
                tokens.add(repr(node.value).lower())
    for banned in (
        "sensory_trigger", "gf_trigger_candidate_from_stimulus",
        "loomingstimulus", "couple_to_live_gf", "psi_dlmn_peak_conductance_source",
    ):
        assert banned not in tokens, banned

    # 5. The 8I boundary is still closed.
    from biological_brain.dynamics.gfs_circuit import (
        UnsupportedSensoryBiophysicalCoupling,
    )
    from biological_brain.dynamics.gf_sensory_drive import (
        ConstantVelocityLoomingStimulus,
    )

    with pytest.raises(UnsupportedSensoryBiophysicalCoupling):
        GFSCircuit(gap_conductance=conductance).run_looming_through_live_circuit(
            ConstantVelocityLoomingStimulus(
                r_m=0.005, v_m_per_s=0.05, d0_m=0.10
            )
        )

    # 6. 7U and 8G remain unresolved and untouched.
    from biological_brain.dynamics.chemical_synapse import (
        PSI_DLMnChemicalSynapse,
    )
    from biological_brain.source_reconciliation import (
        get_source_reconciliation_registry,
    )

    registry = get_source_reconciliation_registry()
    assert set(registry.unresolved()) == {
        "g_gap_young_unit_conflict", "g_gap_old_unit_conflict",
    }
    for conflict_id in registry.unresolved():
        assert registry.get(conflict_id).preferred_side is None
    assert PSI_DLMnChemicalSynapse().mechanism.peak_conductance_uS == (
        pytest.approx(80.0)
    )
    assert PSI_DLMnChemicalSynapse(
        peak_conductance_source="source_weight_as_written"
    ).mechanism.peak_conductance_uS == pytest.approx(0.08)


def test_consumer_dict_invariants_remain_intact():
    """8N's escape guarantees survive, on the branch 8N's own suite uses."""
    from biological_brain.dynamics.action_selection import gf_action_selection
    from biological_brain.dynamics.escape_behavior import (
        escape_behavior_from_circuit,
    )
    from biological_brain.dynamics.gfs_circuit import GFSCircuit

    # Test-side only: the 8G branch that yields a finite DLMn. The adapter
    # itself never selects a branch, and 8G's default is unchanged.
    circuit = GFSCircuit(
        gap_conductance=build_gap_conductance(_enabled_config()),
        psi_dlmn_peak_conductance_source="source_weight_as_written",
    )
    result = circuit.run_live_circuit(
        build_gf_event(_enabled_config()), duration_ms=2.0, settle_ms=50.0
    )
    consumer = gf_action_selection(
        result, escape_behavior_from_circuit(result)
    ).to_consumer_dict()

    assert consumer["escape_guaranteed"] is False
    assert consumer["overall_escape_probability"] is None
    assert consumer["overall_escape_probability_status"] == "unresolved"
    assert consumer["parallel_pathways_exist"] is True
