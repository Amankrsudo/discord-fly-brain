# Release Content Check

Audit date: **2026-10-08**. Base commit: `fad468e59b14047477a1a3e19f15a2e7618d61aa`. This checks the file set proposed by `REQUIRED_RELEASE_SNAPSHOT.md`; it does not make the worktree a release.

## Result

- Required file paths checked: **89**.
- Existing regular files: **89**.
- Missing required paths: **0**.
- All enumerated required paths exist in the current worktree.
- This is a presence check only. Existing artifacts are not thereby validated, reproducibly regenerated, or pinned to a clean commit.

## Required artifact inventory

| Path | Purpose | Evidence class | Provenance | Current Git state | Candidate release decision |
|---|---|---|---|---|---|
| `3.0_RELEASE_SPEC.md` | Authoritative definition of 3.0 boundary and historical baseline | Repository-derived | Repository release specification | tracked clean | RELEASE_REQUIRED |
| `research/source_registry.md` | Reference/source record for claims and datasets | Literature-derived; primary-dataset-derived; repository-derived | Source registry S-01–S-19 | ?? | RELEASE_REQUIRED |
| `research/raw_data_registry.md` | Availability and limitations of raw evidence | Repository-derived | Raw data availability audit | ?? | RELEASE_REQUIRED |
| `research/evidence_ledger.md` | Claim-level evidence and uncertainty | Multiple evidence classes | Current ledger plus E-051 model row | M | RELEASE_REQUIRED |
| `research/evidence_ledger.csv` | Machine-readable claim/evidence ledger | Multiple evidence classes | Generated from evidence ledger | ?? | RELEASE_REQUIRED |
| `research/scripts/generate_evidence_ledger_csv.py` | Reproduce machine-readable evidence ledger | Repository-derived | Generator reads evidence_ledger.md | ?? | RELEASE_REQUIRED |
| `research/conflicts.md` | Preserve named unresolved conflicts | Repository-derived plus cited evidence | Conflict register C-01 onward | ?? | RELEASE_REQUIRED |
| `research/missing_evidence.md` | Document unavailable evidence and gates | Repository-derived | Missing-evidence register | ?? | RELEASE_REQUIRED |
| `research/dependency_graph.md` | Document dependencies/blockers between claims | Repository-derived | Research dependency graph | ?? | RELEASE_REQUIRED |
| `research/anatomy_registry.md` | Methods and interpretation boundaries for anatomy | Primary-dataset-derived; repository-derived | MaleCNS v1.0 records | M | RELEASE_REQUIRED |
| `research/final_anatomy_audit.md` | Final bilateral contact/annotation audit | Primary-dataset-derived | MaleCNS v1.0; minconf 0.5 | ?? | RELEASE_REQUIRED |
| `research/parameter_registry.md` | Source-level parameter evidence inventory | Literature-derived; primary-dataset-derived | Parameter registry | ?? | RELEASE_REQUIRED |
| `research/parameter_adoption_plan.md` | Explain parameter decisions and adoption categories | Repository-derived; assumptions | Parameter adoption review | ?? | RELEASE_REQUIRED |
| `research/parameter_adoption_ledger.csv` | Machine-readable adoption decisions | Repository-derived; assumptions | Parameter adoption review | ?? | RELEASE_REQUIRED |
| `research/model_input_freeze.csv` | Canonical frozen input/provenance table | Multiple evidence classes | Generated input freeze; 108 rows | tracked clean | RELEASE_REQUIRED |
| `research/model_input_freeze.md` | Explain freeze buckets and gates | Repository-derived | Generated from freeze CSV | tracked clean | RELEASE_REQUIRED |
| `research/scripts/build_model_input_freeze.py` | Reproduce input freeze documents | Repository-derived | Builder source | tracked clean | RELEASE_REQUIRED |
| `biological_brain/malecns_ingest.py` | Parse MaleCNS contacts/SWCs/meshes with provenance | Repository-derived; primary-dataset-derived | MaleCNS source constants and parsers | ?? | RELEASE_REQUIRED |
| `biological_brain/malecns_mesh_geometry.py` | Compute mesh surfaces/topology | Primary-dataset-derived; repository-derived | MaleCNS mesh processing implementation | ?? | RELEASE_REQUIRED |
| `biological_brain/malecns_contact_path.py` | Compute anatomical contact geometry/path diagnostics | Repository-derived; model-derived geometric measures | Anatomy implementation | ?? | RELEASE_REQUIRED |
| `biological_brain/malecns_compartment.py` | Retrieve source compartment annotations | Primary-dataset-derived; repository-derived | MaleCNS layer/API | ?? | RELEASE_REQUIRED |
| `research/scripts/precomputed_annotations.py` | Decode Neuroglancer precomputed annotations | Repository-derived | Standard-library reader implementation | ?? | RELEASE_REQUIRED |
| `research/scripts/retrieve_malecns_compartment_post.py` | Join partner contacts to official per-synapse labels | Repository-derived; primary-dataset-derived | Python script + public HTTP range annotation reads | ?? | RELEASE_REQUIRED |
| `research/scripts/analyze_mn5_compartment_post_swc_type.py` | Generate concordance CSV/Markdown | Repository-derived | Analysis script | tracked clean | RELEASE_REQUIRED |
| `research/artifacts/malecns_compartment_post_psi_mn5.csv` | Per-contact official labels | Primary-dataset-derived | Extraction script + external raw/layer | ?? | RELEASE_REQUIRED |
| `research/artifacts/malecns_compartment_post_summary.json` | Counts and extraction metadata | Primary-dataset-derived | Extraction script + external raw/layer | ?? | RELEASE_REQUIRED |
| `research/mn5_compartment_post_swc_type_concordance.csv` | Map contact coordinates to SWC node/type literals | Primary-dataset-derived; repository-derived | Annotation CSV + external SWCs + projection script | tracked clean | RELEASE_REQUIRED |
| `research/mn5_compartment_post_swc_type_concordance.md` | Explain annotation/SWC concordance | Primary-dataset-derived; repository-derived | Concordance analysis | tracked clean | RELEASE_REQUIRED |
| `biological_brain/__init__.py` | Expose reduced model pipeline | Repository-derived | Modified package entry point | M | RELEASE_REQUIRED |
| `biological_brain/model.py` | Describe/reproduce evidence-safe reduced software model | Model-derived; software behavior | Three SAFE inputs in frozen model table | ?? | RELEASE_REQUIRED |
| `biological_brain/model_framework.py` | Describe/reproduce evidence-safe reduced software model | Model-derived; software behavior | Three SAFE inputs in frozen model table | ?? | RELEASE_REQUIRED |
| `biological_brain/reduced_mn5.py` | Describe/reproduce evidence-safe reduced software model | Model-derived; software behavior | Three SAFE inputs in frozen model table | ?? | RELEASE_REQUIRED |
| `biological_brain/provenance.py` | Shared provenance dependency for model components | Repository-derived | Tracked biological_brain module used by model pipeline | tracked clean | RELEASE_REQUIRED |
| `research/reduced_mn5_model.md` | Describe/reproduce evidence-safe reduced software model | Model-derived; software behavior | Three SAFE inputs in frozen model table | ?? | RELEASE_REQUIRED |
| `research/reduced_mn5_verification.md` | Record tested reduced-model limitations and checks | Repository-derived; validation fixtures | Verification report | ?? | RELEASE_REQUIRED |
| `biological_brain/exploratory_mn5.py` | Implementation dependency of current two-gate analysis | Model-derived; assumptions | Exploratory model implementation | ?? | RELEASE_REQUIRED |
| `research/mn5_psi_mn5_final_constraint_model.md` | Explain local and abstract bridge analysis | Model-derived; assumptions | Final constraint model documentation | ?? | RELEASE_REQUIRED |
| `research/mn5_psi_mn5_final_constraint_model_sensitivity.csv` | Machine-readable current model sweep | Model-derived; assumptions | 15528-row model analysis | ?? | RELEASE_REQUIRED |
| `research/scripts/analyze_mn5_two_gate_constraint_model.py` | Reproduce current model sweep | Model-derived; repository-derived | Analysis script + concordance/SWCs | ?? | RELEASE_REQUIRED |
| `research/mn5_spatial_transfer_gate_review.md` | Support limitations around native versus model-derived transfer | Repository-derived; literature-derived | Research evidence reviews | ?? | RELEASE_REQUIRED |
| `research/spatial_transfer_evidence.md` | Support limitations around native versus model-derived transfer | Repository-derived; literature-derived | Research evidence reviews | ?? | RELEASE_REQUIRED |
| `research/da7_evidence.md` | Support receptor/channel evidence boundaries | Literature-derived; repository-derived | Research evidence review | ?? | RELEASE_REQUIRED |
| `research/mn5_psi_genetic_access_audit.md` | Document genetic-access constraints relevant to PSI/MN5 claims | Repository-derived; literature-derived | Research audit | ?? | SUPPORTING |
| `research/psi_mn5_reversal_potential_audit.md` | Record why PSI reversal evidence is unavailable | Repository-derived; literature-derived | Research audit | tracked clean | SUPPORTING |
| `research/psi_mn5_direct_voltage_experiment_audit.md` | Document proposed experimental designs and generated audits | Repository-derived; literature-derived; assumptions | Research design audits and source-backed constraints | ?? | MANUAL_REVIEW |
| `research/psi_mn5_direct_voltage_experiment_audit.csv` | Document proposed experimental designs and generated audits | Repository-derived; literature-derived; assumptions | Research design audits and source-backed constraints | ?? | MANUAL_REVIEW |
| `research/psi_mn5_optical_experiment_design_audit.md` | Document proposed experimental designs and generated audits | Repository-derived; literature-derived; assumptions | Research design audits and source-backed constraints | ?? | MANUAL_REVIEW |
| `research/psi_mn5_optical_experiment_design_audit.csv` | Document proposed experimental designs and generated audits | Repository-derived; literature-derived; assumptions | Research design audits and source-backed constraints | ?? | MANUAL_REVIEW |
| `research/psi_mn5_reversal_experiment_audit.md` | Document proposed experimental designs and generated audits | Repository-derived; literature-derived; assumptions | Research design audits and source-backed constraints | ?? | MANUAL_REVIEW |
| `research/psi_mn5_reversal_experiment_audit.csv` | Document proposed experimental designs and generated audits | Repository-derived; literature-derived; assumptions | Research design audits and source-backed constraints | ?? | MANUAL_REVIEW |
| `research/scripts/build_reversal_experiment_audit.py` | Document proposed experimental designs and generated audits | Repository-derived; literature-derived; assumptions | Research design audits and source-backed constraints | ?? | MANUAL_REVIEW |
| `tests/malecns_real_data.py` | Define external-input fixtures/helpers for MaleCNS tests | Validation fixtures; software validation | External MaleCNS input file expectations | ?? | RELEASE_REQUIRED |
| `tests/test_malecns_anatomy_audit.py` | Validate data parsing/geometry/annotation behavior | Validation fixtures; software validation | Tests for anatomy pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_malecns_compartment.py` | Validate data parsing/geometry/annotation behavior | Validation fixtures; software validation | Tests for anatomy pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_mn5_compartment_post_swc_type_concordance.py` | Validate data parsing/geometry/annotation behavior | Validation fixtures; software validation | Tests for anatomy pipeline | tracked clean | RELEASE_REQUIRED |
| `tests/test_malecns_contact_path.py` | Validate data parsing/geometry/annotation behavior | Validation fixtures; software validation | Tests for anatomy pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_malecns_mesh_geometry.py` | Validate data parsing/geometry/annotation behavior | Validation fixtures; software validation | Tests for anatomy pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_malecns_mesh_parser.py` | Validate data parsing/geometry/annotation behavior | Validation fixtures; software validation | Tests for anatomy pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_malecns_infrastructure.py` | Validate data parsing/geometry/annotation behavior | Validation fixtures; software validation | Tests for anatomy pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_mn5_spatial_transfer_gate_review.py` | Validate provenance gates/model numerics | Validation fixtures; software validation | Tests for analysis/model pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_mn5_two_gate_constraint_model.py` | Validate provenance gates/model numerics | Validation fixtures; software validation | Tests for analysis/model pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_exploratory_mn5.py` | Software tests for implementation used by two-gate analysis | Validation fixtures; software validation | Exploratory MN5 implementation | ?? | RELEASE_REQUIRED |
| `tests/test_parameter_adoption.py` | Validate provenance gates/model numerics | Validation fixtures; software validation | Tests for analysis/model pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_model_input_freeze.py` | Validate provenance gates/model numerics | Validation fixtures; software validation | Tests for analysis/model pipeline | tracked clean | RELEASE_REQUIRED |
| `tests/test_model_framework.py` | Validate provenance gates/model numerics | Validation fixtures; software validation | Tests for analysis/model pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_model_pipeline.py` | Validate provenance gates/model numerics | Validation fixtures; software validation | Tests for analysis/model pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_reduced_mn5.py` | Validate provenance gates/model numerics | Validation fixtures; software validation | Tests for analysis/model pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_reduced_mn5_audit.py` | Validate provenance gates/model numerics | Validation fixtures; software validation | Tests for analysis/model pipeline | ?? | RELEASE_REQUIRED |
| `tests/test_biological_brain.py` | Validation tests for 3.0 biological architecture | Validation fixtures; software validation | 3.0 release modules and current modified test file | M | RELEASE_REQUIRED |
| `research_archive/PAPER_SCOPE_FREEZE.md` | Freeze included/excluded scientific work and claim boundaries | Repository-derived; literature-derived; primary-dataset-derived; model-derived; assumptions; validation fixtures | Repository evidence and cited sources enumerated in the freeze | ?? | RELEASE_REQUIRED |
| `research_archive/VERSION_SCOPE_AUDIT.md` | Compare historical baseline, post-baseline research, and proposed snapshot | Repository-derived | Git history and repository documents | ?? | RELEASE_REQUIRED |
| `research_archive/REQUIRED_RELEASE_SNAPSHOT.md` | List proposed scientific release files and exclusions | Repository-derived | Repository artifact inventory and prior scope decision | ?? | RELEASE_REQUIRED |
| `research_archive/PUBLICATION_SNAPSHOT_AUDIT.md` | Record candidate artifact set and unresolved decisions | Repository-derived | Repository inventory | ?? | RELEASE_REQUIRED |
| `research_archive/PUBLICATION_READINESS.md` | Record scope, snapshot, metadata and validation readiness | Repository-derived | Checkpoint evidence | ?? | RELEASE_REQUIRED |
| `research_archive/CITATION_AUDIT.md` | Document citation and software metadata completeness | Repository-derived | CITATION.cff, references.bib, and source registry | ?? | RELEASE_REQUIRED |
| `research_archive/MALECNS_PUBLICATION_AUDIT.md` | Record dataset provenance, derivatives, and reuse limitations | Primary-dataset-derived; repository-derived | Source/raw-data/anatomy registries and scripts | ?? | RELEASE_REQUIRED |
| `research_archive/RELEASE_MANIFEST_REVIEW.md` | Classify every publication-manifest row and record manual decisions | Repository-derived | Publication manifest and current repository state | ?? | RELEASE_REQUIRED |
| `research_archive/RELEASE_METADATA_BLOCKERS.md` | Record unverified authorship, citation, software license, and dataset terms | Repository-derived | CITATION.cff, references.bib, source registry, and MaleCNS audit | ?? | RELEASE_REQUIRED |
| `research_archive/RELEASE_CONTENT_CHECK.md` | Verify required snapshot paths, provenance, tracking state, and inclusion | Repository-derived; multiple evidence classes | Required release snapshot, manifest, Git status, and source records | ?? | RELEASE_REQUIRED |
| `paper/CLAIM_LANGUAGE_STANDARD.md` | Constrain permitted claims and terminology | Repository-derived; literature-derived; primary-dataset-derived; model-derived | Frozen scientific scope and evidence records | ?? | RELEASE_REQUIRED |
| `paper/PUBLICATION_MANIFEST.csv` | Machine-readable release classification and provenance inventory | Repository-derived; multiple evidence classes | This manifest; row-level source fields | ?? | RELEASE_REQUIRED |
| `paper/claim_evidence_matrix.csv` | Map proposed claims to evidence records | Multiple evidence classes | Research evidence ledger and source records | ?? | RELEASE_REQUIRED |
| `paper/references.bib` | Working bibliography for cited sources | Literature-derived | Repository source registry; primary records still require verification | ?? | SUPPORTING |
| `paper/README.md` | Describe paper-supporting files | Repository-derived | Repository documentation | ?? | RELEASE_REQUIRED |
| `data/README.md` | Document external data dependencies and data limits | Primary-dataset-derived; repository-derived | MaleCNS v1.0 source and raw-data registry | ?? | RELEASE_REQUIRED |
| `methods/provenance/evidence_classification.md` | Define evidence categories and interpretation boundaries | Repository-derived | Project evidence records | ?? | RELEASE_REQUIRED |
| `methods/model_inputs/README.md` | Explain model-input provenance and blocked assumptions | Repository-derived; literature-derived; model-derived; assumptions | Model input freeze and analysis records | ?? | RELEASE_REQUIRED |
| `validation/REPRODUCIBILITY_GAPS.md` | Document missing clean reproduction conditions | Repository-derived | Current audit | ?? | RELEASE_REQUIRED |
| `validation/full_suite_report.md` | Record latest reported suite result and snapshot limits | Repository-derived | Prior full-suite report | ?? | HISTORICAL |

