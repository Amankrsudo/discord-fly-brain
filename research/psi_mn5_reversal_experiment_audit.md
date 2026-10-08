# PSI→MN5 Reversal-Potential Experiment Audit

Experimental-design / evidence-gap audit. **No experiment was performed, no
model was built, no parameter was fitted, no gate was changed.**

## Executive Verdict

A somatic reversal series at PSI→MN5 would **PARTIALLY RESOLVE B-6**. It can
establish that a synaptic current exists, bound its **apparent somatic**
reversal potential, and demonstrate voltage dependence. It **cannot** measure
the local synaptic reversal potential, the synaptic conductance, the synaptic
kinetics, or anything about contact→soma transfer — and it must never be
presented as doing so.

Of 19 quantities audited, **14 are not identifiable** by this design
(`research/psi_mn5_reversal_experiment_audit.csv`).

## B-6 Definition

**B-6 = no PSI→MN5 synaptic conductance or experimentally established reversal
potential.**

Precisely what is known versus missing, from `research/model_input_freeze.csv`:

| quantity | value | provenance | status |
|---|---|---|---|
| contact count | 17 + 26 = 43 (minconf 0.5) | `anatomical_measurement` | SAFE |
| `compartment_post` | `axon` ×43 | `anatomical_measurement` | SAFE |
| `compartment_pre` | `axon` ×38, `unknown` ×5 | `anatomical_measurement` | SAFE |
| transmitter | acetylcholine | `anatomical_measurement` | SAFE |
| receptor identity | Dα7 nAChR (**genetic inference**) | `model_assumption` | ASSUMPTION |
| somatic EPSP (WT) | 4.71 ± 0.35 mV (n=10), −74 mV, **GF stimulated** | `native_experimental_measurement` | ASSUMPTION |
| somatic EPSP (*gfA*¹) | 1.5 ± 0.32 mV (n=7) | `native_experimental_measurement` | ASSUMPTION |
| **reversal potential** | **NONE** | `model_assumption` | **BLOCKED** |
| **synaptic conductance** | **NONE** | `model_assumption` | **BLOCKED** |
| EPSP latency / rise / decay | **NONE** (all three) | `model_assumption` | **BLOCKED** |
| quantal size / release probability / AZ count / density | **NONE** (all four) | `model_assumption` | **BLOCKED** |
| short-term plasticity | **NONE** | `model_assumption` | **BLOCKED** |
| synaptic delay | 0.5 ms **explicitly assumed** | `model_assumption` | ASSUMPTION |

**Known:** where the 43 contacts are, on which compartment, the transmitter, and
one filtered somatic voltage at one holding potential.
**Missing:** the whole synaptic current–voltage relation, and therefore the
driving force, the conductance, and every quantity derived from them.

## What a Reversal Series Can Measure

The measurement logic, stated without pretending it has been performed.

For a synaptic current under a clamp at holding potential `V_h`:

```
I_syn = g_syn · (V_local − E_rev)
```

A somatic series measures `I_somatic(V_hold)` — or, in current clamp, a somatic
EPSP amplitude that is **not proportional to any current at a fixed potential**.

What follows, honestly separated:

1. **Zero-crossing.** The amplitude-vs-holding-potential curve changes sign. The
   crossing estimates **E_rev**. Under somatic voltage clamp this crossing is
   the **somatic apparent reversal**: passive filtering attenuates faster
   components and pulls the observed response toward rest, so the apparent value
   is displaced from the local `E_rev` toward the somatic resting potential.
2. **Voltage dependence.** The *existence* and *direction* of voltage dependence
   is established qualitatively and robustly — this needs no cable knowledge.
3. **Apparent conductance.** `g_apparent = I_peak / (V_hold − E_rev_app)` is
   computable. It is the **somatic** conductance: already multiplied by the
   attenuation between the synapse and the clamp. It is *not* `g_syn` at the
   contact.
4. **Single-point route.** `g = EPSP_amplitude / (V_rest − E_rev)` — the classic
   shortcut — is **unavailable twice over**: `E_rev` is unknown, and the
   somatic EPSP is a filtered voltage, not a current at a known potential.

**Critically: conductance and attenuation are not separable from one another at
a single recording site.** Any conductance extracted from a somatic clamp is
`g_syn × attenuation`. Reporting it as `g_syn` assumes the very quantity that
is blocked.

