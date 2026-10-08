# Parameter Registry — Fly Brain GFS / PSI→MN5

Rule: a parameter with no qualifying measurement is written
**NO QUALIFYING MEASUREMENT FOUND**. No guessed values appear anywhere in this file.

---

## A · MN5 electrophysiology

| Parameter | Value | Uncert. | n | Prep | Temp | Age/Sex | Method | Source | Prov | Applicable to MaleCNS MN5? |
|---|---|---|---|---|---|---|---|---|---|---|
| Resting potential | **−67.8 ± 5.5 mV (SD, n=13)** | SD | 13 | in situ somatic WC, current clamp, zero holding current | not stated | adult, days AEL not stated; F1 ♀ *w*; UAS-mCD8-GFP, D42-GAL4, Cha-GAL80×w1118 | break-in, no holding current | **Ryglewski, Kilo & Duch 2014, Eur J Neurosci 39:151, PMID 24620836, PMC4433752, Table 1** | NEM | yes — **strongest record** |
| Resting potential (alt) | −59 mV | none | n/a | representative figure caption only | not stated | not stated | WC current clamp | Ryglewski & Duch 2012 *J Vis Exp* 66:e3779, PMC3490319, Fig 6 caption | NEM (weak) | with caveat: no n, no uncertainty |
| ⚠ "−65 mV" | **DO NOT CITE** | — | — | — | — | — | — | attributed to Ryglewski & Duch 2009 by Ryglewski+ 2011, but **that value does not appear in [R09]'s full text** | — | **unverifiable secondary attribution** |
| ⚠ "−74 mV" | **NOT a resting potential** | — | — | — | — | — | — | Fayyazuddin 2006 held cells there by **constant current command** | — | clamp setpoint, not a measurement |
| Rin | 102 ± 12 MΩ | type not stated | 22 | in situ somatic WC | **not stated** | **not stated** | patch | Fayyazuddin+ 2006 | NEM | yes |
| Rin (2nd) | **97 ± 31 MΩ** | type not stated | 52 | in situ somatic WC | **~22 °C** | not stated | patch | **Herrera-Valdez, McKiernan, Berger, Ryglewski, Duch & Crook 2013, J Comput Neurosci 34:211, PMID 22878689, PMC6595220** | NEM | yes |
| Rin (3rd, QC thresholds — NOT measurements) | "must be > 80 MΩ" / "> 120 MΩ" / "≥ 100 MΩ" | — | — | — | — | — | — | Ryglewski & Duch 2012 / Ryglewski+ 2011 | — | **acceptance criteria, do not cite as Rin** |
| Cm | **43 ± 2 pF** | SEM | 22 | whole-cell, somatic | not reported | not reported | patch | same | NEM | **CONFLICTED** (C-01) |
| Cm (alt) | **127 ± 16 pF** | SD | **not stated in the sentence** | in situ somatic WC, C-slow compensation, Rs 9–13 MΩ mandatory | **24 °C** | **female, 1–3 d AEL**; F1 ♀ C380-GAL4>UAS-mCD8-GFP; ;Cha-GAL80×♂w1118 | C-slow comp | Ryglewski & Duch 2009 J Neurophysiol 102:3673, PMID 19828724, PMC2804405 | NEM | **CONFLICTED** (C-01). Authors' caveat: *"although large dendritic trees can cause inaccuracies in measurements of Cm"* |
| Cm (alt, **NOT independent**) | **127 ± 16 pF — identical mean AND identical SD** | SD | 52 | in situ somatic WC | **~22 °C** | not stated | patch | **Herrera-Valdez, McKiernan, Berger, Ryglewski, Duch & Crook 2013, J Comput Neurosci 34:211, PMID 22878689, PMC6595220** | NEM | **treat as ONE 127 pF measurement, not two** — [R09] is its cited method source |
| Rm (specific membrane resistance) | NO QUALIFYING MEASUREMENT FOUND for Drosophila | — | — | — | — | — | — | — | — | — |
| Ra (axial resistance) | **90 Ω·cm — *Manduca*, adopted by assertion** | — | — | model | — | — | — | Ryglewski & Duch 2009 citing Meseke+ 2009 (*Manduca*) | LDP | **NO — wrong species** (C-10) |
| Specific Cm used in that model | 1.15 µF/cm² — *Manduca*, adopted | — | — | model | — | — | — | same | LDP | **NO** |
| g_pas used in that model | 0.0001667 Ω⁻¹cm⁻² — *Manduca*, adopted | — | — | model | — | — | — | same | LDP | **NO** |
| Ra in ModelDB 245415 | **NEVER SET** → NEURON default 35.4 Ω·cm | — | — | model | 25 °C | — | — | ModelDB 245415 | MA | **indistinguishable from a default** (C-06) |
| Cm in ModelDB 245415 | **NEVER SET** → NEURON default 1 µF/cm² | — | — | model | — | — | — | same | MA | **indistinguishable from a default** (C-06) |
| Membrane time constant τ | NO QUALIFYING MEASUREMENT FOUND | — | — | — | — | — | — | — | — | — |
| Membrane area (measured) | NO QUALIFYING MEASUREMENT FOUND | — | — | — | — | — | — | — | — | — |
| Membrane area (MaleCNS mesh) | **18,725.6 / 19,665.4 µm²** | 2e-16 rel (cross vs Heron) | — | EM mesh | — | — | triangle area | MaleCNS `.ngmesh` | AM | yes |
| Membrane area (SWC frustum) | 24,803.7 / 25,796.8 µm² | — | — | derived | — | — | truncated-cone lateral | this project | MDE | **~24 % larger than the mesh — different domains, do not equate** |
| Literature central-neuron area | ~13,000 µm² | — | — | — | — | — | — | Duch+ 2008 | LDP | **sub-region only**, not whole-neuron |
| Dendritic length | **"about 6 mm"** (text; exact value is in **Fig. 1E, an image — not extractable**) | — | **11 female flies, 1 day AEL, 25 °C** | Neurobiotin fill + confocal | 25 °C | 1 d AEL, ♀ | geometric reconstruction | **von Hoff & Duch 2010, J Comp Neurol 518:2169, PMID 20437522, PMC4441823** | AM | different specimen/method |
| Dendritic branch count | **"nearly 4,000"** (text; Fig 1E) | — | 11 | same | 25 °C | same | same | same | AM | same |
| Mean dendritic diameter | **"about 0.44 µm average diameter"** (text; Fig 1E) | — | 11 | same | 25 °C | same | same | same | AM | **⚠ an earlier project note of 0.88 µm is not supported — the paper's prose says 0.44 µm** |
| Mean dendritic segment length | 1.5 µm | — | 11 | same | 25 °C | same | same | von Hoff & Duch 2010 | AM | yes |
| Branch orders | 47 ± 6 | — | 11 | same | 25 °C | same | same | same | AM | yes |
| Max path length from soma | 120 ± 7 µm | — | 11 | same | 25 °C | same | same | same | AM | yes |
| Dendrites within 25 / 35 µm of soma | 50 ± 4 % / 80 ± 6 % | — | 11 | same | 25 °C | same | same | same | AM | yes |
| First-order dendritic subtrees | **23** (96 ± 2 % of total dendritic length); **13 anterior, 10 posterior** | — | 11 | same | 25 °C | same | same | same | AM | yes — **the only anterior/posterior subdivision that exists for MN5 dendrites** |
| Branching angle / asymmetry index | 91 ± 32° / 0.32 ± 0.07 | — | 11 | same | 25 °C | same | same | same | AM | yes |
| Axonal length | **NOT REPORTED** — von Hoff & Duch 2010 analyses dendrites only | — | — | — | — | — | — | — | — | — |
| Total cable (MaleCNS) | 7,453.5 / 7,190.2 µm | — | — | EM skeleton | — | — | segment sum | MaleCNS | AM | yes |
| Compartmental split of that cable | 93 % `kind=0` (undefined) / 7 % `kind=2` | — | — | — | — | — | — | MaleCNS | AM | **not** an axonal/dendritic split (C-08) |
| Spike threshold | **−24.1 ± 8.2 mV (SD, n=11)** | SD | 11 | in situ somatic WC | not stated | adult; F1 ♀ *w* | steepest slope at AP onset, just-threshold current injection | **Ryglewski, Kilo & Duch 2014, Table 1** | NEM | yes |
| ⚠ "∼10–15 V, 100 µs pulse" | **NOT an MN5 spike threshold** — it is the threshold for **electrically stimulating the Giant Fiber** | — | n not stated | — | — | — | — | Fayyazuddin+ 2006 | — | **TRAP — do not cite as a spike threshold** |
| Somatic AP amplitude | **45.5 ± 8.6 mV (SD, n=13)** | SD | 13 | in situ somatic | not stated | adult | patch | Ryglewski+ 2014 Table 1 | NEM | yes |
| AP time to peak | **1.20 ± 0.33 ms (n=13)** | SD | 13 | same | — | — | patch | same | NEM | yes |
| AP 50 %-amplitude width | **0.92 ± 0.25 ms (n=13)** | SD | 13 | same | — | — | patch | same | NEM | yes |
| Somatic AP amplitude (alt) | 50–60 mV | — | — | WC | — | — | patch | Fayyazuddin+ 2006 | NEM | yes |
| Soma generates spikes? | **"the soma does not generate action potentials but is mostly passive"**; adult MN5 soma and primary neurite **devoid of VGSC immunolabel** | — | — | — | — | — | — | Ryglewski+ 2009 / 2013 / 2014 | AM | yes |
| g_Na (density) | **NO QUALIFYING MEASUREMENT FOUND.** Ryglewski+ 2009 normalises I–V "to cell size" but **never states the unit** (not pA/pF) | — | — | — | — | — | — | — | — | — |
| g_K (density) | **NO QUALIFYING MEASUREMENT FOUND** (pA and kinetics only) | — | — | — | — | — | — | — | — | — |
| I(A) activation / inactivation | V½ **−12.1 ± 1.4** / **−40.02 ± 0.33** mV | — | n=57 total transient K | 24 °C | 1–3 d AEL, ♀ | patch | Ryglewski & Duch 2009 | NEM | yes |
| I(A) time to peak | 2.42 ± 0.31 ms (−50 mV); 1.46 ± 0.23 ms (+20 mV) | — | — | 24 °C | — | patch | same | NEM | yes |
| I_CF activation / inactivation | V½ **−22.34 ± 2.02** / **−49.33 ± 0.24** mV | — | — | 24 °C | — | patch | same | NEM | yes |
| Transient I(Ca) time to peak | 0.76 ± 0.16 ms; abolished by 500 µM Cd²⁺ | — | — | 24 °C | — | patch | Ryglewski+ 2011 J Physiol 589:5567 | NEM | yes |
| DTX block of transient K | 200 nM blocks **35–40 %** | — | — | 24 °C | — | pharmacology | Ryglewski & Duch 2009 | NEM | yes |
| Shaker localisation | predominantly **axonal** | — | — | — | — | — | immuno | same | AM | yes |
| Leak conductance | **NO MEASURED value for MN5** | — | — | — | — | — | — | — | — | the 1.667e-4 S/cm² is an adopted *Manduca* default |
| Membrane τ | **NO QUALIFYING MEASUREMENT FOUND.** Ryglewski+ 2011 explicitly declines: *"due to uncertainties in voltage control through the large MN5 dendritic tree of more than 6500 μm length we did not attempt quantification of the activation and inactivation time constants"* | — | — | — | — | — | — | — | — | R_in × C_m arithmetic is **not** a measured τ |
| Ra (only measured Drosophila motor-neuron value) | **212.47 ± 3.69 Ω·cm** | — | 5 | **fitted passive model, 3rd-instar larval aCC** | — | larva | fit | **Günay+ 2015 PLoS Comput Biol 11:e1004189, Table 2 — ModelDB 152028** | NEM | **NOT MN5** — but **2.4× the adopted 90 Ω·cm**, evidence 90 is not Drosophila |
| Specific Cm (aCC) | 0.77 ± 0.02 µF/cm² | — | 5 | fitted, larval aCC | — | larva | fit | same | NEM | NOT MN5 |
| Leak density (aCC) | 37.96 ± 4.38 µS/cm² | — | 5 | fitted, larval aCC | — | larva | fit | same | NEM | NOT MN5 |
| Non-somatic / dual-site MN5 recording | **NONE EXISTS.** Every MN5 dataset located is somatic whole-cell. Hürkey 2023 does dual in situ somatic patch — but of MN **pairs**, not two sites on one MN5, and **MN5 was not among the paired cells** | — | — | — | — | — | — | — | — | the strongest negative in this register |
| Spike initiation location (SIZ) | **~100 µm from soma**; **11.25 µm** and **12.1 µm** distal to the most distal posterior dendrite origin | "about"; SD/SEM unstated | 7 animals (intensity); 2 reconstructions (distance) | fills + confocal | — | adult | **anti-VGSC immunocytochemistry — NOT electrophysiology** | **Kuehn & Duch 2013, Eur J Neurosci 37:860, PMID 23279094, PMC3604049** | AM | **not registered** — no axis, no deposit, no transform (M-08) |
| MN5 axonal length | **NOT REPORTED anywhere** | — | — | — | — | — | — | — | — | **M-06** |

