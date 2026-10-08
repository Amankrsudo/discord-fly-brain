"""Tests for the reduced MN5 computational abstraction (3.0D-8Y).

Safety-critical coverage. Every fixture here is a SOFTWARE fixture and is
labelled as such; no invented biological value appears in this file.

Tested:
 1. construction with SAFE inputs succeeds
 2. provenance is preserved
 3. is_cable_model is False
 4. spatial transfer unavailable
 5. PSI->MN5 synaptic physiology unavailable
 6. Dalpha7 unavailable
 7. blocked Ra refused
 8. blocked Rm refused
 9. conflicted Cm refused
10. blocked synaptic conductance refused
11. Dalpha7 conductance refused
12. no hidden biological defaults
13. output identifies itself as an abstraction
14. deterministic for identical software inputs
15. biological-claim safety
16. no leak term exists, by design
"""
import os
import re

import pytest

from biological_brain import reduced_mn5 as rm
from biological_brain.model_framework import (
    BlockedParameterError,
    ModelProvenance,
    ParameterSet,
    ParameterStatus,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
FREEZE_CSV = os.path.join(REPO, "research", "model_input_freeze.csv")

pytestmark = pytest.mark.skipif(
    not os.path.exists(FREEZE_CSV),
    reason="frozen inventory not generated")

#: Every software fixture input carries this marker.
SW = rm.SOFTWARE_INPUT_MARKER


@pytest.fixture()
def sim():
    return rm.ReducedMN5Simulator()


# --- 1. construction with SAFE inputs -------------------------------------

def test_construction_with_safe_inputs_succeeds(sim):
    assert math_is_finite(sim.resting_potential_mv)
    assert math_is_finite(sim.threshold_mv)
    assert math_is_finite(sim.spike_amplitude_mv)
    assert sim.voltage_mv == sim.resting_potential_mv


def math_is_finite(x):
    return isinstance(x, float) and x == x and abs(x) != float("inf")


def test_only_the_three_permitted_inputs_are_used(sim):
    names = [b["parameter"] for b in sim.biological_inputs()]
    assert names == list(rm.PERMITTED_BIOLOGICAL_INPUTS)
    assert len(names) == 3


def test_every_biological_input_is_safe_and_native():
    s = rm.ReducedMN5Simulator()
    for entry in s.biological_inputs():
        assert entry["status"] == ParameterStatus.SAFE.value
        assert entry["provenance"] == (
            ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT.value)
        assert entry["source"].strip()
        assert entry["unit"].strip()


# --- 2. provenance preserved ------------------------------------------------

def test_provenance_is_preserved_in_the_report(sim):
    ps = sim.report()["provenance_summary"]
    assert ps["total"] > 50
    assert set(ps["by_provenance"]) <= {p.value for p in ModelProvenance}
    assert ps["blocked"] > 0
    for entry in sim.biological_inputs():
        assert entry["provenance"] == (
            ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT.value)


# --- 3-6. capability refusals ------------------------------------------------

def test_model_reports_is_cable_model_false(sim):
    assert sim.is_cable_model is False
    assert sim.report()["is_cable_model"] is False
    assert sim.capabilities()["cable_behaviour"] is rm.Capability.BLOCKED


def test_spatial_transfer_is_unavailable(sim):
    assert sim.spatial_transfer_available is False
    assert sim.report()["spatial_transfer_available"] is False
    with pytest.raises(BlockedParameterError):
        rm.require_spatial_transfer()


def test_psi_mn5_synaptic_physiology_is_unavailable(sim):
    assert sim.psi_mn5_synaptic_physiology_available is False
    assert sim.capabilities()["psi_mn5_synaptic_physiology"] is (
        rm.Capability.BLOCKED)
    assert sim.model_synapse_conductance_refused()


def test_dalpha7_is_unavailable(sim):
    assert sim.dalpha7_available is False
    assert sim.capabilities()["dalpha7_receptor_conductance"] is rm.Capability.BLOCKED
    with pytest.raises(BlockedParameterError):
        rm.require_dalpha7_gate()


# --- 7-11. blocked biological supply refused -------------------------------

@pytest.mark.parametrize("name", ["Ra", "Rm", "Cm", "tau_m", "g_pas",
                                  "psi_mn5_gsyn", "psi_mn5_reversal",
                                  "spatial_transfer_ratio",
                                  "Dalpha7 conductance",
                                  "gap_junction_conductance"])
def test_blocked_parameters_are_refused(sim, name):
    with pytest.raises(rm.BiologicalClaimError) as e:
        sim.supply_biological_parameter(
            name, 1.0, ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT,
            ParameterStatus.SAFE, "fabricated")
    assert "not admissible" in str(e.value)


def test_conflicted_cm_refusal_names_the_conflict(sim):
    with pytest.raises(rm.BiologicalClaimError) as e:
        sim.supply_biological_parameter(
            "Cm", 43.0, ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT,
            ParameterStatus.SAFE, "fabricated")
    msg = str(e.value)
    assert "C-01" in msg
    assert "127" in msg and "43" in msg


def test_refusal_reasons_are_specific(sim):
    for name, needle in (("Ra", "BLOCKED"), ("spatial_transfer_ratio",
                                              "NOT AUTHORIZED"),
                         ("psi_mn5_gsyn", "ever been measured"),
                         ("gap_junction_conductance", "1000x")):
        assert needle in rm.ReducedMN5Simulator._refusal_reason(name), name


def test_leak_term_is_refused_and_absent(sim):
    """tau_m is blocked, so there is no decay -- by design, not oversight."""
    with pytest.raises(BlockedParameterError) as e:
        sim.require_leak()
    assert "NO decay term" in str(e.value)
    assert sim.capabilities()["passive_leak_or_decay"] is rm.Capability.BLOCKED
    # Voltage does not relax: only an explicit input moves it.
    v0 = sim.voltage_mv
    sim.step()
    assert sim.voltage_mv == v0


# --- 12. no hidden biological defaults -------------------------------------

def test_no_hidden_biological_defaults_exist():
    src = open(rm.__file__, encoding="utf-8").read()
    for banned in ("TAU_M =", "RA =", "RM =", "CM =", "G_PAS =",
                   "G_SYN =", "G_LEAK =", "DECAY ="):
        assert banned not in src, f"{banned} looks like a default constant"
    # The only module-level numeric biology is the model name/version.
    assert rm.SOFTWARE_INPUT_MARKER


def test_simulator_declares_no_compartment_or_synapse():
    s = rm.ReducedMN5Simulator()
    for banned in ("compartments", "synapse", "axon", "dendrite", "tau",
                   "leak", "cm", "ra", "rm"):
        assert not hasattr(s, banned), banned
    # Anatomy is metadata and must not be reachable as arithmetic.
    assert s._model.anatomy.contact_summary()["total_contacts"] == 43


def test_no_public_numeric_defaults_on_the_simulator():
    s = rm.ReducedMN5Simulator()
    public = [a for a in dir(s) if not a.startswith("_")]
    assert public
    assert not any(a.isupper() for a in public), public


# --- 13. output identifies itself ------------------------------------------

def test_output_identifies_itself_as_a_model_abstraction(sim):
    r = sim.report()
    assert r["kind"] == "reduced computational abstraction"
    assert r["result_kind"] == "model_derived_output"
    assert r["is_measurement"] is False
    assert "not measurements of MN5 physiology" in r["statement"]
    assert r["model"] == rm.MODEL_NAME
    assert r["version"] == rm.MODEL_VERSION
    assert "resting_potential_mv" in r and "threshold_mv" in r
    assert "spike_amplitude_mv" in r
    assert "blocked_capabilities" in r and r["blocked_capabilities"]


def test_spike_event_is_not_a_measurement(sim):
    sim.apply_software_input(100.0, SW)
    event = sim.step()
    assert event is not None
    assert event.is_measurement() is False
    d = event.as_dict()
    assert d["kind"] == "model_output"
    assert d["is_measurement"] is False
    assert "NOT a native MN5 measurement" in d["note"]


def test_absent_by_design_lists_the_missing_parameters(sim):
    absent = " ".join(sim.report()["absent_by_design"])
    for needle in ("tau_m", "Ra", "Rm", "Cm", "g_pas"):
        assert needle in absent, needle


# --- 14. determinism --------------------------------------------------------

def test_identical_software_inputs_give_identical_output(sim):
    sim.apply_software_input(10.0, SW)
    sim.step()
    first = (sim.voltage_mv, [e.peak_mv for e in sim.spikes])
    sim.reset()
    sim.apply_software_input(10.0, SW)
    sim.step()
    second = (sim.voltage_mv, [e.peak_mv for e in sim.spikes])
    assert first == second


def test_run_is_reproducible_across_instances():
    a = rm.ReducedMN5Simulator().run([10.0] * 6)
    b = rm.ReducedMN5Simulator().run([10.0] * 6)
    assert [e.peak_mv for e in a] == [e.peak_mv for e in b]
    assert [e.step_index for e in a] == [e.step_index for e in b]
    assert len(a) == len(b)


def test_software_input_requires_the_non_biological_marker(sim):
    with pytest.raises(rm.BiologicalClaimError) as e:
        sim.apply_software_input(5.0, "")
    assert "SOFTWARE INPUT" in str(e.value)
    with pytest.raises(rm.BiologicalClaimError):
        sim.apply_software_input(5.0, "native MN5 EPSP")


def test_spike_emitted_when_threshold_crossed(sim):
    before = sim.voltage_mv
    assert before < sim.threshold_mv
    ev = sim.run([100.0])
    assert len(ev) == 1
    # The MEASURED AP amplitude is carried as an explicit reference input, and
    # is NOT the modelled excursion. No spike shape is integrated.
    assert ev[0].reference_ap_amplitude_mv == sim.spike_amplitude_mv
    assert ev[0].voltage_excursion_mv == pytest.approx(100.0)
    assert ev[0].spike_shape_modelled() is False
    # Reset to rest on the spike.
    assert sim.voltage_mv == sim.resting_potential_mv


def test_no_spike_below_threshold(sim):
    assert sim.run([1.0, 1.0, 1.0]) == []


# --- 15. biological-claim safety -------------------------------------------

def test_forbidden_biological_claims_are_refused(sim):
    for claim in ("PSI EPSP reproduced",
                  "native MN5 EPSP reproduced",
                  "spatial transfer calculated",
                  "Dalpha7 current calculated",
                  "this is a cable model",
                  "measured MN5 response"):
        with pytest.raises(rm.BiologicalClaimError):
            sim.assert_no_biological_claim(claim)


def test_model_report_contains_no_forbidden_claim(sim):
    """Forbidden phrasings may appear ONLY inside the does_not_claim list."""
    r = sim.report()
    claims = r["does_not_claim"]
    assert claims, "the report must enumerate what it does not claim"
    for item in claims:
        assert isinstance(item, str) and item.strip()
    rest = {k: v for k, v in r.items() if k != "does_not_claim"}
    text = str(rest).lower()
    for banned in ("epsp reproduced", "spatial transfer calculated",
                   "cable model reproduced", "measured mn5 response",
                   "native epsp reproduced", "dalpha7 current calculated"):
        assert banned not in text.replace("is_cable_model", ""), banned


def test_documentation_states_the_abstraction_principle():
    path = os.path.join(REPO, "research", "reduced_mn5_model.md")
    if not os.path.exists(path):
        pytest.skip("reduced_mn5_model.md not written")
    text = open(path, encoding="utf-8").read()
    plain = re.sub(r"\s+", " ", text.replace("*", ""))
    assert ("reduced computational abstraction. Its outputs are model-derived "
            "and are not measurements of MN5 physiology") in plain
    for gate in ("PSI→MN5 spatial voltage transfer: NOT AUTHORIZED",
                 "Dα7 conductance: NOT AUTHORIZED"):
        assert gate in plain


# --- 16. framework integration --------------------------------------------

def test_reduced_model_uses_the_framework_guards():
    """It must not duplicate the provenance machinery."""
    src = open(rm.__file__, encoding="utf-8").read()
    assert "class ModelProvenance" not in src
    assert "class ParameterStatus" not in src
    assert "require_uncontested" in src


def test_reduced_model_reuses_the_frozen_biological_brain_scanner():
    """The new module must not trip the package-wide Dalpha7 scanner."""
    banned = ("dalpha7_conductance", "dalpha7_gamma", "p_release",
              "release_probability_", "depression_time_constant",
              "vesicle_release_rate", "vesicle_pool_initial",
              "alpha_ninf", "beta_num", "alpha_num", "beta_ninf")
    deny_literal = re.compile(
        r"(?is)\b[A-Z_]*FORBIDDEN[A-Z_]*\s*(?::[^=\n]+)?=\s*"
        r"[\(\[\{][^)\]\}]*[\)\]\}]")
    text = deny_literal.sub(" ", open(rm.__file__, encoding="utf-8").read().lower())
    for token in banned:
        assert token not in text, token
