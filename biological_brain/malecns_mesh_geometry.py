"""MaleCNS MN5 surface geometry: area, topology, components (3.0D-8Q).

SCOPE
-----
ANATOMICAL GEOMETRY ONLY. This module measures what the official MaleCNS v1.0
EM surface mesh contains. It deliberately computes nothing electrical: no
length constant, no electrotonic distance, no attenuation, no transfer
resistance, no membrane capacitance, no ``Cm``/``Rm``/``Ra``/``g_pas``.

It consumes the validated parser in :mod:`biological_brain.malecns_ingest`; it
does NOT re-implement or re-validate the binary format.

UNITS
-----
Mesh vertices are RAW NANOMETRES in the Male CNS EM coordinate space (verified
in 8P/8O and cross-checked numerically against the non-mirrored SWC, whose
coordinates are 8 nm voxel units: ``mesh_nm = swc_voxel * 8``). Areas are
therefore computed in nm^2 and any micrometre conversion is explicit at
1e-6 um^2 per nm^2.

NUMERICAL METHOD
----------------
Every triangle is measured twice, by two mathematically independent formulae:

    cross product   area = 0.5 * ||(b-a) x (c-a)||
    Heron           area = sqrt(s(s-l1)(s-l2)(s-l3)) from the three edge lengths

The second never forms a normal, so it exercises a different arithmetic path
entirely. It is numerically fragile for slivers, which is why the cross product
is primary; the maximum absolute and relative discrepancy are reported rather
than assumed. The single-plane shoelace formula is NOT used as a surface-area
check: it measures a triangle's XY projection and equals the 3D area only for a
triangle lying flat in XY. It is reported separately as a silhouette measure.

Everything is chunked so that a mesh with ~1e6 faces never materialises more
than one chunk of coordinates at a time.
"""

from __future__ import annotations

import array
import math
import os
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .malecns_ingest import (
    EvidenceClass,
    MaleCNSMesh,
    MaleCNSMeshFormatError,
    ProvenanceQuantity,
    SkeletonGeometry,
    MESH_TO_SWC_SCALE,
    parse_male_ngmesh,
)

#: Faces processed per chunk. Chosen so a chunk holds well under a few MB.
AREA_CHUNK_FACES = 100_000

#: 1 nm^2 in um^2
NM2_PER_UM2 = 1.0e-6
#: 1 nm in um
NM_PER_UM = 1.0e-3


def _flat_vertices(mesh: MaleCNSMesh) -> array.array:
    """Flat float32 vertex buffer (3*V), read without building Python tuples."""
    raw_n = 3 * mesh.vertex_count
    import struct

    with open(mesh.path, "rb") as h:
        h.seek(mesh.header_bytes)
        raw = h.read(4 * raw_n)
    if len(raw) != 4 * raw_n:
        raise MaleCNSMeshFormatError(
            f"body {mesh.body_id}: truncated vertex buffer")
    buf = array.array("f")
    buf.frombytes(raw)
    if buf.itemsize != 4:
        raise MaleCNSMeshFormatError("platform float32 itemsize != 4")
    return buf


def _flat_faces(mesh: MaleCNSMesh) -> array.array:
    """Flat uint32 face buffer (3*F), validated against the vertex count."""
    import struct

    with open(mesh.path, "rb") as h:
        h.seek(mesh.header_bytes + 12 * mesh.vertex_count)
        raw = h.read(12 * mesh.face_count)
    if len(raw) != 12 * mesh.face_count:
        raise MaleCNSMeshFormatError(
            f"body {mesh.body_id}: truncated face buffer")
    buf = array.array("I")
    buf.frombytes(raw)
    if buf.itemsize != 4:
        raise MaleCNSMeshFormatError("platform uint32 itemsize != 4")
    hi = max(buf)
    if hi >= mesh.vertex_count:
        raise MaleCNSMeshFormatError(
            f"body {mesh.body_id}: face index {hi} >= vertex_count "
            f"{mesh.vertex_count}")
    return buf


# --- 2, 3, 4: area ----------------------------------------------------------


def _triangle_area_cross(verts: Sequence[float], faces: Sequence[int]) -> float:
    """0.5 * ||(b-a) x (c-a)|| for one triangle."""
    ia, ib, ic = faces[0] * 3, faces[1] * 3, faces[2] * 3
    ax, ay, az = verts[ia], verts[ia + 1], verts[ia + 2]
    ux = verts[ib] - ax
    uy = verts[ib + 1] - ay
    uz = verts[ib + 2] - az
    vx = verts[ic] - ax
    vy = verts[ic + 1] - ay
    vz = verts[ic + 2] - az
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    return 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)


def _triangle_area_heron(verts: Sequence[float], faces: Sequence[int]) -> float:
    """Heron's formula from the three edge lengths -- no cross product.

    Mathematically independent of :func:`_triangle_area_cross`: it never forms a
    normal, so it exercises a completely different arithmetic path. It is
    numerically fragile for slivers (a triangle with a near-zero altitude can
    give a slightly negative radicand), which is exactly why the cross product
    is the primary method and this is the check.
    """
    ia, ib, ic = faces[0] * 3, faces[1] * 3, faces[2] * 3
    ax, ay, az = verts[ia], verts[ia + 1], verts[ia + 2]
    bx, by, bz = verts[ib], verts[ib + 1], verts[ib + 2]
    cx, cy, cz = verts[ic], verts[ic + 1], verts[ic + 2]
    la = math.sqrt((bx - cx) ** 2 + (by - cy) ** 2 + (bz - cz) ** 2)
    lb = math.sqrt((cx - ax) ** 2 + (cy - ay) ** 2 + (cz - az) ** 2)
    lc = math.sqrt((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2)
    s = 0.5 * (la + lb + lc)
    radicand = s * (s - la) * (s - lb) * (s - lc)
    if radicand <= 0.0:
        return 0.0
    return math.sqrt(radicand)


def _triangle_projected_area_xy(verts: Sequence[float],
                                faces: Sequence[int]) -> float:
    """Signed-area magnitude of the triangle's projection onto the XY plane.

    This is NOT a surface area. It is the shoelace formula in one plane, and it
    equals the 3D area only for a triangle lying flat in XY. Summing it over a
    closed surface yields a projected silhouette area, so it is reported as its
    own quantity and never as a surface-area cross-check.
    """
    ia, ib, ic = faces[0] * 3, faces[1] * 3, faces[2] * 3
    ax, ay = verts[ia], verts[ia + 1]
    bx, by = verts[ib], verts[ib + 1]
    cx, cy = verts[ic], verts[ic + 1]
    return 0.5 * abs(ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))


