# MN5 / PSI Two-Gate Constrained Model

## 1. Objective

Run a provenance-separated model analysis of the 43 MaleCNS v1.0 PSI→MN5
contacts and the existing exploratory MN5 model. Contact-local calculations
use the audited contact-to-SWC-node mapping. Somatic response is analyzed only
with a separate, abstract GFS cable bridge; no MaleCNS contact is assigned an
anatomical path to the soma.

> The MaleCNS MN5 SWCs available for this analysis do not contain a
> soma-labeled node, so an anatomically reconstructed contact-to-soma path
> could not be established. Therefore somatic spatial transfer is represented
> by an explicitly parameterized cable-model abstraction constrained by
> published GFS modeling and MN5 physiology, rather than claimed as a direct
> anatomical reconstruction. This authorizes MODEL-DERIVED analysis only;
> it is not an experimental voltage-transfer measurement.

## 2. Provenance

The quantities are separated into four evidence layers:

| Layer | Included evidence/quantities | Boundary |
|---|---|---|
| **A. Anatomically verified** | 43 PSI→MN5 contacts (17 left, 26 right); contact-to-node mapping verified for all 43 | No anatomically reconstructed contact-to-soma path exists; no per-contact anatomical somatic transfer is claimed |
| **B. Literature-constrained** | Published GFS cable-model geometry/parameter precedent; recombinant Dα7 channel electrophysiology; MN5 physiology; existing passive parameter ranges | These sources constrain model context, not native PSI-site voltage transfer or native MN5 Dα7 conductance |
| **C. Model assumptions** | Separate abstract soma-transfer bridge; exploratory E_syn and E_Dα7 ranges; effective receptor abundance/conductance | Assumptions are not native measurements; E_syn does not establish a PSI→MN5 reversal potential |
| **D. Model-derived** | Contact-local responses; abstract-bridge somatic transfer; fitted g_PSI; effective g_Dα7 effects | Conditional simulation/calibration outputs, not biological measurements |

| Quantity | Value used/reported | Provenance | What it does not establish |
|---|---|---|---|
| PSI→MN5 contacts and node map | 43; 17 `802401→801970`, 26 `903327→801295`; 43/43 contact-to-node mappings verified | MaleCNS v1.0 anatomical data and audited geometric projection | A soma-connected path or an electrical property |
| Projected SWC node annotations | 43/43 unique mapped nodes; all source Type tokens `0`; one tied-segment case selects node 151 | Existing audited geometric projection | Biological meaning for Type `0`, voltage transfer, or electrical distance |
| MN5 somatic EPSP | 4.71 ± 0.35 mV, n=10, under GF stimulation | Native experimental measurement; comparison target only | An isolated PSI-evoked EPSP or model validation |
| MN5 whole-cell capacitance | C-01 A: 43 ± 2 pF; B: 127 ± 16 pF | Conflicting native measurements; both retained | Adjudication of C-01 |
| GFS DLMn/PSI cable geometry | DLMn dendrite 100 µm; axon 50 µm; proximal process diameter 2 µm; PSI input 12.5 µm from the axon proximal end | Augustin et al. 2019 published model geometry; model precedent | Exact MN5 anatomy or contact-to-soma mapping |
| Passive ranges | Ra 30–400 Ω·cm; Cm 0.6–2.6 µF/cm²; Rm 6–26 kΩ·cm² | Existing literature-derived/model-adopted exploratory ranges | Native MN5 passive measurements |
| Dα7 channel response | EC50 6.7 ± 1.7 µM ACh; Hill 1.0 ± 0.3; n=4; Imax 86 nA and mean maximum current 45 ± 13 nA, at −60 mV | Recombinant Dα7 + CeRIC-3 in *Xenopus* oocytes; literature-derived channel-level constraint | Native MN5 conductance, receptor density, or PSI-synapse kinetics |
| Local voltage, cable transfer, fitted g values, and Dα7 contribution | Results below | MODEL-DERIVED ESTIMATES conditional on the listed assumptions | Biological measurements |

