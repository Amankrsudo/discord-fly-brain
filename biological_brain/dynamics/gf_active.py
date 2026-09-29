"""GF axon active membrane mechanism (3.0D-8A).

THE FIRST LIVE NEURAL-DYNAMICS CHECKPOINT.

3.0D-7G integrated a PASSIVE cable. 3.0D-8A adds the three active membrane
mechanisms of the published Augustin et al. 2019 giant fiber system model, on
top of that existing passive infrastructure, and changes nothing about it.

WHAT IS REPRODUCED
------------------
The three NEURON mechanisms the published model inserts into its GF section,
transcribed from the VENDORED ModelDB 245415 source, which is the
implementation authority for this checkpoint:

    biological_brain/data/modeldb_245415/channels/nat.mod   transient Na, m^3*h
    biological_brain/data/modeldb_245415/channels/nap.mod   persistent Na, m
    biological_brain/data/modeldb_245415/channels/k.mod     delayed rectifier K, m

Every rate expression, voltage dependence, time constant, power in the
conductance expression, and initial condition below is the verbatim expression
from those files. The rate functions are NOT generalised textbook
Hodgkin-Huxley: nat.mod's mtau is '0.13 + 3.43/(1+exp((vm+45.35)/5.98))' and its
htau is '0.36 + exp((vm+20.65)/-10.47)', which are not the classic HH forms;
nap.mod and k.mod both have the voltage-INDEPENDENT 'mtau = 1'. Those
properties are preserved exactly, including the fact that nap and k have no
inactivation gate.

Membrane equation, per GF axon segment i, in the sign convention of the existing
3.0D-7G backend (outward current positive, injected current inward positive)::

    C_m dV_i/dt = -(I_leak + I_Nat + I_Nap + I_K + I_axial_out + I_axial_in)
                  + I_injected

    I_leak = g_leak * (V - E_leak)                      [3.0D-7G, unchanged]
    I_Nat  = g_Nat * m^3 * h * (V - E_Na)               [nat.mod, verbatim]
    I_Nap  = g_Nap * mn     * (V - E_Na)                [nap.mod, verbatim]
    I_K    = g_K   * mk     * (V - E_K)                 [k.mod, verbatim]
    I_axial(out of i toward j) = (V_i - V_j) / R_ij    [3.0D-7G, unchanged]

NUMERICAL METHOD: SEMI-IMPLICIT, AND WHY
----------------------------------------
The three active mechanisms make the membrane equation NONLINEAR in V through
the gating variables, so the linear backward-Euler matrix assembly of 3.0D-7G
cannot be reused unchanged, and 3.0D-8A does NOT rewrite the passive solver.
This checkpoint uses a SEMI-IMPLICIT scheme, which is the most defensible option
the existing architecture supports:

1. GATING VARIABLES, EXACT: each mechanism's state obeys the LINEAR ODE
   x' = (x_inf - x) / tau, with x_inf and tau functions of V only. Holding V
   fixed over the step makes that ODE exactly solvable in closed form, and
   8A integrates it with that exact solution, the same method the source files
   name ('SOLVE states METHOD cnexp'). The gating update is therefore NOT an
   approximation and is independent of the timestep.

2. MEMBRANE VOLTAGE, LINEARISED IMPLICIT: with the gating states advanced, the
   active conductances are treated as CONSTANT over the step and the membrane
   equation is solved implicitly, with the same matrix structure, the same
   assembly, and the same LU factorisation as the 3.0D-7G backward Euler path.
   This is unconditionally stable, which matters because the explicit path is
   NOT: the g_Nat density of 300 mS/cm2 gives the GF membrane a time constant
   of order Cm/g_Nat = 3.3 us, well below the 0.01 ms (10 us) timestep, so an
   explicit step at the policy timestep is unstable here. That is a NUMERICAL
   fact about the published density at the project timestep, not a biological
   one, and it is stated as such.

3. WHAT THIS IS NOT: this is not a fully implicit Newton solve of the coupled
   nonlinear system. A fully implicit treatment would require a Newton
   iteration on (V, m, h, mn, mk) jointly, which the current architecture does
   not provide. 8A does not silently pretend to do it either:
   ``GF_ACTIVE_NUMERICAL_LIMITATION`` records the approximation, and
   ``is_fully_implicit`` is False. The linearised-conductance treatment is
   first-order accurate in the coupling between gating and voltage.

THE TIMESTEP IS NOT CHANGED
----------------------------
``PASSIVE_CABLE_NUMERICAL_POLICY`` is NOT modified. 8A accepts a timestep only
if the existing policy already accepts it (0 < dt <= 0.01 ms), reuses that
policy object rather than declaring a competing one, and never silently raises
dt. ``PASSIVE_CABLE_NUMERICAL_POLICY.default_timestep_ms`` remains 0.01 ms and
``max_timestep_ms`` remains 0.01 ms. Because the scheme is stable but only
first-order, the AP peak is timestep-dependent, and the convergence behaviour is
reported by ``convergence_report()`` with an explicitly NUMERICAL tolerance
label, never a biological one. Numerical stability is not biological accuracy.

INITIAL STATE
-------------
V is initialised to the project's existing resting convention, E_leak = -85 mV,
read from the authorized passive profile rather than hard-coded. Gating
variables are initialised to their own steady state AT THAT VOLTAGE, which is
exactly what every one of the three INITIAL blocks does: nat.mod runs
'trates(v); m = minf; h = hinf', nap.mod runs 'trates(v); m = minf', and k.mod
runs 'trates(v); m = minf'. No gating variable is assigned an arbitrary value.

Note that at -85 mV this is a legitimate initial condition but not a fixed
point of the complete active membrane: the published model itself calls
'neuron.h.finitialize(-65)' (gfpn.py line 189), and 8A does NOT silently adopt
that -65 mV, because -65 mV is a NEURON harness choice rather than a parameter
of the .mod mechanisms. 8A uses the project resting convention the checkpoint
specifies and records the difference, and the membrane relaxes from -85 mV
toward its own active-mechanism resting potential as a RESULT of the
mechanisms, not as an assigned value.

WHAT IS OUT OF SCOPE, AND STAYS OUT
------------------------------------
- Only the GF axon is active. TTMn, PSI and DLMn are NOT given active
  mechanisms here even though gfpn.py inserts the same three into them, because
  this checkpoint is scoped to the GF. Attempting to activate a non-GF
  compartment raises.
- gap2.mod is NOT implemented. The unresolved 7U gap-junction unit conflict is
  not touched, resolved, or approximated. Attempting to add a gap junction
  raises.
- NO chemical synapse, NO Exp2Syn, NO synaptic conductance.
- NO sensory input. 7W, 7X, 7Y and 7Z are not imported; the module has no
  sensory transformation, no decision rule and no motor output.
- NO DmCa1D, NO Slowpoke, NO ShakB/Shaker, NO Para, NO calcium, NO Q10, NO
  temperature scaling. Kadas et al. 2019 establishes the BIOLOGICAL RELEVANCE
  of Para, Shaker, DmCa1D and Slowpoke in GF axonal conduction; that relevance
  is already recorded at 3.0D-7S and is deliberately NOT modelled here, because
  the Augustin mechanism set is the narrower validated computational starting
  point and no exact DmCa1D or Slowpoke equation exists in the vendored source.
  This checkpoint therefore does NOT model the full experimentally known GF
  ion-channel complement.
- NO GF spike threshold. No voltage is ever called a threshold; the AP test
  criterion in ``ap_diagnostic()`` is derived from the generated waveform.

THIS IS MODEL REPRODUCTION, NOT MEASUREMENT
--------------------------------------------
g_Nat = 300 mS/cm2, g_Nap = 0.11 mS/cm2, g_K = 10 mS/cm2, E_Na = +65 mV and
E_K = -74 mV are the published parameters of the Augustin et al. 2019
computational model. They are consumed from the 3.0D-7S authorized profile,
which itself consumes them from the 3.0D-7S evidence registry, and 8A defines
no second copy of any of them. They are NOT GF measurements. The published
active sections are largely based on a Drosophila motoneuron model with
parameters manually adjusted for the GFS model, and 3.0D-7S already records
that. ``AppliedActiveParameter.is_experimental_gf_measurement`` is False for
every applied value and the layer refuses to mark any of them True.

Cm = 1 uF/cm2, g_leak = 0.03 mS/cm2, E_leak = -85 mV and Ra = 35.4 ohm*cm come
from the 3.0D-7F authorized PASSIVE profile through the existing 3.0D-7G
prepared network. 8A neither re-declares nor re-derives them: it consumes the
per-segment capacitance, leak conductance and leak reversal that 7G already
derived from geometry, so removing the active conductances returns exactly the
passive behaviour rather than silently perturbing the passive parameters.
"""

import math
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..active_profiles import (
    ActiveParameterProfile, get_active_parameter_profile,
    available_active_profiles, PROFILE_AUGUSTIN_2019_ACTIVE_MODEL,
)
from ..active_mechanism_registry import (
    ActiveMechanismRegistry, get_active_mechanism_registry,
    KIND_DENSITY_CHANNEL, SOLVE_METHOD_CNEXP,
)
from ..morphology import CompartmentModel
from ..passive_profiles import (
    PROFILE_AUGUSTIN_2019_GFS_PASSIVE,
    AUTHORIZATION_SCOPE_MODEL_REPRODUCTION,
)
from ..provenance import ParameterProvenance, ProvenanceRecord
from .base import NumericalResolution
from .passive_cable import (
    PassiveCableModel, PassiveNetwork, CompartmentElectrical,
    PASSIVE_CABLE_NUMERICAL_POLICY, PassiveUnsupportedError,
    _lu_factor, _lu_solve,
)


MODEL_NAME_GF_ACTIVE_V0 = "gf_active_v0"

# The only section this checkpoint makes active.
GF_ACTIVE_SECTION_ID = "GF_axon"

# The neuron the 3.0D-8A configuration activates. 3.0D-8D configures the same
# engine for TTMN_ACTIVE_NEURON_ID; the mechanism equations are shared and are
# defined once, below, in NatRates and SingleGateRates.
NEURON_GF = "GF"

# The three vendored .mod files, named exactly as the 3.0D-7T registry names
# them so the two layers cannot drift apart silently.
MECHANISM_NAT = "nat"
MECHANISM_NAP = "nap"
MECHANISM_K = "k"

GF_ACTIVE_MECHANISMS = (MECHANISM_NAT, MECHANISM_NAP, MECHANISM_K)

