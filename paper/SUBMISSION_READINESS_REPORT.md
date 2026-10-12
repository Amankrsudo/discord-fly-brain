# Submission Readiness Report

**Status: CONDITIONAL — NOT READY FOR JOURNAL SUBMISSION**  
**Last reconciled:** 2026-10-12  
**Branch:** `review/scientific-claim-corrections`  
**Pull request:** https://github.com/Amankrsudo/discord-fly-brain/pull/1

This report distinguishes historical audit statements from current evidence. A successful review-PDF build and focused tests do not establish final editorial readiness, biological validation, or a green full test suite.

## 1. Current deliverables and evidence

The review-only manuscript source is `paper/REVIEW_MANUSCRIPT.md`; the renderer is `paper/scripts/build_review_pdf.py`. The GitHub Actions workflow builds a PDF and HTML artifact labelled **REVIEW ONLY — NOT FOR SUBMISSION**.

The latest inspected artifact was rebuilt from source commit `7ad7c05be52ba75ada9ba861272aae45244556e4` after correcting stale validation and provenance wording. It is 30 pages (A4; 235,802 bytes). Automated PDF text checks passed for the review-only warning, both closed authorization gates, visible author placeholder, updated checksum-provenance wording, historical test-count qualification, and absence of the superseded stale claims. The PDF text was extracted locally and checked; the eight-figure rendering was visually inspected in the preceding build, while this latest build's CI text/page checks passed.

Actions run: https://github.com/Amankrsudo/discord-fly-brain/actions/runs/38206908260  
Artifact name: `review-only-manuscript-pdf`; artifact ID `11727991324`; digest `sha256:174f7d034f840311784ee905202b43a68f0b617e791a315dcadcad23d0d9c765`; expiry 2026-10-26. Artifact retention is temporary, so preserve a verified copy if needed.

## 2. Current CI status — do not overstate

For Actions run `38205908211`:

- **manuscript-artifacts: PASS.** Figure/table generation, whitespace check, review-PDF build, PDF text/page checks, and manuscript/reference/gate checks completed successfully.
- **focused MN5 provenance/gate tests: PASS.** The required focused step completed successfully.
- **broad test-suite audit: CANCELLED in this run.** The job was cancelled while that non-blocking step was running; this run does not establish a full-suite pass or failure.
- Therefore, **the complete workflow is not a clean all-jobs pass**. The broad-suite audit is explicitly configured as non-blocking because known unrelated baseline problems include missing research documents, asset-inventory drift, and externally staged SWCs. Report any later broad-suite result separately from the focused test result.

Historical counts in earlier reports (including 995 biological-brain tests and 1,773 broad-suite passes with two skips) are historical claims, not fresh evidence from this workflow run. Do not present them as the current full-suite result.

## 3. Editorial blockers before submission

The assembled PDF is a review layout, not an eNeuro-ready submission package. The following require explicit human confirmation or further verification:

- [ ] Replace author-name/order and affiliation placeholders; confirm corresponding author and contact details.
- [ ] Confirm acknowledgements, funding, competing interests, author contributions, and data/code availability statements.
- [ ] Review the machine-rendered bibliography against publisher records and the final in-text citations. Resolve uncited/orphaned references and incomplete or uncertain metadata; do not claim these are all resolved without a fresh citation audit.
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

**Current decision: continue editorial review; do not submit this PDF.** The review artifact and focused validation are useful milestones, but unresolved author metadata, reference/attribution review, final journal layout, and fresh exact-candidate validation remain. This report does not authorize opening either scientific gate or resolving any biological conflict.

---

This status reconciles the earlier `SUBMISSION_READINESS_REPORT.md` with the review-build record and the observed Actions job results as of 2026-10-12.
