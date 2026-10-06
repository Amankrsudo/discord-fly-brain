"""Compare official MN5 compartment_post labels with projected SWC Type codes.

This is a descriptive annotation-concordance analysis, not a biological
compartment interpretation. It uses the existing PSI->MN5 annotation export,
official MaleCNS SWCs, and the project's centerline point-to-segment rule.

The SWCs are expected in the system temporary directory by default:
    em_801970.swc
    em_801295.swc

Run:
    python research/scripts/analyze_mn5_compartment_post_swc_type.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from biological_brain.malecns_contact_path import _point_to_segment  # noqa: E402
from biological_brain.malecns_ingest import (  # noqa: E402
    COORD_UNIT_NM,
    MN5_LEFT,
    MN5_RIGHT,
    PSI_LEFT,
    PSI_RIGHT,
    SkeletonGeometry,
)

EXPECTED_PAIRINGS = {
    MN5_LEFT: PSI_LEFT,
    MN5_RIGHT: PSI_RIGHT,
}
EXPECTED_COUNTS = {MN5_LEFT: 17, MN5_RIGHT: 26}
EXPECTED_NODE_COUNTS = {MN5_LEFT: 8520, MN5_RIGHT: 7991}
SOURCE_LAYER = (
    "gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed")
TIE_TOLERANCE_NM = 1e-9
INTERPRETATION_GUARD = (
    "SWC Type is preserved as a numeric format/annotation code. Its biological "
    "semantics are undocumented by MaleCNS. The compartment_post string is "
    "preserved as a separate official dataset annotation. Concordance does not "
    "establish biological compartment semantics, biological localization, "
    "voltage transfer, or electrical properties.")


@dataclass(frozen=True)
class PointProjection:
    status: str
    node_index: int | None
    swc_type_code: int | None
    projection_distance_nm: float | None
    segment_indices: Tuple[Tuple[int, int], ...]
    candidate_node_indices: Tuple[int, ...]
    candidate_type_codes: Tuple[int, ...]


def project_point_to_swc(
        skeleton: SkeletonGeometry,
        point_nm: Sequence[float],
        tie_tolerance_nm: float = TIE_TOLERANCE_NM,
        ) -> PointProjection:
    """Apply the existing nearest-segment rule while retaining exact ties."""
    if tie_tolerance_nm < 0:
        raise ValueError("tie_tolerance_nm must be nonnegative")
    segments = skeleton.segments()
    if not segments:
        return PointProjection(
            "UNMATCHED_NO_SEGMENTS", None, None, None, (), (), ())

    to_nm = float(skeleton.unit_nm)
    point = tuple(float(value) for value in point_nm)
    ranked = []
    for start, end in segments:
        a = (start.x * to_nm, start.y * to_nm, start.z * to_nm)
        b = (end.x * to_nm, end.y * to_nm, end.z * to_nm)
        distance, projected = _point_to_segment(point, a, b)
        ranked.append((distance, projected, start, end, a, b))

    best_distance = min(record[0] for record in ranked)
    tied = [
        record for record in ranked
        if math.isclose(record[0], best_distance, rel_tol=0.0,
                        abs_tol=tie_tolerance_nm)
    ]
    table = skeleton.by_index()
    candidate_nodes = set()
    for _, projected, start, end, a, b in tied:
        nearest = (start if math.dist(projected, a) <= math.dist(projected, b)
                   else end)
        candidate_nodes.add(nearest.index)

    ordered_candidates = tuple(sorted(candidate_nodes))
    codes = tuple(sorted({table[index].kind for index in ordered_candidates}))
    if len(tied) == 1:
        status = "MATCHED"
    elif len(ordered_candidates) == 1:
        status = "MATCHED_SEGMENT_TIE_SAME_NODE"
    else:
        status = "AMBIGUOUS_NODE"
    selected_node = ordered_candidates[0] if len(ordered_candidates) == 1 else None

    return PointProjection(
        status=status,
        node_index=selected_node,
        swc_type_code=(table[selected_node].kind
                       if selected_node is not None else None),
        projection_distance_nm=best_distance,
        segment_indices=tuple(sorted({
            (record[2].index, record[3].index) for record in tied
        })),
        candidate_node_indices=ordered_candidates,
        candidate_type_codes=codes,
    )


def _read_source_rows(path: str) -> List[Dict[str, str]]:
    required = {
        "contact_index", "pre_body", "post_body", "compartment_post",
        "post_x_raw_8nm", "post_y_raw_8nm", "post_z_raw_8nm",
        "source_layer", "relationship", "provenance",
    }
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        rows = list(reader)
    for row in rows:
        pre, post = int(row["pre_body"]), int(row["post_body"])
        if post not in EXPECTED_PAIRINGS or EXPECTED_PAIRINGS[post] != pre:
            raise ValueError(
                f"unexpected pairing {pre}->{post}; only verified PSI->MN5 "
                "pairings are in scope")
        if row["source_layer"] != SOURCE_LAYER:
            raise ValueError("annotation source is not the recorded MaleCNS v1.0 layer")
        if row["relationship"] != "body_post":
            raise ValueError("annotation relationship is not body_post")
        if row["provenance"] != "anatomical_measurement":
            raise ValueError("official annotation provenance label changed")
    counts = Counter(int(row["post_body"]) for row in rows)
    if dict(counts) != EXPECTED_COUNTS:
        raise ValueError(
            f"expected PSI->MN5 counts {EXPECTED_COUNTS}, got {dict(counts)}")
    keys = [
        (int(row["pre_body"]), int(row["post_body"]),
         int(row["contact_index"]))
        for row in rows
    ]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate source contact identity in annotation export")
    return rows


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze_rows(
        rows: Sequence[Mapping[str, str]],
        skeletons: Mapping[int, SkeletonGeometry],
        ) -> List[Dict[str, object]]:
    """Join source contact rows to a nearest SWC segment/node, without inference."""
    results = []
    for row in rows:
        pre, post = int(row["pre_body"]), int(row["post_body"])
        if EXPECTED_PAIRINGS.get(post) != pre:
            raise ValueError(f"unexpected pairing {pre}->{post}")
        skeleton = skeletons.get(post)
        if (skeleton is None or skeleton.body_id != post
                or float(skeleton.unit_nm) != COORD_UNIT_NM):
            raise ValueError(f"missing or mismatched SWC for body {post}")
        point_raw = tuple(float(row[f"post_{axis}_raw_8nm"])
                          for axis in "xyz")
        projection = project_point_to_swc(
            skeleton, tuple(value * COORD_UNIT_NM for value in point_raw))
        contact_index = int(row["contact_index"])
        results.append({
            "contact_id": f"{pre}->{post}:{contact_index}",
            "contact_index": contact_index,
            "pre_body": pre,
            "post_body": post,
            "compartment_post": row["compartment_post"],
            "post_x_raw_8nm": point_raw[0],
            "post_y_raw_8nm": point_raw[1],
            "post_z_raw_8nm": point_raw[2],
            "swc_node_index": projection.node_index,
            "swc_type_code": projection.swc_type_code,
            "projection_status": projection.status,
            "projection_distance_nm": projection.projection_distance_nm,
            "nearest_segment_node_indices": ";".join(
                f"{a}-{b}" for a, b in projection.segment_indices),
            "candidate_node_indices": ";".join(
                str(index) for index in projection.candidate_node_indices),
            "candidate_type_codes": ";".join(
                str(code) for code in projection.candidate_type_codes),
            "source_layer": row["source_layer"],
            "relationship": row["relationship"],
            "provenance": row["provenance"],
            "interpretation": (
                "Literal source annotation and SWC Type code only; no "
                "biological meaning inferred."),
        })
    return results


def render_report(
        rows: Sequence[Mapping[str, object]],
        skeleton_metadata: Mapping[int, Mapping[str, object]],
        ) -> str:
    pair_counts = Counter(int(row["post_body"]) for row in rows)
    label_type_counts = Counter(
        (str(row["compartment_post"]), row["swc_type_code"])
        for row in rows if row["swc_node_index"] is not None)
    status_counts = Counter(str(row["projection_status"]) for row in rows)
    table_rows = []
    for (label, type_code), count in sorted(label_type_counts.items()):
        table_rows.append(f"| {label} | {type_code} | {count} |")
    body_lines = []
    for body in (MN5_LEFT, MN5_RIGHT):
        subset = [row for row in rows if int(row["post_body"]) == body]
        counts = Counter(
            row["swc_type_code"] for row in subset
            if row["swc_node_index"] is not None)
        counts_text = ", ".join(
            f"code {code}: {count}" for code, count in sorted(counts.items())
        ) or "none"
        meta = skeleton_metadata[body]
        body_lines.append(
            f"| {body} | {pair_counts[body]} | "
                f"{dict(sorted(Counter(row['compartment_post'] for row in subset).items()))} | "
            f"{counts_text} | {meta['node_count']} | "
            f"`{meta['sha256']}` |")
    tie_rows = [
        row for row in rows
        if row["projection_status"] != "MATCHED"
    ]
    tie_details = (
        "\n".join(
            f"- `{row['contact_id']}`: status "
            f"`{row['projection_status']}`, node "
            f"`{row['swc_node_index']}`, candidate nodes "
            f"`{row['candidate_node_indices']}`, candidate Type codes "
            f"`{row['candidate_type_codes']}`, tied segments "
            f"`{row['nearest_segment_node_indices']}`."
            for row in tie_rows
        ) or "- None.")
    return f"""# MN5 compartment_post vs SWC Type Concordance

