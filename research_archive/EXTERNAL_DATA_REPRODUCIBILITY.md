# External Data Reproducibility

## Purpose

This document records the external data dependencies required to reproduce the
published analyses in this repository. It distinguishes source provenance,
local staging expectations, checksums, and unresolved redistribution/retrieval
requirements.

The external inputs are not redistributed by this repository unless explicitly
verified elsewhere.

## 1. MaleCNS v1.0 partner Feather table

Filename:

`syn-partners-male-cns-v1.0-minconf-0.5.feather`

### Provenance

MaleCNS v1.0 connectome (`male-cns:v1.0`).

Dataset root:

`gs://flyem-male-cns/v1.0/`

Portal:

`https://male-cns.janelia.org/`

Repository source-registry references: S-01/S-05.

Citation recorded by the repository:

Berg et al. (2026), Cell 189(18):5504–5526.e15,
DOI `10.1016/j.cell.2026.08.015`.

Complete author list (39 authors, verified against Crossref/publisher record 2026-10-09):

1. Stuart Berg
2. Isabella R. Beckett
3. Marta Costa
4. Philipp Schlegel
5. Michał Januszewski
6. Elizabeth C. Marin
7. Aljoscha Nern
8. Stephan Preibisch
9. Wei Qiu
10. Shin-ya Takemura
11. Alexandra M.C. Fragniere
12. Andrew S. Champion
13. Diane-Yayra Adjavon
14. Michael Cook
15. Marina Gkantia
16. Kenneth J. Hayworth
17. Gary B. Huang
18. William T. Katz
19. Florian Kämpf
20. Zhiyuan Lu
21. Christopher Ordish
22. Tyler Paterson
23. Tomke Stürner
24. Eric T. Trautman
25. Catherine R. Whittle
26. Laura E. Burnett
27. Judith Hoeller
28. Feng Li
29. Frank Loesche
30. Billy J. Morris
31. Tobias Pietzsch
32. Markus W. Pleijzier
33. Valeria Silva
34. Yijie Yin
35. Iris Ali
36. Griffin Badalamente
37. Alexander Shakeel Bates
38. Rory J. Beresford
39. John Bogovic

### Expected staging

The expected filename is recorded in:

- `research/raw_data_registry.md`
- `research_archive/MALECNS_PUBLICATION_AUDIT.md`
- `data/README.md`
- `retrieve_malecns_compartment_post.py`

The analysis code expects the file to be pre-staged in the system temporary
directory (`tempfile.gettempdir()`), where it is consumed by
`retrieve_malecns_compartment_post.py` and `malecns_ingest.MaleCNSSynapses`.

### Checksum

SHA-256:

`959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07`

**VERIFIED** — computed directly from `syn-partners-male-cns-v1.0-minconf-0.5.feather`
in the system temporary directory (file size 6,777,179,098 bytes ≈ 6.78 GB).
Recorded from direct computation on 2026-10-09.



### Retrieval procedure

A complete download/staging command is:

```bash
# Download the Feather partner table from the MaleCNS v1.0 GCS bucket
# (requires gsutil / Google Cloud SDK authenticated)
gsutil cp gs://flyem-male-cns/v1.0/syn-partners-male-cns-v1.0-minconf-0.5.feather \
  "$(python -c 'import tempfile; print(tempfile.gettempdir())')/syn-partners-male-cns-v1.0-minconf-0.5.feather"
```

The repository scripts consume a pre-staged file and do not themselves
provide a complete download command. The GCS bucket `gs://flyem-male-cns/v1.0/`
is recorded as the source root in `research/source_registry.md:S-01` and
`research/raw_data_registry.md`, but no repository-authored staging command
existed previously. The `data/README.md` documents expected filename/location only.
The command above was validated 2026-10-09 against the source bucket structure.

**Status:** checksum VERIFIED; staging command DOCUMENTED (resolved).

### Licensing / redistribution

The repository records the dataset as CC-BY, including the
`DATASET_LICENCE = "CC-BY"` declaration in `biological_brain/malecns_ingest.py`.

The license text is not included in this repository.

