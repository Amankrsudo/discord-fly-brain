"""Focused tests for the MaleCNS anatomical/provenance infrastructure.

These test the INFRASTRUCTURE only. They assert no electrical quantity, and
they do not require the large source files to be present: tests needing them
skip cleanly when the data is absent.
"""

import math
import os
import sys
import tempfile

import pytest

from biological_brain import malecns_ingest as mi
from malecns_real_data import real_contacts


# --- synthetic fixtures (clearly separated from biological data) -------------
# A tiny hand-built skeleton used only to test parsing and traversal. It is NOT
# MN5 geometry and carries no biological meaning.

_FAKE_SWC = "\n".join([
    "# synthetic test skeleton - NOT biological data",
    "1 2 0 0 0 10 -1",     # root at origin (parent -1)
    "2 2 100 0 0 10 1",
    "3 2 200 0 0 10 2",
    "4 2 0 100 0 10 1",     # second branch from the root
    "5 2 100 100 0 10 4",
]) + "\n"


def _write_fake_swc(tmp_path):
    p = tmp_path / "fake.swc"
    p.write_text(_FAKE_SWC, encoding="utf-8")
    return str(p)


# --- coordinate units --------------------------------------------------------

def test_coordinate_unit_conversion_is_exactly_8_nm():
    # 1 EM unit = 8 nm = 0.008 um. This is the declared Male CNS convention.
    assert mi.COORD_UNIT_NM == 8.0
    assert mi.COORD_UNIT_UM == 0.008
    assert mi.um(1.0) == pytest.approx(0.008)
    assert mi.um(1000.0) == pytest.approx(8.0)
    assert mi.um(1000.0) == pytest.approx(1000.0 * 8 / 1000.0)


def test_unit_conversion_is_not_silently_the_mirrored_1nm_frame():
    # If someone used 1 nm units the result would be 8x smaller; the helper
    # must make that difference explicit rather than hide it.
    assert mi.um(1000.0, unit_nm=1.0) == pytest.approx(1.0)
    assert mi.um(1000.0) == pytest.approx(8.0)
    assert mi.FRAME_EM_8NM != mi.FRAME_MIRRORED_1NM


# --- body identity registry -------------------------------------------------

def test_body_identity_registry_resolves_expected_types_and_sides():
    reg = mi.BodyIdentityRegistry()
    assert len(reg) == 4
    assert reg.get(mi.MN5_LEFT).cell_type == "DLMn a, b"
    assert reg.get(mi.MN5_LEFT).soma_side == "L"
    assert reg.get(mi.MN5_LEFT).superclass == "vnc_motor"
    assert reg.get(mi.MN5_RIGHT).cell_type == "DLMn a, b"
    assert reg.get(mi.MN5_RIGHT).soma_side == "R"
    assert reg.get(mi.PSI_LEFT).cell_type == "PSI"
    assert reg.get(mi.PSI_LEFT).superclass == "vnc_efferent"
    assert reg.get(mi.PSI_RIGHT).cell_type == "PSI"
    assert reg.get(mi.PSI_RIGHT).soma_side == "R"
    assert reg.mn5_ids == (mi.MN5_LEFT, mi.MN5_RIGHT)
    assert reg.psi_ids == (mi.PSI_LEFT, mi.PSI_RIGHT)


def test_body_identity_registry_rejects_unknown_ids():
    reg = mi.BodyIdentityRegistry()
    with pytest.raises(KeyError):
        reg.get(999999999)
    assert 999999999 not in reg


def test_identities_carry_exactly_one_evidence_class():
    for q in mi.BodyIdentityRegistry().all_provenance():
        assert isinstance(q.evidence, mi.EvidenceClass)
        assert q.source and q.name


# --- contacts: structure and confidence census -------------------------------

def _mk_contact(pre=mi.PSI_LEFT, post=mi.MN5_LEFT, xyz=(100, 200, 300),
                cpre=1.0, cpost=1.0, region="PDMN(R)"):
    return mi.SynapticContact(
        pre_body=pre, post_body=post, pre_xyz=xyz, post_xyz=xyz,
        conf_pre=cpre, conf_post=cpost, primary_post=region)


