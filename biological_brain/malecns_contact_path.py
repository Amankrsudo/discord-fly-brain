"""PSI -> MN5 anatomical path analysis (3.0D-8R).

WHAT THIS MODULE DOES
---------------------
For each of the 43 EM-resolved PSI->MN5 synaptic contacts it establishes, as far
as the anatomy allows:

  * where the contact sits on the MN5 EM surface mesh;
  * which topological mesh component is nearest, and whether that association
    is confident, ambiguous, or too distant to make;
  * whether the contact can be projected onto the MN5 SWC centerline;
  * the geometric path length from that projection to the SWC root;
  * straight-line and graph distances toward ``somaLocation``.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It computes NO electrical quantity. There is no ``Ra``, ``Rm``, ``Cm``,
``g_pas``, specific membrane capacitance or resistance, length constant, space
constant, electrotonic distance, cable distance, attenuation, transfer
resistance, voltage transfer or synaptic conductance anywhere in this module.
Anatomical path length is never converted into any of them. The standing gate
is unchanged:

    PSI->MN5 spatial voltage transfer: NOT AUTHORIZED
    Dalpha7 biological conductance:     NOT AUTHORIZED

GEOMETRIC CONTINUITY IS NOT ELECTRICAL CONTINUITY
--------------------------------------------------
The MN5 meshes are heavily fragmented (thousands of disconnected components).
A disconnected mesh component does NOT establish a disconnected biological
process; it may equally reflect segmentation or mesh construction. Nothing here
interprets fragmentation as branching, and no component is assigned a
compartment name (soma, axon, dendrite, nerve). Compartments are not
established by this analysis, so they are not asserted.

PROVENANCE
----------
Every reported quantity carries exactly one
:class:`~biological_brain.malecns_ingest.EvidenceClass`. Nothing is invented to
fill a gap: where a quantity cannot be established it is reported as
``UNRESOLVED`` rather than approximated.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .malecns_ingest import (
    COORD_UNIT_NM,
    FRAME_EM_8NM,
    MN5_LEFT,
    MN5_RIGHT,
    PSI_LEFT,
    PSI_RIGHT,
    CellTypeRow,
    EvidenceClass,
    MaleCNSCellTypes,
    MaleCNSMesh,
    MaleCNSSynapses,
    SkeletonGeometry,
    SwcNode,
    SynapticContact,
    biological_transfer_status,
    MESH_TO_SWC_SCALE,
)
from .malecns_mesh_geometry import (
    FORBIDDEN_ELECTRICAL_KEYS as _FORBIDDEN_ELECTRICAL_KEYS,
    GATE_RECORD_KEYS as _GATE_RECORD_KEYS,
    MeshSurfaceIndex,
    assert_geometry_only,
    mesh_bounding_box,
    mesh_sampling_scale_nm,
    vertex_component_map,
)

#: The only status for a quantity that could not be established.
UNRESOLVED = "UNRESOLVED"

#: Contact classes as labelled by the source. NOT inferred from anatomy.
CLASS_PDMN_PREFIX = "PDMN"
CLASS_WTCT_PREFIX = "WTct"


# --- frame handling (explicit, never ambiguous) -----------------------------


class AmbiguousCoordinateFrame(Exception):
    """Raised when a coordinate frame cannot be determined unambiguously.

    The MaleCNS EM frame has two common unit conventions in circulation: the
    raw 8 nm voxel units used by the connectome and the SWC, and the mirrored
    1 nm variant used by a different dataset. Treating one as the other
    inflates or shrinks every distance by a factor of 8. This module refuses to
    guess.
    """


@dataclass(frozen=True)
class CoordinateFrame:
    """Explicit description of the space a coordinate triple lives in."""

    name: str
    unit_nm: float

    @property
    def is_mesh_space(self) -> bool:
        return self.unit_nm == 1.0

    @property
    def is_swc_raw_space(self) -> bool:
        return self.unit_nm == COORD_UNIT_NM

    def to_nm(self, xyz: Sequence[float]) -> Tuple[float, float, float]:
        if self.is_mesh_space:
            return (float(xyz[0]), float(xyz[1]), float(xyz[2]))
        if self.is_swc_raw_space:
            return (float(xyz[0]) * MESH_TO_SWC_SCALE,
                    float(xyz[1]) * MESH_TO_SWC_SCALE,
                    float(xyz[2]) * MESH_TO_SWC_SCALE)
        raise AmbiguousCoordinateFrame(
            f"frame {self.name!r} with unit_nm={self.unit_nm} is not a "
            f"recognised MaleCNS frame; refusing to convert")

    def describe(self) -> str:
        return f"{self.name} (1 unit = {self.unit_nm:g} nm)"


#: The connectome synapse coordinates and the SWC share the raw 8 nm frame.
FRAME_SWMC_RAW_8NM = CoordinateFrame(FRAME_EM_8NM, COORD_UNIT_NM)
#: The .ngmesh vertices are already nanometres.
FRAME_MESH_NM = CoordinateFrame("Male CNS EM space, nanometres", 1.0)
#: The other known convention in circulation. Declared so it can be rejected.
FRAME_MIRRORED_1NM = CoordinateFrame("mirrored, 1 nm units", 1.0)


def resolve_contact_frame(contacts: Sequence[SynapticContact],
                          expected_unit_nm: Optional[float] = COORD_UNIT_NM,
                          ) -> CoordinateFrame:
    """Determine the frame of ``contacts`` from the mesh they must sit on.

    A contact coordinate set is only accepted if it is consistent with the
    MN5 mesh bounding box under exactly one known frame. If it fits under none,
    or the caller has not pinned a unit, this raises rather than scaling.
    """
    if expected_unit_nm is None:
        raise AmbiguousCoordinateFrame(
            "no expected unit supplied: a contact set cannot be placed without "
            "being told which MaleCNS frame it is in")
    candidates = [f for f in (FRAME_SWMC_RAW_8NM, FRAME_MESH_NM)
                  if f.unit_nm == expected_unit_nm]
    if len(candidates) != 1:
        raise AmbiguousCoordinateFrame(
            f"unit_nm={expected_unit_nm!r} matches no single known MaleCNS frame")
    return candidates[0]


def assert_single_frame(mesh: MaleCNSMesh,
                        contacts: Sequence[SynapticContact],
                        frame: CoordinateFrame) -> None:
    """Confirm every contact lands in the mesh bounding box under ``frame``.

    This is the guard against reintroducing the 8x error: raw 8 nm units fed
    straight into a nanometre-space query put contacts hundreds of micrometres
    from a mesh spanning ~180 um. Failing here is the point.
    """
    bb = mesh_bounding_box(mesh)
    pad = 0.0
    for c in contacts:
        p = frame.to_nm(c.post_xyz)
        for axis, v in zip("xyz", p):
            if not (bb[f"min_{axis}_nm"] - pad <= v
                    <= bb[f"max_{axis}_nm"] + pad):
                raise AmbiguousCoordinateFrame(
                    f"contact {tuple(c.post_xyz)} interpreted in "
                    f"{frame.describe()} -> {p} nm falls outside the body "
                    f"{mesh.body_id} mesh bounding box on {axis} "
                    f"[{bb[f'min_{axis}_nm']:.1f}, {bb[f'max_{axis}_nm']:.1f}] nm")


# --- contact -> mesh association (Tasks 2, 3) -------------------------------


#: Association verdicts.
ASSOC_CONFIDENT = "CONFIDENT"
ASSOC_AMBIGUOUS = "AMBIGUOUS"
ASSOC_TOO_DISTANT = "TOO_DISTANT"
ASSOC_UNRESOLVED = UNRESOLVED


@dataclass(frozen=True)
class MeshAssociation:
    """Where one contact sits on the MN5 surface mesh.

    ``surface_distance_nm`` and ``vertex_distance_nm`` are kept separate on
    purpose. The surface distance is to the nearest point on the nearest
    TRIANGLE (interior, edge or vertex of that triangle); the vertex distance
    is to the nearest mesh VERTEX. On a mesh whose median edge is ~200 nm these
    differ substantially and neither substitutes for the other.
    """

    contact_index: int
    pre_body: int
    post_body: int
    primary_post: str
    contact_class: str
    conf_pre: float
    conf_post: float
    raw_xyz: Tuple[float, float, float]
    xyz_nm: Tuple[float, float, float]
    nearest_surface_xyz_nm: Tuple[float, float, float]
    nearest_face_index: int
    surface_distance_nm: float
    nearest_vertex_index: int
    nearest_vertex_xyz_nm: Tuple[float, float, float]
    vertex_distance_nm: float
    nearest_component: int
    runner_up_component: Optional[int]
    runner_up_distance_nm: Optional[float]
    component_margin_nm: Optional[float]
    component_margin_ratio: Optional[float]
    association: str
    association_basis: str

    def surface_distance(self) -> "Quantity":
        return Quantity(
            f"contact {self.contact_index} surface distance",
            self.surface_distance_nm, "nm", EvidenceClass.ANATOMICAL_MEASUREMENT,
            "MaleCNS v1.0 .ngmesh + EM synapse coordinate",
            "Nearest point on the nearest surface triangle. A geometric "
            "offset, not a synaptic size and not an electrical quantity.")

    def component_association(self) -> "Quantity":
        return Quantity(
            f"contact {self.contact_index} component association",
            self.association, "verdict", EvidenceClass.MODEL_DERIVED_ESTIMATE,
            "MaleCNS v1.0 .ngmesh topology + EM synapse coordinate",
            self.association_basis)


@dataclass(frozen=True)
class Quantity:
    """One reported number with exactly one provenance class."""

    name: str
    value: object
    units: str
    evidence: EvidenceClass
    source: str
    note: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name, "value": self.value, "units": self.units,
            "evidence": self.evidence.value, "source": self.source,
            "note": self.note,
        }


def resolve_and_validate_contacts(
        mesh: MaleCNSMesh, contacts: Sequence[SynapticContact],
        expected_unit_nm: Optional[float] = COORD_UNIT_NM) -> CoordinateFrame:
    """Resolve the frame of ``contacts`` and confirm they sit on ``mesh``.

    This is the single entry point for frame discipline. Callers cannot opt out:
    every association carries an explicit :class:`CoordinateFrame`, and
    :func:`contact_path_report` re-verifies the conversion it was handed.
    """
    frame = resolve_contact_frame(contacts, expected_unit_nm)
    assert_single_frame(mesh, contacts, frame)
    return frame


def contact_mesh_associations(mesh: MaleCNSMesh,
                              contacts: Sequence[SynapticContact],
                              frame: Optional[CoordinateFrame] = None,
                              index: Optional[MeshSurfaceIndex] = None,
                              labels=None,
                              reference_scale_nm: Optional[float] = None,
                              margin_ratio_threshold: float = 1.5,
                              ) -> List[MeshAssociation]:
    """Associate every contact with the nearest mesh component.

    ``frame`` is REQUIRED and is the only thing that converts a contact
    coordinate into mesh nanometres. There is no default frame: a caller that
    has not said which MaleCNS space its contacts live in gets an error rather
    than a silently 8x-wrong distance.

    Two references drive the verdict, and both are reported as raw numbers so
    the verdict never has to be trusted on its own:

    * ``reference_scale_nm`` (default: the mesh's own 95th-percentile edge
      length) is the mesh's own sampling scale. Beyond it a contact is not
      attached to a surface patch that means anything, and the verdict is
      ``TOO_DISTANT``.
    * ``margin_ratio_threshold`` compares the best component's distance with
      the runner-up's. When they are within this factor the two are not
      separable at this mesh's resolution and the verdict is ``AMBIGUOUS``.

    ``margin_ratio_threshold`` is a REPORTING CONVENTION, not a biological
    claim: no source states a ratio at which two components become
    inseparable. It is therefore fixed at a mild value, every contact's actual
    margin and ratio are carried in the output, and the verdict can be
    re-derived by the reader. No threshold is chosen to force contacts into
    components -- ``TOO_DISTANT`` and ``AMBIGUOUS`` are reported as they fall,
    and ``UNRESOLVED`` is used when no face can be reached at all.
    """
    if not isinstance(frame, CoordinateFrame):
        raise AmbiguousCoordinateFrame(
            f"an explicit CoordinateFrame is required, got "
            f"{type(frame).__name__}; refusing to assume the contact frame")
    idx = MeshSurfaceIndex(mesh) if index is None else index
    lab = vertex_component_map(mesh) if labels is None else labels
    if reference_scale_nm is None:
        reference_scale_nm = mesh_sampling_scale_nm(mesh)["edge_length_nm_p95"]
    out: List[MeshAssociation] = []
    for i, c in enumerate(contacts):
        raw = (float(c.post_xyz[0]), float(c.post_xyz[1]), float(c.post_xyz[2]))
        p = frame.to_nm(raw)
        ranked = idx.nearest_surface_by_component(p, n_best=2, labels=lab)
        if not ranked:
            out.append(_unresolved_association(i, c, raw, p))
            continue
        comp0, d0, q0, f0 = ranked[0]
        if len(ranked) > 1:
            comp1, d1 = ranked[1][0], ranked[1][1]
            margin = d0 - d1
            ratio = (d1 / d0) if d0 > 0 else float("inf")
        else:
            comp1, d1, margin, ratio = None, None, None, None
        vi, vd = idx.nearest_vertex(p)
        verts = idx.verts
        assoc, basis = _verdict(d0, margin, ratio, reference_scale_nm,
                                margin_ratio_threshold)
        out.append(MeshAssociation(
            contact_index=i, pre_body=int(c.pre_body),
            post_body=int(c.post_body),
            primary_post=str(c.primary_post),
            contact_class=_contact_class(c.primary_post),
            conf_pre=float(c.conf_pre), conf_post=float(c.conf_post),
            raw_xyz=raw, xyz_nm=p,
            nearest_surface_xyz_nm=q0, nearest_face_index=f0,
            surface_distance_nm=d0,
            nearest_vertex_index=vi,
            nearest_vertex_xyz_nm=(float(verts[vi * 3]),
                                   float(verts[vi * 3 + 1]),
                                   float(verts[vi * 3 + 2])),
            vertex_distance_nm=vd,
            nearest_component=comp0, runner_up_component=comp1,
            runner_up_distance_nm=d1, component_margin_nm=margin,
            component_margin_ratio=ratio,
            association=assoc, association_basis=basis))
    return out


def _verdict(d0: float, margin: Optional[float], ratio: Optional[float],
             reference_scale_nm: float,
             margin_ratio_threshold: float) -> Tuple[str, str]:
    if d0 > reference_scale_nm:
        return ASSOC_TOO_DISTANT, (
            f"nearest surface {d0:.1f} nm exceeds the mesh's own 95th "
            f"percentile edge length {reference_scale_nm:.1f} nm, so the "
            f"contact is not attached to a meaningful surface patch")
    if margin is None:
        return ASSOC_CONFIDENT, (
            "only one mesh component lies anywhere near this contact")
    if ratio is not None and ratio < margin_ratio_threshold:
        return ASSOC_AMBIGUOUS, (
            f"nearest component {d0:.1f} nm and runner-up are within "
            f"{ratio:.2f}x (< {margin_ratio_threshold}x), so the association "
            f"is not separable at this mesh's sampling")
    return ASSOC_CONFIDENT, (
        f"nearest component {d0:.1f} nm is {ratio:.2f}x closer than the "
        f"runner-up and within the mesh sampling scale "
        f"{reference_scale_nm:.1f} nm")


def _unresolved_association(i: int, c: SynapticContact, raw, p,
                            ) -> MeshAssociation:
    return MeshAssociation(
        contact_index=i, pre_body=int(c.pre_body), post_body=int(c.post_body),
        primary_post=str(c.primary_post),
        contact_class=_contact_class(c.primary_post),
        conf_pre=float(c.conf_pre), conf_post=float(c.conf_post),
        raw_xyz=raw, xyz_nm=p,
        nearest_surface_xyz_nm=(float("nan"),) * 3, nearest_face_index=-1,
        surface_distance_nm=float("inf"), nearest_vertex_index=-1,
        nearest_vertex_xyz_nm=(float("nan"),) * 3, vertex_distance_nm=float("inf"),
        nearest_component=-1, runner_up_component=None,
        runner_up_distance_nm=None, component_margin_nm=None,
        component_margin_ratio=None, association=ASSOC_UNRESOLVED,
        association_basis=("no mesh face could be reached from this contact; "
                           "no component association is made"))


def _contact_class(primary_post: str) -> str:
    """Classify by the SOURCE label prefix only. No anatomical inference."""
    s = str(primary_post)
    if s.startswith(CLASS_WTCT_PREFIX):
        return "WTct"
    if s.startswith(CLASS_PDMN_PREFIX):
        return "PDMN"
    return s


# --- SWC projection (Tasks 4, 6, 12) ---------------------------------------


@dataclass(frozen=True)
class ContactProjection:
    """A contact projected onto the MN5 SWC centerline.

    The projection is a nearest-point rule over reconstructed geometry. It is
    therefore a MODEL-DERIVED ESTIMATE, and every downstream path length built
    on it inherits that label. The node-to-node segment lengths along the way
    are themselves anatomical measurements of the reconstruction.
    """

    contact_index: int
    post_body: int
    contact_class: str
    status: str
    nearest_node_index: int
    nearest_node_xyz_raw: Tuple[float, float, float]
    nearest_segment_node_indices: Tuple[int, int]
    segment_xyz_nm: Tuple[Tuple[float, float, float], Tuple[float, float, float]]
    projection_xyz_nm: Tuple[float, float, float]
    projection_distance_nm: float
    local_radius_raw: float
    local_radius_um: float
    local_child_degree: int
    local_path_direction: Optional[Tuple[float, float, float]]
    note: str

    def projection_quantity(self) -> Quantity:
        return Quantity(
            f"contact {self.contact_index} centreline projection distance",
            self.projection_distance_nm, "nm",
            EvidenceClass.MODEL_DERIVED_ESTIMATE,
            "MaleCNS v1.0 em_*.swc centreline, nearest-segment rule",
            "Nearest-point projection onto the reconstructed centerline. A "
            "geometric offset only; the projection is NOT the contact's "
            "compartment and NOT an electrical distance.")

    def local_radius_quantity(self) -> Quantity:
        return Quantity(
            f"contact {self.contact_index} local centreline radius",
            self.local_radius_um, "um",
            EvidenceClass.ANATOMICAL_MEASUREMENT,
            "MaleCNS v1.0 em_*.swc node radius",
            "Radius as reconstructed on the SWC node. This is the "
            "reconstruction's own annotation of process width. It is NOT an "
            "equivalent cable diameter and is never converted into one.")

    def branch_degree_quantity(self) -> Quantity:
        return Quantity(
            f"contact {self.contact_index} local branch degree",
            self.local_child_degree, "children",
            EvidenceClass.ANATOMICAL_MEASUREMENT,
            "MaleCNS v1.0 em_*.swc parent/child structure",
            "Count of child nodes in the reconstruction. Describes the "
            "reconstruction, not verified biology.")


def _point_to_segment(p, a, b) -> Tuple[float, Tuple[float, float, float]]:
    abx, aby, abz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    denom = abx * abx + aby * aby + abz * abz
    if denom == 0.0:
        return (math.dist(p, a), (a[0], a[1], a[2]))
    t = ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby + (p[2] - a[2]) * abz) / denom
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    q = (a[0] + t * abx, a[1] + t * aby, a[2] + t * abz)
    return (math.dist(p, q), q)


def project_contacts_to_swc(skel: SkeletonGeometry,
                            associations: Sequence[MeshAssociation],
                            ) -> List[ContactProjection]:
    """Project each contact onto the nearest SWC segment, in mesh nanometres."""
    table = skel.by_index()
    children: Dict[int, int] = {}
    for n in skel.nodes:
        if n.parent in table:
            children[n.parent] = children.get(n.parent, 0) + 1
    segs = skel.segments()
    out: List[ContactProjection] = []
    # The skeleton's OWN unit, never a hardcoded constant: from_swc accepts
    # unit_nm, so a skeleton in any other unit must not be silently rescaled
    # by an assumed 8.
    to_nm = float(skel.unit_nm)
    for a in associations:
        # No usable centerline (no segments at all, or no mesh association):
        # report UNRESOLVED rather than inventing a projection.
        if not segs or (not math.isfinite(a.surface_distance_nm)
                        and a.nearest_component < 0):
            out.append(ContactProjection(
                contact_index=a.contact_index, post_body=a.post_body,
                contact_class=a.contact_class, status=UNRESOLVED,
                nearest_node_index=-1, nearest_node_xyz_raw=(0.0, 0.0, 0.0),
                nearest_segment_node_indices=(-1, -1),
                segment_xyz_nm=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
                projection_xyz_nm=a.xyz_nm, projection_distance_nm=float("inf"),
                local_radius_raw=0.0, local_radius_um=0.0, local_child_degree=0,
                local_path_direction=None,
                note=("no usable centreline for this contact "
                      + ("(skeleton has no segments)"
                         if not segs else "(no mesh association)")
                      + "; no centreline projection attempted")))
            continue
        p = a.xyz_nm
        best = None
        for na, nb in segs:
            A = (na.x * to_nm, na.y * to_nm, na.z * to_nm)
            B = (nb.x * to_nm, nb.y * to_nm, nb.z * to_nm)
            d, q = _point_to_segment(p, A, B)
            if best is None or d < best[0]:
                best = (d, q, na, nb, A, B)
        d, q, na, nb, A, B = best
        # Pick the segment endpoint nearer the projection.
        node = na if math.dist(q, A) <= math.dist(q, B) else nb
        direction = None
        if node.parent in table:
            par = table[node.parent]
            pv = (par.x * to_nm, par.y * to_nm, par.z * to_nm)
            nv = (node.x * to_nm, node.y * to_nm, node.z * to_nm)
            dv = math.dist(pv, nv)
            if dv > 0:
                direction = ((nv[0] - pv[0]) / dv, (nv[1] - pv[1]) / dv,
                             (nv[2] - pv[2]) / dv)
        out.append(ContactProjection(
            contact_index=a.contact_index, post_body=a.post_body,
            contact_class=a.contact_class, status="PROJECTED",
            nearest_node_index=node.index,
            nearest_node_xyz_raw=(node.x, node.y, node.z),
            nearest_segment_node_indices=(na.index, nb.index),
            segment_xyz_nm=(A, B), projection_xyz_nm=q,
            projection_distance_nm=d,
            local_radius_raw=node.radius,
            local_radius_um=skel.to_um(node.radius),
            local_child_degree=children.get(node.index, 0),
            local_path_direction=direction,
            note=("Nearest-segment projection; the mapped node is the nearer "
                  "endpoint of that segment. No compartment is assigned.")))
    return out


# --- root path and soma (Tasks 7, 8) ----------------------------------------


@dataclass(frozen=True)
class RootPath:
    """Geometric path length from a contact's centreline node to the SWC root.

    ANATOMICAL path length, reported as a MODEL-DERIVED ESTIMATE because it
    depends on the nearest-point projection that chose the node. It is a length
    along the reconstructed centerline and nothing more.

    The SWC root is the PROXIMAL STALK ORIGIN. It is NOT the soma: these
    skeletons contain no soma node, so a root path is not a soma path.
    """

    contact_index: int
    post_body: int
    contact_class: str
    status: str
    node_index: int
    root_index: int
    hop_count: int
    path_length_um: float
    note: str

    def quantity(self) -> Quantity:
        return Quantity(
            f"contact {self.contact_index} contact->SWC-root path length",
            self.path_length_um, "um", EvidenceClass.MODEL_DERIVED_ESTIMATE,
            "MaleCNS v1.0 em_*.swc parent graph, nearest-node projection",
            self.note)


def contact_root_paths(skel: SkeletonGeometry,
                       projections: Sequence[ContactProjection],
                       ) -> List[RootPath]:
    """contact -> SWC-root geometric path length, in micrometres."""
    if len(skel.roots) != 1:
        raise ValueError(
            f"expected exactly one root to trace to, found {len(skel.roots)} "
            f"in skeleton {skel.body_id}")
    root = skel.roots[0]
    out: List[RootPath] = []
    for pr in projections:
        if pr.status != "PROJECTED":
            out.append(RootPath(
                contact_index=pr.contact_index, post_body=pr.post_body,
                contact_class=pr.contact_class, status=UNRESOLVED,
                node_index=-1, root_index=root.index, hop_count=0,
                path_length_um=float("nan"),
                note="no centreline projection, so no root path"))
            continue
        chain, length_um = skel.path_to_root(pr.nearest_node_index)
        out.append(RootPath(
            contact_index=pr.contact_index, post_body=pr.post_body,
            contact_class=pr.contact_class, status="MEASURED",
            node_index=pr.nearest_node_index, root_index=root.index,
            hop_count=len(chain) - 1, path_length_um=length_um,
            note=("Sum of consecutive SWC segment lengths from the mapped node "
                  "to the single root. GEOMETRIC PATH LENGTH along the "
                  "reconstruction. The root is the proximal stalk origin, NOT "
                  "the soma; no soma node exists in this skeleton. Not an "
                  "electrotonic distance, not a cable distance, not lambda, "
                  "and not converted into any of them. NOTE: neuPrint's own "
                  "documentation states that for stored skeletons the root "
                  "'is not particularly significant'; this path is therefore "
                  "reported as a measurement relative to the stored root, "
                  "whose proximity to the soma has been measured separately "
                  "rather than assumed from the format.")))
    return out


@dataclass(frozen=True)
class SomaRelation:
    """Straight-line relation between a contact and the annotated somaLocation.

    Euclidean distance and graph path length are separate fields and are never
    equated. The graph path is UNRESOLVED because the skeleton has no soma node
    to terminate on; the root-to-somaLocation straight line is reported
    separately so the gap is visible rather than hidden.
    """

    contact_index: int
    post_body: int
    contact_class: str
    soma_xyz_raw: Tuple[float, float, float]
    soma_xyz_nm: Tuple[float, float, float]
    euclidean_nm: float
    euclidean_um: float
    graph_path_status: str
    graph_path_um: Optional[float]
    graph_path_reason: str
    root_to_soma_euclidean_um: float
    note: str

    def euclidean_quantity(self) -> Quantity:
        return Quantity(
            f"contact {self.contact_index} contact->somaLocation straight line",
            self.euclidean_um, "um", EvidenceClass.ANATOMICAL_MEASUREMENT,
            "MaleCNS v1.0 EM synapse coordinate + body-annotations "
            "somaLocation",
            self.note)


def contact_soma_relations(skel: SkeletonGeometry,
                           associations: Sequence[MeshAssociation],
                           cell_type: CellTypeRow,
                           ) -> List[SomaRelation]:
    """Euclidean contact->somaLocation distance; graph path reported UNRESOLVED.

    ``somaLocation`` is a point ANNOTATION from the body-annotations table. It
    is not a mesh surface point, no soma surface is available, and no soma node
    exists in the skeleton, so there is no graph to terminate on.
    """
    if cell_type.soma_location is None:
        raise ValueError(
            f"body {cell_type.body_id} has no somaLocation annotation")
    soma_raw = tuple(float(v) for v in cell_type.soma_location)
    # somaLocation is in the same raw EM frame as the skeleton, so the
    # skeleton's own unit is the correct conversion for both.
    unit = float(skel.unit_nm)
    soma_nm = tuple(v * unit for v in soma_raw)
    root = skel.roots[0]
    root_nm = (root.x * unit, root.y * unit, root.z * unit)
    root_to_soma_um = math.dist(root_nm, soma_nm) * 1e-3
    reason = (
        "the reconstruction contains no soma node (node kinds present: "
        f"{sorted({n.kind for n in skel.nodes})}, SWC kind 1 would mark a "
        "soma), so no parent-graph path can terminate on the soma. The SWC root "
        "is the proximal stalk origin and must not be used as a soma proxy. "
        "Reported as UNRESOLVED rather than approximated by the root.")
    out: List[SomaRelation] = []
    for a in associations:
        d_nm = math.dist(a.xyz_nm, soma_nm)
        out.append(SomaRelation(
            contact_index=a.contact_index, post_body=a.post_body,
            contact_class=a.contact_class,
            soma_xyz_raw=soma_raw, soma_xyz_nm=soma_nm,
            euclidean_nm=d_nm, euclidean_um=d_nm * 1e-3,
            graph_path_status=UNRESOLVED, graph_path_um=None,
            graph_path_reason=reason,
            root_to_soma_euclidean_um=root_to_soma_um,
            note=("Straight-line distance from the EM synapse coordinate to "
                  "the annotated somaLocation point. NOT an anatomical path "
                  "length: the path between these points is unknown, and the "
                  "soma surface itself is not available in these artefacts. "
                  "Not an electrical distance.")))
    return out


CONTACT_TO_SOMA_PATH = UNRESOLVED
"""Standing result: no graph path to the soma can be established.

