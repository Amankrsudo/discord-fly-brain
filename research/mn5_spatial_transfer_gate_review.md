# MN5 Spatial-Transfer Gate Review

Independent audit. Reviewer did not author the evidence being reviewed and did
not re-run any exhausted literature search. **Audit only — no model was built,
no parameter was fitted, no gate was changed by this review.**

## Executive Verdict

# NOT AUTHORIZED

A key experimentally unconstrained quantity — specific membrane resistance — and
a contested one — whole-cell capacitance — both materially determine PSI→MN5
spatial voltage transfer. Neither can be bounded defensibly from existing
evidence, so any quantitative transfer statement would be speculative.

## Question Being Gated

Can existing evidence support a quantitative biological statement about

```
PSI synapse location  →  local MN5 postsynaptic voltage  →  voltage arriving at MN5 soma
```

without inserting an unmeasured passive parameter or fitting the answer?

**No.** Four of the quantities that determine the answer are BLOCKED or
CONTESTED in `research/model_input_freeze.csv`, and no measurement anywhere in
the evidence base ties them to MN5.

## Evidence Audited

| artifact | rows / scope |
|---|---|
| `research/model_input_freeze.csv` | 108 parameters (40 SAFE, 31 ASSUMPTION, 37 BLOCKED, 15 conflicts) |
| `research/evidence_ledger.csv` | 50 claims (E-001…E-050) |
| `research/spatial_transfer_evidence.md` | primary-source map, marked SEARCH EXHAUSTED |
| `research/missing_evidence.md` | M-01…M-14 |
| `research/dependency_graph.md` | D-1…D-5 |
| `research/final_anatomy_audit.md`, `model_framework.md`, `reduced_mn5_verification.md`, `RELEASE_CHECKLIST.md` | frozen chain |
| `research/model_input_audit.md` | ModelDB 245415, 8-file tree |
| `research/research_done.md`, `search_log.md` | Q-01…Q-15, exhausted branches |

## Direct Experimental Evidence

**There is no MN5 experiment that measured voltage or current at a non-somatic
location.** Verified by `research/research_done.md` Q-01 (SEARCH EXHAUSTED) and
by the freeze: every MN5 electrophysiology dataset is somatic whole-cell.

| route | exists for MN5? | note |
|---|---|---|
| somatic whole-cell | yes | Fayyazuddin 2006, Ryglewski 2009/2011/2012/2014, Herrera-Valdez 2013 |
| dendritic patch | **NO** | electrode access to insect processes documented as impractical (Gouwens & Wilson 2009) |
| axonal patch | **NO** | |
| dual-site (two sites on one MN5) | **NO** | Hürkey 2023 patches MN *pairs*, not two MN5 sites; MN5 was not among them |
| local voltage clamp | **NO** | |
| optical voltage at MN5 sites | **NO** | Yang 2016 ASAP2f is Mi1/Tm3/Tm1 — a different, ~10× smaller neuron |
| impedance / cable measurement | **NO** | |
| focal stimulation of a named distal process **with somatic recording** | **qualitative only** | Fayyazuddin 2006: contact on the peripheral axon; *"fails to propagate antidromically into the dendrite and therefore is filtered by the passive membrane properties"* — no coefficient, and the contact→soma distance is given only as *"span 50 µm"*, not soma-referenced |

**Closest existing item:** Ryglewski & Duch 2009 Fig 1B — a per-compartment
contact→soma **current**-transfer ratio (0.2–1). It is a **simulation**, on
Manduca-derived Ra/Cm adopted by assertion, and the authors disclaim exactness.

## Passive-Parameter Audit

Provenance per the project's five classes. From `model_input_freeze.csv`:

| parameter | value | provenance | status |
|---|---|---|---|
| `Ra` for MN5 | **NONE** | `model_assumption` | **BLOCKED** |
| `Ra` ever applied to MN5 | 90 Ω·cm — *Manduca*, self-described "commonly applied" | `literature_derived_passive_parameter` | ASSUMPTION |
| `Ra`, only measured *Drosophila* motor-neuron value | 212.47 ± 3.69 Ω·cm — **larval aCC** | `native_experimental_measurement` | ASSUMPTION (wrong cell, wrong stage) |
| `Rm` | **NONE** | `model_assumption` | **BLOCKED** |
| `Cm` variant A | 43 ± 2 pF (n=22) | `native_experimental_measurement` | ASSUMPTION (contested, C-01) |
| `Cm` variant B | 127 ± 16 pF | `native_experimental_measurement` | ASSUMPTION (contested, C-01) |
| `tau_m` | **NONE** | `model_assumption` | **BLOCKED** |
| `g_pas` | 1.667e-4 S/cm² — *Manduca* | `literature_derived_passive_parameter` | ASSUMPTION |
| ModelDB `Ra` / `cm` | 35.4 / 1.0 — **never assigned**, NEURON defaults | `model_assumption` | ASSUMPTION |
| `Rin` (somatic, whole-cell) | 102 ± 12 MΩ (n=22); 97 ± 31 MΩ (n=52) | `native_experimental_measurement` | **SAFE** |

### Why `Rin` does not rescue the situation

`Rin` is the only SAFE passive-adjacent measurement. It does **not** determine
axial attenuation. Somatic whole-cell `Rin` is a lumped result of membrane
conductance, membrane area and the dendritic contribution jointly; inverting it
for `Rm` requires *assuming* the geometry and the dendritic weighting — i.e.
assuming the very quantity being asked for. That is circular.

### Why no bounded ("CONDITIONAL") sweep is available

A parameter sweep is defensible only if the sweep limits are defensible. For
`Rm` they are not:

| source | implied Rm |
|---|---|
| Manduca-adopted `g_pas` 1.667e-4 S/cm² | ≈ **5,999 Ω·cm²** |
| larval aCC fitted leak 37.96 µS/cm² | ≈ **26,344 Ω·cm²** |

A **4.4× spread between two non-MN5 sources**, neither of which is MN5 and
between which no evidence ranks them. Choosing sweep bounds would be inventing
the bounds — which is the specific failure this gate exists to prevent. The same
applies to `Ra` (90 vs 212 Ω·cm, 2.4×, different species and life stage) and to
`Cm` (2.95×, unresolved, C-01).

A sweep whose width is invented cannot bound anything, so **CONDITIONAL is not
available**.

## Anatomical Constraints

Anatomy is strong and does **not** rescue the gate.

| item | value | usable for transfer? |
|---|---|---|
| verified PSI→MN5 contacts | 17 + 26 = **43**, 0 cross-pairings | **no** — a location, not a voltage |
| official `compartment_post` | `axon` ×43 | **no** — a label; says where, not what voltage |
| contact → SWC-root path | 169.2–267.8 µm | geometry only |
| contact → `somaLocation` straight line | 110.3–172.9 µm | geometry only |
| contact → soma-**proxy** tree path | 154.1–241.6 µm | rests on a **model assumption** (the proxy) |
| contact → soma-label graph path | **UNRESOLVED** | no soma node exists in any of the 9 skeletons |
| mesh | fragmented (2,587 / 2,765 components), not closed | topological only, never a compartment |
| SWC `kind` | biology `UNDEFINED IN AVAILABLE SOURCE` | cannot partition the arbor |
| SIZ | **UNRESOLVED**, four independent blockers | cannot localise spike initiation |

**Critical:** all 43 contacts are labelled `axon`, while MN5's *dendritic* input
carries the bulk of its synapses. The contacts therefore sit **away from the
dendritic arbor** — which makes the transfer path *less* determined, not more:
the relevant question becomes axonal-to-somal attenuation along the main
process, and nothing measures that.

**No anatomical quantity converts into a voltage.** Distances and labels are
`anatomical_measurement`; a transfer ratio is not.

## Somatic Electrophysiology Constraints

What Fayyazuddin 2006 and later MN5 work actually constrain — and what each
does **not** tell us:

| measurement | value | does it constrain contact→soma transfer? |
|---|---|---|
| somatic EPSP amplitude | 4.71 ± 0.35 mV (n=10), −74 mV, **GF stimulated, PSI never directly** | **No.** A filtered somatic voltage; the amplitude **at the contact is unreported**, so no ratio is computable |
| somatic EPSP, *gfA*¹ | 1.5 ± 0.32 mV (n=7) | No |
| `Rin` | 102 ± 12 / 97 ± 31 MΩ | **No** — lumped with geometry (see above) |
| `Cm` | 43 vs 127 pF | Only a ~2.95× **contested** membrane area |
| resting potential | −67.8 ± 5.5 mV (n=13) | No |
| spike threshold | −24.1 ± 8.2 mV (n=11) | No |
| AP amplitude / width | 45.5 ± 8.6 mV / 0.92 ± 0.25 ms | No — a somatic event |
| qualitative filtering | *"fails to propagate antidromically … filtered by the passive membrane properties"* | Directional **qualitative** statement only |

A transfer **ratio** requires a numerator *and* a denominator. Every MN5 dataset
has a denominator (soma) and **no numerator**. This is the central reason the
gate cannot open on existing data.

## Published-Model Audit

ModelDB 245415 (Augustin, Zylbertal & Partridge 2019, PMID 31001574) is a
**simplified 4-cell GFS latency model**, 8 sections, 51 isopotential segments
each — the paper states its anatomy is *"simplified"* and *"chosen to capture
general cell proportions"*.

| item | finding | treated as native? |
|---|---|---|
| `Ra`, `Rm`, `Cm` | **never assigned** in code; run on NEURON defaults 35.4 Ω·cm, 1 µF/cm² — numerically identical to the two Table-1 "(estimated)" entries | **NO** — indistinguishable from simulator defaults (C-06) |
| `g_gap` | 135 / 34.5 µS in Table 1 vs **nS** as executed by `gap2.mod` — exactly 1000× (C-02) | **NO** — internally contradictory |
| chemical peak | 80 µS vs 0.08 µS as executed — exactly 1000× (C-03); a *different synapse* from `g_gap` | **NO** — must never be pooled |
| `gap2` | linear, non-rectifying — cannot reproduce the measured GFS rectification | **NO** |
| `PSI_DLMn_wt`, `GF_PSI_wt` | 0.00 — the chemical components of two synapses are switched off | **NO** |
| anatomical contact positions | six µm distances map to normalised 0–1 section fractions and reconcile exactly | **geometry only** — a position, never a voltage |
| code converting µm → electrical quantity | **zero** occurrences of electrotonic distance, length constant, attenuation, transfer resistance | — |

The only MN5-specific published transfer map (Ryglewski & Duch 2009 Fig 1B) is
built on Manduca-derived Ra and Cm adopted by assertion, reports steady-state
**current** rather than synaptic **voltage** transfer, and is disclaimed by its
authors as not an exact estimate.

## Remaining Blockers

| # | blocker | why it blocks |
|---|---|---|
| **B-1** | `Rm` for MN5 unmeasured, and un**boundable** | directly sets the length constant; no defensible sweep limits exist |
| **B-2** | `Ra` for MN5 unmeasured; only *Manduca* (90) and larval aCC (212) | sets axial attenuation |
| **B-3** | `Cm` contested 43 vs 127 pF (C-01, ~2.95×) | sets membrane area for any conductance argument |
| **B-4** | no MN5 non-somatic or dual-site voltage measurement | the quantity itself is unmeasured |
| **B-5** | contact→soma path to a **labelled soma** UNRESOLVED | the route's terminus is an assumption |
| **B-6** | no PSI→MN5 synaptic conductance or reversal | the source voltage at the contact is unbounded |

## Gate Decision

# NOT AUTHORIZED

Not CONDITIONAL, because the sweep bounds would have to be invented: the two
non-MN5 `Rm` implications already differ by **4.4×**, and neither ranks above
the other. A bounded model over invented bounds bounds nothing.

Not OPEN, obviously.

No existing conclusion changes. This review confirms and quantifies the verdict
the project already recorded; it overturns nothing.

## Minimum Evidence Needed to Open

Ranked by gate-opening power. **Identifiability is stated explicitly** — no
experiment is claimed to "measure Ra" without demonstration.

