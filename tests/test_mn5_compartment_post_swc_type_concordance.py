"""Focused tests for MN5 annotation concordance analysis.

These tests verify literal annotation handling and geometric projection only.
They do not assign biological meaning to SWC Type codes.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter

import pytest

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT_DIR = os.path.join(ROOT, "research", "scripts")
sys.path.insert(0, SCRIPT_DIR)

import analyze_mn5_compartment_post_swc_type as analysis  # noqa: E402
from biological_brain.malecns_ingest import (  # noqa: E402
    FRAME_EM_8NM,
    SkeletonGeometry,
    SwcNode,
)

ANNOTATIONS = os.path.join(
    ROOT, "research", "artifacts", "malecns_compartment_post_psi_mn5.csv")
RESULTS_CSV = os.path.join(
    ROOT, "research", "mn5_compartment_post_swc_type_concordance.csv")
RESULTS_MD = os.path.join(
    ROOT, "research", "mn5_compartment_post_swc_type_concordance.md")


def _read_rows(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _skeleton(body_id, nodes):
    return SkeletonGeometry(
        body_id=body_id, frame=FRAME_EM_8NM, unit_nm=8.0, nodes=nodes)


def test_expected_mn5_bodies_and_psi_pairings():
    assert set(analysis.EXPECTED_PAIRINGS) == {801970, 801295}
    assert analysis.EXPECTED_PAIRINGS == {
        801970: 802401,
        801295: 903327,
    }


def test_official_export_preserves_labels_and_contact_counts():
    rows = analysis._read_source_rows(ANNOTATIONS)
    assert Counter(int(row["post_body"]) for row in rows) == {
        801970: 17,
        801295: 26,
    }
    assert {row["compartment_post"] for row in rows} == {"axon"}
    assert len({(row["pre_body"], row["post_body"], row["contact_index"])
                for row in rows}) == 43


def test_contact_projects_to_nearest_node_using_segment_geometry():
    skel = _skeleton(801970, [
        SwcNode(index=1, kind=0, x=0, y=0, z=0, radius=1, parent=-1),
        SwcNode(index=2, kind=7, x=10, y=0, z=0, radius=1, parent=1),
    ])
    projected = analysis.project_point_to_swc(skel, (64.0, 16.0, 0.0))
    assert projected.status == "MATCHED"
    assert projected.node_index == 2
    assert projected.swc_type_code == 7
    assert projected.projection_distance_nm == pytest.approx(16.0)
    assert projected.segment_indices == ((1, 2),)


def test_equal_adjacent_segments_are_flagged_and_node_retained():
    skel = _skeleton(801970, [
        SwcNode(index=1, kind=0, x=0, y=0, z=0, radius=1, parent=-1),
        SwcNode(index=2, kind=4, x=10, y=0, z=0, radius=1, parent=1),
        SwcNode(index=3, kind=4, x=20, y=0, z=0, radius=1, parent=2),
    ])
    projected = analysis.project_point_to_swc(skel, (80.0, 0.0, 0.0))
    assert projected.status == "MATCHED_SEGMENT_TIE_SAME_NODE"
    assert projected.node_index == 2
    assert projected.candidate_node_indices == (2,)
    assert projected.candidate_type_codes == (4,)
    assert projected.segment_indices == ((1, 2), (2, 3))


def test_equal_disconnected_segments_are_flagged_as_node_ambiguous():
    skel = _skeleton(801970, [
        SwcNode(index=1, kind=0, x=0, y=0, z=0, radius=1, parent=-1),
        SwcNode(index=2, kind=0, x=10, y=0, z=0, radius=1, parent=1),
        SwcNode(index=3, kind=2, x=20, y=0, z=0, radius=1, parent=-1),
        SwcNode(index=4, kind=2, x=30, y=0, z=0, radius=1, parent=3),
    ])
    projected = analysis.project_point_to_swc(skel, (120.0, 0.0, 0.0))
    assert projected.status == "AMBIGUOUS_NODE"
    assert projected.node_index is None
    assert projected.swc_type_code is None
    assert projected.candidate_node_indices == (2, 3)
    assert projected.candidate_type_codes == (0, 2)


def test_no_segments_is_retained_as_unmatched():
    skel = _skeleton(801970, [
        SwcNode(index=1, kind=0, x=0, y=0, z=0, radius=1, parent=-1),
    ])
    projected = analysis.project_point_to_swc(skel, (0.0, 0.0, 0.0))
    assert projected.status == "UNMATCHED_NO_SEGMENTS"
    assert projected.node_index is None
    assert projected.swc_type_code is None


def test_report_and_csv_keep_codes_literal_and_gates_closed():
    rows = _read_rows(RESULTS_CSV)
    with open(RESULTS_MD, encoding="utf-8") as handle:
        report = handle.read()
    assert len(rows) == 43
    assert all(row["compartment_post"] == "axon" for row in rows)
    assert all(row["swc_type_code"] == "0" for row in rows)
    assert sum(row["projection_status"] == "MATCHED" for row in rows) == 42
    assert sum(
        row["projection_status"] == "MATCHED_SEGMENT_TIE_SAME_NODE"
        for row in rows) == 1
    assert "annotation concordance only" in report
    assert "SWC Type semantics are undocumented by MaleCNS" in report
    assert "concordance does not establish biological compartment semantics" in report.lower()
    assert "does not establish voltage-transfer properties" in report.lower()
    assert "PSI→MN5 spatial voltage transfer: **NOT AUTHORIZED**" in report
    assert "Dα7 biological conductance: **NOT AUTHORIZED**" in report
    assert "kind=0 = axon" not in report
    assert "proof of axonal localization" not in report


def test_source_labels_are_not_normalized_or_reinterpreted():
    rows = analysis._read_source_rows(ANNOTATIONS)
    assert all(row["compartment_post"] == "axon" for row in rows)
    skeleton = _skeleton(801970, [
        SwcNode(index=1, kind=0, x=0, y=0, z=0, radius=1, parent=-1),
        SwcNode(index=2, kind=2, x=1, y=0, z=0, radius=1, parent=1),
    ])
    analyzed = analysis.analyze_rows(
        [{
            "contact_index": "4",
            "pre_body": "802401",
            "post_body": "801970",
            "compartment_post": "axon",
            "post_x_raw_8nm": "1",
            "post_y_raw_8nm": "0",
            "post_z_raw_8nm": "0",
            "source_layer": analysis.SOURCE_LAYER,
            "relationship": "body_post",
            "provenance": "anatomical_measurement",
        }],
        {801970: skeleton},
    )
    assert analyzed[0]["compartment_post"] == "axon"
    assert analyzed[0]["swc_type_code"] == 2
    assert "no biological meaning inferred" in analyzed[0]["interpretation"]
