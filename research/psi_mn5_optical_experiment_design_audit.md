# MN5 Optical Spatial-Voltage-Transfer Experiment Design Audit

Audit / research artifact. **No experiment was performed, no voltage
transfer was calculated, no GEVI value was measured or estimated, no
electrical parameter was introduced, no model was built, and no gate
was opened.** This document encodes the provenance-controlled design
of a *proposed* optical experiment for measuring spatial voltage
transfer between the PSI-contact-bearing MN5 process and the MN5
soma.

## A. Executive Verdict

```
MN5-specific genetic access:          NOT ESTABLISHED
DLMn-population access:               ESTABLISHED
MN5 anatomical identification:        ESTABLISHED PRECEDENT
GEVI compartmental voltage imaging in Drosophila: ESTABLISHED
MN5 + GEVI:                           NOT ESTABLISHED
PSI-specific optical activation:      NOT ESTABLISHED
Spatial voltage transfer:             NOT AUTHORIZED
Dα7 conductance:                      NOT AUTHORIZED
```

Reading of each line:

- **MN5-specific genetic access: NOT ESTABLISHED.** No driver that
  is expressed in MN5 *alone* has been demonstrated in the evidence
  base. The claim that an MN5-specific driver exists is rejected (§C).
- **DLMn-population access: ESTABLISHED.** DLMn Split-GAL4 access
  covers the MN1–5 population. This is population access to all five
  dorsal-longitudinal-muscle motoneurons; it is **not** equivalent to
  an MN5-specific driver, and any optical signal from such a driver
  must be attributed to MN5 by anatomical identification, not by
  driver specificity.
- **MN5 anatomical identification: ESTABLISHED PRECEDENT.** Fayyazuddin
  et al. (2006) identified MN5 by retrograde Texas-red dextran backfill
  from the DLMa/b muscles and performed in-situ somatic whole-cell
  recording. This identifies the soma; it does not identify the
  distal process in a living preparation.
- **GEVI compartmental voltage imaging in Drosophila: ESTABLISHED.**
  ASAP2f has measured voltage signals from multiple compartments of
  individual Drosophila neurons, including soma and axonal/dendritic
  arbors (Yang et al. 2016). This is a method precedent in *other*
  neurons.
- **MN5 + GEVI: NOT ESTABLISHED.** No GEVI has been expressed in,
  imaged in, or validated in MN5 in any source in the evidence base.
- **PSI-specific optical activation: NOT ESTABLISHED.** No PSI-specific
  driver is established in the evidence base; GF stimulation is not
  PSI-specific (§D).
- **Spatial voltage transfer: NOT AUTHORIZED.** No MN5 non-somatic or
  dual-site voltage measurement exists (blocker B-4). This audit
  designs an experiment; it performs none.
- **Dα7 conductance: NOT AUTHORIZED.** No native Dα7 conductance,
  reversal, kinetics or density exists in the evidence base. Nothing
  in this audit touches the receptor.

**The strongest directly relevant GEVI precedent is ASAP2f** (Drosophila
demonstration, multi-compartment voltage signals, substantial linearity
over a broad membrane-potential range in Drosophila work). **ASAP2s**
is a strong alternative with Drosophila two-photon benchmarking and
strong temporal performance, but it is **not declared superior for
MN5**. **ASAP5** is a newer candidate with improved sensitivity for
synaptic voltage events and Drosophila demonstrations, treated as an
alternative candidate, **not established for MN5**.

## B. GEVI Comparison

