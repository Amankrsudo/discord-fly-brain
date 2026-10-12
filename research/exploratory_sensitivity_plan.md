# Exploratory MN5 / PSI / Dα7 model — sensitivity analysis plan and results

Model: `biological_brain/exploratory_mn5.py` (`exploratory_mn5`, version 0.1.0)
Companion documents: `research/exploratory_mn5_model.md` (model description),
`research/exploratory_parameter_ranges.csv` (parameter table).

**This is an exploratory model, not a measurement.**
This model is not a measurement of MN5 spatial voltage transfer or Dα7 conductance. Every simulation output is a MODEL-DERIVED ESTIMATE, conditional on the explicit assumptions in the parameter table. The two gates are unchanged:

- PSI→MN5 postsynaptic spatial voltage transfer: NOT AUTHORIZED
- Dα7 biological conductance: NOT AUTHORIZED

## 1. Purpose

The project previously concluded "cannot model because some biological
parameters are unknown". This analysis replaces that with a transparent
best-effort model that runs across explicit plausible parameter ranges, while
keeping every unknown explicitly labelled as unknown. The sensitivity analysis
answers one question: **which qualitative conclusions survive plausible
parameter variation, and which do not?**

## 2. Sweep grids

The sweep grid is keyed by snake_case names; each maps to a parameter-table
name. No grid value is a biological "correct" value.

| Grid key | Parameter | Values | Tier |
|---|---|---|---|
| `axial_resistivity_ohm_cm` | axial resistivity (Ra) | 30, 90, 200, 400 Ω·cm | TIER B |
| `specific_membrane_capacitance_uf_cm2` | specific membrane capacitance (Cm_spec) | 0.6, 1.15, 2.6 µF/cm² | TIER B |
| `specific_membrane_resistance_kohm_cm2` | specific membrane resistance (Rm) | 6, 10, 20, 26 kΩ·cm² | TIER B |
| `cholinergic_reversal_mv` | cholinergic reversal potential (E_syn) | −15, 0, +10 mV | TIER B |
| `g_psi_ns` | PSI synaptic peak conductance (g_PSI) | 0.01, 0.1, 1, 10, 100, 1000 nS (log) | TIER C (free) |
| `g_dalpha7_ns` | Dα7 maximal conductance (g_Dα7) | 0.01, 0.1, 1, 10, 100, 1000 nS (log) | TIER C (free) |

The two logarithmic conductance ranges are broad and **not biologically
measured**; they exist to expose how conclusions depend on the free
parameters, not to bracket a biological value.

## 3. Design

Five designs, 2078 runs total (Forward Euler, dt = 0.01 ms, duration 15 ms,
adaptive substepping for numerical stability only):

1. **OFAT** (26 runs): every grid parameter varied alone at nominal values.
   The g_Dα7 OFAT runs with the Dα7 component enabled; all other OFATs run
   with the model's own Dα7 setting (disabled by default).
2. **TIER-B factorial** (288 runs): Ra × Cm_spec × Rm × E_syn (4×3×4×3 = 144
   combinations), run at **both** contested capacitance variants (C-01 stays
   explicit and is never adjudicated). g_PSI at its nominal 1 nS; Dα7 off.
3. **g_PSI main effect** (864 runs): TIER-B factorial × the six g_PSI values,
   Dα7 off.
4. **g_Dα7 main effect** (864 runs): TIER-B factorial × the six g_Dα7 values,
   Dα7 enabled, g_PSI at nominal.
5. **g_PSI × g_Dα7 interaction** (36 runs): the two logarithmic ranges
   crossed at nominal TIER-B values, Dα7 enabled.

The full six-way cross product (4·3·4·3·6·6 = 5184 combinations × 2 variants)
is **not** required to classify the conclusions and was not run; the
main-effects-plus-interaction design above is sufficient because every
classification below depends only on one design's outcome set.

## 4. Classification rules

| Class | Rule |
|---|---|
| **ROBUST** | Same qualitative conclusion across the evidence-bounded (TIER B) parameter sets. |
| **PARAMETER-DEPENDENT** | Conclusion changes across parameter sets whose ranges current evidence bounds (TIER B). |
| **UNCONSTRAINED** | Conclusion cannot be meaningfully bounded by current evidence because it depends on a TIER C free parameter — whether or not the outcome happens to be constant across the assumed sweep range. A free parameter has no evidence-bounded plausible range, so no sweep over it can bound a conclusion. |

## 5. Results (real numbers from the implemented model)

Nominal run (variant A, g_PSI = 1 nS, cable mode, Dα7 off): local synaptic
peak depolarization **12.72 mV**, somatic peak **2.06 mV**, attenuation
**0.162** (MODEL-DERIVED ESTIMATE), time to peak 3.81 ms. The measured MN5
threshold excursion is 43.7 mV (V_rest −67.8 mV → V_th −24.1 mV); the
nominal somatic response does not come close.

**OFAT somatic peak depolarization (mV):**

