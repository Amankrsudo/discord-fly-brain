"""Explicit active-conductance authorization profiles (3.0D-7S).

This module is the AUTHORIZATION layer that sits on top of the active
conductance evidence registry, mirroring the 3.0D-7E/7F passive layering:

    ActiveConductanceRegistry   evidence layer     (what sources support)
    ActiveParameterProfile      authorization layer (what we permit ourselves
                                                     to use, for what purpose)

Layering:

    passive_electrical_registry  -> passive_profiles      (3.0D-7E/7F)
    active_conductance_registry  -> active_profiles       (3.0D-7S)

An authorization is NOT a claim of measurement, and it is NOT a licence to
simulate. The single profile here, ``augustin_2019_active_model``, means:

    "These are the published active parameters of the Augustin et al. 2019
     computational model, recorded so that a future, separately validated
     reproduction step may refer to them explicitly."

It does NOT mean:

    "These are experimentally measured properties of GF, or of any GFS neuron."

Hard limits enforced here:

- ``is_default`` is False. The profile is opt-in and is never selected
  implicitly.
- ``eligible_for_live_solver`` is False. Nothing in this profile may be
  connected to ``PassiveCableModel.step()``, and no compartment, no
  CompartmentElectrical and no solver state is ever populated from it.
- No Hodgkin-Huxley equations, no gating variables and no channel currents
  exist in this module or anywhere it is imported.
- The profile is documentation/reproduction authorization only. Quantitative
  GF-specific kinetics stay UNAVAILABLE: the active densities and reversal
  potentials are authorized for a future reproduction attempt, while the
  kinetics required to make that attempt meaningful are not available and are
  therefore not authorized.
"""

from dataclasses import dataclass
from typing import Tuple

from .active_conductance_registry import (
    ActiveConductanceRegistry, get_active_conductance_registry,
)
from .passive_profiles import AUTHORIZATION_SCOPE_MODEL_REPRODUCTION
from .provenance import ParameterProvenance


PROFILE_AUGUSTIN_2019_ACTIVE_MODEL = "augustin_2019_active_model"

_CONTEXT_PUBLISHED_MODEL = "published_model_reproduction"

_MODEL_SCOPE_NOTE = (
    "MODEL REPRODUCTION AUTHORIZATION ONLY. These are the published active "
    "parameters of the simplified Augustin et al. 2019 computational GFS "
    "model. Authorizing them here documents them; it does not establish that "
    "they are experimentally measured GF properties, and it does not enable "
    "any simulation of them. Results obtained under this profile must be "
    "reported as model-reproduction results, never as measurements of "
    "Drosophila escape-circuit biology."
)

_NOT_LIVE_NOTE = (
    "NOT ELIGIBLE FOR THE LIVE SOLVER. This profile is documentation and "
    "reproduction authorization only. It is not connected to "
    "PassiveCableModel.step(), it populates no compartment electrical "
    "quantity, and it creates no gating variable and no channel current. "
    "Live Hodgkin-Huxley implementation requires a separate "
    "parameter-extraction and numerical-validation checkpoint, and a "
    "defensible timestep."
)

_KINETICS_GAP_NOTE = (
    "QUANTITATIVE KINETIC AUTHORIZATION IS ABSENT. The conductance densities "
    "and reversal potentials below are authorized for a future reproduction "
    "attempt, but the activation and inactivation kinetics required to make "
    "that attempt meaningful are NOT available for GF. Channel identity from "
    "Kadas et al. 2019 does not license importing generic Drosophila channel "
    "kinetics."
)


@dataclass(frozen=True)
class AuthorizedActiveParameter:
    """One active quantity explicitly authorized by an active profile.

    Values are copied from the evidence registry, never re-derived, so
    provenance and source stay intact.
    """

    name: str
    channel: str
    value: float
    unit: str
    provenance_category: ParameterProvenance
    source: str
    source_model: str
    neuron_scope: str
    authorization_scope: str
    limitations: str
    eligible_for_live_solver: bool = False


