"""Opt-in passive cable backend for compartment models (3.0D-7G).

This is the first component that actually consumes the authorized passive
parameter profile from 3.0D-7F. It implements ONLY passive cable
dynamics for a CompartmentModel:

    C_m dV/dt = -I_leak + sum(I_axial_in) - sum(I_axial_out) + I_injected

    I_leak  = g_leak * (V - E_leak)          (outward positive)
    I_axial = (V_parent - V_child) / R_link  (parent to child)
    C_m     = Cm_specific * A_membrane
    g_leak  = g_density_specific * A_membrane
    R_link  = Ra_specific * L / A_cross_section        (uniform cylinder)
    R_link  = Ra_specific * L / (pi * r1 * r2)         (linearly tapered, 3.0D-7J)

Every electrical quantity is derived from EXPLICITLY represented geometry
and EXPLICITLY authorized passive parameters. Nothing is inferred:

- No membrane area is fabricated. If a compartment lacks the geometry
  needed for a quantity, the backend raises PassiveGeometryError with the
  offending compartment and field.
- No parameter is read straight from the evidence registry. The backend
  resolves values only through an authorized profile, and only for the
  parameters that profile authorizes.
- Compartment.cable_params is NEVER written. Authorized values live in the
  prepared network, not in the morphology data model.

ISOLATION:
- ``passive_cable_v0`` is never the default. The engine default remains
  lif_voltage at dt = 1 ms, unchanged.
- The engine-wide timestep is NOT changed by this module. The backend
  declares its own numerical policy and REJECTS a timestep that violates
  it, including the engine's 1 ms.

ELECTRICAL REPRESENTATION (3.0D-7I):
- Compartments may carry a declared electrical-representation exclusion.
  Excluded compartments stay in the anatomical morphology but do not enter
  the electrical network.
- The electrical topology is derived independently of the anatomical
  topology. Children of an excluded compartment become electrical roots;
  no axial path is invented across the excluded parent. This is a
  limitation of the current representation, NOT a claim that they are
  biologically disconnected.

NOT a full reproduction of Augustin et al. 2019. That model uses four
cells, 1-3 unbranched sections per cell, 51 isopotential segments per
section, and active conductances in active sections. This backend has no
active conductances and does not perform the 51-segment discretization.
"""

from dataclasses import dataclass, field
from math import pi
from typing import Dict, List, Optional, Tuple

from ..dynamics.base import DynamicsModel, NumericalResolution
from ..electrical_representation import ElectricalExclusion, get_exclusions
from ..geometry_metrics import compute_compartment_metrics
from ..morphology import CompartmentModel
from ..neuron import Neuron
from ..passive_profiles import (
    PassiveParameterProfile, get_passive_parameter_profile,
    PROFILE_AUGUSTIN_2019_GFS_PASSIVE,
)
from ..subdivision import (
    SubdivisionPlan, DerivedSegment, derive_segments, map_placements_for_section,
)
from ..provenance import ProvenanceRecord


MODEL_NAME_PASSIVE_CABLE_V0 = "passive_cable_v0"

AUTHORIZED_CM = "specific_membrane_capacitance"
AUTHORIZED_RA = "specific_axial_resistance"
AUTHORIZED_G_LEAK = "leak_conductance_density"
AUTHORIZED_E_LEAK = "leak_reversal_potential"

PASSIVE_CABLE_REQUIRED_PARAMETERS = (
    AUTHORIZED_CM,
    AUTHORIZED_RA,
    AUTHORIZED_G_LEAK,
    AUTHORIZED_E_LEAK,
)

_UM2_TO_CM2 = 1e-8
_UM_TO_CM = 1e-4
_UF_TO_F = 1e-6
_MS_TO_S = 1e-3
_MV_TO_V = 1e-3


class PassiveBackendError(Exception):
    """Base class for passive cable backend failures."""


class PassiveGeometryError(PassiveBackendError):
    """Required geometry is missing; no value is inferred or fabricated."""


class PassiveAuthorizationError(PassiveBackendError):
    """A parameter or profile that is not authorized was requested."""


