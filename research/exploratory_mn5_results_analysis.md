# Exploratory MN5 / PSI / Dα7 results analysis

This analyzes the existing exploratory model and its sensitivity sweeps; it
does not build or validate a biological model. Every simulated voltage,
attenuation and fitted conductance below is a **MODEL-DERIVED ESTIMATE**,
conditional on the model assumptions. The published 4.71 ± 0.35 mV MN5 EPSP
is a comparison target only (reported under GF stimulation, not direct PSI
stimulation). Matching it is not model validation.

This model is not a measurement of MN5 spatial voltage transfer or Dα7 conductance.

The two hard gates remain closed:

- PSI→MN5 postsynaptic spatial voltage transfer: NOT AUTHORIZED
- Dα7 biological conductance: NOT AUTHORIZED

## A. ROBUST MODEL CONCLUSIONS

- With a positive PSI conductance, the model produces a local depolarization;
  all captured runs have a positive local peak. The nominal C-01 A, 1 nS
  result is 12.72 mV locally and 2.06 mV somatically (attenuation 0.162).
- In cable mode, somatic voltage is below local voltage in every captured
  run. This inequality is robust **within this model**; no value is a measured
  MN5 attenuation. The attenuation is a MODEL-DERIVED ESTIMATE, NOT an experimental spatial-transfer measurement.
- No captured run crosses threshold: 0/2592 across the captured sweep
  designs. At nominal g_PSI, 0/288 TIER-B × C-01 runs cross. This is a
  finding within the explored settings, not evidence that the biological
  pathway cannot cross threshold.
- At nominal g_PSI, changing specific Rm (6–26 kΩ·cm²) changes the
  somatic peak only 2.06–2.10 mV; changing specific Cm (0.6–2.6 µF/cm²)
  changes it 2.02–2.07 mV. These effects are negligible over those model
  ranges only.

| Output | Conclusion | Classification |
|---|---|---|
| Local peak sign | Positive throughout captured runs; magnitude depends on free g_PSI. | Sign ROBUST; magnitude UNCONSTRAINED |
| Somatic peak / attenuation | Soma remains below local voltage; quantitative values vary with assumptions. | Inequality ROBUST; value PARAMETER-DEPENDENT |
| Threshold | No crossing in the explored runs. | ROBUST within sweep; biological capability UNCONSTRAINED |
| Calibrated g_PSI | Nominal fit shifts with C-01; it is not a measured PSI conductance. | PARAMETER-DEPENDENT |
| Dα7 effect | Depends strongly on the free conductance assumption. | UNCONSTRAINED biologically |

## B. PARAMETER-DEPENDENT MODEL CONCLUSIONS

The transparent ranking below uses Spearman rank correlation with average ranks for ties on the existing TIER-B × g_PSI sweep (864 runs per C-01 variant). Correlation ranks monotone association in this design; it is not a causal or biological importance measure. Nominal-point OFAT ranges are shown alongside it.

| Input | Somatic rank association (A / B) | Nominal OFAT somatic peak | Interpretation |
|---|---:|---:|---|
| g_PSI, 0.01–1000 nS (free) | +0.916 / +0.931 | 0.024–18.78 mV | Dominates response magnitude in the sweep; its biological value is unconstrained. |
| Ra, 30–400 Ω·cm | −0.266 / −0.246 | 1.36–2.30 mV | Strongest swept passive effect on soma; attenuation changes about 9× across the OFAT range. |
| E_syn, −15 to +10 mV | +0.117 / +0.121 | 1.60–2.36 mV | Moderate driving-force dependence in this model. |
| Rm, 6–26 kΩ·cm² | +0.014 / +0.015 | 2.06–2.10 mV | Negligible effect in-range. |
| Specific Cm, 0.6–2.6 µF/cm² | −0.011 / approximately 0 | 2.02–2.07 mV | Negligible effect in-range; distinct from whole-cell C-01. |

Therefore **g_PSI dominates somatic response magnitude**;
Ra is the dominant passive uncertainty in transfer. The g_PSI range is a
free exploratory range, not a biological bound. The C-01 effect is
quantified separately because it is not a TIER-B sweep input.

At fixed nominal g_PSI, Ra changes local peak 5.68–29.86 mV and cable
attenuation 0.046–0.405 as Ra rises from 30 to 400 Ω·cm. Across the full
captured parameter designs, somatic peaks span 0.0075–41.47 mV and
attenuation spans 0.019–0.571. The magnitudes are not biological bounds.

### C-01 remains unresolved

Both reported whole-cell capacitance variants are retained without
adjudication: A = 43 pF and B = 127 pF. Across the 144 TIER-B combinations
at g_PSI = 1 nS, A/B ratios are:

| Output | A/B ratio range (median) | Consequence |
|---|---:|---|
| Somatic peak | 1.88–2.08× (2.04×) | Materially different somatic prediction. |
| Local peak | 1.00–1.13× (1.02×) | Nearly unchanged. |
| Attenuation | 1.84–2.02× (1.97×) | Model-derived attenuation changes materially. |
| Threshold crossing | 0 in both variants | No change to the no-crossing result in these runs. |

Nominal MODEL_CALIBRATION to 4.71 mV requires g_PSI ≈ 2.95 nS for A and
≈ 9.38 nS for B (3.17×). These are **MODEL-DERIVED ESTIMATES, not measured
PSI conductances**.

### Published EPSP target and parameter regions

Log-space calibration across all 144 TIER-B combinations × both C-01
variants gives these model-only reachability results, using the existing
g_PSI range [0.01, 1000] nS:

- **CENTRAL:** 240/288 (83.3%) reach the target inside the range. Of those,
  77.9% of fitted values lie in the central third of the log range and 22.1%
  in its upper interior third. Fitted g_PSI spans 1.87–213.4 nS (median
  6.33 nS).
- **EDGE:** 12/288 (4.2%) touch the target band only at g_PSI = 1000 nS.
- **OUTSIDE CURRENT EXPLORATORY RANGE:** 36/288 (12.5%) do not reach the
  target band by 1000 nS and would require a larger assumed conductance.

This demonstrates numerical reachability for many parameter sets, not
biological plausibility, identification of g_PSI, or model validation. The
range is not expanded.

## C. CURRENTLY UNCONSTRAINED

- **Absolute local and somatic response magnitudes:** depend strongly on
  free g_PSI; its sweep limits are assumptions.
- **Biological threshold capability:** no threshold crossing occurs in the
  explored model runs, but the free g_PSI range cannot bound the real
  pathway's capability.
- **Dα7:** with the component enabled, varying free g_Dα7 from 0.01 to
  1000 nS raises the nominal-configuration somatic peak from 2.07 to
  20.61 mV (+0.9% to +903% vs disabled baseline); the local peak changes
  from 12.78 to 67.47 mV. Thus the model effect is parameter-dependent,
  not negligible or robust across this assumed sweep, and its biological
  size is UNCONSTRAINED. These are not native Dα7 conductance or physiology.
- The existing sensitivity grid does **not** vary E_Dα7: it remains at its
  nominal 0 mV value. Dα7 kinetics also remain at their assumed defaults.
  Effects outside these fixed assumptions are unconstrained.
- Absolute spatial transfer remains unconstrained: cable attenuation depends
  on assumed geometry and passive parameters, and the spatial-transfer gate
  remains NOT AUTHORIZED.

The Dα7 component is exploratory and assumption-dependent. Calibration
values are MODEL_CALIBRATION outputs, **not fitted biological parameters**.
The frozen evidence registry and `reduced_mn5.py` were not changed; no range expansion was made.
