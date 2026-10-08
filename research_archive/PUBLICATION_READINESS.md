# Publication Readiness

## Ready

- A candidate evidence inventory, claim matrix, data README, MaleCNS audit, citation audit, reproducibility gap report, external-data reproducibility record (`research_archive/EXTERNAL_DATA_REPRODUCIBILITY.md`), and artifact manifest exist. The existing proposed figure plan is at `paper/figures/FIGURE_PLAN.md`; no figures were generated.
- The repository preserves the relevant evidence classes and records the unresolved C-01/C-02/C-03, native PSI→MN5 transfer, native Dα7 conductance, SIZ registration, and ShakB conductance limits.
- MaleCNS v1.0 identity, source portal, annotation layer, local raw-file expectation, derivative outputs, and available SWC checksums are recorded without downloading data.

## Checkpoint Decisions

1. **Is scientific scope now defined? Yes.** `PAPER_SCOPE_FREEZE.md` defines the included work, exclusions, evidence boundaries, safe/unsafe claims, and the distinct meaning of model-authorized conditional analysis.
2. **Is the exact paper snapshot defined? No.** The proposed contents and exact base commit are recorded, and all 89 required paths currently exist, but the manifest still has manual-review rows, files are uncommitted, external-input provenance is incomplete, and no clean snapshot has been validated. The exact source tree for the historical 1773-pass run is unknown.
3. **Is manuscript drafting authorized? No.** Drafting must wait until the exact paper snapshot is committed and its validation is reproducible.

## Release Snapshot Checkpoint

- `paper/PUBLICATION_MANIFEST.csv` has 78 classified rows: 65 release-required, 8 supporting, 2 historical, 1 internal, 0 private, and 2 manual review.
- The former broad biological-directory, figure-plan, and experimental-design manual-review rows are resolved to file-scoped release entries and supporting documentation. Two manual-review rows remain: incomplete `CITATION.cff` metadata and the unestablished project-wide `LICENSE`. See `RELEASE_MANIFEST_REVIEW.md` and `CITATION_RELEASE_BLOCKERS.md`.
- `RELEASE_CONTENT_CHECK.md` finds all 89 paths enumerated from the required snapshot proposal in the current worktree. This confirms presence only; it does not mean those files are tracked, reproducibly generated, or frozen.
- No files were staged and no commit was created. The current tree is not a release snapshot.

## Not Ready

**Manuscript drafting is not authorized.** The current worktree is dirty at `fad468e59b14047477a1a3e19f15a2e7618d61aa`; core current research records, analysis scripts, derived outputs, model code, and tests are modified or untracked. There is no commit/tree hash for the exact 1773-pass full-suite run. The candidate manifest is provisional, not a frozen release manifest.

## Manual Decisions Required

- Confirm project authors/contributors, citable software title, release version/date, repository URL, DOI, software license, complete citations, and MaleCNS attribution/redistribution terms. Missing citation facts are marked VERIFY_REQUIRED.
- Resolve the two remaining manual-review rows listed in `RELEASE_MANIFEST_REVIEW.md`, and freeze the exact selected artifact rows in `paper/PUBLICATION_MANIFEST.csv`.
- Confirm a permitted MaleCNS Feather staging method and an expected checksum; do not redistribute the dataset without confirming the applicable license and attribution. See `research_archive/EXTERNAL_DATA_REPRODUCIBILITY.md` for the documented provenance, staging expectations, and VERIFY_REQUIRED items.

## Blocking Scientific Issues

- C-01 MN5 capacitance conflict (43 ± 2 pF vs 127 ± 16 pF) remains unresolved.
- C-02 gap-junction unit discrepancy and C-03 PSI→DLMn conductance discrepancy remain unresolved as documented.
- Native PSI→MN5 voltage transfer is unmeasured; contact-to-soma paths are not anatomically established.
- Native Dα7 conductance/density and direct SIZ-to-MaleCNS registration are unavailable.
- Absolute ShakB conductance and MaleCNS SWC `kind` semantics remain unresolved.
- No conditional model result or official `compartment_post` label may be promoted to native physiological measurement.

## Blocking Reproducibility Issues

- No exact selected artifact set is committed or pinned; many required science files are untracked and some evidence records are modified.
- The authoritative release specification is tied to `40cf69e`; the defined paper scope includes the later MN5 analysis as post-baseline research, which must be pinned separately in the new release commit.
- The raw Feather input has no expected checksum or documented download/staging command. It exists only in the current machine's temp directory, not the repository. `research_archive/EXTERNAL_DATA_REPRODUCIBILITY.md` records the following items as `VERIFY_REQUIRED`:
  - Feather SHA-256 checksum
  - complete Feather download/staging procedure
  - complete SWC download/staging procedures
  - external license/redistribution terms
  - complete MaleCNS author attribution
- `LICENSE = VERIFY_REQUIRED`: the project-wide software license is not established by a tracked/root `LICENSE` or `COPYING` file. The incomplete citation scaffold and bibliography are not final release metadata.
- Exact dependency versions and a full clean environment recipe are missing. Current `requirements.txt` is not a research lockfile.
- The reported 1773 passed / 2 skipped run was on a dirty pre-`fad468e` snapshot, with no exact tested tree hash. It does not validate the current worktree.
- Processed outputs exist but are not all pinned to a commit/source snapshot.
- Clean-checkout validation of the release snapshot: VERIFY_REQUIRED.

## Next Required Step

Resolve the manual manifest decisions and metadata, authorship, licensing, and external-data provenance blockers first. Then select exact files, create the release commit descended from `fad468e59b14047477a1a3e19f15a2e7618d61aa`, and validate it from a clean checkout, recording the exact commit/tree identity and results. Only then reassess manuscript-drafting authorization. This checkpoint does not authorize drafting.
