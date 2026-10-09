# Fly Brain 3.0 Manuscript Reading Guide

**Purpose**: A beginner-friendly but scientifically accurate companion to the Fly Brain 3.0 manuscript package. This guide explains what each section does, how every result was obtained, and how to understand and defend the scientific claims.

**Scope**: This is a reading aid, not a replacement for the manuscript. It is based on direct inspection of the actual manuscript files in `paper/` and their source artifacts in `research/`. Where the manuscript documents a gap or limitation, this guide preserves it rather than filling it.

**Abstract status**: **No finalized abstract exists**. The MANUSCRIPT_OUTLINE.md §1 describes a proposed abstract content (one paragraph covering native evidence, closed gates, conditional model). A draft abstract is synthesized in Section 1.3 below — clearly labeled as a proposed summary, not a manuscript file.

---

## 1. The Entire Paper in Plain English

### 1.1 What Fly Brain 3.0 investigates

Fly Brain 3.0 investigates a single, specific question: **when the Giant Fiber neuron (GF) releases onto the motor neuron MN5 via the intermediate interneuron PSI, how much of the postsynaptic signal reaches MN5's soma, and what is the role of the Dα7 nicotinic acetylcholine receptor at that synapse?**

This is a synaptic transmission question in the *Drosophila* escape circuit. The project does not try to build the most biophysically detailed model it can. Instead, it asks: **what do we actually know, what do we actually not know, and what could a transparent, assumption-bounded model say under declared limitations?**

### 1.2 What biological system is being studied

The study focuses on the **Giant Fiber System (GFS)**, a well-characterized escape circuit in the fruit fly *Drosophila melanogaster*.

- **Giant Fiber (GF)**: A large bilaterally paired interneuron in the CNS that receives visual threat input from the optic lobes (LC4 and LPLC2 interneurons). When activated by a looming object, GF triggers the fly's escape jump-and-flight response.
- **TTMn (Tubby Tail Muscle neuron)**: The jump motor neuron. GF connects to TTMn via an electrical (gap junction) synapse.
- **PSI (Protocerebral Surgical Interneuron)**: An intermediate interneuron. GF also connects to PSI via an electrical (gap junction) synapse.
- **MN5 (Motor neuron 5)**: The wing-downstroke motor neuron. PSI connects to MN5 chemically.
- **DLM (Dorsal Longitudinal Muscle)**: MN5 innervates DLM fibers 5 and 6, which produce the wing downstroke that initiates flight.

The specific synapse under investigation is **PSI → MN5**. Body IDs: PSI = 802401 (left) / 903327 (right); MN5 = 801970 (left) / 801295 (right). These are identified from the **MaleCNS v1.0 connectome**, a complete electron-microscopy reconstruction of the adult male *Drosophila* CNS published by Berg et al. 2026 (Cell, DOI: 10.1016/j.cell.2026.08.015) [C-101].

### 1.3 What the project accomplished

| Accomplishment | Evidence class | What it establishes |
|---|---|---|
| Audited contact inventory | AM (anatomical measurement) | 43 PSI→MN5 contacts at minconf 0.5 (17 left, 26 right) [C-102] |
| Verified contact locations | AM | All 43 `compartment_post = axon` [C-103] |
| Collected native MN5 electrophysiology | NEM | Resting potential, threshold, AP amplitude, input resistance [C-301, C-302] |
| Preserved capacitance conflict | NEM (contested) | 43±2 vs 127±16 pF, both retained unresolved [C-303] |
| Built a conditional two-gate model | MDE/MA | 15,528-row sensitivity analysis under declared assumptions [C-601, C-602] |
| Enforced provenance gates | Framework | PSI→MN5 spatial transfer and Dα7 conductance are NOT AUTHORIZED [C-401, C-501] |

### 1.4 What the project did NOT accomplish

- **No native measurement of PSI→MN5 spatial voltage transfer** — Gate A is closed [C-401]
- **No native Dα7 conductance at PSI→MN5** — Gate B is closed [C-501]
- **No resolution of the MN5 capacitance conflict** (C-01: 43 vs 127 pF) [C-303]
- **No resolution of the 1000× unit discrepancies** (C-02: µS vs nS gap junction; C-03: µS vs µS chemical conductance)
- **No biological validation of the model** — software tests pass (1,773 passed, 2 skipped) but this is software validation, not biological validation [C-602]

### 1.5 Why this work matters

The manuscript demonstrates a **provenance-aware methodology** for connectomic modeling: rather than silently adopting default parameters, it explicitly classifies every quantity (native measurement, literature-derived, anatomical, model-derived, assumption), refuses to compute quantities that cannot be established, and tags every model output as conditional. This prevents model-derived sensitivity from being misread as biological fact.

---

## 2. Explain the Manuscript Section by Section

The manuscript outline (in `paper/MANUSCRIPT_OUTLINE.md`) specifies 12 sections. Below is a section-by-section reading guide with the actual content found in the drafts.

### Section 1: Abstract

- **Purpose**: One-paragraph summary of native evidence, closed gates, and the conditional model.
- **Central argument**: The paper reports what is known (anatomy + some biophysics), what is not known (spatial transfer, Dα7 conductance), and what a conditional model can say.
- **Plain-English explanation**: The abstract establishes upfront that the model is NOT a validated biological measurement — it is a provenance-controlled sensitivity analysis.
- **Key terminology**: Provenance, model-derived, native measurement, gate closure.
- **Evidence**: The outline states the abstract should reference C-102, C-103, C-301, C-303, C-401, C-501 as status summaries only.
- **Reviewer question**: Is the abstract honest about the model's limitations?
- **Before moving on**: Understand that "conditional" means the outputs depend on assumptions that cannot be validated from current data.
- **Status**: **No finalized abstract exists in a manuscript file**. The outline (§1) describes its content. A proposed synthesis is in Section 1.3 of this guide.

### Section 2: Introduction

- **Purpose**: Establish the biological context (GFS escape circuit), the value of provenance separation, and the specific gap question.
- **Central argument**: A complete biophysical account requires four sequential gaps: (1) wiring anatomy, (2) contact-to-soma geometry, (3) native biophysics, (4) conditional model synthesis. Only gaps 1 and a partial 3 can be closed from available data.
- **Plain-English explanation**: Explains why the escape circuit matters, identifies MN5 as the wing-downstroke motor neuron with body IDs 801970/801295, and frames the four research questions.
- **Key terminology**: Provenance-aware framework, evidence authorization gates, minimum confidence threshold, native vs. model-derived.
- **Evidence**: Claims C-101 (body identity), C-401/C-501 (gate status). Sources: Berg et al. 2026, Ryglewski & Duch 2009.
- **Reviewer question**: Does the introduction honestly frame the model as assumption-bounded rather than validated?
- **Before moving on**: Understand the four research questions (anatomy, morphology, native constraints, conditional modeling).

### Section 3: Methods Overview (Reproducibility)

- **Purpose**: Declare the five evidence classes and the gates; point to frozen audit artifacts.
- **Central argument**: Every reported quantity carries exactly one evidence class; blocked parameters raise exceptions.
- **Plain-English explanation**: Explains the framework's architecture-level decision to distinguish five evidence classes (NEM, AM, LDP, MDE, MA), each enforced in code. Repository-execution facts and validation fixtures are non-biological and tracked separately by the validation package.
- **Key terminology**: EvidenceClass enum, ParameterSet, BlockedParameterError, BiologicalTransferNotAuthorized.
- **Evidence**: Five-class taxonomy enforced in `model_framework.py:ModelProvenance` and `malecns_ingest.py:EvidenceClass` [C-301, C-302].
- **Reviewer question**: Are all five classes kept distinct and never collapsed? Yes — the code enforces five, not six; "repository-derived" and "validation fixtures" are non-biological and tracked separately.
- **Before moving on**: Methods draft §1 (line 11) and `paper/README.md` (line 13) both correctly state five classes.

### Section 4: Anatomy (Connectome Evidence)

- **Purpose**: Report what MaleCNS v1.0 establishes about PSI→MN5 anatomy, with all thresholds quoted.
- **Central argument**: 43 contacts at minconf 0.5 (17 left, 26 right), all `compartment_post = axon`, all PSI→MN5 contacts are on MN5's axonal compartment.
- **Plain-English explanation**: For each of the 43 synapses between PSI and MN5, the dataset records whether the contact is on an axon, dendrite, etc. All 43 are on the axon — meaning PSI releases onto MN5's axon, not its dendrites near the soma.
- **Key terminology**: minconf (minimum confidence threshold), compartment_post, compartment_pre, body ID, VFB identifier.
- **Evidence**: Claims C-101 (identity), C-102 (contact count), C-103 (compartment labels). Sources: `final_anatomy_audit.md`, `malecns_compartment_post_psi_mn5.csv`.
- **Reviewer question**: Does `compartment_post = axon` imply voltage transfer? No — it's a dataset annotation, not an electrophysiological measurement [C-103].
- **Before moving on**: Understand that anatomical labels do not establish electrical compartment identity [C-203].

### Section 5: Native Electrophysiology (Measured Constraints)

- **Purpose**: Report admissible native MN5 measurements and the documented conflict.
- **Central argument**: Strong native data exists for cell-state identity (resting potential, threshold, AP) and input resistance, but capacitance is conflicted (C-01) and no synaptic conductance is measured.
- **Plain-English explanation**: Lists what has actually been measured in living flies: MN5's resting voltage, spike threshold, action potential shape, and input resistance. Presents both capacitance measurements (43 pF and 127 pF) and explicitly states they conflict without choosing a winner.
- **Key terminology**: NEM (native experimental measurement), n (sample size), SD (standard deviation), input resistance, capacitance, EPSP (excitatory postsynaptic potential).
- **Evidence**: Claims C-301 (cell state), C-302 (input resistance), C-303 (capacitance conflict), C-304 (4.71 mV EPSP as comparison target only). Sources: Fayyazuddin et al. 2006, Ryglewski, Kilo & Duch 2014.
- **Reviewer question**: Why are there two capacitance values? Because they come from different experimental preparations/methods, and the repository preserves both without averaging [C-303].
- **Before moving on**: Understand that the 4.71 mV EPSP was measured under GF (giant fiber) stimulation, not direct PSI stimulation.

### Section 6: Conditional Two-Gate Model (Model-Derived)

- **Purpose**: Describe the abstract cable bridge and effective-conductance sweep as model-derived sensitivity only.
- **Central argument**: A conditional model produces output ranges (15,528 rows) that show what *could* happen under various assumptions, but these outputs are NOT native measurements.
- **Plain-English explanation**: The model simulates 43 contact sites using a simplified cable geometry derived from published GFS work (Augustin et al. 2019), plus an abstract bridge cable. It varies parameters like axial resistivity, capacitance, and conductance over ranges. Every output is tagged as model-derived.
- **Key terminology**: Abstract cable bridge, gPSI (synaptic conductance), E_syn (synaptic reversal potential), local-to-somatic ratio, threshold crossing, C-01 variant A/B.
- **Evidence**: Claims C-402 (abstract bridge), C-503 (Dα7 sweep), C-601 (15,528-row structure). Source: `analyze_mn5_two_gate_constraint_model.py`.
- **Reviewer question**: Are the fitted conductance values (3.58–42.73 nS) biological? No — they are numerical reachability results, not measured conductances [C-601].
- **Before moving on**: Understand that Figure 6 presents min/median/max ranges that are model-derived, not confidence intervals.

