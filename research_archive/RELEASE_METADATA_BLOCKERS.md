# Release Metadata Blockers

Audit date: **2026-10-08**. This record reports only repository evidence. No
authorship, DOI, version, license, citation fields, or dataset terms have been
filled in from memory or inferred from commit authorship.

## A. Scientific blockers

These are unresolved limits on the scientific claims, not missing CFF
metadata:

- Native PSI→MN5 spatial voltage transfer and contact-to-soma anatomy remain
  unmeasured/unresolved.
- Native MN5 Dα7 conductance remains unavailable.
- SIZ registration to MaleCNS remains unresolved.
- C-01 MN5 capacitance discrepancy remains unresolved (43 ± 2 pF versus
  127 ± 16 pF).
- C-02 gap-junction unit discrepancy remains unresolved.
- C-03 PSI→DLMn chemical-synapse discrepancy remains unresolved.
- Absolute ShakB conductance remains unknown.

The repository mapping is preserved: C-02 is the gap-junction discrepancy;
C-03 is the PSI→DLMn chemical-synapse discrepancy. See
[`PAPER_SCOPE_FREEZE.md`](./PAPER_SCOPE_FREEZE.md) and
[`research/conflicts.md`](../research/conflicts.md).

## B. Metadata blockers

### CITATION.cff

`CITATION.cff` now has the following fields populated from confirmed decisions:

- `type: software`
- `title: "House Fly Brain"`
- `version: "1.1"`
- `date-released: "2026-10-08"`
- `repository: "https://github.com/Amankrsudo/discord-fly-brain"`
- `license: MIT`

The exact unresolved items remaining are:

- authors/contributors: `given-names: Aman` (no family name or ORCID supplied);
- DOI status (none assigned; do not invent).

[`CITATION_RELEASE_BLOCKERS.md`](./CITATION_RELEASE_BLOCKERS.md) records the
field-by-field evidence.

### Bibliography and dataset attribution

`paper/references.bib` is a working index, not a publication-ready
bibliography. As detailed in
[`CITATION_AUDIT.md`](./CITATION_AUDIT.md), multiple entries have missing
titles, full authors, identifiers, or formatting details. The MaleCNS article
and dataset records need a complete author list and verified preferred
dataset citation. S-17 remains explicitly unverified and must not be promoted
to evidence. Verify every reference actually used; do not fill fields from
memory.

## C. External-data and reproducibility blockers

- Required external inputs are MaleCNS v1.0 contact data, its precomputed
  synapse-annotation layer, and the MN5 SWC skeleton files. Their documented
  sources and versions are in [`research/raw_data_registry.md`](../research/raw_data_registry.md)
  and [`MALECNS_PUBLICATION_AUDIT.md`](./MALECNS_PUBLICATION_AUDIT.md).
- The expected Feather file is
  `syn-partners-male-cns-v1.0-minconf-0.5.feather`. The extraction script
  consumes a pre-staged file; it does not download it. No complete permitted
  staging command/procedure is recorded.
- No expected checksum for the Feather file is recorded. SWC and mesh
  checksums exist for named files, but do not verify the Feather input.
- The processed annotation CSV/JSON depend on the partner table and public
  annotation layer. The SWC-concordance CSV/Markdown depend on those
  annotations and the external SWCs. The two-gate sensitivity CSV depends on
  the concordance and SWCs.
- Repository records describe MaleCNS as CC-BY, but the applicable license
  text, exact attribution, and bulk-redistribution terms have not been
  independently established here. The raw Feather file must not be included
  or redistributed without that review.
- Exact dependency/environment locking and a clean-checkout release
  validation report are still required. The historical 1773-pass run has no
  established exact source tree and does not validate the proposed snapshot.

No raw MaleCNS Feather data were read or downloaded for this audit.

## D. Human decisions required

Before a public release or final citation record:

1. Confirm scholarly authors/contributors and ORCIDs (family name, ORCID for Aman).
2. Confirm DOI status (none assigned; do not invent).
3. Verify complete bibliography fields and the MaleCNS article/dataset
   attribution and redistribution terms against authoritative records.
4. Establish an allowed external-data staging procedure and expected Feather
   checksum, or explicitly document why the source does not provide one.
5. Finalize a dependency/environment recipe and run validation against the
   exact clean release commit.

These blockers do not authorize staging or committing a release.
