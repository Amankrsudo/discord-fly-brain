# Model Input Freeze — PSI→MN5 / Dα7

**GENERATED FILE.** Do not edit by hand. Regenerate with:
`python research/scripts/build_model_input_freeze.py`

Source of truth: `research/model_input_freeze.csv` (108 parameters).
Machine-readable. Provenance vocabulary is exactly the project's five classes.

**PSI→MN5 spatial voltage transfer: NOT AUTHORIZED**
**Dα7 conductance: NOT AUTHORIZED**

## Counts

| bucket | n |
| --- | --- |
| total parameters audited | **108** |
| **A · SAFE TO USE NOW** | **40** |
| **B · USABLE ONLY AS EXPLICIT MODEL ASSUMPTIONS** | **31** |
| **C · BLOCKED / DO NOT USE** | **37** |
| unresolved conflicts preserved | **15** |

Convention: rows with value `NONE` are provenance-classified `model_assumption`
because any value for them would be a pure invention, and are always blocked.
Exactly one of `safe_now` / `assumption_only` / `blocked` is `yes` per row, and
B is never silently promoted into A.

## Unresolved conflicts preserved

- C-01 unresolved (~2.95x)
- C-02
- C-02 1000x vs executed
- C-03
- C-03 1000x
- C-03 family
- C-06
- C-07 not a conflict
- C-08 semantics undefined
- C-09 premise corrected
- C-10
- C-10 species mismatch
- C-11
- C-11 corrected
- C-12

## A · SAFE TO USE NOW (40)

Measured with adequate provenance in the right biological object.

