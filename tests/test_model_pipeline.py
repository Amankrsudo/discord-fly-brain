"""End-to-end pipeline integration test (3.0D-8AA).

Verifies the complete chain from repository artifacts:

    research/model_input_freeze.csv -> load_frozen_parameters() -> ParameterSet
        -> ReducedMN5Simulator -> report()

without any manual biological parameter editing, and with every provenance and
gate protection still active. Read-only with respect to biology: nothing is
fitted, defaulted or substituted.
"""
import csv
import importlib
import os
import sys

import pytest

from biological_brain import model as entry
from biological_brain import reduced_mn5 as rm
from biological_brain.model_framework import (
    BlockedParameterError,
    ModelProvenance,
    ModelParameter,
    ParameterSet,
    ParameterStatus,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
FREEZE = os.path.join(REPO, "research", "model_input_freeze.csv")

pytestmark = pytest.mark.skipif(
    not os.path.exists(FREEZE), reason="model input freeze not generated")

EXPECTED = {"SAFE": 40, "ASSUMPTION": 31, "BLOCKED": 37}
EXPECTED_TOTAL = 108


# --- the chain loads with no manual editing ---------------------------------

def test_freeze_artifact_is_present_and_locally_addressable():
    assert entry.freeze_present() is True
    assert entry.freeze_path() == os.path.normpath(FREEZE)


def test_csv_loads_into_a_parameter_set():
    params = entry.load_model_inputs()
    assert isinstance(params, ParameterSet)
    assert len(params) == EXPECTED_TOTAL


def test_no_manual_editing_is_required():
    """A fresh load must already carry the SAFE values the model needs."""
    params = entry.load_model_inputs()
    for name in rm.PERMITTED_BIOLOGICAL_INPUTS:
        assert name in params
        assert params.require_uncontested(name) is not None


def test_pipeline_status_counts_match_the_freeze():
    s = entry.pipeline_summary()["freeze"]
    assert s["total_parameters"] == EXPECTED_TOTAL
    assert s["by_status"] == EXPECTED


def test_freeze_csv_row_count_matches_loaded_parameters():
    with open(FREEZE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(entry.load_model_inputs()) == EXPECTED_TOTAL


# --- provenance survives loading --------------------------------------------

def test_provenance_survives_loading():
    params = entry.load_model_inputs()
    for name in rm.PERMITTED_BIOLOGICAL_INPUTS:
        p = params.get(name)
        assert p.provenance is ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT
        assert p.status is ParameterStatus.SAFE
        assert p.source.strip() and p.unit.strip() and p.object.strip()
        assert p.evidence_strength.strip()


def test_every_loaded_parameter_has_exactly_one_provenance():
    params = entry.load_model_inputs()
    summary = params.provenance_summary()
    assert sum(summary["by_provenance"].values()) == EXPECTED_TOTAL
    assert set(summary["by_provenance"]) <= {
        p.value for p in ModelProvenance}


def test_units_are_explicit_on_every_loaded_parameter():
    for p in entry.load_model_inputs()._by_name.values():
        assert p.unit.strip() and p.unit.strip() != "-"


# --- SAFE values reach the model --------------------------------------------

def test_safe_values_reach_the_reduced_model():
    sim = entry.build_reduced_mn5()
    params = entry.load_model_inputs()
    assert sim.resting_potential_mv == params.require_uncontested(
        "MN5 resting potential")
    assert sim.threshold_mv == params.require_uncontested(
        "MN5 spike threshold")
    assert sim.spike_amplitude_mv == params.require_uncontested(
        "MN5 action potential amplitude")


def test_model_inputs_are_exactly_the_three_permitted():
    sim = entry.build_reduced_mn5()
    assert [b["parameter"] for b in sim.biological_inputs()] == list(
        rm.PERMITTED_BIOLOGICAL_INPUTS)


# --- blocked values stay blocked -------------------------------------------

def test_blocked_values_remain_blocked_after_loading():
    params = entry.load_model_inputs()
    for name in ("Dalpha7 channel conductance", "MN5 length constant",
                 "MN5 transfer resistance", "MN5 axoplasmic resistivity "
                 "(Drosophila-measured)", "MN5 specific membrane resistance",
                 "MN5 membrane time constant"):
        p = params.get(name)
        assert p.status is ParameterStatus.BLOCKED, name
        assert p.value is None, name
        with pytest.raises(BlockedParameterError):
            params.require(name)


def test_gated_rows_keep_their_gate_through_the_pipeline():
    params = entry.load_model_inputs()
    assert params.get("Dalpha7 channel conductance").gate == "dalpha7"
    assert params.get("MN5 length constant").gate == "transfer"


def test_pipeline_refuses_a_supplied_blocked_parameter():
    sim = entry.build_reduced_mn5()
    for name in ("Ra", "Rm", "Cm", "axial_resistance_us"):
        with pytest.raises(rm.BiologicalClaimError):
            sim.supply_biological_parameter(
                name, 1.0, ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT,
                ParameterStatus.SAFE, "fabricated")


# --- conflicting values stay conflicted -------------------------------------

def test_conflicts_survive_loading():
    params = entry.load_model_inputs()
    conflicts = params.conflicted_parameters()
    assert conflicts, "the freeze must still record unresolved conflicts"
    assert "C-01" in conflicts
    a = params.get("MN5 whole-cell capacitance (variant A)")
    b = params.get("MN5 whole-cell capacitance (variant B)")
    assert a.conflict_id == "C-01" == b.conflict_id
    assert a.status is b.status is ParameterStatus.ASSUMPTION
    assert a.value != b.value


def test_conflicted_parameters_are_not_usable_uncontested():
    params = entry.load_model_inputs()
    for name in ("MN5 whole-cell capacitance (variant A)",
                 "MN5 whole-cell capacitance (variant B)"):
        with pytest.raises(BlockedParameterError):
            params.require_uncontested(name)


def test_reduced_model_uses_no_contested_value():
    sim = entry.build_reduced_mn5()
    params = entry.load_model_inputs()
    for name in rm.PERMITTED_BIOLOGICAL_INPUTS:
        assert params.get(name).conflict_id == "", name


# --- report generation ------------------------------------------------------

def test_report_is_generated_and_complete():
    r = entry.reduced_mn5_report()
    assert r["model"] == rm.MODEL_NAME
    assert r["result_kind"] == "model_derived_output"
    assert r["is_measurement"] is False
    assert r["is_cable_model"] is False
    assert r["spatial_transfer_available"] is False
    assert r["psi_mn5_synaptic_physiology_available"] is False
    assert r["dalpha7_available"] is False
    assert len(r["biological_inputs"]) == 3
    assert r["provenance_summary"]["by_status"] == EXPECTED
    assert r["blocked_capabilities"]
    assert r["anatomy_metadata"]["total_contacts"] == 43


def test_pipeline_summary_reports_both_gates_closed():
    s = entry.pipeline_summary()
    assert s["gates"]["spatial_voltage_transfer"] == (
        "PSI->MN5 spatial voltage transfer: NOT AUTHORIZED")
    assert s["gates"]["dalpha7_receptor_conductance"] == (
        "Dalpha7 conductance: NOT AUTHORIZED")
    assert "does not perform spatial" in s["scope"]


# --- both gates remain NOT AUTHORIZED through the entry point ---------------

def test_entry_point_gate_functions_raise():
    with pytest.raises(BlockedParameterError):
        entry.require_spatial_transfer()
    with pytest.raises(BlockedParameterError):
        entry.require_dalpha7_gate()


def test_pipeline_capabilities_report_the_expected_surface():
    caps = entry.pipeline_capabilities()
    assert caps["anatomy"] is entry.Capability.AVAILABLE
    assert caps["model_input_freeze_loaded"] is entry.Capability.AVAILABLE
    assert caps["resting_state_representation"] is entry.Capability.AVAILABLE
    for key in ("cable_behaviour", "psi_mn5_synaptic_physiology",
                "psi_mn5_spatial_transfer", "passive_leak_or_decay"):
        assert caps[key] is entry.Capability.BLOCKED, key


# --- no silent fallback anywhere in the chain ------------------------------

def test_no_biological_default_exists_in_the_entry_point():
    src = open(entry.__file__, encoding="utf-8").read()
    for banned in ("= -67", "= -24", "= 45.5", "TAU", "G_SYN", "G_LEAK",
                   "RA =", "CM =", "except:", "except Exception"):
        assert banned not in src, banned


def test_entry_point_does_not_bypass_provenance():
    src = open(entry.__file__, encoding="utf-8").read()
    assert "load_frozen_parameters" in src
    assert "require_uncontested" not in src, (
        "the entry point must not re-implement the guard; the simulator owns it")
    assert "ReducedMN5Simulator(model=build_model" in src


def test_missing_freeze_fails_rather_than_defaulting(tmp_path):
    with pytest.raises(FileNotFoundError) as e:
        entry.build_reduced_mn5(str(tmp_path / "absent.csv"))
    assert "build_model_input_freeze.py" in str(e.value)


def test_pipeline_is_deterministic():
    a = entry.reduced_mn5_report()
    b = entry.reduced_mn5_report()
    assert a["biological_inputs"] == b["biological_inputs"]
    assert a["provenance_summary"] == b["provenance_summary"]


# --- import / package hygiene ----------------------------------------------

def test_entry_point_imports_without_research_retrieval_dependencies():
    src = open(entry.__file__, encoding="utf-8").read()
    for banned in ("tensorstore", "cloudvolume", "urllib", "requests",
                   "http://", "https://"):
        assert banned not in src, banned


def test_reduced_model_needs_no_network_or_optional_dependency():
    for module in (entry, rm):
        src = open(module.__file__, encoding="utf-8").read()
        for banned in ("tensorstore", "cloudvolume", "numpy", "requests"):
            assert banned not in src, (module.__name__, banned)


def test_package_import_exposes_the_entry_point():
    import biological_brain
    assert hasattr(biological_brain, "build_reduced_mn5")
    assert hasattr(biological_brain, "pipeline_summary")
    assert hasattr(biological_brain, "ReducedMN5Simulator")


def test_no_circular_import_between_model_and_reduced_mn5():
    """model -> reduced_mn5 -> model_framework must be acyclic."""
    for name in list(sys.modules):
        if name.startswith("biological_brain.model"):
            del sys.modules[name]
    for name in ("biological_brain.reduced_mn5", "biological_brain.model_framework"):
        sys.modules.pop(name, None)
    mod = importlib.import_module("biological_brain.model")
    assert mod.build_reduced_mn5 is not None


def test_entry_point_does_not_create_a_second_implementation():
    """The entry point must orchestrate, not duplicate."""
    src = open(entry.__file__, encoding="utf-8").read()
    assert "class ReducedMN5Simulator" not in src
    assert "class ParameterSet" not in src
    assert "def mesh_surface_area" not in src