## What It Cannot Measure

- the **local** synaptic reversal potential at the contact
- the **synaptic** conductance independent of attenuation
- synaptic **kinetics** (rise/decay are the filtered time course)
- the **local driving force** `V_local − E_rev`
- quantal size, release probability, active-zone count, receptor density,
  single-channel conductance
- Ra, Rm, or the contest on Cm (C-01)
- the **contact→soma transfer ratio** — a different observable, blocker B-4

## Recording Configuration

All 43 contacts carry `compartment_post = axon`. Two facts make the somatic
choice consequential:

- Fayyazuddin 2006 reports PSI contacts *"span 50 μm and follow the axons out
  into the posterior dorsal motor nerve"* — i.e. **peripheral**, along the main
  process, not on a proximal dendrite.
- The **contact→soma path is UNRESOLVED** (no `kind=1` node exists in any of the
  9 skeletons). The only available figure, contact→soma-**proxy** path
  154.1–241.6 µm, is `model_derived_estimate` resting on a `model_assumption`.

Therefore the anatomy **cannot** establish that a somatic clamp is
electrotonically compact with the synapse. The design therefore faces two
unresolved cases:

| case | consequence for a somatic reversal series |
|---|---|
| contacts proximal enough to be compact | apparent `E_rev` ≈ local `E_rev`; apparent `g` ≈ synaptic `g` |
| contacts distal along the main process | observed I–V is the local I–V convolved with the somatic transfer function; apparent `E_rev` shifted toward rest; apparent `g` reduced |

**Which case holds is not determinable from existing anatomy.** So a somatic
series returns a **bound**, not a value — which is still useful, and is exactly
what "PARTIALLY RESOLVED" should mean.

Local recording at the contact is **not currently feasible**: the synapse is in
the peripheral nerve, not on a dendrite at the soma, and electrode access to
insect small processes is documented as impractical (Gouwens & Wilson 2009).

## Voltage-Clamp / Space-Clamp Requirements

To be demonstrated before any somatic series is interpretable — **no numerical
acceptance threshold is proposed here**, because inventing one is exactly what
this project forbids and no project source supports a specific value:

- **Access / series resistance** reported per cell, with rejection criteria
  stated in advance and applied to every cell.
- **Voltage-clamp error** quantified (bridge balance, charging curve), not assumed.
- **Space clamp** justified for the *stimulated* synapse specifically, using the
  MaleCNS geometry — which requires first resolving the contact→soma path.
- **Holding-potential range** chosen to bracket the sign change; must avoid
  recruiting voltage-dependent postsynaptic currents. MN5 carries large
  transient A-type K⁺ (V½ activation −12.1 ± 1.4 mV; inactivation −40.02 ±
  0.33 mV) and Ca²⁺ currents (activated near −50 mV). Those currents will
  distort a somatic I–V above roughly −60 mV, so the synaptic component must be
  separated by subtraction or pharmacology, and the subtraction itself validated.
- **Distinguishing synaptic from postsynaptic active current** is mandatory here,
  not optional: MN5 is not a passive cell at these voltages.
- **Leak subtraction** validated, with the same space-clamp caveat.

## PSI-Specificity Requirements

This is the largest practical burden and it is **quantifiable from existing
anatomy**:

| body | total postsynapses | distinct presynaptic bodies | PSI contacts | PSI share | largest single partner |
|---|---|---|---|---|---|
| 801970 | 10,529 | **887** | 17 | **0.16 %** | 149 |
| 801295 | 11,260 | **897** | 26 | **0.23 %** | 168 |

(Retrieved from `gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed`.)

PSI is a **minority** input, and the largest individual partner contributes
118–168 synapses — roughly **7–10× more than PSI**. Any stimulation that is
not confined to PSI will be swamped. Required controls:

- **Direct PSI activation** (focal electrical or optogenetic). Fayyazuddin 2006
  stimulated the **giant fiber**, not PSI, and PSI was then driven through the
  GF→PSI electrical synapse — so its recorded response was not PSI-specific.
- **Latency separation** from other known MN5 partners.
- **Polysynaptic exclusion**: with ~887 converging bodies and MN5 driving the
  flight path, network recruitment must be excluded, not assumed.
- **No muscle/peripheral feedback** in the recorded window.
- **Excluding electrical coupling**: PSI→MN5 is a chemical synapse, but PSI
  participates in the GFS gap-junction network, so coupled contributions must be
  controlled.

