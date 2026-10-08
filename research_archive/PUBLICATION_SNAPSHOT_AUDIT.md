# Publication snapshot audit

Audit point: **2026-10-08**, current HEAD `fad468e59b14047477a1a3e19f15a2e7618d61aa`; worktree is dirty with modified and untracked files. This audit does not move, delete, or alter scientific artifacts. Private and deployment content was not opened.

## 1. Intended release snapshot

`3.0_RELEASE_SPEC.md` is the authoritative scope document in the repository, but it explicitly applies to `HEAD=40cf69e` and its established 1151-pass validation. It defines Fly Brain 3.0 as a biological modeling/research architecture (3.0A–3.0D, including the GFS model), not a Discord product release. The current HEAD is later, and the current worktree adds the PSI→MN5 contact-local/abstract-transfer analysis, frozen model-input inventory, reduced MN5 pipeline, and MaleCNS processing artifacts.

The later MN5 analysis is a plausible research-paper extension, but it is not pinned by the 3.0 release specification's source commit. The intended paper scope must decide explicitly whether it covers (a) the full 3.0 GFS architecture, (b) the newer MN5/PSI constraint analysis, or both. This audit does not silently expand the release definition. The exact candidate set below is provisional until this decision and the dirty worktree are resolved.

## 2. Required scientific artifacts

Candidate core for a paper centered on MaleCNS anatomy and the MN5/PSI constraint analysis:

- `3.0_RELEASE_SPEC.md` — scope/product boundary; pin its stated baseline and identify that it predates the current worktree.
- `research/source_registry.md`, `research/raw_data_registry.md`, `research/evidence_ledger.md`, `research/evidence_ledger.csv`, `research/conflicts.md`, `research/missing_evidence.md`, `research/dependency_graph.md`.
- `research/anatomy_registry.md`, `research/final_anatomy_audit.md`, `research/parameter_registry.md`, `research/parameter_adoption_plan.md`, `research/parameter_adoption_ledger.csv`.
- `research/model_input_freeze.csv`, `research/model_input_freeze.md`, `research/scripts/build_model_input_freeze.py`.
- `research/artifacts/malecns_compartment_post_psi_mn5.csv`, `research/artifacts/malecns_compartment_post_summary.json`, `research/mn5_compartment_post_swc_type_concordance.csv`, `research/mn5_compartment_post_swc_type_concordance.md`.
- `research/mn5_psi_mn5_final_constraint_model.md`, `research/mn5_psi_mn5_final_constraint_model_sensitivity.csv`, `research/scripts/analyze_mn5_two_gate_constraint_model.py`, `research/scripts/analyze_mn5_compartment_post_swc_type.py`, `research/scripts/retrieve_malecns_compartment_post.py`, `research/scripts/precomputed_annotations.py`.
- Source modules required by those scripts: `biological_brain/malecns_ingest.py`, `biological_brain/malecns_mesh_geometry.py`, `biological_brain/malecns_contact_path.py`, `biological_brain/malecns_compartment.py`, and `biological_brain/exploratory_mn5.py`.
- If the paper includes the separately verified evidence-safe reduced model: `biological_brain/model.py`, `biological_brain/model_framework.py`, `biological_brain/reduced_mn5.py`, `biological_brain/__init__.py`, `research/reduced_mn5_model.md`, `research/reduced_mn5_verification.md`, and the relevant tests. The modified `__init__.py` and untracked model code must be pinned together.
- Tests supporting included claims/pipelines: `tests/test_malecns_anatomy_audit.py`, `tests/test_malecns_compartment.py`, `tests/test_mn5_compartment_post_swc_type_concordance.py`, `tests/test_malecns_contact_path.py`, `tests/test_malecns_mesh_geometry.py`, `tests/test_malecns_mesh_parser.py`, `tests/test_malecns_infrastructure.py`, `tests/test_mn5_spatial_transfer_gate_review.py`, `tests/test_mn5_two_gate_constraint_model.py`, `tests/test_parameter_adoption.py`, `tests/test_model_input_freeze.py`, `tests/test_model_framework.py`, `tests/test_model_pipeline.py`, `tests/test_reduced_mn5.py`, `tests/test_reduced_mn5_audit.py`.
- `tests/malecns_real_data.py` and its required external data should be listed in validation provenance, not redistributed by default.

