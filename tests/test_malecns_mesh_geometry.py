"""Tests for MN5 .ngmesh surface geometry (3.0D-8Q).

Scope guard: this file exercises ANATOMICAL GEOMETRY ONLY. Every test here
either measures surface area, extent, topology, component membership or
contact position, or asserts that the NOT_AUTHORIZED electrical gate still
refuses. No test computes a length constant, electrotonic distance,
attenuation, transfer resistance, Cm, Rm, Ra or g_pas, and no test may be
added that does so.

Synthetic fixtures are small hand-built polyhedra used to pin down exact
values. They are NOT MN5 geometry and carry no biological meaning.
"""

import array
import math
import os
import struct
import tempfile

import pytest

from biological_brain import malecns_ingest as mi
from biological_brain import malecns_mesh_geometry as mg
from malecns_real_data import real_contacts


# --- synthetic fixtures ------------------------------------------------------


def _write_mesh(tmp_path, name, verts, faces, body=999):
    """Write a minimal .ngmesh from explicit vertex/face lists."""
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
    """A tetrahedron's 4 vertices and 4 outward-consistent faces."""
    verts = [(ox, oy, oz), (ox + s, oy, oz), (ox, oy + s, oz), (ox, oy, oz + s)]
    faces = [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)]
    return verts, faces


def _cube(ox, oy, oz, s):
    """Axis-aligned cube: 6 quads, 12 triangles, total area exactly 6s^2."""
    verts = [(ox + (s if i & 1 else 0), oy + (s if i & 2 else 0),
              oz + (s if i & 4 else 0)) for i in range(8)]
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    faces = []
    for a, b, c, d in quads:
        faces.append((a, b, c))
        faces.append((a, c, d))
    return verts, faces


# --- 2, 3, 4: area by two independent formulae -------------------------------


def test_cube_area_is_exact_and_both_formulae_agree(tmp_path):
    s = 1000.0
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, s))
    cross, deg = mg.mesh_surface_area(mesh, "cross")
    heron, deg_h = mg.mesh_surface_area(mesh, "heron")
    assert cross == pytest.approx(6 * s * s, rel=1e-12)
    assert heron == pytest.approx(6 * s * s, rel=1e-9)
    assert deg == 0
    assert deg_h == 0
    assert cross == pytest.approx(heron, rel=1e-9)


def test_area_methods_reject_unknown_name(tmp_path):
    mesh = _write_mesh(tmp_path, "c.ngmesh", *_cube(0, 0, 0, 10.0))
    with pytest.raises(ValueError):
        mg.mesh_surface_area(mesh, "shoelace")


def test_non_xy_triangle_separates_projection_from_surface_area(tmp_path):
    """Regression guard: the XY-projection formula is NOT a surface area.

    A single triangle in the XZ plane has full 3D area but ZERO XY projection.
    An earlier version of this module used the shoelace formula as its
    independent area check, which silently returned the projection and
    disagreed with the cross product by 113% on the real meshes. The
    independent method must be Heron, and the projection must be reported as
    its own quantity.
    """
    verts = [(0.0, 5.0, 0.0), (1000.0, 5.0, 0.0), (0.0, 5.0, 1000.0)]
    faces = [(0, 1, 2)]
    mesh = _write_mesh(tmp_path, "xz.ngmesh", verts, faces)
    cross, _ = mg.mesh_surface_area(mesh, "cross")
    heron, _ = mg.mesh_surface_area(mesh, "heron")
    projected = mg.mesh_projected_area_nm2(mesh)
    assert cross == pytest.approx(0.5 * 1000.0 * 1000.0, rel=1e-6)
    assert heron == pytest.approx(cross, rel=1e-9)
    assert projected == pytest.approx(0.0, abs=1e-6)


def test_chunking_does_not_change_the_total(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 500.0))
    base, _ = mg.mesh_surface_area(mesh, "cross", chunk=10 ** 9)
    for chunk in (1, 2, 3, 5, 12):
        got, _ = mg.mesh_surface_area(mesh, "cross", chunk=chunk)
        assert got == pytest.approx(base, rel=1e-12)


