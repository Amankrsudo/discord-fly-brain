# Evidence classification

The project distinguishes these classes in claims, parameters, figures, and validation outputs. A result must not silently move from one class to another.

| Class | Meaning | Boundary |
|---|---|---|
| Literature-derived | Value or statement reported by a cited publication. | Preserve the measured object, species, method, units, sample/statistic, and caveats. A parameter used by an earlier model is not automatically a native measurement. |
| Primary-dataset-derived | Value computed from or label read from a deposited primary dataset, such as MaleCNS v1.0. | Record dataset version, source field, body IDs, confidence threshold, and processing. Dataset annotations are not electrophysiology. |
| Repository-derived | Fact read from project source, configuration, artifacts, tests, or executed-model code. | Establishes repository contents or execution, not necessarily biological reality. Track file and tree status. |
| Model-derived | Simulated, fitted, or calculated output from a declared model and inputs. | Conditional on model structure and assumptions; not a biological measurement. |
| Assumptions | Explicit choices used where direct evidence is missing or insufficient. | Keep visible, sensitivity-test where appropriate, and never promote to measured facts. |
| Validation fixtures | Synthetic, hand-authored, or expected values used to test software. | Evidence only that code meets a test expectation; not independent biological or dataset evidence. |

## Open scientific gates

- **Native PSI→MN5 voltage transfer:** not experimentally measured. An optional abstract cable bridge is conditional and model-derived; it is neither native transfer nor a per-contact anatomical path.
- **Native Dα7 conductance:** unavailable. Receptor/channel evidence from other preparations does not establish native MN5 synaptic conductance or density.
- **SIZ registration:** MN5 spike initiating zone is not registered to MaleCNS coordinates or skeletons.
- **C-01, capacitance:** 43 ± 2 pF (n=22) and 127 ± 16 pF (reported SD) conflict and remain separate.
- **C-02, gap-junction conductance:** repository records paper values in µS and executed source values in nS, a 1000× discrepancy.
- **C-03, PSI→DLMn chemical conductance:** repository records paper value 80 µS and executed source value 0.08 µS, a 1000× discrepancy.
- **ShakB absolute conductance:** unknown; plaque fraction or relative evidence does not provide absolute junction conductance.

Additional documented limits include undefined MaleCNS SWC `kind` semantics, no established anatomy-based contact-to-soma paths, and no native PSI-specific voltage measurement. MaleCNS `compartment_post="axon"` is the official annotation label; it does not establish voltage transfer. The 4.71 ± 0.35 mV EPSP is GF-stimulated and is a comparison/calibration target, not a PSI-specific measurement.