## 1. Objective

Describe annotation concordance between the official MaleCNS v1.0
`compartment_post` labels and the numeric SWC Type code at the projected
postsynaptic node for the 43 verified PSI→MN5 contacts. This is not a biological
compartment validation.

## 2. Data and provenance

- Official annotation export: `research/artifacts/malecns_compartment_post_psi_mn5.csv`.
- Annotation layer: `{SOURCE_LAYER}`; relationship: `body_post`.
- Contact coordinates are retained in the source's raw 8 nm coordinates and
  converted to nanometres only for geometric projection.
- Official SWCs: `em_801970.swc` and `em_801295.swc` from the MaleCNS v1.0
  `skeletons-malecns/skeletons-swc/` release.
- The composite `contact_id` preserves the source export's pair-specific
  `contact_index`; it is not represented as an independent official annotation
  UUID.

{INTERPRETATION_GUARD}

## 3. Matching/projection method

Each contact is retained with its pre/post body IDs, exact official
`compartment_post` value, source contact index, and raw postsynaptic coordinate.
The coordinate is projected to the nearest SWC segment with the same point-to-
segment calculation used by `malecns_contact_path.project_contacts_to_swc`.
The projected point is associated with the nearer segment endpoint, matching
that method's node selection rule. All segments tied within
`{TIE_TOLERANCE_NM:g} nm` are retained. A tie is flagged even when the endpoint
node is the same. No maximum-distance cutoff is imposed; geometric offsets are
reported rather than silently filtered.

