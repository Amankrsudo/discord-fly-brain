# Source Registry — Fly Brain GFS / PSI→MN5

Classification: **PRIMARY EXPERIMENT** (actual biological measurement) ·
**PRIMARY DATASET** (original deposited data) · **PRIMARY MODEL/CODE** (original
computational implementation) · **SECONDARY** (review/database/summary) ·
**UNVERIFIED** (lead only, not acceptable as evidence).

All entries verified against primary text unless marked otherwise.

---

## S-01 · MaleCNS v1.0 connectome — **PRIMARY DATASET**

- **Citation:** Berg, S. et al. (2026). *Sexual dimorphism in the complete
  Drosophila male central nervous system connectome.* **Cell** 189(18):5504–5526.e15.
  DOI `10.1016/j.cell.2026.08.015` · PMID 41279223 · preprint bioRxiv `10.1101/2025.10.09.680999`
  (PMCID PMC12636603).
- **URL:** https://male-cns.janelia.org/ · bucket `gs://flyem-male-cns`
- **Species/sex:** *Drosophila melanogaster*, **male**, adult. 166,700 neurons,
  11,710 types; 165,122 traced.
- **Preparation:** FIB-SEM volume; 8 nm isotropic; automatic FFN segmentation +
  Janelia/Cambridge proofreading; Google Research segmentation.
- **Technique:** synaptic-resolution EM connectomics; automatic skeletonisation
  of the proofread segmentation.
- **What it actually measured:** connectivity, cell types, synapses, neuron
  morphologies (as segmentation-derived skeletons and meshes).
- **Parameters extracted:** contact coordinates; body IDs; soma annotations;
  SWC skeletons; meshes; ROI/neuropil labels; per-synapse
  `compartment_pre`/`compartment_post` labels (see S-05).
- **Supplementary:** https://github.com/flyconnectome/2025malecns (15 files,
  verified `truncated:false`). **No axon/dendrite split artifact** (see C-08).
- **Raw data:** public, CC-BY, unauthenticated.
- **Code:** `flyem-snapshot`, `neuprint-python`, `navis`, `natverse/malecns`.
- **Limitations:** SWC `kind` semantics undocumented; no soma node in MN5/PSI
  skeletons; meshes heavily fragmented; skeletons are segmentation-derived.

## S-02 · SWC v1.0.0 format specification — **SECONDARY (authoritative schema)**

- **Citation:** Mehta, K., Ljungquist, B., Ogden, J., Nanda, S., Ascoli, R.A.,
  Ng, L., Ascoli, G.A. (2023). *Online conversion of reconstructed neural
  morphologies into standardized SWC format.* **Nat Commun** 14:7429.
  PMID 37973857 · PMCID **PMC10654402** · https://doi.org/10.1038/s41467-023-42931-x
- **Why it is here:** this is the specification **MaleCNS itself cites** for its
  SWC format (`male-cns.janelia.org/download/`, `[swc]` link).
- **What it defines:** the 7 columns; `Type` codes (Table 1); parent/root
  semantics; soma representation (single root point or multiple points, first
  must be a root); conformance check "no soma samples detected" → warning.
- **Parameters extracted:** `SWC_TYPE_CODES` in `malecns_ingest.py`.
- **Limitations:** a *format* spec. It does not certify that any particular
  producer populated `Type` meaningfully.
- **Raw data:** https://swc-specification.readthedocs.io

## S-03 · MN5 passive + Shaker model — **PRIMARY MODEL/CODE (with measurements)**

- **Citation:** Ryglewski, S. & Duch, C. (2009). *J Neurophysiol* 102(6):3673–3688.
  DOI `10.1152/jn.00693.2009` · PMID 19828724 · PMCID PMC2804405
- **Species/sex:** *Drosophila*, adult MN5.
- **Measured:** somatic whole-cell **Cm = 127 ± 16 pF (SD)**; Shaker/Shal currents.
- **NOT measured:** any cable parameter. Verbatim: *"As values for the passive
  electrical properties of MN5, we used values commonly applied for vertebrate
  and invertebrate neurons (Meseke et al. 2009) (specific membrane capacity,
  Cm = 1.15×10⁻⁶ F·cm⁻², axoplasmic resistance Ra = 90 Ω·cm, passive leak
  conductance g_pas = 0.0001667 Ω⁻¹·cm⁻²)."* → **Manduca-derived**, adopted.
