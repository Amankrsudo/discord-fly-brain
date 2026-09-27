"""Passive electrical parameter evidence registry (3.0D-7E).

Records candidate passive electrical parameters from the literature
with their evidence status and provenance, as an explicit boundary
before any parameter is assigned to CableParameters.

This registry does NOT assign parameters to any Compartment or
CableParameters. It is a documentation and provenance boundary
that makes it possible for a future step (3.0D-7F/7G) to explicitly
choose which parameters, if any, are authorized for simulation and why.

Critical distinctions maintained:
- Whole-cell input resistance (50–100 MΩ) is a physiological observation,
  NOT convertible to specific membrane resistance.
- Augustin model parameters (Cm, Ri, g_leak, E_leak, g_gap) are
  PUBLISHED_MODEL_PARAMETER / ESTIMATED, NOT direct measurements.
- Leak reversal (-85 mV) is from Günay et al., NOT a direct GFS measurement.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .provenance import ParameterProvenance, ProvenanceRecord


_SOURCE_AUGUSTIN = (
    "Augustin et al. 2019 (eLife, PMC6469880) Table 1. "
    "Simplified anatomy chosen to capture general cell proportions and "
    "active/passive membrane-area ratios. Some parameters manually adjusted."
)

_SOURCE_GUNAY = (
    "Günay et al. 2015 Drosophila motoneuron model, cited in Augustin et al. "
    "2019 (PMC6469880 Table 1). Borrowed into the GFS model."
)

_SOURCE_GF_INPUT_RESISTANCE = (
    "Jensen et al. 2015 (JEB, DOI:10.1242/jeb.116964). "
    "Whole-cell input resistance of GF, reported as 50–100 MOhm. "
    "Whole-cell physiological measurement, NOT a specific membrane resistance."
)

_SOURCE_GFS_ELECTROPHYS = (
    "GFS electrophysiology: Hoyle et al. 2003 (PMC3182647); "
    "Buonomano & Levitt 2005 (PMC2946074). "
    "Functional latency/reliability observations, not complete Ri/Rm/Cm parameter sets."
)

_INELIGIBLE_NOTE = (
    "Registered for provenance/documentation only. "
    "Must NOT be assigned to CableParameters without explicit future authorization. "
    "Augustin model parameters are ESTIMATED/PUBLISHED_MODEL_PARAMETER and not "
    "direct GFS measurements; not eligible for direct simulator use."
)


@dataclass
class PassiveParameterEntry:
    """A candidate passive electrical parameter with evidence and provenance."""

    name: str
    value: float
    unit: str
    provenance_category: ParameterProvenance
    source: str
    eligible_for_simulator: bool = False
    notes: str = ""
    value_min: Optional[float] = None
    value_max: Optional[float] = None


@dataclass
class PassiveElectricalRegistry:
    """Evidence registry for candidate passive electrical parameters.

    This is a provenance boundary, NOT an assignment mechanism.
    Parameters are registered with their evidence status but are NOT
    assigned to CableParameters on any Compartment.

    A future step (3.0D-7F/7G) may explicitly authorize specific parameters
    for simulation, documenting why and how each is defensible.
    """

    source: str
    parameters: List[PassiveParameterEntry] = field(default_factory=list)

    def get(self, name: str) -> PassiveParameterEntry:
        for p in self.parameters:
            if p.name == name:
                return p
        raise KeyError(f"Parameter '{name}' not in registry")

    def names(self) -> List[str]:
        return [p.name for p in self.parameters]


def get_passive_electrical_registry() -> PassiveElectricalRegistry:
    """Return the passive electrical parameter evidence registry.

    All parameters are registered with provenance but are NOT eligible
    for direct simulator use. They must be explicitly authorized by a
    future modeling step (3.0D-7F/7G).
    """
    EST = ParameterProvenance.ESTIMATED
    PUB = ParameterProvenance.PUBLISHED_MODEL_PARAMETER
    EXP = ParameterProvenance.EXPERIMENTALLY_CONSTRAINED

    registry = PassiveElectricalRegistry(
        source=(
            "Evidence registry for passive electrical parameters. "
            "ALL values are registered for provenance/documentation only. "
            "NONE are eligible for direct simulator assignment."
        ),
    )

    # 1. Specific membrane capacitance
    registry.parameters.append(PassiveParameterEntry(
        name="specific_membrane_capacitance",
        value=1.0,
        unit="uF/cm2",
        provenance_category=EST,
        source=_SOURCE_AUGUSTIN,
        eligible_for_simulator=False,
        notes=_INELIGIBLE_NOTE,
    ))

    # 2. Specific axial resistance
    registry.parameters.append(PassiveParameterEntry(
        name="specific_axial_resistance",
        value=35.4,
        unit="ohm*cm",
        provenance_category=EST,
        source=_SOURCE_AUGUSTIN,
        eligible_for_simulator=False,
        notes=_INELIGIBLE_NOTE,
    ))

    # 3. Leak conductance density
    registry.parameters.append(PassiveParameterEntry(
        name="leak_conductance_density",
        value=0.03,
        unit="mS/cm2",
        provenance_category=EST,
        source=_SOURCE_AUGUSTIN,
        eligible_for_simulator=False,
        notes=_INELIGIBLE_NOTE,
    ))

    # 4. Leak reversal potential (from Günay et al., NOT direct GFS measurement)
    registry.parameters.append(PassiveParameterEntry(
        name="leak_reversal_potential",
        value=-85.0,
        unit="mV",
        provenance_category=PUB,
        source=_SOURCE_GUNAY,
        eligible_for_simulator=False,
        notes=(
            "From Günay et al. 2015 motoneuron model, borrowed into "
            "Augustin GFS model. NOT a direct measurement of GFS neurons. "
            + _INELIGIBLE_NOTE
        ),
    ))

    # 5. Gap junction conductances (young/old)
    registry.parameters.append(PassiveParameterEntry(
        name="gap_junction_conductance_young",
        value=135.0,
        unit="uS",
        provenance_category=EST,
        source=_SOURCE_AUGUSTIN,
        eligible_for_simulator=False,
        notes="Estimated/fitted to model latency. " + _INELIGIBLE_NOTE,
    ))
    registry.parameters.append(PassiveParameterEntry(
        name="gap_junction_conductance_old",
        value=34.5,
        unit="uS",
        provenance_category=EST,
        source=_SOURCE_AUGUSTIN,
        eligible_for_simulator=False,
        notes="Estimated/fitted to model latency. " + _INELIGIBLE_NOTE,
    ))

    # 6. GF input resistance (whole-cell physiological observation, range)
    registry.parameters.append(PassiveParameterEntry(
        name="gf_input_resistance",
        value=75.0,
        unit="MOhm",
        provenance_category=EXP,
        source=_SOURCE_GF_INPUT_RESISTANCE,
        eligible_for_simulator=False,
        notes=(
            "Whole-cell input resistance, range 50–100 MOhm "
            "(Jensen et al. 2015, JEB). "
            "NOT convertible to specific membrane resistance without "
            "additional assumptions about membrane area and compartment geometry. "
            "Registered as physiological context only. " + _INELIGIBLE_NOTE
        ),
        value_min=50.0,
        value_max=100.0,
    ))

    # 7. GFS electrophysiology context (latency/reliability observations)
    registry.parameters.append(PassiveParameterEntry(
        name="gfs_electrophysiology_reference",
        value=1.0,
        unit="context",
        provenance_category=EXP,
        source=_SOURCE_GFS_ELECTROPHYS,
        eligible_for_simulator=False,
        notes=(
            "Functional latency (GF→TTM 0.7–1.2 ms, GF→DLM 1.3–1.7 ms) and "
            "100 Hz following limits. NOT a complete neuron-specific "
            "Ri/Rm/Cm parameter set. " + _INELIGIBLE_NOTE
        ),
    ))

    return registry