#: The two independent surface-area formulae.
AREA_METHODS = ("cross", "heron")


def mesh_surface_area(mesh: MaleCNSMesh, method: str = "cross",
                      chunk: int = AREA_CHUNK_FACES) -> Tuple[float, int]:
    """Total triangle surface area in nm^2, plus the degenerate-face count.

    ``method`` selects the independent formula (``cross`` or ``heron``). Both
    are computed over the same faces; nothing is filtered, smoothed, repaired
    or decimated.
    """
    if method not in AREA_METHODS:
        raise ValueError(f"unknown area method {method!r}")
    fn = _triangle_area_cross if method == "cross" else _triangle_area_heron
    verts = _flat_vertices(mesh)
    faces = _flat_faces(mesh)
    total = 0.0
    degenerate = 0
    nf = mesh.face_count
    for start in range(0, nf, chunk):
        stop = min(start + chunk, nf)
        for i in range(start * 3, stop * 3, 3):
            a = fn(verts, (faces[i], faces[i + 1], faces[i + 2]))
            if a == 0.0:
                degenerate += 1
            total += a
    return total, degenerate


def mesh_projected_area_nm2(mesh: MaleCNSMesh) -> float:
    """Sum of per-triangle XY-projection areas. A silhouette measure only."""
    verts = _flat_vertices(mesh)
    faces = _flat_faces(mesh)
    total = 0.0
    for i in range(0, 3 * mesh.face_count, 3):
        total += _triangle_projected_area_xy(
            verts, (faces[i], faces[i + 1], faces[i + 2]))
    return total


def validate_area(mesh: MaleCNSMesh, sample: int = 2000,
                  seed: int = 20260902) -> Dict[str, float]:
    """Cross-validate the area by an independent formula plus brute-force sampling."""
    verts = _flat_vertices(mesh)
    faces = _flat_faces(mesh)
    cross, deg_cross = mesh_surface_area(mesh, "cross")
    heron, deg_heron = mesh_surface_area(mesh, "heron")
    rng = random.Random(seed)
    n = mesh.face_count
    max_abs = max_rel = 0.0
    for _ in range(sample):
        i = rng.randrange(n) * 3
        t = (faces[i], faces[i + 1], faces[i + 2])
        a = _triangle_area_cross(verts, t)
        b = _triangle_area_heron(verts, t)
        d = abs(a - b)
        max_abs = max(max_abs, d)
        scale = max(a, b)
        if scale > 0:
            max_rel = max(max_rel, d / scale)
    return {
        "cross_area_nm2": cross,
        "heron_area_nm2": heron,
        "aggregate_abs_difference_nm2": abs(cross - heron),
        "aggregate_relative_difference": (
            abs(cross - heron) / heron if heron else float("nan")),
        "sample_count": float(sample),
        "sample_max_abs_difference_nm2": max_abs,
        "sample_max_relative_difference": max_rel,
        "degenerate_faces_cross": float(deg_cross),
        "degenerate_faces_heron": float(deg_heron),
        "projected_area_xy_nm2": mesh_projected_area_nm2(mesh),
    }


# --- 5, 6: topology ---------------------------------------------------------


@dataclass
class ComponentSummary:
    """A topological component of the mesh. NOT an anatomical label."""

    component_id: int
    vertex_count: int
    face_count: int
    surface_area_nm2: float
    bbox_nm: Tuple[float, float, float, float, float, float]

    def provenance(self) -> ProvenanceQuantity:
        return ProvenanceQuantity(
            name=f"mesh component {self.component_id} area",
            value=self.surface_area_nm2,
            units="nm^2",
            evidence=EvidenceClass.ANATOMICAL_MEASUREMENT,
            source="MaleCNS v1.0 .ngmesh surface",
            note=("TOPOLOGICAL component of the mesh only. NOT labelled soma, "
                  "axon, dendrite or nerve: no independent anatomical "
                  "annotation establishes such an identity here."),
        )


def mesh_topology(mesh: MaleCNSMesh) -> Dict[str, object]:
    """Boundary/non-manifold edges, degenerate and duplicate faces, isolated
    vertices, and topological connected components. Reports; never repairs."""
    faces = _flat_faces(mesh)
    verts = _flat_vertices(mesh)
    V = mesh.vertex_count
    F = mesh.face_count

    used = bytearray(V)
    edges = array.array("q")
    face_keys = array.array("q")
    for i in range(0, 3 * F, 3):
        a, b, c = faces[i], faces[i + 1], faces[i + 2]
        used[a] = used[b] = used[c] = 1
        for u, w in ((a, b), (b, c), (c, a)):
            lo, hi = (u, w) if u < w else (w, u)
            edges.append(lo * V + hi)
        s = sorted((a, b, c))
        face_keys.append((s[0] * V + s[1]) * V + s[2])

    edges = array.array("q", sorted(edges))
    boundary = nonmanifold = interior = 0
    nonmanifold_faces = 0
    i = 0
    n = len(edges)
    while i < n:
        j = i + 1
        while j < n and edges[j] == edges[i]:
            j += 1
        run = j - i
        if run == 1:
            boundary += 1
        elif run == 2:
            interior += 1
        else:
            nonmanifold += 1
            nonmanifold_faces += run
        i = j

    face_keys = array.array("q", sorted(face_keys))
    dup = 0
    i = 0
    while i < F:
        j = i + 1
        while j < F and face_keys[j] == face_keys[i]:
            j += 1
        dup += (j - i) - 1
        i = j

    isolated = sum(1 for u in used if u == 0)
    distinct = interior + boundary + nonmanifold
    return {
        "boundary_edges": boundary,
        "non_manifold_edges": nonmanifold,
        "non_manifold_edge_face_slots": nonmanifold_faces,
        "interior_edges": interior,
        "distinct_edges": distinct,
        "edge_face_slots": 3 * F,
        "euler_characteristic": (V - isolated) - distinct + F,
        "closed_surface": boundary == 0 and nonmanifold == 0,
        "degenerate_faces": mesh_surface_area(mesh, "cross")[1],
        "duplicate_faces": dup,
        "isolated_vertices": isolated,
    }


