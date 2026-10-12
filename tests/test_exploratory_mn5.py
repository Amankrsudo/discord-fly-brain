"""Safety and behaviour tests for the exploratory MN5 model (3.0D-8E).

These tests verify SAFETY INVARIANTS of the exploratory model layer,
not biology: the two gates stay closed, the frozen evidence registry
is never modified, native measurements keep native provenance, every
literature-derived range stays labelled as non-native, every free
parameter stays labelled as an assumption, and the evidence-safe
reduced model is untouched.

The exploratory layer is a best-effort model across explicit
plausible parameter ranges. Nothing here is a measurement of MN5
spatial voltage transfer or Dalpha7 conductance.
"""
import csv
import hashlib
import os
import re

import pytest

from biological_brain import exploratory_mn5 as ex
from biological_brain import model as bm
from biological_brain import model_framework as mf

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
FREEZE_CSV = os.path.join(REPO, "research", "model_input_freeze.csv")
EXPLORATORY_CSV = os.path.join(
    REPO, "research", "exploratory_parameter_ranges.csv")
MODEL_DOC = os.path.join(REPO, "research", "exploratory_mn5_model.md")
PLAN_DOC = os.path.join(REPO, "research", "exploratory_sensitivity_plan.md")
REDUCED_MN5 = os.path.join(REPO, "biological_brain", "reduced_mn5.py")
EXPLORATORY_MODULE = os.path.join(
    REPO, "biological_brain", "exploratory_mn5.py")

#: SHA-256 of reduced_mn5.py when this layer was added. The
#: exploratory layer must never modify the evidence-safe reduced model.
REDUCED_MN5_SHA256 = (
    "8c0d4e0b4fdc3ef68b3669124c580628b90ed3bb298dea11420748a1f799eea4")

#: The seven TIER A rows, named exactly as in the frozen registry.
TIER_A_NAMES = (
    "MN5 resting potential",
    "MN5 spike threshold",
    "MN5 action potential amplitude",
    "MN5 input resistance (set 1)",
    "MN5 input resistance (set 2)",
    "MN5 whole-cell capacitance (variant A)",
    "MN5 whole-cell capacitance (variant B)",
)

pytestmark = pytest.mark.skipif(
    not os.path.exists(FREEZE_CSV),
    reason="frozen inventory not generated")


# --- helpers ---------------------------------------------------------------

