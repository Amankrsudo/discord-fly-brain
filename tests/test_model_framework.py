"""Tests for the provenance-safe model framework (3.0D-8X).

These tests verify SAFETY INVARIANTS, not biology. Every fixture here is a
SOFTWARE fixture with an obviously synthetic marker; none of them is a
biological value, and none can become a production default because the
framework has no default-value constructor path at all.

Covered:
 1. SAFE parameter accepted
 2. ASSUMPTION parameter accepted but visibly marked
 3. BLOCKED parameter rejected
 4. spatial-transfer gate rejection
 5. Dalpha7 gate rejection
 6. missing synaptic conductance rejection
 7. unresolved-conflict parameters rejected
 8. provenance reporting
 9. anatomy/contact metadata loading
10. no biological placeholder defaults
11. capability report
12. regression against the frozen inventory and the anatomy audit
"""
import csv
import math
import os

import pytest

from biological_brain import model_framework as mf
from biological_brain.provenance import ParameterProvenance

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
FREEZE_CSV = os.path.join(REPO, "research", "model_input_freeze.csv")

#: A marker that makes it obvious these are software fixtures.
FIXTURE = "SOFTWARE TEST FIXTURE -- NOT A BIOLOGICAL VALUE"


pytestmark = pytest.mark.skipif(
    not os.path.exists(FREEZE_CSV),
    reason="frozen inventory not generated")


# --- helpers ---------------------------------------------------------------

def _mk(name, value, status, provenance=mf.ModelProvenance.MODEL_ASSUMPTION,
        gate="", symbol="x", unit="dimensionless", notes=""):
    return mf.ModelParameter(
        name=name, symbol=symbol, value=value, unit=unit,
        provenance=provenance, status=status, source=FIXTURE,
        object="test fixture", gate=gate, notes=notes or FIXTURE)


# --- 1. SAFE accepted ------------------------------------------------------

def test_safe_parameter_is_accepted_and_returns_its_value():
    p = _mk("fixture_safe", 1.0, mf.ParameterStatus.SAFE,
            mf.ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT)
    ps = mf.ParameterSet([p])
    assert ps.require("fixture_safe") == 1.0
    assert ps.get("fixture_safe").is_usable
    assert not ps.get("fixture_safe").is_assumption


def test_safe_parameter_without_a_value_is_reported_as_absent():
    p = mf.ModelParameter(
        name="fixture_no_value", symbol="x", value=None,
        unit="categorical", provenance=mf.ModelProvenance.ANATOMICAL_MEASUREMENT,
        status=mf.ParameterStatus.SAFE, source=FIXTURE, object="test fixture")
    with pytest.raises(mf.BlockedParameterError) as e:
        mf.ParameterSet([p]).require("fixture_no_value")
    assert "never filled in" in str(e.value)


# --- 2. ASSUMPTION accepted but marked -------------------------------------

def test_assumption_is_accepted_but_visibly_marked():
    p = _mk("fixture_assumption", 2.0, mf.ParameterStatus.ASSUMPTION)
    ps = mf.ParameterSet([p])
    assert ps.require("fixture_assumption") == 2.0
    assert ps.get("fixture_assumption").is_assumption
    assert ps.assumptions_used() == ["fixture_assumption"]
    summary = ps.provenance_summary()
    assert summary["assumptions_used"] == 1
    assert summary["assumptions"] >= 1
    assert "fixture_assumption" in summary["assumption_names"]


def test_assumption_never_counts_as_safe():
    ps = mf.ParameterSet([_mk("a", 1.0, mf.ParameterStatus.ASSUMPTION)])
    s = ps.provenance_summary()
    assert s["by_status"].get("SAFE", 0) == 0
    assert s["by_status"]["ASSUMPTION"] == 1


# --- 3. BLOCKED rejected ---------------------------------------------------

def test_blocked_parameter_is_rejected_with_an_informative_message():
    p = mf.ModelParameter(
        name="fixture_blocked", symbol="b", value=None, unit="uS",
        provenance=mf.ModelProvenance.MODEL_ASSUMPTION,
        status=mf.ParameterStatus.BLOCKED, source=FIXTURE,
        object="test fixture", gate=mf.GATE_DALPHA7,
        notes="no measurement exists")
    with pytest.raises(mf.BlockedParameterError) as e:
        mf.ParameterSet([p]).require("fixture_blocked")
    msg = str(e.value)
    assert "fixture_blocked" in msg
    assert "BLOCKED" in msg
    assert "No biological fallback value is permitted" in msg
    assert mf.GATE_DALPHA7 in msg
    assert not ps_has_value(p)


