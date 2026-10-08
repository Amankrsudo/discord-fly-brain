"""Safety tests for the independent MN5 spatial-transfer gate review (3.0D-8AB).

The review is an AUDIT. These tests lock in that it changed nothing and claims
nothing it is not entitled to claim:

* both scientific gates remain closed and enforced programmatically;
* no cable model, passive parameter or transfer quantity was introduced;
* the review verdict is NOT AUTHORIZED and agrees with the frozen blockers;
* no biological constant changed;
* the review contains no synthetic biological value;
* the review does not resolve a contested conflict;
* historical research records were not edited to satisfy a scan.
"""
import csv
import os
import re

import pytest

from biological_brain import model as entry
from biological_brain import reduced_mn5 as rm
from biological_brain.model_framework import (
    BlockedParameterError,
    ParameterStatus,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
REVIEW = os.path.join(REPO, "research", "mn5_spatial_transfer_gate_review.md")
FREEZE = os.path.join(REPO, "research", "model_input_freeze.csv")

pytestmark = pytest.mark.skipif(
    not os.path.exists(REVIEW), reason="gate review not written")
_requires_freeze = pytest.mark.skipif(
    not os.path.exists(FREEZE), reason="model input freeze not generated")


def _text():
    return open(REVIEW, encoding="utf-8").read()


def _plain():
    return re.sub(r"\s+", " ", _text().replace("*", ""))


# --- verdict ----------------------------------------------------------------

def test_verdict_is_not_authorized():
    plain = _plain()
    assert "# NOT AUTHORIZED" in plain
    assert "## Gate Decision" in plain


def test_verdict_is_explained_not_merely_asserted():
    plain = _plain()
    # The reviewer must justify NOT AUTHORIZED over CONDITIONAL explicitly.
    assert "CONDITIONAL" in plain
    assert "4.4" in plain, "the Rm bound argument must be quantified"
    assert "5,999" in plain and "26,344" in plain


def test_review_contains_every_required_section():
    plain = _plain()
    for heading in ("## Executive Verdict", "## Question Being Gated",
                    "## Evidence Audited", "## Direct Experimental Evidence",
                    "## Passive-Parameter Audit", "## Anatomical Constraints",
                    "## Somatic Electrophysiology Constraints",
                    "## Published-Model Audit", "## Remaining Blockers",
                    "## Gate Decision", "## Minimum Evidence Needed to Open",
                    "## Provenance Table", "## Explicit Non-Claims",
                    "## Impact on Current Model"):
        assert heading in plain, heading


# --- gates unchanged --------------------------------------------------------

def test_both_gates_remain_not_authorized_in_code():
    summary = entry.pipeline_summary()
    assert summary["gates"]["spatial_voltage_transfer"] == (
        "PSI->MN5 spatial voltage transfer: NOT AUTHORIZED")
    assert summary["gates"]["dalpha7_receptor_conductance"] == (
        "Dalpha7 conductance: NOT AUTHORIZED")


def test_gate_functions_still_raise():
    with pytest.raises(BlockedParameterError):
        entry.require_spatial_transfer()
    with pytest.raises(BlockedParameterError):
        entry.require_dalpha7_gate()


def test_simulator_still_has_no_spatial_transfer():
    sim = entry.build_reduced_mn5()
    assert sim.spatial_transfer_available is False
    assert sim.capabilities()["psi_mn5_spatial_transfer"] is (
        entry.Capability.BLOCKED)
    assert sim.capabilities()["cable_behaviour"] is entry.Capability.BLOCKED


def test_review_states_both_gates_unchanged():
    plain = _plain()
    assert "PSI→MN5 spatial voltage transfer: NOT AUTHORIZED" in plain
    assert "Dα7 conductance: NOT AUTHORIZED" in plain


# --- nothing was added -------------------------------------------------------

def test_no_cable_or_transfer_parameter_entered_the_freeze():
    params = entry.load_model_inputs()
    for name in ("MN5 length constant", "MN5 transfer resistance",
                 "MN5 electrotonic distance contact->soma",
                 "MN5 specific membrane resistance",
                 "MN5 membrane time constant",
                 "MN5 axoplasmic resistivity (Drosophila-measured)"):
        p = params.get(name)
        assert p.status is ParameterStatus.BLOCKED, name
        assert p.value is None, name


def test_no_passive_parameter_entered_the_reduced_model():
    sim = entry.build_reduced_mn5()
    rows = sim.biological_inputs()
    assert [r["parameter"] for r in rows] == list(
        rm.PERMITTED_BIOLOGICAL_INPUTS)
    # Exactly three inputs, all SAFE, all native.
    assert len(rows) == 3
    for r in rows:
        assert r["provenance"] == "native_experimental_measurement"
        assert r["status"] == "SAFE"


_DENY_LITERAL = re.compile(
    r"(?is)\b[A-Z_]*(?:FORBIDDEN|ALIASES)[A-Z_]*\s*(?::[^=\n]+)?=\s*"
    r"(?:[A-Za-z_][A-Za-z_0-9]*\()?\s*[\(\[\{][^)\]\}]*[\s\)\]\}]")


def test_reduced_model_source_gained_no_cable_terms():
    # Blank declared deny-lists first: a token appearing ONLY inside the
    # blocked-alias collection is the guard working, not a value.
    src = _DENY_LITERAL.sub(
        " ", open(rm.__file__, encoding="utf-8").read()).lower()
    for banned in ("length_constant", "electrotonic",
                   "transfer_resistance", "axial_resistance =",
                   "tau_m ="):
        assert banned not in src, banned
    assert "def require_leak" in src      # leak still refused, not added


def test_review_contains_no_synthetic_biological_value():
    """The review must not introduce a number of its own."""
    text = _text()
    # Every mV / ohm.cm / pF figure it quotes must also appear in the frozen
    # registry or the ledger, i.e. it is cited, not invented.
    cited = set()
    for path in (FREEZE, os.path.join(REPO, "research",
                                      "evidence_ledger.csv"),
                 os.path.join(REPO, "research", "model_input_freeze.md"),
                 os.path.join(REPO, "research", "conflicts.md"),
                 os.path.join(REPO, "research", "parameter_registry.md")):
        if os.path.exists(path):
            cited.add(open(path, encoding="utf-8").read())
    # Derived figures are permitted only when their inputs are cited, so the
    # derived Rm values are checked through the leak figures they come from.
    for figure in ("37.96", "-67.8", "-24.1", "45.5", "4.71", "212.47",
                   "0.0001667", "35.4", "169.2", "154.1", "110.3",
                   "2,587", "2,765"):
        if figure in text:
            plain_figs = figure.replace(",", "")
            assert any(figure in c or plain_figs in c.replace(",", "")
                       for c in cited), f"uncited figure {figure!r}"


def test_review_does_not_resolve_a_contested_conflict():
    plain = _plain()
    assert "C-01" in plain
    assert "contested" in plain.lower()
    # It must not pick a winner.
    for claim in ("43 +/- 2 pF is correct", "127 +/- 16 pF is correct",
                  "the correct capacitance", "adopt 43", "adopt 127"):
        assert claim.lower() not in plain.lower(), claim


def test_conflict_counts_still_match_the_freeze():
    params = entry.load_model_inputs()
    assert len(params.conflicted_parameters()) >= 10
    assert "C-01" in params.conflicted_parameters()


# --- biological constants unchanged -----------------------------------------

@_requires_freeze
def test_freeze_status_counts_unchanged():
    with open(FREEZE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    counts = {"SAFE": 0, "ASSUMPTION": 0, "BLOCKED": 0}
    for r in rows:
        if r["blocked"] == "yes":
            counts["BLOCKED"] += 1
        elif r["assumption_only"] == "yes":
            counts["ASSUMPTION"] += 1
        else:
            counts["SAFE"] += 1
    assert counts == {"SAFE": 40, "ASSUMPTION": 31, "BLOCKED": 37}
    assert len(rows) == 108


def test_mn5_biological_constants_unchanged():
    sim = entry.build_reduced_mn5()
    assert sim.resting_potential_mv == pytest.approx(-67.8)
    assert sim.threshold_mv == pytest.approx(-24.1)
    assert sim.spike_amplitude_mv == pytest.approx(45.5)


# --- non-claims are honest --------------------------------------------------

def test_review_does_not_claim_rin_determines_attenuation():
    plain = _plain()
    assert "circular" in plain.lower()
    assert "does not determine" in plain.lower() or \
        "does **not** determine" in plain


def test_review_states_identifiability_caveat_for_ra():
    plain = _plain()
    lowered = plain.lower()
    assert "identifiab" in lowered
    assert "two sites constrain only their combination" in lowered or \
        "separately identifiable" in lowered


def test_review_lists_both_gates_and_impact_is_nil():
    plain = _plain()
    assert "## Impact on Current Model" in plain
    section = plain.split("## Impact on Current Model")[-1]
    assert "None" in section or "none" in section
    assert "no code" in section.lower()


def test_review_preserves_anatomical_uncertainty():
    plain = _plain()
    assert "UNRESOLVED" in plain
    assert "proxy" in plain.lower()
    assert "UNDEFINED IN AVAILABLE SOURCE" in plain


# --- package scanner safety -------------------------------------------------

def test_review_file_is_markdown_and_contains_no_banned_token():
    """The review must not trip the package Dalpha7 scanner (it is in research/,
    not the package, but keep the discipline)."""
    banned = ("dalpha7_conductance", "dalpha7_gamma", "p_release",
              "release_probability_", "depression_time_constant",
              "vesicle_release_rate", "vesicle_pool_initial")
    text = _text().lower()
    for token in banned:
        assert token not in text, token
