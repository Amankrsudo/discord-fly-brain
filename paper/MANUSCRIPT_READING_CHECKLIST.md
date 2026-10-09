# Manuscript Reading Checklist

**Purpose**: A structured, session-by-session reading companion for the Fly Brain 3.0 manuscript package. Work through each session in order; check off items as you confirm understanding.

**Ground rules**:
- All findings are drawn from the manuscript drafts and repository artifacts in `paper/` and `research/`.
- Do NOT treat model-derived outputs as native measurements.
- Do NOT treat the test count (1,773 passed / 2 skipped) as freshly reproduced.
- Do NOT invent results or fill gaps with external knowledge.

---

## Session 1: Big-Picture Understanding

**Files to read**:
- `paper/README.md` (complete)
- `paper/MANUSCRIPT_OUTLINE.md` §1–3 (title, research questions, gate status)
- `paper/CLAIM_EVIDENCE_MAP.md` lines 1–15 (purpose, evidence classes, gate status)

**Key questions to answer**:
1. What biological circuit is being studied, and what specific synapse is the focus?
2. What are the four research questions the manuscript addresses?
3. What do "Gate A" and "Gate B" actually concern, and what is their status?

**Important facts to remember**:
- MN5 = body IDs 801970 (left) / 801295 (right); PSI = 802401 (left) / 903327 (right)
- The manuscript reports what is KNOWN, what is NOT known, and what a conditional model CAN say
- Gates are **evidence constraints on interpretation** — NOT assertions that quantities don't exist

**Completion checkbox**: ☐

---

## Session 2: Introduction and Research Questions

**Files to read**:
- `paper/INTRODUCTION_DRAFT.md` (complete, 62 lines)
- `paper/CLAIM_EVIDENCE_MAP.md` C-101 (lines 20-28)

**Key questions to answer**:
1. How does the introduction establish biological motivation for PSI→MN5?
2. What are the four sequential "gaps" the manuscript identifies?
3. What does the introduction explicitly NOT claim?

**Important facts to remember**:
- The GFS escape pathway: OL → GF → TTMn (jump) / PSI → MN5 → DLM (flight)
- MN5 innervates DLM fibers 5 and 6 contralateral to its soma — a textual assignment from Ryglewski & Duch 2009
- Gap (2) (contact-to-soma geometry) cannot be closed because no soma node exists in the SWCs
- Gap (3) (native biophysics) has a capacitance discrepancy (C-01)

**Completion checkbox**: ☐

---

## Session 3: Methods and Code Architecture

**Files to read**:
- `paper/METHODS_DRAFT.md` §1–3 (study design, data sources, mesh parsing)
- `biological_brain/malecns_ingest.py` lines 1-50, 87-98 (module docstring, EvidenceClass enum)
- `paper/CLAIM_EVIDENCE_MAP.md` C-101–C-204 (anatomy/identity claims)

**Key questions to answer**:
1. What are the five evidence classes and where are they enforced in code?
2. How does the mesh parser validate file integrity?
3. What coordinate frames are maintained and how are they converted?
4. What does `kind=1` mean and how many exist in the skeletons?

**Important facts to remember**:
- Five classes: `NEM`, `AM`, `LDP`, `MDE`, `MA` (NOT six — see DISC-01 discrepancy in README)
- Mesh parser: offset 0 = uint32 vertex count; offset 4 = N×float32 XYZ; then 3F×uint32 triangle indices
- Conversion: `swc_voxel × 8 = mesh_nm` (`MESH_TO_SWC_SCALE = 8.0`)
- Zero `kind=1` (soma) nodes in all 9 skeletons
- `somaLocation` is a point, not a surface; `tosomaLocation` and `rootSide` are unpopulated

**Completion checkbox**: ☐

---

## Session 4: Methods Continued — Contacts, Paths, and Models

**Files to read**:
- `paper/METHODS_DRAFT.md` §4–7 (coordinates, SWC, geometry, contacts)
- `paper/METHODS_DRAFT.md` §8–10 (paths, reduced model, sensitivity analysis)
- `paper/CLAIM_EVIDENCE_MAP.md` C-201–C-402

**Key questions to answer**:
1. What is the difference between `compartment_post` (dataset annotation) and SWC `kind` (format code)?
2. Why can geometric path length NOT be used as electrotonic distance?
3. What are the inputs to the reduced MN5 model, and what is blocked?
4. What parameter grids define the sensitivity analysis?

