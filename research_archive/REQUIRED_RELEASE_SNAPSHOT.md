# Required release snapshot

This is the proposed file set for a **new paper-scoped research release**. It is not a commit or a claim that current files are already frozen.

## Base commit

Use `fad468e59b14047477a1a3e19f15a2e7618d61aa` as the Git ancestry/base because it is current HEAD. It is **not** the paper snapshot. A new release commit must be created after scope selection and review, containing the selected scientific work below. `40cf69e` remains the historical 3.0 implementation-validation baseline named by `3.0_RELEASE_SPEC.md`; it is not a sufficient base for the later MN5 analyses.

## Scientific source and code files to commit

### Scope, evidence, and provenance

- `3.0_RELEASE_SPEC.md` (preserve its stated 40cf69e scope/baseline).
- `research/source_registry.md`
- `research/raw_data_registry.md`
- `research/evidence_ledger.md` and `research/evidence_ledger.csv`
- `research/scripts/generate_evidence_ledger_csv.py`
- `research/conflicts.md`, `research/missing_evidence.md`, `research/dependency_graph.md`
- `research/anatomy_registry.md`, `research/final_anatomy_audit.md`
- `research/parameter_registry.md`, `research/parameter_adoption_plan.md`, `research/parameter_adoption_ledger.csv`
- `research/model_input_freeze.csv`, `research/model_input_freeze.md`, `research/scripts/build_model_input_freeze.py`

### MaleCNS processing and derived data

- `biological_brain/malecns_ingest.py`, `biological_brain/malecns_mesh_geometry.py`, `biological_brain/malecns_contact_path.py`, `biological_brain/malecns_compartment.py`
- `research/scripts/precomputed_annotations.py`, `research/scripts/retrieve_malecns_compartment_post.py`, `research/scripts/analyze_mn5_compartment_post_swc_type.py`
- `research/artifacts/malecns_compartment_post_psi_mn5.csv`, `research/artifacts/malecns_compartment_post_summary.json`
- `research/mn5_compartment_post_swc_type_concordance.csv`, `research/mn5_compartment_post_swc_type_concordance.md`
- `research/final_anatomy_audit.md`

Raw MaleCNS Feather/SWC/mesh source files remain external inputs and are **not** committed in this proposed snapshot. Record their source/version and verified checksums where available. Obtain license/attribution review before redistributing any raw data.

### Reduced MN5 pipeline (include as a separately labeled model)

- `biological_brain/__init__.py`, `biological_brain/model.py`, `biological_brain/model_framework.py`, `biological_brain/reduced_mn5.py`, and the tracked dependency `biological_brain/provenance.py`.
- `research/reduced_mn5_model.md`, `research/reduced_mn5_verification.md`.

These files must remain clear that the reduced model has no leak, cable, synapse, spatial transfer, or Dα7 conductance. Do not expose model gates as opened.

### Conditional two-gate analysis

- `biological_brain/exploratory_mn5.py` (required implementation dependency of the current analysis), plus the listed MaleCNS source modules above.
- `research/mn5_psi_mn5_final_constraint_model.md`, `research/mn5_psi_mn5_final_constraint_model_sensitivity.csv`.
- `research/scripts/analyze_mn5_two_gate_constraint_model.py`.
- `research/mn5_spatial_transfer_gate_review.md`, `research/spatial_transfer_evidence.md`, `research/da7_evidence.md`, `research/mn5_psi_genetic_access_audit.md`, `research/psi_mn5_reversal_potential_audit.md`.
- If design proposals are discussed, include their exact source and generated artifacts: `research/psi_mn5_direct_voltage_experiment_audit.md/.csv`, `research/psi_mn5_optical_experiment_design_audit.md/.csv`, and `research/psi_mn5_reversal_experiment_audit.md/.csv`, with `research/scripts/build_reversal_experiment_audit.py`.

## Analysis outputs to commit

