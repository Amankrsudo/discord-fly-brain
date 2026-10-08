# Spatial Voltage Transfer Evidence Map

**Question:** is there any primary experiment that constrains synaptic-contact →
soma voltage transfer in *Drosophila* MN5?

## ANSWER: NO. SEARCH EXHAUSTED.

Databases: PMC, PubMed, ModelDB, Zenodo, Dryad, Figshare, GitHub, *J Neurosci*,
*eLife*, *PLoS*, *Cell*, *J Neurophysiol*, *Eur J Neurosci*.

Query strings used: `Drosophila MN5 SIZ secondary axon motor neuron`;
`"Isatoz" axon Drosophila`; `Drosophila MN5 sodium channel antibody "spike
initiation zone" 100 µm soma anti-Pan motoneuron`; `Drosophila dendritic patch
clamp motoneuron direct dendritic voltage recording`; `insect motor neuron
dendritic spike direct recording soma axon voltage attenuation cable`; `axon
patch-clamp recording Drosophila neuron axon initial segment direct voltage
recording in vivo`; `"focal" OR "local" dendritic voltage clamp insect motor
neuron named distal process synaptic current measurement`; `Drosophila voltage
indicator ASAP2f ASAP3s in vivo voltage imaging motor neuron arbor`; `Peron 2007
Christensen 2001 insect neuron dendritic signal attenuation locust antennal lobe
Haag Borst`; `site:modeldb.science Drosophila motoneuron MN5 OR DLM OR flight
motor neuron model`.

---

## A · Kuehn & Duch (2013) — *Eur J Neurosci* 37(6):860–875, PMC3604049 · *Drosophila, MN5*

- **Measured:** anti-para (VGSC) immunolabel intensity vs position, mapped onto
  geometric reconstructions; synapse-density maps vs distance to the putative SIZ.
- **NOT measured:** any voltage at any point. The paper gives distance as a
  *reason the measurement is interesting*, verbatim: *"These parameters were
  evaluated because branching structure and distance from the SIZ are important
  parameters for the passive propagation of postsynaptic potentials."*
- **Constrains transfer quantitatively? NO** — zero transfer coefficient.
- **Anatomy: unusually good.** 23 dendritic sub-trees; 4,000 ± 577 branches;
  6,716 ± 731 µm total length (n=30, von Hoff & Duch 2010); cholinergic inputs
  peak **25–65 µm from the SIZ**; the closest 20 µm of dendrite carries elevated
  Rdl-GABA_A density; a **52 ± 4 µm gap** between the most proximal cholinergic
  and most distal GABAergic sub-tree.
- **Value:** this is the *geometry* a future transfer measurement would need —
  which contact sits how far from the spike-initiation region.

## B · Ryglewski & Duch (2009) — *J Neurophysiol* 102(6):3673–3688, PMC2804405

**The closest thing to a contact→soma transfer constraint for MN5 — but it is a
simulation, not a measurement.**

- **Method, verbatim:** *"every dendrite, the axon, and the soma were injected
  with steady-state rectangular current pulses, and the resulting current as
  measured from the soma of the model neuron was divided by the current resulting
  from a similar current injection directly into the soma. The resulting ratio
  indicated the relative current transfer from each segment to the soma of MN5. In
  Fig 1B, each segment is color coded for this ratio. Scale bar from 0.2 (cyan) to
  1 (red)."*
- **Result:** *"the distal dendrites show a slightly lower relative current
  transfer, at similar values as the axon."*
- **What it is NOT:** a steady-state **current**-transfer ratio, not a synaptic
  **voltage** transfer; and it runs on **Manduca-derived** Ra = 90 Ω·cm and
  Cm = 1.15 µF/cm² adopted by assertion.
- **Authors' own caveat:** *"These models were not intended to provide exact
  estimates of how much current from distal processes can be seen in somatic
  voltage-clamp recordings."*
- **Provenance:** `MDE` on `MA`/`LDP` inputs. **Never** to be reported as a
  measurement or converted into an attenuation factor.

## C · Fayyazuddin et al. (2006) — *PLoS Biol* 4(3):e63

**Focal stimulation of a named distal process with somatic recording — but on the
axon, and the distance is not quantified.**

- *"the PSI **bypasses the entire dendritic structure of MN5** and makes multiple
  synaptic contacts that **span 50 µm** and follow the axons out into the
  **posterior dorsal motor nerve**."*
