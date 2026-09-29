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

TIME INTEGRATION (3.0D-7R):
- The declared integration method is explicit and never implicit. The
  default remains the existing explicit forward Euler step, unchanged.
- An implicit backward Euler path is OPT-IN via
  ``PassiveCableModel(..., numerical_method="backward_euler")``. It solves
  A V^{n+1} = b with A assembled from the ACTUAL network connections, so no
  tridiagonal cable structure is assumed and the network is never required
  to stay a tree.
- Backward Euler permits stable passive integration at the existing 0.01 ms
  numerical policy timestep even where explicit Euler violates its spatial
  stability bound. This is a NUMERICAL statement, not a biological claim:
  stability is not accuracy, backward Euler is first-order accurate in time,
  and no biological parameter, timescale or mechanism is introduced.
- The numerical method carries numerical-method provenance only. It is never
  recorded as a biological property of any modelled structure.

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
from enum import Enum
from math import pi
from typing import Dict, List, Optional, Tuple

from ..dynamics.base import DynamicsModel, NumericalResolution
from ..computational_topology import (
    ComputationalTopology,
    get_computational_topology,
)
from ..electrical_representation import (
    ElectricalExclusion,
    GeometryBlocker,
    get_exclusions,
    get_geometry_blockers,
)
from ..geometry_metrics import compute_compartment_metrics
from ..morphology import CompartmentModel
from ..neuron import Neuron
from ..passive_profiles import (
    AuthorizedPassiveParameter, PassiveParameterProfile,
    get_passive_parameter_profile, available_passive_profiles,
    PROFILE_AUGUSTIN_2019_GFS_PASSIVE,
)
from ..subdivision import (
    SubdivisionPlan, DerivedSegment, derive_segments, map_placements_for_section,
)
from ..provenance import ParameterProvenance, ProvenanceRecord


MODEL_NAME_PASSIVE_CABLE_V0 = "passive_cable_v0"

AUTHORIZED_CM = "specific_membrane_capacitance"
AUTHORIZED_RA = "specific_axial_resistance"
AUTHORIZED_G_LEAK = "leak_conductance_density"
AUTHORIZED_E_LEAK = "leak_reversal_potential"

# 3.0D-7O unit contract.
#
# Internal computation is SI: capacitance F, conductance S, resistance ohm,
# current A, time s. The public voltage API stays mV. The canonical unit of
# specific axial resistivity is ohm*cm (ohm.cm) and MUST NOT be confused with
# the printed "ohm/cm" notation, which is a different physical quantity.
# Per-compartment R_axial is a resistance (ohm), not a resistivity, and is
# derived from geometry and Ra; it is never stored on the morphology.
CANONICAL_AXIAL_RESISTIVITY_UNIT = "ohm*cm"
FORBIDDEN_AXIAL_RESISTIVITY_UNITS = ("ohm/cm", "ohm/cm2", "1/ohm*cm")

# 3.0D-7Q numerical representability ceiling for a single section length.
#
# This is a NUMERICAL limit of the electrical representation. It is NOT a
# biological limit, NOT an anatomical claim, and NOT derived from any
# published reconstruction. It exists so that non-representable input fails
# loudly instead of producing a degenerate electrical network.
#
# The ceiling is roughly 2.5e6 times the largest source-backed GFS section
# length (400 um, GF_axon), so it constrains no source-backed geometry. A
# length is never clamped, rescaled, or fabricated to fit it.
MAX_SUBDIVISIBLE_SECTION_LENGTH_UM = 1.0e9

PASSIVE_PARAMETER_CANONICAL_UNITS = {
    AUTHORIZED_CM: "uF/cm2",
    AUTHORIZED_RA: CANONICAL_AXIAL_RESISTIVITY_UNIT,
    AUTHORIZED_G_LEAK: "mS/cm2",
    AUTHORIZED_E_LEAK: "mV",
}

_DERIVED_SI_UNIT_CONVENTIONS = (
    "Derived electrical quantities are computed and stored in SI units: "
    "capacitance in F, conductance in S, axial resistance in ohm, current in A, "
    "time in s. The public voltage API remains mV (V is used only inside the "
    "leak-current conversion). Specific membrane capacitance is uF/cm2, leak "
    "conductance density is mS/cm2, and specific axial resistivity is the "
    "canonical ohm*cm (ohm.cm) and is NEVER treated as the printed 'ohm/cm' "
    "notation, which denotes a different quantity. A per-compartment axial "
    "resistance (ohm) is DERIVED from Ra and geometry; Ra itself is a "
    "resistivity in ohm*cm and is never stored as a resistance."
)

_DERIVED_SCOPE_NOTE = (
    "3.0D-7O establishes the bridge from a source-authorized passive profile "
    "to geometry-derived compartment electrical parameters and a passive "
    "network representation, and nothing more. It does NOT establish biological "
    "validation, correct GFS latency, Hodgkin-Huxley excitability, synaptic "
    "transmission, gap-junction behaviour, or sensory transformation. The "
    "specific source parameters remain published-model/estimated values; the "
    "derived C, g_leak and R values are NOT biological measurements and carry "
    "provenance UNKNOWN by construction."
)


def _derived_provenance(derivation: str) -> ProvenanceRecord:
    """Provenance for a geometry-derived electrical quantity.

    Always UNKNOWN: a derived C/g/R is not a source-reported biological value.
    The specific source parameters keep their own 7F provenance on the profile
    and are referenced by name from the AppliedParameter record.
    """
    return ProvenanceRecord(ParameterProvenance.UNKNOWN, derivation)

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


class PassiveNumericalMethodError(PassiveNumericalResolutionError):
    """The requested numerical integration method is unknown or unsupported."""