| Indicator | Drosophila evidence | compartmental imaging | axonal/process imaging | temporal performance | voltage-response linearity evidence | calibration evidence | MN5-specific evidence | limitations | provenance class | status |
|---|---|---|---|---|---|---|---|---|---|---|
| **ASAP2f** | Yang et al. 2016 (*Cell* 166:245–257): ASAP2f expressed in Mi1/Tm3/Tm1/L1/L2; voltage signals measured from multiple compartments of individual neurons, including soma and axonal/dendritic arbors | YES — soma, dendritic and axonal arbors of the same neuron | YES — axonal arbors imaged; amplitude decayed away from the site of primary synaptic input while time courses were largely preserved | two-photon compatible; tracks transient voltage responses to visual stimuli | substantial linearity over a broad membrane-potential range in the Drosophila work | compared against GCaMP6f calcium signals in the same neurons; no simultaneous electrical reference in the fly | **NONE** | ~10× smaller neurons than MN5; performance not transferable quantitatively; no MN5 validation of linearity, trafficking or expression | Native experimental measurement | ESTABLISHED (other neurons) |
| **ASAP2s** | Chamberland et al. 2017 (*eLife* 6:e25690): benchmarked for two-photon voltage imaging in Drosophila; L2 axon terminals imaged through a cuticle window; single-trial AP detection and graded-potential imaging with subcellular resolution in organotypic slices | YES — soma and dendritic tree (25 locations in slices) | YES — L2 axon terminals in vivo | strong temporal performance; faster kinetics than ArcLight and ASAP1; random-access multi-photon demonstrated | characterized in vitro (response amplitude, kinetics, photostability) | in-vitro voltage-clamp characterization against known voltage steps; not calibrated in MN5 | **NONE** | not declared superior for MN5; single-trial AP detection shown in slices, graded signals in vivo; indicator choice is preparation-specific | Native experimental measurement | ESTABLISHED (other neurons) |
| **ASAP5** | newer candidate (Neuron, 2024): improved sensitivity for unitary synaptic events (cultured neurons); two-photon responses compared in Drosophila (Mi1) | YES — dendrites and soma in culture | YES — spontaneous EPSPs imaged throughout dendrites in culture; Drosophila demonstration in Mi1 | improved AP and subthreshold detection across illumination regimes | enhanced sensitivity near the resting potential; synaptic-event sensitivity demonstrated in culture | compared with JEDI-2P in Drosophila Mi1; not calibrated in MN5 | **NONE** | synaptic-event sensitivity demonstrated in cultured neurons, not at an identified Drosophila synapse; newest of the three, least validated in Drosophila | Native experimental measurement | FEASIBLE_BUT_UNVALIDATED (candidate) |

**Do not invent numerical values.** No indicator amplitude, kinetics,
photostability or SNR figure is quoted here, because none is
supported for MN5. Every performance statement above is qualitative
and attributed to its source neuron; none transfers quantitatively to
MN5.

## C. Genetic Access

**DLMn Split-GAL4 access (MN1–5) is established.** DLMn Split-GAL4
driver lines give genetic access to the MN1–5 population — all five
DLM motoneurons. This is **population access**, and it is explicitly
**NOT equivalent to an MN5-specific driver**: a signal recorded under
a DLMn-population driver could originate from MN1, MN2, MN3, MN4 or
MN5, so MN5 must be identified anatomically within the labelled
population (see below), not by driver specificity.

**No MN5-only driver has been demonstrated in the evidence base.**
The only GFS-circuit driver documented in the evidence base,
OK307-GAL4, is expressed in the GF, DLMmn, TTMmn **and** PSI — it
is neither MN5-specific nor PSI-specific.

**Anatomical identification strategy (established precedent).** MN5 is
identified by retrograde Texas-red dextran backfill injected near the
DLMa/b muscles, transported back to the soma, followed by in-situ
somatic whole-cell recording in a dissected thorax (Fayyazuddin et
al. 2006). MN5 somata are large, in a characteristic location in the
mesothoracic (T2) neuromere, and exit via the posterior dorsal motor
nerve (PDMNa). This strategy identifies the **soma**; it does not, by
itself, identify the distal PSI-contact-bearing process in a living
preparation.

**Rejected claim.** The claim **"MN5-specific driver exists"** is
rejected. No such driver is established in the evidence base, and
DLMn-population (MN1–5) access must never be mislabeled as
MN5-specific access.

## D. PSI Stimulation

GF activation, PSI activation, and direct MN5 activation are three
distinct manipulations and must be kept distinct throughout any design.

| Method | Specificity | Established precedent | Likely confounds | Can isolate PSI→MN5? |
|---|---|---|---|---|
| **GF electrical stimulation** | low for PSI — drives the whole escape pathway (GF→TTMn directly; GF→PSI→MN5 disynaptically) | ESTABLISHED (Fayyazuddin 2006; GFS stimulation protocols) | co-activates TTMn and the whole GFS; PSI is driven *through* the GF→PSI electrical synapse, so the MN5 response is not PSI-specific; network recruitment | **NO** — Fayyazuddin 2006 stimulated the GF, and PSI was never directly activated |
| **PSI genetic activation** (driver + effector) | would be high **if** a PSI-specific driver existed | NOT ESTABLISHED — no PSI-specific driver in the evidence base (OK307-GAL4 is not PSI-specific) | requires a PSI-specific driver that does not exist in the evidence base; expression-level and effector-kinetics unknowns | **NOT ESTABLISHED** — blocked at the driver step |
| **PSI optogenetic activation** | would be high with a PSI-specific driver + opsin | NOT ESTABLISHED — same driver gap, plus no optogenetic PSI activation has been demonstrated | opsin kinetics/expression unknowns; light-scatter activation of neighbouring neurons; requires the missing PSI-specific driver | **NOT ESTABLISHED** — blocked at the driver step |
| **Focal/electrical stimulation at the PSI soma/process** | moderate — depends on stimulus confinement; PSI somata are in the thorax and accessible | focal electrical stimulation is a standard method; not demonstrated for PSI specifically in the evidence base | current spread to neighbouring neurons (887/897 bodies converge on MN5); polysynaptic recruitment; possible activation of passing axons; must be validated by latency and by off-PSI controls | **PARTIALLY** — plausible, but PSI-specificity must be demonstrated by controls, not assumed |

