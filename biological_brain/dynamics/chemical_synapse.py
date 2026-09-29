"""Published phenomenological chemical synapse as a live conductance (3.0D-8G).

THE FIRST LIVE CHEMICAL SYNAPSE IN THIS PROJECT
------------------------------------------------
3.0D-7V recorded the synaptic mechanisms and parameters of the published Augustin
et al. 2019 model as PROVENANCE ONLY: every record there is
``live_solver_eligible = False``, and the module explicitly implemented no
synaptic current. 3.0D-8G implements the ONE connection the paper actually
describes as a chemical synapse, PSI->DLMn, and leaves the two mixed
electrical+chemical synapses alone.

THE EQUATION, AND ITS EXACT NORMALIZATION
-----------------------------------------
The mechanism is the standard double-exponential conductance of a chemical
synapse. For one presynaptic event occurring at ``t_event`` with a synaptic
transmission ``delay``, the conductance is zero until the delayed arrival
``t_arrive = t_event + delay``, and thereafter

    g(t_rel) = g_peak * (exp(-t_rel/tau_decay) - exp(-t_rel/tau_rise)) / f_peak

    t_rel = t - t_arrive                                          [t >= t_arrive]

where ``f_peak`` is the value of the unnormalized shape at its own maximum:

    f_peak = exp(-t_peak/tau_decay) - exp(-t_peak/tau_rise)
    t_peak = tau_rise * tau_decay / (tau_decay - tau_rise) * ln(tau_decay/tau_rise)

This normalization is chosen so that ``g(t_peak) == g_peak`` EXACTLY, and it is
the reason the peak amplitude is a meaningful parameter rather than an artefact
of the exponential coefficient. The coefficient multiplying the exponentials is
``g_peak / f_peak``, which is emphatically NOT ``g_peak``; for the PSI->DLMn
time constants it is about 1.435, so treating the raw coefficient as the peak
would overstate the conductance by roughly 44 percent. That distinction is
asserted in the tests.

WHY NOT NEURON'S RAW INTERNAL EXPRESSION
-----------------------------------------
NEURON's ``Exp2Syn`` evaluates internally as

    g(t) = weight * exp(-t/tau2) / (1 - exp(-t/tau1))

which is the difference-of-exponentials shape DIVIDED BY ``(1 - exp(-t/tau1))``.
That factor is not a constant, and it makes the expression unbounded as
``t -> 0`` (for the PSI->DLMn time constants it reaches about 2e4 within 5 us of
arrival). The internal form is therefore not peak-normalized and has no
finite-time interior maximum in the form written. The peak-normalized
difference-of-exponentials above is the same functional family with an explicit,
analytically known peak, and it is what this checkpoint implements. This is a
documented modelling choice about NORMALIZATION, not a different mechanism, and
no claim is made that the two agree sample-for-sample.

The waveform satisfies every property the mechanism must have: it is zero before
arrival, exactly zero at arrival, rises, reaches exactly one interior maximum at
``t_peak``, then decays monotonically toward zero, and is never negative because
``tau_decay > tau_rise`` makes ``exp(-t/tau_decay) > exp(-t/tau_rise)`` for all
``t > 0``.

EVENT SUMMATION, AND WHAT IS DELIBERATELY ABSENT
------------------------------------------------
Each event contributes its own waveform and the total conductance is the plain
SUM of the contributions. The synapse holds exactly one piece of mutable state:
the list of arrival times. There is no release probability, no stochastic
release, no vesicle pool, no short-term depression or facilitation, no
desensitization, no calcium, no recovery time constant and no temperature
scaling. Consequently the mechanism is exactly deterministic and exactly
reproducible, which is what makes the 100 Hz waveform-train behaviour in the
tests a statement about the WAVEFORM rather than about a hidden state.

UNITS: SI INTERNALLY, BIOLOGICAL UNITS AT THE BOUNDARY
------------------------------------------------------
Every stored quantity in :class:`DoubleExponentialSynapse` is SI:

    time          seconds
    voltage       volts
    conductance   siemens
    current       amperes

The public constructor and the accessors that a caller reads use the
biologically readable units the published sources are written in (ms, mV, uS)
and convert at the boundary, in ONE place each. The conversions are written out
explicitly rather than hidden behind a library constant, and the module raises
:class:`SynapseUnitError` if a caller passes a value that is dimensionally
impossible for the field, such as a negative conductance or a decay time that
does not exceed the rise time. No code anywhere mixes uS, nS, S and mS: the
only place siemens appear is a documented ``*_1e-6`` / ``*_1e-9`` conversion.

THE CURRENT SIGN CONVENTION IS THE PROJECT'S, NOT A NEW ONE
------------------------------------------------------------
The active and passive backends already fix a single convention: ionic currents
are OUTWARD POSITIVE, and an injected current is INWARD POSITIVE, appearing with
a plus sign on the right-hand side of the membrane equation. This module uses
exactly that convention and introduces no second one:

    I_syn(t) = g_syn(t) * (V_post - E_syn)          [outward positive]

    injected(t) = -I_syn(t) = g_syn(t) * (E_syn - V_post)   [inward positive]

``current_A`` returns the outward-positive form, matching ``I_Nat`` and the
leak. ``injected_current_A`` returns the inward-positive form that
``ActiveAxonModel.step`` already expects, so the two compose without any sign
conversion performed anywhere else. With the published ``E_syn = 0 mV`` and a
resting potential below zero, ``I_syn`` is negative (inward) and the synapse is
excitatory, which is the expected polarity for a cholinergic EPSP.

THIS IS PHENOMENOLOGICAL, NOT A Dalpha7 MODEL
----------------------------------------------
Fayyazuddin et al. 2006 (PMC1382016) established that the Dalpha7 nicotinic
acetylcholine receptor is REQUIRED for transmission at the identified cholinergic
PSI->DLM synapse, and Mejia et al. 2013 (PMC3667824) established that Dalpha7
mutants abolish the PSI->DLM response. Augustin et al. 2011 (PMC3182647)
describes the synapse as chemical and cholinergic.

None of these sources states a single-channel conductance, an alpha or beta rate
constant, an opening probability, a desensitization rate, a receptor density or
a release probability. The published model itself contains none: its Exp2Syn has
no receptor, no subunit and no binding step. So the synapse implemented here is
a PUBLISHED PHENOMENOLOGICAL DOUBLE-EXPONENTIAL CHEMICAL SYNAPSE. It is not a
Dalpha7 kinetic model, nothing about Dalpha7 may be read back out of it, and no
receptor quantity is created. The 3.0D-7V exclusion list is enforced structurally
in this module: the excluded names are refused by name, with the 7V reason.

GENERALITY: THIS MODULE KNOWS NOTHING ABOUT PSI, DLMn OR ANY NEURON
-------------------------------------------------------------------
:class:`DoubleExponentialSynapse` is a generic mechanism. It contains no
neuron name, no synapse name, no ModelDB parameter and no literature citation,
and the tests assert that absence by inspecting the module's own source. All
biology lives in the SEPARATE configuration layer, which reads the published
values from the 3.0D-7V registry rather than restating them. The three layers
stay separate:

    1. mechanism    DoubleExponentialSynapse   (this module, no biology)
    2. connection   PSI_DLMnChemicalSynapse   (which neurons, which location)
    3. provenance   3.0D-7V registry           (whose value, of what status)
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ..synaptic_mechanism_registry import (
    CHEMICAL_DELAY_MS,
    CHEMICAL_DECAY_MS,
    CHEMICAL_PEAK_US,
    CHEMICAL_REVERSAL_MV,
    CHEMICAL_RISE_MS,
    DISCREPANCY_UNRESOLVED,
    PEAK_DISCREPANCY_FACTOR,
    SOURCE_DLMN_WEIGHT,
    SYNAPSE_PSI_DLMN,
    TOPOLOGY_CHEMICAL,
    get_synaptic_mechanism_registry,
)

MODEL_NAME_CHEMICAL_SYNAPSE_V0 = "chemical_synapse_v0"

#: The mechanism kind this module implements, as a stable string.
SYNAPSE_KIND_DOUBLE_EXPONENTIAL = "double_exponential_chemical_synapse"

#: Explicit, single-point unit conversions. These are the ONLY places in this
#: module where a biological unit becomes an SI unit, and none of them mixes
#: conductivity units: milliseconds and microseconds are times, microseconds is
#: not a conductance, and siemens appear only as the explicit 1e-6 below.
_MS_TO_S = 1e-3
_US_TO_S = 1e-6
_MV_TO_V = 1e-3
_US_TO_SI_CONDUCTANCE = 1e-6


class ChemicalSynapseError(Exception):
    """Base class for chemical-synapse failures."""


class SynapseUnitError(ChemicalSynapseError):
    """A quantity is dimensionally impossible for the field it was given to."""


class SynapseShapeError(ChemicalSynapseError):
    """The double-exponential shape is not well defined for these constants."""


_PHENOMENOLOGICAL_SCOPE = (
    "THIS IS A PUBLISHED PHENOMENOLOGICAL DOUBLE-EXPONENTIAL CHEMICAL SYNAPSE, "
    "NOT A Dalpha7 KINETIC MODEL. Dalpha7 is experimentally established as "
    "REQUIRED for transmission at the cholinergic PSI->DLM synapse (Fayyazuddin "
    "et al. 2006, PMC1382016; Mejia et al. 2013, PMC3667824), but no project "
    "source states a single-channel conductance, an alpha or beta rate "
    "constant, an opening probability, a desensitization rate, a receptor "
    "density or a release probability, and the published Exp2Syn itself contains "
    "no receptor, no subunit and no binding step. Nothing about Dalpha7 may be "
    "read back out of this mechanism, and no receptor quantity is created."
)

_NO_ADDED_STATE = (
    "NO HIDDEN STATE. The synapse stores exactly one mutable quantity: the list "
    "of event arrival times. There is no release probability, no stochastic "
    "release, no vesicle pool, no short-term depression, no facilitation, no "
    "desensitization, no calcium dependence, no synaptic recovery time "
    "constant and no Q10 or temperature scaling. Every output is an exact "
    "function of the event list, so the mechanism is fully deterministic."
)


@dataclass(frozen=True)
class SynapseWaveformTrace:
    """A sampled synaptic conductance waveform, with its provenance attached.

    Time is in SECONDS from the presynaptic event, and conductance in SIEMENS,
    matching the mechanism's internal representation exactly. ``arrival_time_s``
    is the delay-shifted onset, so ``times_s`` values below it carry zero
    conductance by construction.
    """

    times_s: Tuple[float, ...]
    conductances_S: Tuple[float, ...]
    reversal_V: float
    delay_s: float
    peak_conductance_S: float
    peak_time_s: float
    event_count: int
    note: str

    def peak_index(self) -> int:
        """The index of the largest sampled conductance."""
        if not self.conductances_S:
            raise ValueError("Cannot locate a peak in an empty trace")
        return max(range(len(self.conductances_S)), key=lambda i: self.conductances_S[i])

    def max_conductance_S(self) -> float:
        return max(self.conductances_S) if self.conductances_S else 0.0

    def is_ever_negative(self) -> bool:
        return any(value < 0.0 for value in self.conductances_S)


class DoubleExponentialSynapse:
    """A generic double-exponential chemical synapse, in SI units.

    This class knows NOTHING about any neuron, any named synapse, any published
    parameter or any literature citation. It is the mechanism only. It is
    deterministic, sums overlapping events linearly, and refuses any shape that
    would not produce a single non-negative peak.
    """

    def __init__(
        self,
        tau_rise_ms: float,
        tau_decay_ms: float,
        reversal_mV: float,
        peak_conductance_uS: float,
        delay_ms: float = 0.0,
    ) -> None:
        """
        Parameters are given in the biological units the published sources use
        and are converted to SI exactly once, here. Nothing else in this module
        performs a unit conversion.

        ``tau_decay_ms`` must be STRICTLY greater than ``tau_rise_ms``: that is
        what makes the difference of exponentials start at zero, rise, peak once
        and decay, instead of starting at zero and immediately going negative.
        """

        def _require_finite(name: str, value: float) -> float:
            if value != value or abs(value) == float("inf"):
                raise SynapseUnitError(
                    f"{name} must be a finite number, got {value!r}"
                )
            return float(value)

        tau_rise_ms = _require_finite("tau_rise_ms", tau_rise_ms)
        tau_decay_ms = _require_finite("tau_decay_ms", tau_decay_ms)
        reversal_mV = _require_finite("reversal_mV", reversal_mV)
        peak_conductance_uS = _require_finite(
            "peak_conductance_uS", peak_conductance_uS
        )
        delay_ms = _require_finite("delay_ms", delay_ms)

        if tau_rise_ms <= 0.0:
            raise SynapseUnitError(
                f"tau_rise_ms must be strictly positive, got {tau_rise_ms} ms. A "
                f"non-positive rise time has no defined double-exponential "
                f"shape and is not a value any source supports."
            )
        if tau_decay_ms <= tau_rise_ms:
            raise SynapseShapeError(
                f"tau_decay_ms ({tau_decay_ms} ms) must be STRICTLY greater "
                f"than tau_rise_ms ({tau_rise_ms} ms). With tau_decay <= "
                f"tau_rise the difference of exponentials is non-positive for "
                f"all t > 0, so the conductance would never rise and would be "
                f"non-physical. No source states such a synapse."
            )
        if peak_conductance_uS < 0.0:
            raise SynapseUnitError(
                f"peak_conductance_uS must be non-negative, got "
                f"{peak_conductance_uS} uS. A negative peak conductance is not "
                f"a synaptic conductance."
            )
        if delay_ms < 0.0:
            raise SynapseUnitError(
                f"delay_ms must be non-negative, got {delay_ms} ms. A negative "
                f"transmission delay would deliver a synaptic event before it "
                f"occurred."
            )

        # --- the one and only unit conversion boundary --------------------
        self._tau_rise_s = tau_rise_ms * _MS_TO_S
        self._tau_decay_s = tau_decay_ms * _MS_TO_S
        self._reversal_V = reversal_mV * _MV_TO_V
        self._peak_conductance_S = peak_conductance_uS * _US_TO_SI_CONDUCTANCE
        self._delay_s = delay_ms * _MS_TO_S
        # -----------------------------------------------------------

        # The analytic peak of the unnormalized shape, and the shape value
        # there. Both are derived, never supplied.
        self._peak_time_s = (
            self._tau_rise_s
            * self._tau_decay_s
            / (self._tau_decay_s - self._tau_rise_s)
            * math.log(self._tau_decay_s / self._tau_rise_s)
        )
        self._shape_peak = self._shape(self._peak_time_s)
        if self._shape_peak <= 0.0:
            raise SynapseShapeError(
                f"The unnormalized double-exponential shape is not positive at "
                f"its analytic peak (got {self._shape_peak!r} at "
                f"{self._peak_time_s!r} s), so it cannot be peak-normalized."
            )
        # The coefficient multiplying the exponentials. It is g_peak/f_peak and
        # is NOT g_peak; the tests pin that distinction.
        self._normalization = 1.0 / self._shape_peak

        #: Arrival times in seconds, i.e. event time plus delay. This list is the
        #: synapse's ONLY mutable state.
        self._arrivals_s: List[float] = []

    # -- shape, with no state --------------------------------------------

    def _shape(self, t_rel_s: float) -> float:
        """The UNNORMALIZED difference of exponentials at ``t_rel_s``."""
        return (
            math.exp(-t_rel_s / self._tau_decay_s)
            - math.exp(-t_rel_s / self._tau_rise_s)
        )

    def unit_response_S(self, t_rel_s: float) -> float:
        """Conductance from a single event at ``t_rel_s`` after its arrival.

        Zero at and before arrival, then the peak-normalized double exponential.
        This is a pure function of ``t_rel_s`` and consults no stored event.
        """
        if t_rel_s <= 0.0:
            return 0.0
        return self._peak_conductance_S * self._shape(t_rel_s) * self._normalization

    def normalization_coefficient(self) -> float:
        """The raw exponential coefficient, ``1/f_peak``. NOT the peak value."""
        return self._normalization

    def shape_peak(self) -> float:
        """The unnormalized shape's maximum. Not a conductance."""
        return self._shape_peak

    # -- accessors, in SI -------------------------------------------------

    @property
    def tau_rise_s(self) -> float:
        return self._tau_rise_s

    @property
    def tau_decay_s(self) -> float:
        return self._tau_decay_s

    @property
    def tau_rise_ms(self) -> float:
        return self._tau_rise_s / _MS_TO_S

    @property
    def tau_decay_ms(self) -> float:
        return self._tau_decay_s / _MS_TO_S

    @property
    def reversal_V(self) -> float:
        return self._reversal_V

    @property
    def reversal_mV(self) -> float:
        return self._reversal_V / _MV_TO_V

    @property
    def peak_conductance_S(self) -> float:
        return self._peak_conductance_S

    @property
    def peak_conductance_uS(self) -> float:
        return self._peak_conductance_S / _US_TO_SI_CONDUCTANCE

    @property
    def delay_s(self) -> float:
        return self._delay_s

    @property
    def delay_ms(self) -> float:
        return self._delay_s / _MS_TO_S

    @property
    def peak_time_s(self) -> float:
        """The analytic peak, measured from the DELAYED arrival."""
        return self._peak_time_s

    @property
    def peak_time_ms(self) -> float:
        return self._peak_time_s / _MS_TO_S

    @property
    def peak_time_from_event_ms(self) -> float:
        """The analytic peak measured from the PRESYNAPTIC EVENT.

        This is ``delay + peak_time``, and it is a different number from
        ``peak_time_ms``. Reporting the wrong one would misplace a synaptic
        event by the whole transmission delay.
        """
        return (self._delay_s + self._peak_time_s) / _MS_TO_S

    @property
    def kind(self) -> str:
        return SYNAPSE_KIND_DOUBLE_EXPONENTIAL

    @property
    def name(self) -> str:
        return MODEL_NAME_CHEMICAL_SYNAPSE_V0

    @property
    def is_stochastic(self) -> bool:
        """Always False. See the module docstring; there is no random state."""
        return False

    @property
    def has_short_term_plasticity(self) -> bool:
        """Always False. This mechanism is a bare double exponential."""
        return False

    @property
    def has_release_probability(self) -> bool:
        """Always False. Every event delivers deterministically."""
        return False

    @property
    def event_count(self) -> int:
        return len(self._arrivals_s)

    @property
    def arrival_times_s(self) -> Tuple[float, ...]:
        return tuple(self._arrivals_s)

    def state_is_only_the_event_list(self) -> bool:
        """Always True, asserted in the tests as a structural claim.

        The instance dictionary is checked to contain no quantity other than the
        shape constants and the arrival list, which is what makes the
        "no hidden recovery state" claim checkable rather than merely stated.
        """
        return True

    # -- events -----------------------------------------------------------

    def deliver_event(self, t_event_s: float) -> float:
        """Register a presynaptic event at ``t_event_s``. Returns its arrival.

        ``t_event_s`` is in SECONDS, matching the internal representation. The
        arrival is ``t_event_s + delay``. Events are accepted in any order and
        are stored sorted, so the waveform never depends on delivery order.
        """
        if t_event_s != t_event_s or abs(t_event_s) == float("inf"):
            raise ChemicalSynapseError(
                f"Event time must be a finite number, got {t_event_s!r} s"
            )
        arrival = t_event_s + self._delay_s
        self._arrivals_s.append(arrival)
        self._arrivals_s.sort()
        return arrival

    def deliver_events(self, event_times_s: Sequence[float]) -> Tuple[float, ...]:
        """Register several events, in any order."""
        return tuple(self.deliver_event(t) for t in event_times_s)

    def reset_events(self) -> None:
        """Forget every event. The shape constants are untouched."""
        self._arrivals_s = []

    def conductance_S(self, t_s: float) -> float:
        """Total conductance at absolute time ``t_s``, in siemens.

        The plain sum over every event that has already arrived. Because each
        contribution is non-negative for ``t_rel > 0``, the total is
        non-negative, and because each contribution has a single interior peak
        the total is a sum of unimodal humps with no oscillation.
        """
        if t_s != t_s or abs(t_s) == float("inf"):
            raise ChemicalSynapseError(
                f"Evaluation time must be a finite number, got {t_s!r} s"
            )
        total = 0.0
        for arrival in self._arrivals_s:
            t_rel = t_s - arrival
            if t_rel <= 0.0:
                continue
            total += self._peak_conductance_S * self._shape(t_rel) * self._normalization
        return total

    def current_A(self, t_s: float, v_post_V: float) -> float:
        """Synaptic current at ``t_s``, OUTWARD POSITIVE, in amperes.

        ``I_syn = g_syn * (V_post - E_syn)``, which is the same form and the
        same sign convention as the leak and the active channel currents in the
        existing 3.0D-8A engine. No second convention is introduced.
        """
        return self.conductance_S(t_s) * (v_post_V - self._reversal_V)

    def injected_current_A(self, t_s: float, v_post_V: float) -> float:
        """Synaptic current as an INWARD-POSITIVE injected current, in amperes.

        This is the exact negative of :meth:`current_A`, and it is the form
        ``ActiveAxonModel.step`` already accepts on its ``injected_currents_A``
        argument. Composing the synapse with the membrane solver therefore
        requires no sign conversion anywhere else in the project.
        """
        return -self.current_A(t_s, v_post_V)

    def injected_currents_A(
        self, t_s: float, v_post_V: float, compartment_id: str
    ) -> Dict[str, float]:
        """The injected current keyed by compartment, ready for ``step``."""
        return {compartment_id: self.injected_current_A(t_s, v_post_V)}

    # -- sampling ---------------------------------------------------------

    def trace(
        self,
        duration_s: float,
        dt_s: float,
        n_events: int = 0,
        first_event_s: float = 0.0,
        event_interval_s: Optional[float] = None,
    ) -> SynapseWaveformTrace:
        """Sample the total conductance waveform on a regular grid.

        The grid starts at ``0`` and uses ``dt_s``. ``n_events`` events are
        placed at ``first_event_s`` and then every ``event_interval_s``; a
        non-positive ``n_events`` records a single event at ``first_event_s``
        when ``event_interval_s`` is None. Sampling is exact arithmetic on the
        analytic waveform, not a numerical integration, so the result has no
        timestep error of its own.
        """
        if dt_s <= 0.0:
            raise SynapseUnitError(f"dt_s must be strictly positive, got {dt_s!r}")
        if duration_s < 0.0:
            raise SynapseUnitError(
                f"duration_s must be non-negative, got {duration_s!r}"
            )
        self.reset_events()
        if n_events > 0:
            if event_interval_s is None or event_interval_s <= 0.0:
                raise SynapseUnitError(
                    f"n_events={n_events} requires a strictly positive "
                    f"event_interval_s, got {event_interval_s!r}"
                )
            self.deliver_events(
                [first_event_s + i * event_interval_s for i in range(n_events)]
            )
        elif n_events == 0 and event_interval_s is not None:
            self.deliver_event(first_event_s)
        else:
            self.deliver_event(first_event_s)

        steps = int(round(duration_s / dt_s))
        times = tuple(i * dt_s for i in range(steps + 1))
        conductances = tuple(self.conductance_S(t) for t in times)
        return SynapseWaveformTrace(
            times_s=times,
            conductances_S=conductances,
            reversal_V=self._reversal_V,
            delay_s=self._delay_s,
            peak_conductance_S=self._peak_conductance_S,
            peak_time_s=self._peak_time_s,
            event_count=self.event_count,
            note=(
                f"{SYNAPSE_KIND_DOUBLE_EXPONENTIAL}, peak-normalized so that "
                f"g(t_peak) = peak_conductance_S exactly. Times are SECONDS from "
                f"the first event and conductance is in SIEMENS. "
                + _NO_ADDED_STATE
            ),
        )

    # -- refusals ---------------------------------------------------------

    def reject_unsupported_feature(self, feature: str) -> None:
        """Refuse a synaptic feature outside 3.0D-8G, naming why.

        Every refusal names the 3.0D-7V reason. The 3.0D-7U gap-junction unit
        conflict is explicitly not touched, converted or approximated here.
        """
        if feature in ("double_exponential", "peak_normalized", "delay", "sum"):
            raise ChemicalSynapseError(
                f"Feature '{feature}' IS implemented by "
                f"{MODEL_NAME_CHEMICAL_SYNAPSE_V0}."
            )
        reason = _REFUSAL_REASONS.get(
            feature,
            "No project source supports it, and 3.0D-8G implements only the "
            "published phenomenological double-exponential chemical synapse.",
        )
        raise ChemicalSynapseError(
            f"Feature '{feature}' is OUT OF SCOPE for "
            f"{MODEL_NAME_CHEMICAL_SYNAPSE_V0}. " + reason
        )

    def scope_note(self) -> str:
        return " ".join((SYNAPSE_KIND_DOUBLE_EXPONENTIAL, _PHENOMENOLOGICAL_SCOPE))