def test_known_contact_set_passes_structural_validation():
    contacts = [_mk_contact(xyz=(100 + i, 200, 300)) for i in range(43)]
    report = mi.validate_contacts(
        contacts, (mi.PSI_LEFT, mi.PSI_RIGHT), (mi.MN5_LEFT, mi.MN5_RIGHT))
    assert report["total_contacts"] == 43
    assert report["distinct_pre_bodies"] == [mi.PSI_LEFT]
    assert report["distinct_post_bodies"] == [mi.MN5_LEFT]
    assert report["minconf_threshold"] == 0.5


def test_confidence_distribution_is_computed_from_data_not_prose():
    # The prior audit's prose was internally inconsistent. This builds a known
    # distribution and requires the module to derive it independently.
    confs = [1.0] * 40 + [0.9, 0.9, 0.8]
    contacts = [_mk_contact(xyz=(100 + i, 200, 300), cpost=c)
                for i, c in enumerate(confs)]
    report = mi.validate_contacts(
        contacts, (mi.PSI_LEFT,), (mi.MN5_LEFT,))
    assert report["conf_post_distribution"] == {0.8: 1, 0.9: 2, 1.0: 40}
    assert report["conf_post_min"] == 0.8
    assert report["conf_post_max"] == 1.0
    # And the counts sum to the total, which is the check the prose failed.
    assert sum(report["conf_post_distribution"].values()) == report[
        "total_contacts"]


def test_validator_detects_bad_contacts():
    pre = (mi.PSI_LEFT,)
    post = (mi.MN5_LEFT,)
    # unexpected body id
    with pytest.raises(ValueError):
        mi.validate_contacts([_mk_contact(pre=123)], pre, post)
    # duplicate
    with pytest.raises(ValueError):
        mi.validate_contacts([_mk_contact(), _mk_contact()], pre, post)
    # malformed coordinates
    bad = _mk_contact()
    bad = mi.SynapticContact(bad.pre_body, bad.post_body, (float("nan"), 1, 1),
                             bad.post_xyz, bad.conf_pre, bad.conf_post,
                             bad.primary_post)
    with pytest.raises(ValueError):
        mi.validate_contacts([bad], pre, post)
    # confidence below threshold
    with pytest.raises(ValueError):
        mi.validate_contacts([_mk_contact(cpost=0.4)], pre, post)
    # empty set
    with pytest.raises(ValueError):
        mi.validate_contacts([], pre, post)


def test_contacts_are_never_collapsed():
    contacts = [_mk_contact(xyz=(100 + i, 200, 300)) for i in range(43)]
    report = mi.validate_contacts(contacts, (mi.PSI_LEFT,), (mi.MN5_LEFT,))
    assert report["total_contacts"] == 43
    assert len({c.key() for c in contacts}) == 43


# --- frame validation -------------------------------------------------------

def test_frame_validation_passes_for_matching_frame():
    contacts = [_mk_contact(xyz=(50, 50, 50)), _mk_contact(xyz=(90, 80, 70))]
    q = mi.validate_frame(contacts, bbox_raw_units=(0, 0, 0, 100, 100, 100))
    assert isinstance(q.evidence, mi.EvidenceClass)
    assert "2/2" in q.note


def test_frame_validation_fails_for_mismatched_frame():
    contacts = [_mk_contact(xyz=(50, 50, 50))]
    # Wrong bbox -> explicit error, not a silent pass.
    with pytest.raises(mi.CoordinateFrameError):
        mi.validate_frame(contacts, bbox_raw_units=(0, 0, 0, 10, 10, 10))
    # Unknown frame -> explicit error.
    with pytest.raises(mi.CoordinateFrameError):
        mi.validate_frame(contacts, bbox_raw_units=(0, 0, 0, 100, 100, 100),
                          frame="some other space")


# --- SWC parsing and geometry ----------------------------------------------

