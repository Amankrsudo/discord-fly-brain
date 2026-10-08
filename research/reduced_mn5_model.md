# Reduced MN5 Model — Architecture and Boundaries

**This model is a reduced computational abstraction. Its outputs are
model-derived and are not measurements of MN5 physiology.**

Module: `biological_brain/reduced_mn5.py` · version 1.0.0
Gates: **PSI→MN5 spatial voltage transfer: NOT AUTHORIZED** · **Dα7 conductance: NOT AUTHORIZED**

---

## A. Purpose

To provide the first *executable* MN5 model that the frozen evidence actually
permits — and to make it impossible to mistake for anything more.

It represents a resting state, a threshold, and a spike-output abstraction. It
does not integrate a membrane equation, because every parameter such an equation
requires is blocked or contested.

---

## B. Exact biological inputs

Three. All SAFE, all native experimental measurements, all somatic whole-cell
recordings of adult *Drosophila* MN5.

| parameter | symbol | value | unit |
|---|---|---|---|
| resting potential | — | **−67.8 ± 5.5 (SD), n=13** | mV |
| spike threshold | — | **−24.1 ± 8.2 (SD), n=11** | mV |
| action potential amplitude | — | **+45.5 ± 8.6 (SD), n=13** | mV |

That is the complete biological basis. Nothing else is supplied, defaulted, or
implied.

## C. Provenance of every input

| parameter | provenance | status | source |
|---|---|---|---|
| MN5 resting potential | `native_experimental_measurement` | SAFE | Ryglewski, Kilo & Duch 2014, *Eur J Neurosci* 39:151, Table 1 |
| MN5 spike threshold | `native_experimental_measurement` | SAFE | same |
| MN5 action potential amplitude | `native_experimental_measurement` | SAFE | same |

All three are read from `research/model_input_freeze.csv` and retrieved through
`ParameterSet.require_uncontested()`, so a value carrying an unresolved conflict
could not be substituted even by accident.

**Nothing here is `model_assumption`.** The model's own provenance summary
reports the full 108-row inventory (40 SAFE / 31 ASSUMPTION / 37 BLOCKED) so a
reader can see exactly what was and was not used.

---

## D. What the model can represent

| capability | status |
|---|---|
| resting-state representation | AVAILABLE |
| threshold representation | AVAILABLE |
| spike-output abstraction | AVAILABLE |
| deterministic response to explicitly supplied software inputs | AVAILABLE |
| parameter/provenance reporting | AVAILABLE |

Usage:

```python
from biological_brain.reduced_mn5 import ReducedMN5Simulator, SOFTWARE_INPUT_MARKER

sim = ReducedMN5Simulator()
sim.run([10.0] * 6)                     # software inputs, in mV
[spike.peak_mv for spike in sim.spikes] # model output, never a measurement
sim.report()                             # full provenance + capability surface
```

---

## E. What it cannot represent

- PSI→MN5 EPSP amplitude or kinetics
- distal-to-soma voltage attenuation
- MN5 cable behaviour
- Dα7 currents
- native GFS electrical coupling

`report()["does_not_claim"]` enumerates these explicitly, and
`assert_no_biological_claim()` refuses them programmatically.

---

## F. Why it is not a cable model

Because a cable model needs `Ra`, `Rm` and `Cm`:

| parameter | status | why |
|---|---|---|
| `Ra` | **BLOCKED** | the only value ever applied to Drosophila MN5 is 90 Ω·cm, adopted from *Manduca sexta*. The only *measured* Drosophila motor-neuron value is 212.47 ± 3.69 Ω·cm (larval aCC) — 2.4× different |
| `Rm` | **BLOCKED** | no measurement exists in any accessible source |
| `Cm` | **CONTESTED (C-01)** | 43 ± 2 pF vs 127 ± 16 pF, same cell, same nominal preparation, ~2.95×. No source reconciles them |

`is_cable_model` is `False`, `capabilities()["cable_behaviour"]` is `BLOCKED`,
and the simulator exposes no compartment, no `diam`, no length, no `tau`.

### There is deliberately no leak term

The natural implementation is a leaky integrator, and the project already has
one: `dynamics/lif_voltage.py::LIFVoltageModel`. **It is deliberately not used.**

