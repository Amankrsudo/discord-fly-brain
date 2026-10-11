# Dα7 Evidence Map

**Key question:** *Is there any primary experiment that independently measures
native PSI→MN5 Dα7 synaptic conductance?*

## ANSWER: NO.

Established by searching PubMed, PMC, Google Scholar, FlyBase (+ Gene Reports and
Reference Reports), ModelDB, janelia.org (MANC), male-cns.janelia.org,
elifesciences.org, flywire.ai, Virtual Fly Brain.

Queries: `PSI MN5 Drosophila synapse Giant Fiber escape pathway
electrophysiology`; `Male CNS connectome PSI MN5 synapse number`; `MN5 OR DLM
motor neuron Drosophila synapse number connectome PSI MANC`; `PSI DLMmn current
voltage clamp`; `Drosophila alpha7 nicotinic acetylcholine receptor MN5 DLMn motor
neuron`; `Dalpha7 Drosophila acetylcholine EC50`; `methyllycaconitine Drosophila
alpha7`; `Drosophila alpha7 nAChR single channel conductance native neuron patch
clamp desensitization`; `Dalpha7 calcium permeability heterologous S2 Xenopus`;
`alpha7 nicotinic receptor coupling Kir7.1 inward rectifier`; `Drosophila Kcnj13
Irk Kir7.1 homolog`; `Drosophila alpha7 Kir7.1 coupling`; `Kir7.1 KCNJ13
Drosophila`.

Full texts read: Fayyazuddin+ 2006 (complete), Kadas+ 2012 (PMC6621333),
Korona+ 2022 (PMC9110030), Gaitanidis+ 2025, ModelDB 245415.

---

## Established experimentally in native Drosophila

| Finding | Value | Source |
|---|---|---|
| MN5 somatic synaptic-potential amplitude, WT | **4.71 ± 0.35 mV (SEM, n=10)** at **−74 mV**, current clamp | Fayyazuddin+ 2006 *PLoS Biol* 4(3):e63 |
| Same, *gfA*¹ (Dα7 K46E) | **1.5 ± 0.32 mV (SEM, n=7)**, p = 1×10⁻⁵ | same |
| MN5 somatic capacitance | 43 ± 2 pF (n=22) | same |
| MN5 somatic input resistance | 102 ± 12 MΩ (n=22) | same |
| Visually-mediated jump, Dα7 nulls | abolished in all four alleles, p = 1.9×10⁻⁶ | same |
| Flight / olfactory trap / ERG / phototaxis | **no** significant deficit | same |
| Dα7 null viability | viable, fertile, **little/no locomotor deficit** (10-d climbing, n=3) | Korona+ 2022 *eLife* 11:e74322 |
| α-bungarotoxin resistance conferred by α5/α6/α7 | larval survival 0 % → **72 ± 25 %**, p = 0.0001, n=10 | same |
| α-Btx **binds Dα7 in native adult fly tissue** | Dα7 LBD glycopeptide **NNGSCLYVPPGIFK**, HexNAc-modified **Asn170**, MS, n=3 | same |
| ω-Hexatoxin-Hv1a lethality | **not** conferred by α7 | same |

**Critical measurement caveat on the 4.71 mV figure.** The stimulus was
**electrical activation of the giant fiber through eye electrodes** (or a neck
suction electrode) — **PSI was never directly stimulated.** The recorded quantity
is *"the mean amplitude of the synaptic potential underlying the spike measured
at the soma"* — a **filtered somatic voltage**, not a synaptic-site voltage.
Authors state the peripheral AP *"fails to propagate antidromically into the
dendrite and therefore is filtered by the passive membrane properties."*
Age, sex and temperature for these recordings: **not reported**.

---

## Established anatomically

- **Dα7 immunostaining in native Drosophila** (Fayyazuddin 2006): antibody raised
  **in rat** against a *Drosophila* M3–M4 cytoplasmic-loop fusion protein. Staining
  is "**10–100× stronger**" near the **GF dendrites** than anywhere else; strongest
  colocalisation with **VLD and PLD**; **DMD not labelled**. Punctate pattern on
  GFP-labelled dendrites. Rescued to background in the null *PΔEY6*.
  **Author's own specificity caveat:** some lamina synapses stain even in the null,
  so "the antibody also recognizes another epitope."
- **⚠ PSI axon terminals: NOT REPORTED.** No Dα7 immunostaining of PSI terminals
  exists in any primary source located.
- **⚠ MN5 / DLMn dendrites: NOT REPORTED.** No Dα7 immunostaining of the MN5 or
  DLMn arborisation exists. In the only in vivo MN5 study, the **reporter** (not
  the protein) was imaged.
- **Dα7-GAL4 (P-element enhancer trap)** labels MN5 and the other DLM motoneurons
  — but this is **regulatory-reporter evidence, not protein**. "Presence of a GAL4
  insertion at the locus is not evidence of endogenous Dα7 protein in those cells."
  There is **no** equivalent of Korona's 2022 fluorescent endogenous tagging for Dα6
  (*eLife* 11:e74322).
