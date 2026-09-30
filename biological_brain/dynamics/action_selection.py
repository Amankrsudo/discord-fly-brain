"""GF action selection: what a GF action potential means BEHAVIOURALLY (3.0D-8N).

WHAT 8N ADDS
-------------
3.0D-8J answers "did the GF fire, and when did its action potential peak".
3.0D-8K answers "which motor-output events followed". Neither of them says what
that means for behaviour, and 8N exists precisely because the answer is NOT
simply "the fly escapes".

8N draws one distinction and holds it open:

    gf_ap_detected                  -- TRUE or FALSE, deterministically
    gf_short_mode_program_activated -- TRUE or FALSE, deterministically
    overall_escape_probability       -- UNRESOLVED, always

The first two are consequences of a detected action potential. The third is not
computed, is not approximated, and is not given a placeholder value. Chai et al.
2025 establish exactly why it cannot be filled in from a GF spike: silencing
the GFs "does not eliminate visually evoked escape take-offs", and flies without
GF activity "only perform longer-duration take-off sequences". The GF selects
the SHORT mode; it is not the only way out.

REUSE, NOT DUPLICATION
----------------------
8N does not invent an action-selection abstraction. 3.0D-7Z already owns one in
``biological_brain/sensorimotor_integration.py``:

    EscapeModeDistinction  gf_short_mode_vs_parallel_long_mode
    MotorPathwayRoute       ttm_jump_route, dlm_flight_route
    GFOutputAbstraction     gf_action_potential_timing
    SensorimotorChain       looming_to_motor_output_chain

7Z's distinction record already carries ``parallel_pathway_role``, and it
already records ``mode_selection_probability = None`` and
``decision_threshold = None``. 8N REFERENCES those records by id and adds only
the runtime evaluation: given a real 8J circuit result and a real 8K behaviour
output, what did the GF's action potential actually establish?

The two 7Z motor routes map one-to-one onto the two 8K events -- ``ttm_jump_route``
onto ``TTM_JUMP`` and ``dlm_flight_route`` onto ``DLM_WING_DEPRESSION`` -- and
8N exposes the mapping rather than restating it. 8K's ``MotorOutputEvent``
objects are held BY REFERENCE in :attr:`GFActionSelectionResult.motor_output`;
nothing is copied, re-timed or re-derived.

THE SEMANTIC CHAIN, AND WHERE IT STOPS
---------------------------------------
    detected GF action potential          (8J, deterministic)
        -> GF-mediated SHORT-MODE program activated   (8N, deterministic)
            -> TTM jump + DLM wing depression events  (8K, referenced)

and then it STOPS. A GF action potential is not an escape. 8N therefore
exposes ``is_an_escape_guarantee`` and ``is_a_probability``, both permanently
False, and ``overall_escape_probability`` permanently None, all enforced by
raising constructors so the guarantee cannot be reintroduced by construction.

NO NUMERICAL DECISION VARIABLE EXISTS, AND NONE IS INVENTED
-----------------------------------------------------------
Chai et al. 2025 classify observed behaviour with a 7 ms boundary between short
and long take-off sequences. That is a MEASUREMENT classification of filmed
flies, not a decision threshold inside a model, and 8N does not adopt it as one.
Their working model is explicitly qualitative: "the GF's looming-size
activation threshold is higher than that of the smaller-axon DNs". They report
escape outcomes only relatively -- "the percentage of successful escape outcomes
for GF-silenced flies was only half of that for GF driver-only control flies" --
and never as an absolute probability.

So 8N introduces no probability value, no action-selection threshold, no
long-mode simulation, no competing descending-neuron model, no aging, starvation
or oxidative-stress parameter, no axo-axonic conductance, no synaptic delay, no
synaptic weight and no membrane threshold. 8N detects nothing: it reads
``ap_detected`` from 3.0D-8J and nothing else.
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from .escape_behavior import (
    EscapeBehaviorOutput,
    EscapeEventKind,
    escape_behavior_from_circuit,
)
from .gfs_circuit import LiveCircuitResult

MODEL_NAME_ACTION_SELECTION_V0 = "action_selection_v0"

#: The 3.0D-7Z record that owns the short-mode / parallel-pathway distinction.
#: 8N references it; it does not restate or redefine it.
ESCAPE_MODE_DISTINCTION_ID = "gf_short_mode_vs_parallel_long_mode"

#: The 3.0D-7Z motor routes, mapped onto the two 3.0D-8K events.
ROUTE_FOR_EVENT_KIND = {
    EscapeEventKind.TTM_JUMP: "ttm_jump_route",
    EscapeEventKind.DLM_WING_DEPRESSION: "dlm_flight_route",
}

#: The only value ``overall_escape_probability_status`` may ever take.
UNRESOLVED = "unresolved"


# --- sources -----------------------------------------------------------------

SOURCE_CHAI_2025_PREDATION = (
    "Chai CM, Morrow CM, Parikh DD, von Reyn CR, Leonardo A, Card GM (2025). "
    "Shorter-duration escapes driven by Drosophila giant interneurons promote "
    "survival during predation. Proc R Soc B 292(2047):20241724. PMID 40425165. "
    "PMCID PMC12115834. doi:10.1098/rspb.2024.1724 . THE SOURCE FOR THE "
    "DISTINCTION 8N EXISTS TO HOLD. States that 'genetic silencing of the "
    "giant fibres (GFs) does not eliminate visually evoked escape take-offs, "
    "although without GF activity, flies only perform longer-duration take-off "
    "sequences'; that 'short mode escapes were almost completely eliminated for "
    "GF>Kir2.1 flies' while 'visually mediated long mode escapes are controlled "
    "by alternative non-GF neural pathways'; and that 'despite the presence of "
    "parallel escape pathways, GF-mediated fast escapes are still strongly "
    "accountable for successful predator evasion and survival'. Its own "
    "conclusion is that 'the role of the Drosophila GFs is not to reduce "
    "reaction time during a predator attack but rather to mediate ACTION "
    "SELECTION'. It reports escape outcomes only RELATIVELY -- 'the percentage "
    "of successful escape outcomes for GF-silenced flies was only half of that "
    "for GF driver-only control flies' -- and states NO absolute escape "
    "probability, NO decision threshold in a model, and NO competing-pathway "
    "simulation. Its 7 ms short/long boundary is a measurement classification of "
    "filmed behaviour and is NOT adopted here as a decision variable."
)

SOURCE_MANC_CHEONG_2026 = (
    "Cheong HSJ, Eichler K, Sturner T, Asinof SK, Champion AS, Marin EC, Oram "
    "TB, Sumathipala M, Venkatasubramanian L, Namiki S, Siwanowicz I, Costa M, "
    "Berg S, Janelia FlyEM Project Team, Jefferis GSXE, Card GM (2026). "
    "Organization of circuits linking descending input to motor output in the "
    "Drosophila Male Adult Nerve Cord connectome. eLife 13:RP96084. PMID "
    "42474298. PMCID PMC13384506. doi:10.7554/eLife.96084 . STRUCTURAL "
    "CONTEXT for the short-mode motor program. Records the GF-to-TTMn and "
    "GF-to-PSI-to-DLMn output architecture, and states that tergotrochanteral "
    "muscle activation 'rapidly depresses the middle legs and jump-starts the "
    "power muscles during escape takeoffs'. It is a connectome and supplies no "
    "action-selection probability, no threshold and no timing parameter used "
    "here."
)

SOURCE_GAITANIDIS_2025_AGING = (
    "Gaitanidis A, Pampanin V, Thiem J, Kalaras G, Huthmacher L, Hurkey S, "
    "Kadas D, Dimitriadou A, Ntogka A, Sanyal S, Consoulas C, Duch C (2025). "
    "The Drosophila escape motor circuit shows differential vulnerability to "
    "aging linked to functional decay. PLoS Biol 23(12):e3003553. PMCID "
    "PMC12707685. PMID 41401182. doi:10.1371/journal.pbio.3003553 . CONTEXT: "
    "the GF receives visual input predominantly from LC4 and LPLC2, and the "
    "established GF->TTM / PSI->DLM short-latency pathway is a different "
    "measurement from visually evoked escape latency, the two remaining "
    "experimentally separable. Supports treating the GF-mediated short-latency "
    "pathway as a distinct, independently measurable route rather than as a "
    "proxy for escape generally. 8N implements nothing from its aging findings."
)

SOURCE_CEBALLOS_2026_AXO_AXONIC_FUTURE = (
    "Ceballos C, Lopez J, Roachford T, Sanchez D, Jara S, Robbins K, Spencer CL, "
    "Murphey R, Pena RFO (2026). The Drosophila connectome reveals axo-axonic "
    "synapses on descending neurons. iScience 29(5):115624. PMID 42063566. "
    "PMCID PMC13126034. doi:10.1016/j.isci.2026.115624 . FUTURE MODULATION "
    "CONTEXT ONLY, AND DELIBERATELY NOT IMPLEMENTED. Identifies an "
    "eight-neuron axo-axonic cohort (AN08B098) whose output is 'nearly "
    "exclusive and among the strongest to the GFs', and shows that "
    "optogenetic activation of that cohort raises the likelihood of GF action "
    "potentials, taking a near-threshold electrical stimulus from roughly 20% "
    "responses to 'nearly 100% of the time'. That is a demonstration that GF "
    "excitability is MODULABLE. It supplies NO axo-axonic conductance, synaptic "
    "weight, synaptic delay or membrane threshold, and its own modelling "
    "limitation is stated: the network 'respects synapse counts but IGNORES "
    "CONDUCTANCE DYNAMICS and neuromodulators influences'. Its generic "
    "simulated nAChR parameters, including a 0 mV reversal sourced to Hagberg "
    "et al., are whole-network values and are NOT Axc->GF measurements and must "
    "not be read back as a Dalpha7 or Axc reversal potential. 8N records the "
    "existence of GF modulation and implements none of it."
)


# --- refusal statements ------------------------------------------------------

_NO_ESCAPE_CERTAINTY = (
    "A DETECTED GF ACTION POTENTIAL IS NOT A GUARANTEE THAT THE FLY ESCAPES, "
    "AND 8N NEVER CLAIMS IT IS. Chai et al. 2025 show that GF silencing 'does "
    "not eliminate visually evoked escape take-offs': without GF activity flies "
    "still perform LONGER-DURATION take-off sequences, and the long mode is "
    "produced by 'alternative non-GF neural pathways'. The GF therefore "
    "selects the short mode within a set of parallel escape pathways; it does "
    "not constitute escape. Their own framing is that the GFs 'mediate ACTION "
    "SELECTION'. Anything that read gf_ap_detected=True as 'the fly escapes' "
    "would be wrong in the direction the literature is explicit about."
)

_NO_PROBABILITY = (
    "OVERALL ESCAPE PROBABILITY IS UNRESOLVED AND IS NEVER COMPUTED. It is "
    "None, always, and the status is 'unresolved', always; both are enforced by "
    "constructors that raise. Chai et al. 2025 report escape outcomes only "
    "RELATIVELY -- 'the percentage of successful escape outcomes for GF-silenced "
    "flies was only half of that for GF driver-only control flies' -- and give "
    "no absolute probability and no calibrated decision variable. 3.0D-7Z's "
    "EscapeModeDistinction already records mode_selection_probability as None "
    "and 8N does not fill it in. Converting a simulated GF spike into a "
    "probability of escape would require a decision model, a parallel-pathway "
    "model and behavioural calibration, none of which this project has."
)

_NO_DECISION_THRESHOLD = (
    "NO ACTION-SELECTION THRESHOLD IS USED. Chai et al. 2025 classify filmed "
    "behaviour with a 7 ms boundary between short and long take-off sequences, "
    "but that is a MEASUREMENT classification of observed flies, not a decision "
    "threshold inside a model, and 8N does not adopt it as one. Their working "
    "model is explicitly qualitative: 'the GF's looming-size activation "
    "threshold is higher than that of the smaller-axon DNs'. 8N uses no "
    "threshold, no boundary, no timing cut-off and no membrane threshold of any "
    "kind."
)

_NO_IMPLEMENTATION = (
    "8N IMPLEMENTS NO MECHANISM. It reads the existing 3.0D-8J ap_detected flag "
    "and the existing 3.0D-8K behaviour output, and adds no spike detector, no "
    "solver, no long-mode model, no competing descending-neuron model, no "
    "axo-axonic conductance, no synaptic delay, no synaptic weight and no "
    "membrane threshold. The 2026 axo-axonic finding is recorded as future "
    "modulation context and nothing more."
)


class ActionSelectionError(Exception):
    """Base class for 3.0D-8N failures."""


# --- the result --------------------------------------------------------------

@dataclass(frozen=True)
class GFActionSelectionResult:
    """What a detected GF action potential establishes, and what it does not.

    THREE QUESTIONS, THREE DIFFERENT ANSWER TYPES
    ---------------------------------------------
    ``gf_ap_detected``
        A detected action potential in the GF, read verbatim from 3.0D-8J's
        ``ap_detected``. Deterministic true or false.

    ``gf_short_mode_program_activated``
        That the GF-mediated SHORT-MODE program was activated. Deterministic
        true or false, and true whenever a GF action potential was detected,
        because the GF is the short-mode pathway: 3.0D-7Z's
        ``EscapeModeDistinction`` records that parallel, GF-INDEPENDENT
        circuitry produces the long mode. The two booleans are kept separate
        because they answer different questions, and they are reported
        separately so that a reader can see they are not the same claim.

    ``overall_escape_probability_status``
        ALWAYS ``"unresolved"``. There is no third value. Escape is not
        determined by a GF spike, because parallel escape pathways exist.

    The 3.0D-8K ``MotorOutputEvent`` objects are held BY REFERENCE in
    ``motor_output``. Their times are not copied, re-derived or adjusted, and
    ``motor_output_event_times_ms`` reads them straight through.
    """

    gf_ap_detected: bool
    gf_short_mode_program_activated: bool
    motor_output_available: bool
    motor_output_complete: bool
    overall_escape_probability_status: str
    selection_basis: str
    escape_mode_distinction_id: str
    activated_route_ids: Tuple[str, ...]
    motor_output_event_kinds: Tuple[str, ...]
    motor_output_event_times_ms: Tuple[float, ...]
    motor_output_event_labels: Tuple[str, ...]
    motor_output: EscapeBehaviorOutput
    gf_ap_peak_time_s: Optional[float]
    parallel_pathway_statement: str
    future_modulation_context: str = ""
    overall_escape_probability: None = None
    is_an_escape_guarantee: bool = False
    is_a_probability: bool = False
    models_long_mode: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.overall_escape_probability is not None:
            raise ActionSelectionError(
                "overall_escape_probability must be None, always. Escape is not "
                "determined by a GF action potential. " + _NO_PROBABILITY
            )
        if self.overall_escape_probability_status != UNRESOLVED:
            raise ActionSelectionError(
                "overall_escape_probability_status must be 'unresolved', "
                f"always. Got {self.overall_escape_probability_status!r}. "
                + _NO_ESCAPE_CERTAINTY
            )
        if self.is_an_escape_guarantee:
            raise ActionSelectionError(
                "A detected GF action potential is never a guarantee of escape. "
                + _NO_ESCAPE_CERTAINTY
            )
        if self.is_a_probability:
            raise ActionSelectionError(
                "8N does not compute probabilities. " + _NO_PROBABILITY
            )
        if self.models_long_mode:
            raise ActionSelectionError(
                "8N does not model the long mode. The long mode is produced by "
                "parallel, GF-INDEPENDENT circuitry that 3.0D-7Z records and "
                "that this project does not implement."
            )
        if self.live_solver_eligible:
            raise ActionSelectionError(
                "8N is a behavioural reading of an existing result, not a "
                "solver input."
            )
        if not isinstance(self.motor_output, EscapeBehaviorOutput):
            raise ActionSelectionError(
                "motor_output must be the existing 3.0D-8K EscapeBehaviorOutput, "
                "held by reference. 8N does not copy or rebuild it."
            )
        if not self.escape_mode_distinction_id:
            raise ActionSelectionError(
                "selection must name the 3.0D-7Z EscapeModeDistinction it "
                "rests on."
            )
        if not self.selection_basis:
            raise ActionSelectionError("selection_basis must be stated.")
        if not self.parallel_pathway_statement:
            raise ActionSelectionError(
                "The parallel-pathway statement must be present, because it is "
                "the reason escape probability is left unresolved."
            )
        # The short-mode program cannot be activated without a GF AP: the GF
        # IS the short-mode pathway, so this would be incoherent.
        if self.gf_short_mode_program_activated and not self.gf_ap_detected:
            raise ActionSelectionError(
                "The GF-mediated short-mode program cannot be activated without "
                "a detected GF action potential."
            )
        # No AP means no motor output, whatever 8K says.
        if not self.gf_ap_detected and (
            self.motor_output_available or self.activated_route_ids
        ):
            raise ActionSelectionError(
                "Without a detected GF action potential there is no GF-mediated "
                "motor output, so motor_output_available must be False."
            )
        # Event references must line up with the 8K object exactly.
        if len(self.motor_output_event_kinds) != len(self.motor_output.events):
            raise ActionSelectionError(
                "Event-kind references must match the 8K event count."
            )
        if self.motor_output_available != bool(self.motor_output.escape_triggered):
            raise ActionSelectionError(
                "motor_output_available must agree with the 8K escape_triggered "
                "flag rather than restating it independently."
            )
        if self.motor_output_complete and not (
            self.motor_output.jump_initiated
            and self.motor_output.wing_depression_initiated
        ):
            raise ActionSelectionError(
                "A complete short-mode motor output requires BOTH the TTM jump "
                "and the DLM wing-depression event."
            )
        if self.gf_ap_peak_time_s is not None and not math.isfinite(
            self.gf_ap_peak_time_s
        ):
            raise ActionSelectionError("gf_ap_peak_time_s must be finite.")

    # -- the distinctions, as API ----------------------------------------

    @property
    def escape_was_guaranteed(self) -> bool:
        """Always False. This is the whole point of 3.0D-8N."""
        return False

    @property
    def is_escape_probability_known(self) -> bool:
        """Always False."""
        return False

    @property
    def short_mode_program_is_complete(self) -> bool:
        """Whether BOTH GF-mediated motor events are present.

        This is about MOTOR OUTPUT completeness, not about escape. A partial
        output stays partial: 8K's ``incomplete_short_mode_reason`` is carried
        through rather than being smoothed away.
        """
        return self.motor_output_complete

    @property
    def motor_output_incompleteness_reason(self) -> Optional[str]:
        """3.0D-8K's own reason the motor output is partial, if it is."""
        return self.motor_output.incomplete_short_mode_reason

    @property
    def jump_initiated(self) -> bool:
        return self.motor_output.jump_initiated

    @property
    def wing_depression_initiated(self) -> bool:
        return self.motor_output.wing_depression_initiated

    def to_consumer_dict(self) -> dict:
        """Consumer-safe view: behavioural concepts only.

        No voltage, no conductance, no compartment and no AP amplitude. The
        escape question is present and answered honestly, with the probability
        explicitly ``None`` and a status of ``"unresolved"`` -- never a number.
        """
        return {
            "kind": "gf_action_selection",
            "gf_action_potential_detected": self.gf_ap_detected,
            "gf_short_mode_program_activated": (
                self.gf_short_mode_program_activated
            ),
            "motor_output_available": self.motor_output_available,
            "short_mode_motor_output_complete": self.motor_output_complete,
            "jump_initiated": self.jump_initiated,
            "wing_depression_initiated": self.wing_depression_initiated,
            "motor_output_events": [
                {
                    "event": kind,
                    "behavioral_label": label,
                    "time_ms": time_ms,
                }
                for kind, label, time_ms in zip(
                    self.motor_output_event_kinds,
                    self.motor_output_event_labels,
                    self.motor_output_event_times_ms,
                )
            ],
            "escape_guaranteed": self.escape_was_guaranteed,
            "overall_escape_probability": self.overall_escape_probability,
            "overall_escape_probability_status": (
                self.overall_escape_probability_status
            ),
            "parallel_pathways_exist": True,
        }

    def summary(self) -> str:
        lines = [
            "GF ACTION SELECTION (3.0D-8N)",
            f"  gf_ap_detected                  : {self.gf_ap_detected}",
            f"  gf_short_mode_program_activated : "
            f"{self.gf_short_mode_program_activated}",
            f"  motor_output_available          : "
            f"{self.motor_output_available}",
            f"  short_mode_motor_output_complete: "
            f"{self.motor_output_complete}",
            f"  overall_escape_probability      : "
            f"{self.overall_escape_probability} "
            f"(status: {self.overall_escape_probability_status})",
            f"  escape_was_guaranteed           : "
            f"{self.escape_was_guaranteed}",
        ]
        if self.motor_output_event_kinds:
            lines.append("  referenced 3.0D-8K motor-output events (by reference):")
            for kind, label, time_ms in zip(
                self.motor_output_event_kinds,
                self.motor_output_event_labels,
                self.motor_output_event_times_ms,
            ):
                lines.append(
                    f"    {time_ms:7.3f} ms  {kind:<22} {label}"
                )
        if self.motor_output_incompleteness_reason:
            lines.append(
                "  MOTOR OUTPUT PARTIAL (not promoted to complete): "
                + self.motor_output_incompleteness_reason
            )
        if self.activated_route_ids:
            lines.append(
                "  3.0D-7Z motor routes engaged: "
                + ", ".join(self.activated_route_ids)
            )
        lines.append(f"  selection basis: {self.selection_basis}")
        lines.append(f"  parallel pathways: {self.parallel_pathway_statement}")
        if self.future_modulation_context:
            lines.append(
                "  future modulation context (NOT implemented): "
                + self.future_modulation_context
            )
        lines.append(_NO_ESCAPE_CERTAINTY)
        lines.append(_NO_PROBABILITY)
        return "\n".join(lines)

    def limitations(self) -> str:
        return (
            f"{_NO_ESCAPE_CERTAINTY} {_NO_PROBABILITY} {_NO_DECISION_THRESHOLD} "
            f"{_NO_IMPLEMENTATION}"
        )

    def source_references(self) -> Tuple[str, ...]:
        return (
            SOURCE_CHAI_2025_PREDATION,
            SOURCE_MANC_CHEONG_2026,
            SOURCE_GAITANIDIS_2025_AGING,
            SOURCE_CEBALLOS_2026_AXO_AXONIC_FUTURE,
        )