## Pharmacology and Dα7 Interpretation

**The experiment measures the synaptic RESPONSE, not the receptor.**

| inference | status |
|---|---|
| cholinergic transmission at PSI→MN5 | `anatomical_measurement` — conditional *cha* mutations (Gorczyca & Hall 1984) |
| the receptor is Dα7 | **`model_assumption`** — genetic inference from allele strength vs EPSP amplitude; the rescuing `OK307-GAL4` driver is expressed in GF, DLMmn, TTMmn **and** PSI, so it does not localise Dα7 to MN5 |
| a Dα7-specific `E_rev` | **NOT AVAILABLE.** No native *Drosophila* Dα7 reversal potential exists in the evidence base, and no native single-channel conductance, open probability, kinetics or Ca²⁺ permeability |
| ion selectivity of the native receptor | **NOT AVAILABLE** — the Ca²⁺-permeability statement in the literature is a homology inference from vertebrate α7 |

A generic vertebrate α7 reversal (commonly 0 mV) **must not** be imported, and
the project's existing constraint barring a 0 mV reversal from being read back as
a Dα7 property remains in force. Pharmacological antagonism could *separate*
components of the response; it would not, by itself, identify the receptor
conductance.

## Identifiability Table

Full machine-readable version: `research/psi_mn5_reversal_experiment_audit.csv`
(19 rows).

| Quantity | Identifiable? | Required measurement / assumption | Why |
|---|---|---|---|
| local synaptic `E_rev` | **NO** | a recording site compact with the synapse, or an independent attenuation correction | the observed zero-crossing is a somatic apparent value |
| apparent somatic `E_rev` | **YES** (apparent only) | multi-point series with adequate clamp | needs no cable knowledge, but is not the local value |
| synaptic I–V | **PARTIALLY** | multi-point series | only the zero crossing is filter-robust |
| peak synaptic `g_syn` | **NO** | local recording | `I_peak/(V−E_rev)` gives somatic apparent `g`, already attenuated |
| `g_syn` independent of attenuation | **NO** | nothing at one site | conductance and attenuation are inseparable there |
| conductance kinetics | **NO** | local recording | somatic time course is filtered |
| local driving force | **NO** | local `V_m` and local `E_rev` | neither is supplied |
| quantal size | **NO** | separate miniature experiment | not part of a reversal series |
| release probability | **NO** | failure analysis at a defined site | release sites are peripheral |
| active-zone count | **NO** | EM | different modality |
| receptor density | **NO** | EM crowding or calibrated binding | different modality |
| receptor single-channel conductance | **NO** | single-channel native recording | no native value exists |
| **contact→soma transfer ratio** | **NO** | dual-site or optical recording | different observable (B-4) |
| Ra | **NO** | current injection at **≥3** known locations + identifiability | two sites constrain only Ra·Rm jointly; **no reversal design yields Ra** |
| Rm | **NO** | separate measurement | non-MN5 sources differ 4.4× |
| Cm | **PARTIALLY** (same contested quantity) | nothing in this design | C-01 unresolved |
| transmitter identity | already established | — | not re-derived |
| receptor identity (Dα7) | **NO** | direct identification | inferred only |
| input specificity | **YES** (with controls) | direct PSI stimulation + controls | achievable but demanding |

## Minimum Experiment

**A · Minimum — bounds `E_rev`, establishes voltage dependence.**
Somatic whole-cell voltage clamp on MN5; **direct PSI stimulation**; EPSP
amplitude or synaptic current at ≥5 holding potentials bracketing the sign
change; leak and postsynaptic-current subtraction validated; access resistance
and clamp error reported per cell with pre-stated rejection criteria.
- **Measures:** apparent somatic `E_rev`; existence and sign of voltage
  dependence; an *upper bound* structure on the local value.
- **Controls:** direct-activation specificity, latency separation, polysynaptic
  exclusion, no muscle feedback.
- **Confounds:** space clamp; MN5 A-type K⁺ and Ca²⁺ contamination; leak
  subtraction.
- **Justified:** "a voltage-dependent synaptic current exists at PSI→MN5; its
  somatic apparent reversal lies between X and Y."
- **Still unauthorized:** any local `E_rev`, any `g_syn`, any kinetics, any
  transfer statement.

## Stronger Experiment

