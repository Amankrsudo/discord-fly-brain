# Final Scientific Review

Exploratory MN5 / PSI / Dα7 mechanistic model
(`biological_brain/exploratory_mn5.py`, version 0.1.0).
Reviewed artifacts: `research/exploratory_mn5_model.md`,
`research/exploratory_sensitivity_plan.md`,
`research/exploratory_parameter_ranges.csv`,
`research/exploratory_mn5_results_analysis.md`,
`research/exploratory_mn5_parameter_sensitivity.csv`
(47 quantitative rows), `tests/test_exploratory_mn5.py`
(34 tests), `tests/test_exploratory_mn5_results_analysis.py`
(22 tests).

> **This is a review of a best-effort exploratory model.
> Nothing in this document is a biological measurement.**
> This model is not a measurement of MN5 spatial voltage transfer or Dα7 conductance. Every simulation output is a MODEL-DERIVED ESTIMATE.

## 1. Bottom-line assessment

The model is **scientifically coherent as an exploratory
model** — not as a measurement, not as a validation. It
implements the project strategy correctly: verified native
biology is preserved as TIER A, literature-constrained
passive parameters are carried as TIER B and explicitly
labelled non-native, every unknown is a TIER C/geometry
MODEL_ASSUMPTION, and every conclusion carries a
ROBUST / PARAMETER-DEPENDENT / UNCONSTRAINED
classification backed by 2078 original plus 2592 captured
and 288 calibration runs. Provenance discipline is
maintained throughout: no model output is relabelled as a
measurement, the frozen evidence registry is never read or
written, and both hard gates remain closed.

The model achieves its stated purpose: it replaces "cannot
model because parameters are unknown" with a transparent,
conditional mechanistic account in which the qualitative
conclusions that survive the explored space are separated
from those that do not. **It is sufficient for the current
project stage.**

Known model-scope limits (stated, not hidden): linear
two-compartment reduction with prescribed (not
voltage-gated) conductances; no AP shape, plasticity,
vesicle dynamics or receptor trafficking; assumed process
geometry; Forward Euler with adaptive substepping
(numerical stability only).

## 2. What the model establishes robustly

ROBUST — same qualitative outcome across every explored
parameter set (Ra 30–400 Ω·cm; Cm_spec 0.6–2.6 µF/cm²;
Rm 6–26 kΩ·cm²; E_syn −15…+10 mV; g_PSI and g_Dα7
0.01–1000 nS log; both C-01 variants):

1. A cholinergic PSI-like synaptic input onto the assumed
   process compartment produces a **local depolarization**
   at the synaptic site — local peak > 0 in 2592/2592
   captured runs (and all 2078 original runs).
2. The somatic response is **attenuated relative to the
   local response in cable mode** — attenuation < 1 in
   every cable-mode run (explored span 0.019–0.571). Only
   the inequality is robust; the value is not (§3).
3. **No threshold crossing anywhere in the explored
   space** — 0/2592 runs; the closest approach is 41.47 mV,
   95.0% of the 43.7 mV excursion required (V_rest −67.8
   mV → V_th −24.1 mV, both native measurements), reached
   at g_PSI = 1000 nS with the most favorable TIER-B
   corner. At the nominal g_PSI = 1 nS, 0/288 TIER-B ×
   C-01 combinations cross.
4. **Rm and specific Cm are negligible** within their
   explored ranges (~2% effect on the somatic peak;
   |ρ| ≤ 0.014).
5. The **local depolarization is nearly invariant to the
   C-01 variant** (A/B ratio 1.00–1.13×, median 1.02×) —
   the contested capacitance acts on the soma, not on the
   process compartment where the synapse sits.

## 3. What is parameter-dependent

PARAMETER-DEPENDENT — conclusions that change across
parameters whose ranges current evidence bounds (TIER B)
or across the contested C-01 variants:

1. **Somatic peak at fixed g_PSI** depends on Ra (OFAT
   1.36–2.30 mV, 1.7×; ρ = −0.266/−0.246) and E_syn
   (1.60–2.36 mV, ~1.5×; ρ = +0.117/+0.121, via the
   synaptic driving force).
2. **The attenuation value** depends strongly on Ra
   (OFAT 0.046–0.405, ≈9×; ρ = −0.958/−0.898 — the
   strongest single correlation in the analysis). Ra
   dominates cable-transfer uncertainty.
3. **Every somatic quantity** scales with the unresolved
   C-01 variant: somatic peak 1.88–2.08×, attenuation
   1.84–2.02×, calibrated g_PSI 3.17× (§8).
4. **The g_PSI required for the EPSP target** depends on Ra
   (ρ(log10 g*, Ra) = +0.882/+0.890): more attenuating
   cables demand more conductance.
5. Higher Ra *increases* the local depolarization (ρ =
   +0.159) because axial isolation lets the process
   compartment depolarize more — a model-internal effect.

## 4. What remains unconstrained

UNCONSTRAINED — quantities for which current evidence plus
the sweeps cannot establish a meaningful bound, because they
depend on TIER C free parameters:

1. **The magnitude of the local and somatic responses** —
   dominated by the free g_PSI (ρ = +0.916/+0.931 vs
   somatic; OFAT span 776×). No evidence bounds the
   plausible g_PSI range, so no quantitative response
   magnitude can be bounded.
2. **Whether the real pathway can reach the MN5 spike
   threshold** — no crossing in the explored space, but the
   g_PSI upper bound (1000 nS) is an assumption, not an
   evidence bound.
3. **The Dα7 component's effect size** — large and monotone
   under the assumption set, but g_Dα7, density and kinetics
   are all free (§7).
4. **The calibrated g_PSI as a biological value** — a
   MODEL_CALIBRATION output, moving 3.17× with C-01 and
   2.95 → 1.66 nS with the Dα7 assumption.
5. **Any absolute spatial transfer** — cable attenuation
   depends on unmeasured geometry and unmeasured Ra/Rm.
6. **E_Dα7 was NOT independently swept.** The final
   analysis swept E_syn only; the Dα7 reversal potential was
   carried at its nominal 0 mV and its effect is entirely
   unexamined. No claim about E_Dα7 sensitivity may be
   made.
7. **Unswept TIER C/geometry assumptions** — synaptic
   rise/decay kinetics, Dα7 activation/desensitization
   kinetics, process length (50 µm, anchored on the
   documented contact *span*, not a measured soma-to-contact
   path), process diameter (0.5 µm) and synapse location.
   These are carried as explicit assumptions, not bounds.

## 5. Interpretation of the 4.71 mV EPSP

The published MN5 somatic EPSP (4.71 ± 0.35 mV,
Fayyazuddin+ 2006, n=10) is used **only as a published
comparison target**, and the comparison is scientifically
defensible **strictly as model reachability / calibration —
never as validation**:

- The target was recorded under **GF stimulation**: the
  whole pathway, not an isolated PSI→MN5 event. PSI was
  never directly stimulated and the distal amplitude is
  unreported. The comparison is against a pathway-filtered
  somatic voltage.
- The model reproduces the target within the existing
  explored g_PSI grid for **240/288 (83.3%)** of TIER-B ×
  C-01 combinations (variant A 91.7%, variant B 75.0%), at
  central-to-upper-central positions (g* = 1.87–213.4 nS,
  median 6.33 nS; 77.9% in the central third; nominal
  TIER-B calibrations 2.95 nS (A, log-position 0.49) and
  9.38 nS (B, log-position 0.59)).
- 36/288 (12.5%) — the most attenuating corners — require
  g_PSI > 1000 nS (OUTSIDE CURRENT EXPLORATORY RANGE;
  the range was **not** expanded); 12/288 (4.2%) touch the
  band only at the upper edge.
