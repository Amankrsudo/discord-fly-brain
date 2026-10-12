"""Integration and consistency audit for the MaleCNS anatomy chain (3.0D-8V).

These tests do not re-measure anatomy. They assert that the anatomy/evidence
infrastructure is INTERNALLY CONSISTENT and PROVENANCE-CONTROLLED:

* the retrieved compartment artifact says what the ledger says;
* the markdown ledger and its derived CSV agree;
* no document asserts compartment identity from SWC kind, PDMN/WTct, proximity
  or morphology;
* no document claims a measured spatial transfer or Dalpha7 conductance;
* both scientific gates are stated as closed wherever they are recorded;
* the retracted SIZ figure appears only inside a correction record.

They read repository files only. No network, no Feather, no mesh.
"""
import csv
import json
import os
import re

import pytest

from biological_brain import malecns_compartment as mc
from biological_brain import malecns_ingest as mi

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
RESEARCH = os.path.join(REPO, "research")
ARTIFACTS = os.path.join(RESEARCH, "artifacts")
LEDGER_MD = os.path.join(RESEARCH, "evidence_ledger.md")
LEDGER_CSV = os.path.join(RESEARCH, "evidence_ledger.csv")

_BLANK = {"-", "", "—", "–", "N/A"}
_need_artifacts = pytest.mark.skipif(
    not os.path.exists(os.path.join(
        ARTIFACTS, "malecns_compartment_post_psi_mn5.csv")),
    reason="retrieved compartment artifacts are not present")
_need_ledger = pytest.mark.skipif(
    not os.path.exists(LEDGER_CSV),
    reason="evidence ledger CSV is not present")

GATE_TRANSFER = "PSI→MN5 spatial voltage transfer: NOT AUTHORIZED"
GATE_CONDUCTANCE = "Dα7 conductance: NOT AUTHORIZED"

ALL_MD = ["evidence_ledger.md", "anatomy_registry.md", "conflicts.md",
          "missing_evidence.md", "dependency_graph.md",
          "source_registry.md", "parameter_registry.md",
          "spatial_transfer_evidence.md", "da7_evidence.md",
          "final_anatomy_audit.md"]


def _read(name):
    with open(os.path.join(RESEARCH, name), encoding="utf-8") as fh:
        return fh.read()


def _plain(value):
    return value.replace("*", "").strip()


# --- artifact integrity -----------------------------------------------------