### Section 7: Evidence Gaps and the Two Closed Scientific Gates

- **Purpose**: Make the gate status unmistakable — these quantities are NOT in the native evidence.
- **Central argument**: Gate A (spatial voltage transfer) and Gate B (Dα7 conductance) remain closed because no qualifying primary evidence exists.
- **Plain-English explanation**: Two quantities are explicitly NOT claimed. The manuscript states: "these are evidence constraints on interpretation — the absence of qualifying primary evidence — not assertions that the underlying quantities do not exist."
- **Key terminology**: NOT AUTHORIZED, evidence absence, dual-site recording, resolving experiment.
- **Evidence**: Claims C-401 (Gate A), C-501 (Gate B), C-502 (Dα7 localization partial), C-503 (Dα7 sweep). Sources: `missing_evidence.md`, `da7_evidence.md`.
- **Reviewer question**: What experiment would open the gates? Dual-site recording for Gate A; native conductance measurement + Dα7 manipulation for Gate B [C-401, C-501].
- **Before moving on**: Understand the distinction between "absent from evidence" and "does not exist."

### Section 8: Reproducibility and Validation

- **Purpose**: State the software validation status and reproducibility limitations.
- **Central argument**: Tests verify code paths (1,773 passed, 2 skipped) but this is NOT biological validation. The Feather input has no recorded checksum.
- **Plain-English explanation**: The code works correctly against its own assertions, but that doesn't mean the biology it would compute is correct — because key biological inputs are unknown.
- **Key terminology**: Software validation vs. biological validation, inherited test count, checksum, reproducibility gap.
- **Evidence**: Claims C-602 (test status), C-701 (checksum limitation). Sources: `validation/full_suite_report.md`.
- **Reviewer question**: Was the test suite re-run during this manuscript draft? No — the count is inherited from a prior session [C-602].
- **Before moving on**: Understand that 1,773/2 is a software correctness result, not a biological validity result.

### Section 9: Reproducibility and Data Availability (Discussion section per outline)

- **Purpose**: State what is pinned (SWC hashes, 15,528-row CSV) versus what is not (Feather checksum, staging commands).
- **Central argument**: Some inputs are reproducibly pinned; the main external dataset lacks a verified checksum and staging documentation.
- **Plain-English explanation**: The sensitivity analysis uses pinned SWC files and a pinned CSV, but the raw 6.8 GB synapse table has no recorded checksum and no documented download command.
- **Key terminology**: Pinned, unpinned, SHA-256 checksum, snapshot.
- **Evidence**: Claim C-701. Source: `EXTERNAL_DATA_REPRODUCIBILITY.md`.
- **Before moving on**: Note that the Feather SHA-256 was computed during the 2026-10-09 verification pass (`959d8ef4…`) but the staging command remains undocumented.

### Section 10: Discussion

- **Purpose**: Interpret evidence strengths, model scope, and gate implications.
- **Central argument**: The anatomy is well-established; electrophysiology is partially constrained but conflicted; the model is a conditional sensitivity analysis.
- **Plain-English explanation**: Summarizes what can be claimed confidently (43 axonal contacts, native cell-state measurements) and what cannot (transfer, Dα7 conductance). Discusses the four unresolved conflicts.
- **Key terminology**: Conditional, assumption-bounded, model-derived, gate closure, conflict register.
- **Evidence**: Synthesis of C-102, C-103, C-201, C-301–C-304, C-401, C-501, C-601, C-701.
- **Reviewer question**: Does the discussion overstate any model output? It should not — every model output is labeled MDE.
- **Before moving on**: Understand that the discussion explicitly prohibits claiming "model was experimentally validated."

### Section 11: Limitations

- **Purpose**: Enumerate unresolved conflicts, assumptions, and gate closures.
- **Central argument**: Five categories of limitation: provenance/snapshots, interpretation, software validation, anatomical uncertainties, conflict register.
- **Plain-English explanation**: Explicitly lists what was NOT done — no native transfer measured, no Dα7 conductance, no C-01/C-02/C-03 resolution, no SIZ registration.
- **Key terminology**: VERIFY_REQUIRED, unpinned, ambiguous, AMBIGUOUS contacts.
- **Evidence**: C-01 (capacitance), C-02/C-03 (conductance discrepancies), C-201 (no soma path), C-203 (SWC kind undefined).
- **Before moving on**: Note that 3 contacts are AMBIGUOUS (margin ratios 1.110–1.172), preserved without threshold invention.

### Section 12: Conclusions

- **Purpose**: State the defensible summary.
- **Central argument**: Audited evidence map + conditional model, not validated biophysics.
- **Plain-English explanation**: "The anatomy is well-established; the native electrophysiology is partially constrained but capacitance-conflicted; the spatial voltage transfer and Dα7 conductance remain NOT AUTHORIZED."
- **Key terminology**: Evidence absence vs. non-existence.
- **Evidence**: Summary of C-101–C-701 statuses.
- **Before moving on**: The path forward is experimental (dual-site recording, Dα7 manipulation), not more model tuning.

---

## 3. Introduction: Understand the Motivation

### 3.1 Biological Context (from manuscript)

The GFS mediates the short-latency escape response. GF receives visual input from optic lobe interneurons (LC4, LPLC2), descends bilaterally, and makes two fast output pathways:

1. **GF → TTMn** (jump motor) via an **electrical (gap junction) synapse**
2. **GF → PSI → MN5/DLMn** (wing-downstroke) via an **electrical GF→PSI synapse** followed by a **chemical PSI→MN5 synapse**

MN5 innervates DLM fibers 5 and 6 contralateral to its soma. This is a **textual assignment from the source literature** (Ryglewski & Duch 2009, verbatim), not a project inference [C-101].

### 3.2 Role of GFS and MN5 (from manuscript)

The motivation for combining anatomy, contacts, electrophysiology, and computation is that **a complete biophysical account requires closing four sequential gaps**: (1) exact wiring, (2) geometry of contacts relative to soma, (3) native electrophysiological parameters, (4) conditional model synthesis. The manuscript argues that without closing gaps 2 and 3, any model is assumption-bounded rather than validated.

### 3.3 Research Questions (from manuscript)

1. What native measurements of PSI→MN5/MN5 exist and are admissible?
2. What does MaleCNS v1.0 establish about PSI→MN5 anatomy?
3. What can a conditional, assumption-bounded model say — and what can it not say?
4. Which native quantities remain unmeasured, and what experiment would resolve each?

### 3.4 Novelty Claims and Evidence

| Novelty claim | Evidence source | Status |
|---|---|---|
| Audited contact inventory (43 contacts, minconf 0.5) | MaleCNS v1.0 + final_anatomy_audit.md | Strong [C-102] |
| Provenance-aware framework (raises on blocked params) | model_framework.py, malecns_ingest.py | Strong [C-401, C-501] |
| Minimum-honest model (3 native inputs, no leak) | reduced_mn5.py | Strong [C-602] |
| Conditional two-gate sensitivity (15,528 rows) | analyze_mn5_two_gate_constraint_model.py | Model-derived [C-601] |

**Added for readability (not in manuscript)**: The novelty lies in the methodology of provenance separation, not in any new biological measurement. The manuscript consistently frames this as a methodological demonstration.

---

## 4. Methods: Understand Exactly What Was Done

### 4.1 MaleCNS Data Provenance

- **Input**: `syn-partners-male-cns-v1.0-minconf-0.5.feather` (~6.8 GB) from `gs://flyem-male-cns/v1.0/`
- **Code**: `malecns_ingest.py` (`MaleCNSSynapses.extract`)
- **What it does**: Streams the Feather file using pyarrow, selects synapses where `body_pre ∈ {802401, 903327}` and `body_post ∈ {801970, 801295}`, emits `SynapticContact` records
- **Output**: 43 contacts with raw coordinates (8 nm units), confidence values, `primary_post`
- **Assumptions**: minconf 0.5 applied by source and encoded in filename; never re-filtered
- **Can establish**: Contact count, pairing, body IDs
- **Cannot establish**: Voltage transfer, electrical distance, compartment identity
- **Source**: `malecns_ingest.py:SOURCE_MINCONF`, `MaleCNSSynapses.extract`, line 120

### 4.2 Mesh Parsing and Validation

- **Input**: `.ngmesh` files (binary format) for bodies 801970 and 801295
- **Code**: `malecns_ingest.py:parse_male_ngmesh`
- **What it does**: Parses the byte layout (offset 0: uint32 vertex count N; offset 4: N×float32 XYZ vertices; followed by 3F×uint32 triangle indices)
- **Output**: `MaleCNSMesh` object with vertices, faces
- **Validation**: Rejects files where `4 + 12·N + 12·F ≠ file_size`, where indices fall outside `[0, N−1]`, or where size is inconsistent
- **Assumptions**: Mesh coordinates are raw nanometres in EM space
- **Can establish**: Mesh vertex/face geometry
- **Cannot establish**: Biological compartment identity, electrical properties
- **Source**: `malecns_ingest.py` lines 37-47, `final_anatomy_audit.md` Block I

### 4.3 Coordinate Systems and Transformations

- **Input**: SWC files and .ngmesh files in EM space (8 nm voxel units)
- **Code**: `malecns_ingest.py:MESH_TO_SWC_SCALE = 8.0`, `validate_frame`
- **What it does**: Converts SWC voxel coordinates to mesh nanometres via `swc_voxel × 8 = mesh_nm`; validates that every post-synaptic coordinate falls inside the SWC bounding box
- **Output**: Validated coordinate frame alignment
- **Assumptions**: 8 nm voxel size; no per-mesh calibration
- **Can establish**: Frame consistency between SWC and mesh
- **Cannot establish**: Physical distances in biological units without calibration
- **Source**: `malecns_ingest.py` lines 75-79, 125-135

### 4.4 SWC Morphology Representation

- **Input**: `.swc` files for MN5 bodies 801970 and 801295
- **Code**: `malecns_ingest.py:SkeletonGeometry.from_swc`
- **What it does**: Parses 7-field SWC1 format (index, kind, x, y, z, radius, parent); preserves Type column literally
- **Output**: SWC node geometry with kind codes
- **Key finding**: `kind=0` ≈ 93%, `kind=2` ≈ 7%, `kind=1` = 0 across all 9 skeletons
- **Assumptions**: SWC Type codes have no documented biological assignment procedure
- **Can establish**: Geometric morphology, path distances
- **Cannot establish**: Biological compartment identity (axon/dendrite/soma) from `kind` codes
- **Source**: `malecns_ingest.py:MALECNS_NODE_TYPE_BIOLOGY = "UNDEFINED IN AVAILABLE SOURCE"`

### 4.5 Mesh Geometry and Topology Analysis

