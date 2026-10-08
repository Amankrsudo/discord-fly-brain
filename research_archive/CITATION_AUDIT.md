# Citation metadata audit

Audit date: **2026-10-08**. Audit basis: repository-local `3.0_RELEASE_SPEC.md`, `research/source_registry.md`, parameter/model research records, `CITATION.cff`, and `paper/references.bib`. No external metadata lookup was performed.

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
| `Mehta2023SWC` | S-02: authors, title, journal, year, volume/article number, DOI | Journal abbreviation and citation formatting before publication. |
| `RyglewskiDuch2009` | S-03: authors, journal, year, volume/issue/pages, DOI and identifiers | Article title is absent. **VERIFY_REQUIRED**. |
| `Fayyazuddin2006` | S-04: authors, journal, year, volume/issue/article number, DOI | Article title is absent. **VERIFY_REQUIRED**. |
| `Augustin2019GFS` | S-06: authors, journal, year, volume/issue/article identifier, DOI | Article title is absent. **VERIFY_REQUIRED**. |
| `Hurkey2023` | S-07: first author initial, journal, year, volume/pages, DOI | Full author list and title absent. **VERIFY_REQUIRED**. |
| `Phelan2008` | S-08: first author initial, journal, year, volume/issue/pages, PMID | Full author list, title, and DOI absent. **VERIFY_REQUIRED**. |
| `Orr2014` | S-09 anatomy citation: author names, journal, year, volume/issue/pages, DOI, PMID | Article title absent. **VERIFY_REQUIRED**. |
| `Auger2020` | S-09 age citation: journal, year, volume/issue/article number, DOI | Author list and title absent. **VERIFY_REQUIRED**; current entry lacks an author field. |
| `KuehnDuch2013` | S-10: authors, journal, year, volume/issue/pages, DOI and identifiers | Article title absent. **VERIFY_REQUIRED**. |
| `vonHoffDuch2010` | S-11: author names and year; parameter registry supplies PMID/PMCID | Title, journal, volume/pages, DOI absent from source registry. **VERIFY_REQUIRED**. |
| `Yang2016` | S-12: authors, journal, year, volume/issue/pages, DOI and identifiers | Article title absent. **VERIFY_REQUIRED**. |
| `GouwensWilson2009` | S-13: authors, journal, year, volume/issue/pages | Title, DOI, and identifiers absent. **VERIFY_REQUIRED**. |
| `Meseke2009`, `DuchLevine2000`, `DuchBaylineLevine2000` | S-15: author names, year, journal/volume/pages where recorded; Manduca species boundary | Several titles and publication fields absent. **VERIFY_REQUIRED**; ensure these are used only for cross-species context. |
| `Augustin2017` | S-09 mentions journal, year, volume/issue/article number | Author list and title absent. **VERIFY_REQUIRED**. |
| `Kadas2012` | S-18: first author, journal, year, volume/issue/pages, DOI and identifiers | Full author list and title absent. **VERIFY_REQUIRED**. |
| `Lansdell2012` | S-19: authors, title, journal, year, volume/article number, DOI | Complete against S-19 record; no external verification performed. |

S-14 is a software repository/function citation and needs an exact version/URL if cited. S-16 is a repository/data record with incomplete citation fields. S-17 is explicitly **UNVERIFIED** and must not be promoted into the bibliography as evidence. The source registry and other parameter records cite additional articles; reconcile every citation actually used in the paper against a primary record before release. Do not fill missing fields from memory.

## Decision

The bibliography is a useful working index, not a publication-ready reference list. Corrected author initials for Hürkey, von Hoff, and Wilson match repository records. Remaining incomplete authors, titles, dataset citation details, and project authorship are **VERIFY_REQUIRED**. No DOI, URL, author, access date, or license has been added beyond repository evidence.
