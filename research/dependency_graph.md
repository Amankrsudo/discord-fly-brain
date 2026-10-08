# Dependency Graph — what must be solved before what

Purpose: show the order in which questions must be answered, so effort is not
spent on a question whose prerequisite is missing.

---

## D-1 · The anatomical chain to the soma

```text
PSI contact anatomy                      DONE (43 contacts, 1.67–80.22 nm from surface)
        ↓
Contact → soma region proxy              DONE (154–242 µm, exact tree distance)
   BLOCKED BY: no soma node → path to a LABELLED soma is UNRESOLVED forever
        ↓
SIZ registration                          BLOCKED ×3
        ↓
local synapse location on a named process BLOCKED (93 % of arbor is `kind=0` undefined)
        ↓
spatial voltage transfer                  BLOCKED — GATE 1
        ↓
native synaptic conductance               BLOCKED — no measurement exists
        ↓
Dα7 conductance model                     BLOCKED — GATE 2
```

**Hard structural blocker at the second step.** Because no MaleCNS MN5/PSI
skeleton contains a `kind=1` node, *no amount of further anatomical work on the
existing skeletons can produce a path to a labelled soma.* Progress requires a
different artefact (M-07), not more analysis of these files.

---

## D-2 · The capacitance conflict

```text
43 ± 2 pF (Fayyazuddin 2006, n=22)
127 ± 16 pF (Ryglewski & Duch 2009)        ← ~2.95×, UNRESOLVED
        ↓
Which is MN5's membrane area?
        ↓
passive model geometry (surface area, dendritic/axonal split)
        ↓
spatial transfer model                     ← GATE 1
```

Compounding: Ryglewski & Duch's own passive parameters are **Manduca-derived**
(`RA = 90 Ω·cm`, `Cm = 1.15 µF/cm²`, adopted by assertion), and the MaleCNS mesh
total (18,725.6 / 19,665.4 µm²) differs from the frustum approximation of the
skeleton (24,803.7 / 25,796.8 µm²) by ~24 %. So a transfer model would rest on a
disputed capacitance, an adopted Ra, and two irreconcilable area conventions.

---

## D-3 · The ModelDB conductance chain

```text
Table 1: g_gap 135 / 34.5 µS "(estimated)"
Code:    gap2.mod declares nanosiemens     ← exactly 1000× (C-02)
Table 1: chemical peak 80 µS "(estimated)"
Code:    gfpn.py:52 'PSI_DLMn_wt' = 0.08   ← exactly 1000× (C-03)
        ↓
Ra, Rm, Cm NEVER ASSIGNED
Code runs on NEURON defaults 35.4 Ω·cm, 1 µF/cm²
        ↓
reproducibility decision: are Table 1's "estimated" values
author-chosen, or inherited simulator defaults?   ← UNRESOLVED (C-06)
        ↓
any future GFS model interpretation inherits the ambiguity
```

Note the locus is now narrowed: the authors' own analysis script labels the
`g_gap` axis in **µS** while the consuming mechanism declares **nS**, so the
discrepancy lives inside the published model. Author intent is not recoverable.

---

## D-4 · The compartment-label chain

```text
MaleCNS SWC `kind` column                  FORMAT codes only, biology undocumented
        ↓
is kind=2 axon?                            UNRESOLVED (C-08, E-049) — NOT resolved by D-4 below
        ↓
Berg post-hoc flow-centrality split        exists, PER SYNAPSE, official layer
        ↓
retrieve for the 43 MN5 synapses          ✔ DONE 2026-10-05 — all 43 retrieved, all `axon`
        ↓
locate the linker region / cut node        STILL OPEN — no cut-node artifact released (E-050)
        ↓
name the compartment each PSI contact is on
```

**Status of D-4 as of 2026-10-05.** The per-synapse branch is closed: **M-06 is
RESOLVED in its per-synapse form.** All 43 contacts carry an official
`compartment_post`, with 0 missing and 0 ambiguous. MN5-wide, the same field is
4.3 % / 21.2 % axon and 92.2 % / 78.0 % dendrite, so PSI contacts are
*exclusively* axonal while the bulk of MN5's input is dendritic — consistent with
Fayyazuddin 2006.

**This branch does not lead to either gate.** A compartment **string** is not a
distance (D-5) and not a voltage (E-048). The per-neuron cut node remains
unreleased and remains a *documentation* gap, not a modelling blocker.

---

## D-5 · What does NOT block anything

```text
mesh fragmentation (2,587 / 2,765 components)
        └── does NOT block: SWC centerline gives continuity independently
        └── neuPrint attributes it to segmentation artefacts

3 AMBIGUOUS component associations
        └── does NOT block: all 3 project to unambiguous SWC nodes

SIZ mapping
        └── blocks nothing downstream; it is a modelling nicety, not a gate

GFS gap-junction latency (1.44 / 1.85 ms, Augustin 2019)
        └── independent of the chemical PSI→MN5 gate

compartment_post = axon for all 43 contacts   ← RESOLVED 2026-10-05
        └── does NOT block and does NOT enable: a compartment STRING is not a
            distance and not a voltage (E-048). It tells us the contacts are not
            on the dendritic arbor; it says nothing about how much signal
            reaches the soma.
```

---

## Critical-path summary

**Shortest path to opening Gate 1** (spatial voltage transfer):
`M-02 dual-site recording` alone would supply a contact→soma transfer ratio
directly and *would not require* resolving the capacitance conflict, because a
measured ratio supersedes a modelled one.

**Shortest path to Gate 2** (Dα7 conductance): `M-01` (native PSI→MN5
conductance) must precede any Dα7-specific work, since a receptor conductance
cannot be separated from total synaptic conductance without the latter.

**Both gates are blocked on experiments, not on more computation.** No further
analysis of existing public data will open either one.
