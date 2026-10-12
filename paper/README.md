# Fly Brain 3.0 research package

This directory contains the Fly Brain 3.0 manuscript package: claim/evidence map, abstract draft, introduction, methods, results, discussion drafts, references, figure manifest, eight generated SVG figures, four tables, and supporting documentation.

## Scope

Fly Brain 3.0 covers research and software for a Drosophila giant-fiber-system model and its PSI→MN5 question. The release distinguishes the product's existing 2.0 `GroupBrain` behaviour path, the opt-in 3.0B escape-circuit implementation, and the 3.0D GFS/MN5 research model. The GFS/MN5 model has no Discord entry point. Product behaviour and model outputs are software behaviour; they do not establish biological measurements.

The MaleCNS analysis is restricted to the recorded male adult dataset, identifiers, confidence threshold, and published annotation fields. `compartment_post="axon"` is a dataset label. It is not a voltage-transfer measurement, contact-to-soma path, or electrophysiology result.

## Evidence and validation

The project keeps five evidence classes separate: native experimental measurement (NEM), anatomical measurement (AM), literature-derived passive parameter (LDP), model-derived estimate (MDE), and model assumption (MA). These are enforced in `biological_brain/model_framework.py` (`ModelProvenance`) and `biological_brain/malecns_ingest.py` (`EvidenceClass`). See [evidence classification](../methods/provenance/evidence_classification.md) and [claim/evidence matrix](claim_evidence_matrix.csv).

The validation package records software tests, provenance checks, numerical/model consistency checks, and dataset extraction checks separately from biological evidence. Software tests can show that code meets specified expectations; they are not empirical biological validation. See [full-suite report](../validation/full_suite_report.md) and [reproducibility gaps](../validation/REPRODUCIBILITY_GAPS.md).

## Data and model inputs

The public MaleCNS source and known local inputs/outputs are described in [data/README.md](../data/README.md). The current strongest model-input record is `research/model_input_freeze.csv`, with its generated companion `research/model_input_freeze.md`; neither was changed by this scaffold. See [model input notes](../methods/model_inputs/README.md).

## Manuscript artifacts

- `ABSTRACT_DRAFT.md` — abstract draft (249 words)
- `INTRODUCTION_DRAFT.md`, `METHODS_DRAFT.md`, `RESULTS_DRAFT.md`, `DISCUSSION_DRAFT.md` — manuscript sections
- `CLAIM_EVIDENCE_MAP.md` — 19 claims with evidence classes and provenance
- `CLAIM_LANGUAGE_STANDARD.md` — permitted/prohibited claim wording
- `MANUSCRIPT_OUTLINE.md` — section-by-section plan
- `MANUSCRIPT_CONSISTENCY_AUDIT.md` — cross-document audit (DISC-01 resolved)
- `MANUSCRIPT_READING_GUIDE.md` — beginner-friendly companion (1123 lines)
- `MANUSCRIPT_READING_CHECKLIST.md` — reviewer checklist
- `SUBMISSION_READINESS_REPORT.md` — status tracking (historical audit; reconcile before relying on submission claims)
- `REVIEW_MANUSCRIPT.md` — assembled review-only manuscript source with visible author placeholders, four tables, eight figures, and a generated bibliography insertion point
- `scripts/build_review_pdf.py` — reproducible HTML/PDF builder for editorial review only; output is explicitly NOT FOR SUBMISSION
- `REVIEW_BUILD_BLOCKERS.md` — build pipeline status, limits, and post-build inspection checklist
- `references.bib` — 20 BibTeX entries; DOI and metadata verification is mixed, with unresolved entries explicitly marked for review
- `FIGURE_TABLE_MANIFEST.md` — figure/table registry with sources
- `PUBLICATION_MANIFEST.csv` — machine-readable release classification
- `claim_evidence_matrix.csv` — 8 claims with evidence-class codes
- `figures/FIGURE_1_gfs_circuit.svg` through `FIGURE_8_reproducibility.svg` — 8 generated figures
- `figures/FIGURE_PLAN.md` — figure generation plan
- `tables/FIGURE_TABLE_R1_contact_summary.md` through `R4_reproducibility.md` — 4 tables
- `scripts/generate_figures_tables.py` — figure/table generator script

## Release references and state

The repository identifies these release commits:

- `71f089319076d227029637fe75d6477e60a632ef` — dashboard visual-system redesign.
- `fad468e59b14047477a1a3e19f15a2e7618d61aa` — asset provenance audit reconciliation.

Latest reported full-suite result: **1773 passed, 2 skipped**, with `tests/test_diagnostics.py` excluded. The run was on a dirty worktree and is not tied to an immutable source-tree snapshot; details are in `validation/full_suite_report.md`. It is not biological validation.

## Limitations and unresolved gates

- Native PSI→MN5 spatial voltage transfer is not measured. A conditional abstract cable-bridge analysis is model-derived and does not establish native transfer.
- Native MN5 Dα7 conductance or receptor density is unavailable.
- SIZ registration to MaleCNS remains unresolved.
- C-01 MN5 capacitance values conflict (43 ± 2 pF versus 127 ± 16 pF).
- C-02 gap-junction conductance differs by 1000× between reported paper units and executed source units.
- C-03 PSI→DLMn chemical conductance differs by 1000× between reported paper and executed source.
- Absolute ShakB conductance is unknown.
- SWC `kind` semantics and anatomy-based contact-to-soma paths remain unresolved.
- The 4.71 ± 0.35 mV GF-stimulated EPSP is a comparison/calibration target, not a PSI-specific measurement.

This scaffold does not freeze or reconcile the modified/untracked research worktree. A version-pinned public archive and manual author, license, and data review are still required.
