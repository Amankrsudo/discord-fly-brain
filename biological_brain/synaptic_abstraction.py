"""Synaptic abstraction specification (3.0D-7W).

3.0D-7V recorded WHERE each synaptic number comes from: the verbatim
``gfpn.py`` line, the paper's own value, and the evidence status of each. This
checkpoint answers a different question: IF a synaptic simulator were ever
built, WHAT would it have to represent, and what does the project not have?

It is a specification, not an implementation. There is no current, no
conductance, no synaptic state, no time integration and no connection to any
compartment anywhere in this module.

What a future simulator would need, and what exists
----------------------------------------------------
The three GFS connections are structurally different and must stay that way:

    GF  -> TTMn    ELECTRICAL + CHEMICAL   (mixed)
    GF  -> PSI     ELECTRICAL + CHEMICAL   (mixed)
    PSI -> DLMn    CHEMICAL                (cholinergic, Dalpha7)

The paper states ONE chemical-synapse parameter set (peak 80 uS, rise 0.1 ms,
decay 1 ms, reversal 0 mV, delay 0.15 ms). That is a GENERIC MODEL-CHEMICAL-
SYNAPSE row, not a per-connection measurement of each GFS synapse. Only the
PSI->DLMn instance's own numbers coincide with it; the TTMn and PSI instances
have their own, different, source values, and the paper states no value for
them at all. This module preserves that distinction: the published set is
recorded once, at the scope the source gives it, and is NOT copied onto the
two connections the paper does not cover.

Where the electrical components are concerned, this module only REFERENCES the
existing records. It does not restate a gap conductance, and the 3.0D-7U
``g_gap`` unit conflict stays exactly as 7U left it: recorded, both sides
preserved, neither side preferred.

Pathway observations are targets, not parameters
-------------------------------------------------
Augustin et al. 2011 (PMC3182647) directly stimulated wild-type GFS
preparations and reported GF->TTM latency 0.7-1.2 ms, GF->DLM latency
1.3-1.7 ms, 1:1 following of TTM and DLM at 100 Hz, DLM failures beginning
above 100 Hz because the intermediary chemical PSI->DLMn synapse does not have
time to recover, TTM remaining 1:1 beyond 300 Hz, TTM refractory 1-4 ms and
DLM refractory 7-15 ms.

These are PATHWAY and OUTPUT observations of a preparation. They are encoded
here as validation targets against which a future simulator would be checked.
They are NOT neuron constants, and there is no field on any record in this
module that could place one into ``CompartmentElectrical``, ``CableParameters``
or a ``DynamicsModel``. A target carries a range and a level
(``pathway`` or ``motor_output``), and its ``is_intrinsic_neuron_parameter``
flag is False and cannot be set otherwise.

The DLM high-frequency failure is a statement about the PSI->DLMn synapse
lacking sufficient recovery time. It is recorded as a behavioural observation.
NO recovery time constant is derived from it, because the sources do not state
one, and no such constant is created here.

Dalpha7 stays an identity
-------------------------
Dalpha7 is experimentally required for PSI->DLMn transmission and for the
GF-mediated escape response (Fayyazuddin et al. 2006, PMC1382016; Mejia et
al. 2013). That is identity and function evidence, and it is all the project
has. No single-channel conductance, no alpha or beta rate constant, no opening
probability, no Q10, no reversal estimate and no release model exist in any
project source.

The receptor spec therefore has no numeric fields at all. It cannot be given
one, structurally. The phenomenological ``Exp2Syn`` the source uses contains no
receptor and no subunit, so nothing about Dalpha7 may be read back out of it.

Time parameters are synapse properties
--------------------------------------
The published rise (0.1 ms), decay (1 ms) and delay (0.15 ms) are stored
exactly. The 0.1 ms rise time is a SYNAPTIC RISE PARAMETER, NOT a simulation
timestep: a synaptic time constant describes the synapse, while the timestep
describes the integrator. No record in this module may claim to be a timestep,
and the project's numerical timestep policy is untouched.

Hard boundaries
---------------
``live_solver_eligible`` is False on every record and on the specification
itself, and cannot be set otherwise. This module:

- does NOT implement a synaptic current, conductance, exponential or synapse;
- does NOT import, modify or get imported by ``PassiveCableModel``,
  ``PassiveNetwork``, ``PassiveNetworkState`` or ``CompartmentElectrical``;
- does NOT implement Hodgkin-Huxley kinetics;
- does NOT implement vesicle, release, depression or recovery dynamics;
- does NOT implement Dalpha7 kinetics, and adds no such field;
- does NOT restate, convert, prefer or resolve the 3.0D-7U ``g_gap`` conflict,
  and introduces no corrected gap conductance;
- does NOT duplicate the 3.0D-7V records. Every available parameter below is a
  REFERENCE to a 7V record, so the two layers cannot drift apart;
- does NOT copy the 0.1 ms rise time into a timestep, and does not alter the
  numerical timestep policy.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

from .provenance import ParameterProvenance, ProvenanceRecord
from .synaptic_mechanism_registry import (
    CHEMICAL_DECAY_MS,
    CHEMICAL_DELAY_MS,
    CHEMICAL_PEAK_US,
    CHEMICAL_REVERSAL_MV,
    CHEMICAL_RISE_MS,
    DISCREPANCY_UNRESOLVED,
    SYNAPSE_GF_PSI,
    SYNAPSE_GF_TTMN,
    SYNAPSE_PSI_DLMN,
    TOPOLOGY_CHEMICAL,
    TOPOLOGY_MIXED,
    SynapticEvidenceStatus,
    SynapticMechanismRegistry,
    get_synaptic_mechanism_registry,
)


# --- connection types -------------------------------------------------------
#
# The three GFS connections are structurally different. These names are this
# module's own vocabulary for the specification; the 7V topology record remains
# the authority on what the source builds.

CONNECTION_ELECTRICAL_AND_CHEMICAL = "electrical_and_chemical"
CONNECTION_CHEMICAL = "chemical"


# --- scope of an available parameter ---------------------------------------
#
# The paper's chemical-synapse row is a GENERIC MODEL row. Recording that scope
# is the whole point of these two labels: a value the source states for a
# generic model synapse is not thereby a per-connection measurement of a GFS
# synapse.

SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE = (
    "generic_model_chemical_synapse"
)
SCOPE_CONNECTION_SPECIFIC_SOURCE = "connection_specific_source_value"


# --- validation target levels ----------------------------------------------
#
# A target is a property of a PATHWAY or of a MOTOR OUTPUT in a preparation. It
# is never a property of an individual neuron, and no target may be used as a
# neuron parameter.

LEVEL_PATHWAY = "pathway"
LEVEL_MOTOR_OUTPUT = "motor_output"

_INTRINSIC_REFUSAL = (
    "This is a PATHWAY or OUTPUT observation from directly stimulated "
    "wild-type GFS preparations. It is a VALIDATION TARGET for a future "
    "simulator, NOT an intrinsic property of any single neuron. It must NEVER "
    "be inserted into CompartmentElectrical, CableParameters or a "
    "DynamicsModel as a membrane, refractory or threshold constant."
)


class Availability(Enum):
    """Whether a quantity a mechanistic synapse would need actually exists."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


_NOT_LIVE = (
    "3.0D-7W IS A SPECIFICATION CHECKPOINT ONLY. This record is NOT eligible "
    "for the live solver: no synaptic current is implemented, no synaptic "
    "conductance is computed, no compartment is populated with a synapse, and "
    "the passive backend is unchanged."
)

_NO_TEMPORAL_USE = (
    "This is a SYNAPSE time parameter, NOT a simulation timestep. A synaptic "
    "rise time, decay time or delay describes the synapse; a timestep describes "
    "the integrator. Converting one into the other is a category error, and the "
    "project's numerical timestep policy is untouched by this record."
)

_NO_DALPHA7_NUMBERS = (
    "NO Dalpha7 KINETIC PARAMETER EXISTS IN ANY PROJECT SOURCE. Neither the "
    "published model nor any cited experimental paper states a single-channel "
    "conductance, an alpha or beta rate constant, an opening probability, a "
    "desensitization rate, a Q10, a reversal estimate or a release model. "
    "Dalpha7 is recorded as an experimentally supported receptor IDENTITY AND "
    "FUNCTION and nothing more."
)