**B · Stronger — adds a local-geometry constraint and separates currents.**
As A, plus: drug or voltage protocol isolating the synaptic component from MN5
active currents; focal PSI stimulation with a spatial map of which MN5 partner is
engaged; and, critically, an **independent** determination of the
contact→soma electrotonic status (see X-06 in the gate review) so the somatic
apparent values can be *corrected* rather than merely bounded.
- **Justified:** a corrected `E_rev` estimate with a stated attenuation model.
- **Still unauthorized:** presenting the corrected value as a native MN5
  measurement, and any transfer claim.

## Gate-Opening Experiment

**C · Gate-opening — the actual requirement, and it is NOT a reversal series.**
Gate 1 opens on a **measured contact→soma voltage transfer ratio**: dual-site
recording (somatic + the contact-bearing process) or optical voltage mapping
along the MN5 arbor, during focal PSI stimulation. Ranking from the gate review:

| # | measurement | removes | gives transfer directly? |
|---|---|---|---|
| 1 | dual-site voltage recording | B-4 directly | **yes** |
| 2 | optical voltage mapping | B-4 | yes |
| 3 | **reversal series (this audit)** | **part of B-6** | **no** |
| 4 | ≥3-site current injection | B-1, B-2 jointly | no |
| 5 | Cm reconciliation | B-3 | no |

A reversal series is **#3 of 5**. It is worth doing because it is the cheapest
way to bound the synaptic source before propagation is measured, but it does not
open Gate 1 and must not be sold as doing so.

## Remaining Blockers

Unchanged by this audit. **B-6 becomes PARTIALLY resolved**; B-1 through B-5 are
untouched.

| # | blocker | status after this audit |
|---|---|---|
| B-1 | `Rm` for MN5 unmeasured and unboundable | **unchanged** |
| B-2 | `Ra` for MN5 unmeasured | **unchanged** |
| B-3 | `Cm` contested 43 vs 127 pF | **unchanged** — a reversal series cannot adjudicate it |
| B-4 | no MN5 non-somatic / dual-site voltage | **unchanged** |
| B-5 | contact→soma path to a labelled soma unresolved | **unchanged** |
| B-6 | no synaptic conductance or `E_rev` | **PARTIALLY RESOLVED** — apparent `E_rev` and voltage dependence only |

## Evidence vs Inference vs Proposal

**(i) Direct evidence — Drosophila, MN5:** 43 contacts with official
`compartment_post = axon`; 887/897 distinct presynaptic bodies; one somatic EPSP
at one holding potential with GF stimulated; Rin, V_rest, threshold, AP
amplitude; A-type K⁺ and Ca²⁺ current kinetics.

**(ii) Methodological precedent:** voltage-clamp reversal series as a standard
technique; somatic recording of distal synapses subject to space-clamp error;
electrode access to insect small processes described as impractical.

**(iii) Inference (not measurement):** receptor is Dα7; the proximal dilation is
the soma; the contact→soma-proxy path represents the true route.

**(iv) Proposal (this document):** the A/B/C designs, their controls, their
confounds, and the identifiability table. **Nothing in (iv) has been performed.**

## Final Gate Status

**PSI→MN5 spatial voltage transfer: NOT AUTHORIZED**

**Dα7 conductance: NOT AUTHORIZED**

Neither is opened by this audit. The gate review's verdict is unchanged, and
this audit narrows B-6 only to the extent that an apparent somatic reversal
potential and voltage dependence become experimentally reachable.

## Provenance

| statement | class |
|---|---|
| 43 contacts, `compartment_post = axon`, 887/897 partners | `anatomical_measurement` |
| contact→root / straight-line / proxy paths | `anatomical_measurement` / `model_derived_estimate` |
| contact→soma-proxy path | `model_derived_estimate` on a `model_assumption` |
| somatic EPSP, Rin, V_rest, threshold, AP amplitude, A-type K⁺ | `native_experimental_measurement` |
| MN5 `Cm` (43 / 127 pF) | `native_experimental_measurement`, **contested (C-01)** |
| receptor identity Dα7 | `model_assumption` (genetic inference) |
| synaptic delay 0.5 ms | `model_assumption` (explicitly assumed) |
| the identifiability analysis and all three designs | **proposal**, not measurement |
| apparent `E_rev`, `g_syn`, kinetics, transfer ratio | **NO VALUE EXISTS** |