- All later anti-Dα7 work (Kadas 2012, Gaitanidis 2025) is **restricted to the GF
  visual dendrite** — a different synapse.

---

## Established genetically

- ***gfA*¹ identified as a Dα7 allele** — non-complementation with *PΔD5*/*PΔEY6*;
  dominant/antimorphic; molecular lesion **K46E** in loop 2 of the ligand-binding domain.
- Allele series: WT = *PΔL1* = *PΔEY5* > *PΔ14G* > *PΔ41* > *PΔD5* = *PΔEY6*.
- **Rescues (Fayyazuddin 2006):**
  - `UAS-Dα7` under **OK307-GAL4** rescues GF-driven DLM activation in *PΔD5* (n=4)
    and *PΔEY6* (n=5). **Caveat stated by the authors:** OK307 is expressed in
    *"several elements of the giant fiber circuit (including the giant fiber, DLMmn,
    TTMmn and PSI)"* — **the rescue does not localise the rescuing Dα7 to MN5.**
  - `UAS-Dα7` under **c17-GAL4** (GF-specific) rescues the long-latency response
    (*PΔD5* 2/2; *PΔEY6* 3/3). **This is the spatially restricted rescue**, and it
    is why the authors assign the jump phenotype to Dα7 loss **in the GF**, not at
    PSI→MN5.

---

## Established ONLY in heterologous systems

| Property | System | Source | Comment |
|---|---|---|---|
| Homooligomeric channel, rapid desensitisation, strong rectification above −20 mV, α-Btx-sensitive | **chick** α7 in *Xenopus* oocytes | Couturier+ 1990 *Neuron* 5:847, PMID 1702646 | **Chick, not fly** |
| α-Btx binding-site formation by *Drosophila* α6/α7 chimeras | **S2 cells** | Lansdell & Millar 2004 *J Neurochem* 90:479 | Full text **not retrieved** — do not quote numbers |
| Dα5/Dα7 homomeric & heteromeric functional channels | *Xenopus* oocytes co-expressing CeRIC-3; cultured Drosophila/human cells for binding assays | Lansdell+ 2012 *BMC Neurosci* 13:73 | Primary full text and Table 2 verified via Springer; recombinant-channel results only. |

Lansdell et al. report for recombinant homomeric Dα7 in *Xenopus* oocytes:
EC50 6.7 ± 1.7 µM ACh, Hill slope 1.0 ± 0.3, n=4 dose-response fits,
maximum current detected 86 nA and mean maximum current 45 ± 13 nA. The
oocyte membrane was voltage-clamped at −60 mV. Functional responses were
inconsistent across batches even with RIC-3 (responses >5 nA in about one
third of batches). These are heterologous channel-level results; they do not
measure native MN5 conductance, channel number/density, kinetics at PSI→MN5,
or a synaptic reversal potential. The current values are not converted into a
native conductance.
| Mean open time 0.32 ms, amplitude −4.0 pA at −70 mV | **rat** α7 in rat hippocampal neurons | PMC4007412 | **Rat.** Not insect. |

---

## Model assumptions (NOT measurements)

- *"Dα5, Dα6 and Dα7 … can form homomeric channels … have high permeability to
  calcium, and desensitize rapidly"* — **Grauso, Reenan, Culetto & Sattelle 2002
  *Genetics* 160:1519**, cited in Fayyazuddin 2006. **This is an inference from
  homology to vertebrate α7, stated as background.** No fly measurement.
- Receptor identity at PSI→MN5 itself: *"the PSI-DLMmn synapse, which was
  previously suggested to be cholinergic, is mediated by the Dα7 nAChR"* —
  **inferred from allele strength correlating with EPSP amplitude**, plus one point
  mutant. **Not** direct receptor identification.
- Presynaptic vs postsynaptic location at PSI→MN5: **neither demonstrated by
  imaging.** Presynaptic in nature (PSI is presynaptic), postsynaptic in location
  — by inference only.
- 0.5 ms monosynaptic latency, used by Gaitanidis 2025 to convert pathway hops to
  time: an explicit **assumption** ("if we assume a 0.5 ms latency").

---

## ⚠ Dα7 → Kir7.1 coupling is NOT ESTABLISHED IN DROSOPHILA

The vertebrate Dα7/α7-to-Kir7.1 coupling mechanism must not be assumed to
operate in the fly. The available evidence reviewed here does not establish a
functionally equivalent coupling mechanism in *Drosophila*.

- *Drosophila* has three named inward-rectifier genes: **Irk1, Irk2, Irk3**
  (FlyBase FBgn group FBgg0000509; *Irk3* = CG10369, FBgn0032706).
- Do not state categorically that *Drosophila* has no Kir7.1/KCNJ13 orthologue
  without a current, authoritative orthology record that resolves low-scoring
  candidates. The evidence reviewed here supports **absence of an established
  functional equivalent**, not proof that no orthologue exists.
- No coupling of an insect nAChR to an Irk channel was identified in the sources
  reviewed for this evidence map.
- Irk functions in fly neurons are documented here in non-cholinergic contexts
  (for example, Dpp release in wing development — Dahal+ 2017 *Development*
  144:2771); that does not by itself exclude other functions.

**Modeling implication:** do not build a Dα7→Kir7.1-like coupling pathway into
MN5 without direct fly-specific evidence. This is a constraint on unsupported
mechanistic assumptions, not a claim that orthology is definitively absent.

---

## UNKNOWN — explicit list

Native Dα7 single-channel conductance · open probability · reversal potential ·
activation and desensitisation kinetics · Ca²⁺ permeability · density at PSI→MN5 ·
subsynaptic clustering · direct imaging at PSI terminals or MN5 axons ·
PSI→MN5 quantal size / quantal content / release probability / release-site number ·
EPSP latency, rise time, decay constant · synaptic conductance · synaptic delay ·
any direct measurement of PSI→MN5 receptor identity by imaging or binding.

---

## NO QUALIFYING MEASUREMENT FOUND — PSI→MN5 synapse parameters

| Parameter | Status |
|---|---|
| EPSP latency | **NO QUALIFYING MEASUREMENT FOUND.** Fayyazuddin 2006 explicitly *rejected* a kinetics explanation: in *gfA*¹ *"the EPSP followed without failure and did not show significant changes in shape or jitter."* No kinetics quantified. |
| EPSP rise time / decay τ | **NO QUALIFYING MEASUREMENT FOUND** |
| Reversal potential | **NO QUALIFYING MEASUREMENT FOUND.** Current clamp only, single point (−74 mV). No I–V. |
| Synaptic / peak conductance | **NO QUALIFYING MEASUREMENT FOUND.** Nothing in the literature derives, estimates or names one. |
| Quantal size / content / release probability | **NO QUALIFYING MEASUREMENT FOUND.** No mEPSP, no failure analysis. |
| Active zones / release sites | **NO QUALIFYING MEASUREMENT FOUND.** No T-bar count at PSI→MN5. |
| Short-term plasticity | **NO QUALIFYING MEASUREMENT FOUND** at the synapse. Kadas 2012's CaMKII-T287D raises GF–DLM RP from ~4 ms to ~10–12 ms — a **pathway-fidelity** effect assigned postsynaptically by driver logic, with the authors' own caveats (*cha*-GAL4 PSI expression "assumed", "data not shown"). |
| Receptor density | **NO QUALIFYING MEASUREMENT FOUND.** No quantitative immunostaining, no α-Btx binding density at this synapse. |
| Synaptic delay | **NOT MEASURED.** The ~0.5 ms in Gaitanidis 2025 is an explicit assumption, derived from a TTM→DLM *muscle* offset, not an isolated synaptic delay. |

### Synapse-count conflict

| Source | Count | Caveat |
|---|---|---|
| **MaleCNS v1.0, minconf 0.5** (this project's 43) | 17 + 26 = **43** | **Could not be matched to any publication.** Verified only as a neuPrint query result. |
| MANC (Gaitanidis+ 2025 *PLoS Biol* 23:e3003553, Fig 4C–D) | **~1,000** PSI output synapses onto **all five** DLM motoneurons, along the **axons** | No per-pair breakdown, **no confidence threshold**, **n = 1 male specimen**. Not MN5-specific. |
| MANC, same source Fig 4E | **~600** GFC2 input synapses onto DLM MN axons | Same caveats |
| King & Wyman 1980 / Fayyazuddin 2006 | qualitative only — "multiple synaptic contacts that span 50 μm" | no count |

**Not a contradiction — a dataset artefact.** MANC explicitly annotates PSI among
48 neurons manually reviewed as electrical-transmission cells (Marin+ 2024
*eLife* RP 97766), so automated chemical-synapse counts **undercount** PSI output.
VFB documentation explicitly warns against summing partner counts across datasets
reconstructing the same tissue. The 43 figure is a **minconf-0.5 filter on
MaleCNS**, and must always be quoted with that threshold.

### Transmitter / receptor

- **Transmitter: acetylcholine** — Gorczyca & Hall 1984 *J Neurogenet* 1:289,
  conditional *cha* (ChAT) mutations. *Secondary citation only; full text not
  retrieved.*
- **Receptor: Dα7 nAChR** — Fayyazuddin 2006, **genetic inference** (allele
  strength vs EPSP amplitude). Not direct.

---

## Gate statement

**PSI→MN5 spatial voltage transfer: NOT AUTHORIZED**
**Dα7 conductance: NOT AUTHORIZED**

Nothing in this branch produced qualifying primary evidence. The nearest
quantities are a filtered somatic current-clamp voltage at one holding potential,
and a genetic inference of receptor identity.
