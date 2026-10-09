# Results

This draft presents only findings that are supported by the repository's admissible evidence (native measurements, literature-derived values, anatomical/connectomic data, model-derived conditional outputs, and declared assumptions) and explicitly states what each result does *not* establish. Numerical values that conflict are preserved as conflicts rather than resolved by selection. Each substantive claim is tagged with its evidence-map claim ID `[C-nnn]`; permitted wording follows `paper/CLAIM_LANGUAGE_STANDARD.md`.

---

## 1. Data provenance and reconstruction inputs

PSI and MN5 are identified by their MaleCNS v1.0 body identifiers and VFB identifiers `[C-101]`. MN5 = `801970` (left; VFB `VFB_jrmc37jr`) and `801295` (right; VFB `VFB_jrmc37js`); PSI = `802401` (left) and `903327` (right) `[C-101]`. Both MN5 bodies are annotated `somaSide` L/R, `somaNeuromere` `T2`, `exitNerve` **PDMNa**, and share a group `[C-101]`.

**MN5 cell-type identity is textual, not inferred.** MN5 is the motoneuron that *"innervates the two most dorsal fibers of the dorsal longitudinal wing depressor muscle (DLM)"* — DLM fibers 5 and 6 — **contralateral** to its soma (Ryglewski & Duch 2009, verbatim) `[C-101]`. Provenance: `AM` (anatomical/connectomic observation from the official annotation table).

MaleCNS v1.0 is the source for both synapse counts and per-synapse annotations `[C-102, C-103]`. The synapse layer is read from `gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed` (neuroglancer_annotations_v1) `[C-103]`.

> **Section status**: all claims here are supported by the frozen MaleCNS metadata table.

*Figure/ table proposal*:
- **Table R-1** — Body ID, VFB ID, hemisphere, and cell-type text for PSI/MN5. *Source*: `final_anatomy_audit.md` Block A. *Exists*: No — generate from audit table.

---

## 2. PSI contact inventory and anatomical associations

At minimum confidence 0.5, MaleCNS v1.0 records **43** PSI→MN5 contacts: **17** for pairing `802401→801970` and **26** for `903327→801295` `[C-102]`. These counts are corroborated by two independent sources: the `syn-partners-male-cns-v1.0-minconf-0.5.feather` extraction and the official synapse annotation layer, which contains exactly 17 and 26 annotations for the respective pairings — a non-unique match raises `[C-102]`. Provenance: `AM`; the threshold **must always be quoted** `[C-102]`.

The official `compartment_post` annotation is **`axon` for all 43** contacts — 0 missing, 0 ambiguous, 0 unknown-post `[C-103]`. On body 801295, `compartment_pre` is `unknown` for 5 of the 26 contacts; this is preserved as-is, not imputed `[C-103]`. The post-compartment enum is `["unknown","axon","dendrite","linker","cell-body-fiber"]` `[C-103]`.

For context, across **all** of MN5's inputs the PSI→MN5 contacts fall exclusively in MN5's axonal compartment, while the bulk of MN5's total input is dendritic (801970: 452 axon / 9713 dendrite of 10,529; 801295: 2384 axon / 8787 dendrite of 11,260) — independently consistent with Fayyazuddin et al. 2006: *"the PSI bypasses the entire dendritic structure of MN5 and makes multiple synaptic contacts that span 50 μm and follow the axons out into the posterior dorsal motor nerve."* `[C-102, C-103]`

> **Permitted**: "The official `compartment_post` field is labeled `axon` for all 43 contacts. This reports the dataset annotation and does not establish electrophysiological compartment identity or voltage transfer." `[C-103]`

**Contact geometry** (surface-distance tier, 8 nm voxel domain): for 801970, contact→mesh surface ranges 8.55–51.70 nm (median 35.17); for 801295, 1.67–80.22 nm (median 26.97). All 43 contacts have a nearest surface triangle and index preserved; nearest-vertex distance is tracked separately and never substituted `[C-201]`. Three contacts (801970, indices 8/9/10) are **AMBIGUOUS** (margin ratios 1.110–1.172; runner-up is the same fragment in all three) — preserved, not broken by an invented threshold `[C-201]`.

*Figure/table proposal*:
- **Figure 3** — PSI→MN5 contact mapping at minconf 0.5 (43 contacts). *Source*: `final_anatomy_audit.md` Block C/D; artifact `research/artifacts/malecns_compartment_post_psi_mn5.csv`; generator `retrieve_malecns_compartment_post.py`. *Exists*: No — generate from pinned audit artifact.
- **Figure 4** — `compartment_post`/`compartment_pre` distribution. *Source*: same artifact. *Exists*: No.

