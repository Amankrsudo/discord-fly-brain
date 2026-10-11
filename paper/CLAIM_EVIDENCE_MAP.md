# Claim Evidence Map — Fly Brain 3.0 (PSI→MN5 / Dα7)

**Purpose**: Pair every scientific claim planned for the manuscript with its evidence class, exact source, what the evidence establishes, what it does NOT establish, permitted wording, required citations, and status. This map does NOT alter any code, model parameters, or flight state.

**Evidence classes** (five classes, kept distinct — enforced in `model_framework.py:ModelProvenance` and `malecns_ingest.py:EvidenceClass`):
- `LDP` — Literature-derived (published measurements/parameters from primary sources)
- `NEM` — Native experimental measurement (recorded in this repository's biological object)
- `AM` — Anatomical measurement (connectomic/standard anatomy from datasets)
- `MDE` — Model-derived estimate (output of a declared, assumption-bounded model)
- `MA` — Model assumption (declared assumption, no empirical basis asserted)

**Gate status (unchanged)**:
- **PSI→MN5 spatial voltage transfer: NOT AUTHORIZED** (no native measurement; spatial transfer gate closed — see C-005)
- **Dα7 biological conductance: NOT AUTHORIZED** (no native measurement at PSI→MN5; conductance gate closed — see C-006)

---

## Claim Group 1 — Connectome anatomy and identity

### C-101 | Body identity and cell-type assignment
- **Claim**: MN5 = body IDs `801970` (left, VFB `VFB_jrmc37jr`) and `801295` (right, VFB `VFB_jrmc37js`); PSI = body IDs `802401` (left) and `903327` (right). MN5 innervates DLM fibers 5 and 6 contralateral to its soma.
- **Evidence category**: `AM` (anatomical/connectomic observation, textual)
- **Exact source**: `research/final_anatomy_audit.md` (Block A), citing Ryglewski & Duch 2009 verbatim for DLM fiber identity; MaleCNS v1.0 annotation table for IDs.
- **Establishes**: Body identity and the textual cell-type assignment from the source publication.
- **Does NOT establish**: Any electrical property or voltage transfer.
- **Permitted wording**: "MN5 (body IDs 801970 left / 801295 right; VFB identifiers ...) innervates DLM fibers 5 and 6 contralateral to its soma (Ryglewski & Duch 2009)."
- **Required citations**: Ryglewski & Duch 2009, J Neurophysiol 102:3673; MaleCNS v1.0 (Berg et al. 2026, release).
- **Status**: **Supported**

### C-102 | Contact count
- **Claim**: At minimum confidence 0.5, MaleCNS v1.0 records 43 PSI→MN5 contacts: 17 for `802401→801970` and 26 for `903327→801295`.
- **Evidence category**: `AM` — two independent dataset files agree
- **Exact source**: `research/final_anatomy_audit.md` (Block B); extracted from `MaleCNS v1.0 malecns-v1.0-syn-partners-male-cns-v1.0-minconf-0.5.feather`; cross-checked against the official synapse annotation layer (17 and 26).
- **Establishes**: The exact contact tally with both pairings corroborated by two independent files.
- **Does NOT establish**: Voltage-transfer, distance-based transfer weight, or any per-contact electrical outcome.
- **Permitted wording**: "At minimum confidence 0.5, MaleCNS v1.0 records 43 PSI→MN5 contacts: 17 for body pairing 802401→801970 and 26 for 903327→801295."
- **Required citations**: Berg et al. 2026 (MaleCNS v1.0 release); cite `minconf 0.5` explicitly. (DOI: **VERIFIED** — `10.1016/j.cell.2026.08.015`, confirmed against publisher record; full author list from DOI page, repository uses shorthand "Berg, S. et al.").
- **Status**: **Supported**
- **Figure/Table link**: `paper/figures/FIGURE_PLAN.md` candidate 3 (contact mapping)

### C-103 | Official compartment_post label
- **Claim**: The official MaleCNS `compartment_post` annotation is `axon` for all 43 PSI→MN5 contacts; `compartment_pre` is `axon` for 38 and `unknown` for 5 (all unknown on body 801295).
- **Evidence category**: `AM` (dataset annotation)
- **Exact source**: `research/final_anatomy_audit.md` (Block C); annotation layer info enum `["unknown","axon","dendrite","linker","cell-body-fiber"]`; artifact `research/artifacts/malecns_compartment_post_psi_mn5.csv`.
- **Establishes**: The verbatim dataset label per synapse; 0 missing, 0 ambiguous, 0 unknown-post.
- **Does NOT establish**: Electrophysiological compartment identity, voltage transfer, or SWC biological compartment meaning.
- **Permitted wording**: "The official `compartment_post` field is labeled `axon` for all 43 contacts. This reports the dataset annotation and does not establish electrophysiological compartment identity or voltage transfer."
- **Required citations**: Berg et al. 2026 (MaleCNS v1.0 release; DOI: **VERIFIED** — `10.1016/j.cell.2026.08.015`).
- **Status**: **Supported**
- **Figure/Table link**: Figure candidate 4 (compartment annotations)

---

## Claim Group 2 — Geometry, mesh, soma, and topological limits

### C-201 | No anatomically reconstructed contact-to-soma path
- **Claim**: The MaleCNS MN5 SWCs contain zero soma-labeled nodes (`kind=1`); consequently no anatomically reconstructed contact-to-soma path exists for any of the 43 contacts.
- **Evidence category**: `AM`
- **Exact source**: `research/final_anatomy_audit.md` (Block F, Block K Uncertainty 2), `research/model_input_freeze.md` (MN5 soma node / soma surface, BLOCKED).
- **Establishes**: The permanent absence of a soma node and the permanent UNRESOLVED status of the contact→soma graph path.
- **Does NOT establish**: A substitute distance or voltage transfer.
- **Permitted wording**: "The available MaleCNS SWCs contain no soma-labeled node, so an anatomically reconstructed contact-to-soma path could not be established."
- **Required citations**: MaleCNS v1.0 release (Berg et al. 2026).
- **Status**: **Supported (open anatomic limitation)**
- **Figure/Table link**: Figure candidate 3

### C-202 | Soma-region proxy is an assumption, not a soma
- **Claim**: A proximal soma-region dilation (radius 4.671 µm on 801970, 5.376 µm on 801295) exists near `somaLocation`, but it is modeled as a proxy node (`kind=2`) and is NOT annotated as a soma by any source.
- **Evidence category**: `AM` (geometry) + `MA` (assignment)
- **Exact source**: `research/final_anatomy_audit.md` (Block F); `research/model_input_freeze.md` (MN5 soma-region proxy identification, MN5 compartment split of cable).
- **Establishes**: Dilation geometry and the explicit assumption that the proxy is not a soma.
- **Does NOT establish**: A biological soma surface or compartment identity.
- **Permitted wording**: "A soma-region proximal dilation is present but is a proxy node (`kind=2`) in the MaleCNS skeleton; calling it the soma is a model assumption not grounded in source annotation."
- **Required citations**: MaleCNS v1.0 release (Berg et al. 2026).
- **Status**: **Supported (with stated assumption)**

### C-203 | SWC kind semantics are undefined by the source
- **Claim**: MaleCNS documents the SWC format (0=Undefined, 1=Soma, 2=Axon) but states nothing about how its `Type` column is populated; observed counts are ~93% `kind=0`, ~7% `kind=2`, and zero `kind=1`.
- **Evidence category**: `AM` (measured counts); `MA` (biology undefined)
- **Exact source**: `research/final_anatomy_audit.md` (Block G); `research/model_input_freeze.md` (SWC kind=2 semantics, C-08).
- **Establishes**: The literal Type distribution and the documented lack of source assignment procedure.
- **Does NOT establish**: Any biological compartment mapping for `kind=2`.
- **Permitted wording**: "MaleCNS documents no assignment procedure for the SWC Type column, so the biological compartment corresponding to `kind=2` is undefined in available source."
- **Required citations**: MaleCNS v1.0 release (Berg et al. 2026).
- **Status**: **Supported (open semantic question)**

### C-204 | Mesh topology caveats
- **Claim**: The MN5 mesh is non-closed and fragmented (462k+ boundary edges, 2.6k+ components; largest component holds only 2.8% of area).
- **Evidence category**: `AM`
- **Exact source**: `research/final_anatomy_audit.md` (Block I).
- **Establishes**: The topological status of the mesh, cross product validated to 2e-16 relative error.
- **Does NOT establish**: A biological disconnection or an electrical compartment.
- **Permitted wording**: "The mesh is topologically non-closed and fragmented; fragmentation is attributed by neuPrint to segmentation artifacts, and no component is assigned a compartment name."
- **Required citations**: Berg et al. 2026 (MaleCNS v1.0); neuPrint attribution note.
- **Status**: **Supported**

---

## Claim Group 3 — Native electrophysiology (measured constraints)

### C-301 | MN5 resting potential, spike threshold, and AP amplitude
- **Claim**: Native MN5 measures: resting potential −67.8 ± 5.5 mV (n=13), spike threshold −24.1 ± 8.2 mV (n=11), AP amplitude +45.5 ± 8.6 mV (n=13).
- **Evidence category**: `NEM`
- **Exact source**: `research/model_input_freeze.md` (Section A · SAFE TO USE NOW).
- **Establishes**: Strongest native MN5 voltage measurements, usable as model constraints.
- **Does NOT establish**: PSI-evoked EPSPs or synaptic conductance.
- **Permitted wording**: "Ryglewski, Kilo & Duch 2014 reported native MN5 resting potential −67.8 ± 5.5 mV (n=13), spike threshold −24.1 ± 8.2 mV (n=11), and AP amplitude +45.5 ± 8.6 mV (n=13); used only as measured constraints on a reduced model."
- **Required citations**: Ryglewski, Kilo & Duch 2014, J Neurophysiol 102:3673.
- **Status**: **Supported**

### C-302 | MN5 input resistance (two independent sets)
- **Claim**: Native MN5 input resistance: 102 ± 12 MΩ (n=22) and 97 ± 31 MΩ (n=52), consistent.
- **Evidence category**: `NEM`
- **Exact source**: `research/model_input_freeze.md` (Section A · SAFE TO USE NOW); `malecns_ingest.py` `PASSIVE_PARAMETER_CONTEXT` records 102 ± 12 MΩ (n=22) as Fayyazuddin et al. 2006.
- **Establishes**: Usable native passive-constraint measurements.
- **Does NOT establish**: Specific membrane resistance or cable parameters (different object).
- **Permitted wording**: "Two native measurements of MN5 input resistance were consistent: 102 ± 12 MΩ (n=22) and 97 ± 31 MΩ (n=52)."
- **Required citations**: Fayyazuddin et al. 2006 (for 102 ± 12 MΩ, n=22); Ryglewski, Kilo & Duch 2014 (for 97 ± 31 MΩ, n=52).
- **Status**: **Supported**

### C-303 | Capacitance conflict (C-01) — unresolved
- **Claim**: Two native MN5 capacitance values remain in conflict: 43 ± 2 pF and 127 ± 16 pF; both are retained and no winner is chosen.
- **Evidence category**: `NEM` (conflicted)
- **Exact source**: `research/model_input_freeze.md` (C-01 unresolved; Section A variants A/B).
- **Establishes**: The conflict is real and preserved; authors flagged dendritic space-clamp as a Cm error source for variant B.
- **Does NOT establish**: A single correct capacitance.
- **Permitted wording**: "Two native MN5 whole-cell capacitance values remain in conflict (43 ± 2 pF vs 127 ± 16 pF); per the model-input freeze, both are retained and no value is preferred."
- **Required citations**: Fayyazuddin et al. 2006; Ryglewski & Duch 2009.
- **Status**: **Conflict preserved (qualified)**

### C-304 | MN5 somatic EPSP — GF-stimulated, comparison target only
- **Claim**: Under GF stimulation, the reported 4.71 ± 0.35 mV somatic EPSP (n=10) is a filtered somatic voltage; PSI was not directly stimulated and the distal amplitude is unreported.
- **Evidence category**: `NEM`
- **Exact source**: `research/model_input_freeze.md` (PSI→MN5 EPSP amplitude WT); `research/mn5_psi_mn5_final_constraint_model.md` (Section 3 calibration).
- **Establishes**: A comparison/calibration target for a reduced model.
- **Does NOT establish**: An isolated PSI-evoked EPSP, gPSI, or validation of the PSI→MN5 model.
- **Permitted wording**: "The reported 4.71 ± 0.35 mV somatic EPSP was recorded under GF stimulation. We use it only as a comparison/calibration target; it is not a PSI-specific EPSP."
- **Required citations**: Fayyazuddin et al. 2006 (PLoS Bi 4:e63).
- **Status**: **Supported (comparison target)**

---

## Claim Group 4 — Spatial voltage transfer (Gate A)

### C-401 | Spatial voltage transfer is NOT AUTHORIZED (gate closed)
- **Claim**: Native PSI→MN5 postsynaptic spatial voltage transfer has not been measured in any Drosophila MN5 preparation; the spatial voltage transfer gate is closed.
- **Evidence category**: `MA` (negative evidence / search exhausted)
- **Exact source**: `research/missing_evidence.md` (M-02: "NOT FOUND — SEARCH EXHAUSTED", citing `research_done.md` Q-01); `research/final_anatomy_audit.md` (gate verdict); `research/mn5_spatial_transfer_gate_review.md`.
- **Establishes**: Only that no native measurement exists, so spatial transfer cannot be claimed.
- **Does NOT establish**: Any measured transfer ratio, attenuation, or electrotonic distance. The audit documents that `compartment_post=`axon` does not establish voltage transfer (E-048).
- **Permitted wording**: "No native measurement of PSI→MN5 spatial voltage transfer exists in the reviewed evidence; per the closed gate, this quantity is not reported as a native physiological finding."
- **Required citations**: MaleCNS v1.0; neuPrint skeleton disclaimer on root significance.
- **Status**: **NOT AUTHORIZED (gate closed)**
- **Prohibited wording**: "measured native PSI→MN5 transfer," "measured voltage attenuation," "determined the contact-to-soma path."

### C-402 | Abstract cable bridge is model-derived
- **Claim**: A two-compartment abstract cable bridge (112.5 µm, 2 µm uniform cable, derived from published GFS DLMn geometry) was analyzed as a model-authorized conditional analysis; its outputs are MODEL-DERIVED and conditional on assumptions.
- **Evidence category**: `MDE`
- **Exact source**: `research/mn5_psi_mn5_final_constraint_model.md` (Section 2 Layer D; Section A.2; authorization status §9).
- **Establishes**: The existence and scope of the conditional model bridge and its output ranges (local/somatic peak, peak ratio, threshold crossings) across 2,880 runs.
- **Does NOT establish**: Native contact-to-soma voltage transfer; root↔soma distances are measurements, not documented file properties.
- **Permitted wording**: "We performed a model-authorized conditional analysis using an explicit abstract cable bridge constrained by published GFS geometry. The analysis is permitted under those assumptions; its outputs remain model-derived and do not establish native physiology."
- **Required citations**: Augustin, Zylbertal & Partridge 2019 (eNeuro, DOI 10.1523/ENEURO.0423-18.2019) for bridge geometry precedent.
- **Status**: **Supported (model-derived only)**
- **Figure/Table link**: Figure candidate 5 (two-gate model); Figure candidate 6 (sensitivity)

---

## Claim Group 5 — Dα7 and synaptic conductance (Gate B)

### C-501 | Dα7 conductance is NOT AUTHORIZED (gate closed)
- **Claim**: No native Dα7 conductance, density, kinetics, or reversal potential at PSI→MN5 is measured; the Dα7 conductance gate is closed.
- **Evidence category**: `MA` (negative evidence); recombinant data are `LDP`
- **Exact source**: `research/missing_evidence.md` (M-01, M-04); `research/model_input_freeze.md` (MN5 specific membrane resistance etc. as NONE — no accessible primary measurement); `research/mn5_psi_mn5_final_constraint_model.md` (Gate B §6); `research/final_anatomy_audit.md` (Gate B verdict).
- **Establishes**: Only that native receptor-level data are absent, so native conductance cannot be claimed.
- **Does NOT establish**: Any native conductance value; recombinant oocyte EC50/Hill currents are NOT relabeled as native MN5 conductance.
- **Permitted wording**: "No native PSI→MN5 Dα7 conductance exists in the reviewed evidence; recombinant Dα7 constraints supply channel-level precedent only."
- **Required citations**: Lansdell, Collins, Goodchild & Millar 2012 (BMC Neurosci, DOI 10.1186/1471-2202-13-73) for recombinant channel-level data only.
- **Status**: **NOT AUTHORIZED (gate closed)**

### C-502 | Dα7 localization evidence is partial and conditional
- **Claim**: Dα7 is 10–100× more strongly localized to GF dendrites; native Dα7 binds α-bungarotoxin (NNGSCLYVPPGIFK, Asn170); Dα7 mutant jump is abolished while flight/trap/ERG remain normal. However, no Dα7 immunostaining of PSI terminals or MN5 axons exists in any primary source.
- **Evidence category**: `AM` (localization) + `LDP` (biochemical)
- **Exact source**: `research/model_input_freeze.md` (Dalpha7 localisation at GF dendrites; Dalpha7 native alpha-bungarotoxin binding; Dalpha7 mutant jump phenotype; Dalpha7 localisation at PSI axon terminals / MN5 axons = NOT REPORTED).
- **Establishes**: General Dα7 presence and GF dendritic enrichment; explicitly NOT a PSI-terminal or MN5-axon measurement.
- **Does NOT establish**: Dα7 density or function at the PSI→MN5 synapse.
- **Permitted wording**: "Dα7 is enriched at GF dendrites and binds α-bungarotoxin in native tissue, but is not reported at PSI terminals or MN5 axons in any primary source."
- **Required citations**: Mass-spec binding peptide source; Fayyazuddin et al. 2006 for mutant phenotype.
- **Status**: **Supported (limited, non-synaptic evidence)**

### C-503 | Dα7 effective conductance sweep is model-derived
- **Claim**: An effective `g_Dalpha7` sensitivity sweep (0.01–1000 nS) with E_Dα7 ∈ {−15, 0, +10 mV} was analyzed; every value is a model assumption and all calculated changes are model-derived.
- **Evidence category**: `MDE`
- **Exact source**: `research/mn5_psi_mn5_final_constraint_model.md` (Section 6, §9 authorization).
- **Establishes**: The structure and bounds of the conditional sweep (2,880 runs).
- **Does NOT establish**: Native receptor abundance, conductance, or biological pathway threshold predictions; crossings at large conductances are not biological predictions.
- **Permitted wording**: "Effective Dα7 conductance was swept as a model assumption; outputs are model-derived sensitivity, not native measurements."
- **Required citations**: Lansdell et al. 2012 (recombinant channel-level constraint only).
- **Status**: **Supported (model-derived only)**

---

## Claim Group 6 — Model consistency and validation

### C-601 | Two-gate constrained model produces model-derived outputs
- **Claim**: The two-gate analysis reports 15,528 output rows over a deterministic parameter grid and classifies fitted gPSI and threshold crossings as model-derived estimates.
- **Evidence category**: `MDE`
- **Exact source**: `research/mn5_psi_mn5_final_constraint_model.md` (full document).
- **Establishes**: The analytical structure and row count of the conditional model.
- **Does NOT establish**: Any native electrical quantity; numerical reachability is not biological plausibility or validation.
- **Permitted wording**: "Under the stated model structure and parameter grid, the model produced X outcomes over 15,528 rows. These are model-derived outcomes conditional on the listed assumptions; they are not native physiological measurements."
- **Required citations**: Augustin et al. 2019 (model precedent).
- **Status**: **Supported (model-derived only)**

### C-602 | Software test status is software, not biological validation
- **Claim**: The latest repository pytest run passed 1773 tests and skipped 2, excluding `tests/test_diagnostics.py`.
- **Evidence category**: `AM` (software test result)
- **Exact source**: `paper/claim_evidence_matrix.csv` (C-008); `validation/full_suite_report.md`.
- **Establishes**: Software-level verification of code paths.
- **Does NOT establish**: Biological validity of the MN5 or PSI models.
- **Permitted wording**: "The tests verify code paths against stated assertions and fixtures. This is software validation and is not empirical biological validation."
- **Required citations**: AGENTS.md (test command).
- **Status**: **Supported (software validation only)**

---

## Claim Group 7 — Reproducibility and external data

### C-701 | MaleCNS checksum provenance and reproducibility limits
- **Claim**: A SHA-256 digest for the local staged Feather input is recorded, but no independent publisher-provided expected checksum was identified; the digest supports local-file identity, not independent verification of future remote downloads.
- **Evidence category**: `MA` (limitation documentation)
- **Exact source**: `research/final_anatomy_audit.md` (Block D / Block C provenance note); `paper/claim_evidence_matrix.csv` (C-001 status).
- **Establishes**: The reproducibility limitation is documented.
- **Does NOT establish**: A fully pinned snapshot.
- **Permitted wording**: "Always report the minimum-confidence threshold. A SHA-256 digest is recorded for the local staged Feather, but no independent publisher-provided expected checksum was identified."
- **Required citations**: MaleCNS v1.0 release (Berg et al. 2026).
- **Status**: **Qualified (open limitation)**

---

*Map complete. All claims reference exact source artifacts. Gates A and B remain closed; no claim promotes a model-derived or assumed quantity into a measured native finding.*