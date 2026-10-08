"""Focused tests for the MaleCNS .ngmesh binary parser.

Scope is deliberately narrow: binary-format decoding and its validation. NO
test here computes a surface area, a volume, a cable diameter, a path length or
any electrical quantity, and the NOT_AUTHORIZED gate is asserted intact.
"""

import hashlib
import os
import struct
import tempfile

import pytest

from biological_brain import malecns_ingest as mi

T = tempfile.gettempdir()
_MESHES = {801970: os.path.join(T, "mesh_801970.ngmesh"),
            801295: os.path.join(T, "mesh_801295.ngmesh")}
_SWC = {801970: os.path.join(T, "em_801970.swc"),
        801295: os.path.join(T, "em_801295.swc")}

#: Full hashes verified during the reverse-engineering checkpoint.
EXPECTED_SHA = {
    801970: "034dffd0009e48fa65868124724b1fd1394a8aca2b7ec73306aa443697c35057",
    801295: "0715bfb28230e79eaa9a2ae932f266f10e9c4a7cdeae3fed06ca24f4a2420913",
}

_all_present = all(os.path.exists(p) for p in
                   list(_MESHES.values()) + list(_SWC.values()))
needs_data = pytest.mark.skipif(
    not _all_present,
    reason="MaleCNS .ngmesh / SWC artefacts not present in this environment")


# --- synthetic NON-BIOLOGICAL parser fixtures --------------------------------
# These exercise the parser's rejection paths only. They are NOT MN5 geometry
# and carry no biological meaning; the numbers are 1, 2, 3 on purpose.

def _make_synthetic(tmp_path, name, vertex_count, face_count,
                    body=999, bad_index=None, truncate=0):
    import array

    path = tmp_path / name
    with open(path, "wb") as h:
        h.write(struct.pack("<I", vertex_count))
        v = array.array("f")
        for i in range(vertex_count):
            v.extend((float(i + 1), float(i + 2), float(i + 3)))
        h.write(v.tobytes())
        f = array.array("I")
        for i in range(face_count):
            a, b, c = (i * 3) % vertex_count, (i * 3 + 1) % vertex_count, \
                (i * 3 + 2) % vertex_count
            if bad_index is not None and i == face_count - 1:
                c = bad_index
            f.extend((a, b, c))
        h.write(f.tobytes())
    if truncate:
        with open(path, "r+b") as h:
            h.truncate(max(0, path.stat().st_size - truncate))
    return str(path)


# --- 1, 2, 3, 4, 5, 6, 7, 12, 13: real artefacts ---------------------------

@needs_data
@pytest.mark.parametrize("body_id", [801970, 801295])
def test_real_male_meshes_parse_and_consume_exactly(body_id):
    mesh = mi.parse_male_ngmesh(_MESHES[body_id], body_id)
    assert mesh.body_id == body_id
    assert mesh.coordinate_unit == "nm"
    assert mesh.coordinate_system == "Male CNS EM coordinate space"
    assert mesh.endianness == "little"
    assert mesh.header_bytes == 4
    # Header detection: the leading LE uint32 is the vertex count, and the
    # remainder is an exact multiple of the 12-byte face record.
    with open(_MESHES[body_id], "rb") as h:
        raw_count = struct.unpack("<I", h.read(4))[0]
    assert mesh.vertex_count == raw_count
    assert (mesh.file_size_bytes - 4) % 12 == 0
    assert mesh.vertex_count > 0
    assert mesh.face_count > 0
    # Exact byte budget: nothing left over, nothing padded.
    assert (4 + 12 * mesh.vertex_count + 12 * mesh.face_count
            == mesh.file_size_bytes)
    # Endianness: BE would give absurd counts.
    with open(_MESHES[body_id], "rb") as h:
        be = struct.unpack(">I", h.read(4))[0]
    assert be != mesh.vertex_count
    # Known counts from the reverse-engineering checkpoint.
    expected = {801970: (687842, 913134), 801295: (726682, 957519)}
    assert (mesh.vertex_count, mesh.face_count) == expected[body_id]


@needs_data
@pytest.mark.parametrize("body_id", [801970, 801295])
def test_real_mesh_sha256_matches_verified_value(body_id):
    assert mi.sha256_of(_MESHES[body_id]) == EXPECTED_SHA[body_id]
    mesh = mi.parse_male_ngmesh(_MESHES[body_id], body_id)
    assert mesh.sha256 == EXPECTED_SHA[body_id]


@needs_data
@pytest.mark.parametrize("body_id", [801970, 801295])
def test_real_mesh_vertex_and_face_shapes_and_index_range(body_id):
    mesh = mi.parse_male_ngmesh(_MESHES[body_id], body_id)
    verts = mesh.read_vertices()
    assert len(verts) == mesh.vertex_count
    assert all(len(v) == 3 for v in verts[:64])
    faces = mesh.read_faces()
    assert len(faces) == mesh.face_count
    assert all(len(f) == 3 for f in faces[:64])
    flat = [i for f in faces for i in f]
    assert min(flat) >= 0
    assert max(flat) < mesh.vertex_count
    assert max(flat) == mesh.vertex_count - 1


@needs_data
@pytest.mark.parametrize("body_id", [801970, 801295])
def test_real_mesh_coordinate_ranges_are_nanometre_scale(body_id):
    mesh = mi.parse_male_ngmesh(_MESHES[body_id], body_id)
    r = mesh.coordinate_ranges()
    for axis in ("x", "y", "z"):
        lo, hi = r[axis]
        assert lo < hi
        assert 1e4 < hi < 1e7, (body_id, axis, lo, hi)


