# Model Input Audit — read-only

**Nothing in this file was modified.** Purpose: for every parameter entering any
Fly Brain model, record where it comes from and whether the implementation
matches the paper.

Audited: **ModelDB 245415**, the only GFS model found.
Repository: https://github.com/ModelDBRepository/245415
Tree SHA `feaebc4c3dfdd59f28152b0945fd5f5a1d1dcc7e`, verified `truncated:false` —
**8 files, nothing else:**

| Path | Bytes |
|---|---|
| `channels/gap2.mod` | 254 |
| `channels/k.mod` | 1223 |
| `channels/nap.mod` | 1245 |
| `channels/nat.mod` | 1589 |
| `gfpn.py` | 10010 |
| `gfs_param_scan_conductances.py` | 3667 |
| `readme` | 2015 |

Vendored byte-identically in this repo at
`biological_brain/data/modeldb_245415/`.

**ModelDB 245415 is a GFS model** — Augustin, Zylbertal & Partridge 2019
*eNeuro* 6(2):ENEURO.0423-18.2019, PMID 31001574.
(`modeldb.org/245415` returned a transport error; the GitHub mirror is
authoritative and matches on size.)

---

## A-01 · Structure

4 cells / 8 sections, 51 isopotential segments each — matches the paper
("comprised of four cells"; "Each section is divided into 51 iso-potential
segments").

| Section | Dimensions | Active mechanisms |
|---|---|---|
| `GF` | 8 µm × 400 µm | nat/nap/k + pas |
| `TTMn` | 6 µm × 50 µm | nat/nap/k + pas |
| `TTMn_med` | 6 µm × 60 µm | pas only |
| `TTMn_lat` | 6 µm × 30 µm | pas only |
| `PSI` | 4.5 µm × 90 µm | nat/nap/k + pas |
| `PSI_pas` | 4.5 µm × 170 µm (paper: *estimated*) | pas only |
| `DLMn` | 2→4 µm tapering × 50 µm | nat/nap/k + pas |
| `DLMn_pas` | 2 µm × 100 µm | pas only |

Mechanisms: distributed `nat`, `nap`, `k`, `pas`; point process `gap2` (1
nonspecific, **no state variables**); 3 × NEURON built-in `Exp2Syn`.
**There is no `pas.mod`** — `pas` is built-in.

---

## A-02 · Every parameter, its file value, and its source comment

**`gfpn.py` contains ZERO source comments on any parameter.** The only attribution
in the entire model is the copyright header. Attribution lives solely in the
paper's Table 1.

| Parameter | Value in file | Unit as executed | Source comment in file | Table 1 |
|---|---|---|---|---|
| `gleak` → `cell.g_pas` (L131, L139) | `30e-6` | S/cm² | **NONE** | "(estimated)" |
| `Eleak` → `cell.e_pas` | `-85.0` | mV | **NONE** | Günay 2015 |
| `gnatbar` | `300e-3` | S/cm² | **NONE** | Günay 2015 |
| `gnapbar` | `110e-6` | S/cm² | **NONE** | Günay 2015 |
| `gkbar` | `10e-3` | S/cm² | **NONE** | "(estimated)" |
| `ena` / `ek` | `65` / `-74` | mV | **NONE** | Günay 2015 |
| `g_gap` → `gap2.g` (L171, L175) | `135.0` | **nS** per `gap2.mod:12` | **NONE** | 135/34.5 **µS** "(estimated)" |
| `PSI_DLMn_wt` (L167) | `0.08` | µS per `Exp2Syn` | **NONE** | **80 µS** "(estimated)" |
| `GF_TTMn_wt` (L165) | `0.00` | µS | **NONE** | **no Table 1 row** |
| `GF_PSI_wt` (L166) | `0.00` | µS | **NONE** | **no Table 1 row** |
| `PSI_DLMn_delay` (L167) | `0.15` | ms | **NONE** | "(estimated)" |
| `GF_TTMn_delay` / `GF_PSI_delay` | `1` | ms | **NONE** | **no Table 1 row** |
| `*_syn_tau1/tau2/e` (L32–46) | 0.5/5.0/0; 0.1/5.0/0; 0.1/1.0/0 | ms/ms/mV | **NONE** | "standard value" ×3 |
| `temp` (L146) | `25.0` | °C | **NONE** | **no Table 1 row** |
| `stim_amp` / `stim_dur` / `stim_delay` | `120.0` / `0.03` / `100` | nA/ms/ms | **NONE** | Methods text |
| `muscle_delay` (L64) | `0.35` | ms | **NONE** | "see Materials and Methods" |

All 20: **NO SOURCE COMMENT IN FILE**. All anatomical lengths/diameters
(L17–29) likewise uncommented.

---

## A-03 · The critical negative result: Ra / Rm / Cm are never set

Exhaustive pattern search over all `*.py` and `*.mod` in the vendored tree for
`\bRa\b|\bRm\b|\bcm\b|\.Ra|\.Rm|\.cm|electroton|length_constant|attenuat|distance|lambda`
returned **exactly two hits**, both x-axis *labels*:

```
gfs_param_scan_conductances.py:77: plt.xlabel(param2 + ' (mS/cm^2)')
gfs_param_scan_conductances.py:98: plt.xlabel(param2 + ' (mS/cm^2)')
```

Therefore:

| Quantity | In the code? | Runtime value |
|---|---|---|
| `Ra` | **NEVER SET** | NEURON built-in default **35.4 Ω·cm** |
| `Rm` | **NEVER SET** (and not a NEURON variable; leak is `g_pas`) | — |
| `Cm` | **NEVER SET** | NEURON default **1 µF/cm²** |
| electrotonic distance / λ / attenuation / transfer resistance | **ABSENT** | — |

**Paper Table 1 lists "Specific axial resistance 35.4 Ω/cm (estimated)" and
"Specific membrane capacitance 1 µF/cm2 (estimated)" — numerically identical to
the NEURON defaults, which the code never assigns.** These two "estimated"
parameters are therefore **indistinguishable from simulator defaults** and must
never be cited as Table-1-derived measurements. Provenance: `MA` at best.

---

## A-04 · Does any code convert anatomy into electricity?

**(a) Electrotonic conversion: NO.** Zero occurrences of electrotonic distance,
length constant, attenuation or transfer resistance. No length ever enters Ra, Rm
or Cm. NEURON performs the cable solve internally from `diam`/`L` plus its own
defaults.

**(b) µm → dimensionless position: YES, and it is exact.** All contact sites are
normalised 0–1 section locations, each reconciling exactly with a Table-1 µm
value:

| Code | × section L | = | Table 1 row | Match |
|---|---|---|---|---|
| `TTMn_syn_post_loc = 0.2` × 60 | | 12 µm | "input from GF from medial dendrite proximal end 12 μm" | ✓ |
| `PSI_syn_post_loc = 0.5` × 90 | | 45 µm | "input from GF from PSI axon proximal end 45 μm" | ✓ |
| `GF_syn_pre_loc = 1.0` × 400 | | 400 µm | "contact with TTMn from proximal end 400 μm" | ✓ |
| `PSI_syn_pre_loc = 0.9` × 400 | | 360 µm | "contact with PSI from proximal end 360 μm" | ✓ |
| `DLMn_syn_pre_loc = 0.85` × 90 | | 76.5 µm | "contact with DLMn from PSI axon proximal end 76.5 μm" | ✓ |
| `DLMn_syn_post_loc = 0.25` × 50 | | 12.5 µm | "input from PSI from axon proximal end 12.5 μm" | ✓ |

This converts an anatomical distance into a **geometric position fraction**, not
into an electrical quantity. `gfs_param_scan_conductances.py:34` sweeps
`TTMn_syn_post_loc` from 0 to 1, i.e. moves the contact along the dendrite — still
not into an electrical variable.

**Consequence for this project:** the MaleCNS contact→soma distances
(154–242 µm) have **no pathway** into this model other than via a normalised
section position, and no electrical parameter is reachable from them.

---

## A-05 · Internal inconsistencies found in the published model

1. **µS axis label vs nS execution** — `gfs_param_scan_conductances.py:78,99` label
   `g_gap` in µS; `gap2.mod:12` executes it as nS. Exactly 1000×. (C-02)
2. **80 µS vs 0.08 µS** — Table 1 vs `gfpn.py:52`. Exactly 1000×. (C-03)
3. **Ra and Cm never assigned** yet appear in Table 1 as "estimated". (C-06)
4. **`gfs_param_scan_conductances.py` cannot execute on Python 3** — `double(...)`
   at lines 60–62 is Python 2 only.
5. **`gap2` is linear and non-rectifying** (no voltage-dependent state variable),
   so it **cannot reproduce** the measured GFS rectification (Gj_min/Gj_max = 0.21,
   Phelan 2008) under any parameter choice.
6. **`GF_TTMn_wt` and `GF_PSI_wt` are both `0.00`** — the chemical components of
   the two "mixed" synapses are effectively switched off.
7. **Project-internal documentation error** — `looming_abstraction.py:2095`
   cites an "80 uS versus **134** uS" discrepancy. **No 134 exists** in the paper
   or the code. Traced to no source; do not cite. (C-05)

---

## A-06 · Project-local parameter sources

`biological_brain/active_mechanism_registry.py` sources all channel mechanisms to
primary model files (`na.txt`, `nap.txt`, `k.txt`, `gfpn.txt`, `gap2.txt`) —
this is the project's own provenance mechanism and is sound. Its
`KIND_DENSITY_CHANNEL` / `KIND_POINT_PROCESS` labels are **not** SWC `kind`
values and must never be conflated with them.