| parameter | value | unit | provenance | strength | gate | notes |
| --- | --- | --- | --- | --- | --- | --- |
| MN5 input resistance (set 1) | 102 +/- 12 (n=22) | Mohm | native_experimental_measurement | moderate | none | Genuine native measurement in the right cell. Usable as a measured constraint on a passive model. |
| MN5 input resistance (set 2) | 97 +/- 31 (n=52) | Mohm | native_experimental_measurement | moderate | none | Second independent set; broader n. Consistent with set 1. |
| MN5 resting potential | -67.8 +/- 5.5 SD (n=13) | mV | native_experimental_measurement | moderate | none | Zero holding current after break-in. Strongest MN5 record. |
| MN5 spike threshold | -24.1 +/- 8.2 SD (n=11) | mV | native_experimental_measurement | moderate | none | Steepest slope at AP onset. |
| MN5 action potential amplitude | 45.5 +/- 8.6 SD (n=13) | mV | native_experimental_measurement | moderate | none |  |
| MN5 action potential time to peak | 1.20 +/- 0.33 (n=13) | ms | native_experimental_measurement | moderate | none | Somatic. Relevant to how much of an AP reaches the contact. |
| MN5 action potential 50% width | 0.92 +/- 0.25 (n=13) | ms | native_experimental_measurement | moderate | none | Somatic. |
| MN5 transient A-type K+ activation Vhalf | -12.1 +/- 1.4 | mV | native_experimental_measurement | moderate | none | 24 C. Authors caveat: not all A-type channels fully activated. |
| MN5 transient A-type K+ inactivation Vhalf | -40.02 +/- 0.33 | mV | native_experimental_measurement | moderate | none | 24 C. |
| MN5 Ca-dependent transient A-type activation Vhalf | -22.34 +/- 2.02 | mV | native_experimental_measurement | moderate | none | 24 C. |
| MN5 Ca-dependent transient A-type inactivation Vhalf | -49.33 +/- 0.24 | mV | native_experimental_measurement | moderate | none | 24 C. |
| MN5 transient Ca2+ current time to peak | 0.76 +/- 0.16 | ms | native_experimental_measurement | moderate | none | Abolished by 500 uM Cd2+. |
| MN5 Shaker localisation | predominantly axonal | categorical | anatomical_measurement | moderate | none | Soma and primary neurite lack VGSC label. Anatomical, not electrical. |
| MN5 surface area (EM mesh) | 18725.6 (801970) / 19665.4 (801295) | um2 | anatomical_measurement | strong | none | Cross product, Heron-validated to 2e-16 relative. Usable model geometry. |
| MN5 surface area (SWC frustum approximation) | 24803.7 / 25796.8 | um2 | model_derived_estimate | moderate | none | Truncated-cone lateral area of a 1-D skeleton. ~24% LARGER than the mesh because it is a different domain. Not interchangeable with A_mesh. |
| MN5 dendritic length (literature) | ~6 mm | um | anatomical_measurement | moderate | none | n=11 females, 1 day AEL, 25 C. Exact value is in Fig 1E (an image). |
| MN5 dendritic branch count | nearly 4000 | count | anatomical_measurement | moderate | none |  |
| MN5 mean dendritic diameter | ~0.44 | um | anatomical_measurement | moderate | none | Literature text says 0.44 um. An earlier project note of 0.88 um is NOT supported. |
| MN5 total cable length (SWC) | 7453.5 / 7190.2 | um | anatomical_measurement | strong | none | Total, not dendritic. |
| MN5 soma-region proxy radius | 4.671 (801970) / 5.376 (801295) | um | anatomical_measurement | strong | none | Soma-SIZED dilation 1.45-2.10 um from somaLocation. The measurement is anatomical; calling it the soma is a separate assumption. |
| MN5 somaLocation annotation | (56099,46256,81781) / (43450,45480,81574) | raw 8nm | anatomical_measurement | strong | none | A POINT annotation, not a surface. tosomaLocation and rootSide columns exist but are unpopulated. |
| PSI->MN5 contact count | 17 + 26 = 43 (minconf 0.5) | count | anatomical_measurement | strong | none | Corroborated independently by the annotation layer (17 and 26). ALWAYS quote the minconf threshold. |
| PSI->MN5 official compartment_post | axon x43 | enum | anatomical_measurement | strong | none | Official enum string. A LABEL, not a distance and not a voltage. Dataset annotation, NOT an electrophysiological measurement. |
| PSI->MN5 official compartment_pre | axon x38 / unknown x5 | enum | anatomical_measurement | strong | none | All 5 unknown values are on body 801295. Preserved, not imputed. |
| PSI->MN5 contact coordinates | 43 triples | raw 8nm | anatomical_measurement | strong | none | Exact integer match to the annotation layer; a non-unique match raises. |
| PSI->MN5 contact -> mesh surface distance | 1.67-80.22 (min-max over 43) | nm | anatomical_measurement | strong | none | Nearest surface TRIANGLE point; vertex distance tracked separately and never substituted. |
| PSI->MN5 contact -> SWC-root path length | 169.2-267.8 | um | model_derived_estimate | strong | none | GEOMETRIC path only. Root is the stalk origin, NOT the soma. NOT an electrotonic distance. |
| PSI->MN5 contact -> somaLocation straight line | 110.3-172.9 | um | anatomical_measurement | strong | none | A straight line is NOT a path length. |
| PSI->MN5 transmitter identity | acetylcholine | categorical | anatomical_measurement | moderate | none | Conditional *cha* mutations. Secondary citation; full text not retrieved. |
| Dalpha7 localisation at GF dendrites | 10-100x stronger than elsewhere | dimensionless | anatomical_measurement | moderate | none | Usable, but for a DIFFERENT synapse. Author caveat: the antibody also recognises another lamina epitope. |
| Dalpha7 native alpha-bungarotoxin binding | glycopeptide NNGSCLYVPPGIFK, Asn170 | categorical | anatomical_measurement | strong | none | Mass spectrometry on native tissue. Proves Dalpha7 protein exists and binds alpha-Btx; says nothing about its density at a synapse. |
| Dalpha7 mutant jump phenotype | abolished (4 alleles) | categorical | anatomical_measurement | moderate | none | Flight, trap, ERG and phototaxis were NORMAL. |
| MN1-MN2 / MN3-MN4 coupling coefficient | 0.023 +/- 0.003 SEM (6 pairs) | dimensionless | native_experimental_measurement | strong | none | Real, but NOT MN1->MN5 and not the GFS. |
| other MN1-4 coupling coefficient | 0.01 +/- 0.0027 SEM (10 pairs) | dimensionless | native_experimental_measurement | strong | none | Real, but not MN1->MN5. |
| ShakB identity | inx8 (an innexin, NOT Kv1) | categorical | anatomical_measurement | strong | none | Corrects a Kv1 conflation. No Kv1 evidence exists at any GFS synapse. |
| ShakB isoform asymmetry | GF ShakB(N+16); TTMn/PSI ShakB(L) | categorical | anatomical_measurement | strong | none | Makes GF->TTMn and GF->PSI HETEROTYPIC junctions. RNA in-situ verified. |
| GF->TTMn ShakB plaque fraction | 14.72 +/- 3.99 SD (n=9) | % of GF terminal | native_experimental_measurement | strong | none | fra LOF 3.00 +/- 0.57; Netrin LOF 1.54 +/- 0.48. |
| GF->PSI age dependence of ShakB | NONE (no decline) | categorical | anatomical_measurement | strong | none | The GFS age decline is GF->TTMn-SPECIFIC. A negative result, and a useful one. |
| GF->PSI pathway latency | 1.3-1.7 (WT range) | ms | native_experimental_measurement | moderate | none | A PATHWAY latency, not an isolated synapse latency. |
| GF->TTMn pathway latency | 0.93 (young) / 1.22 (old) | ms | native_experimental_measurement | strong | none | 25 C, n=8-9 per condition. |

