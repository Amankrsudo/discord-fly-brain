"""Explicit electrical-representation declarations (3.0D-7I) and explicit
geometry-readiness blockers (3.0D-7M).

Some compartments are anatomically real in the source-backed morphology
but cannot currently be represented as electrical compartments, because
the source does not provide the geometry the passive cable equations
require. There are two distinct situations, and this module keeps them
distinct:

1. An EXCLUSION (3.0D-7I, 3.0D-7N) for a compartment the selected
   computational abstraction does not represent:

   a. INSUFFICIENT GEOMETRY (3.0D-7I) for a computational-soma convenience:
      the source reports a soma diameter and no soma length at all, so no
      membrane area can be derived. The soma is not a real modelled section of
      the published simplified model; it exists in our topology as a root.

   b. COMPUTATIONAL MODEL SCOPE (3.0D-7N) for a real anatomical/context
      section that the selected abstraction does not model, such as
      GF_medial_dendrite: the Augustin 2019 simplified model represents the GF
      as a single modeled section and specifies no separate computational
      geometry for a medial dendrite. The section is retained in the
      anatomical/context morphology with its placement and provenance
      untouched.

   An excluded compartment never enters a passive network, receives no
   capacitance, leak conductance, or axial resistance, and produces no derived
   subdivision segments or electrical placement mappings. It is never
   silently dropped: the exclusion is an explicit, queryable record.

2. A GEOMETRY BLOCKER (3.0D-7M) for a real modelled section whose
   source-backed geometry is incomplete AND which the selected computational
   abstraction DOES intend to represent. A blocker is NOT an exclusion: the
   section stays in the anatomy, keeps its placement and topology, and is
   never silently dropped from the network. Passive preparation rejects it.
   The GFS models declare no blockers; the machinery remains for any model
   whose abstraction does intend to represent an under-specified section.

This module records those limitations as explicit, provenance-visible
DECLARATIONS rather than as biological facts and rather than as silence.

What an exclusion or a blocker does NOT mean:
- It does NOT mean the compartment is biologically electrically irrelevant.
  The soma and the GF medial dendrite are real, current-carrying parts of
  the neuron.
- It does NOT mean the compartment has zero membrane area.
- It does NOT mean the biological structure does not exist, or that it has no
  geometry in nature. It means the CURRENT source-backed simplified model,
  as published, does not specify enough to represent it computationally.
- It does NOT mean experimental evidence says the compartment is absent.
- It does NOT mean the compartment is electrically disconnected. It means
  the CURRENT computational representation cannot represent it.
- It is NOT an estimate and NOT permission to substitute geometry from
  another reconstruction, another neuron, or another species.

What an exclusion or a blocker DOES mean:
- The compartment remains fully present in the anatomical morphology with
  its source-backed geometry and provenance untouched.
- An excluded compartment does not enter a passive electrical network, so it
  receives no capacitance, no leak conductance, and no axial resistance.
  Children of an excluded compartment become electrical roots; no axial path
  is invented across the excluded compartment.
- A blocked compartment cannot enter a passive electrical network at all, so
  preparing a model that contains it fails explicitly and is never
  approximated, defaulted, or subdivided into invented geometry.

This module is DATA ONLY. It assigns no biological parameter, does not
modify CompartmentGeometry, and does not alter any source-backed value.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .provenance import ParameterProvenance, ProvenanceRecord


EXCLUSION_INSUFFICIENT_GEOMETRY = "insufficient_source_backed_geometry"

EXCLUSION_COMPUTATIONAL_MODEL_SCOPE = "outside_computational_model_scope"

SCOPE_COMPUTATIONAL_LIMITATION = "computational_representation_limitation"

# The geometry fields a section needs before a membrane area can be derived
# at all. A blocker always names which of these are absent.
REQUIRED_GEOMETRY_FIELDS = ("length_um", "diameter_um")

BLOCKER_REASON_INSUFFICIENT_SOURCE_GEOMETRY = (
    "Source-backed simplified GFS model does not provide sufficient geometry "
    "for this computational section."
)

_NOT_BIOLOGICAL_CLAIM = (
    "This is a computational representation limitation caused by "
    "insufficient source-backed geometry. It is NOT a biological claim: the "
    "compartment is anatomically real and electrically relevant, it is not "
    "described as having zero membrane area, and this is not experimental "
    "evidence of anything."
)

_SOURCE_DECISION = (
    "Decision made in 3.0D-7I: the source-backed morphology does not provide "
    "the geometry required to compute a membrane area for this compartment, "
    "and inventing it is forbidden. Declared excluded from passive electrical "
    "representation. " + _NOT_BIOLOGICAL_CLAIM
)

_BLOCKER_SOURCE = (
    "Blocker recorded in 3.0D-7M: the source-backed simplified GFS model does "
    "not provide sufficient geometry for this computational section, so it "
    "cannot enter a passive electrical representation. This records "
    "INCOMPLETE SOURCE EVIDENCE FOR THE COMPUTATIONAL REPRESENTATION ONLY. It "
    "is NOT a claim that the biological structure does not exist, NOT a claim "
    "that the structure has no geometry in nature, NOT an estimate, and NOT "
    "permission to substitute geometry from another reconstruction, another "
    "neuron, or another species. No geometry is invented, defaulted, or "
    "borrowed. " + _NOT_BIOLOGICAL_CLAIM
)

_NOT_ABSENCE_CLAIM = (
    "This is a statement about the SCOPE OF THE SELECTED COMPUTATIONAL MODEL "
    "ONLY. It is NOT a claim that the biological GF lacks a medial dendrite, "
    "NOT a claim that the dendrite is biologically electrically irrelevant, "
    "NOT a claim that the dendrite does not exist, NOT a claim that its "
    "dimensions are zero, and NOT a statement that its geometry can be ignored "
    "in a future detailed anatomical model."
)

_SOURCE_COMPUTATIONAL_SCOPE_DECISION = (
    "Decision made in 3.0D-7N: the selected computational abstraction is the "
    "Augustin 2019 simplified GFS model (eLife, PMC6469880), in which the GF "
    "is represented as a single modeled section and no separate computational "
    "geometry is specified for a GF medial dendrite. The compartment is "
    "therefore excluded from the SELECTED COMPUTATIONAL REPRESENTATION ONLY, "
    "and the compartmental abstraction is declared. The compartment is "
    "retained in the anatomical/context morphology with its existing section "
    "id, topology, placement, and provenance untouched, and no geometry is "
    "invented, borrowed, or substituted from another reconstruction. " +
    _NOT_ABSENCE_CLAIM
)


_SOURCE_DECISION = (
    "Decision made in 3.0D-7I: the source-backed morphology does not provide "
    "the geometry required to compute a membrane area for this compartment, "
    "and inventing it is forbidden. Declared excluded from passive electrical "
    "representation. " + _NOT_BIOLOGICAL_CLAIM
)


@dataclass(frozen=True)
class ElectricalExclusion:
    """Declares one compartment as not electrically representable.

    This is a permission/limitation record, not a parameter. It never
    supplies a value and never modifies the compartment it names.
    """

    compartment_id: str
    reason: str
    reason_detail: str
    scope: str
    provenance: ProvenanceRecord

    def __post_init__(self) -> None:
        if self.scope != SCOPE_COMPUTATIONAL_LIMITATION:
            raise ValueError(
                f"Electrical exclusion scope must be "
                f"'{SCOPE_COMPUTATIONAL_LIMITATION}', got '{self.scope}'"
            )


def insufficient_geometry_exclusion(
    compartment_id: str, reason_detail: str
) -> ElectricalExclusion:
    """Declare a compartment excluded for insufficient source geometry."""
    return ElectricalExclusion(
        compartment_id=compartment_id,
        reason=EXCLUSION_INSUFFICIENT_GEOMETRY,
        reason_detail=reason_detail,
        scope=SCOPE_COMPUTATIONAL_LIMITATION,
        provenance=ProvenanceRecord(ParameterProvenance.UNKNOWN, _SOURCE_DECISION),
    )


def computational_scope_exclusion(
    compartment_id: str, reason_detail: str
) -> ElectricalExclusion:
    """Declare a compartment excluded from the selected computational model.

    Distinct from insufficient_geometry_exclusion: this says the selected
    computational abstraction does not model this compartment at all, not that
    the compartment is intended to be modelled but lacks source geometry.
    """
    return ElectricalExclusion(
        compartment_id=compartment_id,
        reason=EXCLUSION_COMPUTATIONAL_MODEL_SCOPE,
        reason_detail=reason_detail,
        scope=SCOPE_COMPUTATIONAL_LIMITATION,
        provenance=ProvenanceRecord(
            ParameterProvenance.UNKNOWN, _SOURCE_COMPUTATIONAL_SCOPE_DECISION
        ),
    )


@dataclass(frozen=True)
class ElectricalRepresentation:
    """The declared electrical-representation policy for one model.

    Absence (None on the model) means no exclusions have been declared,
    which is the historical behaviour. Exclusions are opt-in and always
    deliberate.
    """

    exclusions: Tuple[ElectricalExclusion, ...] = ()

    def is_excluded(self, compartment_id: str) -> bool:
        return any(e.compartment_id == compartment_id for e in self.exclusions)

    def get(self, compartment_id: str) -> ElectricalExclusion:
        for e in self.exclusions:
            if e.compartment_id == compartment_id:
                return e
        raise KeyError(
            f"Compartment '{compartment_id}' has no electrical-representation "
            f"exclusion declared"
        )

    def excluded_ids(self) -> Tuple[str, ...]:
        return tuple(e.compartment_id for e in self.exclusions)


def get_exclusions(model) -> Tuple[ElectricalExclusion, ...]:
    """Return a model's declared electrical exclusions (possibly empty)."""
    representation: Optional[ElectricalRepresentation] = getattr(
        model, "electrical_representation", None
    )
    if representation is None:
        return ()
    return representation.exclusions


