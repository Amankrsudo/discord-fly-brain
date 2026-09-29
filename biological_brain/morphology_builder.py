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
from .computational_topology import (
    AUGUSTIN_2019_GFS_COMPUTATIONAL_TOPOLOGY,
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


# Sections the Augustin 2019 simplified computational abstraction does not
# model, even though the anatomical/context morphology retains them (3.0D-7N).
# The published model represents the GF as a single modeled section, so its
# medial dendrite is outside the selected computational scope. This is NOT a
# generic "medial dendrite" rule: TTMn's medial dendrite IS modeled by the
# published abstraction (6 um, 60 um) and must remain representable.
_AUGUSTIN_UNMODELLED_SECTIONS = {
    "GF": ("GF_medial_dendrite",),
}


def _declare_electrical_exclusions(model: CompartmentModel, soma_id: str) -> None:
    """Declare compartments that are anatomical but not electrically representable.

    Every GFS soma is reported in the source with a diameter only. Membrane
    capacitance and leak conductance require a membrane SURFACE AREA, and no
    cylindrical soma length is available, so no area can be derived. Each soma
    is therefore declared excluded from passive electrical representation.

    This declaration is a COMPUTATIONAL LIMITATION, not a biological claim:
    the soma is real, it is NOT described as having zero membrane area or as
    having no electrical role, and no axial, capacitance, or leak value is
    invented for it. The anatomical compartment keeps its diameter and
    provenance untouched.

    3.0D-7L: this declaration is applied uniformly to all four GFS somata.
    The GF-only asymmetry introduced in 3.0D-7I was a scoping artifact, not a
    biological difference between neurons: TTMn, PSI, and DLMn have exactly the
    same geometric insufficiency as GF (a source-backed diameter with no
    source-backed length).

    3.0D-7N: GF_medial_dendrite is additionally declared excluded from the
    SELECTED COMPUTATIONAL REPRESENTATION, for a different and separately
    recorded reason. That section exists in the anatomical/context morphology
    and carries a source-backed input placement, but the Augustin 2019
    simplified model represents the GF as a single modeled section and
    specifies no separate computational geometry for it. The exclusion is a
    statement about the scope of the selected computational abstraction; it is
    NOT a claim that the biological GF lacks a medial dendrite, and the
    compartment is retained untouched in the morphology.
    """
    from .electrical_representation import (
        ElectricalRepresentation,
        computational_scope_exclusion,
        insufficient_geometry_exclusion,
    )

    soma_diameter = model.compartments[soma_id].geometry.diameter_um

    exclusions = [
        insufficient_geometry_exclusion(
            soma_id,
            f"{model.neuron_id} soma has a source-backed diameter "
            f"({soma_diameter} um) but no source-backed length, so no "
            f"membrane surface area can be computed. A diameter alone is "
            f"NOT converted into an area, and no soma length is invented. "
            f"This is a computational limitation of the published "
            f"simplified section model, NOT a claim that the biological "
            f"soma has no electrical role.",
        )
    ]

    medial_dendrite_ids = _AUGUSTIN_UNMODELLED_SECTIONS.get(model.neuron_id, ())
    for medial_dendrite_id in medial_dendrite_ids:
        if medial_dendrite_id not in model.compartments:
            continue
        exclusions.append(
            computational_scope_exclusion(
                medial_dendrite_id,
                "The Augustin 2019 simplified computational model represents "
                "the GF as a single modeled section and does not specify "
                "separate computational geometry for the GF medial dendrite. "
                "This compartment is therefore excluded from the selected "
                "Augustin-style computational representation. It is retained "
                "in the anatomical/context morphology with its source-backed "
                "input placement and provenance untouched, and no length or "
                "diameter is invented for it.",
            )
        )

    model.electrical_representation = ElectricalRepresentation(
        exclusions=tuple(exclusions)
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

    # 3.0D-7P: declare the source-backed computational section connectivity of
    # the selected Augustin 2019 abstraction. This is recorded SEPARATELY from
    # the anatomical parent_id/neighbor_ids above, which are left untouched. It
    # exists because the published abstraction wires the modelled sections
    # directly with child.connect(parent, 0, 0), while our anatomical topology
    # routes every section through a soma that the electrical representation
    # excludes. No connection is invented across a soma.
    model.computational_topology = AUGUSTIN_2019_GFS_COMPUTATIONAL_TOPOLOGY

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