# Mechanisms the source repository contains or the literature implicates that
# this checkpoint REFUSES, with the reason each is refused.
#
# MECHANISM_GAP2 is the SINGLE SOURCE OF TRUTH for this name. It is defined
# here, in the first checkpoint that names the vendored mechanism, and
# 3.0D-8C (electrical_coupling) imports it from here rather than restating it.
# 8A refuses gap2 as unsupported; 8C is the checkpoint that implements it.
MECHANISM_GAP2 = "gap2"
MECHANISM_UNSUPPORTED = (
    MECHANISM_GAP2,
    "DmCa1D",
    "Slowpoke",
    "ShakB",
    "Shaker",
    "Para",
    "Exp2Syn",
)

# .mod PARAMETER defaults that gfpn.py never overrides, so they are the rate
# values actually in force in the published model. Read from the 3.0D-7T
# registry at construction; these names are the lookup keys.
NAT_V1_2M = "v1_2m"
NAT_KM = "km"
NAT_V1_2H = "v1_2h"
NAT_KH = "kh"
NAP_V1_2M = "v1_2m"
NAP_KM = "km"
K_V1_2M = "v1_2m"
K_KM = "km"

# The 7S authorized parameter names.
ACTIVE_G_NAT = "g_Na"
ACTIVE_G_NAP = "g_Nap"
ACTIVE_G_K = "g_K"
ACTIVE_E_NA = "E_Na"
ACTIVE_E_K = "E_K"

# The mS/cm2 -> S/cm2 conversion. Applied once, explicitly, and recorded.
_MS_TO_S = 1e-3
# The .mod current expressions are mA/cm2 when gbar is S/cm2 and (v - e) is mV.
# 1 S/cm2 * 1 mV = 1 mA/cm2 exactly, so the density form needs no scaling; the
# per-compartment current in amperes needs the membrane area in cm2, which the
# passive backend already converts. The um2 -> cm2 conversion factor is NOT
# duplicated here; it lives in one place, passive_cable.py.

# Exponent range guard. The .mod rate expressions are evaluated by NEURON's
# TABLE over vmin..vmax, which never overflows. Evaluated directly in Python
# they can, so the exponential argument is clamped to the representable double
# range. This changes NO value inside the representable range and is a
# numerical guard only, recorded as such.
_EXP_ARGUMENT_LIMIT = 700.0


SOURCE_AUGUSTIN_2019 = (
    "Augustin et al. 2019. Drosophila integrative nerve circuit for escape "
    "behavior. eLife 8:e40240. https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ . "
    "The published conductance-based GFS model inserts nat, nap, k and pas into "
    "the GF section (gfpn.py lines 133-144) with the conductance densities and "
    "reversal potentials recorded by 3.0D-7S and the verbatim mechanism source "
    "recorded by 3.0D-7T."
)

SOURCE_MODELDB_245415 = (
    "ModelDBRepository/245415, vendored under "
    "biological_brain/data/modeldb_245415/. Channels nat.mod, nap.mod and k.mod "
    "are the implementation authority for every kinetic expression in this "
    "module; gap2.mod is deliberately NOT implemented here. "
    "https://github.com/ModelDBRepository/245415"
)

SOURCE_KADAS_2019 = (
    "Kadas et al. 2019. eLife https://pmc.ncbi.nlm.nih.gov/articles/PMC6709211/ . "
    "Experimentally implicates Para, Shaker, DmCa1D and Slowpoke in GF axonal "
    "conduction. This establishes the BIOLOGICAL RELEVANCE of those channels "
    "and is recorded at 3.0D-7S; it is NOT modelled by 3.0D-8A, which "
    "reproduces the narrower Augustin mechanism set only."
)

SOURCE_MODEL_STIMULUS = (
    "MODEL-REPRODUCTION TEST FIXTURE, NOT A BIOLOGICAL STIMULUS. gfpn.py lines "
    "60-63 set stim_loc=0.0, stim_dur=0.03 ms, stim_delay=100 ms, "
    "stim_amp=120.0 nA, and construct an IClamp on the proximal GF "
    "(neuron.h.IClamp(self.GF(0.0))). This current step drives circuit-latency "
    "SIMULATIONS in the published model. It is a MODEL STIMULUS chosen by the "
    "model authors, it is not a sensory input, it is not a physiological "
    "threshold or a measurement, and 3.0D-8A uses it only to reproduce the "
    "model's own spike generation."
)


class GFActiveError(Exception):
    """Base class for GF active-mechanism failures."""


class GFActiveAuthorizationError(GFActiveError):
    """A parameter or profile that is not authorized was requested."""


class GFActiveScopeError(GFActiveError):
    """A mechanism or compartment outside 3.0D-8A scope was requested."""


class GFActiveNumericalError(GFActiveError):
    """The requested numerical configuration cannot be honoured."""


_MODEL_REPRODUCTION_SCOPE = (
    "MODEL REPRODUCTION, NOT MEASUREMENT. Every active parameter applied here is "
    "a published parameter of the Augustin et al. 2019 COMPUTATIONAL model, "
    "consumed from the 3.0D-7S authorized profile. None of them is a direct "
    "experimental measurement of the GF or of any GFS neuron, and the published "
    "active sections are largely based on a Drosophila motoneuron model with "
    "parameters manually adjusted for the GFS model. Results obtained from this "
    "layer must be reported as model-reproduction results."
)

_CHANNEL_COMPLEMENT_SCOPE = (
    "THIS IS NOT THE FULL EXPERIMENTALLY KNOWN GF ION-CHANNEL COMPLEMENT. "
    "Kadas et al. 2019 experimentally implicates Para (fast Na), Shaker (K), "
    "DmCa1D (L-type-like Ca) and Slowpoke (BK/Ca-activated K) in GF axonal "
    "conduction. 3.0D-8A implements NONE of them beyond the nat/nap/k pair of "
    "the published model: no ShakB, no DmCa1D, no Slowpoke, no calcium "
    "concentration dynamics, no Q10 and no temperature scaling appear here, and "
    "none is invented. The biological relevance of those channels is recorded at "
    "3.0D-7S and is deliberately out of scope here."
)

_NO_SYNAPSE_SCOPE = (
    "NO SYNAPSE AND NO SENSORY INPUT. 3.0D-8A activates the GF membrane only. "
    "It implements NO chemical synapse, NO Exp2Syn, NO synaptic conductance or "
    "kinetics, NO gap junction, and NO sensory transformation: 3.0D-7W, 3.0D-7X, "
    "3.0D-7Y and 3.0D-7Z are not imported, and the unresolved 3.0D-7U "
    "gap-junction unit conflict is neither touched nor resolved here."
)

_TEMPERATURE_SCOPE = (
    "NO TEMPERATURE DEPENDENCE. nat.mod, nap.mod and k.mod declare 'celsius' "
    "and never reference it; there is no Q10 and no rate scaling in the vendored "
    "source, so none is introduced. The gfs_param_scan_conductances.py sweep "
    "varies conductances only, never a temperature coefficient."
)

GF_ACTIVE_NUMERICAL_LIMITATION = (
    "SEMI-IMPLICIT, NOT FULLY IMPLICIT. The gating states are integrated by the "
    "EXACT solution of their own linear ODE with the rates frozen at the "
    "start-of-step voltage, which is the method the source files name "
    "('SOLVE states METHOD cnexp'), so the gating update itself introduces no "
    "timestep error. The membrane voltage, however, is advanced with the active "
    "conductances held CONSTANT across the step, so the coupling between the "
    "gating states and the voltage is only first-order accurate. A fully "
    "implicit treatment would need a Newton iteration on (V, m, h, mn, mk) "
    "jointly, which this architecture does not provide; 8A does not silently "
    "claim to have done it. Consequence: the action-potential PEAK is "
    "timestep-dependent, and the convergence_report() tolerance is a NUMERICAL "
    "convergence label, not a biological accuracy claim."
)

_STABILITY_NOTE = (
    "STABILITY IS NOT ACCURACY. The linearised implicit solve is "
    "unconditionally stable, and stability is a NUMERICAL property. The g_Nat "
    "density of 300 mS/cm2 with Cm = 1 uF/cm2 puts the active membrane time "
    "constant Cm/g_Nat at about 3.3 us, roughly a third of the 0.01 ms "
    "(10 us) policy timestep, which is why the explicit path cannot be used "
    "at that timestep here: the step would be several membrane time constants "
    "long and the explicit update would not be stable. The gating states, "
    "which carry the still faster kinetics, are advanced by their exact "
    "linear-ODE solution and so are not a stability concern at all. This "
    "ratio is a numerical fact about the published density at the project "
    "timestep, not a biological statement about GF kinetics, and no dt is "
    "raised to work around it."
)

# An explicitly NUMERICAL convergence label. This is NOT a biological tolerance
# and asserts nothing about the accuracy of the model relative to a real GF.
GF_ACTIVE_NUMERICAL_CONVERGENCE_TOLERANCE = (
    "NUMERICAL CONVERGENCE TOLERANCE, NOT A BIOLOGICAL TOLERANCE. Used only to "
    "report how much an action-potential peak and peak time move when the "
    "timestep is halved. It is a numerical discretization label and asserts "
    "nothing about the model's agreement with any experimental measurement."
)


def _exp_clamped(x: float) -> float:
    """``exp`` with the argument clamped to the representable double range.

    A numerical guard, NOT a change to any rate expression. Every argument
    inside (+-700, exp) is returned exactly; only arguments that would raise
    ``OverflowError`` are clamped, which is a region NEURON's TABLE over
    vmin..vmax never evaluates.
    """
    if x > _EXP_ARGUMENT_LIMIT:
        return math.exp(_EXP_ARGUMENT_LIMIT)
    if x < -_EXP_ARGUMENT_LIMIT:
        return math.exp(-_EXP_ARGUMENT_LIMIT)
    return math.exp(x)


@dataclass(frozen=True)
class GFActiveNumericalPolicy:
    """Declared numerical policy for the GF active layer (3.0D-8A).

    A SEPARATE declaration that REUSES the 3.0D-7R policy bounds rather than
    competing with them. The maximum timestep is taken from
    ``PASSIVE_CABLE_NUMERICAL_POLICY.max_timestep_ms`` so the active layer can
    never be used at a timestep the passive layer would reject, and the passive
    policy object itself is not modified.
    """

    max_timestep_ms: float
    default_timestep_ms: float
    integration_method: str
    gating_method: str
    is_fully_implicit: bool
    policy_note: str
    limitation: str

    @property
    def reuses_passive_bounds(self) -> bool:
        return True


