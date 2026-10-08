"""Tests for PSI->MN5 anatomical path analysis (3.0D-8R).

Scope guard: anatomy and geometry only. These tests assert that anatomical
quantities are produced, that ambiguous situations are reported UNRESOLVED
rather than approximated, that every quantity carries exactly one of the five
provenance classes, and that both electrical gates still refuse.

Synthetic fixtures are small hand-built polyhedra and centerlines used to pin
exact values. They are NOT MN5 biology and carry no biological meaning; real
contacts and real meshes are used wherever biology is asserted.
"""

import array
import math
import os
import struct
import tempfile

import pytest

from biological_brain import malecns_contact_path as cp
from biological_brain import malecns_ingest as mi
from biological_brain import malecns_mesh_geometry as mg
from malecns_real_data import real_contacts


# --- synthetic fixtures ------------------------------------------------------


def _write_mesh(tmp_path, name, verts, faces, body=999):
    v = array.array("f")
    for xyz in verts:
        v.extend(float(c) for c in xyz)
    f = array.array("I")
    for tri in faces:
        f.extend(int(i) for i in tri)
    path = tmp_path / name
    with open(path, "wb") as h:
        h.write(struct.pack("<I", len(verts)))
        h.write(v.tobytes())
        h.write(f.tobytes())
    return mi.parse_male_ngmesh(str(path), body)


def _tetra(ox, oy, oz, s):
    verts = [(ox, oy, oz), (ox + s, oy, oz), (ox, oy + s, oz), (ox, oy, oz + s)]
    faces = [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)]
    return verts, faces


def _cube(ox, oy, oz, s):
    verts = [(ox + (s if i & 1 else 0), oy + (s if i & 2 else 0),
              oz + (s if i & 4 else 0)) for i in range(8)]
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    faces = []
    for a, b, c, d in quads:
        faces.append((a, b, c))
        faces.append((a, c, d))
    return verts, faces


class _FakeContact:
    def __init__(self, raw, pre=802401, post=801970, conf_pre=1.0,
                 conf_post=1.0, region="PDMN(R)"):
        self.pre_body = pre
        self.post_body = post
        self.pre_xyz = raw
        self.post_xyz = raw
        self.conf_pre = conf_pre
        self.conf_post = conf_post
        self.primary_post = region


def _raw(xyz):
    """A nanometre triple expressed back in the raw 8 nm unit frame."""
    return tuple(v / mi.MESH_TO_SWC_SCALE for v in xyz)


def _chain_skel(nodes_raw, body=999, unit_nm=mi.COORD_UNIT_NM):
    """Build a SkeletonGeometry from (index, parent, radius, x, y, z) rows."""
    swc = [mi.SwcNode(index=i, parent=p, radius=r, kind=0, x=x, y=y, z=z)
           for i, p, r, x, y, z in nodes_raw]
    return mi.SkeletonGeometry(body_id=body, frame=mi.FRAME_EM_8NM,
                               unit_nm=unit_nm, nodes=swc)


def _cell_type(body, soma_raw):
    return mi.CellTypeRow(body_id=body, cell_type="DLMn a, b",
                          superclass="motor neuron", soma_side="L",
                          soma_neuromere="T2", soma_location=soma_raw,
                          exit_nerve="PDMNa")


# --- 1, 2: coordinate frames ------------------------------------------------


def test_contact_frame_converts_raw_units_to_nanometres():
    frame = cp.resolve_contact_frame([_FakeContact((1000.0, 2000.0, 3000.0))])
    assert frame.is_swc_raw_space
    assert not frame.is_mesh_space
    assert frame.to_nm((1000.0, 2000.0, 3000.0)) == (8000.0, 16000.0, 24000.0)
    # A mesh-space frame must NOT be scaled again.
    mesh_frame = cp.resolve_contact_frame([], expected_unit_nm=1.0)
    assert mesh_frame.is_mesh_space
    assert mesh_frame.to_nm((8000.0, 16000.0, 24000.0)) == (
        8000.0, 16000.0, 24000.0)


def test_frame_conversion_is_not_applied_twice(tmp_path):
    """Regression guard: a coordinate already in mesh space must not be scaled.

    The frame is now an explicit, required argument with no default, so a
    mesh-space coordinate can be passed through untouched and a raw-space one is
    scaled exactly once. Passing anything else raises.
    """
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 10000.0))
    # Already nanometres: must pass through unscaled.
    in_nm = _FakeContact((5000.0, 5000.0, 5000.0))
    a = cp.contact_mesh_associations(mesh, [in_nm], cp.FRAME_MESH_NM)[0]
    assert a.xyz_nm == (5000.0, 5000.0, 5000.0)
    # Raw 8 nm units for the same point: scaled exactly once.
    in_raw = _FakeContact(_raw((5000.0, 5000.0, 5000.0)))
    b = cp.contact_mesh_associations(mesh, [in_raw], cp.FRAME_SWMC_RAW_8NM)[0]
    assert b.xyz_nm == (5000.0, 5000.0, 5000.0)
    assert b.surface_distance_nm == pytest.approx(a.surface_distance_nm,
                                                  rel=1e-9)


def test_associations_require_an_explicit_frame(tmp_path):
    """No default frame: an unlabelled contact set is an error, not a guess."""
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 10000.0))
    with pytest.raises(cp.AmbiguousCoordinateFrame):
        cp.contact_mesh_associations(mesh, [_FakeContact((1.0, 2.0, 3.0))])
    with pytest.raises(cp.AmbiguousCoordinateFrame):
        cp.contact_mesh_associations(mesh, [_FakeContact((1.0, 2.0, 3.0))],
                                     "raw")
    # A coordinate set that only fits a plain-nanometre reading: 5000 raw
    # units would become 40000 nm, outside a 10000 nm cube.
    only_nm = [_FakeContact((5000.0, 5000.0, 5000.0))]
    assert cp.resolve_and_validate_contacts(
        mesh, only_nm, expected_unit_nm=1.0).is_mesh_space
    # The default 8 nm reading of the same numbers is rejected, which shows the
    # declaration is actually honoured rather than cosmetic.
    with pytest.raises(cp.AmbiguousCoordinateFrame):
        cp.resolve_and_validate_contacts(mesh, only_nm)


