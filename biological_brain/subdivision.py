"""Derived computational subdivision of anatomical sections (3.0D-7K).

This is a NUMERICAL DISCRETIZATION layer, not biology.

A source anatomical section is divided into N computational segments for
electrical purposes only. The source compartment remains the
authoritative object: its CompartmentGeometry is never overwritten,
mutated, or extended, and its source-backed provenance is never
duplicated as if each derived segment had been independently measured.

Derived segment geometry:
- length of each segment is the source length divided by the segment count
- for a uniform section, every segment keeps the source diameter
- for a linearly tapered section, each segment's proximal and distal
  diameters are the source taper evaluated at that segment's endpoints

The resulting electrical network conserves, for both conventions:
- sum(segment lengths) = source length
- sum(segment membrane areas) = source membrane area
- sum(segment axial resistances) = source axial resistance

SCIENTIFIC BOUNDARY:
segment_count is an explicit numerical configuration chosen by the
caller. The default is 1, which reproduces the un-subdivided behaviour.
There is deliberately NO automatic or "biologically correct" segment
count, and no d_lambda rule: a justified automatic count would require
neuron-specific active/passive information this project does not have.
A specific published segment count may be requested explicitly for a
reproduction experiment; that would be a modelling choice, not a
biological one.
"""

from dataclasses import dataclass, field
from math import floor
from typing import Dict, Optional, Tuple

from .morphology import Compartment, CompartmentGeometry, PlacementRecord
from .provenance import ParameterProvenance, ProvenanceRecord


DEFAULT_SEGMENT_COUNT = 1

_SOURCE_NUMERICAL = (
    "Derived numerical discretization, not a source anatomical value. "
    "The segment count is an explicit numerical configuration chosen by the "
    "caller. No biological provenance category applies to derived segment "
    "lengths or diameters: they are not measured, not published anatomy, and "
    "not estimated."
)


@dataclass(frozen=True)
class SectionSubdivision:
    """Explicit subdivision configuration for one anatomical section.

    section_id references the source anatomical compartment. The derived
    segments are NOT stored on that compartment.
    """

    section_id: str
    segment_count: int = DEFAULT_SEGMENT_COUNT
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            ParameterProvenance.UNKNOWN, _SOURCE_NUMERICAL
        )
    )
    derivation: str = "numerical subdivision of the source section"

    def __post_init__(self) -> None:
        if self.segment_count < 1:
            raise ValueError(
                f"segment_count must be >= 1, got {self.segment_count} "
                f"for section '{self.section_id}'"
            )


@dataclass(frozen=True)
class SubdivisionPlan:
    """The subdivision configuration for a whole model.

    Sections absent from ``sections`` are subdivided into 1 segment, which
    is the default and preserves the un-subdivided behaviour.
    """

    sections: Tuple[SectionSubdivision, ...] = ()

    def section(self, section_id: str) -> Optional[SectionSubdivision]:
        for s in self.sections:
            if s.section_id == section_id:
                return s
        return None

    def segment_count_for(self, section_id: str) -> int:
        found = self.section(section_id)
        return found.segment_count if found is not None else DEFAULT_SEGMENT_COUNT


@dataclass(frozen=True)
class DerivedSegment:
    """One derived computational segment of a source anatomical section.

    The geometry here is a DERIVED COPY. It is never written back to the
    source CompartmentGeometry.
    """

    segment_id: str
    source_section_id: str
    segment_index: int
    segment_count: int
    geometry: CompartmentGeometry
    source_geometry_provenance: ProvenanceRecord
    subdivision_provenance: ProvenanceRecord
    derivation: str

    @property
    def is_derived_segment(self) -> bool:
        return self.segment_count > 1


def _taper_diameter_at(
    d_proximal: float, d_distal: float, length_um: float, x_um: float
) -> float:
    """Source taper evaluated at a distance from the proximal end."""
    if length_um <= 0:
        return d_proximal
    return d_proximal + (d_distal - d_proximal) * (x_um / length_um)