- Annotation extraction CSV and JSON summary listed above.
- SWC concordance CSV and Markdown report.
- Two-gate sensitivity CSV (15,528 rows as reported by its documentation).
- Evidence ledger CSV and model-input freeze CSV/Markdown, generated from the pinned scripts.
- Any additional output cited in the paper must be regenerated from the pinned snapshot and listed in the manifest. The 6.5 GB partner Feather, cached SWCs, and meshes are external and must not be represented as files in the Git release.

## Tests and validation artifacts to commit

For the MaleCNS/anatomy and two-gate scope:

- `tests/malecns_real_data.py`
- `tests/test_malecns_anatomy_audit.py`, `tests/test_malecns_compartment.py`, `tests/test_mn5_compartment_post_swc_type_concordance.py`, `tests/test_malecns_contact_path.py`, `tests/test_malecns_mesh_geometry.py`, `tests/test_malecns_mesh_parser.py`, `tests/test_malecns_infrastructure.py`
- `tests/test_mn5_spatial_transfer_gate_review.py`, `tests/test_mn5_two_gate_constraint_model.py`, `tests/test_exploratory_mn5.py`
- `tests/test_parameter_adoption.py`, `tests/test_model_input_freeze.py`

If the reduced model is included, also commit `tests/test_model_framework.py`, `tests/test_model_pipeline.py`, `tests/test_reduced_mn5.py`, `tests/test_reduced_mn5_audit.py`, and the necessary relevant changes in `tests/test_biological_brain.py`.

Commit `validation/full_suite_report.md` only as a historical report with its dirty-tree caveat. It does not validate this new snapshot. Add a new report after tests run on a clean checkout of the new release commit. Software tests remain separate from empirical biological evidence.

## Research and paper documentation to commit

- `research_archive/PAPER_SCOPE_FREEZE.md`, `research_archive/VERSION_SCOPE_AUDIT.md`, `research_archive/REQUIRED_RELEASE_SNAPSHOT.md`, `research_archive/PUBLICATION_SNAPSHOT_AUDIT.md`, and updated `research_archive/PUBLICATION_READINESS.md`.
- `research_archive/CITATION_AUDIT.md`, `research_archive/MALECNS_PUBLICATION_AUDIT.md`, and `paper/CLAIM_LANGUAGE_STANDARD.md`.
- `paper/PUBLICATION_MANIFEST.csv`, `paper/claim_evidence_matrix.csv`, `paper/references.bib`, `paper/README.md`, `data/README.md`, `methods/provenance/evidence_classification.md`, `methods/model_inputs/README.md`, `validation/REPRODUCIBILITY_GAPS.md`.
- Update `CITATION.cff` only after authorship, citable title, version, URL, release date, DOI, and software license are verified. Until then it remains a draft and must not be presented as complete citation metadata.

## Historical/internal files to keep out of current results

- Earlier results: `research/MN5_EXPLORATORY_FINAL_STATUS.md` and `research/exploratory_mn5_final_report.md`, `research/exploratory_mn5_model.md`, `research/exploratory_mn5_parameter_sensitivity.csv`, `research/exploratory_mn5_results_analysis.md`, `research/exploratory_mn5_scientific_review.md`, `research/exploratory_parameter_ranges.csv`, `research/exploratory_sensitivity_plan.md`. Retain only as clearly labeled history; do not substitute their old results for the current two-gate analysis.
- One-off diagnostics/fixes: `research/_diag_ledger.py`, `research/_diag2_ledger.py`, `research/_fix_ledger.py`, `research/_fix_ledger2.py`, `research/_fix_ledger3.py`, and `research/_ledger_*.txt`.
- Product/dashboard/MATE files, runtime state, asset audit material, IDE configuration, `.env`, deployment archives, credentials, and local environment directories. Do not inspect or publish private/deployment files.
- `tests/test_visual_command_intent.py` changes and unrelated `fly_bot.py`/`fly_state.json` modifications are product work and are not part of this scientific snapshot.

## Snapshot decision

No exact snapshot exists yet. The paper snapshot is the new commit that explicitly records the selected files above, generated outputs, verified data provenance, and test report from a clean checkout. Do not tag or cite the dirty worktree or the prior 1773/2 run as that snapshot.