## B · USABLE ONLY AS EXPLICIT MODEL ASSUMPTIONS (31)

Exploratory use only. Each MUST remain labelled an assumption wherever it
appears. **Never promote a row from B to A.**

| parameter | value | unit | provenance | strength | gate | notes |
| --- | --- | --- | --- | --- | --- | --- |
| MN5 whole-cell capacitance (variant A) | 43 +/- 2 (n=22) | pF | native_experimental_measurement | moderate | none | Somatic whole-cell. Contradicted by variant B; using either requires assuming which is right. NOT compartment-specific. |
| MN5 whole-cell capacitance (variant B) | 127 +/- 16 SD (n not stated) | pF | native_experimental_measurement | moderate | none | Authors flag dendritic space-clamp as a Cm error source. Same mean and SD re-reported by Herrera-Valdez+ 2013 J Comput Neurosci 34:211; treat as ONE measurement. |
| MN5 resting potential (weak, figure caption) | -59 | mV | native_experimental_measurement | weak | none | Representative trace only: no n, no uncertainty. Prefer the -67.8 mV record. |
| MN5 axoplasmic resistivity (value ever applied) | 90 | ohm.cm | literature_derived_passive_parameter | weak | none | WRONG SPECIES. Self-described as 'values commonly applied'. Manduca MeSH-confirmed. Must remain labelled an adopted default. |
| MN5 specific membrane capacitance (adopted) | 1.15e-6 | F/cm2 | literature_derived_passive_parameter | weak | none | Wrong species; adopted by assertion, never fitted. |
| MN5 passive leak conductance density (adopted) | 0.0001667 | S/cm2 | literature_derived_passive_parameter | weak | none | Wrong species; adopted. |
| Drosophila motor-neuron axoplasmic resistivity (only measured value) | 212.47 +/- 3.69 (n=5) | ohm.cm | native_experimental_measurement | moderate | none | Only MEASURED Drosophila motor-neuron Ra. 2.4x the value adopted for MN5, which is evidence that 90 ohm.cm is not a Drosophila value. Larval aCC, not adult MN5. |
| aCC specific membrane capacitance (for contrast) | 0.77 +/- 0.02 (n=5) | uF/cm2 | native_experimental_measurement | moderate | none | Fitted passive-model parameter, wrong cell. |
| MN5 compartment split of cable | 93% kind=0 / 7% kind=2 | fraction | anatomical_measurement | strong | none | Using kind=2 as the axon is an ASSUMPTION: MaleCNS documents no assignment procedure and the official reader discards node_type. |
| MN5 soma-region proxy identification | nearest SWC node | categorical | model_assumption | none | none | The proxy node is itself kind=2. No source calls it a soma. |
| PSI->MN5 contact -> soma-proxy tree path | 154.1-241.6 | um | model_derived_estimate | moderate | none | Rests on the soma-proxy assumption. A geometric path, never a voltage. |
| MN5 SIZ distance from soma | ~100 | um | literature_derived_passive_parameter | moderate | none | Anti-VGSC IMMUNOCYTOCHEMY, not electrophysiology. Unregistered to MaleCNS: no deposit, no dendrite labels, no axis, no transform. |
| MN5 SIZ localisation from dendrite origin | 11 +/- 3 (n=7) | um | literature_derived_passive_parameter | moderate | none | Measured from the DENDRITE ORIGIN, not the soma. SD-vs-SEM unstated. The retracted '88 +/- 15 um' figure does not exist. |
| PSI->MN5 EPSP amplitude (WT) | 4.71 +/- 0.35 SEM (n=10) | mV | native_experimental_measurement | moderate | none | Current clamp at -74 mV ONLY. A FILTERED somatic voltage: the GF was stimulated, PSI never directly, and the distal amplitude is unreported. |
| PSI->MN5 EPSP amplitude (gfA1) | 1.5 +/- 0.32 SEM (n=7) | mV | native_experimental_measurement | moderate | none | Dalpha7 point mutant. Same caveats as WT. |
| PSI->MN5 synaptic delay | 0.5 (ASSUMED) | ms | model_assumption | weak | none | Explicitly assumed by that paper, derived from a TTM->DLM MUSCLE offset, not an isolated synaptic delay. NEVER measured. |
| PSI->MN5 receptor identity | Dalpha7 nAChR | categorical | model_assumption | moderate | none | GENETIC INFERENCE only: allele strength correlating with EPSP amplitude. Not directly identified. The OK307 rescue driver is NOT localised to MN5. |
| GF gap-junction conductance (paper value) | 135 (young) / 34.5 (old) | uS | model_assumption | weak | none | Explicitly '(estimated)'. Used as a free fitting parameter to reproduce measured latencies. |
| MN5->MN1 coupling | bidirectional, qualitative | categorical | anatomical_measurement | weak | none | Non-rectifying, unlike the GFS. No CC, conductance or latency. |
| GFS rectification index | 0.21 | dimensionless | native_experimental_measurement | moderate | none | Measured in XENOPUS OOCYTES. Must never be quoted as a GFS value. ModelDB's gap2 is linear and cannot reproduce it. |
| simulation temperature | 25 | C | model_assumption | weak | none | No Table 1 row. Matches the experimental temperature; still an assumption. |
| simulation timestep | 1 | ms | model_assumption | weak | none | ACCEPTABLE ONLY for reduced LIF/conductance_v0. Must NOT be claimed to resolve sub-ms biological kinetics. |
| ModelDB stimulation amplitude / duration | 120 / 0.03 | nA / ms | model_assumption | weak | none | A model fixture, not a measurement. |
| ModelDB muscle delay | 0.35 | ms | model_assumption | weak | none | Points at the paper's Methods; not measured. |
| ModelDB PSI->DLMn synaptic delay | 0.15 | ms | model_assumption | weak | none | '(estimated)'. Not a measurement. Distinct from the 0.5 ms assumption used elsewhere. |
| ModelDB chemical peak conductance (paper value) | 80 | uS | model_assumption | weak | none | Explicitly '(estimated)'. Not a measurement. Used as a free parameter. |
| ModelDB Ra (never assigned) | 35.4 | ohm.cm | model_assumption | none | none | Table 1 lists it as '(estimated)' but the code NEVER SETS it. Indistinguishable from the simulator default. |
| ModelDB Cm (never assigned) | 1.0 | uF/cm2 | model_assumption | none | none | Table 1 lists it as '(estimated)' but the code NEVER SETS it. |
| ModelDB leak conductance | 0.03 | mS/cm2 | model_assumption | weak | none | '(estimated)'. |
| ModelDB gnatbar / gnapbar / gkbar | 300e-3 / 110e-6 / 10e-3 | S/cm2 | model_assumption | weak | none | Attributed to Gunay+ 2015 in Table 1. ZERO source comments in the file. gkbar is '(estimated)'. |
| ModelDB GF_TTMn_wt / GF_PSI_wt | 0.00 / 0.00 | uS | model_assumption | weak | none | No Table 1 row. The chemical components of the two 'mixed' synapses are effectively switched OFF. |