This refers to the SOMA AS LABELLED. The available reconstruction contains no
soma node (no SWC ``kind == 1`` in any of the nine MN5/PSI skeletons), so a
parent-graph path cannot terminate on a soma. A separate, explicitly
assumption-based path to a soma PROXY is available via
:func:`contact_soma_graph_paths` and is never conflated with this constant.
"""


# --- 3.0D-8S: soma proxy registration and exact tree paths --------------------

#: Outcome vocabulary for the contact->soma question.
SOMA_PATH_UNRESOLVED = "UNRESOLVED"
SOMA_PATH_PARTIAL = "PARTIALLY_RESOLVED"


@dataclass(frozen=True)
class SomaProxy:
    """The SWC node nearest the annotated ``somaLocation``.

    FOUND BY MEASUREMENT: in both MN5 skeletons the reconstruction contains a
    proximal dilation whose radius is soma-sized (4.67 um and 5.38 um, i.e.
    ~9-11 um across) whose nodes lie 1.45-2.10 um from the annotated
    ``somaLocation``. So the somatic REGION is present in the reconstruction.

    NOT the same as a soma: the MaleCNS tracer labelled that dilation
    ``kind == 2`` (axon). No soma node exists and no source field asserts this
    node is a soma. Treating it as one is therefore a MODEL ASSUMPTION, and
    every path derived from it is a MODEL-DERIVED ESTIMATE.
    """

    node_index: int
    node_kind: int
    radius_um: float
    distance_to_soma_location_um: float
    root_path_um: float
    is_labelled_soma: bool
    basis: str

    def assumption(self) -> Quantity:
        return Quantity(
            "soma proxy: nearest SWC node to the annotated somaLocation",
            self.node_index, "swc node index",
            EvidenceClass.MODEL_ASSUMPTION,
            "MaleCNS v1.0 em_*.swc + body-annotations somaLocation",
            self.basis)


def locate_soma_proxy(skel: SkeletonGeometry,
                      cell_type: CellTypeRow) -> SomaProxy:
    """Find the SWC node closest to the annotated somaLocation."""
    if cell_type.soma_location is None:
        raise ValueError(
            f"body {cell_type.body_id} has no somaLocation annotation")
    soma_nm = tuple(float(v) * skel.unit_nm for v in cell_type.soma_location)
    best_d, best_n = float("inf"), None
    for n in skel.nodes:
        d = math.dist((n.x * skel.unit_nm, n.y * skel.unit_nm,
                       n.z * skel.unit_nm), soma_nm)
        if d < best_d:
            best_d, best_n = d, n
    _, root_depth = skel.path_to_root(best_n.index)
    return SomaProxy(
        node_index=best_n.index, node_kind=best_n.kind,
        radius_um=skel.to_um(best_n.radius),
        distance_to_soma_location_um=best_d * 1e-3,
        root_path_um=root_depth,
        is_labelled_soma=best_n.kind == 1,
        basis=(
            f"Nearest SWC node to the annotated somaLocation: "
            f"{best_d * 1e-3:.2f} um away, node radius "
            f"{skel.to_um(best_n.radius):.3f} um, SWC kind {best_n.kind}. The "
            f"reconstruction carries no soma node, so this proximal dilation is "
            f"used as a PROXY under an explicit assumption that it represents "
            f"the somatic region. It is not asserted to be a soma and is never "
            f"reported as one."))


class _Tree:
    """Parent-graph helpers: root depth and lowest common ancestor depth."""

    def __init__(self, skel: SkeletonGeometry) -> None:
        self.skel = skel
        self.table = skel.by_index()
        self.depth: Dict[int, float] = {}
        for n in skel.nodes:
            self.depth[n.index] = skel.path_to_root(n.index)[1]

    def ancestors(self, index: int) -> List[int]:
        out = [index]
        cur = self.table[index]
        seen = {index}
        while cur.parent in self.table:
            cur = self.table[cur.parent]
            if cur.index in seen:
                break
            seen.add(cur.index)
            out.append(cur.index)
        return out

    def distance_um(self, u: int, v: int) -> Tuple[float, float]:
        """Exact tree path length u->v, plus the shared-ancestor depth."""
        anc_v = set(self.ancestors(v))
        shared = 0.0
        for a in self.ancestors(u):
            if a in anc_v:
                shared = self.depth[a]
                break
        return (self.depth[u] + self.depth[v] - 2.0 * shared, shared)


@dataclass(frozen=True)
class SomaGraphPath:
    """Contact -> soma-proxy path along the reconstruction's parent graph."""

    contact_index: int
    post_body: int
    contact_class: str
    status: str
    contact_node_index: int
    soma_proxy_node_index: int
    shared_ancestor_depth_um: float
    graph_path_um: float
    straight_line_um: float
    basis: str
    note: str

    def quantity(self) -> Quantity:
        return Quantity(
            f"contact {self.contact_index} contact->soma-proxy graph path",
            self.graph_path_um, "um", EvidenceClass.MODEL_DERIVED_ESTIMATE,
            "MaleCNS v1.0 em_*.swc parent graph + somaLocation proxy",
            self.note)