def _component_labels(mesh: MaleCNSMesh) -> Tuple[array.array, List[List[int]]]:
    """Vertex -> component id and the ordered per-component face lists.

    Component 0 is the largest by face count (ties broken by lowest face
    index), so the ids are stable and shared by every consumer of this module.
    Labels are TOPOLOGICAL only.
    """
    faces = _flat_faces(mesh)
    F = mesh.face_count
    parent = list(range(F))

    def find(x: int) -> int:
        r = x
        while parent[r] != r:
            r = parent[r]
        while parent[x] != r:
            parent[x], x = r, parent[x]
        return r

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[max(rx, ry)] = min(rx, ry)

    first_face: Dict[int, int] = {}
    for fi in range(F):
        i = fi * 3
        for k in (faces[i], faces[i + 1], faces[i + 2]):
            prev = first_face.get(k)
            if prev is None:
                first_face[k] = fi
            else:
                union(prev, fi)

    groups: Dict[int, List[int]] = {}
    for fi in range(F):
        groups.setdefault(find(fi), []).append(fi)
    ordered = sorted(groups.values(), key=lambda g: (-len(g), g[0]))

    # -1 marks a vertex no face touches; array('i') zero-fills, so fill with -1.
    labels = array.array("i", b"\xff\xff\xff\xff" * mesh.vertex_count)
    for cid, flist in enumerate(ordered):
        for fi in flist:
            i = fi * 3
            labels[faces[i]] = cid
            labels[faces[i + 1]] = cid
            labels[faces[i + 2]] = cid
    return labels, ordered


def vertex_component_map(mesh: MaleCNSMesh) -> array.array:
    """Map every vertex index to its topological component id.

    An isolated vertex keeps label -1. Labels carry no anatomical meaning.
    """
    return _component_labels(mesh)[0]


def mesh_components(mesh: MaleCNSMesh,
                    max_reported: int = 12) -> Tuple[List[ComponentSummary], int]:
    """Topological connected components via union-find over shared vertices."""
    verts = _flat_vertices(mesh)
    faces = _flat_faces(mesh)
    _labels, ordered = _component_labels(mesh)
    out: List[ComponentSummary] = []
    for cid, flist in enumerate(ordered[:max_reported]):
        area = 0.0
        lo = [float("inf")] * 3
        hi = [float("-inf")] * 3
        vseen = set()
        for fi in flist:
            i = fi * 3
            a, b, c = faces[i], faces[i + 1], faces[i + 2]
            area += _triangle_area_cross(verts, (a, b, c))
            vseen.add(a)
            vseen.add(b)
            vseen.add(c)
        for v in vseen:
            x, y, z = verts[v * 3], verts[v * 3 + 1], verts[v * 3 + 2]
            if x < lo[0]: lo[0] = x
            if y < lo[1]: lo[1] = y
            if z < lo[2]: lo[2] = z
            if x > hi[0]: hi[0] = x
            if y > hi[1]: hi[1] = y
            if z > hi[2]: hi[2] = z
        out.append(ComponentSummary(
            component_id=cid, vertex_count=len(vseen), face_count=len(flist),
            surface_area_nm2=area,
            bbox_nm=(lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]),
        ))
    return out, len(ordered)


def mesh_bounding_box(mesh: MaleCNSMesh) -> Dict[str, float]:
    """Axis-aligned bounding box in nm and um. Extent is NOT a path length."""
    verts = _flat_vertices(mesh)
    xs = verts[0::3]
    ys = verts[1::3]
    zs = verts[2::3]
    out = {}
    for name, buf in (("x", xs), ("y", ys), ("z", zs)):
        lo, hi = float(min(buf)), float(max(buf))
        out[f"min_{name}_nm"] = lo
        out[f"max_{name}_nm"] = hi
        out[f"extent_{name}_nm"] = hi - lo
        out[f"extent_{name}_um"] = (hi - lo) * NM_PER_UM
    return out


# --- 7: soma inclusion (conservative, UNRESOLVED) ----------------------------

#: The only value this module will ever report for soma inclusion.
SOMA_INCLUSION_UNRESOLVED = "UNRESOLVED"


def mesh_sampling_scale_nm(mesh: MaleCNSMesh) -> Dict[str, float]:
    """Edge-length percentiles of the mesh: how finely it is sampled.

    This is the mesh's OWN resolution. It is used as a data-derived reference
    scale (for example when judging whether a contact is meaningfully attached
    to a component) rather than an invented constant. Purely anatomical: no
    cable diameter, no sampling density in a biological sense.
    """
    verts = _flat_vertices(mesh)
    faces = _flat_faces(mesh)
    lengths = array.array("f")
    for i in range(0, 3 * mesh.face_count, 3):
        a, b, c = faces[i], faces[i + 1], faces[i + 2]
        for u, w in ((a, b), (b, c), (c, a)):
            lengths.append(math.sqrt(
                (verts[u * 3] - verts[w * 3]) ** 2
                + (verts[u * 3 + 1] - verts[w * 3 + 1]) ** 2
                + (verts[u * 3 + 2] - verts[w * 3 + 2]) ** 2))
    lengths = array.array("f", sorted(lengths))

    def pct(p: float) -> float:
        return float(lengths[int(p * (len(lengths) - 1))])

    return {
        "edge_length_nm_p05": pct(0.05),
        "edge_length_nm_p50": pct(0.50),
        "edge_length_nm_p95": pct(0.95),
        "edge_length_nm_p99": pct(0.99),
        "edge_length_nm_max": float(lengths[-1]),
        "edge_count": float(len(lengths)),
    }

#: Labels that must never be attached to a topological component.
PROHIBITED_COMPONENT_LABELS = ("soma", "axon", "dendrite", "nerve", "neuropil")


@dataclass(frozen=True)
class SomaInclusionAssessment:
    """Whether the mesh contains the MN5 soma. Deliberately not decided."""

    status: str
    reason: str
    evidence_available: str
    evidence_missing: str
    would_resolve: str
    prohibited_labels: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("reason", "evidence_available", "evidence_missing",
                     "would_resolve"):
            if not isinstance(getattr(self, name), str):
                raise TypeError(
                    f"SomaInclusionAssessment.{name} must be a string, got "
                    f"{type(getattr(self, name)).__name__}")
        if self.status != SOMA_INCLUSION_UNRESOLVED:
            raise ValueError(
                f"soma inclusion status must be {SOMA_INCLUSION_UNRESOLVED!r}, "
                f"got {self.status!r}")

    def provenance(self) -> ProvenanceQuantity:
        return ProvenanceQuantity(
            name="MN5 soma inclusion in EM surface mesh",
            value=self.status,
            units="status",
            evidence=EvidenceClass.ANATOMICAL_MEASUREMENT,
            source="MaleCNS v1.0 .ngmesh surface + EM skeleton",
            note=self.reason,
        )


