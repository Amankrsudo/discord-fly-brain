# Review-only Manuscript PDF — Build and Inspection Status

**Status:** REVIEW PDF BUILT AND VISUALLY INSPECTED — editorial review only, not submission-ready.
**Source branch:** `review/scientific-claim-corrections`.
**Source commit:** `a56875e8e85e73429a50f1a360cd72067ed249c8`.
**CI run:** [GitHub Actions run 38205908211](https://github.com/Amankrsudo/discord-fly-brain/actions/runs/38205908211).

## Implemented

- `paper/REVIEW_MANUSCRIPT.md` assembles the five existing draft sections, four tables, eight SVG figures, a generated reference list, and visible author/affiliation placeholders.
- `paper/scripts/build_review_pdf.py` renders HTML and PDF, labels the output **REVIEW ONLY — NOT FOR SUBMISSION**, and includes the CI source SHA in the generated document.
- `.github/workflows/research-branch-validation.yml` uses a pinned Markdown/WeasyPrint/PyPDF toolchain, builds the PDF, checks extracted text/page count and scientific guardrails, and uploads the PDF and HTML as `review-only-manuscript-pdf` for 14 days.
- The first build exposed a WeasyPrint/pydyf incompatibility; the dependency was pinned. A subsequent visual inspection caught and fixed the SVG base-path issue.
- Draft-only figure/table planning notes were removed from the assembled manuscript source before the successful build.

## Build and inspection results

- **PDF:** 30 pages, A4, 234,922 bytes.
- **Visual inspection:** inspected the rendered 30-page contact sheet; all eight SVG figures are present and visible. Tables and reference list render; no draft-only “Figure/table proposal” / “Exists: No” notes remain.
- **Automated PDF check:** passed on the build job, including review-only label, Gate A/Gate B wording, author placeholder, reference inclusion, and minimum page count.
- **Artifact:** `review-only-manuscript-pdf`, artifact ID `11727401642`; expires 2026-10-26. [Download from Actions](https://github.com/Amankrsudo/discord-fly-brain/actions/runs/38205908211).
- At the time of this status update, the manuscript-artifacts job has passed; the separate Python-test job is still running. This does not mean the full repository suite is green.

## What the build does not establish

- This is a review layout, not journal-formatted or submission-ready.
- The bibliography is mechanically rendered from `references.bib`; incomplete or verification-required metadata remains an editorial issue.
- Author order, affiliations, correspondence, acknowledgements, funding, data/code availability, and final attribution still require human confirmation.
- Figures are grouped in a figure section after the main text and tables; this is not an editorially finalized journal layout.
- Software tests and PDF generation are not empirical biological validation.

## Remaining review items

1. Confirm author order, affiliations, corresponding author, funding, acknowledgements, and data/code availability.
2. Review the machine-rendered bibliography and resolve every verification-required citation.
3. Review CC-BY attribution and data redistribution conditions.
4. Reconcile historical claims in `SUBMISSION_READINESS_REPORT.md` with current provenance and CI evidence.
5. Keep the final source commit and artifact together if the PDF is revised.

## Scientific safeguards preserved

- Gate A — PSI→MN5 spatial voltage transfer: **NOT AUTHORIZED**.
- Gate B — native PSI→MN5 Dα7 conductance: **NOT AUTHORIZED**.
- Do not infer attenuation, transfer resistance, Cm, Rm, g_pas, Ra, time constants, length constants, or electrotonic distance from morphology.
- Preserve C-01 (capacitance) and C-02/C-03 (conductance-unit conflicts) as unresolved.
- The 15,528 sensitivity rows remain conditional model outputs, not native biological validation.