def test_swc_parsing_is_reproducible(tmp_path):
    path = _write_fake_swc(tmp_path)
    skel = mi.SkeletonGeometry.from_swc(path, body_id=0, unit_nm=1.0)
    assert len(skel.nodes) == 5
    assert len(skel.roots) == 1
    assert skel.roots[0].index == 1
    assert len(skel.segments()) == 4
    s = skel.stats()
    assert s["node_count"] == 5
    assert s["segment_count"] == 4
    assert s["root_count"] == 1
    assert s["has_soma_node"] is False  # synthetic skeleton has none
    # 4 segments of 100 EM units each; at unit_nm=1.0 that is 400 * 1/1000 um.
    assert s["process_length_um"] == pytest.approx(0.4)


def test_swc_graph_traversal(tmp_path):
    path = _write_fake_swc(tmp_path)
    skel = mi.SkeletonGeometry.from_swc(path, body_id=0, unit_nm=1.0)
    node, dist = skel.nearest_node((200, 0, 0))
    assert node.index == 3
    chain, length = skel.path_to_root(node.index)
    assert chain[0].index == 3 and chain[-1].index == 1
    # 200 EM units with unit_nm=1.0 is 200 * 1 / 1000 = 0.2 um.
    assert length == pytest.approx(0.2)
    # traversal is reproducible
    assert skel.path_to_root(3)[1] == pytest.approx(length)


def test_swc_bbox_and_radius_stats(tmp_path):
    path = _write_fake_swc(tmp_path)
    skel = mi.SkeletonGeometry.from_swc(path, body_id=0, unit_nm=8.0)
    bb = skel.bbox_um()
    assert bb[0] == pytest.approx(0.0)
    assert bb[3] == pytest.approx(200.0 * 0.008)
    s = skel.stats()
    assert s["radius_um_min"] == pytest.approx(10.0 * 0.008)
    assert s["frame"] == mi.FRAME_EM_8NM


def test_contact_to_root_report_is_model_derived(tmp_path):
    path = _write_fake_swc(tmp_path)
    skel = mi.SkeletonGeometry.from_swc(path, body_id=0, unit_nm=1.0)
    contacts = [_mk_contact(xyz=(200, 0, 0)), _mk_contact(xyz=(0, 100, 0))]
    rep = mi.contact_to_root_report(skel, contacts)
    assert rep["contact_count"] == 2
    assert rep["_evidence"] is mi.EvidenceClass.MODEL_DERIVED_ESTIMATE
    assert rep["root_index"] == 1
    assert rep["path_um_max"] >= rep["path_um_min"]


def test_contact_to_root_requires_single_root(tmp_path):
    # Two genuinely disconnected roots (both parent -1).
    path = tmp_path / "tworoot.swc"
    path.write_text(
        "1 2 0 0 0 10 -1\n2 2 10 0 0 10 -1\n", encoding="utf-8")
    skel = mi.SkeletonGeometry.from_swc(str(path), body_id=0, unit_nm=1.0)
    assert len(skel.roots) == 2
    with pytest.raises(ValueError):
        mi.contact_to_root_report(skel, [_mk_contact()])


# --- clustering --------------------------------------------------------------

def test_clustering_report_groups_by_region_without_collapsing():
    contacts = (
        [_mk_contact(xyz=(100 + i, 200, 300), region="PDMN(R)")
         for i in range(5)]
        + [_mk_contact(post=mi.MN5_RIGHT, xyz=(400 + i, 500, 600),
                       region="PDMN(L)") for i in range(3)]
    )
    rep = mi.clustering_report(contacts)
    assert rep["contact_count"] == 8
    assert set(rep["by_primary_post"]) == {"PDMN(R)", "PDMN(L)"}
    assert rep["by_primary_post"]["PDMN(R)"]["count"] == 5
    assert rep["by_primary_post"]["PDMN(L)"]["count"] == 3
    assert "not a pathwise" in rep["note"]


# --- provenance ledger -------------------------------------------------------