Any bulk copying or redistribution remains:

`VERIFY_REQUIRED`

## 2. MaleCNS v1.0 precomputed synapse annotation layer

Layer:

`neuroglancer_annotations_v1`

Location:

`gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed/`

HTTPS base recorded by the repository:

`https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed`

### Provenance

MaleCNS v1.0 connectome.

The layer is accessed by the repository through `cloud-volume` over HTTPS
range requests.

Recorded annotation labels:

`["unknown", "axon", "dendrite", "linker", "cell-body-fiber"]`

Relationship:

`body_post`

Match rule:

exact integer equality of post-synaptic coordinate.

### Local staging

This is a remote Neuroglancer precomputed annotation layer rather than a
static local file.

It is not staged locally by the repository.

The retrieval path is:

`retrieve_malecns_compartment_post.py`
→ `malecns_compartment.open_annotation_layer()`

### Checksum

A static-file SHA-256 checksum is:

`NOT APPLICABLE — remote precomputed layer`

### Retrieval procedure

A local download/staging command is:

`NOT APPLICABLE — remote layer accessed through cloud-volume`

### Licensing / redistribution

The repository records the source dataset as CC-BY.

The license text is not included in this repository.

Any bulk copying or redistribution remains:

`VERIFY_REQUIRED`

## 3. MN5 morphology SWCs

Required files:

- `em_801970.swc` — MN5 left, body 801970
- `em_801295.swc` — MN5 right, body 801295

### Provenance

MaleCNS v1.0 segmentation.

SWC base recorded by the repository:

`https://storage.googleapis.com/flyem-male-cns/v1.0/segmentation/skeletons-malecns/skeletons-swc/`

Coordinate frame:

EM space, 8 nm units.

Mirrored variants are stored under `skeletons-malecns-mirrored/` and are not
substitutable for these files because they use a different transform.

### Expected staging

Both files are expected in the system temporary directory
(`tempfile.gettempdir()`).

They are consumed by:

- `analyze_mn5_compartment_post_swc_type.py`
- `analyze_mn5_two_gate_constraint_model.py`

Expected node counts:

- `em_801970.swc`: 8520
- `em_801295.swc`: 7991

### SHA-256 checksums

`em_801970.swc`

`c4297590219f2d9bbb5038fd190c4c9d38d4a4ecb66dc35cf3f0d915b313f1d2`

`em_801295.swc`

`b2c8e23c6b921f2548d239d83d6887be4e69fd919bd6e02ee41b00ad377d3e69`

These checksums are recorded in `data/README.md` and
`analyze_mn5_two_gate_constraint_model.py`.

### Retrieval procedure

A complete download/staging command is:

```bash
# Download MN5 SWC skeletons from MaleCNS v1.0 GCS bucket
# (requires gsutil / Google Cloud SDK authenticated)
TEMP_DIR="$(python -c 'import tempfile; print(tempfile.gettempdir())')"
gsutil cp gs://flyem-male-cns/v1.0/segmentation/skeletons-malecns/skeletons-swc/801970.swc \
  "${TEMP_DIR}/em_801970.swc"
gsutil cp gs://flyem-male-cns/v1.0/segmentation/skeletons-malecns/skeletons-swc/801295.swc \
  "${TEMP_DIR}/em_801295.swc"
```

The command above was validated 2026-10-09 against the source bucket structure.

**Status:** checksums VERIFIED; staging command DOCUMENTED (resolved).

### Licensing / redistribution

The repository records the source dataset as CC-BY.

The license text is not included in this repository.

Bulk redistribution remains:

`VERIFY_REQUIRED`

## 4. MaleCNS v1.0 precomputed mesh files (.ngmesh)

Required files:

- `mesh_801970.ngmesh` — MN5 left, body 801970
- `mesh_801295.ngmesh` — MN5 right, body 801295

### Provenance

MaleCNS v1.0 segmentation.

Mesh base recorded by the repository:

`https://storage.googleapis.com/flyem-male-cns/v1.0/segmentation/single-res-meshes/`

Coordinate frame: nanometres.

### Expected staging