GF_ACTIVE_NUMERICAL_POLICY = GFActiveNumericalPolicy(
    max_timestep_ms=PASSIVE_CABLE_NUMERICAL_POLICY.max_timestep_ms,
    default_timestep_ms=PASSIVE_CABLE_NUMERICAL_POLICY.default_timestep_ms,
    integration_method="linearised_implicit_backward_euler",
    gating_method="exact_linear_ode_solution_cnexp",
    is_fully_implicit=False,
    policy_note=(
        "GF active-mechanism integration. The timestep BOUNDS are reused from "
        "3.0D-7R PASSIVE_CABLE_NUMERICAL_POLICY (max "
        f"{PASSIVE_CABLE_NUMERICAL_POLICY.max_timestep_ms} ms) and that policy "
        "is NOT modified: no timestep is raised, and the engine default of 1 ms "
        "remains rejected here exactly as the passive backend rejects it. "
        "Gating states use the exact solution of their own linear ODE, which is "
        "what the vendored .mod files name as 'METHOD cnexp'. The membrane "
        "voltage uses a linearised implicit solve, so the scheme is stable but "
        "only first-order in the gating/voltage coupling. The action-potential "
        "peak is therefore timestep-dependent, and callers must run their own "
        "convergence check with convergence_report()."
    ),
    limitation=GF_ACTIVE_NUMERICAL_LIMITATION,
)

_GF_ACTIVE_RESOLUTION = NumericalResolution(
    timestep_ms=GF_ACTIVE_NUMERICAL_POLICY.default_timestep_ms,
    resolution_note=(
        GF_ACTIVE_NUMERICAL_POLICY.policy_note + " " + _STABILITY_NOTE
    ),
)


# --- the three vendored mechanisms -------------------------------------------
#
# Rate functions transcribed from the vendored .mod files. Each docstring
# quotes the verbatim source expression it implements, so the transcription is
# checkable against the file character for character in the tests.


@dataclass(frozen=True)
class NatRates:
    """nat.mod rates, transcribed verbatim.

    nat.mod lines 96-102::

        minf = 1/(1+exp((vm-v1_2m)/km))
        mtau = 0.13 + 3.43/(1+exp((vm+45.35)/5.98))
        if (mtau<1e-7) {mtau=1e-7}
        hinf = 1/(1+exp((vm-v1_2h)/kh))
        htau = 0.36 + exp((vm+20.65)/-10.47)
        if (htau<1e-7) {htau=1e-7}

    These are NOT the classic Hodgkin-Huxley time constants and are not
    replaced by them. The two ``if (tau<1e-7)`` floors are part of the source
    and are preserved.
    """

    v1_2m: float
    km: float
    v1_2h: float
    kh: float
    mtau_floor: float = 1e-7
    source_file: str = "channels/nat.mod"

    def minf(self, v_mV: float) -> float:
        return 1.0 / (1.0 + _exp_clamped((v_mV - self.v1_2m) / self.km))

    def mtau_ms(self, v_mV: float) -> float:
        tau = 0.13 + 3.43 / (1.0 + _exp_clamped((v_mV + 45.35) / 5.98))
        return tau if tau >= self.mtau_floor else self.mtau_floor

    def hinf(self, v_mV: float) -> float:
        return 1.0 / (1.0 + _exp_clamped((v_mV - self.v1_2h) / self.kh))

    def htau_ms(self, v_mV: float) -> float:
        tau = 0.36 + _exp_clamped((v_mV + 20.65) / -10.47)
        return tau if tau >= self.mtau_floor else self.mtau_floor

    def steady_state(self, v_mV: float) -> Tuple[float, float]:
        """The nat INITIAL block: 'trates(v); m = minf; h = hinf'."""
        return self.minf(v_mV), self.hinf(v_mV)


@dataclass(frozen=True)
class SingleGateRates:
    """nap.mod / k.mod rates, transcribed verbatim.

    Both files, lines 93-95::

        minf = 1/(1+exp((vm-v1_2m)/km))
        mtau = 1

    The time constant is the source CONSTANT 1 ms, independent of voltage. It
    is NOT a voltage-dependent fit, and NEITHER mechanism has an inactivation
    variable: both are steady-state conductance models in the source, which
    reproduces the published model's simplification and is not a full transient
    description of these currents.
    """

    v1_2m: float
    km: float
    mtau_ms: float = 1.0
    source_file: str = ""
    uses_floor: bool = False

    def minf(self, v_mV: float) -> float:
        return 1.0 / (1.0 + _exp_clamped((v_mV - self.v1_2m) / self.km))

    def tau_ms(self, v_mV: float) -> float:
        return self.mtau_ms

    def steady_state(self, v_mV: float) -> Tuple[float,]:
        """The INITIAL block: 'trates(v); m = minf'."""
        return (self.minf(v_mV),)


@dataclass(frozen=True)
class AppliedActiveParameter:
    """One active parameter actually applied to a GF axon segment.

    Carries an explicit distinction that the project keeps everywhere else:
    ``is_experimental_gf_measurement`` is False for every value here, because
    every one of them is a published COMPUTATIONAL model parameter.
    """

    name: str
    value: float
    unit: str
    mechanism: str
    profile_name: str
    provenance_category: ParameterProvenance
    source: str
    source_mechanism_file: str
    is_experimental_gf_measurement: bool = False
    is_model_reproduction_parameter: bool = True

    def __post_init__(self) -> None:
        if self.is_experimental_gf_measurement:
            raise ValueError(
                f"Active parameter '{self.name}' must not be recorded as a "
                f"direct experimental GF measurement. It is a published "
                f"parameter of the Augustin et al. 2019 computational model."
            )

    def limitations(self) -> str:
        return (
            f"MODEL-REPRODUCTION PARAMETER, NOT A GF MEASUREMENT. {self.source} "
            f"{_MODEL_REPRODUCTION_SCOPE} {self.provenance_category.value}"
        )


@dataclass(frozen=True)
class ActiveMechanismRecord:
    """The bound mechanism set: which .mod files this model reproduces."""

    mechanism_name: str
    source_file: str
    source_url: str
    states: Tuple[str, ...]
    conductance_expression: str
    current_expression: str
    solve_method: str
    instantiated_in_gf: bool
    equations: Tuple[str, ...]

    @property
    def has_inactivation_gate(self) -> bool:
        return len(self.states) > 1


@dataclass
class GFActiveSegmentState:
    """Mutable per-segment state: voltage and the three gating sets."""

    compartment_id: str
    voltage_mV: float
    nat_m: float
    nat_h: float
    nap_m: float
    k_m: float
    last_currents_mA_per_cm2: Dict[str, float] = field(default_factory=dict)
    last_conductances_mS_per_cm2: Dict[str, float] = field(default_factory=dict)

    def gating(self) -> Dict[str, float]:
        return {
            "nat_m": self.nat_m, "nat_h": self.nat_h,
            "nap_m": self.nap_m, "k_m": self.k_m,
        }

    def all_finite(self) -> bool:
        values = [
            self.voltage_mV, self.nat_m, self.nat_h, self.nap_m, self.k_m,
        ]
        values.extend(self.last_currents_mA_per_cm2.values())
        values.extend(self.last_conductances_mS_per_cm2.values())
        return all(v == v and abs(v) != float("inf") for v in values)


@dataclass(frozen=True)
class GFActiveNetwork:
    """A prepared GF axon active network.

    Wraps the existing 3.0D-7G ``PassiveNetwork`` and adds the active profile
    and mechanism set. Every passive electrical quantity (capacitance, leak
    conductance, leak reversal, axial resistance, membrane area) is READ from
    that network, so removing the active conductances returns exactly the
    passive behaviour and never perturbs a passive parameter.
    """

    network: PassiveNetwork
    profile: ActiveParameterProfile
    mechanisms: Tuple[ActiveMechanismRecord, ...]
    applied_parameters: Tuple[AppliedActiveParameter, ...]
    segment_ids: Tuple[str, ...]
    preparation_note: str
    scope_note: str
    #: Source sections whose membrane carries the active density channels.
    #: Compartments derived from any other section in this network are PASSIVE
    #: and receive none of the active conductances. For the 3.0D-8A GF network
    #: this is the single axon section, so every compartment is active and the
    #: 3.0D-8A behaviour is unchanged. 3.0D-8D uses it to keep the TTMn
    #: dendrites passive while the axon is active.
    active_source_section_ids: Tuple[str, ...] = ()

    @property
    def model_id(self) -> str:
        return self.network.model_id

    @property
    def segment_count(self) -> int:
        return len(self.segment_ids)

    def compartment_ids(self) -> Tuple[str, ...]:
        return self.segment_ids

    @property
    def active_compartment_ids(self) -> Tuple[str, ...]:
        """Compartment ids whose membrane carries the active channels."""
        active = set(self.active_source_section_ids)
        return tuple(
            c.compartment_id
            for c in self.network.compartments
            if c.source_section_id in active
        )

    @property
    def passive_compartment_ids(self) -> Tuple[str, ...]:
        """Compartment ids whose membrane is passive, with no active channel."""
        active = set(self.active_compartment_ids)
        return tuple(
            c.compartment_id
            for c in self.network.compartments
            if c.compartment_id not in active
        )

    def is_active(self, compartment_id: str) -> bool:
        """Does this compartment's membrane carry the active channels?"""
        return compartment_id in set(self.active_compartment_ids)


@dataclass(frozen=True)
class APDiagnostic:
    """An action-potential diagnostic derived from the generated waveform.

    ``observation_criterion`` is the rule used, and it is a WAVEFORM criterion
    computed from the trace itself, never a claimed biological GF threshold.
    """

    segment_id: str
    observed: bool
    observation_criterion: str
    rest_voltage_mV: float
    peak_voltage_mV: float
    peak_time_ms: float
    end_voltage_mV: float
    depolarization_mV: float
    all_finite: bool
    note: str