def test_report_reverifies_the_frame_conversion(tmp_path):
    """The report re-derives every stored nm coordinate and refuses a mismatch."""
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 10000.0))
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0)])
    ct = _cell_type(999, (0.0, 0.0, 0.0))
    c = _FakeContact(_raw((5000.0, 5000.0, 5000.0)))
    frame = cp.resolve_and_validate_contacts(mesh, [c])
    assoc = cp.contact_mesh_associations(mesh, [c], frame)
    proj = cp.project_contacts_to_swc(skel, assoc)
    paths = cp.contact_root_paths(skel, proj)
    soma = cp.contact_soma_relations(skel, assoc, ct)
    ok = cp.contact_path_report(assoc, paths, soma, proj, skel, ct, mesh=mesh,
                                contacts=[c])
    assert ok["frame"]["resolved"] == frame.describe()
    # Tamper with the stored coordinate and the report must refuse it.
    import dataclasses
    bad = dataclasses.replace(assoc[0], xyz_nm=(1.0, 1.0, 1.0))
    with pytest.raises(cp.AmbiguousCoordinateFrame):
        cp.contact_path_report([bad], paths, soma, proj, skel, ct, mesh=mesh,
                               contacts=[c])


def test_associations_preserve_the_verbatim_source_label(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 10000.0))
    a = cp.contact_mesh_associations(
        mesh, [_FakeContact(_raw((5000.0, 5000.0, 5000.0)),
                            region="WTct(UTct-T2)(L)")],
        cp.FRAME_SWMC_RAW_8NM)[0]
    assert a.contact_class == "WTct"
    assert a.primary_post == "WTct(UTct-T2)(L)"


def test_ambiguous_coordinate_frame_is_rejected():
    with pytest.raises(cp.AmbiguousCoordinateFrame):
        cp.resolve_contact_frame([_FakeContact((1.0, 2.0, 3.0))],
                                 expected_unit_nm=None)
    with pytest.raises(cp.AmbiguousCoordinateFrame):
        cp.resolve_contact_frame([_FakeContact((1.0, 2.0, 3.0))],
                                 expected_unit_nm=3.0)
    # An unrecognised frame cannot convert.
    with pytest.raises(cp.AmbiguousCoordinateFrame):
        cp.CoordinateFrame("somewhere else", 2.0).to_nm((1.0, 2.0, 3.0))


def test_frame_check_catches_the_8x_error(tmp_path):
    """Raw 8 nm units fed to a nanometre-space mesh must be rejected."""
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 10000.0))
    c = _FakeContact((5000.0, 5000.0, 5000.0))  # raw -> 40000 nm, outside
    with pytest.raises(cp.AmbiguousCoordinateFrame):
        cp.assert_single_frame(mesh, [c], cp.FRAME_SWMC_RAW_8NM)


# --- 3, 4, 5: nearest surface, triangle, vertex ----------------------------


def test_nearest_surface_and_triangle_are_exact(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 1000.0))
    # 3 nm above the top face.
    p = (500.0, 500.0, 1003.0)
    assoc = cp.contact_mesh_associations(mesh, [_FakeContact(_raw((500.0, 500.0, 500.0)))], cp.FRAME_SWMC_RAW_8NM)
    assert len(assoc) == 1
    idx = mg.MeshSurfaceIndex(mesh)
    d, q, fi = idx.nearest_surface(p)
    assert d == pytest.approx(3.0, abs=1e-6)
    assert q == pytest.approx((500.0, 500.0, 1000.0), abs=1e-6)
    assert 0 <= fi < mesh.face_count
    # The reported nearest triangle really is the one touched.
    faces = mg._flat_faces(mesh)
    verts = mg._flat_vertices(mesh)
    t = tuple(faces[fi * 3 + k] for k in range(3))
    hit = False
    for a, b, c in ((0, 1, 2), (0, 2, 1), (1, 2, 0), (1, 0, 2), (2, 0, 1),
                    (2, 1, 0)):
        q2 = mg._closest_point_on_triangle(
            p, tuple(verts[t[a] * 3 + k] for k in range(3)),
            tuple(verts[t[b] * 3 + k] for k in range(3)),
            tuple(verts[t[c] * 3 + k] for k in range(3)))
        if math.dist(q2, p) == pytest.approx(d, abs=1e-9):
            hit = True
    assert hit


def test_surface_and_vertex_distances_are_kept_distinct(tmp_path):
    """A surface point mid-triangle has zero surface distance but non-zero
    vertex distance. The two must never be substituted for one another."""
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 1000.0))
    assoc = cp.contact_mesh_associations(
        mesh, [_FakeContact(_raw((500.0, 500.0, 500.0)))], cp.FRAME_SWMC_RAW_8NM)
    idx = mg.MeshSurfaceIndex(mesh)
    p = (500.0, 500.0, 1000.0)  # centre of the top face
    d, q, fi = idx.nearest_surface(p)
    vi, vd = idx.nearest_vertex(p)
    assert d == pytest.approx(0.0, abs=1e-6)
    assert vd > 100.0
    # And the module reports both, distinctly.
    raw = _FakeContact(_raw((500.0, 500.0, 1000.0)))
    a = cp.contact_mesh_associations(mesh, [raw], cp.FRAME_SWMC_RAW_8NM)[0]
    assert a.surface_distance_nm < a.vertex_distance_nm
    assert a.nearest_face_index == fi
    assert a.nearest_vertex_index == vi
    assert a.vertex_distance_nm == pytest.approx(vd, rel=1e-9)


def test_nearest_vertex_is_exact(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 1000.0))
    idx = mg.MeshSurfaceIndex(mesh)
    verts = mg._flat_vertices(mesh)
    p = (300.0, 700.0, 1100.0)
    vi, d = idx.nearest_vertex(p)
    best = min(range(mesh.vertex_count), key=lambda i: math.dist(
        (verts[i * 3], verts[i * 3 + 1], verts[i * 3 + 2]), p))
    assert vi == best
    assert d == pytest.approx(math.dist(
        (verts[best * 3], verts[best * 3 + 1], verts[best * 3 + 2]), p))


# --- 6: component association and ambiguity ---------------------------------


def test_nearest_component_is_identified_and_kept_separate(tmp_path):
    v1, f1 = _tetra(0, 0, 0, 1000.0)
    v2, f2 = _tetra(50000, 0, 0, 1000.0)
    mesh = _write_mesh(tmp_path, "two.ngmesh", v1 + v2,
                       f1 + [(a + 4, b + 4, c + 4) for a, b, c in f2])
    # 3 nm off the first tetrahedron's base face.
    raw = _FakeContact(_raw((500.0, 0.0, -3.0)))
    a = cp.contact_mesh_associations(mesh, [raw], cp.FRAME_SWMC_RAW_8NM)[0]
    assert a.nearest_component == 0
    assert a.runner_up_component == 1
    assert a.runner_up_distance_nm > 40000.0
    assert a.component_margin_ratio > 100.0
    assert a.association == cp.ASSOC_CONFIDENT