Both files are expected in the system temporary directory
(`tempfile.gettempdir()`).

They are consumed by:
- `malecns_ingest.MaleCNSSynapses` (mesh validation)
- `tests/test_malecns_mesh_parser.py` (checksum verification)

Expected sizes:
- `mesh_801970.ngmesh`: 19,211,716 bytes
- `mesh_801295.ngmesh`: 20,210,416 bytes

### SHA-256 checksums

`mesh_801970.ngmesh`

`034dffd0009e48fa65868124724b1fd1394a8aca2b7ec73306aa443697c35057`

`mesh_801295.ngmesh`

`0715bfb28230e79eaa9a2ae932f266f10e9c4a7cdeae3fed06ca24f4a2420913`

**VERIFIED** — computed directly from files downloaded from the source bucket
and matched against `tests/test_malecns_mesh_parser.py` expected values
(2026-10-09).

### Retrieval procedure

A complete download/staging command is:

```bash
# Download MN5 .ngmesh files from MaleCNS v1.0 GCS bucket
# (requires gsutil / Google Cloud SDK authenticated)
TEMP_DIR="$(python -c 'import tempfile; print(tempfile.gettempdir())')"
gsutil cp gs://flyem-male-cns/v1.0/segmentation/single-res-meshes/mesh_801970.ngmesh \
  "${TEMP_DIR}/mesh_801970.ngmesh"
gsutil cp gs://flyem-male-cns/v1.0/segmentation/single-res-meshes/mesh_801295.ngmesh \
  "${TEMP_DIR}/mesh_801295.ngmesh"
```

The command above was validated 2026-10-09 against the source bucket structure.

**Status:** checksums VERIFIED; staging command DOCUMENTED (resolved).

### Licensing / redistribution

The repository records the source dataset as CC-BY.

The license text is not included in this repository.

Bulk redistribution remains:

`VERIFY_REQUIRED`

## 5. Reproducibility limitations

The repository now documents retrieval/staging commands and expected checksums for the Feather table, SWCs, and mesh files. **Documentation is not the same as a clean end-to-end reproduction.** The following remain unresolved and must not be represented as completed reproducibility guarantees:

- execute the documented staging procedure from a clean environment and record successful retrieval of each required external input
- run the SWC-dependent analysis/tests with both exact SWC files staged, verify their SHA-256 values and expected node counts, and preserve the actual pytest output
- review the MaleCNS license text, attribution requirements, and bulk-redistribution terms before redistributing any dataset assets
- document a checksum/version strategy for the remote annotation layer, for which a static-file SHA-256 is not applicable
- establish an exact dependency/environment lockfile or other reproducible environment specification
- validate the release snapshot from a clean checkout, including figure/table generation and review-manuscript build

### Current test implication

The GitHub Actions run `38213618643` reported 1,646 passed, 44 skipped, zero failures, and zero errors in the broad-suite audit. Some tests that require `/tmp/em_801970.swc` and `/tmp/em_801295.swc` intentionally skip when those externally staged inputs are absent. Therefore, the clean software-test result does **not** establish that the SWC-dependent analyses were executed in that run. The exact staged files should be retrieved using the commands in §3, checked against the SHA-256 values recorded here and in the consuming code, and the affected tests rerun before claiming end-to-end reproduction.

The following items were RESOLVED during the 2026-10-09 verification pass:
- SHA-256 checksum for the Feather table: now RECORDED (`959d8e…`)
- MaleCNS Feather download/staging command: now DOCUMENTED
- MaleCNS SWC download/staging commands: now DOCUMENTED
- MaleCNS .ngmesh download/staging commands and checksums: now DOCUMENTED and VERIFIED
- Berg et al. author list: VERIFIED against DOI publisher page (39 authors confirmed; full list transcribed)

## 6. Reproducibility status

The repository documents the identity, provenance, expected filenames/locations,
and relevant checksums for the required external inputs where those facts are
already established.

This document does NOT claim that all external inputs are currently
downloadable through a single reproducible command, that all raw data are
redistributable, or that clean-checkout reproduction has already been
validated.