def ps_has_value(p):
    return p.value is not None


def test_blocked_parameter_cannot_be_constructed_with_a_biological_value():
    with pytest.raises(mf.BlockedParameterError) as e:
        mf.ModelParameter(
            name="fixture_bad", symbol="c", value=0.08, unit="uS",
            provenance=mf.ModelProvenance.MODEL_ASSUMPTION,
            status=mf.ParameterStatus.BLOCKED, source=FIXTURE,
            object="test fixture")
    assert "must not carry a biological value" in str(e.value)


def test_blocked_may_record_what_an_artefact_executed():
    """A code-execution record may carry a number; require() still refuses."""
    p = mf.ModelParameter(
        name="fixture_code_record", symbol="d", value=0.08, unit="uS",
        provenance=mf.ModelProvenance.MODEL_ASSUMPTION,
        status=mf.ParameterStatus.BLOCKED, source=FIXTURE,
        object="test fixture", recorded_value=True)
    assert p.value == 0.08
    with pytest.raises(mf.BlockedParameterError):
        mf.ParameterSet([p]).require("fixture_code_record")


# --- 4. spatial transfer gate ----------------------------------------------

def test_spatial_transfer_gate_always_raises():
    with pytest.raises(mf.BlockedParameterError) as e:
        mf.require_spatial_transfer()
    msg = str(e.value)
    assert "NOT AUTHORIZED" in msg
    assert "axial resistance" in msg
    assert "No biological fallback value is permitted" in msg


def test_spatial_transfer_capability_is_blocked():
    model = mf.build_model()
    assert model.capabilities()["psi_mn5_spatial_transfer"] is \
        mf.Capability.BLOCKED
    assert model.report()["gates"]["spatial_voltage_transfer"] == \
        "NOT AUTHORIZED"


# --- 5. Dalpha7 gate -------------------------------------------------------

def test_dalpha7_gate_always_raises():
    with pytest.raises(mf.BlockedParameterError) as e:
        mf.require_dalpha7_gate()
    assert "NOT AUTHORIZED" in str(e.value)
    assert "Kir7.1" in str(e.value)


def test_dalpha7_interface_is_schema_only():
    model = mf.build_model()
    s = model.dalpha7.schema()
    assert s["available"] is False
    assert s["implemented"] is False
    assert "single_channel_conductance" in s["required_inputs"]
    with pytest.raises(mf.BlockedParameterError):
        model.dalpha7.conductance()
    # No property of the interface yields a number that could pass for a value.
    assert not hasattr(model.dalpha7, "conductance_nS")
    assert not hasattr(model.dalpha7, "value")


# --- 6. missing synaptic conductance --------------------------------------

def test_synaptic_conductance_has_no_default():
    model = mf.build_model()
    assert model.synapse.has_biological_conductance() is False
    with pytest.raises(mf.BlockedParameterError) as e:
        model.synapse.conductance()
    assert "PSI->MN5 synaptic conductance" in str(e.value)


def test_synaptic_interface_declares_no_default_value_attribute():
    model = mf.build_model()
    for banned in ("g_syn", "g_syn_us", "default_conductance", "PEAK_G_SYN"):
        assert not hasattr(model.synapse, banned)


def test_missing_parameter_cannot_be_invented():
    ps = mf.ParameterSet()
    with pytest.raises(KeyError):
        ps.require("nothing like this was ever supplied")


# --- 7. unresolved conflicts rejected --------------------------------------

def test_conflicted_mn5_capacitance_cannot_be_selected_silently():
    """A contested value is reachable only by naming the exact variant."""
    model = mf.build_model()
    names = ("MN5 whole-cell capacitance (variant A)",
             "MN5 whole-cell capacitance (variant B)")
    for name in names:
        p = model.params.get(name)
        assert p.status is mf.ParameterStatus.ASSUMPTION, name
        assert p.conflict_id == "C-01", name
        # require_uncontested refuses: no model can quietly settle C-01.
        with pytest.raises(mf.BlockedParameterError) as e:
            model.params.require_uncontested(name)
        assert "CONTESTED" in str(e.value)
        assert "C-01" in str(e.value)
        # require() still works, but only by naming this exact variant.
        assert isinstance(model.params.require(name), float)
    # And the reduced passive model does not use it at all.
    assert not any("capacitance" in n for n in model.passive.inputs)


