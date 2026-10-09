# Manuscript Outline — Fly Brain 3.0 (PSI→MN5 / Dα7)

**Relationship to `CLAIM_EVIDENCE_MAP.md`**: This outline links each planned manuscript section to the verified claim IDs from `paper/CLAIM_EVIDENCE_MAP.md`. A claim is included in a section only where its evidence status supports the statement.

**Gate status (unchanged)**:
- **PSI→MN5 spatial voltage transfer: NOT AUTHORIZED** — supported only by documented absence (C-401).
- **Dα7 biological conductance: NOT AUTHORIZED** — supported only by documented absence (C-501).

**Framing principle**: The manuscript reports (1) audited native measurements, (2) the conditional two-gate model as model-derived sensitivity, and (3) the precise gaps that block native claims — rather than presenting the model as validated biology.

---

## Proposed title
**Audited anatomy, conditional modeling, and open measurements for the *Drosophila* PSI→MN5 escape synapse**

*(Subtitle framing alternative: a provenance-separated evidence map for the Giant Fiber→MN5 pathway. The final title will be chosen by the user; this is a recommendation only.)*

---

## Research questions
1. What native measurements of the PSI→MN5 / MN5 system exist and are admissible?
2. What does the MaleCNS v1.0 connectome establish about PSI→MN5 anatomy?
3. What can a conditional, assumption-bounded model say — and what can it not say?
4. Which native quantities remain unmeasured, and what experiment would resolve each?

---

## Sections

### 1. Abstract
- **Purpose**: One paragraph: native evidence exists for anatomy and some MN5 biophysics; spatial transfer and Dα7 conductance are unmeasured (gates closed); a provenance-separated conditional model is reported as model-derived sensitivity only.
- **Claims**: C-102, C-103, C-301, C-303, C-401, C-501 (status summary only)
- **Required evidence**: Map status table.
- **Limitations to state**: Model is not validated biology; capacitance conflict unresolved.
- **Additional before drafting**: None.

### 2. Introduction
- **Purpose**: Establish the escape circuit context (GF→TTMn/PSI→MN5/DLMn), the value of provenance separation, and the specific gap question.
- **Claims**: C-101 (identity), the gate-status statements for Gate A (C-401) and Gate B (C-501)
- **Required evidence**: `CLAIM_EVIDENCE_MAP.md`; Berg et al. 2026; Ryglewski & Duch 2009.
- **Limitations**: Do not claim prior model validation of PSI→MN5 transfer.
- **Additional before drafting**: Confirm citation strings for Fayyazuddin+ 2006 and Augustin et al. 2019.

### 3. Methods overview (reproducibility)
- **Purpose**: Declare the five evidence classes and the gates; point readers to the frozen audit artifacts for exact provenance.
- **Claims**: C-401, C-501 (gate definitions)
- **Required evidence**: Methods/provenance documents; `CLAIM_EVIDENCE_MAP.md` evidence-class table; `final_anatomy_audit.md`.
- **Limitations**: Software-validation note C-602 must not imply biological validation.
- **Additional before drafting**: None.

