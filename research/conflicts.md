# Conflict Register — Fly Brain GFS / PSI→MN5

Purpose: so that no future session re-derives these, and so that no conflict is
ever "resolved" by picking the value that looks right.

**Standing rule:** a conflict is closed only by a measurement that adjudicates
it, or by a source that states which value applies to which preparation. It is
never closed by preference, by averaging, or by whichever value a model needs.

Provenance classes used throughout: `NEM` = Native experimental measurement,
`AM` = Anatomical measurement, `LDP` = Literature-derived passive parameter,
`MA` = Model assumption, `MDE` = Model-derived estimate.

---

## C-01 — MN5 whole-cell capacitance: 43 ± 2 pF vs 127 ± 16 pF  · **UNRESOLVED**

| | Source A | Source B |
|---|---|---|
| Value | **43 ± 2 pF**, n = 22 | **127 ± 16 pF** (SD) |
| Source | Fayyazuddin, Zaheer, Hiesinger, Bellen (2006) *PLoS Biol* 4(3):e63, doi:10.1371/journal.pbio.0040063 | Ryglewski & Duch (2009) *J Neurophysiol* 102(6):3673–3688, doi:10.1152/jn.00693.2009, PMID 19828724 |
| Object | Drosophila MN5 | Drosophila MN5 |
| Preparation | whole-cell, somatic | whole-cell, somatic |
| Same quantity? | **Yes** — both total somatic whole-cell capacitance | **Yes** |
| Unit conflict? | No | No |
| Preparation conflict? | Not fully documented as differing | Not fully documented as differing |
| Model vs measurement? | measurement (`NEM`) | measurement (`NEM`) |
| Ratio | **≈ 2.95×** | |

**Status: UNRESOLVED.** Same species, same neuron, same nominal preparation,
3× discrepancy. No source found that reconciles them. Candidate explanations
that remain *unverified*: differing ionic solutions / series compensation,
differing cell-health criteria, differing age or strain, or a subset of cells.

**Do not** average them, and do not treat 127 pF as "the bigger, better" value.
**What would resolve it:** the same cell type measured in one laboratory with a
published series-resistance and bridge-balance protocol and per-cell
distribution, or a source explicitly reconciling the two.

---

## C-02 — Gap-junction conductance: 135 / 34.5 µS (paper) vs 135 / 34.5 nS (executed)  · **UNRESOLVED, exactly 1000×**

| | Source A | Source B |
|---|---|---|
| Value | **135 µS** (young), **34.5 µS** (old), both "(estimated)" | **135** and **34.5** as executed |
| Source | Augustin, Zylbertal & Partridge (2019) *eNeuro* 6(2):ENEURO.0423-18.2019, **PMID 31001574**, PMCID PMC6469880, **Table 1** | ModelDB **245415**, `biological_brain/data/modeldb_245415/gfpn.py:31` → `gap2.mod:12` |
| Unit | µS | `g` declared in **nanosiemens** |
| Same quantity? | Yes — GF→TTMn and GF→PSI gap junction conductance | Yes |
| Model vs measurement? | paper-**estimated** free parameter (`MA`), explicitly "only partially constrained" | execution of that estimate |

**Exact 1000× discrepancy.** Critically, the *model's own analysis script*
labels the axis in µS while the mechanism that consumes it declares nS:
- `gfs_param_scan_conductances.py:78,99` → `plt.ylabel(param1 + ' (uS)')`
- `gap2.mod:12` → `g = 0 (nanosiemens) ... 1nS = 1000 pS`

So the µS figure and the nS execution **coexist inside the published model**.
**Status: UNRESOLVED — locus narrowed to the axis label, author intent not
determinable.** These are NOT GFS-measured values; there is no native
junctional conductance measurement anywhere in the GFS literature (see C-04).

---

## C-03 — PSI→DLMn chemical peak conductance: 80 µS (paper) vs 0.08 µS (executed)  · **UNRESOLVED, exactly 1000×**

