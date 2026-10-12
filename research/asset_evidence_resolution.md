# Asset Evidence Resolution Report

## Scope and method

This report summarizes the second-pass triage in `asset_replacement_ledger.csv` and the decisions documented in `asset_replacement_plan.md`. It records provenance and intended usage; it does not claim that unknown visual assets have been forensically identified or that any biological asset is validated solely from appearance.

## Counts and remaining unknowns

- Starting counts: `UNKNOWN` 41 (before second-pass triage).
- Final `UNKNOWN` 40 (one row was resolved to a supported model-heuristic classification; unknown assets remain unknown unless asset-specific evidence supports reclassification).
- P1: 8 active mating frames.
- P2: 32 unused mating copies.

The 40 mating-related rows remain `UNKNOWN`, with `RESEARCH_REQUIRED` decisions and no identified replacement source. Eight are currently used for visualization only; 32 are unused copies. The ledger retains each row and its evidence limits.

## Group model and weights

The group model and `group_weights.json` are model heuristics, not a connectome-derived biological reconstruction. The weights are hand-designed and not derived from real synapse counts. No asset provenance classification is used to authorize either MN5 scientific gate.

## AI/procedural classification

No row is classified as AI-generated without asset-specific evidence. Unknown provenance is not treated as proof of AI generation. No row is classified as procedurally synthetic without generation-script or equivalent asset-specific evidence.

## Replacement decisions

The audited dashboard hero and fire overlay replacement records include source, creator/license information, processing, and validation in `dashboard_asset_licenses.md` and `dashboard_asset_replacement_log.csv`. The replacement records do not imply that the remaining unknown animation assets have been identified or replaced.

## Scientific boundaries

This is an asset-provenance audit, not a biological validation exercise. PSI→MN5 spatial voltage transfer and native Dα7 conductance remain **NOT AUTHORIZED**. No electrophysiological parameter, compartment identity, or biological mechanism is inferred from visual appearance, asset labels, or model stability.
