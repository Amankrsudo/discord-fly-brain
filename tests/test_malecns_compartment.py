"""Tests for the official MaleCNS compartment_post integration (3.0D-8V).

Scope guard: this module carries a DATASET ANNOTATION only. Tests assert that
the official label is preserved verbatim, that nothing is inferred from SWC kind,
PDMN/WTct, proximity or morphology, and that unmatched contacts raise rather
than receiving a label.

Synthetic tests use a fake reader so the mapping/validation/failure logic is
tested without network access. Real tests query the official MaleCNS layer.
"""
import os
import tempfile

import pytest

from biological_brain import malecns_compartment as mc
from biological_brain import malecns_ingest as mi

SYN = os.path.join(tempfile.gettempdir(),
                   "syn-partners-male-cns-v1.0-minconf-0.5.feather")


# --- synthetic: official enum handling ---------------------------------------

def test_official_enum_is_preserved_verbatim():
    assert mc.COMPARTMENT_ENUM_LABELS == (
        "unknown", "axon", "dendrite", "linker", "cell-body-fiber")


def test_unexpected_enum_is_refused():
    info = {"properties": [{"id": "compartment_post",
                            "enum_labels": ["unknown", "axon", "dendrite"]}]}
    with pytest.raises(mc.CompartmentRetrievalError):
        mc.official_compartment_enum(info)


def test_missing_property_is_refused():
    info = {"properties": [{"id": "body_post_u32", "type": "uint32"}]}
    with pytest.raises(mc.CompartmentRetrievalError):
        mc.official_compartment_enum(info)


def test_verified_pairings_are_exactly_the_two_psi_mn5_pairs():
    assert mc.VERIFIED_PAIRINGS == {
        mi.MN5_LEFT: mi.PSI_LEFT, mi.MN5_RIGHT: mi.PSI_RIGHT}
    assert mc.VERIFIED_PAIRINGS[mi.MN5_LEFT] != mc.VERIFIED_PAIRINGS[mi.MN5_RIGHT]


def test_unknown_body_is_refused():
    with pytest.raises(mc.CompartmentRetrievalError):
        mc.retrieve_post_compartments([], mi.PSI_LEFT, 123456)


def test_cross_pairing_is_refused():
    with pytest.raises(mc.CompartmentRetrievalError):
        mc.retrieve_post_compartments([], mi.PSI_RIGHT, mi.MN5_LEFT)
    with pytest.raises(mc.CompartmentRetrievalError):
        mc.retrieve_post_compartments([], mi.PSI_LEFT, mi.MN5_RIGHT)


# --- synthetic: fake reader mapping and failure modes ------------------------

class _FakeResult:
    def __init__(self, geometry, properties):
        self.geometry = geometry
        self.properties = properties


class _FakeReader:
    """Minimal stand-in exposing only get_by_relationship."""

    def __init__(self, rows):
        # rows: list of (pre, post, cp, cpre, conf_pre, conf_post, pt2)
        self.rows = rows

    def get_by_relationship(self, relationship, value):
        assert relationship == mc.COMPARTMENT_RELATIONSHIP
        sel = [r for r in self.rows if r[1] == value]
        geometry = [[0.0, 0.0, 0.0, float(r[6][0]), float(r[6][1]),
                     float(r[6][2])] for r in sel]
        props = {
            "body_pre_u32": [r[0] for r in sel],
            "body_post_u32": [r[1] for r in sel],
            "compartment_post": [r[2] for r in sel],
            "compartment_pre": [r[3] for r in sel],
            "conf_pre": [r[4] for r in sel],
            "conf_post": [r[5] for r in sel],
        }
        return _FakeResult(geometry, props)


class _FakeContact:
    def __init__(self, raw, pre, post, region="PDMN(R)"):
        self.pre_body = pre
        self.post_body = post
        self.post_xyz = raw
        self.primary_post = region


def _contacts(post, pre, xs):
    return [_FakeContact((x, 1, 2), pre, post) for x in xs]


