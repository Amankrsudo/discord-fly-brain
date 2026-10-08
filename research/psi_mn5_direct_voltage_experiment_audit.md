# Direct PSI→MN5 Voltage-Transfer Experiment Audit

Experimental-design / evidence-gap audit. **No experiment was performed, no
model was built, no parameter was fitted, no gate was changed, no code was
modified.** This document designs the strongest experimentally defensible
direct measurement of voltage transfer between the PSI-contact-bearing MN5
process and the MN5 soma, and states exactly what such a measurement would
and would not identify.

## Executive Verdict

The desired direct observable is

```
ΔV_distal / ΔV_soma
```

for the **same MN5** and a **controlled perturbation**, or an experimentally
equivalent calibrated relationship.

**The scientifically direct configuration — somatic whole-cell patch plus a
second patch on the PSI-contact-bearing axon — is access-blocked.** All 43
PSI→MN5 contacts sit on the axon in the posterior dorsal motor nerve
(PDMN), a *peripheral* nerve in the thorax (Fayyazuddin 2006: contacts
*"span 50 µm and follow the axons out into the posterior dorsal motor
nerve"*). No Drosophila motor axon has ever been patch-clamped in situ;
MN5's axon diameter is **unmeasured** (the freeze records MN5 axonal
length as `NONE`); and Gouwens & Wilson 2009 documented electrode access
to small insect processes as impractical — for *their* preparation
(≈200 nm antennal-lobe processes), which is a statement of practical
difficulty, not a theorem about MN5's unmeasured axon.

**The strongest feasible configuration is somatic whole-cell patch +
genetically encoded voltage indicator (GEVI) imaging at ≥2 sites along the
PSI-contact-bearing process, during direct focal PSI activation**, with the
somatic patch serving as the millivolt calibration reference (configurations
C/E below). The method template is Yang 2016 (ASAP2f, two-photon, in vivo,
Mi1/Tm3/Tm1/L1/L2 — amplitude decayed away from the site of primary
synaptic input while time courses were preserved, and the decay was then
used to *constrain* passive parameters). Axonal GEVI imaging precedents
exist (Chamberland 2017, Liu 2022, Pang 2024 — L1/L2 axon terminals and
arbors) — but **all are in the optic lobe, imaged through a cuticle window;
none is in a thoracic motor nerve, none is in MN5, and none is
PSI-specific.**

A dual-site measurement — electrical or calibrated optical — measures the
transfer ratio **directly** and would resolve **B-4**. It does **not**
separately identify Ra, Rm, or Cm: two sites constrain only the combination
(≈ the electrotonic length); separate identification requires **≥3 known
locations plus known geometry**, and even then only as a model fit (the
vertebrate soma+axon precedent constrains the passive parameter *set* with
anatomically detailed models, not two-site ratios).

**Critical targeting caveat.** MaleCNS EM coordinates cannot currently be
registered onto a living fly: the SIZ registration has four independent
blockers (reconstruction never deposited, zero dendrite-labelled nodes, no
anatomical axis documented, no transform from the light-microscopy frame
into EM space). Therefore the measurement is referenced to the *input site
and the labelled process*, not to any specific one of the 43 EM contacts.
Attributing a measurement to a specific contact requires a registration
that does not exist.

**Both gates remain NOT AUTHORIZED.** This audit designs an experiment; it
performs none and claims no measurement.

## Current Scientific Blocker

**B-4 = no MN5 non-somatic or dual-site voltage measurement.**

Every MN5 electrophysiology dataset in the evidence base is somatic
whole-cell (Fayyazuddin 2006; Ryglewski & Duch 2009; Herrera-Valdez
2013). A transfer ratio needs a numerator (voltage at the contact) and a
denominator (voltage at the soma). Every MN5 dataset has a denominator and
**no numerator**. The previous reversal-potential audit established that a
somatic reversal series does not touch B-4: it bounds the synaptic *source*
(B-6, partially) but says nothing about propagation, because conductance and
attenuation are inseparable at one recording site.

The deeper problem is a **convolution**: a PSI-evoked somatic EPSP is

```
somatic EPSP = (synaptic response at the contact) × (contact→soma transfer)
```

with both factors unknown. Any single-site measurement — electrical or
optical — returns the product, not the factors. Resolving B-4 requires a
**second measurement site** on the contact-bearing process, which is precisely
what has never been done in MN5.

## Existing Experimental Precedent

Every precedent is classified A–E. **No precedent in B–E is proof of
feasibility in MN5.**

### A. Demonstrated directly in MN5

| # | Organism / neuron / preparation | Method | Locations recorded | Voltage directly measured? | Spatial distance | Synaptic input? | Actually identified | Feasibility limitations |
|---|---|---|---|---|---|---|---|---|
| A1 | *Drosophila*, MN5 (DLMn a,b), in situ thorax, retrograde Texas-red dextran backfill (Fayyazuddin 2006) | somatic whole-cell patch; GF stimulated | soma only | **YES — soma only** | contacts *"span 50 µm"* of nerve, **not soma-referenced** | YES (GF→PSI→MN5; PSI never directly stimulated) | somatic EPSP 4.71 ± 0.35 mV (n=10) at −74 mV; *gfA¹* 1.5 ± 0.32 mV (n=7); qualitative statement that a distally generated AP *"fails to propagate antidromically into the dendrite and therefore is filtered by the passive membrane properties"* | no distal voltage, no transfer coefficient; the 50 µm is a nerve span, not a soma-referenced path |
| A2 | *Drosophila*, MN5 (Ryglewski & Duch 2009) | somatic whole-cell + compartmental model | soma; model compartments | soma only (model is simulated) | per-compartment model map | model current injection | Fig 1B **steady-state current**-transfer ratio 0.2–1, on Manduca-derived Ra = 90 Ω·cm and Cm = 1.15 µF/cm² adopted by assertion; authors disclaim exactness | simulation, not measurement; reports current transfer, not synaptic voltage transfer; non-Drosophila passive parameters |
| A3 | *Drosophila*, MN5 (Herrera-Valdez 2013) | somatic whole-cell | soma only | YES — soma only | — | — | somatic electrical properties; re-reports the 127 ± 16 pF capacitance | no non-somatic site |
| A4 | *Drosophila*, MN5 (Kuehn & Duch 2013) | anti-VGSC immunocytochemistry on reconstructions | none (anatomical) | **NO** | SIZ *"about 100 µm from the soma"* and *"11 ± 3 µm around the origin of the most distal posterior dendrite"* (n=7) | no | SIZ *position* (immunolabel, not electrophysiology); cholinergic inputs peak 25–65 µm from the SIZ | SIZ unregistered to MaleCNS (4 blockers); 0 of 43 contacts fall in the literature shell; no voltage measured |

**Category A summary:** MN5 has exactly one recording site demonstrated —
the soma. The closest thing to a distal MN5 measurement is a qualitative
directional statement (A1) and a disclaimed simulation (A2).