class PassiveNumericalMethod(Enum):
    """Declared numerical integration methods for the passive cable backend.

    This is a NUMERICAL-METHOD choice, not a biological choice. It is always
    explicit: the backend keeps the existing explicit forward Euler method as
    the default and the implicit backward Euler method is opt-in, so no
    biological behaviour can depend on a hidden numerical choice.
    """

    FORWARD_EULER = "forward_euler"
    BACKWARD_EULER = "backward_euler"

    @classmethod
    def from_name(cls, name) -> "PassiveNumericalMethod":
        """Resolve a method from a name, rejecting anything unknown clearly.

        Never guesses and never falls back to a default: an unrecognised name
        is an error, because silently substituting an integration method would
        make the numerical behaviour of a simulation undeclared.
        """
        if isinstance(name, cls):
            return name
        if isinstance(name, str):
            for method in cls:
                if name == method.value or name.lower() == method.name.lower():
                    return method
        raise PassiveNumericalMethodError(
            f"Unknown passive numerical integration method {name!r}. No "
            f"method is ever selected implicitly. Available methods: "
            f"{[m.value for m in cls]}. Pass a PassiveNumericalMethod or one "
            f"of those names to PassiveCableModel(numerical_method=...)."
        )


BACKWARD_EULER_BASIS = "standard implicit integration of passive cable equations"

BACKWARD_EULER_SOURCE = (
    "NEURON numerical methodology / Hines & Carnevale. NEURON's published "
    "numerical documentation "
    "(https://www.neuron.yale.edu/neuron/static/papers/nc97/nc3p3.htm) states "
    "that the cable equation can be solved using implicit backward Euler and "
    "that backward Euler has no timestep stability constraint for the passive "
    "linear cable system. NEURON's standard documentation "
    "(https://www.neuron.yale.edu/neuron/static/docs/help/neuron/neuron/nrnoc.html) "
    "records implicit Euler as the default, robustly stable integrator, and "
    "notes that Crank-Nicolson is formally stable but can produce oscillations "
    "for a sufficiently large timestep."
)

BACKWARD_EULER_SCOPE_NOTE = (
    "Backward Euler permits stable passive integration at the existing "
    "0.01 ms numerical policy timestep even when explicit Euler would "
    "violate its spatial stability bound. This is a NUMERICAL statement "
    "about the integrator, NOT a biological claim: stability is not accuracy, "
    "backward Euler remains first-order accurate in time, and the 0.01 ms "
    "timestep remains a project numerical configuration rather than an "
    "established biological timescale. 3.0D-7R establishes numerical "
    "integration infrastructure only: no Hodgkin-Huxley excitability, no "
    "active or synaptic conductance, no gap junction, no sensory "
    "transformation, and no latency reproduction."
)

_NUMERICAL_METHOD_NOTE = (
    "NUMERICAL-METHOD PROVENANCE, NOT BIOLOGICAL PROVENANCE. This record "
    "describes how the passive cable equations are integrated in time. It is "
    "not a source-reported biological property of any modelled structure, it "
    "carries no biological provenance category, and no biological parameter "
    "is derived from it."
)


@dataclass(frozen=True)
class PassiveNumericalMethodRecord:
    """Declared record of the numerical integration method in use.

    ``provenance`` is UNKNOWN by construction: a numerical integrator is not a
    biological measurement, so no biological provenance category applies.
    """

    method: str
    basis: str
    source: str
    provenance: ProvenanceRecord
    note: str

    @property
    def is_biological_provenance(self) -> bool:
        return False



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


def _missing_membrane_geometry_fields(segment) -> str:
    """Name the exact source-backed geometry field(s) a segment is missing.

    Requirement: a geometry rejection must identify the exact missing field
    and the exact section. Nothing is inferred or defaulted here; this only
    reports which required field is absent.
    """
    geometry = segment.geometry
    missing: list = []
    if geometry.length_um is None:
        missing.append("length_um")
    if geometry.diameter_um is None:
        missing.append("diameter_um")
    if geometry.diameter_distal_um is not None and geometry.diameter_um is None:
        missing.append("diameter_um (proximal)")
    if not missing:
        missing.append("none (unclassified geometry shortfall)")
    return ", ".join(missing)


@dataclass(frozen=True)
class AppliedParameter:
    """One electrical parameter derived for a compartment by 3.0D-7O.

    This is the explicit bridge record:

        authorized passive profile
            -> prepared electrical representation
                -> compartment electrical parameter

    Every field records HOW the value was obtained, so a derived quantity is
    never mistaken for a measured biological value. ``provenance`` is
    UNKNOWN by construction: a derived C/g/R is not a source-reported
    biological measurement. The SOURCE specific parameters keep their own 7F
    provenance (ESTIMATED / PUBLISHED_MODEL_PARAMETER) on the profile and are
    referenced here by name through ``source_parameter``.
    """

    name: str
    value: float
    unit: str
    profile_name: str
    source_parameter: Optional[str]
    source_parameter_provenance: Optional[ProvenanceRecord]
    derivation: str
    provenance: ProvenanceRecord
    source_section_id: Optional[str]
    is_geometry_derived: bool

    def __post_init__(self) -> None:
        if self.is_geometry_derived and self.provenance.category != (
            ParameterProvenance.UNKNOWN
        ):
            raise ValueError(
                f"Geometry-derived parameter '{self.name}' must carry "
                f"provenance UNKNOWN, got '{self.provenance.category}'. A "
                f"derived C/g/R is not a source-reported biological value."
            )


@dataclass(frozen=True)
class CompartmentElectrical:
    """Electrical quantities derived for a compartment (never stored on it)."""

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
    profile_name: Optional[str] = None
    applied_parameters: Tuple[AppliedParameter, ...] = ()

    def applied(self, name: str) -> AppliedParameter:
        for parameter in self.applied_parameters:
            if parameter.name == name:
                return parameter
        raise KeyError(
            f"Compartment '{self.compartment_id}' has no applied parameter "
            f"'{name}'. Applied: {[p.name for p in self.applied_parameters]}"
        )


