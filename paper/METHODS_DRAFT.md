# Materials and Methods

This draft documents only methods that are actually implemented and evidenced in the repository. Every statement is grounded in source code, configuration, frozen research artifacts, or primary sources that were explicitly read. Methods are marked native experimental measurement (NEM), anatomical measurement (AM), literature-derived passive parameter (LDP), model-derived estimate (MDE), or model assumption (MA) as appropriate. Repository-execution facts and validation fixtures are tracked separately by the validation package; they are not biological evidence classes. The two scientific gates — **PSI→MN5 spatial voltage transfer: NOT AUTHORIZED** and **Dα7 biological conductance: NOT AUTHORIZED** — are enforced by code paths that raise exceptions rather than degrade; this is the mechanism by which interpretation is constrained `[C-101–C-701]`.

---

## 1. Study design and scope

The study asks four questions and answers each only where the frozen evidence base permits: (1) what native measurements of the PSI→MN5 / MN5 system exist and are admissible; (2) what the MaleCNS v1.0 connectome establishes about PSI→MN5 anatomy; (3) what a conditional, assumption-bounded model can say; (4) which native quantities remain unmeasured and what experiment would resolve each `[C-401, C-501]`.

Three evidence classes are distinguished at the architecture level and never collapsed: **native experimental measurements** (`NEM`/`NATIVE_EXPERIMENTAL_MEASUREMENT`), **literature-derived values** (`LDP`/`LITERATURE_DERIVED_PASSIVE_PARAMETER`), **anatomical/connectomic data** (`AM`/`ANATOMICAL_MEASUREMENT`), **model-derived estimates** (`MDE`/`MODEL_DERIVED_ESTIMATE`), and **assumptions** (`MA`/`MODEL_ASSUMPTION`). The internal 8-category `ParameterProvenance` is bridged to the five-class freeze taxonomy by an explicit, refusal-on-ambiguity function — values whose freeze class is ambiguous are **not auto-classified** `[C-301, C-302, C-303, C-401]`.

Two quantities are **blocked at the framework level**: any code path requesting native PSI→MN5 spatial voltage transfer raises `BiologicalTransferNotAuthorized` (`malecns_ingest.py:require_biological_transfer_authorization`) `[C-401]`; any path requesting native Dα7 conductance raises `BlockedParameterError` (`model_framework.py:require_dalpha7_gate`) `[C-501]`.

> **Section status**: all claims below are supported by code or frozen artifacts.

---

## 2. Data sources and provenance

**MaleCNS v1.0** is the connectomic source. It is licensed CC-BY; citation Berg et al. 2026 (Cell, doi:10.1016/j.cell.2026.08.015). The synapse-pair layer is streamed from `male-cns:v1.0` `syn-partners-male-cns-v1.0-minconf-0.5.feather` (~6.8 GB, ~8 nm voxel units); body-identity and per-synapse annotation tables are read from the `male-cns-v1.0-synapses-precomputed` layer (`neuroglancer_annotations_v1`) `[C-101, C-102]`. The minimum-confidence floor `0.5` is **applied by the source and encoded in file names**; this module records it but never re-filters `[C-101]` (`malecns_ingest.py:SOURCE_MINCONF`, `MaleCNSSynapses.extract`).

The **frozen parameter inventory** `research/model_input_freeze.csv` (108 parameters; 40 SAFE, 31 ASSUMPTION-only, 37 BLOCKED, 15 unresolved conflicts preserved) is the single source for all model inputs `[C-301, C-303]`. It is loaded into a `ParameterSet` that refuses to yield any `BLOCKED` value `[C-401, C-501]` (`model_framework.py:load_frozen_parameters`, `ParameterSet.require`).

**Primary references** used as measured constraints:
- Ryglewski, Kilo & Duch 2014 (native MN5 resting potential, threshold, AP amplitude, input resistance) `[C-301, C-302]`
- Fayyazuddin et al. 2006 (Dα7, 4.71 mV EPSP, n=10 under GF stimulation) `[C-304, C-502]`
- Augustin, Zylbertal & Partridge 2019 (ModelDB 245415 GFS cable-model geometry precedent, doi:10.1523/ENEURO.0423-18.2019) `[C-402]`
- Lansdell, Collins, Goodchild & Millar 2012 (recombinant Dα7 homomeric channel, EC50 6.7 ± 1.7 µM ACh, Hill 1.0 ± 0.3, n=4, −60 mV, max current 86 nA; doi:10.1186/1471-2202-13-73) `[C-503]`

