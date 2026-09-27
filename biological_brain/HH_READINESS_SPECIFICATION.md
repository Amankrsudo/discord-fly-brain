# HH Readiness Specification (3.0D-6)

## Purpose

This document specifies the conditions under which a Hodgkin-Huxley-type
active-channel model may be added to the Biological Brain 3.0 architecture.
It does **not** implement HH, does **not** add ion-channel equations, does
**not** add HH parameters, and does **not** change dt or existing numerical
behavior.

It answers three questions:

1. Is active-channel modeling biologically justified?
2. Is it ready for implementation now?
3. What must be true before it is ready?

---

## 1. WHy HH IS BIOLOGICALLY JUSTIFIED

### Active ion channels are experimentally implicated in the GF

Kadas et al. 2019 (PMC6709211) shows that fast axonal conduction in the
Drosophila giant fiber (GF) relies on **Para** (fast sodium), **Shaker**
(fast potassium), and **L-type calcium** channels. This establishes
biological justification: the GF possesses the molecular machinery for
voltage-gated active conductance.

### The published GFS computational model uses active conductances

Augustin et al. 2019 (PMC6469880) implements the GFS as a multicompartment
conductance-based model in which active sections use **Hodgkin-Huxley-type
conductances**. The model's active channel kinetics are the computational
basis for spike generation and propagation latency.

**Conclusion:** Active-channel modeling is biologically warranted for at least
the GF lineage (GF → TTMn → DLMn, and GF → PSI → DLMn).

---

## 2. WHY HH IS NOT READY FOR IMPLEMENTATION

### Timestep insufficiency

The current simulator timestep is **dt = 1 ms**. The published motoneuron
model (Crotty et al. 2019, PMC6127168) uses dt = 0.01 ms and checks
stability across 0.005–0.02 ms. Na activation kinetics have tau ~ 0.1 ms,
which **cannot** be resolved at 1 ms. The NumericalResolution contract
already documents this constraint (3.0D-3).

Conventional explicit HH integration commonly requires sub-ms resolution
(~0.01 ms in relevant modeling literature, PMC3779145). The exact timestep
must be selected based on the integration method and model kinetics — it is
not a biological property to be hard-coded.

### Insufficient neuron-specific parameter sets

Augustin et al. 2019 states that some GFS model parameters were **manually
adjusted** so that model cells spiked and response latencies matched recorded
values. Published model parameters must therefore **not** be automatically
classified as directly measured GFS parameters.

LC4, LPLC2, and PSI currently have **no source-supported intrinsic HH
parameter sets**. They remain on lif_voltage by default.

### Architectural constraint

An HH implementation would require a different timestep than the current
engine default. The per-neuron dynamics architecture (3.0D-2) and
NumericalResolution contract (3.0D-3) provide the foundation, but the engine
does not yet support per-neuron timesteps or alternative integration methods.

**Conclusion:** HH is biologically justified but not ready. The blocking
factors are numerical resolution, incomplete parameter provenance, and
architectural constraints around timestep.

---

## 3. READINESS CATEGORIES

Each neuron is classified below based on **source-supported evidence**,
**not** on inference or guesswork.

| Neuron   | Readiness Category                                      | Rationale |
|----------|--------------------------------------------------------|-----------|
| GF       | PARTIALLY CONSTRAINED — READY ONLY WITH EXPLICIT BORROWED/MODEL PARAMETERS | Active channels (Para, Shaker, L-type Ca) implicated by Kadas et al. 2019. Augustin model provides HH-type parameters, but values were manually adjusted and are model-specific, not directly measured for this context. |
| TTMn     | PARTIALLY CONSTRAINED | Shares the GF lineage; motoneuron parameters available from Günay et al. 2015 via Augustin et al. 2019, but not neuron-specific validated parameters for the escape-circuit TTMn. |
| DLMn     | PARTIALLY CONSTRAINED | Motor output neuron in the escape pathway; L-type Ca channels implicated, but no complete neuron-specific HH parameter set. |
| PSI      | INSUFFICIENTLY CONSTRAINED | No source-supported intrinsic HH parameter set found. Must remain on lif_voltage until parameters are obtained. |
| LC4      | INSUFFICIENTLY CONSTRAINED | Visual interneuron; no HH parameters available. Must remain on lif_voltage. |
| LPLC2    | INSUFFICIENTLY CONSTRAINED | Visual interneuron; no HH parameters available. Must remain on lif_voltage. |

### Category Definitions

| Category | Meaning |
|----------|---------|
| **READY — FULLY SOURCE-SUPPORTED** | Complete, directly measured or experimentally constrained neuron-specific HH parameters exist for the exact neuron and model context. |
| **READY ONLY WITH EXPLICIT BORROWED/MODEL PARAMETERS** | HH parameters exist from a published model but are borrowed/adjusted, not directly measured for this neuron. Implementation permitted only with explicit provenance attribution. |
| **PARTIALLY CONSTRAINED** | Some parameters exist (e.g. reversal potentials, maximal conductances) but the set is incomplete for a defensible neuron-specific implementation. |
| **INSUFFICIENTLY CONSTRAINED** | No source-supported neuron-specific HH parameters. Cannot implement without inventing values. |
| **BLOCKED** | Implementation blocked by a cross-cutting constraint (e.g. timestep, integration method) even if parameters exist. |

**Current status:** No neuron is READY — FULLY SOURCE-SUPPORTED. GF, TTMn,
and DLMn are PARTIALLY CONSTRAINED / READY ONLY WITH EXPLICIT BORROWED/MODEL
PARAMETERS. PSI, LC4, and LPLC2 are INSUFFICIENTLY CONSTRAINED.

---

## 4. REQUIRED CONDITIONS BEFORE HH IMPLEMENTATION