- **Also contains the only per-compartment contact→soma transfer map for MN5**
  (Fig 1B): a *simulated* steady-state **current**-transfer ratio 0.2–1.
- **Authors' own caveat:** *"These models were not intended to provide exact
  estimates of how much current from distal processes can be seen in somatic
  voltage-clamp recordings."*
- **Parameters extracted:** Cm 127 pF (`NEM`); Ra 90 Ω·cm, Cm 1.15 µF/cm²,
  g_pas 0.0001667 Ω⁻¹cm⁻² (`LDP`, Manduca-derived); transfer map (`MDE`).

## S-04 · MN5 somatic physiology + GF→MN5 circuit — **PRIMARY EXPERIMENT**

- **Citation:** Fayyazuddin, A., Zaheer, M.A., Hiesinger, P.R., Bellen, H.J.
  (2006). *PLoS Biol* 4(3):e63. DOI `10.1371/journal.pbio.0040063`
- **Measured:** Cm = **43 ± 2 pF (n=22)**; Rin = **102 ± 12 MΩ (n=22)**;
  somatic EPSP under GF stimulation **4.71 ± 0.35 mV (n=10)**; gfA1
  1.5 ± 0.32 mV (n=7); somatic AP 50–60 mV.
- **Key anatomical statement:** *"the PSI bypasses the entire dendritic
  structure of MN5 and makes multiple synaptic contacts that span 50 μm and
  follow the axons out into the posterior dorsal motor nerve."*
- **NOT measured:** voltage at the contact; contact-to-soma transfer
  coefficient; the contact-to-soma distance in µm.
- **Provenance:** all values `NEM`.

## S-05 · MaleCNS per-synapse compartment labels — **PRIMARY DATASET**

- **Location:** `gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed/`
  (public, CC-BY, unauthenticated).
- **Layer type:** `neuroglancer_annotations_v1`. Verified properties include
  `compartment_pre` and `compartment_post`, both `uint8`, enum
  `[0,1,2,3,4]` = `["unknown","axon","dendrite","linker","cell-body-fiber"]`.
- **Relationships:** `by_rel_body_pre` (preshift 10, shard 9, minishard 8),
  `by_rel_body_post` (same).
- **What it is:** the flow-centrality axon/dendrite split, applied **per
  synapse** — i.e. the Berg et al. axon/dendrite result *is* deposited here,
  at synapse resolution rather than as a cut-node table.
- **Provenance:** `AM` (data-derived). Not `NEM` — it is a computational label
  derived from a segmentation, not an observation.
- **Retrieval status:** the focused PSI→MN5 subset has been retrieved and
  verified: 43 contacts, 17 on MN5 body 801970 and 26 on body 801295, all with
  the literal released label `compartment_post="axon"`. See the per-contact
  source artifact `research/artifacts/malecns_compartment_post_psi_mn5.csv`
  and the audited projection result
  `research/mn5_compartment_post_swc_type_concordance.csv`. This does not
  establish biological compartment semantics, voltage transfer, or a soma
  path. The focused subset is not a claim that all inputs to either body were
  retrieved for this analysis.
- **Caveat:** a third-party recompile (`YijieYin/connectome_data_prep`,
  `manual_split.py`) blanket-assigns `'dendrite'` to every synapse on motor
  neurons: `motor_syns.loc[:,'compartment'] = 'dendrite'`. MN5 is motor, so that
  release is **actively misleading for MN5** and must not be used.

## S-06 · GFS escape-latency model — **PRIMARY MODEL/CODE**

- **Citation:** Augustin, H., Zylbertal, A. & Partridge, L. (2019). *eNeuro*
  6(2):ENEURO.0423-18.2019. **PMID 31001574** · PMCID PMC6469880 ·
  DOI `10.1523/ENEURO.0423-18.2019`
- **ModelDB:** **245415** — https://github.com/ModelDBRepository/245415
  (verified tree SHA `feaebc4c…`, `truncated:false`, **8 files**).
- **Contents:** `gfpn.py`, `gfs_param_scan_conductances.py`,
  `channels/{gap2,k,nap,nat}.mod`, `readme`.
- **4 cells, 8 sections**, 51 isopotential segments each: GF, TTMn,
  TTMn_med, TTMn_lat, PSI, PSI_pas, DLMn, DLMn_pas.