> **Limitation**: contact counts and labels are dataset annotations; they establish where contacts are, not how much signal reaches the soma `[C-102, C-103]`.

---

## 3. MN5 morphology, mesh integrity, and coordinate registration

The MN5 mesh surface areas are 18,725.6 µm² (801970) and 19,665.4 µm² (801295), computed by cross product and Heron-validated to 2e-16 relative error `[C-204]`. An SWC frustum approximation gives 24,803.7 / 25,796.8 µm² — a **~24% difference** — but this is the difference between two different geometric domains (mesh surface vs. 1-D skeleton lateral area), not an error estimate, and the values are **not interchangeable** `[C-204]`.

The mesh is **not a closed surface**: 462,426 / 495,569 boundary edges and 2,238 / 2,267 non-manifold edges are present `[C-204]`. The mesh has **2,587 / 2,765 components**, and the largest component holds only **2.8% / 2.3%** of total area `[C-204]`. neuPrint attributes this fragmentation to *"artifacts in the underlying segmentation from which the skeletons were generated"* `[C-204]`. No mesh component carries an assigned biological compartment name `[C-204]`.

**Soma-region status**: no `kind=1` (soma) node exists in any of the 9 MN5/PSI skeletons `[C-202]`. A soma-region proximal dilation is present — radius **4.671 µm** on 801970, **5.376 µm** on 801295 — located 1.45–2.10 µm from `somaLocation`, with `somaLocation` itself only 3.87 / 3.50 µm from the nearest mesh surface `[C-202]`. `somaLocation` is a point annotation, not a surface; `tosomaLocation` and `rootSide` columns are unpopulated `[C-202]`.

> **Permitted**: "A soma-region proximal dilation is present but is a proxy node (`kind=2`) in the MaleCNS skeleton; calling it the soma is a model assumption not grounded in source annotation." `[C-202]`

**Coordinate / axis registration**: `somaLocation` falls inside the mesh bounding box and 3.87 / 3.50 µm from the nearest surface `[C-202]`. The SWC root↔`somaLocation` distance is 23.76 / 14.88 µm `[C-201]`. neuPrint states that for stored skeletons *"the root node … is not particularly significant"* `[C-201]` — so root-referenced path lengths remain measurements of the file, not documented file-format properties `[C-201]`.

> **Limitation**: mesh fragmentation and non-closed surfaces do not establish biological disconnection; no component is assigned a compartment name `[C-204]`. The soma-proxy is a geometric anchor, never promoted to a labelled soma `[C-202]`.

*Figure/table proposal*:
- **Table R-2** — Mesh integrity metrics and coordinate-registration distances. *Source*: `final_anatomy_audit.md` Block I/F. *Exists*: No.

---

## 4. Morphological path analysis and its limitations

Root-referenced paths use the geometric SWC root (the stalk origin), which is **not a soma** `[C-201]`. For the 43 contacts, the contact→SWC-root path length ranges 169.2–267.8 µm (801970) and 169.2–230.6 µm (801295); the contact→`somaLocation` straight-line distance ranges 110.3–172.9 µm (801970) and 112.3–169.3 µm (801295) `[C-201]`. Straight-line distance is **never presented as a path length** `[C-201]`.

The contact→soma **graph path is permanently UNRESOLVED**: no soma node exists in the skeletons, so no anatomically reconstructed contact-to-soma path can be established for any of the 43 contacts `[C-201]`. A soma-proxy tree path (154.1–241.6 µm) is computed, but only `MDE` on a `MA` proxy assumption — i.e., it rests on the assumption that the `kind=2` proximal node represents the soma `[C-201]`.

> **Permitted**: "The available MaleCNS SWCs contain no soma-labeled node, so an anatomically reconstructed contact-to-soma path could not be established." `[C-201]`

A straight-line soma distance is **not** an electrotonic distance `[C-201]`. The root↔soma distances are measurements of the file layout, not documented properties of the format `[C-201]`.

> **Section status**: path analysis is geometric only; this is the **M-02** blocker for native spatial voltage transfer `[C-201, C-401]`.

---

## 5. Electrophysiological evidence and model-input provenance

