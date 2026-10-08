"""MaleCNS v1.0 ingestion, geometry and provenance infrastructure (3.0D-8P).

WHAT THIS MODULE IS
-------------------
A reproducible, provenance-preserving **anatomical data layer** for the
FlyEM Male CNS ``v1.0`` connectome, covering the PSI -> MN5 / DLMn a,b
connection that 3.0D established:

    * verified body identities for the two PSI and two MN5 neurons;
    * the 43 individually resolved PSI -> MN5 synaptic contacts, with their
      pre/post coordinates, confidences and anatomical compartment label;
    * MN5 EM skeleton geometry read from the official SWC files;
    * purely anatomical contact -> root traversal;
    * contact clustering and coordinate-frame validation;
    * a provenance ledger that forces every reported quantity to carry exactly
      one evidence class.

WHAT THIS MODULE IS NOT
-----------------------
It is **not** an electrical model. It computes no length constant, no
electrotonic distance, no voltage attenuation, no transfer resistance and no
local-to-somatic conversion. It carries no ``Cm``, ``Ra``, ``g_pas`` or
``E_pas``, and it derives none of them. Attempting to obtain one of those from
this module raises :class:`BiologicalTransferNotAuthorized`.

The reason is a scientific one, not a stylistic one. 3.0D established that
MN5-specific passive parameters cannot be uniquely determined: the two
available whole-cell measurements (43 +/- 2 pF and 102 +/- 12 MOhm from
Fayyazuddin et al. 2006) give two equations for three unknowns (Cm, Rm/g_pas,
Ra), no independent constraint on ``Ra`` exists in any MN5 source, the
recovered skeleton contains no soma node, and the somatic capacitance is
experimentally discrepant by a factor of three. This module preserves the
anatomy that is established and refuses to fill in the electricity that is
not.

DATA SOURCE
-----------
Official Janelia/FlyEM Male CNS public distribution, licensed CC-BY.
Dataset ``male-cns:v1.0``; citation Berg et al. (2026), Cell,
doi:10.1016/j.cell.2026.08.015. No authentication is required. Files are
fetched by the caller and passed in by path; this module never downloads and
never mutates a source file.
"""

from __future__ import annotations

import hashlib
import math
import os
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

DATASET_NAME = "male-cns"
DATASET_VERSION = "v1.0"
DATASET_LICENCE = "CC-BY"
DATASET_CITATION = (
    "Berg et al. (2026) Sexual dimorphism in the complete Drosophila male "
    "central nervous system connectome. Cell. doi:10.1016/j.cell.2026.08.015"
)
PUBLIC_BASE = (
    "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/"
    "flat-connectome/"
)
SWC_BASE = (
    "https://storage.googleapis.com/flyem-male-cns/v1.0/segmentation/"
    "skeletons-malecns/skeletons-swc/"
)
MIRRORED_SWC_BASE = (
    "https://storage.googleapis.com/flyem-male-cns/v1.0/segmentation/"
    "skeletons-malecns-mirrored/skeletons-swc/"
)

#: The non-mirrored Male CNS SWCs are in EM coordinate space, 8 nm units.
#: The MIRRORED set is a different transform and must never be substituted.
COORD_UNIT_NM = 8.0
COORD_UNIT_UM = COORD_UNIT_NM / 1000.0
FRAME_EM_8NM = "male-cns EM space, 8 nm units"
FRAME_MIRRORED_1NM = "mirrored, 1 nm units"

#: The confidence floor is applied by the SOURCE, and is encoded in the file
#: names. This module records it; it never re-filters.
SOURCE_MINCONF = 0.5


class EvidenceClass(Enum):
    """The only five evidence classes permitted in this project.

    A quantity may be promoted out of these classes only by new primary
    measurement, never by model fit or by numerical convenience.
    """

    NATIVE_EXPERIMENTAL_MEASUREMENT = "native_experimental_measurement"
    ANATOMICAL_MEASUREMENT = "anatomical_measurement"
    LITERATURE_DERIVED_PASSIVE_PARAMETER = "literature_derived_passive_parameter"
    MODEL_ASSUMPTION = "model_assumption"
    MODEL_DERIVED_ESTIMATE = "model_derived_estimate"


class BiologicalTransferNotAuthorized(Exception):
    """Raised when anatomical infrastructure is asked for electrical results.

    3.0D concluded the PSI -> MN5 electrical transfer function is scientifically
    underdetermined. This is the single place that decision is enforced, so the
    refusal cannot be bypassed by accident.
    """

    BLOCKER = (
        "MN5 passive parameters are not uniquely determinable from available "
        "evidence: two whole-cell measurements (C and Rin) constrain three "
        "unknowns (Cm, Rm/g_pas, Ra); no independent constraint on Ra exists "
        "in any MN5 source; the recovered EM skeleton contains no soma node so "
        "Cm = C/A cannot be formed; and the somatic capacitance is "
        "experimentally discrepant (43 +/- 2 pF vs 127 +/- 16 pF). No "
        "electrical quantity may be derived from anatomical geometry."
    )


def require_biological_transfer_authorization() -> None:
    """Always raises. The biological transfer gate has not been passed."""
    raise BiologicalTransferNotAuthorized(BiologicalTransferNotAuthorized.BLOCKER)


# --- provenance ---------------------------------------------------------------


@dataclass(frozen=True)
class ProvenanceQuantity:
    """One reported quantity with exactly one evidence class."""

    name: str
    value: object
    units: str
    evidence: EvidenceClass
    source: str
    note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, EvidenceClass):
            raise ValueError(
                f"{self.name!r}: evidence must be an EvidenceClass, got "
                f"{type(self.evidence).__name__}"
            )
        if not self.name or not self.source:
            raise ValueError(f"{self.name!r}: name and source are required")