The source SWC hashes are preserved in
`mn5_compartment_post_swc_type_concordance.csv`. The model consumes the audited
contact/node table and the corresponding cached official SWCs.

There is no anatomically reconstructed contact-to-soma path for any of the
43 contacts. Consequently, per-contact anatomical somatic transfer is not
claimed. Somatic transfer is generated only by the separate abstract cable
bridge; published GFS cable-model geometry/parameters provide its literature/
model precedent. The resulting transfer is MODEL-DERIVED, not an experimental
voltage-transfer measurement.

## 3. Gate A evidence and separate analysis layers

### A.1 Contact-local analysis

The 43 rows preserve the contact IDs, body pairings, exact official
`compartment_post` string, projected SWC node, literal SWC Type code, projection
status/error, and local node geometry. The established annotation concordance
is still only literal annotation concordance: all official labels are
`compartment_post="axon"` and all selected source Type tokens are `0`. Type `0`
is not assigned any biological compartment meaning.

The local patch calculation uses, per mapped contact:

- the selected SWC node's geometric radius; and
- the arithmetic mean length of that node's adjacent SWC edges as an assumed
  local patch length.

It forms a cylindrical patch area `A = 2πrℓ`, then uses
`Cpatch = A·Cm` and `gleak = A/Rm`. For a single conductance input:

`Cpatch·dV/dt = −gleak(V−Vrest) + gPSI(t)(Esyn−V)`.

This is a local single-patch model only. It has no axial path, no soma
compartment, and no contribution from other contacts. Each row is an
independent event with the same assumed per-contact gPSI; no synchronous
release across contacts is assumed. The node radius/edge-derived patch extent,
Cm, Rm, gPSI, and E_syn are modeling inputs, not measurements of synaptic
current or local voltage.

At the illustrative settings gPSI=1 nS, E_syn=0 mV, Cm=1.15 µF/cm²,
Rm=6 kΩ·cm², the model-derived local peak depolarization ranges were:

| MN5 body | Contacts | Local peak min / median / max |
|---|---:|---:|
| 801970 (left) | 17 | 40.13 / 61.09 / 67.71 mV |
| 801295 (right) | 26 | 51.26 / 67.59 / 67.71 mV |

Across the full local sweep (Cm 0.6–2.6 µF/cm², Rm 6–26 kΩ·cm²,
E_syn −15 to +10 mV, gPSI 0.01–1000 nS), the modeled local peak range was
0.58–77.80 mV. This broad range is dominated by free gPSI and the assumed local
patch size. It is not a native voltage estimate and is not transferable to the
soma.

### A.2 Abstract somatic-transfer analysis

The separate abstract model uses a uniform two-compartment cable abstraction
with modeled process length `100 + 12.5 = 112.5 µm` and diameter 2 µm. This
represents the published DLMn dendrite plus the reported location of PSI input
from the axon proximal end, under the additional modeling assumption that this
is a continuous path from the soma. The cable is not traced onto the MaleCNS
SWC, and the result is not a per-contact transfer measurement.

The existing exploratory model equations are used:

`Cs·dVs/dt = −gleak,s(Vs−Vrest) + gax(Vp−Vs)`

`Cp·dVp/dt = −gleak,p(Vp−Vrest) + gax(Vs−Vp) + gPSI(t)(Esyn−Vp)`

with `gax` computed from the assumed cable geometry and swept Ra. The PSI
conductance is the existing double-exponential form, using the Augustin-model
rise/decay values of 0.1/1.0 ms for this analysis. The model delay of 0.15 ms is
not applied; no synaptic onset latency is inferred. The reported
local-to-somatic ratio is the ratio of separately measured peak depolarizations
in the abstraction, not an experimentally measured transfer ratio.

The uniform cable reduces the published dendrite/axon geometry to one
equivalent process. It is intentionally not treated as a reconstructed MN5
path. C-01 A/B, Ra, Cm, Rm, E_syn, and gPSI are swept; the existing ranges are
not expanded.

Across 2,880 runs (both C-01 variants, the discrete passive grids,
E_syn −15/0/+10 mV, and gPSI 0.01–1000 nS):

