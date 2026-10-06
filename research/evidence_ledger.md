# Evidence Ledger — Fly Brain GFS / PSI→MN5

Provenance classes (exactly five, never converted without evidence):
`NEM` Native experimental measurement · `AM` Anatomical measurement ·
`LDP` Literature-derived passive parameter · `MA` Model assumption ·
`MDE` Model-derived estimate.

Evidence strength: **STRONG** (primary, directly measured in the object of
interest) · **MODERATE** (primary but indirect / different preparation / different
species) · **WEAK** (estimated, adopted, or convention-dependent) ·
**NONE** (no qualifying measurement exists).

Direct/Indirect: **D** = measures the named quantity directly · **I** = inferred.
Measured/Modelled: **M** / **Mo**.

---

| ID | Claim | Exact value | Unit | Object | Source | Type | Prov | Strength | D/I | M/Mo | Repro | Conflicts | Dep | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-001 | MN5 whole-cell capacitance | 43 ± 2 (n=22) | pF | Drosophila MN5 | Fayyazuddin+ 2006 PLoS Biol 4:e63 | EXPERIMENT | NEM | MODERATE | D | M | No | **C-01** | M-09 | CONFLICTED | Whole-cell, somatic |
| E-002 | MN5 whole-cell capacitance | 127 ± 16 (SD) | pF | Drosophila MN5 | Ryglewski & Duch 2009 J Neurophysiol 102:3673 | EXPERIMENT | NEM | MODERATE | D | M | No | **C-01** | M-09 | CONFLICTED | ~2.95× E-001 |
| E-003 | MN5 input resistance | 102 ± 12 (n=22) | MΩ | Drosophila MN5 | Fayyazuddin+ 2006 | EXPERIMENT | NEM | MODERATE | D | M | No | — | M-09 | OPEN | |
| E-004 | MN5 somatic EPSP under GF stimulation | 4.71 ± 0.35 (n=10) | mV | Drosophila MN5 | Fayyazuddin+ 2006 | EXPERIMENT | NEM | MODERATE | D | M | No | — | M-02 | OPEN | Distal amplitude **not** reported → no attenuation derivable |
| E-005 | EPSP in gfA1 | 1.5 ± 0.32 (n=7) | mV | Drosophila MN5 | Fayyazuddin+ 2006 | EXPERIMENT | NEM | MODERATE | D | M | No | — | M-02 | OPEN | |
| E-006 | GF→MN5 latency, young | 1.44 | ms | GFS | Augustin+ 2019 eNeuro, Table 1 | EXPERIMENT | NEM | STRONG | D | M | Yes (suppl.) | — | — | OPEN | 5–7 d, 25 °C, n=8–9 |
| E-007 | GF→MN5 latency, old | 1.85 | ms | GFS | Augustin+ 2019 | EXPERIMENT | NEM | STRONG | D | M | Yes (suppl.) | — | — | OPEN | 45–50 d |
| E-008 | GF→TTMn latency WT | 0.93 | ms | GFS | Augustin+ 2019 | EXPERIMENT | NEM | STRONG | D | M | Yes | — | — | OPEN | |
| E-009 | GF gap-junction conductance | **NO MEASUREMENT** | — | GF→PSI, GF→TTMn | — | — | — | **NONE** | — | — | — | — | M-01 | **MISSING** | Only oocyte rectifier index 0.21 |
| E-010 | MN1–MN2 / MN3–MN4 coupling coefficient | 0.023 ± 0.003 SEM (6 pairs) | — | Drosophila MN1–4 | Hürkey+ 2023 Nature 618:118 | EXPERIMENT | NEM | STRONG | D | M | Unclear | — | — | OPEN | **Not MN1→MN5** |
| E-011 | Other MN1–4 CC | 0.01 ± 0.0027 (10 pairs) | — | Drosophila MN1–4 | Hürkey+ 2023 | EXPERIMENT | NEM | STRONG | D | M | Unclear | — | — | OPEN | |
| E-012 | MN1→MN5 coupling coefficient | **NOT REPORTED** | — | Drosophila MN1→MN5 | Hürkey+ 2023 | — | — | **NONE** | — | — | — | **C-12** | M-05 | **MISSING** | Only MN4–MN5 sync index 0.56 (n=11) |
| E-013 | ShakB occupies GF terminal | 14.72 ± 3.99 SD (n=9) | % vol | GF→TTMn | Orr+ 2014 J Neurosci 34:5416 | EXPERIMENT | NEM | STRONG | D | M | Yes (Table 2) | — | — | OPEN | *fra* LOF 3.00±0.57; *Netrin* LOF 1.54±0.48 |
| E-014 | GF→PSI does not age-decline in ShakB | qualitative | — | GF→PSI | Auger+ 2020 PLoS ONE 15:e0224057 | EXPERIMENT | NEM | STRONG | D | M | No | — | — | OPEN | Age decline is GF→TTMn-**specific** |
| E-015 | MN5 dendritic length | 6716 ± 731 (n=30) | µm | Drosophila MN5 | von Hoff & Duch 2010; re-cited Ryglewski+ eLife 2017 | EXPERIMENT | AM | MODERATE | D | M | No | **C-07** | — | OPEN | Literature, **not** MaleCNS |
| E-016 | MN5 dendritic branch count | 4000 ± 577 (n=30) | — | Drosophila MN5 | von Hoff & Duch 2010 | EXPERIMENT | AM | MODERATE | D | M | No | — | — | OPEN | |
| E-017 | MN5 mean dendritic diameter | ≈0.88 | µm | Drosophila MN5 | von Hoff & Duch 2010 | EXPERIMENT | AM | MODERATE | D | M | No | — | M-09 | OPEN | MaleCNS kind=0 median 0.512 µm — same order, not a validation |
| E-018 | MN5 process length (MaleCNS) | 7453.5 / 7190.2 | µm | 801970 / 801295 | MaleCNS `em_*.swc` | DATASET | AM | STRONG | D | M | Yes | **C-07** | — | VERIFIED | Total cable, **not** dendritic |
| E-019 | MN5 mesh surface area | 18725.6 / 19665.4 | µm² | 801970 / 801295 | MaleCNS `.ngmesh` | DATASET | AM | STRONG | D | M | Yes | — | — | VERIFIED | Cross product; Heron agrees to 2e-16 |
| E-020 | MN5 mesh components | 2587 / 2765 | count | 801970 / 801295 | MaleCNS | DATASET | AM | STRONG | D | M | Yes | — | — | VERIFIED | Largest 2.8 % / 2.3 %. **Not** biological compartments |
| E-021 | MN5 mesh is not a closed surface | 462426 / 495569 boundary edges | count | 801970 / 801295 | MaleCNS | DATASET | AM | STRONG | D | M | Yes | — | — | VERIFIED | neuPrint attributes fragmentation to segmentation artefacts |
| E-022 | PSI→MN5 contacts (MaleCNS v1.0, minconf 0.5) | 17 + 26 = 43 | count | 802401→801970; 903327→801295 | MaleCNS syn-partners | DATASET | AM | STRONG | D | M | Yes | — | — | VERIFIED | 0 cross-pairings |
| E-023 | contact → surface distance | 1.67–80.22 (min–max over 43) | nm | all 43 contacts | MaleCNS + mesh | DATASET | AM | STRONG | D | M | Yes | — | — | VERIFIED | Body medians 35.17 / 26.97 |
| E-024 | contact → SWC-root path | 169.2–267.8 | µm | all 43 | MaleCNS | DATASET | MDE | STRONG | I | Mo | Yes | — | M-02 | VERIFIED | **Root is not the soma** |
| E-025 | contact → somaLocation straight line | 110.3–172.9 | µm | all 43 | MaleCNS | DATASET | AM | STRONG | D | M | Yes | — | M-02 | VERIFIED | **Not a path length** |
| E-026 | contact → soma-label graph path | **UNRESOLVED** | — | all 43 | — | — | — | **NONE** | — | — | — | — | M-07 | **MISSING** | Zero `kind=1` nodes in any skeleton |
| E-027 | contact → soma-proxy tree path | 154.1–241.6 | µm | all 43 | MaleCNS | DATASET | MDE | MODERATE | I | Mo | Yes | — | M-07 | PARTIAL | Rests on a `MA` proxy |
| E-028 | soma-region proxy node radius | 4.671 / 5.376 | µm | 801970 / 801295 | MaleCNS + annotations | DATASET | AM | STRONG | D | M | Yes | — | M-07 | VERIFIED | 2.10 / 1.45 µm from `somaLocation` |
| E-029 | SIZ = spike initiating zone | — | — | Drosophila MN5 | Kuehn & Duch 2013 PMC3604049 | EXPERIMENT | AM | STRONG | D | M | — | **C-11** | M-08 | CORRECTED | **Not** "Secondary Isatoz Axon" |
| E-030 | SIZ distance from soma | ≈100 | µm | Drosophila MN5 | Kuehn & Duch 2013 | EXPERIMENT | AM | MODERATE | D | M | No | **C-11** | M-08 | VERIFIED | "about 100 µm"; no numeric uncertainty given |
| E-031 | SIZ localisation from dendrite origin | 11 ± 3 (n=7) | µm | Drosophila MN5 | Kuehn & Duch 2013 | EXPERIMENT | AM | MODERATE | D | M | No | **C-11** | M-08 | VERIFIED | SD-vs-SEM unstated. **Different reference point** from E-030 |
| E-032 | MN5 spatial voltage transfer | **NO MEASUREMENT** | — | Drosophila MN5 | — | — | — | **NONE** | — | — | — | — | **M-02** | **MISSING** | Only a simulation on Manduca Ra/Cm |
| E-033 | MN5 contact→soma current-transfer map | 0.2–1 | ratio | Drosophila MN5 | Ryglewski & Duch 2009 Fig 1B | MODEL | MDE | WEAK | I | Mo | Yes | — | M-02 | **MODEL ONLY** | Authors disclaim exactness |
| E-034 | MN5 passive Ra in the only MN5 model | 90 | Ω·cm | *Manduca* adopted for Drosophila MN5 | Ryglewski & Duch 2009 citing Meseke+ 2009 | — | LDP | **WEAK** | I | Mo | — | **C-10** | **M-03** | **NOT DROSOPHILA** | Species mismatch |
| E-035 | MN5 passive Cm in that model | 1.15e-6 | F·cm⁻² | *Manduca* adopted | Ryglewski & Duch 2009 citing Meseke+ 2009 | — | LDP | **WEAK** | I | Mo | — | **C-10** | M-03 | **NOT DROSOPHILA** | |
| E-036 | GFS gap-junction conductance (paper) | 135 / 34.5 | µS | GFS | Augustin+ 2019 Table 1 | MODEL | MA | **WEAK** | I | Mo | Yes | **C-02** | — | ESTIMATED | Explicitly "(estimated)" |
| E-037 | GFS gap-junction conductance (executed) | 135 / 34.5 | **nS** | GFS | ModelDB 245415 `gap2.mod:12` | CODE | MA | **WEAK** | I | Mo | Yes | **C-02** | — | ESTIMATED | Exactly 1000× |
| E-038 | PSI→DLMn chemical peak (paper) | 80 | µS | PSI→DLMn | Augustin+ 2019 Table 1 | MODEL | MA | **WEAK** | I | Mo | Yes | **C-03** | **M-01** | ESTIMATED | Explicitly "(estimated)" |
| E-039 | PSI→DLMn chemical peak (executed) | 0.08 | µS | PSI→DLMn | ModelDB 245415 `gfpn.py:52` | CODE | MA | **WEAK** | I | Mo | Yes | **C-03** | **M-01** | ESTIMATED | Exactly 1000× |
| E-040 | Ra / Cm in ModelDB 245415 | 35.4 / 1.0 | Ω·cm / µF·cm⁻² | GFS model | NEURON defaults — **never assigned** | CODE | MA | **NONE** | I | Mo | — | **C-06** | M-03 | **NOT SET** | Numerically equal to Table 1's "estimated" entries |
| E-041 | MN1→MN5 latency | **NOT REPORTED** | — | MN1→MN5 | — | — | — | **NONE** | — | — | — | C-12 | M-05 | MISSING | |
| E-042 | MN5 dendritic/axonal length split | **NO QUALIFYING MEASUREMENT** | — | Drosophila MN5 | — | — | — | **NONE** | — | — | — | — | **M-06** | **MISSING** | 93 % of MaleCNS arbor is `kind=0` undefined |
| E-043 | MaleCNS SWC `kind` biology | **UNDEFINED IN AVAILABLE SOURCE** | — | MaleCNS | — | SCHEMA | — | **NONE** | — | — | — | **C-08** | M-06 | MISSING | Format codes only; reader discards `node_type` |
| E-044 | SIZ registration to MaleCNS | **UNRESOLVED** | — | Drosophila MN5 | — | — | — | **NONE** | — | — | — | — | M-08 | MISSING | No deposit, no axis, no transform |
| E-045 | Anatomical voltage decay along an arbor | qualitative decay | — | Drosophila Mi1/Tm3 | Yang+ 2016 Cell 166:245 | EXPERIMENT | NEM | MODERATE | D | M | No | — | M-02 | OPEN | **Not MN5**; method precedent only |
| E-046 | **CLAIM A** — MaleCNS v1.0 assigns `compartment_post='axon'` to all 43 verified PSI→MN5 contacts | axon ×43 (17 on 801970, 26 on 801295) | enum label | 802401→801970; 903327→801295 | MaleCNS v1.0 synapse layer `gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed` | DATASET | AM | STRONG | D | M | Yes | — | **M-06** | **VERIFIED** | Connectomic **dataset annotation**, not an electrophysiological measurement. Missing 0, ambiguous 0, unknown 0. Artifact: `research/artifacts/malecns_compartment_post_psi_mn5.csv` |
| E-047 | **CLAIM B** — PSI→MN5 contacts are exclusively in the axonal compartment per the official annotation | 43/43 axon, vs MN5-wide 4.3 %/21.2 % axon | fraction | MN5 801970 / 801295 | MaleCNS v1.0 synapse layer | DATASET | AM | STRONG | D | M | Yes | — | M-06, M-02 | **VERIFIED** | MN5-wide: 801970 452 axon / 9713 dendrite / 364 cell-body-fiber; 801295 2384 axon / 8787 dendrite / 89 linker. `compartment_pre` axon ×38, unknown ×5 (all on 801295). **Consistent with** Fayyazuddin 2006 "PSI bypasses the entire dendritic structure of MN5" |
| E-048 | **CLAIM C** — the `compartment_post` result does **not** establish spatial voltage transfer | — | — | MN5 | methodological limitation | — | — | **NONE** | — | — | — | — | **M-02** | **UNRESOLVED** | A compartment **string** is not a distance and not a voltage. No Ra/Rm/Cm/length-constant/attenuation/transfer quantity is computed or implied anywhere. Gate remains closed |
| E-049 | **CLAIM D** — SWC `kind=2` remains semantically unresolved for MaleCNS | UNDEFINED IN AVAILABLE SOURCE | — | MaleCNS MN5/PSI | MaleCNS download page cites PMC10654402 for *format* only; neuprint discards `node_type` | SCHEMA | — | **NONE** | — | — | — | **C-08** | **M-06** | **UNRESOLVED** | E-046 does **not** retroactively validate `kind`. Different column, different provenance. Descriptive annotation concordance is reported in `mn5_compartment_post_swc_type_concordance.md`; it does not resolve Type-code biology |
| E-050 | **CLAIM E** — per-neuron cut-node artifact remains unreleased; M-06 resolved only in per-synapse form | 0 cut-node artifacts found | count | MaleCNS v1.0 | 6 locations enumerated with `truncated:false` (2025malecns, flyconnectome/malecns, flyem-male-cns bucket, neuprint-inputs, flywire_annotations, layer info) | DATASET | AM | STRONG | D | M | Yes | — | M-06 | **RESOLVED WITH SCOPE LIMITATION** | M-06 resolved as *per-synapse labels for every contact*; the per-neuron cut node is still unreleased |

---

## Ledger statistics

| Metric | Count |
|---|---|
| Rows | 50 |
| Sources classified | 17 (S-01…S-17) |
| Verified / STRONG | 16 |
| Conflicted | 4 (E-001, E-002, E-018/E-036–E-040 family) |
| **Unresolved / MISSING (no qualifying measurement)** | **12** |
| Distinct conflicts registered | 12 (C-01…C-12) |
| Raw datasets found, public & usable | 12 (added the MaleCNS synapse annotation layer) |
| Raw datasets found but unusable | 1 (truncated `syn-points`) |
| Experiments with **no** raw data | 9 of 11 |
| Conflicts **resolved** tonight | 5 (C-05, C-06, C-07, C-09, C-10, C-11) |
| Conflicts **still unresolved** | 7 |

**No row was promoted between provenance classes.** E-034/E-035 remain `LDP`
and flagged as non-Drosophila rather than being silently reclassified.
