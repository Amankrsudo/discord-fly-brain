# Review-only Manuscript PDF Build — Blockers

**Status:** BLOCKED — no review PDF was built or inspected from this branch.
**Audited ref:** `review/scientific-claim-corrections` at `702aa08e96cc23072cce1a2fceccb00c142af770`.
**Purpose:** Record the concrete requirements for a faithful review-only PDF without silently manufacturing a submission-ready manuscript.

## Findings from the branch audit

1. **The manuscript exists as separate draft files, not a single compilation source.** The branch contains `ABSTRACT_DRAFT.md`, `INTRODUCTION_DRAFT.md`, `METHODS_DRAFT.md`, `RESULTS_DRAFT.md`, and `DISCUSSION_DRAFT.md`, alongside an outline and reading aids. No integrated `MANUSCRIPT.md`, LaTeX entry point, or other canonical assembled manuscript was found.
2. **No PDF build recipe exists in the branch workflow.** `.github/workflows/research-branch-validation.yml` regenerates figures/tables and validates source text/BibTeX structure, but does not invoke Pandoc, LaTeX, or another PDF compiler and does not upload a PDF artifact.
3. **Figures are SVG assets, but there is no manuscript layout/figure-placement map that binds all eight figures and four tables into one final sequence.** The outline and manifest are planning/registry documents; they are not a verified, publication-formatted manuscript.
4. **Submission-readiness claims are not a safe build specification.** `SUBMISSION_READINESS_REPORT.md` contains older statements that all provenance items are resolved and the package is ready for submission. The current branch's methods and Figure 8 explicitly say no independent publisher-provided expected checksum was identified for the staged Feather file; attribution still needs author review. The report also cites inherited test counts and a 2026-10-09 audit, while current branch CI has a focused required test set and a broad-suite audit marked non-blocking.
5. **A rendered PDF could hide editorial decisions if assembled automatically.** The current sources include draft labels and author/affiliation placeholders are unresolved in the separate local Candidate 2 package; that local package is not part of this GitHub branch and cannot be treated as the branch's source or artifact.

## Required steps before a trustworthy review PDF

- [ ] Designate or create one canonical assembled manuscript source from the five draft sections; preserve their scientific wording and claim qualifiers.
- [ ] Resolve section ordering, title, author/affiliation placeholders, acknowledgements/funding, data/code availability, and correspondence fields—or visibly mark each unresolved item as a placeholder in the review PDF.
- [ ] Reconcile the stale statements in `SUBMISSION_READINESS_REPORT.md` with current provenance and CI evidence. Do not claim the Feather has an independent source checksum unless one is identified.
- [ ] Define an explicit figure/table placement order and captions, including all eight SVG figures and the four tables; ensure figures are regenerated from the current branch before rendering.
- [ ] Add a reproducible PDF build command and CI artifact upload, pin or record toolchain versions, and ensure the artifact name labels it **REVIEW ONLY — NOT FOR SUBMISSION**.
- [ ] Run the build on the exact PR head, download the produced artifact, and inspect page count, clipping, SVG rendering, references, figure order, placeholder visibility, and Gate A/B wording.
- [ ] Keep the PDF's source commit SHA and build log alongside the artifact so it is traceable to the reviewed branch snapshot.

## Scientific safeguards for the build

- Gate A (PSI→MN5 spatial voltage transfer) remains **NOT AUTHORIZED**.
- Gate B (native PSI→MN5 Dα7 conductance) remains **NOT AUTHORIZED**.
- Do not derive attenuation, transfer resistance, Cm, Rm, g_pas, Ra, time constants, length constants, or electrotonic distance from morphology.
- Keep C-01 (MN5 capacitance) and C-02/C-03 (conductance-unit conflicts) unresolved.
- Keep the 15,528 sensitivity rows explicitly model-derived and conditional, not native validation.
- Distinguish focused test success from the non-blocking broad-suite audit; do not label all tests green based solely on the workflow job status.

## Outcome

This audit intentionally stops before PDF generation because the branch lacks a canonical assembled manuscript and a defined, inspectable PDF build pipeline. The next safe implementation step is to create that canonical review source and reproducible build workflow, then inspect the actual artifact. No PDF build or visual inspection is claimed here.