@dataclass(frozen=True)
class ExcludedActiveQuantity:
    """A candidate active quantity deliberately left outside a profile."""

    name: str
    reason: str


@dataclass(frozen=True)
class UnreadyActiveKinetics:
    """A kinetic quantity explicitly recorded as NOT authorized."""

    channel: str
    quantity: str
    reason: str


@dataclass(frozen=True)
class ActiveParameterProfile:
    """An explicit, opt-in authorization of active parameters.

    A permission record, not a parameter assignment. It does not populate
    CompartmentElectrical or CableParameters, does not alter any simulation
    path, and is never a default.
    """

    name: str
    description: str
    context: str
    model_reproduction_only: bool
    opt_in: bool
    is_default: bool
    eligible_for_live_solver: bool
    parameters: Tuple[AuthorizedActiveParameter, ...]
    excluded: Tuple[ExcludedActiveQuantity, ...]
    unready_kinetics: Tuple[UnreadyActiveKinetics, ...]
    channel_identities: Tuple[str, ...]
    limitations: str

    def authorized_names(self) -> Tuple[str, ...]:
        return tuple(p.name for p in self.parameters)

    def get(self, name: str) -> AuthorizedActiveParameter:
        for p in self.parameters:
            if p.name == name:
                return p
        raise KeyError(
            f"Active parameter '{name}' is not authorized by profile "
            f"'{self.name}'"
        )

    def is_authorized(self, name: str) -> bool:
        return any(p.name == name for p in self.parameters)

    def any_live_solver_eligible(self) -> bool:
        return any(p.eligible_for_live_solver for p in self.parameters)


_EXPECTED_ACTIVE_PARAMETERS = (
    ("g_Na", "Na (transient)", 300.0, "mS/cm2"),
    ("g_Nap", "Na (persistent)", 0.11, "mS/cm2"),
    ("g_K", "K (delayed rectifier)", 10.0, "mS/cm2"),
    ("E_Na", "Na (transient and persistent)", 65.0, "mV"),
    ("E_K", "K (delayed rectifier)", -74.0, "mV"),
)

_REASON_NOT_GF_MEASURED = (
    "A published computational model parameter, not a GF measurement. Not "
    "authorized as a biological property of any neuron."
)

_REASON_CA_CONDUCTANCE = (
    "No Ca2+ conductance density is authorized. Kadas et al. 2019 implicates "
    "DmCa1D in GF conduction qualitatively, but no Ca conductance density, "
    "reversal potential or calcium kinetics are available in the project "
    "sources, and none are invented."
)

_REASON_BK_CONDUCTANCE = (
    "No BK/Slowpoke conductance density is authorized. Kadas et al. 2019 "
    "reports a qualitative effect on GF conduction velocity, but no "
    "conductance density, reversal potential or calcium-dependent kinetics "
    "are available in the project sources, and none are invented."
)

_REASON_HH_KINETICS = (
    "Hodgkin-Huxley kinetics are not authorized. No GF-specific "
    "quantitative kinetic parameter set exists in the project sources, and "
    "generic Drosophila channel kinetics must not be imported merely because "
    "the channel identity is known."
)


