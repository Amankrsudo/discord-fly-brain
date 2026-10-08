# Missing Evidence Map — Fly Brain GFS / PSI→MN5

For every gap: **the experiment or dataset that would actually resolve it**, not
"more research needed".

Tier 1 blocks modelling · Tier 2 improves accuracy · Tier 3 non-blocking.

---

## TIER 1 — blocks any future electrical modelling

### M-01 · Native PSI→MN5 synaptic conductance
**Status:** NOT FOUND. No primary experiment measures it. The only figure in
circulation (80 µS, Augustin 2019 Table 1) is explicitly **"(estimated)"** and is
executed at 0.08 µS — a 1000× discrepancy (C-03).

**Resolving experiment:** whole-cell recording from MN5 dendrite/axon while
stimulating PSI at a single identified contact, with intracellular current clamp
at a known holding potential, plus a second electrode or a pharmacological
reversal series, so that a synaptic conductance can be solved rather than
inferred from an EPSP amplitude and an assumed driving force. Minimum viable:
EPSP amplitude vs holding potential across a reversal sweep at one contact.

**Gate opened by this:** prerequisite for `Dα7 conductance`.

---

### M-02 · MN5 spatial voltage transfer (contact → soma)
**Status:** NOT FOUND — SEARCH EXHAUSTED (`research_done.md` Q-01). No
Drosophila MN5 experiment constrains it. The only MN5 transfer map is a
*simulation* on Manduca-derived Ra/Cm (Ryglewski & Duch 2009 Fig 1B, current
transfer 0.2–1, explicitly disclaimed as not exact).

**Resolving experiment:** dual-site recording — somatic whole-cell plus direct
dendritic/axonal patch on the process carrying the identified PSI contact —
during focal PSI stimulation. Voltage at the contact and at the soma measured
simultaneously gives the transfer ratio directly for that contact, and sweeping
stimulation across contacts gives the distance dependence. This is the single
experiment that would most reduce downstream uncertainty; Gouwens & Wilson
(2009) note that in insect neurons *"electrode recordings are impossible from
these small processes"* — hence Yang et al. 2016's ASAP2f imaging is the realistic
fallback for a first pass.

**Gate opened by this:** directly.

---

### M-03 · Reliable Drosophila axial resistance (Ra)
**Status:** NOT FOUND for Drosophila. Ra = 90 Ω·cm in the only published MN5
model is **Manduca-derived, adopted by assertion**. ModelDB 245415 never assigns
Ra at all and silently runs on the NEURON default 35.4 Ω·cm (C-06).

**Resolving data:** an axial-resistivity measurement from a Drosophila neuron
with known geometry — e.g. dendritic/axonal patch with a current-density profile,
or a back-propagating-spike width analysis across a known cable. Alternatively,
re-fitting Rin/Cm from a two-site recording (M-02) against the MaleCNS geometry
would *constrain* Ra even without measuring it.

**Gate opened by this:** prerequisite for any transfer computation.

---

### M-04 · Native Dα7 conductance / kinetics at PSI→MN5
**Status:** see `da7_evidence.md`. Heterologous data exist; native
PSI→MN5 conductance is the open question.

**Resolving experiment:** as M-01, plus receptor-specific pharmacology or a
Dα7 null background crossed with the dual-site preparation.

---

### M-05 · MN1→MN5 electrical coupling conductance
**Status:** NOT DETERMINABLE. Hürkey 2023 reports CC for **MN1–4 only**
(0.023 ± 0.003 SEM / 0.01 ± 0.0027). No MN1→MN5 CC, no conductance, no latency.

**Resolving experiment:** dual in situ patch on identified MN1 and MN5 cell
bodies (the Hürkey preparation already achieves this for MN1–4, so the method is
demonstrated), measuring postsynaptic charge ÷ presynaptic charge and the
transmission latency.

---

## TIER 2 — improves accuracy

### M-06 · Per-neuron axon/dendrite compartment split as a cut node

**Status: RESOLVED in its per-synapse form (3.0D-8V). Scope-limited.**

