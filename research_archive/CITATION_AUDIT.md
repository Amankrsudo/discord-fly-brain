# Citation metadata audit

Audit date: **2026-10-12** (updated after targeted primary-record checks). Audit basis: repository-local `3.0_RELEASE_SPEC.md`, `research/source_registry.md`, parameter/model research records, `CITATION.cff`, and `paper/references.bib`, plus targeted publisher/PubMed/PMC metadata checks. This is a partial audit; unchecked entries remain explicitly unresolved.

## CITATION.cff

| Field | Repository evidence | Audit |
|---|---|---|
| `cff-version` | CFF schema version is explicitly recorded in the file | Present as 1.2.0; schema validation was not run. |
| `title` | Project name “Fly Brain 3.0” appears in the authoritative release specification | Present as `Fly Brain 3.0`; **VERIFY_REQUIRED** that this is the intended citable software release title. |
| `type` | Release specification defines a software/modeling project | `software` is a reasonable package classification, but **VERIFY_REQUIRED** for the final citation record. |
| `authors` | No project author/contributor list or ORCIDs were found in the consulted release/source records | Empty. **VERIFY_REQUIRED**. Do not infer from Git commit authors. |
| version, release date, repository URL, DOI | No archival release/version/DOI/URL is established by the cited records | Missing by design. **VERIFY_REQUIRED** after the snapshot is frozen. |
| license | Repository license/attribution evidence for the whole software project is not established by the cited records | Omitted. **VERIFY_REQUIRED** before public release. |

The CFF is an incomplete draft, not a valid final citation package. Do not cite it as a released version.

## paper/references.bib

Entries below were checked only against repository records. A field's presence in the BibTeX file does not make it externally verified.