> **Limitation**: the 4.71 mV EPSP is recorded under GF stimulation, so it is a comparison/calibration target, not a PSI-evoked measurement `[C-304]`.

---

## 3. Mesh format, parsing, and integrity validation

MaleCNS `.ngmesh` files are parsed by a reverse-engineered, byte-budget-validated layout (`malecns_ingest.py:parse_male_ngmesh`):

- **Offset 0**: `uint32` little-endian — vertex count N
- **Offset 4**: N × `float32` (x, y, z) — raw vertices
- **After vertices**: 3F × `uint32` — triangle indices (face count F is implied by file size, not stored)

The parser **rejects** any file where the consumption budget `4 + 12·N + 12·F` does not exactly reproduce the file size, where any triangle index falls outside `[0, N−1]`, or where the size is inconsistent with the float32/uint32 record structure `[C-204]`. Vertices are raw **nanometres** in Male CNS EM coordinate space `[C-202]`. A SHA-256 digest is recorded per mesh, but the synapse-pair Feather has **no recorded expected checksum** (documented limitation) `[C-701]`.

Mesh–SWC registration is **confirmed numerically**: `check_male_mesh_matches_swc` asserts the SWC bounding box scaled by 8 (`MESH_TO_SWC_SCALE = 8.0`) sits within the mesh bounding box (raw units), i.e. `swc_voxel × 8 = mesh_nm` `[C-202]`. The mirrored MaleCNS SWC set (1 nm units) fails this check and is therefore never substitutable `[C-202]`.

> **Limitation**: the mesh is not a closed surface (462k+ boundary edges, 2.6k+ components; largest component holds only 2.8% of area) and carries **no compartment names on components** `[C-204]`.

---

## 4. Coordinate systems and registration

Two frames are maintained and never conflated:
- **SWC coordinates**: raw MaleCNS EM 8 nm voxel units (`COORD_UNIT_NM = 8.0`); frame `FRAME_EM_8NM`
- **Mesh coordinates**: raw nanometres in Male CNS EM space; frame `MESH_COORDINATE_SYSTEM`

Conversion is `swc_voxel × 8 = mesh_nm` (`malecns_ingest.py:MESH_TO_SWC_SCALE`) `[C-202]`. The conversion factor is **derived only from plausibility and the documented convention**, not from a per-mesh calibration `[C-201]`.

**Frame validation** (`validate_frame`): every post-synaptic coordinate from the synapse layer must fall inside the SWC bounding box expressed in raw SWC units; a mismatch raises `CoordinateFrameError` (`malecns_ingest.py:validate_frame`). This is the invariant that distinguishes the 8 nm SWCs from the 1 nm mirrored set `[C-202]`.

> **Limitation**: `somaLocation` is a point annotation, not a surface; `tosomaLocation` and `rootSide` columns are unpopulated `[C-202]`. The SWC root is "not particularly significant" per neuPrint documentation, so root-referenced distances are direct measurements of the file, not documented format properties `[C-201]`.

---

## 5. SWC morphology representation and compartment-label limitations

SWCs are read by `SkeletonGeometry.from_swc` (`malecns_ingest.py`), which preserves the 7-field SWC1 line format (`index, kind, x, y, z, radius, parent`) and skips comments/blank lines `[C-203]`. The `kind` (Type) column carries **format semantics only**: codes are defined by the SWC v1.0.0 spec (PMC10654402) — 0 = Undefined, 1 = Soma, 2 = Axon — but MaleCNS documents **nothing** about how its Type column is populated; the official neuPrint reader discards `node_type` (`malecns_ingest.py:MALECNS_NODE_TYPE_BIOLOGY = "UNDEFINED IN AVAILABLE SOURCE"`) `[C-203]`.

