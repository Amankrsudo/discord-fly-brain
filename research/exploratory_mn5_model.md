# Exploratory MN5 / PSI / Dα7 mechanistic model

Model: `biological_brain/exploratory_mn5.py` (`exploratory_mn5`,
version 0.1.0)
Companion documents: `research/exploratory_sensitivity_plan.md`
(sensitivity design and results),
`research/exploratory_parameter_ranges.csv` (parameter table),
`tests/test_exploratory_mn5.py` (safety and behaviour tests).

> **This model is not a measurement of MN5 spatial voltage transfer or Dα7 conductance.** It is a best-effort EXPLORATORY model. Every simulation output is a MODEL-DERIVED ESTIMATE, conditional on the explicit assumptions listed below. It moves the project from "cannot model because some biological parameters are unknown" to "can run a transparent best-effort model across explicit plausible parameter ranges" — without claiming that any unknown biology has become known.

## 1. Purpose

Provide a transparent, best-effort mechanistic model of the
PSI→MN5 pathway that (a) runs across explicit plausible parameter
ranges, (b) carries every parameter with an explicit provenance and
tier, (c) classifies every qualitative conclusion as ROBUST,
PARAMETER-DEPENDENT or UNCONSTRAINED, and (d) opens no gate and
writes nothing to the frozen evidence registry.

## 2. Evidence-safe boundary

**Exploratory-model authorization labels:** the simulation surface is `MODEL-AUTHORIZED / ANATOMY + LITERATURE CONSTRAINED` for its explicitly assumption-dependent model output, and `MODEL-AUTHORIZED / CHANNEL-CONSTRAINED / NATIVE VALUE MODEL-DERIVED` for its optional Dα7 model component. These labels authorize only conditional model calculations. They do **not** authorize native biological inference: the PSI→MN5 spatial voltage-transfer and native Dα7 conductance gates below remain **NOT AUTHORIZED**.


- The model owns a **private** `ParameterSet`. It does not read
  `research/model_input_freeze.csv` at run time and never writes to
  it; no synthetic value can enter the registry.
- It is a **separate layer** from the evidence-safe reduced model in
  `reduced_mn5.py`, which remains unchanged.
- Gates (unchanged):
  - PSI→MN5 postsynaptic spatial voltage transfer: NOT AUTHORIZED
  - Dα7 biological conductance: NOT AUTHORIZED
- `require_spatial_transfer()` and `require_dalpha7_gate()` from the
  model framework still raise `BlockedParameterError`; this model
  does not call them and does not bypass them.
- The contested whole-cell capacitance (C-01) is carried as **two
  explicit variants** and is never silently adjudicated: the
  constructor requires `capacitance_variant="A"` or `"B"` and raises
  otherwise.

## 3. Parameter provenance table

24 parameters in four tiers. The full table with sources, ranges,
conflicts and notes is `research/exploratory_parameter_ranges.csv`.

| Tier | Count | Provenance | Meaning |
|---|---|---|---|
| TIER_A_NATIVE_MEASUREMENT | 7 | NATIVE_EXPERIMENTAL_MEASUREMENT | Frozen MN5 measurements (resting, threshold, AP amplitude, two Rin sets, two contested Cm variants) |
| TIER_B_LITERATURE_DERIVED_RANGE | 5 | LITERATURE_DERIVED_PASSIVE_PARAMETER | Literature-constrained ranges (Ra, Cm_spec, Rm, E_syn, E_Dα7) — **not** native MN5 measurements |
| TIER_C_FREE_EXPLORATORY_PARAMETER | 9 | MODEL_ASSUMPTION | Free parameters (g_PSI, g_Dα7, Dα7 density/kinetics, synaptic kinetics, effective transfer ratio) |
| TIER_GEOMETRY_MODEL_ASSUMPTION | 3 | MODEL_ASSUMPTION | Geometry assumptions (process length, diameter, synapse location) |