def test_validate_area_reports_both_formulae_and_sample_discrepancy(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 300.0))
    v = mg.validate_area(mesh, sample=50)
    assert v["cross_area_nm2"] == pytest.approx(6 * 300.0 ** 2, rel=1e-12)
    assert v["heron_area_nm2"] == pytest.approx(v["cross_area_nm2"], rel=1e-9)
    assert v["aggregate_relative_difference"] < 1e-9
    assert v["sample_count"] == 50
    assert v["sample_max_relative_difference"] < 1e-6
    assert "projected_area_xy_nm2" in v


def test_degenerate_and_duplicate_faces_are_counted_not_dropped(tmp_path):
    # A collinear triangle has zero area but is still a face in the file.
    verts = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0),
             (0.0, 10.0, 0.0)]
    faces = [(0, 1, 2), (0, 3, 1), (0, 1, 3)]
    mesh = _write_mesh(tmp_path, "degen.ngmesh", verts, faces)
    total, deg = mg.mesh_surface_area(mesh, "cross")
    assert deg == 1
    # Heron is the fragile path on a sliver: it reports the sliver as zero too.
    assert mg.mesh_surface_area(mesh, "heron")[1] == 1
    assert total == pytest.approx(100.0, rel=1e-9)
    t = mg.mesh_topology(mesh)
    assert t["degenerate_faces"] == 1
    assert t["duplicate_faces"] == 1


# --- 5, 6: topology and components ------------------------------------------


def test_closed_cube_has_no_boundary_edges(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 100.0))
    t = mg.mesh_topology(mesh)
    assert t["boundary_edges"] == 0
    assert t["non_manifold_edges"] == 0
    assert t["duplicate_faces"] == 0
    assert t["isolated_vertices"] == 0
    assert t["closed_surface"] is True
    # Euler characteristic of a sphere-like closed surface is 2.
    assert t["euler_characteristic"] == 2
    # 12 triangles -> 18 edge slots -> 9 distinct edges for a cube.
    assert t["edge_face_slots"] == 36
    assert t["distinct_edges"] == 18
    assert t["interior_edges"] == 18


def test_topology_edge_accounting_is_internally_consistent(tmp_path):
    """Regression guard: distinct edges must not be mixed with edge slots."""
    v, f = _tetra(0, 0, 0, 100.0)
    mesh = _write_mesh(tmp_path, "t.ngmesh", v, f)
    t = mg.mesh_topology(mesh)
    assert t["distinct_edges"] == (t["interior_edges"] + t["boundary_edges"]
                                   + t["non_manifold_edges"])
    assert t["edge_face_slots"] == 3 * mesh.face_count
    assert t["euler_characteristic"] == (mesh.vertex_count - t["distinct_edges"]
                                         + mesh.face_count)
    # A closed tetrahedron: every edge shared by exactly two faces.
    assert t["interior_edges"] == 6
    assert t["distinct_edges"] == 6


def test_open_triangle_reports_boundary_edges(tmp_path):
    verts = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 10.0, 0.0)]
    mesh = _write_mesh(tmp_path, "open.ngmesh", verts, [(0, 1, 2)])
    t = mg.mesh_topology(mesh)
    assert t["boundary_edges"] == 3
    assert t["interior_edges"] == 0
    assert t["closed_surface"] is False


def test_non_manifold_edge_is_reported(tmp_path):
    # Three triangles sharing one edge -> that edge is non-manifold.
    verts = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
             (0.0, 0.0, 1.0), (0.0, 0.0, -1.0), (1.0, 1.0, 1.0)]
    faces = [(0, 1, 2), (0, 1, 3), (0, 1, 4), (1, 2, 5)]
    mesh = _write_mesh(tmp_path, "nm.ngmesh", verts, faces)
    t = mg.mesh_topology(mesh)
    assert t["non_manifold_edges"] == 1
    assert t["non_manifold_edge_face_slots"] == 3
    assert t["closed_surface"] is False


