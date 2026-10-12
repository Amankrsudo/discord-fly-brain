# Citation metadata audit

Audit date: **2026-10-12**. Audit basis: repository-local `3.0_RELEASE_SPEC.md`, `research/source_registry.md`, parameter/model research records, `CITATION.cff`, and `paper/references.bib`, plus targeted publisher/PubMed/PMC metadata checks. This is a partial audit; unchecked entries remain explicitly unresolved.

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
| `RyglewskiDuch2009` | S-03: authors, journal, year, volume/issue/pages, DOI and identifiers | Article title is absent. **VERIFY_REQUIRED**. |
| `Fayyazuddin2006` | S-04: authors, journal, year, volume/issue/article number, DOI | Article title is absent. **VERIFY_REQUIRED**. |
| `Augustin2019GFS` | S-06: authors, journal, year, volume/issue/article identifier, DOI | Article title is absent. **VERIFY_REQUIRED**. |
| `Hurkey2023` | Publisher/PubMed record checked | Corrected title to “Gap junctions desynchronize a neural circuit to stabilize insect flight”; author list and issue metadata updated. Verify citation is used only for its measured MN1–MN4 coupling results, not MN5-specific conductance. |
| `Phelan2008` | PubMed/PMC record checked | Corrected title, full author list, issue, pages, DOI, PMID 19084406 and PMCID PMC2663713. Heterologous channel data must not be presented as native GFS conductance. |
| `Orr2014` | S-09 anatomy citation: author names, journal, year, volume/issue/pages, DOI, PMID | Article title absent. **VERIFY_REQUIRED**. |
| `Blagburn2020` | PubMed/PMC record checked | Replaced the misattributed `Auger2020` entry with the verified Blagburn title, author, journal, article number, DOI, PMID 31951567 and PMCID PMC6946141. This is an auditory-input study; the GF→PSI ShakB statement is a secondary citation to Augustin 2017. |
| `KuehnDuch2013` | PubMed/PMC record checked | Corrected title to “Putative excitatory and putative inhibitory inputs are localised in different dendritic domains in a Drosophila flight motoneuron”; identifiers match. Confirm any SIZ-specific sentence against the full paper before submission. |
| `vonHoffDuch2010` | S-11: author names and year; parameter registry supplies PMID/PMCID | Title, journal, volume/pages, DOI absent from source registry. **VERIFY_REQUIRED**. |
| `Yang2016` | S-12: authors, journal, year, volume/issue/pages, DOI and identifiers | Article title absent. **VERIFY_REQUIRED**. |
| `GouwensWilson2009` | S-13: authors, journal, year, volume/issue/pages | Title, DOI, and identifiers absent. **VERIFY_REQUIRED**. |
| `Meseke2009`, `DuchLevine2000`, `DuchBaylineLevine2000` | S-15: author names, year, journal/volume/pages where recorded; Manduca species boundary | Several titles and publication fields absent. **VERIFY_REQUIRED**; ensure these are used only for cross-species context. |
| `Augustin2017` | Publisher/PubMed record checked | Full title, 11 authors, volume 15 issue 9, article e2001655, DOI 10.1371/journal.pbio.2001655, PMID 28902870 and PMCID PMC5597081 verified. Specific GF→PSI interpretation should be checked against the relevant figure/text in the primary article. |
| `Kadas2012` | PubMed/PMC record checked | Corrected full title and four-author list; DOI, PMID 22219280 and PMCID PMC6621333 match. Supports developmental CaMKII/cholinergic GFS claims and the documented PSI driver-validation caveat; not evidence of PSI-selective activation. |
| `Lansdell2012` | S-19: authors, title, journal, year, volume/article number, DOI | Complete against S-19 record; no external verification performed. |

S-14 is a software repository/function citation and needs an exact version/URL if cited. S-16 is a repository/data record with incomplete citation fields. S-17 is explicitly **UNVERIFIED** and must not be promoted into the bibliography as evidence. The source registry and other parameter records cite additional articles; reconcile every citation actually used in the paper against a primary record before release. Do not fill missing fields from memory.

## Decision

The bibliography is a useful working index, not a publication-ready reference list. Corrected author initials for Hürkey, von Hoff, and Wilson match repository records. Remaining incomplete authors, titles, dataset citation details, and project authorship are **VERIFY_REQUIRED**. No DOI, URL, author, access date, or license has been added beyond repository evidence.