## 4. Native MN5 measurements (TIER A)

| Parameter | Value | Source |
|---|---|---|
| MN5 resting potential | −67.8 ± 5.5 SD mV (n=13) | Ryglewski, Kilo & Duch 2014 Eur J Neurosci 39:151 |
| MN5 spike threshold | −24.1 ± 8.2 SD mV (n=11) | Ryglewski, Kilo & Duch 2014 |
| MN5 action-potential amplitude | 45.5 ± 8.6 SD mV (n=13) | Ryglewski, Kilo & Duch 2014 (reference only; no AP shape is modelled) |
| MN5 input resistance (set 1) | 102 ± 12 MΩ (n=22) | Fayyazuddin+ 2006 PLoS Biol 4(3):e63 |
| MN5 input resistance (set 2) | 97 ± 31 MΩ (n=52) | Herrera-Valdez+ 2013 J Comput Neurosci 34:211 |
| MN5 whole-cell capacitance (variant A) | 43 ± 2 pF (n=22) | Fayyazuddin+ 2006 — **C-01 contested** |
| MN5 whole-cell capacitance (variant B) | 127 ± 16 SD pF | Ryglewski & Duch 2009 J Neurophysiol 102:3673 — **C-01 contested** |

The C-01 conflict (43 pF vs 127 pF, ~2.95×) is **unresolved** and
is carried explicitly as two variants. Both variants are run in the
sensitivity analysis; neither is preferred.

## 5. Literature-constrained ranges (TIER B)

| Parameter | Nominal | Plausible range | Note |
|---|---|---|---|
| axial resistivity Ra | 90 Ω·cm | 30–400 Ω·cm | Generic insect default adopted by prior MN5 models; **not** a native MN5 measurement |
| specific membrane capacitance Cm_spec | 1.15 µF/cm² | 0.6–2.6 µF/cm² | Generic default; distinct from the contested whole-cell Cm (C-01) |
| specific membrane resistance Rm | 6 kΩ·cm² | 6–26 kΩ·cm² | Cross-context/model-derived (from g_pas = 1.667e-4 S/cm²); **no Drosophila-specific Rm has ever been measured** |
| cholinergic reversal potential E_syn | 0 mV | −15 to +10 mV | Generic vertebrate α7 figure; **not** a PSI→MN5 measurement |
| Dα7 reversal potential E_Dα7 | 0 mV | −15 to +10 mV | Carried separately from E_syn so the two can be swept independently |

## 6. Explicit assumptions (TIER C + geometry)

All of the following are **MODEL_ASSUMPTION** with no biological
value. Nominal values are round exploratory midpoints, not estimates.

| Parameter | Nominal | Range | Scale |
|---|---|---|---|
| PSI synaptic peak conductance g_PSI | 1 nS | 0.01–1000 nS | log |
| Dα7 maximal conductance g_Dα7 | 1 nS | 0.01–1000 nS | log |
| Dα7 receptor density (relative) | 1 | 0.01–100 | log |
| Dα7 activation time constant | 1 ms | 0.1–10 ms | linear |
| Dα7 desensitization time constant | 5 ms | 1–50 ms | linear |
| Dα7 steady-state desensitization fraction | 0.5 | 0–0.95 | linear |
| PSI synaptic rise time constant | 0.5 ms | 0.1–2 ms | linear |
| PSI synaptic decay time constant | 2 ms | 0.5–10 ms | linear |
| effective spatial transfer ratio | — (unused in cable mode) | 0–1 | linear |
| process length (soma to PSI-contact region) | 50 µm | 50–500 µm | linear |
| process diameter | 0.5 µm | 0.2–2 µm | linear |
| synapse location along the assumed process | 50 µm | 0–50 µm | linear |