def assess_soma_inclusion(mesh: MaleCNSMesh,
                          swc_root_nm: Optional[Tuple[float, float, float]] = None,
                          ) -> SomaInclusionAssessment:
    """Decide nothing. Report that soma inclusion is UNRESOLVED, and why.

    The mesh is one continuous EM surface. Nothing in the MaleCNS v1.0
    artefacts annotates any part of it as soma, and the recovered SWC skeleton
    has no soma node -- its root is the origin of a stalk, not a soma. Proximity
    of a contact to a SWC root is therefore not evidence of somatic contact.
    """
    return SomaInclusionAssessment(
        status=SOMA_INCLUSION_UNRESOLVED,
        reason=(
            "The .ngmesh is a single continuous EM surface with no anatomical "
            "partition: no source in the MaleCNS v1.0 artefacts labels any "
            "connected component as soma. Assigning a component to the soma "
            "would be an unsupported anatomical claim, so no component is "
            "labelled and no soma area is reported."
        ),
        evidence_available=(
            f"body {mesh.body_id}: {mesh.vertex_count} vertices, "
            f"{mesh.face_count} faces, one or more topological components, and a "
            "full axis-aligned extent in the 8 nm EM frame."
        ),
        evidence_missing=(
            "No soma annotation, no soma centroid, no soma node in the "
            "skeleton, and no independent label mapping mesh vertices to "
            "cellular compartments. A SWC root marks a stalk origin and is not "
            "a soma marker."
            + ("" if swc_root_nm is None else
               " A SWC root position was supplied, but it cannot be promoted to "
               "a soma location without the missing annotation.")
        ),
        would_resolve=(
            "An independent anatomical annotation for MN5 (DLMn a,b) carried "
            "into mesh space -- for example a labelled soma segmentation, or the "
            "MaleCNS cell-type somaSide/somaNeuromere field mapped to mesh "
            "coordinates. Neither exists in the ingested artefacts."
        ),
        prohibited_labels=PROHIBITED_COMPONENT_LABELS,
    )


# --- 8: contact -> mesh proximity -------------------------------------------


def _closest_point_on_triangle(
        p: Sequence[float], a: Sequence[float], b: Sequence[float],
        c: Sequence[float]) -> Tuple[float, float, float]:
    """Closest point to ``p`` on triangle abc (Ericson, Real-Time Collision Det.)."""
    abx, aby, abz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    acx, acy, acz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    apx, apy, apz = p[0] - a[0], p[1] - a[1], p[2] - a[2]
    d1 = abx * apx + aby * apy + abz * apz
    d2 = acx * apx + acy * apy + acz * apz
    if d1 <= 0.0 and d2 <= 0.0:
        return a[0], a[1], a[2]
    bpx, bpy, bpz = p[0] - b[0], p[1] - b[1], p[2] - b[2]
    d3 = abx * bpx + aby * bpy + abz * bpz
    d4 = acx * bpx + acy * bpy + acz * bpz
    if d3 >= 0.0 and d4 <= d3:
        return b[0], b[1], b[2]
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        return a[0] + v * abx, a[1] + v * aby, a[2] + v * abz
    cpx, cpy, cpz = p[0] - c[0], p[1] - c[1], p[2] - c[2]
    d5 = abx * cpx + aby * cpy + abz * cpz
    d6 = acx * cpx + acy * cpy + acz * cpz
    if d6 >= 0.0 and d5 <= d6:
        return c[0], c[1], c[2]
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        return a[0] + w * acx, a[1] + w * acy, a[2] + w * acz
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return b[0] + w * (c[0] - b[0]), b[1] + w * (c[1] - b[1]), \
            b[2] + w * (c[2] - b[2])
    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    return a[0] + abx * v + acx * w, a[1] + aby * v + acy * w, \
        a[2] + abz * v + acz * w