@dataclass(frozen=True)
class GeometryBlocker:
    """Declares one modelled section as blocked by incomplete source geometry.

    This is a permission/limitation record, not a parameter and not a
    measurement. It never supplies a value, never modifies the section it
    names, and never denies that the biological structure exists.

    A blocker is distinct from an ElectricalExclusion. An exclusion applies to
    a computational-soma convenience; a blocker applies to a real modelled
    anatomical section (for example GF_medial_dendrite) whose source-backed
    geometry is incomplete. A blocked section is not silently omitted: it
    cannot enter a passive network at all, so preparing its model fails
    explicitly.
    """

    section_id: str
    missing_fields: Tuple[str, ...]
    reason: str
    reason_code: str
    scope: str
    provenance: ProvenanceRecord

    def __post_init__(self) -> None:
        if self.scope != SCOPE_COMPUTATIONAL_LIMITATION:
            raise ValueError(
                f"Geometry blocker scope must be "
                f"'{SCOPE_COMPUTATIONAL_LIMITATION}', got '{self.scope}'"
            )
        if not self.missing_fields:
            raise ValueError(
                "A geometry blocker must name at least one missing field"
            )
        unknown = [
            f for f in self.missing_fields if f not in REQUIRED_GEOMETRY_FIELDS
        ]
        if unknown:
            raise ValueError(
                f"Unknown missing geometry field(s) {unknown}; a section is "
                f"blocked only on {list(REQUIRED_GEOMETRY_FIELDS)}"
            )
        duplicates = len(set(self.missing_fields)) != len(self.missing_fields)
        if duplicates:
            raise ValueError(
                f"Duplicate missing geometry field(s) in {self.missing_fields}"
            )
        # Normalize to the canonical field order so repeated queries and
        # repeated constructions are deterministic.
        ordered = tuple(
            f for f in REQUIRED_GEOMETRY_FIELDS if f in self.missing_fields
        )
        object.__setattr__(self, "missing_fields", ordered)


