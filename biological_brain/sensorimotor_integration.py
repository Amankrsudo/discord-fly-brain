"""Sensorimotor integration / behavioral-decision abstraction (3.0D-7Z).

3.0D-7Y specified the INPUT END: LC4 carrying angular velocity to the GF, LPLC2
carrying the entire angular-size component, the two stimulus features as
external stimulus coordinates, and the published phenomenological model as a sum
of a linear velocity term and a Gaussian size term. 3.0D-7W owns the central
GFS abstraction and its pathway validation targets. 3.0D-7X owns the motor and
neuromuscular-junction output end. This checkpoint specifies what connects
them: the chain from an external looming stimulus to a motor output, and the
explicit boundaries along that chain where the project has evidence, a
qualitative statement, or nothing at all.

The chain
----------
::

    external looming stimulus
        -> 3.0D-7Y visual feature abstraction
        -> GF sensory integration boundary
        -> GF behavioral-output decision boundary
        -> 3.0D-7W central GFS abstraction
        -> 3.0D-7X motor / NMJ output abstraction

``SensorimotorChain`` records this as stage NAMES with an owner per stage. It
carries no weight, no delay, no per-stage contribution and no probability. The
stages are a description of what the project has specified, not a simulation
of a fly.

What this checkpoint is FOR
---------------------------
Three things in the GFS are routinely assumed rather than stated, and this layer
states them explicitly as boundaries.

First, that the GF's output is SPIKE TIMING, not a continuous motor command.
Ache et al. 2019 state that "the timing of a single spike in the giant fiber
(GF) descending neuron determines whether a fly uses a short or long takeoff
when escaping a looming predator", and Ache et al. 2019 (Nat Neurosci) describe
the GF as firing "a single action potential to activate motor neurons in the
ventral nerve cord (VNC)". The behavioral meaning of that output is
experimentally established. The waveform, the threshold voltage, the refractory
mechanism and the conduction delay that would produce it are NOT, and none is
created here.

Second, that BEHAVIORAL STATE is a real variable in the sensorimotor transform
and not a constant. Ache et al. 2019 (Nat Neurosci) report that for the two
landing descending neurons DNp07 and DNp10, "visual responses of both DNs are
severely attenuated during non-flight periods, effectively decoupling visual
stimuli from the landing motor pathway when landing is inappropriate", and that
the resulting flexibility "arises from distinct mechanisms for gating
action-specific descending pathways, such that sensory and motor networks are
coupled or decoupled according to the behavioral state". They further note that
"descending neurons for escape, such as the Giant Fiber and parallel escape DNs,
may conversely be decoupled from visual inputs during flight".

What is recorded here is the EXISTENCE of a state-dependent boundary and the
two states the literature supports. What is NOT recorded is any gating
function, gating strength, gate parameter, or state-transition probability. The
source reports measured spike rates and behavioral response rates for its own
neurons in its own preparation; those are OBSERVATIONS OF THOSE NEURONS, not a
gating function that could be transferred to the GF, and none of them is
recorded as a parameter here.

Third, that SHORT-MODE and LONG-MODE takeoff are DIFFERENT PROGRAMS ON
DIFFERENT PATHWAYS. Ache et al. 2019 attribute the choice to GF spike timing
and refer to parallel escape circuitry alongside the GF. What is NOT recorded
is a numeric decision threshold, a timing boundary in milliseconds, or a
probability of choosing either mode.

What the sources do NOT provide
-------------------------------
None of the sources for this checkpoint states a GF spike threshold, a GF
sensory integration coefficient, a GF sensory synaptic conductance or kinetic,
a spike initiation dynamic, a state-dependent gating function, a quantitative
short-versus-long decision boundary, a quantitative motor-command probability,
or a behavioral-state transition model. The two Ache et al. 2019 papers are
cited for the QUALITATIVE and STRUCTURAL findings above. All nine of those
quantities are recorded as required-but-unavailable and are structurally empty.

The GFS numerical parameters are not duplicated
-----------------------------------------------
The Augustin et al. 2019 computational model (ModelDBRepository/245415) already
supplies the project's central GFS numbers, and they are owned by 3.0D-7V
(parameters and provenance) and 3.0D-7W (pathway validation targets). The
electrophysiological GF-to-TTM and GF-to-DLM latencies, refractory periods and
following ratios are owned by 3.0D-7W. The NMJ quantities for TTMn-TTM and
DLMn-DLM are owned by 3.0D-7X. This layer REFERENCES all of them by identifier
and copies none of their values. ``MotorPathwayRoute`` carries linked
identifiers and no parameter field at all.

Azimuthal context is not quantified
-----------------------------------
Jang et al. 2023 report that "One DN, the giant fiber (GF), responds invariantly
to looming stimuli across tested azimuthal locations" and that the LC4 and LPLC2
input "have small, ipsilaterally restricted receptive fields". The project
therefore records that the GF integrates a spatially distributed visual input
and records NO bilateral weighting function, no azimuthal tuning curve and no
lateral-versus-medial weighting.

Hard boundaries
---------------
``live_solver_eligible`` is False on every record and on the layer itself, and
cannot be set otherwise. This module:

- does NOT implement Hodgkin-Huxley dynamics, for the GF or for anything else;
- does NOT implement a synaptic current at any synapse in the chain;
- does NOT implement a GF spike generator, spike waveform, threshold voltage,
  refractory mechanism or conduction delay;
- does NOT convert a qualitative combination into a coefficient, and does NOT
  recover the coefficients of the Ache et al. 2019 model;
- does NOT implement a state-dependent gating function, gating strength or
  state-transition probability;
- does NOT create a numeric short-versus-long decision boundary or timing rule;
- does NOT duplicate a 3.0D-7W validation number, a 3.0D-7V parameter, or a
  3.0D-7X NMJ quantity;
- does NOT implement a membrane voltage, conductance or reversal potential, and
  has no field in which one could be recorded;
- does NOT interpret the 7Y stimulus features as membrane variables;
- does NOT introduce a timestep and does not change the numerical timestep
  policy;
- does NOT import, modify or get imported by any passive-solver or
  active-mechanism module, and imports no third-party numerical library.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .provenance import ParameterProvenance
from .synaptic_mechanism_registry import SynapticEvidenceStatus


# --- behavioural states ------------------------------------------------------

STATE_PERCHED_NON_FLYING = "perched_non_flying"
STATE_FLYING = "flying"

# --- GF output abstraction ---------------------------------------------------

OUTPUT_SPIKE_TIMING = "single_action_potential_timing"

# --- combination labels ------------------------------------------------------
#
# A COMBINATION TYPE is a qualitative label for the published structure of the
# GF looming-response model. It is not an equation, a weight or a current.

COMBINATION_QUALITATIVE_SUM = "qualitative_sum_of_feature_functions"

# --- route / mode identifiers ------------------------------------------------

ROUTE_TTM_JUMP = "ttm_jump_route"
ROUTE_DLM_FLIGHT = "dlm_flight_route"

ESCAPE_MODE_DISTINCTION = "gf_short_mode_vs_parallel_long_mode"

# --- layer owners ------------------------------------------------------------
#
# The project already has a specification layer for every stage of the chain.
# 7Z names them and copies nothing from them.

LAYER_7Y = "3.0D-7Y"
LAYER_7W = "3.0D-7W"
LAYER_7X = "3.0D-7X"

# --- chain stages ------------------------------------------------------------

_STAGE_STIMULUS = "external looming stimulus"
_STAGE_VISUAL_FEATURES = "3.0D-7Y visual feature abstraction"
_STAGE_GF_INTEGRATION = "GF sensory integration boundary"
_STAGE_GF_DECISION = "GF behavioral-output decision boundary"
_STAGE_CENTRAL_GFS = "3.0D-7W central GFS abstraction"
_STAGE_MOTOR_OUTPUT = "3.0D-7X motor / NMJ output abstraction"


# --- source references ------------------------------------------------------
#
# Each specification layer owns its own source strings and annotates what IT
# uses, following the convention of 3.0D-7V, 7W, 7X and 7Y.

SOURCE_ACHE_2019_GF_LOOMING = (
    "Ache JM, Polsky J, Alghailani S, Parekh R, Breads P, Peek MY, Bock DD, "
    "von Reyn CR, Card GM (2019). Neural Basis for Looming Size and Velocity "
    "Encoding in the Drosophila Giant Fiber Escape Pathway. Curr Biol "
    "29(6):1073-1081.e4. https://pubmed.ncbi.nlm.nih.gov/30827912/ . States "
    "that 'the timing of a single spike in the giant fiber (GF) descending "
    "neuron determines whether a fly uses a short or long takeoff when escaping "
    "a looming predator', that 'LPLC2 and LC4 synapse directly onto the GF via "
    "reconstruction in a fly brain electron microscopy (EM) volume', and that "
    "'A model summing a linear function of angular velocity (provided by LC4) "
    "and a Gaussian function of angular size (provided by LPLC2) replicates GF "
    "looming response dynamics and predicts the peak response time'. The full "
    "text is behind a subscription, so the project holds this abstract-level "
    "statement and NOT the model coefficients. The MODEL STRUCTURE itself is "
    "owned by 3.0D-7Y and is not restated as a number here. States NO GF spike "
    "threshold, NO decision boundary and NO gating function."
)

SOURCE_ACHE_2019_STATE_DEPENDENCE = (
    "Ache JM, Namiki S, Lee A, Branson K, Card GM (2019). State-dependent "
    "decoupling of sensory and motor circuits underlies behavioral flexibility "
    "in Drosophila. Nat Neurosci 22(7):1132-1139. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7444277/ . Identifies the two "
    "landing descending neurons DNp07 and DNp10 and states that 'visual "
    "responses of both DNs are severely attenuated during non-flight periods, "
    "effectively decoupling visual stimuli from the landing motor pathway when "
    "landing is inappropriate', that this 'flexibility is added to this wiring "
    "scheme by coupling or decoupling the DNs from visual inputs depending on "
    "the animal's current behavioral state', and that the flexibility 'arises "
    "from distinct mechanisms for gating action-specific descending pathways, "
    "such that sensory and motor networks are coupled or decoupled according to "
    "the behavioral state'. Describes the GF as firing 'a single action "
    "potential to activate motor neurons in the ventral nerve cord (VNC)', "
    "notes that 'descending neurons for escape, such as the Giant Fiber and "
    "parallel escape DNs, may conversely be decoupled from visual inputs during "
    "flight', and attributes the flight dependence of the two landing DN types "
    "to distinct mechanisms: octopaminergic neuromodulation for DNp07 and "
    "feedback from the flight motor circuit for DNp10. States NO gating "
    "function, NO gating strength, NO state-transition model and NO GF "
    "parameter."
)

SOURCE_AUGUSTIN_2019_GFS_MODEL = (
    "Augustin et al. (2019). Drosophila integrative nerve circuit for escape "
    "behavior. eLife 8:e40240. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ . ModelDB accession "
    "245415: https://github.com/ModelDBRepository/245415 . The modeled GFS "
    "contains the GF, TTMn, PSI and DLMn, with GF->TTMn and GF->PSI upstream of "
    "the two motor pathways. The project's NUMERICAL parameters and topology "
    "for this model are already encoded at 3.0D-7V and 3.0D-7W and are "
    "referenced, never copied, here."
)

SOURCE_AUGUSTIN_JOVE_GFS = (
    "Allen MJ, Allen MJ, Godenschwege TA. Electrophysiological recordings from "
    "the giant fiber pathway of D. melanogaster. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC3182647/ . The GF-to-TTM and "
    "GF-to-DLM latencies, refractory periods and following ratios measured by "
    "this preparation are owned by 3.0D-7W as validation targets and are "
    "referenced, never copied, here."
)

SOURCE_JANG_2023_AZIMUTHAL = (
    "Jang H, Goodman DP, Ausborn J, von Reyn CR (2023). Azimuthal invariance "
    "to looming stimuli in the Drosophila giant fiber escape circuit. J Exp Biol "
    "226(8):jeb244790. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10263144/ . States that 'One DN, "
    "the giant fiber (GF), responds invariantly to looming stimuli across tested "
    "azimuthal locations' and that 'the VPNs LC4 and LPLC2 that provide "
    "ipsilateral visual input to the GF have small, ipsilaterally restricted "
    "receptive fields'. Reports NO bilateral weighting function, NO azimuthal "
    "tuning value and NO numeric GF looming-response latency."
)


# --- the project refuses these inferences -----------------------------------

_NOT_LIVE = (
    "3.0D-7Z IS A SPECIFICATION CHECKPOINT ONLY. This record is NOT eligible "
    "for the live solver: no Hodgkin-Huxley dynamics are implemented, no "
    "synaptic current is computed, no spike is generated, no gating function is "
    "evaluated, and the passive backend and its timestep policy are unchanged."
)

_NO_SPIKE_MECHANISM = (
    "NO SPIKE MECHANISM EXISTS HERE. The GF's output is recorded as the TIMING "
    "of a single action potential, because the behavioral meaning of that "
    "timing is experimentally established. The waveform, the threshold voltage, "
    "the refractory mechanism, the initiation dynamics and the conduction delay "
    "that would generate it are NOT recorded, are NOT derived from the "
    "behavioral finding, and may NOT be inferred from it."
)

_NO_QUANTITATIVE_COMBINATION = (
    "THE COMBINATION IS QUALITATIVE. Ache et al. 2019 report that their model "
    "sums a linear function of angular velocity with a Gaussian function of "
    "angular size. That is the published SHAPE of a stimulus-response "
    "relationship. No slope, no Gaussian amplitude, no Gaussian width, no "
    "offset, no relative weight, no threshold and no coefficient is recorded "
    "here. The full text is behind a subscription, so the project holds the "
    "model sentence and not the equations, and nothing is reconstructed, "
    "re-derived or fitted from a response curve. The model structure is owned "
    "by 3.0D-7Y."
)

_NO_GATING_FUNCTION = (
    "NO STATE-DEPENDENT GATING FUNCTION EXISTS. Ache et al. 2019 establish that "
    "behavioural state changes the coupling between visual input and a motor "
    "pathway, and they attribute the flight dependence of their two landing "
    "neurons to octopaminergic neuromodulation and to feedback from the flight "
    "motor circuit. Those are MECHANISMS DESCRIBED FOR THOSE NEURONS IN THAT "
    "PREPARATION. No gate function, no gate parameter, no gating strength and "
    "no state-transition probability is stated for the GF, none is recorded "
    "here, and no measured spike rate or behavioural response rate from any "
    "other neuron is transferred to the GF as one."
)

_NO_DECISION_BOUNDARY = (
    "NO QUANTITATIVE DECISION BOUNDARY EXISTS. Ache et al. 2019 attribute the "
    "choice between a short-mode and a long-mode takeoff to the timing of a "
    "single GF spike. That is a QUALITATIVE and STRUCTURAL finding about which "
    "pathway and when. No decision threshold, no timing boundary in "
    "milliseconds, no probability of either mode and no selection rule is "
    "stated in any source used by this checkpoint, and none is created here."
)

_NO_PARAMETER_DUPLICATION = (
    "NO PARAMETER IS DUPLICATED. The central GFS synaptic parameters and their "
    "provenance are owned by 3.0D-7V. The GF-to-TTM and GF-to-DLM latencies, "
    "refractory periods and following ratios are owned by 3.0D-7W. The NMJ and "
    "muscle-output quantities for TTMn-TTM and DLMn-DLM are owned by 3.0D-7X. "
    "The visual feature abstraction is owned by 3.0D-7Y. This layer references "
    "each of them by identifier and restates none of their values."
)

_NO_BILATERAL_WEIGHTING = (
    "NO BILATERAL OR AZIMUTHAL WEIGHTING FUNCTION IS CREATED. Jang et al. 2023 "
    "report that the GF responds invariantly to looming across the tested "
    "azimuthal locations, and that the LC4 and LPLC2 input has small, "
    "ipsilaterally restricted receptive fields. The project therefore records "
    "that the GF integrates a spatially distributed visual input, and records "
    "no lateral-versus-medial weighting, no receptive field and no azimuthal "
    "tuning value."
)

_NO_FEATURE_AS_MECHANISM = (
    "THE 7Y STIMULUS FEATURES ARE NOT A MECHANISM. angular_velocity and "
    "angular_size are external stimulus coordinates carried by LC4 and LPLC2 "
    "respectively, as specified at 3.0D-7Y. They are not a membrane voltage, "
    "not a current, not a conductance and not a state of any compartment, and "
    "the sensorimotor input record refuses to be marked as a membrane variable "
    "or as a voltage representation."
)


# --- A: sensorimotor input ----------------------------------------------------


@dataclass(frozen=True)
class SensorimotorInputRecord:
    """One 7Y looming feature arriving at the GF integration boundary.

    This record type carries NO numeric field of any kind. It names a 7Y
    stimulus feature by identifier, names the visual projection neuron that
    carries it, and refuses to be a membrane variable or a voltage
    representation.
    """

    input_id: str
    referenced_layer: str
    feature_id: str
    feature_source_neuron: str
    arrives_at: str
    description: str
    feature_representation: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    is_membrane_variable: bool = False
    uses_membrane_voltage_representation: bool = False
    has_quantitative_parameter: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Sensorimotor input '{self.input_id}' cannot be live-solver "
                f"eligible. 3.0D-7Z specifies the chain, not a simulation."
            )
        if self.is_membrane_variable:
            raise ValueError(
                f"Sensorimotor input '{self.input_id}' must NOT be a membrane "
                f"variable. The 7Y stimulus features are external stimulus "
                f"coordinates, not a state of any compartment."
            )
        if self.uses_membrane_voltage_representation:
            raise ValueError(
                f"Sensorimotor input '{self.input_id}' must not use a membrane "
                f"voltage representation. The 7Y feature is a stimulus "
                f"coordinate; no source states a voltage for it."
            )
        if self.has_quantitative_parameter:
            raise ValueError(
                f"Sensorimotor input '{self.input_id}' must not carry a "
                f"quantitative parameter. 3.0D-7Y records the feature and not a "
                f"value."
            )
        if self.referenced_layer != LAYER_7Y:
            raise ValueError(
                f"Sensorimotor input '{self.input_id}' must reference "
                f"{LAYER_7Y}, which owns the visual feature abstraction."
            )
        if self.feature_representation != "external_stimulus_feature":
            raise ValueError(
                f"Sensorimotor input '{self.input_id}' must be represented as "
                f"an external stimulus feature, got "
                f"'{self.feature_representation}'."
            )
        if not self.source_references:
            raise ValueError(
                f"Sensorimotor input '{self.input_id}' must carry at least one "
                f"source reference."
            )

    @property
    def is_external_stimulus(self) -> bool:
        return True

    def limitations(self) -> str:
        return (
            f"EXTERNAL STIMULUS FEATURE, NOT A MECHANISM. {self.notes} "
            f"{_NO_FEATURE_AS_MECHANISM} {_NO_QUANTITATIVE_COMBINATION} "
            f"{_NO_SPIKE_MECHANISM} {_NOT_LIVE}"
        )


# --- B: GF sensory integration boundary ---------------------------------------


@dataclass(frozen=True)
class GFIntegrationBoundary:
    """Where the GF combines the two looming feature streams.

    The record carries a QUALITATIVE combination type, the identifiers of the
    features and of the 7Y terms that describe them, and the published model
    sentence. It has no field for a coefficient, a slope, a width, an amplitude,
    an offset or a weight, and every mechanistic flag is a hard False that
    raises if set.
    """

    boundary_id: str
    integrates_neuron: str
    input_record_ids: Tuple[str, ...]
    input_feature_ids: Tuple[str, ...]
    referenced_7y_term_ids: Tuple[str, ...]
    combination_type: str
    published_model_statement: str
    combination_is_qualitative: bool
    spatially_distributed_input: bool
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    carries_a_coefficient: bool = False
    is_membrane_current: bool = False
    has_conductance: bool = False
    has_reversal_potential: bool = False
    has_decision_threshold: bool = False
    is_live_solver_eligible: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible or self.is_live_solver_eligible:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' cannot be "
                f"live-solver eligible. A qualitative combination is not a "
                f"mechanism and drives no compartment."
            )
        if not self.combination_is_qualitative:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' must remain a "
                f"QUALITATIVE combination. No source states a coefficient, so "
                f"nothing quantitative may be attached to it."
            )
        if self.carries_a_coefficient:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' must not carry a "
                f"coefficient, slope, width, amplitude, offset or weight. The "
                f"Ache et al. 2019 equations are behind a subscription and are "
                f"not reconstructed here."
            )
        if self.is_membrane_current:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' must NOT be a "
                f"membrane current. It is a published stimulus-response "
                f"FUNCTION and must not be converted into a current."
            )
        if self.has_conductance or self.has_reversal_potential:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' must not carry a "
                f"conductance or a reversal potential. No source states a GF "
                f"sensory conductance; that quantity is owned by 3.0D-7Y and "
                f"is structurally empty there."
            )
        if self.has_decision_threshold:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' must not carry a "
                f"decision threshold. No source states one, and an invented "
                f"threshold would fabricate the behavioral-decision rule this "
                f"checkpoint exists to leave open."
            )
        if self.combination_type != COMBINATION_QUALITATIVE_SUM:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' must carry the "
                f"qualitative combination type "
                f"'{COMBINATION_QUALITATIVE_SUM}', got "
                f"'{self.combination_type}'."
            )
        if not self.input_feature_ids:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' must name the "
                f"looming features it integrates."
            )
        if not self.referenced_7y_term_ids:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' must reference "
                f"the 3.0D-7Y phenomenological terms it corresponds to."
            )
        if not self.source_references:
            raise ValueError(
                f"GF integration boundary '{self.boundary_id}' must carry at "
                f"least one source reference."
            )

    @property
    def is_a_mechanism(self) -> bool:
        """Always False: this is a published function, not a biophysical
        mechanism."""
        return False

    @property
    def input_count(self) -> int:
        return len(self.input_feature_ids)

    def limitations(self) -> str:
        return (
            f"QUALITATIVE COMBINATION, NOT A MECHANISM. "
            f"{self.published_model_statement} {self.notes} "
            f"{_NO_QUANTITATIVE_COMBINATION} {_NO_SPIKE_MECHANISM} "
            f"{_NO_BILATERAL_WEIGHTING} {_NOT_LIVE}"
        )


# --- C: GF output abstraction -------------------------------------------------


@dataclass(frozen=True)
class GFOutputAbstraction:
    """The GF's output as the timing of a single action potential.

    The behavioral meaning of that timing is experimentally established. The
    mechanism that produces it is not, so every mechanistic flag on this record
    is a hard False that raises if set: there is no waveform, no threshold
    voltage, no refractory mechanism and no conduction delay.
    """

    output_id: str
    output_type: str
    target_layer: str
    target_description: str
    behavioural_evidence: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    mechanistic_live_solver_ready: bool = False
    is_membrane_voltage: bool = False
    is_continuous_motor_command: bool = False
    has_spike_waveform: bool = False
    has_threshold_voltage: bool = False
    has_refractory_mechanism: bool = False
    has_conduction_delay: bool = False
    has_quantitative_value: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"GF output '{self.output_id}' cannot be live-solver eligible."
            )
        if self.mechanistic_live_solver_ready:
            raise ValueError(
                f"GF output '{self.output_id}' must not be marked "
                f"mechanistically live-solver ready. No source states a GF "
                f"spike threshold, initiation dynamic or conduction delay."
            )
        if self.is_membrane_voltage or self.is_continuous_motor_command:
            raise ValueError(
                f"GF output '{self.output_id}' must not be a membrane voltage "
                f"or a continuous motor command. The experimentally "
                f"established output is the TIMING of a single action "
                f"potential."
            )
        if (
            self.has_spike_waveform
            or self.has_threshold_voltage
            or self.has_refractory_mechanism
            or self.has_conduction_delay
        ):
            raise ValueError(
                f"GF output '{self.output_id}' must not carry a spike "
                f"waveform, a threshold voltage, a refractory mechanism or a "
                f"conduction delay. No source used by this checkpoint states "
                f"any of them for the GF, and none may be derived from the "
                f"behavioural timing finding."
            )
        if self.has_quantitative_value:
            raise ValueError(
                f"GF output '{self.output_id}' must not carry a quantitative "
                f"value. The timing is behaviourally meaningful; its numeric "
                f"value is a 3.0D-7W validation target and is not copied here."
            )
        if self.output_type != OUTPUT_SPIKE_TIMING:
            raise ValueError(
                f"GF output '{self.output_id}' must be recorded as "
                f"'{OUTPUT_SPIKE_TIMING}', got '{self.output_type}'."
            )
        if self.target_layer != LAYER_7W:
            raise ValueError(
                f"GF output '{self.output_id}' must target {LAYER_7W}, which "
                f"owns the central GFS abstraction and its validation targets."
            )
        if not self.behavioural_evidence:
            raise ValueError(
                f"GF output '{self.output_id}' must state the behavioural "
                f"evidence that makes its timing meaningful."
            )
        if not self.source_references:
            raise ValueError(
                f"GF output '{self.output_id}' must carry at least one source "
                f"reference."
            )

    @property
    def is_discrete(self) -> bool:
        """True: the output is a single action potential, not a graded value."""
        return True

    def limitations(self) -> str:
        return (
            f"SPIKE TIMING, NOT A SPIKE MECHANISM. {self.notes} "
            f"{_NO_SPIKE_MECHANISM} {_NO_PARAMETER_DUPLICATION} {_NOT_LIVE}"
        )


# --- D: behavioural state boundary --------------------------------------------


@dataclass(frozen=True)
class BehavioralStateRecord:
    """A behavioural state in which the sensorimotor transform can differ.

    The record names a state and cites the evidence that the state matters. It
    carries NO gating function, NO gating strength and NO transition
    probability, and it has no numeric field in which one could be placed.
    """

    state_id: str
    state_kind: str
    described_as: str
    coupling_to_visual_input: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    gating_function_available: bool = False
    gating_is_qualitative: bool = True
    has_transition_probability: bool = False
    has_numeric_gate_parameter: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Behavioural state '{self.state_id}' cannot be live-solver "
                f"eligible. A state label is not a state machine."
            )
        if self.gating_function_available:
            raise ValueError(
                f"Behavioural state '{self.state_id}' must not have a gating "
                f"function available. No source states one for the GF, and "
                f"none is created here."
            )
        if not self.gating_is_qualitative:
            raise ValueError(
                f"Behavioural state '{self.state_id}' must keep its gating "
                f"qualitative. A quantitative gate would be an invented "
                f"mechanism."
            )
        if self.has_transition_probability or self.has_numeric_gate_parameter:
            raise ValueError(
                f"Behavioural state '{self.state_id}' must not carry a "
                f"transition probability or a numeric gate parameter. No "
                f"source states either for the GF."
            )
        if self.state_kind != "behavioural_context":
            raise ValueError(
                f"Behavioural state '{self.state_id}' must be recorded as a "
                f"behavioural context, got '{self.state_kind}'."
            )
        if not self.coupling_to_visual_input:
            raise ValueError(
                f"Behavioural state '{self.state_id}' must state how the state "
                f"relates to the coupling of visual input to a motor pathway."
            )
        if not self.source_references:
            raise ValueError(
                f"Behavioural state '{self.state_id}' must carry at least one "
                f"source reference."
            )

    @property
    def has_quantitative_value(self) -> bool:
        """Always False."""
        return False

    def limitations(self) -> str:
        return (
            f"BEHAVIOURAL CONTEXT, NOT A GATING FUNCTION. {self.notes} "
            f"{_NO_GATING_FUNCTION} {_NO_SPIKE_MECHANISM} {_NOT_LIVE}"
        )


# --- E: motor pathway routing -------------------------------------------------


@dataclass(frozen=True)
class MotorPathwayRoute:
    """A named route from the GF to a muscle, by identifier only.

    The record names the descending neurons, the muscle, the linked 3.0D-7W
    connection and target identifiers and the linked 3.0D-7X output identifier.
    It has NO synaptic parameter field and NO NMJ field at all, so a parameter
    cannot be duplicated through it.
    """

    route_id: str
    route_label: str
    descending_neurons: Tuple[str, ...]
    terminal_muscle: str
    behavioural_role: str
    linked_7w_connection_ids: Tuple[str, ...]
    linked_7w_target_ids: Tuple[str, ...]
    linked_7x_output_id: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    owns_synaptic_parameters: bool = False
    owns_nmj_quantities: bool = False
    carries_a_synaptic_parameter: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Motor route '{self.route_id}' cannot be live-solver "
                f"eligible. It names a route and connects nothing."
            )
        if (
            self.owns_synaptic_parameters
            or self.owns_nmj_quantities
            or self.carries_a_synaptic_parameter
        ):
            raise ValueError(
                f"Motor route '{self.route_id}' must not own, duplicate or "
                f"carry a synaptic or NMJ parameter. The synaptic parameters "
                f"belong to 3.0D-7V, the pathway targets to 3.0D-7W and the "
                f"NMJ quantities to 3.0D-7X."
            )
        if LAYER_7W not in self.notes or not self.linked_7w_target_ids:
            raise ValueError(
                f"Motor route '{self.route_id}' must link at least one 3.0D-7W "
                f"validation target so the pathway stays owned by 3.0D-7W."
            )
        if not self.linked_7w_connection_ids:
            raise ValueError(
                f"Motor route '{self.route_id}' must link at least one 3.0D-7W "
                f"connection identifier."
            )
        if not self.linked_7x_output_id:
            raise ValueError(
                f"Motor route '{self.route_id}' must link the 3.0D-7X motor "
                f"output identifier that terminates it."
            )
        if not self.behavioural_role:
            raise ValueError(
                f"Motor route '{self.route_id}' must state its behavioural "
                f"role."
            )
        if not self.source_references:
            raise ValueError(
                f"Motor route '{self.route_id}' must carry at least one source "
                f"reference."
            )

    @property
    def has_quantitative_parameter(self) -> bool:
        """Always False: the record type has no parameter field."""
        return False

    @property
    def stage_count(self) -> int:
        return len(self.descending_neurons) + 1

    def limitations(self) -> str:
        return (
            f"NAMED ROUTE, NOT A SIMULATED PATHWAY. {self.notes} "
            f"{_NO_PARAMETER_DUPLICATION} {_NOT_LIVE}"
        )


# --- F: short versus long escape ----------------------------------------------


@dataclass(frozen=True)
class EscapeModeDistinction:
    """The short-mode versus long-mode takeoff distinction, qualitatively.

    Ache et al. 2019 attribute the choice between the two takeoff programs to
    the timing of a single GF spike, and refer to parallel escape circuitry
    alongside the GF. This record states the STRUCTURE of the distinction. It
    has no threshold, no timing boundary and no probability field, and the
    numeric fields below are structurally None.
    """

    distinction_id: str
    gf_pathway_role: str
    parallel_pathway_role: str
    relative_timing_statement: str
    relative_timing_is_biologically_relevant: bool
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    decision_threshold: None = None
    timing_boundary_ms: None = None
    mode_selection_probability: None = None
    is_numeric_decision_boundary: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Escape-mode distinction '{self.distinction_id}' cannot be "
                f"live-solver eligible. It is a qualitative distinction."
            )
        for field_name in (
            "decision_threshold", "timing_boundary_ms",
            "mode_selection_probability",
        ):
            if getattr(self, field_name) is not None:
                raise ValueError(
                    f"Escape-mode distinction '{self.distinction_id}' must "
                    f"remain qualitative. Field '{field_name}' must stay None: "
                    f"no source states a decision threshold, a timing "
                    f"boundary or a mode-selection probability for the GF, and "
                    f"none may be created here."
                )
        if self.is_numeric_decision_boundary:
            raise ValueError(
                f"Escape-mode distinction '{self.distinction_id}' must not be "
                f"a numeric decision boundary. The GF contribution to each mode "
                f"is a structural finding, not a threshold measurement."
            )
        if not self.relative_timing_is_biologically_relevant:
            raise ValueError(
                f"Escape-mode distinction '{self.distinction_id}' must record "
                f"that relative timing between the pathways is biologically "
                f"relevant. That is the reported mechanism of mode selection."
            )
        if not self.parallel_pathway_role:
            raise ValueError(
                f"Escape-mode distinction '{self.distinction_id}' must state "
                f"the role of the parallel GF-independent circuitry."
            )
        if not self.source_references:
            raise ValueError(
                f"Escape-mode distinction '{self.distinction_id}' must carry "
                f"at least one source reference."
            )

    @property
    def has_numeric_boundary(self) -> bool:
        """Always False."""
        return False

    def limitations(self) -> str:
        return (
            f"QUALITATIVE DISTINCTION, NOT A DECISION RULE. {self.notes} "
            f"{_NO_DECISION_BOUNDARY} {_NO_SPIKE_MECHANISM} {_NOT_LIVE}"
        )


# --- G: unavailable integration quantities ------------------------------------


@dataclass(frozen=True)
class UnavailableIntegrationQuantity:
    """A quantity a mechanistic sensorimotor model would need, and lacks.

    ``value`` is structurally None and cannot be set. Where an equivalent
    exclusion already exists at 3.0D-7V, 7W, 7X or 7Y, it is LINKED rather
    than duplicated.
    """

    quantity_id: str
    quantity_kind: str
    applies_to: str
    why_required: str
    why_unavailable: str
    linked_7y_quantity_id: Optional[str]
    linked_7w_requirement_id: Optional[str]
    linked_7x_quantity_id: Optional[str]
    linked_7v_excluded_name: Optional[str]
    must_not_be_inherited_from: Optional[str]
    value: None = None
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Unavailable integration quantity '{self.quantity_id}' cannot "
                f"be live-solver eligible: it has no value to supply."
            )
        if self.value is not None:
            raise ValueError(
                f"Unavailable integration quantity '{self.quantity_id}' must "
                f"remain unavailable. No source states it, so no value may be "
                f"populated."
            )
        if not self.why_required or not self.why_unavailable:
            raise ValueError(
                f"Unavailable integration quantity '{self.quantity_id}' must "
                f"state both why a mechanistic model would need it and why it "
                f"is unavailable."
            )

    @property
    def value_is_populated(self) -> bool:
        """Always False."""
        return False

    def limitations(self) -> str:
        parts = [
            f"REQUIRED BY A MECHANISTIC SENSORIMOTOR MODEL, CURRENTLY "
            f"UNAVAILABLE. {self.why_required} {self.why_unavailable} This "
            f"quantity stays empty. It is NOT filled with a generic "
            f"Drosophila value, with a value from another neuron class, with a "
            f"value from a different preparation, or with a value "
            f"back-calculated from a behavioural observation."
        ]
        if self.must_not_be_inherited_from:
            parts.append(
                f"It is specifically NOT inherited from "
                f"{self.must_not_be_inherited_from}."
            )
        parts.append(_NOT_LIVE)
        return " ".join(parts)


# --- H: integration validation targets -----------------------------------------


@dataclass(frozen=True)
class IntegrationValidationTarget:
    """A qualitative target a future sensorimotor model would satisfy.

    None of these targets is a number. Where a numeric target exists in the
    project it belongs to 3.0D-7W, and where a functional identity exists it
    belongs to 3.0D-7X or 3.0D-7Y. ``carries_a_value`` is always False.
    """

    target_id: str
    statement: str
    target_kind: str
    observable: str
    requires_record: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    is_numeric_decision_target: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Integration validation target '{self.target_id}' cannot be "
                f"live-solver eligible. It is a target, not a model."
            )
        if self.is_numeric_decision_target:
            raise ValueError(
                f"Integration validation target '{self.target_id}' must not be "
                f"a numeric decision target. No source used by this "
                f"checkpoint states a decision threshold, a timing boundary or "
                f"a mode-selection probability."
            )
        if self.target_kind not in (
            "qualitative_observation", "structural_constraint"
        ):
            raise ValueError(
                f"Integration validation target '{self.target_id}' must be "
                f"qualitative or structural, got '{self.target_kind}'."
            )
        if not self.statement or not self.observable:
            raise ValueError(
                f"Integration validation target '{self.target_id}' must state "
                f"what it asserts and what would be observed."
            )
        if not self.source_references:
            raise ValueError(
                f"Integration validation target '{self.target_id}' must carry "
                f"at least one source reference."
            )

    @property
    def carries_a_value(self) -> bool:
        """Always False: every target here is a statement, not a number."""
        return False

    def limitations(self) -> str:
        return (
            f"{self.notes} {_NO_DECISION_BOUNDARY} "
            f"{_NO_PARAMETER_DUPLICATION} {_NOT_LIVE}"
        )


# --- the chain ----------------------------------------------------------------


@dataclass(frozen=True)
class SensorimotorChain:
    """The sensorimotor chain as stage NAMES with an owner per stage.

    There is no weight, no delay, no signal type, no probability and no
    per-stage contribution between the stages. The record exists so that the
    chain has a single, checkable statement of what the project has specified
    and which checkpoint owns each part.
    """

    chain_id: str
    description: str
    stages: Tuple[str, ...]
    stage_owners: Tuple[str, ...]
    source_references: Tuple[str, ...]
    notes: str
    carries_weights: bool = False
    carries_delays: bool = False
    carries_probabilities: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Sensorimotor chain '{self.chain_id}' cannot be live-solver "
                f"eligible. It names stages; it connects nothing."
            )
        if (
            self.carries_weights
            or self.carries_delays
            or self.carries_probabilities
        ):
            raise ValueError(
                f"Sensorimotor chain '{self.chain_id}' must not carry weights, "
                f"delays or probabilities. No source states them, and inventing "
                f"them would fabricate the mechanism this checkpoint exists to "
                f"specify as absent."
            )
        if len(self.stages) != len(self.stage_owners):
            raise ValueError(
                f"Sensorimotor chain '{self.chain_id}' must name exactly one "
                f"owner per stage."
            )
        for stage in self.stages:
            if not isinstance(stage, str):
                raise ValueError(
                    f"Sensorimotor chain '{self.chain_id}' stages must be "
                    f"stage NAMES, not simulated components."
                )
        required = (
            _STAGE_STIMULUS, _STAGE_VISUAL_FEATURES, _STAGE_GF_INTEGRATION,
            _STAGE_GF_DECISION, _STAGE_CENTRAL_GFS, _STAGE_MOTOR_OUTPUT,
        )
        for stage in required:
            if stage not in self.stages:
                raise ValueError(
                    f"Sensorimotor chain '{self.chain_id}' must name the stage "
                    f"'{stage}'."
                )
        for owner in (LAYER_7Y, LAYER_7W, LAYER_7X):
            if owner not in self.stage_owners:
                raise ValueError(
                    f"Sensorimotor chain '{self.chain_id}' must record "
                    f"{owner} as an owner of one of its stages, so the chain "
                    f"cannot claim territory those layers already hold."
                )
        if not self.source_references:
            raise ValueError(
                f"Sensorimotor chain '{self.chain_id}' must carry at least one "
                f"source reference."
            )

    @property
    def stage_count(self) -> int:
        return len(self.stages)

    def owner_of(self, stage: str) -> str:
        for candidate, owner in zip(self.stages, self.stage_owners):
            if candidate == stage:
                return owner
        raise KeyError(f"Stage '{stage}' not in chain '{self.chain_id}'")

    def limitations(self) -> str:
        return (
            f"{self.notes} {_NO_PARAMETER_DUPLICATION} "
            f"{_NO_GATING_FUNCTION} {_NOT_LIVE}"
        )


# --- the layer ----------------------------------------------------------------


@dataclass(frozen=True)
class SensorimotorIntegration:
    """The sensorimotor chain, specified. NOT modelled.

    Assigns nothing, populates nothing, connects nothing. No compartment, no
    ``CableParameters``, no ``CompartmentElectrical`` and no solver input is
    populated from this layer, and no solver module imports it.
    """

    name: str
    source: str
    model_id: str
    model_citation: str
    sensorimotor_inputs: Tuple[SensorimotorInputRecord, ...]
    gf_integration_boundaries: Tuple[GFIntegrationBoundary, ...]
    gf_outputs: Tuple[GFOutputAbstraction, ...]
    behavioral_states: Tuple[BehavioralStateRecord, ...]
    motor_routes: Tuple[MotorPathwayRoute, ...]
    escape_mode_distinctions: Tuple[EscapeModeDistinction, ...]
    unavailable_integration_quantities: Tuple[UnavailableIntegrationQuantity, ...]
    validation_targets: Tuple[IntegrationValidationTarget, ...]
    chains: Tuple[SensorimotorChain, ...]
    referenced_7y_records: Tuple[str, ...]
    referenced_7w_targets: Tuple[str, ...]
    referenced_7x_outputs: Tuple[str, ...]
    scope_note: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                "The sensorimotor integration abstraction cannot be "
                "live-solver eligible. It is a specification of the chain "
                "between the layers, not a model of it."
            )
        if not self.sensorimotor_inputs:
            raise ValueError(
                "The sensorimotor integration abstraction must specify at "
                "least one sensory input."
            )
        if not self.behavioral_states:
            raise ValueError(
                "The sensorimotor integration abstraction must record at "
                "least one behavioural state."
            )

    # -- lookup -------------------------------------------------------------

    def input_record(self, input_id: str) -> SensorimotorInputRecord:
        for record in self.sensorimotor_inputs:
            if record.input_id == input_id:
                return record
        raise KeyError(f"Sensorimotor input '{input_id}' not in abstraction")

    def input_ids(self) -> Tuple[str, ...]:
        return tuple(record.input_id for record in self.sensorimotor_inputs)

    def boundary(self, boundary_id: str) -> GFIntegrationBoundary:
        for record in self.gf_integration_boundaries:
            if record.boundary_id == boundary_id:
                return record
        raise KeyError(
            f"GF integration boundary '{boundary_id}' not in abstraction"
        )

    def boundary_ids(self) -> Tuple[str, ...]:
        return tuple(
            record.boundary_id for record in self.gf_integration_boundaries
        )

    def gf_output(self, output_id: str) -> GFOutputAbstraction:
        for record in self.gf_outputs:
            if record.output_id == output_id:
                return record
        raise KeyError(f"GF output '{output_id}' not in abstraction")

    def behavioral_state(self, state_id: str) -> BehavioralStateRecord:
        for record in self.behavioral_states:
            if record.state_id == state_id:
                return record
        raise KeyError(f"Behavioural state '{state_id}' not in abstraction")

    def state_ids(self) -> Tuple[str, ...]:
        return tuple(record.state_id for record in self.behavioral_states)

    def route(self, route_id: str) -> MotorPathwayRoute:
        for record in self.motor_routes:
            if record.route_id == route_id:
                return record
        raise KeyError(f"Motor route '{route_id}' not in abstraction")

    def route_ids(self) -> Tuple[str, ...]:
        return tuple(record.route_id for record in self.motor_routes)

    def distinction(self, distinction_id: str) -> EscapeModeDistinction:
        for record in self.escape_mode_distinctions:
            if record.distinction_id == distinction_id:
                return record
        raise KeyError(
            f"Escape-mode distinction '{distinction_id}' not in abstraction"
        )

    def unavailable(self, quantity_id: str) -> UnavailableIntegrationQuantity:
        for record in self.unavailable_integration_quantities:
            if record.quantity_id == quantity_id:
                return record
        raise KeyError(
            f"Unavailable integration quantity '{quantity_id}' not in "
            f"abstraction"
        )

    def unavailable_ids(self) -> Tuple[str, ...]:
        return tuple(
            record.quantity_id
            for record in self.unavailable_integration_quantities
        )

    def target(self, target_id: str) -> IntegrationValidationTarget:
        for record in self.validation_targets:
            if record.target_id == target_id:
                return record
        raise KeyError(
            f"Integration validation target '{target_id}' not in abstraction"
        )

    def target_ids(self) -> Tuple[str, ...]:
        return tuple(record.target_id for record in self.validation_targets)

    def chain(self, chain_id: str) -> SensorimotorChain:
        for record in self.chains:
            if record.chain_id == chain_id:
                return record
        raise KeyError(f"Sensorimotor chain '{chain_id}' not in abstraction")

    # -- boundary -----------------------------------------------------------

    def any_live_solver_eligible(self) -> bool:
        """Always False in 3.0D-7Z."""
        return any(
            record.live_solver_eligible
            for record in (
                *self.sensorimotor_inputs,
                *self.gf_integration_boundaries,
                *self.gf_outputs,
                *self.behavioral_states,
                *self.motor_routes,
                *self.escape_mode_distinctions,
                *self.unavailable_integration_quantities,
                *self.validation_targets,
                *self.chains,
            )
        )

    def any_mechanistically_ready(self) -> bool:
        """Always False: no stage of the chain has a stated mechanism."""
        return any(
            record.mechanistic_live_solver_ready for record in self.gf_outputs
        )

    def any_hodgkin_huxley_kinetics(self) -> bool:
        """Always False: no Hodgkin-Huxley dynamics exist in this layer."""
        return any(
            record.mechanistic_live_solver_ready for record in self.gf_outputs
        ) or any(
            record.is_live_solver_eligible
            for record in self.gf_integration_boundaries
        )

    def any_synaptic_current(self) -> bool:
        """Always False: no synaptic current is computed anywhere in the
        chain."""
        return any(
            record.is_membrane_current
            for record in self.gf_integration_boundaries
        )

    def any_conductance(self) -> bool:
        """Always False: no conductance exists in this layer."""
        return any(
            record.has_conductance
            or record.has_reversal_potential
            for record in self.gf_integration_boundaries
        ) or any(
            record.has_quantitative_parameter for record in self.sensorimotor_inputs
        )

    def any_membrane_voltage(self) -> bool:
        """Always False: no membrane voltage is represented anywhere."""
        return any(
            record.uses_membrane_voltage_representation
            or record.is_membrane_variable
            for record in self.sensorimotor_inputs
        ) or any(record.is_membrane_voltage for record in self.gf_outputs)

    def any_feature_as_membrane_variable(self) -> bool:
        """Always False: a 7Y feature is a stimulus coordinate."""
        return any(
            record.is_membrane_variable for record in self.sensorimotor_inputs
        )

    def any_gating_function(self) -> bool:
        """Always False: no state-dependent gating function exists here."""
        return any(
            record.gating_function_available
            for record in self.behavioral_states
        )

    def any_transition_probability(self) -> bool:
        """Always False: no state-transition probability exists here."""
        return any(
            record.has_transition_probability
            or record.has_numeric_gate_parameter
            for record in self.behavioral_states
        )

    def any_numeric_decision_boundary(self) -> bool:
        """Always False: no short-versus-long decision threshold exists."""
        return any(
            record.is_numeric_decision_boundary
            or record.decision_threshold is not None
            or record.timing_boundary_ms is not None
            or record.mode_selection_probability is not None
            for record in self.escape_mode_distinctions
        )

    def any_numeric_decision_target(self) -> bool:
        """Always False: no validation target here is a number."""
        return any(
            record.is_numeric_decision_target for record in self.validation_targets
        )

    def any_target_value(self) -> bool:
        """Always False: every validation target is a statement."""
        return any(record.carries_a_value for record in self.validation_targets)

    def any_populated_integration_quantity(self) -> bool:
        """Always False: every unavailable quantity stays empty."""
        return any(
            record.value_is_populated
            for record in self.unavailable_integration_quantities
        )

    def any_spike_mechanism(self) -> bool:
        """Always False: no waveform, threshold, refractory or delay."""
        return any(
            record.has_spike_waveform
            or record.has_threshold_voltage
            or record.has_refractory_mechanism
            or record.has_conduction_delay
            for record in self.gf_outputs
        )

    def any_duplicated_parameter(self) -> bool:
        """Always False: 7V, 7W, 7X and 7Y own every parameter."""
        return any(
            record.owns_synaptic_parameters
            or record.owns_nmj_quantities
            or record.carries_a_synaptic_parameter
            for record in self.motor_routes
        )

    def any_chain_weight(self) -> bool:
        """Always False: the chain carries no weight, delay or probability."""
        return any(
            record.carries_weights
            or record.carries_delays
            or record.carries_probabilities
            for record in self.chains
        )

    def any_timestep_policy_change(self) -> bool:
        """Always False in 3.0D-7Z: this layer introduces no timestep."""
        return False

    def visual_feature_sources(self) -> Tuple[str, ...]:
        return tuple(
            record.feature_source_neuron
            for record in self.sensorimotor_inputs
        )

    def verifies_against_7y_7w_7x(self) -> None:
        """Assert every identifier this layer references actually exists.

        This changes nothing; it fails loudly if 7Y, 7W or 7X drift away from
        the identifiers recorded here. The lookups are LAZY so that this
        specification module never becomes an import-time dependency of the
        layers it references.
        """
        from .looming_abstraction import get_looming_abstraction
        from .synaptic_abstraction import get_synaptic_abstraction
        from .motor_output_abstraction import get_motor_output_abstraction

        seven_y = get_looming_abstraction()
        seven_w = get_synaptic_abstraction()
        seven_x = get_motor_output_abstraction()

        # 7Y: every referenced feature, neuron, term and quantity must exist.
        for record in self.sensorimotor_inputs:
            if record.feature_id not in seven_y.feature_ids():
                raise ValueError(
                    f"Sensorimotor input '{record.input_id}' references 7Y "
                    f"feature '{record.feature_id}', which does not exist."
                )
            if record.feature_source_neuron not in seven_y.neuron_classes():
                raise ValueError(
                    f"Sensorimotor input '{record.input_id}' references 7Y "
                    f"neuron '{record.feature_source_neuron}', which does not "
                    f"exist."
                )
            if record.feature_source_neuron not in seven_y.neurons_targeting(
                record.arrives_at
            ):
                raise ValueError(
                    f"Sensorimotor input '{record.input_id}' claims that 7Y "
                    f"neuron '{record.feature_source_neuron}' projects to "
                    f"'{record.arrives_at}', which 7Y does not record."
                )
        for boundary in self.gf_integration_boundaries:
            for feature_id in boundary.input_feature_ids:
                if feature_id not in seven_y.feature_ids():
                    raise ValueError(
                        f"GF integration boundary '{boundary.boundary_id}' "
                        f"references 7Y feature '{feature_id}', which does not "
                        f"exist."
                    )
            for term_id in boundary.referenced_7y_term_ids:
                if term_id not in seven_y.term_ids():
                    raise ValueError(
                        f"GF integration boundary '{boundary.boundary_id}' "
                        f"references 7Y term '{term_id}', which does not "
                        f"exist."
                    )

        # 7W: every referenced target and connection must exist.
        seven_w_targets = {
            target.target_id
            for target in (
                *seven_w.validation_targets, *seven_w.following_targets
            )
        }
        seven_w_connections = set(seven_w.connection_ids())
        for route in self.motor_routes:
            for target_id in route.linked_7w_target_ids:
                if target_id not in seven_w_targets:
                    raise ValueError(
                        f"Motor route '{route.route_id}' references 7W target "
                        f"'{target_id}', which does not exist."
                    )
            for connection_id in route.linked_7w_connection_ids:
                if connection_id not in seven_w_connections:
                    raise ValueError(
                        f"Motor route '{route.route_id}' references 7W "
                        f"connection '{connection_id}', which does not exist."
                    )
        missing_targets = set(self.referenced_7w_targets) - seven_w_targets
        if missing_targets:
            raise ValueError(
                f"Referenced 7W targets do not exist: {sorted(missing_targets)}"
            )

        # 7X: every referenced output and quantity must exist.
        for route in self.motor_routes:
            if route.linked_7x_output_id not in seven_x.output_ids():
                raise ValueError(
                    f"Motor route '{route.route_id}' references 7X output "
                    f"'{route.linked_7x_output_id}', which does not exist."
                )
        missing_outputs = set(self.referenced_7x_outputs) - set(
            seven_x.output_ids()
        )
        if missing_outputs:
            raise ValueError(
                f"Referenced 7X outputs do not exist: "
                f"{sorted(missing_outputs)}"
            )

        # 7Y quantities, where linked.
        seven_y_quantities = set(seven_y.unavailable_ids())
        for record in self.unavailable_integration_quantities:
            if record.linked_7y_quantity_id is not None:
                if record.linked_7y_quantity_id not in seven_y_quantities:
                    raise ValueError(
                        f"Quantity '{record.quantity_id}' links to 7Y quantity "
                        f"'{record.linked_7y_quantity_id}', which does not "
                        f"exist."
                    )

        # 7V exclusions and 7W/7X requirements, where linked.
        from .synaptic_mechanism_registry import (
            get_synaptic_mechanism_registry,
        )

        excluded = set(get_synaptic_mechanism_registry().excluded_names())
        requirements = set(seven_w.requirement_ids())
        nmj_quantities = set(seven_x.unavailable_ids())
        for record in self.unavailable_integration_quantities:
            if record.linked_7v_excluded_name is not None:
                if record.linked_7v_excluded_name not in excluded:
                    raise ValueError(
                        f"Quantity '{record.quantity_id}' links to 7V "
                        f"exclusion '{record.linked_7v_excluded_name}', which "
                        f"does not exist."
                    )
            if record.linked_7w_requirement_id is not None:
                if record.linked_7w_requirement_id not in requirements:
                    raise ValueError(
                        f"Quantity '{record.quantity_id}' links to 7W "
                        f"requirement '{record.linked_7w_requirement_id}', "
                        f"which does not exist."
                    )
            if record.linked_7x_quantity_id is not None:
                if record.linked_7x_quantity_id not in nmj_quantities:
                    raise ValueError(
                        f"Quantity '{record.quantity_id}' links to 7X quantity "
                        f"'{record.linked_7x_quantity_id}', which does not "
                        f"exist."
                    )


# --- construction ------------------------------------------------------------


def _sensorimotor_inputs() -> Tuple[SensorimotorInputRecord, ...]:
    return (
        SensorimotorInputRecord(
            input_id="angular_velocity_to_gf",
            referenced_layer=LAYER_7Y,
            feature_id="angular_velocity",
            feature_source_neuron="LC4",
            arrives_at="GF",
            description=(
                "The angular-velocity feature of an approaching object, as "
                "specified at 3.0D-7Y, arriving at the GF sensory integration "
                "boundary."
            ),
            feature_representation="external_stimulus_feature",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_JANG_2023_AZIMUTHAL,
            ),
            notes=(
                "LC4 CARRIES THE VELOCITY FEATURE. Ache et al. 2019 state that "
                "'We attributed velocity encoding to input from lobula "
                "columnar type 4 (LC4) visual projection neurons' and show by "
                "EM reconstruction that LC4 synapses directly onto the GF. "
                "Jang et al. 2023 record that 'LC4 angular velocity "
                "contribution to the GF response increases as r/v decreases'. "
                "The FEATURE AND ITS SOURCE NEURON ARE OWNED BY 3.0D-7Y; this "
                "record names them and adds no quantity."
            ),
        ),
        SensorimotorInputRecord(
            input_id="angular_size_to_gf",
            referenced_layer=LAYER_7Y,
            feature_id="angular_size",
            feature_source_neuron="LPLC2",
            arrives_at="GF",
            description=(
                "The angular-size feature of an approaching object, as "
                "specified at 3.0D-7Y, arriving at the GF sensory integration "
                "boundary."
            ),
            feature_representation="external_stimulus_feature",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_JANG_2023_AZIMUTHAL,
            ),
            notes=(
                "LPLC2 CARRIES THE SIZE FEATURE. Ache et al. 2019 state that "
                "LPLC2 'provide the entire GF size component' and that 'LPLC2 "
                "and LC4 synapse directly onto the GF'. Jang et al. 2023 record "
                "that LPLC2's angular size contribution 'remains constant' "
                "while the LC4 velocity contribution varies. The radial motion "
                "opponency that makes LPLC2 looming-selective is owned by "
                "3.0D-7Y and is not repeated here."
            ),
        ),
    )


def _gf_integration_boundaries() -> Tuple[GFIntegrationBoundary, ...]:
    return (
        GFIntegrationBoundary(
            boundary_id="gf_sensory_integration_boundary",
            integrates_neuron="GF",
            input_record_ids=("angular_velocity_to_gf", "angular_size_to_gf"),
            input_feature_ids=("angular_velocity", "angular_size"),
            referenced_7y_term_ids=(
                "lc4_angular_velocity_term", "lplc2_angular_size_term",
                "gf_looming_response",
            ),
            combination_type=COMBINATION_QUALITATIVE_SUM,
            published_model_statement=(
                "Ache et al. 2019: 'A model summing a linear function of "
                "angular velocity (provided by LC4) and a Gaussian function of "
                "angular size (provided by LPLC2) replicates GF looming "
                "response dynamics and predicts the peak response time'."
            ),
            combination_is_qualitative=True,
            spatially_distributed_input=True,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_JANG_2023_AZIMUTHAL,
            ),
            notes=(
                "THE GF COMBINES THE TWO FEATURE STREAMS. The COMBINATION IS "
                "QUALITATIVE: a linear angular-velocity function and a "
                "Gaussian angular-size function, summed. The input is also "
                "SPATIALLY DISTRIBUTED: Jang et al. 2023 report that the "
                "giant fiber 'responds invariantly to looming stimuli across "
                "tested azimuthal locations' and that the LC4 and LPLC2 input "
                "has 'small, ipsilaterally restricted receptive fields'. NO "
                "COEFFICIENT, SLOPE, WIDTH, AMPLITUDE, OFFSET, WEIGHT, "
                "CONDUCTANCE, REVERSAL POTENTIAL OR THRESHOLD IS RECORDED, and "
                "the model structure is owned by 3.0D-7Y."
            ),
        ),
    )


def _gf_outputs() -> Tuple[GFOutputAbstraction, ...]:
    return (
        GFOutputAbstraction(
            output_id="gf_action_potential_timing",
            output_type=OUTPUT_SPIKE_TIMING,
            target_layer=LAYER_7W,
            target_description=(
                "The central GFS abstraction owned by 3.0D-7W, which holds "
                "the GF-to-TTM and GF-to-DLM pathway validation targets."
            ),
            behavioural_evidence=(
                "Ache et al. 2019: 'the timing of a single spike in the giant "
                "fiber (GF) descending neuron determines whether a fly uses a "
                "short or long takeoff when escaping a looming predator'. Ache "
                "et al. 2019 (Nat Neurosci) describe the GF as firing 'a "
                "single action potential to activate motor neurons in the "
                "ventral nerve cord (VNC)'."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_ACHE_2019_STATE_DEPENDENCE,
            ),
            notes=(
                "GF SPIKE TIMING IS BEHAVIOURALLY MEANINGFUL. The output of the "
                "integration boundary is the TIMING of a single action "
                "potential, and the sources establish that this timing selects "
                "between escape programs. That is an experimental finding about "
                "an OUTPUT, not a model of the mechanism that produces it. NO "
                "SPIKE WAVEFORM, THRESHOLD VOLTAGE, REFRACTORY MECHANISM, "
                "INITIATION DYNAMIC OR CONDUCTION DELAY IS RECORDED, and the "
                "numeric timing values remain owned by 3.0D-7W."
            ),
        ),
    )


def _behavioral_states() -> Tuple[BehavioralStateRecord, ...]:
    return (
        BehavioralStateRecord(
            state_id=STATE_PERCHED_NON_FLYING,
            state_kind="behavioural_context",
            described_as=(
                "The perched, non-flying behavioural context of the animal."
            ),
            coupling_to_visual_input=(
                "In this state Ache et al. 2019 report that the visual "
                "responses of both landing descending neurons are severely "
                "attenuated, and that escape motor patterns did not occur in "
                "response to looming stimuli in flight trials. The coupling "
                "between a looming stimulus and a motor program therefore "
                "cannot be assumed to be the same in every state."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_STATE_DEPENDENCE,
            ),
            notes=(
                "PERCHED / NON-FLYING IS AN EXPLICIT BOUNDARY, NOT A CONSTANT. "
                "Ache et al. 2019 state that 'visual responses of both DNs are "
                "severely attenuated during non-flight periods, effectively "
                "decoupling visual stimuli from the landing motor pathway when "
                "landing is inappropriate', and that 'information about the "
                "behavioral state, in this case flight vs. non-flight, must be "
                "integrated with sensory information to select the appropriate "
                "action'. NO GATING FUNCTION, GATING STRENGTH OR TRANSITION "
                "PROBABILITY IS RECORDED. The spike rates and behavioural "
                "response rates that source reports are observations of ITS "
                "OWN neurons in ITS OWN preparation, are not a gating function, "
                "and are not transferred to the GF here."
            ),
        ),
        BehavioralStateRecord(
            state_id=STATE_FLYING,
            state_kind="behavioural_context",
            described_as=(
                "The flying behavioural context of the animal."
            ),
            coupling_to_visual_input=(
                "In this state the same landing pathway is strongly driven, "
                "and Ache et al. 2019 report that 'descending neurons for "
                "escape, such as the Giant Fiber and parallel escape DNs, may "
                "conversely be decoupled from visual inputs during flight'. "
                "The coupling therefore differs in the two states."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_STATE_DEPENDENCE,
            ),
            notes=(
                "FLYING IS AN EXPLICIT BOUNDARY, NOT A CONSTANT. Ache et al. "
                "2019 report that the flight dependence of their two landing "
                "neurons has DISTINCT MECHANISMS: octopaminergic "
                "neuromodulation for DNp07, and feedback from the flight motor "
                "circuit for DNp10. Those mechanisms are described for those "
                "neurons in that preparation. NO GATE IS INHERITED FROM THEM "
                "FOR THE GF, no gating function is recorded, and no "
                "octopamine concentration, receptor identity or feedback "
                "strength is transferred to any neuron here."
            ),
        ),
    )


def _motor_routes() -> Tuple[MotorPathwayRoute, ...]:
    return (
        MotorPathwayRoute(
            route_id=ROUTE_TTM_JUMP,
            route_label="GF -> TTMn -> TTM",
            descending_neurons=("GF", "TTMn"),
            terminal_muscle="TTM",
            behavioural_role=(
                "The jump / short-mode escape route. The TTMn drives the "
                "tergotrochanteral muscle, whose activation launches the fly."
            ),
            linked_7w_connection_ids=("GF_TTMn",),
            linked_7w_target_ids=(
                "gf_to_ttm_latency", "ttm_refractory_period",
                "ttm_high_frequency_following",
            ),
            linked_7x_output_id="TTMn_TTM",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_AUGUSTIN_2019_GFS_MODEL, SOURCE_AUGUSTIN_JOVE_GFS,
                SOURCE_ACHE_2019_GF_LOOMING,
            ),
            notes=(
                "THE JUMP ROUTE IS NAMED, NOT PARAMETERISED. The GF-TTMn "
                "connection and its central synapse parameters are owned by "
                "3.0D-7V, the GF-to-TTM latency, refractory period and "
                "following targets by 3.0D-7W, and the TTMn-TTM neuromuscular "
                "junction by 3.0D-7X. This record links those identifiers and "
                "restates none of their values."
            ),
        ),
        MotorPathwayRoute(
            route_id=ROUTE_DLM_FLIGHT,
            route_label="GF -> PSI -> DLMn -> DLM",
            descending_neurons=("GF", "PSI", "DLMn"),
            terminal_muscle="DLM",
            behavioural_role=(
                "The flight-related route. The DLMn drives the dorsal "
                "longitudinal wing depressors, and its disynaptic activation "
                "follows the jump route."
            ),
            linked_7w_connection_ids=("GF_PSI", "PSI_DLMn"),
            linked_7w_target_ids=(
                "gf_to_dlm_latency", "dlm_refractory_period",
                "dlm_high_frequency_following",
            ),
            linked_7x_output_id="DLMn_DLM",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_AUGUSTIN_2019_GFS_MODEL, SOURCE_AUGUSTIN_JOVE_GFS,
                SOURCE_ACHE_2019_GF_LOOMING,
            ),
            notes=(
                "THE FLIGHT ROUTE IS NAMED, NOT PARAMETERISED. The GF-PSI and "
                "PSI-DLMn connections and their central synapse parameters are "
                "owned by 3.0D-7V, the GF-to-DLM latency, refractory period and "
                "following targets by 3.0D-7W, and the DLMn-DLM neuromuscular "
                "junction by 3.0D-7X. This record links those identifiers and "
                "restates none of their values."
            ),
        ),
    )


def _escape_mode_distinctions() -> Tuple[EscapeModeDistinction, ...]:
    return (
        EscapeModeDistinction(
            distinction_id=ESCAPE_MODE_DISTINCTION,
            gf_pathway_role=(
                "The GF pathway contributes to the SHORT-MODE takeoff: the fast "
                "escape in which the fly jumps without prior wing coordination. "
                "Ache et al. 2019 describe this circuit as mediating 'a rapid, "
                "short-duration escape takeoff in response to looming "
                "predators'."
            ),
            parallel_pathway_role=(
                "PARALLEL, GF-INDEPENDENT circuitry contributes to the "
                "LONG-MODE takeoff. Ache et al. 2019 refer to 'the Giant Fiber "
                "and parallel escape DNs' as distinct descending populations, "
                "so the long mode is not produced by the GF pathway alone. "
                "This layer does not name, model or claim that circuit."
            ),
            relative_timing_statement=(
                "RELATIVE TIMING BETWEEN THE PATHWAYS IS BIOLOGICALLY "
                "RELEVANT. Ache et al. 2019 state that 'the timing of a single "
                "spike in the giant fiber (GF) descending neuron determines "
                "whether a fly uses a short or long takeoff when escaping a "
                "looming predator', so which motor program is engaged depends "
                "on when each pathway fires relative to the other."
            ),
            relative_timing_is_biologically_relevant=True,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_ACHE_2019_STATE_DEPENDENCE,
            ),
            notes=(
                "THE SHORT / LONG DISTINCTION IS A STRUCTURAL FINDING. It "
                "states WHICH pathway contributes to WHICH program and THAT "
                "relative timing matters. It does NOT state a decision "
                "threshold, a timing boundary in milliseconds, a probability of "
                "either mode, or a selection rule, and none is created here. "
                "The GF-to-TTM and GF-to-DLM latencies that 3.0D-7W owns are "
                "pathway measurements, NOT a decision boundary, and they are "
                "referenced by name and never copied or combined into one."
            ),
        ),
    )


def _unavailable_integration_quantities() -> (
    Tuple[UnavailableIntegrationQuantity, ...]
):
    no_source = (
        "No source used by this checkpoint states it. Ache et al. 2019 (Curr "
        "Biol) is behind a subscription, so the project holds its abstract-level "
        "findings and not its equations; Ache et al. 2019 (Nat Neurosci) "
        "records spike rates and behavioural response rates for its own "
        "neurons but no GF parameter. "
    )
    return (
        UnavailableIntegrationQuantity(
            quantity_id="gf_spike_threshold",
            quantity_kind="spike_initiation_threshold",
            applies_to="GF",
            why_required=(
                "A mechanistic GF model needs a spike threshold to convert an "
                "integrated input into an action potential."
            ),
            why_unavailable=(
                "Ache et al. 2019 establish that the TIMING of the GF spike is "
                "behaviourally meaningful; neither Ache et al. 2019 paper "
                "states a GF spike threshold voltage. " + no_source
            ),
            linked_7y_quantity_id=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            linked_7v_excluded_name=None,
            must_not_be_inherited_from=(
                "any generic Drosophila threshold, and any threshold inferred "
                "from the behavioural timing finding"
            ),
        ),
        UnavailableIntegrationQuantity(
            quantity_id="gf_sensory_integration_coefficients",
            quantity_kind="phenomenological_model_coefficient",
            applies_to="GF sensory integration boundary",
            why_required=(
                "A working sensorimotor model needs the slope, the Gaussian "
                "amplitude, width and offset, and the relative weighting of the "
                "two terms to evaluate the published combination."
            ),
            why_unavailable=(
                "Ache et al. 2019 (Curr Biol) is behind a subscription "
                "(Europe PMC reports inPMC: N), so the project holds the model "
                "SENTENCE and not the equations. The model STRUCTURE is owned "
                "by 3.0D-7Y, whose lc4_angular_velocity_term, "
                "lplc2_angular_size_term and gf_looming_response records each "
                "record the functional FORM and no coefficient. Nothing is "
                "reconstructed, re-derived or fitted here. " + no_source
            ),
            linked_7y_quantity_id=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            linked_7v_excluded_name=None,
            must_not_be_inherited_from=(
                "the locust LGMD loom-detection model of Gabbiani et al. 1999, "
                "or any coefficient back-fitted to a GF response curve"
            ),
        ),
        UnavailableIntegrationQuantity(
            quantity_id="gf_sensory_synaptic_conductances",
            quantity_kind="synaptic_conductance",
            applies_to="LC4 -> GF and LPLC2 -> GF",
            why_required=(
                "A mechanistic pathway needs a synaptic conductance at each "
                "sensory input to turn feature activity into a current in the "
                "GF."
            ),
            why_unavailable=(
                "Ache et al. 2019 establish the connections by EM "
                "reconstruction but state no conductance for either. "
                + no_source
            ),
            linked_7y_quantity_id="lplc2_to_gf_synaptic_conductance",
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            linked_7v_excluded_name=None,
            must_not_be_inherited_from=(
                "the CENTRAL GF-TTMn chemical peak conductance owned by 3.0D-7V, "
                "which is a different synapse on a different connection and "
                "carries a documented discrepancy"
            ),
        ),
        UnavailableIntegrationQuantity(
            quantity_id="gf_sensory_synaptic_kinetics",
            quantity_kind="synaptic_time_constant",
            applies_to="LC4 -> GF and LPLC2 -> GF",
            why_required=(
                "A mechanistic pathway needs rise and decay time constants to "
                "shape the current each sensory input delivers to the GF."
            ),
            why_unavailable=(
                "Ache et al. 2019 establish the two sensory connections by EM "
                "reconstruction but state no synaptic time constant for either, "
                "and the LC4 and LPLC2 receptor kinetics 3.0D-7Y records "
                "unavailable are receptor quantities, not synaptic time "
                "constants. " + no_source
            ),
            linked_7y_quantity_id=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            linked_7v_excluded_name=None,
            must_not_be_inherited_from=(
                "the CENTRAL PSI->DLMn rise and decay times owned by 3.0D-7V, "
                "which belong to a central synapse and not to a visual input"
            ),
        ),
        UnavailableIntegrationQuantity(
            quantity_id="gf_spike_initiation_dynamics",
            quantity_kind="spike_generation_dynamics",
            applies_to="GF",
            why_required=(
                "A mechanistic GF model needs to know how the integrated input "
                "produces the action potential whose timing the sources show to "
                "be behaviourally meaningful."
            ),
            why_unavailable=(
                "The sources report the TIMING of the spike and its behavioural "
                "consequence, and describe the GF as firing a single action "
                "potential; none of them states the initiation dynamics, the "
                "waveform or the current underlying it. " + no_source
            ),
            linked_7y_quantity_id=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            linked_7v_excluded_name=None,
            must_not_be_inherited_from=(
                "any Hodgkin-Huxley channel set or current recorded for the GF "
                "at 3.0D-7S, which describes a mechanism this checkpoint "
                "explicitly does not implement"
            ),
        ),
        UnavailableIntegrationQuantity(
            quantity_id="state_dependent_gf_gating_function",
            quantity_kind="behavioural_gating_function",
            applies_to="the GF sensorimotor transform",
            why_required=(
                "A mechanistic model of the behavioural-state boundary would "
                "need a function mapping behavioural state onto the strength of "
                "the sensory-to-motor coupling."
            ),
            why_unavailable=(
                "Ache et al. 2019 (Nat Neurosci) establish that the coupling "
                "DIFFERS between flying and non-flight states and attribute the "
                "difference in their own neurons to octopaminergic "
                "neuromodulation and to feedback from the flight motor circuit. "
                "They state no gating function, no gating strength and no "
                "state-transition model for the GF, and no such quantity is "
                "transferred from their neurons. " + no_source
            ),
            linked_7y_quantity_id=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            linked_7v_excluded_name=None,
            must_not_be_inherited_from=(
                "the measured spike rates and behavioural response rates of "
                "DNp07 and DNp10, which are observations of those neurons and "
                "not a gating function"
            ),
        ),
        UnavailableIntegrationQuantity(
            quantity_id="short_vs_long_decision_boundary",
            quantity_kind="behavioural_decision_threshold",
            applies_to="the GF short-mode versus long-mode takeoff choice",
            why_required=(
                "A mechanistic model of escape-mode selection would need the "
                "GF spike timing, or a feature combination, that separates the "
                "short mode from the long mode."
            ),
            why_unavailable=(
                "Ache et al. 2019 attribute the choice to the timing of a "
                "single GF spike. No source used by this checkpoint states a "
                "decision threshold, a timing boundary or a selection rule. "
                + no_source
            ),
            linked_7y_quantity_id=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            linked_7v_excluded_name=None,
            must_not_be_inherited_from=(
                "the GF-to-TTM and GF-to-DLM latencies owned by 3.0D-7W, which "
                "are PATHWAY RESPONSE MEASUREMENTS and are not a decision "
                "boundary, and the difference between them"
            ),
        ),
        UnavailableIntegrationQuantity(
            quantity_id="motor_command_probability",
            quantity_kind="behavioural_probability",
            applies_to="the choice of a motor program at the decision boundary",
            why_required=(
                "A probabilistic model of the decision would need the "
                "probability of each motor program given the sensory input."
            ),
            why_unavailable=(
                "Ache et al. 2019 figure legends refer to 'takeoff or landing "
                "probability given the fly's behavioral state' as a framing for "
                "their experiments, but no source used by this checkpoint "
                "states a motor-command probability for the GF pathway. No "
                "probability is recorded or inferred here. " + no_source
            ),
            linked_7y_quantity_id=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            linked_7v_excluded_name=None,
            must_not_be_inherited_from=(
                "any behavioural response rate measured in another preparation "
                "or for another descending neuron"
            ),
        ),
        UnavailableIntegrationQuantity(
            quantity_id="behavioural_state_transition_model",
            quantity_kind="state_transition_dynamics",
            applies_to="the behavioural state boundary",
            why_required=(
                "A model that moves between states would need transition rates, "
                "hysteresis or a state-transition rule."
            ),
            why_unavailable=(
                "Ache et al. 2019 (Nat Neurosci) manipulate and describe "
                "behavioural state but state no transition model, no transition "
                "rate and no hysteresis parameter. " + no_source
            ),
            linked_7y_quantity_id=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            linked_7v_excluded_name=None,
            must_not_be_inherited_from=(
                "any locomotor or flight-state transition rate from another "
                "model, and any octopamine concentration reported for DNp07"
            ),
        ),
    )


def _validation_targets() -> Tuple[IntegrationValidationTarget, ...]:
    return (
        IntegrationValidationTarget(
            target_id="looming_features_reach_gf_integration_boundary",
            statement=(
                "The two looming features reach the GF sensory integration "
                "boundary as external stimulus coordinates, from LC4 and LPLC2 "
                "respectively."
            ),
            target_kind="structural_constraint",
            observable=(
                "The stimulus features carried at the sensorimotor input "
                "records and the feature identifiers they reference"
            ),
            requires_record="gf_sensory_integration_boundary",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_JANG_2023_AZIMUTHAL,
            ),
            notes=(
                "STRUCTURAL TARGET. The features reach the boundary as "
                "STIMULUS COORDINATES, not as a voltage, a current or a "
                "membrane state. A future model would have to carry both "
                "features into a combination step; it may not convert either "
                "into a membrane quantity."
            ),
        ),
        IntegrationValidationTarget(
            target_id="gf_output_is_spike_timing_not_a_continuous_command",
            statement=(
                "The GF output is represented as the timing of a single action "
                "potential rather than as a continuous motor command."
            ),
            target_kind="qualitative_observation",
            observable=(
                "The GF output record type and its behavioural evidence"
            ),
            requires_record="gf_action_potential_timing",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_ACHE_2019_STATE_DEPENDENCE,
            ),
            notes=(
                "EXPERIMENTALLY SUPPORTED. Ache et al. 2019 state that 'the "
                "timing of a single spike in the giant fiber (GF) descending "
                "neuron determines whether a fly uses a short or long takeoff'. "
                "The numeric timing values are owned by 3.0D-7W and are not "
                "restated here."
            ),
        ),
        IntegrationValidationTarget(
            target_id="ttm_pathway_stays_linked_to_jump_output",
            statement=(
                "The GF -> TTMn -> TTM route remains the jump route, linked to "
                "the 3.0D-7W jump targets and the 3.0D-7X TTM output."
            ),
            target_kind="structural_constraint",
            observable=(
                "The linked 3.0D-7W connection and target identifiers and the "
                "linked 3.0D-7X output identifier on the route record"
            ),
            requires_record=ROUTE_TTM_JUMP,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_AUGUSTIN_2019_GFS_MODEL, SOURCE_AUGUSTIN_JOVE_GFS,
            ),
            notes=(
                "STRUCTURAL TARGET. The route is preserved as a LINK to the "
                "layers that own it, not as a copy of their values."
            ),
        ),
        IntegrationValidationTarget(
            target_id="psi_dlm_pathway_stays_linked_to_flight_output",
            statement=(
                "The GF -> PSI -> DLMn -> DLM route remains the disynaptic "
                "flight-related route, linked to the 3.0D-7W flight targets "
                "and the 3.0D-7X DLM output."
            ),
            target_kind="structural_constraint",
            observable=(
                "The linked 3.0D-7W connection and target identifiers and the "
                "linked 3.0D-7X output identifier on the route record"
            ),
            requires_record=ROUTE_DLM_FLIGHT,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_AUGUSTIN_2019_GFS_MODEL, SOURCE_AUGUSTIN_JOVE_GFS,
            ),
            notes=(
                "STRUCTURAL TARGET. The route is preserved as a LINK to the "
                "layers that own it, not as a copy of their values."
            ),
        ),
        IntegrationValidationTarget(
            target_id="behavioural_state_is_represented_explicitly",
            statement=(
                "Behavioural state is an explicit record with at least the "
                "perched / non-flying and flying contexts, rather than an "
                "implicit constant."
            ),
            target_kind="qualitative_observation",
            observable=(
                "The behavioural state records and the coupling statement each "
                "carries"
            ),
            requires_record="behavioural_states",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_ACHE_2019_STATE_DEPENDENCE,),
            notes=(
                "EXPERIMENTALLY SUPPORTED. Ache et al. 2019 state that "
                "'information about the behavioral state, in this case flight "
                "vs. non-flight, must be integrated with sensory information to "
                "select the appropriate action'. The states are recorded; no "
                "gating function is."
            ),
        ),
        IntegrationValidationTarget(
            target_id="no_invented_quantitative_decision_rule_exists",
            statement=(
                "No quantitative decision rule exists anywhere in this layer: "
                "no decision threshold, no timing boundary, no gating function "
                "and no motor-command probability."
            ),
            target_kind="structural_constraint",
            observable=(
                "The absence of every numeric field on the decision, state and "
                "integration records"
            ),
            requires_record="decision boundary fields",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_ACHE_2019_STATE_DEPENDENCE,
            ),
            notes=(
                "STRUCTURAL TARGET. This is a NEGATIVE target: it asserts that "
                "the project does NOT have a decision rule, and the record "
                "types make that true by construction rather than by "
                "convention."
            ),
        ),
        IntegrationValidationTarget(
            target_id="short_long_pathway_distinction_is_preserved",
            statement=(
                "The short-mode GF route and the parallel GF-independent "
                "long-mode route remain distinguished, with relative timing "
                "recorded as the biologically relevant feature."
            ),
            target_kind="qualitative_observation",
            observable=(
                "The GF pathway role, the parallel pathway role and the "
                "relative-timing statement on the distinction record"
            ),
            requires_record=ESCAPE_MODE_DISTINCTION,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_ACHE_2019_STATE_DEPENDENCE,
            ),
            notes=(
                "EXPERIMENTALLY SUPPORTED. The distinction is recorded as a "
                "STRUCTURE and a TIMING RELATIONSHIP. NO NUMERIC BOUNDARY "
                "SEPARATES THE TWO MODES, and none is created."
            ),
        ),
        IntegrationValidationTarget(
            target_id="7w_and_7x_remain_the_owners",
            statement=(
                "3.0D-7W remains the owner of the GFS validation targets and "
                "3.0D-7X remains the owner of the NMJ and muscle-output "
                "quantities; 3.0D-7Y remains the owner of the visual features "
                "and 3.0D-7V the owner of the central synaptic parameters."
            ),
            target_kind="structural_constraint",
            observable=(
                "The linked identifiers on the route and integration records, "
                "and the reference lists on the layer"
            ),
            requires_record="referenced_7w_targets, referenced_7x_outputs",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_AUGUSTIN_2019_GFS_MODEL, SOURCE_ACHE_2019_GF_LOOMING,
            ),
            notes=(
                "STRUCTURAL TARGET. The layer VERIFIES at construction that "
                "every identifier it references exists in 7Y, 7W or 7X, so the "
                "reference cannot silently become a duplicate."
            ),
        ),
    )


def _chains() -> Tuple[SensorimotorChain, ...]:
    return (
        SensorimotorChain(
            chain_id="looming_to_motor_output_chain",
            description=(
                "The conceptual chain from an external looming stimulus to a "
                "motor output, recorded as stage NAMES with an owner per "
                "stage."
            ),
            stages=(
                _STAGE_STIMULUS,
                _STAGE_VISUAL_FEATURES,
                _STAGE_GF_INTEGRATION,
                _STAGE_GF_DECISION,
                _STAGE_CENTRAL_GFS,
                _STAGE_MOTOR_OUTPUT,
            ),
            stage_owners=(
                "external stimulus",
                LAYER_7Y,
                "3.0D-7Z boundary",
                "3.0D-7Z boundary",
                LAYER_7W,
                LAYER_7X,
            ),
            source_references=(
                SOURCE_ACHE_2019_GF_LOOMING, SOURCE_AUGUSTIN_2019_GFS_MODEL,
            ),
            notes=(
                "A SPECIFICATION CHAIN, NOT A SIMULATOR. The stages are: "
                "external looming stimulus -> 3.0D-7Y visual feature "
                "abstraction -> GF sensory integration boundary -> GF "
                "behavioural-output decision boundary -> 3.0D-7W central GFS "
                "abstraction -> 3.0D-7X motor / NMJ output abstraction. The "
                "visual-feature stage is owned by 3.0D-7Y, the central GFS "
                "stage by 3.0D-7W and the motor-output stage by 3.0D-7X, so "
                "this chain cannot claim territory those layers already hold. "
                "There is NO WEIGHT, NO DELAY and NO PROBABILITY between any "
                "two stages."
            ),
        ),
    )


def get_sensorimotor_integration() -> SensorimotorIntegration:
    """Return the sensorimotor integration / behavioral-decision abstraction.

    SPECIFICATION ONLY. Nothing here is implemented, connected, populated or
    activated: no Hodgkin-Huxley dynamics, no synaptic current, no GF spike
    generator, no gating function, no decision threshold, no probability, no
    timestep, no duplicated parameter, and no change to the passive backend or
    to 3.0D-7U, 3.0D-7V, 3.0D-7W, 3.0D-7X or 3.0D-7Y.
    """
    abstraction = SensorimotorIntegration(
        name="sensorimotor_integration_specification",
        source=(
            "Specification of the SENSORIMOTOR CHAIN that links the layers: an "
            "external looming stimulus to the 3.0D-7Y visual feature "
            "abstraction, through the GF sensory integration boundary and the "
            "GF behavioural-output decision boundary, to the 3.0D-7W central "
            "GFS abstraction and the 3.0D-7X motor/NMJ output abstraction. "
            "Records that the GF output is the timing of a single action "
            "potential, that behavioural state is an explicit boundary with "
            "perched/non-flying and flying contexts, that the TTM and DLM "
            "routes are named links, and that the short-mode GF route and the "
            "parallel GF-independent long-mode route are distinguished by "
            "relative timing. SPECIFICATION ONLY: no mechanism, no coefficient, "
            "no gating function, no decision threshold, no probability, and no "
            "record eligible for the live solver."
        ),
        model_id="ModelDBRepository/245415",
        model_citation=SOURCE_ACHE_2019_GF_LOOMING,
        sensorimotor_inputs=_sensorimotor_inputs(),
        gf_integration_boundaries=_gf_integration_boundaries(),
        gf_outputs=_gf_outputs(),
        behavioral_states=_behavioral_states(),
        motor_routes=_motor_routes(),
        escape_mode_distinctions=_escape_mode_distinctions(),
        unavailable_integration_quantities=(
            _unavailable_integration_quantities()
        ),
        validation_targets=_validation_targets(),
        chains=_chains(),
        referenced_7y_records=(
            "angular_velocity", "angular_size", "LC4", "LPLC2",
            "lc4_angular_velocity_term", "lplc2_angular_size_term",
            "gf_looming_response",
        ),
        referenced_7w_targets=(
            "gf_to_ttm_latency", "gf_to_dlm_latency", "ttm_refractory_period",
            "dlm_refractory_period", "ttm_high_frequency_following",
            "dlm_high_frequency_following",
        ),
        referenced_7x_outputs=("TTMn_TTM", "DLMn_DLM"),
        scope_note=(
            "A SPECIFICATION CHAIN, NOT A NUMERICAL NEURAL SIMULATOR. The chain "
            "is: external looming stimulus -> 3.0D-7Y visual feature "
            "abstraction -> GF sensory integration boundary -> GF "
            "behavioural-output decision boundary -> 3.0D-7W central GFS "
            "abstraction -> 3.0D-7X motor/NMJ output abstraction, recorded as "
            "stage NAMES with an owner per stage and with NO weight, NO delay "
            "and NO probability between any two stages. SENSORIMOTOR INPUT IS "
            "OWNED BY 3.0D-7Y. The angular_velocity and angular_size features "
            "arrive from LC4 and LPLC2 as EXTERNAL STIMULUS COORDINATES; they "
            "are not membrane variables, and the input record refuses to be "
            "marked as one. THE GF COMBINATION IS QUALITATIVE. Ache et al. "
            "2019 report a model summing a linear angular-velocity function "
            "with a Gaussian angular-size function, and the project records "
            "the SHAPE of that combination and NOTHING else: no slope, no "
            "width, no amplitude, no offset, no weight, no conductance, no "
            "reversal potential and no threshold, because the paper is behind a "
            "subscription and the model structure is already owned by 3.0D-7Y. "
            "THE INPUT IS SPATIALLY DISTRIBUTED, NOT WEIGHTED. Jang et al. 2023 "
            "report azimuthal invariance of the GF looming response, and NO "
            "bilateral or azimuthal weighting function is created. THE GF "
            "OUTPUT IS SPIKE TIMING, NOT A SPIKE MECHANISM. Ache et al. 2019 "
            "state that 'the timing of a single spike in the giant fiber (GF) "
            "descending neuron determines whether a fly uses a short or long "
            "takeoff', so the output is recorded as the timing of a single "
            "action potential with no waveform, no threshold voltage, no "
            "refractory mechanism and no conduction delay. BEHAVIORAL STATE IS "
            "AN EXPLICIT BOUNDARY, NOT A CONSTANT AND NOT A GATE. The perched "
            "/ non-flying and flying contexts are both recorded, because Ache "
            "et al. 2019 report that visual responses are 'severely attenuated "
            "during non-flight periods, effectively decoupling visual stimuli "
            "from the landing motor pathway when landing is inappropriate' and "
            "that sensory and motor networks are 'coupled or decoupled "
            "according to the behavioral state'. NO GATING FUNCTION, NO GATING "
            "STRENGTH AND NO STATE-TRANSITION PROBABILITY IS CREATED, and no "
            "spike rate or response rate measured for another neuron is "
            "transferred to the GF as one. THE MOTOR ROUTES ARE NAMED LINKS. "
            "GF -> TTMn -> TTM is the jump route and GF -> PSI -> DLMn -> DLM "
            "is the flight-related route, each linked to its 3.0D-7W connection "
            "and target identifiers and its 3.0D-7X output identifier. NO "
            "SYNAPTIC OR NMJ PARAMETER IS COPIED. THE SHORT / LONG "
            "DISTINCTION IS STRUCTURAL. The GF pathway contributes to the "
            "short-mode takeoff and parallel GF-independent circuitry "
            "contributes to the long mode, with relative timing between them "
            "biologically relevant; NO decision threshold, NO timing boundary "
            "and NO mode-selection probability is created, and the 3.0D-7W "
            "pathway latencies are NOT combined into one. NINE INTEGRATION "
            "QUANTITIES ARE REQUIRED AND UNAVAILABLE: GF spike threshold, GF "
            "sensory integration coefficients, GF sensory synaptic "
            "conductances, GF sensory synaptic kinetics, GF spike initiation "
            "dynamics, state-dependent GF gating function, the quantitative "
            "short-versus-long decision boundary, the quantitative "
            "motor-command probability and the quantitative behavioural-state "
            "transition model. Every one is structurally empty. 3.0D-7V, 7W, "
            "7X and 7Y REMAIN THE OWNERS of every parameter, and this layer "
            "verifies at construction that each identifier it references "
            "actually exists in them. This checkpoint establishes NO "
            "Hodgkin-Huxley dynamics, NO synaptic current, NO spike generator, "
            "NO gating function, NO decision rule, NO probability and NO "
            "simulator input, and it does NOT modify 3.0D-7U, 3.0D-7V, "
            "3.0D-7W, 3.0D-7X or 3.0D-7Y."
        ),
    )
    abstraction.verifies_against_7y_7w_7x()
    return abstraction