### B. Demonstrated in Drosophila, another neuron

| # | Organism / neuron / preparation | Method | Locations recorded | Voltage directly measured? | Spatial distance | Synaptic input? | Actually identified | Feasibility limitations |
|---|---|---|---|---|---|---|---|---|
| B1 | *Drosophila*, Mi1/Tm3/Tm1/L1/L2, in vivo, two-photon through cuticle (Yang 2016, *Cell* 166:245) | ASAP2f GEVI, two-photon; visual stimulation | soma, dendritic and axonal arbors | **YES — optical, relative (ΔF/F)** | Mi1 ≈ 50 µm long; main neurite 200–300 nm; arbor processes ≤ 200 nm | YES (visual input to the arbor) | *"The amplitude of the responses generally decayed away from the site of primary synaptic input in layer M1, but the time courses of the response waveforms were largely preserved"*; the decay was used to **constrain** Ri to 40–420 Ω·cm and Rm to 1–21 kΩ·cm² on the Takemura 2013 Mi1 EM morphology | **not MN5**; ~10× smaller neuron; no simultaneous electrical reference; indicator performance not transferable quantitatively to MN5 |
| B2 | *Drosophila*, L1/L2, in vivo + organotypic slices (Chamberland 2017, *eLife* 6:e25690) | ASAP2s GEVI, random-access multi-photon (FEVIR) | L2 axon terminals (in vivo, through a cuticle window); 25 dendritic locations (slices) | YES — optical, relative | 25 locations on one dendritic tree; single voxels | YES (visual) | single-trial AP detection; graded potentials with subcellular resolution; high SNR > 30 min; ASAP2s faster and larger than ArcLight | optic-lobe neurons, not a motor nerve; no MN5, no PSI |
| B3 | *Drosophila*, L2 axon terminals, in vivo (Liu 2022, *Cell* 185:3408) | JEDI-2P and ASAP3 GEVIs, two-photon | L2 axon termini | YES — optical, relative | axon termini | YES (visual) | JEDI-2P ≈ 60% larger responses than ASAP2f with similarly fast kinetics; 81.6% vs 58.4% fluorescence retained after 2 min | same modality caveat; indicator benchmarking, not transfer |
| B4 | *Drosophila*, T4c, in vivo (Mishra, Serbe-Kamp, Borst & Haag 2023, *J Neurosci* 43:2497) | ArcLight GEVI + GCaMP6f, two-photon | dendrites (medulla M10) **and** axon terminals (lobula plate layer 3) — two compartments of the same cell | YES — optical, relative | dendrite vs axon terminal | YES (visual) | voltage-to-calcium transformation differs between compartments; ArcLight ΔF/F compared with whole-cell patch from T4 cells (Groschner 2022) under identical stimuli | **not simultaneous** patch+imaging; not MN5; not a transfer ratio |
| B5 | *Drosophila*, L1/L2 axonal arbors, in vivo (Pang 2024/2025, *Curr Biol*) | ASAP2f GEVI, two-photon | axonal arbors of individual cells | YES — optical, relative | arbor of one cell | YES (visual) | cell-type-specific temporal tuning of L1/L2 axonal voltage responses | optic lobe; not MN5; not PSI |
| B6 | *Drosophila*, DM1 PN / antennal-lobe LNs (Gouwens & Wilson 2009, *J Neurosci* 29:6239) | attempted electrode recording | small processes | **NO** | processes ≈ 200 nm | — | *"Electrode recordings are impossible from these small processes"*; *"We assume that spikes are large at the SIZ (although we cannot directly test this assumption)"* | the access constraint most cited against configuration A — a statement about their small processes, not about MN5's unmeasured axon |
| B7 | *Drosophila*, multiple neuron classes, larval + adult CNS (Ravenscroft 2020, *J Neurosci* 40:42:7999) | para (NaV) localization + whole-cell patch of adult CNS neurons | soma; DAS localization | patch: soma only | DAS = distal axonal segment, distal to dendritic integration | no | the only Drosophila NaV channel localizes to a **distal axonal segment (DAS)** — the invertebrate counterpart of an AIS, positioned distally; adult CNS whole-cell patch is routine | supports the SIZ/DAS concept; does not demonstrate axonal recording |
| B8 | *Drosophila*, MN1–MN4 pairs, 2–3-day adults (Hürkey 2023, *Nature* 618:118) | **dual** somatic whole-cell patch, two electrodes from opposite sides | soma of each of two MNs | YES — two somata | soma-to-soma | YES (electrical coupling) | coupling coefficients 0.023 ± 0.003 SEM (6 pairs, MN1–MN2/MN3–MN4) and 0.01 ± 0.0027 (10 pairs) | **two cells, not two sites on one cell**; MN5 was not among the patched pairs; MN1→MN5 CC not reported |
| B9 | *Drosophila* larva, aCC MN (Fushiki 2016, *eLife* 5:e13253) | single-site somatic patch, MN driven by a named presynaptic MN's somatic AP | soma only | YES — soma only | contact→soma distance **not reported** | YES | monosynaptic drive of aCC by a identified premotor MN | single site; larval, not adult MN5 |
| B10 | *Drosophila* larva, aCC MN (Giachello 2022, *J Neurosci* 42:35:6724) | somatic patch + connectivity validation | soma only | YES — soma only | — | YES | monosynaptic premotor→aCC connectivity validated electrophysiologically | single site |
| B11 | *Drosophila*, leg motor neurons (Azevedo 2020, *eLife* — size principle) | somatic patch + extracellular | soma; extracellular axonal | patch: soma only | fast/intermediate/slow MN axon diameters differ | — | *"Perhaps because of the small size of its axon, we were unable to identify slow motor neuron spikes with extracellular recordings"* | access precedent: small axon caliber defeats extracellular identification — relevant to any nerve-based design |
| B12 | *Drosophila* larva, aCC MN (PLOS Comput Biol 2015) | morphological simulation of ionic-current filtering | model | NO (model) | SIZ predicted on the primary axon, 70 µm after the most distal branching point | model current injection | a Drosophila MN model predicting distal SIZ; series resistance between the somatic electrode and the distal spike-generating region explains somatic recording artifacts | modeling, not measurement; larval cell |

**Category B summary:** optical subcellular voltage imaging of *another*
Drosophila neuron is demonstrated (B1–B5); axonal GEVI imaging is
demonstrated (B2, B3, B5); dual **somatic** patch of MN *pairs* is
demonstrated (B8); electrode access to small insect processes is documented
as impractical (B6); the Drosophila SIZ is a *distal axonal segment*
(B7, B12). **None of these is MN5, and none images or patches a thoracic
motor-nerve process.**

### C. Demonstrated in another insect