## External data and limits

- Required external inputs include the MaleCNS v1.0 partner Feather table, the v1.0 precomputed synapse annotation layer, and the two named MN5 SWCs. The source portal and GCS roots are recorded in `research/raw_data_registry.md` and `research_archive/MALECNS_PUBLICATION_AUDIT.md`.
- The Feather table plus precomputed annotation layer produce `research/artifacts/malecns_compartment_post_psi_mn5.csv` and `research/artifacts/malecns_compartment_post_summary.json`. Those outputs and the SWCs feed `research/mn5_compartment_post_swc_type_concordance.csv`/`.md`; the concordance and SWCs feed `research/mn5_psi_mn5_final_constraint_model_sensitivity.csv`.
- The extraction script consumes an already-staged Feather file and does not download it. No complete staging command or expected Feather checksum is recorded. SWC hashes are recorded in the analysis scripts; mesh checksums are in the anatomy records.
- The raw Feather file is external and excluded from Git. Do not read, download, or redistribute it as part of this checkpoint. These missing staging/checksum and license-verification items remain reproducibility/release blockers.

## Snapshot decision

The existing figure plan is located at `paper/figures/FIGURE_PLAN.md` and is
listed as supporting material in the publication manifest; no figures have
been generated.

Path existence is **not** sufficient to call the snapshot complete. The worktree is dirty; most candidate artifacts are untracked, metadata/license decisions remain unresolved, and no clean-commit validation exists. Do not stage or commit this as a public release until the blockers are resolved.
