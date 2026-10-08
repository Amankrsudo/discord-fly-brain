# Citation Release Blockers

Audit date: **2026-10-08**. This is a repository-evidence audit of the current
`CITATION.cff` scaffold. It does not validate the CFF schema, verify external
records, or authorize publication.

## Verified repository facts

| CFF field/fact | Established value or state | Exact repository evidence |
|---|---|---|
| `cff-version` | The scaffold declares `1.2.0`. This confirms only what the file currently declares; schema validation has not been run. | [`CITATION.cff`](../CITATION.cff), `cff-version` field. |
| Project name in scope document | The project/release-scope document is titled “Fly Brain 3.0.” This verifies the repository's project name, not that it is the intended citable release title. | [`3.0_RELEASE_SPEC.md`](../3.0_RELEASE_SPEC.md), title and §1. |
| Scope category described by the repository | The release specification describes a biological modelling and research architecture and says it is not a Discord product release. This supports describing the project scope, but does not independently approve a CFF `type`. | [`3.0_RELEASE_SPEC.md`](../3.0_RELEASE_SPEC.md), §2. |
| Citation scaffold state | The CFF file itself says it is a draft scaffold; its authors list is empty. | [`CITATION.cff`](../CITATION.cff), opening message and `authors: []`. |

## Unresolved CFF fields

| Field | Required evidence not established | Status |
|---|---|---|
| `title` | Intended citable software-release title; repository project name alone is insufficient. | `VERIFY_REQUIRED` |
| `type` | Project-authority confirmation that the citable object should be typed as `software`. | `VERIFY_REQUIRED` |
| `authors` | Scholarly contributor list and ORCIDs. Git author/committer identity is not authorship evidence. | `VERIFY_REQUIRED` |
| `version` | Version assigned to the eventual archived release. | `VERIFY_REQUIRED` |
| `date-released` | Release/publication date for that archived version. | `VERIFY_REQUIRED` |
| `url` | Confirmed canonical repository or versioned release URL. A configured Git remote is not by itself an approved citation URL. | `VERIFY_REQUIRED` |
| `doi` | Whether a DOI will be assigned and its verified value if assigned. | `VERIFY_REQUIRED` |
| `license` | Project-wide software license and approved license text. No tracked/root `LICENSE` or `COPYING` file establishes it. | `VERIFY_REQUIRED` |

The CFF is **not publication-ready**. No unresolved value is supplied or
guessed in this audit. The existing title/type scaffold values are retained
with explicit verification comments; absent fields remain absent pending
confirmation.

## Related citation blockers

- [`paper/references.bib`](../paper/references.bib) is incomplete according
  to [`CITATION_AUDIT.md`](./CITATION_AUDIT.md); complete author lists, titles,
  identifiers, and formatting must be verified for references used.
- The MaleCNS article and dataset author attribution and preferred dataset
  citation require verification in
  [`MALECNS_PUBLICATION_AUDIT.md`](./MALECNS_PUBLICATION_AUDIT.md).
- The applicable MaleCNS license text, attribution, and redistribution
  conditions are not reproduced in the repository audit. Do not redistribute
  raw MaleCNS data until verified.