- **Input**: Parsed .ngmesh data
- **Code**: `biological_brain/malecns_mesh_geometry.py`
- **What it does**: Computes surface area via cross product and Heron's formula; checks mesh closure (boundary edges, non-manifold edges, component count)
- **Output**: Surface areas (18,725.6 µm² for 801970, 19,665.4 µm² for 801295); topology metrics (462k+ boundary edges, 2.6k+ components)
- **Validation**: Cross product and Heron agree to 2e-16 relative error
- **Can establish**: Mesh geometric properties
- **Cannot establish**: Biological connectivity or compartment assignment
- **Source**: `final_anatomy_audit.md` Block I, `research/anatomy_registry.md`

### 4.6 PSI Contact-to-Surface Associations

- **Input**: 43 contacts with 8 nm coordinates; MN5 mesh
- **Code**: `malecns_compartment.py` (contact-to-mesh distance)
- **What it does**: Finds nearest surface triangle for each contact; records distance, triangle index, vertex indices
- **Output**: Contact-to-mesh surface distances (1.67–80.22 nm range)
- **Key finding**: 3 contacts are AMBIGUOUS (margin ratios 1.110–1.172, same runner-up fragment)
- **Can establish**: Geometric proximity of contacts to mesh surface
- **Cannot establish**: Electrical significance of surface proximity
- **Source**: `final_anatomy_audit.md` Block D

### 4.7 Contact-to-SWC Projections

- **Input**: 43 contacts; 2 MN5 SWCs
- **Code**: `analyze_mn5_compartment_post_swc_type.py`
- **What it does**: Projects each contact to its nearest SWC node; verifies 1:1 mapping
- **Output**: 43/43 verified mappings; all nodes are `kind=0`
- **Can establish**: Spatial projection of contacts to skeleton nodes
- **Cannot establish**: Any electrical distance or voltage transfer
- **Source**: `research/mn5_compartment_post_swc_type_concordance.csv`

### 4.8 Morphological Path-Distance Calculations

- **Input**: SWC node tree, contact projections
- **Code**: `SkeletonGeometry.path_to_root`
- **What it does**: Computes geometric path length from each contact's nearest SWC node to the tree root (sum of edge distances)
- **Output**: Contact-to-root path lengths (169.2–267.8 µm on 801970; 169.2–230.6 µm on 801295)
- **Key limitation**: Root is NOT a soma (no `kind=1` nodes exist); path is geometric only
- **Can establish**: Geometric path length
- **Cannot establish**: Electrotonic distance or voltage attenuation
- **Source**: `malecns_ingest.py:SkeletonGeometry.path_to_root`, `final_anatomy_audit.md` Block F

### 4.9 Reduced MN5 Model

- **Input**: 3 native measurements (resting potential, threshold, AP amplitude)
- **Code**: `biological_brain/reduced_mn5.py` (`ReducedMN5Simulator`)
- **What it does**: Threshold-only abstraction — no leak, no compartment, no synapse, no cable model
- **Output**: `SpikeEvent` objects when software input drives voltage past threshold
- **Key design**: τ_m (membrane time constant) is BLOCKED; `apply_software_input` requires marker "SOFTWARE INPUT -- NOT A BIOLOGICAL MEASUREMENT"
- **Can establish**: That the model fires when driven by explicit input
- **Cannot establish**: Any native physiology, EPSP shape, conductance, or spatial transfer
- **Source**: `reduced_mn5.py` lines 7-13 (docstring), 47-48 (blocked properties)

### 4.10 ParameterSet and Parameter Authorization

- **Input**: 108 parameters from `research/model_input_freeze.csv` (40 SAFE, 31 ASSUMPTION, 37 BLOCKED, 15 conflicts)
- **Code**: `model_framework.py:ParameterSet`
- **What it does**: Loads frozen parameters; `require()` method raises `BlockedParameterError` for any BLOCKED parameter
- **Output**: Only authorized parameters returned; all blocked parameters raise exceptions
- **Key gates**: 
  - Gate A: `require_biological_transfer_authorization()` and `require_spatial_transfer()` both raise
  - Gate B: `require_dalpha7_gate()` raises
- **Can establish**: Provenance-controlled parameter access
- **Cannot establish**: Any blocked biological quantity
- **Source**: `model_framework.py` lines 68-176 (ParameterSet), `reduced_mn5.py` (capability surface)

### 4.11 Exploratory Sensitivity Analysis

- **Input**: Contact concordance CSV, 2 SWC files (pinned SHA-256), frozen parameter grids, Augustin et al. 2019 geometry
- **Code**: `research/scripts/analyze_mn5_two_gate_constraint_model.py` (`run_analysis`)
- **What it does**: 
  1. Contact-local single-patch: `A = 2πrℓ`, `Cpatch = A·Cm`, `gleak = A/Rm`, integrate `Cpatch·dV/dt = −gleak(V−Vrest) + gPSI(t)(Esyn−V)` at dt=0.01 ms for 15 ms
  2. Abstract two-compartment bridge: 112.5 µm length, 2 µm diameter, derived from GFS DLMn geometry
  3. Dα7 effective-conductance sweep: 0.01–1000 nS with E_Dα7 ∈ {−15, 0, +10} mV
  4. EPSP calibration: fit gPSI against 4.71 mV target
- **Output**: 15,528-row CSV (9,288 local + 2,880 abstract + 2,880 Dα7 + 480 calibration)
- **Can establish**: Model-derived sensitivity ranges under declared assumptions
- **Cannot establish**: Native physiological values or validation
- **Source**: Script constants `GFS_BRIDGE_LENGTH_UM = 112.5`, `GFS_BRIDGE_DIAMETER_UM = 2.0`, `DT_MS = 0.01`

### 4.12 Evidence Classes

| Code | Enum name | Definition |
|---|---|---|
| `NEM` | NATIVE_EXPERIMENTAL_MEASUREMENT | Direct experimental measurement in native tissue |
| `AM` | ANATOMICAL_MEASUREMENT | Connectomic or standard anatomical observation |
| `LDP` | LITERATURE_DERIVED_PASSIVE_PARAMETER | Published parameter from primary literature |
| `MDE` | MODEL_DERIVED_ESTIMATE | Output of a declared, assumption-bounded model |
| `MA` | MODEL_ASSUMPTION | Declared assumption with no empirical basis |

- **Source**: `malecns_ingest.py:EvidenceClass` lines 87-98; `model_framework.py:ModelProvenance`

### 4.13 Automated Tests and Reproducibility

- **Test command**: `python -m pytest tests/ -v --tb=short --ignore=tests/test_diagnostics.py`
- **Result**: 1,773 passed, 2 skipped (INHERITED — not freshly reproduced)
- **Gate tests**: `test_mn5_spatial_transfer_gate_review.py`, `test_parameter_adoption.py`
- **Can establish**: Software correctness against stated assertions
- **Cannot establish**: Biological validity

---

## 5. Results: Understand Every Finding

### Section 1: Data Provenance and Inputs

- **Finding**: MN5 = 801970/801295 (left/right); PSI = 802401/903327. Both MN5 bodies annotated `somaSide` L/R, `somaNeuromere` T2, `exitNerve` PDMNa.
- **Source**: `final_anatomy_audit.md` Block A; MaleCNS v1.0 annotation table
- **Calculation**: Direct read from annotation layer
- **Interpretation**: Body identity is a connectomic annotation [C-101]
- **Evidence class**: AM (anatomical measurement)
- **Limitations**: Textual cell-type assignment, not inferred
- **Reviewer explanation**: "These are body IDs from the MaleCNS v1.0 annotation table — the connectome's own labels for these neurons."

### Section 2: PSI Contact Inventory

- **Finding**: 43 PSI→MN5 contacts at minconf 0.5 (17 left: 802401→801970; 26 right: 903327→801295)
- **Source**: `research/artifacts/malecns_compartment_post_psi_mn5.csv`
- **Calculation**: Extraction from Feather file + cross-check against annotation layer (both report 17 and 26)
- **Interpretation**: Contact count is anatomical; `compartment_post = axon` for all 43
- **Evidence class**: AM
- **Limitations**: 5 contacts on 801295 have `compartment_pre = unknown` (preserved, not imputed)
- **Reviewer explanation**: "At minimum confidence 0.5, the dataset records 43 contacts. All are on MN5's axon. This is a dataset annotation, not a voltage measurement."

### Section 3: MN5 Morphology, Mesh, and Registration

- **Finding**: Mesh surface areas 18,725.6/19,665.4 µm² (cross product); SWC frustum estimates give 24,803.7/25,796.8 µm² (~24% difference — different geometric domains)
- **Source**: `malecns_ingest.py`, `final_anatomy_audit.md` Block I
- **Calculation**: Cross product and Heron formulas validated to 2e-16 relative error
- **Interpretation**: Mesh is non-closed and fragmented (462k+ boundary edges, 2.6k+ components; largest component = 2.8% of area)
- **Evidence class**: AM
- **Limitations**: neuPrint attributes fragmentation to "segmentation artifacts"; no component has a biological compartment name
- **Reviewer explanation**: "The mesh is topologically broken — it's in 2,587 pieces. That's a data artifact, not biology."

### Section 4: Morphological Path Analysis

- **Finding**: Contact→root path lengths 169.2–267.8 µm (801970); contact→somaLocation straight-line 110.3–172.9 µm
- **Source**: `analyze_mn5_two_gate_constraint_model.py`, `final_anatomy_audit.md` Block F/K
- **Calculation**: SWC edge-distance sums
- **Interpretation**: No soma node (`kind=1`) exists in any skeleton; contact→soma graph path is UNRESOLVED
- **Evidence class**: MDE (on explicit node-assignment rule) for paths; MA for soma-proxy assumption
- **Limitations**: Root is "not particularly significant" per neuPrint; straight-line distance ≠ electrotonic distance
- **Reviewer explanation**: "We can measure how long the wire is, but we cannot measure how much voltage gets lost traveling along it. The geometry is necessary but insufficient."

### Section 5: Electrophysiological Evidence

- **Finding**: Resting potential −67.8 ± 5.5 mV (n=13); threshold −24.1 ± 8.2 mV (n=11); AP amplitude +45.5 ± 8.6 mV (n=13); input resistance 102 ± 12 MΩ (n=22) and 97 ± 31 MΩ (n=52)
- **Source**: `model_input_freeze.md` Section A; Fayyazuddin et al. 2006; Ryglewski & Duch 2009
- **Evidence class**: NEM (native experimental measurement)
- **Capacitance conflict**: 43 ± 2 pF vs 127 ± 16 pF — both retained, no winner [C-303]
- **EPSP**: 4.71 ± 0.35 mV (n=10) under GF stimulation — comparison target only [C-304]
- **Reviewer explanation**: "These are real measurements, but the capacitance conflict shows we can't even agree on a basic cellular parameter. That blocks any cable model."

### Section 6: Model Analysis and Sensitivity

