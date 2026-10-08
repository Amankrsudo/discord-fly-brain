# Release Manifest Review

Audit date: **2026-10-08**. The manifest was reviewed against the frozen paper
scope, `REQUIRED_RELEASE_SNAPSHOT.md`, repository-local provenance records, and
the current Git worktree. It remains a candidate inclusion manifest, not a
release.

## Classification totals

The manifest contains **75 rows**. Each row has a controlled
`release_decision` value. Duplicate path references have been removed;
the unique release file set is **93 files** (82 `RELEASE_REQUIRED` +
11 `SUPPORTING` repo files).

| Classification | Count | Meaning in this review |
|---|---:|---|
| A. `RELEASE_REQUIRED` | 64 | Scoped scientific records, implementation dependencies, validation sources, or release-audit documentation. |
| B. `SUPPORTING` | 8 | External input references, figure plan, future-experiment designs, or supplementary evidence records; not all are distributed data files. |
| C. `HISTORICAL` | 2 | Prior results/report retained or identified only as history, not as current evidence. |
| D. `INTERNAL` | 1 | Development-only diagnostics; excluded from the public scientific package. |
| E. `PRIVATE` | 0 | No private-file row is included in the candidate manifest. Private configuration, credentials, IDE state, deployment archives, and runtime state are excluded by policy and were not inspected for contents. |
| F. `MANUAL_REVIEW` | 0 | All manifest decisions are explicit. |

Totals sum to 75. The row-level decisions and rationale are in
[`paper/PUBLICATION_MANIFEST.csv`](../paper/PUBLICATION_MANIFEST.csv).

## Resolved manual-review items

1. **Biological source scope.** The former broad `biological_brain/` entry is
   replaced by a list of the exact modules named by the scientific snapshot
   proposal: MaleCNS parsers/annotation readers, the current exploratory MN5
   engine, the reduced-model modules, package entry point, and shared
   provenance module. The row does not include the package wholesale or add
   unrelated runtime/product modules. The specific module rows retain their
   own provenance details. The exact paths are `biological_brain/malecns_ingest.py`,
   `biological_brain/malecns_mesh_geometry.py`,
   `biological_brain/malecns_contact_path.py`,
   `biological_brain/malecns_compartment.py`,
   `biological_brain/exploratory_mn5.py`, `biological_brain/__init__.py`,
   `biological_brain/model.py`, `biological_brain/model_framework.py`,
   `biological_brain/reduced_mn5.py`, and
   `biological_brain/provenance.py`.
2. **Figure plan.** The existing plan is at
   `paper/figures/FIGURE_PLAN.md`. It lists eight proposed figures using
   existing artifacts, names evidence classes and prohibited implications,
   and states no figures are generated. Its release-spec reference has been
   corrected to the actual root path `3.0_RELEASE_SPEC.md`. The plan is
   classified `SUPPORTING`; it is not a figure/result artifact.
3. **Experimental-design audit bundle.** The direct-voltage, optical, and
   reversal-potential files and builder are classified
   `SUPPORTING` / future experiment design. The documents explicitly state
   that no experiments were performed and no gates were opened. These are not
   experiments, biological validation, or results.
4. **Project `LICENSE`.** Root MIT License file created with
   `Copyright (c) 2026 Aman`. Classified `RELEASE_REQUIRED`.
5. **`CITATION.cff`.** CFF `type: software` confirmed; author recorded as
   `given-names: Aman` (no family name or ORCID supplied); title, version,
   date, repository, and license fields populated. Classified `RELEASE_REQUIRED`.

## Classification notes

- The MaleCNS Feather input, annotation layer, and SWCs are supporting
  external dependencies, not files to copy into the Git release. The raw
  Feather dataset remains excluded.
- The 1773-pass report is marked `HISTORICAL`; its dirty/unknown source tree
  does not validate the proposed snapshot.
- Earlier exploratory outputs are explicitly marked superseded and excluded
  from current results. Diagnostic scripts and reports are `INTERNAL`.
- The manifest does not list any private path as a candidate release artifact.
  Exclusion of private and deployment material is not evidence that such
  material was inspected.

## Decision

All five former manual-review items are resolved with explicit
classifications. The candidate release selection still requires: external-data
reproducibility issues to be addressed, and the uncommitted worktree to be
cleaned before staging a release commit.
