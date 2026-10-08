# Final Anatomy Audit — PSI → MN5 / DLMn a,b

Frozen candidate. Date **2026-10-05**. Supersedes nothing; completes the chain
opened by 3.0D-8Q (mesh), 8R (contact path), 8T (SWC semantics), 8U (literature)
and closed by 8V (official `compartment_post`).

**Verdict up front.** The anatomy chain is **internally consistent,
provenance-controlled and reproducible**. M-06 is resolved in its per-synapse
form. **Both electrical gates remain closed**, and nothing in this audit moves
them.

---

## A · Identity

| Role | Body ID | Cell type | Hemisphere | VFB ID | Annotation status |
|---|---|---|---|---|---|
| MN5 / DLMn a,b | **801970** | `DLMn a, b` (superclass `wm`) | left | `VFB_jrmc37jr` | `Traced` |
| MN5 / DLMn a,b | **801295** | `DLMn a, b` (superclass `wm`) | right | `VFB_jrmc37js` | `Traced` |
| PSI | **802401** | PSI | left | — | — |
| PSI | **903327** | PSI | right | — | — |

Both MN5 bodies: `somaSide` L/R, `somaNeuromere` `T2`, `exitNerve` **PDMNa**,
`group` 801295 (they share a group).

**Identity is textual, not inferred.** MN5 is the motoneuron that *"innervates
the two most dorsal fibers of the dorsal longitudinal wing depressor muscle
(DLM)"* (Ryglewski & Duch 2009, verbatim) — DLM fibres **5 and 6** —
**contralateral** to its soma (Hürkey+ 2023). No project code infers this.

**Provenance:** `AM` (anatomical/connectomic observation).

## B · Synapse count

| pairing | contacts | cross-pairings |
|---|---|---|
| 802401 → 801970 | **17** | 0 |
| 903327 → 801295 | **26** | 0 |
| **total** | **43** | **0** |

Source: MaleCNS v1.0 `syn-partners-male-cns-v1.0-minconf-0.5.feather`
(`minconf 0.5`, `SOURCE_MINCONF`). **The threshold must always be quoted.**

**Independent corroboration:** the official synapse annotation layer contains
exactly **17** and **26** annotations for those pairings — matching the Feather
extraction exactly. Two independent files agree.

**Cross-dataset contrast (not a contradiction):** MANC reports ~1,000 PSI output
synapses onto all five DLM motoneurons, with no per-pair breakdown, no confidence
threshold, and n = 1 specimen. Automated counts undercount PSI output because PSI
is manually annotated as an electrical-transmission neuron.

**Provenance:** `AM`.

## C · Official `compartment_post` result

Source layer: `gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed`
(`neuroglancer_annotations_v1`, CC-BY, unauthenticated).
Official enum, read from the layer's own `info`:
`["unknown","axon","dendrite","linker","cell-body-fiber"]`.

| grouping | n | `compartment_post` |
|---|---|---|
| 801970 (PSI L) | 17 | **axon ×17** |
| 801295 (PSI R) | 26 | **axon ×26** |
| PDMN class | 36 | axon ×36 |
| WTct class | 7 | axon ×7 |
| **total** | **43** | **axon ×43** |

Missing **0** · ambiguous **0** · unknown post-compartment **0**.

`compartment_pre`: **axon ×38**, **unknown ×5 — all 5 on 801295.** Preserved
as-is; not resolved, not imputed.

**For contrast — the same field across all of MN5's input:**

| body | total | axon | dendrite | linker | cell-body-fiber |
|---|---|---|---|---|---|
| 801970 | 10,529 | 452 (4.3 %) | 9,713 (92.2 %) | — | 364 (3.5 %) |
| 801295 | 11,260 | 2,384 (21.2 %) | 8,787 (78.0 %) | 89 (0.8 %) | — |

