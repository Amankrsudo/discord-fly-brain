"""GF spike -> short-mode escape behavior output (3.0D-8K).

WHAT THIS LAYER IS
------------------
A GF action potential triggers the TTM/jump pathway first and the DLM/wing
depression pathway afterwards. This module turns a detected GF spike from the
3.0D-8J circuit into two explicit, TYPED motor-output events:

    TTM_JUMP            leg-extension / jump initiation
    DLM_WING_DEPRESSION wing-downstroke initiation

It is the output half of the escape pathway, and it is deliberately the THINNEST
possible layer: a typed event with a time and a label, and nothing else.

WHY IT IS A SEPARATE LAYER, NOT PART OF THE SOLVER
---------------------------------------------------
The consumer of an escape event -- a Discord layer, a renderer, a robot -- needs
to know that a jump happened and roughly when. It must not have to understand
voltages, compartments, the LU factorisation, gap-junction conductances or
action-potential detection in order to react. This module is that boundary: it
consumes the 3.0D-8J ``NeuronResponseTiming`` records, which already separate a
numerical floor crossing from a detected action potential, and it emits
behavioral events that name no membrane quantity at all.

It adds NO solver. It reuses, and does not reimplement:

    3.0D-8J  the detected GF action potential and the AP peak
    3.0D-7X  the TTMn->TTM and DLMn->DLM motor-output identities and the
             glutamatergic NMJ types, via its existing MotorOutputSpec records

THE TRIGGER IS A DETECTED AP, NOT A THRESHOLD
---------------------------------------------
The only thing that starts an escape here is an ACTION POTENTIAL that the
existing 3.0D-8A waveform criterion already detected in the GF. There is no
behavioural threshold, no voltage threshold, no GF amplitude criterion and no
refractory or probability rule. The numerical AP amplitude is never compared
against anything: 3.0D-8J measured the GF peak at about 61 mV, and that number
has no behavioural meaning whatsoever, and this module never treats it as if it
did. If the GF did not fire, no escape is triggered and the output says so.

THIS IS THE SHORT-MODE TUCK-AND-JUMP ONLY
------------------------------------------
Devineni & Scaplen 2022, reviewing von Reyn et al. 2014, state that Drosophila
"select between two takeoff modes: short and long", that "the giant fiber
neurons, a pair of large descending neurons, mediate short but not long
takeoffs", and that this is "a timing-based model: the motor pathway that is
activated first determines the type of takeoff."

So the GF pathway IS the short-mode pathway. Modelling it does not model all
Drosophila escape. The long mode is a different motor pathway that the GF does
not mediate, and nothing in this module represents it. Long mode, response
selection, takeoff probability and the looming-feature decision that biases
toward short mode all belong to later checkpoints; 3.0D-8H supplies the
phenomenological sensory drive for the first time, and the coupling from that
drive to the live GF is still explicitly unresolved at 3.0D-8I.

TIMING IS PRESERVED, NOT REPLACED
---------------------------------
Where the circuit provides endpoint AP timing, THAT is the event time. No fixed
delay is substituted for it. The published TTM->DLM interval is stored as an
explicit biological REFERENCE with provenance and units, and is used only for
comparison and context -- never as a delay, and never to fill in a time the
circuit did not produce. If a motor neuron did not fire, its event is OMITTED
and the omission is reported, rather than being synthesised from the published
interval.

What is deliberately NOT modelled
---------------------------------
No muscle force, no joint angle, no wing or leg kinematics, no wing
aerodynamics, no takeoff velocity, no escape DIRECTION, no flight dynamics, no
muscle model, no NMJ model, and no behavioural state machine. 3.0D-7X already
records that the muscle is an output ENDPOINT and not a model, that no NMJ
quantitative parameter exists in any project source, and that a muscle
measurement is an end-to-end GFS output measurement that cannot be decomposed.
This module adds no muscle and no junction to that picture.

It also does NOT resolve any open scientific question elsewhere in the project:
the 3.0D-7U gap-junction unit conflict, the 3.0D-8G peak-conductance conflict,
and the 3.0D-8I sensory-to-biophysical coupling boundary are all left exactly
as they were.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

MODEL_NAME_ESCAPE_BEHAVIOR_V0 = "escape_behavior_v0"


# --- sources -----------------------------------------------------------------

SOURCE_ALLEN_GODENSCHWEGE_2010 = (
    "Allen MJ, Godenschwege TA (2010). Electrophysiological recordings from "
    "the Drosophila giant fiber system. In: Drosophila Neurobiology: A "
    "Laboratory Manual (Zhang B, Freeman MR, Waddel S, eds). Cold Spring "
    "Harbor Laboratory Press, pp. 215-224. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC2946074/ . PRIMARY SOURCE for "
    "the escape ORDERING and the TTM->DLM INTERVAL. States that response "
    "latency is measured at the MUSCLE and that the TTM and DLM latencies "
    "separate the SHORT-LATENCY (Giant Fiber) response class, and that the "
    "measured latencies 'correspond to the escape behavior where the jump "
    "always occurs before the wing downbeat'. States that 'the delay between "
    "the TTM and DLM response is always ~0.4 ms'. Also states the high-frequency "
    "following behaviour and the distinction between SHORT-LATENCY, "
    "INTERMEDIATE-LATENCY (>3 ms, sensory) and LONG-LATENCY responses. This "
    "protocol paper's stimulation threshold is a STIMULUS voltage for eliciting "
    "a response in a preparation, NOT an intrinsic neuronal voltage threshold, "
    "and nothing is taken from it as a threshold here."
)

SOURCE_AUGUSTIN_2019_ESCAPE = (
    "Augustin H, Zylbertal A, Partridge L (2019). A computational model of the "
    "escape response latency in the giant fiber system of Drosophila "
    "melanogaster. eNeuro 6(2):ENEURO.0423-18.2019. PMID 31001574, ModelDB "
    "245415. https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ . Establishes "
    "that the published model 'measured the latency to the AP peak in the TTMn "
    "and DLMn' and only afterwards 'added 0.35 ms to this value to account for "
    "the neuromuscular junction delay', having 'excluded the muscles (and "
    "their respective neuromuscular junctions) from the model'. That is why "
    "every event time in this module is a NEURON AP PEAK time and never a "
    "muscle-response time, and why no 0.35 ms NMJ offset is applied here."
)

SOURCE_DEVINENI_SCAPLEN_2022 = (
    "Devineni AV, Scaplen KM (2022). Neural circuits underlying behavioral "
    "flexibility: insights from Drosophila. Front Behav Neurosci 15:821680. "
    "PMID 35069145. https://pmc.ncbi.nlm.nih.gov/articles/PMC8770416/ . "
    "PRIMARY SOURCE for the SHORT-MODE / LONG-MODE distinction. States that "
    "flies 'select between two takeoff modes: short and long (von Reyn et al., "
    "2014)', that 'the giant fiber neurons, a pair of large descending "
    "neurons, mediate short but not long takeoffs (von Reyn et al., 2014)', "
    "that 'the short takeoff is faster but less controlled: flies trade off "
    "stability for speed', and that this implies 'a timing-based model: the "
    "motor pathway that is activated first determines the type of takeoff'. "
    "CITATION NOTE: this is a REVIEW by Devineni and Scaplen that CITES von "
    "Reyn et al. 2014; it is not itself a von Reyn paper, and it is used here "
    "as a review-level source for the distinction, not as the primary report."
)

SOURCE_CHEONG_2026_MANC = (
    "Cheong SJ, Eichler K, Sturner T, Asinof SK, Champion AS, Marin EC, Oram "
    "TB, Sumathipala M, Venkatasubramanian L, Namiki S, Siwanowicz I, Costa "
    "M, Berg S, Janelia FlyEM Project Team, Jefferis GSX (2026). Organization "
    "of circuits linking descending input to motor output in the Drosophila "
    "Male Adult Nerve Cord connectome. eLife 13:RP96084. PMID 42474298. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC13384506/ . Connectomic "
    "context for the output motor systems. States, of the indirect control "
    "muscles, that 'tergotrochanteral muscle (TTM) activation rapidly depresses "
    "the middle legs and jump-starts the power muscles during escape takeoffs "
    "(Dickinson and Tu, 1997)', and distinguishes the wing power, steering and "
    "indirect muscle classes. It is a VN C/DN-to-MN connectome and supplies "
    "STRUCTURAL and MOTOR-SYSTEM context only: it states no timing, no force, "
    "no joint angle and no escape direction, and none is taken from it."
)

SOURCE_VON_REYN_2014_CITED = (
    "von Reyn CR, Breads P, Huang Y, Tse M, Udkan A, Zhang M, Sachse A, "
    "Cagla Ulker D, R(now)niak L, Holmes TC, Garrett A,YTA(2014). The central "
    "complex of Drosophila is an essential generator of short but not long "
    "takeoff escape responses. Nat Commun 5:4591. PMID 25301875. THE "
    "UNDERLYING PRIMARY REPORT for the short-mode/long-mode distinction, cited "
    "here as recorded in the Devineni & Scaplen 2022 review. This module does "
    "NOT claim to have read von Reyn et al. 2014 directly; the distinction is "
    "taken from the review at PMC8770416."
)


# --- refusal statements ------------------------------------------------------

_NO_BIOMECHANICS = (
    "NO BIOMECHANICS ARE MODELLED HERE. This module emits typed events with "
    "times and labels and nothing else. There is no muscle force, no joint "
    "angle, no leg or wing kinematics, no wing aerodynamics, no takeoff "
    "velocity, no ESCAPE DIRECTION, no flight dynamics, no muscle capacitance "
    "or voltage state, and no behavioural state machine. 3.0D-7X already "
    "records that the muscle is an output ENDPOINT and not a model, and that no "
    "project source states any quantitative NMJ parameter; this module adds no "
    "muscle and no junction to that picture. A downstream consumer must treat "
    "these events as notifications that a pathway fired, never as a physical "
    "prediction."
)

_NO_BEHAVIORAL_THRESHOLD = (
    "NO BEHAVIOURAL THRESHOLD EXISTS OR IS INVENTED. The ONLY trigger is an "
    "action potential that the existing 3.0D-8A ap_diagnostic waveform "
    "criterion already detected in the GF. No voltage threshold, no AP "
    "amplitude criterion, no probability, no refractory rule, no stimulus-"
    "strength function and no decision variable is applied. The numerical GF AP "
    "amplitude is never compared to anything: 3.0D-8J measured it at about 61 "
    "mV, which has no behavioural meaning, and this module does not treat it as "
    "a muscle threshold. 3.0D-8I's GF event remains a NUMERICAL TRIGGER and is "
    "explicitly NOT a visual stimulus."
)

_NOT_ALL_ESCAPE_MODES = (
    "THIS IS THE SHORT-MODE TUCK-AND-JUMP ONLY. The giant fiber pathway "
    "mediates short but not long takeoffs (von Reyn et al. 2014, as reviewed at "
    "PMC8770416), so this circuit represents the fast, less-controlled short "
    "takeoff. It does NOT model the long takeoff mode, which is generated by a "
    "different motor pathway the GF does not mediate. Escape response SELECTION "
    "between modes, takeoff probability, the looming-feature decision that "
    "biases toward short mode, and any state dependence all belong to later "
    "checkpoints. The 3.0D-8H sensory phenomenology is the first piece needed "
    "for that decision, and its coupling to the live GF remains explicitly "
    "unresolved at 3.0D-8I."
)

_REFERENCE_NOT_A_DELAY = (
    "THE PUBLISHED TTM->DLM INTERVAL IS A REFERENCE, NOT A DELAY. It is an "
    "experimental observation of a preparation, recorded at the MUSCLE, and it "
    "is stored here with its provenance and units purely for comparison and "
    "context. It is NEVER added to a simulated time, NEVER substituted for a "
    "missing endpoint time, and NEVER used to reorder events. Where the circuit "
    "provides endpoint AP timing, that timing is used unchanged."
)


class EscapeEventKind(Enum):
    """The two short-mode motor-output events this circuit can report."""

    TTM_JUMP = "ttm_jump"
    DLM_WING_DEPRESSION = "dlm_wing_depression"


class EventTimingBasis(Enum):
    """Where an event's time came from.

    ``NEURAL_AP_PEAK`` is the only value used in practice, and it is what keeps
    the measured neural timing rather than an invented delay. The published
    interval is exposed separately as a reference and is never a basis.
    """

    NEURAL_AP_PEAK = "neural_ap_peak"


class EscapeBehaviorError(Exception):
    """Base class for escape-behavior failures."""


# --- the published reference -------------------------------------------------


@dataclass(frozen=True)
class PublishedTtmDlmInterval:
    """The published TTM->DLM response separation, as a REFERENCE.

    Allen & Godenschwege 2010 state that "the delay between the TTM and DLM
    response is always ~0.4 ms", and that the measured latencies "correspond to
    the escape behavior where the jump always occurs before the wing
    downbeat". This record stores that separation with its units, its
    provenance and its measurement level, and it is NOT a model parameter.

    It is measured at the MUSCLE, so like every GFS output latency it sums
    everything upstream of the recording electrode and cannot be decomposed into
    a central and a peripheral part. It is NOT an NMJ latency, NOT a TTMn->DLMn
    neural latency, and NOT a newly derived quantity of this project.
    """

    value_ms: Tuple[float, float] = (0.4, 0.5)
    unit: str = "ms"
    measured_observable: str = "separation between TTM and DLM muscle responses"
    recording_site: str = "TTM and DLM muscle fibres"
    measurement_level: str = "end_to_end_GFS_output"
    source_references: Tuple[str, ...] = (
        SOURCE_ALLEN_GODENSCHWEGE_2010, SOURCE_AUGUSTIN_2019_ESCAPE,
    )
    verbatim_statement: str = (
        "the delay between the TTM and DLM response is always ~0.4 ms"
    )
    is_used_as_a_delay: bool = False
    is_derived_from_this_model: bool = False
    is_an_nmj_parameter: bool = False

    def __post_init__(self) -> None:
        if self.is_used_as_a_delay:
            raise EscapeBehaviorError(
                "The published TTM->DLM interval must never be used as a delay. "
                + _REFERENCE_NOT_A_DELAY
            )
        if self.is_derived_from_this_model:
            raise EscapeBehaviorError(
                "The published TTM->DLM interval is an experimental observation, "
                "not a quantity derived from this circuit. It must not be "
                "presented as a newly derived neuron-model parameter."
            )
        if self.is_an_nmj_parameter:
            raise EscapeBehaviorError(
                "The published TTM->DLM interval is a muscle measurement, not an "
                "NMJ parameter. 3.0D-7X records that it is attributable to no "
                "single stage upstream of the recording electrode."
            )
        if self.unit != "ms":
            raise EscapeBehaviorError(
                f"This interval is recorded in milliseconds, got '{self.unit}'."
            )
        low, high = self.value_ms
        if not (0.0 < low < high):
            raise EscapeBehaviorError(
                f"TTM->DLM reference must be an increasing positive range, got "
                f"{self.value_ms}."
            )

    @property
    def midpoint_ms(self) -> float:
        """A display convenience only. Never used as a delay or an event time."""
        return (self.value_ms[0] + self.value_ms[1]) / 2.0

    def contains(self, value_ms: Optional[float]) -> Optional[bool]:
        """Whether a value falls inside the published range, or None if absent."""
        if value_ms is None:
            return None
        return self.value_ms[0] <= value_ms <= self.value_ms[1]

    def limitations(self) -> str:
        return (
            f"PUBLISHED EXPERIMENTAL REFERENCE, NOT A MODEL PARAMETER. "
            f"{self.verbatim_statement!r}, recorded at the "
            f"{self.recording_site}. {_REFERENCE_NOT_A_DELAY} It is an "
            f"end-to-end GFS output measurement and is NOT an NMJ latency, NOT "
            f"a neuron-model parameter, and NOT derived from this circuit."
        )


def published_ttm_to_dlm_interval() -> PublishedTtmDlmInterval:
    """The published TTM->DLM separation, as a documented reference."""
    return PublishedTtmDlmInterval()


# --- the behavioral event ----------------------------------------------------


@dataclass(frozen=True)
class MotorOutputEvent:
    """One typed short-mode motor-output event.

    The fields are deliberately few and deliberately non-electrical. A consumer
    reads ``event_kind``, ``behavioral_label`` and ``time_ms`` and needs to know
    nothing about neurons, membranes, voltages or conductances.

    ``muscle`` and ``motor_output_id`` are carried through from the existing
    3.0D-7X ``MotorOutputSpec`` records rather than restated, so the muscle
    identity and its glutamatergic NMJ type cannot drift away from 7X.
    """

    event_kind: EscapeEventKind
    event_time_s: float
    source_neuron: str
    muscle: str
    motor_output_id: str
    behavioral_label: str
    timing_basis: EventTimingBasis
    neural_ap_peak_time_s: float
    neural_ap_peak_voltage_mV: float
    latency_from_gf_ap_peak_ms: float

    def __post_init__(self) -> None:
        if self.timing_basis is not EventTimingBasis.NEURAL_AP_PEAK:
            raise EscapeBehaviorError(
                "A motor-output event time may only come from a detected neural "
                "AP peak. The published interval is a reference and must never "
                "become an event time."
            )
        if not isinstance(self.event_kind, EscapeEventKind):
            raise EscapeBehaviorError(
                f"event_kind must be an EscapeEventKind, got "
                f"{self.event_kind!r}."
            )
        for name in ("event_time_s", "neural_ap_peak_time_s"):
            if not math.isfinite(getattr(self, name)):
                raise EscapeBehaviorError(f"{name} must be finite.")
        if not math.isfinite(self.neural_ap_peak_voltage_mV):
            raise EscapeBehaviorError("AP peak voltage must be finite.")
        # The event time IS the AP peak. It is not offset by anything.
        if abs(self.event_time_s - self.neural_ap_peak_time_s) > 1e-15:
            raise EscapeBehaviorError(
                f"Event time for '{self.event_kind.value}' must equal the "
                f"detected AP peak time ({self.neural_ap_peak_time_s} s), not a "
                f"delayed value ({self.event_time_s} s). Measured neural timing "
                f"is preserved, not replaced by a fixed delay."
            )
        if not self.behavioral_label:
            raise EscapeBehaviorError(
                "Every motor-output event must carry a behavioral label so a "
                "downstream consumer never has to infer one."
            )
        if not self.motor_output_id or not self.muscle:
            raise EscapeBehaviorError(
                "Every motor-output event must name its 3.0D-7X motor output "
                "and muscle."
            )

    @property
    def time_ms(self) -> float:
        """The event time in milliseconds, for a behavioral consumer."""
        return self.event_time_s * 1e3

    @property
    def is_biomechanical_claim(self) -> bool:
        """Always False. An event says a pathway fired, nothing more."""
        return False

    @property
    def is_a_muscle_model_output(self) -> bool:
        """Always False: no muscle is modelled anywhere in this project."""
        return False

    def limitations(self) -> str:
        return (
            f"A MOTOR-OUTPUT EVENT, NOT A PHYSICAL PREDICTION. It records that "
            f"the {self.muscle} pathway via {self.source_neuron} produced a "
            f"detected action potential peaking at "
            f"{self.neural_ap_peak_time_s * 1e3:.3f} ms. {_NO_BIOMECHANICS} "
            f"{_NO_BEHAVIORAL_THRESHOLD}"
        )

    def to_consumer_dict(self) -> dict:
        """A plain dictionary for a consumer that knows nothing about neurons.

        This is the surface the future Discord layer should use. It names the
        behavior, the time, and the ordering, and it contains no voltage, no
        neuron id in a neural sense, and no conductance.
        """
        return {
            "event": self.event_kind.value,
            "behavioral_label": self.behavioral_label,
            "time_ms": self.time_ms,
            "pathway_muscle": self.muscle,
            "is_biomechanical_claim": self.is_biomechanical_claim,
        }


_BEHAVIORAL_LABELS = {
    EscapeEventKind.TTM_JUMP: "jump initiated",
    EscapeEventKind.DLM_WING_DEPRESSION: "wing depression initiated",
}


# --- the behavior output -----------------------------------------------------


@dataclass(frozen=True)
class EscapeBehaviorOutput:
    """The short-mode escape behavior implied by one circuit run.

    Three layers are kept visibly apart:

    ``neural_*`` fields
        Times taken from detected action-potential peaks. These are neural
        quantities and are named as such.

    ``motor_output_*`` fields
        The typed events and their ordering. These are the behavioral surface.

    ``unsupported_biomechanics``
        An explicit, non-empty list of what this output does NOT say. It is
        always populated, so a consumer cannot mistake silence for absence of
        evidence.
    """

    escape_triggered: bool
    gf_ap_peak_time_s: Optional[float]
    gf_ap_peak_voltage_mV: Optional[float]
    events: Tuple[MotorOutputEvent, ...]
    ttm_to_dlm_separation_ms: Optional[float]
    ttm_to_dlm_reference: PublishedTtmDlmInterval
    not_triggered_reason: Optional[str]
    incomplete_short_mode_reason: Optional[str] = None
    unsupported_biomechanics: Tuple[str, ...] = (
        "muscle force",
        "joint angle",
        "leg or wing kinematics",
        "wing aerodynamics",
        "takeoff velocity",
        "escape direction",
        "flight dynamics",
        "long-mode takeoff",
        "escape response selection or probability",
    )

    def __post_init__(self) -> None:
        if not self.escape_triggered:
            if self.events:
                raise EscapeBehaviorError(
                    "An untriggered escape must carry no motor-output events."
                )
            if not self.not_triggered_reason:
                raise EscapeBehaviorError(
                    "An untriggered escape must say why it was not triggered."
                )
            if self.gf_ap_peak_time_s is not None:
                raise EscapeBehaviorError(
                    "An untriggered escape must not carry a GF AP peak time."
                )
        else:
            if self.gf_ap_peak_time_s is None or not math.isfinite(
                self.gf_ap_peak_time_s
            ):
                raise EscapeBehaviorError(
                    "A triggered escape must carry a finite GF AP peak time."
                )
            if not self.events:
                raise EscapeBehaviorError(
                    "A triggered escape must carry at least one motor-output "
                    "event."
                )
            if self.not_triggered_reason is not None:
                raise EscapeBehaviorError(
                    "A triggered escape must not carry a not-triggered reason."
                )
        # Ordering: TTM/JUMP before DLM/WING. This is the short-mode signature.
        # A DLM event with NO TTM event is a REAL outcome, not an error: the
        # jump pathway can fail to fire while the wing pathway fires, and that
        # must be reported rather than raised or papered over. But it is not a
        # complete short-mode escape, so it must carry the reason.
        kinds = [event.event_kind for event in self.events]
        if (
            EscapeEventKind.DLM_WING_DEPRESSION in kinds
            and EscapeEventKind.TTM_JUMP not in kinds
        ):
            if not self.incomplete_short_mode_reason:
                raise EscapeBehaviorError(
                    "A wing-depression event without a jump event is not a "
                    "complete short-mode escape, and must say so explicitly."
                )
        elif self.incomplete_short_mode_reason:
            raise EscapeBehaviorError(
                "A complete short-mode escape must not carry an "
                "incompleteness reason."
            )
        if (
            EscapeEventKind.TTM_JUMP in kinds
            and EscapeEventKind.DLM_WING_DEPRESSION in kinds
            and kinds.index(EscapeEventKind.DLM_WING_DEPRESSION)
            < kinds.index(EscapeEventKind.TTM_JUMP)
        ):
            raise EscapeBehaviorError(
                "The TTM jump must precede the DLM wing depression. A source "
                "may be missing, but events are never reordered."
            )
        times = [event.event_time_s for event in self.events]
        if times != sorted(times):
            raise EscapeBehaviorError(
                f"Motor-output events must be in time order, got {times}."
            )
        if not self.unsupported_biomechanics:
            raise EscapeBehaviorError(
                "The unsupported-biomechanics list must stay populated so a "
                "consumer cannot read silence as evidence."
            )

    # -- consumer surface -------------------------------------------------

    @property
    def jump_initiated(self) -> bool:
        """True when the TTM jump event is present."""
        return any(
            event.event_kind is EscapeEventKind.TTM_JUMP
            for event in self.events
        )

    @property
    def wing_depression_initiated(self) -> bool:
        """True when the DLM wing-depression event is present."""
        return any(
            event.event_kind is EscapeEventKind.DLM_WING_DEPRESSION
            for event in self.events
        )

    def event_of(self, kind: EscapeEventKind) -> Optional[MotorOutputEvent]:
        for event in self.events:
            if event.event_kind is kind:
                return event
        return None

    def event_kinds(self) -> Tuple[str, ...]:
        return tuple(event.event_kind.value for event in self.events)

    def behavioral_labels(self) -> Tuple[str, ...]:
        return tuple(event.behavioral_label for event in self.events)

    def to_consumer_dict(self) -> dict:
        """The whole output as plain data for a non-neural consumer."""
        return {
            "escape_triggered": self.escape_triggered,
            "not_triggered_reason": self.not_triggered_reason,
            "incomplete_short_mode_reason": self.incomplete_short_mode_reason,
            "jump_initiated": self.jump_initiated,
            "wing_depression_initiated": self.wing_depression_initiated,
            "events": [event.to_consumer_dict() for event in self.events],
            "ttm_to_dlm_separation_ms": self.ttm_to_dlm_separation_ms,
            "published_ttm_to_dlm_reference_ms": list(
                self.ttm_to_dlm_reference.value_ms
            ),
            "unsupported_biomechanics": list(self.unsupported_biomechanics),
        }

    def summary(self) -> str:
        if not self.escape_triggered:
            return (
                f"NO ESCAPE TRIGGERED. {self.not_triggered_reason} No jump and "
                f"no wing depression are reported."
            )
        lines = [
            "SHORT-MODE ESCAPE BEHAVIOR (GF-mediated).",
            f"  escape triggered by a detected GF action potential peaking at "
            f"{self.gf_ap_peak_time_s * 1e3:.3f} ms.",
        ]
        for event in self.events:
            lines.append(
                f"  {event.event_time_s * 1e3:7.3f} ms  "
                f"{event.behavioral_label} ({event.muscle}, from "
                f"{event.source_neuron}; latency from the GF AP peak "
                f"{event.latency_from_gf_ap_peak_ms:.3f} ms)"
            )
        if self.ttm_to_dlm_separation_ms is not None:
            low, high = self.ttm_to_dlm_reference.value_ms
            inside = self.ttm_to_dlm_reference.contains(
                self.ttm_to_dlm_separation_ms
            )
            lines.append(
                f"  measured TTM->DLM separation (neuron AP peaks): "
                f"{self.ttm_to_dlm_separation_ms:.3f} ms. The published "
                f"experimental reference is {low}-{high} ms, measured at the "
                f"MUSCLE; inside={inside}. That reference is CONTEXT ONLY, is "
                f"never applied as a delay, and the two numbers are not the "
                f"same quantity."
            )
        else:
            lines.append(
                "  TTM->DLM separation: not available, because one of the two "
                "motor neurons did not produce a detected action potential. "
                "The published interval was NOT used to fill the gap."
            )
        if self.incomplete_short_mode_reason:
            lines.append(
                "  INCOMPLETE SHORT-MODE SIGNATURE: "
                + self.incomplete_short_mode_reason
            )
        lines.append(
            "  NOT MODELLED: " + ", ".join(self.unsupported_biomechanics) + "."
        )
        lines.append(_NO_BIOMECHANICS)
        lines.append(_NOT_ALL_ESCAPE_MODES)
        return "\n".join(lines)

    def source_references(self) -> Tuple[str, ...]:
        return (
            SOURCE_ALLEN_GODENSCHWEGE_2010,
            SOURCE_AUGUSTIN_2019_ESCAPE,
            SOURCE_DEVINENI_SCAPLEN_2022,
            SOURCE_CHEONG_2026_MANC,
            SOURCE_VON_REYN_2014_CITED,
        )

    def limitations(self) -> str:
        return (
            f"{_NO_BIOMECHANICS} {_NO_BEHAVIORAL_THRESHOLD} "
            f"{_NOT_ALL_ESCAPE_MODES} {_REFERENCE_NOT_A_DELAY}"
        )


# --- the bridge from the 8J circuit -----------------------------------------

_NO_GF_AP_REASON = (
    "No action potential was detected in the GF, so no escape was triggered. "
    "The only trigger is a detected AP from the existing 3.0D-8A waveform "
    "criterion; there is no threshold, no amplitude criterion and no fallback. "
    "A GF that does not fire produces no motor-output event, and the published "
    "TTM->DLM interval is NOT used to invent one."
)


def escape_behavior_from_circuit(circuit_result) -> EscapeBehaviorOutput:
    """Build a :class:`EscapeBehaviorOutput` from a 3.0D-8I/8J circuit result.

    Consumes the 8J ``response_timings`` -- the SAME detected-AP records, by
    the SAME criterion -- and does not re-detect anything. The GF must have
    produced a detected action potential for any event to be emitted; a
    subthreshold GF response, and a voltage floor crossing, both yield no
    escape.
    """
    from ..motor_output_abstraction import get_motor_output_abstraction
    from .gfs_circuit import LiveCircuitResult

    if not isinstance(circuit_result, LiveCircuitResult):
        raise EscapeBehaviorError(
            "escape_behavior_from_circuit() requires a 3.0D-8I LiveCircuitResult "
            "carrying 3.0D-8J response timings. It does not accept a raw "
            "voltage trace and will not detect a spike itself."
        )

    reference = published_ttm_to_dlm_interval()
    timings = circuit_result.response_timings
    gf = timings.get("GF")
    if gf is None or not gf.ap_detected or gf.ap_peak_time_s is None:
        return EscapeBehaviorOutput(
            escape_triggered=False,
            gf_ap_peak_time_s=None,
            gf_ap_peak_voltage_mV=None,
            events=(),
            ttm_to_dlm_separation_ms=None,
            ttm_to_dlm_reference=reference,
            not_triggered_reason=_NO_GF_AP_REASON,
        )

    motor_output = get_motor_output_abstraction()
    # Muscle identity and NMJ type come from 3.0D-7X, never restated here.
    ttm_output = motor_output.output_for_neuron("TTMn")
    dlm_output = motor_output.output_for_neuron("DLMn")

    events = []
    for neuron_id, kind, output in (
        ("TTMn", EscapeEventKind.TTM_JUMP, ttm_output),
        ("DLMn", EscapeEventKind.DLM_WING_DEPRESSION, dlm_output),
    ):
        timing = timings.get(neuron_id)
        # A motor neuron that did not fire yields NO event. Its time is not
        # synthesised from the published interval.
        if timing is None or not timing.ap_detected or timing.ap_peak_time_s is None:
            continue
        events.append(
            MotorOutputEvent(
                event_kind=kind,
                event_time_s=timing.ap_peak_time_s,
                source_neuron=neuron_id,
                muscle=output.postsynaptic_muscle,
                motor_output_id=output.output_id,
                behavioral_label=_BEHAVIORAL_LABELS[kind],
                timing_basis=EventTimingBasis.NEURAL_AP_PEAK,
                neural_ap_peak_time_s=timing.ap_peak_time_s,
                neural_ap_peak_voltage_mV=timing.ap_peak_voltage_mV,
                latency_from_gf_ap_peak_ms=(
                    timing.ap_peak_time_s - gf.ap_peak_time_s
                ) * 1e3,
            )
        )
    events.sort(key=lambda event: event.event_time_s)

    jump = next(
        (e for e in events if e.event_kind is EscapeEventKind.TTM_JUMP), None
    )
    wing = next(
        (
            e for e in events
            if e.event_kind is EscapeEventKind.DLM_WING_DEPRESSION
        ),
        None,
    )
    separation = (
        (wing.event_time_s - jump.event_time_s) * 1e3
        if jump is not None and wing is not None
        else None
    )

    return EscapeBehaviorOutput(
        escape_triggered=True,
        gf_ap_peak_time_s=gf.ap_peak_time_s,
        gf_ap_peak_voltage_mV=gf.ap_peak_voltage_mV,
        events=tuple(events),
        ttm_to_dlm_separation_ms=separation,
        ttm_to_dlm_reference=reference,
        not_triggered_reason=None,
        incomplete_short_mode_reason=_incomplete_reason(jump, wing, timings),
    )


def _incomplete_reason(jump, wing, timings) -> Optional[str]:
    """Why the short-mode signature is incomplete, or ``None`` if it is not.

    A missing motor-neuron action potential is a real outcome of the circuit and
    is reported as one. The published TTM->DLM interval is NOT used to
    synthesise the absent event or to infer its time.
    """
    missing = []
    if jump is None:
        missing.append(
            "TTMn (leg extension / jump)"
        )
    if wing is None:
        missing.append("DLMn (wing depression)")
    if not missing:
        return None
    detail = []
    for neuron_id, label in (
        ("TTMn", "TTMn (leg extension / jump)"),
        ("DLMn", "DLMn (wing depression)"),
    ):
        timing = timings.get(neuron_id)
        if timing is not None and not timing.ap_detected:
            detail.append(
                f"{label} produced no detected action potential "
                f"(depolarisation {timing.depolarization_mV:.3f} mV against a "
                f"{timing.observation_floor_mV} mV numerical floor)"
            )
        elif timing is None:
            detail.append(f"{label} was not tracked in this run")
    return (
        "NOT A COMPLETE SHORT-MODE ESCAPE: no detected action potential for "
        + ", ".join(missing)
        + ". "
        + "; ".join(detail)
        + ". The published TTM->DLM interval was NOT used to synthesise the "
        "absent event or to infer its time."
    )


def escape_behavior_scope_note() -> str:
    """One statement of what this layer does and refuses to do."""
    return (
        f"{MODEL_NAME_ESCAPE_BEHAVIOR_V0}: turns a detected 3.0D-8J GF action "
        f"potential into two typed short-mode motor-output events, TTM_JUMP and "
        f"DLM_WING_DEPRESSION, reusing the existing 3.0D-8J AP detection and the "
        f"existing 3.0D-7X TTMn->TTM and DLMn->DLM motor-output identities. It "
        f"adds no solver, no spike detector, no muscle, no NMJ and no "
        f"biomechanics. {_NO_BIOMECHANICS} {_NO_BEHAVIORAL_THRESHOLD} "
        f"{_NOT_ALL_ESCAPE_MODES} {_REFERENCE_NOT_A_DELAY} It does not resolve "
        f"the 3.0D-7U gap-junction unit conflict, the 3.0D-8G peak-conductance "
        f"conflict, or the 3.0D-8I sensory-to-biophysical coupling boundary."
    )