_REFERENCES_7V = (
    "This is a REFERENCE to a 3.0D-7V record, not a copy of it. The 7V "
    "registry remains the single source of the verbatim source line, the "
    "paper's value and the provenance classification; 3.0D-7W does not "
    "duplicate or restate those."
)

_REFERENCES_ELECTRICAL = (
    "The electrical component's conductance is owned by the 3.0D-7E passive "
    "parameter record and the 3.0D-7T gap2 source extraction. The 3.0D-7U "
    "g_gap unit conflict remains UNRESOLVED with both sides preserved and "
    "neither side preferred. This module restates no gap conductance, "
    "converts none, and introduces no corrected value."
)

_PATHWAY_SOURCE = (
    "Augustin H, Allen MJ, Partridge L (2011). Electrophysiological recordings "
    "from the giant fiber pathway of D. melanogaster. J Vis Exp (54):e1709. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC3182647/ . Directly stimulated "
    "wild-type GFS preparations. The quantities reported are latencies, "
    "following ratios and refractory periods measured at the pathway and motor "
    "output level."
)

_DALPHA7_SOURCE = (
    "Fayyazuddin A, Zaheer MA, Hiesinger PR, Bellen HJ (2006). The nicotinic "
    "acetylcholine receptor Dalpha7 is required for an escape behavior in "
    "Drosophila. PLoS Biol 4(2):e402. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC1382016/ . Experimental "
    "requirement of Dalpha7 for PSI->DLMn transmission and for the "
    "GF-mediated escape response. States NO kinetic parameters."
)

_MODEL_SOURCE = (
    "Augustin H, Zylbertal A, Partridge L (2019). A computational model of the "
    "escape response latency in the giant fiber system of Drosophila "
    "melanogaster. eNeuro 6(2):ENEURO.0423-18.2019. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ (PMCID PMC6469880). "
    "ModelDB 245415, https://github.com/ModelDBRepository/245415 . Table 1 "
    "states ONE generic chemical-synapse parameter row, labelled a mixture of "
    "'standard value' and 'estimated'."
)


# --- A. connection type -----------------------------------------------------


@dataclass(frozen=True)
class SynapticConnectionSpec:
    """One GFS connection, specified.

    The electrical and chemical components are recorded separately, so a mixed
    connection is never described as either alone. Where an electrical
    component exists, the record only REFERENCES the 7E/7T/7U owners of its
    conductance; it states no gap conductance of its own.
    """

    synapse_id: str
    source_neuron: str
    target_neuron: str
    connection_type: str
    has_electrical_component: bool
    has_chemical_component: bool
    electrical_mechanism: Optional[str]
    chemical_mechanism: Optional[str]
    chemical_receptor: Optional[str]
    electrical_conductance_owner: Optional[str]
    electrical_conflict_references: Tuple[str, ...]
    linked_7v_topology: str
    available_parameter_refs: Tuple[str, ...]
    notes: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Connection '{self.synapse_id}' cannot be live-solver "
                f"eligible. 3.0D-7W specifies connections; it does not build "
                f"or connect them."
            )
        if self.connection_type == CONNECTION_ELECTRICAL_AND_CHEMICAL:
            if not (
                self.has_electrical_component
                and self.has_chemical_component
            ):
                raise ValueError(
                    f"Connection '{self.synapse_id}' is specified as electrical "
                    f"AND chemical and must carry both components."
                )
        elif self.connection_type == CONNECTION_CHEMICAL:
            if self.has_electrical_component:
                raise ValueError(
                    f"Connection '{self.synapse_id}' is specified as chemical "
                    f"and must NOT carry an electrical component."
                )
            if not self.has_chemical_component:
                raise ValueError(
                    f"Connection '{self.synapse_id}' is specified as chemical "
                    f"and must carry a chemical component."
                )
        else:
            raise ValueError(
                f"Connection '{self.synapse_id}' has unknown connection_type "
                f"'{self.connection_type}'"
            )
        if self.has_electrical_component and not self.electrical_mechanism:
            raise ValueError(
                f"Connection '{self.synapse_id}' has an electrical component "
                f"and must name its mechanism."
            )
        if self.has_electrical_component:
            if not self.electrical_conductance_owner:
                raise ValueError(
                    f"Connection '{self.synapse_id}' has an electrical "
                    f"component and must name the records that own its "
                    f"conductance."
                )
            if not self.electrical_conflict_references:
                raise ValueError(
                    f"Connection '{self.synapse_id}' has an electrical "
                    f"component and must reference the unresolved g_gap "
                    f"conflicts rather than restate a conductance."
                )
        if self.has_chemical_component and not self.chemical_mechanism:
            raise ValueError(
                f"Connection '{self.synapse_id}' has a chemical component and "
                f"must name its mechanism."
            )
        if not self.available_parameter_refs:
            raise ValueError(
                f"Connection '{self.synapse_id}' must reference the available "
                f"parameters a future simulator would read."
            )

    @property
    def is_mixed(self) -> bool:
        return self.connection_type == CONNECTION_ELECTRICAL_AND_CHEMICAL

    @property
    def is_chemical_only(self) -> bool:
        return self.connection_type == CONNECTION_CHEMICAL


# --- B/C. available parameters, with evidence classification ----------------


@dataclass(frozen=True)
class SynapticParameterSpec:
    """One quantity a future synaptic simulator would need to READ.

    This record states the parameter a simulator would consume, the scope at
    which its source states it, and how well the source supports it. The
    verbatim line, the paper's number and the provenance classification are NOT
    repeated here: ``linked_7v_quantity`` points at the 7V record that owns
    them, so the two layers cannot drift apart.

    ``is_connection_specific`` is False for the paper's generic chemical-
    synapse row. The paper states one row; it does not state that row as a
    measurement of each individual GFS synapse, and this module does not
    promote it into one.
    """

    parameter_id: str
    synapse_id: str
    parameter_kind: str
    value: float
    unit: str
    scope: str
    is_connection_specific: bool
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    linked_7v_quantity: str
    limitations: str
    is_simulation_timestep: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Synaptic parameter '{self.parameter_id}' cannot be "
                f"live-solver eligible. Specifying a parameter does not "
                f"authorize computing a current from it."
            )
        if self.is_simulation_timestep:
            raise ValueError(
                f"Synaptic parameter '{self.parameter_id}' cannot claim to be "
                f"a simulation timestep. A synaptic rise time, decay time or "
                f"delay is a property of the synapse, not of the integrator."
            )
        if not self.linked_7v_quantity:
            raise ValueError(
                f"Synaptic parameter '{self.parameter_id}' must reference its "
                f"3.0D-7V record rather than restate it."
            )
        if self.scope not in (
            SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE,
            SCOPE_CONNECTION_SPECIFIC_SOURCE,
        ):
            raise ValueError(
                f"Synaptic parameter '{self.parameter_id}' has unknown scope "
                f"'{self.scope}'"
            )
        if (
            self.scope == SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE
            and self.is_connection_specific
        ):
            raise ValueError(
                f"Synaptic parameter '{self.parameter_id}' is a generic model "
                f"synapse value and must NOT be marked connection specific."
            )

    @property
    def provenance(self) -> ProvenanceRecord:
        return ProvenanceRecord(
            self.provenance_category, _MODEL_SOURCE,
        )

    @property
    def is_direct_experimental_measurement(self) -> bool:
        """Always False: no synaptic parameter here is a direct measurement."""
        return False


# --- D. pathway validation targets -----------------------------------------


