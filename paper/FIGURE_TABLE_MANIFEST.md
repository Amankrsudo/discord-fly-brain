# Figure and Table Manifest — Fly Brain 3.0 Manuscript

**Purpose**: List each planned figure and table, its purpose, supporting claims, source data, units/evidence class, generation procedure, status, and output path. Status values: `EXISTING` (already present in repository), `GENERATED` (created in this phase), `BLOCKED` (cannot be produced — data absent), `PENDING VERIFICATION` (needs manual confirmation).

**Provenance key**: `NEM` = native experimental measurement · `AM` = anatomical measurement · `LDP` = literature-derived · `MDE` = model-derived estimate · `MA` = model assumption.

---

## Manuscript reference mapping (proposed)

| Draft section | Proposed figure/table |
|---|---|
| Results §2 | Figure 3 (contact mapping), Table R-1 (contact summary) |
| Results §5 | Table R-2 (mesh/registry table), Table R-3 (native biophysics) |
| Results §6 | Figure 5 (two-gate model), Figure 6 (sensitivity) |
| Results §7 | Figure 7 (gating capability) |
| Results §8 | Figure 8 (reproducibility/validation) |
| Introduction §1 | Figure 1 (circuit diagram) |
| Introduction §2 | Figure 2 (provenance pipeline) |

---

## Figures

### Figure 1 — Escape circuit diagram
- **Purpose**: Context: GF → TTMn / PSI → MN5 → DLMn anatomy.
- **Supporting claims**: `[C-101]`
- **Source**: `malecns_ingest.py:BODY_IDENTITIES`, `model_framework.py:FROZEN_MN5_ANATOMY`
- **Units/class**: `AM` (body identity text)
- **Generation**: vector schematic from frozen body IDs; not auto-generated from data
- **Output**: `paper/figures/FIGURE_1.svg`
- **Status**: PENDING (requires schematic authoring; no data gap)
- **Note**: Circuit topology is textual from Ryglewski & Duch 2009 verbatim (`[C-101]`).

### Figure 2 — Evidence/provenance pipeline
- **Purpose**: Show flow from sources → evidence classes → model inputs → claims, with gate blocks.
- **Supporting claims**: `[C-301, C-401, C-501, C-602]`
- **Source**: `research/model_input_freeze.md`, `research/evidence_ledger.md`, `model_framework.py`
- **Units/class**: MA (non-biological: repository-derived)
- **Generation**: hand-authored diagram
- **Output**: `paper/figures/FIGURE_2.svg`
- **Status**: PENDING (requires schematic authoring)

### Figure 3 — PSI→MN5 contact mapping
- **Purpose**: Bilateral contact counts (17 left / 26 right) at minconf 0.5.
- **Supporting claims**: `[C-102]`
- **Source**: `research/artifacts/malecns_compartment_post_psi_mn5.csv` (43 rows); `research/artifacts/malecns_compartment_post_summary.json`
- **Units/class**: `AM` — counts (dimensionless), minconf threshold 0.5
- **Generation**: bar chart from summary JSON
- **Output**: `paper/figures/FIGURE_3_contact_mapping.svg`
- **Status**: GENERATED

### Figure 4 — compartment_post distribution
- **Purpose**: Show `compartment_post=axon` for all 43; `compartment_pre` axon vs unknown split.
- **Supporting claims**: `[C-103]`
- **Source**: `research/artifacts/malecns_compartment_post_summary.json`
- **Units/class**: `AM` — counts (dimensionless)
- **Generation**: grouped bar chart from summary JSON
- **Output**: `paper/figures/FIGURE_4_compartment_annotations.svg`
- **Status**: GENERATED

### Figure 5 — Two-gate conditional model
- **Purpose**: Illustrate the abstract bridge (112.5 µm / 2 µm cable) vs contact-local patch; mark gates.
- **Supporting claims**: `[C-402, C-201, C-401, C-501]`
- **Source**: `research/mn5_psi_mn5_final_constraint_model.md` §2; `analyze_mn5_two_gate_constraint_model.py` (GFS_BRIDGE_LENGTH_UM, GFS_BRIDGE_DIAMETER_UM)
- **Units/class**: `MA` (abstract bridge geometry from Augustin 2019 precedent)
- **Generation**: annotated diagram
- **Output**: `paper/figures/FIGURE_5_two_gate_model.svg`
- **Status**: PENDING (requires schematic authoring; geometry values verified from code)