class PassiveNumericalResolutionError(PassiveBackendError):
    """The requested timestep violates the backend's declared policy."""


class PassiveUnsupportedError(PassiveBackendError, NotImplementedError):
    """Requested functionality is explicitly out of scope for this backend."""


@dataclass(frozen=True)
class PassiveNumericalPolicy:
    """Declared numerical policy for the passive cable backend.

    This is NUMERICAL CONFIGURATION, not a biological timescale. The
    threshold is anchored to a published passive compartment modelling
    example that integrated at a 10 us timestep, and is offered as a
    starting configuration. It is not claimed to be universally correct;
    a caller may use any timestep at or below the maximum and is
    responsible for their own convergence checks.
    """

    max_timestep_ms: float
    default_timestep_ms: float
    integration_method: str
    policy_note: str


PASSIVE_CABLE_NUMERICAL_POLICY = PassiveNumericalPolicy(
    max_timestep_ms=0.01,
    default_timestep_ms=0.01,
    integration_method="explicit_forward_euler",
    policy_note=(
        "Passive cable integration is conditionally stable; forward Euler "
        "requires a timestep small relative to the fastest membrane time "
        "constant. A published passive compartment cable simulation "
        "(PMC3587358) used 100 um segments with a 10 us timestep, which "
        "anchors the 0.01 ms maximum used here as an INITIAL NUMERICAL "
        "CONFIGURATION. This is a numerical approximation choice, NOT an "
        "experimentally established biological timescale and NOT an "
        "established GFS timestep. The engine default of 1 ms is deliberately "
        "REJECTED by this backend: it is validated for lif_voltage, not for "
        "cable dynamics. Callers must run their own convergence checks."
    ),
)

_PASSIVE_RESOLUTION = NumericalResolution(
    timestep_ms=PASSIVE_CABLE_NUMERICAL_POLICY.max_timestep_ms,
    resolution_note=PASSIVE_CABLE_NUMERICAL_POLICY.policy_note,
)


@dataclass(frozen=True)
class CompartmentElectrical:
    """Electrical quantities derived for one compartment (never stored on it)."""

    compartment_id: str
    membrane_area_cm2: float
    capacitance_F: float
    leak_conductance_S: float
    leak_reversal_mV: float
    axial_resistance_ohm: Optional[float]
    membrane_area_derivation: str
    membrane_area_provenance: ProvenanceRecord
    axial_derivation: str
    anatomical_parent_id: Optional[str] = None
    electrical_parent_id: Optional[str] = None
    electrical_root_reason: str = ""
    source_section_id: Optional[str] = None
    segment_index: Optional[int] = None
    segment_count: int = 1
    is_derived_segment: bool = False
    derivation: str = ""
    source_geometry_provenance: Optional[ProvenanceRecord] = None
    subdivision_provenance: Optional[ProvenanceRecord] = None


@dataclass(frozen=True)
class AxialConnection:
    """An axial current path from a parent compartment to a child."""

    parent_id: str
    child_id: str
    resistance_ohm: float
    derivation: str


@dataclass(frozen=True)
class PlacementMapping:
    """Computational mapping of a source placement onto a derived segment.

    The source distance is preserved in ORIGINAL anatomical-section
    coordinates. The mapping is a numerical discretization, not a new
    biological measurement, and the placement record itself is not
    modified.
    """

    source_section_id: str
    distance_um: float
    kind: str
    segment_id: str
    segment_index: int
    segment_count: int
    mapping_note: str


@dataclass(frozen=True)
class PassiveNetwork:
    """A prepared, immutable passive network derived from one CompartmentModel.

    Ordered deterministically: compartments are sorted by compartment_id
    and connections are sorted by (parent_id, child_id), so repeated
    preparation of the same model yields identical ordering.
    """

    model_id: str
    profile_name: str
    profile_limitations: str
    timestep_ms: float
    compartments: Tuple[CompartmentElectrical, ...]
    connections: Tuple[AxialConnection, ...]
    authorized_parameters: Tuple[Tuple[str, float, str], ...]
    excluded: Tuple[ElectricalExclusion, ...] = ()
    placement_mappings: Tuple[PlacementMapping, ...] = ()
    subdivision_plan: Optional["SubdivisionPlan"] = None

    def compartment(self, compartment_id: str) -> CompartmentElectrical:
        for c in self.compartments:
            if c.compartment_id == compartment_id:
                return c
        raise KeyError(
            f"Compartment '{compartment_id}' is not part of prepared "
            f"network '{self.model_id}'"
        )


