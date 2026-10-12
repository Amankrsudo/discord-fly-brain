# Submission Readiness Report

**Status: CONDITIONAL — NOT READY FOR JOURNAL SUBMISSION**  
**Last reconciled:** 2026-10-12  
**Branch:** `review/scientific-claim-corrections`  
**Pull request:** https://github.com/Amankrsudo/discord-fly-brain/pull/1

This report distinguishes historical audit statements from current evidence. A successful review-PDF build and focused tests do not establish final editorial readiness, biological validation, or a green full test suite.

## 1. Current deliverables and evidence

The review-only manuscript source is `paper/REVIEW_MANUSCRIPT.md`; the renderer is `paper/scripts/build_review_pdf.py`. The GitHub Actions workflow builds a PDF and HTML artifact labelled **REVIEW ONLY — NOT FOR SUBMISSION**.

The latest confirmed review-only PDF was built from source commit `119ac5379af58427a23810fc3bce941e78b824bf` in Actions run [38209499640](https://github.com/Amankrsudo/discord-fly-brain/actions/runs/38209499640). Both jobs passed. The PDF is a review artifact only; it predates the citation corrections committed afterward (`6fdd8a7` and `ee2dc83`) and therefore must be rebuilt before relying on it as the current manuscript snapshot. The earlier visually inspected 30-page build is not the final candidate. Preserve the source commit and artifact together when the next build is available.

## 2. Current CI status — do not overstate

For Actions run `38209499640` on commit `119ac5379af58427a23810fc3bce941e78b824bf`:

- **manuscript-artifacts: PASS.** Figure/table generation, whitespace check, review-PDF build, PDF text/page checks, and manuscript/reference/gate checks completed successfully for that commit.
- **focused MN5 provenance/gate tests: PASS.** The required focused step completed successfully.
- **broad test-suite audit: 1,637 passed, 13 failed, 39 skipped, 3 errors** in 232.88 seconds. The failures/errors include missing research documents (`asset_evidence_resolution.md`, `OVERNIGHT_CHECKPOINT.md`, `research_done.md`), an asset-inventory/hash drift, exploratory-model wording/parameter-count expectations, and absent externally staged SWCs (`/tmp/em_801970.swc`). This is a real non-green broad-suite result, not a pass. The workflow's broad-suite step is configured `continue-on-error`, so the job can still report success despite this audit failure.
- **Current citation corrections are newer than this run** (`6fdd8a7` and `ee2dc83`) and have not yet been validated or rebuilt by Actions at the time of this report update.

The review-PDF and focused-test results apply only to the exact source commit named above. Do not present historical counts (including 1,773 broad-suite passes with two skips) as the current suite result.

## 3. Editorial blockers before submission

The assembled PDF is a review layout, not an eNeuro-ready submission package. The following require explicit human confirmation or further verification:

- [ ] Replace author-name/order and affiliation placeholders; confirm corresponding author and contact details.
- [ ] Confirm acknowledgements, funding, competing interests, author contributions, and data/code availability statements.
- [ ] Rebuild the review PDF after the latest reference corrections. Three mismatched titles were corrected in `paper/references.bib` (Ryglewski & Duch 2009, Fayyazuddin et al. 2006, Yang et al. 2016), and the citation audit was updated; these changes still need a fresh Actions build and final in-text/orphan-reference reconciliation.
- [ ] Resolve remaining uncertain metadata and confirm the preferred MaleCNS dataset citation, project authorship/release metadata, and final attribution. Do not claim the bibliography is fully verified.
- [ ] Review MaleCNS CC-BY attribution and the applicable data redistribution conditions; ensure the final attribution matches the source and journal requirements.
- [ ] Confirm figure legends, image quality, figure placement, and journal-specific formatting in the final submission layout.
- [ ] Rebuild and inspect the PDF after manuscript-source changes, recording the exact source commit and artifact together.
- [ ] Re-run and record the citation/reference audit and all relevant tests against the exact final candidate.

## 4. Provenance claims requiring careful wording

Prior audit notes record a local SHA-256 for the staged MaleCNS Feather and hashes for the two SWC skeletons. A locally computed digest establishes the identity of the staged file; it does **not**, by itself, establish a match to an independently publisher-provided expected checksum. Earlier documentation explicitly noted that no independent publisher-provided expected checksum had been identified for the synapse-pair Feather. Keep that limitation visible unless new independent evidence is added.

The staging command is documented, but successful re-staging depends on external access and environment configuration. Do not equate documentation of a command with independent end-to-end reproducibility. Any mesh-hash claims should identify exactly which files were checked and which expected values were used.

Earlier statements that “all VERIFY_REQUIRED items are resolved” and that the package is “externally reproducible” are too categorical for the current evidence and have been superseded by this report.

## 5. Scientific guardrails — unchanged

- **Gate A — PSI→MN5 spatial voltage transfer: NOT AUTHORIZED.**
- **Gate B — native PSI→MN5 Dα7 conductance: NOT AUTHORIZED.**
- Do not infer attenuation, transfer resistance, (C_m), (R_m), (g_{pas}), (R_a), time constants, length constants, or electrotonic distance from mesh geometry.
- Do not equate morphological path length with electrotonic distance or use a somatic EPSP alone to identify local synaptic conductance or spatial transfer.
- Recombinant receptor data do not establish native PSI→MN5 Dα7 conductance.
- Preserve the unresolved MN5 capacitance conflict C-01 (43 ± 2 pF vs 127 ± 16 pF) and conductance conflicts C-02 (GF gap-junction 135 µS vs 135 nS) and C-03 (PSI→DLMn chemical conductance 80 µS vs 0.08 µS).
- The 15,528 sensitivity rows are conditional model outputs, not native biological validation.
- Retain SWC annotation/provenance caveats and the absence of an established MN5-specific axial-resistivity value.

## 6. Decision

**Current decision: continue editorial review; do not submit this PDF.** Primary-record checks caught three materially incorrect bibliography titles, now corrected on the draft branch, and the audit records what remains unverified. The broad suite currently has 13 failures and 3 errors in the last confirmed run; focused tests and the review-artifact build passed on the preceding commit. The latest citation changes still need CI and PDF regeneration. Author metadata, dataset attribution, final journal layout, and exact-candidate validation remain open. This report does not authorize opening either scientific gate or resolving any biological conflict.

---

This status reconciles the earlier `SUBMISSION_READINESS_REPORT.md` with the review-build record and the observed Actions job results as of 2026-10-12.