@dataclass(frozen=True)
class PathwayValidationTarget:
    """An experimentally observed pathway or output behaviour to validate against.

    A target is what a future simulator would be CHECKED against. It is not an
    input to one, and this record type has no field that could place it on a
    neuron.
    """

    target_id: str
    description: str
    level: str
    value_low: float
    value_high: float
    unit: str
    applies_to: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    is_intrinsic_neuron_parameter: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.is_intrinsic_neuron_parameter:
            raise ValueError(
                f"Validation target '{self.target_id}' must not be an "
                f"intrinsic neuron parameter. Pathway latencies, following "
                f"ratios and refractory periods are observed in a "
                f"preparation, not assigned to a single cell."
            )
        if self.live_solver_eligible:
            raise ValueError(
                f"Validation target '{self.target_id}' cannot be live-solver "
                f"eligible. A target is a check, never a solver input."
            )
        if self.level not in (LEVEL_PATHWAY, LEVEL_MOTOR_OUTPUT):
            raise ValueError(
                f"Validation target '{self.target_id}' has unknown level "
                f"'{self.level}'. Targets are pathway or motor-output "
                f"observations, never neuron-level parameters."
            )
        if self.value_low > self.value_high:
            raise ValueError(
                f"Validation target '{self.target_id}' has an inverted range: "
                f"{self.value_low} > {self.value_high}."
            )
        if self.evidence_status is not (
            SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED
        ):
            raise ValueError(
                f"Validation target '{self.target_id}' must carry the status "
                f"'experimentally_constrained': these are direct experimental "
                f"observations."
            )

    @property
    def is_range(self) -> bool:
        return self.value_low != self.value_high

    @property
    def as_tuple(self) -> Tuple[float, float]:
        return (self.value_low, self.value_high)

    @property
    def is_neuron_parameter_candidate(self) -> bool:
        """Always False: no target is ever a neuron parameter."""
        return False

    def limitations(self) -> str:
        return f"{self.notes} {_INTRINSIC_REFUSAL} {_NOT_LIVE}"


@dataclass(frozen=True)
class HighFrequencyFollowingTarget:
    """An observed high-frequency following behaviour.

    Encoded as the observed stimulus frequencies and the observed outcome, not
    as a rate parameter. ``failure_onset_above_hz`` records where the reported
    response starts to fail; it is an observation, not a fitted threshold, and
    no mechanism is derived from it.
    """

    target_id: str
    muscle_label: str
    follows_one_to_one_at_hz: Tuple[float, ...]
    remains_one_to_one_through_hz: Optional[float]
    failure_onset_above_hz: Optional[float]
    pathway: str
    limiting_factor_description: Optional[str]
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    is_intrinsic_neuron_parameter: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.is_intrinsic_neuron_parameter:
            raise ValueError(
                f"Following target '{self.target_id}' must not be an "
                f"intrinsic neuron parameter."
            )
        if self.live_solver_eligible:
            raise ValueError(
                f"Following target '{self.target_id}' cannot be live-solver "
                f"eligible."
            )
        if not self.follows_one_to_one_at_hz:
            raise ValueError(
                f"Following target '{self.target_id}' must record at least one "
                f"frequency at which 1:1 following was observed."
            )
        for frequency in self.follows_one_to_one_at_hz:
            if frequency <= 0:
                raise ValueError(
                    f"Following target '{self.target_id}' has a non-positive "
                    f"frequency {frequency}."
                )
        if (
            self.failure_onset_above_hz is not None
            and self.failure_onset_above_hz <= 0
        ):
            raise ValueError(
                f"Following target '{self.target_id}' has a non-positive "
                f"failure onset {self.failure_onset_above_hz}."
            )

    @property
    def failure_limited(self) -> bool:
        return self.failure_onset_above_hz is not None

    @property
    def derived_recovery_time_constant(self) -> None:
        """Always None.

        The DLM failure above 100 Hz is reported as insufficient recovery at
        the intermediary chemical PSI->DLMn synapse. No project source states a
        recovery time constant, and this record refuses to derive one from a
        failure frequency.
        """
        return None

    def limitations(self) -> str:
        parts = [self.notes, _INTRINSIC_REFUSAL]
        if self.limiting_factor_description:
            parts.append(
                "The reported limiting factor is recorded as an observation. "
                + self.limiting_factor_description
                + " NO recovery time constant, release probability or vesicle "
                "parameter is derived from it, because no project source "
                "states one."
            )
        parts.append(_NOT_LIVE)
        return " ".join(parts)


# --- E. unavailable mechanistic requirements --------------------------------


@dataclass(frozen=True)
class MechanisticRequirement:
    """A quantity a mechanistic chemical synapse would need, and does not have.

    ``value`` is structurally None and cannot be set. ``value_is_populated`` is
    always False. The requirement is recorded so the gap is explicit and
    auditable, not to be filled in with a generic Drosophila number.
    """

    requirement_id: str
    requirement_kind: str
    why_required: str
    why_unavailable: str
    applies_to: str
    linked_7v_excluded_name: Optional[str]
    value: None = None
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Requirement '{self.requirement_id}' cannot be live-solver "
                f"eligible: it has no value to supply."
            )
        if self.value is not None:
            raise ValueError(
                f"Requirement '{self.requirement_id}' must remain unavailable. "
                f"No project source states this quantity, so no value may be "
                f"populated for it."
            )
        if not self.why_required or not self.why_unavailable:
            raise ValueError(
                f"Requirement '{self.requirement_id}' must state both why a "
                f"mechanistic synapse would need it and why it is unavailable."
            )

    @property
    def availability(self) -> Availability:
        return Availability.UNAVAILABLE

    @property
    def value_is_populated(self) -> bool:
        """Always False."""
        return False

    def limitations(self) -> str:
        return (
            f"REQUIRED BY A MECHANISTIC SYNAPSE, CURRENTLY UNAVAILABLE. "
            f"{self.why_required} {self.why_unavailable} This quantity stays "
            f"empty. It is NOT filled with a generic Drosophila value, with a "
            f"value borrowed from another preparation, or with a value "
            f"inferred from a behavioural observation. {_NOT_LIVE}"
        )


# --- F. Dalpha7 ------------------------------------------------------------


@dataclass(frozen=True)
class ReceptorAbstractionSpec:
    """Dalpha7 as an experimentally supported IDENTITY AND FUNCTION.

    This record type has NO numeric field of any kind: no conductance, no rate
    constant, no opening probability, no Q10, no reversal estimate. It cannot
    be given one through this path, which is the point.
    """

    receptor_identity: str
    synapse_id: str
    ion_permeability: str
    functional_evidence: str
    experimentally_supported: bool
    kinetics_available_for_live_solver: bool
    linked_7v_receptor: str
    prohibited_quantities: Tuple[str, ...]
    notes: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Receptor '{self.receptor_identity}' cannot be live-solver "
                f"eligible."
            )
        if self.kinetics_available_for_live_solver:
            raise ValueError(
                f"Receptor '{self.receptor_identity}' must not claim kinetics "
                f"are available for the live solver. No project source states "
                f"a single-channel conductance or any rate constant for it."
            )
        if not self.experimentally_supported:
            raise ValueError(
                f"Receptor '{self.receptor_identity}' must state its "
                f"experimental support."
            )
        if not self.prohibited_quantities:
            raise ValueError(
                f"Receptor '{self.receptor_identity}' must name the "
                f"quantities it is prohibited from carrying."
            )
        for required in (
            "alpha_rate", "beta_rate", "single_channel_conductance",
            "open_probability", "q10", "reversal_estimate", "release_model",
        ):
            if required not in self.prohibited_quantities:
                raise ValueError(
                    f"Receptor '{self.receptor_identity}' must prohibit "
                    f"'{required}'."
                )

    @property
    def has_quantitative_value(self) -> bool:
        """Always False: the record type carries no number."""
        return False

    def limitations(self) -> str:
        return (
            f"RECEPTOR IDENTITY AND FUNCTION ONLY, EXPERIMENTALLY SUPPORTED. "
            f"{self.notes} {_NO_DALPHA7_NUMBERS} {_NOT_LIVE}"
        )


# --- H. model time parameters ----------------------------------------------