@dataclass(frozen=True)
class DatasetProvenance:
    """Where the ingested data came from and what was done to it."""

    dataset: str = DATASET_NAME
    version: str = DATASET_VERSION
    licence: str = DATASET_LICENCE
    citation: str = DATASET_CITATION
    source_urls: Tuple[str, ...] = ()
    files: Tuple[Tuple[str, int, str], ...] = ()  # (name, size_bytes, sha256)
    minconf: float = SOURCE_MINCONF
    coordinate_units: str = f"1 unit = {COORD_UNIT_NM:g} nm = {COORD_UNIT_UM} um"
    coordinate_frame: str = FRAME_EM_8NM
    transformations_applied: Tuple[str, ...] = ()

    def record_file(self, name: str, path: str) -> None:
        """Append (name, size, sha256) for an ingested file, without mutating it."""
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        entry = (name, os.path.getsize(path), digest.hexdigest())
        object.__setattr__(self, "files", self.files + (entry,))

    def describe(self) -> str:
        lines = [
            f"dataset   : {self.dataset}:{self.version}  ({self.licence})",
            f"citation  : {self.citation}",
            f"minconf   : {self.minconf} (applied by source; not re-filtered here)",
            f"units     : {self.coordinate_units}",
            f"frame     : {self.coordinate_frame}",
            f"transforms: "
            f"{', '.join(self.transformations_applied) or 'none - coordinates are raw'}",
            "files     :",
        ]
        for name, size, digest in self.files:
            lines.append(f"    {name}  {size:,} bytes  sha256:{digest[:24]}")
        return "\n".join(lines)


# --- body identity registry (data records, NOT production biology) ------------


@dataclass(frozen=True)
class BodyIdentity:
    """A verified body-ID -> cell-type record, as PROVENANCE DATA."""

    body_id: int
    cell_type: str
    superclass: str
    soma_side: str
    role: str
    source: str = f"{DATASET_NAME}:{DATASET_VERSION} body-annotations"
    status_label: str = "Reviewed"

    def provenance(self) -> ProvenanceQuantity:
        return ProvenanceQuantity(
            name=f"body {self.body_id} cell type",
            value=self.cell_type,
            units="",
            evidence=EvidenceClass.ANATOMICAL_MEASUREMENT,
            source=self.source,
            note=(
                f"superclass={self.superclass}; somaSide={self.soma_side}; "
                f"role={self.role}; status={self.status_label}. This is a "
                f"PROVENANCE RECORD, not a biological model constant."
            ),
        )


MN5_LEFT = 801970
MN5_RIGHT = 801295
PSI_LEFT = 802401
PSI_RIGHT = 903327

BODY_IDENTITIES: Tuple[BodyIdentity, ...] = (
    BodyIdentity(MN5_LEFT, "DLMn a, b", "vnc_motor", "L",
                 "MN5 / DLMn a,b -- identity established from Fayyazuddin 2006"),
    BodyIdentity(MN5_RIGHT, "DLMn a, b", "vnc_motor", "R",
                 "MN5 / DLMn a,b -- identity established from Fayyazuddin 2006"),
    BodyIdentity(PSI_LEFT, "PSI", "vnc_efferent", "L",
                 "peripherally synapsing interneuron"),
    BodyIdentity(PSI_RIGHT, "PSI", "vnc_efferent", "R",
                 "peripherally synapsing interneuron"),
)


class BodyIdentityRegistry:
    """Resolved body identities, checkable against a loaded annotation table."""

    def __init__(self, identities: Sequence[BodyIdentity] = BODY_IDENTITIES):
        self._by_id = {i.body_id: i for i in identities}

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, body_id: int) -> bool:
        return body_id in self._by_id

    def get(self, body_id: int) -> BodyIdentity:
        if body_id not in self._by_id:
            raise KeyError(
                f"body {body_id} is not in the verified identity registry; "
                f"known: {sorted(self._by_id)}"
            )
        return self._by_id[body_id]

    @property
    def mn5_ids(self) -> Tuple[int, int]:
        return (MN5_LEFT, MN5_RIGHT)

    @property
    def psi_ids(self) -> Tuple[int, int]:
        return (PSI_LEFT, PSI_RIGHT)

    def all_provenance(self) -> List[ProvenanceQuantity]:
        return [i.provenance() for i in
                sorted(self._by_id.values(), key=lambda i: i.body_id)]

    def validate_against(self, table: "MaleCNSCellTypes") -> None:
        """Confirm every registered identity matches the source annotation."""
        for identity in self._by_id.values():
            row = table.row(identity.body_id)
            if row is None:
                raise ValueError(
                    f"body {identity.body_id} absent from "
                    f"{DATASET_NAME}:{DATASET_VERSION} body-annotations"
                )
            for attr, expected in (("cell_type", identity.cell_type),
                                   ("superclass", identity.superclass),
                                   ("soma_side", identity.soma_side)):
                if getattr(row, attr) != expected:
                    raise ValueError(
                        f"body {identity.body_id} {attr}: registry says "
                        f"{expected!r}, source says {getattr(row, attr)!r}"
                    )


# --- Male CNS tables ---------------------------------------------------------


class MalecnsSchemaError(Exception):
    """The source file does not have the schema this module requires."""


@dataclass(frozen=True)
class CellTypeRow:
    body_id: int
    cell_type: str
    superclass: str
    soma_side: str
    soma_neuromere: Optional[str]
    soma_location: Optional[Tuple[float, float, float]]
    exit_nerve: Optional[str]


class MaleCNSCellTypes:
    """``body-annotations-*.feather``, read column-projected."""

    WANTED = ("bodyId", "type", "superclass", "somaSide", "somaNeuromere",
              "somaLocation", "exitNerve")

    def __init__(self, path: str):
        import pyarrow.feather as feather  # imported lazily

        table = feather.read_table(path, columns=list(self.WANTED))
        missing = [c for c in self.WANTED if c not in table.column_names]
        if missing:
            raise MalecnsSchemaError(
                f"body-annotations is missing required columns: {missing}"
            )
        data = table.to_pydict()
        self._rows: Dict[int, CellTypeRow] = {}
        for i, body in enumerate(data["bodyId"]):
            loc = data["somaLocation"][i]
            if isinstance(loc, list):
                loc = tuple(float(v) for v in loc)
            elif loc is not None:
                loc = (float(loc),)
            self._rows[int(body)] = CellTypeRow(
                body_id=int(body),
                cell_type=data["type"][i],
                superclass=data["superclass"][i],
                soma_side=data["somaSide"][i],
                soma_neuromere=data["somaNeuromere"][i],
                soma_location=loc,
                exit_nerve=data["exitNerve"][i],
            )

    def __len__(self) -> int:
        return len(self._rows)

    def row(self, body_id: int) -> Optional[CellTypeRow]:
        return self._rows.get(body_id)

    def soma_records(self, body_ids: Sequence[int]) -> List[ProvenanceQuantity]:
        """Soma ANNOTATION records. No surface area, volume or radius is derived.

        A nucleus is not a soma; nuclei segmentation, if ever loaded, stays a
        separate artefact and is never converted into soma geometry.
        """
        out = []
        for bid in body_ids:
            r = self.row(bid)
            if r is None:
                raise KeyError(f"body {bid} absent from body-annotations")
            out.append(ProvenanceQuantity(
                name=f"body {bid} soma location",
                value=r.soma_location,
                units=f"EM units (1 unit = {COORD_UNIT_NM:g} nm)",
                evidence=EvidenceClass.ANATOMICAL_MEASUREMENT,
                source=f"{DATASET_NAME}:{DATASET_VERSION} body-annotations "
                       f"somaLocation",
                note=(
                    f"somaNeuromere={r.soma_neuromere}; exitNerve={r.exit_nerve}. "
                    f"This is a LOCATION ANNOTATION ONLY. No soma surface area, "
                    f"volume or radius is derived here, and none is available."
                ),
            ))
        return out