| # | Organism / neuron / preparation | Method | Locations recorded | Voltage directly measured? | Spatial distance | Synaptic input? | Actually identified | Feasibility limitations |
|---|---|---|---|---|---|---|---|---|
| C1 | blowfly, CH (centrifugal horizontal) neuron, in vivo (Egelhaaf et al. 2003, *J Neurosci* 23:30:9805) | intracellular microelectrode | **"All recordings were made in the axons of the neurons"** | YES — axonal intracellular, single site | axon (location not dual) | YES (HS input via electrical coupling; columnar inputs) | CH response composition; selective single-cell ablation method | **single-site** axonal recording, not dual-site; large optic-lobe axon, not a thin motor axon |
| C2 | blowfly, photoreceptor axons and LMCs, intact retina (J Neurosci 30:28:9557, 2010) | intracellular electrode + extracellular probe; V_in − V_ex subtraction | axon (intracellular) + nearby extracellular | partially — Vm estimated by subtraction | immediate vicinity | YES (photoreceptor→LMC synapse) | extracellular field potentials modify synaptic transfer; a two-electrode subtraction method in an insect axon | not a patch; not a transfer ratio; subtraction assumes series arrangement |
| C3 | blowfly, mnb1 steering MN, in vivo (Fayyazuddin & Dickinson 1996, *J Neurosci* 16:5216) | somatic intracellular; haltere nerve stimulation | soma | YES — soma only | — | YES (haltere afferents, electrotonic input) | compound EPSP in a steering MN from haltere nerve stimulation | single site; not dual-site |
| C4 | locust, DCMD | somatic intracellular; cuff electrode on the axon (extracellular) | soma; axon (extracellular, multi-unit) | soma YES; axon extracellular spikes only | — | — | DCMD response properties; extracellular axonal spike recording | cuff severs/encircles the nerve; no graded subthreshold axonal voltage |
| C5 | cockroach / cricket | extracellular nerve cuff/hook electrodes | nerve (multi-unit) | NO (spikes, not Vm) | — | — | multi-unit activity | cannot resolve a single synapse or graded voltage |

**Category C summary:** insects have **single-site** axonal intracellular
recordings (C1), an intracellular-plus-extracellular subtraction in an axon
(C2), and routine extracellular nerve recording (C4, C5). **No insect
preparation has demonstrated simultaneous voltage recording at two sites on
one process.**

### D. Demonstrated in vertebrate neurons

| # | Organism / neuron / preparation | Method | Locations recorded | Voltage directly measured? | Spatial distance | Synaptic input? | Actually identified | Feasibility limitations |
|---|---|---|---|---|---|---|---|---|
| D1 | rat, neocortical pyramidal, slice (Stuart & Sakmann 1994, *Nature* 367:69) | **simultaneous soma + apical dendrite whole-cell patch** | soma + dendrite | YES — both, absolute mV | dendrite 100–378 µm from soma | YES (synaptic stimulation; dendritic Na currents) | APs initiate in the axon and actively backpropagate into the dendrite; dendritic patch feasible in large-process neurons | requires a large, visually identified process — the condition Gouwens & Wilson 2009 says insect processes violate |
| D2 | rat, neocortical pyramidal, slice (Stuart, Schiller & Sakmann 1997, *J Physiol* 505:617) | simultaneous soma + dendrite + axon | three sites | YES — all three | — | YES | AP initiation site and propagation sequence | triple patch is the technical ceiling; large processes only |
| D3 | rat, subicular / neocortical pyramidal, slice (Colbert & Johnston 1996; Stuart & Häusser 1994) | simultaneous soma + axon-initial-segment patch | soma + AIS | YES — both | AIS ~10–35 µm from soma | YES | orthodromic APs initiate in the axon, then invade the soma | AIS is accessible because it is large and adjacent to the soma |
| D4 | rat, thick-tufted L5 pyramidal, slice (Kole et al. 2007; Kole & Popovic 2016; saltatory-conduction study 2023) | **simultaneous soma + axon dual patch, up to ~830 µm**; passive cable parameter extraction from soma-axon voltage transients | soma + axon (± dendrite ± AIS) | YES — both, absolute mV | axon 145–830 µm from soma | YES (current injection) | with **anatomically detailed models**, soma-axon transients constrain Ri, Rm, Cm as a *set*; additional soma+dendrite+AIS recordings "found no difference in Ri, Rm and Cm" | parameter identification required **known geometry + model fitting**; two sites alone do not separate Ra/Rm; myelinated mammalian axon, not an insect unipolar process |
| D5 | rat, L5 pyramidal, slice (Palmer & Stuart 2006, *J Neurosci* 26:6:1854) | voltage-sensitive dye (JPW3028) loaded via somatic patch; optical recording of axon, soma, proximal dendrite | multiple axonal sites + soma | YES — optical, voltage-calibrated dye | ~10 µm optical resolution, 10 kHz | YES (electrical and synaptic stimulation) | AP initiation ~35 µm from the axon hillock, in the distal AIS | synthetic dye, not genetically encoded; slice |
| D6 | mouse, L2/3 pyramidal, in vivo (patterned ChR2 + dual-plane structured-illumination voltage imaging, 2023) | simultaneous optical perturbation and voltage monitoring of dendritic and somatic voltage | dendrite + soma | YES — optical | multiple dendritic planes | YES (optogenetically induced) | distance-dependent somato-dendritic attenuation in vivo | vertebrate; not a synapse-specific measurement |
| D7 | mouse, awake (Villette 2019, *Cell* 179:1590 — ASAP3) | GEVI two-photon, simultaneous with electrophysiology | soma + processes | YES — optical + electrical | — | YES | ASAP3 reports subthreshold events in vivo with calibration | vertebrate; indicator performance not transferable to Drosophila MN5 |

**Category D summary:** simultaneous two-site voltage recording is a
**vertebrate technique**, demonstrated for soma+dendrite (D1), soma+AIS
(D3), and soma+axon up to 830 µm (D4), and with voltage-calibrated optical
methods (D5–D7). The D4 identifiability result is the key precedent:
soma+axon transients constrain the passive parameter **set** only when
combined with known geometry and a model fit — they do not, by themselves,
separately identify Ra, Rm and Cm.

### E. Theoretical / modeling precedent

| # | Model | What it does | Status |
|---|---|---|---|
| E1 | Ryglewski & Duch 2009 Fig 1B | per-compartment steady-state **current**-transfer ratio 0.2–1 for MN5 | simulation on Manduca-derived Ra/Cm adopted by assertion; authors disclaim exactness; **never a voltage-transfer measurement** |
| E2 | ModelDB 245415 (Augustin, Zylbertal & Partridge 2019) | simplified 4-cell GFS latency model, 8 sections, 51 segments each | Ra/Rm/Cm **never assigned** — runs on NEURON defaults (35.4 Ω·cm, 1 µF/cm²); anatomy "simplified … chosen to capture general cell proportions" |
| E3 | aCC SIZ model (PLOS Comput Biol 2015) | Drosophila larval MN morphology model; predicts distal SIZ and quantifies somatic recording artifacts from distal events | model, larval cell, adopted channel properties |
| E4 | Yang 2016 passive-parameter constraint | uses the *measured* Mi1 optical decay to bound Ri 40–420 Ω·cm, Rm 1–21 kΩ·cm² | a measurement constraining a model — the template for what an MN5 optical profile could do |