@needs_data
@pytest.mark.parametrize("body_id", [801970, 801295])
def test_mesh_and_swc_register_at_documented_x8(body_id):
    """Confirms mesh_nm == swc_voxel * 8 numerically, not just by doc."""
    mesh = mi.parse_male_ngmesh(_MESHES[body_id], body_id)
    skel = mi.SkeletonGeometry.from_swc(_SWC[body_id], body_id)
    q = mi.check_male_mesh_matches_swc(mesh, skel.bbox_raw())
    assert isinstance(q.evidence, mi.EvidenceClass)
    assert mi.MESH_TO_SWC_SCALE == 8.0
    # Explicit numeric cross-check on one axis, independent of the helper.
    r = mesh.coordinate_ranges()
    skel_lo_x, skel_hi_x = skel.bbox_raw()[0], skel.bbox_raw()[3]
    assert r["x"][0] <= skel_lo_x * 8 + 1e4
    assert r["x"][1] >= skel_hi_x * 8 - 1e4


# --- 9, 10, 11: rejection paths on synthetic non-biological fixtures ---------

def test_parser_rejects_truncated_file(tmp_path):
    path = _make_synthetic(tmp_path, "trunc.ngmesh", 6, 4, truncate=6)
    with pytest.raises(mi.MaleCNSMeshFormatError):
        mi.parse_male_ngmesh(path, 999)


def test_parser_rejects_corrupt_header(tmp_path):
    # Zero vertex count.
    path = tmp_path / "zero.ngmesh"
    path.write_bytes(struct.pack("<I", 0) + b"\x00" * 36)
    with pytest.raises(mi.MaleCNSMeshFormatError):
        mi.parse_male_ngmesh(str(path), 999)
    # Header that leaves a non-multiple-of-12 remainder.
    path2 = tmp_path / "ragged.ngmesh"
    path2.write_bytes(struct.pack("<I", 5) + b"\x00" * 30)
    with pytest.raises(mi.MaleCNSMeshFormatError):
        mi.parse_male_ngmesh(str(path2), 999)
    # Header claiming more vertices than the file can hold.
    path3 = tmp_path / "over.ngmesh"
    path3.write_bytes(struct.pack("<I", 100000) + b"\x00" * 12)
    with pytest.raises(mi.MaleCNSMeshFormatError):
        mi.parse_male_ngmesh(str(path3), 999)


def test_parser_rejects_invalid_face_indices(tmp_path):
    path = _make_synthetic(tmp_path, "badidx.ngmesh", 6, 4, bad_index=9999)
    # The header and byte budget are well formed, so parsing succeeds up to the
    # index check. parse_male_ngmesh validates indices eagerly (fail fast), so
    # the rejection may surface either during parse or on an explicit read.
    mesh = None
    with pytest.raises(mi.MaleCNSMeshFormatError) as excinfo:
        mesh = mi.parse_male_ngmesh(path, 999)
    assert "index" in str(excinfo.value).lower()
    if mesh is not None:
        with pytest.raises(mi.MaleCNSMeshFormatError):
            mesh.read_faces()


def test_parser_rejects_missing_file():
    with pytest.raises(mi.MaleCNSMeshFormatError):
        mi.parse_male_ngmesh(
            os.path.join(T, "definitely-not-here.ngmesh"), 999)


def test_parser_accepts_a_wellformed_synthetic_mesh(tmp_path):
    path = _make_synthetic(tmp_path, "ok.ngmesh", 9, 5)
    mesh = mi.parse_male_ngmesh(path, 999)
    assert mesh.vertex_count == 9
    assert mesh.face_count == 5
    assert len(mesh.read_vertices()) == 9
    assert len(mesh.read_faces()) == 5
    assert mesh.coordinate_unit == "nm"


# --- 11, 13: provenance labels and the preserved gate ----------------------

def test_provenance_classes_are_declared_and_unchanged():
    # The parser introduces geometry only; no new evidence class is invented.
    assert {c.name for c in mi.EvidenceClass} == {
        "NATIVE_EXPERIMENTAL_MEASUREMENT",
        "ANATOMICAL_MEASUREMENT",
        "LITERATURE_DERIVED_PASSIVE_PARAMETER",
        "MODEL_ASSUMPTION",
        "MODEL_DERIVED_ESTIMATE",
    }
    assert len(mi.PASSIVE_PARAMETER_CONTEXT) == 9


def test_male_mesh_records_carry_exactly_one_evidence_class():
    assert isinstance(mi.MESH_COORDINATE_UNIT, str)
    assert mi.MESH_COORDINATE_SYSTEM == "Male CNS EM coordinate space"
    assert mi.SWC_COORDINATE_UNIT == "8 nm voxel units"
    # Mesh surface geometry would be ANATOMICAL_MEASUREMENT; nothing in the
    # parser assigns an electrical class.
    for q in mi.PASSIVE_PARAMETER_CONTEXT:
        assert isinstance(q.evidence, mi.EvidenceClass)


def test_parser_exposes_no_electrical_entry_point():
    for banned in ("length_constant", "electrotonic", "attenuation",
                   "transfer_resistance", "voltage_transfer", "surface_area",
                   "volume", "lambda"):
        assert not hasattr(mi.MaleCNSMesh, banned), banned


def test_biological_transfer_gate_is_preserved():
    assert mi.biological_transfer_status() == "NOT AUTHORIZED"
    with pytest.raises(mi.BiologicalTransferNotAuthorized):
        mi.require_biological_transfer_authorization()
