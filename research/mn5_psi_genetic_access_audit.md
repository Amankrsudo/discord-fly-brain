# MN5 and PSI Genetic-Tool Access Audit

## Scope and conclusion

This audit asks whether documented tools currently support (1) adult MN5-specific
GEVI expression or identification and (2) selective PSI activation. It evaluates
source-reported experiments and bounded official stock-catalog searches; a tool
name or catalog record alone is not treated as evidence of cellular specificity.

**Conclusion:** Adult MN5 soma identification by retrograde muscle backfill is
directly supported. A Dα7 enhancer-trap reporter is directly reported in the
DLM-motoneuron population, but is not MN5-specific and is not evidence of native
Dα7 protein. GEVI imaging is demonstrated in other adult fly neurons, not MN5.
OK307-GAL4 includes PSI among several GFS elements and is not selective. The
primary source that used `cha-GAL4` explicitly says PSI expression was the
exception not experimentally verified. No PSI-specific driver or PSI-selective
activation tool was verified in the searched sources.

**A practical MN5-plus-PSI optical experiment is not currently supported as a
validated tool combination.** Existing work supports individual method
components in other cells or broader populations; it does not demonstrate GEVI
expression in MN5 together with selective PSI activation.

## Evidence categories

- **Catalog metadata:** what the official Bloomington Drosophila Stock Center
  (BDSC) search record says; this does not establish expression specificity.
- **Source-reported experimental validation:** what a primary paper reports
  being expressed, labelled, stimulated, or experimentally checked.
- **Analyst feasibility assessment:** whether those separate facts are enough
  for the proposed MN5-plus-PSI experiment. This is not experimental evidence.

## Candidate tools and evidence