- **Parameters:** Table 1 marks g_gap 135/34.5 µS, chemical peak 80 µS, leak
  0.03 mS/cm², Cm 1 µF/cm², Ra 35.4 Ω·cm — **all "(estimated)"**.
- **Critical:** `Ra` and `Cm` are **never assigned** in the code (see C-06).
  `gap2` is **linear and non-rectifying**, so it cannot reproduce the measured
  rectification of GFS. `GF_TTMn_wt` and `GF_PSI_wt` are both `0.00`.
- **Reproducibility defects:** the published scan script uses Python-2-only
  `double(...)` at lines 60–62; the µS/nS axis conflict (C-02).
- **Raw data:** none deposited; latency n = 8–9 per condition.
- Vendored byte-identically at `biological_brain/data/modeldb_245415/`.

## S-07 · MN1–MN5 electrical coupling — **PRIMARY EXPERIMENT**

- **Citation:** Hürkey, N. et al. (2023). *Nature* 618:118–125.
  PMID 37225999 · DOI `10.1038/s41586-023-06099-0`
- **Measured:** dual in situ patch; CC **0.023 ± 0.003 SEM** (6 pairs) for
  MN1–MN2 and MN3–MN4; **0.01 ± 0.0027** (10 pairs) for other MN1–4
  combinations; AHP CC 0.042; spike-overshoot CC 0.01.
- **NOT measured:** MN1→MN5-specific CC (see C-12); any conductance; latency.
- MN5 "innervates DLM fibres 5 and 6 on the side contralateral to the MN5 soma".
- MN4–MN5 synchronisation index median 0.56 (n=11) vs 0.84 (n=7) ShakB-OE.

## S-08 · GF gap junction biophysics — **PRIMARY EXPERIMENT (heterologous)**

- **Citation:** Phelan, P., Goulding, L.A., Tam, J.L.Y., Allen, M.J., Dawber, R.J.,
  Davies, J.A. & Bacon, J.P. (2008). *Molecular mechanism of rectification at
  identified electrical synapses in the Drosophila giant fiber system.*
  *Current Biology* 18(24):1955–1960. PMID 19084406 · PMCID PMC2663713 · DOI
  `10.1016/j.cub.2008.10.067`. The previously listed title, issue, pages, PMID
  and DOI referred to different or mismatched records.
- **Measured:** **Xenopus oocyte** heterotypic ShakB(N+16)/ShakB(L):
  rectification index Gj_min/Gj_max = **0.21**; Gj reaches only ~50–60 % of max
  by 5 ms; 15–20 % voltage-insensitive fraction; single-Boltzmann fit.
- **Necessity/sufficiency:** `shakB²` abolishes dye coupling; `shakB(n+16)`
  rescues, `shakB(n)` does not.
- **NOT measured:** any absolute Gj in fly neurons. Supplement Tables S1–S3
  not retrievable → `INACCESSIBLE`.
- **Provenance:** `NEM` but **heterologous**; must never be quoted as GFS.

## S-09 · GF→TTMn synapse anatomy and age-dependence — **PRIMARY EXPERIMENT**

- **Citation (anatomy):** Orr, Borgen, Caruccio & Murphey (2014). *J Neurosci*
  34(16):5416–5430. PMID 24740867 · DOI `10.1523/JNEUROSCI.3183-13.2014`
  - ShakB occupies **14.72 ± 3.99 % (SD, n=9)** of GF terminal in WT;
    *frazzled* LOF 3.00 ± 0.57 (n=12); *Netrin* LOF 1.54 ± 0.48 (n=15).
- **Citation (age/auditory input):** Blagburn, J.M. (2020). *A new method of
  recording from the giant fiber of Drosophila melanogaster shows that the
  strength of its auditory inputs remains constant with age.* *PLoS ONE*
  15(1):e0224057. PMID 31951567 · PMCID PMC6946141 · DOI
  `10.1371/journal.pone.0224057`. This paper measures auditory Johnston's organ
  neuron input to GF; it does **not** support a comparison of GF→TTMn versus
  GF→PSI ShakB staining. The previously attributed GF→PSI statement is
  **UNVERIFIED and must not be used** until its actual source is identified.
- Augustin et al. (2017), *Reduced insulin signaling maintains electrical
  transmission in a neural circuit in aging flies*, *PLoS Biology* 15(9):e2001655,
  DOI `10.1371/journal.pbio.2001655`; supports aging-related GFS context, not a
  specific GF→PSI aging effect.

