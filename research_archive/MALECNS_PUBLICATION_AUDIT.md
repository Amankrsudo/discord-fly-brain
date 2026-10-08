# MaleCNS publication audit

Audit date: **2026-10-08**. Audit basis: `research/source_registry.md` S-01/S-05, `research/raw_data_registry.md`, `research/anatomy_registry.md`, `research/final_anatomy_audit.md`, ingestion/retrieval scripts, and read-only checks of documented output/input paths. No raw file contents were read and no data were downloaded.

| Item | Repository evidence / audit result |
|---|---|
| Dataset name/version | MaleCNS v1.0 connectome; source code names it `male-cns`, version `v1.0`. |
| Public source | Portal `https://male-cns.janelia.org/`; dataset root `gs://flyem-male-cns/v1.0/`. |
| Relevant annotation layer | `gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed/`; HTTPS base is embedded in `biological_brain/malecns_compartment.py`. The layer is recorded as `neuroglancer_annotations_v1`. |
| Dataset citation | Source registry records Berg et al. (2026), “Sexual dimorphism in the complete Drosophila male central nervous system connectome,” *Cell* 189(18):5504–5526.e15, DOI `10.1016/j.cell.2026.08.015`, PMID 41279223, PMCID PMC12636603; dataset version 1.0. Full author list still needs verification. |
| License/attribution | Source registry, raw-data registry, anatomy record, and ingestion code state public, unauthenticated, CC-BY. Attribute the MaleCNS source as required by its license. The repository does not contain the license text or a bulk redistribution review: **VERIFY_REQUIRED before redistributing the raw Feather file**. |
| Expected raw format/file | Feather; `syn-partners-male-cns-v1.0-minconf-0.5.feather`; source/test code expects it in the system temporary directory. Inventory estimates approximately 6.5 GB. It carries the minimum-confidence 0.5 contacts. |
| Raw retrieval method | No complete command for downloading/staging the Feather table is documented. `retrieve_malecns_compartment_post.py` consumes the pre-staged Feather and requests matching annotations over HTTP range requests; it does not download the Feather. `malecns_ingest.py` records public GCS bases for other source files. Do not present the processing script as a raw-data downloader. |
| Raw checksum | No expected checksum for the Feather table was found. **Missing.** |
| Local raw-data availability | The exact expected Feather filename was found in the current machine's system temporary directory, outside the repository. Its contents were not read. The raw table is not in the Git repository and will not be part of a clean clone. |
| Other external inputs/checksums | `em_801970.swc` and `em_801295.swc` are expected in the system temporary directory. SHA-256 values are recorded in the concordance/two-gate scripts. Those hashes validate the named SWCs only. `research/anatomy_registry.md` records mesh checksums. |
| Processed outputs | `research/artifacts/malecns_compartment_post_psi_mn5.csv` (15,648 bytes) and `research/artifacts/malecns_compartment_post_summary.json` (1,653 bytes) exist in the worktree and are untracked. They derive from the raw contact Feather plus public annotation layer. `research/mn5_compartment_post_swc_type_concordance.csv` (12,603 bytes) exists and is tracked; its Markdown companion is tracked. These derive from the processed annotation records plus external SWCs. |
| Model-analysis output | `research/mn5_psi_mn5_final_constraint_model_sensitivity.csv` (5,325,185 bytes) exists and is untracked. It depends on the concordance table, expected cached SWCs, and declared model inputs; it is model-derived, not a primary dataset. |

## Interpretation boundary

The audit supports a provenance chain for the recorded 43 contacts (17 and 26 at minconf 0.5) and their official `compartment_post` labels. The `axon` string is a source dataset annotation. It is not an electrophysiological measurement, a SWC `kind` interpretation, a contact-to-soma path, or native voltage transfer. Do not elevate it to those claims.

## Release conditions

Before publication, pin the raw-data version and processed outputs, record a verified checksum for the Feather input if obtainable from source, document a permitted raw-data staging method, and manually confirm license attribution/redistribution terms. No such additions are inferred here.