| Abstract output | Min / median / max | Provenance |
|---|---:|---|
| Local peak depolarization | 0.0055 / 5.56 / 77.26 mV | MODEL-DERIVED |
| Somatic peak depolarization | 0.0028 / 1.81 / 67.08 mV | MODEL-DERIVED |
| Peak ratio, local-to-somatic | 0.085 / 0.517 / 0.892 | MODEL-DERIVED |
| Model time to somatic peak | Recorded per run in CSV | MODEL-DERIVED; not synaptic latency |
| Threshold crossings | 224 / 2,880 | Model outcomes in the specified sweep only |

At the nominal GFS bridge (Ra=35.4 Ω·cm, Cm=1.0 µF/cm², Rm=6 kΩ·cm²,
E_syn=0 mV, gPSI=1 nS):

| C-01 variant | Local peak | Somatic peak | Peak ratio | Threshold |
|---|---:|---:|---:|---|
| A (43 pF) | 1.298 mV | 1.108 mV | 0.854 | Not crossed |
| B (127 pF) | 0.888 mV | 0.510 mV | 0.574 | Not crossed |

These are outputs of the bridge, not contact-specific MN5 predictions.
The complete sensitivity export contains 15,528 rows across the contact-local,
abstract-transfer, Dα7 sensitivity, and EPSP calibration analyses.

## 4. Published GFS model values and their use