### 4. Anatomy (connectome evidence)
- **Purpose**: Report what the MaleCNS v1.0 dataset establishes, with all thresholds quoted.
- **Claims**: C-101 (identity), C-102 (contact count), C-103 (`compartment_post` label), C-201 (no contact→soma path), C-202 (soma-proxy assumption), C-203 (SWC kind undefined), C-204 (mesh topology)
- **Required evidence**: `final_anatomy_audit.md`; `malecns_compartment_post_psi_mn5.csv`; MaleCNS v1.0 release.
- **Limitations**: Never present `compartment_post=`axon` as a voltage/distance; never promote the soma-proxy to a soma; quote `minconf 0.5`.
- **Figure/Table**: Figure 3 (contact mapping); Figure 4 (compartment annotations)
- **Additional before drafting**: None.

### 5. Native electrophysiology (measured constraints)
- **Purpose**: Report admissible native MN5 measurements and the documented conflict.
- **Claims**: C-301 (resting potential / threshold / AP), C-302 (input resistance), C-303 (capacitance conflict C-01, unresolved), C-304 (4.71 mV EPSP as comparison target only)
- **Required evidence**: `model_input_freeze.md` Section A; Fayyazuddin et al. 2006; Ryglewski & Duch 2009.
- **Limitations**: C-303 must state no winner is chosen and no averaging is performed; C-304 must state the EPSP is not a PSI-specific measurement and not model validation.
- **Figure/Table**: Table 5 (native biophysics table with provenance classes)
- **Additional before drafting**: None.

### 6. Conditional two-gate model (model-derived)
- **Purpose**: Describe the abstract cable bridge and the effective-conductance sweep strictly as model-derived sensitivity.
- **Claims**: C-402 (abstract bridge, model-derived), C-503 (Dα7 sweep, model-derived), C-601 (15,528-row structure)
- **Required evidence**: `mn5_psi_mn5_final_constraint_model.md` Sections 2/A.2/3/6/9; Augustin et al. 2019 (geometry precedent only).
- **Limitations**: Must report that per-contact anatomical somatic transfer is NOT claimed (C-201); must label every fitted gPSI and threshold-crossing as model-derived.
- **Figure/Table**: Figure 5 (two-gate model); Figure 6 (sensitivity)
- **Additional before drafting**: None.

### 7. Closed gates and what they block
- **Purpose**: Make the gate status unmistakable — these quantities are NOT in the native evidence.
- **Claims**: C-401 (Gate A closed), C-501 (Gate B closed)
- **Required evidence**: `missing_evidence.md` M-02 (spatial transfer, search exhausted); M-01/M-04 (conductance).
- **Limitations**: Prohibited wording strictly enforced — no "measured native PSI→MN5 transfer" or "native Dα7 conductance."
- **Additional before drafting**: None.

### 8. Validation status (software vs biological)
- **Purpose**: Separate software verification from biological validation.
- **Claims**: C-602 (pytest 1773 passed / 2 skipped)
- **Required evidence**: `validation/full_suite_report.md`; `AGENTS.md`.
- **Limitations**: Explicitly state software validation ≠ biological validation; cite C-402/C-503 as model-derived only.
- **Additional before drafting**: Confirm exact pytest counts from the current snapshot.

### 9. Reproducibility and data availability
- **Purpose**: State what is pinned versus what is not, and where inputs live.
- **Claims**: C-701 (no recorded expected checksum)
- **Required evidence**: `final_anatomy_audit.md`; `EXTERNAL_DATA_REPRODUCIBILITY.md`.
- **Limitations**: State the Feather checksum limitation; document the `minconf 0.5` retrieval scripts.
- **Additional before drafting**: None.

### 10. Discussion
- **Purpose**: Interpret the evidence strengths, the model's proper scope, and the gate implications.
- **Claims**: Synthesis of C-102/C-103 (anatomical strength), C-601/C-602 (model/software scope), C-401/C-501 (open gates)
- **Required evidence**: All claims in `CLAIM_EVIDENCE_MAP.md`; `missing_evidence.md` Tier 1.
- **Limitations**: Do not extrapolate model outputs to native behavior; do not "resolve" C-01, C-02, C-03.
- **Additional before drafting**: None.

### 11. Limitations
- **Purpose**: Enumerate the unresolved conflicts, assumptions, and gate closures explicitly.
- **Claims**: C-303 (C-01 capacitance conflict), C-401 (Gate A), C-501 (Gate B), C-701 (checksums)
- **Required evidence**: `model_input_freeze.md` conflict section; `missing_evidence.md`; `final_anatomy_audit.md` Block K.
- **Additional before drafting**: None.

### 12. Conclusions
- **Purpose**: Native anatomy and selected MN5 biophysics are established; spatial transfer and Dα7 conductance remain unmeasured; the model is a conditional, provenance-separated sensitivity analysis.
- **Claims**: Summary of C-102, C-301, C-401, C-501 statuses.
- **Additional before drafting**: None.

---

## Proposed figures / tables (linked to claims)
- **Figure 1** — Escape circuit diagram (context; C-101)
- **Figure 2** — MaleCNS anatomy pipeline / evidence layers (C-201–C-204)
- **Figure 3** — Contact mapping, 43 contacts with minconf 0.5 (C-102)
- **Figure 4** — `compartment_post` distribution and SWC kind counts (C-103, C-203)
- **Figure 5** — Two-gate conditional model diagram (C-402, C-503)
- **Figure 6** — Sensitivity summary, model-derived min/median/max (C-601)
- **Table 5** — Native MN5 biophysics with provenance classes (C-301–C-304)
- **Table (status)** — Claim evidence map status table (C-401, C-501 gates + C-303 conflict)

---

## Required citations (preliminary)
- Berg et al. 2026 — MaleCNS v1.0 release (anatomy claims)
- Ryglewski, Kilo & Duch 2014 — native MN5 measurements (C-301, C-302)
- Fayyazuddin et al. 2006 — Dα7, 4.71 mV EPSP (C-304, C-502)
- Augustin, Zylbertal & Partridge 2019 — GFS cable-model precedent (C-402)
- Lansdell, Collins, Goodchild & Millar 2012 — recombinant Dα7 channel-level data (C-501, C-503)

---

*Outline complete. Every section is grounded in `CLAIM_EVIDENCE_MAP.md` claim IDs. No section claims native spatial transfer or native Dα7 conductance; both remain explicitly NOT AUTHORIZED.*