Native MN5 physiology is reported with provenance class `NEM` (native experimental measurement) and `LDP` (literature-derived). The strongest admissible native MN5 values are: resting potential **−67.8 ± 5.5 mV** (n=13), spike threshold **−24.1 ± 8.2 mV** (n=11), action-potential amplitude **+45.5 ± 8.6 mV** (n=13), AP time-to-peak **1.20 ± 0.33 ms**, AP 50% width **0.92 ± 0.25 ms**, and input resistance **102 ± 12 MΩ** (n=22) / **97 ± 31 MΩ** (n=52) — the two input-resistance sets are consistent `[C-301, C-302]`. Provenance: Ryglewski, Kilo & Duch 2014 `[C-301, C-302]`.

> **Permitted**: "Ryglewski, Kilo & Duch 2014 reported native MN5 resting potential −67.8 ± 5.5 mV (n=13), spike threshold −24.1 ± 8.2 mV (n=11), and AP amplitude +45.5 ± 8.6 mV (n=13); used only as measured constraints on a reduced model." `[C-301]`

**Capacitance conflict (C-01) — unresolved.** Two native whole-cell capacitance values for MN5 remain in conflict: **43 ± 2 pF** (n=22) and **127 ± 16 pF** `[C-303]`. Variant B's authors flag dendritic space-clamp as a capacitance error source; Herrera-Valdez et al. 2013 J Comput Neurosci 34:211 re-reports the same mean and SD. Per `model_input_freeze.md`, **both values are retained and no winner is chosen** — they are never averaged `[C-303]`.

> **Permitted**: "Two native MN5 whole-cell capacitance values remain in conflict (43 ± 2 pF vs 127 ± 16 pF); per the model-input freeze, both are retained and no value is preferred." `[C-303]`

The **4.71 ± 0.35 mV somatic EPSP** (n=10, current clamp at −74 mV) is recorded under **GF stimulation**; PSI was not directly stimulated and the distal amplitude is unreported `[C-304]`. It is used only as a comparison/calibration target.

> **Permitted**: "The reported 4.71 ± 0.35 mV somatic EPSP was recorded under GF stimulation. We use it only as a comparison/calibration target; it is not a PSI-specific EPSP." `[C-304]`

Several MN5 passive/cable quantities are **blocked / not measured in any accessible primary source**: MN5 axial resistivity (Ra), specific membrane resistance (Rm), membrane time constant, sodium/potassium conductance densities, and axonal length `[C-201, C-303]`. Where adopted from another species, the provenance is flagged `LDP` but explicitly wrong-species: e.g. Ra = 90 Ω·cm is *Manduca*-derived and adopted by assertion, while the only *measured* Drosophila motor-neuron Ra is 212.47 ± 3.69 Ω·cm (larval aCC) `[C-303]`.

> **Limitation**: these values constrain model context only; they are NOT native MN5 cable measurements `[C-303]`.

*Figure/table proposal*:
- **Table R-3** — Admissible native MN5 measurements with provenance class. *Source*: `model_input_freeze.md` Section A. *Exists*: No.

---

## 6. Exploratory model analysis and parameter sensitivity

The two-gate constrained analysis runs **15,528 rows** across a deterministic parameter grid covering (a) contact-local single-patch responses, (b) an abstract somatic-transfer bridge, (c) a Dα7 effective-conductance sensitivity sweep, and (d) EPSP calibration `[C-601]`. Source SWC hashes are preserved in `mn5_compartment_post_swc_type_concordance.csv` `[C-601]`.

**Contact-local analysis**: each of the 43 contacts is projected to a unique SWC node (43/43 verified mappings; all source Type tokens are `0`; one tied-segment case selects node 151) `[C-601]`. The local patch area is `A = 2πrℓ` from the node radius and the arithmetic mean of adjacent SWC edges. At illustrative settings (gPSI = 1 nS, E_syn = 0 mV, Cm = 1.15 µF/cm², Rm = 6 kΩ·cm²), the model-derived local peak depolarization ranged **40.13 / 61.09 / 67.71 mV** (801970) and **51.26 / 67.59 / 67.71 mV** (801295), min/median/max; the full sweep (Cm 0.6–2.6 µF/cm², Rm 6–26 kΩ·cm², E_syn −15 to +10 mV, gPSI 0.01–1000 nS) produced a local peak range of **0.58–77.80 mV**, dominated by free gPSI `[C-601]`.

> **Permitted**: "Under the stated model structure and parameter grid, the model produced X outcomes. These are model-derived outcomes conditional on the listed assumptions; they are not native physiological measurements." `[C-601]`