**PSI→MN5 contacts are exclusively in MN5's axonal compartment while the bulk of
MN5's input is dendritic.** Independently consistent with Fayyazuddin+ 2006:
*"the PSI bypasses the entire dendritic structure of MN5 and makes multiple
synaptic contacts that span 50 μm and follow the axons out into the posterior
dorsal motor nerve."*

**Method:** `cloud-volume` 12.15.1 via
`create_precomputed_annotation`, with two **metadata-only** shims recorded in the
output — `annotation_type` uppercased (`"line"`→`"LINE"`) and legacy positional
`np.hstack`. Matching: exact integer equality of the post-synaptic coordinate
within the `body_post` relationship shard; a non-unique match raises.

**Provenance:** `AM` — an anatomical/connectomic **dataset annotation**.
**Not** `NEM`. Not an electrophysiological measurement. MaleCNS publishes no
assignment procedure for these labels, so the label string is reported verbatim
and **is not interpreted here**.

## D · Contact geometry

| quantity | 801970 | 801295 |
|---|---|---|
| contacts | 17 | 26 |
| contact → mesh surface | min 8.55, med 35.17, mean 31.76, max 51.70 nm | min 1.67, med 26.97, mean 31.91, max 80.22 nm |
| nearest surface point stored | yes (all 43) | yes |
| nearest triangle index | yes | yes |
| nearest vertex distance | tracked **separately**, never substituted | yes |
| component verdict | 14 CONFIDENT / 3 **AMBIGUOUS** / 0 too-distant | 26 CONFIDENT / 0 / 0 |

**The 3 ambiguous contacts** (801970, indices 8/9/10, PSI left) have margins of
only −4.5 to −5.8 nm and ratios 1.110–1.172; the runner-up is the **same
fragment** in all three. **AMBIGUOUS is preserved.** No threshold was invented to
break the tie, and their SWC nodes (139/142) are unambiguous — so the ambiguity
does not propagate into any path result.

**Provenance:** `AM`.

## E · Path measurements

| quantity | 801970 | 801295 | Provenance |
|---|---|---|---|
| contact depth from SWC root | 184.0–267.8 µm | 169.2–230.6 µm | `AM` |
| contact → SWC-root path | 184.0 / 234.4 / 267.8 µm | 169.2 / 177.6 / 230.6 µm | `MDE` (nearest-node projection) |
| contact → `somaLocation` straight line | 110.3 / 157.9 / 172.9 µm | 112.3 / 127.6 / 169.3 µm | `AM` |
| **contact → soma-label graph path** | **UNRESOLVED** | **UNRESOLVED** | no soma node exists |
| contact → soma-**proxy** tree path | 157.8 / 208.1 / 241.6 µm | 154.1 / 162.6 / 215.6 µm | `MDE` on a `MA` proxy |
| distinct projected SWC nodes | 11 (5 shared) | 14 (9 shared) | `AM` |

Four quantities are kept strictly separate: surface distance, root path, soma
straight line, soma-proxy graph path. **The SWC root is never substituted for the
soma.** Euclidean distance is never presented as a path length.

**Provenance caveat:** the root itself carries a documented upstream caveat —
neuPrint states that for stored skeletons *"the root node … is not particularly
significant"*. The root↔soma distances above are **measurements**, not a
documented property of the file format.

## F · Soma-region status

- **No soma node exists.** Zero `kind=1` across all 9 MN5/PSI skeletons. The
  labelled-soma graph path is permanently **UNRESOLVED** for these files.
- **The soma region is present.** Proximal dilation: body 801970 node 23, radius
  **4.671 µm**, **2.10 µm** from `somaLocation`; body 801295 nodes 5–9, radius
  **5.376 µm**, **1.45 µm** from `somaLocation`.
- `somaLocation` falls **inside** the mesh bbox and only **3.87 / 3.50 µm** from
  the nearest mesh surface.
- Root ↔ `somaLocation`: **23.76 / 14.88 µm**.
- `tosomaLocation` and `rootSide` annotation columns exist but are **unpopulated**.
- The proxy node is itself **`kind=2`** — a further reason it is not called a soma.