def test_conflicted_parameters_are_reportable():
    model = mf.build_model()
    conflicts = model.params.conflicted_parameters()
    assert "C-01" in conflicts
    assert any("capacitance (variant B)" in n
               for n in conflicts["C-01"])


def test_conflicted_gap_junction_and_chemical_rows_are_not_usable():
    model = mf.build_model()
    for name in ("GF gap-junction conductance (as executed)",
                 "ModelDB chemical peak conductance (as executed)"):
        p = model.params.get(name)
        assert p.status is mf.ParameterStatus.BLOCKED, name
        with pytest.raises(mf.BlockedParameterError):
            model.params.require(name)
        assert p.recorded_value is True


def test_blocked_spatial_and_dalpha7_rows_stay_blocked():
    model = mf.build_model()
    for name in ("MN5 length constant", "MN5 transfer resistance",
                 "MN5 electrotonic distance contact->soma",
                 "Dalpha7 channel conductance"):
        p = model.params.get(name)
        assert p.status is mf.ParameterStatus.BLOCKED, name
        assert p.value is None, name
        with pytest.raises(mf.BlockedParameterError):
            model.params.require(name)


# --- 8. provenance reporting -----------------------------------------------

def test_provenance_summary_reports_all_five_classes():
    model = mf.build_model()
    s = model.params.provenance_summary()
    assert set(s["by_provenance"]) <= {p.value for p in mf.ModelProvenance}
    for k in ("experimental", "anatomical", "literature_derived",
              "assumptions", "model_derived", "blocked", "safe",
              "assumptions_used"):
        assert k in s
    assert s["total"] > 50
    assert s["blocked"] > 0


def test_bridge_refuses_to_guess_ambiguous_provenance():
    for internal in (ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
                     ParameterProvenance.BORROWED_CROSS_CONTEXT,
                     ParameterProvenance.FITTED_CALIBRATED,
                     ParameterProvenance.ESTIMATED):
        with pytest.raises(mf.UnmappableProvenanceError) as e:
            mf.bridge_provenance(internal)
        assert "explicitly" in str(e.value)


def test_bridge_maps_unambiguous_provenance():
    assert mf.bridge_provenance(
        ParameterProvenance.DIRECTLY_MEASURED) is \
        mf.ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT
    assert mf.bridge_provenance(
        ParameterProvenance.CONNECTOME_DERIVED) is \
        mf.ModelProvenance.ANATOMICAL_MEASUREMENT
    # An explicit declaration always wins.
    assert mf.bridge_provenance(
        ParameterProvenance.ESTIMATED,
        mf.ModelProvenance.LITERATURE_DERIVED_PASSIVE_PARAMETER) is \
        mf.ModelProvenance.LITERATURE_DERIVED_PASSIVE_PARAMETER


def test_bridge_rejects_a_bad_declaration():
    with pytest.raises(TypeError):
        mf.bridge_provenance(ParameterProvenance.ESTIMATED, "literature")


# --- 9. anatomy / contact metadata -----------------------------------------

def test_frozen_anatomy_metadata_loads():
    model = mf.build_model()
    a = model.anatomy
    assert (a.mn5_left, a.mn5_right) == (801970, 801295)
    assert (a.psi_left, a.psi_right) == (802401, 903327)
    assert a.contacts_left == 17
    assert a.contacts_right == 26
    s = a.contact_summary()
    assert s["total_contacts"] == 43
    assert s["compartment_post"] == {"801970": {"axon": 17},
                                     "801295": {"axon": 26}}
    assert s["provenance"] == "anatomical_measurement"
    assert "not a voltage" in s["note"]


def test_anatomy_carries_no_electrical_value():
    model = mf.build_model()
    a = model.anatomy
    for banned in ("g_syn", "g_Da7", "Ra", "Cm", "conductance"):
        assert not hasattr(a, banned)


# --- 10. no biological placeholder defaults -------------------------------

