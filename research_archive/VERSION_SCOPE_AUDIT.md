# Version and scope audit

Audit point: **2026-10-08**. Current HEAD is `fad468e59b14047477a1a3e19f15a2e7618d61aa`; the worktree is dirty. This comparison uses Git trees/history and repository documents only. It does not treat current uncommitted files as part of either commit.

## A. Scientific content at `40cf69e`

`40cf69ed5396f9cb2256a6f6566d47384d87b28d` is the 3.0 implementation baseline named in the later `3.0_RELEASE_SPEC.md`. At that tree, `biological_brain/` and tests contained the 3.0A–3.0C foundation and 3.0D 7A–7Z / 8A–8N architecture: connectome escape circuit, provenance and morphology layers, active GF/TTMn/PSI/DLMn models, GFS circuit and action-selection abstractions, and tests. `40cf69e` itself added the accumulated 7X–8N dependencies listed in its commit message. The later release specification records 1151 passed / 2 warnings on Python 3.10.20 for this baseline.

The `research/` directory was absent at the `40cf69e` tree. The following did **not** yet exist there: MaleCNS PSI→MN5 contact/compartment audit, model-input freeze, reduced MN5 pipeline, final two-gate model, its sensitivity output, and the later claim/evidence ledgers.

## B. Scientific content added after `40cf69e`

The following post-baseline research work was committed by the time of `fad468e`:

| Commit | Committed research content |
|---|---|
| `4af2bd5` | Added `3.0_RELEASE_SPEC.md`; it defines scope but states that it applies to the earlier `40cf69e` baseline. |
| `27ea750` | Added the preliminary exploratory MN5 model reports, parameter ranges, and preliminary sensitivity outputs. These are now superseded for current final results. |
| `30cb22e` | Added `research/anatomy_registry.md`, `research/evidence_ledger.md`, the SWC Type concordance CSV/Markdown, analysis script, and test. |
| `cb399e4` | Added the PSI–MN5 reversal-potential audit. |
| `ab605cc` | Added `research/model_input_freeze.csv/.md`, its builder, and test. This is the source of the 108-row 40/31/37 buckets and NOT AUTHORIZED language for the reduced pipeline. |
| `d312d3e` | Added opt-in 3.0B product signal exposure. This is software/product state, not a biological result; the release spec documents default-off and visibility boundaries. |

Dashboard redesign (`71f0893`) and asset provenance reconciliation (`fad468e`) are in the ancestry but are not scientific results for this paper.

## C. Current scientific artifacts that are uncommitted

### Modified tracked paths

Scientific/research related:

- `biological_brain/__init__.py` — adds public exports for the reduced MN5 pipeline.
- `research/MN5_EXPLORATORY_FINAL_STATUS.md`, `research/anatomy_registry.md`, `research/evidence_ledger.md`.
- Earlier exploratory files: `research/exploratory_mn5_final_report.md`, `research/exploratory_mn5_model.md`, `research/exploratory_mn5_parameter_sensitivity.csv`, `research/exploratory_mn5_results_analysis.md`, `research/exploratory_mn5_scientific_review.md`, `research/exploratory_parameter_ranges.csv`, `research/exploratory_sensitivity_plan.md`.
- `tests/test_biological_brain.py` — modifies a source-text safety test; include only with the model code it validates.

The earlier exploratory outputs are not current final results; the final status document marks them historical/superseded.

### Untracked scientific paths