| Candidate/tool | Identifier or stock | Reported expression/access | Stage and preparation | Specificity validation and classification | Limitations |
|---|---|---|---|---|---|
| Retrograde Texas-red dextran backfill | No genetic driver or stock; no catalog ID applicable | Labels MN5 from the DLMa/b muscle target; used to identify the recorded MN5 soma | Adult *Drosophila*, dissected thoracic preparation; Fayyazuddin et al. (2006) | **Directly supported** for anatomical identification of the soma in that preparation. It is not genetic access and does not establish GEVI expression. | Does not identify the distal PSI-contact-bearing process in a living fly or make expression MN5-specific. |
| Dα7 enhancer-trap GAL4 (GAL4 P-element conversion of KG3295) | Exact BDSC stock identifier not reported in the source; no BDSC/FlyBase stock query for this line was completed | Fayyazuddin et al. report generating the enhancer trap and that its reporter pattern matched Dα7 immunostaining. Project source notes describe labeling MN5 and other DLM motoneurons. | *Drosophila* giant-fiber-circuit tissue; the paper's adult circuit experiments do not establish validation in every adult optical preparation. Exact reporter-image age/conditions were not established here. | **Directly supported** as a reporter line with a DLM-motoneuron-associated pattern; **not supported as MN5-specific**. | A regulatory reporter is not endogenous Dα7 protein. No GEVI expression, MN5-only specificity, or PSI-selective actuation was demonstrated. |
| DLMn Split-GAL4 | Existing optical-design audit names the population but gives no exact driver genotype, stock ID, or primary citation; BDSC search for “DLMn” returned no records | The prior audit describes access to MN1–MN5 as a population. | Adult access in the relevant preparation was not traceable to a named primary experiment in this search. | **Unverified in searched sources** as a specific line or directly validated tool claim. The asserted population-level access cannot be promoted to MN5-specific access. | A population label would not distinguish MN5 from MN1–MN4. The search result is not proof that no such line exists. |
| OK307-GAL4 | Exact BDSC stock identifier not reported in the examined primary source; BDSC search for “OK307” returned no records | Fayyazuddin et al. report expression in “several elements” of the GFS, including GF, DLM motoneurons, TTM motoneurons, and PSI. Their rescue used broad circuit access. | Adult GFS physiology and rescue experiments in *Drosophila*. | **Directly supported** as broad GFS access including PSI and DLMmn; **not selective** for PSI or MN5. | Broad expression means an actuator under this driver would not establish PSI-selective activation. Catalog search did not verify a current stock number. |
| c17-GAL4 | Exact BDSC stock identifier not reported in the examined source; no BDSC/FlyBase stock query for this line was completed | Used as the GF-restricted driver in the Fayyazuddin rescue comparison; project notes identify it as GF-specific. | Adult GFS rescue/physiology in *Drosophila*. | **Directly supported** for the reported GF-targeted rescue role; not a PSI driver. | GF access is not PSI-specific activation. Does not target MN5 selectively. |
| `cha-GAL4` | Exact BDSC stock identifier not reported in the examined source; catalog query not completed successfully | Kadas et al. list cholinergic-neuron expression. They explicitly state their GFS drivers were checked except for PSI, whose driver expression was not experimentally verified (“data not shown”). | GFS transgene experiments in *Drosophila*; driver validation statement is not a cell-resolved adult PSI validation. | **Indirectly supported** as a broad cholinergic driver candidate; **unverified in searched sources** for PSI expression. | Do not treat the driver label, cholinergic identity, or pathway response as proof of expression in PSI. Not a selective PSI actuator. |
| ASAP2f GEVI | Indicator construct; no MN5-specific construct/driver combination reported in the cited experimental sources; no stock query completed | Voltage signals reported across compartments of Mi1/Tm3/Tm1/L1/L2 visual neurons. | Adult *Drosophila* visual system, in vivo; Yang et al. (2016). | **Directly supported** for GEVI imaging in those adult visual neurons; adult MN5 expression **not verified in searched sources**. | Different neurons and tissue; not an MN5 driver, not PSI activation, and not evidence that the construct works in MN5. |
| ASAP2s GEVI | Indicator construct; no MN5-specific construct/driver combination reported in the cited experimental sources; no stock query completed | Two-photon voltage imaging reported in fly visual neurons, including L2 axon terminals; additional compartmental work was in slices. | *Drosophila* visual system; Chamberland et al. (2017). | **Directly supported** for the reported visual-neuron preparations; adult MN5 expression **not verified in searched sources**. | Does not establish expression, calibration, or performance in MN5 or a thoracic motor nerve. |
| ASAP5 GEVI | Indicator candidate; no MN5-specific construct/driver combination reported in the cited experimental sources; no stock query completed | Existing optical-design audit reports cultured-neuron sensitivity work and a *Drosophila* Mi1 comparison. | Cultured neurons and *Drosophila* visual-neuron work; not MN5. | **Directly supported** only for source-reported non-MN5 tests; adult MN5 expression **not verified in searched sources**. | The sensitivity result is not transferable to MN5, and no PSI activation is provided by the indicator. |
| GF electrical stimulation | Eye-electrode stimulation; no driver/stock | Directly activates the GF; PSI is recruited downstream through the GF–PSI pathway. | Adult *Drosophila* GFS physiology; Fayyazuddin et al. (2006). | **Directly supported** for GF stimulation; **not** PSI-selective activation. | A downstream PSI contribution does not make the stimulus PSI-specific; it recruits the circuit. |
| Focal/electrical stimulation at PSI | No named tool, stock, or PSI-specific validation found | Proposed in existing experiment-design audits as a possible approach, subject to confinement and off-target controls. | Proposed future experiment; no qualifying PSI-specific demonstration identified. | **Indirectly supported** as a proposed method only; **unverified in searched sources** as a validated PSI-specific tool. | Current spread, passing axons, and network recruitment must be excluded experimentally; cannot be treated as an established PSI stimulus method. |

## Source-specific findings

### MN5 access and identification

