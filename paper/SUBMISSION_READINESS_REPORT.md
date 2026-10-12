# Submission Readiness Report

**Status: CONDITIONAL — NOT READY FOR JOURNAL SUBMISSION**  
**Last reconciled:** 2026-10-12  
**Branch under current test-fix validation:** `fix/broad-suite-regressions`  
**Test-fix pull request:** https://github.com/Amankrsudo/discord-fly-brain/pull/2

This report distinguishes historical audit statements from current evidence. A successful review-PDF build and passing software tests do not establish final editorial readiness or biological validation.

## 1. Current deliverables and evidence

The review-only manuscript source is `paper/REVIEW_MANUSCRIPT.md`; the renderer is `paper/scripts/build_review_pdf.py`. The GitHub Actions workflow builds a PDF and HTML artifact labelled **REVIEW ONLY — NOT FOR SUBMISSION**.

The latest confirmed review-only PDF build is from Actions run [38213618643](https://github.com/Amankrsudo/discord-fly-brain/actions/runs/38213618643), commit `1b76580690f67fac78c4bf6ef3893cf4ff00e4bd`. The manuscript-artifacts job passed, including figure/table generation, review-PDF generation, PDF checks, and manuscript/reference/scientific-gate validation. Keep the exact source commit and its artifact together; this review PDF is not a submission-ready package.

## 2. Current CI status — exact run

For Actions run [38213618643](https://github.com/Amankrsudo/discord-fly-brain/actions/runs/38213618643), commit `1b76580690f67fac78c4bf6ef3893cf4ff00e4bd`:

- **manuscript-artifacts: PASS.** Figure/table generation, whitespace check, review-PDF build, PDF text/page checks, and manuscript/reference/gate checks completed successfully.
- **focused MN5 provenance/gate tests: PASS — 172 passed, 16 skipped.**
- **broad test-suite audit: 1,646 passed, 44 skipped, 0 failed, 0 errors** in 235.09 seconds.
- **Whitespace/diff check: PASS.** Both workflow jobs completed successfully.

The broad-suite audit step is configured `continue-on-error` in the workflow, so future reviews should continue to inspect the pytest summary rather than relying only on the overall Actions conclusion. The 44 skips are not failures; some external-SWC-dependent tests intentionally skip when the required staged SWC files are absent. A skipped test is not evidence that its data-dependent analysis passed.

## 3. Editorial blockers before submission

The assembled PDF is a review layout, not an eNeuro-ready submission package. The following require explicit human confirmation or further verification:

- [ ] Replace author-name/order and affiliation placeholders; confirm corresponding author and contact details.
- [ ] Confirm acknowledgements, funding, competing interests, author contributions, and data/code availability statements.
- [ ] Perform final in-text/orphan-reference reconciliation against the current rebuilt review PDF. The current Actions run builds successfully, but a passing build alone does not establish that every citation and reference has been manually reconciled.
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

**Current decision: continue editorial review; do not submit this PDF.** The latest confirmed CI run has a clean broad-suite result (1,646 passed, 44 skipped, no failures/errors) and a successful review-only PDF build. This establishes software/build status for the exact commit only; it does not close editorial blockers. Author metadata, acknowledgements/funding/disclosure statements, final citation reconciliation, dataset attribution/licensing review, final journal layout, and exact-candidate human inspection remain open. This report does not authorize opening either scientific gate or resolving any biological conflict.

---

This status was reconciled against Actions run `38213618643` on 2026-10-12. Historical failure counts above are superseded by the latest run; retain them only in the Actions history, not as current status.