- Model/anatomy code: `biological_brain/exploratory_mn5.py`, `biological_brain/malecns_compartment.py`, `biological_brain/malecns_contact_path.py`, `biological_brain/malecns_ingest.py`, `biological_brain/malecns_mesh_geometry.py`, `biological_brain/model.py`, `biological_brain/model_framework.py`, `biological_brain/reduced_mn5.py`.
- Evidence/anatomy/model records: `research/source_registry.md`, `research/raw_data_registry.md`, `research/evidence_ledger.csv`, `research/conflicts.md`, `research/missing_evidence.md`, `research/dependency_graph.md`, `research/final_anatomy_audit.md`, `research/parameter_registry.md`, `research/parameter_adoption_plan.md`, `research/parameter_adoption_ledger.csv`, `research/model_input_audit.md`, `research/reduced_mn5_model.md`, `research/reduced_mn5_verification.md`, `research/mn5_psi_mn5_final_constraint_model.md`, `research/mn5_psi_mn5_final_constraint_model_sensitivity.csv`, `research/mn5_spatial_transfer_gate_review.md`, `research/spatial_transfer_evidence.md`, `research/da7_evidence.md`, `research/mn5_psi_genetic_access_audit.md`, `research/psi_mn5_direct_voltage_experiment_audit.md/.csv`, `research/psi_mn5_optical_experiment_design_audit.md/.csv`, and `research/psi_mn5_reversal_experiment_audit.md/.csv`.
- Data/analysis scripts: `research/artifacts/malecns_compartment_post_psi_mn5.csv`, `research/artifacts/malecns_compartment_post_summary.json`, `research/scripts/analyze_mn5_two_gate_constraint_model.py`, `research/scripts/build_reversal_experiment_audit.py`, `research/scripts/generate_evidence_ledger_csv.py`, `research/scripts/precomputed_annotations.py`, `research/scripts/retrieve_malecns_compartment_post.py`.
- Tests: `tests/malecns_real_data.py`, `tests/test_exploratory_mn5.py`, `tests/test_exploratory_mn5_results_analysis.py`, `tests/test_malecns_anatomy_audit.py`, `tests/test_malecns_compartment.py`, `tests/test_malecns_contact_path.py`, `tests/test_malecns_infrastructure.py`, `tests/test_malecns_mesh_geometry.py`, `tests/test_malecns_mesh_parser.py`, `tests/test_mn5_spatial_transfer_gate_review.py`, `tests/test_mn5_two_gate_constraint_model.py`, `tests/test_model_framework.py`, `tests/test_model_pipeline.py`, `tests/test_parameter_adoption.py`, `tests/test_psi_mn5_optical_experiment_design_audit.py`, `tests/test_psi_mn5_reversal_experiment_audit.py`, `tests/test_reduced_mn5.py`, and `tests/test_reduced_mn5_audit.py`.

Publication-audit and paper metadata files created in this workstream are also untracked. Product/dashboard changes (`fly_bot.py`, `fly_state.json`, and `tests/test_visual_command_intent.py`) are uncommitted but outside the scientific paper scope.

## D. Exact changes necessary for the intended paper scope

The paper scope is the combined, explicitly separated account defined in `PAPER_SCOPE_FREEZE.md`: the committed 3.0 research/software baseline; MaleCNS v1.0 contact/annotation results; the current provenance/input inventories; the evidence-safe reduced model; and the later conditional two-gate analysis. This is a **post-40cf research snapshot**, not a claim that the later research existed at `40cf69e`.

Necessary snapshot changes are therefore:

1. Commit the selected current evidence, anatomy, model-input, reduced-model, final-analysis, output, and validation artifacts listed as required in `REQUIRED_RELEASE_SNAPSHOT.md`.
2. Commit the current modifications to the evidence/anatomy records and the required reduced-model package export/test only if the reduced-model component is retained.
3. Add provenance/checksums for derived outputs and complete the available raw-data staging/environment record; do not include raw MaleCNS data without license review.
4. Include the scope freeze and claim language standard so the authorization boundary travels with results.
5. Keep dashboard/MATE modifications and local/private files out of the scientific release selection.

No change to biological-model behavior, parameter values, or conflict status is needed to resolve the terminology distinction. “MODEL-AUTHORIZED” can consistently mean permission to run an assumption-bound conditional analysis; the outputs stay model-derived. The reduced-model API remains unable to use unmeasured transfer or Dα7 values as biological inputs.

## E. Can the paper describe post-`40cf69e` work?

**Yes, as post-baseline research**, if the manuscript states the exact later snapshot/commit and distinguishes it from the `40cf69e` release-spec validation baseline. The later committed work at `fad468e` includes the model-input freeze and earlier anatomy/concordance records, but the current final two-gate analysis, reduced MN5 pipeline, several source/evidence records, final outputs, and their tests remain uncommitted.

The exact source snapshot for the intended paper is **not established**. `fad468e` is only the base commit; it does not contain all current scientific artifacts. The dirty worktree has no source tree hash corresponding to the reported 1773 passed / 2 skipped result. A new, explicitly scoped release commit must be created and tested before the manuscript can cite a frozen reproducible snapshot.

## F. Exact snapshot that must eventually be committed

The eventual paper snapshot must be a **new release commit descended from**
`fad468e59b14047477a1a3e19f15a2e7618d61aa`. That is the exact determinable
base commit; neither `40cf69e` nor the dirty worktree is the paper release.
The new commit SHA cannot be known until the release content is reviewed and
committed.

That release commit must contain the selected scientific source/code, research
records, derived analysis outputs, claim/evidence documentation, and tests
enumerated in `REQUIRED_RELEASE_SNAPSHOT.md`, with the final selection recorded
in `paper/PUBLICATION_MANIFEST.csv`. It must also include a validation report
generated from a clean checkout of that commit, with the external-data
provenance/staging limits stated. The historical 1773-pass run has no
established exact source tree and must not be used as validation for the new
commit. Until then, the current dirty worktree is not a release and has no
paper-citable snapshot hash.
