# Claim language standard

Use these patterns consistently in the manuscript, figure captions, tables, and supplement. Replace bracketed fields only with values tied to the pinned source artifact.

## Approved wording

### Literature-derived measurements

> “Author et al. reported [quantity] of [value and units] in [biological object/preparation; n and statistic where available]. This is a literature-derived measurement and is not a measurement of [different object or pathway].”

For the 4.71 ± 0.35 mV value:

> “The reported 4.71 ± 0.35 mV somatic EPSP was recorded under GF stimulation. We use it only as a comparison/calibration target; it is not a PSI-specific EPSP.”

### MaleCNS-derived anatomy

> “In MaleCNS v1.0, at minimum confidence 0.5, we identified 43 PSI→MN5 contacts: 17 for body pairing 802401→801970 and 26 for 903327→801295.”

> “The official `compartment_post` field is labeled `axon` for all 43 contacts. This reports the dataset annotation and does not establish electrophysiological compartment identity or voltage transfer.”

### Repository-derived software behavior

> “In the pinned repository snapshot, [module/function] implements [specific behavior] under [declared configuration]. This statement describes software behavior.”

### Model-derived voltage/sensitivity outputs

> “Under the stated model structure and parameter grid, the model produced [output/range/count]. These are model-derived outcomes conditional on the listed assumptions; they are not native physiological measurements.”

### Conditional model analysis

> “We performed a **model-authorized conditional analysis** using [explicit abstract bridge/assumption set]. The analysis is permitted to execute under those assumptions; its outputs remain model-derived and do not establish native physiology.”

### Unresolved evidence

> “[Quantity] remains unresolved/unmeasured in the reviewed evidence. We retain the documented alternatives [A] and [B] without selecting a preferred value.”

For C-02/C-03, retain the repository mapping: **C-02 is the gap-junction unit discrepancy; C-03 is the PSI→DLMn chemical-synapse discrepancy.**

### Software validation

> “The tests verify [code path/invariant/data parsing] against the stated assertions/fixtures. This is software validation and is not empirical biological validation.”

## Prohibited wording

Do not write:

- “The model was experimentally validated” or “biologically validated” based on software tests, numerical convergence, an EPSP fit, or model threshold crossings.
- “We measured native PSI→MN5 transfer,” “measured voltage attenuation,” or “determined the contact-to-soma path” from the abstract bridge or MaleCNS annotation.
- “We measured native Dα7 conductance/density/kinetics” from assumed effective conductance sweeps or recombinant oocyte currents.
- “The SIZ was registered to MaleCNS,” or a biological interpretation of SWC `kind`/Type codes not supported by source documentation.
- “C-01/C-02/C-03 was resolved,” “the correct capacitance/conductance is [one side],” or any unmeasured absolute ShakB conductance.
- “PSI contacts are electrophysiologically axonal” based only on `compartment_post="axon"`.
- “The 4.71 mV EPSP is a PSI EPSP,” “the crossings estimate escape probability,” or “the simulated thresholds predict native behavior.”

## Key distinction

**Model-authorized conditional analysis** means a declared model can execute a calculation under assumptions. **Experimentally validated native physiology** would require independent biological measurements validating the relevant native quantity. The former does not imply the latter.