@dataclass(frozen=True)
class ActiveSegmentDiagnostic:
    """Gating variables and ionic currents for ONE ACTIVE segment.

    Every field is read off the live engine's own segment state. The
    conductances are the DENSITIES in mS/cm2 the .mod equations produce, and
    the currents are the current DENSITIES in mA/cm2, outward positive, exactly
    as 3.0D-8A reports them.

    This type is GENERIC. 3.0D-8D declared an equivalent per-neuron dataclass;
    3.0D-8E lifted it here so GF, TTMn, PSI and DLMn all report through ONE
    definition, and the per-neuron names are kept only as aliases.
    """

    segment_id: str
    voltage_mV: float
    nat_m: float
    nat_h: float
    nap_m: float
    k_m: float
    conductances_mS_per_cm2: Dict[str, float]
    currents_mA_per_cm2: Dict[str, float]

    @property
    def all_finite(self) -> bool:
        values = [
            self.voltage_mV, self.nat_m, self.nat_h, self.nap_m, self.k_m,
        ]
        values.extend(self.conductances_mS_per_cm2.values())
        values.extend(self.currents_mA_per_cm2.values())
        return all(
            value == value and abs(value) != float("inf") for value in values
        )

    @property
    def gates_in_bounds(self) -> bool:
        """Are all four gating variables inside the closed unit interval?"""
        return all(
            0.0 <= value <= 1.0
            for value in (self.nat_m, self.nat_h, self.nap_m, self.k_m)
        )


@dataclass(frozen=True)
class ActiveAxonEquilibriumReport:
    """The unstimulated numerical fixed point of a live GFS active neuron.

    The reported voltage is where this mechanism, on this geometry, with these
    authorized parameters, stops moving. It is a NUMERICAL fixed point of the
    integration. It is NOT a measured resting potential, and no biological
    tolerance is defined or implied.

    The fields are named ``axon_*`` because in EVERY configuration of this
    engine the activated section is that neuron's axon (GF_axon, TTMn_axon,
    PSI_axon, DLMn_axon), which is what the published model activates. The names
    are retained so the 3.0D-8A/8B/8D public API is unchanged.
    """

    axon_voltage_mV: float
    passive_voltages_mV: Dict[str, float]
    axon_gates: ActiveSegmentDiagnostic
    steps: int
    duration_ms: float
    timestep_ms: float
    all_finite: bool
    note: str


@dataclass(frozen=True)
class ConvergencePoint:
    """One point of a timestep-refinement convergence sweep."""

    timestep_ms: float
    peak_voltage_mV: float
    peak_time_ms: float
    all_finite: bool


@dataclass(frozen=True)
class ConvergenceReport:
    """A timestep-refinement comparison with an explicitly NUMERICAL label."""

    tolerance_label: str
    points: Tuple[ConvergencePoint, ...]
    coarsest_timestep_ms: float
    finest_timestep_ms: float
    peak_change_mV: float
    peak_time_change_ms: float
    note: str


def _mechanism_record(
    registry: ActiveMechanismRegistry, name: str, neuron_id: str = "GF"
) -> ActiveMechanismRecord:
    mechanism = registry.get(name)
    if mechanism.kind != KIND_DENSITY_CHANNEL:
        raise GFActiveScopeError(
            f"Mechanism '{name}' is a {mechanism.kind}, not a density channel. "
            f"3.0D-8A reproduces only the density channels "
            f"{list(GF_ACTIVE_MECHANISMS)}."
        )
    if mechanism.solve_method != SOLVE_METHOD_CNEXP:
        raise GFActiveScopeError(
            f"Mechanism '{name}' declares solve method "
            f"'{mechanism.solve_method}', but 3.0D-8A implements the "
            f"'{SOLVE_METHOD_CNEXP}' integration the .mod files name."
        )
    if neuron_id not in mechanism.instantiated_in:
        raise GFActiveScopeError(
            f"Mechanism '{name}' is not instantiated in {neuron_id} by the "
            f"source. The source records it in "
            f"{list(mechanism.instantiated_in)}."
        )
    return ActiveMechanismRecord(
        mechanism_name=name,
        source_file=mechanism.source_file,
        source_url=mechanism.source_url,
        states=tuple(mechanism.states),
        conductance_expression=mechanism.equation("conductance").expression,
        current_expression=mechanism.equation("current").expression,
        solve_method=mechanism.solve_method,
        instantiated_in_gf=neuron_id in mechanism.instantiated_in,
        equations=tuple(e.expression for e in mechanism.equations),
    )