Observed for all 9 MN5/PSI skeletons: `kind=0` ≈ 93%, `kind=2` ≈ 7%, `kind=1` = **0** `[C-202, C-203]`. `swc_type_semantics` reports these counts explicitly with an `interpretation_guard` stating counts are FORMAT CODE counts, not biological axon/dendrite/soma counts `[C-203]`.

> **Permitted**: "MaleCNS documents no assignment procedure for the Type column, so the biological compartment corresponding to `kind=2` is undefined in available source." `[C-203]`

The `compartment_post` annotation column is a **different field with a different provenance** and is reported verbatim (`axon` for all 43 contacts) `[C-103]` (`retrieve_malecns_compartment_post.py`, artifact `research/artifacts/malecns_compartment_post_psi_mn5.csv`). The synapse layer and the Type column are deliberately **not cross-interpreted** `[C-203]`.

> **Limitation**: no soma node (`kind=1`) exists; the soma region is represented only by a proximal dilation near `somaLocation`, which is **not** treated as a soma `[C-202]`.

---

## 6. Geometry and topology analysis

Geometry is computed on raw, unscaled coordinates via `SkeletonGeometry`:
- `bbox_raw()` / `bbox_um()` — bounding box in raw EM units vs. micrometres
- `to_um(v) = v × 8 / 1000` — unit conversion
- `distance(a, b)` — Euclidean distance in raw units
- `path_to_root(node_index)` — geometric path length (sum of edge distances) from a node to its tree root, returned in micrometres `[C-201]`
- `nearest_node(xyz)` — nearest SWC node by Euclidean distance over raw coordinates; **no compartment classification is made** `[C-201]`

**Contact→root traversal** (`contact_to_root_report`) projects each of the 43 post-synaptic coordinates to its nearest SWC node and traces the geometric path to the single tree root. The result is tagged `MODEL_DERIVED_ESTIMATE` because it is reconstructed-morphology geometry plus an explicit node-assignment rule — **not** an experimentally measured electrical distance `[C-201]`. The root is the stalk origin, **not a soma** `[C-201]`.

**Clustering** (`clustering_report`) reports geometry-only contact statistics (3-D extent, nearest-neighbour distances, distribution by `primary_post`). Contacts are **never collapsed**; ordering along the nerve is not established `[C-102]`.

> **Limitation**: path length is geometric only and carries no electrotonic meaning; no length constant, space constant, attenuation, or transfer resistance is computed `[C-201, C-401]`.

---

## 7. PSI contact association methods

Contacts are extracted from the `syn-partners` Feather by `MaleCNSSynapses.extract` (`malecns_ingest.py`): the streaming reader (`pyarrow.ipc`) iterates record batches, selects rows where `body_pre ∈ {802401, 903327}` and `body_post ∈ {801970, 801295}`, and emits `SynapticContact` records carrying raw pre/post coordinates (x, y, z, in 8 nm units), `conf_pre`/`conf_post`, and `primary_post` `[C-101, C-102]`. Coordinates pass through raw — no rescaling, rounding, or transformation `[C-202]`.

Each contact is validated (`SynapticContact.validate`) for body identity and for both confidence values being ≥ `SOURCE_MINCONF` (0.5) `[C-101]`. A duplicate key (body, body, post-coordinate) raises; the contact census is computed from the records themselves via an independent `Counter`, never copied from prose `[C-102]`.

The official `compartment_post` enum is read directly from the annotation layer's `info` (`["unknown","axon","dendrite","linker","cell-body-fiber"]`) by `retrieve_malecns_compartment_post.py`; per-synapse labels are exported to `research/artifacts/malecns_compartment_post_psi_mn5.csv` with exact integer coordinate matching `[C-103]`.

> **Limitation**: `compartment_post` is a dataset annotation, not an electrophysiological measurement `[C-103]`. It tells us where contacts are, not how much signal reaches the soma `[C-103]`.

---

## 8. Morphological path calculations