class MeshSurfaceIndex:
    """Uniform spatial hash over face AABBs, for exact nearest-surface queries.

    Pure standard library. A query expands ring-wise and stops as soon as the
    searched radius is at least the best distance found, so the returned
    nearest point is exact rather than approximate.
    """

    def __init__(self, mesh: MaleCNSMesh, target_faces_per_cell: int = 8) -> None:
        self.mesh = mesh
        self.verts = _flat_vertices(mesh)
        self.faces = _flat_faces(mesh)
        self.bbox = mesh_bounding_box(mesh)
        vol = 1.0
        for axis in "xyz":
            vol *= max(self.bbox[f"extent_{axis}_nm"], 1.0)
        cells = max(1, len(self.faces) // 3 // max(1, target_faces_per_cell))
        self.cell = max((vol / cells) ** (1.0 / 3.0), 1e-6)
        lo = (self.bbox["min_x_nm"], self.bbox["min_y_nm"], self.bbox["min_z_nm"])
        self.n = tuple(
            max(1, int((self.bbox[f"extent_{a}_nm"] / self.cell) + 2))
            for a in "xyz"
        )
        self.lo = lo
        self.bins: Dict[Tuple[int, int, int], List[int]] = {}
        for fi in range(len(self.faces) // 3):
            i = fi * 3
            box = self._face_aabb(fi)
            c0 = self._cell_of(box[0], box[1], box[2])
            c1 = self._cell_of(box[3], box[4], box[5])
            for cx in range(c0[0], c1[0] + 1):
                for cy in range(c0[1], c1[1] + 1):
                    for cz in range(c0[2], c1[2] + 1):
                        self.bins.setdefault((cx, cy, cz), []).append(fi)

    def _face_aabb(self, fi: int) -> Tuple[float, float, float, float, float, float]:
        i = fi * 3
        ax, ay, az = (self.verts[self.faces[i] * 3],
                      self.verts[self.faces[i] * 3 + 1],
                      self.verts[self.faces[i] * 3 + 2])
        bx, by, bz = (self.verts[self.faces[i + 1] * 3],
                      self.verts[self.faces[i + 1] * 3 + 1],
                      self.verts[self.faces[i + 1] * 3 + 2])
        cx, cy, cz = (self.verts[self.faces[i + 2] * 3],
                      self.verts[self.faces[i + 2] * 3 + 1],
                      self.verts[self.faces[i + 2] * 3 + 2])
        return (min(ax, bx, cx), min(ay, by, cy), min(az, bz, cz),
                max(ax, bx, cx), max(ay, by, cy), max(az, bz, cz))

    def _cell_of(self, x: float, y: float,
                 z: float) -> Tuple[int, int, int]:
        """Clamped cell index of one point, computed per axis.

        Each axis uses its own coordinate: a cell index derived from
        the wrong axis would place a face in a distant cell and force
        every query to expand ring-wise until it stumbles onto the
        misplaced face, which is both slow and a premature-termination
        hazard.
        """
        return (
            min(max(int((x - self.lo[0]) / self.cell), 0),
                self.n[0] - 1),
            min(max(int((y - self.lo[1]) / self.cell), 0),
                self.n[1] - 1),
            min(max(int((z - self.lo[2]) / self.cell), 0),
                self.n[2] - 1),
        )

    def _cell_range(self, p: Sequence[float],
                    radius: float) -> Tuple[Tuple[int, int], Tuple[int, int],
                                            Tuple[int, int]]:
        """UNCLAMPED cell index range covering the sphere of ``radius``.

        Clamping here would make a query point outside the mesh bounding box
        collapse onto the boundary cell and never expand, so the range is left
        unclamped and out-of-grid cells are simply absent from ``self.bins``.
        """
        return tuple(
            (int((p[a] - radius - self.lo[a]) / self.cell),
             int((p[a] + radius - self.lo[a]) / self.cell))
            for a in range(3)
        )  # type: ignore[return-value]

    def nearest_surface(self, p: Sequence[float], r0: Optional[float] = None
                        ) -> Tuple[float, Tuple[float, float, float], int]:
        """Exact (distance_nm, closest_point_nm, face_index) on the surface.

        The search starts at half a cell and doubles until the best
        distance found is within the searched radius. Any start radius
        yields the same exact answer, because a face closer than the
        current best must lie inside the searched sphere; starting
        small only avoids scanning a large first ring when the query
        point is already close to the surface.
        """
        span = max(self.bbox["extent_x_nm"], self.bbox["extent_y_nm"],
                   self.bbox["extent_z_nm"])
        radius = self.cell * 0.5 if r0 is None else max(float(r0),
                                                         self.cell)
        best = float("inf")
        best_pt = (0.0, 0.0, 0.0)
        best_fi = -1
        seen = set()
        while True:
            (cx0, cx1), (cy0, cy1), (cz0, cz1) = self._cell_range(p, radius)
            for cx in range(cx0, cx1 + 1):
                for cy in range(cy0, cy1 + 1):
                    for cz in range(cz0, cz1 + 1):
                        key = (cx, cy, cz)
                        if key in seen:
                            continue
                        seen.add(key)
                        for fi in self.bins.get(key, ()):
                            i = fi * 3
                            a = (self.verts[self.faces[i] * 3],
                                 self.verts[self.faces[i] * 3 + 1],
                                 self.verts[self.faces[i] * 3 + 2])
                            b = (self.verts[self.faces[i + 1] * 3],
                                 self.verts[self.faces[i + 1] * 3 + 1],
                                 self.verts[self.faces[i + 1] * 3 + 2])
                            c = (self.verts[self.faces[i + 2] * 3],
                                 self.verts[self.faces[i + 2] * 3 + 1],
                                 self.verts[self.faces[i + 2] * 3 + 2])
                            q = _closest_point_on_triangle(p, a, b, c)
                            d = math.sqrt((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
                                          + (q[2] - p[2]) ** 2)
                            if d < best:
                                best, best_pt, best_fi = d, q, fi
            if best <= radius or not self.bins:
                return best, best_pt, best_fi
            radius *= 2.0
            if radius > 4.0 * max(span, self.cell):
                return best, best_pt, best_fi

    def nearest_surface_by_component(
            self, p: Sequence[float], n_best: int = 2,
            labels: Optional[array.array] = None,
            ) -> List[Tuple[int, float, Tuple[float, float, float], int]]:
        """Best ``n_best`` DISTINCT components as (component_id, distance_nm,
        closest_point_nm, face_index), ordered by increasing distance.

        Component identity is topological only. Needed because this mesh is
        heavily fragmented: a single global nearest point cannot say whether a
        contact belongs to one component or sits equally close to several.
        """
        if labels is None:
            labels = vertex_component_map(self.mesh)
        faces = self.faces
        span = max(self.bbox["extent_x_nm"], self.bbox["extent_y_nm"],
                   self.bbox["extent_z_nm"])
        radius = self.cell * 2.0
        best: Dict[int, Tuple[float, Tuple[float, float, float], int]] = {}
        seen = set()
        extra_rings = 0
        diag = math.sqrt(sum(self.bbox[f"extent_{a}_nm"] ** 2 for a in "xyz"))
        complete = False
        while True:
            (cx0, cx1), (cy0, cy1), (cz0, cz1) = self._cell_range(p, radius)
            for cx in range(cx0, cx1 + 1):
                for cy in range(cy0, cy1 + 1):
                    for cz in range(cz0, cz1 + 1):
                        key = (cx, cy, cz)
                        if key in seen:
                            continue
                        seen.add(key)
                        for fi in self.bins.get(key, ()):
                            i = fi * 3
                            a = (self.verts[faces[i] * 3],
                                 self.verts[faces[i] * 3 + 1],
                                 self.verts[faces[i] * 3 + 2])
                            b = (self.verts[faces[i + 1] * 3],
                                 self.verts[faces[i + 1] * 3 + 1],
                                 self.verts[faces[i + 1] * 3 + 2])
                            c = (self.verts[faces[i + 2] * 3],
                                 self.verts[faces[i + 2] * 3 + 1],
                                 self.verts[faces[i + 2] * 3 + 2])
                            comp = int(labels[faces[i]])
                            cur = best.get(comp)
                            if cur is not None and cur[0] <= 0.0:
                                continue
                            q = _closest_point_on_triangle(p, a, b, c)
                            d = math.sqrt((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
                                          + (q[2] - p[2]) ** 2)
                            if cur is None or d < cur[0]:
                                best[comp] = (d, q, fi)
            if not best:
                if radius >= max(4.0 * diag, self.cell):
                    complete = True
                    break
                radius *= 2.0
                continue
            if len(best) >= n_best:
                ordered = sorted(best.values(), key=lambda t: t[0])
                threshold = ordered[n_best - 1][0]
                # Stop when nothing unseen can beat the n_best-th best, then take
                # one more ring so an exact tie in a neighbouring component is
                # not missed.
                if radius >= threshold:
                    extra_rings += 1
                    if extra_rings >= 2:
                        break
            elif radius >= diag:
                # Fewer than n_best components exist within reach of the whole
                # mesh, so every face has been searched and the answer is final.
                complete = True
                break
            radius *= 2.0
            if radius > 4.0 * max(diag, self.cell):
                complete = True
                break
        ranked = sorted(best.items(), key=lambda kv: kv[1][0])[:n_best]
        if complete and not ranked:
            return []
        return [(cid, d, q, fi) for cid, (d, q, fi) in ranked]

    def nearest_vertex(self, p: Sequence[float]) -> Tuple[int, float]:
        """Exact (vertex_index, distance_nm) to the nearest mesh vertex.

        One complete scan: every vertex is compared, so the first
        vertex attaining the minimum squared distance is returned
        exactly. The vertices are not sorted by position, so no
        index-space window or stride can prune the search; the scan
        is O(n) in the vertex count and roots the distance once.
        """
        verts = self.verts
        n = len(verts) // 3
        best_i, best_d = 0, float("inf")
        for i in range(n):
            d = ((verts[i * 3] - p[0]) ** 2 + (verts[i * 3 + 1] - p[1]) ** 2
                 + (verts[i * 3 + 2] - p[2]) ** 2)
            if d < best_d:
                best_d, best_i = d, i
        return best_i, math.sqrt(best_d)


@dataclass(frozen=True)
class ContactProximity:
    """One EM contact located on the MN5 surface. Geometry only.

    ``post_xyz_raw`` is the connectome coordinate exactly as ingested, in the
    raw 8 nm units of the MaleCNS frame. ``post_xyz_nm`` is the same point
    converted with ``MESH_TO_SWC_SCALE`` so it lives in the mesh's nanometre
    space. Conflating the two silently inflates every distance by 8x, so both
    are carried explicitly.
    """

    pre_body: int
    post_body: int
    post_xyz_raw: Tuple[float, float, float]
    post_xyz_nm: Tuple[float, float, float]
    conf_pre: float
    conf_post: float
    primary_post: str
    nearest_vertex_index: int
    nearest_vertex_xyz_nm: Tuple[float, float, float]
    vertex_distance_nm: float
    nearest_surface_xyz_nm: Tuple[float, float, float]
    surface_distance_nm: float
    surface_face_index: int
    component_id: int
    note: str = ("Straight-line surface proximity in the 8 nm EM frame. NOT a "
                 "conduction path, not a synaptic weight, and not a distance "
                 "to the soma (the soma is not identified in this mesh).")


class ContactFrameError(Exception):
    """Raised when a contact cannot be placed in mesh nanometre space."""


def contact_geometry_report(mesh: MaleCNSMesh, contacts: Sequence,
                            index: Optional[MeshSurfaceIndex] = None,
                            labels: Optional[array.array] = None,
                            tolerance_nm: float = 0.0,
                            ) -> List[ContactProximity]:
    """Locate each post-synaptic contact on the MN5 surface.

    Contact coordinates arrive in the raw 8 nm units of the connectome and are
    multiplied by ``MESH_TO_SWC_SCALE`` to reach the mesh's nanometre space.
    A contact that still falls outside the mesh bounding box means the two
    artefacts are not in a common frame, so this raises rather than returning a
    large, meaningless distance.
    """
    idx = MeshSurfaceIndex(mesh) if index is None else index
    lab = vertex_component_map(mesh) if labels is None else labels
    verts = idx.verts
    bb = mesh_bounding_box(mesh)
    out: List[ContactProximity] = []
    for c in contacts:
        raw = c.post_xyz
        raw_t = (float(raw[0]), float(raw[1]), float(raw[2]))
        p = (raw_t[0] * MESH_TO_SWC_SCALE, raw_t[1] * MESH_TO_SWC_SCALE,
             raw_t[2] * MESH_TO_SWC_SCALE)
        for axis, v in zip("xyz", p):
            lo = bb[f"min_{axis}_nm"] - tolerance_nm
            hi = bb[f"max_{axis}_nm"] + tolerance_nm
            if not (lo <= v <= hi):
                raise ContactFrameError(
                    f"contact {raw_t} in raw 8 nm units -> {p} nm lies outside "
                    f"the body {mesh.body_id} mesh bounding box on {axis} "
                    f"[{bb[f'min_{axis}_nm']:.1f}, {bb[f'max_{axis}_nm']:.1f}] "
                    f"nm. The connectome frame and the mesh frame are not "
                    f"commensurate; refusing to report a proximity distance.")
        vi, vd = idx.nearest_vertex(p)
        sd, sp, fi = idx.nearest_surface(p)
        comp = int(lab[vi]) if vi < len(lab) else -1
        out.append(ContactProximity(
            pre_body=int(c.pre_body), post_body=int(c.post_body),
            post_xyz_raw=raw_t, post_xyz_nm=p,
            conf_pre=float(c.conf_pre), conf_post=float(c.conf_post),
            primary_post=str(c.primary_post),
            nearest_vertex_index=vi,
            nearest_vertex_xyz_nm=(float(verts[vi * 3]), float(verts[vi * 3 + 1]),
                                   float(verts[vi * 3 + 2])),
            vertex_distance_nm=vd,
            nearest_surface_xyz_nm=sp, surface_distance_nm=sd,
            surface_face_index=fi, component_id=comp,
        ))
    return out


# --- 9: area comparison -----------------------------------------------------

#: How an SWC segment is turned into an area, stated as an assumption.
SWC_AREA_MODEL = (
    "lateral area of each segment as a truncated cone, "
    "A = pi*(r1+r2)*sqrt(L^2 + (r1-r2)^2), no end caps, soma excluded"
)


def swc_lateral_area_um2(skeleton: SkeletonGeometry) -> Dict[str, object]:
    """Skeleton-derived lateral area in um^2, with its assumption stated.

    Purely anatomical. The frustum idealisation is a MODELLING ASSUMPTION
    about how to read a 1-D reconstruction, not a measurement of the EM
    surface, and the radii are used exactly as reconstructed. This area must
    not be divided by a capacitance or a resistance to produce any
    electrical parameter.
    """
    to_um = skeleton.unit_nm / 1000.0
    total = 0.0
    counted = 0
    for a, b in skeleton.segments():
        r1 = a.radius * to_um
        r2 = b.radius * to_um
        length = skeleton.distance(a, b) * to_um
        total += math.pi * (r1 + r2) * math.sqrt(
            length * length + (r1 - r2) * (r1 - r2))
        counted += 1
    return {
        "lateral_area_um2": total,
        "segment_count": counted,
        "node_count": len(skeleton.nodes),
        "model": SWC_AREA_MODEL,
        "evidence": EvidenceClass.MODEL_DERIVED_ESTIMATE,
        "note": ("Derived from reconstructed skeleton radii under a stated "
                 "frustum assumption. Not an EM surface measurement, and not a "
                 "substitute for the mesh area. Using it to form Cm, Rm, "
                 "g_pas or any transfer quantity is forbidden."),
    }


@dataclass(frozen=True)
class AreaComparison:
    """Mesh total against other published/derived areas, with domains kept apart.

    These numbers are NOT interchangeable and the dataclass never presents them
    as if they were: the mesh total is the whole reconstructed EM surface, a
    SWC-derived area is a cylindrical approximation of the same skeleton, and a
    literature area may cover only a sub-region of the neuron.
    """

    mesh_total_um2: float
    swc_total_um2: Optional[float]
    swc_domain: str
    literature_um2: Optional[float]
    literature_domain: str
    comparability: str
    caveats: Tuple[str, ...]

    @property
    def mesh_minus_swc_um2(self) -> Optional[float]:
        if self.swc_total_um2 is None:
            return None
        return self.mesh_total_um2 - self.swc_total_um2

    @property
    def mesh_over_swc_ratio(self) -> Optional[float]:
        if not self.swc_total_um2:
            return None
        return self.mesh_total_um2 / self.swc_total_um2


def compare_areas(mesh_area_nm2: float, swc_total_um2: Optional[float] = None,
                  swc_domain: str = "SWC skeleton, conical frustum per segment",
                  literature_um2: Optional[float] = None,
                  literature_domain: str = "unspecified sub-region",
                  ) -> AreaComparison:
    """Set the mesh area beside reference areas without equating them."""
    caveats = [
        "The mesh total is the full EM surface of the reconstructed body; a "
        "SWC-derived area is a convex-hull-per-segment approximation of the "
        "same skeleton at 8 nm sampling, and the two are different domains of "
        "the same object. A ratio between them is informative, not a "
        "validation and not an error estimate.",
        "Any literature area must state which sub-region it covers. A "
        "central-neuron area is not comparable to a whole-neuron mesh total.",
        "No discrepancy here may be resolved by adjusting an electrical "
        "parameter: area is anatomical, and the electrical model stays "
        "NOT AUTHORIZED.",
    ]
    return AreaComparison(
        mesh_total_um2=mesh_area_nm2 * NM2_PER_UM2,
        swc_total_um2=swc_total_um2, swc_domain=swc_domain,
        literature_um2=literature_um2, literature_domain=literature_domain,
        comparability="NOT_COMPARABLE_WITHOUT_DOMAIN_CAVEAT", caveats=tuple(caveats),
    )


# --- 10: gate + report ------------------------------------------------------

def deriving_electrical_quantity_from_geometry() -> None:
    """Always raises. Geometry may not be converted into electrical parameters."""
    from .malecns_ingest import require_biological_transfer_authorization
    require_biological_transfer_authorization()


#: Canonical list of electrical keys that may never appear in anatomical output.
#: Defined here and shared by :mod:`biological_brain.malecns_contact_path` so
#: both modules enforce exactly the same rule.
FORBIDDEN_ELECTRICAL_KEYS = (
    # capitals
    "ra", "rm", "cm", "tau", "lambda",
    # specific membrane properties
    "capacitance", "resistance", "conductance", "g_pas",
    "cm_specific", "rm_specific", "cm_um2", "uf_cm2", "ohm_cm", "ohm_cm2",
    "specific_membrane_capacitance", "specific_membrane_resistance",
    "membrane_conductance", "axial_resistivity", "ra_ohm",
    # cable / electrotonic
    "length_constant", "space_constant", "electrotonic_distance",
    "cable_distance", "electrotonic",
    # transfer
    "attenuation", "attenuation_distance", "transfer_resistance",
    "input_resistance", "axial_resistance", "voltage_transfer",
    "spatial_voltage_transfer", "synaptic_conductance",
    "dalpha7_conductance", "synaptic_delay", "reversal_potential",
)

#: The only keys allowed through the guard, and only when they record a refusal.
GATE_RECORD_KEYS = ("spatial_voltage_transfer",
                     "dalpha7_biological_conductance")


def assert_geometry_only(report: Dict[str, object]) -> None:
    """Fail loudly if a payload carries any electrical key at any depth.

    A gate field is the single exception, and only when its value is a string
    recording NOT AUTHORIZED, so the exception cannot smuggle a number through.
    """
    stack: List[object] = [report]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for k, v in node.items():
                key = str(k).lower()
                if key in GATE_RECORD_KEYS:
                    if isinstance(v, str) and "NOT AUTHORIZED" in v:
                        continue
                    raise AssertionError(
                        f"gate field {k!r} must record a NOT AUTHORIZED string, "
                        f"got {type(v).__name__}")
                if key in FORBIDDEN_ELECTRICAL_KEYS:
                    raise AssertionError(
                        f"anatomical output contains forbidden electrical key "
                        f"{k!r}")
                stack.append(v)
        elif isinstance(node, (list, tuple, set)):
            stack.extend(node)


def mesh_geometry_report(mesh: MaleCNSMesh, contacts: Sequence = (),
                         swc_total_um2: Optional[float] = None,
                         literature_um2: Optional[float] = None,
                         literature_domain: str = "unspecified sub-region",
                         ) -> Dict[str, object]:
    """Full MN5 surface-geometry report. Purely anatomical; electrically empty."""
    area = validate_area(mesh)
    area_nm2 = area["cross_area_nm2"]
    comps, ncomp = mesh_components(mesh)
    index = MeshSurfaceIndex(mesh)
    labels = vertex_component_map(mesh)
    soma = assess_soma_inclusion(mesh)
    prox = contact_geometry_report(mesh, contacts, index=index, labels=labels)

    largest_frac = (comps[0].surface_area_nm2 / area_nm2) if (comps and area_nm2) else None
    report: Dict[str, object] = {
        "body_id": mesh.body_id,
        "vertex_count": mesh.vertex_count,
        "face_count": mesh.face_count,
        "source": mesh.path,
        "sha256": mesh.sha256,
        "coordinate_units": "nm (raw MaleCNS EM space; SWC*8 = mesh)",
        "area": {
            "total_nm2": area_nm2,
            "total_um2": area_nm2 * NM2_PER_UM2,
            "method": "cross product, cross-validated by Heron's formula",
            "cross_area_nm2": area["cross_area_nm2"],
            "heron_area_nm2": area["heron_area_nm2"],
            "aggregate_abs_difference_nm2": area["aggregate_abs_difference_nm2"],
            "aggregate_relative_difference": area["aggregate_relative_difference"],
            "sample_count": area["sample_count"],
            "sample_max_abs_difference_nm2": area["sample_max_abs_difference_nm2"],
            "sample_max_relative_difference": area["sample_max_relative_difference"],
            "degenerate_faces_cross": area["degenerate_faces_cross"],
            "degenerate_faces_heron": area["degenerate_faces_heron"],
            "projected_area_xy_nm2": area["projected_area_xy_nm2"],
            "projected_area_note": (
                "Sum of per-triangle XY-projection areas: a silhouette "
                "measure, NOT a surface area."),
        },
        "topology": mesh_topology(mesh),
        "components": {
            "count": ncomp,
            "largest_area_fraction": largest_frac,
            "labels": "topological only; no component is labelled anatomically",
            "detail": [
                {
                    "component_id": c.component_id,
                    "vertex_count": c.vertex_count,
                    "face_count": c.face_count,
                    "surface_area_nm2": c.surface_area_nm2,
                    "surface_area_um2": c.surface_area_nm2 * NM2_PER_UM2,
                    "bbox_extent_nm": [
                        c.bbox_nm[3] - c.bbox_nm[0], c.bbox_nm[4] - c.bbox_nm[1],
                        c.bbox_nm[5] - c.bbox_nm[2],
                    ],
                }
                for c in comps
            ],
        },
        "bounding_box": mesh_bounding_box(mesh),
        "soma_inclusion": {
            "status": soma.status,
            "reason": soma.reason,
            "evidence_missing": soma.evidence_missing,
            "would_resolve": soma.would_resolve,
        },
        "contact_proximity": {
            "count": len(prox),
            "frame": (
                f"contacts ingested in raw 8 nm units, converted with "
                f"MESH_TO_SWC_SCALE={MESH_TO_SWC_SCALE} to mesh nanometres"),
            "surface_distance_nm": {
                "min": min((p.surface_distance_nm for p in prox), default=None),
                "median": (sorted(p.surface_distance_nm for p in prox)[len(prox) // 2]
                           if prox else None),
                "max": max((p.surface_distance_nm for p in prox), default=None),
            },
            "component_histogram": _histogram([p.component_id for p in prox]),
            "by_primary_post": {
                region: {
                    "count": len(group),
                    "surface_distance_nm": {
                        "min": min(p.surface_distance_nm for p in group),
                        "max": max(p.surface_distance_nm for p in group),
                    },
                    "component_histogram": _histogram(
                        [p.component_id for p in group]),
                }
                for region, group in _group_by_region(prox).items()
            },
            "region_note": (
                "Contacts are grouped by the ingested primary_post label "
                "verbatim. Central and peripheral compartments are reported "
                "separately and are never pooled; the labels are the source's, "
                "not an inference from this mesh."),
            "contacts": [
                {
                    "pre_body": p.pre_body, "post_body": p.post_body,
                    "post_xyz_raw_8nm_units": list(p.post_xyz_raw),
                    "post_xyz_nm": list(p.post_xyz_nm),
                    "conf_pre": p.conf_pre, "conf_post": p.conf_post,
                    "primary_post": p.primary_post,
                    "vertex_distance_nm": p.vertex_distance_nm,
                    "surface_distance_nm": p.surface_distance_nm,
                    "component_id": p.component_id,
                    "note": p.note,
                }
                for p in prox
            ],
        },
        "comparison": _comparison_dict(compare_areas(
            area_nm2, swc_total_um2=swc_total_um2,
            literature_um2=literature_um2, literature_domain=literature_domain)),
        "scope": {
            "anatomy_only": True,
            "biological_transfer_status": "NOT AUTHORIZED",
            "forbidden_conversions": FORBIDDEN_ELECTRICAL_KEYS,
            "note": ("Surface area, extent, topology and contact position only. "
                     "No Cm, Rm, Ra, g_pas, length constant, electrotonic "
                     "distance, attenuation or transfer resistance is computed "
                     "or implied, and none may be derived from these values."),
        },
    }
    assert_geometry_only(report)
    return report


def _group_by_region(prox: Sequence[ContactProximity]) -> Dict[str, List[ContactProximity]]:
    """Group contacts by their ingested primary_post label, verbatim."""
    out: Dict[str, List[ContactProximity]] = {}
    for p in prox:
        out.setdefault(p.primary_post, []).append(p)
    return dict(sorted(out.items(), key=lambda kv: (-len(kv[1]), kv[0])))


def _histogram(values: Sequence[int]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _comparison_dict(cmp_: AreaComparison) -> Dict[str, object]:
    return {
        "mesh_total_um2": cmp_.mesh_total_um2,
        "swc_total_um2": cmp_.swc_total_um2,
        "swc_domain": cmp_.swc_domain,
        "mesh_minus_swc_um2": cmp_.mesh_minus_swc_um2,
        "mesh_over_swc_ratio": cmp_.mesh_over_swc_ratio,
        "literature_um2": cmp_.literature_um2,
        "literature_domain": cmp_.literature_domain,
        "comparability": cmp_.comparability,
        "caveats": list(cmp_.caveats),
    }


def geometry_scope_note() -> str:
    """Human-readable scope statement for a geometry report."""
    return (
        "MN5 (DLMn a,b) surface geometry from the MaleCNS v1.0 .ngmesh bodies "
        "801970 and 801295, in raw nanometres of the 8 nm EM frame. Areas are "
        "measured twice by independent formulae and reconciled to floating-point "
        "round-off. Topology is reported, never repaired, and connected "
        "components carry no anatomical label. Soma inclusion is UNRESOLVED: no "
        "artefact annotates the mesh, and an SWC root is a stalk origin, not a "
        "soma. Mesh totals are set beside SWC-derived and literature areas with "
        "their domains and sampling differences stated, never equated. Nothing "
        "electrical is produced: the PSI->MN5 transfer stays NOT AUTHORIZED and "
        "no Cm, Rm, Ra, g_pas, length constant, attenuation or transfer "
        "resistance follows from any number here."
    )