A leaky integrator requires a membrane time constant. `tau_m` is **BLOCKED** —
no qualifying measurement exists for MN5. Adding a decay would mean inventing a
value, so this model has **no decay term at all**.

**Consequence, stated plainly:** voltage does **not** relax toward rest between
inputs. It moves only when an explicit software input moves it, and returns to
rest only on a spike. That is not a simplification of a leak — it is the
*absence* of one. `require_leak()` raises with this explanation.

---

## G. Why PSI→MN5 synaptic physiology is excluded

No synaptic conductance exists. Across the entire literature:

- no synaptic or peak conductance was ever derived, estimated, or named;
- no reversal potential (one holding point only, −74 mV);
- no EPSP latency, rise time or decay constant — Kuehn/Duch-era work explicitly
  *rejected* a kinetics explanation;
- no quantal size, quantal content, release probability or active-zone count.

The only conductance figures in existence are ModelDB 245415's, which are
explicitly "(estimated)" and are internally contradictory by exactly 1000×
(80 µS in Table 1 vs 0.08 µS as executed). Those are model fixtures, not
measurements.

The 43 official `compartment_post = axon` labels are carried as **metadata**.
They give a contact's compartment; they give no weight, because no conductance
exists to weight it with. The model therefore exposes **no synaptic input path
at all** — `apply_software_input` is the only way to move the voltage, and it
requires the caller to pass `SOFTWARE_INPUT_MARKER`.

---

## H. Why Dα7 is excluded

`Dalpha7Interface` in `model_framework.py` is a **schema**. It declares six
required inputs, reports `available: False, implemented: False`, and its
`conductance()` always raises.

Nothing native exists: no single-channel conductance, open probability,
reversal potential, activation or desensitisation kinetics, Ca²⁺ permeability, or
density at this synapse. Dα7 has never been imaged at PSI terminals or MN5
axons. Receptor identity at PSI→MN5 is a **genetic inference** (allele strength
correlated with EPSP amplitude), not a direct identification — and the rescuing
`OK307-GAL4` driver is expressed in GF, DLMmn, TTMmn *and* PSI, so it does not
localise Dα7 to MN5.

Separately: **Drosophila has no Kir7.1/KCNJ13 orthologue** (only `Irk1/2/3`).
The vertebrate α7→Kir7.1 mechanism has no fly homologue and must not be modelled.

---

## I. Model output vs native measurement

Every output is tagged. `SpikeEvent.is_measurement()` returns `False`
unconditionally, and `as_dict()` carries:

```python
{"kind": "model_output", "is_measurement": False,
 "note": "MODEL-DERIVED OUTPUT of a reduced abstraction. NOT a native MN5
          measurement and not an electrophysiological record."}
```

`report()["result_kind"] = "model_derived_output"` and
`report()["is_measurement"] = False`.

A simulated spike cannot be mistaken for a recorded one, because nothing in the
output type says "measurement" and the only three biological numbers in the
model are inputs that came *from* measurements.

---

## J. How future data can upgrade the model

No redesign is needed.

1. Add the measured value to `research/scripts/build_model_input_freeze.py`
   with provenance `native_experimental_measurement` and `safe_now=yes`.
2. Regenerate: `python research/scripts/build_model_input_freeze.py`.
3. `ReducedPassiveMN5` and this model will see it.

Specific upgrades and what each would enable:

| new measurement | would enable |
|---|---|
| `tau_m` for MN5 | a decay term; a genuine leaky integrator; `dynamics/lif_voltage.py` becomes usable |
| `Ra` **and** `Rm` for Drosophila MN5 | a cable model — the single largest upgrade |
| an adjudicated `Cm` | removes C-01; the two 43/127 pF rows collapse to one |
| native PSI→MN5 synaptic conductance | a synaptic input path, still without Dα7 attribution |
| native Dα7 conductance | the Dα7 interface becomes implementable |

Until each exists, the corresponding capability stays `BLOCKED` and the refusal
messages stand.

---

## K. Biological-claim safety

`assert_no_biological_claim()` refuses "PSI EPSP reproduced", "native MN5 EPSP
reproduced", "spatial transfer calculated", "Dα7 current calculated", "this is a
cable model" and "measured MN5 response". Tests assert the same, and assert that
the module contains no default biological constant and no banned Dα7 token that
would trip the package-wide safety scanner in `tests/test_biological_brain.py`.