## PSI-Contact Anatomical Target

**Verified (anatomical_measurement):** 43 PSI→MN5 contacts (17 on body
801970 / PSI left, 26 on 801295 / PSI right; minconf 0.5; 0 cross-pairings,
independently corroborated by the annotation layer); all 43 carry official
`compartment_post = axon`; contacts lie in the PDMN region; contact
coordinates are exact in MaleCNS EM space (8 nm voxels); `somaLocation` is
a **point annotation** for each body; MN5's `exitNerve` is PDMN; `somaSide`
L/R, `somaNeuromere` T2.

**Unresolved:** no `kind=1` soma node exists in any of the 9 MN5/PSI
skeletons, so the contact→**labelled soma** graph path is permanently
UNRESOLVED; the only soma-referenced paths are (i) contact→`somaLocation`
straight line 110.3–172.9 µm (a straight line is not a path), (ii)
contact→SWC-root path 169.2–267.8 µm (the root is the stalk origin, **not**
the soma, and neuPrint states stored-skeleton root nodes are "not
particularly significant"), and (iii) contact→soma-**proxy** tree path
154.1–241.6 µm (a `model_derived_estimate` resting on the `model_assumption`
that a `kind=2` proximal dilation is the soma). The SIZ is unregistered
(four independent blockers), SWC `kind=2` biology is undefined by the
source, and **0 of 43 contacts fall in the literature SIZ shell** (~100 µm
from the soma) — though note the contact→`somaLocation` straight-line
distances (110–173 µm) are *comparable* to the literature SIZ distance,
which makes the missing registration consequential rather than cosmetic.

**What anatomical localization would actually be needed to target the recording site:**

1. **A transform from MaleCNS EM space into the in-vivo frame.** It does
   not exist. The SIZ registration fails on four independent blockers
   (reconstruction never deposited; zero dendrite-labelled nodes; no
   anatomical axis documented anywhere; no light→EM transform). Without it,
   no EM coordinate — not a contact, not the `somaLocation`, not the
   SIZ — can be placed in a living fly.
2. **Identification of the contact-bearing process in the living
   preparation.** Achievable only if a driver labels MN5 as a whole (the
   process is then imaged and the response profile measured along it);
   attributing any imaged segment to a *specific* EM contact still requires
   the missing registration.
3. **The soma's in-vivo position.** This side *is* targetable: Fayyazuddin
   2006 identified MN5 somata by retrograde Texas-red dextran backfill
   from DLMa/b and patched them in a dissected thorax. The somatic end of
   the measurement is therefore established; the distal end is not.

**Explicit non-conversions (per the task and the frozen chain):**
`somaLocation` is not a measured soma boundary; the proxy path is not a
measured biological path; SWC `kind=2` is not called definitively axon;
no soma-referenced contact distance is invented here (the three distance
quantities above are reported with their caveats and are geometry only);
and no anatomical measurement is converted into an electrical parameter.

## Recording Configuration Comparison

For each configuration: what is directly measured, spatial/temporal
resolution, access problem, perturbation introduced, PSI specificity, local
voltage during PSI activation, direct transfer relationship, Ra/Rm/Cm
requirements, B-4/B-5/B-6 resolution, and what remains unidentified.
**"Direct transfer relationship" means the ratio ΔV_distal/ΔV_soma (or an
experimentally defined equivalent) is the primary observable.**

| Attribute | **A. Soma patch + distal axon patch** | **B. Soma patch + extracellular near PSI-bearing nerve** | **C. Soma patch + optical voltage imaging** | **D. Two optical locations on the same MN5 process** | **E. Local voltage imaging + somatic patch** |
|---|---|---|---|---|---|
| Directly measured | Vm at soma **and** Vm at the contact-bearing process, same event | field potential near the nerve (many axons) + Vm at soma | ΔF/F (relative voltage) at ≥1 process sites + absolute Vm at soma | ΔF/F at ≥2 process sites | as C, with the patch explicitly as the mV reference |
| Spatial resolution | single site, ~1 µm electrode tip | the electrode sampling volume — many axons, cannot isolate one synapse among 43 | subcellular (~0.5–1 µm two-photon; random-access can address 25+ sites) | subcellular ROIs | subcellular ROIs |
| Temporal resolution | full bandwidth (DC–kHz) | full bandwidth, but field potential | ms-scale (ASAP2f/2s kinetics; random-access 686 Hz in slices; in vivo lower) | ms-scale | ms-scale |
| Access problem | **severe**: the contacts are in the PDMN, a peripheral nerve; no Drosophila motor axon has been patched in situ; axon diameter unmeasured; Gouwens & Wilson 2009 document electrode access to small insect processes as impractical (their preparation) | moderate: nerve is surgically accessible in the thorax, but the MN5 axon is not individually addressable within the bundle | **lowest recording-side access**: no distal electrode; needs a MN5 driver, indicator trafficking into the axon, and optical access to the thoracic nerve (none demonstrated in adult Drosophila in the evidence base) | **lowest**: no electrode at all at the distal site; same driver/indicator/access needs as C | as C |
| Perturbation introduced | electrode shunt, access resistance, membrane damage at both sites; worse on a thin axon | minimal at the nerve; but the signal is a volume-conducted mixture | photobleach, indicator expression/trafficking variability, possible photodynamic effects; no mechanical disturbance of the process | as C, no somatic electrode at the distal end | as C; the somatic patch is itself a perturbation at the soma |
| Can PSI be stimulated specifically? | yes, with focal/direct PSI activation + controls (§PSI-Specific Stimulation) | same stimulation possible, but the recorded signal cannot be attributed to PSI→MN5 | same stimulation possible | same stimulation possible | same stimulation possible |
| Local voltage during PSI activation? | **YES — absolute mV at the process** | NO — field potential, not local Vm at the contact | YES — relative ΔF/F at the process (absolute mV only via calibration) | YES — relative ΔF/F at ≥2 process sites | YES — relative at the process, absolute at the soma |
| Direct transfer relationship? | **YES — the ratio is the answer; no cable inversion needed** | NO — field potential is not a Vm ratio | YES — as a calibrated ratio ΔF/F_process / ΔF/F_soma (proportionality cancels if the indicator response is linear and site-independent) | YES — as an experimentally defined **optical** ratio of ΔF/F (uncalibrated to mV without a reference) | YES — same as C |
| Requires Ra? | NO (ratio is measured) | n/a | NO for the ratio; YES if the profile is to be *interpreted* as Ra | NO | NO |
| Requires Rm? | NO | n/a | NO for the ratio; YES for profile interpretation | NO | NO |
| Requires Cm? | NO | n/a | NO | NO | NO |
| Resolves B-4? | **YES** | NO (field potential ≠ local membrane voltage at the contact) | **YES** (if the indicator is verified in MN5) | **PARTIALLY** — non-somatic voltage change observed, but uncalibrated to mV without an electrical reference | **YES** |
| Resolves B-5? | NO — the anatomical path to a labelled soma remains unresolved; the *ratio* does not need the path, but *targeting a specific contact* does | NO | NO | NO | NO |
| Resolves B-6? | NO — a different observable (needs a reversal series or local clamp) | NO | NO | NO | NO |
| Remains unidentified | Ra, Rm separately (need ≥3 sites + geometry); Cm; synaptic conductance; the passive vs active decomposition | everything — the method cannot isolate the synapse | calibration validity in MN5; Ra/Rm separately; Cm; B-5; B-6 | absolute mV; all of C's items | all of C's items |

**Assessment.** A is the scientific gold standard and is access-blocked.
B is realistic to perform but measures the wrong quantity (a field
potential from many axons) and cannot resolve a single synapse. C/E are the
same physical preparation (the distinction is emphasis: which signal is the
measurement and which is the reference) and are the strongest feasible
configuration: they measure the transfer ratio directly, need no Ra/Rm/Cm,
and avoid the distal-electrode access problem entirely — at the cost of
indicator-related confounds and an undemonstrated optical path to a
thoracic motor nerve. D is the no-electrode variant; it yields the ratio as
a relative optical quantity but cannot anchor absolute millivolts.

**On the optical ratio's validity.** If the same indicator sits at both
sites and its response is linear over the operating range, then
ΔF/F ∝ ΔV with a site-independent proportionality (ΔF/F is a fractional
signal, approximately independent of expression level), so the ratio of
ΔF/F equals the ratio of ΔV. This is the standard GEVI argument; it must
be validated per preparation, and **no MN5 validation exists**. The somatic
patch anchors the calibration at the soma only; the distal absolute mV
remains model-dependent unless a distal electrical reference exists.

## Dual-Site Identifiability

**Do not claim two-site recording separately identifies Ra, Rm, or Cm.**
Two sites yield one number per event — the ratio. The electrotonic length
λ depends on Ra, Rm and the geometry jointly; one ratio constrains the
combination, not the parts.

| Quantity | Two-site experiment identifies? | Required assumptions | Reason |
|---|---|---|---|
| distal/somatic voltage ratio | **YES — directly measured** | same cell, same event, controlled perturbation; adequate SNR; indicator linearity (optical) | the ratio *is* the observable |
| local voltage at the PSI region | **YES** (absolute mV with a distal patch; relative ΔF/F with imaging, absolute only via calibration) | electrode shunt acceptable (patch) or indicator linearity + calibration (optical) | second site measures it; calibration transfers ΔF/F to mV |
| Ra | **NO** | — | two sites constrain only the Ra·Rm combination (≈ electrotonic length); separate identification needs **≥3 known locations + known geometry**, or an independent constraint such as Rin *and* the geometry |
| Rm | **NO** | — | same as Ra |
| Cm | **NO** | — | not a transfer observable at all; Cm is a whole-cell somatic measurement (capacitive transient), and the two MN5 values conflict 2.95× (C-01) |
| tau_m | **NO** | — | requires Rm and Cm, neither identified |
| spatial attenuation | **YES as the empirical ratio/profile for the measured path**; NO as a model-derived electrotonic distance | the measured path is the one of interest | the observable is the attenuation itself; expressing it as an electrotonic distance requires Ra/Rm/geometry |
| PSI synaptic conductance | **NO** | — | different observable (B-6); needs a reversal series or local voltage clamp; conductance and attenuation are inseparable at one site |
| PSI E_rev | **NO** | — | different observable (B-6); needs a multi-point reversal series |
| Dα7 conductance | **NO** | — | needs total synaptic conductance first, then Dα7-specific isolation (null + synapse-restricted rescue); no native Dα7 conductance exists |

**The ≥3-location statement (explicit).** With current injection at **≥3
known locations** on the process *and* known geometry, Ra and Rm become
separately identifiable in principle (gate review row 4); **two** locations
constrain only their combination. The vertebrate soma+axon precedent (D4)
shows the passive parameter *set* can be constrained from soma-axon
transients — but only with an anatomically detailed model and fitting, and
the same study verified the constraint by adding more recording sites. Cm is
not identifiable from any voltage-transfer measurement.

**Passive vs active.** MN5 carries subthreshold-active conductances
(transient A-type K⁺, V½ activation −12.1 ± 1.4 mV, inactivation
−40.02 ± 0.33 mV; Ca²⁺ currents activating near −50 mV). A measured
ratio is therefore the **actual** (passive + active) transfer — the
biologically relevant quantity — but it is **not** the passive transfer,
and decomposing the two requires additional pharmacological/experimental
manipulation, not more recording sites.

## Access / Feasibility Constraints

**The distal process is the contact-bearing axon in the PDMN — a peripheral
nerve in the thorax, outside the CNS** (Fayyazuddin 2006). Audit of each
access question, with no invented dimensions or success rates:

- **Axon diameter.** **UNMEASURED for MN5** (the freeze records MN5
  axonal length as `NONE`; the only MN5 caliper data are dendritic,
  ~0.44 µm mean dendritic diameter from literature text, and the MaleCNS
  `kind=0` median radius 0.512 µm — same order, not a validation). No
  statement about MN5 axon diameter is made here. For scale context only:
  the leg-MN size-principle study (B11) reports that a *slow* leg MN's
  small axon defeated extracellular spike identification, and the Mi1
  processes imaged by Yang 2016 were ≤200 nm. These are other cells.
- **Distance/accessibility.** The PDMN is surgically accessible in the
  thorax (GFS preparations routinely expose DLM/TTM), but the individual
  MN5 axon within the nerve bundle is not individually addressable for
  patch. The PDMN's distalmost branch is purely motor (retrograde/anterograde
  staining, Power 1948 via the MN1–MN5 metamorphosis study), which helps
  identify the nerve but not one axon within it.
