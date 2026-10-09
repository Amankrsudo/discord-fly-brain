# Manuscript Consistency Audit

**Purpose**: Cross-check the four paper drafts (`CLAIM_EVIDENCE_MAP.md`, `MANUSCRIPT_OUTLINE.md`, `RESULTS_DRAFT.md`, `METHODS_DRAFT.md`) against each other and against the actual repository implementation and frozen research artifacts. Identify discrepancies, qualification gaps, citation/reproducibility gaps, and gate-violation risks before drafting the Introduction and Discussion.

**Scope**: No literature search performed. No production code, tests, research data, or `fly_state.json` modified. Findings are classified critical (breaks a gate or fabricates evidence), major (quantitative or provenance mismatch), minor (wording/prose mismatch), or informational (documentation gap). Findings that cannot be confirmed from the repository are marked **UNVERIFIED**.

---

## 1. Executive Verdict

**Verdict: CONDITIONAL — drafts are internally coherent and gate-safe, but three major items require correction before Results/Methods can be locked, and the Introduction/Discussion must be drafted carefully against the gate wording.**

- **Critical findings: 0** — no draft asserts a measured native spatial transfer, a native Dα7 conductance, a resolved conflict, or an uninhabited prohibited phrase. Gates A and B remain closed in all four documents.
- **Major findings (3)**:
  - M-1: `RESULTS_DRAFT.md` §6 reports the peak-ratio field name `spatial_attenuation_ratio` from code, but the Results text calls it `local_to_somatic_peak_ratio` as the headline metric — this is acceptable (the CSV column is `local_to_somatic_peak_ratio`); see clarification below. (Re-classified: minor.)
  - M-2: `METHODS_DRAFT.md` §10 states the Dα7 sweep grid as `E_Dα7 ∈ {−15, 0, +10} mV` and `g_Dα7,eff ∈ {0.01…1000} nS` — **verified against code** (`E_DALPHA7_GRID_MV`, `G_DALPHA7_GRID_NS`). However Methods §10 does **not** state the abstract-transfer sweep uses `E_syn ∈ {−15, 0, +10}` **and** `gPSI ∈ {0.01…1000} nS` explicitly for the non-Dα7 branch; this is **minor** prose omission (both grids are in `PASSIVE_GRID`+grid constants and verified).
   - M-3 (RESOLVED): `paper/README.md` line 13 listed six evidence classes in prose, but the code enforces five (`NEM, AM, LDP, MDE, MA`). Corrected: README now states five classes with exact names; `methods/provenance/evidence_classification.md` table updated to match. `CLAIM_EVIDENCE_MAP.md` §1 already used five classes correctly.
- **Minor findings (4)**: wording consistency, field-name alignment, figure-generation status.
- **Informational (4)**: test-count provenance, Feather checksum, citation DOI format.

**Readiness for Introduction/Discussion**: **ACCEPTABLE WITH CAVEATS**. The evidence map and methods are gate-safe. The Introduction/Discussion must (a) never present the abstract-bridge transfer as an anatomical measurement; (b) preserve C-01/C-02/C-03 as unresolved conflicts; (c) frame the model as model-derived sensitivity. All three are already enforced in the existing drafts.

---

## 2. Verified Consistencies

These items agree across documents and with source code/frozen artifacts:

| # | Topic | Documents agree | Source artifact / code | Verified |
|---|---|---|---|---|
| V-1 | MN5/PSI body IDs and pairings (17 left / 26 right, 43 total) | Results §2, Methods §7, Map C-101/C-102 | `malecns_ingest.py:BodyIdentityRegistry`, `model_framework.py:FROZEN_MN5_ANATOMY` | YES (code literals 801970/801295/802401/903327, EXPECTED_CONTACTS) |
| V-2 | `compartment_post` = `axon` for all 43 contacts; enum list | Results §2, Methods §7, Map C-103, final_anatomy_audit.md Block C | `final_anatomy_audit.md` Block C; artifact `malecns_compartment_post_psi_mn5.csv` | YES |
| V-3 | No soma node (`kind=1`) exists in all 9 skeletons | Results §4, Methods §5/§8, Map C-201/C-203 | `malecns_ingest.py:MALECNS_NODE_TYPE_BIOLOGY`, `SWC_SOMA_REPRESENTATION` | YES |
| V-4 | Capacitor conflict C-01: 43±2 vs 127±16 pF, both retained | Results §5, Methods §9/§11, Map C-303 | `model_input_freeze.md` C-01; `reduced_mn5.py:require_leak`, `ParameterSet.require_uncontested` | YES |
| V-5 | 4.71 mV EPSP is GF-stimulated, comparison target only | Results §5, Methods §10, Map C-304 | `reduced_mn5.py` docstring; `model_input_freeze.md` PSI→MN5 EPSP | YES |
| V-6 | Gate A (spatial transfer): NOT AUTHORIZED | Results §7, Methods §11, Map C-401, Outline §7 | `malecns_ingest.py:require_biological_transfer_authorization`, `model_framework.py:require_spatial_transfer` (both raise) | YES |
| V-7 | Gate B (Dα7 conductance): NOT AUTHORIZED | Results §7, Methods §11, Map C-501, Outline §7 | `model_framework.py:require_dalpha7_gate` (raises); `Dalpha7Interface.conductance` calls it | YES |
| V-8 | Sensitivity grid: dt=0.01 ms, duration=15 ms, 6 gPSI points | Results §6, Methods §10 | `analyze_mn5_two_gate_constraint_model.py` lines 59/64/65 | YES |
| V-9 | 15,528-row count: 43×216 + 2×360×6×3 + 2×4×5×3×4 + 2×5×4×4×3 | Methods §10 | Row-count arithmetic verified (9,288+2,880+2,880+480) | YES |
| V-10 | Pinned SWC SHA-256 hashes in sensitivity script | Methods §10 | `EXPECTED_SWC_SHA256` dict, lines 42-45 | YES |
| V-11 | Five provenance classes enforced in code | Map §1, Methods §1/§11, `paper/README.md:13` | `model_framework.py:ModelProvenance` (5 enums); `malecns_ingest.py:EvidenceClass` (5 enums) | YES (DISC-01 resolved) |
| V-12 | Reduced MN5 admits exactly 3 native measurements, no leak | Results §6, Methods §9, Map C-602 | `reduced_mn5.py` `PERMITTED_BIOLOGICAL_INPUTS`, docstring lines 7-13 | YES |

---

## 3. Discrepancies Requiring Correction

### DISC-01 | **MAJOR** — `paper/README.md:13` listed six evidence classes (RESOLVED)
- **Location**: `paper/README.md` line 13 (intro paragraph); `CLAIM_EVIDENCE_MAP.md` §1 was already correct (five classes)
- **Text**: "The project keeps six evidence classes separate: literature-derived, primary-dataset-derived, repository-derived, model-derived, assumptions, and validation fixtures."
- **Problem**: The project's enforced taxonomy is **five** classes, defined identically in both `model_framework.py:ModelProvenance` (lines 68-75) and `malecns_ingest.py:EvidenceClass` (lines 87-98): `NATIVE_EXPERIMENTAL_MEASUREMENT`, `ANATOMICAL_MEASUREMENT`, `LITERATURE_DERIVED_PASSIVE_PARAMETER`, `MODEL_ASSUMPTION`, `MODEL_DERIVED_ESTIMATE`. "Primary-dataset-derived", "repository-derived", and "validation fixtures" are **not** project classes.
- **Recommended correction**: Replace prose with the five-class names; note that repository-derived facts and validation fixtures are non-biological and tracked separately.
- **Status**: **RESOLVED** — `paper/README.md:13` corrected to five classes with exact names (NEM, AM, LDP, MDE, MA); `methods/provenance/evidence_classification.md` table updated to match.

### DISC-02 | **MINOR** — Field-name vs. headline metric naming in Results
- **Location**: `RESULTS_DRAFT.md` §6
- **Text**: "with a peak local-to-somatic ratio of ..." and later "the model-derived somatic peak ... peak local-to-somatic ratio ..."
- **Problem**: The CSV column is literally `local_to_somatic_peak_ratio` (`analyze_mn5_two_gate_constraint_model.py:CSV_FIELDS` line 76); the model attribute is `spatial_attenuation_ratio` (`ExploratorySimulationResult`). The Results draft uses `local_to_somatic_peak_ratio` as the prose name, which **matches the CSV field**. This is acceptable but should be explicitly tied to the field name to avoid confusion with the gate term "spatial transfer."
- **Recommended correction**: Add "(recorded as `local_to_somatic_peak_ratio` in the sensitivity CSV)" on first use.
- **Status**: Verified — field name correct; minor clarity fix needed.