def test_isolated_vertex_is_counted(tmp_path):
    v, f = _tetra(0, 0, 0, 10.0)
    mesh = _write_mesh(tmp_path, "iso.ngmesh", v + [(99.0, 99.0, 99.0)], f)
    t = mg.mesh_topology(mesh)
    assert t["isolated_vertices"] == 1
    labels = mg.vertex_component_map(mesh)
    assert labels[len(v)] == -1


def test_two_disjoint_tetrahedra_are_two_components(tmp_path):
    v1, f1 = _tetra(0, 0, 0, 100.0)
    v2, f2 = _tetra(1000, 0, 0, 100.0)
    verts = v1 + v2
    faces = f1 + [(a + 4, b + 4, c + 4) for a, b, c in f2]
    mesh = _write_mesh(tmp_path, "two.ngmesh", verts, faces)
    comps, n = mg.mesh_components(mesh)
    assert n == 2
    assert [c.component_id for c in comps] == [0, 1]
    # A right tetrahedron on the axes: three right faces of area s^2/2 plus one
    # equilateral face of side s*sqrt(2), area (sqrt(3)/4)*2s^2.
    expected = 3 * (100.0 ** 2 / 2) + (math.sqrt(3) / 2) * 100.0 ** 2
    assert comps[0].surface_area_nm2 == pytest.approx(expected, rel=1e-6)
    assert comps[1].surface_area_nm2 == pytest.approx(expected, rel=1e-6)
    labels = mg.vertex_component_map(mesh)
    assert labels[0] == 0
    assert labels[4] == 1


def test_components_are_labelled_topologically_never_anatomically(tmp_path):
    v1, f1 = _tetra(0, 0, 0, 100.0)
    v2, f2 = _tetra(1000, 0, 0, 100.0)
    mesh = _write_mesh(tmp_path, "two.ngmesh", v1 + v2,
                       f1 + [(a + 4, b + 4, c + 4) for a, b, c in f2])
    comps, _ = mg.mesh_components(mesh)
    names = {f for c in comps for f in dir(c) if not f.startswith("_")}
    for banned in mg.PROHIBITED_COMPONENT_LABELS:
        assert banned not in names
    q = comps[0].provenance()
    assert isinstance(q, mi.ProvenanceQuantity)
    assert q.evidence is mi.EvidenceClass.ANATOMICAL_MEASUREMENT
    assert "NOT labelled" in q.note


# --- 7: soma inclusion is never decided -------------------------------------


def test_soma_inclusion_is_unresolved_even_for_a_perfect_sphere(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 100.0))
    s = mg.assess_soma_inclusion(mesh)
    assert s.status == mg.SOMA_INCLUSION_UNRESOLVED
    assert s.status == "UNRESOLVED"
    assert "no anatomical" in s.reason
    assert "soma" in mg.PROHIBITED_COMPONENT_LABELS


def test_soma_assessment_does_not_accept_a_swc_root_as_a_soma(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 100.0))
    without = mg.assess_soma_inclusion(mesh)
    with_root = mg.assess_soma_inclusion(mesh, swc_root_nm=(0.0, 0.0, 0.0))
    assert with_root.status == without.status == "UNRESOLVED"
    assert isinstance(with_root.evidence_missing, str)
    assert "stalk origin" in with_root.evidence_missing
    assert "promoted to a soma location" in with_root.evidence_missing
    assert with_root.provenance().evidence is mi.EvidenceClass.ANATOMICAL_MEASUREMENT


def test_soma_assessment_cannot_be_constructed_with_a_decided_status():
    with pytest.raises(ValueError):
        mg.SomaInclusionAssessment(
            status="INCLUDED", reason="r", evidence_available="e",
            evidence_missing="m", would_resolve="w", prohibited_labels=("soma",))
    with pytest.raises(TypeError):
        mg.SomaInclusionAssessment(
            status="UNRESOLVED", reason="r", evidence_available="e",
            evidence_missing=("tuple",), would_resolve="w",
            prohibited_labels=("soma",))


# --- 8: contact placement, and the 8 nm -> nm conversion ---------------------


class _FakeContact:
    def __init__(self, raw, pre=1, post=2, conf_pre=1.0, conf_post=1.0,
                 region="PDMN(R)"):
        self.pre_body = pre
        self.post_body = post
        self.pre_xyz = raw
        self.post_xyz = raw
        self.conf_pre = conf_pre
        self.conf_post = conf_post
        self.primary_post = region