**RESOLVED:** the official MaleCNS v1.0 per-synapse `compartment_post`
annotation was retrieved for **all 43** verified PSI→MN5 contacts from
`gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed`. All 43 are
`axon`; missing 0, ambiguous 0, unknown 0. `compartment_pre`: axon ×38,
unknown ×5 (all on 801295). Artifact:
`research/artifacts/malecns_compartment_post_psi_mn5.csv`. Reproducible via
`research/scripts/retrieve_malecns_compartment_post.py`.

**STILL OPEN — the per-neuron cut node is unreleased.** Six locations were
enumerated exhaustively (`truncated:false`): `flyconnectome/2025malecns`,
`flyconnectome/malecns`, the `gs://flyem-male-cns/v1.0/` bucket,
`v1.0/database/neuprint-inputs/`, `flywire_annotations`, and the layer `info`.
No cut node, cut point or subtree artifact exists in any of them. So the
*linker region* that `navis.split_axon_dendrite` defines is still not locatable
as a node set.

**Resolving the remainder:** a statement from the MaleCNS/FlyEM authors, or
release of the per-neuron cut node.

**What this does NOT do:**
- does **not** resolve the SWC `kind=2` question (different column, different
  provenance; MaleCNS documents neither). The comparison is now *possible* and
  has deliberately **not** been performed.
- does **not** supply a distance, a voltage, or any electrical quantity.
- does **not** license any inference from PDMN vs WTct.

---

### M-07 · A soma node or soma surface for MN5
**Status:** the soma *region* is present (radius 4.671 / 5.376 µm dilation
1.45–2.10 µm from `somaLocation`, and `somaLocation` 3.87 / 3.50 µm from the mesh
surface) but no `kind=1` node and no labelled soma surface exist.

**Resolving data:** an official MaleCNS soma-containing SWC, or a statement from
the FlyEM/MaleCNS authors on how the soma is represented.

---

### M-08 · Reliable axial resistance *and* an anatomical axis for SIZ
**Two independent blockers for SIZ**, both verified absent (Q-04, Q-05): no
transform from the Kuehn & Duch Amira frame into MaleCNS EM space, and no
anterior/posterior axis documented anywhere. Plus the reconstruction itself was
**never deposited** (Q-03).

**Resolving data:** (a) a deposit of the Kuehn & Duch MN5 reconstruction;
(b) a published neuroanatomical axis convention for the MaleCNS EM frame;
(c) neuron identity matching at the individual-reconstruction rather than
group level (Ehrhardt 2025 rated only 1–3).

---

### M-09 · Local membrane properties at the PSI contact site
**Status:** nothing. MaleCNS SWC gives a reconstructed radius (kind=0 median
diameter 0.512 µm) — that is an anatomical annotation, **not** a membrane
property, and must never be converted into one.

**Resolving experiment:** small-conductance dendritic/axonal voltage clamp or
loose-seal patch at the mapped contact location.

---

### M-10 · Receptor density at PSI→MN5
**Status:** NOT FOUND. No quantitative density at this synapse.

**Resolving data:** EM-based receptor-crowding analysis of the MN5 spine/contact
volume, or calibrated immuno with a counting standard.

---

## TIER 3 — interesting, non-blocking

### M-11 · Developmental variation in MN5 passive properties — no data found.
### M-12 · Sex differences — **excluded by construction**: MN5 soma→somaLocation,
process length and compartment fractions are effectively identical between 801970
and 801295; but the whole dataset is male, so female comparison is impossible
from MaleCNS.
### M-13 · Ageing effects on MN5 — **nothing found**. Note the GFS *age* literature
is strong but applies to **GF→TTMn only** (Auger 2020: GF→PSI shows *no* ShakB
decline).
### M-14 · Minor morphological uncertainty — the 3 AMBIGUOUS component
associations (801970 contacts 8, 9, 10; margins −4.5 to −5.8 nm; runner-up always
the same fragment, comp 64). Their SWC nodes are unambiguous, so this does not
propagate to any path result.

---

## GATE SUMMARY

**PSI→MN5 spatial voltage transfer: NOT AUTHORIZED** — M-02 unresolved.
**Dα7 conductance: NOT AUTHORIZED** — M-01 and M-04 unresolved.

Nothing in this overnight run produced qualifying primary evidence for either.
