"""Explicit passive parameter authorization profiles (3.0D-7F).

This module is the AUTHORIZATION layer that sits on top of the passive
electrical evidence registry (3.0D-7E). The registry records what the
literature reports; this layer records which of those values may
explicitly be used, for what purpose, and under what limitations.

Layering:

    PassiveElectricalRegistry   evidence layer     (what sources report)
    PassiveParameterProfile     authorization layer (what we permit ourselves to use)

An authorization is NOT a claim of measurement. The single profile in this
module, ``augustin_2019_gfs_passive``, means:

    "Use these published Augustin 2019 model values when explicitly
     reproducing that model's passive assumptions."

It does NOT mean:

    "These values are experimentally established biological properties of
     every GFS neuron."

Scope limits enforced here:

- No Compartment.CableParameters is populated. This module is data only.
- No cable equations, no passive solver, no Hodgkin-Huxley channels.
- No membrane area is inferred, so no whole-cell measurement is ever
  converted into a specific membrane parameter.
- The profile is opt-in. It is never an engine default and never changes
  existing lif_voltage or conductance_v0 behavior.

Unit representation note:
    Specific axial resistance is stored in the canonical unit ohm*cm
    (ohm.cm). Augustin et al. 2019 Table 1 literally prints its entry as
    "Specific axial resistance | 35.4 Ω/cm (estimated)". The paper's
    printed notation is preserved as source text in the per-parameter
    limitation, while ohm*cm is the unambiguous canonical unit used here.
"""

from dataclasses import dataclass
from typing import Tuple

from .passive_electrical_registry import get_passive_electrical_registry
from .provenance import ParameterProvenance


PROFILE_AUGUSTIN_2019_GFS_PASSIVE = "augustin_2019_gfs_passive"

AUTHORIZATION_SCOPE_MODEL_REPRODUCTION = "published_model_reproduction"

_CONTEXT_PUBLISHED_MODEL = "published_model_reproduction"

_SOURCE_DLMN_WHOLE_CELL = (
    "Fayyazuddin et al. 2006 (PLoS Biol 4(3):e63, PMC1382016). "
    "Whole-cell patch clamp from the DLM branch motor neuron MN5: "
    "capacitance 43 +/- 2 pF (n=22), input resistance 102 +/- 12 MOhm (n=22). "
    "Whole-cell physiological measurements of one identified motor neuron. "
    "NOT specific membrane parameters and NOT transferable to GFS neurons."
)

_REASON_WHOLE_CELL = (
    "Whole-cell measurement of an identified motor neuron. Converting it to a "
    "specific membrane parameter would require membrane area, which is not "
    "measured for the modeled cells. Not authorized."
)

_REASON_GF_INPUT_RESISTANCE = (
    "Whole-cell input resistance of GF is a physiological observation, not a "
    "compartmental membrane property. Not authorized in this profile."
)

_REASON_GAP_JUNCTION = (
    "Gap-junction conductance is an estimated/fitted coupling parameter in the "
    "Augustin model, not a passive membrane property of a compartment. "
    "Not authorized in this profile."
)

_REASON_GFS_CONTEXT = (
    "Functional latency and following-frequency observations. Context only, "
    "not a parameter. Not authorized in this profile."
)

_REASON_SYNAPTIC = (
    "Synaptic conductance requires validated mapping from the existing LIF "
    "weight_mV calibration artifacts. No such mapping exists. Not authorized."
)

_REASON_ACTIVE = (
    "Active Na/K/Ca conductance densities and Hodgkin-Huxley kinetics are not "
    "authorized by this passive profile and remain blocked pending "
    "neuron-specific evidence and a defensible integration timestep."
)


@dataclass(frozen=True)
class AuthorizedPassiveParameter:
    """A single passive quantity explicitly authorized by a profile.

    Every field is frozen. Values are copied from the evidence registry
    (never re-derived), so provenance and source stay intact.
    """

    name: str
    value: float
    unit: str
    provenance_category: ParameterProvenance
    source: str
    authorization_scope: str
    limitations: str


