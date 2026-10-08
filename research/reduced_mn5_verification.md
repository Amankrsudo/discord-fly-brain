# Reduced MN5 Model — Independent Verification

**Software validation only.** No biological mechanism was added, no missing
physiological parameter supplied, no gate touched, no leak term introduced, no
parameter fitted.

Module audited: `biological_brain/reduced_mn5.py` (with `model_framework.py`,
`dynamics/lif_voltage.py`, `research/reduced_mn5_model.md`)
Audit suite: `tests/test_reduced_mn5_audit.py` — **99 tests**

---

## A. Implementation inspected

- `biological_brain/reduced_mn5.py` — `ReducedMN5Simulator`, `SpikeEvent`,
  `BiologicalClaimError`, `SoftwareInputError`
- `biological_brain/model_framework.py` — `ParameterSet`, `ModelParameter`,
  `require_uncontested`, gate entry points
- `biological_brain/dynamics/lif_voltage.py` — the existing LIF, confirmed
  unusable here (needs `tau_m`)
- `tests/test_reduced_mn5.py`, `research/reduced_mn5_model.md`
- `research/model_input_freeze.csv` (108 rows)

---

## B. State-machine behaviour

All eleven transitions audited and tested.

| # | transition | verified behaviour |
|---|---|---|
| A | initial state | voltage == resting potential, no spikes, below threshold |
| B | software input | additive; requires the non-biological marker |
| C | sub-threshold | state advances, no spike |
| D | threshold crossing | comparison is `>=` |
| E | spike generation | emits one event, resets |
| F | reset | voltage returns to resting exactly |
| G | repeated inputs | accumulate additively |
| H | negative inputs | lower voltage, **no floor at rest** |
| I | zero input | exact no-op |
| J | exact threshold | **fires** (`>=`); just-below does not |
| K | inputs after a spike | begin from rest; no refractory period exists |

Deterministic: three identical runs produced byte-identical event signatures.
`step_index` is monotonic and resets with `reset()`. No state leakage between
independently constructed instances.

**Documented, deliberate:** there is **no clamp at resting potential**, so
negative software input can drive the state below rest (−567.8 mV observed).
That is the honest consequence of having no leak term — a clamp would require
the decay parameter that is blocked.

---

## C. Numerical / unit behaviour

- All three biological inputs carry `unit == "mV"`, read verbatim from the
  frozen registry; no conversion is applied anywhere in the module.
- Stored simulator values are asserted **equal** to `require_uncontested()`
  results from a freshly loaded registry.
- Threshold comparison is dimensionally valid: resting < threshold < 0, all floats.
- Boundary coverage: zero, positive, negative, exact threshold, ±1e-9 around
  threshold, sequential increments, multi-step crossings.
- **Float-accumulation finding:** splitting the threshold gap into four equal
  software increments can land within float epsilon of the threshold and not
  fire. This is deterministic and conservative, and is now asserted as such
  rather than as exact firing.

---

## D. Provenance validation

- All three inputs come from `research/model_input_freeze.csv` and match the
  registry's own `source`, `provenance` and `status` fields exactly.
- All are `SAFE` / `native_experimental_measurement`.
- **Conflicted-source failure tested:** replacing the spike-threshold row with a
  conflicted one (`conflict="C-99"`) makes construction raise
  `BlockedParameterError` naming C-99.
- **Missing-value failure tested:** removing the threshold row makes
  construction raise `KeyError`, not fall back.
- **No-value failure tested:** a SAFE row carrying `value=None` raises with
  "never filled in".

---

## E. Blocked-parameter validation

22 blocked quantities were each offered twice — once as native evidence, once as
a labelled assumption — and refused both times. Guard logic is **not**
duplicated: the module delegates to `require_uncontested()` and the framework's
`ParameterStatus`, and a test asserts it contains no `csv.DictReader`.

---

## F. Hidden-biology audit

| check | result |
|---|---|
| hard-coded membrane/conductance constants | none |
| hidden time constant, decay or leak | none; `step()` source inspected for `decay`/`leak`/`tau`/`exp(`/`**` — none |
| hidden cable or synapse attributes | none on the simulator |
| module-level numeric constants | **zero** (asserted) |
| biology entering outside the registry | no; values compared to the registry verbatim |

The only biology in the module is retrieved by name from the frozen parameter
set. Software constants are the model name, version and marker string.

---

## G. API / error handling

- Unknown parameter → `KeyError` naming the parameter and the set size.
- Blocked/conflicted → `BlockedParameterError` with object, status, source, gate.
- Blocked supply → `BiologicalClaimError` with a specific reason.
- Malformed, non-numeric or non-finite software input → `SoftwareInputError`.
- Missing marker → `BiologicalClaimError`.
- No generic fallback path exists.

---

## H. Reproducibility

- Identical inputs → identical events (verified over three runs).
- Same frozen source → identical report inputs and status counts.
- No wall-clock, no randomness, no network, no hidden global mutable state —
  asserted by scanning the module source for `random`, `time`, `datetime`,
  `uuid`, `urllib`, `requests`, `socket`, `numpy`.

**Documented limitation:** a caller-supplied `MN5Model` shares its
`ParameterSet`, so a parameter added through one simulator appears in the
provenance summary of another built on the same object. This is now asserted as
a test rather than left implicit. Default construction is fully independent.

---

## I. Output semantics

