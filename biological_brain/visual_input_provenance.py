"""LC4 -> GF and LPLC2 -> GF: explicit connection provenance (3.0D-8M).

WHAT 8M IS, AND WHAT IT IS NOT
--------------------------------
3.0D-7Y records, as a single combined record, that "LC4 and LPLC2 provide
direct input to the GF". That is true and it is the right level for a
provenance layer that wanted to say only "these neurons talk to the GF".

It is not the right level for the model. The two inputs are not
interchangeable: one carries angular VELOCITY and the other angular SIZE, they
are separately established, and they fail separately. Recent work makes that
sharp. Gaitanidis et al. 2025 found that escape-behaviour decline with age is
caused by "the selective decay of synaptic transmission between one specific
visual projection neuron type (LC4) and the dendrite of one identified
descending neuron (GF)" -- and, in the same experiments, that LPLC2-driven
escape does NOT decline the same way. A record that lumps them together cannot
express that, and would hide the single most behaviourally important fact
about this synapse.

So 8M splits the combined 7Y record into two EXPLICIT, SEPARATELY COMPARABLE
connections:

    LC4   -> GF   angular velocity / looming expansion
    LPLC2 -> GF   angular size

It composes the existing 3.0D-7W ``SynapticConnectionSpec`` rather than
redefining a connection type, so connection identity, the chemical/electrical
flags and the live-solver refusal all come from the abstraction the project
already has. What it adds is what that type cannot express: per-claim
provenance that separates ANATOMICAL evidence from FUNCTIONAL evidence, and
separates a paper's OWN DATA from a statement it CITES.

THAT LAST DISTINCTION IS NOT ACADEMIC
-------------------------------------
Reading these papers closely, two of the most quotable statements are not the
citing paper's own result:

  * Namiki et al. 2018 write that "Recent work has confirmed that LC4 neurons
    are functionally presynaptic to the GF and convey information about
    high-velocity looming expansion". That is them CITING von Reyn et al.
    2014. Namiki's own contribution there is glomerular innervation anatomy.

  * Dombrovski et al. 2025 write that "The GF receives direct visual input
    from only one other VPN type (LC4)". That is them CITING Ache et al. 2019.
    Their own data is the LPLC2->GF gradient.

Recording these as if they were independent confirmations would inflate the
apparent weight of evidence, which is the specific failure mode a provenance
layer exists to prevent. So :class:`ConnectionClaim` carries
``evidence_origin`` and both statements are marked ``CITED`` rather than
``OWN_DATA``.

NO QUANTITATIVE KINETICS, AND NONE IS ADDED
-------------------------------------------
The connection is real, direct, and functionally important. None of that makes
it parameterisable. No cited source states a synaptic conductance, a synaptic
weight, a synaptic delay, a release probability, a receptor identity with
affinity, a reversal potential or a receptor density for either connection.
Dombrovski et al. 2025 measured POSTSYNAPTIC GF depolarisation amplitude in
millivolts during looming stimuli; that is a response measurement, not a
synaptic parameter, and it is not a conductance. Gaitanidis et al. 2025 report
a synapse COUNT and a presynaptic active-zone marker density; those are
anatomy, not weight.

Accordingly this module introduces NO new biological numerical constant at all.
It adds no conductance, no weight, no delay, no release probability, no
current conversion, no voltage gain, no threshold, no rheobase and no escape
probability. The mathematical coefficients of the looming drive stay owned by
``gf_sensory_drive.py`` and are deliberately NOT duplicated or referenced by
value here: those coefficients describe a FITTED PHENOMENOLOGICAL GF response,
whereas these records describe the ANATOMICAL AND FUNCTIONAL connection. Two
different things, kept apart.

NOT A SIMULATOR INPUT
----------------------
These records cannot drive anything. ``live_solver_eligible`` is False and
enforced, ``quantitative_parameters`` is None and enforced, and
``couple_to_live_gf()`` raises. Aging, starvation, oxidative stress and
synaptic degradation are recorded as PROVENANCE CONTEXT only; implementing
them would be a biological-state model, which belongs to a later checkpoint.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

from .synaptic_abstraction import (
    CONNECTION_CHEMICAL,
    SynapticConnectionSpec,
)

MODEL_NAME_VISUAL_INPUT_PROVENANCE_V0 = "visual_input_provenance_v0"

CONNECTION_LC4_GF = "LC4_GF"
CONNECTION_LPLC2_GF = "LPLC2_GF"


# --- sources -----------------------------------------------------------------

SOURCE_ACHE_2019_LC4_GF = (
    "Ache JM, Polsky J, Alghailani S, Parekh R, Breads P, Peek MY, Bock DD, "
    "von Reyn CR, Card GM (2019). Neural basis for looming size and velocity "
    "encoding in the Drosophila giant fiber escape pathway. Curr Biol "
    "29(6):1073-1081.e4. PMID 30827912. "
    "https://pubmed.ncbi.nlm.nih.gov/30827912/ . ESTABLISHES the DIRECT "
    "connection: 'LPLC2 and LC4 synapse directly onto the GF via "
    "reconstruction in a fly brain electron microscopy (EM) volume'. This is "
    "ANATOMICAL evidence from EM reconstruction. It also establishes the "
    "feature split -- LC4 conveys angular velocity and LPLC2 angular size -- "
    "and that the two contributions sum to reproduce the GF looming response, "
    "with silencing of each removing its own component. It supplies NO "
    "conductance, weight, delay, receptor or release probability for either "
    "connection."
)

SOURCE_GAITANIDIS_2025_AGING = (
    "Gaitanidis E, et al. (2025). The Drosophila escape motor circuit shows "
    "differential vulnerability to aging linked to functional decay. PLOS Biol "
    "23(12):e3003553. PMID 41401182. PMCID PMC12707685. "
    "doi:10.1371/journal.pbio.3003553 . THE SOURCE FOR THE NEW FINDING IN THIS "
    "CHECKPOINT. States that 'Both LC4 and LPLC2 provide major synaptic input "
    "to the giant fiber descending neuron (GF) dendrite and make up 98.5% of "
    "the GF's direct input synapses from the optic lobe', and that 'behavioral "
    "decline is caused by the selective decay of synaptic transmission between "
    "one specific visual projection neuron type (LC4) and the dendrite of one "
    "identified descending neuron (GF)', with 'presynaptic active zone marker "
    "density ... reduced whereas postsynaptic marker density remains normal'. "
    "Also states that 'LC4 encodes information about velocity of the visual "
    "stimulus', and that escape probability driven by optogenetic LC4 "
    "activation 'declines significantly during aging' in contrast to that "
    "driven by GF or LPLC2 activation. The 98.5% figure and the active-zone "
    "marker density are ANATOMICAL and STRUCTURAL observations; neither is a "
    "synaptic weight or conductance, and neither is used as one."
)

SOURCE_DOMBROVSKI_2025_NATURE = (
    "Dombrovski M, Zang Y, Frighetto G, Vaccari A, Jang H, Mirshahidi PS, Xie "
    "F, Sanfilippo P, Hina BW, Rehan A, Hussein RH, Lee C, Morris A, Frye MA, "
    "von Reyn CR, Kurmangaliyev YZ, Card GM, Zipursky SL (2025). Molecular "
    "gradients shape synaptic specificity of a visuomotor transformation. "
    "Nature 644:453-462. PMID 40468081. PMCID PMC12350164. "
    "doi:10.1038/s41586-025-09037-4 . EXPERIMENTAL FUNCTIONAL EVIDENCE for "
    "LPLC2->GF: 'To directly test whether LPLC2-GF connectivity biases GF "
    "activation, we performed in vivo whole-cell patch-clamp recordings in the "
    "GF during looming stimuli at three elevations. GF membrane depolarization "
    "was larger in response to dorsal than to ventral looming. This provides "
    "direct evidence that the LPLC2-GF synaptic gradient generates a "
    "corresponding gradient of GF activation.' CITATION NOTE: this paper's "
    "statement that 'The GF receives direct visual input from only one other "
    "VPN type (LC4)' is its CITATION to Ache et al. 2019, not its own data. "
    "NO quantitative synaptic kinetics are given; the measured electrical "
    "quantities are POSTSYNAPTIC GF depolarisation amplitudes, which are "
    "response measurements and not synaptic parameters."
)

SOURCE_NAMIKI_2018_ELIFE = (
    "Namiki S, Dickinson MH, Wong AM, Korff W, Card GM (2018). The functional "
    "organization of descending sensory-motor pathways in Drosophila. eLife "
    "7:e34272. PMID 29943730. PMCID PMC6019073. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6019073/ . INDEPENDENT "
    "ANATOMICAL DESCRIPTION of the LC4 glomerulus and its GF innervation: "
    "'The LC4 glomerulus is of particular interest because it is innervated by "
    "the giant fiber (GF, designated DNp01 in our nomenclature)'. CITATION "
    "NOTE: its statement that 'Recent work has confirmed that LC4 neurons are "
    "functionally presynaptic to the GF and convey information about "
    "high-velocity looming expansion' is its CITATION to von Reyn et al. "
    "2014, not its own result; Namiki et al. provide innervation anatomy. It "
    "reports NO conductance, weight, kinetics or receptor for LC4->GF."
)


# --- refusal statements ------------------------------------------------------

_NO_QUANTITATIVE_KINETICS = (
    "NO QUANTITATIVE SYNAPTIC KINETICS ARE RECORDED OR INVENTED HERE. No "
    "cited source states a synaptic conductance, a synaptic weight, a synaptic "
    "delay, a release probability, a receptor identity with affinity, a "
    "reversal potential, or a receptor density for either LC4->GF or "
    "LPLC2->GF. The 98.5% optic-lobe input fraction and the presynaptic "
    "active-zone marker density reported by Gaitanidis et al. 2025 are "
    "ANATOMICAL and STRUCTURAL observations and are NOT conductances or "
    "weights. The millivolt amplitudes measured by Dombrovski et al. 2025 are "
    "POSTSYNAPTIC RESPONSE measurements, not synaptic parameters. Synapse "
    "COUNTS are anatomy, never weights. This module therefore carries no "
    "numeric biological constant of any kind."
)

_NOT_A_SIMULATOR = (
    "THIS RECORD IS PROVENANCE, NOT A SIMULATOR INPUT. It cannot drive the live "
    "GF, cannot inject a current, cannot advance a membrane equation and "
    "cannot contribute to a detected action potential. "
    "quantitative_parameters is None and enforced, live_solver_eligible is "
    "False and enforced, and couple_to_live_gf() raises. The 3.0D-8I "
    "sensory-to-biophysical coupling boundary is unchanged and still open."
)

_NO_AGEING_MODEL = (
    "AGING IS PROVENANCE CONTEXT, NOT A RULE. The selective age-related decay "
    "of LC4->GF transmission is recorded because it establishes that this "
    "synapse is a behaviourally important, selectively vulnerable circuit "
    "element rather than a mere anatomical curiosity. NOTHING here models "
    "aging, starvation, oxidative stress, active-zone loss, synaptic "
    "degradation or any other biological state. Those would be a state model, "
    "which is a later checkpoint's work, and inventing one here would convert "
    "a literature finding into a simulator behaviour that no source states."
)


# --- enums -------------------------------------------------------------------

class ClaimKind(Enum):
    """What KIND of evidence backs a claim."""

    ANATOMICAL = "anatomical_or_structural"
    FUNCTIONAL = "functional_or_electrophysiological"
    CONTEXT = "context"


class EvidenceOrigin(Enum):
    """Whether a source's statement is its OWN DATA or something it CITES.

    This exists because two of the most quotable statements in the literature
    are citations rather than results. Marking them ``CITED`` keeps the
    apparent weight of evidence honest.
    """

    OWN_DATA = "own_data"
    CITED = "cited_by_this_source"


class SensoryFeature(Enum):
    """Which looming feature a visual input neuron carries."""

    ANGULAR_VELOCITY = "angular_velocity_looming_expansion"
    ANGULAR_SIZE = "angular_size"


# --- records -----------------------------------------------------------------

@dataclass(frozen=True)
class ConnectionClaim:
    """ONE provenance claim about a connection, with its kind and its source.

    Each claim is a separate, separately sourced statement. A claim may not be
    quantitative, and a claim never implies a parameter.
    """

    claim: str
    claim_kind: ClaimKind
    evidence_origin: EvidenceOrigin
    source_references: Tuple[str, ...]
    is_quantitative_claim: bool = False
    is_implemented_in_a_solver: bool = False

    def __post_init__(self) -> None:
        if self.is_quantitative_claim:
            raise VisualInputProvenanceError(
                "8M records NO quantitative claim, because no cited source "
                "states a quantitative parameter for either connection. If a "
                "future source does, that belongs in the existing 7V/8G "
                "parameter machinery, not here. " + _NO_QUANTITATIVE_KINETICS
            )
        if self.is_implemented_in_a_solver:
            raise VisualInputProvenanceError(
                "8M implements nothing. A claim may never claim to be "
                "implemented. " + _NOT_A_SIMULATOR
            )
        if not self.claim:
            raise VisualInputProvenanceError("A claim needs a statement.")
        if not self.source_references:
            raise VisualInputProvenanceError(
                f"Claim {self.claim[:40]!r} must carry at least one source."
            )
        if not isinstance(self.claim_kind, ClaimKind):
            raise VisualInputProvenanceError("claim_kind must be a ClaimKind.")
        if not isinstance(self.evidence_origin, EvidenceOrigin):
            raise VisualInputProvenanceError(
                "evidence_origin must be an EvidenceOrigin."
            )


@dataclass(frozen=True)
class VisualInputConnection:
    """One explicit visual input -> GF connection, as inspectable provenance.

    Composes the existing 3.0D-7W ``SynapticConnectionSpec`` rather than
    redefining a connection type, so the chemical/electrical structure and the
    live-solver refusal come from the existing abstraction.
    """

    connection: SynapticConnectionSpec
    sensory_feature: SensoryFeature
    functional_role: str
    claims: Tuple[ConnectionClaim, ...]
    biological_status: str = "experimentally_and_anatomically_established"
    quantitative_implementation_status: str = "unresolved_not_modeled"
    quantitative_parameters: None = None
    live_solver_eligible: bool = False
    ageing_vulnerability_context: Optional[str] = None
    linked_7y_input_id: str = "lc4_and_lplc2_to_gf"
    linked_7y_unavailable_quantity_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise VisualInputProvenanceError(
                "A 3.0D-8M visual input record is NEVER live-solver eligible. "
                + _NOT_A_SIMULATOR
            )
        if self.quantitative_parameters is not None:
            raise VisualInputProvenanceError(
                "quantitative_parameters must be None. " + _NO_QUANTITATIVE_KINETICS
            )
        if not isinstance(self.connection, SynapticConnectionSpec):
            raise VisualInputProvenanceError(
                "A VisualInputConnection must compose the existing 3.0D-7W "
                "SynapticConnectionSpec, not replace it."
            )
        if self.connection.target_neuron != "GF":
            raise VisualInputProvenanceError(
                f"A visual input connection targets the GF, got "
                f"{self.connection.target_neuron!r}."
            )
        if not isinstance(self.sensory_feature, SensoryFeature):
            raise VisualInputProvenanceError(
                "sensory_feature must be a SensoryFeature."
            )
        if not self.claims:
            raise VisualInputProvenanceError(
                "A visual input connection must carry at least one claim."
            )
        if not self.functional_role:
            raise VisualInputProvenanceError(
                "A visual input connection must state its functional role."
            )
        if self.linked_7y_unavailable_quantity_ids and not all(
            isinstance(quantity_id, str) and quantity_id
            for quantity_id in self.linked_7y_unavailable_quantity_ids
        ):
            raise VisualInputProvenanceError(
                "Linked 7Y unavailable-quantity ids must be non-empty strings."
            )

    # -- identity, delegated to the reused type --------------------------

    @property
    def connection_id(self) -> str:
        return self.connection.synapse_id

    @property
    def source_neuron(self) -> str:
        return self.connection.source_neuron

    @property
    def target_neuron(self) -> str:
        return self.connection.target_neuron

    @property
    def connection_type(self) -> str:
        return self.connection.connection_type

    # -- evidence queries -------------------------------------------------

    def claims_of_kind(self, kind: ClaimKind) -> Tuple[ConnectionClaim, ...]:
        return tuple(c for c in self.claims if c.claim_kind is kind)

    @property
    def has_anatomical_evidence(self) -> bool:
        return bool(self.claims_of_kind(ClaimKind.ANATOMICAL))

    @property
    def has_functional_evidence(self) -> bool:
        return bool(self.claims_of_kind(ClaimKind.FUNCTIONAL))

    @property
    def own_data_sources(self) -> Tuple[str, ...]:
        """Sources contributing their OWN result, deduplicated."""
        seen = []
        for claim in self.claims:
            if claim.evidence_origin is not EvidenceOrigin.OWN_DATA:
                continue
            for reference in claim.source_references:
                if reference not in seen:
                    seen.append(reference)
        return tuple(seen)

    @property
    def cited_sources(self) -> Tuple[str, ...]:
        """Sources that are CITED by the above rather than their own result."""
        seen = []
        for claim in self.claims:
            if claim.evidence_origin is not EvidenceOrigin.CITED:
                continue
            for reference in claim.source_references:
                if reference not in seen:
                    seen.append(reference)
        return tuple(seen)

    @property
    def is_anatomically_established(self) -> bool:
        return self.has_anatomical_evidence

    @property
    def is_functionally_established(self) -> bool:
        return self.has_functional_evidence

    @property
    def is_quantitatively_implemented(self) -> bool:
        """Always False."""
        return False

    @property
    def has_conductance(self) -> bool:
        """Always False: no source states one."""
        return False

    @property
    def has_synaptic_weight(self) -> bool:
        """Always False: synapse counts are anatomy, never weights."""
        return False

    @property
    def has_synaptic_delay(self) -> bool:
        """Always False."""
        return False

    @property
    def has_release_probability(self) -> bool:
        """Always False."""
        return False

    # -- the boundary -----------------------------------------------------

    def couple_to_live_gf(self) -> None:
        """ALWAYS RAISES. This record is not a simulator input.

        Raises the existing 3.0D-8I typed exception, so the seam is one
        exception type end to end.
        """
        from .dynamics.gfs_circuit import (
            UnsupportedSensoryBiophysicalCoupling,
        )

        raise UnsupportedSensoryBiophysicalCoupling(
            f"{self.source_neuron} -> {self.target_neuron} IS a real, "
            f"directly established, functionally important connection, and it "
            f"is recorded here as such. It is nonetheless NOT parameterised: "
            f"no cited source states a conductance, weight, delay, receptor "
            f"kinetic or release probability for it. {self.quantitative_status_note()}"
        )

    def quantitative_status_note(self) -> str:
        return (
            f"Status for {self.connection_id}: "
            f"{self.quantitative_implementation_status}. "
            f"{_NO_QUANTITATIVE_KINETICS} {_NOT_A_SIMULATOR} "
            f"{_NO_AGEING_MODEL}"
        )

    def to_inspectable_dict(self) -> dict:
        """Plain data for inspection, with no numeric biological value in it."""
        return {
            "connection_id": self.connection_id,
            "presynaptic": self.source_neuron,
            "postsynaptic": self.target_neuron,
            "connection_type": self.connection_type,
            "has_electrical_component": self.connection.has_electrical_component,
            "has_chemical_component": self.connection.has_chemical_component,
            "sensory_feature": self.sensory_feature.value,
            "functional_role": self.functional_role,
            "biological_status": self.biological_status,
            "quantitative_implementation_status": (
                self.quantitative_implementation_status
            ),
            "anatomical_evidence": [c.claim for c in self.claims_of_kind(
                ClaimKind.ANATOMICAL
            )],
            "functional_evidence": [c.claim for c in self.claims_of_kind(
                ClaimKind.FUNCTIONAL
            )],
            "context_notes": [c.claim for c in self.claims_of_kind(
                ClaimKind.CONTEXT
            )],
            "own_data_sources": len(self.own_data_sources),
            "cited_sources": len(self.cited_sources),
            "quantitative_parameters": self.quantitative_parameters,
            "live_solver_eligible": self.live_solver_eligible,
            "ageing_vulnerability_context": self.ageing_vulnerability_context,
            "linked_7y_input_id": self.linked_7y_input_id,
            "linked_7y_unavailable_quantity_ids": list(
                self.linked_7y_unavailable_quantity_ids
            ),
        }

    def summary(self) -> str:
        lines = [
            f"{self.source_neuron} -> {self.target_neuron}  "
            f"({self.connection_id})",
            f"  connection type        : {self.connection_type} "
            f"(electrical={self.connection.has_electrical_component}, "
            f"chemical={self.connection.has_chemical_component})",
            f"  sensory feature        : {self.sensory_feature.value}",
            f"  functional role        : {self.functional_role}",
            f"  biological status      : {self.biological_status}",
            f"  quantitative status    : "
            f"{self.quantitative_implementation_status}",
            "  ANATOMICAL / STRUCTURAL evidence:",
        ]
        for claim in self.claims_of_kind(ClaimKind.ANATOMICAL):
            lines.append(
                f"    [{claim.evidence_origin.value}] {claim.claim}"
            )
        lines.append("  FUNCTIONAL evidence:")
        for claim in self.claims_of_kind(ClaimKind.FUNCTIONAL):
            lines.append(
                f"    [{claim.evidence_origin.value}] {claim.claim}"
            )
        if self.claims_of_kind(ClaimKind.CONTEXT):
            lines.append("  CONTEXT (not a rule):")
            for claim in self.claims_of_kind(ClaimKind.CONTEXT):
                lines.append(f"    {claim.claim}")
        lines.append(self.quantitative_status_note())
        if self.ageing_vulnerability_context:
            lines.append(
                "  AGEING VULNERABILITY (provenance, NOT a rule): "
                + self.ageing_vulnerability_context
            )
        return "\n".join(lines)


class VisualInputProvenanceError(Exception):
    """Base class for 3.0D-8M provenance failures."""


# --- the two connections -----------------------------------------------------

_LC4_GF_CONNECTION = SynapticConnectionSpec(
    synapse_id=CONNECTION_LC4_GF,
    source_neuron="LC4",
    target_neuron="GF",
    connection_type=CONNECTION_CHEMICAL,
    has_electrical_component=False,
    has_chemical_component=True,
    electrical_mechanism=None,
    chemical_mechanism=None,
    chemical_receptor=None,
    electrical_conductance_owner=None,
    electrical_conflict_references=(),
    linked_7v_topology=None,
    available_parameter_refs=(),
    notes=(
        "DIRECT VISUAL INPUT TO THE GF, CARRYING ANGULAR VELOCITY. LC4 synapses "
        "directly onto GF; there is no intervening interneuron. This is a "
        "chemical connection and has NO electrical component. The chemical "
        "MECHANISM and RECEPTOR are deliberately None: no cited source states "
        "them, and inventing either would be inventing kinetics. "
        "mechanism_and_parameters_unresolved=True declares that absence "
        "explicitly rather than leaving the record silently empty. This record "
        "carries NO conductance, weight, delay or release probability. Its "
        "phenomenological contribution is owned by 3.0D-8H "
        "gf_sensory_drive.py, which implements the FITTED Ache et al. 2019 "
        "response; that fit is a different object from this anatomical and "
        "functional connection, and the two are deliberately not conflated."
    ),
    live_solver_eligible=False,
    mechanism_and_parameters_unresolved=True,
)

_LC4_GF_CLAIMS = (
    ConnectionClaim(
        claim=(
            "LC4 synapses directly onto the GF, established by reconstruction "
            "in a fly brain electron microscopy volume."
        ),
        claim_kind=ClaimKind.ANATOMICAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_ACHE_2019_LC4_GF,),
    ),
    ConnectionClaim(
        claim=(
            "LC4 and LPLC2 together make up 98.5% of the GF's direct input "
            "synapses from the optic lobe. A synapse COUNT and therefore "
            "anatomy, not a weight."
        ),
        claim_kind=ClaimKind.ANATOMICAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_GAITANIDIS_2025_AGING,),
    ),
    ConnectionClaim(
        claim=(
            "LC4's dendrites innervate the LC4 glomerulus, which is itself "
            "innervated by the GF; independent anatomical description of the "
            "same neighbourhood."
        ),
        claim_kind=ClaimKind.ANATOMICAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_NAMIKI_2018_ELIFE,),
    ),
    ConnectionClaim(
        claim=(
            "LC4 conveys angular velocity / looming expansion, and its "
            "contribution is the velocity component of GF looming integration."
        ),
        claim_kind=ClaimKind.FUNCTIONAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(
            SOURCE_ACHE_2019_LC4_GF, SOURCE_GAITANIDIS_2025_AGING,
        ),
    ),
    ConnectionClaim(
        claim=(
            "Optogenetic activation of LC4 elicits fast escape mediated by GF "
            "activation, and blocking LC4 -> GF transmission with tetanus "
            "toxin abolishes the LC4-driven escape component."
        ),
        claim_kind=ClaimKind.FUNCTIONAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_GAITANIDIS_2025_AGING,),
    ),
    ConnectionClaim(
        claim=(
            "LC4 neurons are functionally presynaptic to the GF and convey "
            "high-velocity looming expansion."
        ),
        claim_kind=ClaimKind.FUNCTIONAL,
        evidence_origin=EvidenceOrigin.CITED,
        source_references=(SOURCE_NAMIKI_2018_ELIFE,),
    ),
    ConnectionClaim(
        claim=(
            "The GF receives direct visual input from LC4 in addition to "
            "LPLC2. CITED to Ache et al. 2019 by the citing paper, so it is not "
            "independent confirmation of the LC4 -> GF connection."
        ),
        claim_kind=ClaimKind.ANATOMICAL,
        evidence_origin=EvidenceOrigin.CITED,
        source_references=(SOURCE_DOMBROVSKI_2025_NATURE,),
    ),
)

_LPLC2_GF_CONNECTION = SynapticConnectionSpec(
    synapse_id=CONNECTION_LPLC2_GF,
    source_neuron="LPLC2",
    target_neuron="GF",
    connection_type=CONNECTION_CHEMICAL,
    has_electrical_component=False,
    has_chemical_component=True,
    electrical_mechanism=None,
    chemical_mechanism=None,
    chemical_receptor=None,
    electrical_conductance_owner=None,
    electrical_conflict_references=(),
    linked_7v_topology=None,
    available_parameter_refs=(),
    notes=(
        "DIRECT VISUAL INPUT TO THE GF, CARRYING ANGULAR SIZE. LPLC2 synapses "
        "directly onto GF; there is no intervening interneuron. This is a "
        "chemical connection and has NO electrical component. The chemical "
        "MECHANISM and RECEPTOR are deliberately None. No cited source states a "
        "conductance, weight, delay, receptor affinity or release probability "
        "for this connection. Dombrovski et al. 2025 did identify a Dpr13 / "
        "DIP-epsilon interaction that regulates synapse number along the "
        "dorsoventral axis, but they state no affinity value, no single-synapse "
        "weight and no kinetics, and the mechanism 'precisely regulate[s] "
        "synapse number' is not a current, so none of it is recorded as a "
        "parameter. mechanism_and_parameters_unresolved=True declares that "
        "absence explicitly. This record exists so that the size input is "
        "explicitly comparable to the velocity input on LC4 -> GF."
    ),
    live_solver_eligible=False,
    mechanism_and_parameters_unresolved=True,
)

_LPLC2_GF_CLAIMS = (
    ConnectionClaim(
        claim=(
            "LPLC2 synapses directly onto the GF, established by "
            "reconstruction in a fly brain electron microscopy volume."
        ),
        claim_kind=ClaimKind.ANATOMICAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_ACHE_2019_LC4_GF,),
    ),
    ConnectionClaim(
        claim=(
            "LPLC2 and LC4 together make up 98.5% of the GF's direct input "
            "synapses from the optic lobe. A synapse COUNT and therefore "
            "anatomy, not a weight."
        ),
        claim_kind=ClaimKind.ANATOMICAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_GAITANIDIS_2025_AGING,),
    ),
    ConnectionClaim(
        claim=(
            "LPLC2 conveys angular size, and its contribution is the size "
            "component of GF looming integration."
        ),
        claim_kind=ClaimKind.FUNCTIONAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_ACHE_2019_LC4_GF,),
    ),
    ConnectionClaim(
        claim=(
            "LPLC2 -> GF connectivity experimentally biases GF activation: "
            "in vivo whole-cell GF recordings during looming show larger "
            "depolarization for dorsal than ventral looming, which the "
            "authors report as direct evidence that the LPLC2 -> GF synaptic "
            "gradient generates a corresponding gradient of GF activation."
        ),
        claim_kind=ClaimKind.FUNCTIONAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_DOMBROVSKI_2025_NATURE,),
    ),
    ConnectionClaim(
        claim=(
            "LPLC2's axon terminals transmit visual information to the GF, a "
            "descending neuron that triggers rapid looming-evoked escape."
        ),
        claim_kind=ClaimKind.ANATOMICAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_DOMBROVSKI_2025_NATURE,),
    ),
    ConnectionClaim(
        claim=(
            "Six of the identified descending neurons extend dendrites into "
            "the LPLC2 glomerulus, which is also innervated by GF dendrites: "
            "neighbourhood anatomy, not a statement about this synapse's "
            "kinetics."
        ),
        claim_kind=ClaimKind.ANATOMICAL,
        evidence_origin=EvidenceOrigin.OWN_DATA,
        source_references=(SOURCE_NAMIKI_2018_ELIFE,),
    ),
)


def _build_connections() -> Tuple[VisualInputConnection, ...]:
    return (
        VisualInputConnection(
            connection=_LC4_GF_CONNECTION,
            sensory_feature=SensoryFeature.ANGULAR_VELOCITY,
            functional_role=(
                "Contributes the ANGULAR VELOCITY component of the GF looming "
                "integration. Its phenomenological coefficient is implemented "
                "in 3.0D-8H gf_sensory_drive.py and is NOT duplicated here."
            ),
            claims=_LC4_GF_CLAIMS,
            ageing_vulnerability_context=(
                "NOT MERELY ANATOMICAL. Gaitanidis et al. 2025 identify "
                "LC4 -> GF as the selectively vulnerable element: behavioural "
                "decline is caused by 'the selective decay of synaptic "
                "transmission' at this one connection, with presynaptic "
                "active-zone marker density reduced while postsynaptic marker "
                "density remains normal, and escape probability driven by LC4 "
                "activation declining with age in contrast to that driven by "
                "GF or LPLC2. This is recorded as PROVENANCE CONTEXT ONLY. "
                "Nothing here models aging, starvation, oxidative stress or "
                "synaptic degradation."
            ),
            linked_7y_unavailable_quantity_ids=(
                "lc4_to_gf_synaptic_conductance",
                "lc4_release_probability",
                "sensory_receptor_kinetics",
                "sensory_q10",
                "gf_sensory_reversal_potential",
            ),
        ),
        VisualInputConnection(
            connection=_LPLC2_GF_CONNECTION,
            sensory_feature=SensoryFeature.ANGULAR_SIZE,
            functional_role=(
                "Contributes the ANGULAR SIZE component of the GF looming "
                "integration. Its phenomenological coefficient is implemented "
                "in 3.0D-8H gf_sensory_drive.py and is NOT duplicated here."
            ),
            claims=_LPLC2_GF_CLAIMS,
            ageing_vulnerability_context=None,
            linked_7y_unavailable_quantity_ids=(
                "lplc2_to_gf_synaptic_conductance",
                "lplc2_release_probability",
                "sensory_receptor_kinetics",
                "sensory_q10",
                "gf_sensory_reversal_potential",
            ),
        ),
    )


_CONNECTIONS = _build_connections()


# --- accessors ---------------------------------------------------------------

def get_visual_input_provenance() -> Tuple[VisualInputConnection, ...]:
    """Both visual input -> GF connection records, LC4 first."""
    return _CONNECTIONS


def visual_input_connection(connection_id: str) -> VisualInputConnection:
    for record in _CONNECTIONS:
        if record.connection_id == connection_id:
            return record
    raise KeyError(
        f"Visual input connection '{connection_id}' not found. Known: "
        f"{[r.connection_id for r in _CONNECTIONS]}."
    )


def connection_for_neuron(source_neuron: str) -> VisualInputConnection:
    for record in _CONNECTIONS:
        if record.source_neuron == source_neuron:
            return record
    raise KeyError(
        f"No visual input connection from '{source_neuron}'. Known "
        f"presynaptic neurons: "
        f"{[r.source_neuron for r in _CONNECTIONS]}."
    )


def feature_connection_ids() -> Tuple[str, str]:
    """The two connection ids, velocity first, so they stay comparable."""
    return (
        connection_for_neuron("LC4").connection_id,
        connection_for_neuron("LPLC2").connection_id,
    )


def any_quantitatively_implemented() -> bool:
    """Always False. 8M implements no connection quantitatively."""
    return False


def any_live_solver_eligible() -> bool:
    """Always False."""
    return any(record.live_solver_eligible for record in _CONNECTIONS)


def any_has_conductance() -> bool:
    """Always False."""
    return any(record.has_conductance for record in _CONNECTIONS)


def any_established_anatomically() -> bool:
    return any(record.is_anatomically_established for record in _CONNECTIONS)


def any_established_functionally() -> bool:
    return any(record.is_functionally_established for record in _CONNECTIONS)


def scope_note() -> str:
    """One statement of what 3.0D-8M records and refuses to do."""
    return (
        f"{MODEL_NAME_VISUAL_INPUT_PROVENANCE_V0}: splits the combined 3.0D-7Y "
        f"record into two explicit, separately comparable direct visual inputs "
        f"to the GF -- LC4 -> GF carrying angular velocity and LPLC2 -> GF "
        f"carrying angular size -- by composing the existing 3.0D-7W "
        f"SynapticConnectionSpec and adding per-claim provenance that "
        f"distinguishes ANATOMICAL from FUNCTIONAL evidence and OWN DATA from "
        f"CITED statements. It records the new finding that LC4 -> GF is "
        f"selectively vulnerable to aging and behaviourally important, as "
        f"provenance context only. {_NO_QUANTITATIVE_KINETICS} {_NOT_A_SIMULATOR} "
        f"{_NO_AGEING_MODEL} It introduces no new biological numerical constant, "
        f"does not duplicate the 3.0D-8H mathematical coefficients, and leaves "
        f"the 3.0D-8I sensory-to-biophysical coupling boundary, the 3.0D-8J AP "
        f"detector and the 3.0D-8K behavior layer untouched."
    )
