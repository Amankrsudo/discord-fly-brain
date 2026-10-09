# Abstract (Draft)

We present a provenance-controlled framework for the *Drosophila* PSI→MN5 connection with five code-enforced evidence classes: native experimental measurement (NEM), anatomical measurement (AM), literature-derived passive parameter (LDP), model-derived estimate (MDE), and model assumption (MA). The framework hard-blocks requests for unmeasured native quantities.

MaleCNS v1.0 (Berg et al. 2026) at minconf 0.5 yields 43 PSI→MN5 contacts (17 left, 26 right), all `compartment_post=axon`. SWCs lack a `kind=1` soma node; no anatomically reconstructed contact-to-soma path exists — permanently UNRESOLVED. Contact geometry preserves three distinct metrics (mesh surface, SWC-root path, straight-line to `somaLocation`); none is converted to electrotonic distance.

Admissible native MN5 measurements (Ryglewski et al. 2014; Fayyazuddin et al. 2006): resting potential −67.8 ± 5.5 mV (n=13), spike threshold −24.1 ± 8.2 mV (n=11), AP amplitude +45.5 ± 8.6 mV (n=13), input resistance 102 ± 12 MΩ (n=22) / 97 ± 31 MΩ (n=52). Two capacitance values conflict (43 ± 2 pF vs 127 ± 16 pF; C-01); both retained. The 4.71 ± 0.35 mV somatic EPSP (n=10) was GF-stimulated — a comparison target only. Two 1000× conductance discrepancies (C-02, C-03) preserved unresolved.

Gates NOT AUTHORIZED: Gate A (PSI→MN5 spatial voltage transfer — no native measurement, no Drosophila Ra/Rm/Cm, no soma node) and Gate B (Dα7 conductance — no native MN5 synaptic conductance/density). A conditional two-gate sensitivity sweep (15,528 model-derived rows) produces contact-local, abstract-bridge, and Dα7 outputs explicitly conditional on assumptions — not native measurements or validation.

All outputs are tagged by evidence class; they do not establish biological measurements.