- The calibration has **one free parameter and one target**:
  it demonstrates reachability, not correctness. The fitted
  conductances are MODEL-DERIVED ESTIMATES, not measured
  PSI→MN5 conductances (which remain BLOCKED).
- With the exploratory Dα7 component enabled at g_Dα7 =
  1 nS the fit moves to 1.66 nS: the calibration cannot be
  interpreted without naming the Dα7 assumption.

## 6. Interpretation of PSI→MN5 transfer

- Cable-mode attenuation (nominal 0.162 variant A / 0.081
  variant B at g_PSI = 1 nS) is a **MODEL-DERIVED ESTIMATE**
  conditional on assumed geometry (50 µm × 0.5 µm process)
  and literature-derived Ra/Rm. It is **not** a measured MN5
  attenuation, and the experimental spatial-transfer gate
  remains NOT AUTHORIZED.
- Anatomical context: 43 verified PSI→MN5 EM contacts
  (17: 802401→801970 L; 26: 903327→801295 R; 0
  cross-pairings), all with official postsynaptic
  compartment label "axon" (36 PDMN, 7 WTct). These labels
  are **not** reinterpreted as biological axon/dendrite
  categories; PDMN/WTct and SWC kind=2 must not be
  auto-classified, and the contact→soma graph path remains
  unresolved (MaleCNS SWC contains no kind=1 soma nodes for
  MN5). The two-compartment reduction therefore rests on an
  assumed, not measured, soma-to-contact path.
- Explicit-transfer mode exists for completeness, but the
  transfer ratio there is a caller-supplied MODEL_ASSUMPTION
  in [0, 1], never defaulted and never measured.

## 7. Interpretation of Dα7

- Under the exploratory assumption set the Dα7 component
  raises the local depolarization (12.78 → 67.47 mV) and
  the somatic peak (2.07 → 20.61 mV at nominal TIER-B; up
  to 38.35 mV across the full factorial), monotonically in
  g_Dα7 (ρ = +0.882 somatic / +0.897 local), saturating
  toward the cholinergic reversal potential; the apparent
  attenuation rises 0.162 → 0.306 (a model-internal effect
  of added process depolarization, not a change in
  electrotonic structure). The effect becomes noticeable
  (>10%) from g_Dα7 ≈ 0.1–1 nS.
- **No threshold crossing with Dα7 enabled** (0/864 runs).
- All of this is **UNCONSTRAINED**: g_Dα7, receptor
  density, kinetics and reversal are free MODEL_ASSUMPTIONs
  with no native values, and E_Dα7 was not independently
  swept (§4). The correct statement is only: *under
  exploratory assumption set {g_Dα7 = X nS, kinetics as
  tabulated}, the model predicts Y*. The Dα7 component is an
  assumption probe; it is never used to retroactively
  justify the PSI conductance (calibration always runs with
  Dα7 disabled). The Dα7 gate remains NOT AUTHORIZED.

## 8. C-01 capacitance conflict

Handled correctly: the 43 ± 2 pF (Fayyazuddin+ 2006) vs
127 ± 16 pF (Ryglewski & Duch 2009) conflict (~2.95×) is
carried as **two explicit variants, never adjudicated** —
the constructor requires an explicit variant choice, and
every design runs both. The conflict materially affects
predictions: somatic peak 1.88–2.08× (median 2.04×),
attenuation 1.84–2.02×, calibrated g_PSI 3.17× (larger
than the capacitance ratio itself, via the nonlinear
two-compartment interaction), while the local depolarization
is nearly unchanged (1.00–1.13×). Any quantitative somatic
prediction is conditional on which native measurement is
assumed, and any future calibration must report both
variants. The conflict is **not** resolved by this analysis.

## 9. Claims that must NOT be made

- Model attenuation is **not** a measured MN5 attenuation.
- Calibrated g_PSI (2.95 / 9.38 nS) is **not** a measured
  PSI→MN5 synaptic conductance; that quantity remains
  BLOCKED.