def test_contact_is_scaled_from_raw_units_into_mesh_nanometres(tmp_path):
    """Regression guard for the 8x frame error.

    Contact coordinates are ingested in the raw 8 nm units of the connectome;
    the mesh is in nanometres. Passing the raw value through unconverted put
    every contact ~729 um from a mesh spanning only 184 um, which still looked
    like a plausible number. The conversion must be explicit and enforced.
    """
    s = 1000.0
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, s))
    # A point on the top face (z = s = 1000 nm), expressed in raw 8 nm units:
    # (800, 800, 1000) nm == (100, 100, 125) raw.
    raw = (100.0, 100.0, 125.0)
    prox = mg.contact_geometry_report(mesh, [_FakeContact(raw)])
    p = prox[0]
    assert p.post_xyz_nm == (800.0, 800.0, 1000.0)
    assert p.post_xyz_raw == raw
    # The converted point lies on the top face of the cube: z = s = 1000 nm.
    assert p.surface_distance_nm == pytest.approx(0.0, abs=1e-3)
    assert p.nearest_surface_xyz_nm[2] == pytest.approx(s, rel=1e-6)
    assert p.nearest_vertex_xyz_nm[2] == pytest.approx(s, rel=1e-6)


def test_unconverted_contact_frame_raises_instead_of_reporting_a_far_distance(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 100.0))
    # A raw coordinate far outside the mesh in nm space: the frame is wrong.
    with pytest.raises(mg.ContactFrameError):
        mg.contact_geometry_report(mesh, [_FakeContact((900000.0, 0.0, 0.0))])


def test_contact_proximity_reports_vertex_surface_and_component(tmp_path):
    v, f = _tetra(0, 0, 0, 100.0)
    mesh = _write_mesh(tmp_path, "t.ngmesh", v, f)
    # Just outside a face of the tetrahedron, expressed in raw 8 nm units.
    raw = (12.5 / mg.MESH_TO_SWC_SCALE, 12.5 / mg.MESH_TO_SWC_SCALE, 0.0)
    p = mg.contact_geometry_report(mesh, [_FakeContact(raw)])[0]
    assert p.surface_distance_nm == pytest.approx(0.0, abs=1e-3)
    assert p.vertex_distance_nm >= p.surface_distance_nm
    assert p.component_id == 0
    assert p.surface_face_index >= 0
    assert "NOT a conduction path" in p.note


def test_point_to_triangle_distance_covers_vertex_edge_and_interior(tmp_path):
    a, b, c = (0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 10.0, 0.0)
    # Above an interior point.
    q = mg._closest_point_on_triangle((1.0, 1.0, 5.0), a, b, c)
    assert q == pytest.approx((1.0, 1.0, 0.0), rel=1e-9)
    # Beyond a vertex.
    q = mg._closest_point_on_triangle((-5.0, -5.0, 0.0), a, b, c)
    assert q == pytest.approx(a, rel=1e-9)
    # Off the midpoint of the b-c edge.
    q = mg._closest_point_on_triangle((5.0, 5.0, 3.0), a, b, c)
    assert q == pytest.approx((5.0, 5.0, 0.0), rel=1e-9)


def test_surface_index_matches_brute_force_on_a_cube(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 1000.0))
    idx = mg.MeshSurfaceIndex(mesh, target_faces_per_cell=1)
    for raw in ((50.0, 50.0, 175.0), (187.5, 62.5, 62.5), (-5.0, 2.5, 2.5)):
        p = (raw[0] * mg.MESH_TO_SWC_SCALE, raw[1] * mg.MESH_TO_SWC_SCALE,
             raw[2] * mg.MESH_TO_SWC_SCALE)
        d, pt, fi = idx.nearest_surface(p)
        # Brute force over every triangle.
        verts = mg._flat_vertices(mesh)
        faces = mg._flat_faces(mesh)
        best = float("inf")
        for i in range(0, 3 * mesh.face_count, 3):
            t = (faces[i], faces[i + 1], faces[i + 2])
            q = mg._closest_point_on_triangle(
                p, (verts[t[0] * 3], verts[t[0] * 3 + 1], verts[t[0] * 3 + 2]),
                (verts[t[1] * 3], verts[t[1] * 3 + 1], verts[t[1] * 3 + 2]),
                (verts[t[2] * 3], verts[t[2] * 3 + 1], verts[t[2] * 3 + 2]))
            best = min(best, math.dist(q, p))
        assert d == pytest.approx(best, rel=1e-9)
        assert fi >= 0


