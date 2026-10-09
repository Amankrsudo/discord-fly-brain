# Introduction

This draft is grounded in the frozen evidence base (`research/model_input_freeze.md`, `research/final_anatomy_audit.md`, `research/mn5_psi_mn5_final_constraint_model.md`) and the claim evidence map (`paper/CLAIM_EVIDENCE_MAP.md` `[C-101–C-701]`). Substantive biological framing is tied to claim IDs; provenance classes follow the project's five-class taxonomy.

---

## 1. Biological motivation

The Drosophila Giant Fiber System (GFS) mediates the short-latency takeoff (jump) and escape (flight) response initiated by a looming visual threat detected by the optic lobes `[C-101]`. The principal escape interneuron, the Giant Fiber (GF), descends bilaterally and makes two fast output pathways: a monosynaptic GF→TTMn (jump) pathway and a disynaptic GF→PSI→MN5/DLMn (wing-downstroke) pathway that ultimately drives the dorsal longitudinal wing depressor muscles `[C-101]`. Understanding how a visual threat becomes a motor command requires knowing where and how PSI contacts MN5, and how much of that signal reaches the soma to influence firing `[C-101, C-201]`.

MN5 is the motoneuron that *"innervates the two most dorsal fibers of the dorsal longitudinal wing depressor muscle (DLM)"* — DLM fibers 5 and 6 — contralateral to its soma, a textual assignment from the source literature rather than a project inference `[C-101]`. The two recorded MN5 bodies are identified directly from the MaleCNS v1.0 annotation table: `801970` (left; VFB `VFB_jrmc37jr`) and `801295` (right; VFB `VFB_jrmc37js`) `[C-101]`.

---

## 2. Rationale for combining anatomy, contacts, electrophysiology, and computation

A complete biophysical account of PSI→MN5 transmission must close four gaps in sequence: (1) the exact wiring from PSI to MN5, (2) the geometric relationship of each contact to the MN5 soma, (3) the native electrophysiological parameters of MN5, and (4) a model-based synthesis under declared assumptions `[C-201, C-301, C-401]`.

The MaleCNS v1.0 connectome provides a complete candidate structure for gap (1), but the standard for reporting it is provenance-disciplined: counts must be quoted at a stated minimum-confidence threshold `[C-102]`. Gap (2) requires a reconstructed path from each contact to a labelled soma, which the available skeletons do not supply. Gap (3) is constrained by native whole-cell recordings of MN5 but faces a documented capacitance discrepancy `[C-301, C-303]`. Gap (4) is only meaningful if (2) and (3) can be closed — otherwise it is a conditional, assumption-bounded exercise `[C-201, C-401, C-501]`.

The project therefore treats the four evidence classes separately — native measurement, literature evidence, anatomical data, and model-derived estimate — rather than collapsing them, so that a model-derived sensitivity range is never read back as a native observation `[C-301, C-302, C-402, C-601]`.

---

## 3. Research questions

The manuscript addresses four questions, each answered only where the frozen evidence base permits:

1. **Anatomy**: At minimum confidence 0.5, do the MaleCNS v1.0 synapse and annotation layers agree on the PSI→MN5 contact inventory? `[C-102, C-103]`
2. **Morphology**: Do the MaleCNS MN5 skeletons carry an anatomically reconstructed contact-to-soma path, and how is each contact's SWC Type to be interpreted? `[C-201, C-203]`
3. **Native constraints**: Which native electrophysiological values of MN5 are admissible, and which passive/cable quantities remain unmeasured? `[C-301, C-302, C-303]`
4. **Conditional modeling**: What can an assumption-bounded model produce under explicit bridge geometry, and what must it refuse? `[C-402, C-503, C-601]`

---

## 4. Provenance-aware analysis and authorization gates

The methodological contribution is a **provenance-aware framework** that prevents a blocked quantity from becoming a model constant by accident. Every model input is loaded from `research/model_input_freeze.csv` into a `ParameterSet` that **raises** (`BlockedParameterError`) when a blocked parameter is requested, rather than substituting a value `[C-401, C-501]` (`model_framework.py:ParameterSet.require`). Two gates are enforced at the code level:

- **Gate A — PSI→MN5 spatial voltage transfer: NOT AUTHORIZED.** `require_biological_transfer_authorization()` and `require_spatial_transfer()` both always raise; no code path may claim a measured native transfer `[C-201, C-401]`.
- **Gate B — Dα7 conductance: NOT AUTHORIZED.** `require_dalpha7_gate()` always raises; `Dalpha7Interface.conductance()` calls it `[C-501]`.

This is not a stylistic choice but a scientific one: MN5-specific passive parameters are not uniquely determinable from available evidence — two whole-cell measurements constrain three unknowns (Cm, Rm/g_pas, Ra), no MN5-specific axial resistivity exists (the only measured Drosophila motor-neuron Ra is larval aCC, 212.47 ± 3.69 Ω·cm), the recovered skeleton lacks a soma node, and the somatic capacitance is discrepant by ~3× `[C-201, C-303, C-401]`.

> **Permitted**: "The framework does not infer biological parameters from desired model outputs."

---

## 5. Study scope and what is NOT claimed

**This study establishes** the audited PSI→MN5 contact inventory (43 contacts, 17 left / 26 right, at minconf 0.5), the official `compartment_post` labels (all `axon`), the preserved native MN5 voltage measurements and their conflicts, the geometric contact-to-root paths, and the structure of a provenance-separated conditional model `[C-101, C-102, C-103, C-201, C-301, C-303, C-601]`.

**This study does NOT claim**: a measured native contact-to-soma voltage transfer (`C-401`), a native PSI→MN5 or Dα7 conductance (`C-501, C-502`), resolution of the capacitance discrepancy `C-01`, resolution of the 1000× conductance unit conflicts `C-02/C-03`, a biological interpretation of SWC Type `0` (`C-203`), or registration of the spike-initiation zone to the MaleCNS mesh `[C-202, C-203]`.

The Introduction therefore frames the work as a **provenance-controlled evidence map and a conditional model**, not as a validated biophysical measurement of the PSI→MN5 synapse.

> **Limitation**: the test command is `python -m pytest tests/ -v --tb=short --ignore=tests/test_diagnostics.py`; software validation of code paths is not empirical biological validation `[C-602]`.

*Introduction draft complete. Created at `paper/INTRODUCTION_DRAFT.md`.*`C-102` is the correct citation for input resistance attribution. The audit's DISC-05 (input resistance attribution) was resolved: 102 ± 12 MΩ (n=22) is retained as Fayyazuddin et al. 2006 per the frozen inventory, and the 97 ± 31 MΩ (n=52) set is retained as Ryglewski, Kilo & Duch 2014 — both sources are cited without preference `[C-302, C-303]`.

---
*End of Introduction draft. No production code, tests, or `fly_state.json` modified. No commit or push performed.*