- **Finding**: 15,528-row sensitivity analysis (9,288 local + 2,880 abstract + 2,880 Dα7 + 480 calibration)
- **Source**: `mn5_psi_mn5_final_constraint_model_sensitivity.csv`
- **Local peak ranges**: 0.58–77.80 mV (driven by free gPSI)
- **Abstract bridge ranges**: somatic peak 0.0028/1.812/67.078 mV (min/median/max); local-to-somatic ratio 0.085/0.517/0.892
- **Nominal bridge point**: C-01 A = 1.108 mV; C-01 B = 0.510 mV
- **Fitted gPSI**: 3.58–42.73 nS (at nominal point: A = 4.49 nS, B = 10.16 nS)
- **Dα7 sweep**: 0.005–68.77 mV somatic change; 456/2,880 threshold crossings at largest conductances
- **Evidence class**: MDE (model-derived estimate) for all outputs
- **Key caveat**: Numerical reachability ≠ biological plausibility [C-601]
- **Reviewer explanation**: "These are sensitivity ranges. The model says 'if you assume these parameters, you get these outputs.' It does not say what the biology actually is."

### Section 7: Closed Gates and Evidence Gaps

- **Finding**: Gate A (spatial voltage transfer) — NOT AUTHORIZED; Gate B (Dα7 conductance) — NOT AUTHORIZED
- **Source**: `missing_evidence.md` M-02 (Gate A), M-01/M-04 (Gate B)
- **Evidence class**: MA (negative evidence / search exhausted)
- **Resolving experiments**: Gate A → dual-site recording; Gate B → same + Dα7 manipulation
- **Reviewer explanation**: "Closed gates mean the evidence base doesn't support these measurements — not that they don't exist. We show the boundary honestly."

### Section 8: Reproducibility and Validation

- **Finding**: 1,773 passed / 2 skipped (INHERITED from `validation/full_suite_report.md`)
- **Source**: `AGENTS.md`, `validation/full_suite_report.md`
- **Evidence class**: AM (software test record)
- **Limitations**: Feather checksum NOT RECORDED at manuscript time (updated during 2026-10-09 verification); staging commands NOT DOCUMENTED; test count inherited
- **Reviewer explanation**: "Tests verify code correctness. A million passing tests do not validate biology — especially when the key inputs are unknown."

---

## 6. Explain Every Figure and Table

### Figure 1 — Escape Circuit Diagram

- **What it shows**: The GFS escape pathway: optic lobe → GF → (TTMn jump / PSI → MN5 → DLM muscle)
- **How to read it**: Colored boxes = neurons; dashed lines = electrical synapses; solid lines = chemical synapses
- **Source data**: `malecns_ingest.py:BODY_IDENTITIES`, `model_framework.py:FROZEN_MN5_ANATOMY`
- **Labels**: OL (optic lobe), GF (giant fiber), TTMn (jump motor), PSI (intermediate interneuron), MN5 (motor neuron 5), DLM (flight muscle)
- **Supports**: C-101 (body identity, circuit topology)
- **Main takeaway**: PSI→MN5 is a chemical synapse; GF→TTMn and GF→PSI are electrical
- **Must NOT infer**: Any voltage transfer, conductance value, or biological validation from this schematic

### Figure 2 — Provenance Pipeline

- **What it shows**: Flow from source datasets → evidence classes → model inputs → outputs, with gate enforcement
- **How to read it**: Left column = source datasets; middle = ingestion/anatomical analysis; center = parameter authorization with gates; right = model-derived outputs
- **Source data**: `model_framework.py`, `malecns_ingest.py`, `reduced_mn5.py`, `model_input_freeze.csv`
- **Labels**: Five evidence classes (LDP, NEM, AM, MDE, MA); SAFE/ASSUMPTION/BLOCKED buckets
- **Supports**: C-301, C-401, C-501, C-602
- **Main takeaway**: The five-class taxonomy is enforced at the code level
- **Must NOT infer**: That classes can be collapsed; model outputs are not experimental evidence

### Figure 3 — Contact Mapping

- **What it shows**: Bilateral PSI→MN5 contact counts at minconf 0.5
- **How to read it**: Bar chart — left bar height = 17 (802401→801970), right bar height = 26 (903327→801295)
- **Source data**: `research/artifacts/malecns_compartment_post_summary.json`
- **Labels**: "17" and "26" for contact counts; body ID pairings
- **Supports**: C-102 (contact count)
- **Main takeaway**: 43 total contacts, corroborated by two independent dataset files
- **Must NOT infer**: Complete soma paths, voltage transfer, or contact significance beyond count

### Figure 4 — Compartment Annotations

- **What it shows**: Distribution of `compartment_pre` and `compartment_post` labels across 43 contacts
- **How to read it**: Grouped bars — pre: 43 axon; post: 38 axon + 5 unknown (pre); post: 43 axon
- **Source data**: `research/artifacts/malecns_compartment_post_summary.json`
- **Labels**: `compartment_pre` (38 axon, 5 unknown on 801295); `compartment_post` (all 43 axon)
- **Supports**: C-103 (compartment_post = axon for all 43)
- **Main takeaway**: All contacts are postsynaptically on MN5's axon
- **Must NOT infer**: That "axon" establishes voltage transfer, SWC kind semantics, or biological compartment identity

### Figure 5 — Two-Gate Conditional Model

- **What it shows**: Three panels — contact-local patch, abstract cable bridge, closed gates + sensitivity grid
- **How to read it**: Left panel = contact-local analysis geometry; center = abstract bridge (112.5 µm × 2 µm); right = gate status and sensitivity grid
- **Source data**: `analyze_mn5_two_gate_constraint_model.py` (GFS_BRIDGE_LENGTH_UM, GFS_BRIDGE_DIAMETER_UM)
- **Labels**: "MODEL-DERIVED" on all panels; Gate A/B "NOT AUTHORIZED"
- **Supports**: C-402, C-201, C-401, C-501
- **Main takeaway**: The model is explicitly assumption-bounded; outputs are conditional
- **Must NOT infer**: Native transfer, anatomical soma path, or empirical validation
- **Note**: Footer cites Augustin et al. 2019 as *eNeuro*; the actual journal is *eNeuro* (eLife citation in footer is misleading — source_registry.md S-06 confirms eNeuro)

### Figure 6 — Sensitivity Summary

- **What it shows**: Model-derived min/median/max for local peak, somatic peak, and local-to-somatic ratio
- **How to read it**: Three box plots showing output ranges; A (43 pF) and B (127 pF) variants shown separately
- **Source data**: `mn5_psi_mn5_final_constraint_model_sensitivity.csv` (15,528 rows)
- **Labels**: Local peak (min 40.13 / max 67.71 mV at nominal); somatic (0.0028 / 1.812 / 67.078); ratio (0.085 / 0.517 / 0.892); nominal point A=1.108 / B=0.510
- **Supports**: C-601, C-402, C-503, C-303
- **Main takeaway**: Model-derived ranges, not confidence intervals; both capacitance variants shown without selection
- **Must NOT infer**: Population-level biological estimates; confidence intervals; native conductance values

### Figure 7 — Model Capability/Gating Diagram

- **What it shows**: Capability surface — AVAILABLE/PARTIAL/BLOCKED — with the two gates
- **How to read it**: Status table of what the model can/cannot do
- **Source data**: `reduced_mn5.py:ReducedMN5Simulator.capabilities()`, `model_framework.py:MN5Model.capabilities()`
- **Labels**: AVAILABLE (anatomy), PARTIAL (reduced model), BLOCKED (spatial transfer, Dα7 conductance)
- **Supports**: C-602, C-401, C-501
- **Note**: This is a **stub** — pending hand-authoring (per `FIGURE_PLAN.md`)
- **Must NOT infer**: That capability implies validation

### Figure 8 — Reproducibility Overview

- **What it shows**: Test status and external-data limitations
- **How to read it**: Summary table of what is pinned vs. unpinned
- **Source data**: `validation/full_suite_report.md`, `AGENTS.md`, `EXTERNAL_DATA_REPRODUCIBILITY.md`
- **Labels**: "1773 passed / 2 skipped (inherited)"; "Feather checksum NOT RECORDED"; "staging commands NOT DOCUMENTED"
- **Supports**: C-602, C-701
- **Note**: This is a **stub** — pending hand-authoring
- **Must NOT infer**: Clean-checkout reproducibility from current worktree state

### Table R-1 — Contact Summary

- **What it shows**: Bilateral contact counts with compartment labels
- **Source data**: `malecns_compartment_post_summary.json`
- **Key values**: Left 802401→801970: 17 contacts, all compartment_post=axon; Right 903327→801295: 26 contacts, compartment_pre: 21 axon + 5 unknown
- **Supports**: C-102, C-103
- **Must NOT infer**: Any electrical parameter from counts or labels

### Table R-2 — Native Biophysics

- **What it shows**: Admissible native measurements with n, source, provenance
- **Source data**: `model_input_freeze.csv` (SAFE bucket)
- **Key values**: Resting potential −67.8 ± 5.5 mV (n=13), threshold −24.1 ± 8.2 mV (n=11), AP amplitude +45.5 ± 8.6 mV (n=13), input resistance 102 ± 12 MΩ (n=22) / 97 ± 31 MΩ (n=52)
- **Conflict C-01**: 43 ± 2 pF vs 127 ± 16 pF — both retained, no winner
- **Supports**: C-301, C-302, C-303
- **Must NOT infer**: A single correct capacitance or cable parameters

### Table R-3 — Capability Surface

- **What it shows**: What is available, blocked, or assumption-only
- **Source data**: `model_input_freeze.csv` bucket counts; `reduced_mn5.py`, `model_framework.py`
- **Key values**: 40 SAFE, 31 ASSUMPTION, 37 BLOCKED, 15 conflicts
- **Gates**: Gate A (spatial transfer) BLOCKED; Gate B (Dα7 conductance) BLOCKED
- **Supports**: C-301, C-401, C-501, C-602
- **Must NOT infer**: That blocked quantities are zero or that capability implies biological reality

### Table R-4 — Reproducibility Status

- **What it shows**: Pinned vs unpinned inputs, checksum presence, test-run status
- **Source data**: `validation/full_suite_report.md`, `EXTERNAL_DATA_REPRODUCIBILITY.md`
- **Key values**: Tests 1,773 passed / 2 skipped (INHERITED); SWC SHA-256 pinned; Feather checksum NOT RECORDED; staging commands NOT DOCUMENTED
- **Supports**: C-701, C-602
- **Must NOT infer**: Clean-checkout reproducibility or biological validation from software tests

---

## 7. Discussion: Understand the Interpretation

### 7.1 Strongest Supported Contributions

1. **Audited 43-contact inventory** — two independent dataset files agree [C-102]
2. **Provenance-aware framework** — raises on blocked parameters [C-401, C-501]
3. **Minimum-honest model** — 3 native inputs, no leak, no assumed conductance [C-602]
4. **Conditional sensitivity** — 15,528 rows, explicitly MDE-tagged [C-601]

### 7.2 Anatomical vs. Electrophysiological Evidence

- **Anatomy** (C-101–C-204): Strong — from MaleCNS v1.0, a peer-reviewed EM connectome
- **Native electrophysiology** (C-301–C-304): Moderate — measurements exist but are incomplete (no synaptic conductance, capacitance conflicted)
- **Model-derived** (C-402, C-503, C-601): Conditional — explicit assumptions, not measurements
- **Software validation** (C-602): Strong at code level, zero at biological level

### 7.3 Why Sensitivity is Not Validation