def test_ambiguous_association_is_reported_not_forced(tmp_path):
    """Two equidistant components must yield AMBIGUOUS, not a silent winner."""
    v1, f1 = _tetra(0, 0, 0, 1000.0)
    v2, f2 = _tetra(2000, 0, 0, 1000.0)
    mesh = _write_mesh(tmp_path, "amb.ngmesh", v1 + v2,
                       f1 + [(a + 4, b + 4, c + 4) for a, b, c in f2])
    # Equidistant from both bases.
    a = cp.contact_mesh_associations(mesh, [_FakeContact(_raw((1500.0, 0.0, -3.0)))], cp.FRAME_SWMC_RAW_8NM)[0]
    assert a.runner_up_component is not None
    assert a.component_margin_ratio < 1.5
    assert a.association == cp.ASSOC_AMBIGUOUS
    # The raw evidence is still carried so the reader can disagree.
    assert a.component_margin_nm is not None


def test_too_distant_contact_is_reported_using_the_mesh_own_scale(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 1000.0))
    scale = mg.mesh_sampling_scale_nm(mesh)["edge_length_nm_p95"]
    inside = cp.contact_mesh_associations(
        mesh, [_FakeContact(_raw((500.0, 500.0, 500.0)))], cp.FRAME_SWMC_RAW_8NM)[0]
    outside = cp.contact_mesh_associations(
        mesh, [_FakeContact(_raw((1000.0 + 3000.0, 500.0, 500.0)))],
        cp.FRAME_SWMC_RAW_8NM)[0]
    assert inside.association == cp.ASSOC_CONFIDENT
    assert outside.association == cp.ASSOC_TOO_DISTANT
    assert "95th" in outside.association_basis


def test_component_ranking_returns_distinct_components(tmp_path):
    v1, f1 = _tetra(0, 0, 0, 1000.0)
    v2, f2 = _tetra(3000, 0, 0, 1000.0)
    v3, f3 = _tetra(6000, 0, 0, 1000.0)
    faces = f1 + [(a + 4, b + 4, c + 4) for a, b, c in f2]
    faces = faces + [(a + 8, b + 8, c + 8) for a, b, c in f3]
    mesh = _write_mesh(tmp_path, "three.ngmesh", v1 + v2 + v3, faces)
    idx = mg.MeshSurfaceIndex(mesh)
    labels = mg.vertex_component_map(mesh)
    ranked = idx.nearest_surface_by_component((1500.0, 500.0, -3.0), n_best=3,
                                              labels=labels)
    assert len(ranked) == 3
    ids = [r[0] for r in ranked]
    assert len(set(ids)) == 3
    dists = [r[1] for r in ranked]
    assert dists == sorted(dists)


# --- 7: SWC graph projection ------------------------------------------------


def _assoc_stub(xyz_nm, surface_distance=1.0, cls="PDMN"):
    """A minimal MeshAssociation for tests that exercise the SWC stages only."""
    return cp.MeshAssociation(
        contact_index=0, pre_body=802401, post_body=999,
        primary_post=("WTct(UTct-T2)(L)" if cls == "WTct" else "PDMN(R)"),
        contact_class=cls,
        conf_pre=1.0, conf_post=1.0,
        raw_xyz=tuple(v / mi.MESH_TO_SWC_SCALE for v in xyz_nm),
        xyz_nm=tuple(xyz_nm), nearest_surface_xyz_nm=tuple(xyz_nm),
        nearest_face_index=0, surface_distance_nm=surface_distance,
        nearest_vertex_index=0, nearest_vertex_xyz_nm=tuple(xyz_nm),
        vertex_distance_nm=surface_distance, nearest_component=0,
        runner_up_component=None, runner_up_distance_nm=None,
        component_margin_nm=None, component_margin_ratio=None,
        association=cp.ASSOC_CONFIDENT, association_basis="synthetic")


def test_projection_lands_on_the_nearest_segment():
    # root 1 -> 2 -> 3 along x, in raw 8 nm units: 0, 4000, 8000 nm.
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 10.0, 500.0, 0.0, 0.0),
                        (3, 2, 10.0, 1000.0, 0.0, 0.0)])
    # 6000 nm along the second segment, 500 nm off the centerline.
    proj = cp.project_contacts_to_swc(skel, [_assoc_stub((7000.0, 500.0, 0.0),
                                                        500.0)])[0]
    assert proj.status == "PROJECTED"
    assert proj.projection_distance_nm == pytest.approx(500.0, abs=1e-6)
    assert proj.projection_xyz_nm == pytest.approx((7000.0, 0.0, 0.0), abs=1e-6)
    assert proj.nearest_segment_node_indices == (2, 3)
    # Nearest endpoint of the segment wins; node 3 has a parent, so a local
    # direction exists.
    assert proj.nearest_node_index == 3
    assert proj.local_path_direction[0] == pytest.approx(1.0)
    assert proj.local_radius_um == pytest.approx(10.0 * 8.0 / 1000.0)
    assert proj.local_child_degree == 0
    assert proj.projection_quantity().evidence is mi.EvidenceClass.MODEL_DERIVED_ESTIMATE
    assert "No compartment is assigned" in proj.note


def test_projection_clamps_to_segment_endpoints():
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 10.0, 1000.0, 0.0, 0.0)])
    proj = cp.project_contacts_to_swc(
        skel, [_assoc_stub((-5000.0, 0.0, 0.0), 1.0)])[0]
    assert proj.projection_xyz_nm[0] == pytest.approx(0.0)
    assert proj.projection_distance_nm == pytest.approx(5000.0, abs=1e-6)


def test_point_to_segment_distance_handles_degenerate_segment():
    d, q = cp._point_to_segment((3.0, 4.0, 0.0), (0.0, 0.0, 0.0),
                                (0.0, 0.0, 0.0))
    assert d == pytest.approx(5.0)
    assert q == (0.0, 0.0, 0.0)


# --- 8: root path -----------------------------------------------------------


def test_root_path_length_is_the_sum_of_segments():
    # Two collinear segments totalling 1000 + 2000 = 3000 nm.
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 10.0, 125.0, 0.0, 0.0),
                        (3, 2, 10.0, 375.0, 0.0, 0.0)])
    proj = cp.project_contacts_to_swc(skel, [_assoc_stub((6000.0, 0.0, 0.0))])
    assert proj[0].nearest_node_index == 3
    paths = cp.contact_root_paths(skel, proj)
    assert paths[0].status == "MEASURED"
    assert paths[0].root_index == 1
    assert paths[0].hop_count == 2
    assert paths[0].path_length_um == pytest.approx(3.0, rel=1e-9)
    q = paths[0].quantity()
    assert q.evidence is mi.EvidenceClass.MODEL_DERIVED_ESTIMATE
    assert "stalk origin" in q.note
    assert "Not an electrotonic distance" in q.note


