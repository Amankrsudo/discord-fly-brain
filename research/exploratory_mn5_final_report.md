# Exploratory MN5 / PSI / Dα7 model — final report

## A. Executive summary

This is a best-effort exploratory model: verified biology is kept distinct
from literature-derived parameter ranges and explicit assumptions. It is
not a biological validation. The implementation is a two-compartment
soma/process cable-style simulation. At the nominal C-01 A setting
(43 pF) and assumed g_PSI = 1 nS, the model produced a local peak of
12.72 mV, a somatic peak of 2.06 mV, and an attenuation of 0.162.
Every simulated voltage, attenuation, and calibration result is a
**MODEL-DERIVED ESTIMATE** under the stated parameters.

The strongest sweep findings are that the modeled local response is
depolarizing, cable-mode somatic response is below the local response, and
no explored run crosses the MN5 threshold. g_PSI dominates modeled response
magnitude; Ra most strongly affects modeled transfer. C-01 changes somatic
predictions materially. The Dα7 component's effect varies strongly with its
free assumed conductance. None of these results opens an evidence gate.

## B. What is experimentally known

The model carries native MN5 recordings as **NATIVE MEASUREMENTS**:

- Resting potential: −67.8 ± 5.5 mV SD (n=13).
- Spike threshold: −24.1 ± 8.2 mV SD (n=11), giving a nominal 43.7 mV
  resting-to-threshold excursion.
- Input resistance: 102 ± 12 MΩ (n=22) and a separate 97 ± 31 MΩ (n=52)
  report.
- Whole-cell capacitance reports: 43 ± 2 pF (n=22) and 127 ± 16 pF SD.
  These conflict (C-01); both remain explicit and unresolved.
- The published somatic EPSP of 4.71 ± 0.35 mV (n=10) is an experimental
  observation used below as a comparison target. It was recorded with GF
  stimulation; PSI was not directly stimulated and distal amplitude was
  unreported.

These measurements do not provide a direct PSI→MN5 conductance, the
postsynaptic spatial voltage transfer, or a native Dα7 conductance.

## C. What is literature-derived

The following are **LITERATURE-DERIVED PARAMETERS**, not native MN5
measurements: axial resistivity Ra = 30–400 Ω·cm; specific membrane
capacitance = 0.6–2.6 µF/cm²; specific membrane resistance Rm =
6–26 kΩ·cm²; and exploratory cholinergic reversal range E_syn = −15 to
+10 mV. Ra and specific Cm/Rm use insect or cross-context modeling
precedent; no Drosophila-specific Rm is reported in the evidence base.
E_syn is a generic exploratory range, not a measured PSI→MN5 reversal.

E_Dα7 is separately listed with an exploratory −15 to +10 mV range, but
the final sensitivity sweep **did not vary it**: it stayed at the nominal
0 mV. This does not establish a Dα7 reversal potential.

## D. What is assumed

These are **MODEL ASSUMPTIONS**, not biological measurements or estimates:

- PSI peak conductance g_PSI and Dα7 maximal conductance g_Dα7; each is
  explored from 0.01 to 1000 nS on a logarithmic grid.
- PSI and Dα7 kinetic parameters and Dα7 desensitization settings.
- Process geometry, including length and diameter, and the model's
  synapse-to-soma arrangement.
- The use of a cholinergic PSI-like input and its assumed time course.

The broad conductance sweep ranges are exploration settings, not
evidence-based biological bounds. Dα7 kinetics, E_Dα7, and geometry are
not independently varied in the final result analysis.

## E. Model architecture

The implementation in [exploratory_mn5.py](../biological_brain/exploratory_mn5.py)
represents soma and a PSI-contact-bearing process as two compartments. A
double-exponential PSI conductance drives the process; axial current couples
it to the soma, and the soma voltage is compared with the carried MN5
threshold. It uses Forward Euler integration (dt = 0.01 ms, duration
15 ms) with stability substepping.

In cable mode, transfer emerges from the assumed geometry and electrical
parameters. It is an estimate produced by the model, not measured MN5
attenuation. An alternative explicit-transfer mode accepts a caller-supplied
assumption; that input is not a measurement. Calibration to the published
EPSP disables the Dα7 component.

## F. PSI→MN5 exploratory result

Under C-01 variant A, nominal TIER-B settings, cable mode, Dα7 disabled,
and assumed g_PSI = 1 nS, the model produced:

- local process peak: approximately 12.72 mV;
- somatic peak: approximately 2.06 mV;
- attenuation: approximately 0.162.

These are **MODEL-DERIVED ESTIMATES** under the stated assumptions. They
must not be described as measured PSI→MN5 voltage transfer, MN5 attenuation,
or PSI conductance.

## G. Dα7 exploratory result

With the Dα7 component enabled at nominal settings, the sweep varied
assumed g_Dα7 from 0.01 to 1000 nS with g_PSI = 1 nS. At the nominal
configuration, modeled somatic peak rose from about 2.07 to 20.61 mV
(approximately +0.9% to +903% versus the Dα7-disabled baseline); local
peak rose from about 12.78 to 67.47 mV. No run in the Dα7 main-effect
design crossed threshold.

