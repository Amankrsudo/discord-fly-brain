"""Active conductance evidence registry (3.0D-7S).

Records what the literature supports about giant fiber (GF) active
conductances, with the evidence status and provenance kept explicit, as a
boundary BEFORE any active conductance is used.

This module is DATA ONLY. It:

- does NOT implement Hodgkin-Huxley equations,
- does NOT activate any conductance in the live passive network,
- does NOT populate CompartmentElectrical or CableParameters,
- does NOT populate any gating or HH state variable,
- does NOT calculate any channel current,
- does NOT translate compiled NEURON channel mechanisms into Python.

Two evidence classes are kept strictly apart, because conflating them is the
main way an active model becomes indefensible:

    QUANTITATIVE records   a source explicitly states a value
                           (Augustin 2019 model conductance densities and
                           reversal potentials)
    QUALITATIVE records    a source experimentally implicates a channel in
                           GF conduction, with NO number attached
                           (Kadas et al. 2019)

Provenance boundary maintained here:

- g_Na, g_Nap and g_K are PUBLISHED_MODEL_PARAMETER values of the Augustin
  et al. 2019 computational model. They are NOT direct GF conductance-density
  measurements, NOT GF-specific experimental measurements, and NOT silently
  applicable to every GFS neuron. The published active sections are largely
  based on a Drosophila motoneuron model with parameters manually adjusted
  for the GFS model.
- Kadas et al. 2019 experimentally implicates Para, Shaker, DmCa1D and
  Slowpoke in GF axonal conduction. That establishes channel IDENTITY and
  FUNCTION for GF. It does NOT provide a complete quantitative GF parameter
  set, and no conductance density, kinetic parameter, reversal potential,
  Q10 or single-channel conductance is invented for any of them here.
- A known channel identity is NOT a licence to import generic Drosophila
  channel kinetics. Quantitative kinetic readiness is therefore recorded
  separately, and is currently False for every channel in this registry.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .provenance import ParameterProvenance, ProvenanceRecord


SOURCE_AUGUSTIN_ACTIVE = (
    "Augustin et al. 2019 (eLife, PMC6469880) Table 1, active membrane "
    "parameters of the simplified GFS model; ModelDB 245415 "
    "(ModelDBRepository/245415), file gfpn.py. The published active sections "
    "are largely based on a Drosophila motoneuron model, with parameters "
    "manually adjusted in the GFS model."
)

SOURCE_AUGUSTIN_ACTIVE_CITATION = (
    "Augustin et al. 2019. Drosophila integrative nerve circuit for "
    "escape behavior. eLife 8:e40240. https://pmc.ncbi.nlm.nih.gov/articles/"
    "PMC6469880/ . ModelDB accession 245415: "
    "https://github.com/ModelDBRepository/245415"
)

SOURCE_KADAS_GF_CHANNELS = (
    "Kadas et al. 2019 (eLife, PMC6709211), experimental evidence implicating "
    "specific channel families in Drosophila giant fiber axonal conduction. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6709211/"
)

SOURCE_MODELDB_CHANNELS = (
    "ModelDB 245415 compiled NEURON channel mechanisms, directory 'channels' "
    "(https://github.com/ModelDBRepository/245415/tree/master/channels). "
    "Recorded as the existence of the source implementation only."
)

_MODEL_SCOPE_AUGUSTIN = (
    "Augustin et al. 2019 computational model of the Drosophila escape "
    "pathway (giant fiber system)."
)

_NEURON_SCOPE_AUGUSTIN_ACTIVE = (
    "GFS model neurons as represented by the published model (giant fiber "
    "axon, TTM motoneuron, PSI interneuron, DLM motoneuron). NOT a "
    "GF-specific experimental measurement, and NOT established for each of "
    "those neurons individually."
)

_COMPUTATIONAL_NOT_MEASURED = (
    "MODEL PARAMETER, NOT A MEASUREMENT. This is an active parameter of the "
    "published Augustin 2019 computational model. The paper does NOT establish "
    "it as a direct GF conductance-density measurement, and the published "
    "active sections are largely based on a Drosophila motoneuron model with "
    "parameters manually adjusted for the GFS model. It must NOT be reported "
    "as an experimentally measured GF property, and it must NOT be silently "
    "applied to every GFS neuron."
)

_NOT_LIVE_NOTE = (
    "3.0D-7S is an EVIDENCE AND AUTHORIZATION checkpoint only. This quantity "
    "is NOT eligible for the live solver: no Hodgkin-Huxley mechanism exists "
    "in the passive backend, no compartment is populated with it, no gating "
    "variable exists and no channel current is calculated. Any later use "
    "requires a separate parameter-extraction and numerical-validation "
    "checkpoint."
)

_EXPERIMENTAL_IDENTITY_NOT_QUANTITATIVE = (
    "EXPERIMENTAL CHANNEL IDENTITY/FUNCTION EVIDENCE ONLY. This record carries "
    "NO conductance density, NO activation or inactivation kinetics, NO "
    "reversal potential, NO Q10 and NO single-channel conductance, because no "
    "such GF-specific quantitative value is available in the project's "
    "sources. A known channel identity is NOT a licence to import generic "
    "Drosophila channel kinetics."
)

_NO_GENERIC_KINETICS = (
    "NO GF-SPECIFIC QUANTITATIVE KINETIC PARAMETER SET IS AVAILABLE IN THE "
    "PROJECT SOURCES. Channel identity does not license importing generic "
    "Drosophila channel kinetics, and doing so would invent GF biology. The "
    "compiled NEURON mechanisms in ModelDB 245415 exist as source evidence "
    "but their kinetic tables are NOT extracted, translated or approximated "
    "in this checkpoint; that is a future parameter-extraction and "
    "numerical-validation task."
)


@dataclass(frozen=True)
class ActiveParameterRecord:
    """One active-conductance quantity a source explicitly states.

    ``value`` is the source's own number. ``None`` means the source states no
    value, which is different from a value of zero and is never substituted
    with a default.
    """

    name: str
    channel: str
    value: Optional[float]
    unit: str
    provenance_category: ParameterProvenance
    source: str
    source_citation: str
    source_model: str
    neuron_scope: str
    experimentally_demonstrated_in_gf: bool
    quantitatively_specified_for_gf: bool
    authorized_for_reproduction: bool
    eligible_for_live_solver: bool
    limitations: str
    notes: str = ""

    @property
    def provenance(self) -> ProvenanceRecord:
        """Provenance record for the value, if the source states one."""
        if self.value is None:
            return ProvenanceRecord(
                ParameterProvenance.UNKNOWN,
                "No value is stated by any project source for this quantity.",
            )
        return ProvenanceRecord(self.provenance_category, self.source)

    @property
    def has_value(self) -> bool:
        return self.value is not None


@dataclass(frozen=True)
class ChannelIdentityRecord:
    """Qualitative experimental evidence for a channel in GF.

    This record type cannot hold a number. Attempting to attach one is an
    error, so an invented conductance density, kinetic parameter or reversal
    potential cannot enter the registry through this path.
    """

    channel: str
    ion: str
    function: str
    gf_experimental_evidence: bool
    quantitatively_specified_for_gf: bool
    source: str
    source_citation: str
    limitations: str
    experimental_effect: str = ""

    def __post_init__(self) -> None:
        if not self.gf_experimental_evidence:
            raise ValueError(
                f"Channel identity record '{self.channel}' must state "
                f"experimental GF evidence; this registry only records "
                f"experimentally supported channel identities."
            )

    @property
    def has_quantitative_value(self) -> bool:
        """Always False: a qualitative record never carries a number."""
        return False


@dataclass(frozen=True)
class KineticReadinessRecord:
    """Whether a quantitative GF-specific kinetic set is available."""

    channel: str
    quantity: str
    ready: bool
    source: str
    reason: str

    @property
    def status(self) -> str:
        return "available" if self.ready else "not_available"


@dataclass(frozen=True)
class ChannelImplementationRecord:
    """The existence of a compiled channel implementation, not its content."""

    name: str
    location: str
    kinetics_extracted: bool
    limitation: str


@dataclass(frozen=True)
class ActiveConductanceRegistry:
    """Evidence registry for active conductances. NOT an assignment mechanism.

    Records what sources support and how strongly. It assigns nothing: no
    Compartment, no CableParameters, no CompartmentElectrical and no solver
    state is populated from this registry.
    """

    source: str
    parameters: Tuple[ActiveParameterRecord, ...]
    channel_identities: Tuple[ChannelIdentityRecord, ...]
    kinetic_readiness: Tuple[KineticReadinessRecord, ...]
    channel_implementations: Tuple[ChannelImplementationRecord, ...]
    scope_note: str

    def get(self, name: str) -> ActiveParameterRecord:
        for record in self.parameters:
            if record.name == name:
                return record
        raise KeyError(f"Active parameter '{name}' not in registry")

    def names(self) -> Tuple[str, ...]:
        return tuple(record.name for record in self.parameters)

    def channel(self, channel_name: str) -> ChannelIdentityRecord:
        for record in self.channel_identities:
            if record.channel == channel_name:
                return record
        raise KeyError(f"Channel '{channel_name}' not in registry")

    def channel_names(self) -> Tuple[str, ...]:
        return tuple(record.channel for record in self.channel_identities)

    def readiness(self, channel_name: str, quantity: str) -> KineticReadinessRecord:
        for record in self.kinetic_readiness:
            if record.channel == channel_name and record.quantity == quantity:
                return record
        raise KeyError(
            f"No kinetic readiness record for '{channel_name}' / '{quantity}'"
        )

    def ready_kinetics(self) -> Tuple[str, ...]:
        return tuple(
            f"{record.channel}/{record.quantity}"
            for record in self.kinetic_readiness
            if record.ready
        )

    def any_live_solver_eligible(self) -> bool:
        """Always False in 3.0D-7S: nothing here may reach the live solver."""
        return any(record.eligible_for_live_solver for record in self.parameters)


def _augustin_active_parameter(
    name: str, channel: str, value: float, unit: str, extra: str = ""
) -> ActiveParameterRecord:
    return ActiveParameterRecord(
        name=name,
        channel=channel,
        value=value,
        unit=unit,
        provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
        source=SOURCE_AUGUSTIN_ACTIVE,
        source_citation=SOURCE_AUGUSTIN_ACTIVE_CITATION,
        source_model=_MODEL_SCOPE_AUGUSTIN,
        neuron_scope=_NEURON_SCOPE_AUGUSTIN_ACTIVE,
        experimentally_demonstrated_in_gf=False,
        quantitatively_specified_for_gf=False,
        authorized_for_reproduction=True,
        eligible_for_live_solver=False,
        limitations=_COMPUTATIONAL_NOT_MEASURED + " " + extra + " " + _NOT_LIVE_NOTE,
    )


def _kadas_channel(
    channel: str, ion: str, function: str, effect: str
) -> ChannelIdentityRecord:
    return ChannelIdentityRecord(
        channel=channel,
        ion=ion,
        function=function,
        gf_experimental_evidence=True,
        quantitatively_specified_for_gf=False,
        source=SOURCE_KADAS_GF_CHANNELS,
        source_citation=SOURCE_KADAS_GF_CHANNELS,
        limitations=_EXPERIMENTAL_IDENTITY_NOT_QUANTITATIVE,
        experimental_effect=effect,
    )


def get_active_conductance_registry() -> ActiveConductanceRegistry:
    """Return the active conductance evidence registry.

    All records are evidence only. NONE is eligible for the live solver, and
    building this registry changes no Compartment, no network and no solver.
    """
    parameters = (
        _augustin_active_parameter(
            "g_Na", "Na (transient)", 300.0, "mS/cm2",
            extra=(
                "Sodium conductance density of the published active section "
                "used in the GFS model."
            ),
        ),
        _augustin_active_parameter(
            "g_Nap", "Na (persistent)", 0.11, "mS/cm2",
            extra=(
                "Persistent sodium conductance density of the published "
                "active section used in the GFS model."
            ),
        ),
        _augustin_active_parameter(
            "g_K", "K (delayed rectifier)", 10.0, "mS/cm2",
            extra=(
                "Potassium conductance density of the published active "
                "section used in the GFS model."
            ),
        ),
        _augustin_active_parameter(
            "E_Na", "Na (transient and persistent)", 65.0, "mV",
            extra=(
                "Sodium reversal potential used in the published GFS model. "
                "It is a model assumption, not a GF measurement, and it is "
                "not transferable to a different ion substitution context."
            ),
        ),
        _augustin_active_parameter(
            "E_K", "K (delayed rectifier)", -74.0, "mV",
            extra=(
                "Potassium reversal potential used in the published GFS model. "
                "It is a model assumption, not a GF measurement."
            ),
        ),
    )

    channel_identities = (
        _kadas_channel(
            "Para", "Na+", "fast voltage-gated sodium channel",
            "experimentally implicated in GF action potential conduction",
        ),
        _kadas_channel(
            "Shaker", "K+", "voltage-gated potassium channel",
            "experimentally implicated in GF axonal conduction",
        ),
        _kadas_channel(
            "DmCa1D", "Ca2+", "L-type-like calcium channel",
            "experimentally implicated in GF axonal conduction",
        ),
        _kadas_channel(
            "Slowpoke", "K+", "BK / calcium-activated potassium channel",
            "experimentally affects GF conduction velocity",
        ),
    )

    kinetic_readiness = tuple(
        KineticReadinessRecord(
            channel=channel,
            quantity=quantity,
            ready=False,
            source=SOURCE_MODELDB_CHANNELS,
            reason=_NO_GENERIC_KINETICS,
        )
        for channel, quantity in (
            ("Para", "activation_kinetics"),
            ("Para", "inactivation_kinetics"),
            ("Shaker", "activation_kinetics"),
            ("Shaker", "inactivation_kinetics"),
            ("DmCa1D", "activation_kinetics"),
            ("DmCa1D", "inactivation_kinetics"),
            ("DmCa1D", "calcium_dependent_kinetics"),
            ("Slowpoke", "activation_kinetics"),
            ("Slowpoke", "calcium_dependent_kinetics"),
        )
    )

    channel_implementations = (
        ChannelImplementationRecord(
            name="ModelDB 245415 compiled NEURON channel mechanisms",
            location=(
                "https://github.com/ModelDBRepository/245415/tree/master/channels"
            ),
            kinetics_extracted=False,
            limitation=(
                "The existence of the compiled mechanisms is recorded as "
                "source evidence only. Their kinetics are NOT extracted, "
                "translated into Python Hodgkin-Huxley equations, copied or "
                "approximated in this checkpoint. That requires a separate "
                "parameter-extraction and numerical-validation checkpoint."
            ),
        ),
    )

    return ActiveConductanceRegistry(
        source=(
            "Evidence registry for active conductances. Quantitative model "
            "parameters and qualitative experimental channel identities are "
            "recorded separately. ALL records are evidence only: NONE is "
            "eligible for the live solver and nothing here is activated."
        ),
        parameters=parameters,
        channel_identities=channel_identities,
        kinetic_readiness=kinetic_readiness,
        channel_implementations=channel_implementations,
        scope_note=(
            "GF active channel IDENTITIES are experimentally supported, and the "
            "Augustin et al. 2019 model provides explicit computational active "
            "conductance parameters. Those numerical parameters are MODEL "
            "PARAMETERS rather than direct GF measurements, and the project "
            "does not yet have a sufficiently validated GF-specific kinetic "
            "parameter set for live Hodgkin-Huxley implementation. 3.0D-7S "
            "therefore claims NO full GF HH readiness, NO biologically "
            "validated Na/K kinetics, NO validated Ca kinetics, NO complete "
            "channel distribution and NO experimental reproduction of any "
            "action potential waveform."
        ),
    )