def _freeze_rows():
    with open(FREEZE_CSV, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _table(model):
    return {row["parameter"]: row for row in model.parameter_table()}


@pytest.fixture(scope="module")
def model_a():
    return ex.ExploratoryMN5Model(capacitance_variant="A")


@pytest.fixture(scope="module")
def sensitivity(model_a):
    return model_a.sensitivity_analysis()


@pytest.fixture(scope="module")
def calibration_a(model_a):
    return model_a.calibrate_to_somatic_epsp()


# --- 1. model authorization does not authorize native measurements -------

def test_no_existing_gate_is_opened():
    with pytest.raises(mf.BlockedParameterError):
        mf.require_spatial_transfer()
    with pytest.raises(mf.BlockedParameterError):
        mf.require_dalpha7_gate()
    r = ex.ExploratoryMN5Model(capacitance_variant="A").simulate()
    assert r.gates["spatial_voltage_transfer"] == ex.GATE_STATEMENT_TRANSFER
    assert (r.gates["dalpha7_receptor_conductance"]
            == ex.GATE_STATEMENT_DALPHA7)
    assert "NOT AUTHORIZED" in r.gates["spatial_voltage_transfer"]
    assert "NOT AUTHORIZED" in r.gates["dalpha7_receptor_conductance"]
    summary = bm.pipeline_summary()
    assert "NOT AUTHORIZED" in summary["gates"]["spatial_voltage_transfer"]
    assert "NOT AUTHORIZED" in summary["gates"]["dalpha7_receptor_conductance"]


# --- 2. registry constants never modified -------------------------------

def test_no_biological_constants_in_evidence_registry_are_modified():
    with open(FREEZE_CSV, "rb") as fh:
        before = fh.read()
    m = ex.ExploratoryMN5Model(capacitance_variant="A")
    m.simulate()
    m.calibrate_to_somatic_epsp()
    m.sensitivity_analysis(grid={"g_psi_ns": (0.01, 1.0)})
    with open(FREEZE_CSV, "rb") as fh:
        after = fh.read()
    assert before == after
    summary = mf.load_frozen_parameters(FREEZE_CSV).provenance_summary()
    assert summary["total"] == 108
    assert summary["by_status"] == {"SAFE": 40, "ASSUMPTION": 31,
                                    "BLOCKED": 37}


# --- 3. native measurements keep native provenance ----------------------

def test_native_measurements_retain_native_provenance():
    table = _table(ex.ExploratoryMN5Model(capacitance_variant="A"))
    freeze_values = {}
    for row in _freeze_rows():
        freeze_values[row["parameter"]] = mf._parse_number(row["value"])
    for name in TIER_A_NAMES:
        row = table[name]
        assert row["tier"] == ex.TIER_A
        assert row["provenance"] == "native_experimental_measurement"
        # the value is echoed from the frozen registry, not re-derived
        assert row["value"] == pytest.approx(freeze_values[name])


# --- 4. Ra is never a native MN5 measurement ----------------------------

def test_axial_resistivity_is_never_labelled_a_native_mn5_measurement():
    row = _table(ex.ExploratoryMN5Model(capacitance_variant="A"))[
        "axial resistivity"]
    assert row["provenance"] == "literature_derived_passive_parameter"
    assert row["tier"] == ex.TIER_B
    assert row["status"] == "ASSUMPTION"
    text = (row["source"] + " " + row["notes"]).lower()
    assert "not a native mn5 measurement" in text


# --- 5. Rm is never a native MN5 measurement ----------------------------

def test_specific_membrane_resistance_is_never_labelled_a_native_mn5_measurement():
    row = _table(ex.ExploratoryMN5Model(capacitance_variant="A"))[
        "specific membrane resistance"]
    assert row["provenance"] == "literature_derived_passive_parameter"
    assert row["tier"] == ex.TIER_B
    assert row["status"] == "ASSUMPTION"
    text = (row["source"] + " " + row["notes"]).lower()
    assert "not a native mn5 measurement" in text
    assert "cross-context" in text and "model-derived" in text


# --- 6. the C-01 capacitance conflict stays explicit --------------------

def test_cm_conflict_remains_explicit():
    table = _table(ex.ExploratoryMN5Model(capacitance_variant="A"))
    for variant in ("A", "B"):
        row = table[f"MN5 whole-cell capacitance (variant {variant})"]
        assert row["conflict"] == "C-01 unresolved (~2.95x)"
        assert row["status"] == "ASSUMPTION"
        assert row["provenance"] == "native_experimental_measurement"
    # no default variant: the conflict must be named explicitly
    with pytest.raises(TypeError):
        ex.ExploratoryMN5Model()
    with pytest.raises(ValueError):
        ex.ExploratoryMN5Model(capacitance_variant="C")


# --- 7. PSI g_syn is never labelled measured ----------------------------

def test_psi_synaptic_conductance_is_never_labelled_measured():
    row = _table(ex.ExploratoryMN5Model(capacitance_variant="A"))[
        "PSI synaptic peak conductance"]
    assert row["provenance"] == "model_assumption"
    assert row["status"] == "ASSUMPTION"
    assert row["tier"] == ex.TIER_C
    assert "no source" in row["source"].lower()
    assert "free" in row["source"].lower()
    assert "has ever been measured" in row["notes"].lower()


# --- 8. Dalpha7 g_max is never labelled measured ------------------------

def test_dalpha7_maximal_conductance_is_never_labelled_measured():
    row = _table(ex.ExploratoryMN5Model(capacitance_variant="A"))[
        "Dα7 maximal conductance"]
    assert row["provenance"] == "model_assumption"
    assert row["status"] == "ASSUMPTION"
    assert row["tier"] == ex.TIER_C
    assert "no source" in row["source"].lower()
    assert "never used to retroactively justify" in row["notes"].lower()


# --- 9. reversal assumptions are not PSI-native -------------------------

def test_reversal_assumptions_are_not_labelled_psi_native():
    table = _table(ex.ExploratoryMN5Model(capacitance_variant="A"))
    e_syn = table["cholinergic reversal potential (exploratory)"]
    assert e_syn["provenance"] == "model_assumption"
    assert e_syn["tier"] == ex.TIER_C
    assert e_syn["status"] == "ASSUMPTION"
    assert "model assumption" in (
        e_syn["source"] + " " + e_syn["notes"]).lower()
    assert "not a psi→mn5 measurement" in (
        e_syn["source"] + " " + e_syn["notes"]).lower()
    assert e_syn["plausible_range"] == (-15.0, 10.0)

    e_dalpha7 = table["Dα7 reversal potential (exploratory)"]
    assert e_dalpha7["provenance"] == "model_assumption"
    assert e_dalpha7["tier"] == ex.TIER_C
    assert e_dalpha7["status"] == "ASSUMPTION"
    assert e_dalpha7["plausible_range"] == (-15.0, 10.0)
    text = (e_dalpha7["source"] + " " + e_dalpha7["notes"]).lower()
    assert "model-assumed" in text and "not a native" in text


# --- 10. the transfer ratio is never labelled measured ------------------

def test_transfer_ratio_is_never_labelled_experimentally_measured():
    table = _table(ex.ExploratoryMN5Model(capacitance_variant="A"))
    row = table["effective spatial transfer ratio"]
    assert row["provenance"] == "model_assumption"
    assert row["tier"] == ex.TIER_C
    m = ex.ExploratoryMN5Model(capacitance_variant="A",
                               transfer_mode="explicit",
                               transfer_ratio=0.35)
    r = m.simulate()
    assert r.spatial_attenuation_ratio == pytest.approx(0.35)
    assert r.spatial_attenuation_provenance == "model_assumption"
    rc = ex.ExploratoryMN5Model(capacitance_variant="A").simulate()
    assert rc.spatial_attenuation_provenance == "model_derived_estimate"
    assert 0.0 < rc.spatial_attenuation_ratio < 1.0


# --- 11. model-derived outputs are clearly marked -----------------------

def test_model_derived_outputs_are_clearly_marked(model_a):
    r = model_a.simulate()
    assert r.output_provenance == "model_derived_estimate"
    assert r.is_measurement is False
    assert r.statement == ex.EXPLORATORY_STATEMENT
    assert "not a measurement" in r.statement
    assert r.model_name == "exploratory_mn5"


# --- 12. the sweep never overwrites source parameters -------------------

def test_sensitivity_analysis_does_not_overwrite_source_parameters():
    m = ex.ExploratoryMN5Model(capacitance_variant="A")
    before = m.parameter_table()
    m.sensitivity_analysis(grid={
        "axial_resistivity_ohm_cm": (30.0, 400.0),
        "g_psi_ns": (0.01, 1000.0),
    })
    after = m.parameter_table()
    assert before == after
    for row in before:
        if row["value"] is not None:
            assert m.parameters.require(row["parameter"]) == row["value"]


# --- 13. reduced_mn5.py remains unchanged -------------------------------

def test_reduced_mn5_py_remains_unchanged():
    with open(REDUCED_MN5, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    assert digest == REDUCED_MN5_SHA256
    with open(REDUCED_MN5, encoding="utf-8") as fh:
        src = fh.read()
    assert "exploratory" not in src.lower()
    # the reduced model still builds from the frozen registry alone
    assert bm.build_reduced_mn5() is not None
    summary = bm.pipeline_summary()
    assert "NOT AUTHORIZED" in summary["gates"]["spatial_voltage_transfer"]
    assert "NOT AUTHORIZED" in summary["gates"]["dalpha7_receptor_conductance"]


# --- 14. no synthetic measurement enters the registry -------------------

def test_no_synthetic_measurement_enters_the_evidence_registry():
    registry_names = {row["parameter"] for row in _freeze_rows()}
    exploratory_only = {
        row["parameter"]
        for row in ex.ExploratoryMN5Model(
            capacitance_variant="A").parameter_table()
        if row["tier"] in (ex.TIER_B, ex.TIER_C, ex.TIER_GEOMETRY)
    }
    assert exploratory_only  # the layer carries its own parameters
    assert not (exploratory_only & registry_names)
    # the registry is unchanged in size and its blocked rows stay blocked
    assert len(registry_names) == 108
    blocked_must_stay = (
        "PSI->MN5 synaptic conductance",
        "PSI->MN5 reversal potential",
        "Dalpha7 channel conductance",
        "Dalpha7 reversal potential",
        "MN5 transfer resistance",
        "MN5 specific membrane resistance",
    )
    by_name = {row["parameter"]: row for row in _freeze_rows()}
    for name in blocked_must_stay:
        assert by_name[name]["blocked"] == "yes"
        assert by_name[name]["value"].startswith("NONE")


# --- 15. model authorization and native-measurement status stay distinct ---

def test_final_authorization_states_preserve_native_measurement_limits():
    assert ex.GATE_STATEMENT_TRANSFER == (
        "PSI→MN5 postsynaptic spatial voltage transfer: "
        "MODEL-AUTHORIZED / ANATOMY + LITERATURE CONSTRAINED")
    assert ex.GATE_STATEMENT_DALPHA7 == (
        "Dα7 biological conductance: MODEL-AUTHORIZED / "
        "CHANNEL-CONSTRAINED / NATIVE VALUE MODEL-DERIVED")
    r = ex.ExploratoryMN5Model(capacitance_variant="A").simulate()
    assert r.gates["spatial_voltage_transfer"] == ex.GATE_STATEMENT_TRANSFER
    assert r.gates["dalpha7_receptor_conductance"] == (
        ex.GATE_STATEMENT_DALPHA7)
    required = (
        "MODEL-AUTHORIZED / ANATOMY + LITERATURE CONSTRAINED",
        "MODEL-AUTHORIZED / CHANNEL-CONSTRAINED / NATIVE VALUE MODEL-DERIVED",
        "no anatomically reconstructed contact-to-soma path exists",
        "MODEL-DERIVED",
        "not an experimental voltage-transfer measurement",
    )
    for path in (MODEL_DOC, PLAN_DOC):
        with open(path, encoding="utf-8") as fh:
            text = fh.read().replace("-\n", "").replace("\n", " ").lower()
        for sentence in required:
            assert sentence.lower() in text, (path, sentence)
    with pytest.raises(mf.BlockedParameterError):
        mf.require_spatial_transfer()
    with pytest.raises(mf.BlockedParameterError):
        mf.require_dalpha7_gate()


# --- behaviour: cable transfer -------------------------------------------

def test_cable_mode_attenuates_the_somatic_response(model_a):
    r = model_a.simulate()
    assert 0.0 < r.spatial_attenuation_ratio < 1.0
    assert (r.somatic_peak_depolarization_mv
            < r.local_synaptic_peak_depolarization_mv)
    assert r.spatial_attenuation_provenance == "model_derived_estimate"
    # the measured threshold excursion is 43.7 mV; the nominal
    # exploratory run stays far below it
    assert r.threshold_excursion_required_mv == pytest.approx(43.7)
    assert r.threshold_crossing is False
    assert r.spike_model_output == "NO_MODEL_SPIKE_THRESHOLD_CROSSING"


def test_somatic_peak_is_monotonic_in_g_psi(model_a):
    peaks = []
    for g in ex.DEFAULT_SWEEP_GRID["g_psi_ns"]:
        r = model_a.simulate(
            overrides={"PSI synaptic peak conductance": float(g)})
        peaks.append(r.somatic_peak_depolarization_mv)
    assert all(b > a for a, b in zip(peaks, peaks[1:]))


def test_dalpha7_statement_appears_only_when_enabled(model_a):
    assert model_a.simulate().dalpha7_statement == ""
    m7 = ex.ExploratoryMN5Model(capacitance_variant="A",
                                dalpha7_enabled=True)
    on = m7.simulate()
    assert on.dalpha7_statement == ex.DALPHA7_STATEMENT
    assert "exploratory and assumption-dependent" in on.dalpha7_statement


# --- behaviour: calibration ----------------------------------------------

def test_calibration_requires_dalpha7_disabled():
    m7 = ex.ExploratoryMN5Model(capacitance_variant="A",
                                dalpha7_enabled=True)
    with pytest.raises(ValueError):
        m7.calibrate_to_somatic_epsp()


def test_calibration_is_labelled_model_calibration(calibration_a):
    assert calibration_a.method == ex.CALIBRATION_METHOD == "MODEL_CALIBRATION"
    assert calibration_a.fitted_provenance == "model_derived_estimate"
    assert calibration_a.target_provenance.startswith(
        "native_experimental_measurement")
    assert "comparison target only" in calibration_a.target_provenance
    assert calibration_a.dalpha7_enabled is False
    assert "not a measurement" in calibration_a.statement.lower()


def test_calibration_reaches_the_comparison_target(calibration_a):
    assert calibration_a.target_mv == pytest.approx(4.71)
    assert calibration_a.target_uncertainty_mv == pytest.approx(0.35)
    assert calibration_a.resulting_somatic_peak_depolarization_mv == \
        pytest.approx(4.71, abs=0.35)
    assert 0.0 < calibration_a.fitted_g_psi_ns < 1000.0


# --- behaviour: explicit transfer mode -----------------------------------

def test_explicit_transfer_mode_uses_the_assumed_ratio():
    m = ex.ExploratoryMN5Model(capacitance_variant="A",
                               transfer_mode="explicit",
                               transfer_ratio=0.35)
    r = m.simulate()
    assert r.spatial_attenuation_ratio == pytest.approx(0.35)
    assert r.spatial_attenuation_provenance == "model_assumption"
    assert r.somatic_peak_depolarization_mv == pytest.approx(
        0.35 * r.local_synaptic_peak_depolarization_mv)
    with pytest.raises(ValueError):
        ex.ExploratoryMN5Model(capacitance_variant="A",
                               transfer_mode="explicit")


def test_constructor_rejects_out_of_range_transfer_ratio():
    for bad in (-0.1, 1.5):
        with pytest.raises(ValueError):
            ex.ExploratoryMN5Model(capacitance_variant="A",
                                   transfer_mode="explicit",
                                   transfer_ratio=bad)


# --- behaviour: numerical surface ----------------------------------------

def test_simulation_is_deterministic(model_a):
    r1 = model_a.simulate()
    r2 = model_a.simulate()
    assert (r1.somatic_peak_depolarization_mv
            == r2.somatic_peak_depolarization_mv)
    assert (r1.local_synaptic_peak_depolarization_mv
            == r2.local_synaptic_peak_depolarization_mv)


def test_unknown_override_raises(model_a):
    with pytest.raises(KeyError):
        model_a.simulate(overrides={"not a parameter": 1.0})


def test_synaptic_kinetics_validation(model_a):
    with pytest.raises(ValueError):
        model_a.simulate(overrides={
            "PSI synaptic rise time constant": 5.0,
            "PSI synaptic decay time constant": 1.0})


# --- behaviour: sensitivity design and classification --------------------

def test_sweep_grids_match_the_sensitivity_plan():
    assert ex.DEFAULT_SWEEP_GRID == {
        "axial_resistivity_ohm_cm": (30.0, 90.0, 200.0, 400.0),
        "specific_membrane_capacitance_uf_cm2": (0.6, 1.15, 2.6),
        "specific_membrane_resistance_kohm_cm2": (6.0, 10.0, 20.0, 26.0),
        "cholinergic_reversal_mv": (-15.0, 0.0, 10.0),
        "g_psi_ns": (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
        "g_dalpha7_ns": (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
    }


def test_sensitivity_design_run_counts(sensitivity):
    assert sensitivity.total_runs == 2078
    ofat_runs = sum(len(v["values"]) for v in sensitivity.ofat.values())
    assert ofat_runs == 26
    assert (sensitivity.designs
            ["2_tier_b_factorial_both_capacitance_variants"]["runs"] == 288)
    assert (sensitivity.designs
            ["3_g_psi_main_effect_across_tier_b"]["runs"] == 864)
    assert (sensitivity.designs
            ["4_g_dalpha7_main_effect_across_tier_b"]["runs"] == 864)
    assert (sensitivity.designs
            ["5_g_psi_x_g_dalpha7_interaction"]["runs"] == 36)
    assert 26 + 288 + 864 + 864 + 36 == sensitivity.total_runs


def test_conclusions_use_the_classification_vocabulary(sensitivity):
    vocab = {r.value for r in ex.RobustnessClass}
    assert vocab == {"ROBUST", "PARAMETER-DEPENDENT", "UNCONSTRAINED"}
    assert sensitivity.conclusions == {
        "a PSI synaptic input produces a local depolarization "
        "at the synaptic site": "ROBUST",
        "the somatic response is attenuated relative to the local "
        "synaptic response": "ROBUST",
        "the somatic response does NOT cross the MN5 spike threshold "
        "anywhere in the literature-bounded (TIER B) parameter space "
        "(at the nominal g_PSI)": "ROBUST",
        "whether the somatic response can cross the MN5 spike threshold "
        "by varying the free g_PSI": "UNCONSTRAINED",
        "the Dα7 component's effect on the somatic response":
            "UNCONSTRAINED",
        "the contested whole-cell capacitance (C-01) changes the peak "
        "somatic response": "PARAMETER-DEPENDENT",
    }


def test_g_dalpha7_ofat_is_not_degenerate(sensitivity):
    # the g_Dalpha7 OFAT must run with the component enabled, so the
    # somatic peak varies across the sweep instead of being constant
    peaks = sensitivity.ofat["g_dalpha7_ns"]["somatic_peak_mv_by_value"]
    assert sensitivity.ofat["g_dalpha7_ns"]["dalpha7_enabled"] is True
    assert len(set(peaks)) == len(peaks)


# --- behaviour: reporting surface ----------------------------------------

def test_report_keeps_the_five_sections(model_a, sensitivity):
    rep = model_a.report(sensitivity)
    for section in ("measured_inputs", "literature_derived_ranges",
                    "model_assumptions", "model_derived_outputs",
                    "sensitivity_robustness"):
        assert section in rep
    assert len(rep["measured_inputs"]) == 7
    assert len(rep["literature_derived_ranges"]) == 3
    assert len(rep["model_assumptions"]) == 14
    assert rep["is_measurement"] is False
    assert rep["statement"] == ex.EXPLORATORY_STATEMENT


def test_parameter_ranges_csv_schema():
    with open(EXPLORATORY_CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 24
    assert list(rows[0].keys()) == [
        "parameter", "symbol", "tier", "value", "unit",
        "plausible_range_low", "plausible_range_high", "range_scale",
        "provenance", "status", "source", "object", "conflict",
        "gate", "notes"]
    tiers = {}
    provenance = {}
    for row in rows:
        tiers[row["tier"]] = tiers.get(row["tier"], 0) + 1
        provenance[row["provenance"]] = \
            provenance.get(row["provenance"], 0) + 1
    assert tiers == {ex.TIER_A: 7, ex.TIER_B: 3, ex.TIER_C: 11,
                     ex.TIER_GEOMETRY: 3}
    assert provenance == {"native_experimental_measurement": 7,
                          "literature_derived_passive_parameter": 3,
                          "model_assumption": 14}


def test_documents_carry_the_required_statements():
    for path in (MODEL_DOC, PLAN_DOC, EXPLORATORY_CSV):
        assert os.path.exists(path)
    with open(MODEL_DOC, encoding="utf-8") as fh:
        model_text = fh.read()
    # the fifteen required sections
    for number in range(1, 16):
        assert re.search(rf"^## {number}\. ", model_text,
                         re.MULTILINE), f"missing section {number}"


def test_module_never_opens_a_file_for_writing():
    with open(EXPLORATORY_MODULE, encoding="utf-8") as fh:
        src = fh.read()
    for match in re.finditer(r"open\(([^)]*)\)", src):
        assert not re.search(r"['\"][wax+]['\"]", match.group(1)), \
            match.group(0)