Terminology is fixed at **soma-region proxy**. Promotion to "soma" requires an
authoritative source that does not exist.

**Provenance:** the dilation measurements are `AM`; calling it the soma is a
**Model assumption**; the proxy paths are `MDE`.

## G · SWC semantic status — **UNRESOLVED**

- MaleCNS cites the SWC v1.0.0 spec (PMC10654402) for **format**: 0 = Undefined,
  1 = Soma, 2 = Axon.
- **MaleCNS documents nothing about how its Type column is populated.** The Berg
  paper never uses the string "SWC". The official reader **discards**
  `node_type`. Skeletons are segmentation-derived.
- Observed: `kind=0` ≈ 93 % of cable, `kind=2` ≈ 7 %, `kind=1` zero, root
  `kind=0`.
- **`MALECNS_NODE_TYPE_BIOLOGY = "UNDEFINED IN AVAILABLE SOURCE"`.**
- **The `compartment_post` result does NOT resolve this.** Different column,
  different provenance, different convention. The comparison is now *possible*
  and has deliberately **not** been performed — performing it would be inference.

## H · SIZ status — **UNRESOLVED**

- SIZ = **spike initiating zone** (the expansion "Secondary Isatoz Axon" appears
  in **no** publication).
- **"88 ± 15 µm" does not exist** in Kuehn & Duch 2013. The paper reports **two
  figures from two different reference points**: *"about 100 µm from the soma"*
  (no numeric uncertainty), and *"11 ± 3 µm around the origin of the most distal
  posterior dendrite"* (n = 7, SD-vs-SEM unstated, measured from that
  dendrite's origin).
- Method: **anti-VGSC immunocytochemistry, not electrophysiology.**
- **Four independent blockers:** (1) the reconstruction was **never deposited**;
  (2) **zero dendrite-labelled nodes**; (3) **no anatomical axis documented
  anywhere**; (4) **no transform** from the light-microscopy frame into MaleCNS EM
  space.
- 0 of 43 contacts fall in the literature shell.

## I · Mesh / topology caveats

- The mesh is **not a closed surface**: 462,426 / 495,569 boundary edges,
  2,238 / 2,267 non-manifold edges, 807 / 873 duplicate faces.
- **2,587 / 2,765 components**; largest holds only **2.8 % / 2.3 %** of area.
- Mesh area 18,725.6 / 19,665.4 µm² (cross product, Heron-validated to 2e-16),
  against an SWC frustum approximation of 24,803.7 / 25,796.8 µm² — a **~24 %
  difference between two different domains**, not an error estimate.
- neuPrint attributes fragmentation to *"artifacts in the underlying segmentation
  from which the skeletons were generated"*. **A disconnected component does not
  establish a disconnected biological process.** No component is ever assigned a
  compartment name.
- `syn-points-male-cns-v1.0-minconf-0.5.feather` is a **truncated download** and
  is unusable.
- Radius units are 8 nm, not the spec's µm — an undocumented deviation, inferred
  from plausibility.

## J · Provenance classification

| Block | Class | Note |
|---|---|---|
| Body identities, soma side/neuromere, exit nerve | `AM` | official annotation table |
| 43 contact counts, both pairings | `AM` | two independent files agree |
| `compartment_post` / `compartment_pre` | `AM` | dataset annotation, **not** `NEM` |
| Contact → surface distance, nearest triangle/vertex | `AM` | EM geometry |
| Component verdicts | `AM` + stated convention | margin ratio 1.5× is a convention |
| Contact → SWC-root path; contact → soma-proxy path | `MDE` | rests on a nearest-point projection |
| Soma-region dilation radius/location | `AM` | direct measurement |
| "That dilation is the soma" | `MA` | Model assumption |
| SWC `kind` counts and radii | `AM` | measured; biology undefined |
| SIZ figures (~100 µm; 11 ± 3 µm) | `LDP` | immunolabel literature estimate |
| MN5 Cm 43 ± 2 / 127 ± 16 pF | `NEM` | **CONFLICTED**, unresolved |
| MN5 Ra / Rm / g_pas / leak | `LDP` | *Manduca*-derived, adopted |
| spatial voltage transfer | **NONE** | never measured |
| Dα7 conductance | **NONE** | never measured |