def geometry_blocker(
    section_id: str,
    missing_fields: Tuple[str, ...],
    reason: str = BLOCKER_REASON_INSUFFICIENT_SOURCE_GEOMETRY,
) -> GeometryBlocker:
    """Declare one section blocked by insufficient source-backed geometry."""
    return GeometryBlocker(
        section_id=section_id,
        missing_fields=tuple(missing_fields),
        reason=reason,
        reason_code=EXCLUSION_INSUFFICIENT_GEOMETRY,
        scope=SCOPE_COMPUTATIONAL_LIMITATION,
        provenance=ProvenanceRecord(ParameterProvenance.UNKNOWN, _BLOCKER_SOURCE),
    )


def get_geometry_blockers(model) -> Tuple[GeometryBlocker, ...]:
    """Report modelled sections blocked by incomplete source-backed geometry.

    Deterministic: sections are visited in sorted id order, missing fields are
    reported in the canonical order of REQUIRED_GEOMETRY_FIELDS, and repeated
    calls on an unchanged model return equal results.

    Compartments carrying a declared electrical exclusion are NOT reported:
    an excluded computational soma is a declared limitation, not a missing
    geometry blocker. A blocked section is a real modelled section that
    cannot be represented, and is never silently excluded.
    """
    excluded_ids = {e.compartment_id for e in get_exclusions(model)}
    compartments = getattr(model, "compartments", {})

    blockers = []
    for section_id in sorted(compartments):
        if section_id in excluded_ids:
            continue
        geometry = compartments[section_id].geometry
        missing = tuple(
            field
            for field in REQUIRED_GEOMETRY_FIELDS
            if getattr(geometry, field, None) is None
        )
        if missing:
            blockers.append(geometry_blocker(section_id, missing))
    return tuple(blockers)
