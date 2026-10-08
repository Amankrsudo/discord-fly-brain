# Anatomical Data Map — MN5 / PSI in MaleCNS v1.0

All values independently verified against the released files during 3.0D-8Q / 8R / 8T.
Official per-synapse `compartment_post` retrieved 3.0D-8V.

## Scientific gate status — recorded at the head of the anatomy chain

**PSI→MN5 spatial voltage transfer: NOT AUTHORIZED**
**Dα7 conductance: NOT AUTHORIZED**

This map is **anatomical and connectomic only**. Nothing in it is, or licenses, an
electrical quantity. Specifically, the entries below do **not** yield, and must
never be used to compute: Ra, Rm, Cm, g_pas, specific membrane capacitance or
resistance, length or space constant, electrotonic distance, cable distance,
attenuation, transfer resistance, voltage transfer, synaptic conductance, or
Dα7 conductance. A compartment **label** is not a distance and not a voltage.
See `research/final_anatomy_audit.md` §L for the exact boundary.

---

## Coordinate frame (single authority)

| Fact | Value | Provenance |
|---|---|---|
| Voxel / EM resolution | 8 nm isotropic | `AM` |
| SWC coordinates | **raw 8 nm units** | `AM` |
| `.ngmesh` coordinates | **nanometres** | `AM` |
| Conversion | **`mesh_nm = swc_raw × 8`** | `AM` |
| Synapse coordinates | **raw 8 nm units** (same frame as SWC) | `AM` |
| Mirrored SWC variants | a **different transform** (`navis-flybrains`) — never substituted | `AM` |

The mirrored variants (`801970.swc`, `801295.swc`) are node-for-node identical
in kind and radius but differ in coordinates. Substituting them changes
root↔soma from 23.76/14.88 µm to **117.88/118.84 µm** — a 5× error. The existing
`FRAME_MIRRORED_1NM` guard prevents this.

---

## A-01 · 801970 — MN5 / DLMn a,b, **left**

| Field | Value |
|---|---|
| Body ID | **801970** |
| Cell type | `DLMn a, b` · superclass `wm` (white matter) · `subclass` `wm` |
| VFB ID | `VFB_jrmc37jr` |
| Group | 801295 (shared with the right-hand body) |
| somaSide / somaNeuromere | `L` / `T2` |
| exitNerve | `PDMNa` |
| somaLocation (raw 8 nm) | (56099, 46256, 81781) → **448792, 370048, 654248 nm** |
| Annotation status | `Traced` |
| SWC | `em_801970.swc` — 8520 nodes, single root (idx 1), kinds **{0: 8075, 2: 445}** |
| Process length | **7453.5 µm** |
| kind=0 / kind=2 cable | 6929.7 µm (93.0 %) / 523.9 µm (7.0 %) |
| Radius range | kind=0 0.256–3.328 µm (median **0.256** = global floor) · kind=2 0.256–**4.671** µm (median 0.718) |
| Mesh | `mesh_801970.ngmesh` — 687,842 verts, 913,134 faces, 19,211,716 B |
| SHA-256 | `034dffd0009e48fa65868124724b1fd1394a8aca2b7ec73306aa443697c35057` |
| Mesh surface area | **18,725.6 µm²** (cross product; Heron agrees to 2e-16 rel) |
| Mesh bbox extent | 183.9 × 68.5 × 114.1 µm |
| Mesh topology | 462,426 boundary edges, 2,238 non-manifold, 807 duplicate faces; χ = V−E+F = 2300 |
| Components | **2,587**; largest = **2.8 %** of area |
| Mesh edge p50 / p95 | 198.4 / 508.5 nm |
| **Soma node** | **NONE** (zero `kind=1`) |
| Root kind | **0**, radius 0.256 µm |
| Root ↔ somaLocation | **23.76 µm** |
| Soma-region proxy | node **23**, `kind=2`, radius **4.671 µm**, **2.10 µm** from somaLocation, 26.24 µm along tree from root |
| somaLocation → mesh surface | **3.87 µm** (inside the mesh bbox) |
| PSI presynaptic partner | **802401** (PSI L) — **17** contacts, no cross-pairing |

## A-02 · 801295 — MN5 / DLMn a,b, **right**

Identical structure; differing values:

| Field | Value |
|---|---|
| VFB ID | `VFB_jrmc37js` · group 801295 · somaSide `R` · neuromere `T2` · exitNerve `PDMNa` |
| somaLocation (raw) | (43450, 45480, 81574) → **347600, 363840, 652592 nm** |
| SWC | `em_801295.swc` — 7991 nodes, root idx 1, kinds **{0: 7540, 2: 451}** |
| Process length | **7190.2 µm** |
| kind=0 / kind=2 cable | 6657.0 µm (92.6 %) / 533.2 µm (7.4 %) |
| Radius range | kind=0 0.256–4.890 µm · kind=2 0.256–**5.376** µm (median 0.743) |
| Proximal block | nodes 5–9 all `kind=2`, radius **5.376 µm** — contiguous |
| Mesh | `mesh_801295.ngmesh` — 726,682 verts, 957,519 faces, 20,210,416 B |
| SHA-256 | `0715bfb28230e79eaa9a2ae932f266f10e9c4a7cdeae3fed06ca24f4a2420913` |
| Mesh surface area | **19,665.4 µm²** |
| Mesh bbox extent | 182.7 × 63.5 × 101.1 µm |
| Mesh topology | 495,569 boundary, 2,267 non-manifold, 873 duplicate faces; χ = 2406 |
| Components | **2,765**; largest = **2.3 %** |
| Mesh edge p50 / p95 | 197.7 / 510.7 nm |
| **Soma node** | **NONE** |
| Root ↔ somaLocation | **14.88 µm** |
| Soma-region proxy | node **8**, `kind=2`, radius **5.376 µm**, **1.45 µm** from somaLocation, 15.05 µm from root |
| somaLocation → mesh surface | **3.50 µm** |
| PSI partner | **903327** (PSI R) — **26** contacts = **19 PDMN(L) + 7 WTct(UTct-T2)(L)** |

## A-03 · 802401 — PSI left

`em_802401.swc`: 1545 nodes, kinds {0: 1444, 2: 101}, cable 1781.4 µm
(89.6 % kind=0). No soma node. **17** postsynaptic contacts onto 801970.

## A-04 · 903327 — PSI right

`em_903327.swc`: 1501 nodes, kinds {0: 1402, 2: 99}, cable 1726.5 µm
(90.3 % kind=0). No soma node. **26** postsynaptic contacts onto 801295.

## A-05 · Other MN5 candidate reconstructions

| File | Nodes | Kinds | Verdict |
|---|---|---|---|
| `801970.swc`, `801295.swc` | 8520 / 7991 | {0,2} | **Mirrored** transform of the `em_` files. Not substitutable. |
| `mn5.swc` | 1977 | **all 2** | Different frame entirely (coords ~603424, root radius 3.776 µm, 58,113 µm cable). **Not established as the same biological object.** Not used. |
| Kuehn & Duch 2013 reconstruction | — | — | **Not deposited.** No accession anywhere. |
| Ryglewski eLife 2017 (30 reconstructions) | — | — | **Not deposited.** |
| ModelDB 245415 | — | — | A simplified 4-cell GFS model, **not** an MN5 morphology deposit. |
| FlyWire / hemibrain MN5 meshes | — | — | Transformed **meshes** only (`flywire2mcns_meshes`, `hemibrain2mcns_meshes`), no SWC, no soma label. |

---

## Compartment information — what exists and what does not

**RETRIEVED 2026-10-05 (3.0D-8V).** The official MaleCNS v1.0 per-synapse
`compartment_post` annotation was retrieved for **all 43** verified PSI→MN5
contacts. See `research/artifacts/malecns_compartment_post_psi_mn5.csv` and
`research/final_anatomy_audit.md`.

### Official `compartment_post` for the 43 verified contacts

| pairing | contacts | `compartment_post` |
|---|---|---|
| 802401 → 801970 (PSI L → MN5 L) | 17 | **axon ×17** |
| 903327 → 801295 (PSI R → MN5 R) | 26 | **axon ×26** |
| **total** | **43** | **axon ×43** |

Missing: **0**. Ambiguous: **0**. Unknown post-compartment labels: **0**.
`compartment_pre`: axon ×38, unknown ×5 — **all 5 on 801295**, preserved as-is.

By contact class: PDMN 36 → axon; WTct 7 → axon. **The compartment label is not
confounded with contact class**, so no class-based inference was possible or used.

### For contrast — the same field across ALL of MN5's input

| body | total synapses | axon | dendrite | linker | cell-body-fiber |
|---|---|---|---|---|---|
| 801970 | 10,529 | 452 (4.3 %) | 9,713 (92.2 %) | — | 364 (3.5 %) |
| 801295 | 11,260 | 2,384 (21.2 %) | 8,787 (78.0 %) | 89 (0.8 %) | — |

For the 43 PSI→MN5 contacts, the literal official MaleCNS
`compartment_post` annotation is `axon` in every record. This is an annotation
result only; it does not establish biological axonal localization or
compartment semantics. The whole-input counts below are likewise official
dataset labels, not a biological compartment validation. Independently
consistent with Fayyazuddin+ 2006:
*"the PSI bypasses the entire dendritic structure of MN5 and makes multiple
synaptic contacts that span 50 μm and follow the axons out into the posterior
dorsal motor nerve."*

Note the asymmetry: **`cell-body-fiber` synapses exist on 801970 (364) but not on
801295.** The source's enum contains a category the project's soma-proxy work
had not considered.