class ActiveAxonModel:
    """GENERIC active-axon mechanism model for the published Augustin model.

    This is the single implementation source of the nat/nap/k mechanism used
    by every live axon in this project. The equations, the exact ``cnexp`` gate
    solution and the linearised implicit membrane solve are defined ONCE, here.
    A neuron is a CONFIGURATION of this engine, not a subclass of its own:
    ``neuron_id`` and ``active_section_id`` select which compartment model and
    which section are activated, and nothing else about the mechanism changes.

    3.0D-8A configures it for the GF axon. 3.0D-8D configures the same engine
    for the TTMn axon, leaving the TTMn dendrites passive. Neither neuron gets
    a second copy of the mechanism.
    """

    numerical_resolution = _GF_ACTIVE_RESOLUTION

    def __init__(
        self,
        profile_name: str = PROFILE_AUGUSTIN_2019_ACTIVE_MODEL,
        passive_profile_name: str = PROFILE_AUGUSTIN_2019_GFS_PASSIVE,
        timestep_ms: Optional[float] = None,
        neuron_id: str = NEURON_GF,
        active_section_id: str = GF_ACTIVE_SECTION_ID,
    ) -> None:
        try:
            self._profile: ActiveParameterProfile = (
                get_active_parameter_profile(profile_name)
            )
        except KeyError as exc:
            raise GFActiveAuthorizationError(
                f"Unknown or unauthorized active parameter profile "
                f"'{profile_name}'. No active profile is ever selected "
                f"implicitly. Available: "
                f"{list(available_active_profiles())}"
            ) from exc
        self._passive_profile_name = passive_profile_name
        # The existing 3.0D-7G backend, unchanged. It prepares the geometry, the
        # capacitance, the leak conductance and the axial resistances. 8A adds
        # no geometry and rewrites no passive quantity.
        self._passive = PassiveCableModel(
            profile_name=passive_profile_name, timestep_ms=None
        )
        self._timestep_ms = self._validate_timestep(
            GF_ACTIVE_NUMERICAL_POLICY.default_timestep_ms
            if timestep_ms is None
            else timestep_ms
        )
        self._registry = get_active_mechanism_registry()
        # Which neuron and which section this configuration activates. These
        # are the ONLY neuron-specific inputs; the mechanism is shared.
        self._neuron_id = neuron_id
        self._active_section_id = active_section_id
        self._nat_rates = self._build_nat_rates()
        self._nap_rates = self._build_nap_rates()
        self._k_rates = self._build_k_rates()

    # -- provenance ---------------------------------------------------------

    @property
    def neuron_id(self) -> str:
        """The neuron this configuration activates."""
        return self._neuron_id

    @property
    def active_section_id(self) -> str:
        """The single source section this configuration makes active."""
        return self._active_section_id

    @property
    def name(self) -> str:
        return MODEL_NAME_GF_ACTIVE_V0

    @property
    def profile(self) -> ActiveParameterProfile:
        return self._profile

    @property
    def profile_name(self) -> str:
        return self._profile.name

    @property
    def passive_profile_name(self) -> str:
        return self._passive_profile_name

    @property
    def timestep_ms(self) -> float:
        return self._timestep_ms

    @property
    def is_default(self) -> bool:
        """Always False: 8A is opt-in and is never an engine default."""
        return False

    @property
    def numerical_policy(self) -> GFActiveNumericalPolicy:
        return GF_ACTIVE_NUMERICAL_POLICY

    @property
    def is_fully_implicit(self) -> bool:
        """Always False. See GF_ACTIVE_NUMERICAL_LIMITATION."""
        return False

    @property
    def nat_rates(self) -> NatRates:
        return self._nat_rates

    @property
    def nap_rates(self) -> SingleGateRates:
        return self._nap_rates

    @property
    def k_rates(self) -> SingleGateRates:
        return self._k_rates

    @property
    def rest_voltage_mV(self) -> float:
        """The project resting convention, read from the passive profile.

        E_leak, not a hard-coded literal. The active mechanisms make this a
        legitimate INITIAL condition rather than a fixed point of the complete
        membrane, which is stated in the module docstring.
        """
        return self._passive.resolve_parameter("leak_reversal_potential")

    @property
    def passive_section_ids(self) -> Tuple[str, ...]:
        """The sections this configuration carries WITHOUT any active channel.

        Empty for the 3.0D-8A GF configuration, whose network is exactly the
        axon. A configuration whose neuron has dendrites overrides this to name
        them, and those dendrites are then carried in the SAME cable solve while
        receiving none of the three active conductances.
        """
        return ()

    @property
    def stimulus_fixture_amplitude_A(self) -> float:
        """The default direct-stimulation amplitude, in amperes.

        A NUMERICAL SOLVER FIXTURE, never a biological input. The generic
        3.0D-8A engine declares NO amplitude of its own: it reuses the published
        ModelDB GF circuit-stimulus value, which is a MODEL stimulus belonging to
        the paper's GF circuit simulation. An adapter for a neuron with no
        published stimulus value MUST override this with its own explicitly
        labelled fixture and MUST NOT borrow the GF value as a biological claim
        about that neuron.
        """
        return MODELDB_GF_STIMULUS_AMPLITUDE_A

    @property
    def stimulus_fixture_duration_ms(self) -> float:
        """The default direct-stimulation duration, in milliseconds.

        A NUMERICAL SOLVER FIXTURE, never a biological input. See
        ``stimulus_fixture_amplitude_A``.
        """
        return MODELDB_GF_STIMULUS_DURATION_MS

    def mechanism_records(self) -> Tuple[ActiveMechanismRecord, ...]:
        return tuple(
            _mechanism_record(self._registry, name, self._neuron_id)
            for name in GF_ACTIVE_MECHANISMS
        )

    # -- state queries --------------------------------------------------------

    def voltages_mV(
        self, network: GFActiveNetwork, state: Dict[str, GFActiveSegmentState]
    ) -> Dict[str, float]:
        """The voltage of EVERY prepared segment, active and passive."""
        return {
            segment_id: segment.voltage_mV for segment_id, segment in state.items()
        }

    def axon_diagnostic(
        self,
        network: GFActiveNetwork,
        state: Dict[str, GFActiveSegmentState],
        segment_index: int = 0,
    ) -> ActiveSegmentDiagnostic:
        """Gating variables and ionic currents for one ACTIVE segment."""
        active = network.active_compartment_ids
        if not active:
            raise GFActiveScopeError(
                f"The prepared {self._neuron_id} network carries no active "
                f"compartment."
            )
        segment_id = active[segment_index]
        if not network.is_active(segment_id):
            raise GFActiveScopeError(
                f"Segment '{segment_id}' is not an active compartment."
            )
        segment = state[segment_id]
        return ActiveSegmentDiagnostic(
            segment_id=segment_id,
            voltage_mV=segment.voltage_mV,
            nat_m=segment.nat_m,
            nat_h=segment.nat_h,
            nap_m=segment.nap_m,
            k_m=segment.k_m,
            conductances_mS_per_cm2=dict(segment.last_conductances_mS_per_cm2),
            currents_mA_per_cm2=dict(segment.last_currents_mA_per_cm2),
        )

    def passive_are_inert(
        self, network: GFActiveNetwork, state: Dict[str, GFActiveSegmentState]
    ) -> bool:
        """Do the passive sections carry zero active conductance and zero current?

        This is the check that the passive sections are genuinely PASSIVE, not merely
        labelled so. A passive compartment must never record a non-zero value
        for any of the three active conductance densities or any of the three
        active current densities. A key that has not been recorded yet (a state
        that has never been stepped) counts as no applied conductance, which is
        correct: nothing has been applied to it.
        """
        for segment_id in network.passive_compartment_ids:
            segment = state[segment_id]
            for mechanism in (MECHANISM_NAT, MECHANISM_NAP, MECHANISM_K):
                if segment.last_conductances_mS_per_cm2.get(mechanism, 0.0) != 0.0:
                    return False
                if segment.last_currents_mA_per_cm2.get(mechanism, 0.0) != 0.0:
                    return False
        return True

    # -- rejection ----------------------------------------------------------

    def _validate_timestep(self, timestep_ms: float) -> float:
        if timestep_ms <= 0:
            raise GFActiveNumericalError(
                f"timestep_ms must be positive, got {timestep_ms}"
            )
        if timestep_ms > GF_ACTIVE_NUMERICAL_POLICY.max_timestep_ms:
            raise GFActiveNumericalError(
                f"timestep_ms={timestep_ms} exceeds the maximum "
                f"{GF_ACTIVE_NUMERICAL_POLICY.max_timestep_ms} ms, which "
                f"{MODEL_NAME_GF_ACTIVE_V0} REUSES from "
                f"PASSIVE_CABLE_NUMERICAL_POLICY and never widens. The 3.0D-7R "
                f"policy is not modified by this layer and dt is never silently "
                f"raised. Policy: {GF_ACTIVE_NUMERICAL_POLICY.policy_note}"
            )
        return timestep_ms

    def reject_unsupported_mechanism(self, mechanism_name: str) -> None:
        """Refuse a mechanism outside 3.0D-8A scope, naming why.

        Every refusal is specific: the module is not merely absent, the reason
        it is absent is recorded, and the unresolved 3.0D-7U gap-junction unit
        conflict is explicitly not resolved here.
        """
        if mechanism_name in GF_ACTIVE_MECHANISMS:
            raise GFActiveScopeError(
                f"Mechanism '{mechanism_name}' IS implemented by "
                f"{MODEL_NAME_GF_ACTIVE_V0}."
            )
        reasons = {
            MECHANISM_GAP2: (
                "gap2.mod is NOT implemented in 3.0D-8A. It is a POINT_PROCESS "
                "with a 'vgap' pointer, not a membrane density channel, and the "
                "3.0D-7U gap-junction unit conflict is UNRESOLVED: the source "
                "carries g_gap = 135.0 nS while other records carry it in uS. "
                "3.0D-8A does not touch, resolve, convert or approximate that "
                "conflict."
            ),
            "DmCa1D": (
                "No DmCa1D mechanism exists in the vendored ModelDB source. "
                "Kadas et al. 2019 establishes its biological relevance in GF "
                "conduction; 3.0D-8A implements no Ca2+ conductance, reversal "
                "potential or calcium concentration dynamics, and invents none."
            ),
            "Slowpoke": (
                "No Slowpoke mechanism exists in the vendored ModelDB source. "
                "Kadas et al. 2019 establishes its biological relevance; "
                "3.0D-8A implements no BK/Ca-activated K conductance and "
                "invents none."
            ),
            "ShakB": (
                "No ShakB mechanism exists in the vendored ModelDB source. The "
                "published model represents its potassium current with k.mod, "
                "which is a different and non-identical kinetic description."
            ),
            "Shaker": (
                "No Shaker mechanism exists in the vendored ModelDB source. "
                "Kadas et al. 2019 establishes its biological relevance; "
                "3.0D-8A reproduces the published k.mod and does not add a "
                "Shaker-specific conductance."
            ),
            "Para": (
                "No Para mechanism exists in the vendored ModelDB source. "
                "Kadas et al. 2019 establishes its biological relevance; "
                "3.0D-8A reproduces the published nat.mod and does not add "
                "Para-specific kinetics."
            ),
            "Exp2Syn": (
                "No chemical synapse is implemented. 3.0D-8A activates the GF "
                "membrane only; 3.0D-7W synaptic parameters and mechanisms are "
                "not imported and no synaptic conductance or kinetics is created."
            ),
        }
        raise GFActiveScopeError(
            f"Mechanism '{mechanism_name}' is OUT OF SCOPE for "
            f"{MODEL_NAME_GF_ACTIVE_V0}. "
            + reasons.get(
                mechanism_name,
                "3.0D-8A implements only the vendored density channels "
                f"{list(GF_ACTIVE_MECHANISMS)}.",
            )
        )

    def _require_active_sections(
        self, network: PassiveNetwork, passive_section_ids: Tuple[str, ...]
    ) -> None:
        """Reject any network that is not exactly the requested section set.

        The published model inserts nat/nap/k into GF, PSI, DLMn and TTMn, but
        this engine activates exactly ONE section per configuration. The caller
        may additionally ask for named PASSIVE sections to be carried in the
        same network; the active section must be present either way, and the
        prepared source-section set must match exactly what was requested, so a
        network can never silently carry a section nobody asked for.
        """
        section_ids = {
            c.source_section_id for c in network.compartments
            if c.source_section_id is not None
        }
        expected = {self._active_section_id} | set(passive_section_ids)
        if section_ids != expected:
            raise GFActiveScopeError(
                f"This configuration activates '{self._active_section_id}' for "
                f"neuron '{self._neuron_id}' and requested passive section(s) "
                f"{sorted(passive_section_ids)}, but prepared network "
                f"'{network.model_id}' carries source section(s) "
                f"{sorted(section_ids)}. Active dynamics are refused unless the "
                f"prepared sections are exactly the requested set."
            )

    def _require_active_mechanisms(self, network: PassiveNetwork) -> None:
        """Reject a network carrying any axial-only or excluded structure.

        The GF axon network has no gap junction and no synapse by construction;
        this check makes that explicit rather than assumed.
        """
        for connection in network.connections:
            if "gap" in connection.derivation.lower():
                raise GFActiveScopeError(
                    f"Connection {connection.parent_id}->"
                    f"{connection.child_id} looks gap-junction related. "
                    f"3.0D-8A implements no gap junction."
                )

    # -- rates --------------------------------------------------------------

    def _mod_value(self, mechanism: str, quantity: str) -> float:
        value = self._registry.get(mechanism).quantity(quantity).value
        if value is None:
            raise GFActiveAuthorizationError(
                f"Mechanism '{mechanism}' parameter '{quantity}' has no value "
                f"in the 3.0D-7T verbatim registry."
            )
        return value

    def _build_nat_rates(self) -> NatRates:
        return NatRates(
            v1_2m=self._mod_value(MECHANISM_NAT, NAT_V1_2M),
            km=self._mod_value(MECHANISM_NAT, NAT_KM),
            v1_2h=self._mod_value(MECHANISM_NAT, NAT_V1_2H),
            kh=self._mod_value(MECHANISM_NAT, NAT_KH),
            source_file=self._registry.get(MECHANISM_NAT).source_file,
        )

    def _build_nap_rates(self) -> SingleGateRates:
        return SingleGateRates(
            v1_2m=self._mod_value(MECHANISM_NAP, NAP_V1_2M),
            km=self._mod_value(MECHANISM_NAP, NAP_KM),
            source_file=self._registry.get(MECHANISM_NAP).source_file,
        )

    def _build_k_rates(self) -> SingleGateRates:
        return SingleGateRates(
            v1_2m=self._mod_value(MECHANISM_K, K_V1_2M),
            km=self._mod_value(MECHANISM_K, K_KM),
            source_file=self._registry.get(MECHANISM_K).source_file,
        )

    def verify_against_7s_7t_7f(self) -> None:
        """Assert the mechanism values agree across 7T, 7S and 7F.

        This changes nothing and fails loudly. Where the .mod source and an
        existing project provenance record disagree, this raises with the exact
        conflict rather than silently choosing one side.
        """
        registry = self._registry
        # 7T verbatim .mod / gfpn.py instance values vs the 7S authorized
        # profile. 7T states conductance densities in S/cm2 and 7S in mS/cm2,
        # so the comparison is made on 7T's CANONICAL mS/cm2 value.
        density_links = (
            (MECHANISM_NAT, "gnatbar", ACTIVE_G_NAT),
            (MECHANISM_NAP, "gnapbar", ACTIVE_G_NAP),
            (MECHANISM_K, "gkbar", ACTIVE_G_K),
        )
        for mechanism_name, source_name, profile_name in density_links:
            quantity = registry.get(mechanism_name).quantity(source_name)
            authorized = self._profile.get(profile_name)
            if quantity.canonical_value != authorized.value:
                raise GFActiveAuthorizationError(
                    f"SOURCE CONFLICT for '{profile_name}': 3.0D-7T records "
                    f"{quantity.canonical_value} {quantity.canonical_unit} from "
                    f"{quantity.source_file} line {quantity.source_line}, while "
                    f"the 3.0D-7S authorized profile holds {authorized.value} "
                    f"{authorized.unit}. The conflict is reported, not resolved."
                )
            if quantity.canonical_unit != authorized.unit:
                raise GFActiveAuthorizationError(
                    f"UNIT CONFLICT for '{profile_name}': 3.0D-7T canonical unit "
                    f"'{quantity.canonical_unit}' vs 3.0D-7S unit "
                    f"'{authorized.unit}'. The conflict is reported, not "
                    f"resolved."
                )
        for mechanism_name, source_name, profile_name in (
            (MECHANISM_NAT, "ena", ACTIVE_E_NA),
            (MECHANISM_K, "ek", ACTIVE_E_K),
        ):
            quantity = registry.get(mechanism_name).quantity(source_name)
            authorized = self._profile.get(profile_name)
            if quantity.value != authorized.value:
                raise GFActiveAuthorizationError(
                    f"SOURCE CONFLICT for '{profile_name}': 3.0D-7T records "
                    f"{quantity.value} {quantity.source_unit} vs 3.0D-7S "
                    f"{authorized.value} {authorized.unit}. The conflict is "
                    f"reported, not resolved."
                )
        # The pas instance values are the 7F passive profile's leak parameters.
        pas = registry.get("pas")
        for source_name, passive_name in (
            ("gleak", "leak_conductance_density"),
            ("Eleak", "leak_reversal_potential"),
        ):
            quantity = pas.quantity(source_name)
            passive_value = self._passive.resolve_parameter(passive_name)
            canonical = (
                quantity.canonical_value
                if quantity.canonical_value is not None else quantity.value
            )
            if canonical != passive_value:
                raise GFActiveAuthorizationError(
                    f"SOURCE CONFLICT for '{passive_name}': 3.0D-7T records "
                    f"{canonical} from {quantity.source_file} line "
                    f"{quantity.source_line} vs the 3.0D-7F authorized passive "
                    f"profile value {passive_value}. The conflict is reported, "
                    f"not resolved."
                )
        # 7S must still be on record as a model-reproduction authorization.
        if not self._profile.model_reproduction_only:
            raise GFActiveAuthorizationError(
                f"Active profile '{self._profile.name}' is no longer recorded as "
                f"model-reproduction-only. 3.0D-8A consumes it strictly as a "
                f"model-reproduction authorization."
            )

    # -- preparation --------------------------------------------------------

    def prepare(
        self,
        model: CompartmentModel,
        segment_count: int = 1,
        passive_section_ids: Tuple[str, ...] = (),
    ) -> GFActiveNetwork:
        """Prepare the active network for this configuration's section.

        Geometry, capacitance, leak conductance and axial resistances come from
        the existing 3.0D-7G prepared network and are not re-derived.
        ``segment_count`` is a NUMERICAL discretization, exactly as at 3.0D-7K;
        the default of 1 reproduces the un-subdivided behaviour.

        ``passive_section_ids`` names sections to carry in the SAME network
        WITHOUT any active channel, each at its un-subdivided default. The
        3.0D-8A GF configuration passes none, so its network is exactly the
        axon and its behaviour is unchanged.
        """
        if model.neuron_id != self._neuron_id:
            raise GFActiveScopeError(
                f"CompartmentModel '{model.neuron_id}' is not "
                f"'{self._neuron_id}', which is the neuron this configuration "
                f"activates. Active dynamics are refused for a model this "
                f"configuration was not built for."
            )
        if segment_count < 1:
            raise GFActiveNumericalError(
                f"segment_count must be >= 1, got {segment_count}"
            )
        from ..subdivision import SubdivisionPlan, SectionSubdivision

        unknown = [
            section for section in passive_section_ids
            if section not in model.compartments
        ]
        if unknown:
            raise GFActiveScopeError(
                f"Requested passive section(s) {unknown} are not compartments "
                f"of '{model.neuron_id}'. Available: {sorted(model.compartments)}"
            )
        plan = SubdivisionPlan(
            sections=(
                (SectionSubdivision(self._active_section_id, segment_count),)
                + tuple(
                    SectionSubdivision(section, 1)
                    for section in passive_section_ids
                )
            )
        )
        passive_network = self._passive.prepare(model, plan)
        self._require_active_sections(passive_network, tuple(passive_section_ids))
        self._require_active_mechanisms(passive_network)
        self.verify_against_7s_7t_7f()

        applied = self._applied_parameters()
        active_count = sum(
            1 for c in passive_network.compartments
            if c.source_section_id == self._active_section_id
        )
        return GFActiveNetwork(
            network=passive_network,
            profile=self._profile,
            mechanisms=self.mechanism_records(),
            applied_parameters=applied,
            segment_ids=tuple(
                c.compartment_id for c in passive_network.compartments
            ),
            preparation_note=(
                f"{self._neuron_id} active network prepared at segment_count="
                f"{segment_count} (a NUMERICAL discretization, per 3.0D-7K, not "
                f"a biological claim; the default 1 reproduces the "
                f"un-subdivided behaviour). {len(passive_network.compartments)} "
                f"electrical segment(s), of which {active_count} derive from the "
                f"active source section "
                f"'{self._active_section_id}' and the remaining "
                f"{len(passive_network.compartments) - active_count} are "
                f"PASSIVE, carrying no active channel. Every passive quantity "
                f"(capacitance, leak conductance, leak reversal, axial "
                f"resistance, membrane area) is READ from the existing 3.0D-7G "
                f"prepared network under passive profile "
                f"'{self._passive_profile_name}' and is not re-derived here. "
                f"The active conductances come from the 3.0D-7S authorized "
                f"profile '{self._profile.name}'; the mechanism equations come "
                f"from the vendored .mod files recorded verbatim at 3.0D-7T."
            ),
            scope_note=" ".join((
                _MODEL_REPRODUCTION_SCOPE, _CHANNEL_COMPLEMENT_SCOPE,
                _NO_SYNAPSE_SCOPE, _TEMPERATURE_SCOPE,
                GF_ACTIVE_NUMERICAL_LIMITATION,
            )),
            active_source_section_ids=(self._active_section_id,),
        )

    def _applied_parameters(self) -> Tuple[AppliedActiveParameter, ...]:
        """Resolve the five authorized active parameters, converting units.

        Exactly one conversion is applied, S/cm2 <- mS/cm2, and the profile
        record itself is never rewritten.
        """
        applied: List[AppliedActiveParameter] = []
        for name, mechanism in (
            (ACTIVE_G_NAT, MECHANISM_NAT),
            (ACTIVE_G_NAP, MECHANISM_NAP),
            (ACTIVE_G_K, MECHANISM_K),
        ):
            record = self._profile.get(name)
            if record.unit != "mS/cm2":
                raise GFActiveAuthorizationError(
                    f"Active parameter '{name}' has unit '{record.unit}'; the "
                    f"authorized conductance density unit is 'mS/cm2'. No unit "
                    f"is guessed."
                )
            if record.authorization_scope != AUTHORIZATION_SCOPE_MODEL_REPRODUCTION:
                raise GFActiveAuthorizationError(
                    f"Active parameter '{name}' has authorization scope "
                    f"'{record.authorization_scope}', not "
                    f"'{AUTHORIZATION_SCOPE_MODEL_REPRODUCTION}'. 3.0D-8A "
                    f"consumes 7S strictly as a model-reproduction "
                    f"authorization."
                )
            applied.append(
                AppliedActiveParameter(
                    name=name,
                    value=record.value * _MS_TO_S,
                    unit="S/cm2",
                    mechanism=mechanism,
                    profile_name=self._profile.name,
                    provenance_category=record.provenance_category,
                    source=record.source,
                    source_mechanism_file=(
                        self._registry.get(mechanism).source_file
                    ),
                )
            )
        for name, mechanism in (
            (ACTIVE_E_NA, MECHANISM_NAT),
            (ACTIVE_E_K, MECHANISM_K),
        ):
            record = self._profile.get(name)
            if record.unit != "mV":
                raise GFActiveAuthorizationError(
                    f"Active parameter '{name}' has unit '{record.unit}'; the "
                    f"authorized reversal-potential unit is 'mV'."
                )
            applied.append(
                AppliedActiveParameter(
                    name=name,
                    value=record.value,
                    unit="mV",
                    mechanism=mechanism,
                    profile_name=self._profile.name,
                    provenance_category=record.provenance_category,
                    source=record.source,
                    source_mechanism_file=(
                        self._registry.get(mechanism).source_file
                    ),
                )
            )
        return tuple(applied)

    # -- state --------------------------------------------------------------

    def initial_state(self, active_network: GFActiveNetwork) -> Dict[str, GFActiveSegmentState]:
        """Initialise V to E_leak and every gate to its steady state at V.

        This is exactly what the three INITIAL blocks do; no gating variable is
        assigned an arbitrary value.
        """
        v0 = self.rest_voltage_mV
        state: Dict[str, GFActiveSegmentState] = {}
        for compartment_id in active_network.segment_ids:
            nat_m, nat_h = self._nat_rates.steady_state(v0)
            (nap_m,) = self._nap_rates.steady_state(v0)
            (k_m,) = self._k_rates.steady_state(v0)
            state[compartment_id] = GFActiveSegmentState(
                compartment_id=compartment_id,
                voltage_mV=v0,
                nat_m=nat_m,
                nat_h=nat_h,
                nap_m=nap_m,
                k_m=k_m,
            )
        return state

    # -- the step -----------------------------------------------------------

    def _active_currents(
        self,
        segment: GFActiveSegmentState,
        electrical: CompartmentElectrical,
        applied: Dict[str, float],
        area_cm2: float,
    ) -> Dict[str, float]:
        """Evaluate the three .mod current expressions as CURRENT DENSITIES.

        Returned in mA/cm2, outward positive, which is the sign convention of
        the existing passive backend. ``1 S/cm2 * 1 mV = 1 mA/cm2`` exactly, so
        the density expressions need no unit factor; the per-compartment
        amperes are formed by multiplying by the membrane area.
        """
        v = segment.voltage_mV
        g_nat = applied[ACTIVE_G_NAT] * segment.nat_m ** 3 * segment.nat_h
        g_nap = applied[ACTIVE_G_NAP] * segment.nap_m
        g_k = applied[ACTIVE_G_K] * segment.k_m
        return {
            "nat": g_nat * (v - applied[ACTIVE_E_NA]),
            "nap": g_nap * (v - applied[ACTIVE_E_NA]),
            "k": g_k * (v - applied[ACTIVE_E_K]),
        }

    def step(
        self,
        active_network: GFActiveNetwork,
        state: Dict[str, GFActiveSegmentState],
        injected_currents_A: Optional[Dict[str, float]] = None,
        timestep_ms: Optional[float] = None,
    ) -> Dict[str, float]:
        """Advance the GF active network by one semi-implicit step.

        Order of operations, which IS the method:

        1. Every gate is advanced by the EXACT solution of its own linear ODE
           with the rates frozen at the start-of-step voltage (the source's
           ``METHOD cnexp``). This is exact for the gate and independent of dt.
        2. The resulting conductances are held CONSTANT across the step and the
           membrane equation is solved IMPLICITLY, assembling the same matrix
           structure the 3.0D-7G backward Euler path uses, with the active
           conductances added to the diagonal and their reversal terms moved
           to the right-hand side.

        Returns the per-segment net current in amperes (outward positive).
        """
        dt_ms = self._validate_timestep(
            self._timestep_ms if timestep_ms is None else timestep_ms
        )
        dt_s = dt_ms * 1e-3
        network = active_network.network
        injected = injected_currents_A or {}
        applied = {
            p.name: p.value for p in active_network.applied_parameters
        }

        # -- 1. exact gate advance at the frozen start-of-step voltage
        for segment in state.values():
            v = segment.voltage_mV
            for gate, rates, tau_name in (
                ("nat_m", self._nat_rates, "mtau_ms"),
                ("nat_h", self._nat_rates, "htau_ms"),
                ("nap_m", self._nap_rates, "tau_ms"),
                ("k_m", self._k_rates, "tau_ms"),
            ):
                if gate == "nat_m":
                    target, tau = rates.minf(v), rates.mtau_ms(v)
                elif gate == "nat_h":
                    target, tau = rates.hinf(v), rates.htau_ms(v)
                else:
                    target, tau = rates.minf(v), rates.tau_ms(v)
                setattr(segment, gate, _advance_linear(target, getattr(segment, gate), tau, dt_ms))

        # -- 2. linearised implicit membrane solve
        compartments = network.compartments
        index = {
            c.compartment_id: i for i, c in enumerate(compartments)
        }
        size = len(compartments)
        matrix = [[0.0] * size for _ in range(size)]
        rhs = [0.0] * size

        for i, compartment in enumerate(compartments):
            segment = state[compartment.compartment_id]
            area_cm2 = compartment.membrane_area_cm2
            # A PASSIVE compartment receives NONE of the active conductances.
            # For the 3.0D-8A GF network every compartment is active, so this
            # is True throughout and the 3.0D-8A arithmetic is unchanged.
            if active_network.is_active(compartment.compartment_id):
                currents = self._active_currents(
                    segment, compartment, applied, area_cm2
                )
                g_nat_mS = (
                    applied[ACTIVE_G_NAT] * segment.nat_m ** 3 * segment.nat_h
                ) * 1e3
                g_nap_mS = (applied[ACTIVE_G_NAP] * segment.nap_m) * 1e3
                g_k_mS = applied[ACTIVE_G_K] * segment.k_m * 1e3
                # Total linearised conductance in S: leak + the three active.
                g_nat_S = (
                    applied[ACTIVE_G_NAT]
                    * segment.nat_m ** 3 * segment.nat_h * area_cm2
                )
                g_nap_S = applied[ACTIVE_G_NAP] * segment.nap_m * area_cm2
                g_k_S = applied[ACTIVE_G_K] * segment.k_m * area_cm2
            else:
                currents = {
                    MECHANISM_NAT: 0.0, MECHANISM_NAP: 0.0, MECHANISM_K: 0.0,
                }
                g_nat_mS = g_nap_mS = g_k_mS = 0.0
                g_nat_S = g_nap_S = g_k_S = 0.0
            segment.last_currents_mA_per_cm2 = {
                name: value for name, value in currents.items()
            }
            # Conductive densities, recorded for diagnostics. The leak
            # conductance is the existing passive one, unchanged.
            segment.last_conductances_mS_per_cm2 = {
                MECHANISM_NAT: g_nat_mS,
                MECHANISM_NAP: g_nap_mS,
                MECHANISM_K: g_k_mS,
                "leak": compartment.leak_conductance_S
                / max(area_cm2, 1e-300) * 1e3,
            }
            g_total_S = (
                compartment.leak_conductance_S + g_nat_S + g_nap_S + g_k_S
            )
            matrix[i][i] = compartment.capacitance_F / dt_s + g_total_S
            rhs[i] = (
                (compartment.capacitance_F / dt_s)
                * (segment.voltage_mV * 1e-3)
                + compartment.leak_conductance_S
                * (compartment.leak_reversal_mV * 1e-3)
                + (g_nat_S + g_nap_S) * (applied[ACTIVE_E_NA] * 1e-3)
                + g_k_S * (applied[ACTIVE_E_K] * 1e-3)
                + injected.get(compartment.compartment_id, 0.0)
            )

        for connection in network.connections:
            conductance = 1.0 / connection.resistance_ohm
            i = index[connection.parent_id]
            j = index[connection.child_id]
            matrix[i][i] += conductance
            matrix[j][j] += conductance
            matrix[i][j] -= conductance
            matrix[j][i] -= conductance

        lu, pivots = _lu_factor(matrix, network.model_id)
        solved_V = _lu_solve(lu, pivots, rhs)

        net_current: Dict[str, float] = {}
        for i, compartment in enumerate(compartments):
            segment = state[compartment.compartment_id]
            previous = segment.voltage_mV * 1e-3
            segment.voltage_mV = solved_V[i] * 1e3
            net_current[compartment.compartment_id] = (
                compartment.capacitance_F / dt_s
            ) * (solved_V[i] - previous)
        return net_current

    # -- diagnostics --------------------------------------------------------

    def trace(
        self,
        active_network: GFActiveNetwork,
        segment_id: str,
        duration_ms: float,
        amplitude_A: float = 0.0,
        amplitude_duration_ms: float = 0.0,
        onset_ms: float = 0.0,
        timestep_ms: Optional[float] = None,
    ) -> List[float]:
        """Run from the declared initial state and return the voltage trace.

        ``amplitude_A`` is an INJECTED MODEL CURRENT for reproduction testing,
        not a synaptic or sensory input. ``amplitude_A = 0`` is a valid resting
        run.
        """
        if segment_id not in active_network.segment_ids:
            raise KeyError(
                f"Segment '{segment_id}' is not part of the prepared GF axon "
                f"active network {active_network.segment_ids}"
            )
        if onset_ms < 0 or amplitude_duration_ms < 0 or amplitude_duration_ms > duration_ms:
            raise GFActiveNumericalError(
                f"Invalid stimulus window: onset_ms={onset_ms}, "
                f"amplitude_duration_ms={amplitude_duration_ms}, "
                f"duration_ms={duration_ms}."
            )
        dt_ms = self._validate_timestep(
            self._timestep_ms if timestep_ms is None else timestep_ms
        )
        state = self.initial_state(active_network)
        steps = int(round(duration_ms / dt_ms))
        on_steps = int(round(amplitude_duration_ms / dt_ms))
        onset_steps = int(round(onset_ms / dt_ms))
        trace: List[float] = []
        for k in range(steps):
            injected: Dict[str, float] = {}
            if on_steps and onset_steps <= k < onset_steps + on_steps:
                injected[segment_id] = amplitude_A
            self.step(active_network, state, injected_currents_A=injected,
                      timestep_ms=dt_ms)
            trace.append(state[segment_id].voltage_mV)
        return trace

    def ap_diagnostic(
        self,
        trace: Tuple[float, ...],
        timestep_ms: float,
        segment_id: str,
        observation_floor_mV: float = 0.0,
        reference_voltage_mV: Optional[float] = None,
    ) -> APDiagnostic:
        """Diagnose an action potential from the GENERATED WAVEFORM.

        The observation rule is a WAVEFORM criterion, evaluated against an
        explicit REFERENCE voltage supplied by the caller (by default this
        module's declared rest voltage, ``E_leak``). The trace counts as
        spiking when it (a) rises at least ``observation_floor_mV`` above the
        reference and (b) subsequently falls back to within
        ``observation_floor_mV`` of the reference, i.e. it repolarises.

        The reference is NOT a biological GF threshold: it is a declared
        simulation rest voltage already used to initialise every compartment,
        and the floor is a TEST OBSERVATION LEVEL. No threshold voltage, no
        rheobase and no spike-initiation mechanism is defined or implied here.
        The reference is never read back off the trace, so a trace that is
        still recovering at the end of the window cannot silently define its
        own baseline.
        """
        if not trace:
            raise ValueError("Cannot diagnose an action potential in an empty trace")
        reference = (
            self.rest_voltage_mV
            if reference_voltage_mV is None
            else reference_voltage_mV
        )
        peak = max(trace)
        peak_index = trace.index(peak)
        trough = min(trace[peak_index:]) if peak_index < len(trace) else trace[-1]
        depolarization = peak - reference
        repolarization = peak - trough
        all_finite = all(
            v == v and abs(v) != float("inf") for v in trace
        )
        observed = (
            all_finite
            and depolarization >= observation_floor_mV
            and repolarization >= observation_floor_mV
        )
        return APDiagnostic(
            segment_id=segment_id,
            observed=observed,
            observation_criterion=(
                f"WAVEFORM-DERIVED TEST OBSERVATION, NOT A BIOLOGICAL GF "
                f"THRESHOLD. The trace counts as spiking when it depolarises at "
                f"least {observation_floor_mV} mV above the supplied reference "
                f"voltage of {reference} mV AND subsequently repolarises by at "
                f"least {observation_floor_mV} mV from that peak. The reference "
                f"is a declared simulation rest voltage, never a measured "
                f"threshold; it is supplied by the caller, not read off the "
                f"trace. No threshold voltage, no rheobase and no "
                f"spike-initiation mechanism is defined or implied by this "
                f"criterion."
            ),
            rest_voltage_mV=reference,
            peak_voltage_mV=peak,
            peak_time_ms=peak_index * timestep_ms,
            end_voltage_mV=trace[-1],
            depolarization_mV=depolarization,
            all_finite=all_finite,
            note=(
                f"Numerical diagnostic of a reproduced model waveform. The peak "
                f"and peak time are timestep-dependent because the membrane is "
                f"advanced by a linearised implicit step, not a fully implicit "
                f"Newton solve; see GF_ACTIVE_NUMERICAL_LIMITATION."
            ),
        )

    def convergence_report(
        self,
        active_network: GFActiveNetwork,
        segment_id: str,
        timesteps_ms: Tuple[float, ...],
        duration_ms: float,
        amplitude_A: float = 0.0,
        amplitude_duration_ms: float = 0.0,
    ) -> ConvergenceReport:
        """Compare AP peak and peak time across a timestep refinement.

        The tolerance is labelled NUMERICAL. This reports discretisation
        behaviour and asserts nothing about biological accuracy.
        """
        points: List[ConvergencePoint] = []
        for dt in timesteps_ms:
            trace = tuple(
                self.trace(
                    active_network, segment_id, duration_ms,
                    amplitude_A=amplitude_A,
                    amplitude_duration_ms=amplitude_duration_ms,
                    timestep_ms=dt,
                )
            )
            diagnostic = self.ap_diagnostic(
                trace, dt, segment_id,
                reference_voltage_mV=self.rest_voltage_mV,
            )
            points.append(
                ConvergencePoint(
                    timestep_ms=dt,
                    peak_voltage_mV=diagnostic.peak_voltage_mV,
                    peak_time_ms=diagnostic.peak_time_ms,
                    all_finite=diagnostic.all_finite,
                )
            )
        coarsest, finest = points[0], points[-1]
        return ConvergenceReport(
            tolerance_label=GF_ACTIVE_NUMERICAL_CONVERGENCE_TOLERANCE,
            points=tuple(points),
            coarsest_timestep_ms=coarsest.timestep_ms,
            finest_timestep_ms=finest.timestep_ms,
            peak_change_mV=abs(finest.peak_voltage_mV - coarsest.peak_voltage_mV),
            peak_time_change_ms=abs(finest.peak_time_ms - coarsest.peak_time_ms),
            note=(
                f"Reported as a NUMERICAL discretisation sweep. A non-zero peak "
                f"change under refinement is the expected signature of the "
                f"first-order linearised implicit step and is NOT evidence of "
                f"biological inaccuracy, nor is its absence evidence of "
                f"biological accuracy. No biological tolerance is defined or "
                f"invented here."
            ),
        )

    # -- generic runs ---------------------------------------------------------
    #
    # 3.0D-8E lifted these two runs onto the GENERIC engine. 3.0D-8D left them
    # on the TTMn adapter, which meant they were written for one neuron and had
    # to be copied for the next. They are neuron-agnostic: the only neuron-
    # specific inputs are ``self.neuron_id``, ``self.passive_section_ids`` and
    # the adapter-declared stimulation FIXTURE, none of which changes a single
    # numerical equation. There is exactly ONE implementation of each, here.

    def prepare_active_axon(
        self, model: CompartmentModel, segment_count: int = 1
    ) -> GFActiveNetwork:
        """Prepare the configured active axon plus this neuron's passive sections.

        The generic entry point every run uses. ``segment_count`` subdivides the
        ACTIVE AXON only; the passive sections are carried at their
        un-subdivided default, which is the existing 3.0D-7K behaviour for a
        section that is not being resolved.
        """
        return self.prepare(
            model,
            segment_count=segment_count,
            passive_section_ids=self.passive_section_ids,
        )

    def equilibrium_report(
        self,
        model: CompartmentModel,
        segment_count: int = 11,
        duration_ms: float = 200.0,
        timestep_ms: Optional[float] = None,
    ) -> ActiveAxonEquilibriumReport:
        """Integrate UNSTIMULATED to its own numerical fixed point.

        No voltage is forced and no gating variable is invented. The active
        axon and any passive sections are initialised by the same 8A
        initialization policy (rest voltage read from the 7F passive profile,
        gates at their own steady state there) and are then allowed to find
        their own equilibrium. The result is a NUMERICAL fixed point of the
        integration, never a measured resting potential.
        """
        network = self.prepare_active_axon(model, segment_count=segment_count)
        state = self.initial_state(network)
        dt_ms = self._validate_timestep(
            self._timestep_ms if timestep_ms is None else timestep_ms
        )
        steps = int(round(duration_ms / dt_ms))
        for _ in range(steps):
            self.step(network, state, timestep_ms=dt_ms)

        diagnostic = self.axon_diagnostic(network, state)
        voltages = self.voltages_mV(network, state)
        passive = {
            segment_id: voltages[segment_id]
            for segment_id in network.passive_compartment_ids
        }
        return ActiveAxonEquilibriumReport(
            axon_voltage_mV=diagnostic.voltage_mV,
            passive_voltages_mV=passive,
            axon_gates=diagnostic,
            steps=steps,
            duration_ms=steps * dt_ms,
            timestep_ms=dt_ms,
            all_finite=(
                diagnostic.all_finite
                and all(
                    value == value and abs(value) != float("inf")
                    for value in passive.values()
                )
            ),
            note=(
                f"NUMERICAL FIXED POINT OF THE INTEGRATION, NOT A MEASURED "
                f"{self._neuron_id} RESTING POTENTIAL. No voltage is forced to "
                f"this value and no biological tolerance is defined or implied. "
                f"The value depends on the published model parameters, which are "
                f"computational parameters and not direct {self._neuron_id} "
                f"measurements."
            ),
        )

    def stimulus_response(
        self,
        model: CompartmentModel,
        segment_count: int = 11,
        duration_ms: float = 3.0,
        timestep_ms: Optional[float] = None,
        amplitude_A: Optional[float] = None,
        amplitude_duration_ms: Optional[float] = None,
        observation_floor_mV: float = 40.0,
    ) -> Tuple[Tuple[float, ...], APDiagnostic, GFActiveNetwork]:
        """Run this neuron's labelled direct-stimulation fixture.

        The stimulus is the NUMERICAL SOLVER FIXTURE the adapter declares in
        ``stimulus_fixture_amplitude_A`` / ``stimulus_fixture_duration_ms``,
        overridable per call. It is injected into the PROXIMAL ACTIVE AXON
        segment. It is a SOLVER FIXTURE, NOT a biological input: it is not a
        rheobase, not a spike threshold and not a measurement, and the waveform
        criterion is a numerical observation rule rather than a biological
        threshold. No such value is invented here; each adapter must name the
        provenance of its own fixture.
        """
        if amplitude_A is None:
            amplitude_A = self.stimulus_fixture_amplitude_A
        if amplitude_duration_ms is None:
            amplitude_duration_ms = self.stimulus_fixture_duration_ms
        network = self.prepare_active_axon(model, segment_count=segment_count)
        state = self.initial_state(network)
        dt_ms = self._validate_timestep(
            self._timestep_ms if timestep_ms is None else timestep_ms
        )
        target = network.active_compartment_ids[0]
        on_steps = int(round(amplitude_duration_ms / dt_ms))
        steps = int(round(duration_ms / dt_ms))

        trace = []
        for index in range(steps):
            self.step(
                network, state,
                injected_currents_A=(
                    {target: amplitude_A} if index < on_steps else {}
                ),
                timestep_ms=dt_ms,
            )
            trace.append(state[target].voltage_mV)

        diagnostic = self.ap_diagnostic(
            tuple(trace), dt_ms, target,
            observation_floor_mV=observation_floor_mV,
        )
        return tuple(trace), diagnostic, network

    # -- passive-equivalence control ----------------------------------------

    def with_active_conductances_removed(
        self, network: GFActiveNetwork
    ) -> GFActiveNetwork:
        """A diagnostic copy of ``network`` with the three conductances zeroed.

        Zeroing the three active CONDUCTANCES and leaving the two reversal
        potentials untouched reduces the membrane equation to the 3.0D-7G
        passive one exactly, so the result can be compared against the passive
        backend. This is a DIAGNOSTIC CONTROL, not a supported configuration and
        not a default: it is reachable only by explicitly asking for it, and it
        changes no passive quantity.
        """
        zeroed = tuple(
            replace(parameter, value=0.0)
            if parameter.name
            in (ACTIVE_G_NAT, ACTIVE_G_NAP, ACTIVE_G_K)
            else parameter
            for parameter in network.applied_parameters
        )
        return replace(network, applied_parameters=zeroed)

    def verify_against_7s_7t_7f_and_report(self) -> Dict[str, object]:
        """Run the cross-layer verification and return what was confirmed."""
        self.verify_against_7s_7t_7f()
        return {
            "profile": self._profile.name,
            "passive_profile": self._passive_profile_name,
            "mechanisms": [r.mechanism_name for r in self.mechanism_records()],
            "active_parameters": {
                p.name: (p.value, p.unit) for p in self._applied_parameters()
            },
            "rest_voltage_mV": self.rest_voltage_mV,
            "timestep_ms": self._timestep_ms,
            "fully_implicit": False,
            "scope": active_network_scope_note(),
        }