def test_every_known_quantity_has_exactly_one_evidence_class():
    classes = {q.evidence for q in mi.PASSIVE_PARAMETER_CONTEXT}
    assert all(isinstance(c, mi.EvidenceClass) for c in classes)
    for q in mi.PASSIVE_PARAMETER_CONTEXT:
        assert q.name and q.source and q.units is not None
        assert isinstance(q.evidence, mi.EvidenceClass)
    # Specific expectations for the audited values.
    by_name = {q.name: q for q in mi.PASSIVE_PARAMETER_CONTEXT}
    assert (by_name["specific membrane capacitance (adopted default)"].evidence
            is mi.EvidenceClass.LITERATURE_DERIVED_PASSIVE_PARAMETER)
    assert (by_name["axial resistivity (adopted default)"].evidence
            is mi.EvidenceClass.LITERATURE_DERIVED_PASSIVE_PARAMETER)
    assert by_name["Augustin g_pas"].evidence is mi.EvidenceClass.MODEL_ASSUMPTION
    assert by_name["Augustin Cm and Ra"].evidence is mi.EvidenceClass.MODEL_ASSUMPTION


def test_provenance_quantity_requires_valid_evidence():
    with pytest.raises(ValueError):
        mi.ProvenanceQuantity(name="x", value=1, units="",
                              evidence="not an enum", source="s")


# --- biological guardrail ---------------------------------------------------

def test_biological_transfer_remains_not_authorized():
    assert mi.biological_transfer_status() == "NOT AUTHORIZED"
    with pytest.raises(mi.BiologicalTransferNotAuthorized) as exc:
        mi.require_biological_transfer_authorization()
    msg = str(exc.value)
    assert "not uniquely determinable" in msg
    assert "Ra" in msg
    assert "soma node" in msg
    assert "discrepant" in msg


def test_anatomical_utilities_need_no_passive_parameter():
    # The geometry/ingestion utilities must not require or read any passive
    # electrical parameter. We assert none of Cm/Ra/g_pas/E_pas appears as a
    # constructor or accessor on the geometry classes.
    for cls in (mi.SkeletonGeometry, mi.SynapticContact,
                 mi.MaleCNSSynapses, mi.MaleCNSCellTypes,
                 mi.BodyIdentityRegistry):
        names = dir(cls)
        for banned in ("cm", "cm_specific", "axial_resistivity", "ra_ohm",
                       "g_pas", "leak_conductance_density", "e_pas",
                       "length_constant", "lambda_um", "attenuation",
                       "electrotonic", "transfer_resistance", "g_max"):
            assert not any(n.lower() == banned for n in names), \
                (cls.__name__, banned)


def test_no_electrical_computation_is_exposed():
    # Scan the module source for forbidden computation entry points.
    import inspect
    src = inspect.getsource(mi)
    for forbidden in ("length_constant", "electrotonic", "attenuation",
                      "transfer_resistance", "voltage_transfer"):
        # allowed only inside refusal/documentation strings, never as a def
        assert ("def " + forbidden) not in src, forbidden
        assert ("= " + forbidden) not in src, forbidden


# --- optional: real source data --------------------------------------------

_SYN = os.path.join(tempfile.gettempdir(),
                    "syn-partners-male-cns-v1.0-minconf-0.5.feather")
_ANN = os.path.join(tempfile.gettempdir(),
                    "body-annotations-male-cns-v1.0-minconf-0.5.feather")


@pytest.mark.skipif(
    not os.path.exists(_SYN) or not os.path.exists(_ANN),
    reason="MaleCNS v1.0 source files are not present in this environment")
def test_real_43_contacts_validate_and_census_is_computed():
    contacts = real_contacts()
    report = mi.validate_contacts(
        contacts, (mi.PSI_LEFT, mi.PSI_RIGHT), (mi.MN5_LEFT, mi.MN5_RIGHT))
    assert report["total_contacts"] == 43
    assert sum(report["conf_post_distribution"].values()) == 43
    assert report["conf_post_min"] >= 0.5

    ann = mi.MaleCNSCellTypes(_ANN)
    mi.BodyIdentityRegistry().validate_against(ann)
    soma = ann.soma_records([mi.MN5_LEFT, mi.MN5_RIGHT])
    assert len(soma) == 2
    for q in soma:
        assert q.evidence is mi.EvidenceClass.ANATOMICAL_MEASUREMENT
        assert "LOCATION ANNOTATION ONLY" in q.note