Fayyazuddin et al. (2006), “The nicotinic acetylcholine receptor Dα7 is required
for an escape behavior in *Drosophila*,” *PLoS Biology* 4(3):e63,
[DOI 10.1371/journal.pbio.0040063](https://doi.org/10.1371/journal.pbio.0040063),
[PMID 16494528 / PMCID PMC1382016](https://pmc.ncbi.nlm.nih.gov/articles/PMC1382016/),
used retrograde Texas-red dextran labelling from DLMa/b muscles to identify MN5
for adult in-situ soma recordings. This is the strongest directly supported
MN5-identification method found; it does not provide genetic specificity or a
label for the distal process.

The same paper reports a Dα7 enhancer-trap GAL4 made by converting the KG3295
P-element, with reporter staining matching antibody staining. This supports a
Dα7-locus reporter pattern, not endogenous protein attribution or an MN5-only
driver. The broad OK307-GAL4 rescue is explicitly described as covering GF,
DLMmn, TTMmn, and PSI; its result therefore does not localize the rescue to MN5
or PSI.

### PSI driver validation

Kadas et al. (2012), *Journal of Neuroscience* 32(1):170–182,
[DOI 10.1523/JNEUROSCI.6583-10.2012](https://doi.org/10.1523/JNEUROSCI.6583-10.2012),
[PMID 22219280 / PMCID PMC6621333](https://pmc.ncbi.nlm.nih.gov/articles/PMC6621333/),
state that they verified their GFS GAL4 drivers in intended cells except for
PSI, which was the one unverified case; they also note expression could occur
elsewhere in the CNS. Thus their use of GAL4/UAS in GFS does not establish a
PSI-specific driver. The paper's `cha-GAL4` experiments are broad cholinergic
driver experiments, not selective PSI access.

No primary source reviewed here reports optogenetic activation through a
validated PSI-specific driver. GF stimulation is directly supported, but it
activates GF rather than selectively stimulating PSI. Direct focal PSI
stimulation remains a proposal requiring specificity controls.

### GEVI evidence and official stock catalog

The existing optical-design audit's GEVIs—ASAP2f, ASAP2s, and ASAP5—have
source-reported demonstrations outside MN5. Specifically, ASAP2f was imaged in
adult fly visual neurons (Yang et al., 2016, *Cell* 166:245–257,
[DOI 10.1016/j.cell.2016.05.031](https://doi.org/10.1016/j.cell.2016.05.031),
[PMCID PMC5606228](https://pmc.ncbi.nlm.nih.gov/articles/PMC5606228/)); ASAP2s
was tested in fly visual-neuron preparations (Chamberland et al., 2017,
*eLife* 6:e25690,
[DOI 10.7554/eLife.25690](https://doi.org/10.7554/eLife.25690)); and ASAP5's
reported Drosophila comparison was in Mi1, not MN5. These are method precedents,
not MN5 expression evidence. No construct stock identifier for an MN5 GEVI
combination was verified.

The official BDSC search interface
([BDSC stock search](https://bdsc.indiana.edu/Home/Search)) was queried on
2026-10-06 with the exact text `OK307` and `DLMn`; each completed query returned
no records. The `cha-GAL4` query was attempted but not completed successfully,
so no result is reported for it. No targeted BDSC or FlyBase stock query was
completed for the Dα7 enhancer-trap, c17-GAL4, or any GEVI construct. These are
search-scope limits, not evidence that a corresponding stock does not exist.
No stock number was verified for any candidate in this audit.

## Provenance classification by candidate

- **Retrograde backfill:** primary experimental evidence is Fayyazuddin et al.'s
  adult MN5 soma-identification/recording preparation. Catalog metadata is not
  applicable. Calling it a soma-identification method, not a genetic driver, is
  analyst classification.
- **Dα7 enhancer-trap GAL4:** primary experimental evidence is the reported
  P-element conversion and reporter/immunostaining pattern; the project Dα7
  notes are source-context evidence for the labeled DLM-motoneuron population.
  No stock-catalog search was completed for this line. The conclusion that
  population labeling is not MN5-specific, and that reporter signal is not
  proof of endogenous protein, is analyst interpretation.
- **DLMn Split-GAL4:** the population-access statement appears in the previous
  project optical-design audit, but no exact genotype or primary experimental
  citation was verified here. BDSC `DLMn` metadata returned no record in that
  bounded exact-text query. Treating the line/access claim as unverified is
  analyst classification, not a nonexistence claim.
- **OK307-GAL4:** primary experimental evidence is Fayyazuddin et al.'s
  source-reported expression in multiple GFS elements and broad rescue.
  BDSC `OK307` metadata returned no record in the bounded exact-text query.
  The conclusion that multi-element expression is not PSI-selective is analyst
  synthesis from the reported expression domain.
- **c17-GAL4:** primary experimental evidence supports its use in the GF-targeted
  rescue comparison; no stock-catalog query was completed. Its non-PSI status
  follows from the source-reported GF targeting and is analyst interpretation.
- **`cha-GAL4`:** primary experimental evidence is Kadas et al.'s statement
  that PSI driver expression was not experimentally verified. The BDSC query
  was incomplete and provides no catalog result. Treating it as unverified for
  PSI is an evidence-status classification, not an assertion of absence.
- **ASAP2f, ASAP2s, and ASAP5:** primary experimental evidence supports the
  cited non-MN5 *Drosophila* visual-neuron demonstrations (and, for ASAP5,
  cultured-neuron work). No targeted BDSC/FlyBase construct search was
  completed. Their relevance as method precedents, but not evidence of adult
  MN5 expression, is analyst synthesis.
- **GF electrical stimulation:** primary experimental evidence is the
  eye-electrode stimulation of GF reported by Fayyazuddin et al.; calling it
  non-selective for PSI follows from the directly stimulated cell and circuit
  recruitment and is analyst interpretation.
- **Focal/electrical PSI stimulation:** this is an analyst-proposed experiment,
  not primary experimental evidence or catalog metadata. No validated
  PSI-selective method was found in the sources reviewed.

## Classification summary

- **Directly supported:** adult MN5 soma identification by muscle backfill;
  Dα7-enhancer-trap reporter pattern in the DLM-motoneuron context; broad
  OK307-GAL4 access including PSI and DLMmn; GF activation by eye electrodes;
  GEVI method demonstrations in other fly neurons.
- **Indirectly supported:** `cha-GAL4` as a broad cholinergic driver candidate;
  focal/electrical PSI stimulation as an unvalidated proposed method.
- **Unverified in searched sources:** a named DLMn Split-GAL4 line with a
  source/stock record; an MN5-specific driver; adult MN5 GEVI expression;
  PSI expression validation for `cha-GAL4`; PSI-selective optogenetic activation;
  a validated combined MN5-GEVI plus PSI-selective activation preparation.

## Limits, gates, and stopping status

No conductance, reversal potential, spatial voltage transfer, voltage value,
or Dα7 biological property is introduced or inferred. A fluorescent reporter
pattern is not used to infer Dα7 protein. The audit does not reinterpret SWC
Type, the GFS conductance conflict, MN1→MN5 coupling, or the PSI→MN5 reversal
potential.

The source audit is complete within the stated scope. Stock searching is not
comprehensive: completed BDSC exact-text queries, the incomplete `cha-GAL4`
query, and the unsearched BDSC/FlyBase candidate lines are distinguished above.
Unverified specificity is reported as **“not verified in searched sources”**,
not as proof of nonexistence.

PSI→MN5 postsynaptic spatial voltage transfer: **NOT AUTHORIZED**

Dα7 biological conductance: **NOT AUTHORIZED**

## References

1. Fayyazuddin, A. et al. (2006). *PLoS Biol* 4(3):e63.
   DOI `10.1371/journal.pbio.0040063`; PMID 16494528; PMCID PMC1382016.
2. Kadas, D. et al. (2012). *J Neurosci* 32(1):170–182.
   DOI `10.1523/JNEUROSCI.6583-10.2012`; PMID 22219280; PMCID PMC6621333.
3. Yang, H.H. et al. (2016). *Cell* 166(1):245–257.
   DOI `10.1016/j.cell.2016.05.031`; PMID 27264607; PMCID PMC5606228.
4. Chamberland, S. et al. (2017). *eLife* 6:e25690.
   DOI `10.7554/eLife.25690`.
5. Hao et al. (2024). ASAP5 study, *Neuron* 112(22).
   [Cell Press article](https://www.cell.com/neuron/fulltext/S0896-6273(24)00643-3).
6. Bloomington Drosophila Stock Center, official [stock search](https://bdsc.indiana.edu/Home/Search);
   bounded searches executed 2026-10-06.
