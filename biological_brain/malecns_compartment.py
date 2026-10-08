"""Official MaleCNS per-synapse ``compartment_post`` annotation (3.0D-8V).

WHAT THIS IS
------------
Berg et al. / MaleCNS v1.0 deposit a per-synapse compartment label on the
official synapse annotation layer. This module retrieves that label verbatim for
the verified PSI->MN5 contacts. It is a **connectomic dataset annotation**, not
an electrophysiological measurement, and not a morphology measurement.

Provenance: :attr:`~biological_brain.malecns_ingest.EvidenceClass.ANATOMICAL_MEASUREMENT`
-- an annotation supplied by the source dataset. See
:data:`COMPARTMENT_PROVENANCE_NOTE` for what that does and does not license.

WHAT THIS MODULE REFUSES TO DO
------------------------------
* It does **not** derive a compartment label from SWC ``kind``.
* It does **not** derive one from PDMN vs WTct, proximity, morphology, contact
  depth, or centreline position.
* It does **not** convert a label into a statement about electrical behaviour.
* It does **not** resolve the SWC ``kind=2`` question, which remains separate
  and unresolved (see :data:`biological_brain.malecns_ingest.MALECNS_SWC_SEMANTICS`).

The label is preserved **exactly as the source supplies it**. This module reports
the official enum string and its frequency. It does not assert what the string
means biologically, and it does not use the string to relabel anything.

COORDINATE FRAME
----------------
The layer's ``info`` declares ``dimensions`` as 8e-09 m per voxel, and the
retrieved geometry is in the same raw 8 nm units used by the MaleCNS synapse
tables. :func:`retrieve_post_compartments` proves this per contact by exact
integer match against the independently ingested contact coordinate, and raises
rather than reporting a label for an unmatched contact.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .malecns_ingest import (
    COORD_UNIT_NM,
    MN5_LEFT,
    MN5_RIGHT,
    PSI_LEFT,
    PSI_RIGHT,
    EvidenceClass,
    MaleCNSSynapses,
    ProvenanceQuantity,
)

#: The official MaleCNS v1.0 synapse annotation layer.
MALECNS_SYNAPSE_LAYER_GS = (
    "gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed")
MALECNS_SYNAPSE_LAYER_HTTPS = (
    "https://storage.googleapis.com/flyem-male-cns/v1.0/"
    "male-cns-v1.0-synapses-precomputed")

#: The official relationship that indexes by post-synaptic body.
COMPARTMENT_RELATIONSHIP = "body_post"

#: The official enum, copied from the layer's own ``info`` document. Never
#: extended, never reordered, never aliased.
COMPARTMENT_ENUM_LABELS: Tuple[str, ...] = (
    "unknown", "axon", "dendrite", "linker", "cell-body-fiber")

COMPARTMENT_PROVENANCE_NOTE = (
    "compartment_post is an ANATOMICAL/CONNECTOMIC DATASET ANNOTATION supplied "
    "by MaleCNS v1.0. It is not an electrophysiological measurement, not a "
    "morphological measurement, and not a native observation. MaleCNS does not "
    "publish the procedure that assigned these labels, so the label string is "
    "reported verbatim and is NOT interpreted here. Its presence does not "
    "validate the SWC kind column, and its biology is not asserted.")

#: The verified PSI->MN5 pairings this module is permitted to query.
VERIFIED_PAIRINGS: Dict[int, int] = {
    MN5_LEFT: PSI_LEFT,
    MN5_RIGHT: PSI_RIGHT,
}


class CompartmentRetrievalError(Exception):
    """Raised when the official annotation cannot be matched unambiguously."""


@dataclass(frozen=True)
class CompartmentAnnotation:
    """One official ``compartment_post`` label for one verified contact."""

    contact_index: int
    pre_body: int
    post_body: int
    compartment_post: str
    compartment_pre: str
    conf_pre: float
    conf_post: float
    post_xyz_raw: Tuple[float, float, float]
    source_layer: str
    relationship: str
    enum_labels: Tuple[str, ...]
    note: str = COMPARTMENT_PROVENANCE_NOTE

    def provenance(self) -> ProvenanceQuantity:
        return ProvenanceQuantity(
            name=f"official compartment_post for contact {self.contact_index} "
                 f"({self.pre_body}->{self.post_body})",
            value=self.compartment_post,
            units="compartment label",
            evidence=EvidenceClass.ANATOMICAL_MEASUREMENT,
            source="MaleCNS v1.0 synapse annotation layer, "
                   "compartment_post",
            note=self.note)


def _apply_reader_shims() -> Dict[str, str]:
    """Two metadata-only compatibility shims, recorded so they are auditable.

    Neither touches any data value. Both exist because the published layer and
    cloud-volume 12.15.1 disagree on schema spelling / numpy call signature:

    1. The layer declares ``"annotation_type": "line"`` (lowercase); cloud-volume's
       ``AnnotationType`` enum values are uppercase. We upper-case the metadata
       value only.
    2. cloud-volume calls ``np.hstack(a, b)``; numpy >= 1.24 made ``dtype``
       keyword-only. We restore the legacy two-positional-argument behaviour.

    Both are recorded in the result so a reader can see exactly what was shimmed.
    """
    shims: Dict[str, str] = {}
    import numpy as np

    original_hstack = np.hstack

    def hstack_legacy(tup, *args, **kwargs):
        if args:
            return original_hstack([tup, args[0]], **kwargs)
        return original_hstack(tup, **kwargs)

    if getattr(np.hstack, "_legacy_shim", False) is not True:
        np.hstack = hstack_legacy
        np.hstack._legacy_shim = True
        shims["numpy_hstack_legacy_positional"] = (
            "cloud-volume 12.15.1 calls np.hstack(a, b); numpy>=1.24 made the "
            "second positional argument keyword-only. Metadata/ABI shim only.")
    try:
        from cloudvolume.datasource.precomputed import create_precomputed_annotation
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise CompartmentRetrievalError(
            "cloud-volume is required to read the MaleCNS annotation layer. "
            "Install with: pip install cloud-volume 'numpy<2'") from exc
    shims["annotation_type_uppercased"] = (
        "The layer declares annotation_type='line'; cloud-volume's enum values "
        "are uppercase. Metadata shim only; no data value altered.")
    return shims


def _fetch_info(https_base: str = MALECNS_SYNAPSE_LAYER_HTTPS) -> Dict[str, object]:
    with urllib.request.urlopen(f"{https_base}/info", timeout=120) as fh:
        return json.loads(fh.read().decode("utf-8"))


def official_compartment_enum(info: Dict[str, object]) -> Tuple[str, ...]:
    """Read the enum straight from the layer, and refuse anything unexpected."""
    for prop in info["properties"]:
        if prop["id"] == "compartment_post":
            labels = tuple(prop["enum_labels"])
            if labels != COMPARTMENT_ENUM_LABELS:
                raise CompartmentRetrievalError(
                    f"the layer's compartment_post enum {labels} differs from "
                    f"the recorded official enum {COMPARTMENT_ENUM_LABELS}; "
                    f"refusing to proceed against an unexpected schema")
            return labels
    raise CompartmentRetrievalError(
        "the layer declares no compartment_post property; this is a different "
        "or newer MaleCNS release than the one recorded")


def open_annotation_layer(https_base: str = MALECNS_SYNAPSE_LAYER_HTTPS):
    """Open the official layer. Returns (reader, info, shims)."""
    shims = _apply_reader_shims()
    info = _fetch_info(https_base)
    official_compartment_enum(info)          # fail fast on unexpected schema
    if info.get("@type") != "neuroglancer_annotations_v1":
        raise CompartmentRetrievalError(
            f"unexpected layer type {info.get('@type')!r}")
    info = dict(info)
    info["annotation_type"] = str(info["annotation_type"]).upper()
    from cloudvolume.datasource.precomputed import create_precomputed_annotation
    reader = create_precomputed_annotation(
        https_base.replace("https://storage.googleapis.com/",
                           "gs://").rstrip("/"),
        use_https=True, info=info)
    return reader, info, shims


def retrieve_post_compartments(
        contacts: Sequence,
        expected_pre_body: int,
        post_body: int,
        https_base: str = MALECNS_SYNAPSE_LAYER_HTTPS,
        reader=None,
        ) -> Tuple[List[CompartmentAnnotation], Dict[str, str]]:
    """Official ``compartment_post`` for each contact whose post body is given.

    Each contact is matched to an annotation by **exact integer equality** of the
    post-synaptic coordinate. A contact that does not match exactly one annotation
    raises: this module never attaches a label to a contact it cannot locate.
    """
    if int(post_body) not in VERIFIED_PAIRINGS:
        raise CompartmentRetrievalError(
            f"body {post_body} is not a verified MN5 body "
            f"({sorted(VERIFIED_PAIRINGS)})")
    if VERIFIED_PAIRINGS[int(post_body)] != int(expected_pre_body):
        raise CompartmentRetrievalError(
            f"body pairing {expected_pre_body}->{post_body} is not a verified "
            f"PSI->MN5 pairing; cross-pairings are not permitted")

    shims: Dict[str, str] = {}
    if reader is None:
        reader, info, shims = open_annotation_layer(https_base)
    else:
        info = _fetch_info(https_base)
        shims = {"reader": "supplied by caller"}
    enum = official_compartment_enum(info)

    import numpy as np

    result = reader.get_by_relationship(COMPARTMENT_RELATIONSHIP, int(post_body))
    props = result.properties
    geometry = np.asarray(result.geometry)

    # Restrict to the verified presynaptic partner, then index by post point.
    candidates: Dict[Tuple[int, int, int], List[int]] = {}
    for i, pre in enumerate(props["body_pre_u32"]):
        if int(pre) != int(expected_pre_body):
            continue
        pt2 = (int(geometry[i][3]), int(geometry[i][4]), int(geometry[i][5]))
        candidates.setdefault(pt2, []).append(i)

    out: List[CompartmentAnnotation] = []
    for idx, c in enumerate(contacts):
        if int(c.post_body) != int(post_body) or int(c.pre_body) != int(expected_pre_body):
            continue
        key = (int(c.post_xyz[0]), int(c.post_xyz[1]), int(c.post_xyz[2]))
        hits = candidates.get(key, ())
        if len(hits) != 1:
            raise CompartmentRetrievalError(
                f"contact {idx} of {expected_pre_body}->{post_body} at {key} "
                f"matched {len(hits)} annotations in the official layer "
                f"(expected exactly 1); refusing to assign a label")
        i = hits[0]
        out.append(CompartmentAnnotation(
            contact_index=idx,
            pre_body=int(props["body_pre_u32"][i]),
            post_body=int(props["body_post_u32"][i]),
            compartment_post=str(enum[int(props["compartment_post"][i])]),
            compartment_pre=str(enum[int(props["compartment_pre"][i])]),
            conf_pre=float(props["conf_pre"][i]),
            conf_post=float(props["conf_post"][i]),
            post_xyz_raw=key,
            source_layer=https_base,
            relationship=COMPARTMENT_RELATIONSHIP,
            enum_labels=enum))
    return out, shims


def compartment_summary(
        annotations: Sequence[CompartmentAnnotation]) -> Dict[str, object]:
    """Frequency summary. Descriptive only; no compartment is interpreted."""
    counts: Dict[str, int] = {}
    for a in annotations:
        counts[a.compartment_post] = counts.get(a.compartment_post, 0) + 1
    return {
        "count": len(annotations),
        "label_counts": dict(sorted(counts.items(),
                                    key=lambda kv: (-kv[1], kv[0]))),
        "distinct_labels": sorted(counts),
        "unknown_count": counts.get("unknown", 0),
        "missing_count": sum(1 for a in annotations
                             if not a.compartment_post),
        "provenance": EvidenceClass.ANATOMICAL_MEASUREMENT.value,
        "interpretation_guard": (
            "These are the source's own enum strings, counted. They are NOT "
            "interpreted as axon or dendrite by this project, and they do not "
            "resolve the SWC kind question."),
    }


def contacts_from_feather(feather_path: str,
                          pre_body: int, post_body: int) -> List:
    """Load the verified contacts from the MaleCNS synapse partner table."""
    syn = MaleCNSSynapses(feather_path)
    allc = syn.extract([PSI_LEFT, PSI_RIGHT], [MN5_LEFT, MN5_RIGHT])
    return [c for c in allc
            if int(c.pre_body) == int(pre_body)
            and int(c.post_body) == int(post_body)]


def verified_contact_frame_unit() -> float:
    """The frame the contact coordinates are in, stated explicitly."""
    return float(COORD_UNIT_NM)
