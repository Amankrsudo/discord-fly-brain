# Paper Scope Freeze

This freezes the **scientific claims and terminology** for the eventual paper. It does not freeze source bytes or authorize manuscript drafting; the exact paper snapshot is addressed separately in `VERSION_SCOPE_AUDIT.md` and `REQUIRED_RELEASE_SNAPSHOT.md`.

## Included scientific work

The paper may describe the following work, with each result tied to the evidence class below:

1. **Fly Brain 3.0 software/research scope.** Summarize the architecture defined in `3.0_RELEASE_SPEC.md` at its stated baseline, `40cf69e`: 3.0A–3.0C foundations and the 3.0D GFS model architecture. State that the user-facing product remains the 2.0 behaviour path; 3.0B is opt-in/default-off, and 3.0D GFS has no Discord entry point. This is a description of repository/software state, not proof that the model reproduces biology.
2. **MaleCNS v1.0 PSI→MN5 contact anatomy.** Report 43 partner-table contacts at minimum confidence 0.5: 17 for 802401→801970 and 26 for 903327→801295. Report that the official per-synapse `compartment_post` field is literally `axon` for all 43 records. If including contact-to-SWC projections, describe them as geometric projections under the documented method, preserving the SWC Type token and tie handling. These results do not establish SWC `kind` meaning, an electrical compartment, or a path to soma.
3. **Evidence and parameter inventories.** Report the model-input freeze's 108 rows (40 safe, 31 assumption-only, 37 blocked; 15 conflict entries) as that freeze's categories. The separate parameter-adoption ledger reports 137 decisions (98 KEEP, 0 REPLACE, 0 DERIVE, 17 sensitivity, 22 unresolved). Keep these distinct; they answer different classification questions.
4. **Evidence-safe reduced MN5 software model.** Describe the reduced computational abstraction and its limits. It consumes only the three listed safe somatic values (resting potential, spike threshold, AP amplitude); it is not a cable, leak, synapse, or PSI→MN5 spatial-transfer model. Its outputs are software/model outputs, not physiological validation. Include only if the model code and tests are included in the pinned snapshot.
5. **Conditional two-gate MN5/PSI model analysis.** Describe the contact-local patch calculation and the separate abstract 112.5 µm cable bridge as two distinct model layers. The sweep uses explicit parameter/geometry assumptions and preserves both C-01 variants. It may report the current analysis's 15,528-row export and its documented sampled outputs (for example the 2,880-run ranges, 224/2,880 threshold crossings in the abstract sweep, the EPSP comparison/calibration results, and the 0 versus 456/2,880 no-Dα7/enabled threshold-crossing comparison) only as conditional model-derived outcomes from that exact grid. The enabled Dα7 conductance values and E_Dα7 values are assumptions. They are not population estimates, probabilities, measured conductances, or native pathway threshold predictions.
6. **Software/provenance validation.** Describe tests only as checks of software behavior, numerical consistency, data parsing, or provenance rules. The reported 1773 passed / 2 skipped may be stated only with its dirty-snapshot caveat; it is not a clean-snapshot release result and is not empirical biological validation.

## Excluded scientific work

- No claim that native PSI→MN5 voltage transfer, local voltage, contact-to-soma transfer, or an anatomy-based soma path has been measured or resolved.
- No claim that native MN5 Dα7 conductance, density, open probability, reversal potential, or kinetics have been measured.
- No SIZ coordinate registration to MaleCNS, and no claim that MaleCNS SWC `kind` codes identify biological axon/dendrite compartments.
- No choosing, averaging, correcting, or otherwise resolving C-01, C-02, or C-03. No absolute ShakB conductance value.
- No description of model outputs, fitted conductances, threshold crossings, or the 4.71 mV GF-stimulated EPSP comparison as PSI-specific measurements or empirical model validation.
- No claim that 3.0B signals are normally visible to Discord users, that 3.0D GFS is user-facing, or that Fly Brain 3.0 reproduces GFS latency, escape probability, or whole-animal behavior.
- Do not use the earlier exploratory report's 0/2592 results/calibrations as the current final-analysis results. It is explicitly historical/superseded.
- Dashboard/MATE asset changes, Discord product behavior, debug scripts, design backlogs, and private/deployment material are outside the scientific results.

## Evidence boundaries

