# Review-only Manuscript PDF — Build and Inspection Status

**Status:** A reproducible review-only build pipeline is now committed; artifact generation and inspection are pending the next GitHub Actions run.
**Current branch:** `review/scientific-claim-corrections`.
**Scope:** Editorial review only, explicitly not an eNeuro submission package.

## Implemented

- `paper/REVIEW_MANUSCRIPT.md` assembles the five existing draft sections, four tables, eight SVG figures, a generated reference list, and visible author/affiliation placeholders.
- `paper/scripts/build_review_pdf.py` renders the source to HTML and PDF, labels the output **REVIEW ONLY — NOT FOR SUBMISSION**, and includes the current CI source SHA in the generated document.
- `.github/workflows/research-branch-validation.yml` now installs a pinned Markdown/WeasyPrint/PyPDF toolchain, builds the PDF, checks extracted text/page count and critical scientific guardrails, then uploads the PDF and HTML as `review-only-manuscript-pdf` for 14 days.
- `paper/README.md` points to the assembled source and build instructions.

## What the build does not establish

- It is a review layout, not journal-formatted or submission-ready.
- The bibliography is mechanically rendered from `references.bib`; missing or verification-required metadata remains an editorial issue.
- Author order, affiliations, correspondence, acknowledgements, funding, data/code availability, and final attribution still require human confirmation.
- Figure placement is grouped in a figure section after the main text and tables; it is not yet an editorially finalized journal layout.
- The PDF has not been called successful or inspected until the GitHub Actions run produces an artifact and the artifact is actually checked.

## Required post-build inspection

1. Confirm the `manuscript-artifacts` job succeeds and the `review-only-manuscript-pdf` artifact exists.
2. Download the artifact and inspect page count, SVG rendering, clipping, table width, reference output, placeholders, and all eight figures.
3. Confirm Gate A and Gate B remain **NOT AUTHORIZED**, C-01/C-02/C-03 remain unresolved, and the 15,528 rows are still described as conditional model outputs.
4. Record the exact source commit SHA and build result. If rendering or inspection fails, fix the pipeline before claiming a usable review PDF.

## Scientific safeguards

- Gate A — PSI→MN5 spatial voltage transfer: **NOT AUTHORIZED**.
- Gate B — native PSI→MN5 Dα7 conductance: **NOT AUTHORIZED**.
- Do not infer attenuation, transfer resistance, Cm, Rm, g_pas, Ra, time constants, length constants, or electrotonic distance from morphology.
- Preserve the C-01 capacitance conflict and C-02/C-03 conductance-unit conflicts as unresolved.
- Software tests and PDF generation are not empirical biological validation.