**Net:** the only *established* stimulation is GF electrical
stimulation, which is **not** PSI-specific. PSI-specific activation —
genetic, optogenetic, or focal — is **NOT ESTABLISHED** in the
evidence base and is a prerequisite for any PSI-input-specific
measurement.

## E. Optical Measurement Configuration

Proposed configuration (a design, not a performed experiment):

```
DLMn (population) driver
  → GEVI expression in the DLMn population
  → identify MN5 anatomically (retrograde backfill / soma position)
  → somatic electrophysiology (whole-cell patch, absolute mV reference)
  → image ≥2 spatial locations along the PSI-contact-bearing process
  → activate PSI / GFS (with the specificity controls of §D)
  → compare responses across sites and against the somatic patch
```

Three signal classes must be kept strictly separate:

1. **Directly measured fluorescence** — ΔF/F at each imaged site.
   This is the only quantity the optics measure. It is relative, not
   absolute.
2. **Calibrated voltage** — millivolts, obtained **only** after the
   calibration requirements of §F are met. GEVI fluorescence cannot
   automatically be converted to voltage.
3. **Derived spatial ratio** — ΔF/F_process / ΔF/F_soma. This is an
   *experimentally defined optical ratio*. It equals
   ΔV_process / ΔV_soma **only** under an explicit, validated
   linearity assumption (same indicator at both sites, linear
   response over the operating range, site-independent proportionality).
   That assumption must be stated and marked; it must never be silently
   applied.

## F. Calibration

**ΔF/F ≠ ΔV automatically.** GEVI fluorescence is a relative signal;
converting a fluorescence ratio into a voltage ratio requires an
appropriate calibration/linearity assumption, and that assumption must
be explicitly marked wherever a ratio is interpreted as a voltage
ratio. No conversion formula is implemented as a biological model in
this audit.

Evidence required before any optical ratio is interpreted quantitatively
in MN5:

- **voltage-response calibration** of the indicator in the preparation
  (ΔF/F vs known voltage, ideally anchored by a simultaneous electrical
  reference);
- **operating-range linearity** — the response must be demonstrated
  linear over the voltage range the experiment will traverse;
- **baseline fluorescence** characterization (resting F, stability over
  the recording);
- **bleaching correction** (photobleach trajectory measured and
  corrected);
- **motion correction** (movement artifacts removed or shown
  negligible);
- **optical background** (autofluorescence, out-of-focus light,
  indicator-free regions);
- **spatially varying expression** (expression gradients along the
  process would masquerade as spatial voltage differences);
- **membrane orientation** (indicator orientation relative to the
  membrane can alter the response; relevant in thin processes);
- **indicator kinetics** (response/deactivation times relative to the
  events being measured).

**Linearity caveat.** The claim that ASAP2f is substantially linear
over a broad membrane-potential range is supported for the *Drosophila
neurons in which it was demonstrated*; it is **not** a demonstration
for MN5, and it must be re-validated per preparation before any ΔF/F
ratio is read as a ΔV ratio.

## G. Spatial Sampling

| Configuration | What it establishes | What it does not |
|---|---|---|
| **2 sites** | a pairwise spatial difference between the two sampled locations (soma-referenced process site vs soma, or two process sites) | an attenuation profile; cannot distinguish monotonic attenuation from nonmonotonic behaviour; cannot localize where along the process the change occurs |
| **3+ sites** (spatially registered) | a stronger spatial profile; potentially distinguishes attenuation from nonmonotonic behaviour; the shape of the decay with distance | separate identification of Ra, Rm or Cm |

**Neither configuration identifies Ra, Rm, or Cm.** Two sites constrain
only the Ra·Rm combination (≈ the electrotonic length); separate
identification requires ≥3 *known* locations **plus** known geometry,
and even then only as a model fit. Cm is not a transfer observable at
all — it is a whole-cell somatic measurement, and the two MN5 values
remain contested (C-01). Any statement that a spatial optical
measurement "measures" Ra, Rm or Cm is an over-claim and is rejected
by this audit.