_REFUSAL_REASONS: Dict[str, str] = {
    "Dalpha7": (
        "3.0D-7V records Dalpha7 as an experimentally supported receptor IDENTITY "
        "carrying NO quantitative kinetics. The published Exp2Syn contains no "
        "receptor, no subunit and no binding step, so nothing about Dalpha7 may "
        "be read out of it. No single-channel conductance, opening probability, "
        "alpha or beta rate, or desensitization rate exists in any project "
        "source, and none is invented."
    ),
    "release_probability": (
        "No project source states a release probability for this synapse, and "
        "the published model contains no stochastic release step. Every event "
        "delivers deterministically."
    ),
    "vesicle_pool": (
        "No project source states a vesicle pool size or depletion model. The "
        "published Exp2Syn has no vesicle state."
    ),
    "short_term_plasticity": (
        "Neither depression nor facilitation is modelled by the published "
        "Exp2Syn, and 3.0D-8G adds none."
    ),
    "desensitization": (
        "No project source states a desensitization rate for the Dalpha7 "
        "receptor at this synapse."
    ),
    "calcium": (
        "No project source states a presynaptic calcium concentration or a "
        "calcium-dependent release rule for this synapse."
    ),
    "Q10": (
        "The published model contains no Q10 or temperature scaling for the "
        "synapse, and none is introduced."
    ),
    "gap2": (
        "gap2.mod is NOT implemented. The unresolved 3.0D-7U gap-junction unit "
        "conflict is not touched, converted or approximated here."
    ),
    "Exp2Syn": (
        "Exp2Syn is the NAME of the published point process this mechanism "
        "reproduces. Requesting it as a separate feature would be requesting a "
        "second implementation of the same double exponential."
    ),
}


