"""Focused tests for the final MN5 model's provenance-safe analysis surfaces."""
from __future__ import annotations

import math
import os
import tempfile

import pytest

from research.scripts import analyze_mn5_two_gate_constraint_model as analysis


def _swc_paths():
    return {
        body: os.path.join(tempfile.gettempdir(), f"em_{body}.swc")
        for body in analysis.EXPECTED_CONTACTS
    }


@pytest.fixture(scope="module")
def analysis_result():
    return analysis.run_analysis(swc_paths=_swc_paths())


def test_preserves_all_43_audited_contact_mappings():
    contacts = analysis.load_contact_geometry(swc_paths=_swc_paths())
    assert len(contacts) == 43
    assert {body: sum(c.post_body == body for c in contacts)
            for body in (801970, 801295)} == {801970: 17, 801295: 26}
    assert all(c.pre_body == analysis.EXPECTED_PRE[c.post_body]
               for c in contacts)
    assert len({c.contact_id for c in contacts}) == 43
    assert all(c.swc_type_code == 0 for c in contacts)
    assert not any(hasattr(c, "soma_path_um") for c in contacts)
    tied = [c for c in contacts
            if c.projection_status == "MATCHED_SEGMENT_TIE_SAME_NODE"]
    assert len(tied) == 1
    assert tied[0].node_index == 151


def test_contact_local_response_uses_real_local_geometry_without_a_soma_path():
    contacts = analysis.load_contact_geometry(swc_paths=_swc_paths())
    peaks = [
        analysis.contact_local_peak(
            contact, g_psi_ns=1.0, e_syn_mv=0.0,
            cm_spec_uf_cm2=1.15, rm_kohm_cm2=6.0)
        for contact in contacts
    ]
    assert len(peaks) == 43
    assert all(math.isfinite(peak) and math.isfinite(time)
               for peak, time in peaks)
    assert all(peak > 0.0 for peak, _ in peaks)
    assert min(peak for peak, _ in peaks) < max(peak for peak, _ in peaks)


def test_abstract_transfer_is_separate_model_authorized_and_model_derived():
    result = analysis.simulate_abstract_transfer("A")
    assert result.output_provenance == "model_derived_estimate"
    assert result.spatial_attenuation_provenance == "model_derived_estimate"
    assert 0.0 < result.spatial_attenuation_ratio < 1.0
    assert (result.somatic_peak_depolarization_mv
            < result.local_synaptic_peak_depolarization_mv)
    assert result.gates["spatial_voltage_transfer"] == (
        "PSI→MN5 postsynaptic spatial voltage transfer: "
        "MODEL-AUTHORIZED / ANATOMY + LITERATURE CONSTRAINED")
    assert result.gates["dalpha7_receptor_conductance"] == (
        "Dα7 biological conductance: MODEL-AUTHORIZED / "
        "CHANNEL-CONSTRAINED / NATIVE VALUE MODEL-DERIVED")


def test_dalpha7_zero_condition_matches_disabled_model():
    disabled = analysis.simulate_abstract_transfer("A")
    enabled_zero = analysis.simulate_abstract_transfer(
        "A", dalpha7_enabled=True, g_dalpha7_effective=0.0)
    assert (enabled_zero.local_synaptic_peak_depolarization_mv
            == disabled.local_synaptic_peak_depolarization_mv)
    assert (enabled_zero.somatic_peak_depolarization_mv
            == disabled.somatic_peak_depolarization_mv)


def test_dalpha7_effect_depends_on_free_effective_conductance():
    disabled = analysis.simulate_abstract_transfer("A")
    low = analysis.simulate_abstract_transfer(
        "A", dalpha7_enabled=True, g_dalpha7_effective=0.01)
    high = analysis.simulate_abstract_transfer(
        "A", dalpha7_enabled=True, g_dalpha7_effective=1000.0)
    assert low.output_provenance == high.output_provenance == (
        "model_derived_estimate")
    assert high.local_synaptic_peak_depolarization_mv > (
        low.local_synaptic_peak_depolarization_mv)
    assert high.somatic_peak_depolarization_mv > (
        disabled.somatic_peak_depolarization_mv)


def test_analysis_outputs_are_finite_and_have_expected_shape(analysis_result):
    rows, summary = analysis_result
    assert len(rows) == 15528
    assert summary["all_outputs_finite"] is True


def test_calibration_is_model_derived_comparison_not_validation(analysis_result):
    rows, summary = analysis_result
    calibration = summary["calibrated_g_PSI_at_nominal_passives"]
    assert calibration["A"]["g_PSI_nS"] == pytest.approx(4.49, abs=0.02)
    assert calibration["B"]["g_PSI_nS"] == pytest.approx(10.16, abs=0.03)
    assert all(item["provenance"] == "model_derived_estimate"
               for item in calibration.values())
    calibration_rows = [
        row for row in rows
        if row["analysis_id"] == "EPSP_TARGET_MODEL_CALIBRATION"
    ]
    assert calibration_rows
    assert all("not model validation" in row["interpretation"].lower()
               for row in calibration_rows)


def test_threshold_crossings_are_limited_to_explicit_dalpha7_sweep(
        analysis_result):
    rows, summary = analysis_result
    crossings = [row for row in rows if row["threshold_crossing"] is True]
    abstract_crossings = [
        row for row in crossings
        if row["analysis_id"] == "ABSTRACT_SOMATIC_TRANSFER"
    ]
    dalpha7_crossings = [
        row for row in crossings
        if row["analysis_id"] == "DALPHA7_EFFECTIVE_CONDUCTANCE_SWEEP"
    ]
    assert len(abstract_crossings) == summary["abstract_threshold_crossings"]
    assert len(dalpha7_crossings) == summary["dalpha7_threshold_crossings"]
    assert len(crossings) == (
        summary["abstract_threshold_crossings"]
        + summary["dalpha7_threshold_crossings"])
    assert abstract_crossings and dalpha7_crossings
    assert all(float(row["g_PSI_nS"]) in (100.0, 1000.0)
               for row in abstract_crossings)
    assert all(float(row["g_Dalpha7_effective_nS"]) in (100.0, 1000.0)
               for row in dalpha7_crossings)


def test_dalpha7_reversal_value_is_model_assumed_not_biological():
    from biological_brain.exploratory_mn5 import (
        ExploratoryMN5Model,
        FREE_PARAMETERS,
        TIER_C,
    )

    row = {
        item["parameter"]: item
        for item in ExploratoryMN5Model(
            capacitance_variant="A").parameter_table()
    }["Dα7 reversal potential (exploratory)"]
    assert row["tier"] == TIER_C
    assert row["provenance"] == "model_assumption"
    assert row["status"] == "ASSUMPTION"
    assert "Dα7 reversal potential (exploratory)" in FREE_PARAMETERS


def test_same_explicit_model_inputs_are_deterministic():
    first = analysis.simulate_abstract_transfer(
        "A", ra=35.4, cm=1.0, rm=6.0, e_syn=0.0, g_psi=1.0)
    second = analysis.simulate_abstract_transfer(
        "A", ra=35.4, cm=1.0, rm=6.0, e_syn=0.0, g_psi=1.0)
    assert first == second