Thus the model effect is parameter-dependent across the assumed g_Dα7
range, and its biological magnitude is **UNCONSTRAINED**. These outputs
do not measure native Dα7 conductance or physiology. E_Dα7 remained fixed
at 0 mV, and Dα7 kinetics remained at their assumed defaults.

## H. Sensitivity analysis

The existing sweep uses one-at-a-time changes, a TIER-B factorial across
both C-01 variants, g_PSI and g_Dα7 main-effect sweeps, and a g_PSI ×
g_Dα7 interaction. It did not run the full cross-product. A transparent
Spearman rank comparison over the existing TIER-B × g_PSI design gives
somatic peak associations of +0.916/+0.931 for g_PSI, −0.266/−0.246
for Ra, +0.117/+0.121 for E_syn, approximately +0.014/+0.015 for Rm,
and −0.011/approximately 0 for specific Cm (C-01 A/B).

This ranks monotone association in the selected sweep, not biological
causality. The ranking and nominal OFAT ranges indicate that g_PSI
dominates modeled response magnitude, while Ra dominates attenuation
(nominal OFAT attenuation 0.046–0.405 across Ra 30–400 Ω·cm). Rm and
specific Cm have small effects on the nominal somatic peak within their
tested ranges. The unresolved C-01 effect is separate and substantial.

## I. C-01 capacitance conflict

C-01 remains unresolved: variant A = 43 pF and variant B = 127 pF. Across
144 TIER-B combinations at assumed g_PSI = 1 nS, the variant A/B ratios
were:

| Model output | A/B ratio range (median) |
|---|---:|
| Somatic peak | 1.88–2.08× (2.04×) |
| Local peak | 1.00–1.13× (1.02×) |
| Attenuation | 1.84–2.02× (1.97×) |
| Threshold crossing | None for either variant in these runs |

At nominal calibration settings, the variants also return different
calibration outputs (see J). Neither capacitance report is selected or
resolved here.

## J. 4.71 mV EPSP comparison

The published 4.71 ± 0.35 mV somatic EPSP is a **comparison target only**.
MODEL_CALIBRATION uses log-space fitting of g_PSI with Dα7 disabled. At
nominal TIER-B settings, the model calibration returned approximately
2.95 nS under C-01 variant A and 9.38 nS under variant B. These are
**MODEL_CALIBRATION / MODEL-DERIVED ESTIMATES**, not measured PSI
conductances.

Across 288 TIER-B × C-01 combinations, the target was reachable within
the existing g_PSI sweep range for 240 (83.3%). Twelve (4.2%) touched the
target band only at the upper edge (1000 nS); 36 (12.5%) did not reach the
band within the range and would require a value outside it. Among reachable
fits, 77.9% fell in the central third of the log range. This is numerical
reachability under assumptions, **not model validation**; no range was
expanded.

## K. Robust conclusions

- All captured PSI-input runs produced a positive local depolarization.
- In cable mode, somatic response remained below the local response in all
  captured runs.
- No captured run crossed the threshold (0/2592); for nominal g_PSI,
  none of the 288 TIER-B × C-01 runs crossed.
- Within the tested ranges, Rm and specific Cm had small effects on the
  nominal somatic peak.

These are robustness statements about the implemented model and explored
parameter sets, not biological facts about the real pathway.

## L. Parameter-dependent conclusions

- Somatic response magnitude varies strongly with g_PSI; Ra changes modeled
  somatic response and has the largest passive effect on transfer.
- E_syn changes the modeled driving force and response within its assumed
  range.
- C-01 changes somatic peak and attenuation materially while leaving local
  peak nearly unchanged.
- The magnitude of the Dα7 model effect changes strongly with assumed
  g_Dα7.

## M. Unconstrained conclusions

The biological values of g_PSI, g_Dα7, Dα7 kinetics, and Dα7 reversal are
not established by this analysis. Absolute local/somatic response
magnitudes and real-pathway threshold capability are consequently not
bounded by the assumed sweep limits. Absolute biological spatial transfer
is likewise unconstrained by the cable calculation and assumed geometry.

## N. What the model cannot establish biologically

This model cannot establish a measured PSI→MN5 postsynaptic voltage
transfer, PSI synaptic conductance, native Dα7 conductance or effect,
biological spike initiation (or its absence), or whether its simplified
two-compartment geometry represents the real MN5 arbor. Reaching the
published EPSP target does not validate the model or identify the pathway
conductance.

## O. Final gate status

**Both hard gates remain closed and unchanged:**

- PSI→MN5 postsynaptic spatial voltage transfer: NOT AUTHORIZED
- Dα7 biological conductance: NOT AUTHORIZED

All calibration values remain **MODEL-DERIVED ESTIMATES** produced by
**MODEL_CALIBRATION**; no biological measurement or gate status is changed
by this final report.