The sensitivity analysis varies parameters over ranges and reports output distributions. This shows **what the model would do if these assumptions were true** — it does not show that the assumptions ARE true. The 4.71 mV EPSP calibration is labeled "numerical reachability is not biological plausibility" [C-601].

### 7.4 Why C-01 Remains Unresolved

Two native whole-cell capacitance values (43 ± 2 pF and 127 ± 16 pF) conflict at ~2.95× for the same cell/nominal preparation. Variant B's authors cite dendritic space-clamp as an error source. The repository retains both without averaging — because averaging two conflicting measurements creates a false sense of precision [C-303].

### 7.5 Why C-02 and C-03 Remain Unresolved

- **C-02**: GF gap-junction conductance: 135 µS (paper Table 1) vs 135 nS (executed in `gap2.mod`) — exactly 1000× difference, units unrecoverable
- **C-03**: PSI→DLMn chemical conductance: 80 µS (paper) vs 0.08 µS (executed) — exactly 1000×, different synapse from C-02

Both are preserved as `BLOCKED`/`recorded_value` rows. No code path substitutes one for the other. The manuscript does not endorse whether µS or nS is correct — the discrepancy itself is the finding [C-303].

### 7.6 What the Closed Gates Mean Scientifically

Gates are **evidence constraints on interpretation** — the absence of qualifying primary evidence — not assertions that the quantities do not exist [C-401, C-501]. They prevent model-derived sensitivity from being misread as native physiology.

### 7.7 Experiments That Would Resolve Gates

- **Gate A**: Dual-site recording (somatic whole-cell + focal dendritic/axonal patch at contact) during direct PSI stimulation [M-02]
- **Gate B**: Same dual-site preparation with pharmacological reversal/conductance series + Dα7 manipulation [M-01, M-04]

### 7.8 Defensible Novelty Claims

The methodological novelty is the **provenance-aware framework** that prevents blocked quantities from becoming model constants. This is defensible because: (1) the gates are enforced in code, (2) every output is tagged with evidence class, (3) the model honestly refuses to compute unestablishable quantities.

### 7.8 Claims Requiring Caution

Any model-derived output that could be misread as native: fitted gPSI, somatic peaks, threshold crossings. The manuscript requires these be labeled MDE.

---

## 8. Scientific Gates — A Dedicated Explanation

### Gate A: PSI→MN5 Spatial Voltage Transfer — NOT AUTHORIZED [C-401]

**What quantity each gate concerns**: The fraction of postsynaptic voltage change at a PSI→MN5 synaptic contact that reaches MN5's soma — i.e., how much of the local EPSP is "seen" at the soma.

**Why the current evidence does not authorize estimating it**:
1. **No axial resistivity (Ra)**: No Drosophila-specific MN5 Ra measurement exists; only *Manduca* Ra is available (adopted, wrong species) [C-303]
2. **No specific membrane resistance (Rm)**: No native MN5 Rm measurement exists [C-303]
3. **No capacitance resolved**: C-01 conflict (43 vs 127 pF) means Cm enters every cable equation undetermined [C-303]
4. **No soma node**: MaleCNS SWCs have zero `kind=1` nodes; no anatomically reconstructed contact-to-soma path exists [C-201]

**What evidence is missing**: A direct measurement of voltage attenuation from PSI contacts to the MN5 soma in a Drosophila preparation. The literature search (M-02) is exhausted — no such measurement exists in any primary source.

**Why mesh geometry is insufficient**: Mesh surface area can compute capacitance under assumed specific capacitance, but without Ra and the soma path, no cable equation can be solved. Mesh fragmentation (2,587 components) further precludes electrical compartment assignment.

**Why a somatic EPSP does not establish local synaptic conductance or spatial attenuation**: The 4.71 mV EPSP was measured under GF (giant fiber) stimulation, not direct PSI stimulation. It is a filtered somatic voltage that integrates input from all GF-driven pathways — it does not isolate PSI→MN5 transmission, let alone the transfer ratio from contact to soma.

**Why recombinant receptor data cannot establish native PSI→MN5 conductance**: Lansdell et al. 2012 (Dα7 channel EC50, Hill slope) was measured in Xenopus oocytes, not in Drosophila MN5. Oocyte currents do not translate to native synaptic conductance without knowing receptor density, single-channel conductance, and open probability at the synapse.

**What future experiment could provide stronger evidence**: Dual-site recording — somatic whole-cell patch + focal dendritic/axonal patch at the specific PSI contact, during direct PSI activation. This would directly measure the spatial transfer coefficient.

### Gate B: Dα7 Biological Conductance — NOT AUTHORIZED [C-501]

**What quantity each gate concerns**: The native Dα7 nAChR-mediated synaptic conductance at the PSI→MN5 synapse — combining receptor density, single-channel conductance, open probability, and driving force.

**Why the current evidence does not authorize estimating it**:
1. **No native Dα7 at PSI terminals**: Dα7 is enriched at GF dendrites (10–100×) and binds α-bungarotoxin in native tissue, but is **NOT REPORTED** at PSI presynaptic terminals in any primary source [C-502]
2. **No native Dα7 at MN5 axons**: Similarly, no Dα7 immunostaining of MN5 axons exists [C-502]
3. **No native single-channel conductance**: Phelan et al. 2008 Tables S1–S3 (containing ShakB/Dα7 conductance) are INACCESSIBLE; no native Dα7 unitary current recorded
4. **No Drosophila Kir7.1**: The vertebrate α7→Kir7.1 coupling mechanism cannot be modeled because Drosophila lacks the KCNJ13/Kir7.1 orthologue [C-501]

**What evidence is missing**: Direct measurement of Dα7-mediated current at the PSI→MN5 synapse (e.g., focal synaptic recordings with Dα7 antagonists, or imaging of Dα7 at both pre- and postsynaptic sites).

**Why recombinant receptor data is insufficient**: Lansdell et al. 2012 EC50 (6.7 ± 1.7 µM ACh) and max current (86 nA) are channel-level pharmacology in oocytes. Converting this to native synaptic conductance requires: receptor density at the synapse, single-channel conductance in native membrane, open probability at physiological voltage, and synaptic geometry — none of which exist for PSI→MN5.

**What future experiment could provide stronger evidence**: The same dual-site preparation with pharmacological conductance series (varying [ACh] while blocking Dα7) plus Dα7-specific genetic manipulation. A native PSI→MN5 synaptic conductance measurement (M-01) is itself a prerequisite for opening Gate B.

---

## 9. Numerical Conflicts and Provenance

### Conflict Register

| Conflict | Values | Unit discrepancy | Repository status | Source |
|---|---|---|---|---|
| C-01 | 43 ± 2 pF vs 127 ± 16 pF | ~2.95× (same units, different preparations) | UNRESOLVED — both retained, no winner chosen | Fayyazuddin 2006 vs Ryglewski & Duch 2009 |
| C-02 | 135/34.5 µS vs 135/34.5 nS | Exactly 1000× (different units) | UNRESOLVED — recorded_value=True, BLOCKED | Augustin 2019 Table 1 vs gap2.mod |
| C-03 | 80 µS vs 0.08 µS | Exactly 1000× (same units? or µS vs µS) | UNRESOLVED — recorded_value=True, BLOCKED | Augustin 2019 vs gap2.mod |
| C-04 | Chemical synapse vs gap junction grouping | Premise corrected | CORRECTED — tracked separately | C-03 vs C-02 are different mechanisms |
| C-09 | ShakB = Kv1? | Premise corrected | CORRECTED | ShakB = inx8 (innexin), not Kv1 |

### The Five Evidence Classes

| Code | Full name | Definition | Source |
|---|---|---|---|
| `NEM` | `NATIVE_EXPERIMENTAL_MEASUREMENT` | Direct measurement in native tissue | `malecns_ingest.py:EvidenceClass`, `model_framework.py:ModelProvenance` |
| `AM` | `ANATOMICAL_MEASUREMENT` | Connectomic or standard anatomical observation | Same |
| `LDP` | `LITERATURE_DERIVED_PASSIVE_PARAMETER` | Published parameter from primary literature | Same |
| `MDE` | `MODEL_DERIVED_ESTIMATE` | Output of a declared, assumption-bounded model | Same |
| `MA` | `MODEL_ASSUMPTION` | Declared assumption with no empirical basis | Same |

**Key distinction**: The internal model framework uses 8 categories (`ParameterProvenance` in `model_input_freeze.md`), bridged to the five-class freeze taxonomy by an explicit, refusal-on-ambiguity function — values whose freeze class is ambiguous are NOT auto-classified [C-301].

**NOTE**: `paper/README.md` (line 13) and `methods/provenance/evidence_classification.md` both correctly state the project's five evidence classes (NEM, AM, LDP, MDE, MA), enforced in `model_framework.py:ModelProvenance` and `malecns_ingest.py:EvidenceClass`. "Repository-derived" and "validation fixtures" are non-biological and tracked separately by the validation package; they are not evidence classes.

---

## 10. Important Terminology Glossary

- **Drosophila**: Fruit fly (*Drosophila melanogaster*), a genetic model organism
- **Giant Fiber System (GFS)**: A bilateral escape circuit in the fly CNS; GF receives visual input and triggers jump/flight
- **MN5**: Motor neuron 5; innervates DLM fibers 5 and 6; body IDs 801970 (left) / 801295 (right); VFB IDs VFB_jrmc37jr / VFB_jrmc37js
- **PSI**: Protocerebral Surgical Interneuron; intermediate interneuron between GF and MN5; body IDs 802401 (left) / 903327 (right)
- **DLMn**: Dorsal Longitudinal Muscle motoneuron — MN5 is one of the DLMn neurons
- **MaleCNS**: The Male CNS project — a complete EM connectome of the adult male *Drosophila* CNS (Berg et al. 2026, Cell)
- **SWC**: A standardized neuron morphology file format (7 columns: index, type/kind, x, y, z, radius, parent). Format spec: Mehta et al. 2023, Nat Commun
- **Mesh (.ngmesh)**: Binary mesh format from MaleCNS; vertex count + float32 XYZ + triangle indices
- **Synaptic contact**: A presynaptic site from one neuron to a postsynaptic site on another, identified in EM
- **Compartment annotation**: Dataset label (`compartment_pre`/`compartment_post`) assigned per synapse; the MaleCNS enum is `["unknown","axon","dendrite","linker","cell-body-fiber"]`
- **SIZ**: Spike Initiation Zone — the axon initial segment where action potentials are generated. Registration of SIZ to MaleCNS mesh remains UNRESOLVED [C-202]
- **Input resistance**: Ratio of voltage change to current injected at the soma (measured: 102 ± 12 MΩ n=22, 97 ± 31 MΩ n=52) [C-302]
- **Membrane capacitance**: Capacitance of the neuronal membrane (conflicted: 43±2 vs 127±16 pF) [C-303]
- **Synaptic reversal potential (E_syn)**: Theoretical voltage at which net synaptic current = 0. For acetylcholine: −15 to +10 mV (model assumption, swept) [C-402]
- **Conductance**: Measure of ion flow through channels (units: S, µS, nS). gPSI = PSI→MN5 conductance (not measured); g_Dα7 = Dα7 receptor conductance (NOT AUTHORIZED)
- **Spatial voltage transfer**: Fraction of voltage change at a synaptic contact that reaches the soma (NOT AUTHORIZED — Gate A) [C-401]
- **Attenuation**: Reduction in signal amplitude as it propagates from site of origin to recording site
- **Morphological path distance**: Geometric length along the SWC skeleton from a point to root (measured: 169–268 µm) — NOT electrotonic distance [C-201]
- **Electrotonic distance**: Distance weighted by cable properties (Ra, Rm, Cm) — NOT computed in this work [C-401]
- **Parameter sensitivity**: How model outputs change as parameters vary over a range
- **Provenance**: Traceability of a datum to its source: measurement, dataset, literature, assumption, or model
- **Identifiability**: Whether a parameter can be uniquely determined from available data (MN5 Cm is NOT identifiable — overdetermined conflict)
- **Model-derived estimate (MDE)**: Output of a declared, assumption-bounded model — explicitly NOT a native measurement
- **Evidence authorization gate**: A code-level enforcement that prevents a blocked quantity from being used as if measured
- **minconf**: Minimum confidence threshold (0.5) applied by the MaleCNS source and encoded in filenames
- **Gap junction**: Electrical synapse via innexins (ShakB/inx8 in Drosophila) — direct cytoplasmic connection between cells
- **Dα7**: Drosophila nicotinic acetylcholine receptor α7 subunit — receptor at cholinergic synapses
- **Neuroglancer annotations**: Precomputed annotation layer format used by MaleCNS for synapse compartments
- **cloud-volume**: Library for reading neuroglancer precomputed data over HTTP range requests