@dataclass(frozen=True)
class SynapticContact:
    """One individual EM synaptic contact, with raw source fields."""

    pre_body: int
    post_body: int
    pre_xyz: Tuple[float, float, float]
    post_xyz: Tuple[float, float, float]
    conf_pre: float
    conf_post: float
    primary_post: str

    def validate(self, pre_ids: Sequence[int], post_ids: Sequence[int],
                 minconf: float = SOURCE_MINCONF) -> None:
        if self.pre_body not in pre_ids:
            raise ValueError(
                f"unexpected pre-synaptic body {self.pre_body}, expected "
                f"{sorted(pre_ids)}"
            )
        if self.post_body not in post_ids:
            raise ValueError(
                f"unexpected post-synaptic body {self.post_body}, expected "
                f"{sorted(post_ids)}"
            )
        for label, xyz in (("pre", self.pre_xyz), ("post", self.post_xyz)):
            if len(xyz) != 3 or any(
                    v is None or not math.isfinite(float(v)) for v in xyz):
                raise ValueError(
                    f"malformed {label}-synaptic coordinate {xyz!r}"
                )
        for label, c in (("pre", self.conf_pre), ("post", self.conf_post)):
            if c is None or not math.isfinite(float(c)):
                raise ValueError(f"missing {label} confidence")
            if float(c) < minconf:
                raise ValueError(
                    f"{label} confidence {c} below source threshold {minconf}"
                )

    def key(self) -> Tuple[int, int, Tuple[float, float, float]]:
        return (self.pre_body, self.post_body, self.post_xyz)


class MaleCNSSynapses:
    """Stream ``syn-partners-*.feather`` and extract selected pairings.

    The file is ~6.8 GB and cannot be held in memory, so it is streamed one
    Arrow record batch at a time. Coordinates are passed through RAW; this class
    never rescales, rounds or transforms them.
    """

    WANTED = ("x_pre", "y_pre", "z_pre", "body_pre", "conf_pre",
              "x_post", "y_post", "z_post", "body_post", "conf_post",
              "primary_post")

    def __init__(self, path: str):
        import pyarrow as pa
        import pyarrow.ipc as ipc

        self._reader = ipc.open_file(pa.memory_map(path))
        have = set(self._reader.schema.names)
        missing = [c for c in self.WANTED if c not in have]
        if missing:
            raise MalecnsSchemaError(
                f"syn-partners is missing required columns: {missing}"
            )

    def extract(self, pre_ids: Sequence[int],
                post_ids: Sequence[int]) -> List[SynapticContact]:
        pre_set, post_set = set(pre_ids), set(post_ids)
        out: List[SynapticContact] = []
        for i in range(self._reader.num_record_batches):
            batch = self._reader.get_batch(i)
            pre = batch.column("body_pre").to_pylist()
            post = batch.column("body_post").to_pylist()
            hits = [j for j in range(batch.num_rows)
                    if pre[j] in pre_set and post[j] in post_set]
            if hits:
                d = batch.to_pydict()
                for j in hits:
                    out.append(SynapticContact(
                        pre_body=int(pre[j]),
                        post_body=int(post[j]),
                        pre_xyz=(d["x_pre"][j], d["y_pre"][j], d["z_pre"][j]),
                        post_xyz=(d["x_post"][j], d["y_post"][j], d["z_post"][j]),
                        conf_pre=float(d["conf_pre"][j]),
                        conf_post=float(d["conf_post"][j]),
                        primary_post=d["primary_post"][j],
                    ))
            del batch
            if hits:
                del d
        return out


def validate_contacts(contacts: Sequence[SynapticContact],
                      pre_ids: Sequence[int], post_ids: Sequence[int],
                      minconf: float = SOURCE_MINCONF) -> Dict[str, object]:
    """Structural validation plus an INDEPENDENTLY COMPUTED confidence census.

    The confidence distribution is computed from the records themselves and is
    never copied from prose. It is returned so a report can print measured
    counts rather than a remembered summary.
    """
    seen = set()
    for c in contacts:
        c.validate(pre_ids, post_ids, minconf)
        k = c.key()
        if k in seen:
            raise ValueError(f"duplicate contact record: {k}")
        seen.add(k)
    if not contacts:
        raise ValueError("no contacts extracted")

    pre_counts = Counter(float(c.conf_pre) for c in contacts)
    post_counts = Counter(float(c.conf_post) for c in contacts)
    post_vals = [float(c.conf_post) for c in contacts]
    return {
        "total_contacts": len(contacts),
        "distinct_pre_bodies": sorted({c.pre_body for c in contacts}),
        "distinct_post_bodies": sorted({c.post_body for c in contacts}),
        "conf_pre_distribution": dict(sorted(pre_counts.items())),
        "conf_post_distribution": dict(sorted(post_counts.items())),
        "conf_post_min": min(post_vals),
        "conf_post_max": max(post_vals),
        "minconf_threshold": minconf,
        "primary_post_distribution": dict(
            sorted(Counter(c.primary_post for c in contacts).items())),
    }


# --- coordinate frame --------------------------------------------------------


class CoordinateFrameError(Exception):
    """Coordinates and morphology are not in a common, declared frame."""


def um(units: float, unit_nm: float = COORD_UNIT_NM) -> float:
    """Convert Male CNS EM units to micrometres. 1 unit = 8 nm = 0.008 um."""
    return float(units) * float(unit_nm) / 1000.0