| Parameter | Values → somatic peak (mV) |
|---|---|
| Ra (Ω·cm) | 30 → 2.30; 90 → 2.06; 200 → 1.73; 400 → 1.36 |
| Cm_spec (µF/cm²) | 0.6 → 2.07; 1.15 → 2.06; 2.6 → 2.02 |
| Rm (kΩ·cm²) | 6 → 2.06; 10 → 2.08; 20 → 2.10; 26 → 2.10 |
| E_syn (mV) | −15 → 1.60; 0 → 2.06; +10 → 2.36 |
| g_PSI (nS) | 0.01 → 0.024; 0.1 → 0.24; 1 → 2.06; 10 → 9.05; 100 → 15.72; 1000 → 18.78 |
| g_Dα7 (nS, Dα7 on) | 0.01 → 2.07; 0.1 → 2.24; 1 → 4.01; 10 → 13.19; 100 → 19.59; 1000 → 20.61 |

**Design summaries:**

| Design | Runs | Somatic peak (mV) | Attenuation | Threshold crossings |
|---|---|---|---|---|
| 2. TIER-B factorial, both Cm variants | 288 | 0.53 – 2.68 | 0.022 – 0.408 | 0 |
| 3. g_PSI main effect | 864 | 0.014 – 41.47 | 0.040 – 0.538 | 0 |
| 4. g_Dα7 main effect (Dα7 on) | 864 | 1.04 – 38.35 | 0.043 – 0.571 | 0 |
| 5. g_PSI × g_Dα7 interaction | 36 | 0.052 – 20.61 | 0.162 – 0.305 | 0 |

**Calibration (MODEL_CALIBRATION, comparison target only):** fitting g_PSI to
the published somatic EPSP (4.71 ± 0.35 mV, Fayyazuddin+ 2006) yields
g_PSI = **2.95 nS** (variant A) / **9.38 nS** (variant B). The fitted values
are MODEL-DERIVED ESTIMATES, not measurements of the PSI→MN5 synaptic
conductance, which remains BLOCKED. Calibration always runs with Dα7 disabled.

## 6. Conclusions and robustness classification

| # | Conclusion | Class |
|---|---|---|
| 1 | A PSI synaptic input produces a local depolarization at the synaptic site (all 2078 runs: local peak > 0). | **ROBUST** |
| 2 | The somatic response is attenuated relative to the local synaptic response (all cable-mode runs: attenuation < 1). | **ROBUST** |
| 3 | At the nominal g_PSI, the somatic response does **NOT** cross the MN5 spike threshold anywhere in the literature-bounded (TIER B) parameter space (0 of 288 runs cross). | **ROBUST** |
| 4 | Whether the somatic response can cross the threshold by varying the free g_PSI. Across the assumed decade range the somatic peak saturates below the 43.7 mV excursion (OFAT max 18.78 mV; design 3 max 41.47 mV), but g_PSI has no evidence-bounded plausible range, so the question cannot be bounded. | **UNCONSTRAINED** |
| 5 | The Dα7 component's effect on the somatic response. Within the model it raises the somatic peak (design 4 spans 1.04–38.35 mV), but g_Dα7 is free, so the size of the effect cannot be bounded. | **UNCONSTRAINED** |
| 6 | The contested whole-cell capacitance (C-01) changes the peak somatic response: variant A (43 pF) and variant B (127 pF) peaks differ by roughly a factor of two across every design. | **PARAMETER-DEPENDENT** |

## 7. What this design deliberately does not do

- It does not sweep the TIER C kinetics (synaptic rise/decay, Dα7
  activation/desensitization) or the geometry assumptions; those are carried as
  explicit assumptions, not swept, because sweeping them would not change any
  classification (they are all free parameters — UNCONSTRAINED by rule).
- It does not hard-code a biological "correct" value anywhere in the grid.
- It does not write anything back to the frozen evidence registry
  (`research/model_input_freeze.csv`); the model owns a private parameter set.
- It does not open either gate. The cable-mode attenuation is a
  MODEL-DERIVED ESTIMATE and the experimental spatial-transfer gate remains
  closed.

**Exploratory-model authorization labels:** this sensitivity analysis is `MODEL-AUTHORIZED / ANATOMY + LITERATURE CONSTRAINED` only for conditional, assumption-dependent model calculations. This label does not authorize native biological inference; PSI→MN5 spatial voltage transfer and native Dα7 conductance remain **NOT AUTHORIZED**.

**Authorization and evidence limits:** `MODEL-AUTHORIZED / ANATOMY + LITERATURE CONSTRAINED` and `MODEL-AUTHORIZED / CHANNEL-CONSTRAINED / NATIVE VALUE MODEL-DERIVED` authorize only conditional model calculations. Outputs are **MODEL-DERIVED**, not native biological measurements. The available somatic EPSP is **not an experimental voltage-transfer measurement**, and no anatomically reconstructed contact-to-soma path exists. PSI→MN5 spatial voltage transfer and native Dα7 conductance remain **NOT AUTHORIZED** for native biological inference.