---

## 11. Reviewer Preparation

### Questions Grouped by Topic

#### Biological Significance

**Q1: Why study PSI→MN5 specifically?**
- **Answer**: PSI→MN5 is the chemical synapse in the Giant Fiber System escape pathway. Understanding how visual threat signals propagate from GF through PSI to MN5 is fundamental to the escape response circuit.
- **Evidence**: C-101 (circuit topology from Ryglewski & Duch 2009); INTRODUCTION_DRAFT.md §1
- **Uncertainty**: The study does not claim to have measured this transmission — only to have audited the evidence base and built a conditional model.

**Q2: Is 43 contacts a lot or a few?**
- **Answer**: For a single synaptic pathway, 43 is a substantial number of independent release sites, suggesting strong and reliable transmission. However, quantity does not establish efficacy without knowing release probability and postsynaptic response.
- **Evidence**: C-102 (contact count, 43 at minconf 0.5)
- **Uncertainty**: Contact count does not establish release probability or postsynaptic response amplitude.

#### Novelty

**Q3: What is genuinely new here?**
- **Answer**: The novelty is methodological — a provenance-aware framework that enforces evidence-class separation and raises on blocked parameters. No new biological measurement is claimed.
- **Evidence**: C-401, C-501 (gate enforcement); DISCUSSION_DRAFT.md §9
- **Uncertainty**: Reviewers may expect new biological findings; the paper must be framed as a methodological demonstration.

**Q4: Hasn't the GFS been modeled before?**
- **Answer**: Yes — Augustin et al. 2019 (ModelDB 245415) modeled the GF→TTMn/PSI→DLMn circuit. But no prior work has audited and enforced evidence-class separation for the PSI→MN5 synapse specifically.
- **Evidence**: C-402 (model precedent); source_registry.md S-06, S-03
- **Uncertainty**: The GFS model precedent exists but does not resolve the PSI→MN5 gate.

#### Data Provenance

**Q5: Where does the anatomical data come from?**
- **Answer**: MaleCNS v1.0, a complete male *Drosophila* CNS connectome published by Berg et al. 2026 (Cell, DOI: 10.1016/j.cell.2026.08.015, CC-BY).
- **Evidence**: C-101; `malecns_ingest.py:DATASET_CITATION`
- **Uncertainty**: The Feather file (~6.8 GB) lacks a verified checksum and staging documentation.

**Q6: Is the Feather checksum verified?**
- **Answer**: The SHA-256 was computed during the 2026-10-09 verification pass: `959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07`. However, the repository had NOT previously recorded it — it was NOT RECORDED before this audit.
- **Evidence**: `EXTERNAL_DATA_REPRODUCIBILITY.md`; `data/README.md`; computed from local file
- **Uncertainty**: No independent third-party checksum from the source repository (Janelia/MaleCNS portal) was obtained.

**Q7: Can someone reproduce the analysis from a clean checkout?**
- **Answer**: Not fully. The raw Feather file is not in the repository and has no documented staging command. SWC hashes are pinned, but the Feather input is externally staged.
- **Evidence**: C-701; `EXTERNAL_DATA_REPRODUCIBILITY.md` §4
- **Uncertainty**: The staging command is NOT DOCUMENTED — the repo records no download procedure.

#### Anatomical Validation

**Q8: How were contacts validated?**
- **Answer**: Two independent dataset files were cross-checked: the synapse-partners Feather extracted 43 contacts (17+26), and the official annotation layer independently confirmed 17 and 26 for the respective pairings.
- **Evidence**: C-102; `final_anatomy_audit.md` Block B; RESULTS_DRAFT.md §2
- **Uncertainty**: The non-unique match (both sources agree on 17/26) raises C-102 — this is a corroboration, not a guarantee of individual contact accuracy.

**Q9: Does `compartment_post = axon` mean the contact is on the axon?**
- **Answer**: Yes — but this is a **dataset annotation**, not an electrophysiological measurement. The MaleCNS annotation layer uses a flow-centrality algorithm (navis `split_axon_dendrite`) to assign compartment labels.
- **Evidence**: C-103; source_registry.md S-14 (navis algorithm)
- **Uncertainty**: The annotation has no uncertainty estimate; the algorithm can misassign at ties or orphans.

#### Contact Interpretation

**Q10: Do more contacts mean stronger transmission?**
- **Answer**: Potentially — but without knowing release probability, vesicle pool size, postsynaptic receptor density, and the unitary response amplitude, contact count alone cannot predict efficacy.
- **Evidence**: Contact count is AM (anatomical), not NEM (functional measurement)
- **Uncertainty**: Release probability, vesicle depletion, and postsynaptic response are among the 13 structurally empty (value=None) parameters [C-303 constraints]

**Q11: Why are 3 contacts AMBIGUOUS?**
- **Answer**: Their nearest-triangle distance margin ratios are 1.110–1.172 (the runner-up is the same fragment in all three cases). Rather than inventing a threshold, they are preserved as AMBIGUOUS.
- **Evidence**: C-201; `final_anatomy_audit.md` Block D
- **Uncertainty**: No resolution was forced — the ambiguity is reported honestly.

#### SWC Type Semantics

**Q12: What does SWC `kind=2` mean?**
- **Answer**: In the SWC v1.0.0 specification, Type 2 = Axon. But MaleCNS documents **nothing** about how its Type column is populated, so `kind=2` in MaleCNS may NOT mean biological axon.
- **Evidence**: C-203; `malecns_ingest.py:MALECNS_NODE_TYPE_BIOLOGY = "UNDEFINED IN AVAILABLE SOURCE"`
- **Uncertainty**: The project treats `kind` codes as format semantics only, never biologically interpreted.

**Q13: Why is there no soma node?**
- **Answer**: All 9 MN5/PSI skeletons have zero `kind=1` (soma) nodes. The soma region is represented only by a proximal dilation near `somaLocation`, modeled as `kind=2`.
- **Evidence**: C-202; `final_anatomy_audit.md` Block F/K
- **Uncertainty**: A soma-proxy path (154.1–241.6 µm) is computed but flagged as MDE on MA assumption.

#### Model Design

**Q14: Why is the model so simple (threshold only, no leak)?**
- **Answer**: Because Mn5 passive parameters are underdetermined — two whole-cell measurements (43 pF, 102 MΩ; or 127 pF, 97 MΩ) give 2 equations for 3 unknowns (Cm, Rm, Ra), and no independent Ra constraint exists. No leak = no assumed τ_m.
- **Evidence**: C-301, C-303; METHODS_DRAFT.md §9
- **Uncertainty**: This is a deliberate minimum-honest design, not a simplification choice.

**Q15: What is the abstract cable bridge?**
- **Answer**: A uniform two-compartment cable (112.5 µm length, 2 µm diameter) derived from published GFS DLMn geometry (Augustin et al. 2019). It's NOT traced onto the MaleCNS SWC and makes no per-contact anatomical soma path.
- **Evidence**: C-402; `GFS_BRIDGE_LENGTH_UM = 112.5, GFS_BRIDGE_DIAMETER_UM = 2.0`
- **Uncertainty**: Bridge geometry is from published precedent, not MaleCNS anatomy.

#### Sensitivity Analysis

**Q16: Are the sensitivity ranges confidence intervals?**
- **Answer**: No. The sweep is a deterministic grid over parameter space, not a probability distribution. Min/median/max describe sampled model outcomes only.
- **Evidence**: C-601; METHODS_DRAFT.md §10
- **Uncertainty**: The parameter ranges (especially gPSI 0.01–1000 nS) are exploratory, not physiologically constrained.

**Q17: What does fitted gPSI = 4.49 nS mean?**
- **Answer**: It is the conductance that, under the stated model assumptions at the nominal GFS-bridge point, would produce a 4.71 mV somatic peak. It is model-derived — numerical reachability, not biological validation.
- **Evidence**: C-601; RESULTS_DRAFT.md §6
- **Uncertainty**: This is an inverse fit, not a measurement. It depends entirely on the assumption that the bridge geometry and passive parameters are correct.

#### Capacitance Conflict

**Q18: Why can't you just pick the better capacitance measurement?**
- **Answer**: Both are native measurements from the same nominal preparation (Fayyazuddin et al. 2006 for 43 pF; Ryglewski & Duch 2009 for 127 pF). Variant B's own authors cite dendritic space-clamp as an error source, but variant A has its own limitations. Without an independent discriminator, choosing one would be arbitrary.
- **Evidence**: C-303; DISCUSSION_DRAFT.md §5
- **Uncertainty**: The ~2.95× discrepancy is itself the finding — the parameter is not identifiable from current evidence.

#### Conductance Discrepancies

**Q19: Does the 1000× gap-junction discrepancy mean the model is wrong?**
- **Answer**: It means the model's code uses nanosiemens while the paper's Table 1 reports microsiemens. Whether this is a bug, a deliberate rescaling, or an axis-label error is unrecoverable from the repository.
- **Evidence**: C-02; `conflicts.md` line 89, 165; source_registry.md S-06 line 125-131
- **Uncertainty**: The repository records both values but does not endorse either.

**Q20: Are C-02 and C-03 the same issue?**
- **Answer**: No. C-02 is the GF gap-junction (electrical synapse, 135 µS vs 135 nS). C-03 is the PSI→DLMn chemical synapse (80 µS vs 0.08 µS). They are different synapses with different mechanisms.
- **Evidence**: C-04 (premise corrected); `biological_summary_evidence_audit.md` lines 117-118
- **Uncertainty**: The project explicitly avoids pooling these.

#### The Two Scientific Gates

