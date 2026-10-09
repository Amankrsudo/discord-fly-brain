# Evidence classification

The project distinguishes five evidence classes — enforced in `biological_brain/model_framework.py` (`ModelProvenance`) and `biological_brain/malecns_ingest.py` (`EvidenceClass`) — in claims, parameters, figures, and validation outputs. A result must not silently move from one class to another. Repository-execution facts and validation fixtures are recorded separately by the validation package; they are not biological evidence classes.

| Class | Code | Meaning | Boundary |
|---|---|---|---|
| Native experimental measurement | `NATIVE_EXPERIMENTAL_MEASUREMENT` (NEM) | Value derived from direct measurement in native tissue (e.g., electrophysiology recordings, EPSPs). | Preserve measured object, species, method, units, sample size, and caveats. A parameter used by an earlier model is not automatically a native measurement. |
| Anatomical measurement | `ANATOMICAL_MEASUREMENT` (AM) | Connectomic or standard anatomical observation from deposited datasets (e.g., MaleCNS v1.0 synapse annotations, compartment labels). | Record dataset version, source field, body IDs, confidence threshold, and processing. Dataset annotations are labels, not electrophysiology. |
| Literature-derived passive parameter | `LITERATURE_DERIVED_PASSIVE_PARAMETER` (LDP) | Value or statement reported by a cited publication. | Preserve the measured object, species, method, units, sample/statistic, and caveats. |
| Model-derived estimate | `MODEL_DERIVED_ESTIMATE` (MDE) | Simulated, fitted, or calculated output from a declared model and inputs. | Conditional on model structure and assumptions; not a biological measurement. |
| Model assumption | `MODEL_ASSUMPTION` (MA) | Explicit choices where direct evidence is missing or insufficient; includes facts read from repository source/configuration. | Keep visible, sensitivity-test where appropriate, and never promote to measured facts. |

## Open scientific gates

- **Native PSI→MN5 voltage transfer:** not experimentally measured. An optional abstract cable bridge is conditional and model-derived; it is neither native transfer nor a per-contact anatomical path.
- **Native Dα7 conductance:** unavailable. Receptor/channel evidence from other preparations does not establish native MN5 synaptic conductance or density.
- **SIZ registration:** MN5 spike initiating zone is not registered to MaleCNS coordinates or skeletons.
- **C-01, capacitance:** 43 ± 2 pF (n=22) and 127 ± 16 pF (reported SD) conflict and remain separate.
- **C-02, gap-junction conductance:** repository records paper values in µS and executed source values in nS, a 1000× discrepancy.
- **C-03, PSI→DLMn chemical conductance:** repository records paper value 80 µS and executed source value 0.08 µS, a 1000× discrepancy.
- **ShakB absolute conductance:** unknown; plaque fraction or relative evidence does not provide absolute junction conductance.

Additional documented limits include undefined MaleCNS SWC `kind` semantics, no established anatomy-based contact-to-soma paths, and no native PSI-specific voltage measurement. MaleCNS `compartment_post="axon"` is the official annotation label; it does not establish voltage transfer. The 4.71 ± 0.35 mV EPSP is GF-stimulated and is a comparison/calibration target, not a PSI-specific measurement.