**Important facts to remember**:
- `compartment_post` comes from neuroglancer_annotations_v1 layer; `kind` comes from SWC format
- The 43 contacts are projected to 43 unique SWC nodes, all `kind=0`
- Reduced model admits exactly 3 native inputs (resting potential, threshold, AP amplitude) — NO leak, NO Cm
- Bridge geometry: `GFS_BRIDGE_LENGTH_UM = 112.5`, `GFS_BRIDGE_DIAMETER_UM = 2.0` (from Augustin 2019)
- Parameter grids: Ra ∈ {30,35.4,90,200,400} Ω·cm, Cm ∈ {0.6,1.0,1.15,2.6} µF/cm², Rm ∈ {6,10,20,26} kΩ·cm², E_syn ∈ {-15,0,+10} mV, gPSI ∈ {0.01...1000} nS

**Completion checkbox**: ☐

---

## Session 5: Native Electrophysiology Results

**Files to read**:
- `paper/RESULTS_DRAFT.md` §1, §2, §5 (data provenance, contacts, electrophysiology)
- `paper/tables/FIGURE_TABLE_R2_native_biophysics.md`
- `paper/CLAIM_EVIDENCE_MAP.md` C-102, C-301, C-302, C-303, C-304

**Key questions to answer**:
1. What are the strongest native MN5 measurements, and their evidence class?
2. Why is the 4.71 mV EPSP a comparison target, not a PSI measurement?
3. How is the capacitance conflict (C-01) handled?

**Important facts to remember**:
- Resting potential: −67.8 ± 5.5 mV (n=13), threshold: −24.1 ± 8.2 mV (n=11), AP amplitude: +45.5 ± 8.6 mV (n=13) [NEM]
- Input resistance: 102 ± 12 MΩ (n=22, Fayyazuddin 2006) AND 97 ± 31 MΩ (n=52, Ryglewski & Duch 2014) — both retained [NEM]
- Capacitance: 43 ± 2 pF vs 127 ± 16 pF — both retained, no winner, no averaging [NEM, contested]
- 4.71 mV EPSP: recorded under GF stimulation, not direct PSI stimulation

**Completion checkbox**: ☐

---

## Session 6: Model-Derived Results and Sensitivity

**Files to read**:
- `paper/RESULTS_DRAFT.md` §6 (conditional model analysis)
- `paper/figures/FIGURE_6_sensitivity.svg`
- `paper/figures/FIGURE_5_two_gate_model.svg`
- `paper/CLAIM_EVIDENCE_MAP.md` C-402, C-503, C-601

**Key questions to answer**:
1. What is the 15,528-row decomposition, and what does each component test?
2. What are the nominal-point somatic peak values for C-01 variants A and B?
3. Why is fitted gPSI NOT a measured conductance?
4. What does the Dα7 sweep actually vary?

**Important facts to remember**:
- 15,528 = 9,288 (contact-local) + 2,880 (abstract) + 2,880 (Dα7) + 480 (calibration)
- Nominal bridge point: A (43 pF) = 1.108 mV; B (127 pF) = 0.510 mV
- Local-to-somatic ratio: 0.085 / 0.517 / 0.892 (min/median/max)
- Fitted gPSI: 3.58–42.73 nS — numerical reachability, NOT biological plausibility
- Dα7 sweep: 0.01–1000 nS, E_Dα7 ∈ {-15, 0, +10} mV — model assumption, not native measurement

**Completion checkbox**: ☐

---

## Session 7: Closed Gates and Evidence Gaps

**Files to read**:
- `paper/RESULTS_DRAFT.md` §7 (gates and evidence gaps)
- `paper/CLAIM_EVIDENCE_MAP.md` C-401, C-501, C-502

**Key questions to answer**:
1. What distinguishes "evidence absence" from "quantity does not exist"?
2. What resolving experiment does the manuscript propose for Gate A?
3. Why is recombinant Dα7 data insufficient for Gate B?

**Important facts to remember**:
- Gate A resolves experiment: dual-site recording (somatic + focal contact patch) during direct PSI stimulation
- Gate B resolves experiment: same + pharmacological series + Dα7 manipulation
- Dα7 is enriched at GF dendrites but NOT REPORTED at PSI terminals or MN5 axons
- Drosophila lacks Kir7.1/KCNJ13 — the vertebrate α7→Kir coupling cannot be modeled

**Completion checkbox**: ☐

---

## Session 8: Reproducibility and Validation

**Files to read**:
- `paper/RESULTS_DRAFT.md` §8 (reproducibility)
- `paper/tables/FIGURE_TABLE_R4_reproducibility.md`
- `paper/MANUSCRIPT_CONSISTENCY_AUDIT.md` §5, §6 (reproducibility gaps)
- `research_archive/EXTERNAL_DATA_REPRODUCIBILITY.md` §4 (limitations)