**Abstract somatic-transfer bridge**: a uniform two-compartment cable (112.5 µm length, 2 µm diameter) derived from published GFS DLMn geometry (DLMn dendrite 100 µm + PSI input 12.5 µm from the axon proximal end) `[C-402]`. This bridge is **not** traced onto the MaleCNS SWC and is **not** a per-contact anatomical somatic transfer `[C-402, C-201]`. Across the 2,880-row bridge sweep, the model-derived somatic-peak depolarization ranged **0.0028 / 1.81 / 67.08 mV** (min/median/max), with a peak local-to-somatic ratio (CSV field `local_to_somatic_peak_ratio`) of **0.085 / 0.517 / 0.892** `[C-402]`. At the nominal GFS-bridge point (Ra = 35.4 Ω·cm, Cm = 1.0 µF/cm², Rm = 6 kΩ·cm²), somatic peak was **1.108 mV (C-01 A)** and **0.510 mV (C-01 B)** `[C-402]`.

> **Permitted**: "We performed a model-authorized conditional analysis using [explicit abstract bridge/assumption set]. The analysis is permitted to execute under those assumptions; its outputs remain model-derived and do not establish native physiology." `[C-402]`

**Calibration to the published MN5 EPSP**: the 4.71 mV somatic EPSP is a GF-stimulated comparison target; PSI was not directly stimulated `[C-304]`. Fitted gPSI (a model-derived estimate of the conductance that would reproduce the 4.71 mV target under the stated assumptions) ranged **3.58–42.73 nS** across 480 settings; at the nominal GFS-bridge point the fitted values were 4.49 nS (C-01 A) and 10.16 nS (C-01 B) `[C-601]`.

> **Limitation**: numerical reachability of the EPSP target is NOT biological plausibility or validation `[C-601]`. Fitted conductance is model-derived, not a native measurement `[C-401, C-501]`.

**Dα7 effective-conductance sweep** (Gate B): over 2,880 runs, matched somatic peak change ranged 0.005–68.77 mV (median 5.73 mV); Dα7-enabled runs produced 456/2,880 threshold crossings, occurring only at the largest assumed conductances (184/480 at 100 nS; 272/480 at 1000 nS) `[C-503]`.

> **Permitted**: "Effective Dα7 conductance was swept as a model assumption; outputs are model-derived sensitivity, not native measurements." `[C-503]`
> **Prohibited**: "Native Dα7 conductance" — this is NOT AUTHORIZED `[C-501]`.

*Figure/table proposal*:
- **Figure 5** — Two-gate conditional model diagram. *Source*: `mn5_psi_mn5_final_constraint_model.md`. *Exists*: No.
- **Figure 6** — Sensitivity summary (model-derived min/median/max). *Source*: `mn5_psi_mn5_final_constraint_model_sensitivity.csv`; generator `analyze_mn5_two_gate_constraint_model.py`. *Exists*: No — generator script exists; CSV exists; figure not rendered.

---

## 7. Evidence gaps and the two closed scientific gates

