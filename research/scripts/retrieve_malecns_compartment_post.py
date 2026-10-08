"""Retrieve official MaleCNS compartment_post for the verified PSI->MN5 contacts.

RESEARCH SCRIPT (not production biological modelling code). Writes a
machine-readable artifact to research/artifacts/.

Run:
    python research/scripts/retrieve_malecns_compartment_post.py
"""
from __future__ import annotations

import collections
import csv
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from biological_brain import malecns_compartment as mc   # noqa: E402
from biological_brain import malecns_ingest as mi        # noqa: E402

FEATHER = os.path.join(
    tempfile.gettempdir(),
    "syn-partners-male-cns-v1.0-minconf-0.5.feather")
OUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "artifacts")


def main() -> int:
    reader, info, shims = mc.open_annotation_layer()
    rows = []
    per_body = {}
    for post, pre in ((mi.MN5_LEFT, mi.PSI_LEFT),
                      (mi.MN5_RIGHT, mi.PSI_RIGHT)):
        contacts = mc.contacts_from_feather(FEATHER, pre, post)
        anns, _ = mc.retrieve_post_compartments(
            contacts, pre, post, reader=reader)
        if len(anns) != len(contacts):
            raise SystemExit(
                f"{pre}->{post}: {len(anns)} annotations for "
                f"{len(contacts)} contacts")
        cmap = {a.contact_index: a for a in anns}
        for i, c in enumerate(contacts):
            a = cmap[i]
            rows.append({
                "contact_index": i,
                "pre_body": pre,
                "post_body": post,
                "primary_post": c.primary_post,
                "contact_class": ("WTct" if str(c.primary_post).startswith("WTct")
                                  else ("PDMN" if str(c.primary_post).startswith("PDMN")
                                        else str(c.primary_post))),
                "compartment_post": a.compartment_post,
                "compartment_pre": a.compartment_pre,
                "conf_pre": round(a.conf_pre, 6),
                "conf_post": round(a.conf_post, 6),
                "post_x_raw_8nm": a.post_xyz_raw[0],
                "post_y_raw_8nm": a.post_xyz_raw[1],
                "post_z_raw_8nm": a.post_xyz_raw[2],
                "source_layer": mc.MALECNS_SYNAPSE_LAYER_GS,
                "source_https": mc.MALECNS_SYNAPSE_LAYER_HTTPS,
                "relationship": mc.COMPARTMENT_RELATIONSHIP,
                "match_rule": "exact integer equality of post-synaptic coordinate",
                "provenance": "anatomical_measurement",
                "provenance_note": "connectomic dataset annotation; "
                                   "not electrophysiological",
            })
        per_body[post] = {
            "contacts": len(contacts),
            "compartment_post": dict(collections.Counter(
                a.compartment_post for a in anns)),
            "compartment_pre": dict(collections.Counter(
                a.compartment_pre for a in anns)),
        }

    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, "malecns_compartment_post_psi_mn5.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    summary = {
        "total_contacts": len(rows),
        "retrieved": len(rows),
        "missing": 0,
        "unknown_label_count": sum(
            1 for r in rows if r["compartment_post"] == "unknown"),
        "compartment_post_overall": dict(collections.Counter(
            r["compartment_post"] for r in rows)),
        "compartment_pre_overall": dict(collections.Counter(
            r["compartment_pre"] for r in rows)),
        "by_mn5_body": {str(k): v for k, v in per_body.items()},
        "by_contact_class": {
            k: dict(collections.Counter(
                r["compartment_post"] for r in rows
                if r["contact_class"] == k))
            for k in sorted({r["contact_class"] for r in rows})},
        "by_pairing": {
            f"{r['pre_body']}->{r['post_body']}": r["compartment_post"]
            for r in rows},
        "source_layer": mc.MALECNS_SYNAPSE_LAYER_GS,
        "layer_info_type": info["@type"],
        "official_enum_labels": list(mc.COMPARTMENT_ENUM_LABELS),
        "reader_shims_applied": sorted(shims),
        "provenance": "anatomical_measurement",
        "interpretation_guard": mc.COMPARTMENT_PROVENANCE_NOTE,
    }
    json_path = os.path.join(OUT_DIR, "malecns_compartment_post_summary.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print(json.dumps(summary, indent=2)[:4000])
    print()
    print("wrote", csv_path)
    print("wrote", json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
