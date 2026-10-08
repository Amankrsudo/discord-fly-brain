# Parameter Adoption Plan — Fly Brain 3.0 Drosophila GFS Model

**Status:** ONE-SHOT PARAMETER ADOPTION PASS (provenance-first)
**Date:** 2026-10-06
**Scope:** Every biological parameter discovered across `biological_brain/`, `research/`, and the vendored ModelDB 245415 source.
**Companion artifact:** `research/parameter_adoption_ledger.csv` (the canonical machine-readable ledger, one row per parameter, 15 columns).

## The one rule

This pass optimizes for **scientifically defensible parameter provenance**, not for making the model run or look biologically complete. A parameter that remains unresolved is a **successful outcome**. The objective is to make every parameter's epistemic status explicit. The biology is deliberately **not** completed.

## Method

1. **Read-only audit** of every parameter-defining module and evidence record (registries, frozen inventory, conflict register, dynamics modules, ModelDB source, escape-circuit metadata).
2. **Classification** of every parameter into exactly one of five categories — **KEEP, REPLACE, DERIVE, SENSITIVITY_SWEEP, REMAIN_UNRESOLVED** — against the eight-level evidence hierarchy (only levels 1–4 may authorize a biological parameter; levels 5–8 must never silently become biological truth).
3. **No architecture rewrite.** The existing provenance-safe architecture already implements every adoption decision; this pass consolidates and makes it explicit.

### Evidence hierarchy

| Level | Class | May authorize a biological parameter? |
|---|---|---|
| 1 | Direct native experimental measurement in the relevant neuron/synapse | **yes** |
| 2 | Direct anatomical measurement in the relevant preparation | **yes** |
| 3 | Authoritative MaleCNS / connectome measurement | **yes** |
| 4 | Published parameter explicitly measured for the same biological system | **yes** |
| 5 | Literature-derived estimate | no (model reproduction / sensitivity only) |
| 6 | Model assumption | no |
| 7 | Model-fitted value | no |
| 8 | Value chosen for plausible simulation behavior | no |

### The five adoption categories

- **KEEP** — leave the implementation unchanged.
- **REPLACE** — replace only when a stronger primary measurement exists. **None found.**
- **DERIVE** — implement a deterministic derivation. **None authorized** (every would-be derivation is a forbidden conversion).
- **SENSITIVITY_SWEEP** — a clearly labelled sensitivity experiment that answers "how does the model depend on this unresolved assumption?", never "what is the biological value?".
- **REMAIN_UNRESOLVED** — block biological use; preserve existing archival/model-reproduction value where needed for reproducibility; expose provenance and a warning.

---

## A. PARAMETER ADOPTION SUMMARY

| Category | Count | Biological model authorized? |
|---|---|---|
| KEEP | 98 | yes (native/anatomical) or conditional (model-reproduction / phenomenological) |
| REPLACE | 0 | — |
| DERIVE | 0 | — |
| SENSITIVITY_SWEEP | 17 | no (Tier B/C exploratory + geometry assumptions) |
| REMAIN_UNRESOLVED | 22 | no (blocked / NOT AUTHORIZED) |
| **Total** | **137** | |

**Headline result:** the model is already in the correct provenance-safe state. Every parameter that can be authorized is already KEPT with its provenance; every parameter that cannot is already blocked. **No code change to the biological model was required.** The deliverables of this pass are the ledger, this plan, and a regression test that pins the adoption decisions.

---

## B. KEEP LIST

### B1. Native MN5 measurements (evidence level 1 — the only parameters authorized as biological MN5 values)