---

## B · PSI→MN5 synapse

| Parameter | Value | Status |
|---|---|---|
| Contact count (MaleCNS v1.0, **minconf 0.5**) | **17** (802401→801970) + **26** (903327→801295) = **43**; 0 cross-pairings | **AM**. Not matched to any publication; a neuPrint query result. Always quote the threshold. |
| Contact count (MANC) | ~1,000 PSI→ all five DLM MNs (axons); ~600 GFC2→DLM axons | **No per-pair value, no threshold, n=1 specimen.** Not MN5-specific. Not a contradiction — automated counts undercount PSI output. |
| Contact extent | "multiple contacts that span 50 µm", following the axons into the posterior dorsal motor nerve | qualitative, Fayyazuddin+ 2006 |
| Transmitter | **Acetylcholine** | conditional *cha* (ChAT) mutations; Gorczyca & Hall 1984 *J Neurogenet* 1:289 (secondary citation, full text not retrieved) |
| Receptor | **Dα7 nAChR** | **genetic inference only** (allele strength vs EPSP amplitude) — not directly identified |
| EPSP amplitude | **4.71 ± 0.35 mV (SEM, n=10)** at −74 mV, current clamp | NEM, but a **filtered somatic** voltage; **GF stimulated, PSI never directly stimulated**; age/sex/temp not reported |
| EPSP amplitude, *gfA*¹ | 1.5 ± 0.32 mV (SEM, n=7), p=1×10⁻⁵ | same caveats |
| EPSP latency | **NO QUALIFYING MEASUREMENT FOUND** | Fayyazuddin 2006 explicitly rejected a kinetics explanation |
| EPSP rise time | **NO QUALIFYING MEASUREMENT FOUND** | |
| EPSP decay τ | **NO QUALIFYING MEASUREMENT FOUND** | |
| Reversal potential | **NO QUALIFYING MEASUREMENT FOUND** | current clamp at one point only; no I–V |
| Conductance | **NO QUALIFYING MEASUREMENT FOUND** | nothing derives, estimates or names one |
| Quantal size | **NO QUALIFYING MEASUREMENT FOUND** | |
| Quantal content | **NO QUALIFYING MEASUREMENT FOUND** | |
| Release probability | **NO QUALIFYING MEASUREMENT FOUND** | |
| Active zones / release sites | **NO QUALIFYING MEASUREMENT FOUND** | no T-bar count at this synapse |
| Receptor density | **NO QUALIFYING MEASUREMENT FOUND** | no quantitative immuno, no α-Btx binding density here |
| Short-term plasticity | **NO QUALIFYING MEASUREMENT FOUND** at the synapse | Kadas 2012 pathway-fidelity only, authors' own caveats |
| Synaptic delay | **NOT MEASURED** | the ~0.5 ms used by Gaitanidis 2025 is an explicit **assumption** from a TTM→DLM muscle offset |
| ModelDB chemical peak (paper) | 80 µS "(estimated)" | **MA** — C-03 |
| ModelDB chemical peak (executed) | 0.08 µS | **MA** — exactly 1000× |