| | Source A | Source B |
|---|---|---|
| Value | **80 µS** "(estimated)" | **0.08** |
| Source | Augustin 2019 Table 1, "Chemical synapse peak conductance" | `gfpn.py:52` → `'PSI_DLMn_wt': 0.08`, consumed as `neuron.h.NetCon(..., 0.08, ...)` |
| Unit | µS | µS (NEURON `Exp2Syn` `NET_RECEIVE(weight (uS))`; peak normalised to 1) |
| Same quantity? | Yes | Yes |
| Model vs measurement? | paper-**estimated** (`MA`) | execution |

**Exact 1000×.** `0.08 µS = 80 nS`.

> **Critical separation:** **0.08 is the PSI→DLMn CHEMICAL synapse. 135/34.5
> are GAP JUNCTIONS on a different cell (GF).** These two are *not* in conflict
> with each other; each is 1000× below its own Table 1 value. Any ledger entry
> that pools 0.08 with 80/135/34.5 is wrong.

---

## C-04 — "0.08 vs 80/135/34.5 µS" as a single conflict  · **PREMISE CORRECTED**

The original framing was four mutually inconsistent values. Verified outcome:

| Value | What it actually is | Measured or not |
|---|---|---|
| 135, 34.5 µS | GF gap junction, GFS-specific | **not measured** (estimated) |
| 80 µS / 0.08 µS | PSI→DLMn chemical peak, GFS-specific | **not measured** (estimated) |
| Gj_min/Gj_max = 0.21 | **Xenopus oocyte** heterotypic ShakB(N+16)/ShakB(L) | measured, but *not* in fly neurons |
| CC 0.023 / 0.01 | **MN1–4** motor-neuron pairs | measured in fly, but *not* GFS and *not* MN1→MN5 |
| Gj_min/Gj_max ≈ 0.05 | **generic crustacean** (crayfish giant synapse) | neither |

**No generic insect or vertebrate gap-junction conductance figure appears among
135, 34.5, 80 or 0.08.** Four values, two synapses, two independent 1000×
errors.

---

## C-05 — Project documentation error: "80 µS versus 134 µS"  · **CORRECTED (project-internal)**

`biological_brain/looming_abstraction.py:2095` describes a documented
**"80 uS versus 134 uS"** discrepancy for the GF-TTMn chemical peak
conductance. **No `134` appears in Augustin 2019 or in `gfpn.py`.** Traced to
no source. **Do not cite this figure.** Corrected here; the originating
docstring should be updated.

---

## C-06 — Ra and Cm: listed as "estimated" but NEVER SET in the model  · **RESOLVED as a finding**

| | Paper | Code |
|---|---|---|
| Specific axial resistance | **35.4 Ω·cm** "(estimated)", Table 1 | **never assigned** → NEURON built-in default **35.4 Ω·cm** |
| Specific membrane capacitance | **1 µF/cm²** "(estimated)", Table 1 | **never assigned** → NEURON default **1 µF/cm²** |
| Specific membrane resistance (Rm) | not a Table 1 row | not a NEURON variable; leak is `g_pas` = 0.03 mS/cm² |

Verified by exhaustive pattern search over all `*.py` and `*.mod` in ModelDB
245415: the only hits for `Ra|Rm|cm` are two x-axis *labels*.

**Status: RESOLVED as a reproducibility finding.** The paper's two "estimated"
passive parameters are numerically identical to the simulator defaults, and the
model never assigns them. **Therefore they cannot be distinguished from
simulator defaults, and must never be cited as Table-1-derived measurements.**
Provenance is at best `MA` (adopted default), not `LDP`.

---

## C-07 — MN5 dendritic length: >6 mm (literature) vs MaleCNS SWC  · **NOT A CONFLICT**

| | Literature | MaleCNS |
|---|---|---|
| Figure | ~6,716 ± 731 µm total dendritic length (n = 30, Vonhoff & Duch 2010, re-cited Ryglewski et al. *eLife* 2017;6:e25690) | 7,453.5 µm (801970) / 7,190.2 µm (801295) total cable; **93 % of it carries SWC `kind=0` = formally "undefined"** |
| Comparable? | **No** | — |

The MaleCNS figure is *total* cable, not dendritic length, and 93 % of it is
**unlabelled**, not "axon". The agreement in magnitude is therefore expected
and carries no information about compartment identity.
**Status: NOT A CONFLICT — different quantities and different conventions.**

---