**Key questions to answer**:
1. What is the difference between software validation and biological validation?
2. What is recorded as VERIFY_REQUIRED for the Feather file?
3. What test count is reported and how is its provenance stated?

**Important facts to remember**:
- 1,773 passed / 2 skipped — INHERITED, not freshly reproduced [C-602]
- Feather SHA-256: VERIFIED (959d8ef4… computed 2026-10-09)
- Staging command: NOT DOCUMENTED — no repository download procedure exists
- Test command: `python -m pytest tests/ -v --tb=short --ignore=tests/test_diagnostics.py`

**Completion checkbox**: ☐

---

## Session 9: Discussion and Limitations

**Files to read**:
- `paper/DISCUSSION_DRAFT.md` (complete, 125 lines)
- `paper/CLAIM_EVIDENCE_MAP.md` C-701

**Key questions to answer**:
1. What are the strongest supported contributions vs. model-derived outputs?
2. Why are C-01, C-02, C-03 not resolved in the discussion?
3. What is the "minimum-honest model" principle?

**Important facts to remember**:
- C-02: GF gap-junction 135 µS (paper) vs 135 nS (executed) — 1000×
- C-03: PSI→DLMn chemical 80 µS (paper) vs 0.08 µS (executed) — 1000× (different synapse from C-02)
- Minimum-honest model: only 3 safe native inputs, no leak, no assumed conductance, no Cm
- 3 contacts are AMBIGUOUS (margin ratios 1.110–1.172)

**Completion checkbox**: ☐

---

## Session 10: Figures, Tables, and Manuscript Integration

**Files to read**:
- `paper/FIGURE_TABLE_MANIFEST.md` (complete)
- All 8 SVG figures and 4 tables
- `paper/figures/FIGURE_PLAN.md`

**Key questions to answer**:
1. Which figures are fully generated vs. stubs?
2. What claim IDs does each figure/table support?
3. What must NOT be inferred from each visual?

**Important facts to remember**:
- Figures 3, 4, 6: fully generated
- Figures 1, 2, 5: hand-authored schematics (generated)
- Figures 7, 8: STUBS (minimal SVG, pending hand-authoring)
- Figure 6 shows C-01 variants A/B separately, both shown, no winner chosen
- All model-derived figures must display "MODEL-DERIVED" labeling

**Completion checkbox**: ☐

---

## Session 11: Reviewer Questions and Self-Test

**Files to read**:
- `paper/MANUSCRIPT_READING_GUIDE.md` §11 (reviewer questions)
- `paper/MANUSCRIPT_READING_GUIDE.md` §13 (self-test)

**Key questions to answer**:
1. Can you answer all 30 reviewer questions from memory?
2. Did you pass all 35 self-test questions?

**Important facts to remember**:
- The guide's answer key preserves all caveats and uncertainties
- No answer should be stronger than the evidence warrants
- "NOT AUTHORIZED" means "absent from evidence" — not "does not exist"

**Completion checkbox**: ☐

---

## Session 12: Final Scientific Self-Review

Before considering submission, verify:

1. **Gate integrity**: Every mention of spatial voltage transfer says "NOT AUTHORIZED" or "absent" [C-401] ☐
2. **Gate integrity**: Every mention of Dα7 conductance says "NOT AUTHORIZED" or "absent" [C-501] ☐
3. **Conflict preservation**: C-01, C-02, C-03 are "unresolved" — no winner chosen [C-303] ☐
4. **Evidence-class discipline**: Model outputs are tagged MDE/MA; native measurements tagged NEM [C-301] ☐
5. **Test-count honesty**: 1,773/2 is "inherited," not "freshly reproduced" [C-602] ☐
6. **No geometry→electricity**: Mesh area is never converted to conductance without assumed Cm [C-401] ☐
7. **No distance→attenuation**: Path length is geometric, never electrotonic [C-201] ☐
8. **Provenance chain**: Every claim ID traces to an exact source artifact [C-101–C-701] ☐
9. **Abstract bridge framing**: Bridge is model-authorized conditional analysis, NOT native measurement [C-402] ☐
10. **Citation accuracy**: Berg DOI = 10.1016/j.cell.2026.08.015 (not Augustin's DOI) ☐

**All items checked**: ☐ Yes — ready for submission consideration

**Issues discovered during self-review**:
(Leave space for notes)

---
*Checklist created at `paper/MANUSCRIPT_READING_CHECKLIST.md`. Based on direct inspection of manuscript files and repository artifacts.*
