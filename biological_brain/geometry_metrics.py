"""Geometry-derived compartment metrics (3.0D-7D).

Computes purely geometric quantities from explicitly supplied compartment
geometry. NO electrical parameters (Ri, Rm, Cm, leak, reversal) are
assigned — those require specific membrane properties not part of this
architecture step.

Formulas:
- Cross-sectional area (circle): A = π * d² / 4
- Cylinder lateral surface area: A_lat = π * d * L
- Cylinder volume: V = (π * d² * L) / 4
- Frustum lateral surface area: A_lat = π * (r1 + r2) * slant
  where r1 = d1/2, r2 = d2/2, slant = √((r1-r2)² + L²)
- Frustum volume: V = (π * L / 3) * (r1² + r2² + r1*r2)

The frustum formulas reduce to cylinder formulas when d1 = d2. This
is an exact geometric convention for conical frusta, not a biological
approximation.

Provenance:
- Derived metrics carry category UNKNOWN with a source string identifying
  the parent geometry fields, preserving the original classifications
  (PUBLISHED_MODEL_PARAMETER, ESTIMATED) intact on the source geometry.
- A derivation_note records the formula used.
"""

from dataclasses import dataclass, field
from math import pi, sqrt
from typing import Dict, Optional

from .morphology import CableParameters, Compartment, CompartmentModel
from .provenance import ParameterProvenance, ProvenanceRecord


@dataclass
class CompartmentMetrics:
    """Geometry-derived metrics for a compartment (no electrical parameters).

    All quantities are DERIVED from the compartment's geometry using
    documented geometric conventions. They are not biological measurements.

    For non-tapered sections (single diameter), cylinder formulas apply.
    For tapered sections (proximal + distal diameter), frustum-of-a-cone
    formulas apply. When d1 = d2, the frustum formulas reduce to the
    cylinder formulas.

    Quantities that cannot be computed (missing geometry) remain None.
    """
    compartment_id: str
    cross_sectional_area_um2: Optional[float] = None
    lateral_surface_area_um2: Optional[float] = None
    volume_um3: Optional[float] = None
    proximal_cross_sectional_area_um2: Optional[float] = None
    distal_cross_sectional_area_um2: Optional[float] = None
    is_tapered: bool = False
    derivation_note: str = ""
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(ParameterProvenance.UNKNOWN, "")
    )


def compute_compartment_metrics(compartment: Compartment) -> CompartmentMetrics:
    """Compute geometry-derived metrics from a compartment's geometry.

    Does NOT assign any electrical parameters (Ri, Rm, Cm, leak, etc.).
    CableParameters on the compartment is returned unchanged.

    Missing geometry:
    - diameter_um=None → all area/volume metrics None
    - length_um=None → only cross-sectional area (no lateral surface area or volume)
    - diameter_distal_um=None → treated as cylindrical (non-tapered)
    """
    geom = compartment.geometry
    prov = compartment.provenance

    metrics = CompartmentMetrics(compartment_id=compartment.compartment_id)

    d1 = geom.diameter_um
    d2 = geom.diameter_distal_um
    length = geom.length_um

    # No diameter → cannot compute any geometric metric
    if d1 is None:
        metrics.derivation_note = (
            f"Cannot derive metrics: diameter_um is None. "
            f"(length_um={length})"
        )
        metrics.provenance = ProvenanceRecord(
            ParameterProvenance.UNKNOWN,
            f"Source geometry incomplete: diameter_um=None",
        )
        return metrics

    # Determine if this is a tapered section
    is_tapered = d2 is not None and d1 != d2
    metrics.is_tapered = is_tapered

    # Build source provenance reference
    source_parts = [f"diameter_um({prov.diameter_um.category.value})"]
    if d2 is not None:
        source_parts.append(f"diameter_distal_um({prov.diameter_distal_um.category.value})")
    if length is not None:
        source_parts.append(f"length_um({prov.length_um.category.value})")
    metrics.provenance = ProvenanceRecord(
        ParameterProvenance.UNKNOWN,
        f"Derived from {', '.join(source_parts)}",
    )

    # Cross-sectional area (exact circle from diameter)
    if is_tapered:
        metrics.proximal_cross_sectional_area_um2 = pi * d1 ** 2 / 4
        metrics.distal_cross_sectional_area_um2 = pi * d2 ** 2 / 4
    else:
        metrics.cross_sectional_area_um2 = pi * d1 ** 2 / 4

    # Lateral surface area and volume (require length)
    if length is None:
        if is_tapered:
            metrics.derivation_note = (
                f"Tapered frustum: d1={d1} um, d2={d2} um. "
                f"Lateral surface area and volume cannot be computed without length. "
                f"Derived from {', '.join(source_parts)}"
            )
        else:
            metrics.derivation_note = (
                f"Cross-sectional area only: d={d1} um. "
                f"Lateral surface area and volume cannot be computed without length. "
                f"Derived from {', '.join(source_parts)}"
            )
        return metrics

    if is_tapered:
        # Frustum of a cone — exact geometric formula
        r1 = d1 / 2
        r2 = d2 / 2
        slant = sqrt((r1 - r2) ** 2 + length ** 2)
        metrics.lateral_surface_area_um2 = pi * (r1 + r2) * slant
        metrics.volume_um3 = (pi * length / 3) * (r1 ** 2 + r2 ** 2 + r1 * r2)
        metrics.derivation_note = (
            f"Frustum of a cone: d1={d1} um, d2={d2} um, L={length} um. "
            f"Derived from {', '.join(source_parts)}"
        )
    else:
        # Cylinder — exact geometric formula
        metrics.lateral_surface_area_um2 = pi * d1 * length
        metrics.volume_um3 = pi * d1 ** 2 * length / 4
        metrics.derivation_note = (
            f"Cylinder: d={d1} um, L={length} um. "
            f"Derived from {', '.join(source_parts)}"
        )

    return metrics


def compute_all_metrics(model: CompartmentModel) -> Dict[str, CompartmentMetrics]:
    """Compute geometry-derived metrics for all compartments in a model."""
    return {
        comp_id: compute_compartment_metrics(comp)
        for comp_id, comp in model.compartments.items()
    }


def assert_no_electrical_parameters(compartment: Compartment) -> None:
    """Verify that CableParameters remain unassigned (all None).

    Raises AssertionError if any electrical parameter was populated.
    This is a sanity check that geometry metrics do not introduce
    electrical parameters.
    """
    cp = compartment.cable_params
    assert cp.axial_resistance_ohm_cm is None
    assert cp.membrane_capacitance_uf_per_cm2 is None
    assert cp.leak_conductance_ms_per_cm2 is None
    assert cp.leak_reversal_mV is None