@dataclass(frozen=True)
class AxialConnection:
    """An axial current path from a parent compartment to a child compartment.

    ``computational_source``/``source_model_id``/``direction`` are populated
    when the path comes from a declared computational section connection
    (3.0D-7P) and are empty for a purely anatomical parentage. In both cases
    this is an ordinary axial cable connection: NOT a gap junction and NOT a
    chemical synapse.
    """

    parent_id: str
    child_id: str
    resistance_ohm: float
    derivation: str
    computational_source: str = ""
    source_model_id: str = ""
    source_statement: str = ""
    direction: str = ""
    computational_derivation: str = ""
    computational_provenance: Optional[ProvenanceRecord] = None


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
class PassiveParameterApplication:
    """The declared bridge from an authorized profile to applied parameters.

    Network-level record (3.0D-7O). It states which profile supplied the four
    specific parameters, in which units, under which provenance, and what this
    checkpoint does and does not establish.
    """

    profile_name: str
    model_reproduction_only: bool
    source_parameters: Tuple["AuthorizedPassiveParameter", ...]
    unit_conventions: str
    scope_note: str


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
    parameter_application: Optional[PassiveParameterApplication] = None
    computational_topology: Optional[ComputationalTopology] = None

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


def assemble_backward_euler_matrix(
    network: PassiveNetwork, dt_s: float
) -> List[List[float]]:
    """Assemble A in ``A V^{n+1} = b`` for implicit backward Euler.

    For every electrical compartment i:

        C_i dV_i/dt = -g_i (V_i - E_i) + sum_j (V_j - V_i)/R_ij + I_i

    Backward Euler evaluates the right-hand side at t + dt, which gives

        A_ii = C_i/dt + g_i + sum_j 1/R_ij
        A_ij = -1/R_ij            (for every axial connection i <-> j)
        b_i  = (C_i/dt) V_i^n + g_i E_i + I_i

    All quantities are SI: F, S, ohm, s, A, V.

    The matrix is built from the ACTUAL network connections, so a network is
    never assumed to be a tridiagonal one-compartment cable. Any graph the
    prepared network describes (tree, branch or otherwise) is assembled and
    solved as-is.
    """
    index = {
        c.compartment_id: i for i, c in enumerate(network.compartments)
    }
    size = len(network.compartments)
    matrix = [[0.0] * size for _ in range(size)]

    for i, compartment in enumerate(network.compartments):
        matrix[i][i] = (
            compartment.capacitance_F / dt_s + compartment.leak_conductance_S
        )

    for connection in network.connections:
        conductance = 1.0 / connection.resistance_ohm
        i = index[connection.parent_id]
        j = index[connection.child_id]
        matrix[i][i] += conductance
        matrix[j][j] += conductance
        matrix[i][j] -= conductance
        matrix[j][i] -= conductance

    return matrix


def _lu_factor(matrix: List[List[float]], model_id: str) -> Tuple:
    """LU factorisation with partial pivoting (deterministic, no dependencies)."""
    size = len(matrix)
    lu = [row[:] for row in matrix]
    pivots = list(range(size))
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(lu[r][col]))
        if lu[pivot][col] == 0.0:
            raise PassiveNumericalResolutionError(
                f"The implicit system for network '{model_id}' is singular at "
                f"column {col}: the assembled backward Euler matrix cannot be "
                f"factored. This indicates a degenerate electrical network "
                f"(for example a zero axial resistance), never a silent "
                f"fallback to another integration method."
            )
        if pivot != col:
            lu[col], lu[pivot] = lu[pivot], lu[col]
            pivots[col], pivots[pivot] = pivots[pivot], pivots[col]
        pivot_value = lu[col][col]
        for r in range(col + 1, size):
            factor = lu[r][col] / pivot_value
            lu[r][col] = factor
            if factor:
                for c in range(col + 1, size):
                    lu[r][c] -= factor * lu[col][c]
    return lu, pivots


def _lu_solve(lu: List[List[float]], pivots: List[int], rhs: List[float]) -> List[float]:
    """Solve ``A x = rhs`` from an existing factorisation."""
    size = len(rhs)
    y = [rhs[pivots[i]] for i in range(size)]
    for i in range(1, size):
        total = y[i]
        row = lu[i]
        for j in range(i):
            total -= row[j] * y[j]
        y[i] = total
    x = [0.0] * size
    for i in range(size - 1, -1, -1):
        total = y[i]
        row = lu[i]
        for j in range(i + 1, size):
            total -= row[j] * x[j]
        x[i] = total / row[i]
    return x