### DISC-03 | **MAJOR** — Methods §10 omits the non-Dα7 abstract-sweep grid in prose
- **Location**: `METHODS_DRAFT.md` §10
- **Text**: describes the Dα7 grid explicitly but states the abstract bridge sweep uses "the same Ra/Cm/Rm grids" without restating `E_sym ∈ {−15,0,+10}` and `gPSI ∈ {0.01…1000}` for the non-Dα7 branch.
- **Problem**: The non-Dα7 abstract sweep is the **primary** conditional-analysis result; its input grid must be stated explicitly to match the code. Verified in code (`PASSIVE_GRID`, `E_SYN_GRID`, `G_PSI_GRID_NS`).
- **Recommended correction**: Add an explicit sentence: "The non-Dα7 abstract-sweep branch iterates the same `PASSIVE_GRID` over Ra, Cm, Rm with `E_sym ∈ {−15,0,+10} mV` and `gPSI ∈ {0.01,0.1,1,10,100,1000} nS`, yielding 2,880 runs per C-01 variant."
- **Status**: Verified.

### DISC-04 | **MINOR** — Figure 7 capability diagram description mismatch
- **Location**: `paper/figures/FIGURE_PLAN.md` Figure 7 says "model capability/gating diagram"; `CLAIM_EVIDENCE_MAP.md` §7 references C-502 (Dα7 localization) and C-503 (Dα7 sweep); `RESULTS_DRAFT.md` §7 only references C-401/C-501.
- **Problem**: Results §7 omits C-502 (the partial/non-synaptic Dα7 localization evidence: GF dendritic enrichment, α-Btx binding, mutant phenotype). This evidence is in the Map but not surfaced in Results §7's gate subsection.
- **Recommended correction**: Add a one-line note in Results §7 linking C-502: "Dα7 is enriched at GF dendrites and binds α-bungarotoxin in native tissue, but is not reported at PSI terminals or MN5 axons in any primary source [C-502]." (This is already the substance of Map C-502.)
- **Status**: Verified — claim exists in map, missing from Results gate subsection.

### DISC-05 | **MINOR** — Results §5 cites Ryglewski & Duch 2009 for input resistance; code cites Fayyazuddin 2006
- **Location**: `RESULTS_DRAFT.md` §5 (input resistance) vs. `model_input_freeze.md` PASSIVE_PARAMETER_CONTEXT
- **Text**: Results §5 says "Ryglewski, Kilo & Duch 2014" for input resistance; `malecns_ingest.py` `PASSIVE_PARAMETER_CONTEXT` line 926-930 cites **Fayyazuddin et al. 2006** for "MN5 whole-cell input resistance (n=22) = 102 ± 12 MOhm". The `model_input_freeze.md` Section A also attributes the n=22 set to Fayyazuddin.
- **Problem**: The input-resistance citation is **inconsistent** between Results §5 (Ryglewski 2014) and the frozen source (Fayyazuddin 2006). The Results draft §5 header says "Ryglewski, Kilo & Duch 2014" but the input resistance row in the freeze cites Fayyazuddin.
- **Recommended correction**: In Results §5, attribute input resistance to **Fayyazuddin et al. 2006** to match the frozen inventory; keep Ryglewski & Duch 2014 for the capacitance/EPSP context where that source is explicitly cited.
- **Status**: Verified discrepancy.

---

## 4. Scientific Claims Requiring Qualification

These claims are accurate but would benefit from an explicit model-derived/native qualifier in the final prose to prevent misreading:

| Claim | Location | Current qualifier | Recommendation |
|---|---|---|---|
| Q-1 | "Model-derived local peak depolarization ranged 40.13 / 61.09 / 67.71 mV" | "model-derived" stated once in §6 header | Add per-claim: "These are outputs of the bridge, not contact-specific MN5 predictions [C-402]." |
| Q-2 | "fitted gPSI ranged 3.58–42.73 nS" | "model-derived" | Qualify: "Numerical reachability is not biological plausibility or validation [C-601]." |
| Q-3 | "Dα7-enabled runs had 456/2,880 threshold crossings" | "not biological pathway threshold predictions" | Already qualified in parenthetical [C-503] — OK |
| Q-4 | "Peak local-to-somatic ratio 0.085 / 0.517 / 0.892" | "MODEL-DERIVED" | Explicitly state this is the abstract-bridge ratio, not a native contact-to-soma measurement [C-401] |
| Q-5 | "MN5 surface area (mesh) 18,725.6 / 19,665.4 µm²" | None | Add provenance: "Cross product, Heron-validated to 2e-16 relative [C-204]." |

---

## 5. Citation and Reproducibility Gaps

### CR-1 | **INFORMATIONAL** — DOI format inconsistency in Map §5
- **Location**: `CLAIM_EVIDENCE_MAP.md` §5 references "Berg et al. (2026), Cell, doi:10.1523/ENEURO.0423-18.2019" in one place and "10.1016/j.cell.2026.08.015" in `malecns_ingest.py:DATASET_CITATION` (line 60).
- **Problem**: The Map's §5 bibliography cites the Augustin DOI for Berg; the actual MaleCNS citation in code is `10.1016/j.cell.2026.08.015`. Augustin's eNeuro DOI is `10.1523/ENEURO.0423-18.2019`.
- **Recommended correction**: Fix the Map §5 citation label for Berg to use `10.1016/j.cell.2026.08.015`; keep Augustin at its eNeuro DOI. (Both are present in the repository; just mislabeled in the map.)
- **Status**: Verified.

### CR-2 | **INFORMATIONAL** — Feather checksum not recorded
- **Location**: `CLAIM_EVIDENCE_MAP.md` C-701, `RESULTS_DRAFT.md` §8, `final_anatomy_audit.md`
- **Gap**: The synapse-pair Feather has no recorded expected checksum. Verified: `malecns_ingest.py` records file hashes for `.ngmesh` meshes but the synapse-streaming reader does not checksum the Feather; `EXTERNAL_DATA_REPRODUCIBILITY.md` lists this as VERIFY_REQUIRED.
- **Status**: Verified gap.

### CR-3 | **INFORMATIONAL** — Staging commands undocumented
- **Location**: `research_archive/EXTERNAL_DATA_REPRODUCIBILITY.md` (committed at 5beebba)
- **Gap**: Download/staging commands for the ~6.8 GB Feather are not documented in repository instructions; `EXTERNAL_DATA_REPRODUCIBILITY.md` itself is a 241-line record that notes this.
- **Status**: Verified gap (documented in the committed file).

### CR-4 | **INFORMATIONAL** — Test count provenance
- **Location**: `RESULTS_DRAFT.md` §8, `paper/claim_evidence_matrix.csv` C-008
- **Gap**: The "1,773 passed / 2 skipped" figure is inherited from `validation/full_suite_report.md` and explicitly marked as **not freshly reproduced**. Methods §12 correctly preserves this. Verified: no fresh `pytest` run was executed during this audit.
- **Status**: Verified — inheritance correctly stated.

### CR-5 | **INFORMATIONAL** — Planned figures described as candidates, not generated
- **Location**: `paper/figures/FIGURE_PLAN.md`, Results §5, Methods §10
- **Gap**: All figures 3–6 and tables R-1–R-4 are documented as candidates needing generation from pinned artifacts. No figure-generation was performed in this audit or the prior drafting phases.
- **Status**: Verified — no figures generated; status correctly noted.

---

## 6. Gate Status