## C-08 — SWC `kind=2` as "axon"  · **UNRESOLVED (terminology, not value)**

| | Position | Evidence |
|---|---|---|
| For axon | SWC v1.0.0 spec (PMC10654402) Table 1 defines Type 2 = Axon, and MaleCNS cites that spec for format | Format code only |
| Against asserting axon | MaleCNS documents nothing about Type population; the paper never uses the string "SWC"; neuprint's `skeleton_swc_to_df()` **discards** `node_type`; skeletons are segmentation-derived; files already deviate from spec defaults on radius units | No guarantee |

Observed distribution: `kind=2` is 5.2–5.6 % of nodes but only **7.0–7.4 % of
cable**, and contains *every* large radius (max 4.671 / 5.376 µm) in a
contiguous proximal block. That is *consistent* with an axon and *also*
consistent with a calibre-selected subset.

**Status: UNRESOLVED.** This project does not treat `kind=2` as axon. See
`anatomy_registry.md`.

---

## C-09 — ShakB as Kv1  · **PREMISE CORRECTED**

ShakB is **inx8**, an *innexin*, not a potassium channel. No primary source
describes the GFS electrical synapse as Kv1-mediated, and no Kv1 conductance or
kinetics was measured at any GFS synapse. Heterotypic junctions: GF expresses
ShakB(N+16); TTMn and PSI express ShakB(L) (Phelan et al. 2008 *Curr Biol*
18(22):1440–5, PMID 18976832).

---

## C-10 — Manduca ≠ Drosophila provenance trap  · **RESOLVED as a finding**

Three frequently-cited sources are **Manduca sexta**, not Drosophila:

| Source | Actually |
|---|---|
| Duch & Levine (2000) *J Neurosci* 20:6950 | *Manduca sexta* MN5 |
| Duch, Bayline & Levine (2000) *Dev Biol* | *Manduca sexta* |
| Meseke, Evers & Duch (2009) *J Neurophysiol* 102:41 | *Manduca sexta* flight motoneuron |

**Consequence — the single most important provenance finding in this project:**
Ryglewski & Duch (2009) state *"As values for the passive electrical properties
of MN5, we used values commonly applied for vertebrate and invertebrate neurons
(Meseke et al. 2009) (specific membrane capacity, Cm = 1.15×10⁻⁶ F·cm⁻²,
axoplasmic resistance Ra = 90 Ω·cm, passive leak conductance
g_pas = 0.0001667 Ω⁻¹·cm⁻²)."*

So the only published MN5 passive model runs on **Manduca-derived Ra and Cm**,
adopted by assertion, never fitted. Anyone treating those as Drosophila MN5
parameters is wrong.

---

## C-11 — SIZ literature figure: 88 ± 15 µm  · **CORRECTED — the figure does not exist**

Earlier project code encoded `SIZ_LITERATURE_DISTANCE_UM = 88.0 ± 15` and
expanded SIZ as "Secondary Isatoz Axon". Verified against PMC3604049:

- **"88 ± 15 µm" does not occur in Kuehn & Duch 2013.**
- **SIZ = "spike initiating zone"** — the expansion "Secondary Isatoz Axon"
  appears in **no** publication.
- The paper reports **two different figures from two different reference points**:
  - **"about 100 µm from the soma"** (no numeric uncertainty given);
  - **"11 ± 3 µm around the origin of the most distal posterior dendrite"**,
    n = 7, measured from *that dendrite's origin*, not from the soma. The paper
    does not state whether 3 is SD or SEM.

88 ± 15 appears to be a corrupted merge of the two. Corrected in
`biological_brain/malecns_contact_path.py` (3.0D-8U).

---

## C-12 — MN1→MN5 coupling coefficient  · **NOT DETERMINABLE**

Hürkey et al. (2023) *Nature* 618:118–125, PMID 37225999 report coupling
coefficients for **MN1–4 combinations only** (0.023 ± 0.003 SEM for MN1–MN2 and
MN3–MN4; 0.01 ± 0.0027 for all others). **No MN1→MN5-specific CC is reported.**
MN5 is characterised only indirectly via an in-vivo MN4–MN5 synchronisation
index (median 0.56, n = 11). Status: **NOT DETERMINABLE from published data.**
