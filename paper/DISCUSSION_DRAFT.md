# Discussion

This draft interprets the repository-derived and model-derived findings in `paper/RESULTS_DRAFT.md`, grounded in the evidence map (`paper/CLAIM_EVIDENCE_MAP.md`) and the frozen research audits. Every substantive point is tagged with its claim ID. Provenance classes are distinguished explicitly: native measurement (`NEM`), literature-derived (`LDP`), anatomical (`AM`), model-derived estimate (`MDE`), and assumption (`MA`).

---

## 1. Summary of the strongest repository-derived findings

The repository establishes a provenance-controlled **anatomical and provenance framework** for the PSI→MN5 connection, not a validated biophysical measurement. The strongest findings are:

- **Wiring**: at `minconf 0.5`, MaleCNS v1.0 records **43** PSI→MN5 contacts (17 left for `802401→801970`; 26 right for `903327→801295`), corroborated by two independent dataset files (the synapse-partners Feather and the official annotation layer) `[C-101, C-102]`.
- **Contact location**: the official `compartment_post` label is `axon` for all 43 contacts, 0 missing/ambiguous/unknown-post `[C-103]`.
- **Mesh/SWC registration**: the MaleCNS 8 nm voxel frame is numerically confirmed against the mesh frame (`swc × 8 = mesh_nm`) with a validated byte-budget mesh parser `[C-202]`.
- **Provenance enforcement**: the framework raises rather than defaults on any blocked parameter; both scientific gates are hard-enforced `[C-401, C-501]`.

These are **audited anatomical and methodological facts**, not physiological measurements.

---

## 2. What contact geometry and morphological paths can establish

The contact-local geometric quantities are well-defined: contact-to-mesh surface distance (1.67–80.22 nm), contact-to-SWC-root path length (169.2–267.8 µm on 801970, 169.2–230.6 µm on 801295), and contact-to-`somaLocation` straight-line distance (110.3–172.9 µm) `[C-201]`. Three geometric distances are kept strictly separate and never substituted `[C-201]`.

However, **geometry is never converted into electricity** in this work. The boundary is explicit (`final_anatomy_audit.md` Block L, `[C-201, C-401]`): no `Ra`, `Rm`, `Cm`, `g_pas`, length constant, space constant, electrotonic distance, attenuation, transfer resistance, or voltage transfer is derivable from mesh area, SWC radii, or path lengths. The contact→root paths are geometric (`MDE` on an explicit node-assignment rule) `[C-201]`; the contact→soma graph path is **permanently UNRESOLVED** because no `kind=1` (soma) node exists in any skeleton `[C-201, C-202]`.

> **Permitted**: "A root-referenced path length is not an electrotonic distance."

---

## 3. What native electrophysiology constrains — and what it cannot identify

The admissible native MN5 measurements are strong on cell-state identity but **silent** on synaptic transfer quantities. Resting potential −67.8 ± 5.5 mV (n=13), spike threshold −24.1 ± 8.2 mV (n=11), AP amplitude +45.5 ± 8.6 mV (n=13), and input resistance 102 ± 12 MΩ (n=22) / 97 ± 31 MΩ (n=52) are all somatic whole-cell recordings used as reduced-model constraints `[C-301, C-302]`. These constrain a threshold-only abstraction but do **not** identify a synaptic conductance, a reversal potential, or a voltage-transfer function `[C-301, C-304]`.

The **4.71 ± 0.35 mV somatic EPSP** (n=10) was recorded under GF stimulation; PSI was never directly stimulated and the distal EPSP amplitude is unreported `[C-304]`. It is retained as a comparison/calibration target, never as a PSI→MN5 measurement `[C-304]`.

> **Permitted**: "The reported 4.71 ± 0.35 mV somatic EPSP was recorded under GF stimulation. We use it only as a comparison/calibration target; it is not a PSI-specific EPSP."

**Native MN5 capacitance is the central unresolved conflict (C-01)**: 43 ± 2 pF (n=22) vs 127 ± 16 pF, the same cell and nominal preparation, ~2.95× apart; variant B's authors flag dendritic space-clamp as a source of error `[C-303]`. Both are retained; no value is preferred, averaged, or selected `[C-303]`. Because Cm is contested and Ra/Rm do not exist for MN5, **no cable model is licensed** — which is precisely the premise that blocks Gate A `[C-201, C-303, C-401]`.

**Passive parameter provenance (C-10)**: Mn5-specific Ra, Rm, and leak have no native measurement; the sole Mn5 passive model adopts *Manduca* values self-described as "values commonly applied" `[C-303, C-301]`. The only measured Drosophila motor-neuron Ra is 212.47 ± 3.69 Ω·cm (larval aCC) — 2.4× the value applied for Mn5 `[C-303]`. These are flagged as wrong-species adopted defaults, never silently promoted.

---

## 4. How exploratory model sensitivity should be interpreted