**No row was promoted between classes.** `compartment_post` is `AM`, not `NEM`.

## K · Remaining anatomy uncertainties

| # | Uncertainty | Blocks a gate? |
|---|---|---|
| 1 | SWC `kind=2` biology undefined by the source | No |
| 2 | Contact → **soma** graph path permanently UNRESOLVED (no soma node) | **Yes** — this is the M-02 blocker |
| 3 | Soma-region proxy is an assumption, not a labelled soma | Yes, indirectly |
| 4 | SIZ unregistered (4 independent blockers) | No |
| 5 | Per-neuron cut node unreleased (M-06 scope limit) | No |
| 6 | 3 contacts have undetermined mesh component | No |
| 7 | `compartment_pre = unknown` for 5 contacts on 801295 | No |
| 8 | Mesh fragmentation and non-closed surfaces | No |
| 9 | SWC root significance not guaranteed by the source | Weakens root-referenced paths |
| 10 | `cell-body-fiber` synapses on 801970 (364), absent on 801295 — unexplained | No |

## L · Exact boundary between anatomy evidence and electrical modelling

**Everything in this document is anatomy or connectomics.** The boundary is:

**PERMITTED from this chain:** body identity · synapse identity and count ·
official per-synapse compartment label · surface distance and nearest
surface/triangle/vertex · component identity as topology · SWC process geometry ·
root-referenced path length · soma-annotation straight-line distance · mesh area,
extent and topology · literature anatomical figures with their provenance.

**NEVER PERMITTED from this chain:** Ra · Rm · Cm · specific membrane capacitance
or resistance · g_pas · leak conductance · length constant λ · space constant ·
electrotonic distance · cable distance · attenuation · transfer resistance ·
input resistance · axial resistance · voltage transfer · spatial voltage
transfer · synaptic conductance · Dα7 conductance · receptor kinetics · reversal
potential · synaptic delay.

**The specific traps this audit closes:**
1. `compartment_post = "axon"` is a **label**, not a distance and not a voltage.
   It tells us where the contacts are; it says nothing about how much signal
   reaches the soma.
2. A root-referenced path length is **not** an electrotonic distance.
3. The soma-region proxy is **not** a soma.
4. `kind=2` is **not** axon because the synapse layer says axon somewhere.
5. PDMN/WTct carry **no** compartment information — all 43 are `axon` regardless
   of class, so the label cannot be confounded with or inferred from the class.

**Gate status, stated at the boundary:**
**PSI→MN5 spatial voltage transfer: NOT AUTHORIZED**
**Dα7 conductance: NOT AUTHORIZED**

---

## M-06

**RESOLVED — per-synapse `compartment_post` annotation.**

All 43 verified contacts carry an official label; 0 missing, 0 ambiguous.
Scope limitation: the **per-neuron cut node remains unreleased**.

## PSI→MN5 spatial voltage transfer

**NOT AUTHORIZED.** Never measured in any species-independent, Drosophila MN5
preparation. `compartment_post` does not establish it (E-048).

## Dα7 conductance

**NOT AUTHORIZED.** No native measurement exists; Dα7 has never been imaged at
PSI terminals or MN5 axons; Drosophila has no Kir7.1/KCNJ13 orthologue.

## Final verdict

The anatomy evidence chain is **internally consistent, provenance-controlled,
reproducible, and ready to freeze.** It produces no unsupported electrical
inference, and it identifies exactly which experiment — not which further data
analysis — would be required to open either gate.