- Exploratory g_Dα7 values are **not** native Dα7
  conductances.
- Reproducing 4.71 mV is **not** validation of the cable
  model (reachability only, one free parameter,
  pathway-filtered target).
- "No threshold crossing" is a **model-space result within
  an assumed g_PSI range**, not a biological prediction
  that PSI cannot drive MN5 to threshold.
- The EM "axon" compartment label is **not** a biological
  axon/dendrite classification, and the contact→soma path
  is unresolved.
- E_Dα7 was **not** independently sensitivity-tested.
- GEVI ΔF/F is **not** ΔV (optical experiment audit).
- The 12.5% of calibration points requiring g_PSI >
  1000 nS are **not** evidence of biological impossibility —
  the range is an assumption.
- No fitted value in this project is a fitted biological
  parameter.

## 10. Scientifically defensible claims

1. A cholinergic PSI-like input onto the assumed process
   compartment produces a local depolarization under every
   explored parameter set (ROBUST).
2. The somatic response is smaller than the local response
   in cable mode under every explored parameter set (ROBUST).
3. At the nominal g_PSI, no literature-bounded passive
   parameter combination brings the soma to threshold
   (ROBUST negative finding, conditional on the nominal
   g_PSI).
4. The model reproduces the published 4.71 mV somatic EPSP
   for 83.3% of TIER-B × C-01 combinations at
   central-to-upper-central g_PSI values (MODEL_CALIBRATION;
   MODEL-DERIVED ESTIMATE).
5. Within the model, g_PSI dominates the response magnitude
   and Ra dominates the transfer; Cm_spec and Rm are
   negligible within their explored ranges.
6. The unresolved C-01 conflict scales every somatic
   prediction ~2× and the calibration 3.17×
   (PARAMETER-DEPENDENT).
7. The project can now state, transparently, which
   conclusions are robust, which are parameter-dependent,
   and which are unconstrained — with measured biology,
   literature-derived ranges, model assumptions and
   model-derived estimates kept strictly separate.

## 11. Final gate status

**Unchanged and closed:**

- PSI→MN5 postsynaptic spatial voltage transfer: NOT AUTHORIZED
- Dα7 biological conductance: NOT AUTHORIZED

No gate was opened, no parameter range was expanded, no
frozen registry was read or written, and no biological
constant was modified by this review.

## 12. Recommended next scientific step

**No further broad audit is recommended.** The exploratory
model is sufficient for the current project stage: its
purpose was to convert "cannot model" into a transparent,
provenance-controlled best-effort model with classified
conclusions, and that purpose is achieved and verified
(22/22 analysis tests, 34/34 model tests). The correct
action now is to **preserve the current artifact set
unchanged** and to treat any future change as evidence
driven: if and when a direct experimental constraint
becomes available (most consequentially a measured
PSI→MN5 synaptic conductance, a measured MN5
soma-to-contact path, or an adjudicated C-01), it would
enter as a TIER A/B replacement for the specific
assumption it constrains — at which point, and only then,
the affected classifications should be recomputed. Until
such evidence exists, the honest scientific output of this
project is the classified, conditional model itself.

---

**Provenance summary of this review:** native MN5
measurements (resting −67.8 mV, threshold −24.1 mV, AP
amplitude 45.5 mV, Rin 102/97 MΩ, Cm 43/127 pF contested,
somatic EPSP 4.71 ± 0.35 mV) are NATIVE EXPERIMENTAL
MEASUREMENTS used as references or comparison targets;
Ra/Cm_spec/Rm/E_syn/E_Dα7 are LITERATURE-DERIVED PASSIVE
PARAMETERS (not native MN5 measurements); g_PSI, g_Dα7,
kinetics and geometry are MODEL ASSUMPTIONS; every
simulation output, calibration and sensitivity coefficient
is a MODEL-DERIVED ESTIMATE.

This model is not a measurement of MN5 spatial voltage
transfer or Dα7 conductance.