@dataclass(frozen=True)
class SynapseTimeParameters:
    """The published chemical-synapse time parameters, stored exactly.

    These are the values a future simulator would read, at the scope the paper
    states them. Each is a SYNAPSE parameter. None is a timestep, and no
    record here may claim to be one.
    """

    rise_ms: float
    decay_ms: float
    delay_ms: float
    scope: str
    linked_7v_quantities: Tuple[str, ...]
    source_references: Tuple[str, ...]
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                "Synapse time parameters cannot be live-solver eligible."
            )
        if self.rise_ms != CHEMICAL_RISE_MS:
            raise ValueError(
                f"Rise time must be stored exactly as the published "
                f"{CHEMICAL_RISE_MS} ms, got {self.rise_ms}."
            )
        if self.decay_ms != CHEMICAL_DECAY_MS:
            raise ValueError(
                f"Decay time must be stored exactly as the published "
                f"{CHEMICAL_DECAY_MS} ms, got {self.decay_ms}."
            )
        if self.delay_ms != CHEMICAL_DELAY_MS:
            raise ValueError(
                f"Delay must be stored exactly as the published "
                f"{CHEMICAL_DELAY_MS} ms, got {self.delay_ms}."
            )
        if self.scope != SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE:
            raise ValueError(
                "The published time parameters are a generic model "
                "chemical-synapse row and must be recorded at that scope."
            )

    @property
    def any_is_timestep(self) -> bool:
        """Always False: none of these is a timestep."""
        return False

    def limitations(self) -> str:
        return (
            f"The published chemical-synapse rise ({self.rise_ms} ms), decay "
            f"({self.decay_ms} ms) and delay ({self.delay_ms} ms) are stored "
            f"exactly, at the scope the paper states them: a generic model "
            f"chemical synapse, NOT a per-connection measurement of each GFS "
            f"synapse. {_NO_TEMPORAL_USE} The project's numerical timestep "
            f"policy is NOT read, derived from or altered by this record. "
            f"{_NOT_LIVE}"
        )


# --- the specification ------------------------------------------------------


@dataclass(frozen=True)
class SynapticAbstraction:
    """What a future synaptic simulator would need. NOT that simulator.

    Assigns nothing, populates nothing, connects nothing. No compartment, no
    ``CableParameters``, no ``CompartmentElectrical``, no solver input is
    populated from this specification, and no solver module imports it.
    """

    name: str
    source: str
    model_id: str
    model_citation: str
    pathway_citation: str
    receptor_citation: str
    connections: Tuple[SynapticConnectionSpec, ...]
    parameters: Tuple[SynapticParameterSpec, ...]
    validation_targets: Tuple[PathwayValidationTarget, ...]
    following_targets: Tuple[HighFrequencyFollowingTarget, ...]
    unavailable_requirements: Tuple[MechanisticRequirement, ...]
    receptor_specs: Tuple[ReceptorAbstractionSpec, ...]
    time_parameters: SynapseTimeParameters
    referenced_conflicts: Tuple[str, ...]
    scope_note: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                "The synaptic abstraction cannot be live-solver eligible. It "
                "is a specification of what a future simulator would need."
            )

    # -- lookup ------------------------------------------------------------

    def connection(self, synapse_id: str) -> SynapticConnectionSpec:
        for record in self.connections:
            if record.synapse_id == synapse_id:
                return record
        raise KeyError(f"Connection '{synapse_id}' not in specification")

    def connection_ids(self) -> Tuple[str, ...]:
        return tuple(record.synapse_id for record in self.connections)

    def parameter(self, parameter_id: str) -> SynapticParameterSpec:
        for record in self.parameters:
            if record.parameter_id == parameter_id:
                return record
        raise KeyError(f"Parameter '{parameter_id}' not in specification")

    def parameters_for(self, synapse_id: str) -> Tuple[SynapticParameterSpec, ...]:
        return tuple(
            record
            for record in self.parameters
            if record.synapse_id == synapse_id
        )

    def validation_target(self, target_id: str) -> PathwayValidationTarget:
        for record in self.validation_targets:
            if record.target_id == target_id:
                return record
        raise KeyError(f"Validation target '{target_id}' not in specification")

    def following_target(self, target_id: str) -> HighFrequencyFollowingTarget:
        for record in self.following_targets:
            if record.target_id == target_id:
                return record
        raise KeyError(f"Following target '{target_id}' not in specification")

    def requirement(self, requirement_id: str) -> MechanisticRequirement:
        for record in self.unavailable_requirements:
            if record.requirement_id == requirement_id:
                return record
        raise KeyError(f"Requirement '{requirement_id}' not in specification")

    def requirement_ids(self) -> Tuple[str, ...]:
        return tuple(
            record.requirement_id for record in self.unavailable_requirements
        )

    def receptor(self, name: str) -> ReceptorAbstractionSpec:
        for record in self.receptor_specs:
            if record.receptor_identity == name:
                return record
        raise KeyError(f"Receptor '{name}' not in specification")

    def mixed_connections(self) -> Tuple[str, ...]:
        return tuple(
            record.synapse_id for record in self.connections if record.is_mixed
        )

    def chemical_only_connections(self) -> Tuple[str, ...]:
        return tuple(
            record.synapse_id
            for record in self.connections
            if record.is_chemical_only
        )

    # -- boundary ----------------------------------------------------------

    def any_live_solver_eligible(self) -> bool:
        """Always False in 3.0D-7W."""
        return any(
            record.live_solver_eligible
            for record in (
                *self.connections,
                *self.parameters,
                *self.validation_targets,
                *self.following_targets,
                *self.unavailable_requirements,
                *self.receptor_specs,
                self.time_parameters,
            )
        )

    def any_populated_requirement(self) -> bool:
        """Always False: every unavailable requirement stays empty."""
        return any(
            record.value_is_populated
            for record in self.unavailable_requirements
        )

    def any_timestep_claim(self) -> bool:
        """Always False: no record claims to be a simulation timestep."""
        return (
            any(record.is_simulation_timestep for record in self.parameters)
            or self.time_parameters.any_is_timestep
        )

    def any_intrinsic_neuron_parameter(self) -> bool:
        """Always False: no target is an intrinsic neuron constant."""
        return any(
            record.is_intrinsic_neuron_parameter
            for record in (*self.validation_targets, *self.following_targets)
        )

    def any_receptor_kinetics(self) -> bool:
        """Always False in 3.0D-7W: no receptor kinetics exist."""
        return any(
            record.kinetics_available_for_live_solver
            for record in self.receptor_specs
        )

    def generic_scope_parameters(self) -> Tuple[str, ...]:
        return tuple(
            record.parameter_id
            for record in self.parameters
            if record.scope == SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE
        )

    def connection_specific_parameters(self) -> Tuple[str, ...]:
        return tuple(
            record.parameter_id
            for record in self.parameters
            if record.scope == SCOPE_CONNECTION_SPECIFIC_SOURCE
        )

    def any_direct_experimental_measurement(self) -> bool:
        """Always False: no synaptic parameter is a direct measurement."""
        return any(
            record.is_direct_experimental_measurement
            for record in self.parameters
        )

    def verifies_against_provenance(self) -> None:
        """Assert this specification agrees with the 7V registry it references.

        Every available parameter here is a REFERENCE to a 7V record. This
        check confirms the reference resolves, that the 7V provenance
        classification is the one recorded here, and that the peak
        conductance discrepancy is still recorded as unresolved on the 7V side.
        It changes nothing; it only fails loudly if the layers drift apart.
        """
        registry = get_synaptic_mechanism_registry()
        by_key: Dict[Tuple[str, str], object] = {}
        for record in registry.quantities:
            by_key[(record.synapse_id, record.name)] = record
        for record in self.parameters:
            synapse_id, _, name = record.linked_7v_quantity.partition(".")
            source = by_key.get((synapse_id, name))
            if source is None:
                raise ValueError(
                    f"Parameter '{record.parameter_id}' references 7V record "
                    f"'{record.linked_7v_quantity}', which does not exist."
                )
            if source.provenance_category is not record.provenance_category:
                raise ValueError(
                    f"Parameter '{record.parameter_id}' claims provenance "
                    f"'{record.provenance_category.value}' but 7V record "
                    f"'{record.linked_7v_quantity}' is "
                    f"'{source.provenance_category.value}'. The layers have "
                    f"drifted apart."
                )
        peak = by_key.get((SYNAPSE_PSI_DLMN, "peak_conductance"))
        if peak is not None and peak.value_agreement != DISCREPANCY_UNRESOLVED:
            raise ValueError(
                "The 7V peak conductance discrepancy must remain recorded as "
                "unresolved. 3.0D-7W does not resolve it."
            )