A future HH implementation **must** satisfy all of the following:

1. **Parameter provenance.** Every biological parameter must carry an
   explicit `ProvenanceRecord` with a typed `ParameterProvenance` category
   and a human-readable source. Borrowed values must be labeled
   `BORROWED_CROSS_CONTEXT`. Manually adjusted values must be labeled
   `FITTED_CALIBRATED`. Estimated values must be labeled `ESTIMATED`.
   No parameter may be silently relabeled as `DIRECTLY_MEASURED`.

2. **Defensible parameter set.** A complete, neuron-specific HH parameter set
   must exist for each neuron that uses the HH model. Borrowed values are
   permitted only if explicitly attributed and clearly documented as such.

3. **Appropriate numerical resolution.** The HH model must declare a
   `NumericalResolution` with a `timestep_ms` justified by the integration
   method and kinetics. The engine must support the declared timestep
   (potentially via per-neuron timestep scheduling or sub-stepping).

4. **Suitable integration method.** The integration method must be
   documented and justified for the HH kinetics in question (e.g. explicit
   forward Euler, exponential Euler, Rush-Larsen). Stability analysis should
   accompany the choice.

5. **Experimental validation.** The HH model must be validated against
   experimental electrophysiological behavior (e.g. action-potential waveform,
   conduction latency, firing patterns). Published reference observations
   (GF-TTM ~0.7–1.2 ms, GF-DLM ~1.3–1.7 ms latency; 100 Hz following limits)
   may serve as validation targets but must not be used as tuning targets
   that override parameter provenance.

6. **Preservation of existing models.** The existing `lif_voltage` and
   `conductance_v0` models must remain numerically unchanged. HH is an
   opt-in model selected per-neuron, never a silent replacement.

7. **No silent replacement.** No measured or existing value may be silently
   replaced with a borrowed or estimated value. All substitutions must be
   traceable through `ProvenanceRecord`.

---

## 5. NUMERICAL REQUIREMENT

- **Current reduced models remain at dt = 1 ms.** No change to the engine
  timestep. `lif_voltage` and `conductance_v0` are validated at 1 ms.
- **Future active-channel models must declare their own NumericalResolution.**
  The `NumericalResolution` dataclass (3.0D-3) on the `DynamicsModel` protocol
  is the contract for this declaration.
- **Conventional explicit HH implementations commonly require sub-ms
  resolution.** Modeling literature (e.g. Drosophila motoneuron model,
  PMC6127168) uses dt ~ 0.01 ms. Forward Euler with HH kinetics can become
  numerically unstable at larger timesteps (PMC3779145).
- **The exact timestep must be selected based on the numerical method and
  model kinetics.** It is not a biological fact and must not be hard-coded
  as such.
- **dt = 1 ms must NOT be treated as sufficient for conventional explicit HH
  kinetics.** Any HH implementation at dt = 1 ms (if ever supported) must be
  explicitly documented as an APPROXIMATION with sub-threshold
  approximation notes.

---

## 6. PROVENANCE REQUIREMENT

HH parameters must be distinguished using the existing
`ParameterProvenance` taxonomy (3.0D-1A, `biological_brain/provenance.py`):

| Category | Meaning | Example |
|----------|---------|---------|
| `DIRECTLY_MEASURED` | Electrophysiology + EM reconstruction in same specimen | N/A for HH — no such data exists for GFS neurons |
| `EXPERIMENTALLY_CONSTRAINED` | Constrained by experimental fit or recording | Voltage-clamp I-V curves constraining reversal potential |
| `CONNECTOME_DERIVED` | Synapse counts from EM connectome | N/A for intrinsic channel parameters |
| `PUBLISHED_MODEL_PARAMETER` | Value from a published computational model | HH g_Na, g_K, E_Na, E_K from Günay et al. 2015 |
| `BORROWED_CROSS_CONTEXT` | Borrowed from a different neuron/cell type or species | GFS channel parameters borrowed from motoneuron model |
| `FITTED_CALIBRATED` | Manually adjusted or calibrated for simulator behavior | Augustin-adjusted values to match spike latencies |
| `ESTIMATED` | Estimated in the source, not measured | Model parameter ranges |
| `UNKNOWN` | No source or evidence available | Any parameter lacking citation |

### Specifically: Augustin et al. 2019

Augustin et al. explicitly states that some parameters were **manually
adjusted** to match recorded behavior. These values must be classified as
`FITTED_CALIBRATED`, **not** as `DIRECTLY_MEASURED` or `PUBLISHED_MODEL_PARAMETER`
in the narrow sense. The `evidence_to_provenance` mapping in `provenance.py`
already routes string labels to the correct enum categories; new HH parameter
ingestion must use explicit `ProvenanceRecord` entries.

---

## BLOCKERS SUMMARY

| Blocker | Detail |
|---------|--------|
| dt = 1 ms | Cannot resolve HH kinetics (tau ~ 0.1 ms). Must support sub-ms dt or alternative integration. |
| No neuron-specific HH parameters | No DIRECTLY_MEASURED or EXPERIMENTALLY_CONSTRAINED HH parameters exist for GF, TTMn, DLMn, PSI, LC4, or LPLC2. Published values are BORROWED_CROSS_CONTEXT or FITTED_CALIBRATED. |
| Engine architecture | No per-neuron timestep or sub-stepping mechanism. All neurons share the engine's dt. |
| LC4/LPLC2/PSI | INSUFFICIENTLY_CONSTRAINED — no HH parameters available at all. |
| No experimental validation framework | AHH model would need validation against AP waveform, latency, and firing patterns before biological claims can be made. |

---

## STATUS

**NOT READY.** HH is biologically justified but blocked by numerical
resolution, parameter provenance, and architectural constraints. This
specification will be revisited when the required conditions in Section 4
are met.