class GFActiveAxonModel(ActiveAxonModel):
    """3.0D-8A COMPATIBILITY ADAPTER: the live GF axon.

    This is the 3.0D-8A public API, unchanged. It is a thin configuration of the
    generic :class:`ActiveAxonModel` engine, pinning the neuron to the GF and
    the activated section to the GF axon, and it does not define, override or
    duplicate any mechanism. The equations, the exact gate solution and the
    membrane solve all live in the engine, once.
    """

    def __init__(
        self,
        profile_name: str = PROFILE_AUGUSTIN_2019_ACTIVE_MODEL,
        passive_profile_name: str = PROFILE_AUGUSTIN_2019_GFS_PASSIVE,
        timestep_ms: Optional[float] = None,
    ) -> None:
        super().__init__(
            profile_name=profile_name,
            passive_profile_name=passive_profile_name,
            timestep_ms=timestep_ms,
            neuron_id=NEURON_GF,
            active_section_id=GF_ACTIVE_SECTION_ID,
        )


def _advance_linear(target: float, current: float, tau_ms: float, dt_ms: float) -> float:
    """Exact advance of ``x' = (target - x)/tau`` over ``dt``.

    This is the closed-form solution of the linear ODE the three .mod files
    define, with ``target`` and ``tau`` held at their start-of-step values, and
    is the method the source names as ``cnexp``. Because the gate equation is
    linear with frozen coefficients, this introduces NO timestep error for the
    gating variables themselves.
    """
    if tau_ms <= 0:
        raise GFActiveNumericalError(
            f"A gating time constant of {tau_ms} ms is not positive."
        )
    return target + (current - target) * _exp_clamped(-dt_ms / tau_ms)


def active_network_scope_note() -> str:
    return " ".join((
        _MODEL_REPRODUCTION_SCOPE, _CHANNEL_COMPLEMENT_SCOPE, _NO_SYNAPSE_SCOPE,
        _TEMPERATURE_SCOPE, GF_ACTIVE_NUMERICAL_LIMITATION, _STABILITY_NOTE,
        SOURCE_MODEL_STIMULUS,
    ))


#: The published model's own circuit-latency stimulus, as a MODEL STIMULUS.
#: gfpn.py lines 60-63. It is a reproduction fixture for the model authors'
#: latency simulation, NOT a biological stimulus, NOT a sensory input and NOT
#: a threshold.
MODELDB_GF_STIMULUS_AMPLITUDE_A = 120.0e-9
MODELDB_GF_STIMULUS_DURATION_MS = 0.03
MODELDB_GF_STIMULUS_LOCATION = 0.0
MODELDB_GF_STIMULUS_SOURCE = SOURCE_MODEL_STIMULUS