| Major result or statement | Evidence class(es) | Permitted interpretation |
|---|---|---|
| 3.0 architecture, product boundary, feature flags, module behavior | Repository-derived | What the pinned code/specification implements or exposes; not biological performance. |
| Published MN5/GFS measurements and model geometry | Literature-derived | Quote source, biological object, method, units, sample/statistic, and caveat; do not recast adopted or estimated model values as native measurements. |
| 43 PSI→MN5 contacts and official annotation labels | Primary-dataset-derived | MaleCNS v1.0 records at minconf 0.5; `compartment_post` is a dataset label. |
| Contact-to-node projection, mesh metrics, and extraction tables | Primary-dataset-derived plus repository-derived method | Values derive from the named source files under the pinned parser/projection method; projection is not a biological compartment or electrical path. |
| Freeze and adoption counts | Repository-derived | Counts in their respective artifacts and taxonomies; do not merge the 108-row and 137-row schemes. |
| Reduced MN5 simulator outputs | Model-derived, based on literature/dataset/repository inputs | Software abstraction using only its permitted values; not a native physiology prediction. |
| Contact-local and abstract-bridge voltage, conductance fits, sensitivity, or threshold outcomes | Model-derived plus assumptions | Conditional deterministic outputs under stated model structures and input grid; no native transfer/conductance inference. |
| Explicit geometry, patch size, E_syn/E_Dα7, effective conductance, and other free sweep values | Assumption | State as assumptions every time; a sensitivity range is not a biological range or confidence interval. |
| Unit tests, synthetic fixtures, expected-value assertions | Validation fixture / software validation | Evidence only that code meets encoded checks; not experimental or biological evidence. |

## Model authorization terminology

Use **“model-authorized conditional analysis”** to mean that the separate two-gate analysis is permitted to execute a calculation under explicitly documented assumptions and constraints. The repository's final analysis documents explicitly use `MODEL-AUTHORIZED` in this restricted sense and keep resulting transfer/conductance outputs `MODEL-DERIVED`.

The reduced-model freeze's **“NOT AUTHORIZED”** remains correct for its narrower API/pipeline: that pipeline refuses to accept native PSI→MN5 transfer or native Dα7 conductance as established biological inputs and does not perform those calculations. The separate conditional analysis does not alter that freeze or open a native evidence gate. No code or freeze values are changed by this terminology resolution.

`MODEL-AUTHORIZED` does **not** mean experimentally validated, a native physiological measurement, native in-vivo PSI→MN5 transfer, native Dα7 conductance measurement, or direct SIZ registration.

## Unresolved gates

- Native PSI→MN5 spatial voltage transfer and contact-to-soma anatomy remain unmeasured/unresolved.
- Native MN5 Dα7 conductance remains unavailable.
- SIZ registration to MaleCNS remains unresolved.
- C-01 remains unresolved: 43 ± 2 pF versus 127 ± 16 pF.
- **Repository mapping:** C-02 is the GF gap-junction discrepancy (135/34.5 µS in the paper table versus 135/34.5 nS in executed source); C-03 is the PSI→DLMn chemical-synapse discrepancy (80 µS versus 0.08 µS). The prompt's short labels reverse these two; this scope follows `research/conflicts.md` and `research/parameter_adoption_plan.md`. Neither conflict is resolved here.
- Absolute ShakB conductance remains unknown.

## Paper-safe claims

- MaleCNS v1.0 contains the recorded 43 PSI→MN5 partner contacts at minconf 0.5 in the two stated pairings.
- The official `compartment_post` annotation is `axon` on those 43 records, as a connectomic dataset label.
- No per-contact anatomy-based path to soma or native voltage-transfer measurement is established in the reviewed records.
- The input freeze and adoption ledger report their stated counts in separate taxonomies.
- The two-gate analysis explores local and abstract-bridge model behavior over explicitly declared assumptions; its outputs are conditional and model-derived.
- Software tests check implementation/provenance/numerical expectations, not empirical biological validity.

## Paper-unsafe claims

- “We measured native PSI→MN5 voltage transfer,” “the 43 contacts have measured somatic transfer,” or equivalent.
- “Native MN5 Dα7 conductance/density was measured,” or treating an assumed effective conductance as one.
- “The SIZ was registered to MaleCNS” or “SWC Type 0 means axon/dendrite.”
- Any statement that C-01/C-02/C-03 is resolved, or any absolute ShakB conductance claim.
- “The model was experimentally/biologically validated” based on tests, numerical fit, the 4.71 mV GF-stimulation comparison, or threshold crossings.
- Treating a model-authorized conditional analysis as experimentally validated native physiology, a probability, or a direct measurement.