def build_augustin_2019_active_model_profile() -> ActiveParameterProfile:
    """Build the opt-in Augustin 2019 active model documentation profile.

    Values are read from the active conductance evidence registry so this
    layer can never drift from the recorded evidence. If the registry no
    longer reports the expected value, unit, channel or provenance category,
    this raises instead of silently authorizing something else.
    """
    registry: ActiveConductanceRegistry = get_active_conductance_registry()

    authorized = []
    for name, channel, value, unit in _EXPECTED_ACTIVE_PARAMETERS:
        record = registry.get(name)
        if record.value != value or record.unit != unit:
            raise ValueError(
                f"Evidence drift for '{name}': registry reports "
                f"{record.value} {record.unit}, profile expects {value} {unit}"
            )
        if record.channel != channel:
            raise ValueError(
                f"Channel drift for '{name}': registry reports "
                f"'{record.channel}', profile expects '{channel}'"
            )
        if record.provenance_category is not (
            ParameterProvenance.PUBLISHED_MODEL_PARAMETER
        ):
            raise ValueError(
                f"Provenance drift for '{name}': registry reports "
                f"{record.provenance_category}, profile expects "
                f"PUBLISHED_MODEL_PARAMETER"
            )
        if record.experimentally_demonstrated_in_gf:
            raise ValueError(
                f"Provenance drift for '{name}': a published model parameter "
                f"must not be recorded as a direct GF measurement"
            )
        authorized.append(
            AuthorizedActiveParameter(
                name=record.name,
                channel=record.channel,
                value=record.value,
                unit=record.unit,
                provenance_category=record.provenance_category,
                source=record.source,
                source_model=record.source_model,
                neuron_scope=record.neuron_scope,
                authorization_scope=AUTHORIZATION_SCOPE_MODEL_REPRODUCTION,
                limitations=record.limitations,
                eligible_for_live_solver=False,
            )
        )

    unready = tuple(
        UnreadyActiveKinetics(
            channel=record.channel,
            quantity=record.quantity,
            reason=record.reason,
        )
        for record in registry.kinetic_readiness
    )

    return ActiveParameterProfile(
        name=PROFILE_AUGUSTIN_2019_ACTIVE_MODEL,
        description=(
            "Active conductance densities and reversal potentials of the "
            "simplified Augustin et al. 2019 giant fiber system model, "
            "recorded for explicit documentation and for a future, separately "
            "validated reproduction step. NOT authorized for the live solver."
        ),
        context=_CONTEXT_PUBLISHED_MODEL,
        model_reproduction_only=True,
        opt_in=True,
        is_default=False,
        eligible_for_live_solver=False,
        parameters=tuple(authorized),
        excluded=(
            ExcludedActiveQuantity(
                name="g_Ca",
                reason=_REASON_CA_CONDUCTANCE,
            ),
            ExcludedActiveQuantity(
                name="E_Ca",
                reason=_REASON_CA_CONDUCTANCE,
            ),
            ExcludedActiveQuantity(
                name="g_BK",
                reason=_REASON_BK_CONDUCTANCE,
            ),
            ExcludedActiveQuantity(
                name="E_BK",
                reason=_REASON_BK_CONDUCTANCE,
            ),
            ExcludedActiveQuantity(
                name="hodgkin_huxley_kinetics",
                reason=_REASON_HH_KINETICS,
            ),
            ExcludedActiveQuantity(
                name="q10_kinetic_scaling",
                reason=_REASON_HH_KINETICS,
            ),
            ExcludedActiveQuantity(
                name="gf_directly_measured_conductance_density",
                reason=_REASON_NOT_GF_MEASURED,
            ),
        ),
        unready_kinetics=unready,
        channel_identities=registry.channel_names(),
        limitations=(
            _MODEL_SCOPE_NOTE + " " + _NOT_LIVE_NOTE + " " + _KINETICS_GAP_NOTE
        ),
    )


def available_active_profiles() -> Tuple[str, ...]:
    """Names of every active parameter profile that can be opted into."""
    return (PROFILE_AUGUSTIN_2019_ACTIVE_MODEL,)


def get_active_parameter_profile(name: str) -> ActiveParameterProfile:
    """Return an active parameter profile by name (explicit opt-in).

    No active profile is a default, and none is eligible for the live solver.
    The caller must name the profile it wants.
    """
    if name == PROFILE_AUGUSTIN_2019_ACTIVE_MODEL:
        return build_augustin_2019_active_model_profile()
    raise KeyError(
        f"Unknown active parameter profile '{name}'. "
        f"Available: {available_active_profiles()}"
    )