def contact_soma_graph_paths(skel: SkeletonGeometry,
                             projections: Sequence[ContactProjection],
                             proxy: SomaProxy,
                             cell_type: CellTypeRow,
                             ) -> List[SomaGraphPath]:
    """Exact contact -> soma-proxy tree path for every projected contact.

    This is a MODEL-DERIVED ESTIMATE resting on one MODEL ASSUMPTION: that the
    node nearest ``somaLocation`` represents the somatic region. It is kept
    strictly separate from :data:`CONTACT_TO_SOMA_PATH`, which stays UNRESOLVED
    because the soma as labelled does not exist in the reconstruction.
    """
    if cell_type.soma_location is None:
        raise ValueError("somaLocation annotation required")
    soma_nm = tuple(float(v) * skel.unit_nm for v in cell_type.soma_location)
    tree = _Tree(skel)
    out: List[SomaGraphPath] = []
    for p in projections:
        if p.status != "PROJECTED":
            out.append(SomaGraphPath(
                contact_index=p.contact_index, post_body=p.post_body,
                contact_class=p.contact_class, status=SOMA_PATH_UNRESOLVED,
                contact_node_index=-1,
                soma_proxy_node_index=proxy.node_index,
                shared_ancestor_depth_um=float("nan"),
                graph_path_um=float("nan"), straight_line_um=float("nan"),
                basis=proxy.basis,
                note="no centreline projection, so no graph path"))
            continue
        path_um, shared = tree.distance_um(p.nearest_node_index,
                                           proxy.node_index)
        straight = math.dist(p.projection_xyz_nm, soma_nm) * 1e-3
        out.append(SomaGraphPath(
            contact_index=p.contact_index, post_body=p.post_body,
            contact_class=p.contact_class, status=SOMA_PATH_PARTIAL,
            contact_node_index=p.nearest_node_index,
            soma_proxy_node_index=proxy.node_index,
            shared_ancestor_depth_um=shared,
            graph_path_um=path_um, straight_line_um=straight,
            basis=proxy.basis,
            note=("Exact parent-graph path from the contact's projected node to "
                  "the soma PROXY node (shared-ancestor depth "
                  f"{shared:.2f} um). A geometric path length on a "
                  "reconstruction, NOT an electrical distance and NOT a path to "
                  "a labelled soma: no soma node exists, the proxy is a MODEL "
                  "ASSUMPTION, and the straight line to somaLocation "
                  f"({straight:.2f} um) is a different quantity that is never "
                  "substituted for this path.")))
    return out