def test_root_path_needs_exactly_one_root():
    two_roots = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                             (2, -1, 10.0, 100.0, 0.0, 0.0)])
    with pytest.raises(ValueError):
        cp.contact_root_paths(two_roots, [])


def test_unprojected_contact_yields_unresolved_root_path():
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 10.0, 1000.0, 0.0, 0.0)])
    proj = [cp.ContactProjection(
        contact_index=0, post_body=999, contact_class="PDMN",
        status=cp.UNRESOLVED, nearest_node_index=-1,
        nearest_node_xyz_raw=(0.0, 0.0, 0.0),
        nearest_segment_node_indices=(-1, -1),
        segment_xyz_nm=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        projection_xyz_nm=(0.0, 0.0, 0.0), projection_distance_nm=float("inf"),
        local_radius_raw=0.0, local_radius_um=0.0, local_child_degree=0,
        local_path_direction=None, note="synthetic")]
    paths = cp.contact_root_paths(skel, proj)
    assert paths[0].status == cp.UNRESOLVED
    assert math.isnan(paths[0].path_length_um)


# --- 9: soma distance, and the refusal to fake a soma path ------------------


def test_soma_euclidean_distance_is_reported_and_path_is_unresolved():
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 10.0, 1000.0, 0.0, 0.0)])
    # somaLocation 1000 nm along x from the root.
    ct = _cell_type(999, (125.0, 0.0, 0.0))
    rel = cp.contact_soma_relations(skel, [_assoc_stub((0.0, 0.0, 0.0))], ct)[0]
    assert rel.euclidean_um == pytest.approx(1.0, rel=1e-9)
    assert rel.graph_path_status == cp.UNRESOLVED
    assert rel.graph_path_um is None
    assert "no soma node" in rel.graph_path_reason
    assert rel.root_to_soma_euclidean_um == pytest.approx(1.0, rel=1e-9)
    assert rel.euclidean_quantity().evidence is mi.EvidenceClass.ANATOMICAL_MEASUREMENT
    assert cp.CONTACT_TO_SOMA_PATH == "UNRESOLVED"


def test_soma_relation_requires_an_annotation():
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0)])
    with pytest.raises(ValueError):
        cp.contact_soma_relations(skel, [], _cell_type(999, None))


# --- 10: class separation ---------------------------------------------------


def test_pdmn_and_wtct_are_kept_separate_and_never_relabelled():
    assert cp._contact_class("PDMN(R)") == "PDMN"
    assert cp._contact_class("WTct(UTct-T2)(L)") == "WTct"
    assert cp._contact_class("something else") == "something else"
    d = cp.class_geometry_comparison([], [], [], [])
    assert "PDMN is NOT assumed to be axon" in d["labels_preserved"]
    assert "WTct is NOT assumed to be dendrite" in d["labels_preserved"]
    assert "not among the dataset's named peripheral nerves" in (
        d["labels_preserved"])
    assert "No functional" in d["no_functional_inference"]


def test_wtct_is_not_a_named_peripheral_nerve_exit():
    # The source's exitNerve for both MN5 bodies is PDMNa; WTct is a primary_post
    # label, not an exit nerve. This test pins that distinction.
    ct = _cell_type(801295, (43450.0, 45480.0, 81574.0))
    assert ct.exit_nerve == "PDMNa"
    assert cp._contact_class("WTct(UTct-T2)(L)") != ct.exit_nerve


# --- 11: outliers -----------------------------------------------------------


def test_outliers_are_flagged_and_not_dropped():
    class _A:
        def __init__(self, i, d):
            self.contact_index = i
            self.post_body = 801970
            self.contact_class = "PDMN"
            self.surface_distance_nm = d
            self.association = cp.ASSOC_CONFIDENT
            self.runner_up_component = None
            self.component_margin_nm = None
    vals = [10.0, 11.0, 12.0, 13.0, 400.0]
    rep = cp.distance_validation([_A(i, d) for i, d in enumerate(vals)])
    assert rep["overall"]["n"] == 5
    assert rep["overall"]["max"] == 400.0
    assert len(rep["outliers"]) == 1
    o = rep["outliers"][0]
    assert o["contact_index"] == 4
    assert o["ratio_to_median"] > 3.0
    # Present in the distribution, not removed from it.
    assert rep["overall"]["n"] == len(vals)


def test_distance_validation_handles_empty_input():
    rep = cp.distance_validation([])
    assert rep["overall"]["n"] == 0
    assert rep["outliers"] == []
    assert rep["by_class"]["PDMN"]["n"] == 0


# --- 12, 13: provenance, SIZ, gates ----------------------------------------

FIVE_CLASSES = {e.value for e in mi.EvidenceClass}
assert len(FIVE_CLASSES) == 5


def test_provenance_has_exactly_five_categories():
    assert FIVE_CLASSES == {
        "native_experimental_measurement", "anatomical_measurement",
        "literature_derived_passive_parameter", "model_assumption",
        "model_derived_estimate"}


def test_every_quantity_carries_one_provenance_class(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 1000.0))
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 10.0, 8000.0, 0.0, 0.0)])
    ct = _cell_type(999, (125.0, 0.0, 0.0))
    contacts = [_FakeContact(_raw((500.0, 500.0, 500.0))),
                _FakeContact(_raw((600.0, 600.0, 600.0)), region="WTct(UTct-T2)(L)")]
    frame = cp.resolve_and_validate_contacts(mesh, contacts)
    assoc = cp.contact_mesh_associations(mesh, contacts, frame)
    proj = cp.project_contacts_to_swc(skel, assoc)
    paths = cp.contact_root_paths(skel, proj)
    soma = cp.contact_soma_relations(skel, assoc, ct)
    rep = cp.contact_path_report(assoc, paths, soma, proj, skel, ct, mesh=mesh,
                                 contacts=contacts)
    ledger = rep["provenance_ledger"]
    assert ledger
    for q in ledger:
        assert q["evidence"] in FIVE_CLASSES
        assert q["name"] and q["source"]
    # Aggregates are provenance-labelled too, not just per-contact values.
    names = " ".join(q["name"] for q in ledger)
    assert "contact set: surface distance aggregate" in names
    assert "contact set: root path aggregate" in names
    assert "contact set: distinct projected centreline nodes" in names
    # And the verbatim source label survives into every per-contact row.
    for row in rep["associations"]["by_contact"]:
        assert row["primary_post_verbatim"] in ("PDMN(R)", "WTct(UTct-T2)(L)")
    assert set(rep["provenance_counts"]) <= FIVE_CLASSES
    # Both classes actually appear, so the ledger is not vacuous.
    assert len(rep["provenance_counts"]) >= 2