## H. EM Registration

Existing project facts:

- **43 PSI→MN5 contacts** (17 on body 801970 / PSI left, 26 on body
  801295 / PSI right; minconf 0.5; 0 cross-pairings, independently
  corroborated by the annotation layer).
- **All 43 contacts carry the official postsynaptic compartment label
  `axon`** (MaleCNS v1.0 synapse annotation layer).
- **Contact coordinates exist in MaleCNS EM space** (8 nm voxels).

**A live optical measurement cannot be assigned to an individual EM
contact without an EM→live registration procedure.** Such a
registration does not exist: the SIZ registration has four independent
blockers (the reconstruction was never deposited; there are zero
dendrite-labelled nodes; no anatomical axis is documented anywhere; and
there is no transform from the light-microscopy frame into MaleCNS EM
space). Therefore any optical site in this design is referenced to the
**input site and the anatomically identified process**, never to a
specific one of the 43 EM contacts. Claiming that a measured optical
site "corresponds to" or "is registered to" a specific EM contact is
unsupported and is rejected.

Related anatomical limits (unchanged): the contact→**labelled soma**
graph path is permanently unresolved (zero `kind=1` nodes in all 9
MN5/PSI skeletons); the contact→soma-proxy path is a
model-derived estimate resting on a model assumption; the SWC `kind=2`
biology is undefined by the source; and the published contact distances
(nerve span ≈50 µm; root-referenced path 169.2–267.8 µm;
`somaLocation` straight line 110.3–172.9 µm) are geometry only — a
straight line is not a path length, and none is a soma-referenced
biological path.

## I. Controls

Every configuration must include, at minimum:

1. **no-stimulation control** — identical imaging without stimulation,
   to expose stimulus-locked vs spontaneous signals;
2. **GEVI-only optical artifact control** — indicator expression
   without stimulation (and, where possible, a no-indicator
   preparation) to separate optical/photodynamic artifacts from voltage
   signals;
3. **motion control** — movement monitoring/correction, or a
   demonstration that motion artifacts are negligible in the window;
4. **photobleaching control** — bleach trajectory measured and
   corrected, with stability demonstrated over the recording;
5. **MN1–4 comparison** — sibling DLM motoneurons imaged under the
   same population driver, to show the measured signal is MN5-specific
   and not a population-wide artifact (dual somatic patch of MN1–4
   pairs is established: Hürkey 2023; MN5 was not among them);
6. **MN5 anatomical confirmation** — independent confirmation of MN5
   identity (backfill/soma position) in every preparation;
7. **direct MN5 stimulation/control** — direct somatic current
   injection in MN5 (established), which probes somatofugal transfer —
   the reverse direction; reciprocity is **not** guaranteed in a cell
   with subthreshold-active conductances;
8. **GF-vs-PSI stimulation comparison** — the same measurement under
   GF stimulation and under direct PSI activation, to separate
   pathway-driven from PSI-specific components;
9. **Dα7-independent negative control where experimentally
   appropriate** — appropriate only *after* the total synaptic
   conductance is known; the Dα7-specific component cannot be isolated
   before that;
10. **electrical coupling confound assessment** — PSI participates in
    the GFS gap-junction network (GF→PSI is electrical, via
    ShakB/innexin), while PSI→MN5 itself is chemical (acetylcholine);
    coupled contributions from the network must be controlled, not
    assumed absent.

## J. Acceptance Criteria

Every acceptance criterion below is a **PROPOSED_EXPERIMENTAL_CRITERION**.
None is an existing biological fact, a published standard, or a
demonstrated result.

1. reproducible stimulus-locked process signal — **PROPOSED_EXPERIMENTAL_CRITERION**
2. signal absent in no-stimulation controls — **PROPOSED_EXPERIMENTAL_CRITERION**
3. signal survives motion/bleaching correction — **PROPOSED_EXPERIMENTAL_CRITERION**
4. MN5 identity independently confirmed — **PROPOSED_EXPERIMENTAL_CRITERION**
5. spatially separated sites show reproducible differences — **PROPOSED_EXPERIMENTAL_CRITERION**
6. calibration demonstrates that measured GEVI changes can be interpreted quantitatively within the tested voltage range — **PROPOSED_EXPERIMENTAL_CRITERION**
7. stimulation pathway is independently validated — **PROPOSED_EXPERIMENTAL_CRITERION**

## K. What the Experiment Cannot Identify

These inequalities are preserved explicitly:

```
transfer ratio ≠ Ra
transfer ratio ≠ Rm
transfer ratio ≠ Cm
local voltage ≠ synaptic conductance
somatic EPSP ≠ local synaptic voltage
Erev ≠ conductance
GEVI fluorescence ≠ voltage without calibration
anatomical contact ≠ electrophysiologically active contact
```

In words: a measured spatial ratio (optical or electrical) does not
identify any passive parameter; a local voltage does not measure a
synaptic conductance (conductance and attenuation are inseparable at
one site); a somatic EPSP is a filtered voltage, not the local
synaptic voltage at the contact; a reversal potential is not a
conductance; GEVI fluorescence is not voltage unless calibrated; and
an anatomical contact is not thereby shown to be the
electrophysiologically active contact.

## L. Minimum Gate-Opening Experiment

The smallest experimentally credible configuration that could resolve
**B-4** (no MN5 non-somatic or dual-site voltage measurement):

- **DLMn-population GEVI access** (established for MN1–5) — not
  MN5-specific, so anatomical identification is mandatory;
- **anatomical MN5 identification** (retrograde backfill / soma
  position — established precedent);
- **somatic whole-cell reference** (established; absolute mV anchor
  and calibration reference);
- **≥2 process imaging sites** along the PSI-contact-bearing process;
- **validated PSI/GF stimulation** with the §D specificity controls
  (PSI-specific activation is currently NOT ESTABLISHED and is a
  prerequisite);
- **GEVI calibration** per §F before any ratio is read as a voltage
  ratio;
- **optical artifact controls** per §I;
- **EM/live registration — required only if individual PSI contacts
  are claimed**; without it, no optical site may be attributed to one
  of the 43 EM contacts.

**This is a PROPOSED EXPERIMENT, not completed evidence.** No element
of it has been performed in MN5, and it resolves B-4 only if executed
successfully. It would **not** identify Ra, Rm, Cm, the synaptic
conductance, Erev, or the Dα7 conductance.

## Provenance

| Statement | Class |
|---|---|
| ASAP2f multi-compartment Drosophila voltage imaging; broad-range linearity | Native experimental measurement (other neurons) |
| ASAP2s Drosophila two-photon benchmarking; temporal performance | Native experimental measurement (other neurons) |
| ASAP5 synaptic-event sensitivity; Drosophila Mi1 comparison | Native experimental measurement (other neurons / culture) |
| DLMn Split-GAL4 MN1–5 population access | Native experimental measurement (tool capability; primary citation to be supplied) |
| No MN5-specific driver; no PSI-specific driver | Model assumption (absence claim; per project convention, absent quantities are classed model assumption because any positive claim would be an invention) |
| MN5 identification by backfill + somatic whole-cell | Native experimental measurement |
| GFS electrical stimulation established; GF ≠ PSI activation | Native experimental measurement |
| 43 contacts, all `compartment_post = axon`, EM coordinates | Anatomical measurement |
| EM→live registration unresolved; no soma node; SIZ blockers | Anatomical measurement / Model assumption (absence) |
| ΔF/F ≠ ΔV; calibration requirements | Native experimental measurement (indicator property) |
| 2-site vs 3+ sampling behaviour | Model assumption (design convention) |
| Ra/Rm/Cm not identified by either configuration | Model-derived estimate (identifiability analysis, not a measurement) |
| The project's adopted passive parameters (specific membrane capacitance, axial resistivity, leak density) | Literature-derived passive parameter (adopted model inputs under conflict C-10; not used or introduced here) |
| MN5 subthreshold-active conductances | Native experimental measurement (freeze SAFE rows) |
| PSI minority input (0.16% / 0.23%); largest partner 7–10× | Anatomical measurement |
| MN5 axon diameter unmeasured | Model assumption (absence) |
| Contacts in the PDMN peripheral nerve | Anatomical measurement |
| Electrode access to small insect processes impractical (their preparation) | Native experimental measurement |
| Optical access to a thoracic motor nerve not demonstrated | Model assumption (absence) |
| MN1–4 dual somatic patch established | Native experimental measurement |
| MN5 Cm contested (C-01) | Native experimental measurement, contested |
| Dα7 conductance; spatial voltage transfer | Model assumption (absence) — **BLOCKED** |
| The minimum gate-opening experiment | Model assumption (proposal) — **PROPOSED_EXPERIMENTAL_CRITERION** |

Machine-readable companion: `research/psi_mn5_optical_experiment_design_audit.csv`.

## Final Gate Status

- **PSI→MN5 postsynaptic spatial voltage transfer: NOT AUTHORIZED**
- **Dα7 biological conductance: NOT AUTHORIZED**

This audit changes no biological constant, introduces no parameter,
adds no synthetic measurement, and opens no gate.