## S-10 · SIZ localisation — **PRIMARY EXPERIMENT**

- **Citation:** Kuehn, C. & Duch, C. (2013). “Putative excitatory and putative
  inhibitory inputs are localised in different dendritic domains in a Drosophila
  flight motoneuron.” *Eur J Neurosci* 37(6):860–875. DOI
  `10.1111/ejn.12104` · PMID 23279094 · PMCID **PMC3604049**
- **Measured:** anti-VGSC (AB5210, anti-SP19) immunocytochemistry + fills +
  confocal co-localisation. **Not electrophysiology.**
- **Figures:** "about **100 µm from the soma**"; "**11 ± 3 µm** around the origin
  of the most distal posterior dendrite", n = 7 (11.25 and 12.1 µm in the two
  reconstructions shown). *"within a distance of about 12 micrometers in either
  direction along the primary neurite from the origin of this dendrite."*
- **Not an exact coordinate** — an immunolabel-derived interval.
- **Raw data:** **none deposited.** No accession, no supplementary data
  statement. Reconstruction export to NEURON is described as a *capability*, not
  a deposit.
- **See C-11:** the project's former 88 ± 15 µm figure does not exist.

## S-11 · MN5 dendritic morphology — **PRIMARY EXPERIMENT**

- **Citation:** von Hoff, F.H. & Duch, C. (2010) — 30 geometric MN5
  reconstructions; **6,716 ± 731 µm** dendritic length, **4,000 ± 577** branches,
  mean dendritic diameter **about 0.44 µm**. The primary article's prose
  explicitly describes dendrites as having “about 0.44 µm average diameter”
  (PMID 20437522; PMCID PMC4441823). The earlier 0.88 µm entry is unsupported;
  no distinct radius, population, or MaleCNS measurement is indicated.
- Cross-check: MaleCNS MN5 `kind=0` median **diameter 0.512 µm**, `kind=2`
  1.436 µm — same order, but not a validation of compartment identity.

## S-12 · In vivo Drosophila voltage imaging of an arbor — **PRIMARY EXPERIMENT**

- **Citation:** Yang, H.H., St-Pierre, F., Sun, X., Ding, X., Lin, M.Z.,
  Clandinin, T.R. (2016). *Cell* 166(1):245–257. PMID 27264607 · PMCID PMC5606228
  · DOI `10.1016/j.cell.2016.05.031`
- **Measured:** ASAP2f voltage along Mi1/Tm3/Tm1/L1/L2 arbors in vivo.
  *"The amplitude of the responses generally decayed away from the site of
  primary synaptic input in layer M1, but the time courses … were largely
  preserved throughout the length of the neuron."*
- **Constrains:** passive (Ri, Rm) sets for **Mi1**, not MN5.
- **Why it matters here:** the closest existing *method* for contact→soma
  transfer, in Drosophila, but a different neuron ~10× smaller.

## S-13 · Insect signal-propagation modelling limits — **PRIMARY EXPERIMENT**

- **Citation:** Gouwens, N.W. & Wilson, M.I. (2009). *J Neurosci* 29(19):6239–6255.
- **Key limitation, verbatim:** *"Electrode recordings are impossible from
  these small processes, so we instead implemented a biophysical model."*;
  *"We assume that spikes are large at the SIZ (although we cannot directly
  test this assumption)."*

## S-14 · navis `split_axon_dendrite` — **PRIMARY MODEL/CODE**

- **Repo:** `navis-org/navis` (note: `natverse/navis` 404s).
  Function `split_axon_dendrite` in `navis/morpho/manipulation.py`.
- **Signature:** `split_axon_dendrite(x, metric="synapse_flow_centrality",
  flow_thresh=0.9, split="prepost", cellbodyfiber=False, reroot_soma=True,
  label_only=False)`
- **Mechanics:** `is_linker = x.nodes[metric] >= x.nodes[metric].max() * flow_thresh`;
  then connected components; axon vs dendrite by `frac_prepost` ratio (>1 ⇒ axon).
- **Output:** per-node *and per-connector* `compartment` ∈ {axon, dendrite,
  linker, cellbodyfiber} — matching the MaleCNS enum plus `unknown`.
- **Determinism:** no RNG, but not robust: ties all enter the linker, orphans
  assigned by `graph._geodesic_nearest`, and it refuses neurons with
  `len(x.root) > 1` (needs `heal_skeleton` first).