**Q21: Why can't the model compute voltage transfer from the SWC path lengths?**
- **Answer**: Path length is geometric — it measures wire length, not electrical resistance. Without Ra, Rm, and Cm (all unknown/conflicted for MN5), no cable equation can be solved.
- **Evidence**: C-401, C-201; `require_spatial_transfer()` always raises
- **Uncertainty**: Geometric distance ≠ electrotonic distance. The gap is fundamental.

**Q22: Why can't Dα7 conductance be computed from recombinant data?**
- **Answer**: Recombinant channel EC50 (6.7 µM ACh) tells us the concentration-response, not the native synaptic conductance. Converting requires receptor density, single-channel conductance, open probability, and driving force — none measured at PSI→MN5.
- **Evidence**: C-501; source_registry.md S-19
- **Uncertainty**: Oocyte expression ≠ native synapse.

**Q23: Are the gates a statement that these quantities are zero?**
- **Answer**: No. The gates are "evidence constraints on interpretation" — the absence of qualifying primary evidence. The biological quantities may exist; they are simply not measurable from current evidence.
- **Evidence**: C-401, C-501; DISCUSSION_DRAFT.md §7
- **Uncertainty**: This is a critical distinction for reviewers to understand.

#### Reproducibility

**Q24: Is the Feather checksum now recorded?**
- **Answer**: Yes — `959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07` (computed 2026-10-09). But the staging command is still NOT DOCUMENTED.
- **Evidence**: `data/README.md`, `EXTERNAL_DATA_REPRODUCIBILITY.md`
- **Uncertainty**: No third-party verification of the checksum from Janelia.

**Q25: Do the tests validate the biology?**
- **Answer**: No. Tests verify code paths against assertions. 1,773 passed / 2 skipped means the code behaves as specified — not that the model produces biological truth.
- **Evidence**: C-602; METHODS_DRAFT.md §12
- **Uncertainty**: The test count is inherited, not freshly reproduced.

#### Dataset Licensing and Attribution

**Q26: Is the CC-BY license sufficient for redistribution?**
- **Answer**: The repository records CC-BY but does NOT include the license text or a bulk-redistribution review. VERIFY_REQUIRED before republishing.
- **Evidence**: `data/README.md` line 16; `EXTERNAL_DATA_REPRODUCIBILITY.md`
- **Uncertainty**: Bulk redistribution of the 6.8 GB Feather requires manual license review.

**Q27: Is the Berg et al. author list correct?**
- **Answer**: Verified against the DOI publisher page (Cell, doi.org/10.1016/j.cell.2026.08.015) — 39 authors, 20 explicitly listed plus "et al." Transcribed into `references.bib`.
- **Evidence**: `references.bib`; webfetch of DOI page
- **Uncertainty**: The repository previously used shorthand "Berg, S. et al." — now updated with full names.

#### Limitations and Future Experiments

**Q28: What is the single biggest limitation?**
- **Answer**: The unresolved capacitance conflict (C-01) combined with missing Ra and the absence of a soma node. Without these, no cable model of MN5 is licensed, which is the structural reason Gate A remains closed.
- **Evidence**: C-303; DISCUSSION_DRAFT.md §5
- **Uncertainty**: This is a fundamental identifiability problem, not a data gap that can be filled with more of the same measurements.

**Q29: What experiment would be most informative?**
- **Answer**: A dual-site recording — somatic whole-cell patch + focal dendritic/axonal patch at a specific PSI contact, during direct PSI stimulation. This would directly measure spatial voltage transfer (opening Gate A) and provide a native synaptic conductance baseline for Dα7 work (opening Gate B).
- **Evidence**: C-401, C-501; METHODS_DRAFT.md §10, `missing_evidence.md` M-02
- **Uncertainty**: This is a technically demanding experiment on small processes; Yang et al. 2016 ASAP2f imaging is the realistic first-pass fallback.

**Q30: Could you at least bound the capacitance?**
- **Answer**: No — the two values (43 pF, 127 pF) are both published native measurements. Without knowing which preparation/method is correct, bounding would require introducing a new assumption, which violates the project's provenance policy.
- **Evidence**: C-303
- **Uncertainty**: The project's principle is to preserve conflicts, not resolve them by fiat.

---

## 12. Oral Explanation Practice

### 30-second explanation (general scientific audience)

> "We studied a fruit fly escape circuit: when the fly sees a looming object, a giant fiber neuron triggers a jump via one pathway and a wing-fold via another pathway through PSI to MN5. We used the complete male fly brain connectome to map exactly where PSI connects to MN5 — we found 43 synaptic contacts, all on MN5's axon. Then we asked: what constraints do we actually have for modeling this synapse? We found strong data for some neuron properties but a conflict on others, and we found that two key quantities — how much signal reaches the soma, and the Dα7 receptor's contribution — simply haven't been measured. So we built a transparent sensitivity model under explicit assumptions, and we built software that refuses to pretend unknown quantities are known."

### Two-minute explanation (neuroscientist)

> "The Drosophila Giant Fiber System controls escape behavior. GF activates TTMn (jump) and PSI→MN5 (wing downstroke). We focused on the PSI→MN5 chemical synapse. Using MaleCNS v1.0 from Berg et al. 2026, we identified 43 contacts at minconf 0.5 — 17 left (802401→801970) and 26 right (903327→801295). All compartment_post labels are 'axon', corroborated by two independent dataset files.
>
> The critical limitation is that we cannot compute voltage transfer from contact to soma. MN5 morphologies lack a soma node (all kind=1 absent), and the two native capacitance measurements conflict by ~3× (43 vs 127 pF), leaving Ra, Rm, and Cm undetermined. No Drosophila-specific axial resistivity exists — only Manduca data, which is wrong species.
>
> We designed a provenance-aware framework that enforces five evidence classes (NEM native measurement, AM anatomical, LDP literature-derived, MDE model-derived, MA model assumption) and raises exceptions when blocked parameters are requested. Two gates are closed by design: PSI→MN5 spatial voltage transfer (no native measurement; literature search exhausted) and Dα7 conductance (no native data at PSI terminals or MN5 axons; Drosophila lacks Kir7.1).
>
> Under these constraints, we ran a 15,528-row sensitivity analysis: contact-local patches, an abstract cable bridge (112.5×2 µm from Augustin 2019 GFS geometry), and a Dα7 effective-conductance sweep. All outputs are model-derived — numerical reachability, not biological validation. The 4.71 mV EPSP calibration fits gPSI from 3.58–42.73 nS, but this is fitting an assumption, not measuring a quantity.
>
> Software tests pass (1,773 passed, 2 skipped) — but this is code verification, not biological validation."

### Five-minute explanation (prospective reviewer or collaborator)

> "**[Opening — motivation]** The Drosophila Giant Fiber System is a canonical escape circuit. GF mediates the jump response via TTMn and the flight response via PSI→MN5→DLM. Understanding how visual threat becomes motor command requires knowing the PSI→MN5 synapse's properties. This is a well-studied circuit, but the specific quantitative question of synaptic transfer from PSI contacts to the MN5 soma has not been directly measured.
>
> **[Anatomical evidence — the strong part]** We used the MaleCNS v1.0 connectome (Berg et al. 2026, Cell, DOI 10.1016/j.cell.2026.08.015) to conduct a provenance-controlled anatomical audit. At minimum confidence 0.5, we found exactly 43 PSI→MN5 contacts — 17 for the left pairing (802401→801970) and 26 for the right (903327→801295). This count is corroborated by two independent dataset files: the synapse-partners Feather table and the official annotation layer. All 43 contacts have compartment_post='axon' — PSI releases onto MN5's axon, not its dendrites near the soma.
>
> **[The architectural barrier — why we can't compute voltage transfer]** To convert this anatomy into voltage transfer, we would need: (1) the contact-to-soma path, (2) axial resistivity, (3) specific membrane resistance, (4) membrane capacitance. We have none of these for MN5. The SWC skeletons have zero soma nodes — the soma is represented only by a proximal dilation near somaLocation, which we treat as a proxy under explicit assumption. The two native capacitance measurements conflict by ~2.95× (43 vs 127 pF). No Drosophila axial resistivity exists — only Manduca, which is wrong species.
>
> **[Our methodological contribution — the framework]** Rather than silently defaulting to generic parameters, we built a ParameterSet that raises BlockedParameterError whenever a blocked parameter is requested. This enforces five evidence classes and two authorization gates. Gate A (PSI→MN5 spatial voltage transfer) is NOT AUTHORIZED — no native measurement exists, the literature search is exhausted, and the geometry alone is insufficient. Gate B (Dα7 conductance) is NOT AUTHORIZED — no native Dα7 at PSI terminals or MN5 axons, and Drosophila lacks the Kir7.1 orthologue for the vertebrate α7→Kir coupling mechanism.
>
> **[What the model produces]** Under these constraints, we ran a deterministic sensitivity analysis: 15,528 rows covering contact-local patches (9,288), an abstract cable bridge (2,880), a Dα7 effective-conductance sweep (2,880), and EPSP calibration (480). At the nominal GFS-bridge point, the model-derived somatic peak was 1.108 mV (using 43 pF) or 0.510 mV (using 127 pF). Fitted gPSI ranged 3.58–42.73 nS. Local-to-somatic peak ratio: 0.085/0.517/0.892. All of these are explicitly tagged model-derived estimates — numerical reachability, not biological validation.
>
> **[Why we're honest about limitations]** We preserve all conflicts without choosing a winner: capacitance (C-01), gap-junction units (C-02, µS vs nS, 1000×), chemical conductance (C-03, 1000×). The test suite passes (1,773 passed, 2 skipped) — but this is software validation, not biological validation. The Feather input has no recorded expected checksum (now computed as 959d8ef4… during our verification pass, but the staging command is still undocumented).
>
> **[What's next]** The path forward is experimental: a dual-site recording (somatic whole-cell + focal dendritic/axonal patch at identified contacts) during direct PSI stimulation, combined with pharmacological conductance series and Dα7 manipulation. This would directly test spatial transfer (Gate A) and establish native conductance (Gate B). More model tuning would not resolve the fundamental identifiability gap.
>
> **[Contribution]** The value of this work is the methodology: a provenance-aware framework that prevents assumption-bounded outputs from being misread as native measurements. We report what is known, what is unknown, and what cannot be computed — and we built software that enforces those boundaries."

---

## 13. Self-Test

### Short-Answer Questions (20)

1. What are the four body IDs for PSI and MN5 in the MaleCNS v1.0 dataset?
2. How many PSI→MN5 contacts are recorded at minimum confidence 0.5, and how are they split between left and right?
3. What is the `compartment_post` label for all 43 contacts, and what does it actually mean?
4. What is the exact SHA-256 checksum computed for the MaleCNS synapse-partner Feather file?
5. What are the two native MN5 capacitance values in conflict (C-01), and what are their sample sizes or sources?
6. What is Gate A, and why is it NOT AUTHORIZED?
7. What is Gate B, and why is it NOT AUTHORIZED?
8. How many evidence classes does the framework enforce, and what are they?
9. What is the size of the sensitivity analysis CSV, and how is it decomposed?
10. What is the abstract cable bridge geometry (length and diameter), and its source?
11. What are the model-derived somatic peak values at the nominal GFS-bridge point for C-01 variants A and B?
12. What is the local-to-somatic peak ratio range (min/median/max)?
13. What are the three native MN5 measurements the reduced model admits?
14. What is the 4.71 mV EPSP and how is it used in the model?
15. What does `kind=1` mean in SWC format, and how many are found in the MN5/PSI skeletons?
16. What is the source of the GFS gap-junction conductance discrepancy (C-02)?
17. What is the source of the PSI→DLMn chemical conductance discrepancy (C-03)?
18. What is the test count, and is it claimed as freshly reproduced?
19. What experiment does the manuscript propose as the resolving experiment for Gate A?
20. What are the four gap-junction conflicts, and how many parameters are in the frozen inventory?

### Multiple-Choice Questions (10)

1. Which journal published the MaleCNS v1.0 connectome?
   A) eLife  B) Cell  C) Nature  D) Neuron

