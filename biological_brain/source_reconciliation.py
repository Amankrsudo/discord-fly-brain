"""Source/code unit reconciliation (3.0D-7U).

3.0D-7E registered the gap-junction conductances as the published model states
them: 135 uS for the young fly and 34.5 uS for the old fly. 3.0D-7T extracted the
compiled NEURON source and found that the same ModelDB model expresses the
electrical synapse conductance in NANOSIEMENS, so that the literal source
statement is 135.0 nS.

Those two statements differ by a factor of exactly 1000. This module records
that disagreement as a TYPED RECONCILIATION RECORD. It does not resolve it.

The conflict
------------
Three source statements, all from the same published model:

    PAPER Table 1        "Gap junctions conductance (ggap, young fly)
                          135 uS (estimated)"
    PAPER Table 1        "Gap junctions conductance (ggap, old fly)
                          34.5 uS (estimated)"
    PAPER Results        "Setting the gap junction conductance (ggap) of all
                          model electrical synapses to 135 uS resulted in the
                          voltage recordings shown in Figure 2B, top."
    MODELDB gfpn.py      'g_gap': 135.0     assigned to gap2.g
    MODELDB gap2.mod     g = 0 (nanosiemens)
    MODELDB gfpn.py      self.GF_TTMn_gap.g = params['g_gap']
    MODELDB gfpn.py      self.GF_PSI_gap.g = params['g_gap']

Read literally, the code executes 135.0 nS, which is 0.135 uS. Read as the
paper states it, the intended conductance is 135 uS. The ratio is 1000.

What this module does NOT do
----------------------------
It does NOT decide which statement is wrong. Three explanations remain open and
the project's sources do not discriminate between them:

    (a) the gap2.mod UNIT DECLARATION is wrong and the mechanism is in fact
        microS;
    (b) the gfpn.py NUMERIC VALUES are wrong for the declared nanoSiemens unit;
    (c) the PAPER's stated unit is wrong.

No authoritative erratum, correction, or maintainer statement has been found.
Accordingly this record is ``source_code_unit_conflict`` / ``unresolved`` and
carries no corrected value.

It also does NOT:

- add a ``corrected_g_gap`` parameter, or any parameter that stands in for a
  resolved answer;
- change the 3.0D-7E values 135.0 uS and 34.5 uS;
- change any 3.0D-7T extraction, provenance or verbatim text;
- convert the paper's 135 uS into 135 nS, or the source's 135 nS into 135 uS, as
  if either conversion settled the question;
- authorize a gap-junction conductance for the live solver;
- touch the passive solver, the active profiles or the timestep policy.

The only conversion performed is the UNAMBIGUOUS, EXACT SI prefix conversion
nS -> uS, and it exists solely so the two sides can be compared on one axis.
It is a comparison operation, NOT a correction: the converted figure is labelled
``modeldb_literal_uS`` and never presented as the gap junction conductance to
use.

Scope of the comparison
-----------------------
The conversion axis is chosen so that the two sides are comparable: both are
expressed in MICROsiemens, the unit the paper states. The paper side therefore
needs no conversion, and the ModelDB side is converted from nanoSiemens. Both
original statements remain stored at full precision in their own units.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from .provenance import ParameterProvenance, ProvenanceRecord


# --- status vocabularies ----------------------------------------------------

CONFLICT_STATUS_SOURCE_CODE_UNIT_CONFLICT = "source_code_unit_conflict"
RESOLUTION_STATUS_UNRESOLVED = "unresolved"

# Side labels. Neither is privileged: the ordering is document order, not
# precedence.
SIDE_PAPER_INTENDED = "paper_intended"
SIDE_MODELDB_LITERAL = "modeldb_literal"


class ConflictStatus(Enum):
    """Typed classification of a recorded source disagreement.

    Only one member exists in 3.0D-7U. A second member naming a resolution
    ('fixed', 'corrected', 'modeldb_error', 'paper_error', ...) may only be added
    when an authoritative source establishes it, and adding one requires
    changing this module's documentation, not merely its data.
    """

    SOURCE_CODE_UNIT_CONFLICT = CONFLICT_STATUS_SOURCE_CODE_UNIT_CONFLICT


class ResolutionStatus(Enum):
    """Typed resolution state of a recorded source disagreement."""

    UNRESOLVED = RESOLUTION_STATUS_UNRESOLVED


# --- exact paper and source conductances ------------------------------------
#
# These are the required fixtures. They are literal constants, NOT the result of
# a floating-point chain: 1e-3 * 135.0 is not used to produce 0.135 anywhere in
# this module's data, and a test asserts the stored values are exact.

PAPER_YOUNG_US = 135.0
PAPER_OLD_US = 34.5
MODELDB_YOUNG_NS = 135.0
MODELDB_OLD_NS = 34.5
MODELDB_YOUNG_US = 0.135
MODELDB_OLD_US = 0.0345
YOUNG_DISCREPANCY_FACTOR = 1000.0
OLD_DISCREPANCY_FACTOR = 1000.0

# The only conversion this module performs, stated exactly.
NS_PER_US = 1000.0

# Canonical comparison axis.
COMPARISON_UNIT = "uS"

# --- source references ------------------------------------------------------

SOURCE_PAPER_CITATION = (
    "Augustin H, Zylbertal A, Partridge L (2019). A computational model of the "
    "escape response latency in the giant fiber system of Drosophila "
    "melanogaster. eNeuro 6(2):ENEURO.0423-18.2019. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ "
    "(PMCID PMC6469880, PMID 31001574)."
)

SOURCE_PAPER_TABLE1 = (
    SOURCE_PAPER_CITATION + " Table 1, 'Physiological parameters', rows 'Gap "
    "junctions conductance (ggap, young fly)' and 'Gap junctions conductance "
    "(ggap, old fly)'. Both rows are annotated '(estimated)'."
)

SOURCE_PAPER_RESULTS = (
    SOURCE_PAPER_CITATION + " Results, 'A conductance-based model of the "
    "Drosophila GFS reproduces aging-related latency increase': \"Setting the "
    "gap junction conductance (ggap) of all model electrical synapses to 135 uS "
    "resulted in the voltage recordings shown in Figure 2B, top.\" and "
    "\"Decreasing ggap to 34.5 uS results in longer membrane charging time to "
    "firing threshold\"."
)

SOURCE_GFPN_DECLARATION = (
    "ModelDB 245415, gfpn.py line 31: 'g_gap': 135.0"
)

SOURCE_GFPN_ASSIGNMENT_TTMN = (
    "ModelDB 245415, gfpn.py line 171: "
    "self.GF_TTMn_gap.g = params['g_gap']"
)

SOURCE_GFPN_ASSIGNMENT_PSI = (
    "ModelDB 245415, gfpn.py line 175: "
    "self.GF_PSI_gap.g = params['g_gap']"
)

SOURCE_GAP2_UNIT = (
    "ModelDB 245415, channels/gap2.mod line 12: "
    "g = 0 (nanosiemens) :1 (nanosiemens) : 1nS = 1000 pS"
)

SOURCE_GAP2_CURRENT = (
    "ModelDB 245415, channels/gap2.mod line 20: i = (v - vgap)*g*(0.001)"
)

SOURCE_SCAN_AXIS = (
    "ModelDB 245415, gfs_param_scan_conductances.py line 78: "
    "plt.ylabel(param1 + ' (uS)')"
)

SOURCE_SCAN_RANGE = (
    "ModelDB 245415, gfs_param_scan_conductances.py line 28: "
    "ranges['g_gap'] = np.arange(20, 160, 10), and line 40: old_g_gap = 34.5"
)

#: A 2025 preprint that reuses the paper's two numbers. Recorded because it is
#: the most likely source to be MISREAD as independent corroboration of the
#: microSiemens reading, and it is not: see :data:`_DERIVATIVE_NOTE`.
SOURCE_LOPEZ_2025_DERIVATIVE = (
    "Lopez J, Boerner J, Robbins K, Pena RF, Murphey R (2025). Frazzled/DCC "
    "regulates gap junction formation at a Drosophila giant synapse through "
    "transcription. bioRxiv preprint 2025.04.08.647628, posted 9 April 2025. "
    "https://doi.org/10.1101/2025.04.08.647628 . Its Figure 5B parameter-scan "
    "axis is labelled 'min L = 34.5 uS, max L = 135 uS, Gap Junction "
    "Conductance (uS)', i.e. the same two numbers as the Augustin 2019 paper, "
    "in microSiemens. Read from the full text of the 48-page PDF."
)

_DERIVATIVE_NOTE = (
    "A 2025 preprint (Lopez et al., bioRxiv 2025.04.08.647628) scans the same "
    "34.5-135 uS range and therefore APPEARS to corroborate the paper's "
    "microSiemens reading. IT IS NOT INDEPENDENT EVIDENCE. Its own text states "
    "that it 'set our limits of gap junction conductance following parameters "
    "found in Augustin (2019)' and 'set the upper and lower limits of "
    "conductivity based on parameters found in the Augustin (2019) model', so "
    "it inherits the paper's microSiemens figures rather than measuring them. "
    "The strings 'nS' and 'nanoSiemens' do not occur anywhere in its 48 pages, "
    "so it never engages with the gap2.mod unit declaration and cannot "
    "discriminate between the two representations. It is recorded as a "
    "DERIVATIVE source and adds no independent evidence in either direction. "
)

_NO_CORRECTION_NOTE = (
    "NO CORRECTED VALUE EXISTS. There is deliberately NO 'corrected_g_gap' "
    "parameter and no other field standing in for a resolved answer. Neither "
    "side is preferred, and the converted figure exists only so the two "
    "statements can be compared on one axis."
)

_UNRESOLVED_NOTE = (
    "UNRESOLVED. The three source statements disagree by a factor of exactly "
    "1000 and no authoritative source establishes which is right. Three "
    "explanations remain open: (a) the gap2.mod UNIT DECLARATION is wrong and "
    "the mechanism is in fact microS; (b) the gfpn.py NUMERIC VALUES are wrong "
    "for the declared nanoSiemens unit; (c) the PAPER's stated unit is wrong. "
    "No erratum, correction or maintainer statement has been found that "
    "discriminates between them. The status is NOT 'fixed', NOT 'corrected', "
    "NOT 'biologically resolved', and this record asserts neither a ModelDB "
    "error nor a paper error."
)

_CONVERSION_NOT_A_CORRECTION = (
    "The normalized value is a COMPARISON, not a correction. "
    "1 nanoSiemens = 1e-3 microSiemens exactly, so 135 nS = 0.135 uS and "
    "34.5 nS = 0.0345 uS. Stating that conversion does NOT decide which "
    "statement is correct, does NOT license replacing 135 uS with 0.135 uS in "
    "any evidence record, and does NOT authorize either figure for the solver."
)

_NO_SOLVER_NOTE = (
    "NOT ELIGIBLE FOR THE LIVE SOLVER. This record authorizes no gap-junction "
    "conductance, populates no Compartment, no CableParameters and no "
    "CompartmentElectrical, and changes no solver behaviour, no passive profile "
    "and no timestep policy."
)


@dataclass(frozen=True)
class UnitConversion:
    """One exact unit conversion, recorded with its arithmetic.

    Only exact SI prefix conversions belong here. A conversion that would need
    an assumption (for example converting a membrane conductance DENSITY to a
    whole-cell conductance without an area) is not a conversion and is not
    recorded as one.
    """

    from_unit: str
    to_unit: str
    multiplier_from_to: float
    arithmetic: str
    unambiguous: bool = True
    is_correction: bool = False

    def __post_init__(self) -> None:
        if not self.unambiguous:
            raise ValueError(
                "This module records only unambiguous conversions."
            )
        if self.is_correction:
            raise ValueError(
                "A unit conversion in 3.0D-7U is a COMPARISON, never a "
                "correction. Resolving the conflict would require an "
                "authoritative source, not a unit conversion."
            )

    def convert(self, value: float) -> float:
        return value * self.multiplier_from_to


@dataclass(frozen=True)
class ConductanceSide:
    """One side of the disagreement, stored in its OWN source unit.

    ``value`` and ``unit`` are the source's own statement, unconverted. The
    normalized comparison value lives on the conflict record, not here, so that
    a converted figure can never be mistaken for a source statement.
    """

    side: str
    label: str
    value: float
    unit: str
    verbatim_statement: str
    source: str
    source_references: Tuple[str, ...]
    provenance_category: ParameterProvenance
    limitations: str

    def __post_init__(self) -> None:
        if self.side not in (SIDE_PAPER_INTENDED, SIDE_MODELDB_LITERAL):
            raise ValueError(
                f"Unknown side '{self.side}'. Only '{SIDE_PAPER_INTENDED}' and "
                f"'{SIDE_MODELDB_LITERAL}' exist; this registry records no "
                f"third, authoritative side."
            )
        if not self.verbatim_statement:
            raise ValueError(
                f"Side '{self.side}' must carry its source's verbatim text."
            )
        if not self.source_references:
            raise ValueError(
                f"Side '{self.side}' must carry at least one source reference."
            )

    @property
    def is_preferred(self) -> bool:
        """Always False. This registry never prefers one side over the other."""
        return False

    @property
    def provenance(self) -> ProvenanceRecord:
        return ProvenanceRecord(self.provenance_category, self.source)


@dataclass(frozen=True)
class SourceConflictRecord:
    """One recorded, still-unresolved disagreement between two sources.

    The record holds BOTH sides in their own units, one normalized comparison
    value, and the exact discrepancy factor. It deliberately has NO field for a
    resolved value and NO field for a preferred side.
    """

    conflict_id: str
    parameter_name: str
    fly_condition: str
    paper_side: ConductanceSide
    modeldb_side: ConductanceSide
    conversion: UnitConversion
    normalized_comparison_value: float
    normalized_comparison_unit: str
    discrepancy_factor: float
    conflict_status: ConflictStatus
    resolution_status: ResolutionStatus
    explanatory_note: str
    source_references: Tuple[str, ...]
    linked_records: Tuple[Tuple[str, str, str], ...]
    preferred_side: Optional[str] = None
    corrected_value_available: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.preferred_side is not None:
            raise ValueError(
                f"Conflict '{self.conflict_id}' must not name a preferred "
                f"side. The disagreement is unresolved; preferring one side "
                f"would be a resolution this checkpoint cannot make."
            )
        if self.corrected_value_available:
            raise ValueError(
                f"Conflict '{self.conflict_id}' must not report a corrected "
                f"value. No authoritative source establishes one."
            )
        if self.live_solver_eligible:
            raise ValueError(
                f"Conflict '{self.conflict_id}' cannot be live-solver "
                f"eligible. A reconciliation record authorizes nothing."
            )
        if self.conflict_status is not (
            ConflictStatus.SOURCE_CODE_UNIT_CONFLICT
        ):
            raise ValueError(
                f"Conflict '{self.conflict_id}' has status "
                f"'{self.conflict_status.value}', but 3.0D-7U records exactly "
                f"one status: "
                f"'{CONFLICT_STATUS_SOURCE_CODE_UNIT_CONFLICT}'."
            )
        if self.resolution_status is not ResolutionStatus.UNRESOLVED:
            raise ValueError(
                f"Conflict '{self.conflict_id}' has resolution status "
                f"'{self.resolution_status.value}'. No authoritative source "
                f"establishes a resolution, so the only permitted status is "
                f"'{RESOLUTION_STATUS_UNRESOLVED}'."
            )
        if self.paper_side.side != SIDE_PAPER_INTENDED:
            raise ValueError(
                f"Conflict '{self.conflict_id}' must place the paper statement "
                f"on the '{SIDE_PAPER_INTENDED}' side."
            )
        if self.modeldb_side.side != SIDE_MODELDB_LITERAL:
            raise ValueError(
                f"Conflict '{self.conflict_id}' must place the source statement "
                f"on the '{SIDE_MODELDB_LITERAL}' side."
            )
        if self.paper_side.value <= 0.0 or self.modeldb_side.value <= 0.0:
            raise ValueError(
                f"Conflict '{self.conflict_id}' must compare positive "
                f"conductances; a non-positive value is not a conductance."
            )
        if self.normalized_comparison_unit != COMPARISON_UNIT:
            raise ValueError(
                f"Conflict '{self.conflict_id}' must normalize onto the "
                f"comparison unit '{COMPARISON_UNIT}'."
            )
        if self.discrepancy_factor <= 1.0:
            raise ValueError(
                f"Conflict '{self.conflict_id}' must report a discrepancy "
                f"factor greater than 1, otherwise the two sides would agree."
            )
        if not self.source_references:
            raise ValueError(
                f"Conflict '{self.conflict_id}' must carry source references."
            )

    @property
    def both_sides_preserved(self) -> bool:
        """True: the record stores each side in its own source unit."""
        return (
            self.paper_side.unit == "uS"
            and self.modeldb_side.unit == "nS"
        )

    @property
    def is_resolved(self) -> bool:
        """Always False in 3.0D-7U."""
        return self.resolution_status is not ResolutionStatus.UNRESOLVED

    def sides(self) -> Tuple[ConductanceSide, ...]:
        return (self.paper_side, self.modeldb_side)

    def side(self, side_label: str) -> ConductanceSide:
        for entry in self.sides():
            if entry.side == side_label:
                return entry
        raise KeyError(
            f"Side '{side_label}' not in conflict '{self.conflict_id}'"
        )

    def status_text(self) -> str:
        return (
            f"{self.conflict_status.value}/{self.resolution_status.value}"
        )


@dataclass(frozen=True)
class SourceReconciliationRegistry:
    """Recorded source disagreements. NOT a resolution mechanism.

    The registry stores conflicts, links them to the evidence records that
    hold the original values, and asserts no resolution. It assigns nothing and
    is never consulted by the passive solver, the active profiles or any
    DynamicsModel.
    """

    name: str
    source: str
    model_id: str
    conflicts: Tuple[SourceConflictRecord, ...]
    scope_note: str

    def get(self, conflict_id: str) -> SourceConflictRecord:
        for record in self.conflicts:
            if record.conflict_id == conflict_id:
                return record
        raise KeyError(f"Source conflict '{conflict_id}' not in registry")

    def names(self) -> Tuple[str, ...]:
        return tuple(record.conflict_id for record in self.conflicts)

    def for_parameter(self, parameter_name: str) -> Tuple[str, ...]:
        return tuple(
            record.conflict_id
            for record in self.conflicts
            if record.parameter_name == parameter_name
        )

    def unresolved(self) -> Tuple[str, ...]:
        return tuple(
            record.conflict_id
            for record in self.conflicts
            if record.resolution_status is ResolutionStatus.UNRESOLVED
        )

    def for_fly_condition(self, condition: str) -> SourceConflictRecord:
        for record in self.conflicts:
            if record.fly_condition == condition:
                return record
        raise KeyError(f"No recorded conflict for fly condition '{condition}'")

    def any_resolved(self) -> bool:
        """Always False in 3.0D-7U: no conflict is resolved."""
        return any(record.is_resolved for record in self.conflicts)

    def any_live_solver_eligible(self) -> bool:
        """Always False in 3.0D-7U."""
        return any(record.live_solver_eligible for record in self.conflicts)

    def any_preferred_side(self) -> bool:
        """Always False in 3.0D-7U: neither side is privileged."""
        return any(
            record.paper_side.is_preferred or record.modeldb_side.is_preferred
            for record in self.conflicts
        )

    def linked_record_names(self) -> Tuple[str, ...]:
        seen: Dict[str, None] = {}
        for record in self.conflicts:
            for target, _, _ in record.linked_records:
                seen.setdefault(target, None)
        return tuple(seen)

    def linked_records_for(self, conflict_id: str) -> Tuple[
        Tuple[str, str, str], ...
    ]:
        return self.get(conflict_id).linked_records

    def links_to_record(self, target_record_name: str) -> Tuple[str, ...]:
        """Conflicts that link to a named evidence record."""
        return tuple(
            record.conflict_id
            for record in self.conflicts
            for target, _, _ in record.linked_records
            if target == target_record_name
        )


_NS_TO_US = UnitConversion(
    from_unit="nS",
    to_unit=COMPARISON_UNIT,
    multiplier_from_to=1.0 / NS_PER_US,
    arithmetic=(
        "1 nS = 1e-3 uS exactly; 135.0 nS * 1e-3 = 0.135 uS; "
        "34.5 nS * 1e-3 = 0.0345 uS"
    ),
)


def _paper_side(fly_condition: str, value: float, statement: str) -> ConductanceSide:
    return ConductanceSide(
        side=SIDE_PAPER_INTENDED,
        label=f"paper_intended_{fly_condition}",
        value=value,
        unit="uS",
        verbatim_statement=statement,
        source=SOURCE_PAPER_TABLE1,
        source_references=(
            SOURCE_PAPER_TABLE1,
            SOURCE_PAPER_RESULTS,
        ),
        provenance_category=ParameterProvenance.ESTIMATED,
        limitations=(
            "The paper's Table 1 row is annotated '(estimated)': this is a "
            "MODEL PARAMETER CHOSEN TO MATCH RECORDED LATENCIES, not a direct "
            "measurement of a gap junction. The Results text states that "
            "setting g_gap to this value reproduces the young- and old-fly "
            "latencies. The paper states the unit as MICROsiemens. "
            + _UNRESOLVED_NOTE
        ),
    )


def _modeldb_side(fly_condition: str, value: float) -> ConductanceSide:
    statement = "'g_gap': 135.0"
    if fly_condition == "old":
        statement = (
            "gfpn.py declares only the young value 135.0; the old value 34.5 "
            "appears in gfs_param_scan_conductances.py line 40 as "
            "old_g_gap = 34.5, and is assigned through the same set_param path"
        )
    return ConductanceSide(
        side=SIDE_MODELDB_LITERAL,
        label=f"modeldb_literal_{fly_condition}",
        value=value,
        unit="nS",
        verbatim_statement=statement,
        source=(
            "ModelDB 245415 compiled source: gfpn.py assigns g_gap to "
            "gap2.g, whose parameter is declared in channels/gap2.mod as "
            "g = 0 (nanosiemens)."
        ),
        source_references=(
            SOURCE_GFPN_DECLARATION,
            SOURCE_GFPN_ASSIGNMENT_TTMN,
            SOURCE_GFPN_ASSIGNMENT_PSI,
            SOURCE_GAP2_UNIT,
            SOURCE_GAP2_CURRENT,
            SOURCE_SCAN_AXIS,
            SOURCE_SCAN_RANGE,
        ),
        provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
        limitations=(
            "This is the LITERAL EXECUTION UNIT of the compiled mechanism, "
            "not a reinterpretation. gap2.mod declares g in nanoSiemens and "
            "gap2's current expression 'i = (v - vgap)*g*(0.001)' is dimensioned "
            "for that unit. " + _UNRESOLVED_NOTE
        ),
    )


def _conflict(
    conflict_id: str,
    fly_condition: str,
    paper_value: float,
    modeldb_value: float,
    normalized_value: float,
    discrepancy_factor: float,
    linked_records: Tuple[Tuple[str, str, str], ...],
) -> SourceConflictRecord:
    paper_statement = (
        f"Table 1: 'Gap junctions conductance (ggap, {fly_condition} fly) "
        f"{paper_value} uS (estimated)'"
    )
    note = (
        f"The paper states {paper_value} uS and the compiled ModelDB source "
        f"executes {modeldb_value} nS = {normalized_value} uS. The ratio is "
        f"exactly {discrepancy_factor:g}. " + _CONVERSION_NOT_A_CORRECTION + " "
        + _UNRESOLVED_NOTE + " " + _NO_CORRECTION_NOTE + " " + _NO_SOLVER_NOTE
        + " " + _DERIVATIVE_NOTE
    )
    return SourceConflictRecord(
        conflict_id=conflict_id,
        parameter_name="g_gap",
        fly_condition=fly_condition,
        paper_side=_paper_side(fly_condition, paper_value, paper_statement),
        modeldb_side=_modeldb_side(fly_condition, modeldb_value),
        conversion=_NS_TO_US,
        normalized_comparison_value=normalized_value,
        normalized_comparison_unit=COMPARISON_UNIT,
        discrepancy_factor=discrepancy_factor,
        conflict_status=ConflictStatus.SOURCE_CODE_UNIT_CONFLICT,
        resolution_status=ResolutionStatus.UNRESOLVED,
        explanatory_note=note,
        source_references=(
            SOURCE_PAPER_TABLE1,
            SOURCE_PAPER_RESULTS,
            SOURCE_GFPN_DECLARATION,
            SOURCE_GFPN_ASSIGNMENT_TTMN,
            SOURCE_GFPN_ASSIGNMENT_PSI,
            SOURCE_GAP2_UNIT,
            SOURCE_GAP2_CURRENT,
            SOURCE_SCAN_AXIS,
            SOURCE_SCAN_RANGE,
            SOURCE_LOPEZ_2025_DERIVATIVE,
        ),
        linked_records=linked_records,
    )


def get_source_reconciliation_registry() -> SourceReconciliationRegistry:
    """Return the source reconciliation registry.

    DATA ONLY. It records the g_gap unit disagreement and asserts NO
    resolution. The 3.0D-7E values, the 3.0D-7T extractions, every passive
    profile and every solver behaviour are unchanged by building it.
    """
    return SourceReconciliationRegistry(
        name="modeldb_245415_g_gap_unit_conflict",
        source=(
            "Reconciliation record for the g_gap UNIT disagreement between the "
            "Augustin et al. 2019 paper and the ModelDB 245415 compiled source. "
            "Both sides are preserved in their own units. The conflict is "
            "unresolved, neither side is preferred, no corrected value exists, "
            "and nothing here is eligible for the live solver."
        ),
        model_id="ModelDBRepository/245415",
        conflicts=(
            _conflict(
                conflict_id="g_gap_young_unit_conflict",
                fly_condition="young",
                paper_value=PAPER_YOUNG_US,
                modeldb_value=MODELDB_YOUNG_NS,
                normalized_value=MODELDB_YOUNG_US,
                discrepancy_factor=YOUNG_DISCREPANCY_FACTOR,
                linked_records=(
                    (
                        "gap_junction_conductance_young",
                        "passive_electrical_registry",
                        "3.0D-7E holds 135.0 uS and is UNCHANGED by this "
                        "record.",
                    ),
                    (
                        "gap2",
                        "active_mechanism_registry",
                        "3.0D-7T gap2 extraction, whose quantity 'g_gap' "
                        "records the source value 135.0 in nS with its "
                        "canonical comparison pair 0.135 uS.",
                    ),
                    (
                        "g_gap",
                        "active_mechanism_registry",
                        "3.0D-7T gap2 quantity 'g_gap' at gfpn.py line 31.",
                    ),
                    (
                        "gfpn.py",
                        "ModelDBRepository/245415",
                        "Lines 31, 171 and 175: declaration and both "
                        "assignments.",
                    ),
                    (
                        "channels/gap2.mod",
                        "ModelDBRepository/245415",
                        "Line 12 declares g = 0 (nanosiemens); line 20 is the "
                        "current expression.",
                    ),
                ),
            ),
            _conflict(
                conflict_id="g_gap_old_unit_conflict",
                fly_condition="old",
                paper_value=PAPER_OLD_US,
                modeldb_value=MODELDB_OLD_NS,
                normalized_value=MODELDB_OLD_US,
                discrepancy_factor=OLD_DISCREPANCY_FACTOR,
                linked_records=(
                    (
                        "gap_junction_conductance_old",
                        "passive_electrical_registry",
                        "3.0D-7E holds 34.5 uS and is UNCHANGED by this "
                        "record.",
                    ),
                    (
                        "gfs_param_scan_conductances.py",
                        "ModelDBRepository/245415",
                        "Line 40 sets old_g_gap = 34.5, the value this record "
                        "tracks on the literal side.",
                    ),
                    (
                        "gfpn.py",
                        "ModelDBRepository/245415",
                        "Lines 198-200: set_param('g_gap', ...) assigns gp.g "
                        "to both gap2 objects, the path the scan uses.",
                    ),
                    (
                        "channels/gap2.mod",
                        "ModelDBRepository/245415",
                        "Line 12 declares g = 0 (nanosiemens).",
                    ),
                ),
            ),
        ),
        scope_note=(
            "The paper states the gap junction conductance in MICROsiemens "
            "(135 uS young, 34.5 uS old) and reports that those values reproduce "
            "the recorded young- and old-fly latencies. The compiled ModelDB "
            "source declares the gap2 conductance parameter in NANOSIEMENS, so "
            "the literal source executes 135.0 nS, which is 0.135 uS. The two "
            "statements differ by a factor of exactly 1000. NO authoritative "
            "source establishes whether the gap2.mod unit declaration is wrong, "
            "whether the gfpn.py numbers are wrong for that unit, or whether "
            "the paper's unit is wrong, so this record is a "
            "source_code_unit_conflict and is UNRESOLVED. It names no preferred "
            "side, holds no corrected value, and defines no 'corrected_g_gap' "
            "parameter. Both 3.0D-7E values remain exactly 135.0 uS and 34.5 "
            "uS, and both 3.0D-7T source values remain exactly 135.0 nS and "
            "34.5 nS. This checkpoint changes no solver behaviour, no passive "
            "profile, no active profile and no timestep policy."
        ),
    )
