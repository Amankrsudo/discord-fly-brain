**Table R-2.** Admissible native MN5 electrophysiological measurements (SAFE bucket of `model_input_freeze.csv`) with provenance. Conflicts are preserved unresolved (see C-01) [C-301, C-302, C-303].

| Parameter | Value (n) | Unit | Source | Provenance | Claim |
|---|---|---|---|---|---|
| MN5 resting potential | −67.8 ± 5.5 SD (n=13) | mV | Ryglewski, Kilo & Duch 2014 | `native_experimental_measurement` | [C-301] |
| MN5 spike threshold | −24.1 ± 8.2 SD (n=11) | mV | Ryglewski, Kilo & Duch 2014 | `native_experimental_measurement` | [C-301] |
| MN5 action potential amplitude | +45.5 ± 8.6 SD (n=13) | mV | Ryglewski, Kilo & Duch 2014 | `native_experimental_measurement` | [C-301] |
| MN5 action potential time to peak | 1.20 ± 0.33 (n=13) | ms | Ryglewski, Kilo & Duch 2014 | `native_experimental_measurement` | [C-301] |
| MN5 AP 50% width | 0.92 ± 0.25 (n=13) | ms | Ryglewski, Kilo & Duch 2014 | `native_experimental_measurement` | [C-301] |
| MN5 input resistance (set 1) | 102 ± 12 (n=22) | MOhm | Fayyazuddin et al. 2006 | `native_experimental_measurement` | [C-302] |
| MN5 input resistance (set 2) | 97 ± 31 (n=52) | MOhm | Ryglewski, Kilo & Duch 2014 | `native_experimental_measurement` | [C-302] |

**Conflict C-01 (capacitance, unresolved) — both retained, no winner chosen [C-303]**:

| Parameter | Variant A | Variant B | Provenance |
|---|---|---|---|
| MN5 whole-cell capacitance (variant A) | 43 +/- 2 (n=22) | — | native_experimental_measurement (contested) |
| MN5 whole-cell capacitance (variant B) | 127 +/- 16 SD (n not stated) | — | native_experimental_measurement (contested) |
| MN5 whole-cell capacitance (Ryglewski & Duch 2009) | — | 127 ± 16 | native_experimental_measurement (contested) |

- **Source**: `C:\Users\shreya\discord-fly-brain\research\model_input_freeze.csv` (sha256: ca007050f8bfc285…)
- **Caveat**: the 4.71 ± 0.35 mV somatic EPSP (n=10) was recorded under GF stimulation and is a comparison target only, not a PSI-specific measurement [C-304].