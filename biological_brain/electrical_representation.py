"""Explicit electrical-representation declarations (3.0D-7I).

Some compartments are anatomically real in the source-backed morphology
but cannot currently be represented as electrical compartments, because
the source does not provide the geometry the passive cable equations
require. The canonical example is a soma for which only a diameter is
reported: membrane capacitance and leak conductance need a membrane
SURFACE AREA, and no cylindrical soma length is available.

This module records that limitation as an explicit, provenance-visible
DECLARATION rather than as a biological fact and rather than as silence.

What an exclusion does NOT mean:
- It does NOT mean the compartment is biologically electrically irrelevant.
  The soma is a real, current-carrying part of the neuron.
- It does NOT mean the compartment has zero membrane area.
- It does NOT mean experimental evidence says the compartment is absent.
- It does NOT mean the compartment is electrically disconnected. It means
  the CURRENT computational representation cannot represent it.

What an exclusion DOES mean:
- The compartment remains fully present in the anatomical morphology with
  its source-backed geometry and provenance untouched.
- The compartment does not enter a passive electrical network, so it
  receives no capacitance, no leak conductance, and no axial resistance.
- Children of an excluded compartment become electrical roots in the
  derived electrical topology. No axial path is invented across the
  excluded compartment.

This module is DATA ONLY. It assigns no biological parameter, does not
modify CompartmentGeometry, and does not alter any source-backed value.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .provenance import ParameterProvenance, ProvenanceRecord


EXCLUSION_INSUFFICIENT_GEOMETRY = "insufficient_source_backed_geometry"

SCOPE_COMPUTATIONAL_LIMITATION = "computational_representation_limitation"

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
        provenance=ProvenanceRecord(
            ParameterProvenance.UNKNOWN, _SOURCE_DECISION
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