2. What does minconf 0.5 mean?
   A) 50% of contacts are missing  B) Minimum confidence threshold  C) 0.5 µm spatial resolution  D) 50% of neurons are traced

3. The SWC `kind` column in MaleCNS is:
   A) Biologically assigned (axon/dendrite/soma)  B) Format-defined only (semantics undefined by source)  C) Auto-generated from mesh geometry  D) Manually curated per skeleton

4. The reduced MN5 model has:
   A) Full passive cable dynamics with leak  B) Threshold-only abstraction with no leak  C) Active conductances from Dα7  D) Cable parameters from Manduca

5. The Dα7 effective conductance sweep varies g_Dα7 over what range?
   A) 0.1–10 nS  B) 0.01–1000 nS  C) 1–100 nS  D) Not swept (blocked)

6. Figure 8 (reproducibility) currently is:
   A) Fully generated with all data  B) A stub pending hand-authoring  C) Missing entirely  D) Replaced by Figure 5

7. Which citation has the DOI `10.1016/j.cell.2026.08.015`?
   A) Augustin et al. 2019  B) Fayyazuddin et al. 2006  C) Berg et al. 2026  D) Ryglewski & Duch 2009

8. What is the GFS bridge length used in the model?
   A) 100 µm  B) 112.5 µm  C) 150 µm  D) 2 µm

9. The manuscript's stated test command excludes which file:
   A) test_diagnostics.py  B) test_malecns_*.py  C) test_mn5_*.py  D) No exclusion

10. Figures 7 and 8 are currently:
    A) Fully generated SVG diagrams  B) Stubs pending hand-authoring  C) Missing  D) Data tables only

### Figure/Table Interpretation Questions (5)

1. In Figure 3 (contact mapping), what is the difference in height between the two bars, and what does this represent?

2. In Figure 4 (compartment annotations), what proportion of compartment_pre labels are "unknown," and on which body?

3. In Figure 6 (sensitivity), what do the two colored bars (A and B) at the bottom represent, and why are both shown?

4. In Table R-3 (capability surface), which capabilities are BLOCKED and what gates do they correspond to?

5. In Figure 5 (two-gate model), what is the critical distinction between the "Contact-local patch" panel and the "Abstract cable bridge" panel?

---

## Answer Key

### Short-Answer Answers

1. PSI: 802401 (left), 903327 (right); MN5: 801970 (left), 801295 (right) [C-101]

2. 43 contacts total: 17 left (802401→801970) + 26 right (903327→801295) [C-102]

3. All 43 are labeled `compartment_post = axon`. This is a **dataset annotation** from the MaleCNS annotation layer (neuroglancer_annotations_v1), not an electrophysiological measurement. It marks where the contact is on the postsynaptic morphology, but does not establish voltage transfer [C-103]

4. `959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07` (6,777,179,098 bytes ≈ 6.78 GB, computed 2026-10-09)

5. 43 ± 2 pF (n=22, Fayyazuddin et al. 2006) vs 127 ± 16 pF (Ryglewski & Duch 2009); both retained, no winner chosen [C-303]

6. Gate A = PSI→MN5 spatial voltage transfer. NOT AUTHORIZED because: no Drosophila Ra, no Rm, unresolved Cm, no soma node → no cable equation solvable → no voltage transfer computable [C-401]

7. Gate B = Dα7 biological conductance. NOT AUTHORIZED because: no native Dα7 at PSI terminals or MN5 axons, no native single-channel conductance, Drosophila lacks Kir7.1 orthologue for α7→Kir coupling [C-501]

8. Five classes: `NEM` (native experimental measurement), `AM` (anatomical measurement), `LDP` (literature-derived parameter), `MDE` (model-derived estimate), `MA` (model assumption). Enforced in `model_framework.py:ModelProvenance` and `malecns_ingest.py:EvidenceClass` (lines 87-98)

9. 15,528 rows = 9,288 contact-local + 2,880 abstract transfer + 2,880 Dα7 sweep + 480 calibration [C-601]

10. Length 112.5 µm (100 µm DLMn dendrite + 12.5 µm PSI input from Augustin et al. 2019); diameter 2 µm [C-402]

11. Variant A (43 pF): 1.108 mV; Variant B (127 pF): 0.510 mV [C-303]

12. 0.085 / 0.517 / 0.892 (min / median / max) [C-402]

13. Resting potential (−67.8 mV), spike threshold (−24.1 mV), AP amplitude (+45.5 mV) — all from Ryglewski, Kilo & Duch 2014 [C-301]

14. The 4.71 mV somatic EPSP recorded under GF stimulation (not direct PSI stimulation) — used only as a calibration target for fitting gPSI, explicitly NOT a PSI-specific measurement [C-304]

15. `kind=1` = Soma in SWC v1.0.0 spec. Zero found across all 9 MN5/PSI skeletons — the soma region is represented only by a `kind=2` proximal dilation as a proxy [C-201, C-202]

16. C-02: Augustin et al. 2019 Table 1 reports 135 µS (young) / 34.5 µS (old); `gap2.mod` executes 135 nS / 34.5 nS — exactly 1000× [C-303]

17. C-03: Augustin et al. 2019 reports 80 µS; executed value is 0.08 µS — exactly 1000× [C-303]

18. 1,773 passed / 2 skipped. NOT freshly reproduced — inherited from `validation/full_suite_report.md` [C-602]

19. Dual-site recording: somatic whole-cell patch + focal dendritic/axonal patch at identified contact, during direct PSI stimulation [C-401]

20. Four conflicts (C-01, C-02, C-03, C-09) — note C-04/C-09 are premise corrections. The frozen inventory has 108 parameters [C-303]

### Multiple-Choice Answers

1. **B** (Cell)
2. **B** (Minimum confidence threshold)
3. **B** (Format-defined only, semantics undefined by source)
4. **B** (Threshold-only abstraction with no leak)
5. **B** (0.01–1000 nS)
6. **B** (Stub pending hand-authoring)
7. **C** (Berg et al. 2026)
8. **B** (112.5 µm)
9. **A** (test_diagnostics.py)
10. **B** (Stubs pending hand-authoring)

### Figure/Table Interpretation Answers

1. The right bar (26 contacts) is 56% taller than the left (17 contacts), representing 56% more contacts on the right pairing (903327→801295 vs 802401→801970) at minconf 0.5 [C-102].

2. 5 of 43 (11.6%) compartment_pre labels are "unknown," all on body 801295 (right MN5) [C-103]. In Figure 4's visualization, these appear as the gray bar.

3. The two bars represent C-01 capacitance variants: A (43 pF, red) and B (127 pF, orange). Both are shown because the manuscript refuses to choose a winner — the conflict is preserved rather than resolved [C-303].

4. BLOCKED capabilities: PSI→MN5 spatial voltage transfer (Gate A) and Dα7 receptor conductance (Gate B). Both raise exceptions when requested; no code path may claim them as measured [C-401, C-501].

5. The "Contact-local patch" panel uses actual contact geometry projected to SWC nodes (A = 2πrℓ, with real node radius and edge length). The "Abstract cable bridge" panel uses a uniform 112.5×2 µm cable derived from Augustin 2019 GFS geometry — NOT traced onto any MaleCNS SWC. The critical distinction: the patch is contact-specific but assumption-laden; the bridge is abstract geometry from published precedent, with no per-contact anatomical mapping [C-402, C-201].

---

## Appendix: Files Inspected

The following files were directly read during preparation of this guide:

- `paper/MANUSCRIPT_OUTLINE.md` (complete, 137 lines)
- `paper/CLAIM_EVIDENCE_MAP.md` (complete, 241 lines)
- `paper/INTRODUCTION_DRAFT.md` (complete, 62 lines)
- `paper/METHODS_DRAFT.md` (complete, 195 lines)
- `paper/RESULTS_DRAFT.md` (complete, 180 lines)
- `paper/DISCUSSION_DRAFT.md` (complete, 125 lines)
- `paper/MANUSCRIPT_CONSISTENCY_AUDIT.md` (complete, 178 lines)
- `paper/FIGURE_TABLE_MANIFEST.md` (complete, 147 lines)
- `paper/SUBMISSION_READINESS_REPORT.md` (updated 2026-10-09)
- `paper/REFERENCES.bib` (complete, 204 lines)
- `paper/README.md` (complete, 42 lines)
- `paper/claim_evidence_matrix.csv` (complete, 9 rows)
- All 8 SVG figures (Figure 1, 2, 3, 4, 5, 6, 7, 8)
- All 4 tables (R1, R2, R3, R4)
- `paper/figures/FIGURE_PLAN.md` (complete, 16 lines)
- `research/source_registry.md` (complete, 303 lines)
- `research/final_anatomy_audit.md` (referenced via consistency audit)
- `research/model_input_freeze.md` (referenced via claims)
- `research/missing_evidence.md` (referenced via claims)
- `research/conflicts.md` (referenced via claims)
- `research_archive/EXTERNAL_DATA_REPRODUCIBILITY.md` (complete, 241→249 lines)
- `research_archive/MALECNS_PUBLICATION_AUDIT.md` (complete, 26 lines)
- `research_archive/REPRODUCIBILITY_GAPS.md`
- `data/README.md` (complete, 47 lines)
- `AGENTS.md` (repository-level)
- `biological_brain/malecns_ingest.py` (lines 1-50, 87-98, key functions referenced)
- DOI verification: doi.org/10.1016/j.cell.2026.08.015 (webfetch)

**Missing/unavailable materials identified**:
1. The Feather staging procedure is NOT DOCUMENTED — no repository-authored download command exists
2. The MANUSCRIPT_CONSISTENCY_AUDIT.md line 8 mentions "DOI: VERIFY_REQUIRED" for Berg citation — this was updated during the 2026-10-09 verification pass

**Completed this correction pass**:
- Abstract draft created: `paper/ABSTRACT_DRAFT.md` (249 words)
- Figures 7 and 8 fully authored from verified data (capability surface, reproducibility overview)
- Evidence-class count corrected: six → five across all paper files (README, evidence_classification, OUTLINE, READING_GUIDE, CONSISTENCY_AUDIT, CLAIM_EVIDENCE_MATRIX, FIGURE_PLAN, METHODS_DRAFT)
- Bibliography completed: all `references.bib` entries now have verified titles and metadata (Phase 2 done)
