"""Focused tests for the 3.0D GFS NUMERICAL DEMONSTRATION boundary.

This is an OPT-IN, EXPLICITLY-LABELLED numerical demonstration, not a sensory
or visual prediction. The tests are mostly negative: their job is to prove the
feature cannot be turned into a fake sensory bridge, cannot acquire an implicit
gap-junction default, and cannot present a GF action potential as guaranteed
escape.

Scope note: the demonstration is driven by an explicit numerical GF event
because 8L sensory phenomenology and the 8I sensory-to-live-GF coupling are
deliberately unavailable. `/scare` is a 2.0 `VIS_LC` weighted group injection
and supplies no angular size, no angular velocity and no stimulus vector.
"""

import ast
import inspect

import pytest

import gfs_demonstration
from biological_brain.configuration import (
    GFS_DEMONSTRATION_FIXTURE_PROVENANCE,
    GFS_DEMONSTRATION_PROVENANCE_REQUIRED_FRAGMENT,
    BiologicalMode,
    GFSNumericalDemonstrationConfig,
    GFSNumericalDemonstrationConfigError,
)
from gfs_demonstration import (
    GF_EVENT_FIXTURE_PROVENANCE,
    GFS_DEMONSTRATION_SNAPSHOT_KEY,
    GFSNumericalDemonstrationError,
    build_gap_conductance,
    build_gf_event,
    run_gfs_numerical_demonstration,
)
from biological_brain.dynamics.gfs_circuit import GFEventSource, GFSCircuit


def _disabled_config():
    """The default, explicitly-disabled configuration."""
    return GFSNumericalDemonstrationConfig(
        gap_conductance_value=None,
        gap_conductance_unit=None,
        gap_conductance_provenance=None,
    )


def _code_tokens(module):
    """Identifiers, literals and imports in a module's CODE, ignoring prose.

    The adapter's docstrings deliberately NAME the things it refuses -- 135,
    34.5, LoomingStimulus, couple_to_live_gf -- so a raw text scan would flag
    the very sentences that document the guarantees. This walks the AST and
    returns only real code tokens.
    """
    with open(module.__file__, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    tokens = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            tokens.add(node.id)
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr)
        elif isinstance(node, ast.arg):
            tokens.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            tokens.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tokens.add(node.name)
        elif isinstance(node, ast.ClassDef):
            tokens.add(node.name)
        elif isinstance(node, ast.Constant):
            tokens.add(repr(node.value))
    return {token.lower() for token in tokens}