- **Would patching sever the axon?** A suction electrode on the nerve
  severs it (the standard larval NMJ preparation draws the nerve into a
  suction electrode, cutting the CNS side). The PSI contacts lie *between*
  the CNS and the muscle, so severing either side of the contact region
  removes the signal path being measured. A focal loose-patch on the nerve
  surface does not sever, but then it is an extracellular field recording
  (configuration B), not a patch.
- **Does the preparation preserve the PSI-bearing process?** Undemonstrated.
  The Fayyazuddin 2006 in-situ MN5 preparation (dissected thorax, flight
  muscles and gut removed, Texas-red backfill) preserves the soma and
  nerve well enough for somatic patch; whether it preserves the distal
  axon's viability for a second electrode is unknown and untested.
- **Would a local patch alter the measured voltage?** Yes — access
  resistance, seal leakage, membrane damage, and electrode shunt are
  documented confounds of dendritic/axonal patching, and are worse on thin
  processes. A distal patch that shunts the membrane biases the very ratio
  it measures (typically attenuating it).
- **Is extracellular recording more realistic?** More realistic
  *technically* (loose-patch/focal and nerve-cuff methods are routine in
  insects), but it measures a multi-axon field potential, cannot resolve
  one synapse among 43, and cannot measure graded subthreshold voltage at
  a defined site. It does not deliver the target observable.