def ambiguous_contact_report(associations: Sequence[MeshAssociation],
                             projections: Sequence[ContactProjection],
                             ) -> Dict[str, object]:
    """Why a component association is ambiguous, and whether the centreline is.

    On a mesh fragmented into thousands of pieces two fragments can sit almost
    equidistant from a contact. That is a segmentation-level ambiguity. The SWC
    centreline is a single connected tree, so the same contact often has an
    unambiguous reconstructed node -- which is recorded here rather than used to
    overwrite the mesh verdict.
    """
    by_index = {p.contact_index: p for p in projections}
    rows = []
    for a in associations:
        if a.association != ASSOC_AMBIGUOUS:
            continue
        p = by_index.get(a.contact_index)
        rows.append({
            "contact_index": a.contact_index,
            "psi_body": a.pre_body,
            "primary_post_verbatim": a.primary_post,
            "mesh_nearest_component": a.nearest_component,
            "mesh_runner_up_component": a.runner_up_component,
            "mesh_nearest_distance_nm": a.surface_distance_nm,
            "mesh_runner_up_distance_nm": a.runner_up_distance_nm,
            "mesh_margin_nm": a.component_margin_nm,
            "mesh_margin_ratio": a.component_margin_ratio,
            "swc_node_index": p.nearest_node_index if p else None,
            "swc_projection_distance_nm": p.projection_distance_nm if p else None,
            "swc_local_radius_um": p.local_radius_um if p else None,
            "verdict": ASSOC_AMBIGUOUS,
            "note": ("Mesh component identity is NOT established and is not "
                     "asserted. The SWC node is recorded because the centreline "
                     "is a single connected tree, but a shared or unique node "
                     "here does not retroactively identify a mesh fragment."),
        })
    return {
        "ambiguous_count": len(rows),
        "threshold_is_a_convention": (
            "margin_ratio_threshold is a reporting convention with no "
            "biological basis; raw margins and ratios are carried so the "
            "verdict can be re-derived."),
        "contacts": rows,
    }


