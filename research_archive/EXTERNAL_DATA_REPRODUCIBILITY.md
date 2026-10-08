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

The complete author list remains `VERIFY_REQUIRED`.

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

`NOT RECORDED — VERIFY_REQUIRED`

No expected checksum for this Feather table is currently recorded in the
repository.

### Retrieval procedure

A complete download/staging command is:

`NOT DOCUMENTED — VERIFY_REQUIRED`

The repository scripts consume a pre-staged file and do not themselves
provide a complete download command.

### Licensing / redistribution

The repository records the dataset as CC-BY, including the
`DATASET_LICENCE = "CC-BY"` declaration in `biological_brain/malecns_ingest.py`.

The license text is not included in this repository.

Bulk redistribution/republication of the raw Feather table remains:

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

`NOT DOCUMENTED — VERIFY_REQUIRED`

The analysis scripts expect the files to be pre-staged in the temporary
directory.

### Licensing / redistribution

The repository records the source dataset as CC-BY.

The license text is not included in this repository.

Bulk redistribution remains:

`VERIFY_REQUIRED`

## 4. Reproducibility limitations

The following items remain unresolved and must not be represented as completed
reproducibility guarantees:

- SHA-256 checksum for the Feather table
- complete download/staging command for the Feather table
- complete download/staging commands for the SWCs
- license text and bulk-redistribution terms
- complete Berg et al. author attribution
- checksum for the remote annotation layer (not a static file)
- exact dependency/environment lockfile
- clean-checkout validation of the release snapshot

## 5. Reproducibility status

The repository documents the identity, provenance, expected filenames/locations,
and relevant checksums for the required external inputs where those facts are
already established.

This document does NOT claim that all external inputs are currently
downloadable through a single reproducible command, that all raw data are
redistributable, or that clean-checkout reproduction has already been
validated.