## C · BLOCKED / DO NOT USE (37)

Requires an unresolved biological measurement, or either scientific gate.

| parameter | value | unit | provenance | strength | gate | notes |
| --- | --- | --- | --- | --- | --- | --- |
| MN5 axoplasmic resistivity (Drosophila-measured) | NONE | ohm.cm | model_assumption | none | transfer | no measurement in any accessible primary source. Hard blocker for any cable computation. |
| MN5 specific membrane resistance | NONE | ohm.cm2 | model_assumption | none | none | no measurement in any accessible primary source. Rm is not a NEURON variable (leak is g_pas). 1/g_pas arithmetic is NOT a measurement. |
| MN5 membrane time constant | NONE | ms | model_assumption | none | none | no measurement in any accessible primary source. Rin x Cm arithmetic ignores the arbor and is not a measured tau. |
| MN5 sodium conductance density | NONE | mS/cm2 | model_assumption | none | none | no measurement in any accessible primary source. Ryglewski & Duch 2009 J Neurophysiol 102:3673 normalises I-Vs 'to cell size' but never states the unit (it is NOT pA/pF). |
| MN5 potassium conductance density | NONE | mS/cm2 | model_assumption | none | none | no measurement in any accessible primary source. pA and kinetics exist; densities do not. |
| MN5 axonal length | NONE | um | model_assumption | none | none | no measurement in any accessible primary source. V10 analyses dendrites only. |
| MN5 soma node / soma surface | NONE (no kind=1 node) | um2 | model_assumption | none | none | Zero soma nodes in all 9 MN5/PSI skeletons. Contact->soma path is permanently UNRESOLVED. |
| PSI->MN5 EPSP latency | NONE | ms | model_assumption | none | none | no measurement in any accessible primary source. F06 explicitly REJECTED a kinetics explanation. |
| PSI->MN5 EPSP rise time | NONE | ms | model_assumption | none | none | no measurement in any accessible primary source |
| PSI->MN5 EPSP decay time constant | NONE | ms | model_assumption | none | none | no measurement in any accessible primary source |
| PSI->MN5 reversal potential | NONE | mV | model_assumption | none | dalpha7 | no measurement in any accessible primary source. Single holding point only; no I-V. |
| PSI->MN5 synaptic conductance | NONE | uS | model_assumption | none | dalpha7 | no measurement in any accessible primary source. Nothing in the literature derives, estimates or names one. This is the prerequisite for any Dalpha7 work. |
| PSI->MN5 receptor density | NONE | receptors/um2 | model_assumption | none | none | no measurement in any accessible primary source. No quantitative immuno, no alpha-Btx binding density here. |
| PSI->MN5 active zone / release site count | NONE | count | model_assumption | none | none | no measurement in any accessible primary source. No T-bar count at this synapse. |
| PSI->MN5 quantal size | NONE | mV | model_assumption | none | none | no measurement in any accessible primary source. No mEPSP analysis. |
| PSI->MN5 release probability | NONE | categorical | model_assumption | none | none | no measurement in any accessible primary source |
| PSI->MN5 short-term plasticity | NONE | categorical | model_assumption | none | none | no measurement in any accessible primary source at the synapse. Kadas 2012 is pathway fidelity only. |
| Dalpha7 channel conductance | NONE | nS | model_assumption | none | dalpha7 | no measurement in any accessible primary source. THIS IS THE GATE. Nothing native exists. |
| Dalpha7 single-channel conductance | NONE | pS | model_assumption | none | dalpha7 | no measurement in any accessible primary source. Heterologous chick/rat values MUST NOT be substituted. |
| Dalpha7 reversal potential | NONE | mV | model_assumption | none | dalpha7 | no measurement in any accessible primary source. A 0 mV reversal is explicitly barred from being read back as a Dalpha7 property. |
| Dalpha7 activation kinetics | NONE | 1/ms | model_assumption | none | dalpha7 | no measurement in any accessible primary source |
| Dalpha7 desensitisation kinetics | NONE | 1/ms | model_assumption | none | dalpha7 | no measurement in any accessible primary source |
| Dalpha7 Ca2+ permeability | NONE | dimensionless | model_assumption | weak | dalpha7 | no measurement in any accessible primary source. Grauso+ 2002 is a HOMOLOGY INFERENCE from vertebrate alpha7, stated as background. Adopting it would be a species assumption, and a permeability is needed before any Ca2+-coupled model. |
| Dalpha7 receptor density at PSI->MN5 | NONE | receptors/um2 | model_assumption | none | dalpha7 | no measurement in any accessible primary source |
| Dalpha7 subunit stoichiometry | NONE | categorical | model_assumption | none | dalpha7 | no measurement in any accessible primary source |
| Dalpha7 localisation at PSI axon terminals | NOT REPORTED | categorical | model_assumption | none | dalpha7 | No Dalpha7 immunostaining of PSI terminals exists in any primary source. |
| Dalpha7 localisation at MN5/DLMn axons | NOT REPORTED | categorical | model_assumption | none | dalpha7 | No Dalpha7 immunostaining of the MN5 arbor exists. The MN5 signal was a GAL4 REPORTER, not protein. |
| Dalpha7 -> Kir7.1 coupling | CHANNEL ABSENT | categorical | anatomical_measurement | strong | dalpha7 | THERE IS NO Kir7.1/KCNJ13 ORTHOLOGUE IN Drosophila. The vertebrate alpha7->Kir7.1 mechanism cannot be modelled here. |
| GF gap-junction conductance (as executed) | 135 / 34.5 | nS | model_assumption | weak | none | gap2.mod declares nanosiemens. EXACTLY 1000x below Table 1. The model's own scan script labels the axis in uS. Intent unrecoverable. |
| GF->PSI native junctional conductance | NONE | nS | model_assumption | none | none | no measurement in any accessible primary source in native neurons. Only Xenopus-oocyte rectification exists. |
| GF->TTMn native junctional conductance | NONE | nS | model_assumption | none | none | no measurement in any accessible primary source in native neurons. |
| MN1->MN5 coupling coefficient | NOT REPORTED | categorical | model_assumption | none | none | H23 reports CC for MN1-4 combinations ONLY. MN5 appears solely via an MN4-MN5 synchronisation index (0.56, n=11). |
| ShakB single-channel conductance | NONE | nS | model_assumption | none | none | In P08 Tables S1-S3, which are INACCESSIBLE. No unitary current or Po. |
| MN5 electrotonic distance contact->soma | NONE (not computed) | space constants | model_assumption | none | transfer | BLOCKED twice: no Drosophila Ra, and no measured transfer. Never computed anywhere in this project. |
| MN5 length constant | NONE (not computed) | um | model_assumption | none | transfer | BLOCKED: requires Ra and Rm, neither of which is measured for Drosophila. |
| MN5 transfer resistance | NONE (not computed) | Mohm | model_assumption | none | transfer | BLOCKED. Never computed in this project. |
| ModelDB chemical peak conductance (as executed) | 0.08 | uS | model_assumption | weak | dalpha7 | EXACTLY 1000x below Table 1. This is the only PSI->DLMn conductance figure in existence and it is internally contradictory. |