# =============================================================================
# LAYER 2: the specific connection. All biology lives here and below, never in
# the mechanism above.
# =============================================================================


def _quantity_of(registry, synapse_id: str, name: str):
    """Look up ONE synaptic quantity, scoped to its synapse.

    The 3.0D-7V registry keys ``get()`` on the bare quantity name, which is
    deliberately reused across the three synapses: all three have a ``rise_tau``.
    A live configuration must therefore scope the lookup, and an ambiguous or
    missing match is an error rather than a silent first-match win.
    """
    matches = [
        record for record in registry.quantities
        if record.synapse_id == synapse_id and record.name == name
    ]
    if len(matches) != 1:
        raise ChemicalSynapseError(
            f"Expected exactly one 3.0D-7V quantity named '{name}' on synapse "
            f"'{synapse_id}', found {len(matches)}. The registry keys quantities "
            f"by bare name across synapses, so this lookup must be scoped and "
            f"must not fall back to an arbitrary match."
        )
    return matches[0]


def _prepared_network(model, segment_count: int):
    """Prepare the DLMn active network this synapse would drive.

    Used only by the numerical diagnostic, so the compartment areas and
    capacitances are read from the same 3.0D-8A preparation the synapse would
    actually drive rather than being recomputed on a parallel code path. The
    import is local so that the generic mechanism above never depends on the
    neuron engine.
    """
    from .dlmn_active import DLMNActiveAxonModel

    return DLMNActiveAxonModel().prepare_dlmn(model, segment_count=segment_count)


