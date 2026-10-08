# Raw Data Availability Registry

Purpose: so nobody re-asks whether raw traces exist.

| Experiment | Raw data? | Format | Public? | Directly usable? | Location | Notes |
|---|---|---|---|---|---|---|
| Fayyazuddin 2006 — MN5 somatic physiology | **NO** | — | No | — | *PLoS Biol* 4(3):e63 | Cm 43±2 pF (n=22), Rin 102±12 MΩ (n=22), EPSP 4.71±0.35 mV (n=10). Traces not deposited. |
| Ryglewski & Duch 2009 — MN5 Cm + passive model | **NO** | — | No | — | PMID 19828724 | Cm 127±16 pF. Passive params adopted from *Manduca*. No deposit. |
| Kuehn & Duch 2013 — SIZ immunolabel | **NO** | — | No | — | PMCID PMC3604049 | No data-availability statement. **Reconstruction never deposited** (Zenodo/Dryad/Figshare/GitHub/ModelDB all searched). |
| Ryglewski et al. 2017 — 30 MN5 reconstructions | **NO** | — | No | — | *eLife* 6:e25690 | No linked dataset. |
| von Hoff & Duch 2010 — 30 MN5 morphologies | **NO** | — | No | — | — | 6,716±731 µm, 4,000±577 branches, about 0.44 µm average dendritic diameter (primary text; PMID 20437522, PMCID PMC4441823). |
| Augustin 2019 — GFS latency | **PARTIAL** | supplementary CSV | Yes | Yes (inverted triangles) | *eNeuro* 6(2), PMID 31001574, S1 Table | n=8–9 per condition. **Model code IS public (ModelDB 245415).** Latency 1.44 ms young / 1.85 ms old at 25 °C. |
| Orr 2014 — GF→TTMn plaque fraction | **PARTIAL** | table in open PDF | Yes | Yes | *J Neurosci* 34(16):5416 | Table 2 in the OA PDF. ShakB 14.72±3.99 % (n=9). |
| Hürkey 2023 — MN1–4 coupling | **PARTIAL** | — | Unclear | Values in text only | *Nature* 618:118–125 | CC 0.023±0.003 (6 pairs), 0.01±0.0027 (10 pairs). **No MN1→MN5 CC.** |
| Phelan 2008 — ShakB biophysics | **NO** | — | **INACCESSIBLE** | — | *Curr Biol* 18(22):1440 | Rectifier 0.21 in **Tables S1–S3, not retrievable**. Absolute Gj is the missing number. |
| Yang 2016 — in vivo arbor voltage | **NO** | — | Unclear | — | PMCID PMC5606228 | ASAP2f imaging in Mi1/Tm3/Tm1. |
| Fayyazuddin gfA1 / gfA2 mutants | **NO** | — | No | — | same | 1.5±0.32 mV (n=7) in gfA1. |

## Deposited datasets — fully reusable

| Dataset | Raw? | Format | Public? | Usable? | Location |
|---|---|---|---|---|---|
| **MaleCNS v1.0 connectome** | **YES** | feather / SWC / ngmesh / precomputed | Yes, CC-BY, unauthenticated | **Yes** | `gs://flyem-male-cns/v1.0/` · https://male-cns.janelia.org |
| MN5 meshes (801970, 801295) | YES | `.ngmesh` binary | Yes | Yes | `…/v1.0/segmentation/…` — SHA-256 recorded in `anatomy_registry.md` |
| MN5 skeletons | YES | SWC, 8 nm units | Yes | Yes | `…/segmentation/skeletons-malecns/skeletons-swc/` |
| MN5 skeletons (mirrored) | YES | SWC | Yes | **No** — different transform | `…/skeletons-malecns-mirrored/` |
| MN5 skeletons (unisex atlas) | YES | SWC, **1 µm** units | Yes | Cross-dataset only | `…/skeletons-unisex-template/` |
| **Per-synapse compartment labels** | YES | neuroglancer precomputed | Yes | **YES — highest-value unexploited dataset** | `gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed/` |
| FlyWire→MaleCNS meshes | YES | neuroglancer mesh | Yes | Yes | `gs://flyem-male-cns/flywire2mcns_meshes/` |
| hemibrain v1.2→MaleCNS meshes | YES | neuroglancer mesh | Yes | Yes | `gs://flyem-male-cns/hemibrain2mcns_meshes/v1.2` |
| neuPrint neo4j DB | YES | neo4j dump + CSVs | Yes | Yes (large) | `…/v1.0/database/{neo4j,neuprint-inputs}` |
| Paper-derived tables (15 files) | YES | csv/feather/parquet/xlsx | Yes | Yes | https://github.com/flyconnectome/2025malecns |
| FlyWire skeletons + NBLAST | YES | — | Yes | Yes | Zenodo **10877326** |
| FlyWire synapses + edge list | YES | — | Yes | Yes | Zenodo **10676866** |

## Known-broken / unusable

| Artefact | Problem |
|---|---|
| `syn-points-male-cns-v1.0-minconf-0.5.feather` | **Truncated download** — expects 1,330,795,073 metadata bytes, reads 1,081,555,701. Unusable. |
| `body_ann.feather` | Duplicate of `body-annotations-…feather` |
| `flyem_cns_z0720_07m_dvidcoords_n5` | Requires `tensorstore` — not installed in this environment |

## Not a data deposit — do not cite as one

- **ModelDB 245415** is a *model*, not an MN5 morphology deposit.
- `looming_abstraction.py:2095`'s "134 µS" — traced to no source.