## Unresolved conflicts — no winner chosen

| parameter | conflict | why it stays open |
| --- | --- | --- |
| MN5 whole-cell capacitance | C-01 | 43 ± 2 pF vs 127 ± 16 pF, same cell, same nominal preparation, ~2.95×. No source reconciles them. Neither may be averaged or preferred. |
| MN5 Ra provenance | C-10 / new | The only value ever applied (90 Ω·cm) is *Manduca*-derived, adopted by assertion. The only *measured* Drosophila motor-neuron Ra is 212.47 ± 3.69 Ω·cm (larval aCC) — 2.4× larger. |
| MN5 passive parameter provenance | C-10 | Cm, Ra and g_pas in the sole MN5 model are *Manduca* values, self-described as "commonly applied". |
| gap-junction conductance | C-02 | 135 / 34.5 µS in Table 1 vs 135 / 34.5 **nS** as executed by `gap2.mod`. Exactly 1000×. The model's own scan script labels the axis in µS. |
| chemical peak conductance | C-03 | 80 µS in Table 1 vs **0.08 µS** as executed. Exactly 1000×. This is a *different synapse* from C-02 and the two must never be pooled. |
| MN1→MN5 coupling coefficient | C-12 | Not reported by any source; only MN1–4 coefficients exist. |
| SWC `kind=2` semantics | C-08 | MaleCNS documents no assignment procedure; the official reader discards `node_type`. Biology UNDEFINED IN AVAILABLE SOURCE. |
| MN5 dendritic diameter | corrected | Literature text says 0.44 µm; an earlier project note of 0.88 µm is unsupported. |
| SIZ distance | C-11 | "88 ± 15 µm" does not exist in Kuehn & Duch 2013. Corrected to ~100 µm from soma and 11 ± 3 µm from the dendrite origin. |