# --- construction -----------------------------------------------------------


def _parameter(
    parameter_id: str,
    synapse_id: str,
    parameter_kind: str,
    value: float,
    unit: str,
    scope: str,
    is_connection_specific: bool,
    linked_7v_quantity: str,
    limitations: str,
) -> SynapticParameterSpec:
    registry = get_synaptic_mechanism_registry()
    synapse_id_7v, _, name_7v = linked_7v_quantity.partition(".")
    source = None
    for record in registry.quantities:
        if record.synapse_id == synapse_id_7v and record.name == name_7v:
            source = record
            break
    if source is None:
        raise ValueError(
            f"Parameter '{parameter_id}' references 7V record "
            f"'{linked_7v_quantity}', which does not exist."
        )
    return SynapticParameterSpec(
        parameter_id=parameter_id,
        synapse_id=synapse_id,
        parameter_kind=parameter_kind,
        value=value,
        unit=unit,
        scope=scope,
        is_connection_specific=is_connection_specific,
        evidence_status=source.evidence_status,
        provenance_category=source.provenance_category,
        linked_7v_quantity=linked_7v_quantity,
        limitations=f"{limitations} {_REFERENCES_7V} {_NOT_LIVE}",
    )


def _connections() -> Tuple[SynapticConnectionSpec, ...]:
    return (
        SynapticConnectionSpec(
            synapse_id=SYNAPSE_GF_TTMN,
            source_neuron="GF",
            target_neuron="TTMn",
            connection_type=CONNECTION_ELECTRICAL_AND_CHEMICAL,
            has_electrical_component=True,
            has_chemical_component=True,
            electrical_mechanism="gap2",
            chemical_mechanism="Exp2Syn",
            chemical_receptor=None,
            electrical_conductance_owner=(
                "3.0D-7E passive parameter records "
                "gap_junction_conductance_young and "
                "gap_junction_conductance_old; 3.0D-7T gap2 source extraction"
            ),
            electrical_conflict_references=(
                "g_gap_young_unit_conflict", "g_gap_old_unit_conflict",
            ),
            linked_7v_topology=SYNAPSE_GF_TTMN,
            available_parameter_refs=(
                "GF_TTMn.chemical_rise_time_ms",
                "GF_TTMn.chemical_decay_time_ms",
                "GF_TTMn.chemical_reversal_mv",
                "GF_TTMn.chemical_delay_ms",
                "GF_TTMn.chemical_peak_conductance",
            ),
            notes=(
                "MIXED ELECTRICAL AND CHEMICAL. A future simulator would have "
                "to represent BOTH components on this one connection: a "
                "gap2-mediated electrical component and an Exp2Syn "
                "phenomenological chemical component. The source gives this "
                "chemical component its OWN parameters, which differ from the "
                "paper's single chemical-synapse row, and it gives them a "
                "chemical weight of 0.00 in the default parameter set, so the "
                "chemical component contributes no conductance there. That is "
                "a fact about the parameter set, NOT a statement that the "
                "synapse is purely electrical. " + _REFERENCES_ELECTRICAL
            ),
        ),
        SynapticConnectionSpec(
            synapse_id=SYNAPSE_GF_PSI,
            source_neuron="GF",
            target_neuron="PSI",
            connection_type=CONNECTION_ELECTRICAL_AND_CHEMICAL,
            has_electrical_component=True,
            has_chemical_component=True,
            electrical_mechanism="gap2",
            chemical_mechanism="Exp2Syn",
            chemical_receptor=None,
            electrical_conductance_owner=(
                "3.0D-7E passive parameter records "
                "gap_junction_conductance_young and "
                "gap_junction_conductance_old; 3.0D-7T gap2 source extraction"
            ),
            electrical_conflict_references=(
                "g_gap_young_unit_conflict", "g_gap_old_unit_conflict",
            ),
            linked_7v_topology=SYNAPSE_GF_PSI,
            available_parameter_refs=(
                "GF_PSI.chemical_rise_time_ms",
                "GF_PSI.chemical_decay_time_ms",
                "GF_PSI.chemical_reversal_mv",
                "GF_PSI.chemical_delay_ms",
                "GF_PSI.chemical_peak_conductance",
            ),
            notes=(
                "MIXED ELECTRICAL AND CHEMICAL. Structurally identical in kind "
                "to GF->TTMn: a future simulator would represent a gap2 "
                "electrical component and an Exp2Syn chemical component on the "
                "same connection. The source's own rise time for this "
                "instance coincides with the paper's row, its decay time and "
                "delay do not, and its chemical weight is 0.00. None of that "
                "makes the paper's row a measurement of THIS synapse. "
                + _REFERENCES_ELECTRICAL
            ),
        ),
        SynapticConnectionSpec(
            synapse_id=SYNAPSE_PSI_DLMN,
            source_neuron="PSI",
            target_neuron="DLMn",
            connection_type=CONNECTION_CHEMICAL,
            has_electrical_component=False,
            has_chemical_component=True,
            electrical_mechanism=None,
            chemical_mechanism="Exp2Syn",
            chemical_receptor="Dalpha7",
            electrical_conductance_owner=None,
            electrical_conflict_references=(),
            linked_7v_topology=SYNAPSE_PSI_DLMN,
            available_parameter_refs=(
                "chemical_rise_time_ms",
                "chemical_decay_time_ms",
                "chemical_reversal_mv",
                "chemical_delay_ms",
                "chemical_peak_conductance",
            ),
            notes=(
                "CHEMICAL, CHOLINERGIC, NO ELECTRICAL COMPONENT. This is the "
                "only chemical-only connection in the pathway and the only one "
                "whose own source values match the paper's single "
                "chemical-synapse row. A future simulator would model it as a "
                "phenomenological double-exponential process acting on a "
                "Dalpha7 nAChR, and it would be the connection that fails at "
                "high stimulus frequency. Dalpha7 is an experimentally "
                "supported identity; NO receptor kinetics exist for it."
            ),
        ),
    )


