# Asset Replacement Audit Plan

## A. Objective and scope

Inventory project assets and model representations, record provenance and claim evidence, and identify any justified replacement work. This is an audit; it does not replace or regenerate assets and does not alter production behavior.

## B. Inventory and method

The ledger contains 709 data rows with stable path-derived IDs, one row per asset. Runtime, test, and documentation references were traced through the renderers, controller, dashboard, model code, and asset manifests. Duplicate worktree assets remain individual rows. A file's repository presence or visual appearance does not establish its author or generation method.

The evidence-resolution second pass began from the exact 41 `UNKNOWN` rows and investigated the 40 MATE-family files and `group_weights.json`. Full exact starting rows, source findings, the JSON graph, implementation trace, and decisions appear in [asset_evidence_resolution.md](asset_evidence_resolution.md). Existing unrelated worktree edits were left untouched.

## C. Decision summary

### Provenance

| Provenance | Count |
|---|---:|
| PRIMARY_EXPERIMENTAL | 0 |
| AUTHORITATIVE_DATA | 2 |
| PUBLISHED_RECONSTRUCTION | 0 |
| LITERATURE_DERIVED | 1 |
| MODEL_DERIVED | 10 |
| PROCEDURAL_SYNTHETIC | 0 |
| AI_GENERATED | 0 |
| PLACEHOLDER | 4 |
| VISUAL_ONLY | 652 |
| UNKNOWN | 40 |

### Replacement decision

| Decision | Count |
|---|---:|
| KEEP | 13 |
| REPLACE | 2 |
| REMOVE | 0 |
| RESEARCH_REQUIRED | 40 |
| UNRESOLVED | 0 |
| VISUAL_ONLY | 654 |

### Usage

| Usage type | Count |
|---|---:|
| BIOLOGICAL_COMPUTATION | 5 |
| VISUALIZATION_ONLY | 143 |
| TEST_FIXTURE | 6 |
| DOCUMENTATION_ONLY | 7 |
| UNUSED | 548 |

All 709 original rows remain. Confirmed AI-generated count: zero. Confirmed procedural-synthetic count: zero.

## D. Evidence-resolution outcomes

The 40 mating-depiction files form one provenance family: eight active frames and 32 unused copies/variants. Corresponding filenames are byte-identical across four repository paths. The README's scientific-grounding statement has no traceable citation; all 40 rows retain provenance `UNKNOWN` and decision `RESEARCH_REQUIRED`. Eight active frames are P1; 32 unused copies/variants are P2. No replacement source was identified.

`group_weights.json` is `MODEL_DERIVED` and `KEEP` only as a hand-designed legacy 2.0 behavior-simulation heuristic. The code expressly says coefficients were not derived from real synapse counts. They are not biological synaptic strengths, conductances, currents, probabilities, or calibrated measurements. No JSON values or model behavior changed.

## E. Replacement readiness

One decorative fallback hero has been replaced with a human-authored, CC BY 4.0 DBCLS Drosophila illustration after source and license verification. The original file remains preserved. No suitable licensed human-made replacement set was identified for the active multi-state behavior animations and overlays; those remain unchanged and are recorded in `dashboard_asset_replacement_log.csv`. The 40 MATE assets remain excluded and untouched. Do not repeat the MATE pack's scientific-grounding claim as verified until its source and frame mapping are recovered. Keep `group_weights.json` in its documented product heuristic scope; biological use would require separate edge-level evidence and derivation.

## F. Scientific gates preserved

This asset audit does not authorize or alter any scientific gate:

- PSI→MN5 spatial voltage-transfer mechanism remains **NOT AUTHORIZED**.
- Dα7 PSI→MN5 conductance remains **NOT AUTHORIZED**.
- SIZ coordinate registration remains unresolved.
- Local PSI→MN5 synaptic conductance remains unresolved.
- The 80 µS vs 0.08 µS synaptic-weight conflict remains unresolved.
- The 135/34.5 µS vs nS gap-junction conflict remains unresolved.
- ShakB absolute GFS conductance remains unresolved.
- No parameter is inferred from model stability.
- Somatic MN5 measurements are not converted into local axonal parameters.
- Model-derived geometry is not presented as experimental anatomy.

## G. Mating visualization specification

The MATE family remains `UNKNOWN` / `RESEARCH_REQUIRED`; its provenance decision is unchanged. The replacement research specifies removing the forced MATE visual from active product display and showing the model-selected behavior instead. No images are replaced or deleted in this phase. See [mating_asset_replacement_spec.md](mating_asset_replacement_spec.md) for the primary-source review, claim boundary, implementation criteria, and licensing requirements.

## H. Validation

`tests/test_asset_replacement.py` checks row counts and stable IDs, all 40 mating rows, the group-weight provenance/decision, source support for `KEEP` and resolved provenance, explicit AI/procedural evidence, replacement-target consistency, visual-only separation, unchanged group model/weight fingerprints, and preservation of scientific gates. Focused asset tests, related dashboard/biological tests, and collection-only validation are required for this audit; the computationally heavy full suite is not required.

## I. Next biological component audit

The next evidence-backed research target is the **opt-in Fly Brain 3.0 static
research-summary panel**, defined in `biological_brain/status_summary.py` and
rendered by `brain_dashboard.py::_biological_panel`. Its compact summary places
connectome observations, literature values, model-derived estimates, and
unresolved assumptions together; the panel does not show all the source,
version, confidence-threshold, and uncertainty context carried by the local
audits. Research the panel claim-by-claim before changing its wording or
representation.

This is a prioritization only. No production behavior or panel content changes
are authorized by this selection. Do not infer PSI-to-MN5 voltage transfer,
local conductance, contact-to-soma path, or SWC type semantics. The 40 mating
assets and their ledger status remain untouched. The candidate inventory,
ranking, source precheck, scientific-gate review, and proposed research
workflow are recorded in [next_biological_asset_audit.md](next_biological_asset_audit.md).

## J. Research-summary panel evidence audit

The selected Fly Brain 3.0 research-summary panel has now received a separate primary-source and claim-language audit. Its concern is evidence labeling and provenance in a rendered static panel, not replacement of an image or biological asset. See [biological_summary_evidence_audit.md](biological_summary_evidence_audit.md), [biological_summary_claim_ledger.csv](biological_summary_claim_ledger.csv), and [biological_summary_panel_spec.md](biological_summary_panel_spec.md).

No asset decision or provenance row is changed by that audit. No production panel, model, or scientific gate was modified. The panel specification remains research-only pending a separate implementation task.


## K. Dashboard visual replacement

The optional hero fallback uses `dashboard assests/fly_hero_human_commons_ccby.png`, and the decorative fire/burn overlay now uses the rasterized Carl Olsen flame in `dashboard assests/fly_behavior_assets_codex_v2/effects/fire_overlay.png`. Their source, creator, licenses, attribution, processing, dimensions, and validation are recorded in `dashboard_asset_licenses.md` and `dashboard_asset_replacement_log.csv`; both provenance ledger rows are marked `REPLACED_VALIDATED`. The original hero image remains in the repository; the original fire overlay was replaced in its existing slot. No behavior animation, ice/shock overlay, MATE asset, scientific asset, biological model, or gate was changed.