- **Source of the algorithm:** Schneider-Mizell et al.

## S-15 · *Manduca* sources — **SECONDARY for this project (wrong species)**

Meseke, Evers & Duch (2009) *J Neurophysiol* 102(1):41–58, PMID 19386754;
Duch & Levine (2000) *J Neurosci* 20(18):6950–6961; Duch, Bayline & Levine
(2000) *Dev Biol*. **All *Manduca sexta*.** Frequently mis-cited as
Drosophila. See C-10.

## S-16 · FlyWire annotations repo — **PRIMARY DATASET (negative result)**

- https://github.com/flyconnectome/flywire_annotations — recursive tree verified
  `truncated:false`. Contains **no** cut-node, compartment or flow-centrality
  file. `morphology_group` was explicitly **removed** in v3.0.0.
- **Conclusion:** FlyWire did **not** release a per-neuron axon/dendrite split
  either. No sister-dataset shortcut exists.

## S-17 · GFS coupling citations that could NOT be verified — **UNVERIFIED**

`Thomas & Spangler 2002`, `Johannes et al.`, `Vogel & Claassen`,
`Adams et al.` — **no matching primary source found for GFS electrical
coupling.** Do not cite. (A real and heavily cited GFS paper is Stebbings,
Alexander & King 2002, PMID 12407015, but it is *behavioural/habituation*, not
an electrical-coupling measurement.)

## S-18 · GFS GAL4 driver validation caveat — **SOURCE MISMATCH / UNVERIFIED**

- The previously supplied citation, Kadas et al. (2012), DOI
  `10.1523/JNEUROSCI.6583-10.2012`, is titled “Constitutive activation of
  Ca2+/calmodulin-dependent protein kinase II during development impairs central
  cholinergic transmission in a circuit underlying escape behavior in
  Drosophila.” Its verified metadata does **not** match the previously
  attributed PSI-specific GAL4-driver-validation claim.
- **Status:** the claim that PSI driver expression was not experimentally
  determined (“data not shown”) is **UNVERIFIED** against this source and must
  not be attributed to Kadas et al. until a matching primary source is found.
- **Safe conclusion:** no PSI-specific driver validation is established by the
  citation currently attached to this claim. This is a source-attribution gap,
  not proof that no such validation exists.

## S-19 · Recombinant Dα7 functional-channel data — **PRIMARY EXPERIMENT**

- **Citation:** Lansdell, S.J., Collins, T., Goodchild, J. & Millar, N.S.
  (2012). “The Drosophila nicotinic acetylcholine receptor subunits Dα5 and
  Dα7 form functional homomeric and heteromeric ion channels.” *BMC
  Neuroscience* 13:73. DOI
  [10.1186/1471-2202-13-73](https://doi.org/10.1186/1471-2202-13-73).
- **Preparation/method:** recombinant Drosophila Dα7 cRNA with *C. elegans*
  RIC-3 (CeRIC-3) expressed in *Xenopus* oocytes; two-electrode voltage clamp
  at −60 mV; ACh dose-response measurements.
- **Dα7 homomer Table 2:** EC50 6.7 ± 1.7 µM; Hill slope 1.0 ± 0.3; n = 4
  independent dose-response fits; maximum current detected 86 nA and mean
  maximum current 45 ± 13 nA across 6–20 oocytes.
- **Source caveat:** the authors report inconsistent functional expression:
  responses >5 nA occurred in about one third of tested oocyte batches, even
  with RIC-3.
- **Relevance:** channel-level pharmacological context only. The current,
  EC50, and Hill slope are not native MN5 conductance, receptor density,
  synaptic kinetics, or PSI→MN5 reversal-potential measurements. No current
  is converted to native conductance in this project.

---

## Cross-dataset MN5 identity note

MN5 is innervates **DLM fibres 5 and 6**, soma in the mesothoracic neuromere of
the VNC — i.e. the **MANC portion** of MaleCNS, not the brain. In the Ehrhardt
et al. wing-MN nomenclature it is **DLMna/b** = MaleCNS bodies **801970 (L)**
and **801295 (R)**. Per-group connectivity published in *eLife* 2025:
169/321 MN groups matched to previous descriptions. No published geometric
transform exists from the Kuehn & Duch Amira frame into MaleCNS EM space —
only identity matching by morphology/hemilineage with a 1–3 confidence rating.