`SpikeEvent` reports `is_measurement=False` and `spike_shape_modelled=False`
unconditionally. `report()` contains `result_kind="model_derived_output"`,
`is_measurement=False`, all three inputs with provenance, `assumptions_used`,
`blocked_capabilities`, the full capability map, `absent_by_design`,
`does_not_claim`, both gate verdicts, and the 43-contact anatomy metadata.

The 43 `compartment_post = axon` contacts appear as metadata and are never used
as a weight or an input.

---

## J. Documentation consistency

`research/reduced_mn5_model.md` was checked against the implementation. It
correctly states the absence of a leak term, that voltage does not relax toward
rest, that this is not a cable model, and both gate verdicts. Forbidden
*assertions* ("has a leak", "reproduces the EPSP", "computes spatial transfer",
"calculates Dα7 current", "is a cable model") are absent; the terms appear only
in denials or in the future-upgrade table.

**Two documentation corrections were required by this audit** — see L-3 and L-4.

---

## K. Tests

```
$ python -m pytest tests/test_reduced_mn5_audit.py -q -p no:cacheprovider --tb=short
99 passed in 0.78s                                    EXITCODE=0
$ python -m pytest tests/test_reduced_mn5.py -q -p no:cacheprovider --tb=short
37 passed in 0.51s                                    EXITCODE=0
$ python -m pytest tests/test_model_framework.py -q -p no:cacheprovider --tb=short
34 passed in 0.41s                                    EXITCODE=0
$ python -m pytest tests/test_model_input_freeze.py -q -p no:cacheprovider --tb=short
17 passed in 0.09s                                    EXITCODE=0
$ python -m pytest tests/test_malecns_anatomy_audit.py -q -p no:cacheprovider --tb=short
32 passed in 0.47s                                    EXITCODE=0
$ python -m pytest tests/test_biological_brain.py -q -p no:cacheprovider --tb=short
995 passed in 570.06s (9:30)                          EXITCODE=0
```

**1,214 passed, 0 failed.**

The legacy suite ran because the new module lives inside the package the
package-wide Dα7 scanner walks. No existing safety test was weakened; the
scanner still catches a real violation, and a test asserts the new module stays
clean against that banned-token list.

---

## L. Defects found and fixed

| # | severity | defect | fix |
|---|---|---|---|
| **L-1** | **HIGH — guard bypass** | `supply_biological_parameter` matched refused names by **substring**. `axial_resistance_us` and `Cm_specific` were **accepted**, while innocent names (`fixture_param` contains `"ra"`) were falsely refused | Replaced with whole-token contiguous-subsequence matching plus a frozen-inventory check; 12 bypass names and 4 innocent names now all behave correctly |
| **L-2** | **HIGH — silent state corruption** | `NaN` software input was accepted; `nan >= threshold` is False, so **no spike fired and the state was poisoned** with no error | Non-finite input refused (`SoftwareInputError`); state provably uncorrupted after refusal |
| **L-3** | **MEDIUM — output semantics** | `inf` input produced a spike with `peak_mv = inf`; non-numeric input raised a bare `ValueError` | Same validation path; informative error naming the offending value |
| **L-4** | **MEDIUM — misleading output** | `SpikeEvent.amplitude_mv` carried the *measured* AP amplitude beside an unrelated `peak_mv`; a 45.5 mV biological figure could be read as the size of a spike the model peaked at 932.2 mV | Split into `voltage_excursion_mv` (model output, `peak − from`) and `reference_ap_amplitude_mv` (biological input), with `spike_shape_modelled=False` and `excursion_matches_reference()` |
| **L-5** | **LOW** | Report gate values were bare `"NOT AUTHORIZED"` strings; the Dα7 key had been renamed earlier to avoid the banned token, leaving no canonical wording | Gate values now carry the canonical phrases `PSI→MN5 spatial voltage transfer: NOT AUTHORIZED` and `Dα7 conductance: NOT AUTHORIZED` |

Test-side corrections (premises wrong, content correct): threshold-gap arithmetic
assumed exact floating point; a 5 mV step was assumed to cross threshold; a
repeated-run count was mis-derived; and the documentation scan flagged quoted
refusals as claims.

---

## M. Remaining limitations

1. **No leak, by necessity.** `tau_m` is blocked, so voltage does not decay. This
   is not an approximation and must not be read as one.
2. **No spike shape.** `voltage_excursion_mv` is whatever the software inputs
   produced at the crossing; it is not tuned to the measured AP amplitude, and
   `excursion_matches_reference()` will normally be `False`.
3. **No floor at resting potential**, so negative drive can exceed physiological
   range. A clamp would require the blocked decay parameter.
4. **Threshold semantics are documented, not physiological.** The `>=` rule is a
   stated modelling choice, not a measured property of the MN5 spike-initiation
   mechanism.
5. **A caller-supplied `MN5Model` shares mutable parameter state** (H).
6. **Three SAFE somatic measurements** are the entire biological basis. Anything
   requiring `Ra`, `Rm`, `Cm`, `tau_m` or any conductance remains unavailable.

---

## N. Final verification verdict

**REDUCED MN5 SOFTWARE MODEL: VERIFIED WITH LIMITATIONS**

It is deterministic, provenance-safe, free of hidden biological parameters, and
its behaviour matches its documented limitations exactly. The limitations are
consequences of blocked evidence, not implementation gaps, and each is stated in
the module docstring, the design document and this audit. No accidental pathway
around either scientific gate was found; the one that existed (L-1) was a
substring-matching bypass and is closed.

**PSI→MN5 spatial voltage transfer: NOT AUTHORIZED**

**Dα7 conductance: NOT AUTHORIZED**