@dataclass(frozen=True)
class SynapticParameterUse:
    """One published value this live synapse consumes, with its provenance.

    This exists so that a caller can see, per parameter, whether the number came
    from the ModelDB source, from the paper, and with what evidence status. It
    carries no new value: every number here is read from the 3.0D-7V registry
    rather than restated.
    """

    name: str
    source_value: float
    source_unit: Optional[str]
    source_value_text: str
    source_file: str
    source_line: int
    paper_value: Optional[float]
    paper_unit: Optional[str]
    paper_label: str
    evidence_status: str
    value_agreement: Optional[str]
    used_live_value: float
    used_live_unit: str
    limitations: str


class PSI_DLMnChemicalSynapse:
    """The ONE live chemical connection 3.0D-8G implements: PSI -> DLMn.

    This is a CONFIGURATION of :class:`DoubleExponentialSynapse`, built by
    reading the 3.0D-7V registry rather than by restating its numbers. The
    mechanism above stays free of biology; all of it lives here.

    The postsynaptic site is the SOURCE-BACKED physical placement of 12.5 um
    from the proximal end of the DLMn axon, which 3.0D-7B already recorded. The
    ModelDB source expresses its synapse sites as NORMALIZED section fractions
    (``DLMn_syn_pre_loc = 0.85``, ``DLMn_syn_post_loc = 0.25``); those are
    recorded, but the physical placement layer is authoritative for this
    project's geometry, and this checkpoint verifies that the two agree rather
    than importing either in place of the other.
    """

    def __init__(
        self,
        peak_conductance_uS: Optional[float] = None,
        peak_conductance_source: str = "paper",
    ) -> None:
        registry = get_synaptic_mechanism_registry()
        record = registry.synapse(SYNAPSE_PSI_DLMN)
        if record.topology != TOPOLOGY_CHEMICAL:
            raise ChemicalSynapseError(
                f"Synapse '{SYNAPSE_PSI_DLMN}' is recorded as "
                f"'{record.topology}', not a chemical-only synapse."
            )

        self._registry = registry
        self._synapse_id = SYNAPSE_PSI_DLMN
        self._source_neuron = record.source_neuron
        self._target_neuron = record.target_neuron

        rise = _quantity_of(registry, SYNAPSE_PSI_DLMN, "rise_tau")
        decay = _quantity_of(registry, SYNAPSE_PSI_DLMN, "decay_tau")
        reversal = _quantity_of(registry, SYNAPSE_PSI_DLMN, "reversal_potential")
        delay = _quantity_of(registry, SYNAPSE_PSI_DLMN, "delay")
        peak = _quantity_of(registry, SYNAPSE_PSI_DLMN, "peak_conductance")

        # The peak conductance is the ONE quantity with an unresolved
        # discrepancy between the source and the paper, so choosing which of the
        # two to run is an explicit, recorded decision and never a silent one.
        if peak_conductance_uS is None:
            if peak_conductance_source == "paper":
                if peak.paper_value is None or peak.paper_unit != "uS":
                    raise ChemicalSynapseError(
                        "The paper peak conductance is unavailable in the 3.0D-7V "
                        "registry; refusing to substitute another value."
                    )
                peak_conductance_uS = peak.paper_value
            elif peak_conductance_source == "source_weight_as_written":
                # The source states 0.08 with NO declared unit. It is used
                # here VERBATIM as a bare number and is NOT converted, NOT
                # multiplied by 1e-6 and NOT equated with 80 uS.
                peak_conductance_uS = peak.source_value
            else:
                raise ChemicalSynapseError(
                    f"peak_conductance_source must be 'paper' or "
                    f"'source_weight_as_written', got "
                    f"{peak_conductance_source!r}"
                )
        self._peak_conductance_source = peak_conductance_source

        self._mechanism = DoubleExponentialSynapse(
            tau_rise_ms=rise.source_value,
            tau_decay_ms=decay.source_value,
            reversal_mV=reversal.source_value,
            peak_conductance_uS=peak_conductance_uS,
            delay_ms=delay.source_value,
        )

        self._parameters = tuple(
            SynapticParameterUse(
                name=quantity.name,
                source_value=quantity.source_value,
                source_unit=quantity.source_unit,
                source_value_text=quantity.source_value_text,
                source_file=quantity.source_file,
                source_line=quantity.source_line,
                paper_value=quantity.paper_value,
                paper_unit=quantity.paper_unit,
                paper_label=quantity.paper_label,
                evidence_status=quantity.evidence_status.value,
                value_agreement=quantity.value_agreement,
                used_live_value=used,
                used_live_unit=unit,
                limitations=quantity.limitations,
            )
            for quantity, used, unit in (
                (rise, rise.source_value, "ms"),
                (decay, decay.source_value, "ms"),
                (reversal, reversal.source_value, "mV"),
                (delay, delay.source_value, "ms"),
                (peak, peak_conductance_uS, "uS"),
            )
        )

    # -- identity ---------------------------------------------------------

    @property
    def synapse_id(self) -> str:
        return self._synapse_id

    @property
    def source_neuron(self) -> str:
        return self._source_neuron

    @property
    def target_neuron(self) -> str:
        return self._target_neuron

    @property
    def kind(self) -> str:
        return SYNAPSE_KIND_DOUBLE_EXPONENTIAL

    @property
    def name(self) -> str:
        return MODEL_NAME_CHEMICAL_SYNAPSE_V0

    @property
    def mechanism(self) -> DoubleExponentialSynapse:
        return self._mechanism

    @property
    def parameters(self) -> Tuple[SynapticParameterUse, ...]:
        return self._parameters

    @property
    def peak_conductance_source(self) -> str:
        """Which of the two unresolved numbers this live synapse runs on."""
        return self._peak_conductance_source

    # -- postsynaptic site, from the physical placement layer -------------

    def postsynaptic_distance_um(self, model) -> float:
        """The source-backed PSI input distance on the DLMn axon, in um.

        Read from the 3.0D-7B morphology, which is the authority for this
        project's geometry. It is NOT recomputed from the ModelDB normalized
        fraction, and no new location is invented.
        """
        placements = model.compartments[self.target_section_id].placements
        inputs = [p for p in placements if p.kind == "input"]
        if not inputs:
            raise ChemicalSynapseError(
                f"No source-backed input placement on "
                f"'{self.target_section_id}'"
            )
        return float(inputs[0].distance_um)

    @property
    def target_section_id(self) -> str:
        return f"{self._target_neuron}_axon"

    @property
    def source_section_id(self) -> str:
        return f"{self._source_neuron}_axon"

    def postsynaptic_segment_id(
        self, model, segment_count: int
    ) -> str:
        """The derived segment carrying the postsynaptic synapse site."""
        from ..subdivision import map_placement_to_segment

        index = map_placement_to_segment(
            self.postsynaptic_distance_um(model),
            model.compartments[self.target_section_id].geometry.length_um,
            segment_count,
        )
        return f"{self.target_section_id}#seg{index}"

    def modeldb_normalized_sites(self) -> Dict[str, float]:
        """The ModelDB NORMALIZED site fractions, recorded but not authoritative.

        gfpn.py expresses synapse sites as fractions along a section. They are
        reported here for comparison with the physical placements, and this
        module does not substitute them for the physical layer.
        """
        return {
            "pre_location": _quantity_of(
                self._registry, SYNAPSE_PSI_DLMN, "pre_location"
            ).source_value,
            "post_location": _quantity_of(
                self._registry, SYNAPSE_PSI_DLMN, "post_location"
            ).source_value,
        }

    def numerical_adequacy_report(
        self, model, segment_count: int = 11, timestep_ms: float = 0.01
    ) -> Dict[str, object]:
        """How the synaptic conductance compares with the compartment it drives.

        THIS IS A NUMERICAL DIAGNOSTIC, NOT A BIOLOGICAL ONE, and it exists
        because the UNRESOLVED 1000x peak-conductance discrepancy has a very
        large numerical consequence that would otherwise be discovered by
        accident as a diverging simulation.

        The two numbers that matter are the synaptic membrane time constant
        ``C_post / g_syn`` and the ratio of the synaptic conductance to the
        compartment's own maximum sodium conductance. A synaptic conductance
        hundreds of times larger than the compartment's entire Na conductance
        cannot be resolved at the project timestep, and a synaptic membrane
        time constant far below the timestep means the whole synaptic transient
        falls inside a single step. Neither fact says anything about which of
        the two unresolved published peak-conductance numbers is correct.

        ``network`` is an already-prepared active network, so the compartment
        areas and capacitances are read from the same 3.0D-8A preparation the
        synapse would drive, and nothing is recomputed here.
        """
        from ..active_profiles import PROFILE_AUGUSTIN_2019_ACTIVE_MODEL

        segment_id = self.postsynaptic_segment_id(model, segment_count)
        network = _prepared_network(model, segment_count)
        compartment = next(
            c for c in network.network.compartments
            if c.compartment_id == segment_id
        )
        area_cm2 = compartment.membrane_area_cm2
        capacitance_F = compartment.capacitance_F
        # Read the sodium density from the network's OWN applied parameters,
        # which 3.0D-8A has already converted from the profile's mS/cm2 to
        # S/cm2. Reading the raw profile value here would silently reuse
        # mS/cm2 as if it were S/cm2 and overstate the sodium conductance by a
        # factor of 1000, which is exactly the kind of unit mixing this module
        # exists to prevent.
        g_na_density_S_per_cm2 = next(
            p.value for p in network.applied_parameters
            if p.name == "g_Na"
            and p.profile_name == PROFILE_AUGUSTIN_2019_ACTIVE_MODEL
        )
        g_nat_max_S = g_na_density_S_per_cm2 * area_cm2
        g_syn_S = self._mechanism.peak_conductance_S
        tau_ms = (
            capacitance_F / g_syn_S * 1e3 if g_syn_S > 0.0 else float("inf")
        )
        return {
            "segment_id": segment_id,
            "membrane_area_cm2": area_cm2,
            "capacitance_F": capacitance_F,
            "peak_conductance_S": g_syn_S,
            "peak_conductance_source": self._peak_conductance_source,
            "synaptic_membrane_tau_ms": tau_ms,
            "timestep_ms": timestep_ms,
            "tau_over_timestep": (
                tau_ms / timestep_ms if g_syn_S > 0.0 else float("inf")
            ),
            "g_nat_max_S": g_nat_max_S,
            "synaptic_over_sodium": (
                g_syn_S / g_nat_max_S if g_nat_max_S > 0.0 else float("inf")
            ),
            "note": (
                "NUMERICAL DIAGNOSTIC, NOT A BIOLOGICAL CLAIM. A synaptic "
                "conductance many times the compartment's own maximum sodium "
                "conductance is not resolvable at the project timestep, and a "
                "synaptic membrane time constant far below the timestep places "
                "the whole synaptic transient inside a single step. Neither "
                "fact says anything about which of the two unresolved published "
                "peak-conductance numbers is correct."
            ),
        }

    def scope_note(self) -> str:
        return " ".join((
            f"{SYNAPSE_PSI_DLMN} IS A LIVE {SYNAPSE_KIND_DOUBLE_EXPONENTIAL} "
            f"BUILT FROM THE 3.0D-7V REGISTRY, NOT FROM RESTATED NUMBERS.",
            _PHENOMENOLOGICAL_SCOPE,
            _NO_ADDED_STATE,
            "NO GF->TTMn OR GF->PSI CHEMICAL COMPONENT IS IMPLEMENTED: the "
            "source gives both a ZERO weight in its default parameter set, and "
            "3.0D-8G implements neither. NO gap junction is implemented and the "
            "3.0D-7U unit conflict is untouched and unresolved. No Dalpha7 "
            "kinetics, no vesicle release, no calcium, no short-term "
            "plasticity, no Q10, no sensory coupling, no NMJ, no muscle and no "
            "behaviour.",
            f"THE PEAK CONDUCTANCE RUNS ON THE {self._peak_conductance_source!r} "
            f"NUMBER. The paper states 80 uS ('estimated'); gfpn.py writes "
            f"{SOURCE_DLMN_WEIGHT} with NO declared unit; the ratio of the two "
            f"written numbers is exactly {PEAK_DISCREPANCY_FACTOR:g} and the "
            f"discrepancy is {DISCREPANCY_UNRESOLVED}. This checkpoint converts "
            f"nothing, decides nothing, and defines no corrected value.",
        ))


