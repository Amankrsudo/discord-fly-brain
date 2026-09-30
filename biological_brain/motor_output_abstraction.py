"""Motor-output and neuromuscular-junction abstraction (3.0D-7X).

3.0D-7W specified the CENTRAL synapses and the pathway-level validation
targets. This checkpoint specifies the OUTPUT END of the giant fiber system:
the motor neuron to muscle neuromuscular junctions (NMJs), and the fact that
standard GFS electrophysiology measures the muscle, not the synapse.

Why the muscle matters to a circuit model
------------------------------------------
Standard GFS electrophysiology stimulates the GF and records from the TTM and
DLM muscles. The response latency, the refractory period and the high-frequency
following ratio are therefore all measured AT THE MUSCLE. They are end-to-end
GFS output measurements, and they sum everything upstream of the recording
electrode:

    brain/GF stimulus
        -> GF conduction
        -> central synapse(s)
        -> motor neuron propagation
        -> glutamatergic NMJ
        -> muscle response

Nothing in the recorded latency can be attributed exclusively to the NMJ. The
sources say so explicitly: the short TTM latency is attributed to the robust
GF-TTMn electrochemical synapse, the longer DLM latency to the disynaptic
pathway and the central PSI-DLMn chemical synapse, and the long DLM refractory
period to "relatively labile chemical synapses at the PSI-DLMn junction". The
NMJ is one term in a sum the project cannot decompose.

This layer records that measurement boundary. It is METADATA about how an
experiment was performed, not a set of numbers, and nothing here splits a
latency into a central part and a peripheral part.

The two NMJs
------------
TTMn innervates the tergotrochanteral muscle (TTM), the main extensor of the
mesothoracic femur/leg. DLMn innervates the dorsal longitudinal muscles (DLM),
the wing depressors, which are indirect flight muscles. Both NMJs are
GLUTAMATERGIC. That is an experimentally supported IDENTITY and TYPE, and it is
all the project has for either junction.

What the project does NOT have for either NMJ is any quantitative parameter. No
cited source states an NMJ conductance, a glutamate concentration, a release
probability, a vesicle pool, a receptor density, a receptor kinetic constant, a
single-channel conductance, a rise time, a decay time, a reversal potential, a
calcium coupling, a depression or facilitation parameter, or a Q10. Those are
recorded below as required-but-unavailable, and each is structurally empty.

Glutamate identity does not license a receptor subtype. Mejia et al. 2012
report that the GF-TTMn connection is cholinergic and that Dalpha7 subunits are
needed at PSI-DLMn, while explicitly noting that "it is unknown whether Dalpha7
nAChR subunits are present at this synapse" (GF-TTMn). Separately, the classic
Drosophila NMJ receptor literature (Jan and Jan 1976, Schuster 1991, Qin 2005,
Marrus 2004) is largely LARVAL. None of it is imported here: the adult GFS NMJ
is a different preparation and its receptor complement is not established here.

Direct motor-neuron stimulation is an experimental bypass
-----------------------------------------------------------
Moving the stimulating electrodes from the eyes to the thorax activates the
motor neurons directly, bypassing the GF and the entire central circuit. This
is used to test whether the motor neuron and NMJ output remain functional when
upstream GFS transmission is impaired. In shak-B2 mutants and tetanus-toxin
expressing flies, which give NO muscle response to brain stimulation, thoracic
stimulation still produces a muscle response to every stimulus. The sources
conclude from this that the failure is at central synapses and "not the NMJs".

That is a BINARY FUNCTIONAL result: the NMJ works, or it does not. It is not
a transfer function, and no NMJ parameter may be inferred from it. A response
under bypass stimulation says the downstream path is intact; it says nothing
quantitative about how much transmission occurs or how fast.

No muscle model
---------------
The muscle is, at this checkpoint, an experimentally observed OUTPUT ENDPOINT
and nothing more. There is no muscle capacitance, no muscle membrane
resistance, no muscle voltage state, no contractile state, no calcium
dynamics, no muscle force, and no stretch-activation model anywhere in this
module or in the project. A model that recorded muscle voltage would be a new
checkpoint requiring its own evidence, not an extension of this one.

Relationship to 3.0D-7W
-----------------------
7W remains authoritative for the central synaptic abstraction and for every
pathway validation target. This layer REFERENCES the 7W targets by identifier
and does not restate their numbers, so the two cannot drift apart. A latency is
referenced, never copied.

Hard boundaries
---------------
``live_solver_eligible`` is False on every record and on the layer itself, and
cannot be set otherwise. This module:

- does NOT implement a muscle, a muscle membrane, or a contractile element;
- does NOT implement an NMJ current, conductance, or glutamate receptor;
- does NOT implement transmitter release, vesicles, depletion or recovery;
- does NOT add glutamate receptor kinetics, density or conductance;
- does NOT infer an NMJ transfer function from a bypass-stimulation result;
- does NOT split a measured end-to-end latency into NMJ and central parts;
- does NOT duplicate the 3.0D-7W validation targets or their numbers;
- does NOT copy the central PSI->DLMn rise, decay or reversal values onto an
  NMJ;
- does NOT import larval Drosophila NMJ receptor data;
- does NOT implement sensory or looming input;
- does NOT modify the 3.0D-7U gap-junction reconciliation, the 3.0D-7V synaptic
  provenance registry or the 3.0D-7W synaptic abstraction;
- does NOT import, modify or get imported by ``PassiveCableModel``,
  ``PassiveNetwork``, ``PassiveNetworkState`` or ``CompartmentElectrical``, and
  does not change the numerical timestep policy.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from .provenance import ParameterProvenance, ProvenanceRecord
from .synaptic_mechanism_registry import (
    SynapticEvidenceStatus,
    get_synaptic_mechanism_registry,
)
from .synaptic_abstraction import get_synaptic_abstraction


# --- connection types -------------------------------------------------------

CONNECTION_CHEMICAL_NMJ = "chemical_neuromuscular_junction"

# --- neurotransmitter identity ----------------------------------------------

NEUROTRANSMITTER_GLUTAMATE = "glutamate"

# --- measurement boundary labels -------------------------------------------
#
# A muscle response recorded under standard GFS electrophysiology is an
# end-to-end GFS output measurement, never an NMJ measurement.

MEASUREMENT_END_TO_END_GFS_OUTPUT = "end_to_end_GFS_output"


class MeasurementLevel(Enum):
    """What a recorded quantity was measured at, in the preparation."""

    END_TO_END_GFS_OUTPUT = "end_to_end_GFS_output"
    MOTOR_NEURON_BYPASS = "motor_neuron_bypass_output"


_STAGE_BRAIN_STIMULUS = "brain/GF stimulus"
_STAGE_GF_CONDUCTION = "GF conduction"
_STAGE_CENTRAL_SYNAPSE = "central circuit synapse(s)"
_STAGE_MOTOR_NEURON = "motor neuron propagation"
_STAGE_NMJ = "glutamatergic neuromuscular junction"
_STAGE_MUSCLE = "muscle response"


# --- source references ------------------------------------------------------

SOURCE_AUGUSTIN_JOVE_GFS = (
    "Augustin H, Allen MJ, Partridge L (2011). Electrophysiological "
    "recordings from the giant fiber pathway of D. melanogaster. J Vis Exp "
    "(47):e2412. https://pmc.ncbi.nlm.nih.gov/articles/PMC3182647/ . Defines "
    "the standard brain-stimulation, muscle-recording assay; states the "
    "GF-TTM latency of 0.7-1.2 ms, the GF-DLM latency of 1.3-1.7 ms, the TTM "
    "and DLM refractory periods of 1-4 ms and 7-15 ms, 1:1 following at 100 Hz "
    "with DLM failures above 100 Hz, and identifies the NMJs of TTMn-TTM and "
    "DLMn-DLM as chemical (glutamatergic). States NO NMJ parameter."
)

SOURCE_ALLEN_GODENSCHWEGE_MANUAL = (
    "Allen MJ, Godenschwege TA (2010). Electrophysiological recordings from "
    "the Drosophila giant fiber system. In: Drosophila Neurobiology: A "
    "Laboratory Manual (Zhang B, Freeman MR, Waddel S, eds). Cold Spring "
    "Harbor Laboratory Press, pp. 215-224. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC2946074/ . The GFS "
    "electrophysiology protocol and recording convention: brain stimulation "
    "with muscle recording. States NO NMJ parameter."
)

SOURCE_ALLEN_MURPHEY_GF_TTMN = (
    "Allen MJ, Murphey RK (2007). The chemical component of the mixed GF-TTMn "
    "synapse in Drosophila melanogaster uses acetylcholine as its "
    "neurotransmitter. Eur J Neurosci 26(2):439-445. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC1974813/ . Establishes the "
    "CENTRAL GF-TTMn chemical component as cholinergic, and documents direct "
    "thoracic motor-neuron stimulation as a bypass: motor-neuron stimulation "
    "'always resulted in a muscle response to every stimulus' even in flies "
    "giving no response to brain stimulation, which the authors use to "
    "conclude the failure is at CNS synapses 'and not the NMJs'. States NO NMJ "
    "parameter."
)

SOURCE_MEJIA_NANOINJECTION = (
    "Mejia M, Heghinian MD, Mari F, Busch A, Mari F, Godenschwege TA (2012). "
    "Paired nanoinjection and electrophysiology assay to screen for bioactivity "
    "of compounds using the Drosophila melanogaster Giant Fiber System. J Vis "
    "Exp (62):e3597. https://pmc.ncbi.nlm.nih.gov/articles/PMC3466648/ . "
    "States that 'the neuromuscular junctions (NMJ) of the TTMn and the DLMn "
    "with the jump (TTM) and flight muscles (DLM) are glutamatergic', and "
    "uses direct thoracic motor-neuron stimulation to show NMJ function is "
    "unaffected while a Dalpha7 antagonist disrupts the central PSI-DLMn "
    "synapse. Explicitly notes it is unknown whether Dalpha7 subunits are "
    "present at GF-TTMn. States NO NMJ parameter."
)

SOURCE_GODENSCHWEGE_ROBO = (
    "Godenschwege TA, Simpson JH, Shan X, Bashaw GJ, Goodman CS, Murphey RK "
    "(2002). Ectopic expression in the giant fiber system of Drosophila "
    "reveals distinct roles of roundabout (Robo), Robo2, and Robo3 in "
    "dendritic guidance and synaptic connectivity. J Neurosci 22(8):3117-3129. "
    "Reports animals with no response to brain stimulation 'but thoracic "
    "stimulation of these specimen revealed that the neuromuscular junction "
    "response is normal'. States NO NMJ parameter."
)

# --- the project refuses these inferences -----------------------------------

_NOT_LIVE = (
    "3.0D-7X IS A SPECIFICATION CHECKPOINT ONLY. This record is NOT eligible "
    "for the live solver: no NMJ current is implemented, no synaptic "
    "conductance is computed, no muscle is modelled, no compartment is "
    "populated with a muscle or a junction, and the passive backend is "
    "unchanged."
)

_NO_NMJ_NUMBERS = (
    "NO QUANTITATIVE NMJ PARAMETER EXISTS IN ANY PROJECT SOURCE. None of the "
    "cited papers states an NMJ conductance, a glutamate concentration, a "
    "release probability, a vesicle pool, a receptor density, a receptor "
    "kinetic constant, a single-channel conductance, a rise time, a decay "
    "time, a reversal potential, a calcium coupling, a depression or "
    "facilitation parameter, or a Q10 for either NMJ. The recorded muscle "
    "responses are end-to-end GFS output measurements that sum every stage "
    "upstream of the recording electrode, and they cannot be decomposed into "
    "NMJ and central contributions. None of these quantities is created, "
    "estimated, borrowed or fitted here."
)

_MEASUREMENT_BOUNDARY = (
    "A MUSCLE RESPONSE IS AN END-TO-END GFS OUTPUT MEASUREMENT. It is recorded "
    "at the muscle after brain or motor-neuron stimulation, so it sums GF "
    "conduction, every central synapse, motor-neuron propagation, the NMJ, "
    "and the muscle's own response. It is NOT an NMJ measurement, and the "
    "measured latency, refractory period or following ratio cannot be "
    "attributed exclusively to the neuromuscular junction. The cited sources "
    "themselves attribute the short TTM latency to the robust GF-TTMn "
    "electrochemical synapse, the longer DLM latency to the disynaptic pathway "
    "and the central PSI-DLMn chemical synapse, and the long DLM refractory "
    "period to labile chemical synapses at the CENTRAL PSI-DLMn junction."
)

_NO_MUSCLE_MODEL = (
    "THE MUSCLE IS AN OUTPUT ENDPOINT, NOT A MODEL. There is no muscle "
    "capacitance, no muscle membrane resistance, no muscle voltage state, no "
    "contractile state, no muscle calcium dynamics, no muscle force and no "
    "stretch-activation model anywhere in this project. A muscle that could "
    "be integrated would be a separate checkpoint with its own evidence "
    "requirements."
)

_NO_BYPASS_INFERENCE = (
    "A BYPASS-STIMULATION RESULT IS BINARY, NOT QUANTITATIVE. Direct thoracic "
    "or motor-neuron stimulation shows whether the motor neuron and NMJ output "
    "path is FUNCTIONAL. It does not measure a transfer function, a "
    "conductance, a quantal size or a latency, and NO NMJ parameter may be "
    "inferred, fitted or back-calculated from it."
)

_REFERENCES_7W = (
    "This is a REFERENCE to a 3.0D-7W validation target, identified by name. "
    "The 7W abstraction remains the single owner of the pathway validation "
    "numbers; 3.0D-7X does not restate, copy or re-derive any of them."
)

_NO_LARVAL_IMPORT = (
    "LARVAL NMJ RECEPTOR DATA IS NOT IMPORTED. The classic Drosophila NMJ "
    "receptor literature is largely larval, and the adult GFS NMJ is a "
    "different preparation. No larval glutamate receptor subunit, "
    "conductance or kinetic value is carried over to the adult TTM or DLM "
    "NMJ, and no receptor subtype is asserted for either."
)


# --- A/B: motor output specifications --------------------------------------


@dataclass(frozen=True)
class MotorOutputSpec:
    """One motor neuron to muscle neuromuscular junction.

    This record type carries NO numeric field of any kind. It cannot be given
    an NMJ conductance, a rise time, a decay time, a reversal potential, a
    release probability or a receptor parameter through this path, which is
    the point.
    """

    output_id: str
    presynaptic_neuron: str
    postsynaptic_muscle: str
    connection_type: str
    neurotransmitter: str
    biological_role: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    experimentally_supported: bool
    kinetics_available_for_live_solver: bool
    source_references: Tuple[str, ...]
    notes: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Motor output '{self.output_id}' cannot be live-solver "
                f"eligible. 3.0D-7X specifies the output end of the GFS; it "
                f"does not model a muscle or a junction."
            )
        if self.connection_type != CONNECTION_CHEMICAL_NMJ:
            raise ValueError(
                f"Motor output '{self.output_id}' must be a "
                f"'{CONNECTION_CHEMICAL_NMJ}', got "
                f"'{self.connection_type}'."
            )
        if self.neurotransmitter != NEUROTRANSMITTER_GLUTAMATE:
            raise ValueError(
                f"Motor output '{self.output_id}' must be recorded as "
                f"glutamatergic. The sources state no other transmitter for "
                f"the GFS NMJs."
            )
        if self.kinetics_available_for_live_solver:
            raise ValueError(
                f"Motor output '{self.output_id}' must not claim kinetics are "
                f"available. No project source states an NMJ conductance, "
                f"kinetic constant or time course."
            )
        if not self.experimentally_supported:
            raise ValueError(
                f"Motor output '{self.output_id}' must state its "
                f"experimental support; this layer records experimentally "
                f"supported NMJ identities and types."
            )
        if self.evidence_status is not (
            SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED
        ):
            raise ValueError(
                f"Motor output '{self.output_id}' must carry the status "
                f"'experimentally_constrained': the glutamatergic identity and "
                f"type are direct experimental observations."
            )
        if not self.source_references:
            raise ValueError(
                f"Motor output '{self.output_id}' must carry at least one "
                f"source reference."
            )
        if not self.biological_role:
            raise ValueError(
                f"Motor output '{self.output_id}' must state its biological "
                f"role."
            )

    @property
    def has_quantitative_value(self) -> bool:
        """Always False: the record type carries no number."""
        return False

    @property
    def is_nmj(self) -> bool:
        return self.connection_type == CONNECTION_CHEMICAL_NMJ

    def limitations(self) -> str:
        return (
            f"EXPERIMENTALLY SUPPORTED NMJ IDENTITY AND TYPE. {self.notes} "
            f"{_NO_NMJ_NUMBERS} {_MEASUREMENT_BOUNDARY} {_NO_MUSCLE_MODEL} "
            f"{_NO_LARVAL_IMPORT} {_NOT_LIVE}"
        )


# --- C: output measurement boundary ----------------------------------------


@dataclass(frozen=True)
class OutputMeasurementBoundary:
    """What a recorded muscle response actually is, and what it is not.

    ``measurement_stages`` names the sequence a standard GFS recording
    traverses, from the stimulating electrode to the recording electrode. It is
    a list of STAGE NAMES, not a chain of simulated components, and it carries
    no timing, no weighting and no per-stage contribution.
    """

    measurement_id: str
    recorded_observable: str
    recording_site: str
    stimulus_site: str
    measurement_level: str
    attributable_to_nmj_exclusively: bool
    measurement_stages: Tuple[str, ...]
    source_references: Tuple[str, ...]
    notes: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Measurement boundary '{self.measurement_id}' cannot be "
                f"live-solver eligible."
            )
        if self.attributable_to_nmj_exclusively:
            raise ValueError(
                f"Measurement boundary '{self.measurement_id}' must not be "
                f"attributable to the NMJ exclusively. A muscle recording "
                f"sums every stage upstream of the recording electrode."
            )
        if self.measurement_level is not (
            MeasurementLevel.END_TO_END_GFS_OUTPUT
        ):
            raise ValueError(
                f"Measurement boundary '{self.measurement_id}' must be "
                f"recorded at the end-to-end GFS output level."
            )
        required = (
            _STAGE_BRAIN_STIMULUS,
            _STAGE_GF_CONDUCTION,
            _STAGE_CENTRAL_SYNAPSE,
            _STAGE_MOTOR_NEURON,
            _STAGE_NMJ,
            _STAGE_MUSCLE,
        )
        for stage in required:
            if stage not in self.measurement_stages:
                raise ValueError(
                    f"Measurement boundary '{self.measurement_id}' must name "
                    f"the stage '{stage}'."
                )
        # The stages are names, never numbers.
        for stage in self.measurement_stages:
            if not isinstance(stage, str):
                raise ValueError(
                    f"Measurement boundary '{self.measurement_id}' stages "
                    f"must be stage NAMES, not simulated components."
                )

    @property
    def is_end_to_end(self) -> bool:
        return True

    @property
    def is_nmj_measurement(self) -> bool:
        """Always False."""
        return False

    @property
    def stage_count(self) -> int:
        return len(self.measurement_stages)

    def limitations(self) -> str:
        return (
            f"{self.notes} {_MEASUREMENT_BOUNDARY} {_NO_MUSCLE_MODEL} "
            f"{_NOT_LIVE}"
        )


# --- D: direct motor-neuron stimulation bypass -----------------------------


@dataclass(frozen=True)
class BypassConditionSpec:
    """An experimental condition that bypasses part of the circuit.

    Recorded as an EXPERIMENTAL CONDITION only. It is not a simulator input,
    not a stimulation protocol the project can drive, and not a source of
    parameters. ``quantitative_nmj_parameter_derivable`` is always False.
    """

    bypass_id: str
    description: str
    stimulation_site: str
    bypassed_stages: Tuple[str, ...]
    purpose: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    measurement_level: str
    quantitative_nmj_parameter_derivable: bool
    source_references: Tuple[str, ...]
    notes: str
    is_simulator_input: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Bypass condition '{self.bypass_id}' cannot be live-solver "
                f"eligible."
            )
        if self.is_simulator_input:
            raise ValueError(
                f"Bypass condition '{self.bypass_id}' must not be a simulator "
                f"input at 3.0D-7X. It is recorded as an experimental "
                f"condition, not as a drive the project can apply."
            )
        if self.quantitative_nmj_parameter_derivable:
            raise ValueError(
                f"Bypass condition '{self.bypass_id}' must not permit a "
                f"quantitative NMJ parameter to be derived. A bypass result "
                f"shows the output path is functional; it measures no "
                f"transfer function."
            )
        if self.measurement_level is not (
            MeasurementLevel.MOTOR_NEURON_BYPASS
        ):
            raise ValueError(
                f"Bypass condition '{self.bypass_id}' must be recorded at "
                f"the motor-neuron bypass level."
            )
        if not self.bypassed_stages:
            raise ValueError(
                f"Bypass condition '{self.bypass_id}' must name what it "
                f"bypasses."
            )

    @property
    def yields_nmj_parameter(self) -> None:
        """Always None: no NMJ parameter is derivable from a bypass result."""
        return None

    def limitations(self) -> str:
        return (
            f"EXPERIMENTAL BYPASS CONDITION, NOT A SIMULATOR INPUT. "
            f"{self.notes} {_NO_BYPASS_INFERENCE} {_NOT_LIVE}"
        )


# --- E: validation target linkage ------------------------------------------


@dataclass(frozen=True)
class OutputValidationLink:
    """A pointer to a 3.0D-7W validation target. Never a copy of it.

    This record type has NO numeric field. The value, unit and range of the
    linked target live in 7W and are not restated here, so the two layers
    cannot drift apart and a latency can never be re-typed as an NMJ
    parameter.
    """

    link_id: str
    linked_7w_target: str
    linked_7w_layer: str
    recorded_observable: str
    classification: str
    is_nmj_parameter: bool
    measurement_level: str
    source_references: Tuple[str, ...]
    notes: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Validation link '{self.link_id}' cannot be live-solver "
                f"eligible."
            )
        if self.is_nmj_parameter:
            raise ValueError(
                f"Validation link '{self.link_id}' must NOT be an NMJ "
                f"parameter. Every linked target is a pathway or output "
                f"measurement that happens to be recorded at a muscle."
            )
        if self.classification != MEASUREMENT_END_TO_END_GFS_OUTPUT:
            raise ValueError(
                f"Validation link '{self.link_id}' must be classified as "
                f"'{MEASUREMENT_END_TO_END_GFS_OUTPUT}'."
            )
        if self.linked_7w_layer != "3.0D-7W":
            raise ValueError(
                f"Validation link '{self.link_id}' must reference 3.0D-7W, "
                f"which owns the target."
            )
        if not self.notes:
            raise ValueError(
                f"Validation link '{self.link_id}' must state why the linked "
                f"target is not an NMJ parameter."
            )

    @property
    def carries_a_value(self) -> bool:
        """Always False: the number lives in 7W and is not copied here."""
        return False

    def limitations(self) -> str:
        return (
            f"{self.notes} {_MEASUREMENT_BOUNDARY} {_REFERENCES_7W} "
            f"{_NOT_LIVE}"
        )


# --- B: unavailable NMJ quantities ------------------------------------------


@dataclass(frozen=True)
class UnavailableNmjQuantity:
    """An NMJ quantity a mechanistic junction would need, and does not have.

    ``value`` is structurally None and cannot be set. Where an equivalent
    exclusion already exists in 3.0D-7V or 3.0D-7W, it is LINKED rather than
    duplicated.
    """

    quantity_id: str
    quantity_kind: str
    applies_to: str
    why_required: str
    why_unavailable: str
    linked_7v_excluded_name: Optional[str]
    linked_7w_requirement_id: Optional[str]
    must_not_be_inherited_from: Optional[str]
    value: None = None
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Unavailable NMJ quantity '{self.quantity_id}' cannot be "
                f"live-solver eligible: it has no value to supply."
            )
        if self.value is not None:
            raise ValueError(
                f"Unavailable NMJ quantity '{self.quantity_id}' must remain "
                f"unavailable. No project source states it, so no value may "
                f"be populated."
            )
        if not self.why_required or not self.why_unavailable:
            raise ValueError(
                f"Unavailable NMJ quantity '{self.quantity_id}' must state "
                f"both why a mechanistic NMJ would need it and why it is "
                f"unavailable."
            )

    @property
    def value_is_populated(self) -> bool:
        """Always False."""
        return False

    def limitations(self) -> str:
        parts = [
            f"REQUIRED BY A MECHANISTIC NMJ, CURRENTLY UNAVAILABLE. "
            f"{self.why_required} {self.why_unavailable} This quantity stays "
            f"empty. It is NOT filled with a generic Drosophila value, with a "
            f"larval NMJ value, with a value borrowed from another "
            f"preparation, or with a value back-calculated from a measured "
            f"latency or a bypass-stimulation result."
        ]
        if self.must_not_be_inherited_from:
            parts.append(
                f"It is specifically NOT inherited from "
                f"{self.must_not_be_inherited_from}."
            )
        parts.append(_NOT_LIVE)
        return " ".join(parts)


# --- the layer -------------------------------------------------------------


@dataclass(frozen=True)
class MotorOutputAbstraction:
    """The GFS output end, specified. NOT modelled.

    Assigns nothing, populates nothing, connects nothing. No compartment, no
    ``CableParameters``, no ``CompartmentElectrical`` and no solver input is
    populated from this layer, and no solver module imports it.
    """

    name: str
    source: str
    model_id: str
    model_citation: str
    motor_outputs: Tuple[MotorOutputSpec, ...]
    measurement_boundaries: Tuple[OutputMeasurementBoundary, ...]
    bypass_conditions: Tuple[BypassConditionSpec, ...]
    validation_links: Tuple[OutputValidationLink, ...]
    unavailable_nmj_quantities: Tuple[UnavailableNmjQuantity, ...]
    referenced_7w_targets: Tuple[str, ...]
    scope_note: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                "The motor-output abstraction cannot be live-solver eligible. "
                "It is a specification of the GFS output end, not a model of "
                "it."
            )
        if not self.motor_outputs:
            raise ValueError(
                "The motor-output abstraction must specify at least one "
                "motor output."
            )

    # -- lookup ------------------------------------------------------------

    def output(self, output_id: str) -> MotorOutputSpec:
        for record in self.motor_outputs:
            if record.output_id == output_id:
                return record
        raise KeyError(f"Motor output '{output_id}' not in abstraction")

    def output_ids(self) -> Tuple[str, ...]:
        return tuple(record.output_id for record in self.motor_outputs)

    def output_for_muscle(self, muscle: str) -> MotorOutputSpec:
        for record in self.motor_outputs:
            if record.postsynaptic_muscle == muscle:
                return record
        raise KeyError(f"No motor output recorded for muscle '{muscle}'")

    def output_for_neuron(self, neuron: str) -> MotorOutputSpec:
        for record in self.motor_outputs:
            if record.presynaptic_neuron == neuron:
                return record
        raise KeyError(f"No motor output recorded for neuron '{neuron}'")

    def boundary(self, measurement_id: str) -> OutputMeasurementBoundary:
        for record in self.measurement_boundaries:
            if record.measurement_id == measurement_id:
                return record
        raise KeyError(f"Measurement boundary '{measurement_id}' not in abstraction")

    def bypass(self, bypass_id: str) -> BypassConditionSpec:
        for record in self.bypass_conditions:
            if record.bypass_id == bypass_id:
                return record
        raise KeyError(f"Bypass condition '{bypass_id}' not in abstraction")

    def link(self, link_id: str) -> OutputValidationLink:
        for record in self.validation_links:
            if record.link_id == link_id:
                return record
        raise KeyError(f"Validation link '{link_id}' not in abstraction")

    def link_ids(self) -> Tuple[str, ...]:
        return tuple(record.link_id for record in self.validation_links)

    def unavailable(self, quantity_id: str) -> UnavailableNmjQuantity:
        for record in self.unavailable_nmj_quantities:
            if record.quantity_id == quantity_id:
                return record
        raise KeyError(
            f"Unavailable NMJ quantity '{quantity_id}' not in abstraction"
        )

    def unavailable_ids(self) -> Tuple[str, ...]:
        return tuple(
            record.quantity_id for record in self.unavailable_nmj_quantities
        )

    def links_to_target(self, target_id: str) -> Tuple[str, ...]:
        return tuple(
            record.link_id
            for record in self.validation_links
            if record.linked_7w_target == target_id
        )

    # -- boundary ----------------------------------------------------------

    def any_live_solver_eligible(self) -> bool:
        """Always False in 3.0D-7X."""
        return any(
            record.live_solver_eligible
            for record in (
                *self.motor_outputs,
                *self.measurement_boundaries,
                *self.bypass_conditions,
                *self.validation_links,
                *self.unavailable_nmj_quantities,
            )
        )

    def any_populated_nmj_quantity(self) -> bool:
        """Always False: every unavailable NMJ quantity stays empty."""
        return any(
            record.value_is_populated
            for record in self.unavailable_nmj_quantities
        )

    def any_nmj_kinetics(self) -> bool:
        """Always False in 3.0D-7X: no NMJ kinetics exist."""
        return any(
            record.kinetics_available_for_live_solver
            for record in self.motor_outputs
        )

    def any_nmj_quantitative_value(self) -> bool:
        """Always False: the output records carry no number."""
        return any(record.has_quantitative_value for record in self.motor_outputs)

    def any_nmj_measurement(self) -> bool:
        """Always False: no recorded quantity is an NMJ measurement."""
        return any(
            record.is_nmj_measurement
            for record in self.measurement_boundaries
        ) or any(record.is_nmj_parameter for record in self.validation_links)

    def any_nmj_exclusive_attribution(self) -> bool:
        """Always False: no measurement is attributed to the NMJ alone."""
        return any(
            record.attributable_to_nmj_exclusively
            for record in self.measurement_boundaries
        )

    def any_simulator_input(self) -> bool:
        """Always False: the bypass condition is not drivable."""
        return any(record.is_simulator_input for record in self.bypass_conditions)

    def any_derivable_nmj_parameter(self) -> bool:
        """Always False: a bypass result yields no NMJ parameter."""
        return any(
            record.quantitative_nmj_parameter_derivable
            for record in self.bypass_conditions
        )

    def any_linked_value(self) -> bool:
        """Always False: links carry no number of their own."""
        return any(record.carries_a_value for record in self.validation_links)

    def glutamatergic_outputs(self) -> Tuple[str, ...]:
        return tuple(
            record.output_id
            for record in self.motor_outputs
            if record.neurotransmitter == NEUROTRANSMITTER_GLUTAMATE
        )

    def verifies_against_7w(self) -> None:
        """Assert this layer agrees with the 7W targets it references.

        Every linked target must exist in 7W, and the linked value must still
        be a pathway or output observation rather than an NMJ parameter. This
        changes nothing; it fails loudly if the layers drift apart.
        """
        seven_w = get_synaptic_abstraction()
        by_id: Dict[str, object] = {}
        for record in seven_w.validation_targets:
            by_id[record.target_id] = record
        for record in seven_w.following_targets:
            by_id[record.target_id] = record
        for record in self.validation_links:
            target = by_id.get(record.linked_7w_target)
            if target is None:
                raise ValueError(
                    f"Validation link '{record.link_id}' references 7W target "
                    f"'{record.linked_7w_target}', which does not exist."
                )
            if getattr(target, "is_intrinsic_neuron_parameter", False):
                raise ValueError(
                    f"Validation link '{record.link_id}' references 7W target "
                    f"'{record.linked_7w_target}', which has been marked an "
                    f"intrinsic neuron parameter."
                )
        missing = set(self.referenced_7w_targets) - set(by_id)
        if missing:
            raise ValueError(
                f"Referenced 7W targets do not exist: {sorted(missing)}"
            )


# --- construction -----------------------------------------------------------


def _motor_outputs() -> Tuple[MotorOutputSpec, ...]:
    return (
        MotorOutputSpec(
            output_id="TTMn_TTM",
            presynaptic_neuron="TTMn",
            postsynaptic_muscle="TTM",
            connection_type=CONNECTION_CHEMICAL_NMJ,
            neurotransmitter=NEUROTRANSMITTER_GLUTAMATE,
            biological_role=(
                "The TTMn drives the tergotrochanteral muscle, the main "
                "extensor of the mesothoracic femur and leg. Its activation is "
                "what launches the fly: the monosynaptic GF-TTMn pathway is "
                "what extends the femur and propels the fly off the ground "
                "before the disynaptic DLM pathway contracts."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            experimentally_supported=True,
            kinetics_available_for_live_solver=False,
            source_references=(
                SOURCE_AUGUSTIN_JOVE_GFS, SOURCE_MEJIA_NANOINJECTION,
                SOURCE_ALLEN_GODENSCHWEGE_MANUAL,
            ),
            notes=(
                "CHEMICAL NEUROMUSCULAR JUNCTION, GLUTAMATERGIC, EXPERIMENTALLY "
                "SUPPORTED. Augustin et al. 2011 identify the TTMn-TTM NMJ as "
                "chemical (glutamatergic); Mejia et al. 2012 state that 'the "
                "neuromuscular junctions (NMJ) of the TTMn and the DLMn with "
                "the jump (TTM) and flight muscles (DLM) are glutamatergic'. "
                "The identity and type are experimentally supported. NO "
                "quantitative NMJ parameter is stated by any source, and the "
                "muscle is recorded, not modelled. Note that the 0.1 ms rise, "
                "1.0 ms decay and 0 mV reversal recorded in 3.0D-7V belong to "
                "the CENTRAL PSI->DLMn synapse and are NOT properties of this "
                "junction."
            ),
        ),
        MotorOutputSpec(
            output_id="DLMn_DLM",
            presynaptic_neuron="DLMn",
            postsynaptic_muscle="DLM",
            connection_type=CONNECTION_CHEMICAL_NMJ,
            neurotransmitter=NEUROTRANSMITTER_GLUTAMATE,
            biological_role=(
                "DLMn motor neurons innervate the dorsal longitudinal "
                "muscles, the wing depressors, which are indirect flight "
                "muscles that move the wings indirectly by distorting the "
                "thoracic cuticle. Their di-synaptic activation via PSI is "
                "delayed relative to the monosynaptic TTM activation so that "
                "the TTM can first extend the femur."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            experimentally_supported=True,
            kinetics_available_for_live_solver=False,
            source_references=(
                SOURCE_AUGUSTIN_JOVE_GFS, SOURCE_MEJIA_NANOINJECTION,
                SOURCE_ALLEN_GODENSCHWEGE_MANUAL,
            ),
            notes=(
                "CHEMICAL NEUROMUSCULAR JUNCTION, GLUTAMATERGIC, EXPERIMENTALLY "
                "SUPPORTED. The DLMn->DLM NMJ is the terminal output of the "
                "DISYNAPTIC branch, reached through the central, Dalpha7-"
                "dependent, cholinergic PSI->DLMn synapse. The NMJ itself is "
                "glutamatergic and distinct from that central cholinergic "
                "step: the two must not be conflated. NO source states a "
                "quantitative NMJ parameter, and the reported long DLM "
                "refractory period is attributed by the sources to LABILE "
                "CHEMICAL SYNAPSES AT THE CENTRAL PSI-DLMn JUNCTION, not to "
                "this NMJ and not to this muscle."
            ),
        ),
    )


def _measurement_boundaries() -> Tuple[OutputMeasurementBoundary, ...]:
    stages = (
        _STAGE_BRAIN_STIMULUS,
        _STAGE_GF_CONDUCTION,
        _STAGE_CENTRAL_SYNAPSE,
        _STAGE_MOTOR_NEURON,
        _STAGE_NMJ,
        _STAGE_MUSCLE,
    )
    return (
        OutputMeasurementBoundary(
            measurement_id="ttm_muscle_response",
            recorded_observable=(
                "Postsynaptic potential recorded from the TTM muscle after a "
                "supra-threshold brain stimulus."
            ),
            recording_site="TTM muscle fibre (glass microelectrode)",
            stimulus_site="brain, via electrodes passed through the eyes",
            measurement_level=MeasurementLevel.END_TO_END_GFS_OUTPUT,
            attributable_to_nmj_exclusively=False,
            measurement_stages=stages,
            source_references=(
                SOURCE_AUGUSTIN_JOVE_GFS, SOURCE_ALLEN_GODENSCHWEGE_MANUAL,
            ),
            notes=(
                "END-TO-END GFS OUTPUT. A TTM recording after brain "
                "stimulation sums GF conduction, the monosynaptic "
                "electro-chemical GF-TTMn central synapse, TTMn propagation, "
                "the TTMn->TTM glutamatergic NMJ, and the muscle's own "
                "response. The sources attribute the very short TTM latency to "
                "the robust GF-TTMn electrochemical synapse, which is a "
                "CENTRAL contribution and is a direct reason the measured "
                "latency cannot be read as an NMJ latency. TTM traces also "
                "show more amplitude and shape variability than DLM traces "
                "because the TTM fibres are smaller; the reported latency is "
                "stated to be unaffected by this."
            ),
        ),
        OutputMeasurementBoundary(
            measurement_id="dlm_muscle_response",
            recorded_observable=(
                "Postsynaptic potential recorded from a DLM muscle fibre "
                "after a supra-threshold brain stimulus."
            ),
            recording_site="DLM muscle fibre 45a or 45b (glass microelectrode)",
            stimulus_site="brain, via electrodes passed through the eyes",
            measurement_level=MeasurementLevel.END_TO_END_GFS_OUTPUT,
            attributable_to_nmj_exclusively=False,
            measurement_stages=stages,
            source_references=(
                SOURCE_AUGUSTIN_JOVE_GFS, SOURCE_ALLEN_GODENSCHWEGE_MANUAL,
            ),
            notes=(
                "END-TO-END GFS OUTPUT. A DLM recording after brain "
                "stimulation sums GF conduction, the electro-chemical GF->PSI "
                "central synapse, the central cholinergic PSI->DLMn synapse, "
                "DLMn propagation, the DLMn->DLM glutamatergic NMJ, and the "
                "muscle's own response. This is the DISYNAPTIC branch, so the "
                "recorded latency spans TWO central synapses in addition to "
                "the NMJ. The sources attribute the longer DLM latency to the "
                "disynaptic pathway and the central chemical PSI-DLMn synapse, "
                "which is a direct reason the measured latency cannot be read "
                "as an NMJ latency."
            ),
        ),
    )


def _bypass_conditions() -> Tuple[BypassConditionSpec, ...]:
    return (
        BypassConditionSpec(
            bypass_id="direct_motor_neuron_stimulation",
            description=(
                "Direct stimulation of the motor neurons by moving the "
                "stimulating electrodes out of the eyes and onto the anterior "
                "thorax, down into the fused thoracic ganglia."
            ),
            stimulation_site="thoracic ganglia, via the anterior thorax",
            bypassed_stages=(
                _STAGE_BRAIN_STIMULUS,
                _STAGE_GF_CONDUCTION,
                _STAGE_CENTRAL_SYNAPSE,
            ),
            purpose=(
                "To activate the motor neurons directly, bypassing the GF and "
                "the entire central circuit, and thereby to assess whether the "
                "motor neuron and NMJ output remain functional when upstream "
                "GFS transmission is impaired. This is what allows a central "
                "defect to be distinguished from a peripheral one."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            quantitative_nmj_parameter_derivable=False,
            measurement_level=MeasurementLevel.MOTOR_NEURON_BYPASS,
            source_references=(
                SOURCE_ALLEN_MURPHEY_GF_TTMN, SOURCE_MEJIA_NANOINJECTION,
                SOURCE_AUGUSTIN_JOVE_GFS, SOURCE_GODENSCHWEGE_ROBO,
            ),
            notes=(
                "EXPERIMENTAL BYPASS CONDITION, NOT A SIMULATOR INPUT. "
                "Allen and Murphey 2007 moved the electrodes to the thoracic "
                "ganglia and report that motor-neuron stimulation 'always "
                "resulted in a muscle response to every stimulus', including "
                "in flies that gave NO response to brain stimulation, and use "
                "this to conclude the failure is at CNS synapses 'and not the "
                "NMJs'. Mejia et al. 2012 use the same bypass to show NMJ "
                "function is unaffected while a Dalpha7 antagonist disrupts "
                "the central PSI-DLMn synapse. Augustin et al. 2011 state that "
                "a shakB mutant response 'can be restored by stimulating "
                "thoracic ganglia directly, demonstrating that the delayed "
                "effect is not due to disrupted neuromuscular transmission'. "
                "3.0D-7X records this as an EXPERIMENTAL CONDITION. It is NOT "
                "implemented as a simulator input, and NO NMJ parameter is "
                "derived from it."
            ),
        ),
    )


def _validation_links() -> Tuple[OutputValidationLink, ...]:
    return (
        OutputValidationLink(
            link_id="ttm_latency_output_measurement",
            linked_7w_target="gf_to_ttm_latency",
            linked_7w_layer="3.0D-7W",
            recorded_observable="GF-TTM response latency",
            classification=MEASUREMENT_END_TO_END_GFS_OUTPUT,
            is_nmj_parameter=False,
            measurement_level=MeasurementLevel.END_TO_END_GFS_OUTPUT,
            source_references=(SOURCE_AUGUSTIN_JOVE_GFS,),
            notes=(
                "REFERENCED, NOT DUPLICATED. The 0.7-1.2 ms range is owned by "
                "the 3.0D-7W target 'gf_to_ttm_latency' and is NOT restated "
                "here. It is recorded at the TTM muscle after brain "
                "stimulation, so it is an END-TO-END GFS OUTPUT MEASUREMENT "
                "and NOT an NMJ intrinsic parameter. It is explicitly NOT an "
                "isolated TTMn->TTM NMJ latency."
            ),
        ),
        OutputValidationLink(
            link_id="dlm_latency_output_measurement",
            linked_7w_target="gf_to_dlm_latency",
            linked_7w_layer="3.0D-7W",
            recorded_observable="GF-DLM response latency",
            classification=MEASUREMENT_END_TO_END_GFS_OUTPUT,
            is_nmj_parameter=False,
            measurement_level=MeasurementLevel.END_TO_END_GFS_OUTPUT,
            source_references=(SOURCE_AUGUSTIN_JOVE_GFS,),
            notes=(
                "REFERENCED, NOT DUPLICATED. The 1.3-1.7 ms range is owned by "
                "the 3.0D-7W target 'gf_to_dlm_latency' and is NOT restated "
                "here. It is recorded at the DLM muscle after brain "
                "stimulation, so it is an END-TO-END GFS OUTPUT MEASUREMENT "
                "and NOT an NMJ intrinsic parameter. It spans two central "
                "synapses in addition to the NMJ, and is explicitly NOT an "
                "isolated DLMn->DLM NMJ latency."
            ),
        ),
        OutputValidationLink(
            link_id="ttm_following_output_measurement",
            linked_7w_target="ttm_high_frequency_following",
            linked_7w_layer="3.0D-7W",
            recorded_observable="TTM frequency of following to stimulus trains",
            classification=MEASUREMENT_END_TO_END_GFS_OUTPUT,
            is_nmj_parameter=False,
            measurement_level=MeasurementLevel.END_TO_END_GFS_OUTPUT,
            source_references=(SOURCE_AUGUSTIN_JOVE_GFS,),
            notes=(
                "REFERENCED, NOT DUPLICATED. The observed following "
                "frequencies are owned by the 3.0D-7W target "
                "'ttm_high_frequency_following' and are NOT restated here. "
                "The ratio of successful muscle responses to delivered "
                "stimuli is measured at the TTM, so it is an END-TO-END GFS "
                "OUTPUT MEASUREMENT, not a property of the NMJ."
            ),
        ),
        OutputValidationLink(
            link_id="dlm_following_output_measurement",
            linked_7w_target="dlm_high_frequency_following",
            linked_7w_layer="3.0D-7W",
            recorded_observable="DLM frequency of following to stimulus trains",
            classification=MEASUREMENT_END_TO_END_GFS_OUTPUT,
            is_nmj_parameter=False,
            measurement_level=MeasurementLevel.END_TO_END_GFS_OUTPUT,
            source_references=(
                SOURCE_AUGUSTIN_JOVE_GFS, SOURCE_MEJIA_NANOINJECTION,
            ),
            notes=(
                "REFERENCED, NOT DUPLICATED. The observed following "
                "frequencies and the failure onset are owned by the 3.0D-7W "
                "target 'dlm_high_frequency_following' and are NOT restated "
                "here. The ratio is measured at the DLM, so it is an "
                "END-TO-END GFS OUTPUT MEASUREMENT, not a property of the "
                "NMJ. Where the DLM fails to follow above 100 Hz, the sources "
                "attribute the failure to the intermediary CENTRAL chemical "
                "PSI->DLMn synapse not recovering in time, NOT to the "
                "glutamatergic NMJ; Mejia et al. 2012 independently show that "
                "the DLM follows 1:1 under direct motor-neuron stimulation "
                "while the central synapse is blocked."
            ),
        ),
        OutputValidationLink(
            link_id="ttm_refractory_output_measurement",
            linked_7w_target="ttm_refractory_period",
            linked_7w_layer="3.0D-7W",
            recorded_observable=(
                "Minimal interval between twin stimuli still producing two "
                "TTM muscle responses"
            ),
            classification=MEASUREMENT_END_TO_END_GFS_OUTPUT,
            is_nmj_parameter=False,
            measurement_level=MeasurementLevel.END_TO_END_GFS_OUTPUT,
            source_references=(SOURCE_AUGUSTIN_JOVE_GFS,),
            notes=(
                "REFERENCED, NOT DUPLICATED, AND NOT AN NMJ PARAMETER. The "
                "1-4 ms range is owned by the 3.0D-7W target "
                "'ttm_refractory_period'. It is defined as the minimal time "
                "between twin stimulus pulses that still produces TWO "
                "RESPONSES FROM THE MUSCLE, so it is a property of the "
                "observed OUTPUT. It is NOT an intrinsic refractory constant "
                "of the TTMn, NOT a threshold of the muscle, and NOT a "
                "depression or recovery parameter of the TTMn->TTM NMJ. No "
                "value is restated here and none is transferred to the NMJ."
            ),
        ),
        OutputValidationLink(
            link_id="dlm_refractory_output_measurement",
            linked_7w_target="dlm_refractory_period",
            linked_7w_layer="3.0D-7W",
            recorded_observable=(
                "Minimal interval between twin stimuli still producing two "
                "DLM muscle responses"
            ),
            classification=MEASUREMENT_END_TO_END_GFS_OUTPUT,
            is_nmj_parameter=False,
            measurement_level=MeasurementLevel.END_TO_END_GFS_OUTPUT,
            source_references=(SOURCE_AUGUSTIN_JOVE_GFS,),
            notes=(
                "REFERENCED, NOT DUPLICATED, AND NOT AN NMJ PARAMETER. The "
                "7-15 ms range is owned by the 3.0D-7W target "
                "'dlm_refractory_period'. It is defined on MUSCLE RESPONSES, "
                "so it is a property of the observed OUTPUT. It is NOT an "
                "intrinsic refractory constant of the DLMn and NOT a "
                "depression parameter of the DLMn->DLM NMJ. The sources "
                "explicitly attribute the comparatively long DLM refractory "
                "period to relatively labile chemical synapses at the CENTRAL "
                "PSI-DLMn junction, so transferring it to the NMJ would "
                "misplace the reported mechanism."
            ),
        ),
    )


def _unavailable_nmj_quantities() -> Tuple[UnavailableNmjQuantity, ...]:
    no_source = (
        "No project source states this quantity for either GFS NMJ. The "
        "recorded muscle responses are end-to-end measurements that sum every "
        "stage upstream of the electrode and cannot be decomposed to recover "
        "an NMJ value."
    )
    return (
        UnavailableNmjQuantity(
            quantity_id="nmj_peak_conductance",
            quantity_kind="nmj_conductance",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs a synaptic conductance to convert "
                "transmitter occupancy into a current."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            must_not_be_inherited_from=(
                "the 80 uS central chemical-synapse peak conductance recorded "
                "in 3.0D-7V, which belongs to the CENTRAL PSI->DLMn synapse and "
                "is itself subject to an unresolved factor-1000 discrepancy"
            ),
        ),
        UnavailableNmjQuantity(
            quantity_id="glutamate_concentration",
            quantity_kind="transmitter_dynamics",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs the glutamate concentration or "
                "occupancy at the receptor over time to drive receptor "
                "opening."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=(
                "transmitter_concentration_time_course"
            ),
            must_not_be_inherited_from=(
                "the cholinergic CENTRAL PSI->DLMn synapse, whose transmitter "
                "is acetylcholine and not glutamate at all"
            ),
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_release_probability",
            quantity_kind="presynaptic_release",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs the probability that a motor neuron "
                "spike releases transmitter, to set the amplitude of the "
                "resulting current."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name="release_probability",
            linked_7w_requirement_id="release_probability",
            must_not_be_inherited_from=None,
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_vesicle_pool_and_depletion",
            quantity_kind="presynaptic_vesicle_dynamics",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs a releasable vesicle pool and a "
                "depletion rule to model how transmission fails when stimuli "
                "arrive faster than the junction can recover."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name="vesicle_pool_size",
            linked_7w_requirement_id="vesicle_pool_and_depletion",
            must_not_be_inherited_from=None,
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_receptor_density",
            quantity_kind="receptor_density",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs the number of receptors at the "
                "postsynaptic site to scale the total junctional conductance."
            ),
            why_unavailable=(
                "No source states a receptor density for either adult GFS NMJ. "
                + no_source
            ),
            linked_7v_excluded_name="dalpha7_receptor_density",
            linked_7w_requirement_id="dalpha7_receptor_density",
            must_not_be_inherited_from=(
                "LARVAL Drosophila NMJ receptor density data, which describes a "
                "different preparation"
            ),
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_receptor_kinetics",
            quantity_kind="receptor_gating",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic glutamatergic NMJ needs receptor gating "
                "kinetics to compute the receptor's open probability."
            ),
            why_unavailable=(
                "The sources state only that both NMJs are GLUTAMATERGIC. They "
                "name no receptor subtype for either junction, and no rate "
                "constant of any kind. " + no_source
            ),
            linked_7v_excluded_name="dalpha7_alpha_rate",
            linked_7w_requirement_id="dalpha7_receptor_kinetics",
            must_not_be_inherited_from=(
                "LARVAL Drosophila NMJ glutamate receptor subunit data, and not "
                "the cholinergic Dalpha7 central receptor, which is a different "
                "receptor at a different synapse"
            ),
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_receptor_single_channel_conductance",
            quantity_kind="receptor_conductance",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs the single-channel conductance of the "
                "receptor to convert an open probability into a current."
            ),
            why_unavailable=(
                "No source states a single-channel conductance for either "
                "adult GFS NMJ. " + no_source
            ),
            linked_7v_excluded_name="dalpha7_single_channel_conductance",
            linked_7w_requirement_id="dalpha7_receptor_conductance",
            must_not_be_inherited_from=(
                "LARVAL Drosophila NMJ single-channel measurements"
            ),
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_rise_time",
            quantity_kind="nmj_synaptic_time_constant",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ would need a synaptic rise time to shape "
                "the junctional current."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            must_not_be_inherited_from=(
                "the 0.1 ms rise time recorded in 3.0D-7V, which is a property "
                "of the CENTRAL PSI->DLMn double-exponential Exp2Syn and of "
                "the published generic chemical-synapse row, NOT of either NMJ"
            ),
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_decay_time",
            quantity_kind="nmj_synaptic_time_constant",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ would need a synaptic decay time to shape "
                "the junctional current."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            must_not_be_inherited_from=(
                "the 1.0 ms decay time recorded in 3.0D-7V, which belongs to "
                "the CENTRAL synapse, not to either NMJ"
            ),
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_reversal_potential",
            quantity_kind="nmj_reversal",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ would need a junctional reversal potential "
                "to determine the sign of the synaptic current."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            must_not_be_inherited_from=(
                "the 0 mV reversal recorded in 3.0D-7V, which is a STANDARD "
                "VALUE of the central phenomenological Exp2Syn and is not a "
                "measured glutamate receptor reversal"
            ),
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_calcium_release_coupling",
            quantity_kind="presynaptic_calcium",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs the coupling from presynaptic "
                "calcium to release."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name="calcium_dependent_release",
            linked_7w_requirement_id="calcium_release_coupling",
            must_not_be_inherited_from=None,
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_short_term_depression",
            quantity_kind="synaptic_plasticity",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs short-term depression parameters to "
                "model any use-dependent reduction in release."
            ),
            why_unavailable=(
                "Where the DLM fails to follow at high frequency, the sources "
                "attribute the failure to the intermediary CENTRAL "
                "PSI->DLMn chemical synapse not recovering, not to the "
                "glutamatergic NMJ. No depression parameter is stated for "
                "either NMJ and none may be fitted to a following ratio. "
                + no_source
            ),
            linked_7v_excluded_name="synaptic_depression_model",
            linked_7w_requirement_id="short_term_depression_parameters",
            must_not_be_inherited_from=None,
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_facilitation",
            quantity_kind="synaptic_plasticity",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs facilitation parameters to describe "
                "any increase in release with repeated activity."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name="facilitation_model",
            linked_7w_requirement_id="facilitation_parameters",
            must_not_be_inherited_from=None,
        ),
        UnavailableNmjQuantity(
            quantity_id="nmj_q10_temperature_scaling",
            quantity_kind="temperature_dependence",
            applies_to="TTMn_TTM and DLMn_DLM",
            why_required=(
                "A mechanistic NMJ needs a temperature coefficient to state "
                "how its kinetics change with temperature."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name="q10_synaptic_scaling",
            linked_7w_requirement_id="q10_synaptic_scaling",
            must_not_be_inherited_from=None,
        ),
    )


def get_motor_output_abstraction() -> MotorOutputAbstraction:
    """Return the motor-output / NMJ abstraction specification.

    SPECIFICATION ONLY. Nothing here is implemented, connected, populated or
    activated: no muscle, no muscle membrane, no contractile element, no NMJ
    current, no glutamate receptor, no transmitter release, no solver input,
    and no change to the passive backend, the timestep policy, 3.0D-7E,
    3.0D-7S, 3.0D-7T, 3.0D-7U, 3.0D-7V or 3.0D-7W.
    """
    abstraction = MotorOutputAbstraction(
        name="gfs_motor_output_and_nmj_specification",
        source=(
            "Specification of the OUTPUT END of the giant fiber system: the "
            "TTMn->TTM and DLMn->DLM glutamatergic neuromuscular junctions, "
            "the fact that standard GFS muscle recordings are END-TO-END GFS "
            "OUTPUT measurements that cannot be attributed to the NMJ, the "
            "direct motor-neuron stimulation bypass as an experimental "
            "condition, and the NMJ quantities a mechanistic junction would "
            "need but that no project source supplies. SPECIFICATION ONLY: no "
            "muscle, no NMJ current, no receptor, no release dynamics, and no "
            "record eligible for the live solver."
        ),
        model_id="ModelDBRepository/245415",
        model_citation=SOURCE_AUGUSTIN_JOVE_GFS,
        motor_outputs=_motor_outputs(),
        measurement_boundaries=_measurement_boundaries(),
        bypass_conditions=_bypass_conditions(),
        validation_links=_validation_links(),
        unavailable_nmj_quantities=_unavailable_nmj_quantities(),
        referenced_7w_targets=(
            "gf_to_ttm_latency",
            "gf_to_dlm_latency",
            "ttm_refractory_period",
            "dlm_refractory_period",
            "ttm_high_frequency_following",
            "dlm_high_frequency_following",
        ),
        scope_note=(
            "TWO GLUTAMATERGIC NMJs. TTMn innervates the tergotrochanteral "
            "muscle (TTM) and DLMn innervates the dorsal longitudinal muscles "
            "(DLM). Both NMJs are CHEMICAL and GLUTAMATERGIC, an "
            "EXPERIMENTALLY SUPPORTED IDENTITY AND TYPE. NO quantitative NMJ "
            "parameter exists in any project source, and the motor-output "
            "record type carries no numeric field at all. GLUTAMATE IDENTITY "
            "DOES NOT LICENSE A RECEPTOR SUBTYPE: no receptor subtype is "
            "asserted for either junction, and no LARVAL Drosophila NMJ "
            "receptor data is imported, because the adult GFS NMJ is a "
            "different preparation. THE MUSCLE IS AN OUTPUT ENDPOINT, NOT A "
            "MODEL. There is no muscle capacitance, resistance, voltage "
            "state, contractile state, calcium dynamics, force or "
            "stretch-activation model anywhere in the project. THE MEASUREMENT "
            "BOUNDARY IS THE POINT OF THIS CHECKPOINT. A muscle response is "
            "an END_TO_END_GFS_OUTPUT: brain/GF stimulus, GF conduction, "
            "central circuit synapse(s), motor neuron propagation, "
            "neuromuscular junction, muscle response. The recorded latency, "
            "refractory period and following ratio therefore CANNOT be "
            "attributed exclusively to the NMJ. The sources themselves "
            "attribute the short TTM latency to the central GF-TTMn "
            "electrochemical synapse, the longer DLM latency to the disynaptic "
            "pathway and the central chemical PSI-DLMn synapse, and the long "
            "DLM refractory period to labile chemical synapses at the CENTRAL "
            "PSI-DLMn junction. THE BYPASS IS AN EXPERIMENTAL CONDITION, NOT A "
            "SIMULATOR INPUT. Direct thoracic or motor-neuron stimulation "
            "bypasses the GF and the central circuit and shows whether the "
            "motor neuron and NMJ output path is still FUNCTIONAL: in shak-B2 "
            "and tetanus-toxin flies that give no muscle response to brain "
            "stimulation, thoracic stimulation still produces a response to "
            "every stimulus, which the authors use to conclude the failure is "
            "central 'and not the NMJs'. That result is BINARY. NO NMJ "
            "PARAMETER, transfer function, conductance, quantal size or "
            "latency may be inferred or back-calculated from it. VALIDATION "
            "TARGETS ARE REFERENCED, NOT DUPLICATED. The GF-TTM latency, "
            "GF-DLM latency, TTM and DLM refractory periods, and TTM and DLM "
            "high-frequency following behaviour are owned by 3.0D-7W and are "
            "not restated here. Every link record has no numeric field, so a "
            "pathway measurement can never be re-typed as an NMJ parameter. "
            "Each is classified as a PATHWAY/OUTPUT MEASUREMENT recorded at a "
            "muscle, and each is explicitly NOT an NMJ intrinsic parameter. "
            "FOURTEEN NMJ QUANTITIES ARE REQUIRED AND UNAVAILABLE: NMJ "
            "conductance, glutamate concentration, release probability, "
            "vesicle pool and depletion, receptor density, receptor kinetics, "
            "single-channel conductance, rise time, decay time, reversal "
            "potential, calcium coupling, short-term depression, facilitation "
            "and Q10. Every one is structurally empty. The rise time, decay "
            "time and reversal potential are additionally barred from being "
            "inherited from the central PSI->DLMn values recorded in 3.0D-7V, "
            "which belong to a different synapse and, for the reversal "
            "potential, are a standard model value rather than a measurement. "
            "This checkpoint establishes NO muscle model, NO NMJ current, NO "
            "glutamate receptor, NO transmitter release and NO simulator "
            "input, and it does NOT modify 3.0D-7U, 3.0D-7V or 3.0D-7W."
        ),
    )
    abstraction.verifies_against_7w()
    return abstraction