Most current MN5 research files and model modules in this list are untracked; `anatomy_registry.md` and `evidence_ledger.md` are modified. The set is not yet a frozen snapshot.

## 3. Supporting artifacts

These may support claims, methods, limitations, or a supplement after scope review and pinning:

- `research/da7_evidence.md`, `research/spatial_transfer_evidence.md`, `research/mn5_spatial_transfer_gate_review.md`, `research/psi_mn5_reversal_potential_audit.md`.
- `research/mn5_psi_genetic_access_audit.md` for the documented genetic-access limitations relevant to receptor claims.
- `research/psi_mn5_direct_voltage_experiment_audit.md`, its CSV, `research/psi_mn5_optical_experiment_design_audit.md`, its CSV, `research/psi_mn5_reversal_experiment_audit.md`, its CSV.
- `research/model_framework.md`, `research/model_pipeline.md`, `research/reduced_mn5_model.md`, `research/reduced_mn5_verification.md`.
- `research/final_anatomy_audit.md` and processed MaleCNS outputs named above.
- `research/FLY_BRAIN_3_0_FINAL_STATUS.md` is an untracked summary and not an authority; verify each statement against its source artifacts before using it.

## 4. Historical/superseded artifacts

- `research/MN5_EXPLORATORY_FINAL_STATUS.md` explicitly labels itself historical and superseded by the 15,528-row final constraint analysis. Retain only as historical context, not as current results.
- `research/exploratory_mn5_final_report.md`, `research/exploratory_mn5_model.md`, `research/exploratory_mn5_parameter_sensitivity.csv`, `research/exploratory_mn5_results_analysis.md`, `research/exploratory_mn5_scientific_review.md`, `research/exploratory_parameter_ranges.csv`, and `research/exploratory_sensitivity_plan.md` are earlier exploratory outputs. Do not mix their former sweep counts/calibrations with the current analysis without an explicit comparison.
- `research/OVERNIGHT_CHECKPOINT.md` and `research/RELEASE_CHECKLIST.md` are interim workflow records, not the current publication manifest or release validation.
- `3.0_RELEASE_SPEC.md` itself records the older `40cf69e` baseline and 1151 passed / 2 warnings; that result is historical relative to the later 1773/2 report.
- Older `research_archive/historical/` material, if later added, requires individual provenance and supersession labels. Nothing is moved in this checkpoint.

## 5. Internal-only artifacts

Do not include in the paper/release snapshot unless a separate review establishes a reproducible scientific role:

- One-off ledger diagnostics/fixes: `research/_diag_ledger.py`, `research/_diag2_ledger.py`, `research/_fix_ledger.py`, `research/_fix_ledger2.py`, `research/_fix_ledger3.py`, `research/_ledger_diag.txt`, `research/_ledger_diag2.txt`, `research/_ledger_fix_report.txt`, `research/_ledger_fix_report2.txt`, `research/_ledger_fix_report3.txt`.
- Asset/dashboard audits and product-facing specifications: `research/asset_evidence_resolution.md`, `research/asset_provenance_triage.md`, `research/biological_summary_claim_ledger.csv`, `research/biological_summary_evidence_audit.md`, `research/biological_summary_panel_spec.md`, `research/mating_asset_replacement_spec.md`, `research/next_biological_asset_audit.md`, `research/asset_replacement_ledger.csv`, `research/asset_replacement_plan.md`.
- Planning/backlog/novelty materials: `research/experiments_ranked.md`, `research/novelty_audit.md`, `research/research_done.md`, `research/search_log.md`, `research/RELEASE_CHECKLIST.md`, `FLY_BRAIN_2_0_ROADMAP.md`, `COPILOT_TEST_REPORT.md`.
- Product/dashboard implementation and runtime state: `fly_bot.py`, `brain_dashboard.py`, `dashboard_animation.py`, `fly_state.json`, `group_brain.py`, `dashboard assests/`, `sprites/`; these are outside the scientific paper dataset and include non-paper product work.
- Development helpers `build_clean_zip.ps1`, `__zip_build_temp__.py`, `rebuild_clean_zip.py`; not publication methods unless separately justified.

