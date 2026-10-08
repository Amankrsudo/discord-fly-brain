"""Tests for the one-shot parameter adoption pass.

These tests pin the ADOPTION DECISIONS recorded in
`research/parameter_adoption_ledger.csv` and
`research/parameter_adoption_plan.md`. They enforce the
provenance-first invariants of the pass:

* the ledger is structurally intact (15 columns, five categories);
* no parameter was REPLACED or DERIVED (no stronger measurement
  exists; every would-be derivation is a forbidden conversion);
* the eight native MN5 measurements are the only KEEP-as-biological
  rows and are uncontested;
* every REMAIN_UNRESOLVED row carries no value (absence is
  represented, never filled in);
* the three conflicts (C-01, C-02, C-03) are preserved with both
  sides and no preferred side;
* both scientific gates stay closed and the reduced MN5 model
  consumes only the three uncontested native measurements;
* no forbidden conversion (mesh area / path length / contact
  distance / somatic EPSP -> an electrical parameter) was applied;
* the four direct-stimulus amplitudes are KEEP as fixtures, not
  as biological inputs.
"""
import csv
import os

import pytest

from biological_brain.model_framework import (
    BlockedParameterError,
    SynapticInterface,
    build_model,
    require_dalpha7_gate,
    require_spatial_transfer,
)
from biological_brain.reduced_mn5 import (
    PERMITTED_BIOLOGICAL_INPUTS,
    ReducedMN5Simulator,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
LEDGER_CSV = os.path.join(REPO, "research", "parameter_adoption_ledger.csv")

COLUMNS = [
    "parameter_name", "module", "current_value", "units",
    "current_provenance", "best_source", "evidence_level",
    "classification", "authorized_for_biological_model",
    "replacement_value", "replacement_units", "uncertainty",
    "reason", "conflict_status", "implementation_action",
]

CATEGORIES = {"KEEP", "REPLACE", "DERIVE", "SENSITIVITY_SWEEP",
              "REMAIN_UNRESOLVED"}

NATIVE_MN5_MEASUREMENTS = (
    "MN5 resting potential",
    "MN5 spike threshold",
    "MN5 action potential amplitude",
    "MN5 input resistance set 1",
    "MN5 input resistance set 2",
    "MN5 whole-cell capacitance variant A",
    "MN5 whole-cell capacitance variant B",
    "MN5 somatic EPSP",
)

DIRECT_STIMULUS_AMPLITUDES = (
    "GF direct-stimulus amplitude",
    "TTMn direct-stimulus amplitude",
    "PSI direct-stimulus amplitude",
    "DLMn direct-stimulus amplitude",
)


def _rows():
    with open(LEDGER_CSV, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == COLUMNS
        return list(reader)


def _by_name(rows):
    return {r["parameter_name"]: r for r in rows}


def _row_containing(rows, substring):
    matches = [r for r in rows if substring in r["parameter_name"]]
    assert len(matches) == 1, (
        f"expected exactly one row containing {substring!r}, "
        f"got {len(matches)}")
    return matches[0]


class TestLedgerIntegrity:
    """The ledger parses and every row is well-formed."""

    def test_ledger_parses_with_fifteen_columns(self):
        rows = _rows()
        assert rows
        for r in rows:
            assert set(r.keys()) == set(COLUMNS)

    def test_parameter_names_are_unique(self):
        names = [r["parameter_name"] for r in _rows()]
        assert len(names) == len(set(names))

    def test_every_classification_is_one_of_five_categories(self):
        for r in _rows():
            assert r["classification"] in CATEGORIES, r["parameter_name"]

    def test_every_evidence_level_is_a_digit_0_to_8(self):
        for r in _rows():
            assert r["evidence_level"].strip().isdigit(), r["parameter_name"]
            assert 0 <= int(r["evidence_level"]) <= 8

    def test_conflict_status_is_none_or_a_c_id(self):
        for r in _rows():
            cs = r["conflict_status"].strip()
            assert cs == "none" or cs.startswith("C-0"), r["parameter_name"]


class TestNoReplaceNoDerive:
    """No stronger measurement exists; every derivation is forbidden."""

    def test_zero_replace_and_zero_derive(self):
        rows = _rows()
        assert not [r for r in rows if r["classification"] == "REPLACE"]
        assert not [r for r in rows if r["classification"] == "DERIVE"]

    def test_no_row_carries_a_replacement_value(self):
        for r in _rows():
            assert not r["replacement_value"].strip(), r["parameter_name"]


class TestNativeMeasurementsAreKeep:
    """The eight native MN5 measurements are the only biological KEEPs."""

    def test_eight_native_mn5_measurements_are_keep(self):
        by_name = _by_name(_rows())
        for name in NATIVE_MN5_MEASUREMENTS:
            assert name in by_name, name
            assert by_name[name]["classification"] == "KEEP", name
            assert by_name[name]["evidence_level"] == "1", name

    def test_reduced_mn5_inputs_are_uncontested(self):
        by_name = _by_name(_rows())
        for name in ("MN5 resting potential", "MN5 spike threshold",
                     "MN5 action potential amplitude"):
            assert by_name[name]["conflict_status"].strip() == "none"

    def test_contested_capacitance_variants_carry_c01(self):
        by_name = _by_name(_rows())
        for name in ("MN5 whole-cell capacitance variant A",
                     "MN5 whole-cell capacitance variant B"):
            assert by_name[name]["conflict_status"].startswith("C-01")


class TestBlockedCarriesNoValue:
    """A blocked quantity is represented as absence, never filled in."""

    def test_every_remain_unresolved_row_has_empty_replacement_value(self):
        for r in _rows():
            if r["classification"] == "REMAIN_UNRESOLVED":
                assert not r["replacement_value"].strip(), r["parameter_name"]


class TestConflictsPreserved:
    """C-01, C-02 and C-03 keep both sides with no preferred side."""

    def test_c01_capacitance_both_sides_no_winner(self):
        rows = [r for r in _rows()
                if r["conflict_status"].startswith("C-01")]
        assert len(rows) == 2
        values = {r["current_value"].strip() for r in rows}
        assert values == {"43", "127"}
        for r in rows:
            assert not r["replacement_value"].strip()
            assert "adjudicated" in r["implementation_action"]

    def test_c02_gap_junction_both_sides_no_winner(self):
        # The C-02 conflict is carried directly by the two GFS
        # gap-junction conductance rows, whose current_value
        # records BOTH the paper (µS) and ModelDB (nS) sides.
        rows = [r for r in _rows()
                if r["conflict_status"].startswith("C-02")
                and "µS" in r["current_value"]
                and "nS" in r["current_value"]]
        assert len(rows) == 2
        for r in rows:
            assert not r["replacement_value"].strip()
            assert "no preferred side" in r["implementation_action"]

    def test_c02_is_inherited_by_the_lif_electrical_weights(self):
        # The 3.0B LIF electrical weights inherit the same C-02
        # conflict via the gap_junction_conductance_us=135 field;
        # their current_value is the mV weight, not the conductance.
        rows = [r for r in _rows()
                if r["conflict_status"].startswith("C-02")
                and "µS" not in r["current_value"]]
        assert len(rows) == 2
        for r in rows:
            assert r["classification"] == "KEEP"
            assert "C-02" in r["reason"]
            assert not r["replacement_value"].strip()

    def test_c03_peak_conductance_both_sides_no_winner(self):
        rows = [r for r in _rows()
                if r["conflict_status"].startswith("C-03")]
        assert rows
        for r in rows:
            assert "0.08" in r["current_value"]
            assert "80" in r["current_value"]
            assert not r["replacement_value"].strip()
            assert "both sides preserved" in r["implementation_action"]


class TestGatesStayClosed:
    """Both scientific gates raise rather than degrade."""

    def test_require_spatial_transfer_raises(self):
        with pytest.raises(BlockedParameterError):
            require_spatial_transfer()

    def test_require_dalpha7_gate_raises(self):
        with pytest.raises(BlockedParameterError):
            require_dalpha7_gate()

    def test_synaptic_interface_conductance_raises(self):
        params = build_model().params
        with pytest.raises(BlockedParameterError):
            SynapticInterface(params).conductance()

    def test_reduced_mn5_consumes_only_three_uncontested_inputs(self):
        sim = ReducedMN5Simulator()
        inputs = sim.biological_inputs()
        assert [i["parameter"] for i in inputs] == list(
            PERMITTED_BIOLOGICAL_INPUTS)
        assert len(inputs) == 3
        values = {i["parameter"]: i["value"] for i in inputs}
        assert values["MN5 resting potential"] == -67.8
        assert values["MN5 spike threshold"] == -24.1
        assert values["MN5 action potential amplitude"] == 45.5


class TestForbiddenConversionsAbsent:
    """No electrical parameter was derived from a geometric quantity."""

    def test_no_electrotonic_length_constant_was_derived(self):
        row = _row_containing(_rows(), "electrotonic length constant")
        assert row["classification"] == "REMAIN_UNRESOLVED"
        assert not row["replacement_value"].strip()

    def test_no_spatial_transfer_ratio_was_derived(self):
        row = _row_containing(_rows(), "effective spatial transfer ratio")
        assert row["classification"] == "SENSITIVITY_SWEEP"
        assert not row["replacement_value"].strip()

    def test_no_psi_mn5_conductance_was_derived_from_epsp(self):
        row = _row_containing(_rows(), "PSI->MN5 synaptic conductance")
        assert row["classification"] == "REMAIN_UNRESOLVED"
        assert not row["replacement_value"].strip()
        assert "EPSP" in row["reason"]


class TestFixturesAreNotBiological:
    """The four direct-stimulus amplitudes are fixtures, not biology."""

    def test_four_direct_stimulus_amplitudes_are_keep_fixtures(self):
        by_name = _by_name(_rows())
        for name in DIRECT_STIMULUS_AMPLITUDES:
            row = by_name[name]
            assert row["classification"] == "KEEP", name
            auth = row["authorized_for_biological_model"]
            assert auth.startswith("fixture"), name
            assert not auth.startswith("yes"), name