def test_nearest_vertex_matches_brute_force(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 1000.0))
    idx = mg.MeshSurfaceIndex(mesh)
    verts = mg._flat_vertices(mesh)
    for p in ((300.0, 700.0, 1100.0), (-100.0, 0.0, 0.0), (1500.0, 900.0, 0.0)):
        vi, d = idx.nearest_vertex(p)
        best = min(range(mesh.vertex_count), key=lambda i: math.dist(
            (verts[i * 3], verts[i * 3 + 1], verts[i * 3 + 2]), p))
        assert vi == best
        assert d == pytest.approx(math.dist(
            (verts[best * 3], verts[best * 3 + 1], verts[best * 3 + 2]), p),
            rel=1e-12)


# --- 9: area comparison keeps domains apart ---------------------------------


def test_swc_lateral_area_states_its_assumption(tmp_path):
    p = tmp_path / "seg.swc"
    # One segment of length 100 um, constant radius 5 um, file already in um.
    p.write_text("1 0 0.0 0.0 0.0 5.0 -1\n2 0 100.0 0.0 0.0 5.0 1\n",
                 encoding="utf-8")
    skel = mi.SkeletonGeometry.from_swc(str(p), body_id=0, unit_nm=1000.0)
    r = mg.swc_lateral_area_um2(skel)
    assert r["segment_count"] == 1
    # Lateral area of a cylinder: 2*pi*r*L.
    assert r["lateral_area_um2"] == pytest.approx(2 * math.pi * 5.0 * 100.0,
                                                  rel=1e-9)
    assert r["evidence"] is mi.EvidenceClass.MODEL_DERIVED_ESTIMATE
    assert "truncated cone" in r["model"]
    assert "forbidden" in r["note"]


def test_area_comparison_never_claims_the_domains_match():
    c = mg.compare_areas(1.0e10, swc_total_um2=25000.0, literature_um2=13000.0,
                         literature_domain="central sub-region only")
    assert c.comparability == "NOT_COMPARABLE_WITHOUT_DOMAIN_CAVEAT"
    assert c.mesh_total_um2 == pytest.approx(10000.0, rel=1e-9)
    assert c.mesh_over_swc_ratio == pytest.approx(0.4, rel=1e-9)
    assert c.mesh_minus_swc_um2 == pytest.approx(-15000.0, rel=1e-9)
    assert c.literature_domain == "central sub-region only"
    joined = " ".join(c.caveats)
    assert "not a validation" in joined
    assert "NOT AUTHORIZED" in joined


def test_area_comparison_handles_absent_references():
    c = mg.compare_areas(1.0e9)
    assert c.swc_total_um2 is None
    assert c.literature_um2 is None
    assert c.mesh_over_swc_ratio is None
    assert c.mesh_minus_swc_um2 is None


# --- 10: the electrical gate stays shut -------------------------------------


def test_geometry_cannot_produce_an_electrical_parameter():
    with pytest.raises(mi.BiologicalTransferNotAuthorized):
        mg.deriving_electrical_quantity_from_geometry()
    assert mi.biological_transfer_status() == "NOT AUTHORIZED"


def test_geometry_module_exposes_no_electrical_conversion():
    for banned in ("cm_from_area", "axial_resistivity", "length_constant",
                   "electrotonic_distance", "g_pas", "transfer_resistance"):
        assert not hasattr(mg, banned)
    for cls in (mg.ComponentSummary, mg.ContactProximity, mg.AreaComparison,
                mg.SomaInclusionAssessment, mg.MeshSurfaceIndex):
        names = {n.lower() for n in dir(cls)}
        for banned in mg.FORBIDDEN_ELECTRICAL_KEYS:
            assert banned not in names