def test_framework_declares_no_default_biological_value():
    """Nothing in the framework may ship a biological constant."""
    src = open(mf.__file__, encoding="utf-8").read()
    # No module-level numeric defaults on parameter-bearing names.
    for banned in ("G_SYN =", "G_DA7 =", "RA_DEFAULT", "RM_DEFAULT",
                   "CM_DEFAULT", "E_SYN =", "G_GAP ="):
        assert banned not in src, f"{banned} looks like a default constant"
    # The interfaces expose no module-level numeric default constants.
    model = mf.build_model()
    for obj in (model.passive, model.synapse, model.coupling, model.dalpha7):
        public = [a for a in dir(obj) if not a.startswith("_")]
        assert public, type(obj).__name__
        assert not any("DEFAULT" in a.upper() for a in public)
        assert not any(a.startswith("G_") for a in public)


def test_fixture_marker_is_used_in_every_test_parameter():
    p = _mk("fixture_x", 1.0, mf.ParameterStatus.SAFE)
    assert FIXTURE in p.source
    assert "NOT A BIOLOGICAL VALUE" in p.source


def test_every_frozen_parameter_has_a_source_and_object():
    model = mf.build_model()
    for name in ("MN5 resting potential", "MN5 spike threshold",
                 "Dalpha7 channel conductance"):
        p = model.params.get(name)
        assert p.source.strip(), name
        assert p.object.strip(), name
        assert p.unit.strip(), name


# --- 11. capability report -------------------------------------------------

def test_capability_report_matches_the_frozen_position():
    model = mf.build_model()
    caps = model.capabilities()
    assert caps["anatomy"] is mf.Capability.AVAILABLE
    assert caps["reduced_passive_mn5"] is mf.Capability.PARTIAL
    assert caps["psi_mn5_synaptic_physiology"] is mf.Capability.BLOCKED
    assert caps["psi_mn5_spatial_transfer"] is mf.Capability.BLOCKED
    assert caps["dalpha7_receptor_conductance"] is mf.Capability.BLOCKED
    assert caps["gfs_electrical_coupling"] is mf.Capability.PARTIAL
    notes = model.capability_notes()
    assert set(notes) == set(caps)
    assert "Ra and Rm are BLOCKED" in model.passive.summary()["why_not_cable"]


def test_passive_model_uses_only_safe_inputs():
    model = mf.build_model()
    for name, value in model.passive.inputs.items():
        p = model.params.get(name)
        assert p.status is mf.ParameterStatus.SAFE, name
        assert p.provenance is mf.ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT
        assert isinstance(value, float)
    assert model.passive.summary()["is_cable_model"] is False


def test_coupling_interface_has_no_native_conductance():
    model = mf.build_model()
    assert model.coupling.native_conductance_available() is False
    with pytest.raises(mf.BlockedParameterError):
        model.coupling.coupling_coefficient()
    rep = model.coupling.interface_report()
    assert rep["mn1_mn5_coupling_coefficient_available"] is False
    assert "1000x" in rep["note"]


# --- 12. regression against the frozen inventory ---------------------------

def test_framework_status_counts_match_the_frozen_csv():
    model = mf.build_model()
    with open(FREEZE_CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    want = {"SAFE": 0, "ASSUMPTION": 0, "BLOCKED": 0}
    for r in rows:
        if r["blocked"] == "yes":
            want["BLOCKED"] += 1
        elif r["assumption_only"] == "yes":
            want["ASSUMPTION"] += 1
        else:
            want["SAFE"] += 1
    got = model.params.provenance_summary()["by_status"]
    assert got["SAFE"] == want["SAFE"]
    assert got["ASSUMPTION"] == want["ASSUMPTION"]
    assert got["BLOCKED"] == want["BLOCKED"]
    assert want == {"SAFE": 40, "ASSUMPTION": 31, "BLOCKED": 37}


def test_missing_freeze_file_fails_loudly(tmp_path):
    missing = str(tmp_path / "nope.csv")
    with pytest.raises(FileNotFoundError) as e:
        mf.load_frozen_parameters(missing)
    assert "build_model_input_freeze.py" in str(e.value)


def test_number_parser_handles_uncertainty_and_categories():
    assert mf._parse_number("-67.8 +/- 5.5 SD (n=13)") == -67.8
    assert mf._parse_number("43 +/- 2 (n=22)") == 43.0
    assert mf._parse_number("~100") == 100.0
    assert mf._parse_number("NONE") is None
    assert mf._parse_number("NOT REPORTED") is None
    assert mf._parse_number("axon") is None
    assert mf._parse_number("") is None
    assert mf._parse_number("18725.6 (801970) / 19665.4 (801295)") == 18725.6


def test_report_declares_the_non_inference_principle():
    model = mf.build_model()
    assert "does not infer biological parameters" in \
        model.report()["non_inference"]