The 50 µm process length is anchored on the documented PSI contact
SPAN in the peripheral nerve (Fayyazuddin+ 2006: contacts "span 50
µm" of the PDMN); the soma-to-contact path length itself is
unmeasured, so 50 µm is a lower-anchored assumption.

## 7. PSI synaptic model

Double-exponential conductance kinetics (rise/decay), integrated
with Forward Euler (dt = 0.01 ms, duration 15 ms, adaptive
substepping for numerical stability only — the subdivision changes
no parameter, no provenance and no conclusion):

    g_syn(t) = g_PSI · (exp(−t/τ_decay) − exp(−t/τ_rise)) / norm
    I_syn(t) = g_syn(t) · (E_syn − V_process)

- Kinetics (τ_rise, τ_decay) are MODEL_ASSUMPTION — millisecond-scale
  exploratory values, **not** MN5/PSI-native.
- g_PSI is a free TIER C parameter; no PSI→MN5 synaptic conductance
  has ever been measured in any source.
- E_syn is a generic cholinergic exploratory range, **not** a
  PSI→MN5 measurement.
- The model contains no synaptic plasticity, no vesicle dynamics and
  no receptor trafficking.

## 8. Dα7 exploratory model

An optional Dα7 receptor component (enabled with
`dalpha7_enabled=True`):

    g_Dα7(t) = g_Dα7_max · (1 − exp(−t/τ_act)) · (1 − D_∞·(1 − exp(−t/τ_des)))
    I_Dα7(t) = g_Dα7(t) · (E_Dα7 − V_process)

with a free maximal conductance, activation and desensitization time
constants, a steady-state desensitization fraction and an optional
Ca-permeability factor (carried as the relative density parameter;
no absolute density is implied).

**The Dα7 component is exploratory and assumption-dependent.** It is
never used to retroactively justify the existence or magnitude of the
PSI conductance: calibration always runs with the Dα7 component
disabled, and enabling Dα7 never changes any g_PSI value.

## 9. Spatial transfer implementation

Two modes, kept apart:

- **cable** (default): the process is a single cylindrical
  compartment with axial resistance derived from Ra, length and
  diameter; attenuation emerges from the two-compartment integration
  and is reported as a **MODEL-DERIVED ESTIMATE**. The experimental
  spatial-transfer gate remains closed.
- **explicit**: the caller supplies `transfer_ratio` directly
  (a MODEL_ASSUMPTION in [0, 1]; never defaulted, never measured);
  the somatic peak is `transfer_ratio × local peak` and the
  attenuation is labelled `model_assumption`.

Nominal cable-mode attenuation is 0.162 (variant A) / 0.081
(variant B) at g_PSI = 1 nS. Neither number is a measurement.

## 10. Sensitivity design

Five designs, 2078 runs: OFAT (26), TIER-B factorial at both
capacitance variants (288), g_PSI main effect (864), g_Dα7 main
effect with Dα7 enabled (864), and the g_PSI × g_Dα7 interaction
(36). Grids: Ra {30, 90, 200, 400} Ω·cm; Cm_spec {0.6, 1.15, 2.6}
µF/cm²; Rm {6, 10, 20, 26} kΩ·cm²; E_syn {−15, 0, +10} mV; g_PSI
and g_Dα7 {0.01, 0.1, 1, 10, 100, 1000} nS (log). Full design,
grids and rules are in `research/exploratory_sensitivity_plan.md`.

## 11. Robustness classification

- **ROBUST** — same qualitative conclusion across the evidence-bounded
  (TIER B) parameter sets.
- **PARAMETER-DEPENDENT** — conclusion changes across parameter sets
  whose ranges current evidence bounds (TIER B).
- **UNCONSTRAINED** — conclusion depends on a TIER C free parameter
  whose plausible range current evidence cannot bound; it cannot be
  meaningfully bounded whether or not the outcome happens to be
  constant across the assumed sweep range.

Classified conclusions (see the sensitivity plan for the numbers):

1. A PSI synaptic input produces a local depolarization — **ROBUST**.
2. The somatic response is attenuated relative to the local response
   (cable mode) — **ROBUST**.
3. At the nominal g_PSI, the somatic response does **not** cross the
   MN5 spike threshold anywhere in the TIER B parameter space
   (0/288 runs) — **ROBUST**.
4. Whether threshold crossing can be reached by varying the free
   g_PSI — **UNCONSTRAINED**.
5. The Dα7 component's effect on the somatic response —
   **UNCONSTRAINED**.
6. The contested whole-cell capacitance (C-01) changes the peak
   somatic response (~2× between variants) — **PARAMETER-DEPENDENT**.

## 12. Comparison with known MN5 observations

The published MN5 somatic EPSP is 4.71 ± 0.35 mV (Fayyazuddin+
2006, n=10, GF stimulated, somatic whole-cell; PSI was never directly
stimulated and the distal amplitude is unreported). It is used as a
**comparison target only**: MODEL_CALIBRATION fits g_PSI to it,
yielding g_PSI = 2.95 nS (variant A) / 9.38 nS (variant B). The
fitted conductances are **MODEL-DERIVED ESTIMATES**, not
measurements of the PSI→MN5 synaptic conductance, which remains
BLOCKED. Because the published EPSP was recorded under GF stimulation
(the whole pathway, not an isolated PSI→MN5 event), the comparison is
against a pathway-filtered somatic voltage.

## 13. What the model can conclude

- A cholinergic PSI-like synaptic input onto the assumed process
  compartment produces a local depolarization under every parameter
  set tested (ROBUST).
- The somatic response is smaller than the local response in cable
  mode under every parameter set tested (ROBUST).
- At the nominal g_PSI, no combination of the literature-bounded
  passive parameters (Ra, Cm_spec, Rm, E_syn) brings the soma to
  threshold (ROBUST negative finding, 0/288 runs).
- The C-01 capacitance choice changes the somatic peak by roughly a
  factor of two, so any quantitative somatic prediction is
  PARAMETER-DEPENDENT on the unresolved conflict.

## 14. What the model cannot conclude

- Whether the somatic response can reach threshold: the answer depends
  on the free g_PSI, whose plausible range no evidence bounds
  (UNCONSTRAINED). Even at g_PSI = 1000 nS the somatic peak
  saturates below the 43.7 mV threshold excursion — but the sweep
  range is an assumption, not a bound.
- Anything quantitative about Dα7: its conductance, density and
  kinetics are all free (UNCONSTRAINED).
- Any absolute spatial attenuation: the cable-mode number depends on
  unmeasured geometry and unmeasured Ra/Rm; the experimental
  spatial-transfer gate remains closed.
- Any biological "correct" value for a swept parameter: the grids are
  exploratory ranges, not confidence intervals.

## 15. Remaining biological uncertainties

- PSI→MN5 synaptic conductance, reversal potential and receptor
  identity (the registry records receptor identity as ASSUMPTION and
  the conductance as BLOCKED).
- Dα7 conductance, density, kinetics and reversal at PSI→MN5 (all
  BLOCKED in the registry; all free here).
- MN5 process geometry (length, diameter, soma-to-contact path) —
  unmeasured; only the 50 µm contact span is documented.
- MN5 specific membrane resistance — never measured in Drosophila.
- The C-01 whole-cell capacitance conflict (43 vs 127 pF).
- Whether the two-compartment reduction captures the electrotonic
  structure of the real MN5 arbor (the MaleCNS mesh cannot currently
  resolve the contact→soma path: zero kind=1 nodes).

---

**Final gate status (unchanged):**

- PSI→MN5 postsynaptic spatial voltage transfer: NOT AUTHORIZED
- Dα7 biological conductance: NOT AUTHORIZED

This model is not a measurement of MN5 spatial voltage transfer or Dα7 conductance.


Clarification: no anatomically reconstructed contact-to-soma path exists.

Clarification: the available somatic EPSP is not an experimental voltage-transfer measurement.