### Figure 6 — Sensitivity summary
- **Purpose**: Model-derived min/median/max for local peak, somatic peak, and local-to-somatic ratio; distinguish Gate A (no native path) and Gate B (model-only sweep).
- **Support**: `[C-601, C-402, C-503, C-303]`
- **Source**: `research/mn5_psi_mn5_final_constraint_model_sensitivity.csv` (15,528 rows; verified: 9,288 local + 2,880 abstract + 2,880 Dα7 + 480 calibration)
- **Units/class**: `MDE` (model-derived estimates)
- **Generation**: SVG from CSV aggregates (numpy); nominal-point C-01 A/B values embedded
- **Output**: `paper/figures/FIGURE_6_sensitivity.svg`
- **Status**: GENERATED (verified against source CSV: somatic min/median/max 0.0028/1.812/67.078; ratio 0.085/0.517/0.892; local nominal 40.13–67.71 mV)

### Figure 7 — Model capability/gating
- **Purpose**: Capability surface (AVAILABLE / PARTIAL / BLOCKED) with the two gates.
- **Supporting claims**: `[C-602, C-401, C-501]`
- **Source**: `reduced_mn5.py:ReducedMN5Simulator.capabilities()`, `model_framework.py:MN5Model.capabilities()`
- **Units/class**: `AM` (repository-derived capability surface)
- **Generation**: SVG from verified capability values
- **Output**: `paper/figures/FIGURE_7_capability.svg`
- **Status**: GENERATED (capability values from code; diagram layout minimal)

### Figure 8 — Validation/reproducibility overview
- **Purpose**: Test categories and exclusions, snapshot status, external dependencies.
- **Supporting claims**: `[C-602, C-701]`
- **Source**: `validation/full_suite_report.md`, `AGENTS.md`, `research_archive/EXTERNAL_DATA_REPRODUCIBILITY.md`
- **Units/class**: `AM` (software test record)
- **Generation**: SVG summary with gate-safe labeling
- **Output**: `paper/figures/FIGURE_8_reproducibility.svg`
- **Status**: GENERATED (diagram layout minimal; facts from audit record)

---

## Tables

### Table R-1 — PSI→MN5 contact summary
- **Purpose**: Bilateral contact counts and compartments at minconf 0.5.
- **Supporting claims**: `[C-101, C-102, C-103]`
- **Source**: `research/artifacts/malecns_compartment_post_summary.json`
- **Units/class**: counts (dimensionless), `AM`
- **Generation**: Markdown table from JSON
- **Output**: `paper/tables/FIGURE_TABLE_R1_contact_summary.md`
- **Status**: GENERATED

### Table R-2 — Native MN5 biophysics with provenance
- **Purpose**: Admissible native measurements with n, provenance, and conflict flag.
- **Supporting claims**: `[C-301, C-302, C-303, C-304]`
- **Source**: `research/model_input_freeze.md` Section A (filtered to NEM rows)
- **Units/class**: `NEM` (native experimental measurement)
- **Generation**: Markdown table from `model_input_freeze.csv` (provenance = native_experimental_measurement, safe_now = yes)
- **Output**: `paper/tables/FIGURE_TABLE_R2_native_biophysics.md`
- **Status**: GENERATED

### Table R-3 — Model gate and capability surface
- **Purpose**: What is available, blocked, or assumption-only; gate status.
- **Supporting claims**: `[C-301, C-401, C-501, C-602]`
- **Source**: `research/model_input_freeze.md` (bucket counts), `reduced_mn5.py`/`model_framework.py` (capabilities)
- **Units/class**: `AM`/`MA` (repository-derived capability)
- **Generation**: Markdown table from model code + freeze counts
- **Output**: `paper/tables/FIGURE_TABLE_R3_capability.md`
- **Status**: GENERATED

### Table R-4 — Reproducibility status
- **Purpose**: Pinned vs unpinned inputs, checksum presence, test-run status.
- **Supporting claims**: `[C-701, C-602]`
- **Source**: `research/model_input_freeze.md` (40/31/37 counts), `EXTERNAL_DATA_REPRODUCIBILITY.md`, `validation/full_suite_report.md`
- **Units/class**: `AM` (repository record)
- **Generation**: Markdown table from audit files
- **Output**: `paper/tables/FIGURE_TABLE_R4_reproducibility.md`
- **Status**: GENERATED

---

## Generation procedure

A single script `paper/scripts/generate_figures_tables.py` (created in this phase) reads the verified source CSVs/JSON and writes the `GENERATED` figures and tables as SVG and Markdown. It records the source-file SHA-256 digests of each input at runtime so regenerated outputs can be checked against the same inputs. The script uses only `csv`, `json`, `hashlib`, `os`, and `numpy` (all confirmed available or standard-library); **no** matplotlib/pandas is required.

> **Constraint**: Gate A (spatial voltage transfer) and Gate B (Dα7 conductance) are NOT AUTHORIZED. No generated figure or table implies that mesh geometry, somatic EPSPs, generic passive parameters, or model sensitivity resolves either gate. Model-derived results are visibly labeled `MDE` and never presented as native measurements.

---
*Manifest created at `paper/FIGURE_TABLE_MANIFEST.md`. Source data verified by direct inspection; claim IDs cross-checked against `CLAIM_EVIDENCE_MAP.md`."*