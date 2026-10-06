"""Tests for the frozen model-input inventory (3.0D-8W).

These tests enforce the SAFETY INVARIANTS of
`research/model_input_freeze.csv` / `.md`. They do not re-derive any value.

Invariants checked:
* every parameter carries exactly one of the project's five provenance classes;
* exactly one safety flag per row; bucket B is never promoted into bucket A;
* gate-blocked parameters stay blocked, and neither gate is opened;
* no synthetic biological value has been introduced (value "NONE" => blocked);
* units are explicit -- never blank, never a bare dash;
* unresolved conflicts remain unresolved (no silent winner);
* ModelDB defaults are never represented as native measurements;
* the generated markdown is in sync with the generated CSV.
"""
import csv
import importlib.util
import os
import re

import pytest

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
RESEARCH = os.path.join(REPO, "research")
FREEZE_CSV = os.path.join(RESEARCH, "model_input_freeze.csv")
FREEZE_MD = os.path.join(RESEARCH, "model_input_freeze.md")
BUILDER = os.path.join(RESEARCH, "scripts", "build_model_input_freeze.py")

NEM = "native_experimental_measurement"
AM = "anatomical_measurement"
LDP = "literature_derived_passive_parameter"
MA = "model_assumption"
MDE = "model_derived_estimate"
FIVE = {NEM, AM, LDP, MA, MDE}

GATE_TRANSFER = "spatial voltage transfer"
GATE_DA7 = "dalpha7"


