"""Builder: convert source-backed GFS morphology into CompartmentModel (3.0D-7C).

This creates the computational topology (compartment nodes + parent/child
relationships + placement metadata) from the Augustin et al. 2019
morphology specification (3.0D-7B). It does NOT implement passive cable
equations, HH, or any electrical simulation.

Architectural choice: the soma is represented as a root compartment
carrying the source-backed soma diameter. No length geometry is assigned
to the soma (length is unknown). This is a topology convenience, not a
biological assertion that the soma is a cylindrical cable compartment.

This builder creates a computational topology from the simplified Augustin
morphology specification. It must NOT claim to be a full 3D reconstruction
or connectome-derived morphology.
"""

from typing import Dict

from .morphology import (
    CableParameters,
    Compartment,
    CompartmentGeometry,
    CompartmentModel,
    CompartmentProvenance,
    CompartmentState,
    PlacementRecord,
)
from .gfs_morphology import (
    CompartmentSpec,
    GFSMorphology,
    NeuronSpec,
    PlacementSpec,
    get_gfs_morphology,
)


def _build_geometry(comp_spec: CompartmentSpec) -> CompartmentGeometry:
    """Transfer geometry values from source-backed CompartmentSpec to CompartmentGeometry.

    Preserves proximal and distal diameters separately (no averaging).
    No values are invented — all remain None where the source does not specify.
    """
    geom = CompartmentGeometry(anatomical_role=comp_spec.name)
    if comp_spec.length is not None:
        geom.length_um = comp_spec.length.value
    if comp_spec.diameter is not None:
        geom.diameter_um = comp_spec.diameter.value
    if comp_spec.diameter_distal is not None:
        geom.diameter_distal_um = comp_spec.diameter_distal.value
    return geom


def _build_provenance(comp_spec: CompartmentSpec) -> CompartmentProvenance:
    """Transfer provenance records from source-backed CompartmentSpec.

    Preserves per-value provenance without relabeling.
    """
    prov = CompartmentProvenance()
    if comp_spec.length is not None:
        prov.length_um = comp_spec.length.provenance
    if comp_spec.diameter is not None:
        prov.diameter_um = comp_spec.diameter.provenance
    if comp_spec.diameter_distal is not None:
        prov.diameter_distal_um = comp_spec.diameter_distal.provenance
    return prov


def _build_placement_record(placement: PlacementSpec) -> PlacementRecord:
    """Convert a source-backed PlacementSpec into a PlacementRecord."""
    return PlacementRecord(
        distance_um=placement.distance.value,
        kind=placement.kind,
        description=placement.description,
        provenance=placement.distance.provenance,
    )


def _match_placements(comp_spec: CompartmentSpec, neuron_spec: NeuronSpec) -> list:
    """Collect placement specs that target this compartment by name."""
    records = []
    for placement in neuron_spec.placements:
        if placement.compartment == comp_spec.name:
            records.append(_build_placement_record(placement))
    return records


def _declare_electrical_exclusions(model: CompartmentModel, soma_id: str) -> None:
    """Declare compartments that are anatomical but not electrically representable.

    The GF soma is reported in the source with a diameter only. Membrane
    capacitance and leak conductance require a membrane SURFACE AREA, and no
    cylindrical soma length is available, so no area can be derived. The soma
    is therefore declared excluded from passive electrical representation.

    This declaration is a COMPUTATIONAL LIMITATION, not a biological claim:
    the soma is real, it is not described as having zero membrane area, and
    no axial, capacitance, or leak value is invented for it. The anatomical
    compartment keeps its diameter and provenance untouched.

    Scope note: only the GF soma is declared here, as scoped for 3.0D-7I. The
    TTMn, PSI, and DLMn somas have the same geometric insufficiency and are
    NOT declared excluded; they continue to be rejected by explicit geometry
    errors rather than being silently omitted. That asymmetry is a known
    open question, not a biological difference between neurons.
    """
    from .electrical_representation import (
        ElectricalRepresentation, insufficient_geometry_exclusion,
    )

    if model.neuron_id != "GF":
        return

    model.electrical_representation = ElectricalRepresentation(
        exclusions=(
            insufficient_geometry_exclusion(
                soma_id,
                "GF soma has a source-backed diameter (8 um) but no "
                "source-backed length, so no membrane surface area can be "
                "computed. A diameter alone is NOT converted into an area, and "
                "no soma length is invented.",
            ),
        )
    )


def build_compartment_model(neuron_spec: NeuronSpec) -> CompartmentModel:
    """Construct a CompartmentModel from a source-backed NeuronSpec.

    Topological structure:
    - A soma compartment is created as the root (carrying the source-backed
      soma diameter) — see "Architectural choice" below.
    - Each CompartmentSpec becomes a child compartment of the soma.

    Architectural choice: the soma compartment carries diameter but no
    length geometry (unknown). This is a topology convenience, not a
    biological assertion that the soma is a cylindrical cable compartment.

    No cable parameters, coordinates, branch angles, or intermediate
    segment lengths are invented.
    """
    model = CompartmentModel(neuron_id=neuron_spec.neuron_type)

    soma_id = f"{neuron_spec.neuron_type}_soma"

    # Create soma as root compartment
    soma = Compartment(
        compartment_id=soma_id,
        geometry=CompartmentGeometry(anatomical_role="soma"),
    )
    if neuron_spec.soma_diameter is not None:
        soma.geometry.diameter_um = neuron_spec.soma_diameter.value
        soma.provenance.diameter_um = neuron_spec.soma_diameter.provenance
    model.add_compartment(soma)

    # Create child compartments from specs
    for comp_spec in neuron_spec.compartments:
        comp = Compartment(
            compartment_id=f"{neuron_spec.neuron_type}_{comp_spec.name}",
            parent_id=soma_id,
            geometry=_build_geometry(comp_spec),
            cable_params=CableParameters(),
            provenance=_build_provenance(comp_spec),
            state=CompartmentState(),
        )
        comp.placements = _match_placements(comp_spec, neuron_spec)
        model.add_compartment(comp)
        if comp.compartment_id not in soma.neighbor_ids:
            soma.neighbor_ids.append(comp.compartment_id)

    _declare_electrical_exclusions(model, soma_id)

    return model


def build_gfs_compartment_models() -> Dict[str, CompartmentModel]:
    """Build CompartmentModel for all four GFS neurons (GF, TTMn, PSI, DLMn).

    Returns a mapping of neuron_type → CompartmentModel.
    """
    gfs = get_gfs_morphology()
    return {
        neuron_type: build_compartment_model(spec)
        for neuron_type, spec in gfs.neurons.items()
    }
