**Table R-4.** Reproducibility and validation status. Historical broad-suite counts are inherited and must not be presented as current CI results [C-602, C-701].

| Item | Value | Status | Evidence class |
|---|---|---|---|
| Focused MN5 provenance/gate tests | Required focused step passed in Actions run 38205908211 | PASS for that run | Software validation |
| Broad repository test suite | Audit step cancelled in Actions run 38205908211; earlier counts are historical/inherited | NOT VERIFIED by this run | Software validation |
| Test command (focused) | `tests/test_reduced_mn5.py`, `tests/test_model_framework.py`, `tests/test_parameter_adoption.py`, `tests/test_malecns_compartment.py`, `tests/test_malecns_contact_path.py`, `tests/test_mn5_spatial_transfer_gate_review.py` | PASS in run 38205908211 | Software validation |
| SWC SHA-256 pinning (sensitivity script) | 2 cached MN5 SWCs pinned in script | Recorded in source; provenance scope should be checked against each input | AM / software provenance |
| MaleCNS synapse-pair Feather checksum | Local staged-file SHA-256 recorded; no independent publisher-provided expected checksum identified | PARTIAL — local identity only | Data provenance |
| Data download/staging procedure | Staging command documented; successful re-staging depends on external access and environment | DOCUMENTED, not end-to-end independently verified here | Data provenance |
| External data license/attribution | CC-BY recorded; final manuscript attribution and redistribution conditions require human review | REVIEW REQUIRED | Data provenance |
| Review-only PDF | 30-page PDF built and text-checked in run 38205908211; visual inspection recorded separately | BUILD PASS; not submission-ready | Editorial artifact |
| Model sensitivity rows | 15,528 conditional model-derived rows | GENERATED; not native validation | MDE |

> Software validation is not empirical biological validation [C-602].