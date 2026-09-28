"""Compartment/morphology architecture for future cable modeling (3.0D-7A).

This module defines the data structures needed to represent multi-compartment
neurons. It is an ARCHITECTURE-ONLY step: no passive cable solver, no HH,
no biological values are defined here.

The architecture distinguishes five concerns:
1. Topology    — how compartments connect (parent/neighbor relationships)
2. Geometry    — length, diameter, position (biological data, provenance-tracked)
3. Cable params — axial resistance, membrane capacitance, leak (biophysical)
4. Provenance  — where each geometry value came from
5. Simulation state — voltage/current/state variables

All biological geometry fields default to None (unknown). No values are
invented in this step.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .provenance import ParameterProvenance, ProvenanceRecord

if TYPE_CHECKING:  # pragma: no cover
    from .electrical_representation import ElectricalRepresentation


def _unknown_provenance() -> ProvenanceRecord:
    """Default provenance for unknown biological values."""
    return ProvenanceRecord(ParameterProvenance.UNKNOWN, "")


@dataclass
class CompartmentGeometry:
    """Anatomical geometry of a compartment.

    Geometry is biological data. All fields default to None (unknown).
    When populated, each value must have a matching ProvenanceRecord
    in CompartmentProvenance explaining its origin.

    Do NOT assign default biological values here.
    """
    length_um: Optional[float] = None  # compartment length (µm)
    diameter_um: Optional[float] = None  # proximal compartment diameter (µm)
    diameter_distal_um: Optional[float] = None  # distal diameter for tapered compartments (µm)
    position: Optional[Tuple[float, float, float]] = None  # (x, y, z)
    anatomical_role: Optional[str] = None  # e.g. "soma", "dendrite", "axon"


@dataclass
class CompartmentProvenance:
    """Provenance records for biological geometry values.

    Every geometry value, when present, must have a matching provenance
    record here. Defaults are UNKNOWN with no source.

    When morphology is later populated, each value should be classified as:
    - DIRECTLY_MEASURED (reconstructed/measured)
    - PUBLISHED_MODEL_PARAMETER (derived from a published reconstruction)
    - CONNECTOME_DERIVED (connectome/morphology-derived)
    - BORROWED_CROSS_CONTEXT (borrowed from another neuron/species)
    - ESTIMATED (estimated in the source)
    - FITTED_CALIBRATED (manually adjusted)
    - UNKNOWN (no source or evidence available)
    """
    length_um: ProvenanceRecord = field(default_factory=_unknown_provenance)
    diameter_um: ProvenanceRecord = field(default_factory=_unknown_provenance)
    diameter_distal_um: ProvenanceRecord = field(default_factory=_unknown_provenance)
    position: ProvenanceRecord = field(default_factory=_unknown_provenance)
    anatomical_role: ProvenanceRecord = field(default_factory=_unknown_provenance)


@dataclass
class CableParameters:
    """Biophysical cable parameters for a compartment membrane.

    These are simulation-relevant properties distinct from geometry.
    All default to None (not assigned — no invented values).

    NOTE: Axial resistance between compartments is typically derived
    from geometry (length, diameter) and cytoplasmic resistivity. It
    is NOT computed here — that is part of the passive cable solver
    deferred to a later phase.
    """
    axial_resistance_ohm_cm: Optional[float] = None
    membrane_capacitance_uf_per_cm2: Optional[float] = None
    leak_conductance_ms_per_cm2: Optional[float] = None
    leak_reversal_mV: Optional[float] = None


@dataclass
class CompartmentState:
    """Simulation state for a single compartment.

    This is simulation state (not biological data). The default voltage
    initializes the compartment at the standard Drosophila resting level
    to match existing Neuron behavior. Biological resting potential values
    are tracked separately on Neuron.resting_potential.
    """
    voltage_mV: float = -70.0


@dataclass
class PlacementRecord:
    """Records a contact or input placement on a compartment.

    Stores distance from proximal end, kind ('contact' or 'input'),
    description, and the provenance of the distance value.
    """
    distance_um: float
    kind: str
    description: str = ""
    provenance: ProvenanceRecord = field(default_factory=_unknown_provenance)


@dataclass
class Compartment:
    """A single compartment in a multi-compartment neuron model.

    Distinguishes five concerns (not mixed):
    1. Topology     — compartment_id, parent_id, neighbor_ids
    2. Geometry     — geometry (CompartmentGeometry)
    3. Cable params — cable_params (CableParameters)
    4. Provenance   — provenance (CompartmentProvenance)
    5. State        — state (CompartmentState)

    placements: List[PlacementRecord] stores contact/input metadata
    (distances from proximal end) for future synaptic location mapping.
    """
    compartment_id: str
    parent_id: Optional[str] = None
    neighbor_ids: List[str] = field(default_factory=list)
    geometry: CompartmentGeometry = field(default_factory=CompartmentGeometry)
    cable_params: CableParameters = field(default_factory=CableParameters)
    provenance: CompartmentProvenance = field(default_factory=CompartmentProvenance)
    state: CompartmentState = field(default_factory=CompartmentState)
    placements: List[PlacementRecord] = field(default_factory=list)


@dataclass
class CompartmentModel:
    """Multi-compartment morphology model for a neuron.

    When attached to a Neuron (compartment_model field), this enables
    spatial/cable behavior in future phases. When absent (None), the
    neuron uses current single-compartment behavior.

    passive_profile_name names the explicitly authorized passive parameter
    profile that a passive backend would use for this model (3.0D-7F/7G).
    It is None by default and is never inferred: a passive backend requires
    it to be set explicitly. It is a permission record only and assigns no
    values to Compartment.cable_params.

    electrical_representation records compartments that are anatomically
    represented but NOT currently representable as electrical compartments
    (3.0D-7I), typically because the source provides no geometry from which
    a membrane area could be computed. It is None by default (no exclusions
    declared). Excluded compartments keep their full anatomical geometry,
    topology, and provenance; they are simply omitted from a derived
    electrical network. This is a computational limitation, not a
    biological claim.

    No passive cable solver, HH, or biological values are implemented here.
    """

    def is_electrically_excluded(self, compartment_id: str) -> bool:
        """Whether a compartment is declared not electrically representable."""
        if self.electrical_representation is None:
            return False
        return self.electrical_representation.is_excluded(compartment_id)
    neuron_id: str
    compartments: Dict[str, Compartment] = field(default_factory=dict)
    passive_profile_name: Optional[str] = None
    electrical_representation: Optional["ElectricalRepresentation"] = None

    def add_compartment(self, compartment: Compartment) -> None:
        """Add a compartment to the model."""
        self.compartments[compartment.compartment_id] = compartment

    def add_connection(self, parent_id: str, child_id: str) -> None:
        """Establish a topological parent-child connection between compartments."""
        parent = self.compartments.get(parent_id)
        child = self.compartments.get(child_id)
        if parent is None:
            raise KeyError(f"Parent compartment '{parent_id}' not found")
        if child is None:
            raise KeyError(f"Child compartment '{child_id}' not found")
        child.parent_id = parent_id
        if child_id not in parent.neighbor_ids:
            parent.neighbor_ids.append(child_id)