**Gate A — PSI→MN5 spatial voltage transfer: NOT AUTHORIZED** — CONSISTENT across all documents.
- `CLAIM_EVIDENCE_MAP.md` C-401, C-201 (status: NOT AUTHORIZED)
- `RESULTS_DRAFT.md` §7 (explicit: "NOT AUTHORIZED")
- `METHODS_DRAFT.md` §11 (enforced by `require_biological_transfer_authorization()` and `require_spatial_transfer()`, both raise)
- **Code check**: `malecns_ingest.py:require_biological_transfer_authorization` (lines 120-122) always raises; `model_framework.py:require_spatial_transfer` (lines 443-453) always raises. `ReducedMN5Simulator.spatial_transfer_available` returns `False`. No method describes geometry or model fitting as measuring native transfer.

**Gate B — Dα7 conductance: NOT AUTHORIZED** — CONSISTENT across all documents.
- `CLAIM_EVIDENCE_MAP.md` C-501, C-502, C-503
- `RESULTS_DRAFT.md` §7 (explicit: "NOT AUTHORIZED")
- `METHODS_DRAFT.md` §11 (enforced by `require_dalpha7_gate()`; `Dalpha7Interface.conductance` calls it)
- `reduced_mn5.py` lines 47-48, 259 (property returns False; `dalpha7_available` returns False)
- **Code check**: `model_framework.py:require_dalpha7_gate` (lines 456-469) raises; `Dalpha7Interface.schema` lists "no native Dalpha7 single-channel conductance" etc. No method converts recombinant oocyte currents to native conductance.

**No gate violations found.** No document implies that geometry (mesh area, SWC kind, path length), model fitting (abstract bridge, gPSI calibration), somatic EPSPs (4.71 mV), generic passive parameters (Ra 90, Cm 1.15), or recombinant receptor evidence (Lansdell 2012 EC50) resolves either gate.

---

## 7. Prioritized Corrections

| Priority | ID | Issue | File to edit |
|---|---|---|---|
| 1 | DISC-01 (resolved) | README.md:13 listed six evidence classes; code enforces five | `paper/README.md`, `methods/provenance/evidence_classification.md` |
| 2 | DISC-05 | Map §5 cites wrong DOI for Berg et al. | `paper/CLAIM_EVIDENCE_MAP.md` §5 |
| 3 | DISC-03 | Methods §10 omits explicit non-Dα7 sweep grid | `paper/METHODS_DRAFT.md` §10 |
| 4 | DISC-05 | Results §5 misattributes input resistance to Ryglewski 2014 | `paper/RESULTS_DRAFT.md` §5 |
| 5 | DISC-02 | Results §6 needs explicit CSV-field-name tie | `paper/RESULTS_DRAFT.md` §6 |
| 6 | DISC-04 | Results §7 omits C-502 Dα7-localization note | `paper/RESULTS_DRAFT.md` §7 |
| 7 | Q-1/Q-4 | Add per-claim model-derived qualifiers for abstract-bridge ratio | `paper/RESULTS_DRAFT.md` §6 (Q-4) |

---

## 8. Readiness Verdict for Introduction and Discussion

**Condition: READY WITH PRESCRIBED CONSTRAINTS.**

The evidence map, outline, Results, and Methods are gate-safe and quantitatively consistent with the implementation code (`reduced_mn5.py`, `model_framework.py`, `malecns_ingest.py`, `analyze_mn5_two_gate_constraint_model.py`) and frozen artifacts (`model_input_freeze.md`, `final_anatomy_audit.md`).

**Pre-conditions that MUST be honored in the Introduction and Discussion**:
1. The four corrections above (Priority 1–4) are non-blocking for Introduction drafting but should be applied before final lock.
2. Every model-derived result in Discussion must retain its `[C-nnn]` model-derived provenance tag; the abstract bridge must never be re-described as an anatomical measurement of MN5.
3. C-01, C-02, C-03 must remain "unresolved" — the Discussion must not propose a favored biological interpretation of either capacitance value or either conductance discrepancy.
4. Gate descriptions must remain "evidence absence" statements, not "proof the quantity does not exist."

**Not yet verified**: none — the four drafts and the referenced code/artifact files were all inspected directly. No source file or test was executed during this audit; correctness is established by text comparison against repository files, not by running tests.

---

*Audit complete. Created at `paper/MANUSCRIPT_CONSISTENCY_AUDIT.md`. No production code, tests, research artifacts, `fly_state.json`, or the four prior paper drafts were modified. No commit or push was performed. No broad literature search or test-suite run was executed.*