The two-gate analysis produces 15,528 model-derived rows (9,288 contact-local + 2,880 abstract transfer + 2,880 Dα7 sweep + 480 EPSP calibration) over a deterministic parameter grid `[C-601]`. Each is tagged `model_derived_estimate` in the CSV and is **conditional on declared assumptions** `[C-402, C-503, C-601]`.

- The **contact-local single-patch** analysis uses each contact's projected SWC node radius and mean adjacent edge length to form `A = 2πrℓ`; node Type tokens are preserved literally and never biologically interpreted `[C-203, C-601]`.
- The **abstract somatic-transfer bridge** is a uniform 112.5 µm / 2 µm cable derived from published GFS DLMn geometry (Augustin et al. 2019); it is **not traced onto any MaleCNS SWC** and makes no per-contact anatomical soma path `[C-201, C-402]`. Its peak local-to-somatic ratio (`local_to_somatic_peak_ratio`, 0.085–0.892) is the ratio of modeled local-to-somatic peaks, **not an experimentally measured transfer ratio** `[C-402, C-401]`.
- The **Dα7 effective-conductance sweep** (`g_Dα7,effective` 0.01–1000 nS) is a model assumption; recombinant oocyte currents (Lansdell et al. 2012) supply channel-level constraints only and are **not converted to native conductance** `[C-501, C-503]`.

> **Permitted**: "Under the stated model structure and parameter grid, the model produced X outcomes. These are model-derived outcomes conditional on the listed assumptions; they are not native physiological measurements."

The calibrated gPSI (3.58–42.73 nS, fitting the 4.71 mV target) is a numerical reachability result, explicitly **not** biological plausibility or validation `[C-304, C-601]`. Threshold crossings (456/2,880 when Dα7 is enabled) occur only at the largest assumed conductances and are **not biological pathway predictions** `[C-503]`.

The **reduced Mn5 model** (`reduced_mn5.py`) admits only the three SAFE native measurements and has **no leak term** (τ_m is blocked), so voltage moves only under explicit software input and returns to rest only on a spike `[C-301, C-602, C-303]`. Its spikes are modeled events (`is_measurement() → False`), never recorded events `[C-601]`.

---

## 5. Unresolved capacitance discrepancy (C-01) and downstream consequences

C-01 — two native Mn5 whole-cell capacitance values at ~2.95× odds — is preserved with **no winner chosen** `[C-303]`. The dispute cannot be resolved by the available evidence: both are whole-cell recordings of the same nominal preparation, and variant B's own authors cite dendritic space-clamp as a Cm error source `[C-303]`. Because Cm enters every cable and passive equation, **no passive or cable model of Mn5 can proceed** without resolving C-01 — which is the structural reason Gate A remains closed `[C-201, C-401]`.

The reduced model sidesteps C-01 by admitting no Cm at all (it is a threshold-only abstraction); the exploratory sweep carries both A and B variants separately so that any downstream reader can see how the conflict propagates `[C-301, C-601]`.

---

## 6. The 1000× conductance discrepancies (C-02, C-03)

Two unit-level conflicts are preserved, not pooled:
- **C-02**: the published GF gap-junction conductance (135 µS young / 34.5 µS old, Table 1) is executed in `gap2.mod` as **135 / 34.5 nS** — exactly 1000× lower, with the model's own scan script labeling the axis in µS `[C-303]`.
- **C-03**: the published PSI→DLMn chemical peak conductance (80 µS) is executed as **0.08 µS** — also exactly 1000× `[C-303]`. This is a **different synapse** from C-02 and the two must never be pooled.

Both are recorded as `recorded_value=True` (evidence about the artefact, not a usable biological constant) and remain `BLOCKED` for model use `[C-303]`. No code path substitutes the executed value for the table value.

---

## 7. Why Gate A and Gate B remain NOT AUTHORIZED

**Gate A (PSI→MN5 spatial voltage transfer)** is closed because no native measurement exists and four premises remain unresolved: no Drosophila-specific axial resistivity (only *Manduca*, adopted), no specific membrane resistance, an adjudicated capacitance (C-01 contested), and no labelled soma node to close an anatomical path `[C-201, C-401]`. The literature search for a transfer measurement is exhausted (`missing_evidence.md` M-02); the only Drosophila transfer figure is a *Manduca*-parameter simulation explicitly disclaimed as inexact `[C-401]`.

**Gate B (Dα7 conductance)** is closed because no native Dα7 conductance, single-channel conductance, open probability, reversal potential, kinetics, density, or imaging at PSI→MN5 exists `[C-501]`. Dα7 is 10–100× enriched at GF dendrites and binds α-bungarotoxin in native tissue, but it is **not reported** at PSI terminals or Mn5 axons in any primary source `[C-502]`. The recombinant Lansdell et al. 2012 currents (EC50 6.7 ± 1.7 µM ACh) supply channel-level constraints only `[C-503]`. Additionally, Drosophila has **no Kir7.1/KCNJ13 orthologue**, so the vertebrate α7→Kir7.1 mechanism that underlies functional α-bungarotoxin block cannot be modeled `[C-501]`.