def _parameters() -> Tuple[SynapticParameterSpec, ...]:
    generic_note = (
        "The paper states this value ONCE, in a single generic "
        "chemical-synapse row of Table 1. It is a PUBLISHED MODEL PARAMETER at "
        "the scope of the model, NOT a direct experimental measurement of this "
        "individual GFS synapse and NOT a per-connection value."
    )
    source_note = (
        "This value is the SOURCE's own number for this specific connection. "
        "It is a PUBLISHED MODEL PARAMETER. The paper states no value for this "
        "connection, and the generic chemical-synapse row is NOT copied onto "
        "it."
    )
    records = [
        _parameter(
            parameter_id="chemical_peak_conductance",
            synapse_id=SYNAPSE_PSI_DLMN,
            parameter_kind="chemical_peak_conductance",
            value=CHEMICAL_PEAK_US,
            unit="uS",
            scope=SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE,
            is_connection_specific=False,
            linked_7v_quantity=f"{SYNAPSE_PSI_DLMN}.peak_conductance",
            limitations=(
                generic_note
                + " The source writes 0.08 with NO declared unit; the ratio of "
                "the two written numbers is exactly 1000. That is an OBSERVED, "
                "UNRESOLVED DISCREPANCY and is NOT a unit conversion. This "
                "checkpoint converts nothing, decides nothing and defines no "
                "corrected value."
            ),
        ),
        _parameter(
            parameter_id="chemical_rise_time_ms",
            synapse_id=SYNAPSE_PSI_DLMN,
            parameter_kind="chemical_rise_time_ms",
            value=CHEMICAL_RISE_MS,
            unit="ms",
            scope=SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE,
            is_connection_specific=False,
            linked_7v_quantity=f"{SYNAPSE_PSI_DLMN}.rise_tau",
            limitations=generic_note + " " + _NO_TEMPORAL_USE,
        ),
        _parameter(
            parameter_id="chemical_decay_time_ms",
            synapse_id=SYNAPSE_PSI_DLMN,
            parameter_kind="chemical_decay_time_ms",
            value=CHEMICAL_DECAY_MS,
            unit="ms",
            scope=SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE,
            is_connection_specific=False,
            linked_7v_quantity=f"{SYNAPSE_PSI_DLMN}.decay_tau",
            limitations=generic_note + " " + _NO_TEMPORAL_USE,
        ),
        _parameter(
            parameter_id="chemical_reversal_mv",
            synapse_id=SYNAPSE_PSI_DLMN,
            parameter_kind="chemical_reversal_mv",
            value=CHEMICAL_REVERSAL_MV,
            unit="mV",
            scope=SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE,
            is_connection_specific=False,
            linked_7v_quantity=f"{SYNAPSE_PSI_DLMN}.reversal_potential",
            limitations=(
                generic_note
                + " A reversal potential of 0 mV is a STANDARD VALUE of the "
                "phenomenological model, not a measured Dalpha7 reversal "
                "potential, and it must not be read back out as one."
            ),
        ),
        _parameter(
            parameter_id="chemical_delay_ms",
            synapse_id=SYNAPSE_PSI_DLMN,
            parameter_kind="chemical_delay_ms",
            value=CHEMICAL_DELAY_MS,
            unit="ms",
            scope=SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE,
            is_connection_specific=False,
            linked_7v_quantity=f"{SYNAPSE_PSI_DLMN}.delay",
            limitations=(
                generic_note
                + " This is a connection-construction argument in the source, "
                "NOT a simulation timestep. " + _NO_TEMPORAL_USE
            ),
        ),
    ]

    # The two mixed connections carry the SOURCE's own values. The paper
    # states none for them, and the generic row is deliberately not applied.
    source_values = (
        (SYNAPSE_GF_TTMN, "rise_tau", "chemical_rise_time_ms", "ms"),
        (SYNAPSE_GF_TTMN, "decay_tau", "chemical_decay_time_ms", "ms"),
        (SYNAPSE_GF_TTMN, "reversal_potential", "chemical_reversal_mv", "mV"),
        (SYNAPSE_GF_TTMN, "delay", "chemical_delay_ms", "ms"),
        (SYNAPSE_GF_PSI, "rise_tau", "chemical_rise_time_ms", "ms"),
        (SYNAPSE_GF_PSI, "decay_tau", "chemical_decay_time_ms", "ms"),
        (SYNAPSE_GF_PSI, "reversal_potential", "chemical_reversal_mv", "mV"),
        (SYNAPSE_GF_PSI, "delay", "chemical_delay_ms", "ms"),
    )
    registry = get_synaptic_mechanism_registry()
    for synapse_id, name_7v, kind, unit in source_values:
        source = next(
            record
            for record in registry.quantities
            if record.synapse_id == synapse_id and record.name == name_7v
        )
        records.append(
            _parameter(
                parameter_id=f"{synapse_id}.{kind}",
                synapse_id=synapse_id,
                parameter_kind=kind,
                value=source.source_value,
                unit=source.source_unit or unit,
                scope=SCOPE_CONNECTION_SPECIFIC_SOURCE,
                is_connection_specific=True,
                linked_7v_quantity=f"{synapse_id}.{name_7v}",
                limitations=(
                    source_note
                    + (
                        " The source's chemical weight for this connection is "
                        "0.00 in the default parameter set, so this chemical "
                        "component contributes NO conductance there. That is a "
                        "property of the parameter set, not of the synapse."
                        if name_7v == "rise_tau"
                        else ""
                    )
                    + " "
                    + (
                        _NO_TEMPORAL_USE
                        if unit == "ms"
                        else ""
                    )
                ),
            )
        )

    for synapse_id in (SYNAPSE_GF_TTMN, SYNAPSE_GF_PSI):
        source = next(
            record
            for record in registry.quantities
            if record.synapse_id == synapse_id
            and record.name == "peak_conductance"
        )
        records.append(
            _parameter(
                parameter_id=f"{synapse_id}.chemical_peak_conductance",
                synapse_id=synapse_id,
                parameter_kind="chemical_peak_conductance",
                value=source.source_value,
                unit=source.source_unit or "no_declared_unit",
                scope=SCOPE_CONNECTION_SPECIFIC_SOURCE,
                is_connection_specific=True,
                linked_7v_quantity=f"{synapse_id}.peak_conductance",
                limitations=(
                    source_note
                    + " The source declares NO UNIT for this weight. The "
                    "paper's 80 uS is a GENERIC model row and is NOT applied "
                    "here: it is not this connection's value, and the "
                    "unresolved 1000-fold discrepancy between the two written "
                    "numbers is not settled by this checkpoint."
                ),
            )
        )
    return tuple(records)


def _validation_targets() -> Tuple[PathwayValidationTarget, ...]:
    return (
        PathwayValidationTarget(
            target_id="gf_to_ttm_latency",
            description=(
                "Latency from directly stimulating the GF to a TTM response, "
                "in directly stimulated wild-type GFS preparations."
            ),
            level=LEVEL_PATHWAY,
            value_low=0.7,
            value_high=1.2,
            unit="ms",
            applies_to=SYNAPSE_GF_TTMN,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=ParameterProvenance.EXPERIMENTALLY_CONSTRAINED,
            source_references=(_PATHWAY_SOURCE,),
            notes=(
                "REPORTED RANGE 0.7 to 1.2 ms. A future synaptic simulator "
                "would be validated by whether its GF->TTM latency falls in "
                "this range under the reported stimulation conditions. The "
                "range is used as a check on an output, never as a parameter "
                "of the GF, the TTMn or the synapse between them."
            ),
        ),
        PathwayValidationTarget(
            target_id="gf_to_dlm_latency",
            description=(
                "Latency from directly stimulating the GF to a DLM response. "
                "This is the path THROUGH the chemical PSI->DLMn synapse, so "
                "it is the primary pathway-level check on that synapse."
            ),
            level=LEVEL_PATHWAY,
            value_low=1.3,
            value_high=1.7,
            unit="ms",
            applies_to=SYNAPSE_PSI_DLMN,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=ParameterProvenance.EXPERIMENTALLY_CONSTRAINED,
            source_references=(_PATHWAY_SOURCE,),
            notes=(
                "REPORTED RANGE 1.3 to 1.7 ms. This target spans TWO "
                "connections, the electrical-plus-chemical GF->PSI and the "
                "chemical PSI->DLMn, so it constrains the pathway rather than "
                "either synapse alone. The range is a check on an output and "
                "is NEVER a synaptic delay parameter; the published 0.15 ms "
                "synaptic delay and this 1.3-1.7 ms pathway latency are "
                "different quantities and must not be conflated."
            ),
        ),
        PathwayValidationTarget(
            target_id="ttm_refractory_period",
            description=(
                "Reported TTM refractory period in directly stimulated "
                "wild-type GFS preparations."
            ),
            level=LEVEL_MOTOR_OUTPUT,
            value_low=1.0,
            value_high=4.0,
            unit="ms",
            applies_to="TTM motor output",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=ParameterProvenance.EXPERIMENTALLY_CONSTRAINED,
            source_references=(_PATHWAY_SOURCE,),
            notes=(
                "REPORTED RANGE 1 to 4 ms. This is an observed refractory "
                "PERIOD OF THE TTM RESPONSE in a preparation. It is NOT an "
                "intrinsic refractory constant of the TTMn, it is not a "
                "threshold parameter, and it is not a property of the "
                "GF->TTMn synapse. The wide reported range is preserved as "
                "given and is NOT narrowed, averaged or fitted."
            ),
        ),
        PathwayValidationTarget(
            target_id="dlm_refractory_period",
            description=(
                "Reported DLM refractory period in directly stimulated "
                "wild-type GFS preparations."
            ),
            level=LEVEL_MOTOR_OUTPUT,
            value_low=7.0,
            value_high=15.0,
            unit="ms",
            applies_to="DLM motor output",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=ParameterProvenance.EXPERIMENTALLY_CONSTRAINED,
            source_references=(_PATHWAY_SOURCE,),
            notes=(
                "REPORTED RANGE 7 to 15 ms. The DLM refractory period is much "
                "LONGER than the TTM's, which is consistent with the reported "
                "limitation of the intermediary chemical PSI->DLMn synapse at "
                "high frequency. It is an observed refractory PERIOD OF THE "
                "DLM RESPONSE, NOT an intrinsic refractory constant of the "
                "DLMn and NOT a depression parameter of the synapse. No "
                "recovery time constant is derived from it. The reported range "
                "is preserved as given."
            ),
        ),
    )