**Gate A — PSI→MN5 spatial voltage transfer: NOT AUTHORIZED.** No native measurement of spatial voltage transfer to the soma exists in any Drosophila MN5 preparation; the literature search is exhausted (`missing_evidence.md` M-02; `research_done.md` Q-01) `[C-401]`. The only Drosophila transfer map is a *simulation* on *Manduca*-derived passive parameters (Ryglewski & Duch 2009 Fig 1B, current-transfer 0.2–1, explicitly disclaimed as not exact) `[C-401]`. The MaleCNS `compartment_post=`axon` annotation does not establish voltage transfer `[C-103, C-401]`, and no anatomically reconstructed contact-to-soma path exists `[C-201]`. The abstract-bridge transfer above is the conditional model's assumption-bounded output, **not** an experimental measurement `[C-401]`.

> **Permitted**: "No native measurement of PSI→MN5 spatial voltage transfer exists in the reviewed evidence; per the closed gate, this quantity is not reported as a native physiological finding." `[C-401]`

The resolving experiment is a dual-site recording (somatic whole-cell plus focal dendritic/axonal patch at the identified contact) during direct PSI stimulation; Yang et al. 2016's ASAP2f imaging is the realistic first-pass fallback (`missing_evidence.md` M-02) `[C-401]`.

**Gate B — Dα7 biological conductance: NOT AUTHORIZED.** No native Dα7 conductance, density, kinetics, or reversal potential at PSI→MN5 is measured `[C-501]`. The Dα7 recombinant channel-level data (Lansdell et al. 2012: EC50 6.7 ± 1.7 µM ACh, Hill 1.0 ± 0.3, n=4, max current 86 nA at −60 mV) supply **channel-level constraints only** and are **not** relabeled as native MN5 conductance `[C-501, C-503]`. Dα7 is not imaged at PSI terminals or MN5 axons in any primary source: localization is reported only as "NOT REPORTED" for both `[C-502]`. The Dα7 effective-conductance sweep is a model-derived sensitivity analysis `[C-503]`.

> **Permitted**: "No native PSI→MN5 Dα7 conductance exists in the reviewed evidence; recombinant Dα7 constraints supply channel-level precedent only." `[C-501]`

Gates are described as **evidence constraints** — the absence of qualifying primary evidence — not as proof that the underlying biological quantities do not exist `[C-401, C-501]`.

**Unresolved conflicts preserved (not selected)**: C-01 (43 vs 127 pF, ~2.95×), C-02 (gap-junction 135 µS table vs 135 nS executed, 1000×), C-03 (PSI→DLMn conductance 80 µS vs 0.08 µS, 1000×) `[C-303]`. These remain open per `model_input_freeze.md`; no value is endorsed `[C-303]`.

> **Section status**: gates closed and evidence gaps enumerated from `missing_evidence.md` Tier 1 `[C-401, C-501]`.

*Figure/table proposal*:
- **Figure 7** — Model capability/gating diagram. *Source*: `model_input_freeze.md`, `missing_evidence.md`. *Exists*: No.
- **Table R-4** — Resolved vs blocked quantities (minimum-honest model). *Source*: `model_input_freeze.md` §Minimum honest model. *Exists*: No.

---

## 8. Reproducibility and validation

**Software validation**: the repository pytest run (excluding `tests/test_diagnostics.py`) reported **1773 passed and 2 skipped** `[C-602]`. This verifies code paths and invariants against stated fixtures; it is **software validation, not empirical biological validation** `[C-602]`.

> **Permitted**: "The tests verify code paths against stated assertions and fixtures. This is software validation and is not empirical biological validation." `[C-602]`

**Reproducibility**: the MaleCNS inputs consumed here carry **no recorded expected checksum**, so exact-tree-snapshot reproducibility is partially constrained `[C-701]`. The retrieval and analysis are scripted (`retrieve_malecns_compartment_post.py`, `analyze_mn5_two_gate_constraint_model.py`) and the audited contact artifact is exported at `research/artifacts/malecns_compartment_post_psi_mn5.csv`, but the Feather download is a truncated/unpinned snapshot `[C-701]`.

> **Limitation**: external-data reproducibility items are documented in `EXTERNAL_DATA_REPRODUCIBILITY.md` and remain VERIFY_REQUIRED for checksumming and staging commands `[C-701]`.

*Figure/table proposal*:
- **Figure 8** — Validation/reproducibility overview. *Source*: `validation/full_suite_report.md`. *Exists*: No.

---

## Section status summary

| # | Result section | Evidence coverage | Remaining gap for drafting |
|---|---|---|---|
| 1 | Data provenance and inputs | Fully supported `[C-101]` | None |
| 2 | PSI contact inventory | Fully supported `[C-102, C-103]` | Generate figures 3/4 from audit artifact |
| 3 | MN5 morphology / mesh / registration | Fully supported `[C-202, C-204]` | Generate Table R-2 from audit |
| 4 | Path analysis & limitations | Fully supported `[C-201]` | None |
| 5 | Electrophysiology & provenance | Supported + conflict preserved `[C-301–C-304]` | Generate Table R-3 from freeze |
| 6 | Model analysis & sensitivity | Model-derived outputs reported `[C-402, C-503, C-601]` | Generate figures 5/6; CSV exists |
| 7 | Evidence gaps & closed gates | Fully supported `[C-401, C-501]` | None |
| 8 | Reproducibility & validation | Supported `[C-602, C-701]` | Generate figure 8 |

> **Cannot yet be written**: native spatial voltage transfer (Gate A) and native Dα7 conductance (Gate B) are reported as **evidence absences**, not Results — see §7. No numerical results were invented; all values are drawn verbatim from the admissible source artifacts listed under each claim.

---
*End of Results draft. Created at `paper/RESULTS_DRAFT.md`. No production code, tests, research artifacts, or `fly_state.json` were modified. No commit or push was performed.*