def _builder():
    spec = importlib.util.spec_from_file_location("freeze_builder", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rows():
    with open(FREEZE_CSV, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


_need = pytest.mark.skipif(
    not os.path.exists(FREEZE_CSV),
    reason="model input freeze has not been generated")


@_need
def test_every_parameter_has_exactly_one_provenance_category():
    rows = _rows()
    assert len(rows) > 50
    for r in rows:
        assert r["provenance"] in FIVE, (
            f"{r['parameter']}: provenance {r['provenance']!r} is not one of "
            f"the five permitted classes")


@_need
def test_exactly_one_safety_flag_per_parameter():
    for r in _rows():
        flags = [k for k in ("safe_now", "assumption_only", "blocked")
                 if r[k] == "yes"]
        assert len(flags) == 1, (
            f"{r['parameter']}: flags {flags}, expected exactly one")
        assert r["safe_now"] != "yes" or r["blocked"] != "yes"


@_need
def test_bucket_b_is_never_promoted_into_bucket_a():
    """A parameter may not be both safe and assumption-only."""
    for r in _rows():
        assert not (r["safe_now"] == "yes" and r["assumption_only"] == "yes")
    mod = _builder()
    rows = mod._normalise_units(mod.ROWS)
    for r in rows:
        p = dict(zip(mod.COLUMNS, r))
        assert p["safe_now"] == "yes" or p["assumption_only"] == "yes" \
            or p["blocked"] == "yes"


@_need
def test_blocked_parameters_cannot_be_marked_safe():
    for r in _rows():
        if r["blocked"] == "yes":
            assert r["safe_now"] == "no", r["parameter"]
            assert r["assumption_only"] == "no", r["parameter"]


@_need
def test_units_are_explicit():
    for r in _rows():
        u = r["unit"].strip()
        assert u, f"{r['parameter']}: unit is blank"
        assert u != "-", f"{r['parameter']}: unit is a bare dash"
        # A unit may qualify its symbol ("% of GF terminal", "space
        # constants") but must stay a short unit, not prose.
        assert len(u) <= 24, f"{r['parameter']}: unit {u!r} looks like prose"
        assert u in ("dimensionless", "categorical") or re.search(
            r"[a-zA-ZµΩ%0-9]", u), (
            f"{r['parameter']}: unit {u!r} carries no unit symbol")


@_need
def test_no_synthetic_biological_value_was_introduced():
    """value NONE must always be blocked; a real value must cite a source."""
    for r in _rows():
        if r["value"].strip() == "NONE":
            assert r["blocked"] == "yes", (
                f"{r['parameter']}: value NONE but not blocked")
            assert r["notes"].strip(), r["parameter"]
        assert r["source"].strip(), r["parameter"]
        assert r["object"].strip(), r["parameter"]


@_need
def test_gate_blocked_parameters_remain_blocked():
    gates = {GATE_TRANSFER, GATE_DA7, "transfer", "dalpha7"}
    for r in _rows():
        if r["gate"] in gates and r["gate"]:
            assert r["blocked"] == "yes", (
                f"{r['parameter']} is gate-gated ({r['gate']}) but not blocked")


@_need
def test_spatial_voltage_transfer_remains_blocked():
    names = ("MN5 electrotonic distance contact->soma", "MN5 length constant",
             "MN5 transfer resistance")
    byname = {r["parameter"]: r for r in _rows()}
    for n in names:
        assert n in byname, n
        r = byname[n]
        assert r["blocked"] == "yes"
        assert r["safe_now"] == "no"
        assert r["value"] == "NONE (not computed)"


@_need
def test_dalpha7_conductance_remains_blocked():
    byname = {r["parameter"]: r for r in _rows()}
    r = byname["Dalpha7 channel conductance"]
    assert r["blocked"] == "yes"
    assert r["safe_now"] == "no"
    assert r["gate"] == GATE_DA7
    assert r["value"] == "NONE"
    # And the Kir7.1 coupling must stay blocked: the channel does not exist.
    kir = byname["Dalpha7 -> Kir7.1 coupling"]
    assert kir["blocked"] == "yes"
    assert "orthologue" in kir["notes"].lower()


@_need
def test_conflicted_mn5_capacitance_is_not_safe():
    byname = {r["parameter"]: r for r in _rows()}
    for n in ("MN5 whole-cell capacitance (variant A)",
              "MN5 whole-cell capacitance (variant B)"):
        r = byname[n]
        assert r["safe_now"] == "no", n
        assert r["assumption_only"] == "yes", n
        assert "C-01" in r["conflict"], n


@_need
def test_unresolved_conflicts_remain_unresolved():
    """No conflict may be recorded as resolved in the inventory."""
    text = open(FREEZE_MD, encoding="utf-8").read()
    for cid in ("C-01", "C-02", "C-03", "C-08", "C-10", "C-12"):
        assert cid in text, f"{cid} missing from the freeze document"
    assert "Unresolved conflicts — no winner chosen" in text
    # The two 1000x discrepancies are recorded against the right synapses.
    rows = {r["parameter"]: r for r in _rows()}
    gap = rows["GF gap-junction conductance (as executed)"]
    assert "1000x" in gap["notes"] and gap["blocked"] == "yes"
    chem = rows["ModelDB chemical peak conductance (as executed)"]
    assert "1000x" in chem["notes"] and chem["blocked"] == "yes"
    # And they must be flagged as DIFFERENT synapses, never pooled.
    assert "different synapse" in text.lower(), (
        "the 1000x pairs must be recorded as two different synapses")
    assert "must never be pooled" in text.lower()


@_need
def test_modeldb_defaults_are_not_native_measurements():
    rows = {r["parameter"]: r for r in _rows()}
    for n in ("ModelDB Ra (never assigned)", "ModelDB Cm (never assigned)"):
        r = rows[n]
        assert r["provenance"] != NEM, n
        assert r["provenance"] == MA, n
        assert "NEVER SET" in r["notes"], n
        assert r["conflict"].startswith("C-06"), n
        assert r["safe_now"] == "no", n
    # Paper-level 'estimated' values must not be NEM either.
    for n in ("GF gap-junction conductance (paper value)",
              "ModelDB chemical peak conductance (paper value)"):
        assert rows[n]["provenance"] == MA, n


@_need
def test_wrong_species_parameters_are_flagged():
    rows = {r["parameter"]: r for r in _rows()}
    r = rows["MN5 axoplasmic resistivity (value ever applied)"]
    assert "WRONG SPECIES" in r["notes"]
    assert r["provenance"] == LDP
    assert r["safe_now"] == "no"


@_need
def test_anatomy_values_are_safe_but_not_electrical():
    """Anatomy is usable; the same values must not be presented as electrical."""
    rows = {r["parameter"]: r for r in _rows()}
    r = rows["PSI->MN5 contact -> SWC-root path length"]
    assert r["safe_now"] == "yes"
    assert r["provenance"] == MDE
    assert "NOT an electrotonic distance" in r["notes"]
    c = rows["PSI->MN5 official compartment_post"]
    assert c["safe_now"] == "yes"
    assert c["provenance"] == AM
    assert "not a distance" in c["notes"].lower()


@_need
def test_generated_markdown_is_in_sync_with_the_csv():
    rows = _rows()
    text = open(FREEZE_MD, encoding="utf-8").read()
    assert "GENERATED FILE" in text
    for header, key in (("## A · SAFE TO USE NOW", "safe_now"),
                        ("## B · USABLE ONLY AS EXPLICIT MODEL ASSUMPTIONS",
                         "assumption_only"),
                        ("## C · BLOCKED / DO NOT USE", "blocked")):
        assert header in text, header
        n = sum(1 for r in rows if r[key] == "yes")
        m = re.search(re.escape(header) + r" \((\d+)\)", text)
        assert m, header
        assert int(m.group(1)) == n, f"{header}: md says {m.group(1)}, csv {n}"
    m = re.search(r"total parameters audited \| \*\*(\d+)\*\*", text)
    assert m and int(m.group(1)) == len(rows)


@_need
def test_both_gates_stated_closed_in_the_freeze_document():
    text = open(FREEZE_MD, encoding="utf-8").read()
    assert "PSI→MN5 spatial voltage transfer: NOT AUTHORIZED" in text
    assert "Dα7 conductance: NOT AUTHORIZED" in text


@_need
def test_builder_rejects_a_malformed_row():
    """The generator's own validation must still bite."""
    mod = _builder()
    bad = [("X", "x", "1", "V", "o", "s", "t", "not_a_class", "strong", "D",
            "M", "yes", "none", "yes", "no", "no", "none", "n")]
    assert mod._validate(bad), "malformed provenance must be rejected"
    bad2 = [("X", "x", "1", "V", "o", "s", "t", MA, "strong", "D", "M",
             "yes", "none", "yes", "yes", "no", "none", "n")]
    assert mod._validate(bad2), "two safety flags must be rejected"
    bad3 = [("X", "x", "NONE", "V", "o", "s", "t", MA, "strong", "D", "M",
             "yes", "none", "yes", "no", "no", "none", "n")]
    assert mod._validate(bad3), "value NONE must not be safe"