Contact→root path lengths are geometric SWC edge sums in micrometres via `path_to_root` `[C-201]`. The range is 169.2–267.8 µm (801970) and 169.2–230.6 µm (801295); contact→`somaLocation` straight-line distance is 110.3–172.9 µm (801970) and 112.3–169.3 µm (801295) `[C-201]`.

Three geometric quantities are kept strictly separate and never substituted: (a) contact→mesh surface distance, (b) SWC-root path length, (c) soma-proxy graph path `[C-201]`. The soma-proxy tree path (154.1–241.6 µm) is computed to the `kind=2` proximal dilation **only under the assumption** that this node stands in for the soma `[C-202]`; calling the proxy a soma is a `MA` assumption, and the path is `MDE` on that assumption `[C-201]`.

**The contact-to-soma graph path is UNRESOLVED**: zero `kind=1` nodes exist across all 9 skeletons, so no anatomically reconstructed path to a labelled soma can be formed for any of the 43 contacts `[C-201]`. Straight-line distance is never presented as a path length `[C-201]`.

> **Limitation**: this is the M-02 blocker. A per-contact anatomical somatic path cannot be established from the available MaleCNS SWCs `[C-201, C-401]`.

---

## 9. Reduced MN5 model design

The reduced model is `biological_brain/reduced_mn5.py` (`ReducedMN5Simulator`) `[C-602]`. It is a **threshold-only abstraction** with no leak, no compartment, no synapse, no cable model, and no hidden parameters `[C-602]`. It admits **exactly three** native measurements, all somatic whole-cell recordings (Ryglewski, Kilo & Duch 2014): resting potential −67.8 mV (n=13), spike threshold −24.1 mV (n=11), AP amplitude +45.5 mV (n=13) `[C-301]`. These are obtained via `ParameterSet.require_uncontested`, which additionally refuses contested values — so the unresolved C-01 capacitance is never silently consumed `[C-303]`.

A membrane time constant (τ_m) is **blocked** (`require_leak` raises `BlockedParameterError`); consequently the model has **no decay term** — voltage moves only when an explicitly software input moves it, and the model returns to rest only on a spike `[C-201, C-303]`. All other passive/cable quantities (Ra, Rm, Cm, g_pas, length constant, transfer resistance, input resistance as a cable parameter) are `BLOCKED` at the inventory level and raise if requested `[C-401]` (`model_framework.py:load_frozen_parameters`, `ParameterSet.require`).

Voltage is moved only by `apply_software_input`, which requires the marker `"SOFTWARE INPUT -- NOT A BIOLOGICAL MEASUREMENT"`; without it, `BiologicalClaimError` is raised `[C-602]`. Each emitted `SpikeEvent` is explicitly `is_measurement() → False`, `spike_shape_modelled() → False`, and `voltage_excursion_mv` (peak − from) is **not** the biological AP amplitude; the measured amplitude is echoed separately as `reference_ap_amplitude_mv` for comparison only `[C-301, C-601]`.

> **Limitation**: this is not a passive or cable model; it cannot reproduce an EPSP, compute attenuation, estimate native gPSI, or model Dα7 `[C-303, C-401, C-501]`. The 43 contacts are metadata only and play no role in its arithmetic `[C-601]`.

---

## 10. Exploratory parameter sensitivity

The sensitivity analysis is implemented in `research/scripts/analyze_mn5_two_gate_constraint_model.py` (`run_analysis`) `[C-601]`. It reads four inputs: (1) the audited contact map `research/mn5_compartment_post_swc_type_concordance.csv` (43 contacts, 17 left / 26 right), (2) the two cached official MaleCNS SWCs at paths `tempmdir/em_{body}.swc` with **pinned SHA-256 hashes** (`EXPECTED_SWC_SHA256` in the script), (3) the frozen parameter grids, (4) the published GFS DLMn geometry from Augustin et al. 2019 `[C-601, C-402]`.

Two analyses run:

**Contact-local single-patch analysis**: for each of 43 contacts, a cylindrical patch area `A = 2πrℓ` is formed from the selected SWC node's radius and the arithmetic mean length of its adjacent SWC edges; capacitance `Cpatch = A·Cm` and leak `gleak = A/Rm` (nS) are computed; a single-conductance voltage equation `Cpatch·dV/dt = −gleak(V−Vrest) + gPSI(t)(Esyn−V)` is integrated at `dt = 0.01 ms` for `15 ms` `[C-601]` (`analyze_mn5_two_gate_constraint_model.py:contact_local_peak`). Node Type tokens are preserved literally; **none is biologically interpreted** `[C-203]`.

**Abstract two-compartment somatic-transfer bridge** (`simulate_abstract_transfer`): a uniform cable of length `100 + 12.5 = 112.5 µm` and diameter `2 µm`, derived from published GFS DLMn geometry (dendrite 100 µm + PSI input 12.5 µm from the axon proximal end) `[C-402]` (`mn5_psi_mn5_final_constraint_model.md` §2 Layer D). **The bridge is not traced onto any MaleCNS SWC**; it does not assign an anatomical soma path to any contact `[C-402, C-201]`. The existing two-compartment equations are integrated at `dt = 0.01 ms` `[C-402]`.

Parameter grids: `Ra ∈ {30, 35.4, 90, 200, 400} Ω·cm`, `Cm ∈ {0.6, 1.0, 1.15, 2.6} µF/cm²`, `Rm ∈ {6, 10, 20, 26} kΩ·cm²`, `E_syn ∈ {−15, 0, +10} mV`, `gPSI ∈ {0.01, 0.1, 1, 10, 100, 1000} nS`, `E_Dα7 ∈ {−15, 0, +10} mV`, `g_Dα7,eff ∈ {0.01…1000} nS` `[C-402]`. The non-Dα7 abstract-transfer branch iterates the `PASSIVE_GRID` over Ra, Cm, and Rm with `E_syn ∈ {−15, 0, +10} mV` and `gPSI ∈ {0.01, 0.1, 1, 10, 100, 1000} nS`, yielding 2,880 runs per C-01 variant (A and B); the Dα7 sweep adds a second 2,880-run branch holding gPSI = 1 nS while sweeping `E_Dα7` and `g_Dα7,eff`. Both C-01 capacitance variants A/B are carried separately; both are reported but **neither is selected** `[C-303]`. Outputs are written to `mn5_psi_mn5_final_constraint_model_sensitivity.csv` (15,528 rows: 9,288 contact-local + 2,880 abstract + 2,880 Dα7 + 480 calibration) `[C-601]`.

**EPSP calibration** (`fit_g_psi_to_target`): fits `gPSI` within the existing 0.01–1000 nS exploratory range against the 4.71 mV comparison target; `gPSI` is reported as model-derived only, and numerical reach is explicitly **not** biological plausibility `[C-304, C-601]`.

> **Limitation**: the sweep is a deterministic grid, not a probability distribution or confidence interval `[C-601]`. Min/median/max describe sampled model outcomes only `[C-402]`. The Dα7 sweep (`g_Dα7,effective`) is a model assumption; recombinant oocyte currents are **not** converted to native conductance `[C-501, C-503]`.

---

## 11. Evidence classification and authorization gates

Every reported quantity carries exactly one of the five frozen provenance classes (`malecns_ingest.py:EvidenceClass`): `NATIVE_EXPERIMENTAL_MEASUREMENT`, `ANATOMICAL_MEASUREMENT`, `LITERATURE_DERIVED_PASSIVE_PARAMETER`, `MODEL_ASSUMPTION`, `MODEL_DERIVED_ESTIMATE` `[C-301, C-302]`. The `ParameterSet.require` method **raises** (`BlockedParameterError`) for any `BLOCKED` parameter rather than substituting a value `[C-401, C-501]`.

**Gate A — PSI→MN5 spatial voltage transfer: NOT AUTHORIZED.** Enforced by `malecns_ingest.py:require_biological_transfer_authorization()` (always raises) and `model_framework.py:require_spatial_transfer()` (always raises). The block rests on four unresolved premises: no MN5-specific axial resistivity (the only measured Drosophila motor-neuron Ra is larval aCC, 212.47 ± 3.69 Ω·cm; Manduca value adopted by assertion), no specific membrane resistance (Rm), an adjudicated whole-cell capacitance (C-01 contested), and no labelled soma node to close an anatomical path `[C-201, C-401]`.

