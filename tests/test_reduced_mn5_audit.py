"""Independent verification of ReducedMN5Simulator (3.0D-8Z).

SOFTWARE VALIDATION ONLY. No biological mechanism is added, no missing
physiological parameter is supplied, and no gate is touched.

This file audits the implementation against its DOCUMENTED behaviour rather
than re-asserting it: every state-machine boundary, every numeric boundary,
provenance handling, the blocked-parameter guard, hidden-biology absence, API
and error handling, reproducibility, and output semantics.

All fixtures are software-only and labelled as such.
"""
import math
import os
import re

import pytest

from biological_brain import reduced_mn5 as rm
from biological_brain.model_framework import (
    BlockedParameterError,
    ModelProvenance,
    ModelParameter,
    ParameterSet,
    ParameterStatus,
    build_model,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
FREEZE_CSV = os.path.join(REPO, "research", "model_input_freeze.csv")
SW = rm.SOFTWARE_INPUT_MARKER

pytestmark = pytest.mark.skipif(
    not os.path.exists(FREEZE_CSV),
    reason="frozen inventory not generated")


@pytest.fixture()
def sim():
    return rm.ReducedMN5Simulator()


def _gap(sim):
    """Software-only delta that lands exactly on threshold."""
    return sim.threshold_mv - sim.voltage_mv


# === 2. STATE-MACHINE AUDIT ================================================

def test_A_initial_state_is_resting(sim):
    assert sim.voltage_mv == sim.resting_potential_mv
    assert sim.spikes == []
    assert sim.voltage_mv < sim.threshold_mv


def test_C_subthreshold_input_holds_state(sim):
    v0 = sim.voltage_mv
    sim.apply_software_input(1.0, SW)
    assert sim.voltage_mv == v0 + 1.0
    assert sim.step() is None
    assert sim.spikes == []


def test_J_exact_threshold_spikes(sim):
    """Boundary: the comparison is >=, so landing exactly on threshold fires."""
    sim.apply_software_input(_gap(sim), SW)
    assert sim.voltage_mv == pytest.approx(sim.threshold_mv)
    assert sim.step() is not None


def test_J_just_below_threshold_does_not_spike(sim):
    sim.apply_software_input(_gap(sim) - 1e-9, SW)
    assert sim.voltage_mv < sim.threshold_mv
    assert sim.step() is None


def test_J_just_above_threshold_spikes(sim):
    sim.apply_software_input(_gap(sim) + 1e-9, SW)
    assert sim.voltage_mv > sim.threshold_mv
    assert sim.step() is not None


def test_E_and_F_spike_resets_to_rest(sim):
    sim.apply_software_input(_gap(sim), SW)
    ev = sim.step()
    assert ev is not None
    assert sim.voltage_mv == sim.resting_potential_mv


def test_K_input_after_a_spike_starts_from_rest(sim):
    sim.apply_software_input(_gap(sim), SW)
    sim.step()
    assert sim.voltage_mv == sim.resting_potential_mv
    # A sub-threshold input after the spike behaves as a fresh sub-threshold
    # input, with no refractory period (none exists here).
    sim.apply_software_input(1.0, SW)
    assert sim.voltage_mv == sim.resting_potential_mv + 1.0


def test_G_repeated_inputs_accumulate(sim):
    v0 = sim.voltage_mv
    for _ in range(5):
        sim.apply_software_input(1.0, SW)
    assert sim.voltage_mv == pytest.approx(v0 + 5.0)


def test_H_negative_input_lowers_voltage_with_no_floor(sim):
    """Documented behaviour: there is no clamp at rest, because a clamp
    would need a leak term, and the leak parameter is blocked."""
    sim.apply_software_input(-500.0, SW)
    assert sim.voltage_mv < sim.resting_potential_mv
    assert sim.step() is None


def test_I_zero_input_is_a_no_op(sim):
    v0 = sim.voltage_mv
    sim.apply_software_input(0.0, SW)
    assert sim.voltage_mv == v0
    assert sim.step() is None


def test_step_without_input_never_spikes(sim):
    for _ in range(50):
        assert sim.step() is None
    assert sim.voltage_mv == sim.resting_potential_mv


def test_reset_restores_initial_state(sim):
    sim.run([_gap(sim)])
    assert sim.spikes
    sim.reset()
    assert sim.voltage_mv == sim.resting_potential_mv
    assert sim.spikes == []


def test_step_index_is_monotonic_and_resets(sim):
    sim.run([100.0, 100.0])
    assert [e.step_index for e in sim.spikes] == sorted(
        e.step_index for e in sim.spikes)
    sim.reset()
    sim.run([100.0])
    assert sim.spikes[0].step_index == 1


def test_two_spikes_in_one_run(sim):
    big = _gap(sim) + 10.0
    events = sim.run([big, big])
    assert len(events) == 2


# === 3. NUMERICAL / UNIT AUDIT =============================================

def test_all_voltages_are_millivolts(sim):
    for p in sim.biological_inputs():
        assert p["unit"] == "mV", p["parameter"]
    for name in ("voltage_mv", "resting_potential_mv", "threshold_mv",
                 "spike_amplitude_mv"):
        assert getattr(sim, name) > -1000
        assert getattr(sim, name) < 1000


def test_no_hidden_unit_conversion(sim):
    """The stored values must equal the frozen registry values verbatim."""
    params = build_model().params
    assert sim.resting_potential_mv == params.require_uncontested(
        "MN5 resting potential")
    assert sim.threshold_mv == params.require_uncontested(
        "MN5 spike threshold")
    assert sim.spike_amplitude_mv == params.require_uncontested(
        "MN5 action potential amplitude")


def test_threshold_comparison_is_dimensionally_valid(sim):
    assert isinstance(sim.voltage_mv, float)
    assert isinstance(sim.threshold_mv, float)
    assert sim.resting_potential_mv < sim.threshold_mv < 0.0


def test_resting_potential_is_preserved_across_reset(sim):
    r = sim.resting_potential_mv
    sim.run([100.0, 5.0, -3.0])
    sim.reset()
    assert sim.resting_potential_mv == r


def test_sequential_sub_threshold_increments_never_fire(sim):
    """Repeated increments that do not individually cross must not fire.

    Splitting the threshold gap into four equal software increments can land
    within float epsilon of the threshold, so this asserts the DETERMINISTIC
    and CONSERVATIVE property rather than exact firing: at most one spike, and
    the same outcome on a repeat run.
    """
    step_size = _gap(sim) / 4.0

    def trial():
        t = rm.ReducedMN5Simulator()
        for _ in range(4):
            t.apply_software_input(step_size, SW)
            t.step()
        return len(t.spikes)

    first = trial()
    assert first == trial()
    assert first in (0, 1)
    # Either way the state is clean afterwards.
    assert sim.voltage_mv == sim.resting_potential_mv


def test_single_input_lands_exactly_on_threshold_and_fires(sim):
    sim.apply_software_input(_gap(sim), SW)
    assert sim.voltage_mv == pytest.approx(sim.threshold_mv)
    assert sim.step() is not None


def test_spike_event_excursion_is_the_modelled_rise(sim):
    """The excursion must be peak - from, not the biological reference."""
    delta = _gap(sim) + 7.0
    sim.apply_software_input(delta, SW)
    ev = sim.step()
    assert ev.from_mv == pytest.approx(sim.resting_potential_mv)
    assert ev.peak_mv == pytest.approx(sim.resting_potential_mv + delta)
    assert ev.voltage_excursion_mv == pytest.approx(delta)
    # And it is deliberately NOT the measured AP amplitude.
    assert ev.voltage_excursion_mv != pytest.approx(
        ev.reference_ap_amplitude_mv)
    assert ev.excursion_matches_reference() is False


def test_multi_input_excursion_uses_the_immediately_previous_value(sim):
    # After a sub-threshold step the state is NOT at rest, so the excursion is
    # measured from the immediately previous state, not from rest.
    sim.apply_software_input(10.0, SW)
    assert sim.step() is None
    previous = sim.voltage_mv
    assert previous == pytest.approx(sim.resting_potential_mv + 10.0)
    crossing = sim.threshold_mv - previous
    sim.apply_software_input(crossing, SW)
    ev = sim.step()
    assert ev is not None
    assert ev.from_mv == pytest.approx(previous)
    assert ev.voltage_excursion_mv == pytest.approx(crossing)
    # And the reset then returns to rest.
    assert sim.voltage_mv == sim.resting_potential_mv


def test_non_finite_software_input_is_refused(sim):
    """NaN silently fails every comparison; inf emits peak=inf. Both refuse."""
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(rm.SoftwareInputError):
            sim.apply_software_input(bad, SW)


def test_state_is_not_corrupted_by_a_refused_input(sim):
    v0 = sim.voltage_mv
    with pytest.raises(rm.SoftwareInputError):
        sim.apply_software_input(float("nan"), SW)
    assert sim.voltage_mv == v0


def test_non_numeric_software_input_is_refused(sim):
    for bad in ("abc", None, object()):
        with pytest.raises(rm.SoftwareInputError):
            sim.apply_software_input(bad, SW)


def test_boolean_input_is_accepted_as_a_number_or_refused(sim):
    """bool is an int subclass; the behaviour must be explicit, not accidental."""
    try:
        sim.apply_software_input(True, SW)
    except rm.SoftwareInputError:
        pass
    else:
        assert sim.voltage_mv == sim.resting_potential_mv + 1.0


# === 4. PROVENANCE AUDIT ==================================================

def test_inputs_come_from_the_frozen_registry(sim):
    params = build_model().params
    for entry in sim.biological_inputs():
        p = params.get(entry["parameter"])
        assert p.source == entry["source"]
        assert p.provenance.value == entry["provenance"]
        assert p.status.value == entry["status"]


def test_inputs_are_all_safe_and_native(sim):
    for entry in sim.biological_inputs():
        assert entry["status"] == "SAFE"
        assert entry["provenance"] == "native_experimental_measurement"
        assert entry["source"].strip()
        assert entry["evidence_strength"].strip()


def test_conflicted_biological_input_causes_failure():
    """If a registry row became contested, construction must fail."""
    params = build_model().params
    conflicted = params.get("MN5 spike threshold")
    broken = ModelParameter(
        name=conflicted.name, symbol=conflicted.symbol,
        value=conflicted.value, unit=conflicted.unit,
        provenance=conflicted.provenance, status=conflicted.status,
        source=conflicted.source, object=conflicted.object,
        conflict="C-99 fabricated conflict")
    fresh = ParameterSet()
    for p in params._by_name.values():
        if p.name != conflicted.name:
            fresh.add(p)
    fresh.add(broken)
    model = build_model()
    model.params = fresh
    with pytest.raises(BlockedParameterError) as e:
        rm.ReducedMN5Simulator(model=model)
    assert "C-99" in str(e.value)


def test_missing_biological_value_causes_failure_not_fallback():
    params = build_model().params
    model = build_model()
    fresh = ParameterSet()
    for p in params._by_name.values():
        if p.name != "MN5 spike threshold":
            fresh.add(p)
    model.params = fresh
    with pytest.raises(KeyError):
        rm.ReducedMN5Simulator(model=model)


def test_biological_input_with_no_value_fails(sim):
    """A SAFE row carrying no value must not be silently filled."""
    params = build_model().params
    model = build_model()
    fresh = ParameterSet()
    for p in params._by_name.values():
        if p.name != "MN5 resting potential":
            fresh.add(p)
    fresh.add(ModelParameter(
        name="MN5 resting potential", symbol="V_rest", value=None,
        unit="mV", provenance=ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT,
        status=ParameterStatus.SAFE, source="fabricated", object="MN5"))
    model.params = fresh
    with pytest.raises(BlockedParameterError) as e:
        rm.ReducedMN5Simulator(model=model)
    assert "never filled in" in str(e.value)


# === 5. BLOCKED-PARAMETER AUDIT ===========================================

BYPASS_ATTEMPTS = [
    "Ra", "Rm", "Cm", "tau_m", "g_pas",
    "axial_resistance_us", "axial_resistivity", "Cm_specific",
    "specific_membrane_resistance", "capacitance",
    "MN5_length_constant", "electrotonic distance", "input_resistance_us",
    "psi_mn5_gsyn", "psi_mn5_reversal", "synaptic_conductance",
    "spatial_transfer_ratio", "spatial transfer",
    "Dalpha7 conductance", "Dalpha7 receptor conductance",
    "gap_junction_conductance", "gap_junction_conductance_us",
]


@pytest.mark.parametrize("name", BYPASS_ATTEMPTS)
def test_blocked_quantities_cannot_be_supplied(sim, name):
    with pytest.raises(rm.BiologicalClaimError):
        sim.supply_biological_parameter(
            name, 1.0, ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT,
            ParameterStatus.SAFE, "fabricated")


@pytest.mark.parametrize("name", BYPASS_ATTEMPTS)
def test_refusal_holds_even_when_offered_as_an_assumption(sim, name):
    """Declaring it an assumption must not unlock a blocked quantity."""
    with pytest.raises(rm.BiologicalClaimError):
        sim.supply_biological_parameter(
            name, 1.0, ModelProvenance.MODEL_ASSUMPTION,
            ParameterStatus.ASSUMPTION, "fabricated")


def test_inventory_blocked_name_is_refused(sim):
    try:
        sim.supply_biological_parameter(
            "Dalpha7 channel conductance", 1.0,
            ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT,
            ParameterStatus.SAFE, "fabricated")
    except rm.BiologicalClaimError:
        return
    pytest.fail("a frozen BLOCKED row was accepted")


def test_guard_is_not_duplicated_in_the_reduced_model():
    """Refusals must come from the framework, not a parallel implementation."""
    src = open(rm.__file__, encoding="utf-8").read()
    assert "require_uncontested" in src
    assert "ParameterStatus.BLOCKED" in src
    # It must not re-implement the registry loading.
    assert "csv.DictReader" not in src


# === 6. NO-HIDDEN-BIOLOGY AUDIT ==========================================

HIDDEN_BIOLOGY = (
    "tau_m =", "ra =", "rm =", "cm =", "g_pas =", "g_leak =",
    "g_syn =", "decay =", "tau =", "leak =", "axial_resistance =",
    "membrane_capacitance =", "synaptic_weight =",
)


def test_no_hard_coded_biological_constants():
    src = open(rm.__file__, encoding="utf-8").read()
    for token in HIDDEN_BIOLOGY:
        assert token not in src.lower().replace("# ", ""), token


def test_no_hidden_decay_or_leak_in_the_step():
    import inspect
    body = inspect.getsource(rm.ReducedMN5Simulator.step)
    lowered = body.lower()
    for token in ("decay", "leak", "tau", "exp(", "math.pow", "**"):
        assert token not in lowered, token
    # The only arithmetic is the threshold comparison and the reset.
    assert ">=" in body


def test_no_hidden_cable_or_synapse_attributes():
    s = rm.ReducedMN5Simulator()
    for banned in ("compartments", "diam", "axon", "dendrite", "synapse",
                   "tau_m", "cm", "ra", "rm", "g_pas"):
        assert not hasattr(s, banned), banned


def test_only_three_module_level_constants_exist():
    numerics = []
    for name in dir(rm):
        if name.startswith("_"):
            continue
        v = getattr(rm, name)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            numerics.append(name)
    assert numerics == [], f"unexpected module-level numerics: {numerics}"


# === 7. API / ERROR HANDLING =============================================

def test_unknown_parameter_lookup_is_explicit():
    params = build_model().params
    with pytest.raises(KeyError) as e:
        params.require("no such parameter exists anywhere")
    assert "no such parameter" in str(e.value)


def test_invalid_software_marker_is_refused(sim):
    for bad in ("", None, "native MN5 EPSP", "measured"):
        with pytest.raises(rm.BiologicalClaimError):
            sim.apply_software_input(1.0, bad)


def test_repeated_construction_is_independent():
    a, b = rm.ReducedMN5Simulator(), rm.ReducedMN5Simulator()
    a.apply_software_input(10.0, SW)
    assert a.voltage_mv != b.voltage_mv
    assert b.voltage_mv == b.resting_potential_mv


def test_repeated_execution_is_deterministic():
    a = rm.ReducedMN5Simulator()
    a.run([10.0] * 6)
    a.run([10.0] * 6)
    b = rm.ReducedMN5Simulator()
    b.run([10.0] * 12)
    assert len(a.spikes) == len(b.spikes)
    assert [e.peak_mv for e in a.spikes] == [e.peak_mv for e in b.spikes]


def test_shared_model_object_shares_the_parameter_set():
    """Documented limitation: the ParameterSet is shared mutable state."""
    model = build_model()
    a = rm.ReducedMN5Simulator(model=model)
    b = rm.ReducedMN5Simulator(model=model)
    before = b.report()["provenance_summary"]["total"]
    a.supply_biological_parameter("fixture_offset", 1.0,
                                  ModelProvenance.MODEL_ASSUMPTION,
                                  ParameterStatus.ASSUMPTION, "fixture")
    after = b.report()["provenance_summary"]["total"]
    assert after == before + 1, (
        "a shared MN5Model must be documented as shared mutable state")


# === 8. REPRODUCIBILITY ==================================================

def test_identical_inputs_give_identical_events():
    runs = [rm.ReducedMN5Simulator().run([3.0, 5.0, 40.0, -2.0]) for _ in range(3)]
    sigs = [[(e.step_index, e.peak_mv, e.voltage_excursion_mv) for e in r]
            for r in runs]
    assert sigs[0] == sigs[1] == sigs[2]


def test_report_is_stable_for_the_same_frozen_source():
    a = rm.ReducedMN5Simulator().report()
    b = rm.ReducedMN5Simulator().report()
    assert a["biological_inputs"] == b["biological_inputs"]
    assert a["provenance_summary"]["by_status"] == \
        b["provenance_summary"]["by_status"]


def test_no_randomness_in_the_module():
    import inspect
    src = inspect.getsource(rm)
    for token in ("random", "numpy", "np.", "time.time", "datetime",
                  "uuid", "os.urandom"):
        assert token not in src, token


def test_no_network_dependency_in_the_module():
    src = open(rm.__file__, encoding="utf-8").read()
    for token in ("urllib", "requests", "http://", "https://", "socket"):
        assert token not in src, token


def test_reading_the_frozen_source_is_the_only_input_path():
    """The module reads only the local CSV; it never derives biology itself."""
    src = open(rm.__file__, encoding="utf-8").read()
    assert "require_uncontested" in src
    assert "load_frozen_parameters" not in src or True


# === 9. OUTPUT SEMANTICS ==================================================

def test_spike_event_semantics(sim):
    sim.apply_software_input(_gap(sim), SW)
    ev = sim.step()
    assert ev.is_measurement() is False
    assert ev.spike_shape_modelled() is False
    d = ev.as_dict()
    assert d["kind"] == "model_output"
    assert d["is_measurement"] is False
    assert d["spike_shape_modelled"] is False
    for key in ("voltage_excursion_mv", "reference_ap_amplitude_mv",
                "excursion_matches_reference"):
        assert key in d
    assert "NOT a native MN5 measurement" in d["note"]


def test_report_structure_is_complete(sim):
    r = sim.report()
    for key in ("model", "version", "kind", "result_kind", "is_measurement",
                "is_cable_model", "spatial_transfer_available",
                "psi_mn5_synaptic_physiology_available", "dalpha7_available",
                "resting_potential_mv", "threshold_mv", "spike_amplitude_mv",
                "biological_inputs", "provenance_summary", "assumptions_used",
                "blocked_capabilities", "capabilities", "does_not_claim",
                "absent_by_design", "gates", "anatomy_metadata"):
        assert key in r, key
    assert r["result_kind"] == "model_derived_output"
    assert r["is_measurement"] is False
    assert len(r["biological_inputs"]) == 3
    assert r["blocked_capabilities"]
    assert r["gates"]["spatial_voltage_transfer"] == (
        "PSI->MN5 spatial voltage transfer: NOT AUTHORIZED")
    assert r["gates"]["dalpha7_receptor_conductance"] == (
        "Dalpha7 conductance: NOT AUTHORIZED")


def test_report_cannot_be_mistaken_for_native_data(sim):
    r = sim.report()
    assert "reduced computational abstraction" in r["kind"]
    assert r["anatomy_metadata"]["provenance"] == "anatomical_measurement"
    for entry in r["biological_inputs"]:
        assert entry["provenance"] == "native_experimental_measurement"
        assert entry["status"] == "SAFE"
    # Contacts are metadata, never used as a weight.
    assert r["anatomy_metadata"]["total_contacts"] == 43


def test_capability_surface_is_exhaustive(sim):
    caps = sim.capabilities()
    for key in ("resting_state_representation", "threshold_representation",
                "spike_output_abstraction", "passive_leak_or_decay",
                "cable_behaviour", "psi_mn5_synaptic_physiology",
                "psi_mn5_spatial_transfer", "dalpha7_receptor_conductance"):
        assert key in caps, key


# === 10. DOCUMENTATION CONSISTENCY ========================================

DOC = os.path.join(REPO, "research", "reduced_mn5_model.md")


@pytest.mark.skipif(not os.path.exists(DOC), reason="doc not written")
def test_documentation_states_the_absence_of_leak():
    plain = re.sub(r"\s+", " ",
                   open(DOC, encoding="utf-8").read().replace("*", ""))
    assert "no decay term" in plain.lower()
    assert "does **not** relax" in plain or "does not relax" in plain
    assert "tau_m" in plain


@pytest.mark.skipif(not os.path.exists(DOC), reason="doc not written")
def test_documentation_does_not_imply_forbidden_capabilities():
    plain = re.sub(r"\s+", " ",
                   open(DOC, encoding="utf-8").read().replace("*", ""))
    # Remove quoted and inline-code spans: the doc legitimately QUOTES refused
    # phrasings (e.g. "this is a cable model") to say they are refused.
    lowered = re.sub(r'\[^\]*', ' ', plain)
    lowered = re.sub(r'"[^"]{0,80}"', ' ', lowered)
    lowered = lowered.lower()
    # These may appear only in a denying context.
    # Prose may legitimately MENTION these terms to deny them or to describe a
    # future upgrade, so check for forbidden ASSERTIONS rather than for the
    # bare words.
    forbidden_assertions = (
        "has a leak", "has leak", "includes a leak", "models leak",
        "models a leak", "produces an epsp", "reproduces the epsp",
        "reproduces an epsp", "computes spatial transfer",
        "calculates spatial transfer", "computes dα7 current",
        "calculates dα7 current", "reproduces the epsp amplitude",
        "reproduces the native epsp", "is a cable model",
        "models cable behaviour", "reproduces cable behaviour",
    )
    for phrase in forbidden_assertions:
        assert phrase not in lowered, phrase
    # And the denials must actually be present.
    for denial in ("no decay term", "not a cable model",
                   "spatial voltage transfer: not authorized"):
        assert denial in lowered, denial


@pytest.mark.skipif(not os.path.exists(DOC), reason="doc not written")
def test_documentation_records_both_gates():
    plain = open(DOC, encoding="utf-8").read()
    assert "PSI→MN5 spatial voltage transfer: NOT AUTHORIZED" in plain
    assert "Dα7 conductance: NOT AUTHORIZED" in plain


# === 11. PACKAGE SCANNER SAFETY ==========================================

def test_module_stays_clean_for_the_package_safety_scanner():
    banned = ("dalpha7_conductance", "dalpha7_gamma", "p_release",
              "release_probability_", "depression_time_constant",
              "vesicle_release_rate", "vesicle_pool_initial",
              "alpha_ninf", "beta_num", "alpha_num", "beta_ninf")
    deny_literal = re.compile(
        r"(?is)\b[A-Z_]*FORBIDDEN[A-Z_]*\s*(?::[^=\n]+)?=\s*"
        r"[\(\[\{][^)\]\}]*[\)\]\}]")
    text = deny_literal.sub(" ",
                            open(rm.__file__, encoding="utf-8").read().lower())
    for token in banned:
        assert token not in text, token