def _module_imports(module):
    with open(module.__file__, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
    return " ".join(imported)


def _enabled_config(**overrides):
    """A valid enabled configuration using the 1.0 nS numerical fixture."""
    kwargs = dict(
        gap_conductance_value=1.0,
        gap_conductance_unit="nS",
        gap_conductance_provenance=GFS_DEMONSTRATION_FIXTURE_PROVENANCE,
        enabled=True,
    )
    kwargs.update(overrides)
    return GFSNumericalDemonstrationConfig(**kwargs)


# --- disabled is the default and constructs nothing ------------------------


def test_disabled_config_is_the_default_and_constructs_no_gfs_circuit():
    # The dataclass default is off, and the three conductance fields have no
    # default: a caller must always state a position, even when disabled.
    disabled = _disabled_config()
    assert disabled.enabled is False
    assert disabled.gf_event_time_s == 0.0
    assert disabled.duration_ms == 5.0
    assert disabled.settle_ms == 200.0

    # The adapter refuses to build anything at all when disabled.
    assert run_gfs_numerical_demonstration(disabled) == {}
    with pytest.raises(GFSNumericalDemonstrationError):
        build_gap_conductance(disabled)
    with pytest.raises(GFSNumericalDemonstrationError):
        build_gf_event(disabled)

    # No GFSCircuit is constructed: the adapter's enabled branch is never
    # reached. Proven by the fact that neither builder ran, and asserted
    # structurally in the no-default test below.
    assert "GFSCircuit(" in inspect.getsource(run_gfs_numerical_demonstration)
    early_return = inspect.getsource(
        run_gfs_numerical_demonstration
    ).index("if not config.enabled")
    circuit_call = inspect.getsource(
        run_gfs_numerical_demonstration
    ).index("circuit = GFSCircuit(")
    assert early_return < circuit_call


def test_flycontroller_defaults_to_disabled_and_leaves_snapshot_unchanged(
    tmp_path,
):
    """`/scare` semantics are untouched while the demonstration is off."""
    import asyncio

    from fly_controller import FlyController

    # A dedicated checkpoint, so the assertion does not depend on whatever
    # ambient state a previous test persisted to fly_state.json.
    controller = FlyController(checkpoint_path=str(tmp_path / "off.json"))
    # The controller built an explicitly DISABLED configuration, not None.
    assert isinstance(
        controller.gfs_demonstration_config, GFSNumericalDemonstrationConfig
    )
    assert controller.gfs_demonstration_config.enabled is False
    # LEGACY_2_0 remains the default biological mode.
    assert controller.biological_brain.mode is BiologicalMode.LEGACY_2_0
    # The controller exposes NO execution method: the demonstration is a
    # developer/research fixture, not a behaviour path.
    assert not hasattr(controller, "_gfs_demonstration_payload")

    snapshot = asyncio.run(controller.trigger_group("VIS_LC", pulses=3))

    # The existing /scare path is unchanged: VIS_LC is a 2.0 weighted group
    # injection, and it places NO looming stimulus key in the snapshot.
    stimuli = snapshot["stimuli"]
    for looming_key in ("loomingLeft", "loomingRight", "loomingFront"):
        assert looming_key not in stimuli
    assert "VIS_LC" not in stimuli
    assert stimuli.get("lightLevel") == 1.0
    assert stimuli.get("temperature") == 0.5
    # And the demonstration contributes no key whatsoever.
    assert GFS_DEMONSTRATION_SNAPSHOT_KEY not in snapshot
    # Nothing was merged into the 2.0 signals.
    for key in (
        "bio_escape_signal", "bio_flight_signal", "bio_threat_signal",
    ):
        assert key not in snapshot or not snapshot[key]
    # No conductance and no event exist for a disabled demonstration.
    with pytest.raises(GFSNumericalDemonstrationError):
        build_gap_conductance(controller.gfs_demonstration_config)


# --- enabled requires explicit gap-conductance fields -----------------------


def test_enabled_config_requires_explicit_gap_conductance_fields():
    provenance = GFS_DEMONSTRATION_FIXTURE_PROVENANCE

    for missing, kwargs in (
        ("value", dict(
            gap_conductance_value=None, gap_conductance_unit="nS",
            gap_conductance_provenance=provenance,
        )),
        ("unit", dict(
            gap_conductance_value=1.0, gap_conductance_unit=None,
            gap_conductance_provenance=provenance,
        )),
        ("unit empty", dict(
            gap_conductance_value=1.0, gap_conductance_unit="",
            gap_conductance_provenance=provenance,
        )),
        ("provenance", dict(
            gap_conductance_value=1.0, gap_conductance_unit="nS",
            gap_conductance_provenance=None,
        )),
    ):
        with pytest.raises(GFSNumericalDemonstrationConfigError):
            GFSNumericalDemonstrationConfig(enabled=True, **kwargs)

    # A provenance that does not identify the value as a fixture is refused,
    # so the demonstration cannot be configured while claiming a biological
    # GFS conductance.
    with pytest.raises(GFSNumericalDemonstrationConfigError):
        GFSNumericalDemonstrationConfig(
            gap_conductance_value=135.0,
            gap_conductance_unit="nS",
            gap_conductance_provenance="the real GFS gap junction conductance",
            enabled=True,
        )

    # from_mapping is the operator boundary and raises on any missing key
    # rather than defaulting it.
    with pytest.raises(GFSNumericalDemonstrationConfigError):
        GFSNumericalDemonstrationConfig.from_mapping({"enabled": True})
    with pytest.raises(GFSNumericalDemonstrationConfigError):
        GFSNumericalDemonstrationConfig.from_mapping(None)
    built = GFSNumericalDemonstrationConfig.from_mapping({
        "gap_conductance_value": 1.0,
        "gap_conductance_unit": "nS",
        "gap_conductance_provenance": provenance,
        "enabled": True,
    })
    assert built.enabled is True
    assert built.duration_ms == 5.0 and built.settle_ms == 200.0

    # A valid enabled config does construct.
    assert _enabled_config().enabled is True


def test_no_implicit_gap_conductance_default_exists():
    """Neither 8I's constructor nor the product config may default a value."""
    # 8I's own requirement is untouched by this checkpoint.
    parameters = inspect.signature(GFSCircuit.__init__).parameters
    assert "gap_conductance" in parameters
    assert parameters["gap_conductance"].default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        GFSCircuit()

    # The config's three conductance fields are REQUIRED arguments: a caller
    # must always pass them, so there is no way to omit them by accident.
    config_fields = set(
        GFSNumericalDemonstrationConfig.__dataclass_fields__
    )
    for field in (
        "gap_conductance_value", "gap_conductance_unit",
        "gap_conductance_provenance",
    ):
        assert field in config_fields
    with pytest.raises(TypeError):
        GFSNumericalDemonstrationConfig()

    # 8C's refusal of a project value is still reachable and still raises.
    from biological_brain.dynamics.electrical_coupling import (
        ElectricalCouplingUnresolvedValueError,
        from_unresolved_project_conductance,
    )

    with pytest.raises(ElectricalCouplingUnresolvedValueError):
        from_unresolved_project_conductance()

    # The adapter itself has no conductance constant and no fallback path in
    # its CODE. Its docstring names 135/34.5 only to record that 7U is
    # unresolved, so the scan is on code tokens rather than prose.
    tokens = _code_tokens(gfs_demonstration)
    for banned in ("135", "135.0", "34.5", "34.5", "1.0", "'ns'", "'us'"):
        assert banned.lower() not in tokens, banned
    assert "default_gap" not in tokens
    assert "gap_ns" not in tokens
    # 7U is still unresolved in the reconciliation registry.
    from biological_brain.source_reconciliation import (
        get_source_reconciliation_registry,
    )

    registry = get_source_reconciliation_registry()
    assert set(registry.unresolved()) == {
        "g_gap_young_unit_conflict", "g_gap_old_unit_conflict",
    }
    for conflict_id in registry.unresolved():
        assert registry.get(conflict_id).preferred_side is None
        assert registry.get(conflict_id).discrepancy_factor == pytest.approx(
            1000.0
        )


def test_constructed_conductance_has_is_default_false():
    config = _enabled_config()
    conductance = build_gap_conductance(config)

    # The value and unit are carried through exactly as configured; the
    # adapter performs no unit conversion of its own.
    assert conductance.value == pytest.approx(1.0)
    assert conductance.unit == "nS"
    assert conductance.is_default is False
    # And it is the caller's declared fixture, not a library default.
    assert conductance.provenance == GFS_DEMONSTRATION_FIXTURE_PROVENANCE
    assert (
        GFS_DEMONSTRATION_PROVENANCE_REQUIRED_FRAGMENT
        in conductance.provenance
    )
    assert "7U" in conductance.provenance
    assert "no preferred side" in conductance.provenance
    # An unrecognised unit is refused by 8C, not silently coerced.
    with pytest.raises(Exception):
        build_gap_conductance(_enabled_config(gap_conductance_unit="nSiemens"))


# --- the event is a numerical solver fixture, never a visual stimulus -------


def test_gf_event_source_is_direct_numerical_stimulus():
    event = build_gf_event(_enabled_config())
    assert event.source is GFEventSource.DIRECT_NUMERICAL_STIMULUS
    # FUTURE_SENSORY_COUPLING would assert a bridge that does not exist, so it
    # must not be used.
    assert event.source is not GFEventSource.FUTURE_SENSORY_COUPLING
    assert event.source.is_visual_stimulus is False
    assert event.source.is_connected_to_the_sensory_phenomenology is False
    assert event.is_visual_stimulus is False
    assert event.is_sensory_phenomenology_output is False
    # The configured time is carried through.
    assert event.event_time_s == 0.0
    assert build_gf_event(
        _enabled_config(gf_event_time_s=0.25)
    ).event_time_s == 0.25


def test_event_provenance_identifies_a_numerical_solver_fixture():
    provenance = GF_EVENT_FIXTURE_PROVENANCE
    lowered = provenance.lower()
    # It says what it is...
    assert "numerical solver trigger" in lowered
    assert "3.0d gfs numerical demonstration fixture" in lowered
    assert "discord/product command" in lowered
    # ...and, explicitly, what it is NOT.
    assert "not a visual stimulus" in lowered
    assert "not a looming stimulus" in lowered
    assert "not a sensory drive" in lowered
    assert "not a measured biological event" in lowered
    # It also records that the sensory route is deliberately unavailable.
    assert "8l" in lowered and "not used" in lowered
    assert "couple_to_live_gf" in provenance
    assert "remains unsupported" in lowered
    # The event object carries it.
    assert build_gf_event(_enabled_config()).provenance == provenance


def test_adapter_does_not_use_8l_or_any_sensory_coupling():
    """No 8L import, no LoomingStimulus, no couple_to_live_gf, no thresholding."""
    # Scanned over CODE tokens: the adapter's docstring names LoomingStimulus
    # and couple_to_live_gf only to record that it refuses both.
    tokens = _code_tokens(gfs_demonstration)
    for banned in (
        "sensory_trigger", "gf_trigger_candidate_from_stimulus",
        "loomingstimulus", "gftriggercandidate", "gf_sensory_drive",
        "couple_to_live_gf", "action_threshold", "spike_threshold",
        "run_looming_through_live_circuit", "phenomenologicalgfdrive",
    ):
        assert banned not in tokens, banned

    # Import audit: only 3.0D-8C/8I/8K/8N and the config record.
    joined = _module_imports(gfs_demonstration)
    assert "gfs_circuit" in joined
    assert "electrical_coupling" in joined
    assert "escape_behavior" in joined
    assert "action_selection" in joined
    for banned in (
        "sensory_trigger", "gf_sensory_drive", "sensorimotor_integration",
        "fly_bot", "fly_controller", "discord", "numpy", "random",
    ):
        assert banned not in joined, banned

    # The adapter contains no biological equation and no unit conversion in
    # its code.
    for banned in (
        "1e-09", "1e-06", "1000.0", "math.exp", "nanosiemens",
    ):
        assert banned not in tokens, banned
    # It does not touch 8G's unresolved branch.
    assert "psi_dlmn_peak_conductance_source" not in tokens

    # 8I's boundary is still closed after integration: the sensory coupling
    # raises, a looming stimulus cannot be driven through the circuit, and a
    # GFSpikeEvent carries no coupling method at all.
    from biological_brain.dynamics.gfs_circuit import (
        GFSpikeEvent, UnsupportedSensoryBiophysicalCoupling,
    )
    from biological_brain.dynamics.gf_sensory_drive import (
        ConstantVelocityLoomingStimulus,
    )

    circuit = GFSCircuit(
        gap_conductance=build_gap_conductance(_enabled_config())
    )
    with pytest.raises(UnsupportedSensoryBiophysicalCoupling):
        circuit.run_looming_through_live_circuit(
            ConstantVelocityLoomingStimulus(
                r_m=0.005, v_m_per_s=0.05, d0_m=0.10
            )
        )
    # The typed boundary object also still refuses, and the circuit exposes no
    # convenience coupling method.
    trace = circuit.run_sensory_phenomenology(
        ConstantVelocityLoomingStimulus(
            r_m=0.005, v_m_per_s=0.05, d0_m=0.10
        ),
        duration_s=0.5,
        samples=51,
    )
    boundary = circuit.boundary(trace, circuit.run_live_circuit(
        build_gf_event(_enabled_config()), duration_ms=2.0, settle_ms=50.0
    ))
    with pytest.raises(UnsupportedSensoryBiophysicalCoupling):
        boundary.couple_to_live_gf()
    assert boundary.coupling_status.value == "unresolved"
    event = GFSpikeEvent(0.0, GFEventSource.DIRECT_NUMERICAL_STIMULUS, "p")
    assert not hasattr(event, "couple_to_live_gf")


# --- unresolved biology is preserved through the consumer dict --------------


def test_consumer_dict_preserves_unresolved_escape_biology():
    """8N's guarantees must survive the product boundary unchanged."""
    from biological_brain.dynamics.action_selection import (
        GFActionSelectionResult, gf_action_selection,
    )
    from biological_brain.dynamics.escape_behavior import (
        escape_behavior_from_circuit,
    )
    from biological_brain.dynamics.gfs_circuit import GFSpikeEvent

    # 8G's own default is 'paper'. The demonstration must not choose a branch,
    # so the invariants are verified on the 8G branch that yields a finite
    # DLMn, exactly as the 3.0D-8N suite does.
    conductance = build_gap_conductance(_enabled_config())
    circuit = GFSCircuit(
        gap_conductance=conductance,
        psi_dlmn_peak_conductance_source="source_weight_as_written",
    )
    result = circuit.run_live_circuit(
        build_gf_event(_enabled_config()), duration_ms=2.0, settle_ms=50.0
    )
    behaviour_of = escape_behavior_from_circuit
    behaviour = behaviour_of(result)
    consumer = gf_action_selection(result, behaviour).to_consumer_dict()

    # The four guarantees this checkpoint must not break.
    assert consumer["escape_guaranteed"] is False
    assert consumer["overall_escape_probability"] is None
    assert consumer["overall_escape_probability_status"] == "unresolved"
    assert consumer["parallel_pathways_exist"] is True

    # The adapter is a pure pass-through of 8N's consumer dict. It assigns no
    # probability and no guarantee: the only occurrences of those words are
    # inside refusal and limitation prose.
    source = inspect.getsource(gfs_demonstration)
    for assignment in (
        "overall_escape_probability =", "escape_guaranteed =",
        "parallel_pathways_exist =", "overall_escape_probability_status =",
    ):
        assert assignment not in source, assignment
    for numeric in ("0.87", "0.5", "0.95"):
        assert numeric not in source, numeric

    # 8N still refuses to be promoted to a guarantee or a probability, both on
    # the instance and at construction.
    selection = gf_action_selection(result, behaviour_of(result))
    assert selection.escape_was_guaranteed is False
    assert selection.is_escape_probability_known is False
    assert selection.overall_escape_probability is None
    assert selection.overall_escape_probability_status == "unresolved"
    with pytest.raises(Exception):
        GFActionSelectionResult(
            **{
                field: getattr(selection, field)
                for field in GFActionSelectionResult.__dataclass_fields__
            },
            overall_escape_probability=0.5,
        )


def test_snapshot_key_never_appears_on_a_behaviour_path():
    """The demonstration is unreachable from behaviour commands, enabled or not."""
    import asyncio

    from fly_controller import FlyController
    import biological_brain.configuration as cfg

    # Disabled (default): no key, and no execution method exists.
    assert GFS_DEMONSTRATION_SNAPSHOT_KEY not in asyncio.run(
        FlyController().trigger_group("VIS_LC", pulses=3)
    )

    # Enabled: STILL no key, because no behaviour command calls the adapter.
    # This is the corrective property of this checkpoint.
    cfg.BIOLOGICAL_CIRCUITS["escape"] = True
    try:
        controller = FlyController(
            biological_mode=BiologicalMode.BIOLOGICAL_3_0,
            gfs_demonstration_config=_enabled_config(),
        )
        assert controller.gfs_demonstration_config.enabled is True
        assert not hasattr(controller, "_gfs_demonstration_payload")
        for method, args in (
            ("trigger_group", ("VIS_LC", 3)),
            ("stimulate_flag", ()),
            ("set_ambient", ()),
            ("overload", ()),
        ):
            snapshot = asyncio.run(
                getattr(controller, method)(*args)
            )
            assert GFS_DEMONSTRATION_SNAPSHOT_KEY not in snapshot, method
    finally:
        cfg.BIOLOGICAL_CIRCUITS["escape"] = False

    # The key name is stable and clearly not one of the 2.0 bio signals.
    assert GFS_DEMONSTRATION_SNAPSHOT_KEY == "gfs_3d"
    for forbidden in (
        "bio_escape_signal", "bio_flight_signal", "bio_threat_signal",
    ):
        assert forbidden != GFS_DEMONSTRATION_SNAPSHOT_KEY
    # The adapter never writes into those keys.
    source = inspect.getsource(gfs_demonstration)
    for forbidden in (
        "bio_escape_signal", "bio_flight_signal", "bio_threat_signal",
    ):
        assert forbidden not in source, forbidden


def test_adapter_publishes_only_the_8n_consumer_surface():
    """The published dict is 8N's, unmodified, plus nothing."""
    from biological_brain.dynamics.action_selection import (
        gf_action_selection,
    )
    from biological_brain.dynamics.escape_behavior import (
        escape_behavior_from_circuit,
    )

    # A run that completes, using the 8G branch that yields a finite DLMn (the
    # 3.0D-8N suite's own fixture). The demonstration never selects a branch;
    # this is test-side only.
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

    assert set(consumer) == {
        "kind", "gf_action_potential_detected",
        "gf_short_mode_program_activated", "motor_output_available",
        "short_mode_motor_output_complete", "jump_initiated",
        "wing_depression_initiated", "motor_output_events",
        "escape_guaranteed", "overall_escape_probability",
        "overall_escape_probability_status", "parallel_pathways_exist",
    }
    assert consumer["kind"] == "gf_action_selection"
    # No conductance, no voltage and no unit leaks into the product surface.
    blob = repr(consumer).lower()
    for banned in ("mv", "conductance", "siemens", "provenance"):
        assert banned not in blob, banned
    # 8G is untouched by the demonstration.
    from biological_brain.dynamics.chemical_synapse import (
        PSI_DLMnChemicalSynapse,
    )

    assert PSI_DLMnChemicalSynapse().mechanism.peak_conductance_uS == (
        pytest.approx(80.0)
    )
    assert PSI_DLMnChemicalSynapse(
        peak_conductance_source="source_weight_as_written"
    ).mechanism.peak_conductance_uS == pytest.approx(0.08)
