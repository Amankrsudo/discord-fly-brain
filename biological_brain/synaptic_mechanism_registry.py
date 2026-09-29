"""Synaptic mechanism provenance and evidence boundary (3.0D-7V).

The 3.0D-7S/7T layers established the ACTIVE MEMBRANE mechanisms of the
published GFS model. This checkpoint records the SYNAPTIC mechanisms and
parameters that ``gfpn.py`` actually uses, with the same discipline: the
source's own text, the paper's own value, the evidence status of each, and an
explicit refusal to authorize any of it.

What the source actually contains
---------------------------------
``gfpn.py`` instantiates THREE separate ``Exp2Syn`` point processes, one per
chemical connection, and each carries its OWN five parameters:

    self.TTMn_syn   tau1 0.5   tau2 5.0   e 0   weight 0.00   delay 1
    self.PSI_syn    tau1 0.1   tau2 5.0   e 0   weight 0.00   delay 1
    self.DLMn_syn   tau1 0.1   tau2 1.0   e 0   weight 0.08   delay 0.15

The paper's Table 1 states ONE chemical-synapse parameter set: peak
conductance 80 uS, rise tau 0.1 ms, decay tau 1 ms, reversal 0 mV, delay
0.15 ms. That set matches the DLMn (PSI->DLMn) instance on rise, decay,
reversal and delay. It does NOT match the TTMn or PSI instances, and the paper
states no separate value for those two mixed chemical components.

This asymmetry is recorded, not resolved. The project does not know whether
the paper's single row is intended to cover only the chemical-only PSI->DLMn
synapse or all three, and no source in the project settles it.

Two chemical weights are ZERO
-----------------------------
``GF_TTMn_wt`` and ``GF_PSI_wt`` are both ``0.00``. In the source's default
parameter set the CHEMICAL component of the two mixed synapses therefore
contributes no conductance, and the paper states no value for either. This is
recorded as the source states it. It is NOT an inference that the mixed
synapses are purely electrical: the ``Exp2Syn`` objects and ``NetCon``
connections exist, they are simply given zero weight in this parameter set.

Peak conductance: an observed, unresolved numeric discrepancy
-------------------------------------------------------------
The paper states a peak conductance of 80 uS. The source writes
``'PSI_DLMn_wt': 0.08`` and assigns it as the ``NetCon`` weight argument. The
source declares NO unit for that quantity. The ratio between the two numbers is
1000.

This registry records both numbers verbatim, records the ratio, and records
the discrepancy as UNRESOLVED. It does not convert 0.08 into 80 uS or 80 uS into
0.08, does not decide which is intended, and defines no corrected value. The
observed ratio is a numeric relationship between two written numbers; it is NOT
a unit conversion, and no unit for the source quantity is assumed here.

Per 3.0D-7U, which is authoritative for source-conflict handling, such a
discrepancy is recorded with a typed status and left unresolved until an
authoritative source settles it. No new conflict type is invented here, and the
7U records are not modified.

Dalpha7: identity evidence only
--------------------------------
The PSI->DLMn synapse is cholinergic and acts on the Dalpha7 nicotinic
acetylcholine receptor. Fayyazuddin et al. 2006 (PMC1382016) established that
Dalpha7 is REQUIRED for the escape behaviour and for transmission at that
identified cholinergic synapse. Mejia et al. 2013 (PMC3667824) established
that Dalpha7 mutants abolish the PSI->DLM response. Augustin et al. 2011
(PMC3182647) describes the chemical (cholinergic) PSI->DLMn synapse.

NONE of these sources states a single-channel conductance, an alpha/beta rate
constant, an opening probability, a desensitization rate, or any other
receptor kinetic parameter. Their quantitative statements are EPSP amplitudes,
response latencies, refractory periods and following frequencies, all measured
at the circuit or muscle level.

So Dalpha7 is recorded here as RECEPTOR IDENTITY AND FUNCTION, experimentally
supported, and carrying NO quantitative kinetic parameter. The source model
uses a phenomenological double-exponential ``Exp2Syn``, which is not a
receptor-level model at all: it has no receptor, no subunit, and no binding
kinetics. Nothing about Dalpha7 may be read back out of it.

Hard boundaries
---------------
Every record is observational. ``live_solver_eligible`` is False throughout and
cannot be set otherwise. This module:

- does NOT implement a synaptic current, a conductance, an exponential or any
  synapse;
- does NOT implement Hodgkin-Huxley kinetics;
- does NOT populate ``CompartmentElectrical``, ``CableParameters`` or
  ``PassiveNetwork``;
- does NOT create Dalpha7 conductance, opening probability, alpha/beta rates,
  release probability, vesicle pool, depression, desensitization or
  calcium-dependent release;
- does NOT modify the 3.0D-7U reconciliation records, the 3.0D-7E parameter
  values or the 3.0D-7T mechanism extractions;
- does NOT convert the 0.1 ms rise time into a timestep. A synaptic rise time
  is a property of a synapse, not a numerical integration choice. The
  project's timestep policy is unchanged.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from .provenance import ParameterProvenance, ProvenanceRecord


# --- evidence status --------------------------------------------------------


class SynapticEvidenceStatus(Enum):
    """Evidence status of a synaptic quantity or identity.

    The first three statuses are carried alongside, and in agreement with,
    :class:`biological_brain.provenance.ParameterProvenance`, which already
    represents them; this enum adds only the distinctions the existing taxonomy
    cannot express.
    """

    PUBLISHED_MODEL_PARAMETER = "published_model_parameter"
    ESTIMATED = "estimated"
    EXPERIMENTALLY_CONSTRAINED = "experimentally_constrained"
    STANDARD_VALUE = "standard_value"
    IDENTITY_ONLY = "identity_only"
    UNSUPPORTED_FOR_KINETIC_MODEL = "unsupported_for_kinetic_model"
    NO_VALUE_STATED = "no_value_stated"


# Synapse identifiers, matching gfpn.py's own object names.
SYNAPSE_GF_TTMN = "GF_TTMn"
SYNAPSE_GF_PSI = "GF_PSI"
SYNAPSE_PSI_DLMN = "PSI_DLMn"

# Topology kinds.
TOPOLOGY_MIXED = "mixed_electrical_and_chemical"
TOPOLOGY_CHEMICAL = "chemical_cholinergic"


# --- exact fixtures ---------------------------------------------------------
#
# The paper's stated chemical-synapse values. Literal constants, not the
# result of a floating-point chain.
CHEMICAL_PEAK_US = 80.0
CHEMICAL_RISE_MS = 0.1
CHEMICAL_DECAY_MS = 1.0
CHEMICAL_REVERSAL_MV = 0.0
CHEMICAL_DELAY_MS = 0.15

# The source's own weight, verbatim. The source declares no unit for it.
SOURCE_DLMN_WEIGHT = 0.08
SOURCE_GF_TTMN_WEIGHT = 0.00
SOURCE_GF_PSI_WEIGHT = 0.00

# The observed numeric ratio between the paper's peak conductance and the
# source's written weight. This is an OBSERVED RATIO, not a unit conversion.
PEAK_DISCREPANCY_FACTOR = 1000.0

DISCREPANCY_UNRESOLVED = "unresolved_observed_discrepancy"


# --- source references ------------------------------------------------------

SOURCE_PAPER = (
    "Augustin H, Zylbertal A, Partridge L (2019). A computational model of the "
    "escape response latency in the giant fiber system of Drosophila "
    "melanogaster. eNeuro 6(2):ENEURO.0423-18.2019. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ "
    "(PMCID PMC6469880, PMID 31001574)."
)

SOURCE_PAPER_TABLE1 = (
    SOURCE_PAPER + " Table 1, 'Physiological parameters', rows 'Chemical "
    "synapse rise tau' (0.1 ms, 'standard value'), 'Chemical synapse decay "
    "tau' (1 ms, 'standard value'), 'Chemical synapse reversal potential' "
    "(0 mV, 'standard value'), 'Chemical synapse delay' (0.15 ms, "
    "'estimated') and 'Chemical synapse peak conductance' (80 uS, "
    "'estimated')."
)

SOURCE_PAPER_SYNAPSE_TEXT = (
    SOURCE_PAPER + " Materials and Methods, 'Model conductances': \"The "
    "PSI-DLMn chemical synapse is modeled as a double-exponential process.\""
)

SOURCE_GFPN_TTMN = (
    "ModelDB 245415, gfpn.py lines 84-87 and 165: TTMn_syn = "
    "neuron.h.Exp2Syn(...); tau1, tau2 and e assigned; NetCon with weight "
    "GF_TTMn_wt and delay GF_TTMn_delay."
)

SOURCE_GFPN_PSI = (
    "ModelDB 245415, gfpn.py lines 100-103 and 166: PSI_syn = "
    "neuron.h.Exp2Syn(...); tau1, tau2 and e assigned; NetCon with weight "
    "GF_PSI_wt and delay GF_PSI_delay."
)

SOURCE_GFPN_DLMN = (
    "ModelDB 245415, gfpn.py lines 117-120 and 167: DLMn_syn = "
    "neuron.h.Exp2Syn(...); tau1, tau2 and e assigned; NetCon with weight "
    "PSI_DLMn_wt and delay PSI_DLMn_delay."
)

SOURCE_GFPN_WEIGHT_ASSIGNMENT = (
    "ModelDB 245415, gfpn.py line 167: NetCon(..., "
    "self.params['PSI_DLMn_delay'], self.params['PSI_DLMn_wt'], ...). The "
    "source assigns the weight as a NetCon argument and declares NO unit for "
    "it."
)

SOURCE_FAYYAZUDDIN = (
    "Fayyazuddin A, Zaheer MA, Hiesinger PR, Bellen HJ (2006). The nicotinic "
    "acetylcholine receptor Dalpha7 is required for an escape behavior in "
    "Drosophila. PLoS Biol 4(2):e402. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC1382016/ . Direct "
    "electrophysiological and genetic evidence that Dalpha7 is required for "
    "transmission at the identified cholinergic PSI->DLM motor neuron synapse. "
    "States NO single-channel conductance and NO kinetic parameters."
)

SOURCE_MEJIA = (
    "Mejia M, Heghinian MD, Marí F, Godenschwege TA (2013). New tools for "
    "targeted disruption of cholinergic synaptic transmission in Drosophila "
    "melanogaster. PLoS One 8(5):e60049. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC3667824/ . Electrophysiological "
    "evidence that Dalpha7 mutants abolish the PSI->DLM response. States NO "
    "single-channel conductance and NO kinetic parameters."
)

SOURCE_AUGUSTIN_JOVE = (
    "Augustin H, Allen MJ, Partridge L (2011). Electrophysiological recordings "
    "from the giant fiber pathway of D. melanogaster. J Vis Exp (54):e1709. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC3182647/ . Describes the "
    "electro-chemical GF->TTMn and GF->PSI synapses and the chemical "
    "(cholinergic) PSI->DLMn synapse. States NO synaptic conductance, NO "
    "reversal potential and NO kinetic parameters for the PSI->DLMn synapse."
)

SOURCE_RECONCILIATION_PRECEDENT = (
    "3.0D-7U, biological_brain/source_reconciliation.py, is authoritative for "
    "source-conflict handling: conflicts are recorded with a typed status, "
    "both sides are preserved, and no side is preferred."
)

_NO_UNIT_STATED = (
    "THE SOURCE DECLARES NO UNIT for this quantity. It is written as a bare "
    "number in gfpn.py. No unit is assumed or invented here."
)

_NOT_A_MEASUREMENT = (
    "This is a PUBLISHED MODEL PARAMETER, NOT a direct experimental "
    "measurement of the GFS chemical synapse. The paper labels this value "
    "itself. It must NOT be reported as a measured synapse property."
)

_NOT_LIVE = (
    "3.0D-7V IS A PROVENANCE CHECKPOINT ONLY. This record is NOT eligible for "
    "the live solver: no synaptic current is implemented, no synaptic "
    "conductance is computed, no compartment is populated with a synapse, and "
    "the passive backend is unchanged."
)

_NO_RECEPTOR_KINETICS = (
    "NO RECEPTOR KINETICS EXIST IN THE PROJECT SOURCES. Neither the published "
    "model nor any cited experimental paper states a Dalpha7 single-channel "
    "conductance, an alpha or beta rate constant, an opening probability, a "
    "desensitization rate, a release probability, a vesicle pool, a "
    "depression model or a calcium-dependent release rule for this synapse. "
    "The source model uses a phenomenological double-exponential Exp2Syn, "
    "which contains no receptor, no subunit and no binding kinetics. Nothing "
    "about Dalpha7 may be read back out of it, and no such quantity is created "
    "here."
)


@dataclass(frozen=True)
class SynapticQuantityRecord:
    """One synaptic quantity, with its source text and its paper value apart.

    ``source_value_text`` is the verbatim ``gfpn.py`` line. ``source_value`` and
    ``source_unit`` are the source's own number and its own unit, which for the
    ``NetCon`` weight is no unit at all.

    ``paper_value`` and ``paper_unit`` are the paper's statement, and
    ``paper_label`` is the paper's OWN label for it ('standard value',
    'estimated', ...). The two are stored side by side and never merged: an
    identical number in two sources is not evidence that either is measured.

    ``value_agreement`` states the observed relationship between the two
    written numbers, or ``None`` where the paper states no value. It is an
    observation about the source text, not a claim about biology.
    """

    name: str
    synapse_id: str
    quantity_kind: str
    source_value_text: str
    source_value: float
    source_unit: Optional[str]
    source_file: str
    source_line: int
    source_references: Tuple[str, ...]
    paper_value: Optional[float]
    paper_unit: Optional[str]
    paper_label: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    value_agreement: Optional[str]
    assignment_statements: Tuple[str, ...] = ()
    limitations: str = ""
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Synaptic quantity '{self.name}' cannot be live-solver "
                f"eligible in 3.0D-7V. Recording a synaptic value does not "
                f"authorize implementing, connecting or activating it."
            )
        if self.source_value_text is None or not self.source_value_text.strip():
            raise ValueError(
                f"Synaptic quantity '{self.name}' must carry its verbatim "
                f"source line."
            )
        if not self.source_references:
            raise ValueError(
                f"Synaptic quantity '{self.name}' must carry at least one "
                f"source reference."
            )
        if (self.paper_value is None) != (self.paper_unit is None):
            raise ValueError(
                f"Synaptic quantity '{self.name}' must state both a paper "
                f"value and a paper unit, or neither."
            )
        if self.value_agreement is not None and self.paper_value is None:
            raise ValueError(
                f"Synaptic quantity '{self.name}' reports an agreement with a "
                f"paper value, but the paper states none."
            )

    @property
    def provenance(self) -> ProvenanceRecord:
        return ProvenanceRecord(self.provenance_category, self.source_references[0])

    @property
    def has_paper_value(self) -> bool:
        return self.paper_value is not None

    @property
    def has_source_unit(self) -> bool:
        return self.source_unit is not None

    @property
    def values_are_identical(self) -> bool:
        """True only when BOTH sources state a value and they are equal.

        An identical number is NOT evidence of measurement. This property
        reports only what the two texts say, and callers must not read it as a
        provenance upgrade.
        """
        return (
            self.paper_value is not None
            and self.paper_value == self.source_value
        )

    def source_reference_text(self) -> str:
        return (
            f"{self.source_file} line {self.source_line}: "
            f"{self.source_value_text}"
        )


@dataclass(frozen=True)
class SynapseTopologyRecord:
    """One synaptic connection as the published model builds it.

    Records the electrical and chemical components SEPARATELY, so that a
    'mixed' synapse is never collapsed into either kind alone.
    """

    synapse_id: str
    source_neuron: str
    target_neuron: str
    topology: str
    has_electrical_component: bool
    has_chemical_component: bool
    gap_junction_mechanism: Optional[str]
    chemical_mechanism: Optional[str]
    source_references: Tuple[str, ...]
    notes: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Synapse '{self.synapse_id}' cannot be live-solver eligible."
            )
        if self.topology == TOPOLOGY_MIXED:
            if not (self.has_electrical_component and self.has_chemical_component):
                raise ValueError(
                    f"Synapse '{self.synapse_id}' is declared mixed and must "
                    f"carry BOTH an electrical and a chemical component."
                )
        elif self.topology == TOPOLOGY_CHEMICAL:
            if self.has_electrical_component:
                raise ValueError(
                    f"Synapse '{self.synapse_id}' is declared chemical and "
                    f"must NOT carry an electrical component."
                )
            if not self.has_chemical_component:
                raise ValueError(
                    f"Synapse '{self.synapse_id}' is declared chemical and "
                    f"must carry a chemical component."
                )
        else:
            raise ValueError(
                f"Synapse '{self.synapse_id}' has unknown topology "
                f"'{self.topology}'"
            )
        if self.has_electrical_component and not self.gap_junction_mechanism:
            raise ValueError(
                f"Synapse '{self.synapse_id}' has an electrical component and "
                f"must name its gap junction mechanism."
            )
        if self.has_chemical_component and not self.chemical_mechanism:
            raise ValueError(
                f"Synapse '{self.synapse_id}' has a chemical component and "
                f"must name its chemical mechanism."
            )

    @property
    def is_mixed(self) -> bool:
        return self.topology == TOPOLOGY_MIXED

    @property
    def is_chemical_only(self) -> bool:
        return self.topology == TOPOLOGY_CHEMICAL


@dataclass(frozen=True)
class ReceptorIdentityRecord:
    """An experimentally supported receptor IDENTITY, never its kinetics.

    This record type structurally cannot carry a number. It has no field for a
    conductance, a rate constant, an opening probability or a desensitization
    rate, so none can be attached to Dalpha7 by this path.
    """

    receptor: str
    synapse_id: str
    ion: str
    function: str
    experimentally_supported: bool
    quantitative_kinetics_available: bool
    source_references: Tuple[str, ...]
    limitations: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Receptor '{self.receptor}' cannot be live-solver eligible."
            )
        if self.quantitative_kinetics_available:
            raise ValueError(
                f"Receptor '{self.receptor}' must not claim available "
                f"kinetics. No project source states a single-channel "
                f"conductance or any rate constant for it."
            )
        if not self.experimentally_supported:
            raise ValueError(
                f"Receptor record '{self.receptor}' must state its "
                f"experimental support; this registry records experimentally "
                f"supported identities."
            )

    @property
    def has_quantitative_value(self) -> bool:
        """Always False: an identity record carries no number."""
        return False


@dataclass(frozen=True)
class ExcludedSynapticQuantity:
    """A synaptic quantity deliberately NOT created, and why."""

    name: str
    reason: str
    evidence_status: SynapticEvidenceStatus

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError(
                f"Excluded quantity '{self.name}' must state why it is "
                f"excluded."
            )
        if self.evidence_status is not (
            SynapticEvidenceStatus.UNSUPPORTED_FOR_KINETIC_MODEL
        ):
            raise ValueError(
                f"Excluded quantity '{self.name}' must carry the status "
                f"'unsupported_for_kinetic_model'."
            )


@dataclass(frozen=True)
class SynapticMechanismRegistry:
    """Synaptic mechanism provenance. NOT an activation mechanism.

    Assigns nothing. No compartment, no ``CableParameters``, no
    ``CompartmentElectrical`` and no solver input is populated from this
    registry, and the passive backend does not import it.
    """

    name: str
    source: str
    model_id: str
    model_citation: str
    quantities: Tuple[SynapticQuantityRecord, ...]
    synapses: Tuple[SynapseTopologyRecord, ...]
    receptor_identities: Tuple[ReceptorIdentityRecord, ...]
    excluded: Tuple[ExcludedSynapticQuantity, ...]
    scope_note: str

    def get(self, name: str) -> SynapticQuantityRecord:
        for record in self.quantities:
            if record.name == name:
                return record
        raise KeyError(f"Synaptic quantity '{name}' not in registry")

    def names(self) -> Tuple[str, ...]:
        return tuple(record.name for record in self.quantities)

    def synapse(self, synapse_id: str) -> SynapseTopologyRecord:
        for record in self.synapses:
            if record.synapse_id == synapse_id:
                return record
        raise KeyError(f"Synapse '{synapse_id}' not in registry")

    def synapse_ids(self) -> Tuple[str, ...]:
        return tuple(record.synapse_id for record in self.synapses)

    def quantities_for_synapse(self, synapse_id: str) -> Tuple[str, ...]:
        return tuple(
            record.name
            for record in self.quantities
            if record.synapse_id == synapse_id
        )

    def receptor(self, name: str) -> ReceptorIdentityRecord:
        for record in self.receptor_identities:
            if record.receptor == name:
                return record
        raise KeyError(f"Receptor '{name}' not in registry")

    def excluded_names(self) -> Tuple[str, ...]:
        return tuple(record.name for record in self.excluded)

    def synapse_names_with_paper_value(self) -> Tuple[str, ...]:
        return tuple(
            f"{record.synapse_id}.{record.name}"
            for record in self.quantities
            if record.has_paper_value
        )

    def any_live_solver_eligible(self) -> bool:
        """Always False in 3.0D-7V."""
        return any(record.live_solver_eligible for record in self.quantities)

    def any_receptor_kinetics(self) -> bool:
        """Always False in 3.0D-7V: no receptor kinetics exist here."""
        return any(
            record.quantitative_kinetics_available
            for record in self.receptor_identities
        )

    def discrepancies(self) -> Tuple[SynapticQuantityRecord, ...]:
        return tuple(
            record
            for record in self.quantities
            if record.value_agreement == DISCREPANCY_UNRESOLVED
        )

    def verify_verbatim_source(self) -> None:
        """Assert every recorded source line matches gfpn.py verbatim.

        The source is vendored under ``biological_brain/data/modeldb_245415/``
        so provenance is checkable offline. The test suite calls this, so a
        transcription error cannot pass unnoticed.
        """
        cache: Dict[str, Tuple[str, ...]] = {}
        for record in self.quantities:
            lines = cache.get(record.source_file)
            if lines is None:
                import os

                root = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "data", "modeldb_245415",
                )
                with open(
                    os.path.join(root, record.source_file), encoding="utf-8"
                ) as handle:
                    lines = tuple(handle.read().split("\n"))
                cache[record.source_file] = lines
            if not 1 <= record.source_line <= len(lines):
                raise AssertionError(
                    f"{record.name}: line {record.source_line} is outside "
                    f"{record.source_file}"
                )
            actual = lines[record.source_line - 1]
            if actual != record.source_value_text:
                raise AssertionError(
                    f"{record.name} {record.source_file} line "
                    f"{record.source_line}: recorded text is not verbatim.\n"
                    f"  recorded: {record.source_value_text!r}\n"
                    f"  file:     {actual!r}"
                )


def _quantity(
    name: str,
    synapse_id: str,
    quantity_kind: str,
    source_value_text: str,
    source_value: float,
    source_unit: Optional[str],
    source_line: int,
    source_references: Tuple[str, ...],
    paper_value: Optional[float],
    paper_unit: Optional[str],
    paper_label: str,
    evidence_status: SynapticEvidenceStatus,
    provenance_category: ParameterProvenance,
    value_agreement: Optional[str],
    assignment_statements: Tuple[str, ...] = (),
    limitations: str = "",
) -> SynapticQuantityRecord:
    return SynapticQuantityRecord(
        name=name,
        synapse_id=synapse_id,
        quantity_kind=quantity_kind,
        source_value_text=source_value_text,
        source_value=source_value,
        source_unit=source_unit,
        source_file="gfpn.py",
        source_line=source_line,
        source_references=source_references,
        paper_value=paper_value,
        paper_unit=paper_unit,
        paper_label=paper_label,
        evidence_status=evidence_status,
        provenance_category=provenance_category,
        value_agreement=value_agreement,
        assignment_statements=assignment_statements,
        limitations=limitations,
    )


def _no_paper_value(
    paper_label: str, extra: str = ""
) -> str:
    return (
        "The paper states NO value for this quantity. The paper's Table 1 "
        f"gives a single chemical-synapse row, labelled {paper_label}, and the "
        "project sources do not state which of the three Exp2Syn instances it "
        "is intended to cover. No paper value is inferred for the other "
        "instances, and no value is invented. " + _NOT_A_MEASUREMENT + " " + extra
    )


def _quantities() -> Tuple[SynapticQuantityRecord, ...]:
    records = [
        # --- PSI -> DLMn: the instance the paper's row matches ---
        _quantity(
            name="rise_tau",
            synapse_id=SYNAPSE_PSI_DLMN,
            quantity_kind="synaptic_rise_time_constant",
            source_value_text="                 'DLMn_syn_tau1': 0.1,",
            source_value=0.1,
            source_unit="ms",
            source_line=42,
            source_references=(SOURCE_GFPN_DLMN, SOURCE_PAPER_TABLE1),
            paper_value=CHEMICAL_RISE_MS,
            paper_unit="ms",
            paper_label="'standard value'",
            evidence_status=SynapticEvidenceStatus.STANDARD_VALUE,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement="identical_written_value",
            assignment_statements=(
                "        self.DLMn_syn.tau1 = params['DLMn_syn_tau1'];",
            ),
            limitations=(
                "The source and the paper write the same number. An identical "
                "written value is NOT evidence that either is measured. "
                + _NOT_A_MEASUREMENT + " This is a property of the synapse, "
                "NOT a simulation timestep, and must never be used to set an "
                "integration step. " + _NOT_LIVE
            ),
        ),
        _quantity(
            name="decay_tau",
            synapse_id=SYNAPSE_PSI_DLMN,
            quantity_kind="synaptic_decay_time_constant",
            source_value_text="                 'DLMn_syn_tau2': 1.0,",
            source_value=1.0,
            source_unit="ms",
            source_line=43,
            source_references=(SOURCE_GFPN_DLMN, SOURCE_PAPER_TABLE1),
            paper_value=CHEMICAL_DECAY_MS,
            paper_unit="ms",
            paper_label="'standard value'",
            evidence_status=SynapticEvidenceStatus.STANDARD_VALUE,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement="identical_written_value",
            assignment_statements=(
                "        self.DLMn_syn.tau2 = params['DLMn_syn_tau2'];",
            ),
            limitations=(
                "Identical written values are NOT measurement evidence. "
                + _NOT_A_MEASUREMENT + " " + _NOT_LIVE
            ),
        ),
        _quantity(
            name="reversal_potential",
            synapse_id=SYNAPSE_PSI_DLMN,
            quantity_kind="synaptic_reversal_potential",
            source_value_text="                 'DLMn_syn_e': 0,",
            source_value=0.0,
            source_unit="mV",
            source_line=44,
            source_references=(SOURCE_GFPN_DLMN, SOURCE_PAPER_TABLE1),
            paper_value=CHEMICAL_REVERSAL_MV,
            paper_unit="mV",
            paper_label="'standard value'",
            evidence_status=SynapticEvidenceStatus.STANDARD_VALUE,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement="identical_written_value",
            assignment_statements=(
                "        self.DLMn_syn.e = params['DLMn_syn_e'];",
            ),
            limitations=(
                "A reversal potential of 0 mV is a STANDARD VALUE of the "
                "phenomenological model, not a measured Dalpha7 reversal "
                "potential. The source and the paper write the same number, "
                "and an identical written value is NOT evidence that either "
                "is measured. " + _NOT_A_MEASUREMENT + " " + _NOT_LIVE
            ),
        ),
        _quantity(
            name="delay",
            synapse_id=SYNAPSE_PSI_DLMN,
            quantity_kind="synaptic_transmission_delay",
            source_value_text="                 'PSI_DLMn_delay': 0.15,",
            source_value=0.15,
            source_unit="ms",
            source_line=51,
            source_references=(SOURCE_GFPN_DLMN, SOURCE_PAPER_TABLE1),
            paper_value=CHEMICAL_DELAY_MS,
            paper_unit="ms",
            paper_label="'estimated'",
            evidence_status=SynapticEvidenceStatus.ESTIMATED,
            provenance_category=ParameterProvenance.ESTIMATED,
            value_agreement="identical_written_value",
            assignment_statements=(
                "        self.PSI_DLMn_con = neuron.h.NetCon(self.PSI("
                "params['DLMn_syn_pre_loc'])._ref_v, self.DLMn_syn, 0, "
                "self.params['PSI_DLMn_delay'], self.params['PSI_DLMn_wt'], "
                "sec = self.PSI)",
            ),
            limitations=(
                "This delay is a connection-construction argument, NOT a "
                "simulation timestep. It must never be used to set an "
                "integration step. The source and the paper write the same "
                "number, and an identical written value is NOT evidence that "
                "either is measured. "
                + _NOT_A_MEASUREMENT + " " + _NOT_LIVE
            ),
        ),
        _quantity(
            name="peak_conductance",
            synapse_id=SYNAPSE_PSI_DLMN,
            quantity_kind="synaptic_peak_conductance",
            source_value_text="                 'PSI_DLMn_wt': 0.08,",
            source_value=SOURCE_DLMN_WEIGHT,
            source_unit=None,
            source_line=52,
            source_references=(
                SOURCE_GFPN_DLMN, SOURCE_GFPN_WEIGHT_ASSIGNMENT,
                SOURCE_PAPER_TABLE1,
            ),
            paper_value=CHEMICAL_PEAK_US,
            paper_unit="uS",
            paper_label="'estimated'",
            evidence_status=SynapticEvidenceStatus.ESTIMATED,
            provenance_category=ParameterProvenance.ESTIMATED,
            value_agreement=DISCREPANCY_UNRESOLVED,
            assignment_statements=(
                "NetCon(..., self.params['PSI_DLMn_delay'], "
                "self.params['PSI_DLMn_wt'], ...)",
            ),
            limitations=(
                "OBSERVED, UNRESOLVED NUMERIC DISCREPANCY. The paper states a "
                "peak conductance of 80 uS. The source writes 0.08 and "
                "declares NO unit for it. The ratio of the two written numbers "
                f"is exactly {PEAK_DISCREPANCY_FACTOR:g}. That ratio is an "
                "OBSERVATION ABOUT TWO WRITTEN NUMBERS, not a unit "
                "conversion: no unit is assumed for the source quantity, and "
                "this record does not convert one value into the other, does "
                "not decide which is intended, and defines no corrected "
                "value. " + _NO_UNIT_STATED + " " + _NOT_A_MEASUREMENT
                + " " + _NOT_LIVE
            ),
        ),
        # --- GF -> TTMn: the source states values the paper does not ---
        _quantity(
            name="rise_tau",
            synapse_id=SYNAPSE_GF_TTMN,
            quantity_kind="synaptic_rise_time_constant",
            source_value_text="                 'TTMn_syn_tau1': 0.5,",
            source_value=0.5,
            source_unit="ms",
            source_line=32,
            source_references=(SOURCE_GFPN_TTMN,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "        self.TTMn_syn.tau1 = params['TTMn_syn_tau1'];",
            ),
            limitations=_no_paper_value(
                "'standard value'",
                "The source value 0.5 ms differs from the paper's 0.1 ms; "
                "the project does not know whether the paper's row is meant to "
                "cover this instance. The discrepancy is recorded, not "
                "resolved. " + _NOT_LIVE,
            ),
        ),
        _quantity(
            name="decay_tau",
            synapse_id=SYNAPSE_GF_TTMN,
            quantity_kind="synaptic_decay_time_constant",
            source_value_text="                 'TTMn_syn_tau2': 5.0,",
            source_value=5.0,
            source_unit="ms",
            source_line=33,
            source_references=(SOURCE_GFPN_TTMN,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "        self.TTMn_syn.tau2 = params['TTMn_syn_tau2'];",
            ),
            limitations=_no_paper_value(
                "'standard value'",
                "The source value 5.0 ms differs from the paper's 1 ms. "
                "Recorded, not resolved. " + _NOT_LIVE,
            ),
        ),
        _quantity(
            name="reversal_potential",
            synapse_id=SYNAPSE_GF_TTMN,
            quantity_kind="synaptic_reversal_potential",
            source_value_text="                 'TTMn_syn_e': 0,    ",
            source_value=0.0,
            source_unit="mV",
            source_line=34,
            source_references=(SOURCE_GFPN_TTMN,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "        self.TTMn_syn.e = params['TTMn_syn_e'];",
            ),
            limitations=_no_paper_value("'standard value'") + " " + _NOT_LIVE,
        ),
        _quantity(
            name="peak_conductance",
            synapse_id=SYNAPSE_GF_TTMN,
            quantity_kind="synaptic_peak_conductance",
            source_value_text="                 'GF_TTMn_wt': 0.00,",
            source_value=SOURCE_GF_TTMN_WEIGHT,
            source_unit=None,
            source_line=48,
            source_references=(SOURCE_GFPN_TTMN,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "NetCon(..., self.params['GF_TTMn_delay'], "
                "self.params['GF_TTMn_wt'], ...)",
            ),
            limitations=_no_paper_value(
                "'estimated'",
                "The source weight is ZERO. In the source's default parameter "
                "set the chemical component of this mixed synapse therefore "
                "contributes no conductance. That is a statement about THIS "
                "PARAMETER SET, not a claim that the synapse has no chemical "
                "component: the Exp2Syn object and the NetCon both exist. "
                + _NO_UNIT_STATED + " " + _NOT_LIVE,
            ),
        ),
        _quantity(
            name="delay",
            synapse_id=SYNAPSE_GF_TTMN,
            quantity_kind="synaptic_transmission_delay",
            source_value_text="                 'GF_TTMn_delay': 1,",
            source_value=1.0,
            source_unit="ms",
            source_line=47,
            source_references=(SOURCE_GFPN_TTMN,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "NetCon(..., self.params['GF_TTMn_delay'], ...)",
            ),
            limitations=_no_paper_value(
                "'estimated'",
                "The source delay 1 ms differs from the paper's 0.15 ms. "
                "Recorded, not resolved. This is a connection-construction "
                "argument, NOT a simulation timestep. " + _NOT_LIVE,
            ),
        ),
        # --- GF -> PSI: the source states values the paper does not ---
        _quantity(
            name="rise_tau",
            synapse_id=SYNAPSE_GF_PSI,
            quantity_kind="synaptic_rise_time_constant",
            source_value_text="                 'PSI_syn_tau1': 0.1,",
            source_value=0.1,
            source_unit="ms",
            source_line=37,
            source_references=(SOURCE_GFPN_PSI,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "        self.PSI_syn.tau1 = params['PSI_syn_tau1'];",
            ),
            limitations=_no_paper_value(
                "'standard value'",
                "The source value happens to equal the paper's 0.1 ms, but "
                "the paper states no value for THIS instance, so the "
                "coincidence is NOT a paper agreement and is not recorded as "
                "one. " + _NOT_LIVE,
            ),
        ),
        _quantity(
            name="decay_tau",
            synapse_id=SYNAPSE_GF_PSI,
            quantity_kind="synaptic_decay_time_constant",
            source_value_text="                 'PSI_syn_tau2': 5.0,",
            source_value=5.0,
            source_unit="ms",
            source_line=38,
            source_references=(SOURCE_GFPN_PSI,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "        self.PSI_syn.tau2 = params['PSI_syn_tau2'];",
            ),
            limitations=_no_paper_value(
                "'standard value'",
                "The source value 5.0 ms differs from the paper's 1 ms. "
                "Recorded, not resolved. " + _NOT_LIVE,
            ),
        ),
        _quantity(
            name="reversal_potential",
            synapse_id=SYNAPSE_GF_PSI,
            quantity_kind="synaptic_reversal_potential",
            source_value_text="                 'PSI_syn_e': 0,",
            source_value=0.0,
            source_unit="mV",
            source_line=39,
            source_references=(SOURCE_GFPN_PSI,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "        self.PSI_syn.e = params['PSI_syn_e'];",
            ),
            limitations=_no_paper_value("'standard value'") + " " + _NOT_LIVE,
        ),
        _quantity(
            name="peak_conductance",
            synapse_id=SYNAPSE_GF_PSI,
            quantity_kind="synaptic_peak_conductance",
            source_value_text="                 'GF_PSI_wt': 0.00,",
            source_value=SOURCE_GF_PSI_WEIGHT,
            source_unit=None,
            source_line=50,
            source_references=(SOURCE_GFPN_PSI,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "NetCon(..., self.params['GF_PSI_delay'], "
                "self.params['GF_PSI_wt'], ...)",
            ),
            limitations=_no_paper_value(
                "'estimated'",
                "The source weight is ZERO. In the source's default parameter "
                "set the chemical component of this mixed synapse therefore "
                "contributes no conductance. That is a statement about THIS "
                "PARAMETER SET, not a claim that the synapse has no chemical "
                "component: the Exp2Syn object and the NetCon both exist. "
                + _NO_UNIT_STATED + " " + _NOT_LIVE,
            ),
        ),
        _quantity(
            name="delay",
            synapse_id=SYNAPSE_GF_PSI,
            quantity_kind="synaptic_transmission_delay",
            source_value_text="                 'GF_PSI_delay': 1,",
            source_value=1.0,
            source_unit="ms",
            source_line=49,
            source_references=(SOURCE_GFPN_PSI,),
            paper_value=None,
            paper_unit=None,
            paper_label="no value stated for this instance",
            evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
            provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            value_agreement=None,
            assignment_statements=(
                "NetCon(..., self.params['GF_PSI_delay'], ...)",
            ),
            limitations=_no_paper_value(
                "'estimated'",
                "The source delay 1 ms differs from the paper's 0.15 ms. "
                "Recorded, not resolved. This is a connection-construction "
                "argument, NOT a simulation timestep. " + _NOT_LIVE,
            ),
        ),
    ]
    # Location arguments: recorded, and never confused with conductances.
    locations = (
        ("pre_location", SYNAPSE_GF_TTMN, 35, "                 'TTMn_syn_pre_loc': 1.0,    ", 1.0),
        ("post_location", SYNAPSE_GF_TTMN, 36, "                 'TTMn_syn_post_loc': 0.2,", 0.2),
        ("pre_location", SYNAPSE_GF_PSI, 40, "                 'PSI_syn_pre_loc': 0.9,", 0.9),
        ("post_location", SYNAPSE_GF_PSI, 41, "                 'PSI_syn_post_loc': 0.5,", 0.5),
        ("pre_location", SYNAPSE_PSI_DLMN, 45, "                 'DLMn_syn_pre_loc': 0.85,", 0.85),
        ("post_location", SYNAPSE_PSI_DLMN, 46, "                 'DLMn_syn_post_loc': 0.25,", 0.25),
    )
    synapse_reference = {
        SYNAPSE_GF_TTMN: SOURCE_GFPN_TTMN,
        SYNAPSE_GF_PSI: SOURCE_GFPN_PSI,
        SYNAPSE_PSI_DLMN: SOURCE_GFPN_DLMN,
    }
    for name, synapse_id, line, text, value in locations:
        records.append(
            _quantity(
                name=name,
                synapse_id=synapse_id,
                quantity_kind="synapse_location_fraction",
                source_value_text=text,
                source_value=value,
                source_unit="normalized_location",
                source_line=line,
                source_references=(synapse_reference[synapse_id],),
                paper_value=None,
                paper_unit=None,
                paper_label="no value stated for this instance",
                evidence_status=SynapticEvidenceStatus.NO_VALUE_STATED,
                provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
                value_agreement=None,
                limitations=(
                    "A normalized location along the section, NOT a "
                    "conductance and NOT a time. The paper states no value. "
                    + _NOT_A_MEASUREMENT + " " + _NOT_LIVE
                ),
            )
        )
    return tuple(records)


def _synapses() -> Tuple[SynapseTopologyRecord, ...]:
    return (
        SynapseTopologyRecord(
            synapse_id=SYNAPSE_GF_TTMN,
            source_neuron="GF",
            target_neuron="TTMn",
            topology=TOPOLOGY_MIXED,
            has_electrical_component=True,
            has_chemical_component=True,
            gap_junction_mechanism="gap2",
            chemical_mechanism="Exp2Syn",
            source_references=(
                SOURCE_AUGUSTIN_JOVE, SOURCE_GFPN_TTMN, SOURCE_GFPN_DLMN,
            ),
            notes=(
                "MIXED ELECTRICAL AND CHEMICAL. The paper describes the GF "
                "forming 'electro-chemical synapses' with the TTMn. The source "
                "builds both components: a gap2 point process bound to the GF "
                "voltage in wire_cells(), and an Exp2Syn receiving a NetCon. "
                "The electrical component's g_gap unit conflict is recorded "
                "and unresolved by 3.0D-7U and is NOT resolved here."
            ),
        ),
        SynapseTopologyRecord(
            synapse_id=SYNAPSE_GF_PSI,
            source_neuron="GF",
            target_neuron="PSI",
            topology=TOPOLOGY_MIXED,
            has_electrical_component=True,
            has_chemical_component=True,
            gap_junction_mechanism="gap2",
            chemical_mechanism="Exp2Syn",
            source_references=(
                SOURCE_AUGUSTIN_JOVE, SOURCE_GFPN_PSI, SOURCE_GFPN_DLMN,
            ),
            notes=(
                "MIXED ELECTRICAL AND CHEMICAL. The paper describes the GF "
                "forming 'electro-chemical synapses' with the contralateral "
                "PSI. The source builds both components: a gap2 point process "
                "and an Exp2Syn receiving a NetCon. The electrical "
                "component's g_gap unit conflict is recorded and unresolved by "
                "3.0D-7U and is NOT resolved here."
            ),
        ),
        SynapseTopologyRecord(
            synapse_id=SYNAPSE_PSI_DLMN,
            source_neuron="PSI",
            target_neuron="DLMn",
            topology=TOPOLOGY_CHEMICAL,
            has_electrical_component=False,
            has_chemical_component=True,
            gap_junction_mechanism=None,
            chemical_mechanism="Exp2Syn",
            source_references=(
                SOURCE_AUGUSTIN_JOVE, SOURCE_PAPER_SYNAPSE_TEXT,
                SOURCE_GFPN_DLMN, SOURCE_FAYYAZUDDIN, SOURCE_MEJIA,
            ),
            notes=(
                "CHEMICAL, CHOLINERGIC, NO ELECTRICAL COMPONENT. The paper "
                "states the PSI-DLMn chemical synapse is modeled as a "
                "double-exponential process, and the source builds exactly "
                "one Exp2Syn with a NetCon and no gap2. This is the only "
                "CHEMICAL-ONLY synapse in the model and the only one the "
                "paper's Table 1 row is matched against in this registry."
            ),
        ),
    )


def _receptors() -> Tuple[ReceptorIdentityRecord, ...]:
    return (
        ReceptorIdentityRecord(
            receptor="Dalpha7",
            synapse_id=SYNAPSE_PSI_DLMN,
            ion="Na+ / Ca2+ permeable nicotinic cation",
            function=(
                "Required for transmission at the identified cholinergic "
                "PSI->DLM motor neuron synapse, and therefore for "
                "GF-mediated escape behaviour"
            ),
            experimentally_supported=True,
            quantitative_kinetics_available=False,
            source_references=(
                SOURCE_FAYYAZUDDIN, SOURCE_MEJIA, SOURCE_AUGUSTIN_JOVE,
            ),
            limitations=(
                "RECEPTOR IDENTITY AND FUNCTION ONLY, EXPERIMENTALLY "
                "SUPPORTED. Fayyazuddin et al. 2006 established that Dalpha7 "
                "is required at this synapse by genetic and "
                "electrophysiological means; Mejia et al. 2013 established "
                "that Dalpha7 mutants abolish the PSI->DLM response. NEITHER "
                "source states a single-channel conductance, an alpha or beta "
                "rate constant, an opening probability or any other receptor "
                "kinetic parameter, and their quantitative results are EPSP "
                "amplitudes, latencies, refractory periods and following "
                "frequencies measured at the circuit or muscle level. The "
                "source model uses a phenomenological double-exponential "
                "Exp2Syn, which contains NO receptor, NO subunit and NO "
                "binding kinetics, so nothing about Dalpha7 may be read back "
                "out of it. " + _NO_RECEPTOR_KINETICS + " " + _NOT_LIVE
            ),
        ),
    )


def _excluded() -> Tuple[ExcludedSynapticQuantity, ...]:
    reason = _NO_RECEPTOR_KINETICS
    return tuple(
        ExcludedSynapticQuantity(
            name=name, reason=reason,
            evidence_status=SynapticEvidenceStatus.UNSUPPORTED_FOR_KINETIC_MODEL,
        )
        for name in (
            "dalpha7_single_channel_conductance",
            "dalpha7_opening_probability",
            "dalpha7_alpha_rate",
            "dalpha7_beta_rate",
            "dalpha7_desensitization_rate",
            "dalpha7_receptor_density",
            "release_probability",
            "vesicle_pool_size",
            "synaptic_depression_model",
            "facilitation_model",
            "calcium_dependent_release",
            "presynaptic_calcium_concentration",
            "synaptic_recovery_time_constant",
            "q10_synaptic_scaling",
        )
    )


def get_synaptic_mechanism_registry() -> SynapticMechanismRegistry:
    """Return the synaptic mechanism provenance registry.

    DATA ONLY. Nothing here is implemented, connected or activated: no
    synaptic current, no receptor kinetics, no change to any compartment and
    no change to the passive backend, the timestep policy, the 3.0D-7E
    evidence records, the 3.0D-7T extractions or the 3.0D-7U reconciliation.
    """
    return SynapticMechanismRegistry(
        name="augustin_2019_gfs_synaptic_mechanisms",
        source=(
            "Synaptic mechanism provenance for the Augustin et al. 2019 GFS "
            "model: the verbatim gfpn.py source line, the paper's stated value "
            "where one exists, and the evidence status of each, kept "
            "explicitly apart. ALL records are observational: NONE is eligible "
            "for the live solver and nothing is implemented or activated."
        ),
        model_id="ModelDBRepository/245415",
        model_citation=SOURCE_PAPER,
        quantities=_quantities(),
        synapses=_synapses(),
        receptor_identities=_receptors(),
        excluded=_excluded(),
        scope_note=(
            "The model builds THREE Exp2Syn point processes, not one. Only the "
            "PSI->DLMn instance matches the paper's single Table 1 "
            "chemical-synapse row on rise, decay, reversal and delay; the "
            "paper states no value for the TTMn or PSI instances, and the "
            "source values for those differ from the paper's. TWO chemical "
            "weights are ZERO, so the chemical component of both mixed "
            "synapses contributes no conductance in the source's default "
            "parameter set. The paper states a peak conductance of 80 uS while "
            "the source writes 0.08 with NO declared unit; the ratio of the "
            "two written numbers is exactly 1000. That is an OBSERVED, "
            "UNRESOLVED DISCREPANCY, not a unit conversion: this checkpoint "
            "converts nothing, decides nothing, and defines no corrected "
            "value. Topology is recorded per synapse: GF->TTMn and GF->PSI are "
            "MIXED electrical and chemical, PSI->DLMn is CHEMICAL cholinergic "
            "with no electrical component. Dalpha7 is recorded as an "
            "EXPERIMENTALLY SUPPORTED RECEPTOR IDENTITY AND FUNCTION carrying "
            "NO quantitative kinetics, because no project source states a "
            "single-channel conductance or any rate constant for it, and the "
            "phenomenological Exp2Syn contains no receptor at all. The 0.1 ms "
            "rise time IS a SYNAPSE property, NOT a timestep, and the 0.01 ms "
            "numerical policy is untouched. This checkpoint "
            "establishes NO synaptic implementation, NO synaptic current, NO "
            "receptor kinetic model and NO resolution of the 3.0D-7U "
            "gap-junction unit conflict."
        ),
    )