- **Does optical voltage imaging avoid the access problem?** For the
  *recording* side, yes — no distal electrode at all. It introduces
  different requirements: a driver expressed in MN5 (not verified in the
  evidence base; the only GFS-circuit driver documented, OK307-GAL4, is
  expressed in GF, DLMmn, TTMmn **and** PSI and is not MN5-specific),
  indicator trafficking into the axon, and optical access to the thoracic
  nerve (demonstrated for optic-lobe axon terminals through a cuticle
  window — B2/B3/B5 — but **not** for a thoracic motor nerve in adult
  Drosophila in the evidence base).

**The Gouwens & Wilson 2009 statement, faithfully reported:** *"Electrode
recordings are impossible from these small processes"* — said of ≈200 nm
processes of Drosophila antennal-lobe neurons, in the context of assuming
SIZ spike size without being able to test it. This is a strong statement of
practical difficulty **for that preparation**; it is **not** a proof of
impossibility for MN5's unmeasured axon, and it must not be cited as one.
The correct reading: dual-patch (configuration A) has no insect
motor-axon precedent and must be considered access-blocked **until a
Drosophila motor axon is patched in situ** — a demonstration that itself
does not yet exist.

## Optical Voltage-Imaging Alternative

Could GEVIs provide local voltage at the PSI-bearing axon, simultaneous
soma voltage, a spatial voltage profile, and repeated measurements? Each
precedent tier is separated:

- **Voltage-imaging precedent (general):** GEVI two-photon imaging is a
  maturing field — ASAP1/2f/2s (Yang 2016; Chamberland 2017), ASAP3
  (Villette 2019, awake mice), JEDI-2P (Liu 2022, ~60% larger than
  ASAP2f in L2), ASAP4/ASAP5 (2023–2024), ArcLight (slower, smaller).
- **Drosophila precedent:** Mi1/Tm3/Tm1/L1/L2 soma+dendrite+axon arbors
  (Yang 2016); L2 axon terminals through a cuticle window (Chamberland
  2017; Liu 2022); T4c dendrite **and** axon terminal compartments of the
  same cell (Mishra 2023); L1/L2 axonal arbors of individual cells in
  vivo (Pang 2024/2025). Repeated measurements over >30 min with high SNR
  are documented (Chamberland 2017; Liu 2022).
- **MN5 precedent:** **NONE.** No GEVI has been expressed in or imaged in
  MN5 in any source in the evidence base.
- **Axonal targeting precedent:** L1/L2 axon terminals and arbors
  (Chamberland 2017; Liu 2022; Pang 2024/2025) — but these are optic-lobe
  arbors behind a cuticle window, not a thoracic motor nerve.
- **PSI-specific targeting precedent:** **NONE.** No PSI-specific driver is
  established in the evidence base (OK307-GAL4 is not PSI-specific), and
  no MN5-specific driver is verified in the evidence base either.

**What GEVIs could provide, honestly:** (i) local voltage at the
contact-bearing process **as ΔF/F** (relative, not absolute mV); (ii)
simultaneous soma voltage **if combined with a somatic patch** (the patch
is the only absolute reference; Yang 2016 did not patch, and Mishra 2023
compared ArcLight to T4 whole-cell patches from a *different* set of cells,
not simultaneously); (iii) a spatial voltage profile along the process —
the exact observable that Yang 2016 used to *constrain* (not measure)
passive parameters in Mi1; (iv) repeated measurements (documented in L1/L2
for >30 min).

**Do not assume an indicator's performance in another neuron applies
quantitatively to MN5.** Mi1 is ~50 µm long with ≤200 nm processes; the
MN5 process to the contacts is ~170–270 µm (root-referenced) with a
soma-region radius of ~4.7–5.4 µm. The larger MN5 processes plausibly
favor imaging SNR, but expression level, trafficking, membrane environment,
photobleach over a longer arbor, and the unverified driver are all
unquantified for MN5. Every GEVI number cited here (amplitude, kinetics,
photostability) is from another cell type and is **not** transferred to
MN5.

## PSI-Specific Stimulation

How could PSI activation be distinguished from other presynaptic neurons,
electrical coupling, polysynaptic effects, network activity, and
muscle/peripheral feedback?

- **GF stimulation ≠ PSI activation.** Fayyazuddin 2006 stimulated the
  **giant fiber**; PSI was then driven through the GF→PSI *electrical*
  synapse, so the recorded MN5 response was not PSI-specific. GF
  stimulation additionally drives GF→TTMn directly and recruits the whole
  escape pathway. Any design must stimulate PSI **directly**.
- **Direct PSI activation.** Focal electrical stimulation at the PSI
  soma/process (PSI somata are in the thorax and accessible), or
  optogenetic activation — but a PSI-specific driver is **not established**
  in the evidence base (OK307-GAL4 is expressed in GF, DLMmn, TTMmn and
  PSI), so optogenetic PSI isolation is currently undemonstrated.
- **Latency separation.** The GF→PSI→MN5 pathway latency is 1.3–1.7 ms
  (WT, a *pathway* latency, not an isolated synapse latency). Direct PSI
  stimulation should shorten the latency relative to GF stimulation; a
  latency distinct from both GF-driven and polysynaptic recruitment is a
  necessary control.
- **Polysynaptic exclusion.** MN5 receives input from **887/897 distinct
  presynaptic bodies**; PSI contributes only 17/10,529 (0.16%) and
  26/11,260 (0.23%) of MN5's postsynapses, while the largest single
  partner contributes 149/168 synapses — roughly 7–10× more than PSI. Any
  non-specific stimulation will be swamped. Network recruitment (MN5 itself
  drives the flight path) must be excluded by stimulus isolation and
  pharmacological controls, not assumed.
- **Electrical-coupling exclusion.** PSI→MN5 is chemical (acetylcholine;
  conditional *cha* mutations), but PSI participates in the GFS gap-junction
  network (GF→PSI is electrical, heterotypic ShakB). Coupled contributions
  from the network must be controlled; the measured MN5 response to direct
  PSI stimulation is the chemical component plus any recruited coupling.