| BibTeX key | Registry match | Fields requiring verification |
|---|---|---|
| `Berg2026MaleCNS`, `MaleCNSv1` | S-01: paper title, journal, year, volume/issue/pages, DOI, dataset v1.0 | Complete author list and preferred dataset citation; dataset entry reuses paper attribution only as a provisional record. **VERIFY_REQUIRED**. |
| `Mehta2023SWC` | Publisher/PubMed record checked | Title, seven authors, journal, year, volume/issue/article number, DOI, PMID 37973857 and PMCID PMC10654402 match the indexed record; final eNeuro formatting remains. |
| `RyglewskiKiloDuch2014` | PubMed/PMC primary record checked | Added the missing entry with title, authors, *European Journal of Neuroscience* 39(10):1572–1585, DOI 10.1111/ejn.12517, PMID 24620836 and PMCID PMC4433752. Sources: https://pubmed.ncbi.nlm.nih.gov/24620836/ and https://pmc.ncbi.nlm.nih.gov/articles/PMC4433752/. This is the postembryonic MN5 maturation paper; ensure the manuscript's specific reported measurements are supported by its tables/text. |
| `RyglewskiDuch2009` | PubMed/PMC record checked | Correct title is “Shaker and Shal Mediate Transient Calcium-Independent Potassium Current in a Drosophila Flight Motoneuron”; DOI 10.1152/jn.00693.2009, PMID 19828724, PMCID PMC2804405 match. The paper reports MN5 channel physiology and adopts passive cable parameters from Manduca; it is not a native measurement of those passive parameters. |
| `Fayyazuddin2006` | PubMed/PMC record checked | Correct title is “The Nicotinic Acetylcholine Receptor Dα7 Is Required for an Escape Behavior in Drosophila”; four authors, PLoS Biology 4(3):e63, DOI 10.1371/journal.pbio.0040063, PMID 16494528, PMCID PMC1382016 match. This is not a “novel developmental pathway” paper. |
| `Augustin2019GFS` | S-06: authors, journal, year, volume/issue/article identifier, DOI | Article title is absent. **VERIFY_REQUIRED**. |
| `Hurkey2023` | Publisher/PubMed record checked | Corrected title to “Gap junctions desynchronize a neural circuit to stabilize insect flight”; author list and issue metadata updated. Verify citation is used only for its measured MN1–MN4 coupling results, not MN5-specific conductance. |
| `Phelan2008` | PubMed/PMC record checked | Corrected title, full author list, issue, pages, DOI, PMID 19084406 and PMCID PMC2663713. Heterologous channel data must not be presented as native GFS conductance. |
| `Orr2014` | BibTeX currently includes title, author list, journal, year, volume/issue/pages, DOI, and PMID | Fields are present in the working bibliography; verify all against the primary record and ensure claims remain limited to GF→TTMn/ShakB evidence. **VERIFY_REQUIRED**. |
| `Blagburn2020` | PubMed/PMC record checked | Replaced the misattributed `Auger2020` entry with the verified Blagburn title, author, journal, article number, DOI, PMID 31951567 and PMCID PMC6946141. This is an auditory-input study; the GF→PSI ShakB statement is a secondary citation to Augustin 2017. |
| `KuehnDuch2013` | PubMed/PMC record checked | Corrected title to “Putative excitatory and putative inhibitory inputs are localised in different dendritic domains in a Drosophila flight motoneuron”; identifiers match. Confirm any SIZ-specific sentence against the full paper before submission. |
| `vonHoffDuch2010` | PMC/PubMed record checked; PMID 20437522, PMCID PMC4441823, DOI 10.1002/cne.22380 | Correct title is “Tiling Among Stereotyped Dendritic Branches in an Identified Drosophila Motoneuron.” The prior title/DOI pairing was incorrect; bibliography corrected. This supports MN5 dendritic morphology/tiling, not electrotonic transfer. **Metadata corrected; in-text use still requires review**. |
| `Yang2016` | PubMed/PMC record checked | Correct title is “Subcellular Imaging of Voltage and Calcium Signals Reveals Neural Processing In Vivo”; six authors, Cell 166(1):245–257, DOI 10.1016/j.cell.2016.05.031, PMID 27264607, PMCID PMC5606228 match. Its visual-system experiments are not direct MN5 transfer evidence. |
| `GouwensWilson2009` | BibTeX currently includes title, author list, journal, year, volume/issue/pages, DOI, and PMID | Fields are present in the working bibliography; independently verify against the primary record and confirm relevance to claims. **VERIFY_REQUIRED**. |
| `Meseke2009` | Publisher/PubMed record checked; DOI 10.1152/jn.90899.2008, PMID 19386754 | Correct title is “Developmental changes in dendritic shape and synapse location tune single-neuron computations to changing behavioral functions.” It studies Manduca MN5 across development; do not treat its passive model parameters as native Drosophila MN5 measurements. **Metadata corrected**. |
| `DuchLevine2000` | PubMed/PMC record checked; DOI 10.1523/JNEUROSCI.20-18-06950.2000, PMID 10995839, PMCID PMC6772846 | Correct title is “Remodeling of membrane properties and dendritic architecture accompanies the postembryonic conversion of a slow into a fast motoneuron.” This is Manduca sexta MN5, not Drosophila MN5. **Metadata corrected**. |
| `DuchBaylineLevine2000` | DOI 10.1006/dbio.2000.9854 resolves to Tam et al., “Voltage-gated calcium channels direct neuronal migration in Caenorhabditis elegans” (PMID 10993677), unrelated to the purported Manduca paper | Removed the mismatched DOI from the entry and flagged title/source identity as **VERIFY_REQUIRED**. Do not cite this entry until the intended primary source is identified. |
| `Augustin2017` | Publisher/PubMed record checked | Full title, 11 authors, volume 15 issue 9, article e2001655, DOI 10.1371/journal.pbio.2001655, PMID 28902870 and PMCID PMC5597081 verified. Specific GF→PSI interpretation should be checked against the relevant figure/text in the primary article. |
| `Kadas2012` | PubMed/PMC record checked | Corrected full title and four-author list; DOI, PMID 22219280 and PMCID PMC6621333 match. Supports developmental CaMKII/cholinergic GFS claims and the documented PSI driver-validation caveat; not evidence of PSI-selective activation. |
| `Lansdell2012` | Working BibTeX includes authors, title, journal, year, volume/pages, DOI | Metadata is populated from the source registry but no external verification is recorded in this audit. **VERIFY_REQUIRED**; recombinant receptor data do not establish native PSI→MN5 conductance. |
| `HerreraValdez2013` | PubMed/PMC record checked; DOI 10.1007/s10827-012-0416-6, PMID 22878689, PMCID PMC6595220 | Added to the bibliography because the Results draft cites it for the capacitance discussion. The paper is a motor-neuron model; its reported capacitance discussion must not be interpreted as native spatial-transfer validation. |