> Gates are **evidence constraints on interpretation** — the absence of qualifying primary evidence — not assertions that the underlying quantities do not exist `[C-401, C-501]`.

**Resolving experiments** (`missing_evidence.md`, Tier 1):
- Gate A (M-02): dual-site recording (somatic whole-cell plus focal dendritic/axonal patch at the identified contact) during direct PSI stimulation; ASAP2f imaging is a realistic first-pass fallback `[C-401]`.
- Gate B (M-01/M-04): the same dual-site preparation with pharmacological reversal/conductance series, plus a Dα7-specific manipulation; a native PSI→MN5 synaptic conductance (M-01) is itself a prerequisite for any Dα7 work `[C-501]`.

---

## 8. Limitations

**Provenance and snapshots**: the synapse-pair Feather carries **no recorded expected checksum**; download/staging commands are **not documented** in repository instructions; external-data license redistribution and author attribution are **VERIFY_REQUIRED** per `research_archive/EXTERNAL_DATA_REPRODUCIBILITY.md` `[C-701]`. The two cached SWCs consumed by the sensitivity script are pinned by SHA-256 in the script itself `[C-601]`.

**Interpretation**: every model output is conditional on declared assumptions and must not be read as native physiology `[C-402, C-503]`. The 43 contacts are metadata in the reduced model and play no role in its arithmetic `[C-601]`. "Measured" quantities in the results are exclusively native electrophysiology (resting potential, threshold, AP amplitude, input resistance, the GF-stimulated EPSP) `[C-301, C-302, C-304]`; native PSI→MN5 conductance, spatial transfer, and Dα7 conductance are **absent**, not zero `[C-401, C-501]`.

**Software validation**: 1,773 passed / 2 skipped is inherited from `validation/full_suite_report.md` and was **not freshly reproduced** during drafting `[C-602]`. Test coverage verifies code paths and invariants, not biological validity `[C-602]`.

**Anatomical uncertainties preserved** (not resolved): SWC `kind=2` biology is undefined by the source `[C-203]`; the 3 AMBIGUOUS contacts (margins 1.110–1.172, same runner-up fragment) are preserved without threshold invention `[C-201]`; per-neuron cut-node release remains unreleased (`M-06`, scope-limited) `[C-201]`.

---

## 9. Defensible contributions and future work

**Defensible contributions**:
1. A frozen, reproducible **anatomical audit** of the 43 PSI→MN5 contacts with both-synapse-layer corroboration and quoted minconf `[C-101, C-102, C-103]`.
2. A **provenance-aware model framework** (`model_framework.py`) that enforces the five-class taxonomy and raises on any blocked parameter, making gate violations impossible by construction `[C-401, C-501]`.
3. A **conditional two-gate sensitivity analysis** (15,528 rows) whose model-derived outputs are explicitly tagged and never relabeled as native measurements `[C-601]`.
4. A **minimum-honest model** (`ReducedMN5Simulator`) that uses only three SAFE native inputs and contains no leak, compartment, synapse, or assumed conductance `[C-602]`.

**Future work** is constrained to the resolving experiments above: native MN5 axial resistivity (M-03), a measured contact→soma voltage transfer (M-02) to open Gate A, and a native PSI→MN5 synaptic conductance (M-01) plus Dα7 measurements (M-04) to open Gate B `[C-401, C-501]`. Developmental, sex, and ageing variation are excluded by construction (all MaleCNS is male; GF→TTMn age literature does not apply to GF→PSI) `[C-201, C-301]`.

---

## 10. Conclusion

The repository delivers an **audited, provenance-controlled evidence map** and a **conditional, assumption-bounded model** of the PSI→MN5 connection — not a validated biophysical measurement of it. The anatomy is well-established; the native electrophysiology is partially constrained but capacitance-conflicted; the spatial voltage transfer and Dα7 conductance remain **NOT AUTHORIZED** by the absence of qualifying primary evidence, not by a judgment that they do not exist. The path forward is experimental: dual-site recording and Dα7-specific manipulations, not further model tuning `[C-201, C-301, C-401, C-501]`.

> **Prohibited**: "The model was experimentally validated," "measured native PSI→MN5 transfer," "native Dα7 conductance," "resolved C-01," "SIZ registered to MaleCNS."

*Discussion draft complete. Created at `paper/DISCUSSION_DRAFT.md`.*`C-402` is the correct reference for the conditional-bridge model structure. The abstract bridge geometry is derived from published GFS DLMn precedent (Augustin et al. 2019), not from MaleCNS anatomy; this provenance distinction is enforced in the model (`GFS_BRIDGE_LENGTH_UM`, `GFS_BRIDGE_DIAMETER_UM`) `[C-402]`.

---
*End of Discussion draft. No production code, tests, research artifacts, or `fly_state.json` were modified. No commit or push was performed. No test suite was executed. All claim IDs and source references verified against `paper/CLAIM_EVIDENCE_MAP.md` and the implementation files.*