**Gate B — Dα7 conductance: NOT AUTHORIZED.** Enforced by `model_framework.py:require_dalpha7_gate()` (always raises). The block rests on: no native Dα7 single-channel conductance / open probability / reversal / kinetics / density at PSI→MN5; no Dα7 imaging at PSI terminals or MN5 axons; and the absence in Drosophila of the Kir7.1/KCNJ13 orthologue that mediates vertebrate α7→Kir coupling `[C-501]`.

The gates are **evidence constraints on interpretation**, not assertions that the underlying biological quantities do not exist `[C-401, C-501]`. A model-authorized conditional analysis (the abstract bridge, the Dα7 effective-conductance sweep) is permitted to execute under declared assumptions, but its outputs remain model-derived `[C-402, C-503]`.

> **Unresolved conflicts preserved (no selection)**: C-01 (43 vs 127 pF), C-02 (gap-junction 135 µS table vs 135 nS executed, 1000×), C-03 (chemical conductance 80 µS vs 0.08 µS, 1000×) `[C-303]`. These are recorded in `model_input_freeze.md` and loaded as `BLOCKED`/`recorded_value` rows; no value is endorsed `[C-303]`.

---

## 12. Software testing and reproducibility

Tests verify code paths and invariants, **not** biological validity `[C-602]`. The test command is `python -m pytest tests/ -v --tb=short --ignore=tests/test_diagnostics.py` (per `AGENTS.md`) `[C-602]`.

The **reported** full-suite figure of **1,773 passed and 2 skipped** is inherited from an existing validation matrix (`validation/full_suite_report.md`) and was **not freshly reproduced** during Results-draft or Methods-draft writing `[C-602]`. Specific gates verified by test files include:
- `tests/test_malecns_anatomy_audit.py` — contact counts and pairings
- `tests/test_malecns_compartment.py` — annotation provenance
- `tests/test_malecns_contact_path.py` — unresolved contact→soma path
- `tests/test_mn5_two_gate_constraint_model.py` — sensitivity-row integrity and finite-output assertion
- `tests/test_mn5_spatial_transfer_gate_review.py` — gate-closed status
- `tests/test_parameter_adoption.py` — no blocked parameter is admitted as a value
- `tests/test_psi_mn5_optical_experiment_design_audit.py` / `tests/test_psi_mn5_reversal_experiment_audit.py` — genetic-access / reversal-potential absences `[C-101, C-303, C-401, C-501]`

> **Reproducibility limitations**: the synapse-pair Feather has **no recorded expected checksum**; the download/staging commands are **not documented**; and external-data license redistribution and author attribution remain **VERIFY_REQUIRED** per `research_archive/EXTERNAL_DATA_REPRODUCIBILITY.md` `[C-701]`. The two cached SWCs used by the sensitivity script are pinned by SHA-256 in the script itself `[C-601]`.

---

## Internal notes: linkage to planned figures and tables

The Methods here ground the following planned figure/table generation:
- **Figure 3** (contact mapping) ← §7 + artifact `malecns_compartment_post_psi_mn5.csv` `[C-102, C-103]`
- **Figure 4** (compartment annotations) ← §7 + `retrieve_malecns_compartment_post.py` `[C-103]`
- **Figure 5** (two-gate model) ← §10 + `analyze_mn5_two_gate_constraint_model.py` `[C-402, C-601]`
- **Figure 6** (sensitivity) ← §10 + `mn5_psi_mn5_final_constraint_model_sensitivity.csv` `[C-601]`
- **Table R-2** (mesh/registration) ← §3–§4 `[C-202, C-204]`
- **Table R-3** (native biophysics) ← §2 + `model_input_freeze.md` Section A `[C-301, C-302]`

No figures or tables are generated in this phase.

---

*Methods draft complete. Created at `paper/METHODS_DRAFT.md`. Production code, tests, research artifacts, the evidence map, outline, and Results draft were not modified; `fly_state.json` was not altered; no commit or push was performed; the full test suite was not rerun.*