## 6. Private/do-not-publish artifacts

Exclude by default and do not inspect: `.env`, `fly-deploy-clean.zip`, `.vscode/`, `.kilo/`, local credentials/tokens/private configuration, and personal or machine-specific files. IDE configuration is not part of the scientific archive. No private file or deployment archive was read during this audit.

## 7. Conflicts or ambiguities requiring manual decision

1. **Paper scope:** the authoritative release spec is pinned to 40cf69e; the current MN5 constraint analysis is later and uncommitted. Decide whether the paper is the 3.0 release paper, an MN5/PSI research paper, or a clearly scoped combination.
2. **Gate wording:** `research/model_input_freeze.md` and the reduced pipeline state PSI→MN5 spatial transfer and Dα7 conductance are NOT AUTHORIZED. The later two-gate analysis calls an abstract bridge/effective Dα7 sweep MODEL-AUTHORIZED. Preserve the distinction: this is conditional model authorization only, never native measurement authorization. The paper's model scope and wording must be approved.
3. **Input freeze:** freeze says 108 rows (40 safe, 31 assumption-only, 37 blocked; 15 conflict entries). The parameter adoption plan separately reports 137 rows (98 KEEP, 17 sensitivity, 22 unresolved). These are different classification schemes, but the paper must state which artifact answers which question and ensure no counts are conflated.
4. **MaleCNS raw data:** repository records CC-BY, but the raw Feather has no checksum and no documented download/staging command; redistribution terms need manual review.
5. **Citation metadata:** project authorship, complete author lists, many titles, release version/DOI/URL, and a project-wide software license are absent or incomplete. See `CITATION_AUDIT.md`.
6. **Validation snapshot:** latest reported 1773 passed / 2 skipped was run before `fad468e` on a dirty tree based on `71f0893`; no exact tree hash exists. It cannot validate the present dirty worktree.
7. **Output pinning:** key processed/analyzed outputs currently exist as untracked files and are not tied to a commit.
8. **Prior archive index:** `research_archive/ARCHIVE_INDEX.md` refers to `research/3.0_RELEASE_SPEC.md` as missing, while the authoritative file is present at repository root as `3.0_RELEASE_SPEC.md`. Correct that inventory path before treating the index as a release manifest.

## 8. Exact files that must be included for the paper

Provisional core list is the “Required scientific artifacts” list in section 2, plus the applicable supporting records in section 3. At minimum, a paper using the MaleCNS and two-gate claims must include the exact evidence/source registries, conflict/input freezes, contact and annotation outputs, SWC concordance inputs, analysis script and model dependency, relevant tests, citation records, and a machine-readable manifest. If the paper discusses the reduced MN5 pipeline, include its code, freeze builder/input, verification report, and tests as a separate model with its limitations. Source data may be cited and retrieved under verified terms; the large raw Feather file should not be bundled until the license and checksum/retrieval questions are resolved.

The exact selected paths are enumerated row-by-row in `paper/PUBLICATION_MANIFEST.csv`; rows marked conditional require a scope decision. No row is yet frozen to a reproducible commit.

## 9. Exact files that must NOT be included

- Private/do-not-publish paths and directories in section 6.
- Internal-only product, dashboard, runtime, asset, debugging, and build-helper paths in section 5.
- Superseded exploratory results in section 4 as current evidence. They may appear only in a clearly labeled historical comparison if scientifically necessary.
- Unverified citations (S-17) and any artifact or data whose source/license cannot be established.
- No raw external dataset should be copied into the release by default; any redistribution requires affirmative license/attribution review.

This is an audit, not a commit, archive freeze, or approval to draft.