- *"the action potential generated at the distal PSI-DLMmn synapse on the axon
  appeared **small and broad** in somatic recordings … suggesting that the
  peripherally generated action potential **fails to propagate antidromically into
  the dendrite** and therefore is filtered by the passive membrane properties."*
- **Measured:** somatic EPSP 4.71 ± 0.35 mV (n=10) at −74 mV; Cm 43 ± 2 pF;
  Rin 102 ± 12 MΩ.
- **NOT measured:** voltage at the contact; any transfer coefficient. The contact
  is on the **peripheral axon**, and the contact→soma distance is given only as
  "spans 50 µm" of nerve, **not as a soma-referenced length**.
- **Constrains transfer quantitatively? NO.** It is a lower bound of the wrong
  kind: a distal synaptic event reaches the soma suprathreshold, but with the
  distal amplitude unreported no attenuation factor can be derived. The "fails to
  propagate antidromically" statement is qualitative and refers to axon→dendrite.

## D · Yang et al. (2016) — *Cell* 166(1):245–257, PMC5606228

**The only in vivo Drosophila measurement of input-site-to-distal-site voltage
decay along an arbor. Not MN5.**

- ASAP2f voltage, single voxels, in Mi1 / Tm3 / Tm1 / L1 / L2, 25 ms flashes.
- *"**The amplitude of the responses generally decayed away from the site of
  primary synaptic input in layer M1, but the time courses of the response
  waveforms were largely preserved throughout the length of the neuron.**"*
- **Constrains transfer? YES, but for a different cell** — the attenuation was then
  used to **constrain** passive parameters (Ri swept 40–420 Ω·cm, Rm 1–21 kΩ·cm²)
  on the Takemura 2013 Mi1 EM morphology, not derived from them.
- **Anatomy reported:** Mi1 ≈ 50 µm long, main neurite 200–300 nm diameter, arbor
  processes ≤ 200 nm. That is ~10× smaller than the MN5 arbor.
- **Why it matters:** it is the realistic method template for a first MN5
  measurement, because Gouwens & Wilson 2009 established that electrode access to
  insect processes is generally impossible.

## E · Adjacent methods (not MN5)

| Study | System | What |
|---|---|---|
| Chamberland+ 2017 *eLife* 6:e25690 | Drosophila L1/L2 | ASAP2s two-photon, 25 locations on the dendritic tree, 686 Hz, 31-trial averages. Method precedent. |
| Gouwens & Wilson 2009 *J Neurosci* 29:6239 | Drosophila DM1 PN, antennal-lobe LN | *"Electrode recordings are impossible from these small processes"*; *"We assume that spikes are large at the SIZ (although we cannot directly test this assumption)."* |
| Fushiki+ 2016 *eLife* 5:e13253 | Drosophila larva aCC | Single-site somatic recording of an MN driven by a named presynaptic MN's somatically-driven APs. Contact→soma distance not reported. |
| Moreaux & Laurent 2007 *Front Neural Circuits* 1:2 | locust antennal-lobe PN | **Calcium**, not voltage, from dendritic signals at 500–750 Hz. |
| Peron 2007; Christensen+ 2001; Haag & Borst 1996 | blowfly/locust | Cited by Gouwens & Wilson for poor dendritic signal propagation. Not voltage-transfer measurements. |

---

## Strongest available substitutes, ranked

1. **Yang 2016** — a genuine in vivo Drosophila measurement of input-site-to-distal
   voltage decay, with a quantitative passive-parameter constraint. Wrong neuron.
2. **Ryglewski & Duch 2009 Fig 1B** — the only per-compartment contact→soma transfer
   map for MN5 itself. Simulated, on adopted non-MN5 parameters, and reports
   **steady-state current**, not synaptic voltage.
3. **Kuehn & Duch 2013** — the geometry (which contacts sit 25–65 µm from the SIZ)
   that any future measurement would need, plus an explicit statement that
   propagation is unresolved.

## What would resolve it

**Dual-site recording:** somatic whole-cell plus a direct patch on the MN5 process
carrying an identified PSI contact, during focal PSI stimulation. Voltage at the
contact and at the soma measured simultaneously gives the transfer ratio **for
that contact**, and sweeping stimulation across contacts gives the distance
dependence. Given the demonstrated difficulty of dendritic access in insect
neurons, the realistic first step is **ASAP2f imaging** along the MaleCNS MN5
arbor (Yang 2016 template), with focal stimulation at contacts whose position on
the arbor is known from the EM reconstruction.

This is **M-02** in `missing_evidence.md` and is the shortest path to opening the
first gate.