@_need_artifacts
def test_artifact_covers_exactly_the_43_verified_contacts():
    with open(os.path.join(ARTIFACTS,
                           "malecns_compartment_post_psi_mn5.csv"),
              encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 43
    assert sum(1 for r in rows if r["post_body"] == str(mi.MN5_LEFT)) == 17
    assert sum(1 for r in rows if r["post_body"] == str(mi.MN5_RIGHT)) == 26
    assert {r["pre_body"] for r in rows
            if r["post_body"] == str(mi.MN5_LEFT)} == {str(mi.PSI_LEFT)}
    assert {r["pre_body"] for r in rows
            if r["post_body"] == str(mi.MN5_RIGHT)} == {str(mi.PSI_RIGHT)}


@_need_artifacts
def test_artifact_labels_are_official_enum_strings_only():
    with open(os.path.join(ARTIFACTS,
                           "malecns_compartment_post_psi_mn5.csv"),
              encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        assert r["compartment_post"] in mc.COMPARTMENT_ENUM_LABELS
        assert r["compartment_pre"] in mc.COMPARTMENT_ENUM_LABELS
        assert r["provenance"] == "anatomical_measurement"
        assert r["source_layer"] == mc.MALECNS_SYNAPSE_LAYER_GS
        assert r["relationship"] == mc.COMPARTMENT_RELATIONSHIP


@_need_artifacts
def test_artifact_summary_agrees_with_its_own_csv():
    with open(os.path.join(ARTIFACTS,
                           "malecns_compartment_post_psi_mn5.csv"),
              encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open(os.path.join(ARTIFACTS,
                           "malecns_compartment_post_summary.json"),
              encoding="utf-8") as fh:
        s = json.load(fh)
    counts = {}
    for r in rows:
        counts[r["compartment_post"]] = counts.get(
            r["compartment_post"], 0) + 1
    assert s["compartment_post_overall"] == counts
    assert s["total_contacts"] == len(rows)
    assert s["retrieved"] == len(rows)
    assert s["missing"] == 0
    assert s["official_enum_labels"] == list(mc.COMPARTMENT_ENUM_LABELS)


# --- ledger synchronisation -------------------------------------------------

@_need_ledger
def test_csv_is_in_sync_with_the_markdown_ledger():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen", os.path.join(RESEARCH, "scripts",
                            "generate_evidence_ledger_csv.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    md_rows = mod.parse(LEDGER_MD)
    with open(LEDGER_CSV, encoding="utf-8") as fh:
        csv_rows = list(csv.reader(fh))
    assert csv_rows[0] == mod.HEADER
    assert len(csv_rows) - 1 == len(md_rows)
    for a, b in zip(csv_rows[1:], md_rows):
        assert a == b, f"ledger drift at {a[0]}"


@_need_ledger
def test_claims_a_to_e_are_present_and_correctly_classified():
    with open(LEDGER_CSV, encoding="utf-8") as fh:
        rows = {r[0]: r for r in list(csv.reader(fh))[1:]}
    for cid in ("E-046", "E-047", "E-048", "E-049", "E-050"):
        assert cid in rows, f"claim {cid} missing from the ledger"

    # CLAIM A / B: verified dataset annotations, AM, strong, direct, reproducible.
    for cid in ("E-046", "E-047"):
        assert rows[cid][7] == "AM"
        assert rows[cid][8] == "STRONG"
        assert rows[cid][9] == "D"
        assert "VERIFIED" in rows[cid][14]
    assert "dataset annotation" in rows["E-046"][15]
    assert "not an electrophysiological measurement" in (
        rows["E-046"][15] + rows["E-047"][15])

    # CLAIM C: methodological limitation, no evidence class, unresolved.
    assert rows["E-048"][7] in _BLANK
    assert _plain(rows["E-048"][8]) == "NONE"
    assert "UNRESOLVED" in rows["E-048"][14]
    assert "does not establish spatial voltage transfer" in _plain(
        rows["E-048"][1])

    # CLAIM D: SWC kind still unresolved.
    assert rows["E-049"][7] in _BLANK
    assert _plain(rows["E-049"][8]) == "NONE"
    assert "UNRESOLVED" in rows["E-049"][14]
    assert "does not retroactively validate" in _plain(rows["E-049"][15])

    # CLAIM E: resolved with an explicit scope limitation.
    assert "RESOLVED WITH SCOPE LIMITATION" in rows["E-050"][14]
    assert "unreleased" in rows["E-050"][1]


# --- contradiction sweep over the repository -------------------------------

_CONTRADICTIONS = [
    (r"PSI\s+(contacts?|synapses?)[^.]{0,80}\bare\s+dendritic\b",
     "PSI->MN5 contacts are officially labelled axon, not dendritic"),
    (r"\bPDMN\b[^.]{0,40}=\s*(the\s+)?axon\b",
     "PDMN was never established as axon"),
    (r"\bWTct\b[^.]{0,40}=\s*(the\s+)?dendrite\b",
     "WTct was never established as dendrite"),
    (r"kind\s*=\s*2\b[^.]{0,40}(is|means|denotes)\s+(the\s+)?axon",
     "SWC kind=2 biology is UNDEFINED IN AVAILABLE SOURCE"),
    (r"compartment_post\s*(=|:)\s*axon[^.]{0,60}(electrophysiolog|measured)",
     "compartment_post is a dataset annotation, not a measurement"),
]


@pytest.mark.parametrize("name", ALL_MD)
def test_no_contradictory_compartment_claims(name):
    text = _read(name)
    for pattern, why in _CONTRADICTIONS:
        hit = re.search(pattern, text, re.I)
        assert hit is None, (
            f"{name} contains a contradictory claim matching {pattern!r} "
            f"({why}): {hit.group(0)[:120]!r}")


_CORRECTION_MARKERS = ("does not exist", "does not occur", "correction",
                       "corrected", "corrupted merge", "retracted",
                       "former value", "not supported")


@pytest.mark.parametrize("name", ALL_MD)
def test_siz_wrong_value_is_never_asserted_as_current(name):
    """The retracted '88 +/- 15 um' figure may appear ONLY in a correction."""
    text = _read(name)
    for m in re.finditer(r"88\s*(?:\u00b1|\+/-)\s*15", text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        line = text[line_start:line_end if line_end != -1 else len(text)]
        low = line.lower()
        assert any(k in low for k in _CORRECTION_MARKERS), (
            f"{name}: the retracted SIZ figure 88+/-15 is asserted on a line "
            f"that is not a correction record: {line.strip()[:160]!r}")


def test_gate_vocabulary_is_consistent_across_the_chain():
    for name in ("anatomy_registry.md", "missing_evidence.md",
                 "final_anatomy_audit.md"):
        text = _read(name)
        assert GATE_TRANSFER in text, name
        assert GATE_CONDUCTANCE in text, name


def test_compartment_module_refuses_to_infer_compartment():
    for banned in ("compartment_from_swc_kind", "compartment_from_class",
                   "infer_compartment", "compartment_from_proximity",
                   "compartment_from_depth", "compartment_from_morphology"):
        assert not hasattr(mc, banned)
    assert mi.MALECNS_NODE_TYPE_BIOLOGY == "UNDEFINED IN AVAILABLE SOURCE"


@_need_ledger
def test_axon_label_is_not_promoted_to_a_measurement():
    """The retrieved label must stay AM and must not appear as an NEM claim."""
    with open(LEDGER_CSV, encoding="utf-8") as fh:
        rows = {r[0]: r for r in list(csv.reader(fh))[1:]}
    assert rows["E-046"][7] == "AM"
    assert rows["E-046"][7] != "NEM"
    assert rows["E-047"][7] == "AM"
    assert "not an electrophysiological measurement" in (
        mc.COMPARTMENT_PROVENANCE_NOTE)