def test_siz_mapping_is_unresolved_with_structural_reasons():
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0)])
    ct = _cell_type(999, (0.0, 0.0, 0.0))
    r = cp.siz_mapping(skel, ct, [])
    assert r["SIZ_MAPPING"] == "UNRESOLVED"
    assert r["node_kinds_present"] == [0]
    assert r["dendrite_labelled_nodes_present"] is False
    w = r["why_unresolved"]
    assert "ESTIMATE" in w
    assert "dendrite" in w
    assert "registration method" in w
    assert "NOT a SIZ" in r["shell_note"]


def test_gates_are_preserved_and_unchanged():
    g = cp.gates()
    assert g["spatial_voltage_transfer"] == (
        "PSI->MN5 spatial voltage transfer: NOT AUTHORIZED")
    assert g["dalpha7_biological_conductance"] == (
        "Dalpha7 biological conductance: NOT AUTHORIZED")
    assert g["status_field"] == "NOT AUTHORIZED"


def test_electrical_keys_are_rejected_at_any_depth():
    cp.assert_no_electrical_keys({"a": [{"b": 1}]})
    for bad in ("ra", "lambda", "electrotonic_distance", "attenuation",
                "transfer_resistance", "g_pas", "voltage_transfer"):
        with pytest.raises(AssertionError):
            cp.assert_no_electrical_keys({"x": {bad: 1.0}})
    with pytest.raises(AssertionError):
        cp.assert_no_electrical_keys([{"cm_specific": 1.0}])
    # A gate field holding a number is still rejected.
    with pytest.raises(AssertionError):
        cp.assert_no_electrical_keys({"spatial_voltage_transfer": 0.5})


def test_module_defines_no_electrical_conversion_helpers():
    for banned in ("electrotonic_distance", "length_constant", "space_constant",
                   "attenuation", "transfer_resistance", "axial_resistance",
                   "cable_diameter", "specific_membrane_capacitance"):
        assert not hasattr(cp, banned)
    note = cp.anatomy_only_scope_note()
    assert "NOT AUTHORIZED" in note
    assert "UNRESOLVED" in note


# --- optional: real MaleCNS data -------------------------------------------

_T = tempfile.gettempdir()
_SYN = os.path.join(_T, "syn-partners-male-cns-v1.0-minconf-0.5.feather")
_ANN = os.path.join(_T, "body-annotations-male-cns-v1.0-minconf-0.5.feather")
_MESH = {b: os.path.join(_T, f"mesh_{b}.ngmesh") for b in (801970, 801295)}
_SWC = {b: os.path.join(_T, f"em_{b}.swc") for b in (801970, 801295)}

_real = pytest.mark.skipif(
    not all(os.path.exists(p) for p in
            [_SYN, _ANN] + list(_MESH.values()) + list(_SWC.values())),
    reason="MaleCNS v1.0 source files are not present in this environment")


def _pipeline(body, contacts):
    mesh = mi.parse_male_ngmesh(_MESH[body], body)
    skel = mi.SkeletonGeometry.from_swc(_SWC[body], body_id=body)
    ct = mi.MaleCNSCellTypes(_ANN).row(body)
    frame = cp.resolve_and_validate_contacts(mesh, contacts)
    assoc = cp.contact_mesh_associations(mesh, contacts, frame)
    proj = cp.project_contacts_to_swc(skel, assoc)
    paths = cp.contact_root_paths(skel, proj)
    soma = cp.contact_soma_relations(skel, assoc, ct)
    return mesh, skel, ct, assoc, proj, paths, soma


@_real
def test_real_43_contacts_keep_their_source_counts():
    contacts = real_contacts()
    assert len(contacts) == 43
    left = [c for c in contacts if c.post_body == mi.MN5_LEFT]
    right = [c for c in contacts if c.post_body == mi.MN5_RIGHT]
    assert (len(left), len(right)) == (17, 26)
    # No cross-pairing: every PSI contacts only its own-side MN5.
    assert {c.pre_body for c in left} == {mi.PSI_LEFT}
    assert {c.pre_body for c in right} == {mi.PSI_RIGHT}


@_real
def test_real_contacts_all_place_near_the_mn5_surface():
    """Recomputes the 1.7-80.2 nm range from scratch and does not assume it."""
    contacts = real_contacts()
    all_d = []
    for body in (mi.MN5_LEFT, mi.MN5_RIGHT):
        grp = [c for c in contacts if c.post_body == body]
        mesh = mi.parse_male_ngmesh(_MESH[body], body)
        assoc = cp.contact_mesh_associations(mesh, grp, cp.FRAME_SWMC_RAW_8NM)
        assert len(assoc) == len(grp)
        for a in assoc:
            assert 0.0 <= a.surface_distance_nm < 200.0
            assert a.nearest_face_index >= 0
            assert a.nearest_component >= 0
            all_d.append(a.surface_distance_nm)
    assert len(all_d) == 43
    assert min(all_d) == pytest.approx(1.7, abs=0.2)
    assert max(all_d) == pytest.approx(80.2, abs=0.2)
    rep = cp.distance_validation(assoc)  # last body only; sanity of the API
    assert rep["overall"]["n"] == len(assoc)


@_real
def test_real_root_paths_are_measured_and_labelled_model_derived():
    contacts = real_contacts()
    grp = [c for c in contacts if c.post_body == mi.MN5_RIGHT]
    _m, _s, _c, assoc, proj, paths, _so = _pipeline(mi.MN5_RIGHT, grp)
    assert all(p.status == "MEASURED" for p in paths)
    for p in paths:
        assert p.path_length_um > 0
        assert p.hop_count > 0
        assert p.root_index == 1
    st = cp._stats([p.path_length_um for p in paths])
    # Contacts sit on processes a few hundred um from the stalk-origin root.
    assert 100.0 < st["min"] < st["max"] < 500.0


@_real
def test_real_soma_path_stays_unresolved_but_euclidean_is_reported():
    contacts = real_contacts()
    grp = [c for c in contacts if c.post_body == mi.MN5_LEFT]
    _m, skel, ct, assoc, proj, paths, soma = _pipeline(mi.MN5_LEFT, grp)
    assert not any(n.kind == 1 for n in skel.nodes)  # no soma node
    for s in soma:
        assert s.graph_path_status == "UNRESOLVED"
        assert s.graph_path_um is None
        assert s.euclidean_um > 0
    # The root is near the soma annotation but is NOT used as a proxy.
    st = cp._stats([s.root_to_soma_euclidean_um for s in soma])
    assert 20.0 < st["min"] < 30.0  # ~23.8 um for body 801970