- **Muscle/peripheral feedback exclusion.** The DLM is the effector; in a
  reduced preparation the muscle should not contract (or the recording
  window must precede feedback). The standard GFS output recording is at
  the DLM itself — a different measurement site from MN5.
- **Pharmacological isolation (proposal).** Cholinergic antagonism would
  abolish the chemical component; labelled a proposal, not a published
  standard for this synapse.

## Minimum Gate-Opening Experiment

The smallest experiment that could genuinely resolve **B-4** — i.e. that
directly observes voltage at a non-somatic site on the PSI-contact-bearing
MN5 process during a controlled perturbation, referenced to the soma.

- **Recording:** somatic whole-cell patch on MN5 (established: Fayyazuddin
  2006 in-situ thorax, Texas-red backfill) **plus** a GEVI (ASAP2f-class)
  expressed in MN5, imaged at ≥2 sites along the PSI-contact-bearing
  process (two-photon; random-access if available). *The dual-patch version
  (soma + distal electrode) is the scientifically direct form but is
  access-blocked (§Access).*
- **Stimulation:** direct, focal PSI activation (electrical at the PSI
  soma/process, or optogenetic if a PSI-specific driver is established),
  with the controls of §PSI-Specific Stimulation.
- **Measured quantity:** ΔF/F(t) at the process sites and Vm(t) at the
  soma, time-locked to the same events; the primary endpoint is the
  experimentally defined ratio ΔF/F_process / ΔF/F_soma (equal to
  ΔV_process/ΔV_soma if the indicator response is linear and site-independent),
  and secondarily the decay of ΔF/F with path distance from the input site.
- **Controls:** driver/indicator expression verification in MN5; latency
  separation from GF-driven and polysynaptic responses; polysynaptic and
  network-recruitment exclusion; no muscle feedback in the window; response
  absent when stimulation is moved off PSI; indicator response verified
  against the somatic patch in the same cell (calibration check).
- **Primary endpoint:** a non-zero, reproducible, sign-consistent
  ΔF/F_process / ΔF/F_soma ratio, with a distance-dependent decay along
  the process.
- **Acceptance criteria** — **PROPOSED EXPERIMENTAL CRITERION** (no
  published standard exists for MN5; these are proposals, not standards):
  1. the optically recorded event is time-locked to direct PSI stimulation
     with a latency consistent with monosynaptic activation and distinct
     from GF-driven and polysynaptic latencies;
  2. the response is abolished by cholinergic antagonism;
  3. the ratio is reproducible across cells (proposed n ≥ 5) with
     consistent sign;
  4. ΔF/F amplitude decays monotonically with path distance from the input
     site;
  5. the somatic patch and the optical signal at the soma agree in timing
     and sign (calibration check).
- **Major confounds:** indicator linearity/trafficking/expression gradient;
  photobleach; the measured transfer is **actual** (passive + active), not
  purely passive — MN5's A-type K⁺ and Ca²⁺ conductances will contribute;
  inability to attribute the measurement to a specific EM contact without
  the missing EM→in-vivo registration; possible contamination from other
  MN5 partners if stimulation is not PSI-specific; muscle feedback.
- **What it establishes:** **B-4 resolved** — the first direct observation
  of non-somatic voltage on the PSI-contact-bearing MN5 process during
  synaptic activation, referenced to the soma; an empirical transfer ratio
  (and profile) for the measured path, superseding any modelled attenuation
  for that path.
- **What remains unresolved:** Ra and Rm *separately* (need ≥3 sites +
  geometry); Cm (B-3, unrelated observable); the anatomical
  contact→soma path to a labelled soma (B-5) and the EM→in-vivo
  registration; PSI synaptic conductance and E_rev (B-6); Dα7 conductance
  (gate 2); the passive vs active decomposition.

## Stronger Experiment

The stronger design adds, **as separate measurements** (not pretended to be
simultaneous at one site):

1. **≥3 optical sites along the process** (random-access multi-photon, the
   Chamberland 2017 method) during direct PSI activation. Three or more
   sites give the *shape* of the decay, which — with known geometry —
   begins to constrain the Ra·Rm combination and, in principle, separates
   them (the ≥3-location statement). This is what Yang 2016 did for Mi1
   (constraining Ri 40–420 Ω·cm and Rm 1–21 kΩ·cm²), and it constrains
   rather than measures.
2. **A somatic reversal series at PSI→MN5** (the previous audit's design
   X-03): bounds the synaptic source (apparent somatic E_rev, voltage
   dependence) — partially resolving B-6 — so the input is bounded before
   propagation is measured.
3. **Dα7 null + synapse-restricted rescue** (X-04), *after* (2), to
   isolate the receptor-specific component of the conductance.
4. **If access is ever demonstrated:** the dual-patch at the contact
   (configuration A) — the gold standard that measures the ratio in
   absolute mV at both ends.

**Why it is stronger:** it measures the transfer ratio, bounds the synaptic
input, and begins parameter separation, each on its own terms. It is also
honest about limits: (1) constrains a parameter *set* (with geometry and a
model fit), not two-site identification; (2) bounds rather than measures
the local synaptic reversal; (3) the Dα7 component requires the total
conductance first; (4) none of the four components has been demonstrated
in MN5. It does **not** pretend to measure everything at once.

## What the Experiment Would Actually Identify

If the minimum experiment (or its stronger variant) succeeded:

| Claim | Allowed? | Direct observable / remaining confound |
|---|---|---|
| direct spatial transfer ratio | **YES** | the ratio ΔV_distal/ΔV_soma (electrical) or ΔF/F ratio (optical, linear-indicator assumption) for the same cell and event |
| local PSI-contact voltage | **YES** — absolute mV with a distal patch; relative ΔF/F with imaging (absolute only via calibration) | electrode shunt (patch) or indicator linearity/calibration (optical) |
| cable model | **PARTIALLY** | the measured ratio/profile *constrains* a cable model for the measured path; a full cable model still needs Ra, Rm, Cm and geometry |
| Ra | **NO** | two sites constrain only the Ra·Rm combination; separate identification needs ≥3 known locations + known geometry |
| Rm | **NO** | same |
| Cm | **NO** | not a transfer observable; the 43 vs 127 pF conflict (C-01) is untouched |
| PSI synaptic conductance | **NO** | needs a reversal series or local clamp (B-6); inseparable from attenuation at one site |
| PSI E_rev | **NO** | needs a multi-point reversal series; a somatic series yields only the *apparent* somatic value |
| Dα7 conductance | **NO** | needs total conductance first, then Dα7-specific isolation; no native Dα7 conductance exists |

## What It Would NOT Identify

- **Ra, Rm, Cm individually** — the identifiability limit above; this is
  the most likely over-claim and must be resisted.