### Source layer

`gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed`
(`neuroglancer_annotations_v1`, CC-BY, unauthenticated). Official enum read from
the layer's own `info`: `["unknown","axon","dendrite","linker","cell-body-fiber"]`.
Matching rule: exact integer equality of the post-synaptic coordinate within the
`body_post` relationship shard; any non-unique match raises.

### What the compartment table does NOT provide

| Source | Axon/dendrite info | Cut node / cut point | Soma node |
|---|---|---|---|
| MaleCNS SWC skeletons | `kind=2` on 5.2–5.6 % of nodes — **format code only, biology undocumented** | **NO** | **NO** |
| **MaleCNS synapse layer** | **YES — per-synapse, retrieved for all 43** | **NO** (per-synapse labels only) | n/a |
| neuPrint `male-cns:v1.0` | reader **discards** `node_type` | **NO** | not exposed |
| `flyconnectome/2025malecns` | **NO** | **NO** | — |
| FlyWire annotations | **NO** | **NO** | — |
| `flyem-male-cns` bucket (full enumeration) | synapse layer only | **NO** | **NO** |

**Conclusions held separate.** The published flow-centrality split is recoverable
**per synapse**, not as a per-neuron cut node or subtree. No cut-point artifact
exists in any public MaleCNS release.

**⚠ The `compartment_post` result does NOT resolve the SWC `kind=2` question.**
They are different columns with different provenance. A descriptive annotation
concordance comparison has now been performed (see
`mn5_compartment_post_swc_type_concordance.md`). It does not assign biological
meaning to either column, and the `kind` column's biology remains
**UNDEFINED IN AVAILABLE SOURCE** (see `conflicts.md` C-08).

**Do not** substitute SWC `kind` for this. **Do not** use the third-party
`YijieYin/connectome_data_prep` recompile: its `manual_split.py` sets every
motor-neuron synapse to `'dendrite'` by fiat.

---

## Contact → path results (all `AM` / `MDE`, none electrical)

| Quantity | 801970 | 801295 | Provenance |
|---|---|---|---|
| Contacts | 17 | 26 | `AM` |
| contact → surface | min 8.55, med 35.17, mean 31.76, max 51.70 nm | min 1.67, med 26.97, mean 31.91, max 80.22 nm | `AM` |
| Component verdict | 14 CONFIDENT / 3 **AMBIGUOUS** / 0 too-distant | 26 CONFIDENT / 0 / 0 | `AM` + convention |
| contact depth from root | 184.0–267.8 µm | 169.2–230.6 µm | `AM` |
| contact → SWC-root path | 184.0 / 234.4 / 267.8 µm | 169.2 / 177.6 / 230.6 µm | `MDE` (projection step) |
| contact → somaLocation straight line | 110.3 / 157.9 / 172.9 µm | 112.3 / 127.6 / 169.3 µm | `AM` |
| **contact → soma-label graph path** | **UNRESOLVED** | **UNRESOLVED** | no soma node exists |
| contact → soma-**proxy** tree path | 157.8 / 208.1 / 241.6 µm | 154.1 / 162.6 / 215.6 µm | `MDE` on a `MA` proxy |
| Distinct projected SWC nodes | 11 (5 shared) | 14 (9 shared) | `AM` |
| Contacts in literature SIZ band | 0 | 0 | — |

---

## Known missing / unreliable anatomy

1. **No soma node** in any of the 9 MN5/PSI skeletons. Zero `kind=1`.
2. **`kind` semantics undocumented** by MaleCNS (see `conflicts.md` C-08).
3. **Meshes are not closed surfaces** — 29 % of distinct edges are boundary;
   thousands of open fragments. Never described as watertight.
4. **Mesh fragmentation is a segmentation artefact**, corroborated by neuPrint:
   skeletons *"consist of multiple fragments … due to artifacts in the
   underlying segmentation from which the skeletons were generated."*
5. **Stored SWC root significance is not guaranteed** — neuPrint: *"the root
   node … is not particularly significant, so the directionality of the nodes …
   is arbitrary."* The project's root↔soma distance is a *measurement*, not a
   format property.
6. **Radius units are 8 nm, not µm** — a documented deviation from the SWC spec
   default. Inferred from plausibility (median 0.256 µm diameter 0.512 µm vs the
   literature mean dendritic diameter ≈0.44 µm); **not stated by MaleCNS**.
7. **`tosomaLocation` and `rootSide` exist as annotation columns but are
   `None`/`unpopulated`** for all four bodies.
8. **`syn-points-male-cns-v1.0-minconf-0.5.feather` is a truncated download**
   (expects 1,330,795,073 metadata bytes, reads 1,081,555,701). **Unusable.**
9. **No anterior/posterior axis documented anywhere** — not in annotations, not
   in the MaleCNS pages, not in this project. Blocks SIZ registration.