# --- the bridge --------------------------------------------------------------

_SELECTION_BASIS_GF_AP = (
    "A detected GF action potential establishes that the GF-MEDIATED SHORT-MODE "
    "program was activated. 3.0D-7Z's EscapeModeDistinction records that the "
    "GF pathway contributes the short mode while PARALLEL, GF-INDEPENDENT "
    "circuitry produces the long mode, so a GF action potential is evidence "
    "about WHICH motor program was selected, not about whether the fly escapes."
)

_SELECTION_BASIS_NO_AP = (
    "No GF action potential was detected, so neither the GF-mediated short-mode "
    "program nor any GF motor output was activated. This is a statement about "
    "the GF pathway only: parallel escape pathways are not represented here and "
    "are not ruled out."
)

_PARALLEL_PATHWAY_STATEMENT = (
    "PARALLEL ESCAPE PATHWAYS EXIST, WHICH IS WHY ESCAPE PROBABILITY IS LEFT "
    "UNRESOLVED. Chai et al. 2025 state that GF silencing 'does not eliminate "
    "visually evoked escape take-offs' and that without GF activity flies 'only "
    "perform longer-duration take-off sequences', with the long mode 'controlled "
    "by alternative non-GF neural pathways'. So a GF action probability cannot "
    "be read as an escape probability, and 3.0D-8N does not compute one."
)

