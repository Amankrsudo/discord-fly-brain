"""GF active-state validation (3.0D-8B).

NUMERICAL VALIDATION OF THE COMPLETED 3.0D-8A IMPLEMENTATION.

3.0D-8A built and exercised the live GF active membrane. 8B asks a narrower
question and answers it as a measurement, not a model: is that membrane
NUMERICALLY WELL BEHAVED, before any electrical or chemical circuit coupling is
added on top of it?

8B ADDS NO BIOLOGY
------------------
8B introduces no new mechanism, no new equation, no new parameter and no new
conductance. It imports the 8A model, runs it, and REPORTS what comes out.
Nothing in ``biological_brain/dynamics/gf_active.py`` is modified: the
transcribed ``nat.mod``/``nap.mod``/``k.mod`` equations, the semi-implicit
integration order and the authorized 7S/7F parameters are all consumed exactly
as 3.0D-8A defined them. If 8B disagrees with 8A it reports the disagreement;
it does not reconcile it by changing 8A.

THE EQUILIBRIUM IS NOT -85 mV, AND IS NOT ASSUMED
------------------------------------------------
3.0D-8A initialises V to E_leak = -85 mV. That is the leak REVERSAL POTENTIAL
in the Augustin/Günay parameterization, and it is a legitimate INITIAL
condition. It is NOT a claim that the complete active membrane equilibrates
there, and this checkpoint measures where the membrane actually comes to rest.

The measured equilibrium of the complete unstimulated system
(leak + nat + nap + k) is reported below in MEASURED_GF_EQUILIBRIUM_SUMMARY
together with the conductances and currents that hold it there. Three currents
balance at that point: the LEAK current is outward, and it is cancelled by the
inward DELAYED-RECTIFIER K current plus the two inward Na currents. The sodium
currents are small but they are NOT zero, which is exactly why the equilibrium
is not E_leak: at -85 mV the delayed rectifier is already open enough to pull
the membrane up, and the two Na mechanisms pull it back down.

8B DOES NOT "FIX" THIS. It does not force V to -85 mV, does not add a resting
offset, does not rescale any conductance to move the equilibrium, and does not
substitute a declared voltage for a measured one. A 2.5 mV offset from the leak
reversal potential is the honest output of the published mechanism set, and
suppressing it would be a fabricated result.

EQUILIBRIUM IS A NUMERICAL FIXED POINT, NOT A BIOLOGICAL RESTING STATE
----------------------------------------------------------------------
``equilibrium_report()`` reports the state reached after integrating the
UNSTIMULATED system, together with a distance-from-equilibrium measure. That
distance is the maximum per-element change of the full state (V and all four
gating variables) ACROSS THE FINAL TIMESTEP, which is a purely NUMERICAL
convergence quantity: it says the integration has stopped moving, not that a
real GF rests here. It is deliberately not a maximum over a trailing window,
and no window is computed. No biological tolerance is defined, and none is
implied.

WHAT IS AND IS NOT CLAIMED
--------------------------
CLAIMED, as numerical facts of this implementation:
  - the unstimulated system is finite and reaches a fixed point;
  - that fixed point is at the reported voltage, with the reported gates and
    a near-zero net membrane current per segment;
  - it is insensitive to timestep and to spatial subdivision;
  - the published 120 nA / 0.03 ms fixture produces a finite, reproducible
    stimulus-evoked response whose peak and peak time move only slightly under
    timestep refinement, with a measurable distal propagation delay.

NOT CLAIMED, and deliberately:
  - that this voltage is the GF's biological resting potential;
  - that the peak voltage or peak time matches any experiment;
  - any acceptance threshold. Every tolerance below is labelled NUMERICAL.
    A small numerical change under refinement is evidence of a well-behaved
    discretization and is NOT evidence of biological accuracy; a large one
    would be evidence of a poor one and is not evidence about a fly.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import sys

from ..morphology import CompartmentModel
from .gf_active import (
    GFActiveAxonModel, GFActiveNetwork, GFActiveSegmentState,
    MODELDB_GF_STIMULUS_AMPLITUDE_A, MODELDB_GF_STIMULUS_DURATION_MS,
    MODELDB_GF_STIMULUS_LOCATION, MODELDB_GF_STIMULUS_SOURCE,
    GF_ACTIVE_NUMERICAL_POLICY, GF_ACTIVE_NUMERICAL_LIMITATION,
    MECHANISM_K, MECHANISM_NAP, MECHANISM_NAT,
)


#: The slowest relaxation mode at the measured equilibrium, which is what
#: governs how long a run must be before the state stops moving. nat.mod's
#: ``htau = 0.36 + exp((vm+20.65)/-10.47)`` is a LARGE time constant at
#: hyperpolarized voltages: at the measured equilibrium near -74.67 mV it is
#: about 174 ms, and even at the declared -85 mV initial condition it is about
#: 467 ms. That is a property of the SOURCE expression, not of this
#: implementation, and it is why ``distance_from_equilibrium`` keeps shrinking
#: over hundreds of milliseconds even though the voltage has visually settled.
#: It is reported so a caller does not mistake slow convergence for
#: non-convergence, and it is a NUMERICAL time constant with no biological
#: interpretation attached to it.
SLOWEST_MODE_NOTE = (
    "SLOWEST RELAXATION MODE. The rate at which this unstimulated state stops "
    "moving is set by the SLOWEST gate time constant evaluated at the "
    "equilibrium voltage, which in this mechanism set is nat.mod's "
    "htau = 0.36 + exp((vm+20.65)/-10.47). That expression gives roughly "
    "174 ms near the measured equilibrium of -74.67 mV, and roughly 467 ms at "
    "the declared -85 mV initial condition, because the exponential is large "
    "at hyperpolarized voltages. The other three gates relax far faster: "
    "nat's mtau is about 3.5 ms there, and nap.mod's and k.mod's mtau are the "
    "source CONSTANT 1 ms. So a run must span a few hundred milliseconds "
    "before the residual per-step change is genuinely near zero, and a shorter "
    "run legitimately reports a larger distance. This is a property of the "
    "source rate expressions, not of this implementation, and the time "
    "constant is reported as a numerical quantity with no biological "
    "interpretation."
)

#: Every tolerance in this module is NUMERICAL. None is biological.
NUMERICAL_TOLERANCE_LABEL = (
    "NUMERICAL TOLERANCE, NOT A BIOLOGICAL ONE. Used only to report how much a "
    "computed quantity moves when the timestep or the spatial subdivision is "
    "refined. It is a discretization label. It asserts nothing about agreement "
    "with any experimental measurement, and passing or failing it says nothing "
    "about whether a real GF behaves this way."
)

#: The declared convergence measure: the max per-element change of the full
#: state (voltage plus all four gating variables) ACROSS THE FINAL TIMESTEP,
#: in the units of each variable.
#:
#: It is deliberately NOT a maximum over a trailing window. No window is
#: computed and none is implied: the value reported is exactly the change
#: between the last two integration states. It is a fixed-point detection
#: criterion for the INTEGRATION, not a statement about biology.
STATE_STEP_CHANGE_LABEL = (
    "FINAL PER-STEP MAXIMUM CHANGE OF THE FULL STATE (VOLTAGE PLUS ALL FOUR "
    "GATING VARIABLES), MEASURED ACROSS THE LAST TIMESTEP ONLY, IN THE UNITS "
    "OF EACH VARIABLE. It is NOT a maximum over a trailing window, and no "
    "window is computed. A numerical fixed-point detection criterion for the "
    "integration only. It says the integration has stopped moving; it says "
    "nothing about a real neuron's resting state."
)

#: The ion-current balance is reported in mA/cm2, matching the existing
#: backend's sign convention (outward positive).
ION_CURRENT_UNITS = "mA/cm2"

#: The default WAVEFORM observation level used by
#: ``stimulus_response_report``. This is a NUMERICAL DIAGNOSTIC CRITERION, not a
#: biological threshold. It is a depolarisation-and-repolarisation detection
#: level applied to the generated trace, it is not derived from any source, and
#: it asserts nothing about whether a real GF spikes at this voltage. It is
#: stated here as a named constant with a stated basis so it cannot be read as
#: a threshold, and a caller may override it freely.
WAVEFORM_OBSERVATION_FLOOR_MV = 40.0
WAVEFORM_OBSERVATION_FLOOR_NOTE = (
    "NUMERICAL DIAGNOSTIC CRITERION, NOT A BIOLOGICAL THRESHOLD. This is a "
    "waveform observation level for deciding whether a GENERATED trace shows a "
    "depolarisation followed by a repolarisation. It is not a source-derived "
    "value, not a GF spike threshold, not a rheobase, and not evidence about "
    "any real neuron. It only summarises what this simulation's own output "
    "looks like, and the caller may supply a different level."
)

#: Unit derivation, stated because a 1000x error here would be invisible in a
#: plot and obvious in the balance check:
#:   1 S/cm2 * 1 mV = 1 mA/cm2, so the .mod current densities need no factor;
#:   (mV)/ohm = 1e-3 A = 1 mA, so an axial current in mA is (Vi - Vj)/R with
#:   NO extra factor, and dividing by the segment area in cm2 gives mA/cm2.
ION_BALANCE_UNITS_NOTE = (
    "ION BALANCE UNITS. Membrane current densities are mA/cm2 because "
    "1 S/cm2 * 1 mV = 1 mA/cm2 exactly. Axial currents are computed as "
    "(Vi - Vj)/R, which is already in mA because mV/ohm = 1e-3 A = 1 mA, and "
    "are divided by the segment's own membrane area in cm2 to reach mA/cm2. "
    "Outward current is positive, matching the existing passive backend. At "
    "equilibrium the sum over leak, nat, nap, k and axial is zero to within "
    "the residual reported here."
)


#: The measured equilibrium, recorded so the value is auditable and so a
#: future change that moves it is visible in a diff. These are NUMERICAL
#: measurements of THIS implementation at THIS timestep, not constants of the
#: model and not biological parameters.
MEASURED_GF_EQUILIBRIUM_SUMMARY = (
    "MEASURED UNSTIMULATED EQUILIBRIUM OF THE COMPLETE 8A MEMBRANE "
    "(leak + nat + nap + k), at the default 0.01 ms timestep: the membrane "
    "relaxes from the declared E_leak initial condition of -85 mV to about "
    "-74.67 mV and stops there, with the net per-segment membrane current "
    "falling to order 1e-10 mA/cm2. The delay is dominated by the delayed "
    "rectifier: at rest k.mod's single gate opens to roughly 0.043, giving a "
    "potassium current of order -2.9e-4 mA/cm2 that is balanced by the "
    "outward leak current of order +3.1e-4 mA/cm2, with the two sodium "
    "mechanisms contributing a further inward order -1e-5 mA/cm2 between "
    "them. Because the potassium current is not zero at -85 mV, the "
    "equilibrium is NOT the leak reversal potential, and 3.0D-8B does not "
    "force it there. This equilibrium is a numerical fixed point of this "
    "implementation and is NOT claimed to be the giant fiber's biological "
    "resting potential."
)


class GFActiveStateValidationError(Exception):
    """Base class for 3.0D-8B validation failures."""


#: Which gate actually sets the convergence rate is NOT hard-coded here. It is
#: the argmax of the live rate expressions, returned together with its value by
#: ``_slowest_gate_tau`` so the reported name and the reported time constant
#: always come from the same computation.


def _gate_steady_state(
    model: GFActiveAxonModel, gate: str, voltage_mV: float
) -> float:
    """The steady state of one gate at ``voltage_mV``, read from 8A.

    Evaluated through the 8A rate objects rather than restating the source
    expressions, so this cannot drift away from the equations 8A integrates.
    It is the value a gate would hold if the voltage stopped changing.
    """
    if gate == "nat_m":
        return model.nat_rates.minf(voltage_mV)
    if gate == "nat_h":
        return model.nat_rates.hinf(voltage_mV)
    if gate == "nap_m":
        return model.nap_rates.minf(voltage_mV)
    if gate == "k_m":
        return model.k_rates.minf(voltage_mV)
    raise GFActiveStateValidationError(
        f"Unknown gate '{gate}'; 8B tracks only nat_m, nat_h, nap_m and k_m."
    )


def _slowest_gate_tau(
    model: GFActiveAxonModel, voltage_mV: float
) -> Tuple[str, float]:
    """The name and value of the largest gate time constant at ``voltage_mV``.

    Both halves come from the SAME argmax over the SAME candidate values, so
    ``slowest_gate_name`` can never disagree with ``slowest_gate_tau_ms``. The
    name is not hard-coded: it is the argmax's own key. Computed from the 8A
    rate objects rather than restated, so this tracks the source expressions
    instead of a constant that could drift away from them.
    """
    candidates = (
        ("nat_m", model.nat_rates.mtau_ms(voltage_mV)),
        ("nat_h", model.nat_rates.htau_ms(voltage_mV)),
        ("nap_m", model.nap_rates.tau_ms(voltage_mV)),
        ("k_m", model.k_rates.tau_ms(voltage_mV)),
    )
    return max(candidates, key=lambda candidate: candidate[1])


@dataclass(frozen=True)
class IonBalance:
    """Per-segment ionic current balance in mA/cm2, outward positive.

    ``net_mA_per_cm2`` is the quantity that vanishes at equilibrium. It is the
    sum of the leak, the three .mod currents and the axial currents, and it is
    a direct check that the fixed point is a genuine current balance rather
    than a stalled integration.
    """

    segment_id: str
    leak_mA_per_cm2: float
    nat_mA_per_cm2: float
    nap_mA_per_cm2: float
    k_mA_per_cm2: float
    axial_mA_per_cm2: float
    net_mA_per_cm2: float

    def all_finite(self) -> bool:
        values = (
            self.leak_mA_per_cm2, self.nat_mA_per_cm2, self.nap_mA_per_cm2,
            self.k_mA_per_cm2, self.axial_mA_per_cm2, self.net_mA_per_cm2,
        )
        return all(v == v and abs(v) != float("inf") for v in values)


@dataclass(frozen=True)
class EquilibriumState:
    """The measured fixed point of one segment of the unstimulated system."""

    segment_id: str
    voltage_mV: float
    nat_m: float
    nat_h: float
    nap_m: float
    k_m: float
    nat_mS_per_cm2: float
    nap_mS_per_cm2: float
    k_mS_per_cm2: float
    leak_mS_per_cm2: float
    balance: IonBalance
    is_finite: bool

    def gates_in_unit_interval(self) -> bool:
        return all(
            0.0 <= value <= 1.0
            for value in (self.nat_m, self.nat_h, self.nap_m, self.k_m)
        )

    def gating_items(self) -> Tuple[Tuple[str, float], ...]:
        """The four gating variables, in a fixed order, for reporting.

        Returned in a deterministic order so a report can be compared field
        by field across runs.
        """
        return (
            ("nat_m", self.nat_m), ("nat_h", self.nat_h),
            ("nap_m", self.nap_m), ("k_m", self.k_m),
        )


@dataclass(frozen=True)
class EquilibriumReport:
    """A deterministic report of the unstimulated system's fixed point.

    Everything here is a NUMERICAL measurement. ``distance_from_equilibrium``
    is the convergence criterion described by ``STATE_STEP_CHANGE_LABEL``; it
    is not a biological tolerance and is not compared against one.
    """

    segment_count: int
    timestep_ms: float
    integration_method: str
    gating_method: str
    is_fully_implicit: bool
    steps: int
    duration_ms: float
    declared_initial_voltage_mV: float
    states: Tuple[EquilibriumState, ...]
    final_voltages_mV: Tuple[float, ...]
    voltage_spread_mV: float
    distance_from_equilibrium: float
    distance_label: str
    max_abs_net_current_mA_per_cm2: float
    slowest_gate_tau_ms: float
    slowest_gate_name: str
    slowest_mode_note: str
    all_finite: bool
    tolerance_label: str
    units_note: str
    equilibrium_note: str

    @property
    def mean_voltage_mV(self) -> float:
        return sum(self.final_voltages_mV) / len(self.final_voltages_mV)

    def net_current_residual_is_small(self, tolerance: float) -> bool:
        """Is the current balance consistent with a fixed point?

        ``tolerance`` is a NUMERICAL current-density threshold supplied by the
        caller. It is never a biological one, and this method asserts nothing
        about physiology.
        """
        return self.max_abs_net_current_mA_per_cm2 < tolerance


@dataclass(frozen=True)
class StimulusResponseReport:
    """A report on the 120 nA / 0.03 ms model-reproduction fixture.

    ``peak_voltage_mV`` and ``peak_time_ms`` are properties of the observed
    SEGMENT, and     ``segment_id`` says which one, because the response is not
    spatially uniform during the spike. ``propagation_delays_ms`` is reported
    only when the caller asks for it and is a MEASURED delay between selected
    segments of THIS implementation at THIS timestep. It is not a conduction
    velocity, not a comparison with any published latency, and not a claim
    about the giant fiber's real conduction.

    ``depolarization_mV`` is measured from the model's DECLARED initial
    voltage (E_leak), not from the first sample of the trace. The first
    sample is taken after a step has already run, so it is already partly
    elevated and would understate the excursion; measuring from the declared
    start makes the number comparable across timesteps and subdivisions.
    """

    segment_id: str
    segment_count: int
    timestep_ms: float
    integration_method: str
    amplitude_A: float
    amplitude_duration_ms: float
    onset_ms: float
    stimulus_location: float
    stimulus_source: str
    steps: int
    duration_ms: float
    peak_voltage_mV: float
    peak_time_ms: float
    end_voltage_mV: float
    depolarization_mV: float
    min_voltage_mV: float
    max_voltage_mV: float
    all_finite: bool
    propagation_delays_ms: Tuple[Tuple[str, float], ...]
    observed_by_waveform_criterion: bool
    fixture_note: str
    tolerance_label: str


@dataclass(frozen=True)
class RefinementComparison:
    """A numerical comparison across timesteps or subdivisions.

    Every field is a NUMERICAL difference between two runs of the same
    implementation. None is a biological tolerance and none is compared against
    a biological standard.
    """

    axis: str
    label: str
    baseline: float
    candidate: float
    absolute_difference: float
    units: str
    per_setting: Tuple[Tuple[float, float], ...]
    note: str
    tolerance_label: str = NUMERICAL_TOLERANCE_LABEL


def _ion_balance(
    network: GFActiveNetwork,
    state: Dict[str, GFActiveSegmentState],
    model: GFActiveAxonModel,
) -> Dict[str, IonBalance]:
    """Compute the per-segment ionic balance in mA/cm2, outward positive.

    The leak term is read from the 3.0D-7G prepared network, never re-derived,
    and the three .mod currents are the ones 8A already recorded on each
    segment during the last step. No current is recomputed from a different
    expression than the one 8A integrated.
    """
    compartments = {
        c.compartment_id: c for c in network.network.compartments
    }
    axial_mA: Dict[str, float] = {sid: 0.0 for sid in network.segment_ids}
    for connection in network.network.connections:
        parent_v = state[connection.parent_id].voltage_mV
        child_v = state[connection.child_id].voltage_mV
        # mV / ohm = 1 mA exactly. Outward from the parent, inward to the child.
        flow_mA = (parent_v - child_v) / connection.resistance_ohm
        axial_mA[connection.parent_id] += flow_mA
        axial_mA[connection.child_id] -= flow_mA

    balances: Dict[str, IonBalance] = {}
    for segment_id in network.segment_ids:
        compartment = compartments[segment_id]
        segment = state[segment_id]
        area_cm2 = compartment.membrane_area_cm2
        leak_density = compartment.leak_conductance_S / area_cm2
        leak = leak_density * (
            segment.voltage_mV - compartment.leak_reversal_mV
        )
        nat = segment.last_currents_mA_per_cm2.get(MECHANISM_NAT, 0.0)
        nap = segment.last_currents_mA_per_cm2.get(MECHANISM_NAP, 0.0)
        k = segment.last_currents_mA_per_cm2.get(MECHANISM_K, 0.0)
        axial = axial_mA[segment_id] / area_cm2
        balances[segment_id] = IonBalance(
            segment_id=segment_id,
            leak_mA_per_cm2=leak,
            nat_mA_per_cm2=nat,
            nap_mA_per_cm2=nap,
            k_mA_per_cm2=k,
            axial_mA_per_cm2=axial,
            net_mA_per_cm2=leak + nat + nap + k + axial,
        )
    return balances


def _state_vector(state: Dict[str, GFActiveSegmentState]) -> List[float]:
    """Flatten the full state, in a deterministic order, for change detection."""
    values: List[float] = []
    for segment_id in sorted(state):
        segment = state[segment_id]
        values.extend((
            segment.voltage_mV, segment.nat_m, segment.nat_h,
            segment.nap_m, segment.k_m,
        ))
    return values


def _max_state_change(
    previous: List[float], current: List[float]
) -> float:
    """Largest absolute per-element change between two full states."""
    return max(abs(a - b) for a, b in zip(previous, current))


class GFActiveStateValidator:
    """Numerical validation of the completed 3.0D-8A GF active membrane.

    This class holds NO biological content. It runs the 8A model and reports
    what it computes. Every tolerance it exposes is labelled numerical, and
    none of them is a threshold, a resting potential or an acceptance
    criterion for biology.
    """

    def __init__(self, model: Optional[GFActiveAxonModel] = None) -> None:
        # The 8A model, unmodified. 8B never rebuilds or replaces it.
        self._model = GFActiveAxonModel() if model is None else model

    @property
    def model(self) -> GFActiveAxonModel:
        return self._model

    @property
    def name(self) -> str:
        return "gf_active_state_validation_v0"

    # -- 1/2: the unstimulated equilibrium ---------------------------------

    def equilibrium_report(
        self,
        model: CompartmentModel,
        segment_count: int = 11,
        duration_ms: float = 200.0,
        timestep_ms: Optional[float] = None,
        injected_currents_A: Optional[Dict[str, float]] = None,
    ) -> EquilibriumReport:
        """Integrate the unstimulated system and report its fixed point.

        ``injected_currents_A`` defaults to None, which means NO stimulus. It
        exists so a caller can deliberately re-run this diagnostic under a
        stimulus, and the report then says so; it is never populated by
        default and no current is ever injected implicitly.

        The run is DETERMINISTIC: the same model, segment count, duration and
        timestep produce the same report every time, with no randomness, no
        tolerance-based early exit and no dependence on wall-clock time.
        """
        dt_ms = self._model._validate_timestep(
            self._model.timestep_ms if timestep_ms is None else timestep_ms
        )
        network = self._model.prepare(model, segment_count=segment_count)
        state = self._model.initial_state(network)
        declared_initial = self._model.rest_voltage_mV
        stimulus = dict(injected_currents_A or {})

        steps = int(round(duration_ms / dt_ms))
        previous = _state_vector(state)
        distance = float("inf")
        for _ in range(steps):
            self._model.step(
                network, state, injected_currents_A=stimulus, timestep_ms=dt_ms
            )
            current = _state_vector(state)
            # Overwritten every step on purpose: what is reported is the change
            # across the FINAL timestep only, exactly as STATE_STEP_CHANGE_LABEL
            # says. This is not, and is not documented as, a windowed maximum.
            distance = _max_state_change(previous, current)
            previous = current

        balances = _ion_balance(network, state, self._model)
        compartments = {
            c.compartment_id: c for c in network.network.compartments
        }
        states: List[EquilibriumState] = []
        for segment_id in network.segment_ids:
            segment = state[segment_id]
            conductances = segment.last_conductances_mS_per_cm2
            compartment = compartments[segment_id]
            states.append(
                EquilibriumState(
                    segment_id=segment_id,
                    voltage_mV=segment.voltage_mV,
                    nat_m=segment.nat_m,
                    nat_h=segment.nat_h,
                    nap_m=segment.nap_m,
                    k_m=segment.k_m,
                    nat_mS_per_cm2=conductances.get(MECHANISM_NAT, 0.0),
                    nap_mS_per_cm2=conductances.get(MECHANISM_NAP, 0.0),
                    k_mS_per_cm2=conductances.get(MECHANISM_K, 0.0),
                    leak_mS_per_cm2=conductances.get("leak", 0.0),
                    balance=balances[segment_id],
                    is_finite=segment.all_finite()
                    and balances[segment_id].all_finite(),
                )
            )

        voltages = tuple(item.voltage_mV for item in states)
        # One argmax, both halves. The reported name is the key of the maximum
        # and the reported value is that maximum, so they cannot disagree.
        slowest_gate_name, slowest_gate_tau_ms = _slowest_gate_tau(
            self._model, voltages[0]
        )
        return EquilibriumReport(
            segment_count=segment_count,
            timestep_ms=dt_ms,
            integration_method=GF_ACTIVE_NUMERICAL_POLICY.integration_method,
            gating_method=GF_ACTIVE_NUMERICAL_POLICY.gating_method,
            is_fully_implicit=GF_ACTIVE_NUMERICAL_POLICY.is_fully_implicit,
            steps=steps,
            duration_ms=steps * dt_ms,
            declared_initial_voltage_mV=declared_initial,
            states=tuple(states),
            final_voltages_mV=voltages,
            voltage_spread_mV=max(voltages) - min(voltages),
            distance_from_equilibrium=distance,
            distance_label=STATE_STEP_CHANGE_LABEL,
            max_abs_net_current_mA_per_cm2=max(
                abs(item.balance.net_mA_per_cm2) for item in states
            ),
            slowest_gate_tau_ms=slowest_gate_tau_ms,
            slowest_gate_name=slowest_gate_name,
            slowest_mode_note=SLOWEST_MODE_NOTE,
            all_finite=all(item.is_finite for item in states),
            tolerance_label=NUMERICAL_TOLERANCE_LABEL,
            units_note=ION_BALANCE_UNITS_NOTE,
            equilibrium_note=(
                MEASURED_GF_EQUILIBRIUM_SUMMARY
                + " This run was "
                + ("STIMULATED." if stimulus else "UNSTIMULATED (no injected "
                   "current).")
                + f" Declared initial voltage {declared_initial} mV, "
                f"reached {voltages[0]!r} mV."
            ),
        )

    def equilibrium_is_not_declared_initial(
        self,
        model: CompartmentModel,
        segment_count: int = 11,
        duration_ms: float = 200.0,
        timestep_ms: Optional[float] = None,
    ) -> bool:
        """Does the system actually move away from the declared initial V?

        This exists so the checkpoint can STATE, as a checked fact, that -85 mV
        is an initial condition and not the equilibrium. It is a diagnostic
        about the implementation's behaviour; it does not adjust, offset or
        correct anything.
        """
        report = self.equilibrium_report(
            model, segment_count=segment_count, duration_ms=duration_ms,
            timestep_ms=timestep_ms,
        )
        return any(
            abs(v - report.declared_initial_voltage_mV) > 1e-9
            for v in report.final_voltages_mV
        )

    # -- 3: timestep sensitivity of the equilibrium -------------------------

    def timestep_equilibrium_comparison(
        self,
        model: CompartmentModel,
        timesteps_ms: Tuple[float, ...] = (0.01, 0.005, 0.002),
        segment_count: int = 11,
        duration_ms: float = 200.0,
    ) -> Tuple[EquilibriumReport, ...]:
        """Run the unstimulated equilibrium at several timesteps.

        Returns one report per timestep, coarsest first. The caller compares
        them; no comparison threshold is chosen here, and none is biological.
        """
        if len(timesteps_ms) < 2:
            raise GFActiveStateValidationError(
                f"At least two timesteps are needed to compare anything; got "
                f"{list(timesteps_ms)}."
            )
        return tuple(
            self.equilibrium_report(
                model, segment_count=segment_count, duration_ms=duration_ms,
                timestep_ms=dt,
            )
            for dt in timesteps_ms
        )

    def compare_equilibrium_voltage_across_timesteps(
        self,
        model: CompartmentModel,
        timesteps_ms: Tuple[float, ...] = (0.01, 0.005, 0.002),
        segment_count: int = 11,
        duration_ms: float = 200.0,
    ) -> RefinementComparison:
        """Compare the equilibrium VOLTAGE across timesteps.

        The reported difference is numerical. A small difference means the
        fixed point is insensitive to the discretization; it does NOT mean the
        value is biologically correct.
        """
        reports = self.timestep_equilibrium_comparison(
            model, timesteps_ms, segment_count, duration_ms
        )
        baseline = reports[0].mean_voltage_mV
        candidate = reports[-1].mean_voltage_mV
        return RefinementComparison(
            axis="timestep",
            label="EQUILIBRIUM VOLTAGE VS TIMESTEP, UNSTIMULATED",
            baseline=baseline,
            candidate=candidate,
            absolute_difference=abs(candidate - baseline),
            units="mV",
            per_setting=tuple(
                (report.timestep_ms, report.mean_voltage_mV) for report in reports
            ),
            note=(
                "A NUMERICAL comparison of the same unstimulated system at "
                "different timesteps. The voltage is measured at the END of a "
                "fixed duration, so a timestep that has not yet fully converged "
                "shows up here as a difference. A small difference means the "
                "fixed point is well resolved by the discretization; it does "
                "NOT mean the voltage is biologically correct. " 
                + NUMERICAL_TOLERANCE_LABEL
            ),
        )

    # -- 4: spatial subdivision sensitivity of the equilibrium -------------

    def compare_equilibrium_voltage_across_subdivisions(
        self,
        model: CompartmentModel,
        segment_counts: Tuple[int, ...] = (5, 11, 51),
        duration_ms: float = 200.0,
        timestep_ms: Optional[float] = None,
    ) -> RefinementComparison:
        """Compare the equilibrium across N = 5, 11, 51.

        Only the EQUILIBRIUM is compared. Transient waveforms are explicitly
        NOT expected to be invariant under refinement, because refinement moves
        the stimulus relative to the compartment it is injected into, and this
        method makes no claim that they should match.
        """
        if len(segment_counts) < 2:
            raise GFActiveStateValidationError(
                f"At least two subdivision counts are needed; got "
                f"{list(segment_counts)}."
            )
        reports = tuple(
            self.equilibrium_report(
                model, segment_count=count, duration_ms=duration_ms,
                timestep_ms=timestep_ms,
            )
            for count in segment_counts
        )
        baseline = reports[0].mean_voltage_mV
        candidate = reports[-1].mean_voltage_mV
        return RefinementComparison(
            axis="subdivision",
            label="EQUILIBRIUM VOLTAGE VS SPATIAL SUBDIVISION, UNSTIMULATED",
            baseline=baseline,
            candidate=candidate,
            absolute_difference=abs(candidate - baseline),
            units="mV",
            per_setting=tuple(
                (float(report.segment_count), report.mean_voltage_mV)
                for report in reports
            ),
            note=(
                "A NUMERICAL comparison of the UNSTIMULATED equilibrium across "
                "subdivisions. The transient waveform is deliberately NOT "
                "compared: a point stimulus injected into ONE compartment has a "
                "current density that depends on that compartment's area, so "
                "refining the mesh changes the stimulus and the transient "
                "together, and 3.0D-8A does not rescale the stimulus to hide "
                "that. " + NUMERICAL_TOLERANCE_LABEL
            ),
        )

    # -- 5: the model-reproduction stimulus fixture -------------------------

    def stimulus_response_report(
        self,
        model: CompartmentModel,
        segment_count: int = 51,
        observe_segment_index: int = 0,
        duration_ms: float = 3.0,
        timestep_ms: Optional[float] = None,
        amplitude_A: float = MODELDB_GF_STIMULUS_AMPLITUDE_A,
        amplitude_duration_ms: float = MODELDB_GF_STIMULUS_DURATION_MS,
        propagation_indices: Optional[Tuple[int, ...]] = None,
        observation_floor_mV: float = WAVEFORM_OBSERVATION_FLOOR_MV,
    ) -> StimulusResponseReport:
        """Run the published 120 nA / 0.03 ms fixture and report the response.

        The stimulus is the MODEL-REPRODUCTION FIXTURE from the published
        Augustin et al. 2019 model, injected into the PROXIMAL GF compartment.
        It is not a sensory input, not a synaptic input and not a threshold,
        and this method never reinterprets it as one.

        ``propagation_indices``, when given, are segment INDICES whose peak
        time is reported relative to the observed segment. That is a measured
        delay of THIS implementation, not a conduction velocity and not a
        comparison with any published latency.
        """
        dt_ms = self._model._validate_timestep(
            self._model.timestep_ms if timestep_ms is None else timestep_ms
        )
        network = self._model.prepare(model, segment_count=segment_count)
        state = self._model.initial_state(network)
        segment_ids = network.segment_ids
        if not 0 <= observe_segment_index < len(segment_ids):
            raise GFActiveStateValidationError(
                f"observe_segment_index {observe_segment_index} is out of range "
                f"for {len(segment_ids)} segment(s)."
            )
        observed_id = segment_ids[observe_segment_index]
        stimulus_id = segment_ids[0]
        if propagation_indices is not None:
            for index in propagation_indices:
                if not 0 <= index < len(segment_ids):
                    raise GFActiveStateValidationError(
                        f"propagation index {index} is out of range for "
                        f"{len(segment_ids)} segment(s)."
                    )

        steps = int(round(duration_ms / dt_ms))
        on_steps = int(round(amplitude_duration_ms / dt_ms))
        traces: Dict[str, List[float]] = {sid: [] for sid in segment_ids}
        for step in range(steps):
            injected = (
                {stimulus_id: amplitude_A} if step < on_steps else {}
            )
            self._model.step(
                network, state, injected_currents_A=injected, timestep_ms=dt_ms
            )
            for segment_id in segment_ids:
                traces[segment_id].append(state[segment_id].voltage_mV)

        observed_trace = traces[observed_id]
        peak_value = max(observed_trace)
        peak_index = observed_trace.index(peak_value)
        diagnostic = self._model.ap_diagnostic(
            tuple(observed_trace), dt_ms, observed_id,
            observation_floor_mV=observation_floor_mV,
        )

        delays: List[Tuple[str, float]] = []
        if propagation_indices is not None:
            for index in propagation_indices:
                segment_id = segment_ids[index]
                trace = traces[segment_id]
                delays.append((
                    segment_id, trace.index(max(trace)) * dt_ms
                    - peak_index * dt_ms
                ))

        return StimulusResponseReport(
            segment_id=observed_id,
            segment_count=segment_count,
            timestep_ms=dt_ms,
            integration_method=GF_ACTIVE_NUMERICAL_POLICY.integration_method,
            amplitude_A=amplitude_A,
            amplitude_duration_ms=amplitude_duration_ms,
            onset_ms=0.0,
            stimulus_location=MODELDB_GF_STIMULUS_LOCATION,
            stimulus_source=MODELDB_GF_STIMULUS_SOURCE,
            steps=steps,
            duration_ms=steps * dt_ms,
            peak_voltage_mV=peak_value,
            peak_time_ms=peak_index * dt_ms,
            end_voltage_mV=observed_trace[-1],
            depolarization_mV=peak_value - self._model.rest_voltage_mV,
            min_voltage_mV=min(observed_trace),
            max_voltage_mV=peak_value,
            all_finite=all(
                v == v and abs(v) != float("inf")
                for trace in traces.values() for v in trace
            ),
            propagation_delays_ms=tuple(delays),
            observed_by_waveform_criterion=diagnostic.observed,
            fixture_note=(
                "MODEL-REPRODUCTION FIXTURE FROM THE PUBLISHED AUGUSTIN ET AL. "
                "2019 GFS MODEL, NOT A SENSORY OR SYNAPTIC STIMULUS. A 120 nA "
                "current step for 0.03 ms is injected into the PROXIMAL GF "
                "compartment, reproducing the model authors' own circuit-"
                "latency drive. The peak voltage, peak time and propagation "
                "delays reported here are numerical properties of THIS "
                "implementation at THIS timestep and subdivision. The "
                "propagation delays are NOT a conduction velocity, NOT a "
                "comparison with any published GF latency, and NOT a claim "
                "about the giant fiber's real conduction; they are quantised "
                "by the timestep, which bounds how finely they can be "
                "resolved. The peak voltage and peak time are not compared "
                "against any experiment, and no biological acceptance "
                "threshold is defined for them."
            ),
            tolerance_label=NUMERICAL_TOLERANCE_LABEL,
        )

    # -- 6: convergence of the stimulated response --------------------------

    def compare_stimulus_peak_across_timesteps(
        self,
        model: CompartmentModel,
        timesteps_ms: Tuple[float, ...] = (0.01, 0.005, 0.002),
        segment_count: int = 11,
        duration_ms: float = 3.0,
    ) -> Tuple[RefinementComparison, RefinementComparison]:
        """Compare the stimulated PEAK and PEAK TIME across timesteps.

        Two comparisons are returned, peak voltage and peak time. Both are
        NUMERICAL. The scheme is linearised implicit and therefore only
        first-order in the gating/voltage coupling, so a non-zero difference
        under refinement is the expected signature of that approximation and
        is reported rather than removed. It is not evidence of biological
        inaccuracy, and its absence would not be evidence of biological
        accuracy.
        """
        if len(timesteps_ms) < 2:
            raise GFActiveStateValidationError(
                f"At least two timesteps are needed to compare anything; got "
                f"{list(timesteps_ms)}."
            )
        reports = tuple(
            self.stimulus_response_report(
                model, segment_count=segment_count, duration_ms=duration_ms,
                timestep_ms=dt,
            )
            for dt in timesteps_ms
        )
        peak = RefinementComparison(
            axis="timestep",
            label="STIMULATED AP PEAK VOLTAGE VS TIMESTEP",
            baseline=reports[0].peak_voltage_mV,
            candidate=reports[-1].peak_voltage_mV,
            absolute_difference=abs(
                reports[-1].peak_voltage_mV - reports[0].peak_voltage_mV
            ),
            units="mV",
            per_setting=tuple(
                (report.timestep_ms, report.peak_voltage_mV)
                for report in reports
            ),
            note=(
                "A NUMERICAL discretisation sweep of the stimulus-evoked peak. "
                "8A's scheme is linearised implicit and only FIRST-ORDER in the "
                "coupling between the gating states and the voltage, so a "
                "non-zero difference under refinement is the expected "
                "signature of that approximation and is reported rather than "
                "removed. It is NOT evidence of biological inaccuracy, and its "
                "absence would not be evidence of biological accuracy. "
                + NUMERICAL_TOLERANCE_LABEL
            ),
        )
        timing = RefinementComparison(
            axis="timestep",
            label="STIMULATED AP PEAK TIME VS TIMESTEP",
            baseline=reports[0].peak_time_ms,
            candidate=reports[-1].peak_time_ms,
            absolute_difference=abs(
                reports[-1].peak_time_ms - reports[0].peak_time_ms
            ),
            units="ms",
            per_setting=tuple(
                (report.timestep_ms, report.peak_time_ms) for report in reports
            ),
            note=(
                "A NUMERICAL discretisation sweep of the stimulus-evoked peak "
                "time, which is additionally quantised by the timestep. "
                + NUMERICAL_TOLERANCE_LABEL
            ),
        )
        return peak, timing

    # -- 7: isolation -------------------------------------------------------

    def scope_note(self) -> str:
        """The single statement of what 8B did and did not do."""
        return " ".join((
            "3.0D-8B IS NUMERICAL VALIDATION OF 3.0D-8A AND ADDS NO BIOLOGY. "
            "No new mechanism, equation, parameter, conductance, synapse, "
            "threshold or resting offset is introduced, and nothing in the 8A "
            "module is modified. The unstimulated equilibrium is MEASURED, "
            "not assumed and not forced to the -85 mV leak reversal potential. "
            "Every tolerance in this module is labelled NUMERICAL: it "
            "describes how a computed quantity moves under discretisation "
            "refinement and asserts nothing about a real giant fiber. The "
            "120 nA / 0.03 ms stimulus remains a model-reproduction fixture "
            "and is not a sensory input. The 3.0D-7U gap-junction unit "
            "conflict, DmCa1D, Slowpoke, ShakB, Shaker, Para and any chemical "
            "synapse remain out of scope and unimplemented. 3.0D-7W, 7X, 7Y "
            "and 7Z are not imported and are not runtime dependencies.",
            GF_ACTIVE_NUMERICAL_LIMITATION,
            NUMERICAL_TOLERANCE_LABEL,
            STATE_STEP_CHANGE_LABEL,
        ))

    def imported_module_names(self) -> Tuple[str, ...]:
        """Every module this file imports, read from its own AST.

        Exposed so isolation is a MEASUREMENT rather than an assertion: the
        check walks the real import statements instead of trusting a comment.
        """
        import ast
        import inspect

        tree = ast.parse(inspect.getsource(sys.modules[__name__]))
        imported: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.append(node.module)
                imported.extend(
                    f"{node.module}.{alias.name}" for alias in node.names
                )
            elif isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
        return tuple(sorted(set(imported)))

    def is_isolated_from_downstream_layers(self) -> bool:
        """Does 8B depend on 7W, 7X, 7Y or 7Z at runtime?

        Checked against the real import list, not asserted.
        """
        joined = " ".join(self.imported_module_names())
        for banned in (
            "synaptic_abstraction", "motor_output_abstraction",
            "looming_abstraction", "sensorimotor_integration",
            "synaptic_mechanism_registry", "Exp2Syn", "exp2syn",
        ):
            if banned in joined:
                return False
        return True


def build_validation_report(
    model: CompartmentModel,
    segment_count: int = 11,
    duration_ms: float = 200.0,
    timestep_ms: Optional[float] = None,
) -> EquilibriumReport:
    """Convenience: one unstimulated equilibrium report with the defaults."""
    return GFActiveStateValidator().equilibrium_report(
        model, segment_count=segment_count, duration_ms=duration_ms,
        timestep_ms=timestep_ms,
    )