def derive_segments(
    compartment: Compartment, plan: Optional[SubdivisionPlan] = None
) -> Tuple[DerivedSegment, ...]:
    """Derive computational segments for one source section.

    Returns a single segment whose id equals the section id when the
    segment count is 1, so un-subdivided behaviour is unchanged.
    """
    source = plan.segment_count_for(compartment.compartment_id) if plan is not None \
        else DEFAULT_SEGMENT_COUNT
    subdivision = plan.section(compartment.compartment_id) if plan is not None else None

    geometry = compartment.geometry
    source_provenance = ProvenanceRecord(
        ParameterProvenance.UNKNOWN,
        "Source geometry provenance of section "
        f"'{compartment.compartment_id}' is preserved on the derived segment "
        f"and is not restated per segment as an independent measurement",
    )
    subdivision_provenance = (
        subdivision.provenance if subdivision is not None
        else ProvenanceRecord(ParameterProvenance.UNKNOWN, _SOURCE_NUMERICAL)
    )

    if source == 1 or geometry.length_um is None:
        return (
            DerivedSegment(
                segment_id=compartment.compartment_id,
                source_section_id=compartment.compartment_id,
                segment_index=0,
                segment_count=1,
                geometry=CompartmentGeometry(
                    length_um=geometry.length_um,
                    diameter_um=geometry.diameter_um,
                    diameter_distal_um=geometry.diameter_distal_um,
                    position=geometry.position,
                    anatomical_role=geometry.anatomical_role,
                ),
                source_geometry_provenance=source_provenance,
                subdivision_provenance=subdivision_provenance,
                derivation=(
                    f"no subdivision: source section used as one electrical "
                    f"compartment"
                ),
            ),
        )

    length_um = geometry.length_um
    segment_length_um = length_um / source
    d_proximal = geometry.diameter_um
    d_distal = geometry.diameter_distal_um
    is_taper = d_distal is not None and d_distal != d_proximal

    segments = []
    for i in range(source):
        x0 = i * segment_length_um
        x1 = (i + 1) * segment_length_um
        if is_taper:
            proximal = _taper_diameter_at(d_proximal, d_distal, length_um, x0)
            distal = _taper_diameter_at(d_proximal, d_distal, length_um, x1)
            derivation = (
                f"derived numerical discretization: segment {i} of {source} of "
                f"section '{compartment.compartment_id}', length "
                f"{length_um}/{source} = {segment_length_um} um, diameters "
                f"evaluated on the source linear taper at x={x0}..{x1} um"
            )
        else:
            proximal = d_proximal
            distal = d_proximal if d_distal is not None else None
            derivation = (
                f"derived numerical discretization: segment {i} of {source} of "
                f"section '{compartment.compartment_id}', length "
                f"{length_um}/{source} = {segment_length_um} um, source "
                f"diameter carried to every segment"
            )
        segments.append(
            DerivedSegment(
                segment_id=f"{compartment.compartment_id}#seg{i}",
                source_section_id=compartment.compartment_id,
                segment_index=i,
                segment_count=source,
                geometry=CompartmentGeometry(
                    length_um=segment_length_um,
                    diameter_um=proximal,
                    diameter_distal_um=distal,
                    anatomical_role=geometry.anatomical_role,
                ),
                source_geometry_provenance=source_provenance,
                subdivision_provenance=subdivision_provenance,
                derivation=derivation,
            )
        )
    return tuple(segments)


def map_placement_to_segment(
    distance_um: float, section_length_um: float, segment_count: int
) -> int:
    """Map a source placement distance onto a derived segment index.

    Source placement distances are measured from the proximal end of the
    ORIGINAL anatomical section and are not modified. This is a
    computational mapping only.

    The exact distal endpoint clamps deterministically to the final
    segment.
    """
    if segment_count < 1:
        raise ValueError(f"segment_count must be >= 1, got {segment_count}")
    if section_length_um is None or section_length_um <= 0:
        raise ValueError(
            "Cannot map a placement without a source section length"
        )
    segment_length_um = section_length_um / segment_count
    index = int(floor(distance_um / segment_length_um))
    if index < 0:
        return 0
    if index > segment_count - 1:
        return segment_count - 1
    return index


def map_placements_for_section(
    compartment: Compartment, segments: Tuple[DerivedSegment, ...]
) -> Tuple[Tuple[PlacementRecord, str, int], ...]:
    """Map every source placement of a section onto its derived segment.

    Returns tuples of (source PlacementRecord, derived segment id, index).
    The PlacementRecord is returned unmodified: the original distance in
    original-section coordinates is preserved.
    """
    count = segments[0].segment_count
    mapped = []
    for placement in compartment.placements:
        index = map_placement_to_segment(
            placement.distance_um, compartment.geometry.length_um, count
        )
        mapped.append((placement, segments[index].segment_id, index))
    return tuple(mapped)