_FUTURE_MODULATION_CONTEXT = (
    "FUTURE MODULATION CONTEXT, NOT IMPLEMENTED. Ceballos et al. 2026 identify "
    "an eight-neuron axo-axonic cohort (AN08B098) whose output is 'nearly "
    "exclusive and among the strongest to the GFs', and show that optogenetic "
    "activation of it raises the likelihood of GF action potentials, taking a "
    "near-threshold stimulus from roughly 20% responses to nearly 100%. That "
    "establishes that GF excitability is MODULABLE. It supplies no axo-axonic "
    "conductance, weight, delay or membrane threshold, and its own network "
    "model explicitly 'ignores conductance dynamics'. Nothing from it is "
    "implemented in 3.0D-8N."
)


def gf_action_selection(
    circuit_result: LiveCircuitResult,
    escape_behavior: Optional[EscapeBehaviorOutput] = None,
) -> GFActionSelectionResult:
    """Read the behavioural meaning of a circuit run, without adding a solver.

    Consumes the 3.0D-8J ``ap_detected`` flag from ``circuit_result`` and the
    3.0D-8K ``EscapeBehaviorOutput``, deriving the latter through 8K's own
    ``escape_behavior_from_circuit`` when it is not supplied. It detects
    nothing, thresholds nothing and simulates nothing.
    """
    if not isinstance(circuit_result, LiveCircuitResult):
        raise ActionSelectionError(
            "gf_action_selection() requires a 3.0D-8I/8J LiveCircuitResult "
            "carrying response timings. It does not accept a raw voltage trace "
            "and will not detect a spike itself."
        )
    if escape_behavior is None:
        escape_behavior = escape_behavior_from_circuit(circuit_result)
    if not isinstance(escape_behavior, EscapeBehaviorOutput):
        raise ActionSelectionError(
            "escape_behavior must be a 3.0D-8K EscapeBehaviorOutput, or None to "
            "derive it from the circuit result via 8K's own function."
        )

    gf_timing = circuit_result.response_timings.get("GF")
    gf_ap_detected = bool(
        gf_timing is not None and gf_timing.ap_detected
    )
    # The GF IS the short-mode pathway, per 3.0D-7Z's EscapeModeDistinction, so
    # a detected GF action potential activates the short-mode program. This is
    # a statement about WHICH program, never about escape.
    short_mode = gf_ap_detected

    events = escape_behavior.events
    kinds = tuple(event.event_kind.value for event in events)
    route_ids = tuple(
        ROUTE_FOR_EVENT_KIND[event.event_kind] for event in events
    )
    complete = bool(
        escape_behavior.jump_initiated
        and escape_behavior.wing_depression_initiated
    )

    return GFActionSelectionResult(
        gf_ap_detected=gf_ap_detected,
        gf_short_mode_program_activated=short_mode,
        motor_output_available=bool(escape_behavior.escape_triggered),
        motor_output_complete=complete,
        overall_escape_probability_status=UNRESOLVED,
        selection_basis=(
            _SELECTION_BASIS_GF_AP if gf_ap_detected
            else _SELECTION_BASIS_NO_AP
        ),
        escape_mode_distinction_id=ESCAPE_MODE_DISTINCTION_ID,
        activated_route_ids=route_ids,
        motor_output_event_kinds=kinds,
        motor_output_event_times_ms=tuple(
            event.event_time_s * 1e3 for event in events
        ),
        motor_output_event_labels=tuple(
            event.behavioral_label for event in events
        ),
        motor_output=escape_behavior,
        gf_ap_peak_time_s=(
            gf_timing.ap_peak_time_s if gf_ap_detected else None
        ),
        parallel_pathway_statement=_PARALLEL_PATHWAY_STATEMENT,
        future_modulation_context=_FUTURE_MODULATION_CONTEXT,
    )


def action_selection_scope_note() -> str:
    """One statement of what 3.0D-8N adds and refuses to add."""
    return (
        f"{MODEL_NAME_ACTION_SELECTION_V0}: reads the 3.0D-8J detected GF action "
        f"potential and the 3.0D-8K motor-output events and states what they "
        f"establish behaviourally, on top of the existing 3.0D-7Z "
        f"EscapeModeDistinction and MotorPathwayRoute records rather than a new "
        f"selection abstraction. It answers THREE questions with three different "
        f"kinds of answer: gf_ap_detected and gf_short_mode_program_activated "
        f"are deterministic booleans, and overall_escape_probability is None "
        f"with status 'unresolved', always. {_NO_ESCAPE_CERTAINTY} "
        f"{_NO_PROBABILITY} {_NO_DECISION_THRESHOLD} {_NO_IMPLEMENTATION} It "
        f"introduces no probability value, no action-selection threshold, no "
        f"long-mode model, no competing descending-neuron model, no "
        f"axo-axonic conductance and no new numerical biological constant, and "
        f"it does not modify 3.0D-8H, 3.0D-8I, 3.0D-8J or 3.0D-8K."
    )