def validate_frame(contacts: Sequence[SynapticContact],
                   bbox_raw_units: Tuple[float, ...],
                   frame: str = FRAME_EM_8NM,
                   unit_nm: float = COORD_UNIT_NM) -> ProvenanceQuantity:
    """Check contacts lie inside a declared morphology bounding box.

    ``bbox_raw_units`` MUST be in the same RAW units as the synapse
    coordinates (use :meth:`SkeletonGeometry.bbox_raw`), not in micrometres --
    mixing the two would rescale the box by 1000x and hide the mismatch this
    check exists to catch.

    A frame mismatch is an explicit error. This is the invariant that
    distinguishes the EM (8 nm) skeletons from the MIRRORED (1 nm) set: the
    mirrored skeletons fail it, which is why they must never be substituted.
    """
    if frame not in (FRAME_EM_8NM, FRAME_MIRRORED_1NM):
        raise CoordinateFrameError(
            f"unknown coordinate frame {frame!r}; expected one of "
            f"{[FRAME_EM_8NM, FRAME_MIRRORED_1NM]!r}"
        )
    lo = [um(v, unit_nm) for v in bbox_raw_units[:3]]
    hi = [um(v, unit_nm) for v in bbox_raw_units[3:]]
    inside = 0
    for c in contacts:
        x, y, z = (um(v, unit_nm) for v in c.post_xyz)
        if (lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]
                and lo[2] <= z <= hi[2]):
            inside += 1
    if inside != len(contacts):
        raise CoordinateFrameError(
            f"frame mismatch: only {inside}/{len(contacts)} contacts fall "
            f"inside the morphology bounding box in {frame!r}. Either the "
            f"contacts or the skeleton are in a different transform."
        )
    return ProvenanceQuantity(
        name="coordinate frame registration",
        value=frame,
        units=f"1 unit = {COORD_UNIT_NM:g} nm = {COORD_UNIT_UM} um",
        evidence=EvidenceClass.ANATOMICAL_MEASUREMENT,
        source=f"{DATASET_NAME}:{DATASET_VERSION} syn-partners + skeletons",
        note=(f"{inside}/{len(contacts)} post-synaptic points inside the "
              f"morphology bounding box; no transformation applied."),
    )


# --- SWC geometry (no cable model) ------------------------------------------

# --- SWC node "kind" / Type column semantics (3.0D-8T) -----------------------
#
# The MaleCNS download page states its skeletons are "in SWC format" and cites
# the SWC v1.0.0 specification as that format:
#   male-cns.janelia.org/download/ -> "[swc]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10654402"
#   = Mehta, Ljungquist, Ogden, Nanda, Ascoli RA, Ng, Ascoli GA (2023)
#     "Online conversion of reconstructed neural morphologies into standardized
#      SWC format", Nat Commun 14:7429. That paper's Table 1 defines the codes.
#
# CRITICAL: MaleCNS itself documents NOTHING about how the Type column is
# POPULATED for its skeletons. The paper never uses the string "SWC". No
# MaleCNS page, README or annotation column describes it. The only official
# statement about the column is that the official reader DISCARDS it:
#   neuprint-python skeleton docs, skeleton_swc_to_df():
#     "Create a DataFrame from and SWC file. The 'node_type' column is
#      discarded."
# neuPrint also states the skeletons are segmentation-derived -- "skeletons from
# neuprint sometimes consist of multiple fragments ... due to artifacts in the
# underlying segmentation from which the skeletons were generated" -- which
# independently corroborates the mesh fragmentation measured in 3.0D-8Q.
#
# CONSEQUENCE FOR THIS PROJECT: the code values below are the FORMAT's codes,
# not a MaleCNS biological claim. kind=2 is not asserted to be axon here.

#: SWC v1.0.0 Type codes, from PMC10654402 Table 1. Format semantics only.
SWC_TYPE_CODES: Dict[int, str] = {
    0: "Undefined (structure type unknown or unspecified)",
    1: "Soma",
    2: "Axon",
    3: "Basal dendrite",
    4: "Apical dendrite",
    5: "Custom (user defined element)",
    6: "Unspecified neurite (axon or dendrite)",
    7: "Glia process",
}

#: The SWC spec's own wording on Type 0, which matters for reading MaleCNS.
SWC_TYPE_ZERO_NOTE = (
    "Per PMC10654402: Type 0 is 'used when the structural domain of an SWC "
    "point is not established in the reconstruction, and could correspond to "
    "any portion of the morphology, including soma or glia process'. So a "
    "predominantly-Type-0 arbor is UNLABELLED, not dendritic.")

#: Status of the MaleCNS biological interpretation of the Type column.
MALECNS_NODE_TYPE_BIOLOGY = "UNDEFINED IN AVAILABLE SOURCE"

MALECNS_SWC_SEMANTICS = (
    "MaleCNS v1.0 publishes SWC skeletons and cites the SWC v1.0.0 "
    "specification (PMC10654402) for the FORMAT, but does not document how the "
    "Type/kind column is populated for its neurons. The skeletons are derived "
    "from the proofread segmentation rather than hand-traced with compartment "
    "annotation, and the official neuPrint reader discards the node_type "
    "column entirely. Consequently the numeric codes carry format meaning only: "
    "kind=2 is NOT established by any MaleCNS source as biological axon, and "
    "this project does not treat it as axon. Berg et al. (2025) obtain their "
    "axon/dendrite split by a POST-HOC flow-centrality algorithm applied to the "
    "skeleton, not from this column.")

#: neuPrint's own caveat about the stored root.
SWC_ROOT_SIGNIFICANCE_CAVEAT = (
    "neuPrint documentation states that for stored skeletons 'the root node "
    "... is not particularly significant, so the directionality of the nodes "
    "(parent to child or vice-versa) on any given neuron branch is arbitrary'. "
    "That is a general caution about the stored root, and it applies to these "
    "MaleCNS skeletons. This project measures the root's distance to the "
    "annotated somaLocation directly rather than assuming the root is "
    "proximal, and reports that measurement; but 'root == proximal stalk "
    "origin' is a MEASURED LOCALISATION, not a documented property of the file.")

#: The SWC spec's soma representation, for the record.
SWC_SOMA_REPRESENTATION = (
    "Per PMC10654402 the soma in a standardized SWC can consist of a single "
    "root point or multiple points, the first of which must be a root; and the "
    "specification's own conformance check emits a warning when 'no soma "
    "samples' are detected. MaleCNS MN5/PSI skeletons contain zero kind==1 "
    "nodes, so they do not carry a soma sample under that convention. Whether "
    "MaleCNS represents the soma by another means is NOT STATED by any "
    "available source.")