Augustin, Zylbertal & Partridge (2019), DOI
[10.1523/ENEURO.0423-18.2019](https://doi.org/10.1523/ENEURO.0423-18.2019),
provides a published mechanistic PSI→DLMn cable-model precedent. Its reported
model geometry/parameters include:

| Published model value | Role in this analysis |
|---|---|
| PSI diameter 4.5 µm; axon 90 µm; estimated dendrite 170 µm; input site 76.5 µm from PSI axon proximal end | Recorded as presynaptic model context; not used to assign postsynaptic MN5 geometry |
| DLMn dendrite 100 µm; axon 50 µm; proximal diameter 2 µm; PSI input 12.5 µm from DLMn axon proximal end | Used only to define the 112.5 µm, 2 µm uniform abstract cable bridge |
| Leak 0.03 mS/cm²; Cm 1 µF/cm²; Ra 35.4 Ω·cm | Published model estimates; 35.4 Ω·cm and 1 µF/cm² included as sweep points. The leak estimate is not adopted because it corresponds to Rm≈33.3 kΩ·cm², outside the pre-existing 6–26 range |
| Synapse rise 0.1 ms; decay 1 ms; Erev 0 mV; delay 0.15 ms | Rise/decay used in both model analyses; 0 mV is a nominal model precedent inside the assumed E_syn range; delay not used |
| Chemical peak conductance 80 µS | Not used as MN5 conductance. It is a published model-estimated parameter, not a native measurement; gPSI remains a free parameter |

The ModelDB implementation's code/parameter caveats recorded in
`source_registry.md` remain applicable. None of these values validates the
MaleCNS soma path or native MN5 conductance.

## 5. Gate A sensitivity and EPSP comparison

At the nominal point, increasing Ra from 30 to 400 Ω·cm reduced the modeled
peak ratio from 0.880 to 0.211 for C-01 A, and from 0.652 to 0.102 for C-01 B.
At nominal passive settings, the E_syn sweep changed the somatic peak from
0.863 to 1.271 mV (A) and 0.397 to 0.585 mV (B). Over the same nominal
settings, changing Cm from 0.6 to 2.6 µF/cm² changed the somatic peak by about
18% (A) and 8% (B); changing Rm from 6 to 26 kΩ·cm² changed it by about 3%
(A) and 2% (B). These are model-local sensitivity comparisons, not biological
effect sizes.

### C-01

At gPSI=1 nS and E_syn=0 mV, paired abstract runs across the passive grid gave
the B/A somatic-peak ratio 0.445–0.543 (median 0.463). Thus the abstract
prediction for variant B was approximately 46% of variant A at the median
matched setting. The peak transfer ratio also changed (B/A 0.462–0.780,
median 0.544). Neither capacitance is selected as correct.

### Calibration to the published MN5 EPSP

The 4.71 mV somatic EPSP is a GF-stimulated experimental comparison target; PSI
was not directly stimulated. Calibration is MODEL_CALIBRATION, not validation
and not measurement of gPSI.

| Calibration set | CENTRAL | EDGE | OUTSIDE current gPSI range | Fitted gPSI range |
|---|---:|---:|---:|---:|
| C-01 A, 240 passive/E_syn settings | 240 | 0 | 0 | 3.58–11.66 nS |
| C-01 B, 240 passive/E_syn settings | 220 | 20 | 0 | 8.31–42.73 nS |
| Total, 480 settings | 460 | 20 | 0 | 3.58–42.73 nS |

Classification uses the existing assumed log range 0.01–1000 nS: CENTRAL is
the middle third in log space; EDGE is a fit in either outer third; OUTSIDE
means the target midpoint is not reachable inside the current range. At the
published-model passive nominal point and E_syn=0 mV, fitted values were
4.49 nS (A) and 10.16 nS (B), both CENTRAL. All are MODEL-DERIVED estimates.
Numerical reachability is not biological plausibility or validation.

## 6. Gate B evidence and model

Lansdell et al. (2012), DOI
[10.1186/1471-2202-13-73](https://doi.org/10.1186/1471-2202-13-73), reports
functional recombinant homomeric Dα7 in *Xenopus* oocytes with CeRIC-3. Table 2
reports EC50 6.7 ± 1.7 µM ACh, Hill slope 1.0 ± 0.3, n=4, maximum current
detected 86 nA, and mean maximum current 45 ± 13 nA; the membrane was held at
−60 mV. Functional expression was variable, with responses >5 nA in about one
third of batches.

The Dα7 pathway literature reports a reduction in the MN5 somatic synaptic
potential under Dα7 perturbation and supports pathway relevance. It does not
measure native Dα7 conductance, density, or localization at PSI→MN5. The
recombinant currents are not converted to nS: the receptor number/native
expression, synaptic ACh exposure, and relevant native driving force are
unknown. The existing model's activation/desensitization time course remains
assumed; it does not derive kinetics from EC50/Hill.

Gate B sweeps `g_Dalpha7_effective` over the existing free range 0.01–1000 nS,
E_Dα7 over the exploratory −15 to +10 mV range, both C-01 variants, and the
same Ra/Cm/Rm grids. gPSI=1 nS and E_syn=0 mV are held for this comparison.
Every g_Dα7_effective value is a MODEL ASSUMPTION; calculated changes are
MODEL-DERIVED.

Recombinant Dα7 electrophysiology provides channel-level experimental
constraints only. Native MN5 Dα7 receptor number/density/open probability is
not directly measured. Effective native g_Dalpha7 therefore remains
MODEL-DERIVED; no recombinant current value is relabeled as native MN5
conductance. This sweep is a model-derived effective-conductance sensitivity
analysis, not a measurement of native conductance.

Across 2,880 runs:

- Matched local-peak change versus no-Dα7 ranged 0.002–75.91 mV; median
  10.79 mV.
- Matched somatic-peak change ranged 0.005–68.77 mV; median 5.73 mV.
- No-Dα7 baselines had 0 threshold crossings; Dα7-enabled runs had 456/2,880
  crossings. Crossings occurred only at the largest assumed conductances:
  184/480 at 100 nS and 272/480 at 1000 nS; these are not biological pathway
  threshold predictions.
- At g_Dalpha7_effective=0.01 nS the median somatic change was 0.009 mV;
  at 1000 nS it was 45.50 mV. The effect is strongly parameter-dependent and
  the native value remains biologically unconstrained.

E_Dα7 (−15 to +10 mV) is a TIER-C exploratory model assumption; no direct
Dα7 reversal-potential source constrains it. It is not a Dα7 reversal-potential
measurement. The result does not establish native receptor conductance,
abundance, kinetics, or a measured Dα7 contribution.

## 7. Assumptions and sensitivity design

- The 43 contacts retain left/right pairing and are modeled independently in
  the contact-local analysis; no unsupported simultaneous-release assumption
  is made.
- The local patch length and cylindrical area approximation are model
  assumptions based on adjacent SWC geometry.
- The 112.5 µm uniform cable is a bridge from published GFS DLMn geometry, not
  a MaleCNS contact-to-soma path. No per-contact anatomical somatic transfer
  is claimed.
- The abstract bridge, exploratory E_syn and E_Dα7 ranges, and effective
  receptor abundance/conductance are model assumptions. Existing ranges are
  not expanded.
- C-01 A/B remain separate; the 4.71 mV EPSP remains a comparison target.
- The sweep is a deterministic grid, not a probability distribution or
  confidence interval. Min/median/max describe sampled model outcomes only.

The full deterministic per-contact and abstract sweep rows are in
`mn5_psi_mn5_final_constraint_model_sensitivity.csv`; generation is implemented
by `scripts/analyze_mn5_two_gate_constraint_model.py`.

## 8. What remains unmeasured / unresolved

- No anatomically reconstructed contact-to-soma path for any of the 43
  contacts; all 43 remain unresolved for that quantity.
- No native PSI→MN5 local voltage, somatic voltage-transfer ratio, or
  synaptic reversal potential.
- No native PSI synaptic conductance; fitted gPSI values are model-derived
  comparisons only.
- No native MN5 Dα7 effective conductance, density, synaptic kinetics, or
  Dα7 reversal potential.
- No resolution of C-01 (43 vs 127 pF).
- No biological interpretation of SWC Type `0`.

## 9. Authorization status

**Gate A — PSI→MN5 postsynaptic spatial voltage transfer: MODEL-AUTHORIZED /
ANATOMY + LITERATURE CONSTRAINED.** The 43 actual MaleCNS contacts and
contact-to-node mappings are anatomically verified. No anatomically
reconstructed contact-to-soma path exists, so per-contact anatomical somatic
transfer is NOT claimed. Somatic transfer comes from the separate abstract
cable-model bridge using published GFS cable-model geometry/parameters as its
precedent. The resulting transfer is MODEL-DERIVED and is NOT an experimental
voltage-transfer measurement.

**Gate B — Dα7 biological conductance: MODEL-AUTHORIZED /
CHANNEL-CONSTRAINED / NATIVE VALUE MODEL-DERIVED.** Recombinant Dα7
electrophysiology supplies channel-level constraints. Native MN5 receptor
number/density/open probability are not directly measured; effective native
g_Dalpha7 remains MODEL-DERIVED. No recombinant current value is relabeled as
native MN5 conductance. The Dα7 sweep is a model-derived effective-conductance
sensitivity analysis.

These authorizations permit conditional model outputs only. Neither authorizes
a claim that native PSI→MN5 voltage transfer or native MN5 Dα7 conductance was
experimentally measured.

## References

1. Berg et al. (2026). MaleCNS v1.0 release and per-synapse annotation layer.
2. Fayyazuddin et al. (2006). “The nicotinic acetylcholine receptor Dα7 is
   required for an escape behavior in *Drosophila*.” *PLoS Biology* 4(3):e63.
   DOI [10.1371/journal.pbio.0040063](https://doi.org/10.1371/journal.pbio.0040063).
3. Augustin, Zylbertal & Partridge (2019). “A Computational Model of the
   Escape Response Latency in the Giant Fiber System of *Drosophila
   melanogaster*.” *eNeuro* 6(2):ENEURO.0423-18.2019. DOI
   [10.1523/ENEURO.0423-18.2019](https://doi.org/10.1523/ENEURO.0423-18.2019).
4. Lansdell, Collins, Goodchild & Millar (2012). “The *Drosophila* nicotinic
   acetylcholine receptor subunits Dα5 and Dα7 form functional homomeric and
   heteromeric ion channels.” *BMC Neuroscience* 13:73. DOI
   [10.1186/1471-2202-13-73](https://doi.org/10.1186/1471-2202-13-73).