def test_mapping_preserves_the_official_label_string(monkeypatch):
    rows = [(802401, 801970, 1, 1, 0.8, 0.9, (10, 1, 2)),
            (802401, 801970, 2, 1, 0.7, 0.9, (20, 1, 2))]
    reader = _FakeReader(rows)
    monkeypatch.setattr(mc, "_fetch_info", lambda *a, **k: {
        "properties": [{"id": "compartment_post",
                        "enum_labels": list(mc.COMPARTMENT_ENUM_LABELS)}]})
    anns, _ = mc.retrieve_post_compartments(
        _contacts(801970, 802401, [10, 20]), 802401, 801970, reader=reader)
    assert [a.compartment_post for a in anns] == ["axon", "dendrite"]
    assert all(a.enum_labels == mc.COMPARTMENT_ENUM_LABELS for a in anns)
    assert anns[0].provenance().evidence is mi.EvidenceClass.ANATOMICAL_MEASUREMENT


def test_unmatched_contact_raises_rather_than_being_labelled(monkeypatch):
    rows = [(802401, 801970, 1, 1, 0.8, 0.9, (10, 1, 2))]
    reader = _FakeReader(rows)
    monkeypatch.setattr(mc, "_fetch_info", lambda *a, **k: {
        "properties": [{"id": "compartment_post",
                        "enum_labels": list(mc.COMPARTMENT_ENUM_LABELS)}]})
    with pytest.raises(mc.CompartmentRetrievalError):
        mc.retrieve_post_compartments(
            _contacts(801970, 802401, [10, 999]), 802401, 801970, reader=reader)


def test_ambiguous_coordinate_match_raises(monkeypatch):
    rows = [(802401, 801970, 1, 1, 0.8, 0.9, (10, 1, 2)),
            (802401, 801970, 2, 1, 0.7, 0.9, (10, 1, 2))]
    reader = _FakeReader(rows)
    monkeypatch.setattr(mc, "_fetch_info", lambda *a, **k: {
        "properties": [{"id": "compartment_post",
                        "enum_labels": list(mc.COMPARTMENT_ENUM_LABELS)}]})
    with pytest.raises(mc.CompartmentRetrievalError):
        mc.retrieve_post_compartments(
            _contacts(801970, 802401, [10]), 802401, 801970, reader=reader)


def test_wrong_presynaptic_body_is_not_picked_up(monkeypatch):
    rows = [(802401, 801970, 1, 1, 0.8, 0.9, (10, 1, 2))]
    reader = _FakeReader(rows)
    monkeypatch.setattr(mc, "_fetch_info", lambda *a, **k: {
        "properties": [{"id": "compartment_post",
                        "enum_labels": list(mc.COMPARTMENT_ENUM_LABELS)}]})
    # Only the 903327->801295 pairing is asked for, and the fake has none.
    with pytest.raises(mc.CompartmentRetrievalError):
        mc.retrieve_post_compartments(
            _contacts(801295, 903327, [10]), 903327, 801295, reader=reader)


def test_summary_counts_labels_without_interpreting(monkeypatch):
    rows = [(802401, 801970, 1, 1, 0.8, 0.9, (10, 1, 2)),
            (802401, 801970, 2, 1, 0.7, 0.9, (20, 1, 2)),
            (802401, 801970, 0, 1, 0.6, 0.9, (30, 1, 2))]
    reader = _FakeReader(rows)
    monkeypatch.setattr(mc, "_fetch_info", lambda *a, **k: {
        "properties": [{"id": "compartment_post",
                        "enum_labels": list(mc.COMPARTMENT_ENUM_LABELS)}]})
    anns, _ = mc.retrieve_post_compartments(
        _contacts(801970, 802401, [10, 20, 30]), 802401, 801970,
        reader=reader)
    s = mc.compartment_summary(anns)
    assert s["count"] == 3
    assert s["label_counts"] == {"axon": 1, "dendrite": 1, "unknown": 1}
    assert s["unknown_count"] == 1
    assert s["missing_count"] == 0
    assert s["provenance"] == "anatomical_measurement"
    assert "NOT interpreted as axon or dendrite" in s["interpretation_guard"]