def test_assert_geometry_only_rejects_electrical_keys():
    mg.assert_geometry_only({"area": {"total_nm2": 1.0}, "components": []})
    with pytest.raises(AssertionError):
        mg.assert_geometry_only({"area": {"total_nm2": 1.0}, "Cm": 1.15})
    with pytest.raises(AssertionError):
        mg.assert_geometry_only({"nested": [{"length_constant": 5.0}]})


def test_synthetic_report_is_anatomical_and_complete(tmp_path):
    mesh = _write_mesh(tmp_path, "cube.ngmesh", *_cube(0, 0, 0, 1000.0))
    contacts = [_FakeContact((12.5, 12.5, 12.5)),
                _FakeContact((62.5, 62.5, 125.0), region="WTct(UTct-T2)(L)")]
    rep = mg.mesh_geometry_report(mesh, contacts, swc_total_um2=12000.0,
                                  literature_um2=6000.0)
    assert rep["area"]["total_um2"] == pytest.approx(6.0, rel=1e-9)
    assert rep["topology"]["closed_surface"] is True
    assert rep["components"]["count"] == 1
    assert rep["soma_inclusion"]["status"] == "UNRESOLVED"
    assert rep["contact_proximity"]["count"] == 2
    assert set(rep["contact_proximity"]["by_primary_post"]) == {
        "PDMN(R)", "WTct(UTct-T2)(L)"}
    assert rep["scope"]["anatomy_only"] is True
    assert rep["scope"]["biological_transfer_status"] == "NOT AUTHORIZED"
    mg.assert_geometry_only(rep)


def test_scope_note_states_the_boundaries():
    note = mg.geometry_scope_note()
    assert "UNRESOLVED" in note
    assert "NOT AUTHORIZED" in note
    assert "stalk origin" in note


# --- optional: real MaleCNS source data ------------------------------------

_T = tempfile.gettempdir()
_SYN = os.path.join(_T, "syn-partners-male-cns-v1.0-minconf-0.5.feather")
_MESHES = {801970: os.path.join(_T, "mesh_801970.ngmesh"),
           801295: os.path.join(_T, "mesh_801295.ngmesh")}
_SWC = {801970: os.path.join(_T, "em_801970.swc"),
        801295: os.path.join(_T, "em_801295.swc")}

_real = pytest.mark.skipif(
    not os.path.exists(_SYN)
    or not all(os.path.exists(p) for p in list(_MESHES.values()) + list(_SWC.values())),
    reason="MaleCNS v1.0 source files are not present in this environment")


def _real_mesh(body):
    return mi.parse_male_ngmesh(_MESHES[body], body)


@_real
@pytest.mark.parametrize("body", (801970, 801295))
def test_real_mesh_area_formulae_agree(body):
    mesh = _real_mesh(body)
    v = mg.validate_area(mesh, sample=200)
    assert v["cross_area_nm2"] > 0
    # Two independent formulae must agree to near round-off on the real mesh.
    assert v["aggregate_relative_difference"] < 1e-9
    assert v["sample_max_relative_difference"] < 1e-6
    assert v["degenerate_faces_cross"] == 0
    # The projection is a different quantity and must not be reported as area.
    assert v["projected_area_xy_nm2"] < v["cross_area_nm2"]


@_real
@pytest.mark.parametrize("body", (801970, 801295))
def test_real_mesh_topology_is_reported_without_repair(body):
    mesh = _real_mesh(body)
    t = mg.mesh_topology(mesh)
    assert t["distinct_edges"] == (t["interior_edges"] + t["boundary_edges"]
                                   + t["non_manifold_edges"])
    assert t["euler_characteristic"] == (mesh.vertex_count - t["distinct_edges"]
                                         + mesh.face_count)
    assert t["isolated_vertices"] == 0
    # Recorded as measured, whatever it is: this module repairs nothing.
    assert isinstance(t["closed_surface"], bool)
    assert t["edge_face_slots"] == 3 * mesh.face_count