## Minimum honest model — what may be simulated today

| capability | possible now? | blocker |
| --- | --- | --- |
| 1. anatomy only | **YES** | — |
| 2. passive MN5 response | **PARTIAL** | needs Ra and Rm (blocked); Cm conflicted. A reduced single-compartment or LIF model is possible using the safe rows, but is not a cable model. |
| 3. PSI→MN5 synaptic response | **NO** | synaptic conductance never measured (M-01) |
| 4. spatial transfer contact→soma | **NO** | Ra blocked **and** no measured transfer (M-02) — **GATE 1** |
| 5. Dα7-mediated conductance | **NO** | no native Dα7 conductance; no Kir7.1 orthologue — **GATE 2** |
| 6. GFS electrical coupling | **PARTIAL** | no native Gj; 1000× internal conflict; MN1→MN5 CC unreported. Not a gate. |

Nothing in bucket C may be implemented. Buckets A and B may be used, with B
labelled as assumptions.

## Final statement

108 parameters audited. **40 SAFE**, **31 ASSUMPTION-ONLY**,
**37 BLOCKED**. 15 unresolved conflicts preserved with no
winner chosen.

**PSI→MN5 spatial voltage transfer: NOT AUTHORIZED**
**Dα7 conductance: NOT AUTHORIZED**