| Parameter | Value | Source |
|---|---|---|
| MN5 resting potential | −67.8 mV (±5.5 SD, n=13) | Ryglewski, Kilo & Duch 2014, Eur J Neurosci 39:151 (PMID 24620836, PMC4433752, Table 1) |
| MN5 spike threshold | −24.1 mV (±8.2 SD, n=11) | same |
| MN5 action potential amplitude | +45.5 mV (±8.6 SD, n=13) | same |
| MN5 input resistance (set 1) | 102 MΩ (±12, n=22) | Fayyazuddin+ 2006, PLoS Biol 4(3):e63 |
| MN5 input resistance (set 2) | 97 MΩ (±31, n=52) | Herrera-Valdez+ 2013, J Comput Neurosci 34:211 (PMID 22878689, PMC6595220) |
| MN5 whole-cell capacitance (variant A) | 43 pF (±2, n=22) | Fayyazuddin+ 2006 — **CONTESTED (C-01)** |
| MN5 whole-cell capacitance (variant B) | 127 pF (±16 SD) | Ryglewski & Duch 2009, J Neurophysiol 102:3673 — **CONTESTED (C-01)** |
| MN5 somatic EPSP | 4.71 mV (±0.35, n=10) | Fayyazuddin+ 2006 — **comparison target only** |

These are the only parameters the reduced MN5 model consumes. The first three are the sole inputs of `ReducedMN5Simulator`; Rin and the two Cm variants are carried by the exploratory model; the EPSP is a calibration target only.

### B2. MaleCNS anatomy (evidence level 3)

MN5 bodies 801970 / 801295; PSI bodies 802401 / 903327; 17 contacts (802401→801970) + 26 contacts (903327→801295) = **43 total**; coordinate unit 1.0 nm with the `mesh_nm = SWC_coordinate × 8` convention. Pure metadata; carries no electrical value.

### B3. Published-model morphology (evidence level 4, model reproduction only)

GF axon 400 µm × 8 µm; TTMn axon 50 µm × 6 µm, medial dendrite 60 µm, lateral dendrite 30 µm; PSI axon 90 µm × 4.5 µm, dendrite 170 µm (**ESTIMATED — preserved, not promoted**); DLMn axon 50 µm tapering 2→4 µm, dendrite 100 µm × 2 µm; PSI input placement on the DLMn axon at 12.5 µm (anatomy only, not acted on).

### B4. Published-model active conductances (evidence level 4, model reproduction only)

g_Na 300 mS/cm², g_Nap 0.11 mS/cm², g_K 10 mS/cm², E_Na +65 mV, E_K −74 mV (Augustin et al. 2019; gfpn.py `gnatbar=300e-3`, `gnapbar=110e-6`, `gkbar=10e-3`, `ena=65`, `ek=-74`). All are `PUBLISHED_MODEL_PARAMETER`; `is_experimental_gf_measurement` is False and the layer refuses to mark it True. The published active sections are largely based on a Drosophila motoneuron model with parameters manually adjusted for the GFS model.

### B5. ModelDB mechanism rate parameters (evidence level 4)

nat: v1_2m −30 mV, km 6 mV, v1_2h −55 mV, kh −7 mV; nap: v1_2m −30 mV, km 6 mV; k: v1_2m −30 mV, km 6 mV. Verbatim `.mod` rate parameters; the implementation authority for the rate expressions. nap and k have a voltage-independent `mtau = 1` and no inactivation gate.

### B6. Synaptic mechanism parameters (evidence level 4/6, model reproduction only)

TTMn_syn: tau1 0.5 ms, tau2 5.0 ms, e 0 mV, delay 1 ms, pre_loc 1.0, post_loc 0.2, **weight 0.00** (chemical component inert). PSI_syn: tau1 0.1 ms, tau2 5.0 ms, e 0 mV, delay 1 ms, pre_loc 0.9, post_loc 0.5, **weight 0.00** (chemical component inert). DLMn_syn: tau1 0.1 ms, tau2 1.0 ms, e 0 mV, delay 0.15 ms, pre_loc 0.85, post_loc 0.25, **peak conductance 0.08 (source) / 80 µS (paper) — CONTESTED (C-03)**. The 0 mV reversal is a model assumption, not a measured reversal.

### B7. Numerical solver fixtures (evidence level 8 — NOT biological)