## 4. PSI→MN5 concordance

| MN5 body | Contacts | Official label counts | Projected SWC Type-code counts | SWC nodes | SWC SHA-256 |
|---:|---:|---|---|---:|---|
{os.linesep.join(body_lines)}

Overall contingency table (matched nodes only):

| `compartment_post` literal | SWC Type code | Contacts |
|---|---:|---:|
{os.linesep.join(table_rows)}

## 5. Comparison contacts

No additional MN5 input contacts are included. The locally available official
annotation export contains only the 43 verified PSI→MN5 pairings. Although the
official layer supports a broader `body_post` relationship, the corresponding
per-contact records were not available in the local export for this analysis;
no alternative source was substituted.

## 6. Unmatched/ambiguous records

- Total PSI→MN5 contacts: {len(rows)}.
- Matched to one projected node: {sum(row['swc_node_index'] is not None for row in rows)}.
- Unmatched: {status_counts.get('UNMATCHED_NO_SEGMENTS', 0)}.
- Nearest-segment ties: {sum(row['projection_status'] != 'MATCHED' for row in rows)}.
- Candidate-node ambiguities: {status_counts.get('AMBIGUOUS_NODE', 0)}.
- Projection statuses: `{dict(sorted(status_counts.items()))}`.

Tie details:
{tie_details}

Every contact is retained in the CSV, including flagged ties and any unmatched
case. The projection distance is the geometric distance to the reconstructed
centerline, not an electrical or physiological distance.

## 7. Interpretation

The table reports annotation concordance only: it places each literal
`compartment_post` annotation alongside the numeric SWC Type code selected by a
stated geometric projection rule. No biological interpretation is assigned to
either field.

## 8. Limitations

- SWC Type semantics are undocumented by MaleCNS.
- Concordance does not establish biological compartment semantics.
- Projection uncertainty remains; nearest-segment ties and geometric offsets
  are explicitly recorded.
- This does not establish voltage-transfer properties.
- This does not reopen the MN5 spatial-transfer gate.

## 9. Gate status

PSI→MN5 spatial voltage transfer: **NOT AUTHORIZED**

Dα7 biological conductance: **NOT AUTHORIZED**
"""


def run_analysis(
        annotations_csv: str,
        swc_dir: str,
        output_csv: str,
        output_md: str,
        ) -> List[Dict[str, object]]:
    source_rows = _read_source_rows(annotations_csv)
    skeletons: Dict[int, SkeletonGeometry] = {}
    metadata: Dict[int, Dict[str, object]] = {}
    for body in (MN5_LEFT, MN5_RIGHT):
        swc_path = os.path.join(swc_dir, f"em_{body}.swc")
        if not os.path.isfile(swc_path):
            raise FileNotFoundError(f"official SWC not found: {swc_path}")
        skeleton = SkeletonGeometry.from_swc(swc_path, body)
        if len(skeleton.nodes) != EXPECTED_NODE_COUNTS[body]:
            raise ValueError(
                f"{swc_path}: expected {EXPECTED_NODE_COUNTS[body]} nodes, "
                f"found {len(skeleton.nodes)}")
        skeletons[body] = skeleton
        metadata[body] = {
            "node_count": len(skeleton.nodes),
            "sha256": _sha256(swc_path),
        }

    results = analyze_rows(source_rows, skeletons)
    fieldnames = list(results[0])
    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    with open(output_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    report = render_report(results, metadata)
    with open(output_md, "w", encoding="utf-8", newline="") as handle:
        handle.write(report)
    return results


def main() -> int:
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--annotations-csv",
        default=os.path.join(root, "research", "artifacts",
                             "malecns_compartment_post_psi_mn5.csv"))
    parser.add_argument("--swc-dir", default=tempfile.gettempdir())
    parser.add_argument(
        "--output-csv",
        default=os.path.join(root, "research",
                             "mn5_compartment_post_swc_type_concordance.csv"))
    parser.add_argument(
        "--output-md",
        default=os.path.join(root, "research",
                             "mn5_compartment_post_swc_type_concordance.md"))
    args = parser.parse_args()
    results = run_analysis(
        args.annotations_csv, args.swc_dir, args.output_csv, args.output_md)
    print(f"analyzed {len(results)} PSI->MN5 contacts")
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