---

## C · Dα7

See `da7_evidence.md` in full. Summary:

| Property | Native Drosophila | Heterologous |
|---|---|---|
| Localisation at PSI terminals | **NOT REPORTED** | — |
| Localisation at MN5/DLMn axons | **NOT REPORTED** | — |
| Localisation at GF dendrites | 10–100× stronger than elsewhere (immuno, n.d.) | — |
| α-Btx binding | **YES** — Dα7 LBD glycopeptide NNGSCLYVPPGIFK, Asn170, MS, n=3 | — |
| Mutant phenotypes | jump abolished (4 alleles); flight/trap/ERG normal; null viable+fertile, no locomotor deficit | — |
| Rescue | `c17`-GAL4 (GF-specific) — spatially restricted; `OK307`-GAL4 — **not** localised to MN5 | — |
| Single-channel conductance | **NO MEASUREMENT** | chick/rat α7 |
| Open probability | **NO MEASUREMENT** | rat α7 |
| Reversal potential | **NO MEASUREMENT** | chick α7 |
| Activation/desensitisation kinetics | **NO MEASUREMENT** | chick/rat α7 |
| Ca²⁺ permeability | **NO MEASUREMENT** | homology inference only (Grauso+ 2002) |
| Density at PSI→MN5 | **NO MEASUREMENT** | — |
| Subsynaptic clustering | **NO MEASUREMENT** | — |
| **Kir7.1 coupling** | **IMPOSSIBLE — no KCNJ13 orthologue in *Drosophila*** (Irk1/2/3 only) | vertebrate mechanism |
| **Native PSI→MN5 Dα7 conductance** | **NO MEASUREMENT — THIS IS THE GATE** | — |