def test_module_defines_no_inference_helpers():
    """Negative control: no compartment may be derived from anything else."""
    for banned in ("compartment_from_swc_kind", "compartment_from_class",
                   "compartment_from_proximity", "infer_compartment",
                   "compartment_from_depth", "compartment_from_morphology"):
        assert not hasattr(mc, banned)
    assert "does **not** derive a compartment label from SWC" in (
        mc.__doc__ or "")


def test_provenance_note_forbids_electrophysiological_reading():
    assert "not an electrophysiological measurement" in (
        mc.COMPARTMENT_PROVENANCE_NOTE)
    assert "does not validate the SWC kind column" in (
        mc.COMPARTMENT_PROVENANCE_NOTE)


def test_frame_is_explicit():
    assert mc.verified_contact_frame_unit() == mi.COORD_UNIT_NM
    assert mi.COORD_UNIT_NM == 8.0
    assert "8 nm" in mc.__doc__


# --- real data --------------------------------------------------------------

_real = pytest.mark.skipif(
    not os.path.exists(SYN), reason="MaleCNS synapse table is not present")
_layer = pytest.mark.skipif(
    True, reason="set MALECNS_ALLOW_NETWORK_TESTS=1 to run network tests")


def _net():
    return os.environ.get("MALECNS_ALLOW_NETWORK_TESTS") == "1"


_realnet = pytest.mark.skipif(
    not _net(),
    reason="network tests opt-in via MALECNS_ALLOW_NETWORK_TESTS=1")


@_real
def test_real_contact_counts_from_the_official_table():
    left = mc.contacts_from_feather(SYN, mi.PSI_LEFT, mi.MN5_LEFT)
    right = mc.contacts_from_feather(SYN, mi.PSI_RIGHT, mi.MN5_RIGHT)
    assert len(left) == 17
    assert len(right) == 26
    assert len(left) + len(right) == 43
    assert {c.pre_body for c in left} == {mi.PSI_LEFT}
    assert {c.pre_body for c in right} == {mi.PSI_RIGHT}


@_realnet
def test_real_all_43_contacts_receive_an_official_label():
    reader, _info, shims = mc.open_annotation_layer()
    assert shims, "reader shims must be recorded"
    total = 0
    for post, pre in ((mi.MN5_LEFT, mi.PSI_LEFT),
                      (mi.MN5_RIGHT, mi.PSI_RIGHT)):
        contacts = mc.contacts_from_feather(SYN, pre, post)
        anns, _ = mc.retrieve_post_compartments(
            contacts, pre, post, reader=reader)
        assert len(anns) == len(contacts)
        for a in anns:
            assert a.compartment_post in mc.COMPARTMENT_ENUM_LABELS
            assert a.pre_body == pre and a.post_body == post
            assert a.provenance().evidence is (
                mi.EvidenceClass.ANATOMICAL_MEASUREMENT)
        total += len(anns)
    assert total == 43


@_realnet
def test_real_official_labels_for_all_43_contacts():
    reader, _info, _shims = mc.open_annotation_layer()
    seen = {}
    for post, pre in ((mi.MN5_LEFT, mi.PSI_LEFT),
                      (mi.MN5_RIGHT, mi.PSI_RIGHT)):
        contacts = mc.contacts_from_feather(SYN, pre, post)
        anns, _ = mc.retrieve_post_compartments(
            contacts, pre, post, reader=reader)
        s = mc.compartment_summary(anns)
        seen[post] = s["label_counts"]
    # Recorded expectation, retrieved 2026-10-05 from MaleCNS v1.0.
    assert seen[mi.MN5_LEFT] == {"axon": 17}
    assert seen[mi.MN5_RIGHT] == {"axon": 26}