@dataclass(frozen=True)
class ExcludedPassiveParameter:
    """A candidate quantity deliberately left outside a profile."""

    name: str
    reason: str


@dataclass(frozen=True)
class PassiveParameterProfile:
    """An explicit, opt-in authorization of passive parameters.

    A profile is a permission record, not a parameter assignment. It does
    not populate CableParameters and does not alter any simulation path.
    """

    name: str
    description: str
    context: str
    model_reproduction_only: bool
    opt_in: bool
    parameters: Tuple[AuthorizedPassiveParameter, ...]
    excluded: Tuple[ExcludedPassiveParameter, ...]
    limitations: str

    def authorized_names(self) -> Tuple[str, ...]:
        return tuple(p.name for p in self.parameters)

    def get(self, name: str) -> AuthorizedPassiveParameter:
        for p in self.parameters:
            if p.name == name:
                return p
        raise KeyError(
            f"Parameter '{name}' is not authorized by profile '{self.name}'"
        )

    def is_authorized(self, name: str) -> bool:
        return any(p.name == name for p in self.parameters)


_AUGUSTIN_MODEL_REPRODUCTION_LIMITATION = (
    "MODEL REPRODUCTION ONLY. These values are the published passive "
    "assumptions of the simplified Augustin 2019 GFS model. Using them means "
    "reproducing that model's assumptions. It does NOT mean these are "
    "experimentally established biological properties of GFS neurons, and it "
    "does NOT establish that these are the correct values for any real cell. "
    "Results obtained under this profile must be reported as model-reproduction "
    "results, never as measurements of Drosophila escape-circuit biology."
)

_AUGUSTIN_SEGMENTATION_NOTE = (
    "The published model discretizes each modeled section into 51 isopotential "
    "segments. That segmentation is a property of the reproduction target, not "
    "an authorization granted by this profile."
)

_EXPECTED_AUGUSTIN_PARAMETERS = (
    ("specific_membrane_capacitance", 1.0, "uF/cm2", ParameterProvenance.ESTIMATED),
    ("specific_axial_resistance", 35.4, "ohm*cm", ParameterProvenance.ESTIMATED),
    ("leak_conductance_density", 0.03, "mS/cm2", ParameterProvenance.ESTIMATED),
    (
        "leak_reversal_potential",
        -85.0,
        "mV",
        ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
    ),
)

_UNIT_LIMITATIONS = {
    "specific_membrane_capacitance": (
        "Specific membrane capacitance in uF/cm2, as reported by Augustin. "
        "Not a whole-cell capacitance."
    ),
    "specific_axial_resistance": (
        "Specific axial resistivity. CANONICAL UNIT: ohm*cm (ohm.cm). "
        "Augustin et al. 2019 Table 1 literally prints the entry as "
        "'Specific axial resistance | 35.4 Ω/cm (estimated)'. That printed "
        "notation is retained here as source text only; the canonical unit "
        "for specific axial resistance is ohm*cm, and that is the unit stored "
        "here. NOT ohm*cm2, and NOT a per-compartment axial resistance — "
        "deriving that requires geometry and remains the responsibility of a "
        "future solver step."
    ),
    "leak_conductance_density": (
        "Leak conductance density in mS/cm2, as reported by Augustin. "
        "Estimated in the source, not measured in GFS neurons."
    ),
    "leak_reversal_potential": (
        "Leak reversal potential attributed by Augustin to the Günay et al. "
        "motoneuron model, not a direct measurement of GFS neurons."
    ),
}