---

## D · GFS electrical coupling (never mixed with section B)

| Connection | Quantity | Value | Prov | Note |
|---|---|---|---|---|
| **GF→PSI** | junctional conductance | **NO QUALIFYING MEASUREMENT FOUND** | — | only oocyte rectifier index 0.21 |
| GF→PSI | rectification index | 0.21 (oocytes, 4 pairs) | NEM **heterologous** | never quote as GFS |
| GF→PSI | Gj kinetics | ~50–60 % of max by 5 ms | NEM heterologous | |
| GF→PSI | age-dependence | **NONE** — no ShakB decline | NEM | Auger 2020 |
| GF→PSI | latency | 1.3–1.7 ms (pathway, WT range) | NEM | not synapse-specific |
| **GF→TTMn** | junctional conductance | **NO QUALIFYING MEASUREMENT FOUND** | — | |
| GF→TTMn | ShakB plaque fraction | 14.72 ± 3.99 % SD (n=9) | NEM | *fra* LOF 3.00±0.57; *Netrin* LOF 1.54±0.48 |
| GF→TTMn | latency | 0.93 ms young / 1.22 ms old | NEM | Augustin 2019 |
| GF→TTMn | following-frequency ceiling | 1:1 to 300 Hz WT | NEM | fails at 100 Hz in *shakB²* |
| GF→TTMn | age-dependence | latency rises with age; ShakB falls | NEM | synapse-**specific** |
| **MN1→MN5** | coupling coefficient | **NOT REPORTED** | — | CC given for MN1–4 only |
| MN1–MN2 / MN3–MN4 | CC | 0.023 ± 0.003 SEM (6 pairs) | NEM | Hürkey 2023 |
| other MN1–4 | CC | 0.01 ± 0.0027 SEM (10 pairs) | NEM | |
| MN1–MN5 | latency | **NOT REPORTED** | — | |
| MN4–MN5 | synchronisation index | median 0.56 (n=11) | NEM | ShakB-OE 0.84 (n=7) |
| **MN5→MN1** | bidirectional, non-rectifying | qualitative only | NEM | no CC, no conductance, no latency |
| **ShakB** | = **inx8**, an innexin — **not Kv1** | — | — | GF: ShakB(N+16); TTMn/PSI: ShakB(L) → heterotypic |
| ShakB | single-channel conductance / unitary current / Po / Vj Boltzmann params | **NO QUALIFYING MEASUREMENT FOUND** | — | in Phelan 2008 Tables S1–S3 — **INACCESSIBLE** |
| ModelDB g_gap | 135 / 34.5 µS paper vs **nS** executed | — | MA | exactly 1000×, C-02 |