- **The passive (as opposed to actual) transfer** — MN5's subthreshold-active
  conductances mean the measured ratio includes active spread; decomposing
  it needs pharmacological manipulation, not more sites.
- **The synaptic source** (conductance, E_rev, kinetics) — a different
  observable family (B-6), measured by a reversal series, not by a
  transfer measurement.
- **A specific one of the 43 EM contacts** — without the missing EM→in-vivo
  registration, the measurement is referenced to the input site and the
  labelled process, not to an EM coordinate.
- **The anatomical contact→soma path** (B-5) — unchanged; the voltage ratio
  bypasses the path (it measures two points directly) but the anatomical
  blocker persists for any path-based modeling, and *targeting* a specific
  contact requires the registration.
- **Anything about Dα7** — gate 2 is independent and untouched.

## Impact on B-1 through B-6

| Blocker | Impact of a successful dual-site/optical measurement | Reasoning |
|---|---|---|
| B-1 Rm unmeasured/unboundable | **UNCHANGED** (joint constraint only) | two sites constrain Ra·Rm jointly; separate Rm needs ≥3 sites + geometry |
| B-2 Ra unmeasured | **UNCHANGED** (joint constraint only) | same |
| B-3 Cm conflict 43 vs 127 pF | **UNCHANGED** | Cm is not a transfer observable; a voltage ratio cannot adjudicate the conflict |
| B-4 no non-somatic/dual-site voltage | **RESOLVED** — this is the point of the experiment | a second measurement site on the PSI-contact-bearing process is exactly the missing observable |
| B-5 contact→soma path to a labelled soma | **UNCHANGED** | the ratio does not need the path, but the anatomical gap persists; targeting a specific contact needs the missing registration |
| B-6 PSI synaptic conductance/reversal | **UNCHANGED** | needs a reversal series (partially resolvable separately) or a local clamp |

**Do not assume solving B-4 solves B-1/B-2/B-3/B-6.** The measurement is
one observable; the blockers are five.

## Gate Consequences

- **PSI→MN5 spatial voltage transfer: NOT AUTHORIZED.** This audit performs
  no experiment and measures nothing. The gate would open only on a real,
  successful dual-site or calibrated optical measurement — a future outcome,
  not a present claim. Until then, any transfer statement would still be
  speculative.
- **Dα7 biological conductance: NOT AUTHORIZED.** Nothing in this audit
  touches the receptor; no native Dα7 conductance exists in the evidence
  base.
- No biological constant was changed, no synthetic data created, no code
  modified, no contested conflict silently resolved (C-01 remains open), and
  no existing gate opened.

## Evidence vs Inference vs Proposal

**(i) Direct evidence — Drosophila, MN5:** 43 contacts with
`compartment_post = axon` in the PDMN region; 887/897 distinct
presynaptic bodies (PSI a 0.16–0.23% minority input); one somatic EPSP at
one holding potential with the GF stimulated; Rin, V_rest, threshold, AP
amplitude/width; A-type K⁺ and Ca²⁺ current voltage dependence; the
in-situ somatic patch preparation (Fayyazuddin 2006).

**(ii) Direct evidence — other preparations (methodological precedent
only):** subcellular GEVI imaging in Drosophila visual neurons (Yang 2016;
Chamberland 2017; Liu 2022; Mishra 2023; Pang 2024/2025); single-site
axonal intracellular recording in a blowfly (C1); simultaneous soma+axon /
soma+dendrite patch in vertebrates (D1–D4); voltage-calibrated optical
recording of axonal Vm with a patch reference in vertebrates (D5–D7); the
electrode-access constraint for small insect processes (B6).

**(iii) Inference (not measurement):** that the `kind=2` proximal dilation
is the soma; that SWC `kind=2` is axon; that the contact→soma-proxy path
is the biological route; that an indicator's performance in Mi1/L1/L2/T4
transfers quantitatively to MN5; that a linear, site-independent GEVI
response holds in MN5.

**(iv) Proposal (this document):** configurations A–E, the minimum and
stronger experiments, their controls, confounds, and acceptance criteria.
**Nothing in (iv) has been performed.**

## Recommended Next Step

Ranked:

1. **Verify whether an MN5-specific driver exists** (a literature and
   stock-center check — not an experiment). This is the prerequisite for
   *any* optical configuration; the evidence base contains none. If none
   exists, the optical design is blocked at the driver step, and the
   cheapest high-value experiment remains the somatic reversal series
   (X-03), which bounds the synaptic source (B-6) on an established
   preparation.
2. **The minimum optical experiment (C/E)** — somatic patch + GEVI along
   the PSI-contact-bearing process during direct PSI activation — if and
   only if (1) yields a driver. It resolves B-4 and delivers the empirical
   transfer ratio/profile.
3. **In parallel, the somatic reversal series (X-03)** — cheapest,
   feasible today, partially resolves B-6, and bounds the input before
   propagation is measured.
4. **Dual-patch (A) remains the gold standard** but is access-blocked
   pending a first demonstration of in-situ patch-clamp of a Drosophila
   motor axon — a demonstration that does not yet exist in any source.

## Provenance

| Statement | Class |
|---|---|
| 43 contacts, `compartment_post = axon`, PDMN region, 887/897 partners, PSI 0.16–0.23% share | `anatomical_measurement` |
| contact→root / straight-line / proxy distances | `anatomical_measurement` / `model_derived_estimate` (geometry only) |
| "the proximal dilation is the soma" | `model_assumption` |
| MN5 Rin, V_rest, V_th, AP amplitude/width, A-type K⁺ and Ca²⁺ voltage dependence | `native_experimental_measurement` |
| somatic EPSP 4.71 mV at −74 mV, GF stimulated | `native_experimental_measurement` (PSI not directly stimulated) |
| MN5 Cm 43 / 127 pF | `native_experimental_measurement`, **contested (C-01)** |
| MN5 axon diameter | **NONE — unmeasured** |
| receptor identity Dα7 | `model_assumption` (genetic inference) |
| Yang 2016 decay profile and Ri/Rm bounds | `native_experimental_measurement` (**different neurons**) |
| Chamberland 2017 / Liu 2022 / Mishra 2023 / Pang 2024 GEVI results | `native_experimental_measurement` (**different neurons**) |
| Gouwens & Wilson 2009 access statement | `native_experimental_measurement` (their preparation) |
| vertebrate dual-site precedents (D1–D7) | `native_experimental_measurement` (**different species**) |
| Ryglewski & Duch 2009 Fig 1B transfer map | `model_derived_estimate` on adopted inputs |
| the identifiability analysis, configurations A–E, and both experiment designs | **proposal**, not measurement |
| ΔV_distal/ΔV_soma for MN5 | **NO VALUE EXISTS** |

**Final gate status, restated verbatim:**

- **PSI→MN5 spatial voltage transfer: NOT AUTHORIZED**
- **Dα7 biological conductance: NOT AUTHORIZED**