GF circuit stimulus 120 nA / 0.03 ms / 100 ms delay (the published model's own circuit stimulus); TTMn fixture 50 nA / 0.03 ms; PSI fixture 50 nA / 0.03 ms; DLMn fixture 20 nA / 0.03 ms (sized to the thin tapered axon on numerical grounds only — **not** a claim that a DLMn needs less current); muscle delay 0.35 ms; NEURON `finitialize(-65)` (a harness choice, deliberately not adopted by 3.0D-8A). Each is declared, named and provenance-labelled by its own checkpoint; none is a rheobase, threshold or measurement.

### B8. 3.0B LIF product path (evidence level 6/8 — phenomenological, NOT the 3.0D biological model)

LC4/LPLC2: V_rest −70, V_threshold −50, V_reset −75, tau_m 15 ms (APPROXIMATION). GF: V_rest −65 (DIRECTLY_MEASURED), V_threshold −45, tau_m 5 ms, refractory 5 ticks (INFERRED). TTMn/PSI/DLMn: V_rest −70, V_threshold −55, tau_m 10/15/10 ms (APPROXIMATION). Synaptic weights: LC4→GF 15 mV (2290 EM), LPLC2→GF 10 mV (1443 EM), GF→TTMn electrical 17 mV, GF→PSI electrical 16.5 mV, GF→TTMn/PSI chemical 5 mV (30 EM), PSI→DLMn chemical 17 mV. These are the 2.0/3.0B `GroupBrain` product path; the sensory→GF looming equations are phenomenological fixtures and are **not** converted into biological membrane conductances.

---

## C. REPLACE LIST

**Empty.** No parameter has a stronger primary measurement available that would justify replacing its current value. In particular:

- No stronger MN5 resting potential, threshold, AP amplitude, Rin or EPSP exists than the Ryglewski/Fayyazuddin/Herrera-Valdez records already KEPT.
- No Drosophila-specific Ra, Rm, g_pas or tau_m exists to replace the literature-derived defaults (they remain REMAIN_UNRESOLVED, not replaced).
- No native PSI→MN5 conductance, Dα7 conductance or spatial transfer measurement exists to replace any blocked quantity.

---

## D. DERIVE LIST

**Empty.** Every would-be derivation is a **forbidden conversion** and is therefore not authorized:

| Forbidden conversion | Why it is forbidden |
|---|---|
| MESH AREA → Cm / Rm / g_pas / Ra | A geometric area is not an electrical parameter. |
| PATH LENGTH → ELECTROTONIC DISTANCE | Requires Ra and Rm, both blocked. |
| CONTACT DISTANCE → VOLTAGE ATTENUATION | The spatial-transfer gate is NOT AUTHORIZED. |
| SOMATIC EPSP → LOCAL SYNAPTIC CONDUCTANCE | A somatic voltage is not a local conductance. |
| Rin → Rm or tau_m | Requires geometry and Cm (contested); no independent authorization. |
| Whole-cell Cm → specific Cm | Requires membrane area; the two Cm variants are contested (C-01). |

The only derivations that exist are **geometry-derived electrical quantities** (per-compartment C, g_leak, R_axial) inside the opt-in passive backend, and those carry provenance `UNKNOWN` by construction — they are not source-reported biological values and are not adopted as biological parameters.

---

## E. SENSITIVITY LIST

Every sweep answers **"how does the exploratory model depend on this unresolved assumption?"**, never "what is the biological value?". Every sweep output carries: parameter, candidate_range, units, provenance, `biological_status=UNRESOLVED`, output_metric, result. No best-performing sweep value is promoted to a biological truth.

### Tier B (literature-derived, evidence level 5)

| Parameter | Nominal | Sweep range |
|---|---|---|
| axial resistivity | 90 Ω·cm | 30, 90, 200, 400 Ω·cm |
| specific membrane capacitance | 1.15 µF/cm² | 0.6, 1.15, 2.6 µF/cm² |
| specific membrane resistance | 6.0 kΩ·cm² | 6, 10, 20, 26 kΩ·cm² |
| cholinergic reversal potential | 0 mV | −15, 0, +10 mV |

### Tier C (free exploratory, evidence level 6)

| Parameter | Nominal | Sweep range |
|---|---|---|
| PSI synaptic peak conductance | 1.0 nS | 0.01–1000 nS (log) |
| Dα7 maximal conductance | 1.0 nS | 0.01–1000 nS (log) |
| Dα7 receptor density (relative) | 1.0 | 0.01–100 (log) |
| Dα7 activation time constant | 1.0 ms | 0.1–10 ms |
| Dα7 desensitization time constant | 5.0 ms | 1–50 ms |
| Dα7 steady-state desensitization fraction | 0.5 | 0–0.95 |
| PSI synaptic rise time constant | 0.5 ms | 0.1–2 ms |
| PSI synaptic decay time constant | 2.0 ms | 0.5–10 ms |
| effective spatial transfer ratio | (none) | 0–1 (explicit mode only) |
| Dα7 reversal potential (exploratory) | 0 mV | −15, 0, +10 mV |

### Geometry assumptions (evidence level 6)

| Parameter | Nominal | Sweep range |
|---|---|---|
| process length (soma to PSI-contact region) | 50 µm | 50–500 µm |
| process diameter | 0.5 µm | 0.2–2 µm |
| synapse location along the assumed process | 50 µm | 0–50 µm |

The exploratory model runs a 15,528-row sensitivity analysis with robustness classification (ROBUST / PARAMETER-DEPENDENT / UNCONSTRAINED). The C-01 capacitance conflict is carried as **two explicit variants** and is never adjudicated. Calibration against the 4.71 mV somatic EPSP is a `MODEL_CALIBRATION`; the fitted g_PSI is preserved as a `model_derived_estimate` and is **not** a measurement of the PSI→MN5 synaptic conductance (which remains BLOCKED). Calibration always runs with the Dα7 component disabled.

---

## F. UNRESOLVED / BLOCKED LIST

Every parameter below has **no qualifying measurement** and is blocked from the biological model. Each is represented as absence (no value), never filled in.

| Parameter | Why blocked |
|---|---|
| PSI→MN5 synaptic conductance | No measurement in any source; `SynapticInterface.conductance()` raises. |
| PSI→MN5 spatial voltage transfer | **NOT AUTHORIZED** gate; `require_spatial_transfer()` raises. |
| Dα7 biological conductance | **NOT AUTHORIZED** gate; `Dalpha7Interface.conductance()` raises. |
| Dα7 single-channel conductance | No native measurement. |
| Dα7 open probability | No native measurement. |
| Dα7 reversal potential (biological) | No native measurement; the 0 mV model value is barred from being read back out. |
| Dα7 activation kinetics (biological) | No native measurement. |
| Dα7 desensitization kinetics (biological) | No native measurement. |
| Dα7 density at PSI→MN5 | No measurement; no Dα7 imaging at PSI terminals or MN5 axons. |
| PSI→MN5 reversal potential (biological) | No direct measurement. |
| MN1→MN5 coupling coefficient | Unreported. |
| tau_m (membrane time constant) | No qualifying MN5 measurement; `ReducedMN5` carries **no leak term** by construction. |
| Rm (specific membrane resistance, biological) | No Drosophila-specific measurement. |
| electrotonic length constant λ | Cannot be derived (Ra and Rm both blocked). |
| ShakB absolute conductance | No quantitative rectification law or absolute conductance in any source. |
| contact→soma / SIZ mapping | The ~100 µm SIZ estimate is not mapped onto MaleCNS coordinates without a justified registration. |
| specific membrane capacitance (biological) | The 1.0 µF/cm² default is a generic insect default, not a native MN5 measurement. |
| specific axial resistance Ra (biological) | No Drosophila-specific measurement. |
| leak conductance density g_pas (biological) | No native MN5 measurement. |
| leak reversal potential E_leak (biological) | −85 mV is a model convention, not the measured MN5 resting potential (−67.8 mV). |

---

## G. CONFLICT LIST

Three unresolved conflicts are preserved with **both sides, no preferred side, no corrected value**. A conflict is closed only by a measurement that adjudicates it or a source stating which value applies to which preparation — never by preference, averaging, or whichever value a model needs.

| ID | Parameter | Side A | Side B | Discrepancy |
|---|---|---|---|---|
| **C-01** | MN5 whole-cell capacitance | 43 ± 2 pF (Fayyazuddin+ 2006, n=22) | 127 ± 16 pF (Ryglewski & Duch 2009; same mean/SD re-reported by Herrera-Valdez+ 2013 = ONE measurement) | ~2.95× |
| **C-02** | GFS gap-junction conductance | 135.0 / 34.5 **µS** (Augustin 2019 Table 1, '(estimated)') | 135.0 / 34.5 **nS** (gfpn.py assigns to `gap2.g`, which `gap2.mod` declares in nanosiemens) | exactly 1000× |
| **C-03** | PSI→DLMn peak conductance | 80 **µS** (Augustin 2019 Table 1, '(estimated)') | 0.08 (gfpn.py `PSI_DLMn_wt`, no declared unit) | ~1000× |

**C-02 and C-03 are the same 1000× unit ambiguity in two different parameters.** For C-03 the live synapse runs on either the paper value (80 µS) or the source weight as written (0.08), chosen explicitly by `peak_conductance_source`; it converts nothing and decides nothing. For C-02, `from_unresolved_project_conductance()` always raises; a conductance must be supplied explicitly with its unit.

---

## H. FILES CHANGED

| File | Change |
|---|---|
| `research/parameter_adoption_ledger.csv` | **Created.** The canonical machine-readable adoption ledger (137 parameters, 15 columns). |
| `research/parameter_adoption_plan.md` | **Created.** This human-readable report (sections A–J). |
| `tests/test_parameter_adoption.py` | **Created.** Regression test pinning the adoption decisions (see §I). |

**No biological-model code was changed.** The existing architecture already implements every adoption decision; this pass consolidates and makes it explicit. The reduced MN5 model, the exploratory model, the active/passive backends, the synaptic and coupling primitives, and both scientific gates are unchanged.

---

## I. TEST RESULTS

A new regression test `tests/test_parameter_adoption.py` pins the adoption decisions:

1. **Ledger integrity** — the CSV parses, has the 15 required columns, and every row's classification is one of the five categories.
2. **No REPLACE / no DERIVE** — the ledger contains zero REPLACE and zero DERIVE rows (no stronger measurement exists; every would-be derivation is a forbidden conversion).
3. **Native measurements are KEEP** — the eight native MN5 measurements (resting, threshold, AP amplitude, Rin ×2, Cm ×2, EPSP) are all classified KEEP.
4. **Blocked parameters carry no value** — every REMAIN_UNRESOLVED row has an empty `replacement_value` (a blocked quantity is represented as absence, never filled in).
5. **Conflicts are preserved** — C-01, C-02 and C-03 each appear with both sides and no preferred side.
6. **Gates stay closed** — `require_spatial_transfer()` and `require_dalpha7_gate()` raise; `SynapticInterface.conductance()` raises; `ReducedMN5` consumes only the three uncontested native measurements.
7. **Forbidden conversions are absent** — no parameter is derived from mesh area, path length, contact distance or somatic EPSP.
8. **Fixtures are not biological** — the four direct-stimulus amplitudes are classified KEEP with `fixture` authorization, not `yes`.

(Full pytest summary captured in the final adoption report.)

---

## J. SCIENTIFIC GATE STATUS

| Gate | Status |
|---|---|
| PSI→MN5 spatial voltage transfer | **NOT AUTHORIZED** |
| Dα7 conductance | **NOT AUTHORIZED** |
| ShakB absolute conductance | **NOT AUTHORIZED** |
| 8G (PSI→DLMn) biological conductance | **UNRESOLVED** (C-03, ~1000×) |
| 7U (GFS gap-junction) biological unit interpretation | **UNRESOLVED** (C-02, exactly 1000×) |

Both scientific gates are enforced by `require_spatial_transfer()` and `require_dalpha7_gate()`, which raise rather than degrade. The two unit conflicts are preserved with both sides and no preferred side. **The biology is not completed, and that is the correct outcome.**

---

## Non-inference statement

The framework does not infer biological parameters from desired model outputs. No parameter was invented, averaged, converted across a forbidden boundary, or promoted from a model assumption to a biological measurement by this pass. Every parameter's epistemic status is now explicit in the ledger.