| # | measurement | directly measures | removes | MN5-specific? | PSI-relevant region? | gives transfer directly? | identifiability |
|---|---|---|---|---|---|---|---|
| 1 | **Dual-site voltage recording** — somatic patch + second electrode on the PSI-contact-bearing process, during focal PSI stimulation | V at contact and V at soma, same event | **B-4 directly**; constrains B-1/B-2 jointly | yes | yes | **YES — the ratio is the answer, no cable inversion needed** | The transfer ratio is *measured*, not identified from a model. Ra and Rm are **not separately identified** from two sites and must not be claimed. |
| 2 | **Optical voltage mapping** (ASAP2f/ASAP3s) along the MN5 arbor during focal PSI stimulation | V vs position along the arbor | **B-4**; gives distance dependence | yes | yes | yes, spatially resolved | Gives a decay profile. Ra/Rm remain **non-identified individually** — only a constraint set. Yang 2016 is the template (Mi1, not MN5). |
| 3 | **Reversal-potential series at a single PSI contact** | EPSP amplitude vs holding potential | **B-6** (bounds the source); gives synaptic conductance | yes | yes | no — bounds the input, not its propagation | Conductance is identifiable from an I–V without cable assumptions. |
| 4 | **Two-site current injection at ≥3 known locations** on the MN5 main process | current attenuation vs distance | **B-1 and B-2 jointly** | yes | yes | no — constrains, does not measure | With **≥3** locations and known geometry, Ra and Rm become *separately identifiable*; **two** locations constrain only their combination. Demonstrating this is required before claiming "Ra measured". |
| 5 | MN5 `Cm` reconciliation | one capacitance | **B-3** | yes | n/a | no | Requires per-cell distributions under one protocol. |
| 6 | MN5 soma-node reconstruction | a real terminus for the path | **B-5** | yes | yes | no | Would replace the proxy assumption with anatomy. |

**Recommended next task: #1 (dual-site) or #2 (optical), ideally after #3** so
the input is bounded before propagation is measured. #3 is the cheapest and
removes B-6 first.

## Provenance Table

| conclusion | class |
|---|---|
| 43 contacts, `compartment_post = axon` | `anatomical_measurement` |
| contact→surface / root-path / straight-line distances | `anatomical_measurement` |
| contact→soma-**proxy** path | `model_derived_estimate` |
| "that proxy is the soma" | `model_assumption` |
| MN5 `Rin`, `V_rest`, `V_th`, `AP_amp` | `native_experimental_measurement` |
| MN5 `Cm` (both variants) | `native_experimental_measurement`, **contested** |
| Manduca `Ra`/`Cm`/`g_pas` as applied to MN5 | `literature_derived_passive_parameter` |
| larval aCC `Ra`/`Cm`/leak as applied to MN5 | `native_experimental_measurement`, **wrong object** |
| ModelDB 35.4 / 1.0 | `model_assumption` (simulator default) |
| Ryglewski 2009 Fig 1B transfer map | `model_derived_estimate` on adopted inputs |
| Yang 2016 decay profile | `native_experimental_measurement` (**different neuron**) |
| MN5 spatial voltage transfer | **NONE — never measured** |

## Explicit Non-Claims

This review does **not** assert, and must not be cited as asserting:

- that MN5 spatial voltage transfer has been measured, estimated or bounded
- that `Rin` determines or bounds attenuation
- that either capacitance value is correct
- that `kind = 2` is axon
- that `compartment_post = axon` implies any particular voltage
- that a `Rin × Cm` product is a membrane time constant
- that any cited figure is an MN5 measurement when it is not
- that ModelDB defaults or *Manduca* / larval-aCC values are native MN5 data

## Impact on Current Model

**None.** No code, constant, parameter or verdict changed.

Gate status, restated verbatim:

- **PSI→MN5 spatial voltage transfer: NOT AUTHORIZED**
- **Dα7 conductance: NOT AUTHORIZED**

- `ReducedMN5Simulator` remains a threshold-only abstraction; this review adds
  no integration and no passive term.
- Both scientific gates remain as recorded.
- The framework already refuses spatial transfer
  (`require_spatial_transfer()` raises), and the freeze already marks
  electrotonic distance, length constant and transfer resistance as
  `NONE (not computed)` / BLOCKED.
- `M-02` in `missing_evidence.md` is confirmed, not amended.