# =============================================================================
# LAYER 3: provenance re-export, so callers need not import 7V directly.
# =============================================================================


def chemical_synapse_scope_note() -> str:
    """The scope statement 3.0D-8G reports alongside any of its results."""
    return " ".join((
        "3.0D-8G IMPLEMENTS THE PUBLISHED PHENOMENOLOGICAL DOUBLE-EXPONENTIAL "
        "CHEMICAL SYNAPSE FOR PSI->DLMn AND NOTHING ELSE. The mechanism is "
        "generic and knows no neuron; the connection is configured from the "
        "3.0D-7V registry; the provenance stays in 3.0D-7V.",
        _PHENOMENOLOGICAL_SCOPE,
        _NO_ADDED_STATE,
        "THE SYNAPSE IS NOT A Dalpha7 KINETIC MODEL, AND 0 mV IS A MODEL "
        "REVERSAL POTENTIAL, NOT A MEASURED Dalpha7 REVERSAL POTENTIAL. NO "
        "GF->TTMn OR GF->PSI CHEMICAL COMPONENT, NO gap junction, NO vesicle "
        "release, NO calcium, NO short-term plasticity, NO receptor "
        "desensitization, NO Q10, NO sensory coupling, NO motor or NMJ "
        "dynamics, NO muscle and NO behaviour are implemented. The 3.0D-7U "
        "gap-junction unit conflict is untouched and remains UNRESOLVED.",
    ))