@dataclass(frozen=True)
class SwcNode:
    index: int
    kind: int
    x: float
    y: float
    z: float
    radius: float
    parent: int


def swc_type_semantics(skel: "SkeletonGeometry") -> Dict[str, object]:
    """Report the measured kind distribution WITHOUT asserting biology.

    Returns the observed code counts plus the documented status of their
    meaning. This deliberately reports rather than interprets: the MaleCNS
    biological interpretation of the Type column is
    ``UNDEFINED IN AVAILABLE SOURCE`` (see :data:`MALECNS_SWC_SEMANTICS`), so a
    count of ``kind=2`` is a count of a FORMAT CODE, not of axons.
    """
    counts: Dict[int, int] = {}
    for n in skel.nodes:
        counts[n.kind] = counts.get(n.kind, 0) + 1
    total_nodes = len(skel.nodes)
    by_kind_radius: Dict[int, List[float]] = {}
    for n in skel.nodes:
        by_kind_radius.setdefault(n.kind, []).append(skel.to_um(n.radius))
    cable_by_kind: Dict[int, float] = {}
    table = skel.by_index()
    for n in skel.nodes:
        p = table.get(n.parent)
        if p is not None:
            d = skel.distance(n, p)
            cable_by_kind[n.kind] = cable_by_kind.get(n.kind, 0.0) + d
    total_cable = sum(cable_by_kind.values())
    return {
        "body_id": skel.body_id,
        "node_count": total_nodes,
        "kinds_present": sorted(counts),
        "node_count_by_kind": dict(sorted(counts.items())),
        "fraction_by_kind": {
            k: v / total_nodes if total_nodes else 0.0
            for k, v in sorted(counts.items())},
        "cable_length_um_by_kind": dict(sorted(cable_by_kind.items())),
        "cable_fraction_by_kind": {
            k: (v / total_cable if total_cable else 0.0)
            for k, v in sorted(cable_by_kind.items())},
        "radius_um_by_kind": {
            k: {"min": min(v), "median": sorted(v)[len(v) // 2], "max": max(v)}
            for k, v in sorted(by_kind_radius.items())},
        "root_indices": [n.index for n in skel.roots],
        "root_kinds": [n.kind for n in skel.roots],
        "has_soma_node_any_source": any(n.kind == 1 for n in skel.nodes),
        "format_code_meanings": {
            k: SWC_TYPE_CODES.get(k, "UNDEFINED IN AVAILABLE SOURCE")
            for k in sorted(counts)},
        "malecns_biological_meaning": MALECNS_NODE_TYPE_BIOLOGY,
        "interpretation_guard": (
            "Counts above are counts of SWC FORMAT CODES. They are NOT counts "
            "of axons, dendrites or somata: no MaleCNS source documents the "
            "biological meaning of this column, and the official neuPrint "
            "reader discards it."),
        "type_zero_note": SWC_TYPE_ZERO_NOTE,
        "root_caveat": SWC_ROOT_SIGNIFICANCE_CAVEAT,
        "soma_representation": SWC_SOMA_REPRESENTATION,
    }


@dataclass
class SkeletonGeometry:
    """Pure geometry. No passive parameter, no channel, no cable model."""

    body_id: int
    frame: str
    unit_nm: float
    nodes: List[SwcNode]

    @classmethod
    def from_swc(cls, path: str, body_id: int,
                 frame: str = FRAME_EM_8NM,
                 unit_nm: float = COORD_UNIT_NM) -> "SkeletonGeometry":
        nodes: List[SwcNode] = []
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 6:
                    continue
                try:
                    nodes.append(SwcNode(
                        index=int(parts[0]), kind=int(parts[1]),
                        x=float(parts[2]), y=float(parts[3]), z=float(parts[4]),
                        radius=float(parts[5]),
                        parent=int(parts[6]) if len(parts) > 6 else -1,
                    ))
                except ValueError:
                    continue
        if not nodes:
            raise ValueError(f"{path}: no SWC nodes parsed")
        return cls(body_id=body_id, frame=frame, unit_nm=unit_nm, nodes=nodes)

    def to_um(self, v: float) -> float:
        return float(v) * self.unit_nm / 1000.0

    @property
    def roots(self) -> List[SwcNode]:
        return [n for n in self.nodes if n.parent < 0]

    def by_index(self) -> Dict[int, SwcNode]:
        return {n.index: n for n in self.nodes}

    def segments(self) -> List[Tuple[SwcNode, SwcNode]]:
        table = self.by_index()
        out = []
        for n in self.nodes:
            if n.parent in table:
                out.append((table[n.parent], n))
        return out

    def bbox_um(self) -> Tuple[float, ...]:
        """Bounding box in MICROMETRES."""
        xs = [self.to_um(n.x) for n in self.nodes]
        ys = [self.to_um(n.y) for n in self.nodes]
        zs = [self.to_um(n.z) for n in self.nodes]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

    def bbox_raw(self) -> Tuple[float, ...]:
        """Bounding box in RAW EM units -- the same units as synapse
        coordinates. Use this with :func:`validate_frame`."""
        return (
            min(n.x for n in self.nodes), min(n.y for n in self.nodes),
            min(n.z for n in self.nodes),
            max(n.x for n in self.nodes), max(n.y for n in self.nodes),
            max(n.z for n in self.nodes),
        )

    def stats(self) -> Dict[str, object]:
        segs = self.segments()
        lengths = [self.distance(a, b) for a, b in segs]
        radii = [self.to_um(n.radius) for n in self.nodes]
        return {
            "body_id": self.body_id,
            "frame": self.frame,
            "node_count": len(self.nodes),
            "segment_count": len(segs),
            "root_count": len(self.roots),
            "root_indices": [n.index for n in self.roots],
            "node_kinds": sorted({n.kind for n in self.nodes}),
            "has_soma_node": any(n.kind == 1 for n in self.nodes),
            "radius_um_min": min(radii), "radius_um_max": max(radii),
            "process_length_um": sum(self.to_um(v) for v in lengths),
            "bbox_um": self.bbox_um(),
        }

    @staticmethod
    def distance(a: SwcNode, b: SwcNode) -> float:
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2
                         + (a.z - b.z) ** 2)

    def nearest_node(self, xyz: Tuple[float, float, float]) -> Tuple[SwcNode, float]:
        """Nearest node in EM units.

        The rule is EXPLICIT and Euclidean over raw coordinates. No
        compartment, axon/dendrite or proximity-based classification is made.
        """
        px, py, pz = xyz
        best, best_d = None, float("inf")
        for n in self.nodes:
            d = math.sqrt((n.x - px) ** 2 + (n.y - py) ** 2 + (n.z - pz) ** 2)
            if d < best_d:
                best, best_d = n, d
        return best, best_d

    def path_to_root(self, node_index: int) -> Tuple[List[SwcNode], float]:
        """Geometric path length from a node to its tree root, in micrometres."""
        table = self.by_index()
        if node_index not in table:
            raise KeyError(
                f"node {node_index} not in skeleton {self.body_id}")
        chain: List[SwcNode] = []
        cur = table[node_index]
        chain.append(cur)
        seen = {cur.index}
        while cur.parent in table:
            cur = table[cur.parent]
            if cur.index in seen:
                raise ValueError(f"cycle in parent graph at node {cur.index}")
            seen.add(cur.index)
            chain.append(cur)
        total = sum(self.distance(a, b) for a, b in zip(chain, chain[1:]))
        return chain, self.to_um(total)


def contact_to_root_report(skel: SkeletonGeometry,
                           contacts: Sequence[SynapticContact],
                           tolerance_um: float = 1e-6) -> Dict[str, object]:
    """Anatomical contact -> root traversal.

    The result is a MODEL-DERIVED ESTIMATE: it comes from reconstructed
    morphology plus an explicit node-assignment rule, and is NOT an
    experimentally measured electrical distance. No cable model is involved.
    """
    if len(skel.roots) != 1:
        raise ValueError(
            f"expected exactly one root to trace to, found "
            f"{len(skel.roots)} in skeleton {skel.body_id}"
        )
    lengths, assign = [], []
    for c in contacts:
        node, d = skel.nearest_node(c.post_xyz)
        chain, length = skel.path_to_root(node.index)
        lengths.append(length)
        assign.append((node.index, skel.to_um(d)))
    lengths.sort()
    return {
        "body_id": skel.body_id,
        "contact_count": len(contacts),
        "root_index": skel.roots[0].index,
        "path_um_min": lengths[0],
        "path_um_median": lengths[len(lengths) // 2],
        "path_um_max": lengths[-1],
        "tolerance_um": tolerance_um,
        "node_assignments": assign,
        "_evidence": EvidenceClass.MODEL_DERIVED_ESTIMATE,
    }


def clustering_report(contacts: Sequence[SynapticContact],
                      unit_nm: float = COORD_UNIT_NM) -> Dict[str, object]:
    """Geometry-only contact statistics. Contacts are NEVER collapsed."""
    pts = [tuple(um(v, unit_nm) for v in c.post_xyz) for c in contacts]
    nn = sorted(
        min(math.dist(a, b) for j, b in enumerate(pts) if j != i)
        for i, a in enumerate(pts)
    )
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    groups: Dict[str, List[Tuple[float, float, float]]] = {}
    for c, p in zip(contacts, pts):
        groups.setdefault(c.primary_post, []).append(p)
    return {
        "contact_count": len(contacts),
        "extent_um": (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)),
        "nearest_neighbour_um": {"min": nn[0],
                                  "median": nn[len(nn) // 2],
                                  "max": nn[-1]},
        "by_primary_post": {
            label: {
                "count": len(v),
                "extent_um": (max(p[0] for p in v) - min(p[0] for p in v),
                               max(p[1] for p in v) - min(p[1] for p in v),
                               max(p[2] for p in v) - min(p[2] for p in v)),
            }
            for label, v in sorted(groups.items())
        },
        "note": ("bbox extent is a THREE-DIMENSIONAL extent, not a pathwise "
                 "synaptic span; contact ordering along the nerve is NOT "
                 "established"),
    }


# --- known-quantity provenance ledger ----------------------------------------

#: Literature context recorded so it cannot be mistaken for a measurement
#: produced by this module. These are PASSIVE PARAMETERS this module does not
#: use and does not derive.
PASSIVE_PARAMETER_CONTEXT: Tuple[ProvenanceQuantity, ...] = (
    ProvenanceQuantity(
        name="MN5 whole-cell capacitance (Fayyazuddin et al. 2006, n=22)",
        value="43 +/- 2 pF", units="pF",
        evidence=EvidenceClass.NATIVE_EXPERIMENTAL_MEASUREMENT,
        source="Fayyazuddin et al. 2006 PLoS Biol 4(3):e63, PMC1382016",
        note="Somatic patch, compensation-derived, access resistance "
             "generally kept below 20 MOhm.",
    ),
    ProvenanceQuantity(
        name="MN5 whole-cell capacitance (Ryglewski et al. 2010)",
        value="127 +/- 16 pF", units="pF",
        evidence=EvidenceClass.NATIVE_EXPERIMENTAL_MEASUREMENT,
        source="Ryglewski et al. 2010 J Neurosci 30:4087, PMC2804405",
        note="Conflicts with the 43 pF value by ~3x; DISCREPANCY UNRESOLVED.",
    ),
    ProvenanceQuantity(
        name="MN5 whole-cell input resistance (Fayyazuddin et al. 2006, n=22)",
        value="102 +/- 12 MOhm", units="MOhm",
        evidence=EvidenceClass.NATIVE_EXPERIMENTAL_MEASUREMENT,
        source="Fayyazuddin et al. 2006 PLoS Biol 4(3):e63, PMC1382016",
    ),
    ProvenanceQuantity(
        name="specific membrane capacitance (adopted default)",
        value=1.15, units="uF/cm^2",
        evidence=EvidenceClass.LITERATURE_DERIVED_PASSIVE_PARAMETER,
        source="Ryglewski & Duch 2009 J Neurophysiol 102:3673-3688; cited to "
               "Meseke et al. 2009 (Manduca sexta)",
        note="'values commonly applied for vertebrate and invertebrate "
             "neurons' -- NOT measured in MN5.",
    ),
    ProvenanceQuantity(
        name="axial resistivity (adopted default)",
        value=90.0, units="ohm.cm",
        evidence=EvidenceClass.LITERATURE_DERIVED_PASSIVE_PARAMETER,
        source="Ryglewski & Duch 2009 J Neurophysiol 102:3673-3688",
        note="NOT measured in MN5; no independent constraint exists.",
    ),
    ProvenanceQuantity(
        name="passive leak conductance density (adopted default)",
        value=1.667e-4, units="S/cm^2",
        evidence=EvidenceClass.LITERATURE_DERIVED_PASSIVE_PARAMETER,
        source="Ryglewski & Duch 2009 J Neurophysiol 102:3673-3688",
        note="Inconsistent with MN5 Rin = 102 MOhm at 13,000 um^2.",
    ),
    ProvenanceQuantity(
        name="Augustin g_pas",
        value=30e-6, units="S/cm^2",
        evidence=EvidenceClass.MODEL_ASSUMPTION,
        source="Augustin et al. 2019 ModelDB 245415 gfpn.py line 56",
        note="Explicitly assigned in the ModelDB script; not an MN5 "
             "measurement.",
    ),
    ProvenanceQuantity(
        name="Augustin E_pas",
        value=-85.0, units="mV",
        evidence=EvidenceClass.MODEL_ASSUMPTION,
        source="Augustin et al. 2019 ModelDB 245415 gfpn.py line 57",
        note="Explicitly assigned; repo cites Gunay et al. 2015.",
    ),
    ProvenanceQuantity(
        name="Augustin Cm and Ra",
        value="1.0 uF/cm^2 ; 35.4 ohm.cm",
        units="uF/cm^2 ; ohm.cm",
        evidence=EvidenceClass.MODEL_ASSUMPTION,
        source="NEURON defaults; NOT assigned anywhere in gfpn.py",
        note="Never set by the ModelDB script.",
    ),
)



# --- MaleCNS .ngmesh surface mesh (binary) ---------------------------------
#
# FORMAT, reverse-engineered from the official artefacts and verified on both
# MN5 meshes. There is NO magic number and NO version field; the layout is
# fully determined and every byte is accounted for:
#
#   offset 0                 uint32  little-endian   vertex_count N
#   offset 4                 float32 little-endian   N x (x, y, z) vertices
#   offset 4 + 12*N          uint32  little-endian   3*F triangle indices
#
# There is NO face-count field: F is implied by the file size, and the file is
# rejected unless 4 + 12*N + 12*F reproduces the exact size.
#
# Evidence (see validate_male_ngmesh / the checkpoint report):
#   * size % 12 == 4 for both meshes, so a 4-byte header is forced
#   * the leading uint32 LE is 687842 / 726682, and (size - 4) % 12 == 0
#   * every triangle index lies in [0, N-1]; max index is exactly N-1
#   * 4 + 12*N + 12*F == file size exactly, for both meshes
#   * the coordinate magnitudes are nanometre-scale, and reproduce the SWC
#     bounding box once multiplied by 8 (see MESH_TO_SWC_SCALE)
#
# Coordinates are RAW NANOMETRES in the Male CNS EM coordinate space. The
# non-mirrored MaleCNS SWCs are in 8 nm voxel units, so registration is
# swc_voxel * 8 = mesh_nm. This was resolved from the official download
# documentation and is confirmed numerically by check_male_mesh_matches_swc().

#: swc_voxel * MESH_TO_SWC_SCALE == mesh_nanometres
MESH_TO_SWC_SCALE = 8.0
MESH_COORDINATE_UNIT = "nm"
MESH_COORDINATE_SYSTEM = "Male CNS EM coordinate space"
SWC_COORDINATE_UNIT = "8 nm voxel units"

MESH_HEADER_BYTES = 4
MESH_VERTEX_DTYPE = "float32"
MESH_INDEX_DTYPE = "uint32"
MESH_BYTES_PER_VERTEX = 12
MESH_BYTES_PER_FACE = 12


class MaleCNSMeshFormatError(Exception):
    """The .ngmesh file does not match the verified MaleCNS layout."""


@dataclass(frozen=True)
class MaleCNSMesh:
    """A parsed MaleCNS single-resolution surface mesh.

    Geometry only. No electrical quantity is derived, implied or permitted
    from this object; see :data:`BIOLOGICAL_TRANSFER_STATUS`.
    """

    body_id: int
    path: str
    file_size_bytes: int
    sha256: str
    vertex_count: int
    face_count: int
    coordinate_unit: str = MESH_COORDINATE_UNIT
    coordinate_system: str = MESH_COORDINATE_SYSTEM
    endianness: str = "little"
    header_bytes: int = MESH_HEADER_BYTES

    def read_vertices(self) -> List[Tuple[float, float, float]]:
        """Return (N, 3) float32 vertices, raw, in nanometres."""
        if self.file_size_bytes % 4:
            raise MaleCNSMeshFormatError(
                f"body {self.body_id}: size {self.file_size_bytes} is not a "
                f"multiple of 4; cannot be a float32/uint32 mesh")
        import array

        with open(self.path, "rb") as handle:
            handle.seek(MESH_HEADER_BYTES)
            raw = handle.read(MESH_BYTES_PER_VERTEX * self.vertex_count)
        if len(raw) != MESH_BYTES_PER_VERTEX * self.vertex_count:
            raise MaleCNSMeshFormatError(
                f"body {self.body_id}: truncated vertex section "
                f"({len(raw)} of {MESH_BYTES_PER_VERTEX * self.vertex_count} "
                f"bytes)")
        flat = array.array("f")
        flat.frombytes(raw)
        if flat.itemsize != 4:
            raise MaleCNSMeshFormatError(
                f"platform float32 item size is {flat.itemsize}, expected 4")
        return [tuple(flat[i * 3:(i * 3) + 3]) for i in range(self.vertex_count)]

    def read_faces(self) -> List[Tuple[int, int, int]]:
        """Return (F, 3) uint32 triangle indices, validated against N."""
        import array

        count = self.face_count * 3
        with open(self.path, "rb") as handle:
            handle.seek(MESH_HEADER_BYTES
                        + MESH_BYTES_PER_VERTEX * self.vertex_count)
            raw = handle.read(MESH_BYTES_PER_FACE * self.face_count)
        if len(raw) != MESH_BYTES_PER_FACE * self.face_count:
            raise MaleCNSMeshFormatError(
                f"body {self.body_id}: truncated face section "
                f"({len(raw)} of {MESH_BYTES_PER_FACE * self.face_count} "
                f"bytes)")
        flat = array.array("I")
        flat.frombytes(raw)
        if flat.itemsize != 4:
            raise MaleCNSMeshFormatError(
                f"platform uint32 item size is {flat.itemsize}, expected 4")
        lo, hi = min(flat), max(flat)
        if lo < 0 or hi >= self.vertex_count:
            raise MaleCNSMeshFormatError(
                f"body {self.body_id}: face index out of range "
                f"[{lo}, {hi}] for {self.vertex_count} vertices")
        return [tuple(flat[i * 3:(i * 3) + 3]) for i in range(self.face_count)]

    def coordinate_ranges(self) -> Dict[str, Tuple[float, float]]:
        """Per-axis min/max of the raw vertex coordinates, in nanometres."""
        verts = self.read_vertices()
        out = {}
        for axis, name in enumerate(("x", "y", "z")):
            vals = [v[axis] for v in verts]
            out[name] = (min(vals), max(vals))
        return out


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_male_ngmesh(path: str, body_id: int) -> MaleCNSMesh:
    """Parse a MaleCNS ``.ngmesh`` and validate the full byte budget.

    Raises :class:`MaleCNSMeshFormatError` for any deviation. Nothing is
    guessed, padded, truncated or reinterpreted.
    """
    import struct

    if not os.path.exists(path):
        raise MaleCNSMeshFormatError(f"mesh not found: {path}")
    size = os.path.getsize(path)
    if size <= MESH_HEADER_BYTES:
        raise MaleCNSMeshFormatError(
            f"{path}: {size} bytes is too small to contain a header")
    if (size - MESH_HEADER_BYTES) % MESH_BYTES_PER_VERTEX != 0:
        raise MaleCNSMeshFormatError(
            f"{path}: size {size} is not consistent with a "
            f"{MESH_HEADER_BYTES}-byte header plus 12-byte records "
            f"(remainder {(size - MESH_HEADER_BYTES) % MESH_BYTES_PER_VERTEX})")
    with open(path, "rb") as handle:
        header = handle.read(MESH_HEADER_BYTES)
    vertex_count = struct.unpack("<I", header)[0]
    if vertex_count <= 0:
        raise MaleCNSMeshFormatError(
            f"{path}: vertex_count is {vertex_count}, must be positive")
    remainder = size - MESH_HEADER_BYTES - MESH_BYTES_PER_VERTEX * vertex_count
    if remainder <= 0 or remainder % MESH_BYTES_PER_FACE != 0:
        raise MaleCNSMeshFormatError(
            f"{path}: face section of {remainder} bytes is not a positive "
            f"multiple of {MESH_BYTES_PER_FACE}")
    face_count = remainder // MESH_BYTES_PER_FACE
    mesh = MaleCNSMesh(
        body_id=body_id, path=path, file_size_bytes=size,
        sha256=sha256_of(path), vertex_count=vertex_count, face_count=face_count,
    )
    # Full byte-budget and index validation.
    consumed = (MESH_HEADER_BYTES + MESH_BYTES_PER_VERTEX * vertex_count
                + MESH_BYTES_PER_FACE * face_count)
    if consumed != size:
        raise MaleCNSMeshFormatError(
            f"{path}: consumed {consumed} bytes != size {size}")
    mesh.read_faces()
    return mesh


def check_male_mesh_matches_swc(mesh: MaleCNSMesh, swc_xyz: Tuple[float, ...],
                                tolerance_frac: float = 0.10) -> ProvenanceQuantity:
    """Confirm a mesh and a SWC agree after the documented x8 registration.

    ``swc_xyz`` is a SWC bounding box in 8 nm voxel units. The mesh box, in
    nanometres, must contain the SWC box scaled by 8. This is the numeric
    confirmation of :data:`MESH_TO_SWC_SCALE`.
    """
    ranges = mesh.coordinate_ranges()
    lo = [ranges[n][0] for n in ("x", "y", "z")]
    hi = [ranges[n][1] for n in ("x", "y", "z")]
    scaled_lo = [swc_xyz[i] * MESH_TO_SWC_SCALE for i in range(3)]
    scaled_hi = [swc_xyz[i + 3] * MESH_TO_SWC_SCALE for i in range(3)]
    inside = []
    for i in range(3):
        span = max(hi[i] - lo[i], 1e-9)
        inside.append(
            lo[i] - tolerance_frac * span <= scaled_lo[i]
            and scaled_hi[i] <= hi[i] + tolerance_frac * span)
    if not all(inside):
        raise MaleCNSMeshFormatError(
            f"body {mesh.body_id}: SWC box x{MESH_TO_SWC_SCALE:g} "
            f"{[round(v) for v in scaled_lo]}..{[round(v) for v in scaled_hi]} "
            f"nm does not sit inside the mesh box "
            f"{[round(v) for v in lo]}..{[round(v) for v in hi]} nm")
    return ProvenanceQuantity(
        name=f"body {mesh.body_id} mesh/SWC registration",
        value=f"swc x {MESH_TO_SWC_SCALE:g} = mesh nm",
        units="nm",
        evidence=EvidenceClass.ANATOMICAL_MEASUREMENT,
        source=f"{DATASET_NAME}:{DATASET_VERSION} .ngmesh + SWC",
        note=("Numeric confirmation of the documented coordinate convention; "
              "geometric only and carries no electrical meaning."),
    )


def biological_transfer_status() -> str:
    """The standing scientific status. Infrastructure must not change it."""
    return "NOT AUTHORIZED"


def scope_note() -> str:
    return (
        "3.0D-8P MaleCNS ingestion, geometry and provenance infrastructure. "
        "Establishes and preserves the anatomy of the PSI -> MN5 / DLMn a,b "
        "connection with full provenance: four verified body identities, 43 "
        "individually resolved EM contacts, an explicitly validated 8 nm "
        "coordinate frame, MN5 EM skeleton geometry, purely anatomical "
        "contact-to-root traversal, contact clustering, soma ANNOTATION "
        "records, and a five-class provenance ledger. It computes NO length "
        "constant, electrotonic distance, voltage attenuation, transfer "
        "resistance or local-to-somatic conversion, and it derives no Cm, "
        "Ra, g_pas or E_pas. Requesting any of those raises "
        "BiologicalTransferNotAuthorized. The biological PSI->MN5 transfer "
        "remains NOT AUTHORIZED because MN5 passive parameters are not "
        "uniquely determinable: two whole-cell measurements constrain three "
        "unknowns, no independent Ra constraint exists, the recovered "
        "skeleton has no soma node, and the somatic capacitance is discrepant "
        "by ~3x."
    )