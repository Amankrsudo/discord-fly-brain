# PSI→MN5 Synaptic Reversal Potential Audit

## Question and conclusion

Can existing evidence constrain the PSI→MN5 synaptic reversal potential
(`E_syn`) or effective cholinergic driving force? **No direct quantitative
constraint was found.** The current exploratory interval, −15 to +10 mV, should
remain unchanged for reproducibility, but it is an **exploratory model
assumption**, not a biological or MN5-specific range. The available sources do
not justify narrowing it, and they do not establish that its endpoints bound
the native synapse.

No native PSI→MN5 synaptic conductance, Dα7 biological conductance, Dα7
kinetics, or PSI→MN5 spatial voltage attenuation is estimated here. The
PSI→MN5 postsynaptic spatial-voltage-transfer gate and the Dα7 biological
conductance gate remain **NOT AUTHORIZED**.

## Evidence table

| Source | Preparation, synapse and method | What was actually measured or specified | Evidence class | Relevance to `E_syn` and limitation |
|---|---|---|---|---|
| Fayyazuddin, A., Zaheer, M.A., Hiesinger, P.R. & Bellen, H.J. (2006), “The nicotinic acetylcholine receptor Dα7 is required for an escape behavior in *Drosophila*,” *PLoS Biology* 4(3):e63. [DOI: 10.1371/journal.pbio.0040063](https://doi.org/10.1371/journal.pbio.0040063), PMID 16494528, PMCID PMC1382016. | Adult *Drosophila* giant-fiber circuit; somatic whole-cell recordings from MN5 in an exposed thoracic-ganglion preparation, with the GF electrically stimulated through eye electrodes. Comparisons also used Dα7 mutant alleles and rescue. | Somatic EPSP amplitude underlying the spike: 4.71 ± 0.35 mV (n=10) in wild type and 1.5 ± 0.32 mV (n=7) in `gfA1`; circuit following/failure and genetic effects were also measured. | Native experimental measurement (EPSP and circuit/genetic effects). | Directly relevant to the pathway and supports Dα7 involvement, but the stimulus was GF, not focal PSI; the readout is a filtered somatic potential. It is current-clamp amplitude evidence, not a voltage-clamp I–V or reversal measurement. One EPSP amplitude at one operating point cannot identify a reversal potential or driving force. |
| Augustin, H., Allen, M.J. & Partridge, L. (2011), “Electrophysiological recordings from the giant fiber pathway of *D. melanogaster*,” *Journal of Visualized Experiments* 54:e1709. [DOI: 10.3791/1709](https://doi.org/10.3791/1709), PMCID PMC3182647. | Adult fly GFS recording protocol; electrical GF stimulation and pathway/muscle recordings. | Describes electrophysiological recording of circuit responses and the chemical PSI→DLM-motoneuron connection. | Primary-method source; pathway response measurements are native experimental evidence. | Identifies the relevant circuit context and method, not a PSI→MN5 voltage-clamp series. No synaptic I–V or reversal value is reported in the project’s source notes. |
| Mejia, M., Heghinian, M.D., Marí, F. & Godenschwege, T.A. (2013), “New tools for targeted disruption of cholinergic synaptic transmission in *Drosophila melanogaster*,” *PLOS ONE* 8(5):e60049. [DOI: 10.1371/journal.pone.0060049](https://doi.org/10.1371/journal.pone.0060049), PMCID PMC3667824. | *Drosophila* GFS; genetic manipulation of Dα7 and electrophysiological pathway-output assays. | Tests effects of cholinergic-transmission disruption on GFS function. | Native experimental/genetic evidence. | Relevant to cholinergic/Dα7 dependence, but pathway output is not an MN5 voltage-clamp I–V. It supplies no reversal or quantitative driving-force constraint. |
| Augustin, H., Zylbertal, A. & Partridge, L. (2019), “Aging-associated changes in the function of the Drosophila giant fiber system,” *eNeuro* 6(2):ENEURO.0423-18.2019. [DOI: 10.1523/ENEURO.0423-18.2019](https://doi.org/10.1523/ENEURO.0423-18.2019), PMID 31001574, PMCID PMC6469880; associated model: [ModelDB 245415](https://modeldb.science/245415). | Adult GFS evidence plus a conductance-based computational model; model includes a chemical PSI→DLMn synapse. | In the model code, `DLMn_syn_e` is assigned `0` mV (`gfpn.py`, default parameter set). This is a simulator input; the model’s principal measured comparison is pathway latency, not an EPSP reversal. | Model assumption, not a biological measurement. | Demonstrates use of 0 mV as a modeling convention in a different GFS model. It does not show that the authors measured that value, and it cannot establish native PSI→MN5 `E_syn`. |
| Gorczyca & Hall (1984), *Journal of Neurogenetics* 1:289; cited in the project’s [Dα7 evidence notes](./da7_evidence.md). | Reported in those notes as conditional `cha`/choline-acetyltransferase evidence for transmitter identity. | Existing project notes cite it as support for acetylcholine at PSI→MN5; the primary article/full text and complete bibliographic details were not independently verified for this audit. | Secondary-cited primary evidence; status not independently verified here. | Potential support for cholinergic identity only. No reversal-potential measurement is documented in the project notes. It is not used to assign a numerical `E_syn`. |
| Couturier et al. (1990), *Neuron* 5:847, PMID 1702646; summarized in the project’s [Dα7 evidence notes](./da7_evidence.md). | Chick α7 receptor expressed in *Xenopus* oocytes (heterologous system). | Receptor/channel properties in that non-fly system. | Heterologous experimental evidence. | Different species, receptor preparation, and ionic environment; no same-preparation MN5 or PSI→MN5 measurement. No numerical result from it is transferred into the model range. |

## Direct versus indirect evidence

1. **Directly measured PSI→MN5 synaptic reversal potential?** No qualifying
   measurement found.
2. **PSI→MN5 EPSP reversal or synaptic I–V relation?** None found. The MN5 EPSP
   in Fayyazuddin et al. is a somatic current-clamp voltage response to GF
   stimulation. It is not a holding-potential series. A single EPSP amplitude
   does not determine a reversal potential.
3. **Pharmacological or ionic manipulation that constrains reversal?** No
   PSI→MN5 pharmacological/ionic reversal experiment is documented in the
   examined project sources. Dα7 allele and rescue experiments address pathway
   function/receptor involvement, not ionic reversal.
4. **Evidence for cholinergic transmission?** The PSI→DLM-motoneuron connection
   is described as chemical/cholinergic in the GFS literature and project
   sources; Dα7-dependent genetic effects provide supporting pathway/receptor
   evidence. This is evidence about transmitter/receptor identity, not an
   `E_syn` measurement. The cited `cha` source remains secondary-cited in this
   project, and its primary text was not verified here.
5. **Relevant native Dα7 channel reversal measured in the same preparation?**
   None found. The project’s Dα7 evidence notes list heterologous or
   cross-species receptor studies, not a native PSI→MN5 channel measurement.
6. **Defensible literature-derived numerical interval?** No primary source
   examined here establishes a quantitative interval for native PSI→MN5. A
   generic or vertebrate nicotinic-channel reversal cannot be transferred
   across species, receptor composition, ionic solutions, and preparation as
   if it were an MN5 measurement.

## Status of the existing model range

The exploratory parameter table carries `E_syn = −15 to +10 mV`, nominal
0 mV, and labels it a generic cholinergic exploratory range. Its note refers
to a generic vertebrate α7 value but does not identify the primary measurement
or experimental ionic conditions supporting either endpoint. The older GFS
model’s `DLMn_syn_e = 0` is an assigned model parameter, not experimental
evidence. Thus:

- **Do not change the numerical exploratory interval on this audit.** There is
  no relevant evidence for a defensible narrower interval.
- **Do not call the interval literature-constrained for PSI→MN5.** Its endpoints
  and nominal value remain model choices/assumptions; they are not a biological
  bound, a measured reversal, or a native driving force.
- The model’s driving force is conditional on its assumed `E_syn` and modeled
  local membrane voltage. It is not measured biological driving force and does
  not resolve spatial voltage transfer.
- This audit does not modify the exploratory model, its parameters, the
  evidence ledger, or the conflict register. It identifies no new
  measurement-status change and no genuine numerical conflict.

## What would constrain it

A focal PSI-evoked MN5 synaptic current or response measured over controlled
postsynaptic holding potentials, with adequate control of series resistance,
ionic conditions, and the distal synapse’s voltage-clamp error, could locate an
EPSC reversal or a synaptic I–V relation. Because the synapse is distal, a
somatic series alone may not equal the local synaptic reversal without
addressing space-clamp limitations. This is a description of missing evidence,
not a proposal to infer or model conductance from the existing EPSP.

## Final status

- PSI→MN5 reversal potential: **UNKNOWN**.
- PSI→MN5 EPSP I–V / reversal: **NOT MEASURED in the evidence reviewed**.
- Existing exploratory `E_syn` interval (−15 to +10 mV): **RETAIN unchanged
  as an assumption; not biologically constrained**.
- Native PSI synaptic conductance: **not estimated**.
- Dα7 biological conductance, density, and kinetics: **not estimated**.
- PSI→MN5 postsynaptic spatial voltage transfer: **NOT AUTHORIZED**.
- Dα7 biological conductance: **NOT AUTHORIZED**.