@_real
def test_real_wtct_and_pdmn_are_separated_with_real_geometry():
    contacts = real_contacts()
    grp = [c for c in contacts if c.post_body == mi.MN5_RIGHT]
    _m, _s, _c, assoc, proj, paths, soma = _pipeline(mi.MN5_RIGHT, grp)
    rep = cp.class_geometry_comparison(assoc, paths, soma, proj)
    assert rep["by_class"]["PDMN"]["contact_count"] == 19
    assert rep["by_class"]["WTct"]["contact_count"] == 7
    assert rep["by_class"]["WTct"]["surface_distance_nm"]["n"] == 7
    assert rep["by_class"]["PDMN"]["surface_distance_nm"]["n"] == 19


@_real
def test_real_contacts_share_reconstructed_nodes_without_claiming_compartments():
    contacts = real_contacts()
    grp = [c for c in contacts if c.post_body == mi.MN5_LEFT]
    _m, _s, _c, assoc, proj, _p, _so = _pipeline(mi.MN5_LEFT, grp)
    rep = cp.contact_sharing_report(assoc, proj)
    b = rep["by_body"][str(mi.MN5_LEFT)]
    assert b["contact_count"] == 17
    assert b["distinct_swc_nodes"] <= 17
    # Sharing is reported as a reconstructed-location fact and nothing more.
    assert "No compartment" in rep["caveat"]


@_real
def test_real_full_report_is_anatomical_and_gated():
    contacts = real_contacts()
    grp = [c for c in contacts if c.post_body == mi.MN5_RIGHT]
    mesh, skel, ct, assoc, proj, paths, soma = _pipeline(mi.MN5_RIGHT, grp)
    rep = cp.contact_path_report(assoc, paths, soma, proj, skel, ct, mesh=mesh)
    assert rep["contacts"]["total"] == 26
    assert rep["contacts"]["by_class"] == {"PDMN": 19, "WTct": 7}
    assert rep["soma"]["contact_to_soma_graph_path"] == "UNRESOLVED"
    assert rep["soma"]["has_soma_node_in_skeleton"] is False
    assert rep["siz_mapping"]["SIZ_MAPPING"] == "UNRESOLVED"
    assert rep["authorization"]["electrical_modeling_performed"] is False
    assert rep["gates"]["spatial_voltage_transfer"].endswith("NOT AUTHORIZED")
    assert rep["gates"]["dalpha7_biological_conductance"].endswith(
        "NOT AUTHORIZED")
    assert rep["associations"]["reference_scale_nm"] > 0
    # Fragmentation must be stated, never read as branching.
    assert "does NOT establish a disconnected biological process" in (
        rep["mesh"]["fragmentation_note"])
    cp.assert_no_electrical_keys(rep)
    mg.assert_geometry_only({k: v for k, v in rep.items()
                             if k != "authorization"})

# --- 3.0D-8S: soma proxy registration, exact tree paths, ambiguity -----------

def test_soma_proxy_is_found_but_never_called_a_soma():
    """A soma-sized proximal node exists; it is still not a labelled soma."""
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 300.0, 1000.0, 0.0, 0.0)])
    # somaLocation 25 raw units (200 nm) off node 2, which is soma-scale.
    ct = _cell_type(999, (975.0, 0.0, 0.0))
    proxy = cp.locate_soma_proxy(skel, ct)
    assert proxy.node_index == 2
    assert proxy.node_kind == 0
    assert proxy.is_labelled_soma is False
    assert proxy.distance_to_soma_location_um == pytest.approx(0.2, rel=1e-6)
    assert proxy.radius_um == pytest.approx(300.0 * 8.0 / 1000.0)
    # The assumption is labelled as an assumption, not a measurement.
    q = proxy.assumption()
    assert q.evidence is mi.EvidenceClass.MODEL_ASSUMPTION
    assert "not asserted to be a soma" in q.note
    assert "PROXY" in q.note
    # And the labelled-soma constant stays UNRESOLVED.
    assert cp.CONTACT_TO_SOMA_PATH == "UNRESOLVED"


def test_soma_proxy_requires_the_annotation():
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0)])
    with pytest.raises(ValueError):
        cp.locate_soma_proxy(skel, _cell_type(999, None))


def test_tree_distance_is_exact_on_a_known_tree():
    # Chain 1->2->3->4 along x at 0, 1000, 3000, 6000 nm.
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 10.0, 125.0, 0.0, 0.0),
                        (3, 2, 10.0, 375.0, 0.0, 0.0),
                        (4, 3, 10.0, 750.0, 0.0, 0.0)])
    tree = cp._Tree(skel)
    assert tree.distance_um(1, 4)[0] == pytest.approx(6.0, rel=1e-9)
    assert tree.distance_um(2, 4)[0] == pytest.approx(5.0, rel=1e-9)
    assert tree.distance_um(3, 3)[0] == pytest.approx(0.0, abs=1e-12)
    assert tree.distance_um(1, 4)[1] == pytest.approx(0.0, abs=1e-12)
    assert tree.distance_um(3, 4)[1] == pytest.approx(3.0, rel=1e-9)


def test_branching_tree_distance_uses_the_shared_ancestor():
    # root 1 at x=0; branch 1->2->3 along +x; branch 1->4->5 along -x.
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 10.0, 1000.0, 0.0, 0.0),
                        (3, 2, 10.0, 3000.0, 0.0, 0.0),
                        (4, 1, 10.0, -1000.0, 0.0, 0.0),
                        (5, 4, 10.0, -3000.0, 0.0, 0.0)])
    tree = cp._Tree(skel)
    # Coordinates are raw 8 nm units: 1000 raw = 8000 nm = 8 um.
    # 3 -> 5 must pass back through the root: 24 + 8 + 16 = 48 um.
    d, shared = tree.distance_um(3, 5)
    assert d == pytest.approx(48.0, rel=1e-9)
    assert shared == pytest.approx(0.0, abs=1e-12)
    # 2 -> 3 shares the node-2 ancestor at depth 8 um.
    d2, shared2 = tree.distance_um(2, 3)
    assert d2 == pytest.approx(16.0, rel=1e-9)
    assert shared2 == pytest.approx(8.0, rel=1e-9)


def test_contact_soma_graph_path_is_partial_and_never_a_soma_claim():
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0),
                        (2, 1, 300.0, 1000.0, 0.0, 0.0),
                        (3, 2, 10.0, 3000.0, 0.0, 0.0)])
    # somaLocation exactly at node 2 (raw 1000 = 8000 nm).
    ct = _cell_type(999, (1000.0, 0.0, 0.0))
    proxy = cp.locate_soma_proxy(skel, ct)
    assert proxy.node_index == 2
    assoc = [_assoc_stub((3000.0, 100.0, 0.0), 100.0)]
    proj = cp.project_contacts_to_swc(skel, assoc)
    paths = cp.contact_soma_graph_paths(skel, proj, proxy, ct)
    assert paths[0].status == cp.SOMA_PATH_PARTIAL
    assert paths[0].soma_proxy_node_index == proxy.node_index
    assert paths[0].graph_path_um == pytest.approx(8.0, rel=1e-9)
    # Straight line and graph path are different numbers and both are kept.
    assert paths[0].graph_path_um != pytest.approx(paths[0].straight_line_um)
    assert paths[0].graph_path_um > 0
    q = paths[0].quantity()
    assert q.evidence is mi.EvidenceClass.MODEL_DERIVED_ESTIMATE
    assert "NOT a path to a labelled soma" in q.note
    assert "never substituted for this path" in q.note


