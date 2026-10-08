# Reproducibility gaps

This audit uses repository records and read-only existence checks. It does not download data, run scientific analyses, or rerun the full test suite.

## Environment and dependencies

- Current interpreter: Python 3.10.20.
- `requirements.txt` contains only lower bounds / unpinned dependencies: `discord.py>=2.4`, `python-dotenv`, and `Pillow>=10.0.0`.
- No project lockfile or full research environment specification was found. The current full-suite result does not include a saved `pip freeze` or exact installed dependency versions.
- The MaleCNS contact reader and SWC/mesh processing code largely use Python standard-library facilities, but the large Feather parser and research tests have external package requirements not pinned by the repository's `requirements.txt`. A clean install recipe for every research workflow is missing.

## Test command and source snapshot

- Latest reported full-suite result: **1773 passed, 2 skipped**.
- The reported command was `python -m pytest tests/ -v --tb=short --ignore=tests/test_diagnostics.py`.
- `3.0_RELEASE_SPEC.md` gives a different historical canonical command, `python -m pytest tests/ -q --tb=short --ignore=tests/test_diagnostics.py`, and a result of 1151 passed / 2 warnings at `HEAD=40cf69e` on Python 3.10.20. Do not present that as the current full-suite result.
- Current HEAD is `fad468e59b14047477a1a3e19f15a2e7618d61aa`; the worktree is dirty with modified and untracked files.
- The 1773/2 run happened before the asset audit reconciliation commit and on a dirty worktree based on `71f089319076d227029637fe75d6477e60a632ef`. The exact tested file state/tree hash and execution date were not recorded. It is unknown whether every current scientific worktree file was included in that run.
- No clean checkout of the intended paper snapshot has been tested. Software tests are not empirical biological validation.

## MaleCNS source data and retrieval

- Source recorded by the repository: MaleCNS v1.0, `male-cns:v1.0`, portal `https://male-cns.janelia.org/`, root `gs://flyem-male-cns/v1.0/`.
- Required raw table: `syn-partners-male-cns-v1.0-minconf-0.5.feather` (about 6.5 GB), expected in the OS temporary directory. It exists in the current machine's temporary directory outside the repository; it is not part of a clone or Git snapshot.
- The repository documents no exact command to download/stage that raw table and no expected SHA-256 for it. Do not infer a retrieval command or checksum.
- `research/scripts/retrieve_malecns_compartment_post.py` reads the pre-staged Feather file and requests matching annotation-layer entries over HTTP range requests; it does not download the Feather file.
- The source registry records the public distribution as CC-BY. The exact license text and release-specific raw-data redistribution review are not stored in this repository; verify before republishing the raw table.
- Two SWC files are external cached inputs: `em_801970.swc` and `em_801295.swc`. Their SHA-256 values are embedded in the concordance/two-gate scripts. Those hashes do not validate the Feather source. Mesh hashes are recorded in `research/anatomy_registry.md`.

## Processed data generation

The scripts document these commands and outputs:

| Command | Expected input | Expected output |
|---|---|---|
| `python research/scripts/retrieve_malecns_compartment_post.py` | Temp-directory Feather file; public annotation layer | `research/artifacts/malecns_compartment_post_psi_mn5.csv`; `research/artifacts/malecns_compartment_post_summary.json` |
| `python research/scripts/analyze_mn5_compartment_post_swc_type.py` | Processed annotation CSV; cached `em_801970.swc` and `em_801295.swc` | `research/mn5_compartment_post_swc_type_concordance.csv`; `.md` companion |
| `python research/scripts/analyze_mn5_two_gate_constraint_model.py` | Concordance CSV; cached SWCs with expected hashes | `research/mn5_psi_mn5_final_constraint_model_sensitivity.csv` (15,528 rows reported by current analysis documentation) |

The processed artifacts exist in the current worktree, but the two-gate outputs and several input records are untracked. Their exact file bytes are not pinned to a public commit. The processing path and annotation interpretation are documented in `research/final_anatomy_audit.md`, `research/anatomy_registry.md`, and the scripts.

## Model-input generation and model code

- `research/model_input_freeze.csv` is the current strongest parameter input artifact; `research/model_input_freeze.md` is its generated explanation.
- The builder documents `python research/scripts/build_model_input_freeze.py`; it writes both artifacts. It has not been rerun in this checkpoint.
- The freeze records 108 parameters: 40 safe, 31 assumption-only, 37 blocked; 15 conflict entries are retained. PSI→MN5 native spatial voltage transfer and native Dα7 conductance are marked **NOT AUTHORIZED** in the freeze and reduced-model pipeline.
- The separate two-gate research analysis calls its abstract bridge / effective Dα7 sweep model-authorized. This is only interpretable as conditional model output; the differing authorization wording requires a scope decision and precise description before publication. It does not authorize native measurements or values.
- The reduced pipeline's source and test files are part of the dirty/untracked worktree. Pin exact revisions of the freeze, builders, analysis scripts, model modules, and tests together before claiming reproducibility.

## Remaining reproducibility blockers

1. Select and commit/pin the exact scientific file set and resolve whether the later MN5 two-gate analysis is within the paper's scope defined by the older `3.0_RELEASE_SPEC.md`.
2. Provide a clean environment specification with exact dependency versions and supported Python version.
3. Record a reproducible, permitted way to obtain/stage the external Feather/SWC inputs and a verified checksum for the Feather file.
4. Pin the processed outputs to a source revision and record their generation environment.
5. Re-run focused and full software suites on the chosen clean snapshot if a current release validation claim is needed. Keep these results separate from biological evidence.
6. Reconcile freeze versus analysis gate wording without changing the scientific status of the unresolved gates.