@_real
@pytest.mark.parametrize("body", (801970, 801295))
def test_real_mesh_is_fragmented_and_no_component_is_labelled(body):
    mesh = _real_mesh(body)
    comps, n = mg.mesh_components(mesh, max_reported=3)
    assert n > 1
    for c in comps:
        assert c.component_id in (0, 1, 2)
        assert "NOT labelled" in c.provenance().note


@_real
@pytest.mark.parametrize("body", (801970, 801295))
def test_real_mesh_soma_stays_unresolved(body):
    s = mg.assess_soma_inclusion(_real_mesh(body))
    assert s.status == "UNRESOLVED"
    assert s.would_resolve


@_real
def test_real_43_contacts_all_land_on_the_surface_in_the_right_frame():
    """Every contact must place near the mesh, in nanometres.

    This is the guard on the frame/unit conversion. If the raw 8 nm units were
    used directly, distances would come out around 729 um on a mesh spanning
    184 um; the test asserts the contacts sit within a few hundred nm instead.
    """
    contacts = real_contacts()
    assert len(contacts) == 43
    per_body = {mi.MN5_LEFT: [], mi.MN5_RIGHT: []}
    for c in contacts:
        per_body[c.post_body].append(c)
    assert len(per_body[mi.MN5_LEFT]) == 17
    assert len(per_body[mi.MN5_RIGHT]) == 26
    for body, group in per_body.items():
        mesh = _real_mesh(body)
        prox = mg.contact_geometry_report(mesh, group)
        assert len(prox) == len(group)
        for p in prox:
            # Raw units are 8x smaller than the mesh-space nanometres.
            assert p.post_xyz_nm[0] == pytest.approx(p.post_xyz_raw[0] * 8.0)
            assert p.surface_distance_nm >= 0.0
            assert p.surface_distance_nm < 500.0
            assert p.component_id >= 0


@_real
def test_real_contacts_keep_central_and_peripheral_regions_separate():
    contacts = real_contacts()
    group = [c for c in contacts if c.post_body == mi.MN5_RIGHT]
    prox = mg.contact_geometry_report(_real_mesh(mi.MN5_RIGHT), group)
    regions = {p.primary_post for p in prox}
    # Both a central and a peripheral label are present and are not pooled.
    assert "PDMN(L)" in regions
    assert any(r.startswith("WTct") for r in regions)
    by_region = mg._group_by_region(prox)
    assert sum(len(g) for g in by_region.values()) == len(prox)
    assert {k: len(v) for k, v in by_region.items()} == {
        "PDMN(L)": 19, "WTct(UTct-T2)(L)": 7}


@_real
def test_real_mesh_area_is_beside_not_equal_to_reference_areas():
    body = mi.MN5_LEFT
    mesh = _real_mesh(body)
    skel = mi.SkeletonGeometry.from_swc(_SWC[body], body_id=body)
    swc_area = mg.swc_lateral_area_um2(skel)["lateral_area_um2"]
    rep = mg.mesh_geometry_report(mesh, [], swc_total_um2=swc_area,
                                  literature_um2=13000.0,
                                  literature_domain="central sub-region")
    a = rep["area"]
    c = rep["comparison"]
    assert a["total_um2"] > 0
    assert c["swc_total_um2"] == pytest.approx(swc_area, rel=1e-12)
    assert c["comparability"] == "NOT_COMPARABLE_WITHOUT_DOMAIN_CAVEAT"
    assert c["literature_domain"] == "central sub-region"
    assert c["caveats"]
    # The whole-neuron mesh total and a central-only literature area differ in
    # domain; the report must never pretend they are the same quantity.
    assert c["mesh_total_um2"] != pytest.approx(13000.0, rel=1e-6)
    mg.assert_geometry_only(rep)


@_real
def test_real_swc_lateral_area_reproduces_the_known_figure():
    """Independently re-derive the ~24,804 um^2 figure for body 801970."""
    skel = mi.SkeletonGeometry.from_swc(_SWC[801970], body_id=801970)
    r = mg.swc_lateral_area_um2(skel)
    assert r["lateral_area_um2"] == pytest.approx(24803.7, rel=1e-3)
    assert r["segment_count"] == r["node_count"] - 1