def test_unprojected_contact_yields_unresolved_soma_path():
    skel = _chain_skel([(1, -1, 10.0, 0.0, 0.0, 0.0)])
    ct = _cell_type(999, (0.0, 0.0, 0.0))
    proxy = cp.locate_soma_proxy(skel, ct)
    proj = [cp.ContactProjection(
        contact_index=0, post_body=999, contact_class="PDMN",
        status=cp.UNRESOLVED, nearest_node_index=-1,
        nearest_node_xyz_raw=(0.0, 0.0, 0.0),
        nearest_segment_node_indices=(-1, -1),
        segment_xyz_nm=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        projection_xyz_nm=(0.0, 0.0, 0.0), projection_distance_nm=float("inf"),
        local_radius_raw=0.0, local_radius_um=0.0, local_child_degree=0,
        local_path_direction=None, note="synthetic")]
    paths = cp.contact_soma_graph_paths(skel, proj, proxy, ct)
    assert paths[0].status == cp.SOMA_PATH_UNRESOLVED
    assert math.isnan(paths[0].graph_path_um)


def test_ambiguous_report_keeps_the_verdict_and_records_the_centreline(
        tmp_path):
    v1, f1 = _tetra(0, 0, 0, 1000.0)
    v2, f2 = _tetra(2000, 0, 0, 1000.0)
    mesh = _write_mesh(tmp_path, "amb2.ngmesh", v1 + v2,
                       f1 + [(a + 4, b + 4, c + 4) for a, b, c in f2])
    a = cp.contact_mesh_associations(mesh,
                                     [_FakeContact(_raw((1500.0, 0.0, -3.0)))],
                                     cp.FRAME_SWMC_RAW_8NM)[0]
    rep = cp.ambiguous_contact_report([a], [])
    assert rep["ambiguous_count"] == 1
    row = rep["contacts"][0]
    assert row["verdict"] == cp.ASSOC_AMBIGUOUS
    assert row["mesh_nearest_component"] == a.nearest_component
    assert row["mesh_runner_up_component"] == a.runner_up_component
    assert row["mesh_margin_ratio"] == a.component_margin_ratio
    assert "NOT established" in row["note"]
    assert "convention" in rep["threshold_is_a_convention"]


def test_ambiguous_report_is_empty_when_all_are_confident():
    assert cp.ambiguous_contact_report([], [])["ambiguous_count"] == 0

@_real
def test_real_mn5_has_a_soma_region_but_no_soma_node():
    """The registration finding that changes the soma-path answer.

    Both MN5 skeletons carry a soma-sized proximal dilation adjacent to the
    annotated somaLocation, but no soma node exists, so the path to a labelled
    soma stays UNRESOLVED while a proxy path is PARTIALLY_RESOLVED.
    """
    for body in (mi.MN5_LEFT, mi.MN5_RIGHT):
        skel = mi.SkeletonGeometry.from_swc(_SWC[body], body_id=body)
        ct = mi.MaleCNSCellTypes(_ANN).row(body)
        assert not any(n.kind == 1 for n in skel.nodes)
        proxy = cp.locate_soma_proxy(skel, ct)
        assert proxy.is_labelled_soma is False
        # Soma-sized: a radius above 3 um is a soma-scale profile, not a twig.
        assert proxy.radius_um > 3.0
        # And it sits right on the annotated soma, not 20 um away.
        assert proxy.distance_to_soma_location_um < 3.0
        assert proxy.assumption().evidence is mi.EvidenceClass.MODEL_ASSUMPTION


@_real
def test_real_contact_to_soma_proxy_graph_path():
    contacts = real_contacts()
    for body, n_expected in ((mi.MN5_LEFT, 17), (mi.MN5_RIGHT, 26)):
        grp = [c for c in contacts if c.post_body == body]
        assert len(grp) == n_expected
        mesh, skel, ct, assoc, proj, paths, soma = _pipeline(body, grp)
        proxy = cp.locate_soma_proxy(skel, ct)
        g = cp.contact_soma_graph_paths(skel, proj, proxy, ct)
        assert len(g) == n_expected
        for row in g:
            assert row.status == cp.SOMA_PATH_PARTIAL
            assert row.graph_path_um > 0
            # A path is never shorter than the straight line it approximates.
            assert row.graph_path_um >= row.straight_line_um - 1e-6
            assert row.quantity().evidence is (
                mi.EvidenceClass.MODEL_DERIVED_ESTIMATE)
        stats = cp._stats([r.graph_path_um for r in g])
        assert 100.0 < stats["min"] < stats["max"] < 400.0
        # The labelled-soma constant must remain UNRESOLVED regardless.
        assert cp.CONTACT_TO_SOMA_PATH == "UNRESOLVED"


@_real
def test_real_ambiguous_contacts_stay_ambiguous_and_are_explained():
    contacts = real_contacts()
    grp = [c for c in contacts if c.post_body == mi.MN5_LEFT]
    _m, _s, _c, assoc, proj, _p, _so = _pipeline(mi.MN5_LEFT, grp)
    rep = cp.ambiguous_contact_report(assoc, proj)
    # The 3 ambiguous contacts on body 801970 are reported, not resolved.
    assert rep["ambiguous_count"] == 3
    for row in rep["contacts"]:
        assert row["verdict"] == cp.ASSOC_AMBIGUOUS
        assert row["mesh_runner_up_component"] is not None
        assert 1.0 <= row["mesh_margin_ratio"] < 1.5
        assert row["swc_node_index"] is not None
        assert "NOT established" in row["note"]
    # The runner-up is the same fragment in all three: a segmentation-level
    # ambiguity between two nearby pieces, not three independent findings.
    assert len({r["mesh_runner_up_component"]
                for r in rep["contacts"]}) == 1


@_real
def test_real_siz_stays_unresolved_with_verified_absences():
    skel = mi.SkeletonGeometry.from_swc(_SWC[mi.MN5_LEFT], body_id=mi.MN5_LEFT)
    ct = mi.MaleCNSCellTypes(_ANN).row(mi.MN5_LEFT)
    r = cp.siz_mapping(skel, ct, [])
    assert r["SIZ_MAPPING"] == "UNRESOLVED"
    assert r["dendrite_labelled_nodes_present"] is False
    assert r["dendrite_labelled_node_count"] == 0
    assert r["anterior_posterior_axis_documented"] is False
    assert r["requires_taxonomy_resolution"] is True
    assert "axis is documented anywhere in the available material" in (
        r["axis_evidence"])