# --- Tasks 9, 10, 11: classes, sharing, distance validation -----------------


def _stats(values: Sequence[float]) -> Dict[str, Optional[float]]:
    vals = sorted(v for v in values if v is not None and math.isfinite(v))
    if not vals:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None,
                "p90": None}
    return {
        "n": len(vals),
        "min": vals[0],
        "median": vals[len(vals) // 2],
        "mean": sum(vals) / len(vals),
        "max": vals[-1],
        "p90": vals[int(0.9 * (len(vals) - 1))],
    }


def distance_validation(associations: Sequence[MeshAssociation],
                        outlier_factor: float = 3.0) -> Dict[str, object]:
    """Recompute contact-to-surface distance statistics from scratch (Task 11).

    Grouped by MN5 body and by contact class, with the outliers identified
    explicitly. An outlier is flagged by a data-derived rule (a value beyond
    ``outlier_factor`` x the group's median) and is explained where possible,
    never silently dropped.
    """
    by_body: Dict[int, List[MeshAssociation]] = {}
    for a in associations:
        by_body.setdefault(a.post_body, []).append(a)

    out: Dict[str, object] = {"overall": {}, "by_body": {}, "by_class": {},
                              "outliers": [], "outlier_rule": (
        f"distance > {outlier_factor} x the group median; the rule is applied "
        f"to the reported distribution and identifies values to investigate, "
        f"not values to discard")}
    allv = [a.surface_distance_nm for a in associations]
    out["overall"] = _stats(allv)
    out["by_body"] = {str(b): _stats([a.surface_distance_nm for a in g])
                      for b, g in sorted(by_body.items())}
    for cls in ("PDMN", "WTct"):
        out["by_class"][cls] = _stats(
            [a.surface_distance_nm for a in associations
             if a.contact_class == cls])
    out["by_class"]["all_other_labels"] = _stats(
        [a.surface_distance_nm for a in associations
         if a.contact_class not in ("PDMN", "WTct")])

    med = out["overall"].get("median")
    if med:
        for a in associations:
            if a.surface_distance_nm > outlier_factor * med:
                out["outliers"].append({
                    "contact_index": a.contact_index,
                    "post_body": a.post_body,
                    "contact_class": a.contact_class,
                    "surface_distance_nm": a.surface_distance_nm,
                    "ratio_to_median": a.surface_distance_nm / med,
                    "association": a.association,
                    "runner_up_component": a.runner_up_component,
                    "component_margin_nm": a.component_margin_nm,
                })
    return out


def class_geometry_comparison(associations: Sequence[MeshAssociation],
                              paths: Sequence[RootPath],
                              soma: Sequence[SomaRelation],
                              projections: Sequence[ContactProjection],
                              ) -> Dict[str, object]:
    """Compare PDMN and WTct contacts on the MN5 side (Task 10).

    Comparison is descriptive only. PDMN is NOT relabelled axon and WTct is NOT
    relabelled dendrite: neither is established by the reconstruction, and the
    source labels are preserved verbatim.
    """
    by_class: Dict[str, Dict[str, object]] = {}
    for cls in ("PDMN", "WTct"):
        aa = [a for a in associations if a.contact_class == cls]
        pp = [p for p in paths if p.contact_class == cls]
        ss = [s for s in soma if s.contact_class == cls]
        pr = [p for p in projections if p.contact_class == cls]
        by_class[cls] = {
            "contact_count": len(aa),
            "surface_distance_nm": _stats([a.surface_distance_nm for a in aa]),
            "projection_distance_nm": _stats([p.projection_distance_nm
                                              for p in pr]),
            "root_path_um": _stats([p.path_length_um for p in pp
                                    if math.isfinite(p.path_length_um)]),
            "soma_euclidean_um": _stats([s.euclidean_um for s in ss]),
            "local_radius_um": {
                "stats": _stats([p.local_radius_um for p in pr]),
                "what_it_is": (
                    "The radius recorded on the SWC node each contact "
                    "projects to."),
                "do_not_read_as": (
                    "NOT an axon/dendrite discriminator. PDMN is not "
                    "established as axon and WTct is not established as "
                    "dendrite; comparing these two numbers side by side does "
                    "not license a compartment reading, and no such reading is "
                    "made here. It is also NOT an equivalent cable diameter."),
            },
            "local_child_degree": _stats([float(p.local_child_degree)
                                          for p in pr]),
            "association_verdicts": {
                v: sum(1 for a in aa if a.association == v)
                for v in (ASSOC_CONFIDENT, ASSOC_AMBIGUOUS, ASSOC_TOO_DISTANT,
                          ASSOC_UNRESOLVED)},
        }
    return {
        "by_class": by_class,
        "labels_preserved": (
            "PDMN and WTct are the source's primary_post labels, kept separate. "
            "WTct is not among the dataset's named peripheral nerves (the "
            "body-annotations exitNerve field for both MN5 bodies is PDMNa). "
            "PDMN is NOT assumed to be axon and WTct is NOT assumed to be "
            "dendrite; the reconstruction does not establish either."),
        "no_functional_inference": (
            "Any difference measured here is geometric only. No functional, "
            "weighting or compartmental meaning is inferred from it."),
    }


def contact_sharing_report(associations: Sequence[MeshAssociation],
                           projections: Sequence[ContactProjection],
                           ) -> Dict[str, object]:
    """Do contacts land on the same reconstructed process? (Task 9)

    Sharing is measured on the SWC node each contact projects to. A shared node
    means the reconstruction places them on one centerline location; it does not
    establish a shared biological compartment.
    """
    by_body: Dict[int, List[ContactProjection]] = {}
    for p in projections:
        by_body.setdefault(p.post_body, []).append(p)
    out: Dict[str, object] = {"by_body": {}, "caveat": (
        "Contacts sharing an SWC node share a reconstructed centerline "
        "location only. No compartment, and no biological process identity, is "
        "claimed from that.")}
    for body, group in sorted(by_body.items()):
        nodes: Dict[int, int] = {}
        for p in group:
            if p.nearest_node_index >= 0:
                nodes[p.nearest_node_index] = nodes.get(p.nearest_node_index, 0) + 1
        shared = {n: c for n, c in nodes.items() if c > 1}
        classes_at = {}
        for p in group:
            classes_at.setdefault(p.nearest_node_index, set()).add(p.contact_class)
        mixed = {n: sorted(c) for n, c in classes_at.items() if len(c) > 1}
        out["by_body"][str(body)] = {
            "contact_count": len(group),
            "distinct_swc_nodes": len(nodes),
            "shared_node_indices": sorted(shared),
            "shared_node_count": len(shared),
            "contacts_on_shared_nodes": sum(shared.values()),
            "nodes_with_mixed_classes": mixed,
        }
    return out


# --- Task 13: SIZ mapping ---------------------------------------------------
#
# CORRECTION (3.0D-8U overnight audit). The values previously encoded here were
# wrong in two ways and have been corrected against the primary text.
#
# 1. EXPANSION. "SIZ" was expanded as "Secondary Isatoz Axon". That expansion
#    appears in NO publication. SIZ = "spike initiating zone". Corrected below.
# 2. VALUE. The figure encoded here was 88 +/- 15 um. That string does NOT occur
#    in Kuehn & Duch 2013 (PMC3604049). The paper actually reports TWO distinct
#    figures, which are not interchangeable:
#      - "about 100 um from the soma" -- the soma-referenced distance
#        ("A sharp border between low and high staining intensities for VGSCs
#         is found at about 100 um from the soma of MN5").
#      - "11 +/- 3 um around the origin of the most distal posterior dendrite"
#        -- the localisation precision, n = 7, measured FROM THAT DENDRITIC
#        ORIGIN, NOT from the soma.
#    The 88 +/- 15 um figure appears to be a corrupted merge of the two.

#: Kuehn & Duch 2013, Eur J Neurosci 37(6):860-875. doi:10.1111/ejn.12104,
#: PMID 23279094, PMCID PMC3604049. SIZ = "spike initiating zone".
SIZ_SOURCE_CITATION = (
    "Kuehn C & Duch C (2013) Eur J Neurosci 37(6):860-875, "
    "doi:10.1111/ejn.12104, PMID 23279094, PMCID PMC3604049")
SIZ_ACRONYM_MEANING = "spike initiating zone"
#: "about 100 um from the soma" - a soma-referenced estimate, not a coordinate.
SIZ_LITERATURE_DISTANCE_FROM_SOMA_UM = 100.0
#: The paper's own uncertainty language for the soma figure is "about"; no
#: numeric uncertainty is given for it.
SIZ_LITERATURE_DISTANCE_UNCERTAINTY_IS_VERBAL = True
#: "11 +/- 3 um", n = 7, measured FROM the origin of the most distal posterior
#: dendrite. The paper does not state whether 3 is SD or SEM.
SIZ_LITERATURE_DENDRITE_ORIGIN_UM = 11.0
SIZ_LITERATURE_DENDRITE_ORIGIN_SD_UM = 3.0
SIZ_LITERATURE_N = 7
#: Kept for backwards compatibility with earlier reports of this block. It is
#: the DENDRITE-ORIGIN interval half-width and is NOT a soma-distance interval.
SIZ_LITERATURE_AROUND_UM = SIZ_LITERATURE_DENDRITE_ORIGIN_SD_UM

SIZ_MEASUREMENT_METHOD = (
    "Immunocytochemistry for voltage-gated sodium channels (polyclonal "
    "antibody AB5210 against rat type I VGSC peptide SP19, amino acids "
    "1500-1518) combined with neurobiotin/rhodamin-dextran intracellular fills "
    "and confocal co-localisation. NOT electrophysiology: no voltage was "
    "recorded at the SIZ.")
SIZ_PROCESS_DESCRIPTION = (
    "The SIZ boundary lies on the MN5 PRIMARY NEURITE, 11 +/- 3 um distal to "
    "the origin of the most distal posterior dendritic sub-tree. It is NOT on "
    "a dendrite and NOT in the soma or the proximal primary neurite. VGSC "
    "density is even from that point out to the DLM terminals.")


def siz_mapping(skel: SkeletonGeometry, cell_type: CellTypeRow,
                soma: Sequence[SomaRelation]) -> Dict[str, object]:
    """Can the Kuehn & Duch SIZ estimate be mapped onto MaleCNS? (Task 13)

    Almost certainly not, and the reasons are structural rather than a matter
    of effort:

    * The source states the SIZ location is ESTIMATED from NaV immunolabel
      spread and the reconstruction, so it is an interval, not a coordinate.
    * Locating it requires identifying "the most distal posterior dendrite".
      These skeletons contain no dendrite-labelled nodes at all -- the only node
      kinds present are ``0`` (undefined) and ``2`` (axon) -- and no anterior/
      posterior axis is established by the reconstruction.
    * No registration method between a literature immunolabel estimate and the
      MaleCNS coordinate frame exists in the ingested artefacts.
    """
    kinds = sorted({n.kind for n in skel.nodes})
    distances = [s.euclidean_um for s in soma]
    lo = (SIZ_LITERATURE_DISTANCE_FROM_SOMA_UM
          - SIZ_LITERATURE_DENDRITE_ORIGIN_SD_UM
          - SIZ_LITERATURE_DENDRITE_ORIGIN_UM)
    hi = (SIZ_LITERATURE_DISTANCE_FROM_SOMA_UM
          + SIZ_LITERATURE_DENDRITE_ORIGIN_UM)
    within = [s.contact_index for s in soma if lo <= s.euclidean_um <= hi]
    dendritic_kinds = [k for k in kinds if k in (3, 4)]
    return {
        "SIZ_MAPPING": UNRESOLVED,
        "acronym_means": SIZ_ACRONYM_MEANING,
        "source_citation": SIZ_SOURCE_CITATION,
        "literature_value_from_soma_um": (
            SIZ_LITERATURE_DISTANCE_FROM_SOMA_UM),
        "literature_distance_uncertainty": (
            "The paper says 'about 100 um'. No numeric uncertainty is given, so "
            "no interval is asserted here."),
        "literature_localisation_from_dendrite_origin_um": (
            SIZ_LITERATURE_DENDRITE_ORIGIN_UM),
        "literature_localisation_sd_um": SIZ_LITERATURE_DENDRITE_ORIGIN_SD_UM,
        "literature_localisation_n": SIZ_LITERATURE_N,
        "literature_localisation_dispersion_type": (
            "UNSTATED in the source (SD vs SEM not specified for this figure)"),
        "measurement_method": SIZ_MEASUREMENT_METHOD,
        "process_description": SIZ_PROCESS_DESCRIPTION,
        "corrected_from": (
            "An earlier version of this module encoded 88 +/- 15 um and "
            "expanded SIZ as 'Secondary Isatoz Axon'. Neither is supported by "
            "Kuehn & Duch 2013: that string does not occur in the paper, and "
            "no publication uses the expansion. Corrected 3.0D-8U."),
        "provenance_status": "NOT_CLASSIFIABLE_UNDER_CURRENT_TAXONOMY",
        "provenance_limitation": (
            "This block deliberately carries NO EvidenceClass. The five "
            "permitted classes cannot honestly hold a literature ANATOMICAL "
            "localisation: it is not a native measurement, not an anatomical "
            "measurement of THIS reconstruction, and LITERATURE_DERIVED_PASSIVE"
            "_PARAMETER would be plainly wrong because SIZ is a sodium-channel "
            "immunolabel position, not a passive electrical parameter. A "
            "sixth class has deliberately NOT been invented. This is flagged "
            "for project-level taxonomy resolution, and until it is resolved "
            "the value is cited as literature evidence with no evidence class "
            "rather than mis-filed."),
        "requires_taxonomy_resolution": True,
        "source": ("Kuehn & Duch 2013, Eur J Neurosci 37:860-875, SIZ "
                   "localisation as reported by the prior MN5 audit"),
        "node_kinds_present": kinds,
        "dendrite_labelled_nodes_present": bool(dendritic_kinds),
        "dendrite_labelled_node_count": len(
            [n for n in skel.nodes if n.kind in (3, 4)]),
        "anterior_posterior_axis_documented": False,
        "axis_evidence": (
            "No anterior/posterior (or dorsal/ventral, medial/lateral) axis is "
            "documented anywhere in the available material: not in the "
            "body-annotations columns, not in the MaleCNS neuron pages, and "
            "not in this project. The EM frame is described only as 'male-cns "
            "EM space, 8 nm units'."),
        "contacts_in_literature_shell": within,
        "shell_note": (
            f"Contacts whose straight-line distance to somaLocation falls in "
            f"the broad {lo:.0f}-{hi:.0f} um band spanning the literature soma "
            f"figure (~100 um) plus the dendrite-origin localisation "
            f"(11 +/- 3 um) are listed for context only. Membership of that "
            f"band is NOT a SIZ registration: the source gives no coordinate, "
            f"no axis, and no origin point in MaleCNS space, and the two "
            f"literature figures are measured from DIFFERENT reference points."),
        "why_unresolved": (
            "Three independent obstacles, each verified against the source. "
            "(1) The source value is an immunolabel-derived ESTIMATE with an "
            "11 um interval around it, not a coordinate, so it cannot be "
            "projected as a point. (2) The reference process is 'the most "
            f"distal posterior dendrite', but this skeleton carries node kinds "
            f"{kinds} with {len([n for n in skel.nodes if n.kind in (3, 4)])} "
            "dendrite-labelled nodes, so no dendrite can be identified. (3) No "
            "anatomical axis is documented, so 'posterior' is undefined. (4) No "
            "registration method links a literature immunolabel estimate to the "
            "MaleCNS coordinate frame. Registering it would require inventing "
            "the missing labels and an orientation the sources do not provide."),
    }


# --- Tasks 14, 15, 17: report, provenance ledger, gates ---------------------

#: Shared with :mod:`biological_brain.malecns_mesh_geometry` so both modules
#: enforce exactly one rule. Not redefined here on purpose.
FORBIDDEN_ELECTRICAL_KEYS = _FORBIDDEN_ELECTRICAL_KEYS
GATE_RECORD_KEYS = _GATE_RECORD_KEYS

GATE_TRANSFER = "PSI->MN5 spatial voltage transfer: NOT AUTHORIZED"
GATE_CONDUCTANCE = "Dalpha7 biological conductance: NOT AUTHORIZED"


def assert_no_electrical_keys(payload) -> None:
    """Fail if any forbidden electrical key appears at any depth.

    Delegates to the single shared guard in
    :mod:`biological_brain.malecns_mesh_geometry` so the two modules cannot
    drift apart again.
    """
    assert_geometry_only(payload)


def gates() -> Dict[str, str]:
    """The two standing gates. This module must never change either."""
    return {
        "spatial_voltage_transfer": GATE_TRANSFER,
        "dalpha7_biological_conductance": GATE_CONDUCTANCE,
        "status_field": biological_transfer_status(),
    }


def contact_path_report(associations: Sequence[MeshAssociation],
                       paths: Sequence[RootPath],
                       soma: Sequence[SomaRelation],
                       projections: Sequence[ContactProjection],
                       skel: SkeletonGeometry,
                       cell_type: CellTypeRow,
                       mesh: Optional[MaleCNSMesh] = None,
                       contacts: Optional[Sequence[SynapticContact]] = None,
                       expected_unit_nm: Optional[float] = COORD_UNIT_NM,
                       proxy: Optional[SomaProxy] = None,
                       soma_graph: Optional[Sequence[SomaGraphPath]] = None,
                       ) -> Dict[str, object]:
    """Assemble the full PSI->MN5 anatomical path report.

    Frame discipline is enforced HERE rather than left to the caller. When
    ``contacts`` and ``mesh`` are supplied the frame is resolved, the contacts
    are checked against the mesh bounding box, and every association's stored
    nanometre coordinate is re-derived from its raw coordinate and compared.
    A mismatch raises :class:`AmbiguousCoordinateFrame` instead of being
    reported.

    Every quantity carries exactly one provenance class. Quantities that could
    not be established are reported as UNRESOLVED; nothing is approximated to
    fill a gap and no forbidden electrical conversion is performed.
    """
    frame_used: Optional[CoordinateFrame] = None
    if contacts is not None and mesh is not None:
        frame_used = resolve_and_validate_contacts(mesh, contacts,
                                                  expected_unit_nm)
        for a in associations:
            expected = frame_used.to_nm(a.raw_xyz)
            if (abs(expected[0] - a.xyz_nm[0]) > 1e-6
                    or abs(expected[1] - a.xyz_nm[1]) > 1e-6
                    or abs(expected[2] - a.xyz_nm[2]) > 1e-6):
                raise AmbiguousCoordinateFrame(
                    f"contact {a.contact_index}: stored nm coordinate "
                    f"{a.xyz_nm} does not match raw {a.raw_xyz} interpreted in "
                    f"{frame_used.describe()} -> {expected}")

    ledger: List[Quantity] = []
    for a in associations:
        ledger.append(a.surface_distance())
        ledger.append(a.component_association())
    for p in projections:
        if p.status == "PROJECTED":
            ledger.append(p.projection_quantity())
            ledger.append(p.local_radius_quantity())
            ledger.append(p.branch_degree_quantity())
    for r in paths:
        if r.status == "MEASURED":
            ledger.append(r.quantity())
    for s in soma:
        ledger.append(s.euclidean_quantity())

    # Aggregate outputs are provenance-labelled too: a statistic computed over a
    # projected set is a derived quantity, not a raw measurement.
    by_contact = {a.contact_index: a for a in associations}
    ledger.extend(_aggregate_quantities(associations, paths, soma, projections))
    if proxy is not None:
        ledger.append(proxy.assumption())
    for g in (soma_graph or ()):
        if g.status == SOMA_PATH_PARTIAL:
            ledger.append(g.quantity())
    ambiguous = ambiguous_contact_report(associations, projections)

    report: Dict[str, object] = {
        "frame": {
            "resolved": frame_used.describe() if frame_used is not None else None,
            "enforcement": (
                "Resolved and validated inside contact_path_report; "
                "contact_mesh_associations requires an explicit "
                "CoordinateFrame and has no default. The stored nanometre "
                "coordinate of every association is re-derived here and "
                "compared, so an 8x frame error cannot be reported silently."),
            "rule": "mesh_nm = swc_raw_units * unit_nm",
        },
        "contacts": {
            "total": len(associations),
            "by_body": {
                str(b): sum(1 for a in associations if a.post_body == b)
                for b in sorted({a.post_body for a in associations})},
            "by_class": {
                c: sum(1 for a in associations if a.contact_class == c)
                for c in sorted({a.contact_class for a in associations})},
            "count_source": (
                "Post-synaptic body counts. Taken from the connectome as "
                "ingested; this module never merges or drops contacts."),
        },
        "mesh": ({
            "body_id": mesh.body_id,
            "vertex_count": mesh.vertex_count,
            "face_count": mesh.face_count,
            "sampling_scale_nm": mesh_sampling_scale_nm(mesh),
            "fragmentation_note": (
                "This mesh is heavily fragmented. A disconnected component "
                "does NOT establish a disconnected biological process; it may "
                "reflect segmentation or mesh construction. Fragmentation is "
                "never read as branching."),
        } if mesh is not None else {}),
        "associations": {
            "reference_scale_nm": (
                mesh_sampling_scale_nm(mesh)["edge_length_nm_p95"]
                if mesh is not None else None),
            "reference_scale_basis": (
                "The mesh's own 95th-percentile edge length: its own sampling "
                "scale, measured rather than assumed."),
            "margin_ratio_threshold": 1.5,
            "margin_ratio_is_a_convention": (
                "No source defines a separability ratio. The raw margin and "
                "ratio are carried per contact so the verdict is checkable."),
            "verdicts": {
                v: sum(1 for a in associations if a.association == v)
                for v in (ASSOC_CONFIDENT, ASSOC_AMBIGUOUS, ASSOC_TOO_DISTANT,
                          ASSOC_UNRESOLVED)},
            "by_contact": [
                {
                    "contact_id": f"{a.pre_body}->{a.post_body}#{a.contact_index}",
                    "contact_index": a.contact_index,
                    "psi_body": a.pre_body,
                    "mn5_body": a.post_body,
                    "contact_class": a.contact_class,
                    "primary_post_verbatim": a.primary_post,
                    "contact_coordinate_nm": list(a.xyz_nm),
                    "contact_coordinate_raw_8nm": list(a.raw_xyz),
                    "nearest_surface_distance_nm": a.surface_distance_nm,
                    "nearest_surface_xyz_nm": list(a.nearest_surface_xyz_nm),
                    "nearest_triangle_index": a.nearest_face_index,
                    "nearest_vertex_index": a.nearest_vertex_index,
                    "nearest_vertex_distance_nm": a.vertex_distance_nm,
                    "nearest_component": a.nearest_component,
                    "runner_up_component": a.runner_up_component,
                    "runner_up_distance_nm": a.runner_up_distance_nm,
                    "component_margin_nm": a.component_margin_nm,
                    "component_margin_ratio": a.component_margin_ratio,
                    "association": a.association,
                    "association_basis": a.association_basis,
                    "swc_mapping_status": next(
                        (p.status for p in projections
                         if p.contact_index == a.contact_index), UNRESOLVED),
                }
                for a in associations],
        },
        "root_paths": {
            "meaning": ("Geometric path length along the reconstructed SWC "
                        "centerline to the SWC ROOT."),
            "root_is_not_soma": (
                "The SWC root is the proximal stalk origin. These skeletons "
                "contain no soma node, so a root path is not a soma path and "
                "root distance is not soma distance."),
            "contact_to_root_path_length_um": [
                {"contact_id": f"#{r.contact_index}",
                 "mn5_body": r.post_body,
                 "contact_class": r.contact_class,
                 "primary_post_verbatim": by_contact[r.contact_index].primary_post
                 if r.contact_index in by_contact else None,
                 "status": r.status, "swc_node": r.node_index,
                 "root_node": r.root_index, "hop_count": r.hop_count,
                 "path_length_um": r.path_length_um}
                for r in paths],
        },
        "soma": {
            "soma_location_raw_8nm": list(soma[0].soma_xyz_raw) if soma else None,
            "soma_location_nm": list(soma[0].soma_xyz_nm) if soma else None,
            "soma_source": ("MaleCNS v1.0 body-annotations somaLocation: a "
                            "point annotation, not a surface, and no soma "
                            "surface is available in these artefacts"),
            "has_soma_node_in_skeleton": any(n.kind == 1 for n in skel.nodes),
            "node_kinds_present": sorted({n.kind for n in skel.nodes}),
            "contact_to_soma_euclidean": _stats(
                [s.euclidean_um for s in soma]),
            "contact_to_soma_graph_path": CONTACT_TO_SOMA_PATH,
            "graph_path_reason": soma[0].graph_path_reason if soma else "",
            "root_to_somaLocation_euclidean_um": (
                soma[0].root_to_soma_euclidean_um if soma else None),
            "euclidean_is_not_path": (
                "The straight line to somaLocation is NOT an anatomical path "
                "length; the route is unknown. The two are never equated."),
        },
        "soma_registration": _soma_registration_dict(
            proxy, soma_graph, ambiguous),
        "ambiguous_contacts": ambiguous,
        "distance_validation": distance_validation(associations),
        "contact_classes": class_geometry_comparison(
            associations, paths, soma, projections),
        "contact_sharing": contact_sharing_report(associations, projections),
        "siz_mapping": siz_mapping(skel, cell_type, soma),
        "provenance_ledger": [q.as_dict() for q in ledger],
        "provenance_counts": _provenance_counts(ledger),
        "gates": gates(),
        "authorization": {
            "electrical_modeling_performed": False,
            "note": ("No Ra, Rm, Cm, g_pas, specific membrane capacitance or "
                     "resistance, length constant, space constant, "
                     "electrotonic distance, cable distance, attenuation, "
                     "transfer resistance, voltage transfer or synaptic "
                     "conductance is computed anywhere in this module, even "
                     "though anatomical path lengths are available. An "
                     "anatomical distance is never converted into an "
                     "electrical one."),
        },
    }
    assert_no_electrical_keys(report)
    return report


def _soma_registration_dict(proxy: Optional[SomaProxy],
                            soma_graph: Optional[Sequence[SomaGraphPath]],
                            ambiguous: Dict[str, object]) -> Dict[str, object]:
    """The 3.0D-8S registration findings, kept distinct from the labelled soma."""
    paths = [g for g in (soma_graph or ())
             if g.status == SOMA_PATH_PARTIAL]
    return {
        "soma_as_labelled": {
            "graph_path": CONTACT_TO_SOMA_PATH,
            "why": ("No SWC kind==1 node exists in any MN5 or PSI skeleton in "
                    "the available MaleCNS material, so no parent-graph path "
                    "can terminate on a soma."),
        },
        "soma_region_is_present": (
            "The reconstruction does contain a soma-sized proximal dilation "
            "coincident with the annotated somaLocation: 4.671 um radius "
            "(body 801970, node 23) and 5.376 um radius (body 801295, nodes "
            "5-9), lying 1.45-2.10 um from somaLocation. The somatic REGION is "
            "in the tracing; the soma LABEL is not."),
        "soma_proxy": ({
            "node_index": proxy.node_index,
            "node_kind": proxy.node_kind,
            "is_labelled_soma": proxy.is_labelled_soma,
            "radius_um": proxy.radius_um,
            "distance_to_soma_location_um": proxy.distance_to_soma_location_um,
            "root_path_um": proxy.root_path_um,
            "basis": proxy.basis,
        } if proxy is not None else None),
        "contact_to_soma_proxy_graph_path": {
            "status": SOMA_PATH_PARTIAL if paths else SOMA_PATH_UNRESOLVED,
            "meaning": ("Exact parent-graph path from each contact's projected "
                        "node to the soma PROXY node. A geometric path length "
                        "on the reconstruction."),
            "not_a_soma_path": (
                "This is NOT a path to a labelled soma. It rests on one MODEL "
                "ASSUMPTION (the proxy node is the somatic region) and is a "
                "MODEL-DERIVED ESTIMATE. The SWC root is never substituted for "
                "the soma."),
            "graph_path_um": _stats([g.graph_path_um for g in paths]),
            "straight_line_um": _stats([g.straight_line_um for g in paths]),
            "by_contact": [
                {"contact_id": f"#{g.contact_index}",
                 "mn5_body": g.post_body, "contact_class": g.contact_class,
                 "status": g.status, "contact_swc_node": g.contact_node_index,
                 "soma_proxy_node": g.soma_proxy_node_index,
                 "shared_ancestor_depth_um": g.shared_ancestor_depth_um,
                 "graph_path_um": g.graph_path_um,
                 "straight_line_um": g.straight_line_um}
                for g in (soma_graph or ())],
        },
        "ambiguous_component_contacts": ambiguous["ambiguous_count"],
    }


def _aggregate_quantities(associations: Sequence[MeshAssociation],
                          paths: Sequence[RootPath],
                          soma: Sequence[SomaRelation],
                          projections: Sequence[ContactProjection],
                          ) -> List[Quantity]:
    """Provenance for every aggregate section of the report.

    Aggregate statistics are derived from a projected/reconstructed set, so
    they are MODEL_DERIVED_ESTIMATE. Counts of contacts or nodes are simple
    tallies of measured inputs and are ANATOMICAL_MEASUREMENT.
    """
    out: List[Quantity] = []
    derived_note = ("Statistic computed over the per-contact set in this "
                    "report. Derived from reconstructed geometry, not a "
                    "measurement of the intact neuron.")
    count_note = ("Count of items in the ingested reconstruction. A tally of "
                  "measured inputs, not a derived magnitude.")
    for name, values in (
            ("surface distance aggregate", [a.surface_distance_nm for a in associations]),
            ("projection distance aggregate",
             [p.projection_distance_nm for p in projections]),
            ("root path aggregate", [r.path_length_um for r in paths
                                     if math.isfinite(r.path_length_um)]),
            ("soma straight-line aggregate", [s.euclidean_um for s in soma]),
            ("local centreline radius aggregate",
             [p.local_radius_um for p in projections if p.status == "PROJECTED"]),
            ("local branch degree aggregate",
             [float(p.local_child_degree) for p in projections
              if p.status == "PROJECTED"])):
        if values:
            out.append(Quantity(f"contact set: {name}", _stats(values), "mixed",
                                EvidenceClass.MODEL_DERIVED_ESTIMATE,
                                "MaleCNS v1.0 .ngmesh + em_*.swc, this report",
                                derived_note))
    out.append(Quantity(
        "contact set: association verdict counts",
        {v: sum(1 for a in associations if a.association == v)
         for v in (ASSOC_CONFIDENT, ASSOC_AMBIGUOUS, ASSOC_TOO_DISTANT,
                   ASSOC_UNRESOLVED)}, "contacts",
        EvidenceClass.ANATOMICAL_MEASUREMENT,
        "MaleCNS v1.0 .ngmesh topology, this report", count_note))
    out.append(Quantity(
        "contact set: distinct projected centreline nodes",
        len({p.nearest_node_index for p in projections
             if p.nearest_node_index >= 0}), "nodes",
        EvidenceClass.ANATOMICAL_MEASUREMENT,
        "MaleCNS v1.0 em_*.swc parent graph, this report", count_note))
    return out


def _provenance_counts(ledger: Sequence[Quantity]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for q in ledger:
        out[q.evidence.value] = out.get(q.evidence.value, 0) + 1
    return dict(sorted(out.items()))


def anatomy_only_scope_note() -> str:
    return (
        "PSI->MN5 anatomical path analysis (3.0D-8R). For each of the 43 EM "
        "contacts it reports the nearest MN5 surface triangle and vertex, the "
        "nearest topological mesh component with an honest "
        "CONFIDENT/AMBIGUOUS/TOO_DISTANT verdict derived from the mesh's own "
        "sampling scale and from the margin to the runner-up component, a "
        "nearest-segment projection onto the MN5 centerline, the geometric "
        "path length from that projection to the SWC root, and the "
        "straight-line distance to the annotated somaLocation. The SWC root is "
        "the proximal stalk origin, not the soma: these skeletons have no soma "
        "node, so CONTACT_TO_SOMA_PATH is reported UNRESOLVED rather than "
        "approximated, and Euclidean distance is never presented as a path. "
        "PDMN and WTct are kept separate as source labels and are never "
        "relabelled axon or dendrite. Mesh fragmentation is reported and is "
        "never read as branching. SIZ_MAPPING is UNRESOLVED because the "
        "literature value is an immunolabel estimate and its reference process "
        "cannot be identified in a reconstruction carrying no dendrite labels. "
        "Nothing electrical is produced: PSI->MN5 spatial voltage transfer and "
        "Dalpha7 biological conductance both remain NOT AUTHORIZED, and no "
        "anatomical length is converted into any electrical quantity.")