@dataclass
class PassiveNetworkState:
    """Mutable simulation state for a prepared network.

    Kept separate from the immutable network and from the morphology data
    model so that no Compartment electrical state is ever written.
    """

    voltages_mV: Dict[str, float] = field(default_factory=dict)


class _SegmentCompartmentProxy:
    """A transient read-only view of one derived segment.

    Exposes exactly the attributes ``compute_compartment_metrics`` reads so
    the existing geometry conventions can be reused verbatim for derived
    segments. The source Compartment and its CompartmentGeometry are never
    written to.
    """

    __slots__ = ("compartment_id", "geometry", "provenance")

    def __init__(self, segment: DerivedSegment, source_provenance) -> None:
        self.compartment_id = segment.segment_id
        self.geometry = segment.geometry
        self.provenance = source_provenance


def leak_current_A(electrical: CompartmentElectrical, voltage_mV: float) -> float:
    """Outward leak current in amperes for a compartment at a given voltage.

    Positive when the compartment is depolarized above the leak reversal
    potential (current leaves the cell); negative when below it.
    """
    return electrical.leak_conductance_S * (voltage_mV - electrical.leak_reversal_mV) * _MV_TO_V


class PassiveCableModel(DynamicsModel):
    """Opt-in passive cable backend. Never a default; isolated from lif_voltage."""

    numerical_resolution = _PASSIVE_RESOLUTION

    def __init__(
        self,
        profile_name: str,
        timestep_ms: Optional[float] = None,
    ) -> None:
        """Build the backend against an explicitly named authorized profile.

        ``profile_name`` is REQUIRED. There is no default profile: the
        caller must name the authorization it wants, and the CompartmentModel
        must independently declare the same profile.
        """
        self._profile: PassiveParameterProfile = get_passive_parameter_profile(profile_name)
        self._timestep_ms = self._validate_timestep(
            PASSIVE_CABLE_NUMERICAL_POLICY.default_timestep_ms
            if timestep_ms is None
            else timestep_ms
        )
        self._quantities = self._resolve_authorized_quantities(self._profile)

    @property
    def name(self) -> str:
        return MODEL_NAME_PASSIVE_CABLE_V0

    @property
    def profile(self) -> PassiveParameterProfile:
        """The authorized profile this backend was built with."""
        return self._profile

    @property
    def profile_name(self) -> str:
        return self._profile.name

    @property
    def timestep_ms(self) -> float:
        return self._timestep_ms

    @property
    def is_default(self) -> bool:
        """Always False. The passive backend is never an engine default."""
        return False

    @property
    def numerical_policy(self) -> PassiveNumericalPolicy:
        return PASSIVE_CABLE_NUMERICAL_POLICY

    def _validate_timestep(self, timestep_ms: float) -> float:
        if timestep_ms <= 0:
            raise PassiveNumericalResolutionError(
                f"timestep_ms must be positive, got {timestep_ms}"
            )
        if timestep_ms > PASSIVE_CABLE_NUMERICAL_POLICY.max_timestep_ms:
            raise PassiveNumericalResolutionError(
                f"timestep_ms={timestep_ms} exceeds the maximum "
                f"{PASSIVE_CABLE_NUMERICAL_POLICY.max_timestep_ms} ms declared by "
                f"{MODEL_NAME_PASSIVE_CABLE_V0}. The engine default of 1 ms is "
                f"validated for lif_voltage and is NOT silently accepted here. "
                f"Policy: {PASSIVE_CABLE_NUMERICAL_POLICY.policy_note}"
            )
        return timestep_ms

    def _resolve_authorized_quantities(
        self, profile: PassiveParameterProfile
    ) -> Dict[str, float]:
        """Resolve only the parameters this profile explicitly authorizes.

        The evidence registry is never consulted directly. A profile that
        does not authorize a required quantity is a hard error.
        """
        resolved: Dict[str, float] = {}
        for name in PASSIVE_CABLE_REQUIRED_PARAMETERS:
            if not profile.is_authorized(name):
                raise PassiveAuthorizationError(
                    f"Profile '{profile.name}' does not authorize required "
                    f"passive parameter '{name}'"
                )
            resolved[name] = profile.get(name).value
        return resolved

    def resolve_parameter(self, name: str) -> float:
        """Return an authorized parameter value by name.

        Anything not authorized by this backend's profile raises, so an
        unauthorized parameter cannot silently enter the solver.
        """
        if name not in PASSIVE_CABLE_REQUIRED_PARAMETERS:
            raise PassiveUnsupportedError(
                f"Parameter '{name}' is not consumed by "
                f"{MODEL_NAME_PASSIVE_CABLE_V0}. This backend integrates "
                f"passive membrane and axial cable dynamics only. Authorized "
                f"parameters: {list(PASSIVE_CABLE_REQUIRED_PARAMETERS)}"
            )
        return self._quantities[name]

    def authorized_parameters(self) -> Tuple[Tuple[str, float, str], ...]:
        """Authorized parameter name/value/unit triples, with provenance retained."""
        return tuple(
            (p.name, p.value, p.unit)
            for p in self._profile.parameters
            if p.name in PASSIVE_CABLE_REQUIRED_PARAMETERS
        )

    def _require_profile_declaration(self, model: CompartmentModel) -> None:
        declared = getattr(model, "passive_profile_name", None)
        if declared is None:
            raise PassiveAuthorizationError(
                f"CompartmentModel '{model.neuron_id}' declares no passive "
                f"profile. The passive backend is opt-in: set "
                f"model.passive_profile_name explicitly (e.g. "
                f"'{PROFILE_AUGUSTIN_2019_GFS_PASSIVE}'). No profile is ever "
                f"selected implicitly."
            )
        if declared != self._profile.name:
            raise PassiveAuthorizationError(
                f"CompartmentModel '{model.neuron_id}' declares passive profile "
                f"'{declared}' but this backend was built with "
                f"'{self._profile.name}'. They must match."
            )

    def prepare(
        self,
        model: CompartmentModel,
        subdivision_plan: Optional[SubdivisionPlan] = None,
    ) -> PassiveNetwork:
        """Derive electrical quantities for the electrically eligible compartments.

        Compartments carrying a declared electrical-representation exclusion
        (3.0D-7I) do not enter the network and receive no capacitance, leak
        conductance, or axial resistance. The electrical topology is derived
        separately from the anatomical topology: a child whose anatomical
        parent is excluded becomes an electrical root and no axial path is
        invented across the excluded parent.

        A ``subdivision_plan`` (3.0D-7K) may split eligible sections into
        derived computational segments. The source CompartmentGeometry is
        never written; derived segment geometry exists only inside the
        prepared network. The default segment count is 1, which reproduces
        the un-subdivided behaviour exactly.

        Raises PassiveGeometryError when a required geometry field is absent
        from an eligible compartment. No geometry is inferred and no value is
        fabricated.
        """
        self._require_profile_declaration(model)
        if not model.compartments:
            raise PassiveGeometryError(
                f"CompartmentModel '{model.neuron_id}' has no compartments"
            )

        cm_specific = self._quantities[AUTHORIZED_CM]
        g_specific = self._quantities[AUTHORIZED_G_LEAK]
        ra_specific = self._quantities[AUTHORIZED_RA]
        e_leak_mV = self._quantities[AUTHORIZED_E_LEAK]

        exclusions = get_exclusions(model)
        excluded_ids = {e.compartment_id for e in exclusions}
        unknown = excluded_ids - set(model.compartments)
        if unknown:
            raise PassiveGeometryError(
                f"Model '{model.neuron_id}' declares electrical exclusions for "
                f"compartments that do not exist: {sorted(unknown)}"
            )

        eligible = [
            cid for cid in sorted(model.compartments) if cid not in excluded_ids
        ]
        if not eligible:
            raise PassiveGeometryError(
                f"Model '{model.neuron_id}' has no electrically representable "
                f"compartments: all are excluded from electrical "
                f"representation."
            )

        # Derive computational segments for every eligible section, in
        # deterministic order. Excluded sections get no segments at all.
        unit_ids_by_section: Dict[str, List[str]] = {}
        all_segments: Dict[str, List[DerivedSegment]] = {}
        for section_id in eligible:
            segments = derive_segments(model.compartments[section_id], subdivision_plan)
            all_segments[section_id] = list(segments)
            unit_ids_by_section[section_id] = [s.segment_id for s in segments]

        prepared: List[CompartmentElectrical] = []
        for section_id in eligible:
            compartment = model.compartments[section_id]
            segments = all_segments[section_id]

            for segment in segments:
                # A derived copy; the source CompartmentGeometry is untouched.
                metrics = compute_compartment_metrics(
                    _SegmentCompartmentProxy(segment, compartment.provenance)
                )

                if metrics.lateral_surface_area_um2 is None:
                    raise PassiveGeometryError(
                        f"Compartment '{segment.segment_id}' of model "
                        f"'{model.neuron_id}' has no computable membrane area. "
                        f"Missing geometry: length_um="
                        f"{segment.geometry.length_um}, diameter_um="
                        f"{segment.geometry.diameter_um}. "
                        f"Membrane capacitance and leak conductance require an "
                        f"explicit membrane area; no area is inferred or "
                        f"fabricated. Geometry detail: {metrics.derivation_note}"
                    )

                anatomical_parent_id = compartment.parent_id
                if anatomical_parent_id not in unit_ids_by_section:
                    electrical_parent_id = None
                elif segment.segment_index == 0:
                    # Segment 0 inherits the section's electrical parent,
                    # which is the distal segment of the parent section.
                    electrical_parent_id = unit_ids_by_section[anatomical_parent_id][-1]
                else:
                    # Segments 1..N-1 form a linear electrical chain.
                    electrical_parent_id = segments[
                        segment.segment_index - 1
                    ].segment_id

                electrical_root_reason = ""
                axial_resistance_ohm = None
                if electrical_parent_id is None:
                    if anatomical_parent_id is None:
                        axial_derivation = "anatomical root: no parent axial path"
                    else:
                        axial_derivation = (
                            f"electrical root: anatomical parent "
                            f"'{anatomical_parent_id}' is declared excluded from "
                            f"electrical representation, so no axial path is "
                            f"invented across it"
                        )
                        electrical_root_reason = (
                            f"anatomical parent '{anatomical_parent_id}' is not "
                            f"electrically represented"
                        )
                else:
                    if segment.geometry.length_um is None:
                        raise PassiveGeometryError(
                            f"Compartment '{segment.segment_id}' has no "
                            f"length_um; axial resistance is undefined."
                        )
                    length_cm = segment.geometry.length_um * _UM_TO_CM
                    d_proximal = segment.geometry.diameter_um
                    d_distal = segment.geometry.diameter_distal_um

                    if d_distal is not None and d_distal != d_proximal:
                        # Linearly tapered circular cable (3.0D-7J).
                        r1_cm = (d_proximal / 2.0) * _UM_TO_CM
                        r2_cm = (d_distal / 2.0) * _UM_TO_CM
                        axial_resistance_ohm = (
                            ra_specific * length_cm / (pi * r1_cm * r2_cm)
                        )
                        axial_derivation = (
                            f"linearly tapered circular cable: "
                            f"R = Ra * L / (pi * r1 * r2) = {ra_specific} ohm*cm * "
                            f"{length_cm} cm / (pi * {r1_cm} cm * {r2_cm} cm), "
                            f"from proximal r1={r1_cm} cm and distal r2={r2_cm} cm"
                        )
                    else:
                        if metrics.cross_sectional_area_um2 is None:
                            raise PassiveGeometryError(
                                f"Compartment '{segment.segment_id}' has no "
                                f"computable cross-sectional area; axial "
                                f"resistance is undefined."
                            )
                        area_cm2 = metrics.cross_sectional_area_um2 * _UM2_TO_CM2
                        axial_resistance_ohm = ra_specific * length_cm / area_cm2
                        axial_derivation = (
                            f"uniform cylinder: R = Ra * L / A = "
                            f"{ra_specific} ohm*cm * {length_cm} cm / "
                            f"{area_cm2} cm2"
                        )

                membrane_area_cm2 = metrics.lateral_surface_area_um2 * _UM2_TO_CM2
                prepared.append(
                    CompartmentElectrical(
                        compartment_id=segment.segment_id,
                        membrane_area_cm2=membrane_area_cm2,
                        capacitance_F=cm_specific * _UF_TO_F * membrane_area_cm2,
                        leak_conductance_S=g_specific * _MS_TO_S * membrane_area_cm2,
                        leak_reversal_mV=e_leak_mV,
                        axial_resistance_ohm=axial_resistance_ohm,
                        membrane_area_derivation=metrics.derivation_note,
                        membrane_area_provenance=metrics.provenance,
                        axial_derivation=axial_derivation,
                        anatomical_parent_id=anatomical_parent_id,
                        electrical_parent_id=electrical_parent_id,
                        electrical_root_reason=electrical_root_reason,
                        source_section_id=segment.source_section_id,
                        segment_index=segment.segment_index,
                        segment_count=segment.segment_count,
                        is_derived_segment=segment.is_derived_segment,
                        derivation=segment.derivation,
                        source_geometry_provenance=segment.source_geometry_provenance,
                        subdivision_provenance=segment.subdivision_provenance,
                    )
                )

        # Derived placement mapping, in source-section coordinates.
        placement_mappings: List[PlacementMapping] = []
        for section_id in eligible:
            segments = all_segments[section_id]
            for placement, segment_id, index in map_placements_for_section(
                model.compartments[section_id], tuple(segments)
            ):
                placement_mappings.append(
                    PlacementMapping(
                        source_section_id=section_id,
                        distance_um=placement.distance_um,
                        kind=placement.kind,
                        segment_id=segment_id,
                        segment_index=index,
                        segment_count=segments[0].segment_count,
                        mapping_note=(
                            f"computational mapping: source placement distance "
                            f"{placement.distance_um} um from the proximal end of "
                            f"section '{section_id}' mapped onto derived segment "
                            f"{index} of {segments[0].segment_count}. The source "
                            f"distance is unchanged and remains in original "
                            f"section coordinates."
                        ),
                    )
                )
        placement_mappings.sort(
            key=lambda p: (p.source_section_id, p.distance_um, p.kind)
        )

        connections: List[AxialConnection] = []
        for compartment in prepared:
            electrical_parent_id = compartment.electrical_parent_id
            if electrical_parent_id is None:
                continue
            if compartment.axial_resistance_ohm is None:
                raise PassiveGeometryError(
                    f"Compartment '{compartment.compartment_id}' has no axial "
                    f"resistance; connection from '{electrical_parent_id}' "
                    f"cannot be represented."
                )
            connections.append(
                AxialConnection(
                    parent_id=electrical_parent_id,
                    child_id=compartment.compartment_id,
                    resistance_ohm=compartment.axial_resistance_ohm,
                    derivation=compartment.axial_derivation,
                )
            )
        connections.sort(key=lambda c: (c.parent_id, c.child_id))

        return PassiveNetwork(
            model_id=model.neuron_id,
            profile_name=self._profile.name,
            profile_limitations=self._profile.limitations,
            timestep_ms=self._timestep_ms,
            compartments=tuple(prepared),
            connections=tuple(connections),
            authorized_parameters=self.authorized_parameters(),
            excluded=tuple(exclusions),
            placement_mappings=tuple(placement_mappings),
            subdivision_plan=subdivision_plan,
        )

    def initial_state(self, model: CompartmentModel) -> PassiveNetworkState:
        """Build an initial state from the compartments' represented voltages.

        Reads CompartmentState.voltage_mV only. Compartments declared as not
        electrically representable receive no state. No electrical state is
        written back onto any Compartment.
        """
        excluded_ids = {e.compartment_id for e in get_exclusions(model)}
        return PassiveNetworkState(
            voltages_mV={
                compartment_id: model.compartments[compartment_id].state.voltage_mV
                for compartment_id in sorted(model.compartments)
                if compartment_id not in excluded_ids
            }
        )

    def step(
        self,
        network: PassiveNetwork,
        state: PassiveNetworkState,
        injected_currents_A: Optional[Dict[str, float]] = None,
        timestep_ms: Optional[float] = None,
    ) -> Dict[str, float]:
        """Advance the passive network by one explicit forward Euler step.

        Returns the per-compartment net current in amperes (outward
        positive) that produced the update, keyed by compartment id.
        """
        dt_ms = self._validate_timestep(
            network.timestep_ms if timestep_ms is None else timestep_ms
        )
        dt_s = dt_ms * 1e-3
        injected = injected_currents_A or {}

        net_current: Dict[str, float] = {}
        for compartment in network.compartments:
            cid = compartment.compartment_id
            net_current[cid] = injected.get(cid, 0.0) - leak_current_A(
                compartment, state.voltages_mV[cid]
            )

        for connection in network.connections:
            delta = (
                state.voltages_mV[connection.parent_id]
                - state.voltages_mV[connection.child_id]
            ) * _MV_TO_V
            current = delta / connection.resistance_ohm
            net_current[connection.child_id] += current
            net_current[connection.parent_id] -= current

        for compartment in network.compartments:
            cid = compartment.compartment_id
            dV_dt = net_current[cid] / compartment.capacitance_F
            state.voltages_mV[cid] += dV_dt * dt_s * 1e3

        return net_current

    def simulate(
        self,
        model: CompartmentModel,
        steps: int,
        injected_currents_A: Optional[Dict[str, float]] = None,
    ) -> Tuple[PassiveNetwork, PassiveNetworkState]:
        """Prepare a model and run a fixed number of passive steps."""
        network = self.prepare(model)
        state = self.initial_state(model)
        for _ in range(steps):
            self.step(network, state, injected_currents_A=injected_currents_A)
        return network, state

    def inject_sensory_current(self, neuron: Neuron, current: float) -> None:
        raise PassiveUnsupportedError(
            "Sensory mV-to-current conversion is not available in the passive "
            "cable backend. No input resistance or membrane area measurement "
            "exists for the modeled neurons, so a sensory voltage step "
            "cannot be converted to a current without inventing biology."
        )

    def receive_synaptic_spike(self, neuron: Neuron, weight: float, sign: int) -> None:
        raise PassiveUnsupportedError(
            "Synaptic integration is not implemented in the passive cable "
            "backend. Existing weight_mV values are LIF calibration artifacts "
            "and are NOT reinterpreted as currents or conductances here. Use "
            "the backend-level step() API with explicit injected currents."
        )

    def receive_electrical_current(self, neuron: Neuron, current: float) -> None:
        raise PassiveUnsupportedError(
            "Gap-junction (electrical synapse) conductance is not authorized "
            "and is not implemented in the passive cable backend."
        )

    def decay_conductances(self, neuron: Neuron) -> None:
        raise PassiveUnsupportedError(
            "No conductances are decayed: the passive cable backend has no "
            "synaptic or active conductance state."
        )

    def integrate(self, neuron: Neuron, input_current: float = 0.0) -> bool:
        raise PassiveUnsupportedError(
            "The passive cable backend integrates a CompartmentModel, not a "
            "single-compartment Neuron. Use prepare() and step() with an "
            "explicit profile and timestep."
        )

    def reset(self, neuron: Neuron) -> None:
        raise PassiveUnsupportedError(
            "The passive cable backend has no single-compartment reset. "
            "Discard the PassiveNetworkState to reset a simulation."
        )
