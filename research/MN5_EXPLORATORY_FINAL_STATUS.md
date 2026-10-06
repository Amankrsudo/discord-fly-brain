# MN5 Exploratory Model — Final Status

## 1. Objective

Explore, with explicit assumptions, how an input at the putative PSI-contact
process could produce local and somatic MN5 voltage responses, how passive
properties affect their relationship, and how an optional Dα7 component
changes model output. The goal was a transparent exploratory model, not a
biological parameter estimate or validation.

## 2. Evidence base

The evidence ledger, frozen input registry, anatomy registry, and model
parameter table retain distinct provenance. In this summary, **native
measurement**, **anatomical measurement**, **literature-derived parameter**,
**model assumption**, **model-derived estimate**, and **model calibration**
are not interchangeable.

- **Native experimental measurements:** MN5 resting potential
  (−67.8 ± 5.5 mV SD), spike threshold (−24.1 ± 8.2 mV SD), input
  resistance reports (102 ± 12 and 97 ± 31 MΩ), and the two conflicting
  whole-cell capacitance reports (43 ± 2 and 127 ± 16 pF SD). These are
  carried with their source and limitations in the evidence registry.
  The 4.71 ± 0.35 mV (SEM, n=10) somatic EPSP is also a native experimental
  observation, but it was recorded under GF stimulation; PSI was not
  directly stimulated and distal amplitude was not reported.
- **Anatomical measurements:** MaleCNS v1.0 records 43 verified PSI→MN5
  contacts (17 and 26 at minconf 0.5) and assigns
  `compartment_post="axon"` to all 43. The measured straight-line
  contact-to-somaLocation distances span 110.3–172.9 µm; a straight line is
  not a path length. These are anatomical/connectomic observations and
  labels, not electrical measurements. Available geometric tree paths do
  not provide electrotonic distance or voltage transfer; the soma-proxy
  path is conditional on a proxy assumption, and the traced MN5
  reconstructions have no soma node.
- **Literature-derived parameters:** exploratory ranges are used for Ra
  (30–400 Ω·cm), specific membrane capacitance (0.6–2.6 µF/cm²), specific
  membrane resistance (6–26 kΩ·cm²), and E_syn (−15 to +10 mV). These draw
  on generic insect or cross-context modeling precedent, not native MN5
  measurements. The ranges are assumptions for exploration, not confidence
  intervals. An E_Dα7 range is listed separately; it was not independently
  swept and stayed at 0 mV.
- **Model assumptions:** g_PSI and g_Dα7 are free exploratory conductances
  (each swept from 0.01 to 1000 nS); synaptic/receptor kinetics,
  desensitization, and simplified process geometry are assumed. Their
  sweep ranges do not bound biological values.
- **Model-derived estimates:** simulated local/somatic voltages, attenuation,
  threshold comparisons, and sensitivity results are outputs conditional
  on the chosen model parameters. They are not measurements.
- **Model-calibration outputs:** fitted g_PSI values result from fitting the
  model to the published somatic EPSP target. They are model-derived
  estimates, not measured PSI conductances.

## 3. Model

The existing [exploratory MN5 implementation](../biological_brain/exploratory_mn5.py)
uses a two-compartment soma/process cable-style abstraction. A
double-exponential PSI-like conductance drives the assumed contact-bearing
process; axial coupling transfers current to the soma. An optional
assumption-based Dα7 conductance contributes a separate process current.
Cable-mode attenuation emerges from assumed geometry and passive
parameters. The model is separate from the evidence-safe reduced model.

## 4. Main results

### ROBUST WITHIN MODEL SPACE

- Captured PSI-input runs produced a positive local depolarization.
- In cable mode, somatic response remained below local response in all
  captured runs.
- No captured run crossed the model's MN5 threshold comparison (0/2592);
  at nominal g_PSI, none of the 288 TIER-B × C-01 runs crossed.
- Rm and specific Cm effects on the nominal somatic peak were small within
  their tested ranges. This does not establish their biological effects
  outside those ranges.

### PARAMETER-DEPENDENT