@dataclass(frozen=True)
class BackwardEulerOperator:
    """The assembled and factorised implicit operator for one network.

    The operator depends ONLY on the immutable prepared network and the
    timestep, so it carries no simulation state: discarding a
    PassiveNetworkState fully resets the implicit integration path.
    """

    model_id: str
    timestep_ms: float
    compartment_ids: Tuple[str, ...]
    matrix: Tuple[Tuple[float, ...], ...]
    lu: Tuple[Tuple[float, ...], ...]
    pivots: Tuple[int, ...]
    method_provenance: PassiveNumericalMethodRecord
    assembly_note: str

    def solve(self, rhs: List[float]) -> List[float]:
        """Solve ``A V^{n+1} = b`` in volts."""
        return _lu_solve(
            [list(row) for row in self.lu], list(self.pivots), rhs
        )



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
        numerical_method=None,
    ) -> None:
        """Build the backend against an explicitly named authorized profile.

        ``profile_name`` is REQUIRED. There is no default profile: the
        caller must name the authorization it wants, and the CompartmentModel
        must independently declare the same profile.

        ``numerical_method`` is the declared time-integration method
        (3.0D-7R). It is REQUIRED to be explicit when it is not the default:
        the default remains the existing explicit forward Euler method, so no
        existing behaviour changes and no biological behaviour can depend on a
        hidden numerical choice. The implicit backward Euler method is opt-in
        via ``numerical_method="backward_euler"``.
        """
        try:
            self._profile: PassiveParameterProfile = (
                get_passive_parameter_profile(profile_name)
            )
        except KeyError as exc:
            # 3.0D-7O: an unknown or unauthorized profile is rejected clearly
            # and typed, never silently substituted with any other profile.
            raise PassiveAuthorizationError(
                f"Unknown or unauthorized passive parameter profile "
                f"'{profile_name}'. No profile is ever selected implicitly. "
                f"Available authorized profiles: "
                f"{list(available_passive_profiles())}"
            ) from exc
        self._timestep_ms = self._validate_timestep(
            PASSIVE_CABLE_NUMERICAL_POLICY.default_timestep_ms
            if timestep_ms is None
            else timestep_ms
        )
        self._quantities = self._resolve_authorized_quantities(self._profile)
        self._numerical_method = (
            PassiveNumericalMethod.FORWARD_EULER
            if numerical_method is None
            else PassiveNumericalMethod.from_name(numerical_method)
        )
        # Derived purely from an immutable network plus a timestep; never
        # simulation state. Cleared by reset_state().
        self._operator_cache: Dict[tuple, BackwardEulerOperator] = {}

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

    @property
    def numerical_method(self) -> PassiveNumericalMethod:
        """The declared time-integration method for this backend instance."""
        return self._numerical_method

    @property
    def numerical_method_provenance(self) -> PassiveNumericalMethodRecord:
        """Numerical-method record for the selected method.

        Numerical-method provenance only. It states how the passive cable
        equations are integrated in time and is NOT a biological claim, so no
        biological provenance category is attached to it.
        """
        if self._numerical_method is PassiveNumericalMethod.BACKWARD_EULER:
            return PassiveNumericalMethodRecord(
                method=PassiveNumericalMethod.BACKWARD_EULER.value,
                basis=BACKWARD_EULER_BASIS,
                source=BACKWARD_EULER_SOURCE,
                provenance=ProvenanceRecord(
                    ParameterProvenance.UNKNOWN, _NUMERICAL_METHOD_NOTE
                ),
                note=BACKWARD_EULER_SCOPE_NOTE,
            )
        return PassiveNumericalMethodRecord(
            method=PassiveNumericalMethod.FORWARD_EULER.value,
            basis="explicit forward Euler integration of passive cable equations",
            source=(
                "Explicit numerical method retained unchanged from 3.0D-7G. It "
                "is conditionally stable and requires a timestep small "
                "relative to the fastest spatial-discretization time constant "
                "of the prepared network, which the 7Q validation showed is "
                "violated for sufficiently subdivided passive cables at the "
                "0.01 ms policy timestep."
            ),
            provenance=ProvenanceRecord(
                ParameterProvenance.UNKNOWN, _NUMERICAL_METHOD_NOTE
            ),
            note=(
                "The explicit method remains the default and is never "
                "silently replaced. Its conditional stability is a numerical "
                "property, not a biological claim."
            ),
        )

    def clear_numerical_cache(self) -> None:
        """Drop every assembled implicit operator.

        Called by reset_state(). The cache holds no simulation state: each
        entry is a pure function of an immutable prepared network and a
        timestep.
        """
        self._operator_cache.clear()

    @property
    def numerical_cache_size(self) -> int:
        """How many implicit operators are currently assembled and cached.

        Exposed so that "no hidden state survives reset" is observable rather
        than asserted. The cache holds no voltage or current state: every
        entry is a pure function of an immutable prepared network and a
        timestep.
        """
        return len(self._operator_cache)

    def backward_euler_operator(
        self,
        network: PassiveNetwork,
        timestep_ms: Optional[float] = None,
    ) -> BackwardEulerOperator:
        """Assemble and factorise the implicit operator for ``network``.

        The matrix is built from the actual network connections and cached
        per (network content, timestep), so repeated steps at one timestep do
        not refactorise an identical matrix. The cache is cleared by
        ``reset_state()`` and holds no voltage or current state.
        """
        if self._numerical_method is not PassiveNumericalMethod.BACKWARD_EULER:
            raise PassiveNumericalMethodError(
                f"backward_euler_operator() requires the backward Euler "
                f"method, but this backend declares "
                f"'{self._numerical_method.value}'. The explicit method is "
                f"never silently switched to an implicit one; construct the "
                f"backend with numerical_method='backward_euler'."
            )
        dt_ms = self._validate_timestep(
            network.timestep_ms if timestep_ms is None else timestep_ms
        )
        key = (
            network.model_id,
            network.profile_name,
            dt_ms,
            tuple(
                (
                    c.compartment_id, c.capacitance_F, c.leak_conductance_S,
                    c.leak_reversal_mV,
                )
                for c in network.compartments
            ),
            tuple(
                (c.parent_id, c.child_id, c.resistance_ohm)
                for c in network.connections
            ),
        )
        cached = self._operator_cache.get(key)
        if cached is not None:
            return cached

        dt_s = dt_ms * 1e-3
        matrix = assemble_backward_euler_matrix(network, dt_s)
        lu, pivots = _lu_factor(matrix, network.model_id)
        operator = BackwardEulerOperator(
            model_id=network.model_id,
            timestep_ms=dt_ms,
            compartment_ids=tuple(
                c.compartment_id for c in network.compartments
            ),
            matrix=tuple(tuple(row) for row in matrix),
            lu=tuple(tuple(row) for row in lu),
            pivots=tuple(pivots),
            method_provenance=self.numerical_method_provenance,
            assembly_note=(
                f"Implicit backward Euler operator assembled from the actual "
                f"{len(network.connections)} network connection(s) of "
                f"{len(network.compartments)} electrical compartment(s) at "
                f"dt={dt_ms} ms (dt={dt_s} s). A_ii = C_i/dt + g_i + "
                f"sum_j 1/R_ij, A_ij = -1/R_ij, assembled in SI units from the "
                f"immutable prepared network. No tridiagonal cable structure "
                f"is assumed. {BACKWARD_EULER_SCOPE_NOTE}"
            ),
        )
        self._operator_cache[key] = operator
        return operator

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
            parameter = profile.get(name)
            # 3.0D-7O unit guard: the specific axial resistivity must be the
            # canonical ohm*cm. The source prints "ohm/cm", which is a
            # different quantity and must never be silently used.
            forbidden = [
                unit for unit in FORBIDDEN_AXIAL_RESISTIVITY_UNITS
                if unit in parameter.unit.lower()
            ]
            if forbidden:
                raise PassiveAuthorizationError(
                    f"Profile '{profile.name}' parameter '{name}' has "
                    f"non-canonical unit '{parameter.unit}'. Specific axial "
                    f"resistivity is canonically "
                    f"'{CANONICAL_AXIAL_RESISTIVITY_UNIT}' (ohm.cm) and must "
                    f"never be treated as {forbidden}."
                )
            expected_unit = PASSIVE_PARAMETER_CANONICAL_UNITS[name]
            if parameter.unit != expected_unit:
                raise PassiveAuthorizationError(
                    f"Profile '{profile.name}' parameter '{name}' has unit "
                    f"'{parameter.unit}' but the canonical unit is "
                    f"'{expected_unit}'"
                )
            resolved[name] = parameter.value
        return resolved

    def parameter_application(self) -> PassiveParameterApplication:
        """The declared bridge record for this backend's profile (3.0D-7O)."""
        return PassiveParameterApplication(
            profile_name=self._profile.name,
            model_reproduction_only=self._profile.model_reproduction_only,
            source_parameters=tuple(
                self._profile.get(name)
                for name in PASSIVE_CABLE_REQUIRED_PARAMETERS
            ),
            unit_conventions=_DERIVED_SI_UNIT_CONVENTIONS,
            scope_note=_DERIVED_SCOPE_NOTE,
        )

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

    @staticmethod
    def _reject_degenerate_geometry(
        model: CompartmentModel, eligible: List[str]
    ) -> None:
        """Reject geometry that cannot form a well-posed cable (3.0D-7Q).

        Two classes of invalid input are rejected rather than turned into a
        degenerate or inert electrical network:

        1. A non-positive length (the all-zero-length case, and the negative
           length case). A zero-length section has zero membrane area, so it
           has zero capacitance and zero leak conductance, and its axial path
           has zero axial resistance, i.e. infinite axial conductance, which
           makes the network singular. Such a section is never emitted as an
           inert node.
        2. A length that exceeds ``MAX_SUBDIVISIBLE_SECTION_LENGTH_UM`` or is
           not finite. This is a NUMERICAL representability limit, not a
           biological limit and not an anatomical claim.

        A missing length is NOT rejected here: it is handled by the explicit
        source-backed geometry blockers (3.0D-7M) and by the per-segment axial
        resistance check, so that the established blocker messages are
        unchanged. No length is inferred, defaulted, clamped, or fabricated.
        """
        for section_id in eligible:
            length = model.compartments[section_id].geometry.length_um
            if length is None:
                continue
            if length != length or length in (float("inf"), float("-inf")):
                raise PassiveGeometryError(
                    f"Section '{section_id}' of model '{model.neuron_id}' has "
                    f"length_um={length}, which is not a finite length. An "
                    f"electrical cable requires a finite, positive, "
                    f"source-backed length. The length is not inferred, "
                    f"defaulted, or fabricated."
                )
            if length <= 0.0:
                raise PassiveGeometryError(
                    f"Section '{section_id}' of model '{model.neuron_id}' has "
                    f"length_um={length}. A zero-length or negative-length "
                    f"section has no membrane area, therefore no membrane "
                    f"capacitance and no leak conductance, and its axial path "
                    f"has zero axial resistance, i.e. infinite axial "
                    f"conductance, which would make the electrical network "
                    f"singular. Preparation fails instead of emitting a "
                    f"degenerate or inert network. The length is not inferred, "
                    f"defaulted, or fabricated."
                )
            if length > MAX_SUBDIVISIBLE_SECTION_LENGTH_UM:
                raise PassiveGeometryError(
                    f"Section '{section_id}' of model '{model.neuron_id}' has "
                    f"length_um={length}, which exceeds the maximum "
                    f"subdivisible length "
                    f"{MAX_SUBDIVISIBLE_SECTION_LENGTH_UM} um. This is a "
                    f"NUMERICAL representability limit of the electrical "
                    f"representation, not a biological limit and not an "
                    f"anatomical claim. The length is not clamped, rescaled, "
                    f"or fabricated."
                )

    @staticmethod
    def _reject_geometry_blockers(
        model: CompartmentModel,
        subdivision_plan: Optional[SubdivisionPlan],
    ) -> None:
        """Reject a model whose source-backed geometry is incomplete (3.0D-7M).

        Runs before any segmentation, so an explicit subdivision plan cannot
        bypass a blocker: subdivision may split source-backed geometry into
        segments but can never manufacture geometry the source does not give.

        The rejection names the exact section and the exact missing fields, and
        states that this is a computational-representation limitation rather
        than a claim that the biological structure is absent. No value is
        inferred, defaulted, or fabricated.
        """
        blockers: Tuple[GeometryBlocker, ...] = get_geometry_blockers(model)
        if not blockers:
            return

        first = blockers[0]

        planned_note = ""
        if subdivision_plan is not None:
            subdivided = [
                f"'{blocker.section_id}'="
                f"{subdivision_plan.segment_count_for(blocker.section_id)}"
                for blocker in blockers
                if subdivision_plan.segment_count_for(blocker.section_id) > 1
            ]
            if subdivided:
                planned_note = (
                    f" An explicit subdivision plan does NOT bypass this "
                    f"blocker: subdivision can split source-backed geometry "
                    f"into segments but cannot manufacture missing geometry "
                    f"(requested {', '.join(subdivided)})."
                )

        others_note = ""
        if len(blockers) > 1:
            others_note = " Other blocked section(s): " + ", ".join(
                f"'{blocker.section_id}' missing "
                f"{', '.join(blocker.missing_fields)}"
                for blocker in blockers[1:]
            ) + "."

        raise PassiveGeometryError(
            f"Compartment '{first.section_id}' of model '{model.neuron_id}' has "
            f"no computable membrane area. Missing required source-backed "
            f"geometry field(s): {', '.join(first.missing_fields)}. "
            f"Blocker reason: {first.reason} Scope: '{first.scope}' "
            f"(code '{first.reason_code}'). This records INCOMPLETE SOURCE "
            f"EVIDENCE for the current computational representation. It is NOT "
            f"a claim that the biological structure does not exist, NOT a "
            f"claim that it has no geometry in nature, NOT an estimate, and "
            f"NOT permission to substitute geometry from another "
            f"reconstruction. No value is inferred, defaulted, or "
            f"fabricated.{others_note}{planned_note}"
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
        from an eligible compartment, or when a modelled section is blocked by
        incomplete source-backed geometry (3.0D-7M). No geometry is inferred,
        substituted, or fabricated, and a blocked section is never silently
        excluded.
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

        # 3.0D-7Q: reject geometry that cannot form a well-posed cable, before
        # any derivation. A non-positive or non-representable length is invalid
        # input, never a reason to emit a degenerate network.
        self._reject_degenerate_geometry(model, eligible)

        # 3.0D-7M: explicit source-backed geometry blockers. A blocked section
        # is a REAL modelled anatomical section with incomplete source geometry
        # (for example GF_medial_dendrite). It is not excluded, not omitted and
        # not approximated: preparation fails, naming the section and exactly
        # which geometry fields are missing. This check runs BEFORE any
        # segmentation, so a subdivision plan can never manufacture geometry
        # that the source does not provide.
        self._reject_geometry_blockers(model, subdivision_plan)

        # 3.0D-7P: resolve the declared computational section connectivity. Only
        # connections whose BOTH endpoints exist in this model apply, and every
        # endpoint must be electrically eligible: a declared connection is never
        # silently dropped and never routed through an excluded structure.
        declared_topology = get_computational_topology(model)
        computational_topology = None
        if declared_topology is not None:
            applicable = declared_topology.connections_within(model.compartments)
            for connection in applicable:
                for section_id, role in (
                    (connection.parent_section_id, "parent"),
                    (connection.child_section_id, "child"),
                ):
                    if section_id in excluded_ids:
                        raise PassiveGeometryError(
                            f"Model '{model.neuron_id}' declares computational "
                            f"topology '{declared_topology.name}' connecting "
                            f"'{connection.parent_section_id}' -> "
                            f"'{connection.child_section_id}', but its "
                            f"{role} section '{section_id}' is declared "
                            f"excluded from electrical representation. The "
                            f"connection is neither dropped silently nor "
                            f"routed through the excluded structure."
                        )
                assert connection.parent_section_id in eligible
                assert connection.child_section_id in eligible
            computational_topology = declared_topology

        # Derive computational segments for every eligible section, in
        # deterministic order. Excluded sections get no segments at all.
        unit_ids_by_section: Dict[str, List[str]] = {}
        all_segments: Dict[str, List[DerivedSegment]] = {}
        for section_id in eligible:
            segments = derive_segments(model.compartments[section_id], subdivision_plan)
            all_segments[section_id] = list(segments)
            unit_ids_by_section[section_id] = [s.segment_id for s in segments]

        prepared: List[CompartmentElectrical] = []
        computational_connections_by_segment: Dict[str, object] = {}
        for section_id in eligible:
            compartment = model.compartments[section_id]
            segments = all_segments[section_id]

            for segment in segments:
                # A derived copy; the source CompartmentGeometry is untouched.
                metrics = compute_compartment_metrics(
                    _SegmentCompartmentProxy(segment, compartment.provenance)
                )

                if metrics.lateral_surface_area_um2 is None:
                    missing = _missing_membrane_geometry_fields(segment)
                    raise PassiveGeometryError(
                        f"Compartment '{segment.segment_id}' of model "
                        f"'{model.neuron_id}' has no computable membrane area. "
                        f"Missing required source-backed geometry field(s): "
                        f"{missing}. Present: length_um="
                        f"{segment.geometry.length_um}, diameter_um="
                        f"{segment.geometry.diameter_um}. "
                        f"Membrane capacitance and leak conductance require an "
                        f"explicit membrane area; no value is inferred, "
                        f"substituted, or fabricated. Geometry detail: "
                        f"{metrics.derivation_note}"
                    )

                anatomical_parent_id = compartment.parent_id
                # 3.0D-7P: a declared computational topology is authoritative
                # for the sections it names. A section it does not name falls
                # back to the anatomical parent, so models with no declared
                # computational abstraction are entirely unaffected.
                computational_connection = None
                if computational_topology is not None:
                    computational_connection = (
                        computational_topology.connection_for_child(
                            segment.source_section_id
                        )
                    )

                if computational_connection is not None:
                    computational_parent_id = (
                        computational_connection.parent_section_id
                    )
                    if segment.segment_index == 0:
                        # 3.0D-7Q: exact NEURON semantics. The source states
                        # child.connect(parent, 0, 0), i.e. the CHILD's
                        # PROXIMAL end (x=0) joins the PARENT's PROXIMAL end
                        # (x=0). The source section connection therefore
                        # attaches at child segment 0 and parent segment 0, and
                        # is never moved to the child's distal end merely
                        # because the section is subdivided. Segments 1..N-1
                        # keep the 7K linear chain below.
                        electrical_parent_id = unit_ids_by_section[
                            computational_parent_id
                        ][0]
                        computational_connections_by_segment[
                            segment.segment_id
                        ] = computational_connection
                    else:
                        # 7K internal chain: segment i hangs off segment i-1.
                        electrical_parent_id = segments[
                            segment.segment_index - 1
                        ].segment_id
                elif segment.segment_index > 0:
                    # Segments 1..N-1 form a linear electrical chain whatever
                    # the section's parent situation.
                    electrical_parent_id = segments[
                        segment.segment_index - 1
                    ].segment_id
                elif anatomical_parent_id in unit_ids_by_section:
                    # Segment 0 inherits the section's electrical parent,
                    # which is the distal segment of the parent section.
                    electrical_parent_id = unit_ids_by_section[anatomical_parent_id][-1]
                else:
                    electrical_parent_id = None

                electrical_root_reason = ""
                axial_resistance_ohm = None
                if electrical_parent_id is None:
                    if computational_connection is None and anatomical_parent_id is None:
                        axial_derivation = "anatomical root: no parent axial path"
                    else:
                        axial_derivation = (
                            f"electrical root: no computational or eligible "
                            f"anatomical parent, so no axial path is invented"
                        )
                        electrical_root_reason = (
                            f"no computational parent is declared and "
                            f"anatomical parent "
                            f"'{anatomical_parent_id}' is not electrically "
                            f"represented"
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
                capacitance_F = cm_specific * _UF_TO_F * membrane_area_cm2
                leak_conductance_S = g_specific * _MS_TO_S * membrane_area_cm2

                # 3.0D-7O: explicit bridge records. Each derived value names the
                # profile that supplied its specific parameter, the geometry it
                # was derived from, and carries UNKNOWN provenance because it is
                # not a source-reported biological measurement.
                capacitance_derivation = (
                    f"membrane capacitance: C = Cm_specific * membrane_area = "
                    f"{cm_specific} uF/cm2 * {membrane_area_cm2} cm2 = "
                    f"{capacitance_F} F, from "
                    f"{metrics.derivation_note}"
                )
                leak_derivation = (
                    f"leak conductance: g_leak = g_leak_density * membrane_area "
                    f"= {g_specific} mS/cm2 * {membrane_area_cm2} cm2 = "
                    f"{leak_conductance_S} S, from {metrics.derivation_note}"
                )
                reversal_derivation = (
                    f"leak reversal potential: E_leak = "
                    f"{e_leak_mV} mV, taken directly from the authorized "
                    f"profile; it is not derived from geometry"
                )

                applied: List[AppliedParameter] = [
                    AppliedParameter(
                        name="capacitance",
                        value=capacitance_F,
                        unit="F",
                        profile_name=self._profile.name,
                        source_parameter=AUTHORIZED_CM,
                        source_parameter_provenance=ProvenanceRecord(
                            self._profile.get(AUTHORIZED_CM).provenance_category,
                            self._profile.get(AUTHORIZED_CM).source,
                        ),
                        derivation=capacitance_derivation,
                        provenance=_derived_provenance(
                            f"Derived in 3.0D-7O by applying the authorized "
                            f"profile parameter '{AUTHORIZED_CM}' to the "
                            f"geometry-derived membrane area of source section "
                            f"'{segment.source_section_id}'. {capacitance_derivation} "
                            f"This is a DERIVED value, not a measured biological "
                            f"capacitance; the specific parameter itself remains an "
                            f"estimated model value."
                        ),
                        source_section_id=segment.source_section_id,
                        is_geometry_derived=True,
                    ),
                    AppliedParameter(
                        name="leak_conductance",
                        value=leak_conductance_S,
                        unit="S",
                        profile_name=self._profile.name,
                        source_parameter=AUTHORIZED_G_LEAK,
                        source_parameter_provenance=ProvenanceRecord(
                            self._profile.get(AUTHORIZED_G_LEAK).provenance_category,
                            self._profile.get(AUTHORIZED_G_LEAK).source,
                        ),
                        derivation=leak_derivation,
                        provenance=_derived_provenance(
                            f"Derived in 3.0D-7O by applying the authorized "
                            f"profile parameter '{AUTHORIZED_G_LEAK}' to the "
                            f"geometry-derived membrane area of source section "
                            f"'{segment.source_section_id}'. {leak_derivation} "
                            f"This is a DERIVED value, not a measured biological "
                            f"conductance; the specific parameter itself remains an "
                            f"estimated model value."
                        ),
                        source_section_id=segment.source_section_id,
                        is_geometry_derived=True,
                    ),
                    AppliedParameter(
                        name="leak_reversal_potential",
                        value=e_leak_mV,
                        unit="mV",
                        profile_name=self._profile.name,
                        source_parameter=AUTHORIZED_E_LEAK,
                        source_parameter_provenance=ProvenanceRecord(
                            self._profile.get(AUTHORIZED_E_LEAK).provenance_category,
                            self._profile.get(AUTHORIZED_E_LEAK).source,
                        ),
                        derivation=reversal_derivation,
                        provenance=_derived_provenance(
                            f"Applied in 3.0D-7O directly from the authorized "
                            f"profile parameter '{AUTHORIZED_E_LEAK}'. It is NOT "
                            f"derived from geometry and is NOT a direct measurement "
                            f"of a GFS neuron; the source attributes it to the "
                            f"Gunay et al. motoneuron model."
                        ),
                        source_section_id=segment.source_section_id,
                        is_geometry_derived=False,
                    ),
                ]

                if axial_resistance_ohm is not None:
                    axial_is_taper = (
                        segment.geometry.diameter_distal_um is not None
                        and segment.geometry.diameter_distal_um
                        != segment.geometry.diameter_um
                    )
                    applied.append(
                        AppliedParameter(
                            name="axial_resistance",
                            value=axial_resistance_ohm,
                            unit="ohm",
                            profile_name=self._profile.name,
                            source_parameter=AUTHORIZED_RA,
                            source_parameter_provenance=ProvenanceRecord(
                                self._profile.get(AUTHORIZED_RA).provenance_category,
                                self._profile.get(AUTHORIZED_RA).source,
                            ),
                            derivation=axial_derivation,
                            provenance=_derived_provenance(
                                f"Derived in 3.0D-7O by applying the authorized "
                                f"profile parameter '{AUTHORIZED_RA}' (canonical "
                                f"unit {CANONICAL_AXIAL_RESISTIVITY_UNIT}) to the "
                                f"geometry of source section "
                                f"'{segment.source_section_id}'. {axial_derivation} "
                                f"This is a DERIVED per-compartment resistance in "
                                f"ohm, not the specific axial resistivity and not a "
                                f"measured biological value."
                                + (
                                    " The 3.0D-7J linearly tapered circular cable "
                                    "convention R = Ra * L / (pi * r1 * r2) is used "
                                    "exactly and is not replaced or approximated."
                                    if axial_is_taper
                                    else " Uniform circular cylinder convention "
                                    "R = Ra * L / A."
                                )
                            ),
                            source_section_id=segment.source_section_id,
                            is_geometry_derived=True,
                        )
                    )

                prepared.append(
                    CompartmentElectrical(
                        compartment_id=segment.segment_id,
                        membrane_area_cm2=membrane_area_cm2,
                        capacitance_F=capacitance_F,
                        leak_conductance_S=leak_conductance_S,
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
                        profile_name=self._profile.name,
                        applied_parameters=tuple(applied),
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
                    computational_source=(
                        computational_connections_by_segment.get(
                            compartment.compartment_id
                        ).source_text()
                        if computational_connections_by_segment.get(
                            compartment.compartment_id
                        )
                        else ""
                    ),
                    source_model_id=(
                        computational_connections_by_segment[
                            compartment.compartment_id
                        ].source_model_id
                        if computational_connections_by_segment.get(
                            compartment.compartment_id
                        )
                        else ""
                    ),
                    source_statement=(
                        computational_connections_by_segment[
                            compartment.compartment_id
                        ].source_statement
                        if computational_connections_by_segment.get(
                            compartment.compartment_id
                        )
                        else ""
                    ),
                    direction=(
                        computational_connections_by_segment[
                            compartment.compartment_id
                        ].direction
                        if computational_connections_by_segment.get(
                            compartment.compartment_id
                        )
                        else ""
                    ),
                    computational_derivation=(
                        computational_connections_by_segment[
                            compartment.compartment_id
                        ].derivation
                        if computational_connections_by_segment.get(
                            compartment.compartment_id
                        )
                        else ""
                    ),
                    computational_provenance=(
                        computational_connections_by_segment[
                            compartment.compartment_id
                        ].provenance
                        if computational_connections_by_segment.get(
                            compartment.compartment_id
                        )
                        else None
                    ),
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
            parameter_application=self.parameter_application(),
            computational_topology=computational_topology,
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
        """Advance the passive network by one step with the declared method.

        Dispatches to the declared numerical method only. The default remains
        the existing explicit forward Euler step, which is unchanged; the
        implicit backward Euler step is reached only when the backend was
        explicitly constructed with it.

        Returns the per-compartment net current in amperes (outward positive)
        that produced the update, keyed by compartment id.
        """
        if self._numerical_method is PassiveNumericalMethod.BACKWARD_EULER:
            return self._step_backward_euler(
                network, state, injected_currents_A, timestep_ms
            )
        return self._step_forward_euler(
            network, state, injected_currents_A, timestep_ms
        )

    def _step_forward_euler(
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

    def _step_backward_euler(
        self,
        network: PassiveNetwork,
        state: PassiveNetworkState,
        injected_currents_A: Optional[Dict[str, float]] = None,
        timestep_ms: Optional[float] = None,
    ) -> Dict[str, float]:
        """Advance the passive network by one implicit backward Euler step.

        Solves, in SI units (V in volts):

            [C_i/dt + g_i + sum_j 1/R_ij] V_i^{n+1}
              - sum_j (1/R_ij) V_j^{n+1}
            = (C_i/dt) V_i^n + g_i E_i + I_i

        The injected-current convention is unchanged: a positive injected
        current is INWARD and appears on the right-hand side, exactly as in
        the explicit step, so a positive current still depolarizes a
        compartment.

        Returns the per-compartment net current in amperes (outward positive)
        that produced the update, C_i (V^{n+1} - V^n)/dt, keyed by compartment
        id.
        """
        dt_ms = self._validate_timestep(
            network.timestep_ms if timestep_ms is None else timestep_ms
        )
        dt_s = dt_ms * 1e-3
        injected = injected_currents_A or {}
        operator = self.backward_euler_operator(network, dt_ms)

        compartments = network.compartments
        previous_V = [
            state.voltages_mV[c.compartment_id] * 1e-3 for c in compartments
        ]
        rhs = [
            (c.capacitance_F / dt_s) * previous_V[i]
            + c.leak_conductance_S * (c.leak_reversal_mV * 1e-3)
            + injected.get(c.compartment_id, 0.0)
            for i, c in enumerate(compartments)
        ]
        solved_V = operator.solve(rhs)

        net_current: Dict[str, float] = {}
        for i, compartment in enumerate(compartments):
            cid = compartment.compartment_id
            state.voltages_mV[cid] = solved_V[i] * 1e3
            net_current[cid] = (
                compartment.capacitance_F / dt_s
            ) * (solved_V[i] - previous_V[i])
        return net_current

    def reset_state(
        self,
        model: CompartmentModel,
        network: PassiveNetwork,
        state: PassiveNetworkState,
    ) -> None:
        """Reset a passive simulation to the compartments' represented voltages.

        Every network compartment is restored from the represented voltage of
        the SOURCE section it was derived from, so a subdivided network is
        reset segment by segment without any segment keeping a value.

        The integration methods carry no hidden state: no electrical state is
        written back onto any Compartment, and every assembled implicit
        operator is dropped, so nothing survives the reset.
        """
        initial = self.initial_state(model)
        restored: Dict[str, float] = {}
        for compartment in network.compartments:
            source_id = (
                compartment.source_section_id
                if compartment.source_section_id is not None
                else compartment.compartment_id
            )
            if source_id not in initial.voltages_mV:
                raise PassiveBackendError(
                    f"Cannot reset network '{network.model_id}': compartment "
                    f"'{compartment.compartment_id}' derives from section "
                    f"'{source_id}', which carries no represented initial "
                    f"voltage. No default voltage is invented."
                )
            restored[compartment.compartment_id] = initial.voltages_mV[source_id]
        state.voltages_mV.clear()
        state.voltages_mV.update(restored)
        self.clear_numerical_cache()


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