# --- 3.0D-8T: SWC kind semantics are format codes, not biology --------------

def test_swc_type_codes_match_the_official_specification():
    """The codes are the SWC v1.0.0 Table 1 values, as FORMAT semantics."""
    assert mi.SWC_TYPE_CODES[0].startswith("Undefined")
    assert mi.SWC_TYPE_CODES[1] == "Soma"
    assert mi.SWC_TYPE_CODES[2] == "Axon"
    assert mi.SWC_TYPE_CODES[3] == "Basal dendrite"
    assert mi.SWC_TYPE_CODES[4] == "Apical dendrite"
    assert mi.SWC_TYPE_CODES[6].startswith("Unspecified neurite")
    assert mi.SWC_TYPE_CODES[7] == "Glia process"
    # Type 0 is explicitly NOT "dendrite" in the spec.
    assert "could correspond to any portion" in mi.SWC_TYPE_ZERO_NOTE


def test_malecns_node_type_biology_is_preserved_as_undefined():
    assert mi.MALECNS_NODE_TYPE_BIOLOGY == "UNDEFINED IN AVAILABLE SOURCE"
    assert "not documented" not in mi.MALECNS_SWC_SEMANTICS.lower()
    assert "UNDEFINED" in mi.MALECNS_SWC_SEMANTICS.upper() or \
        "does not document" in mi.MALECNS_SWC_SEMANTICS
    # The guard must say kind=2 is not established as axon.
    assert "NOT established" in mi.MALECNS_SWC_SEMANTICS
    assert "discards the node_type" in mi.MALECNS_SWC_SEMANTICS
    assert "not particularly significant" in mi.SWC_ROOT_SIGNIFICANCE_CAVEAT
    assert "no soma samples" in mi.SWC_SOMA_REPRESENTATION


def test_type_semantics_report_counts_codes_without_interpreting():
    # Built directly so the kinds are explicit: root kind 0, one kind-2 node.
    nodes = [mi.SwcNode(index=1, parent=-1, radius=10.0, kind=0,
                        x=0.0, y=0.0, z=0.0),
             mi.SwcNode(index=2, parent=1, radius=300.0, kind=2,
                        x=1000.0, y=0.0, z=0.0),
             mi.SwcNode(index=3, parent=2, radius=10.0, kind=0,
                        x=2000.0, y=0.0, z=0.0)]
    skel = mi.SkeletonGeometry(body_id=0, frame=mi.FRAME_EM_8NM,
                               unit_nm=mi.COORD_UNIT_NM, nodes=nodes)
    r = mi.swc_type_semantics(skel)
    assert r["kinds_present"] == [0, 2]
    assert r["node_count_by_kind"] == {0: 2, 2: 1}
    assert r["fraction_by_kind"][2] == pytest.approx(1 / 3)
    assert r["root_kinds"] == [0]
    assert r["has_soma_node_any_source"] is False
    # Format meanings travel with the codes.
    assert r["format_code_meanings"][0].startswith("Undefined")
    assert r["format_code_meanings"][2] == "Axon"
    # ...but the biological column stays undefined and guarded.
    assert r["malecns_biological_meaning"] == "UNDEFINED IN AVAILABLE SOURCE"
    assert "NOT counts of axons" in r["interpretation_guard"]
    # Cable accounting: both segments present, kind 2 carries the thick one.
    assert r["cable_length_um_by_kind"][0] > 0
    assert r["cable_length_um_by_kind"][2] > 0
    assert r["radius_um_by_kind"][2]["max"] > r["radius_um_by_kind"][0]["max"]
    assert "not particularly significant" in r["root_caveat"]


def test_module_never_equates_kind_two_with_axon():
    """Negative control: the code must not turn a format code into biology."""
    for src in (mi.MALECNS_SWC_SEMANTICS,
                mi.SWC_TYPE_ZERO_NOTE,
                mi.SWC_ROOT_SIGNIFICANCE_CAVEAT,
                mi.SWC_SOMA_REPRESENTATION):
        assert src
    assert not hasattr(mi, "SWC_KIND_TWO_IS_AXON")
    assert not hasattr(mi, "kind_to_compartment")
    assert not hasattr(cp, "kind_to_compartment")

@_real
def test_real_malecns_mn5_kind_convention_is_recorded_not_interpreted():
    """Pin the measured MN5 SWC convention as a regression guard.

    Both MN5 skeletons: zero kind==1, root kind==0, and kind==2 covering only a
    small minority of the arbor. Under the SWC spec kind==1 would be soma, so
    the absence is a real, verified fact about these files. It is reported; no
    biological label is attached to any code.
    """
    for body in (mi.MN5_LEFT, mi.MN5_RIGHT):
        skel = mi.SkeletonGeometry.from_swc(_SWC[body], body_id=body)
        r = mi.swc_type_semantics(skel)
        assert r["kinds_present"] == [0, 2], "unexpected third kind value"
        assert r["has_soma_node_any_source"] is False
        assert r["root_kinds"] == [0], "root is not kind 0"
        assert r["node_count_by_kind"][2] > 0
        # The overwhelming majority of the arbor carries the undefined code.
        assert r["fraction_by_kind"][0] > 0.9
        assert r["cable_fraction_by_kind"][0] > 0.9
        # kind=2 carries every large radius: it is a calibre-selected subset.
        assert r["radius_um_by_kind"][2]["max"] > 4.0
        assert r["radius_um_by_kind"][0]["max"] < r["radius_um_by_kind"][2]["max"]
        # The guard travels with the data.
        assert r["malecns_biological_meaning"] == "UNDEFINED IN AVAILABLE SOURCE"
        assert "NOT counts of axons" in r["interpretation_guard"]


@_real
def test_real_mn5_soma_region_proxy_node_is_kind_two_not_soma():
    """The proxy node is kind=2, which is another reason not to call it soma."""
    for body in (mi.MN5_LEFT, mi.MN5_RIGHT):
        skel = mi.SkeletonGeometry.from_swc(_SWC[body], body_id=body)
        ct = mi.MaleCNSCellTypes(_ANN).row(body)
        proxy = cp.locate_soma_proxy(skel, ct)
        node = skel.by_index()[proxy.node_index]
        # kind 2 is the SWC FORMAT code, whatever it may mean biologically.
        assert node.kind == 2
        assert proxy.is_labelled_soma is False
        assert proxy.radius_um > 3.0