def _following_targets() -> Tuple[HighFrequencyFollowingTarget, ...]:
    return (
        HighFrequencyFollowingTarget(
            target_id="ttm_high_frequency_following",
            muscle_label="TTM",
            follows_one_to_one_at_hz=(100.0, 300.0),
            remains_one_to_one_through_hz=300.0,
            failure_onset_above_hz=None,
            pathway="GF -> TTMn (mixed electrical and chemical)",
            limiting_factor_description=None,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=ParameterProvenance.EXPERIMENTALLY_CONSTRAINED,
            source_references=(_PATHWAY_SOURCE,),
            notes=(
                "OBSERVED 1:1 FOLLOWING. TTM follows 1:1 at 100 Hz and REMAINS "
                "1:1 BEYOND 300 Hz under the reported experimental conditions. "
                "No failure was reported for TTM within the tested range, so "
                "NO failure frequency is recorded and none is invented. A "
                "future simulator would be validated by whether its TTM output "
                "sustains 1:1 following across this range."
            ),
        ),
        HighFrequencyFollowingTarget(
            target_id="dlm_high_frequency_following",
            muscle_label="DLM",
            follows_one_to_one_at_hz=(100.0,),
            remains_one_to_one_through_hz=100.0,
            failure_onset_above_hz=100.0,
            pathway="GF -> PSI (mixed) -> PSI -> DLMn (chemical, Dalpha7)",
            limiting_factor_description=(
                "Above 100 Hz, DLM responses begin to FAIL because the "
                "intermediary CHEMICAL PSI->DLMn synapse does not have "
                "sufficient time to recover between stimuli."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=ParameterProvenance.EXPERIMENTALLY_CONSTRAINED,
            source_references=(_PATHWAY_SOURCE,),
            notes=(
                "OBSERVED 1:1 FOLLOWING AT 100 Hz, WITH FAILURES BEGINNING "
                "ABOVE 100 Hz. The failure onset is recorded as the reported "
                "behavioural observation 'above 100 Hz', NOT as a fitted "
                "threshold. The limitation is attributed to the intermediary "
                "chemical synapse's recovery, and this is where the project "
                "runs out of parameters: NO recovery time constant, NO release "
                "probability, NO vesicle pool and NO depletion model exist in "
                "any project source. The mechanism is therefore documented and "
                "left unimplemented, rather than reverse-engineered from the "
                "failure frequency."
            ),
        ),
    )


def _unavailable_requirements() -> Tuple[MechanisticRequirement, ...]:
    no_source = (
        "No project source states this quantity. The published model uses a "
        "phenomenological double-exponential Exp2Syn, which represents none of "
        "it, and reading these out of that form would be inventing them."
    )
    return (
        MechanisticRequirement(
            requirement_id="release_probability",
            requirement_kind="presynaptic_release",
            why_required=(
                "A mechanistic chemical synapse needs the probability that a "
                "presynaptic spike releases transmitter, to set the amplitude "
                "of the resulting current."
            ),
            why_unavailable=no_source,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="release_probability",
        ),
        MechanisticRequirement(
            requirement_id="vesicle_pool_and_depletion",
            requirement_kind="presynaptic_vesicle_dynamics",
            why_required=(
                "A mechanistic synapse needs a releasable vesicle pool and a "
                "depletion rule to model how transmission fails when stimuli "
                "arrive faster than the synapse can recover. This is precisely "
                "the behaviour reported to limit DLM following above 100 Hz."
            ),
            why_unavailable=no_source,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="vesicle_pool_size",
        ),
        MechanisticRequirement(
            requirement_id="recovery_time_constant",
            requirement_kind="presynaptic_recovery",
            why_required=(
                "A mechanistic synapse needs a recovery time constant to "
                "describe how quickly it returns to its releasable state after "
                "a failure."
            ),
            why_unavailable=(
                "The DLM high-frequency failure is reported as insufficient "
                "recovery at the PSI->DLMn synapse, but NO source states a "
                "recovery time constant and none may be derived from a failure "
                "frequency. " + no_source
            ),
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="synaptic_recovery_time_constant",
        ),
        MechanisticRequirement(
            requirement_id="transmitter_concentration_time_course",
            requirement_kind="transmitter_dynamics",
            why_required=(
                "A mechanistic synapse needs the transmitter concentration or "
                "occupancy at the receptor over time to drive receptor "
                "opening."
            ),
            why_unavailable=no_source,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name=None,
        ),
        MechanisticRequirement(
            requirement_id="dalpha7_receptor_kinetics",
            requirement_kind="receptor_gating",
            why_required=(
                "A mechanistic cholinergic synapse needs Dalpha7 gating "
                "kinetics, that is an alpha and a beta rate constant or "
                "equivalent, to compute the receptor's open probability."
            ),
            why_unavailable=(
                "Fayyazuddin et al. 2006 and Mejia et al. 2013 establish "
                "Dalpha7's IDENTITY and REQUIREMENT, and state no rate "
                "constants. " + _NO_DALPHA7_NUMBERS
            ),
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="dalpha7_alpha_rate",
        ),
        MechanisticRequirement(
            requirement_id="dalpha7_receptor_conductance",
            requirement_kind="receptor_conductance",
            why_required=(
                "A mechanistic synapse needs the single-channel conductance of "
                "the receptor to convert an open probability into a current."
            ),
            why_unavailable=_NO_DALPHA7_NUMBERS,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="dalpha7_single_channel_conductance",
        ),
        MechanisticRequirement(
            requirement_id="dalpha7_open_probability",
            requirement_kind="receptor_gating",
            why_required=(
                "A mechanistic synapse needs the receptor's steady-state open "
                "probability or its steady-state activation and desensitization "
                "rates."
            ),
            why_unavailable=_NO_DALPHA7_NUMBERS,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="dalpha7_opening_probability",
        ),
        MechanisticRequirement(
            requirement_id="dalpha7_receptor_density",
            requirement_kind="receptor_density",
            why_required=(
                "A mechanistic synapse needs the number of receptors at the "
                "postsynaptic site to scale the total synaptic conductance."
            ),
            why_unavailable=_NO_DALPHA7_NUMBERS,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="dalpha7_receptor_density",
        ),
        MechanisticRequirement(
            requirement_id="calcium_release_coupling",
            requirement_kind="presynaptic_calcium",
            why_required=(
                "A mechanistic synapse needs the coupling from presynaptic "
                "calcium to release, to explain why release depends on "
                "presynaptic activity."
            ),
            why_unavailable=no_source,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="calcium_dependent_release",
        ),
        MechanisticRequirement(
            requirement_id="presynaptic_calcium_concentration",
            requirement_kind="presynaptic_calcium",
            why_required=(
                "A mechanistic synapse needs the presynaptic calcium "
                "concentration, or the parameters to compute it, that drive "
                "release."
            ),
            why_unavailable=no_source,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="presynaptic_calcium_concentration",
        ),
        MechanisticRequirement(
            requirement_id="short_term_depression_parameters",
            requirement_kind="synaptic_plasticity",
            why_required=(
                "A mechanistic synapse needs short-term depression "
                "parameters, a use-dependent reduction in release, to model "
                "the reduced following reported at high frequency."
            ),
            why_unavailable=(
                "The reported DLM failure is attributed to the synapse not "
                "recovering in time, but NO project source states a depression "
                "parameter and none may be fitted to a following ratio. "
                + no_source
            ),
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="synaptic_depression_model",
        ),
        MechanisticRequirement(
            requirement_id="facilitation_parameters",
            requirement_kind="synaptic_plasticity",
            why_required=(
                "A mechanistic synapse needs facilitation parameters to "
                "describe any increase in release with repeated activity."
            ),
            why_unavailable=no_source,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="facilitation_model",
        ),
        MechanisticRequirement(
            requirement_id="q10_synaptic_scaling",
            requirement_kind="temperature_dependence",
            why_required=(
                "A mechanistic synapse needs a temperature coefficient to state "
                "how its kinetics change with temperature."
            ),
            why_unavailable=no_source,
            applies_to=SYNAPSE_PSI_DLMN,
            linked_7v_excluded_name="q10_synaptic_scaling",
        ),
    )


def _receptors() -> Tuple[ReceptorAbstractionSpec, ...]:
    return (
        ReceptorAbstractionSpec(
            receptor_identity="Dalpha7 nAChR",
            synapse_id=SYNAPSE_PSI_DLMN,
            ion_permeability="Na+ / Ca2+ permeable nicotinic cation",
            functional_evidence="experimentally supported",
            experimentally_supported=True,
            kinetics_available_for_live_solver=False,
            linked_7v_receptor="Dalpha7",
            prohibited_quantities=(
                "alpha_rate",
                "beta_rate",
                "single_channel_conductance",
                "open_probability",
                "q10",
                "reversal_estimate",
                "release_model",
                "desensitization_rate",
                "receptor_density",
            ),
            notes=(
                "Dalpha7 is experimentally REQUIRED for transmission at the "
                "identified cholinergic PSI->DLMn motor neuron synapse and "
                "therefore for the GF-mediated escape response. That is "
                "identity and function evidence and it is all the project has. "
                "The receptor spec carries no number and cannot be given one: "
                "it has no field for a conductance, a rate constant, an opening "
                "probability, a Q10, a reversal estimate or a release model. "
                "The published 0 mV synaptic reversal is a STANDARD VALUE of "
                "the phenomenological model and must NOT be read back out as a "
                "Dalpha7 reversal estimate. " + _DALPHA7_SOURCE
            ),
        ),
    )


def _time_parameters() -> SynapseTimeParameters:
    return SynapseTimeParameters(
        rise_ms=CHEMICAL_RISE_MS,
        decay_ms=CHEMICAL_DECAY_MS,
        delay_ms=CHEMICAL_DELAY_MS,
        scope=SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE,
        linked_7v_quantities=(
            f"{SYNAPSE_PSI_DLMN}.rise_tau",
            f"{SYNAPSE_PSI_DLMN}.decay_tau",
            f"{SYNAPSE_PSI_DLMN}.delay",
        ),
        source_references=(_MODEL_SOURCE,),
    )


def get_synaptic_abstraction() -> SynapticAbstraction:
    """Return the synaptic abstraction specification.

    SPECIFICATION ONLY. Nothing here is implemented, connected, populated or
    activated: no synaptic current, no conductance, no receptor kinetics, no
    vesicle or release dynamics, no change to any compartment, and no change to
    the passive backend, the timestep policy, 3.0D-7E, 3.0D-7S, 3.0D-7T or
    3.0D-7U. The 3.0D-7U ``g_gap`` unit conflict is referenced exactly as 7U
    left it and is not resolved.
    """
    abstraction = SynapticAbstraction(
        name="gfs_synaptic_abstraction_specification",
        source=(
            "Specification of what a future synaptic simulator for the "
            "Augustin et al. 2019 GFS model would have to represent: the "
            "structural type of each connection, the parameters actually "
            "available and the scope at which each source states them, the "
            "evidence classification of each, the experimentally observed "
            "pathway behaviours a future simulator would be validated "
            "against, and the mechanistic quantities a future simulator would "
            "need but that no project source supplies. SPECIFICATION ONLY: "
            "nothing is implemented, connected or activated, and no record is "
            "eligible for the live solver."
        ),
        model_id="ModelDBRepository/245415",
        model_citation=_MODEL_SOURCE,
        pathway_citation=_PATHWAY_SOURCE,
        receptor_citation=_DALPHA7_SOURCE,
        connections=_connections(),
        parameters=_parameters(),
        validation_targets=_validation_targets(),
        following_targets=_following_targets(),
        unavailable_requirements=_unavailable_requirements(),
        receptor_specs=_receptors(),
        time_parameters=_time_parameters(),
        referenced_conflicts=(
            "g_gap_young_unit_conflict", "g_gap_old_unit_conflict",
        ),
        scope_note=(
            "THREE CONNECTIONS, TWO KINDS. GF->TTMn and GF->PSI are MIXED "
            "electrical and chemical, and a future simulator would have to "
            "represent both components on each. PSI->DLMn is CHEMICAL and "
            "cholinergic, with NO electrical component. The electrical "
            "components are specified only by REFERENCE to the 3.0D-7E "
            "conductance records, the 3.0D-7T gap2 extraction and the 3.0D-7U "
            "g_gap unit conflicts, which remain UNRESOLVED; this checkpoint "
            "states no gap conductance and corrects none. THE PUBLISHED "
            "PARAMETERS ARE A GENERIC MODEL ROW. The paper states ONE "
            "chemical-synapse set: 80 uS, 0.1 ms rise, 1 ms decay, 0 mV "
            "reversal, 0.15 ms delay, labelled a mixture of 'standard value' "
            "and 'estimated'. These are PUBLISHED MODEL PARAMETERS, not direct "
            "experimental measurements, and they are NOT per-connection values "
            "for each GFS synapse. Only the PSI->DLMn instance's own source "
            "values coincide with that row; the TTMn and PSI instances have "
            "their own different values and the paper states none for them, so "
            "the generic row is deliberately NOT copied onto them. Every "
            "parameter here is a REFERENCE to a 3.0D-7V record rather than a "
            "copy, so the layers cannot drift apart. The 80 uS and the "
            "source's unitless 0.08 differ by a factor of exactly 1000; that "
            "discrepancy is observed, unresolved, and not a unit conversion. "
            "0.1 ms, 1 ms and 0.15 ms are stored EXACTLY as the published "
            "values. The 0.1 ms rise time IS a SYNAPTIC RISE PARAMETER, NOT a "
            "SIMULATION TIMESTEP, and the project's numerical timestep policy "
            "is untouched. VALIDATION TARGETS ARE NOT PARAMETERS. The reported "
            "latencies (0.7-1.2 ms GF->TTM, 1.3-1.7 ms GF->DLM), refractory "
            "periods (TTM 1-4 ms, DLM 7-15 ms) and following behaviours (TTM "
            "1:1 through at least 300 Hz; DLM 1:1 at 100 Hz with failures "
            "above 100 Hz) are PATHWAY and MOTOR OUTPUT observations of "
            "directly stimulated preparations. They are encoded as checks a "
            "future simulator would face and are NEVER neuron constants; no "
            "record here can be placed on a neuron. The DLM failure is "
            "attributed to insufficient recovery at the chemical PSI->DLMn "
            "synapse, and NO recovery time constant, release probability or "
            "vesicle parameter is derived from it, because no source states "
            "one. MECHANISTIC REQUIREMENTS STAY UNAVAILABLE. Release "
            "probability, vesicle pool and depletion, recovery, transmitter "
            "time course, Dalpha7 gating and conductance, receptor density, "
            "calcium coupling and short-term depression are all recorded as "
            "required and currently unavailable, and each is structurally empty. "
            "DALPHA7 REMAINS AN IDENTITY. Experimentally supported, with "
            "kinetics_available_for_live_solver false and no numeric field on "
            "the record that could hold a conductance, a rate constant, an "
            "opening probability, a Q10, a reversal estimate or a release "
            "model. This checkpoint establishes NO synaptic implementation, NO "
            "synaptic current, NO synaptic conductance, NO receptor kinetic "
            "model and NO resolution of the 3.0D-7U conflict."
        ),
    )
    abstraction.verifies_against_provenance()
    return abstraction
