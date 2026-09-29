"""Source-backed GFS morphology specification (3.0D-7B).

Contains only the anatomical values reported in Augustin et al. 2019
(eLife, PMC6469880) Table 1, with explicit provenance for each.
No invented 3D coordinates, branch angles, compartment counts,
cable parameters, membrane areas, or other biological values.

This is a data-layer parameterization for future compartment construction
(3.0D-7C/7D). It is NOT a simulation model.

Provenance classification:
- All Augustin model anatomy values are classified as PUBLISHED_MODEL_PARAMETER
  (the paper states the anatomy is "simplified" and "chosen to capture general
  cell proportions" and "active/passive membrane-area ratios"; some parameters
  were "manually adjusted"). These are NOT DIRECTLY_MEASURED and are not
  individual-neuron reconstructions.
- The 170 μm PSI dendrite length is classified as ESTIMATED (the paper
  explicitly states this value was estimated).
- Boerner & Godenschwege 2010 (PMC2946086) provides anatomical context
  (3D reconstructions, stereotyped contact regions) but no exact geometry
  is imported from that source.

Section diameters (3.0D-7L):
The published simplified model represents each neuron's sections as
unbranched cylinders of a single reported diameter: 8 um for GF, 6 um for
TTMn, 4.5 um for PSI. Those values are attached to each modeled section so
that every modeled section has a complete source-backed geometry for the
passive cable representation. They remain PUBLISHED_MODEL_PARAMETER values
of a simplified model, not per-section anatomical measurements.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .provenance import ParameterProvenance, ProvenanceRecord


_SOURCE_AUGUSTIN = (
    "Augustin et al. 2019 (eLife, PMC6469880) Table 1. "
    "Simplified anatomy chosen to capture general cell proportions and "
    "active/passive membrane-area ratios. Some parameters manually adjusted."
)

_SOURCE_BOERNER = (
    "Boerner & Godenschwege 2010 (PMC2946086). "
    "GF and TTMn morphology reconstructed in 3D and registered to Drosophila "
    "VNC standard. Stereotyped GF→TTMn and GF→PSI contact regions. "
    "Anatomical context only — no exact geometry imported."
)


@dataclass
class MorphologyParameter:
    """A single source-backed morphology value with provenance."""

    value: float
    unit: str
    provenance: ProvenanceRecord


@dataclass
class CompartmentSpec:
    """Geometry specification for a named compartment section.

    Compartment/section names (e.g. "axon", "medial_dendrite") derive
    from the Augustin model descriptions. Only values reported in
    PMC6469880 Table 1 are populated; all others remain None (unknown).

    No invented compartments, coordinates, or cable parameters.
    """

    name: str
    length: Optional[MorphologyParameter] = None
    diameter: Optional[MorphologyParameter] = None
    diameter_distal: Optional[MorphologyParameter] = None


@dataclass
class PlacementSpec:
    """A distance-based placement (contact or input) on a compartment.

    All distances are measured from the compartment's proximal end,
    as reported in Augustin et al. 2019 Table 1.
    """

    compartment: str
    distance: MorphologyParameter
    kind: str
    description: str = ""


@dataclass
class NeuronSpec:
    """Source-backed morphology for one neuron type."""

    neuron_type: str
    soma_diameter: Optional[MorphologyParameter] = None
    compartments: List[CompartmentSpec] = field(default_factory=list)
    placements: List[PlacementSpec] = field(default_factory=list)
    context_sources: List[str] = field(default_factory=list)


@dataclass
class GFSMorphology:
    """Complete GFS morphology specification.

    Contains only values from Augustin et al. 2019 (PMC6469880) Table 1.
    No invented values, no passive cable solver, no HH equations.
    """

    source: str
    neurons: Dict[str, NeuronSpec] = field(default_factory=dict)


def _mk(value: float, provenance_category: ParameterProvenance,
        source: str) -> MorphologyParameter:
    """Create a MorphologyParameter with provenance."""
    return MorphologyParameter(
        value=value,
        unit="um",
        provenance=ProvenanceRecord(provenance_category, source),
    )


def get_gfs_morphology() -> GFSMorphology:
    """Return the source-backed GFS morphology specification.

    All values come from Augustin et al. 2019 (eLife, PMC6469880) Table 1.
    The PSI dendrite length (170 um) is estimated per the source.
    All other anatomy values are published model parameters.
    """
    prov_pub = ParameterProvenance.PUBLISHED_MODEL_PARAMETER
    prov_est = ParameterProvenance.ESTIMATED

    gfs = GFSMorphology(source=_SOURCE_AUGUSTIN)

    # --- GF ---
    gf = NeuronSpec(
        neuron_type="GF",
        soma_diameter=_mk(8.0, prov_pub, _SOURCE_AUGUSTIN),
        context_sources=[_SOURCE_BOERNER],
    )
    gf.compartments.append(CompartmentSpec(
        name="axon",
        length=_mk(400.0, prov_pub, _SOURCE_AUGUSTIN),
        diameter=_mk(8.0, prov_pub, _SOURCE_AUGUSTIN),
    ))
    # GF→PSI contact distance from GF proximal end
    gf.placements.append(PlacementSpec(
        compartment="axon",
        distance=_mk(360.0, prov_pub, _SOURCE_AUGUSTIN),
        kind="contact",
        description="GF→PSI contact distance from GF proximal end",
    ))
    # GF→TTMn contact distance
    gf.placements.append(PlacementSpec(
        compartment="axon",
        distance=_mk(400.0, prov_pub, _SOURCE_AUGUSTIN),
        kind="contact",
        description="GF→TTMn contact distance from GF proximal end",
    ))
    # GF input on medial dendrite
    gf.compartments.append(CompartmentSpec(
        name="medial_dendrite",
    ))
    gf.placements.append(PlacementSpec(
        compartment="medial_dendrite",
        distance=_mk(12.0, prov_pub, _SOURCE_AUGUSTIN),
        kind="input",
        description="GF input location on medial dendrite from proximal end",
    ))
    gfs.neurons["GF"] = gf

    # --- TTMn ---
    ttmn = NeuronSpec(
        neuron_type="TTMn",
        soma_diameter=_mk(6.0, prov_pub, _SOURCE_AUGUSTIN),
        context_sources=[_SOURCE_BOERNER],
    )
    # 3.0D-7L: the published simplified model uses a single 6 um diameter for
    # TTMn. No source-backed length exists for the TTMn soma; none is invented.
    ttmn.compartments.append(CompartmentSpec(
        name="axon",
        length=_mk(50.0, prov_pub, _SOURCE_AUGUSTIN),
        diameter=_mk(6.0, prov_pub, _SOURCE_AUGUSTIN),
    ))
    ttmn.compartments.append(CompartmentSpec(
        name="medial_dendrite",
        length=_mk(60.0, prov_pub, _SOURCE_AUGUSTIN),
        diameter=_mk(6.0, prov_pub, _SOURCE_AUGUSTIN),
    ))
    ttmn.compartments.append(CompartmentSpec(
        name="lateral_dendrite",
        length=_mk(30.0, prov_pub, _SOURCE_AUGUSTIN),
        diameter=_mk(6.0, prov_pub, _SOURCE_AUGUSTIN),
    ))
    gfs.neurons["TTMn"] = ttmn

    # --- PSI ---
    psi = NeuronSpec(
        neuron_type="PSI",
        soma_diameter=_mk(4.5, prov_pub, _SOURCE_AUGUSTIN),
        context_sources=[_SOURCE_BOERNER],
    )
    # 3.0D-7L: the published simplified model uses a single 4.5 um diameter
    # for PSI. No source-backed length exists for the PSI soma; none is invented.
    psi.compartments.append(CompartmentSpec(
        name="axon",
        length=_mk(90.0, prov_pub, _SOURCE_AUGUSTIN),
        diameter=_mk(4.5, prov_pub, _SOURCE_AUGUSTIN),
    ))
    # PSI dendrite length — EXPLICITLY estimated per source.
    # The 4.5 um section diameter is a published model parameter; the length
    # stays ESTIMATED and is not upgraded.
    psi.compartments.append(CompartmentSpec(
        name="dendrite",
        length=_mk(170.0, prov_est, _SOURCE_AUGUSTIN),
        diameter=_mk(4.5, prov_pub, _SOURCE_AUGUSTIN),
    ))
    # GF input on PSI axon
    psi.placements.append(PlacementSpec(
        compartment="axon",
        distance=_mk(45.0, prov_pub, _SOURCE_AUGUSTIN),
        kind="input",
        description="GF input location on PSI axon from proximal end",
    ))
    # PSI→DLMn contact
    psi.placements.append(PlacementSpec(
        compartment="axon",
        distance=_mk(76.5, prov_pub, _SOURCE_AUGUSTIN),
        kind="contact",
        description="PSI→DLMn contact distance from PSI axon proximal end",
    ))
    gfs.neurons["PSI"] = psi

    # --- DLMn ---
    dlmn = NeuronSpec(
        neuron_type="DLMn",
        soma_diameter=_mk(2.0, prov_pub, _SOURCE_AUGUSTIN),
    )
    # DLMn dendrite and axon proximal diameter
    dlmn.compartments.append(CompartmentSpec(
        name="dendrite",
        length=_mk(100.0, prov_pub, _SOURCE_AUGUSTIN),
        diameter=_mk(2.0, prov_pub, _SOURCE_AUGUSTIN),
    ))
    # DLMn axon (proximal diameter 2.0, distal diameter 4.0)
    dlmn.compartments.append(CompartmentSpec(
        name="axon",
        length=_mk(50.0, prov_pub, _SOURCE_AUGUSTIN),
        diameter=_mk(2.0, prov_pub, _SOURCE_AUGUSTIN),
        diameter_distal=_mk(4.0, prov_pub, _SOURCE_AUGUSTIN),
    ))
    # PSI input on DLMn axon
    dlmn.placements.append(PlacementSpec(
        compartment="axon",
        distance=_mk(12.5, prov_pub, _SOURCE_AUGUSTIN),
        kind="input",
        description="PSI input location on DLMn axon from proximal end",
    ))
    gfs.neurons["DLMn"] = dlmn

    return gfs


def get_morphology_parameter(gfs: GFSMorphology, neuron_type: str,
                             compartment_name: str, attr: str) -> Optional[MorphologyParameter]:
    """Look up a single morphology parameter by neuron type, compartment, and attribute.

    Returns None if the compartment or attribute is not populated.
    """
    neuron = gfs.neurons.get(neuron_type)
    if neuron is None:
        return None
    for comp in neuron.compartments:
        if comp.name == compartment_name:
            return getattr(comp, attr, None)
    return None