S-14 is a software repository/function citation and needs an exact version/URL if cited. S-16 is a repository/data record with incomplete citation fields. S-17 is explicitly **UNVERIFIED** and must not be promoted into the bibliography as evidence. The source registry and other parameter records cite additional articles; reconcile every citation actually used in the paper against a primary record before release. Do not fill missing fields from memory.


## 2026-10-12 working-bibliography reconciliation

A fresh repository-local field scan of `paper/references.bib` on the test-fix branch found **21 entries**. Most article entries now contain author, title, journal, year, and DOI fields; `MaleCNSv1` is a dataset-style entry and intentionally has no DOI field. Presence of a field is not independent verification of its value. The rows above distinguish populated working metadata from verified publisher/PubMed metadata.

**Important citation-rendering limitation:** `paper/REVIEW_MANUSCRIPT.md` does not contain machine-readable BibTeX citation commands or citation-key references. The review build script inserts the entire bibliography at `BIBLIOGRAPHY_INSERT` and prints each BibTeX key as a label. Consequently, the current build cannot mechanically prove that every in-text author–year citation maps to the intended bibliography entry or identify true orphan references. Claim IDs (for example, `[C-101]`) refer to the claim evidence map; they are not bibliographic citations. This is an editorial/source-format limitation, not a successful citation reconciliation.

Before submission, reconcile author–year citations in the assembled manuscript against the primary records and the 21 bibliography entries, then convert the final source to the journal's required citation style. Do not remove entries solely because the current Markdown source does not contain their BibTeX keys; the source uses prose citations and claim IDs, and each reference's role must be reviewed first.

A repository-local scan also confirms that several entries previously described as having missing titles in older registry notes now have title fields in the working BibTeX. Those changes update field-presence status only; they do not silently promote the records to externally verified status.


**Specific corrections made on 2026-10-12:** the Augustin et al. 2019 GFS model title, Meseke et al. 2009 title, Duch & Levine 2000 title, and von Hoff & Duch 2010 title/DOI were corrected against publisher/PubMed/PMC records. The `DuchBaylineLevine2000` DOI mismatch was identified and removed rather than replaced with a guessed DOI. These metadata corrections do not constitute a complete in-text citation audit.

**In-text citation scan:** the Results draft cites Herrera-Valdez et al. (2013), which was absent from the BibTeX file; a verified entry has now been added. The scan also found a few author-string variants and draft notes that need editorial cleanup. The build script does not parse author–year citations, so this remains a manual manuscript-level check rather than a complete automated reconciliation.

## Decision

The bibliography remains a working index, not a publication-ready reference list. The targeted checks corrected three materially mismatched titles (Ryglewski & Duch 2009, Fayyazuddin et al. 2006, and Yang et al. 2016) and verified the metadata noted above. Remaining unresolved items include the preferred MaleCNS dataset citation, project authorship/release metadata, the exact source/title and use of GouwensWilson2009, Augustin2019GFS, Orr2014, vonHoffDuch2010, and the Manduca references, plus full in-text citation reconciliation. The Ryglewski–Kilo–Duch 2014 metadata gap is resolved against PubMed/PMC, but whether each cited numerical measurement is correctly attributed still requires primary-text/table verification. Other unresolved entries remain **VERIFY_REQUIRED** until checked against the final manuscript and authoritative records. No DOI, URL, author, access date, or license has been added beyond repository evidence.