def _augustin_profile_exclusions() -> Tuple[ExcludedPassiveParameter, ...]:
    """Quantities deliberately left outside the Augustin reproduction profile.

    Built per call so each profile instance owns its own collection.
    """
    return (
        ExcludedPassiveParameter(
            name="gf_input_resistance",
            reason=_REASON_GF_INPUT_RESISTANCE,
        ),
        ExcludedPassiveParameter(
            name="gap_junction_conductance_young",
            reason=_REASON_GAP_JUNCTION,
        ),
        ExcludedPassiveParameter(
            name="gap_junction_conductance_old",
            reason=_REASON_GAP_JUNCTION,
        ),
        ExcludedPassiveParameter(
            name="gfs_electrophysiology_reference",
            reason=_REASON_GFS_CONTEXT,
        ),
        ExcludedPassiveParameter(
            name="dlmn_whole_cell_capacitance",
            reason=_REASON_WHOLE_CELL,
        ),
        ExcludedPassiveParameter(
            name="dlmn_whole_cell_input_resistance",
            reason=_REASON_WHOLE_CELL,
        ),
        ExcludedPassiveParameter(
            name="chemical_synapse_conductance",
            reason=_REASON_SYNAPTIC,
        ),
        ExcludedPassiveParameter(
            name="active_na_conductance_density",
            reason=_REASON_ACTIVE,
        ),
        ExcludedPassiveParameter(
            name="active_k_conductance_density",
            reason=_REASON_ACTIVE,
        ),
        ExcludedPassiveParameter(
            name="active_ca_conductance_density",
            reason=_REASON_ACTIVE,
        ),
        ExcludedPassiveParameter(
            name="hodgkin_huxley_parameters",
            reason=_REASON_ACTIVE,
        ),
    )


def build_augustin_2019_gfs_passive_profile() -> PassiveParameterProfile:
    """Build the opt-in Augustin 2019 GFS passive reproduction profile.

    Values are read from the passive electrical evidence registry so this
    layer can never drift from the recorded evidence. If the registry no
    longer reports the expected value, unit, or provenance category, this
    raises instead of silently authorizing something else.
    """
    registry = get_passive_electrical_registry()

    authorized = []
    for name, value, unit, category in _EXPECTED_AUGUSTIN_PARAMETERS:
        entry = registry.get(name)
        if entry.value != value or entry.unit != unit:
            raise ValueError(
                f"Evidence drift for '{name}': registry reports "
                f"{entry.value} {entry.unit}, profile expects {value} {unit}"
            )
        if entry.provenance_category != category:
            raise ValueError(
                f"Provenance drift for '{name}': registry reports "
                f"{entry.provenance_category}, profile expects {category}"
            )
        authorized.append(
            AuthorizedPassiveParameter(
                name=entry.name,
                value=entry.value,
                unit=entry.unit,
                provenance_category=entry.provenance_category,
                source=entry.source,
                authorization_scope=AUTHORIZATION_SCOPE_MODEL_REPRODUCTION,
                limitations=_UNIT_LIMITATIONS[name],
            )
        )

    return PassiveParameterProfile(
        name=PROFILE_AUGUSTIN_2019_GFS_PASSIVE,
        description=(
            "Passive membrane and axial properties of the simplified "
            "Augustin et al. 2019 giant fiber system model, authorized for "
            "explicit reproduction of that published model's assumptions."
        ),
        context=_CONTEXT_PUBLISHED_MODEL,
        model_reproduction_only=True,
        opt_in=True,
        parameters=tuple(authorized),
        excluded=_augustin_profile_exclusions(),
        limitations=(
            _AUGUSTIN_MODEL_REPRODUCTION_LIMITATION
            + " " + _AUGUSTIN_SEGMENTATION_NOTE
        ),
    )


def available_passive_profiles() -> Tuple[str, ...]:
    """Names of every passive parameter profile that can be opted into."""
    return (PROFILE_AUGUSTIN_2019_GFS_PASSIVE,)


def get_passive_parameter_profile(name: str) -> PassiveParameterProfile:
    """Return a passive parameter profile by name (explicit opt-in).

    No profile is a default. The caller must name the profile it wants.
    """
    if name == PROFILE_AUGUSTIN_2019_GFS_PASSIVE:
        return build_augustin_2019_gfs_passive_profile()
    raise KeyError(
        f"Unknown passive parameter profile '{name}'. "
        f"Available: {available_passive_profiles()}"
    )