- g_PSI had the strongest rank association with somatic peak (+0.916/+0.931
  for C-01 A/B); Ra had the strongest passive influence on the cable-mode
  attenuation (nominal OFAT 0.046–0.405 across its tested range).
- E_syn, C-01, and assumed g_Dα7 changed modeled outputs. The C-01
  consequences are detailed below.
- These are sensitivities in the analyzed model designs, not evidence of
  biological causation or parameter importance.

### BIOLOGICALLY UNCONSTRAINED

Absolute PSI response magnitude and real-pathway threshold capability
remain unconstrained because g_PSI has no evidence-bounded biological
range. Absolute spatial voltage transfer and the biological size of any
Dα7 effect are also unconstrained.

## 5. C-01 conflict

C-01 remains unresolved: one native report gives 43 ± 2 pF; another gives
approximately 127 ± 16 pF SD. Across the 144 TIER-B combinations at
assumed g_PSI = 1 nS, the variant A/B ratios were 1.88–2.08× (median
2.04×) for somatic peak, 1.00–1.13× (median 1.02×) for local peak, and
1.84–2.02× (median 1.97×) for cable-mode attenuation. Neither report is
selected or reconciled here.

## 6. EPSP comparison

The published 4.71 ± 0.35 mV somatic EPSP is a comparison target, not a
directly stimulated PSI→MN5 measurement. At nominal exploratory settings,
model calibration returned about 2.95 nS under C-01 A and 9.38 nS under
C-01 B. These are **MODEL_CALIBRATION / MODEL-DERIVED ESTIMATES**, not
measured PSI conductances.

Across 288 TIER-B × C-01 settings, 240 (83.3%) reached the target within
the existing g_PSI sweep; 12 were edge-only and 36 did not reach the target
band within range. **Reachability/calibration ≠ validation.** Matching a
comparison target does not validate the model or identify a biological
conductance.

## 7. Dα7

The existing sweep varied assumed g_Dα7 from 0.01 to 1000 nS with g_PSI
held at nominal 1 nS and the other Dα7 settings held at their assumed
defaults. At nominal configuration, the model-produced somatic peak
increased from about 2.07 to 20.61 mV; no Dα7 main-effect run crossed
threshold. This establishes parameter sensitivity of the model output,
not native Dα7 physiology or conductance.

**E_Dα7 was not independently swept.** It remained at 0 mV. Dα7
conductance, reversal, kinetics, and biological effect therefore remain
unestablished by this model.

## 8. Hard gates

PSI→MN5 spatial voltage transfer:  
**NOT AUTHORIZED**

Dα7 biological conductance:  
**NOT AUTHORIZED**

## 9. Final scientific interpretation

This project has established a reproducible, explicitly assumption-based
way to explore a simplified PSI-like input to MN5 and identify which
outputs are robust or sensitive within its tested space. It shows that
assumed g_PSI dominates modeled response magnitude, Ra strongly shapes
modeled transfer, and unresolved C-01 affects somatic predictions. It has
not established the real synaptic conductance, spatial voltage transfer,
threshold behavior, or native Dα7 contribution.

## 10. What would require new evidence

- Directly measured PSI→MN5 synaptic conductance/reversal and local-versus-
  somatic voltage response under identified PSI stimulation.
- Native MN5 electrical transfer constraints and soma/contact geometry
  sufficient to ground spatial-transfer estimates.
- Direct evidence for Dα7 conductance, reversal, and kinetics at the
  relevant native synapse.
- Resolution or better source-level characterization of the C-01
  capacitance discrepancy.

These are evidence gaps, not a new model-development plan. See the
[final exploratory model report](./exploratory_mn5_final_report.md),
[results analysis](./exploratory_mn5_results_analysis.md),
[model description](./exploratory_mn5_model.md), [parameter table](./exploratory_parameter_ranges.csv),
[sensitivity table](./exploratory_mn5_parameter_sensitivity.csv),
[sensitivity plan](./exploratory_sensitivity_plan.md), and project
[evidence ledger](./evidence_ledger.md) for detailed provenance.
