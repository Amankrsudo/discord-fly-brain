"""Published Ache et al. 2019 sensory->GF phenomenological model (3.0D-8H).

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
3.0D-7Y specified the visual input END of the giant fiber pathway: LC4 as the
angular-velocity projection neuron, LPLC2 as the angular-size projection
neuron, both directly presynaptic to the GF, and the published GF looming
response as a MODEL. 7Y deliberately carried no numbers: the record types there
refuse to hold a coefficient, and the ``PhenomenologicalModelTerm`` refuses to
claim the equation is available.

3.0D-8H supplies those numbers. It implements the four-component Ache et al.
2019 model of the GF looming response QUANTITATIVELY, as a deterministic,
pure, side-effect-free evaluation of published functions of stimulus
coordinates.

THIS IS NOT A SYNAPSE, AND IT DRIVES NO MEMBRANE
-------------------------------------------------
The single most important property of this module is what it is NOT. The
component amplitudes are in MILLIVOLTS because the published model expresses
them in millivolts, and that is the ONLY reason. They are:

    NOT synaptic conductances
    NOT currents
    NOT a conversion of either
    NOT a claim about LC4 or LPLC2 membrane voltage
    NOT the voltage state of the live GFActiveAxonModel

The published model is a fit to a stimulus-response relationship. It says the
GF response is a weighted sum of a linear function of angular velocity and
three functions of angular size. It says nothing about what current that
corresponds to, through which receptor, with what reversal potential.

This module therefore has NO conductance field, NO current field, NO reversal
potential, NO receptor, NO release probability, NO vesicle pool, NO calcium,
NO Q10 and NO stochastic term, and it imports neither ``gf_active`` nor
``chemical_synapse`` nor ``electrical_coupling`` nor any membrane solver. It
cannot be handed to ``ActiveAxonModel.step``: it is not a state vector and not
a current. Converting it into one is a SEPARATE research question with no
defensible source-backed answer yet, and 8H deliberately leaves that boundary
open rather than crossing it with an invented conversion such as
"1 mV of drive = X nA".

NAMING: WHY THIS IS NOT CALLED "GF MEMBRANE VOLTAGE"
----------------------------------------------------
Ache et al. 2019 and the later paper that reproduces the model verbatim both
NOTATE the combined output as ``vGF`` and describe it as the "GF membrane
potential (Vm)". This project deliberately does NOT reuse that name, because
this project has a LIVE GF whose membrane potential IS simulated, and two
different things must not share one name. The output here is called
``weighted_gf_drive``. :attr:`PhenomenologicalGFDrive.
phenomenological_gf_model_output_mV` is available as an explicitly labelled
alias, and its docstring states what it is. The naming divergence from the
paper is recorded rather than hidden.

THE EQUATIONS, EXACTLY AS PUBLISHED
-----------------------------------
All four components are functions of the STIMULUS evaluated at ``t - delay``,
where the stimulus carries the FULL angular size ``q`` in DEGREES and the FULL
angular velocity ``q_dot`` in DEGREES/SECOND. The published model is
formulated in terms of the full stimulus angle and angular speed, i.e.
``q = 2*theta`` and ``q_dot = 2*theta_dot``, where ``theta`` is the HALF
angular size. The factor of two therefore lives INSIDE the LC4 expression as
written below, and the model accepts ``q`` and ``q_dot`` directly. Feeding it
``theta`` and ``theta_dot`` instead would halve every term that carries the
factor, and a test asserts that the two routes agree rather than assuming it.

    V_LC4(t)  = C1 * q_dot(t - d1)                                        [1]

    V_LPLC2(t) = C2 * exp( -( (ln q(t - d2) - ln C3)^2 ) / (2 * C4^2) )   [2]

    V_i1(t)   = C5 + C6 / ( 1 + exp( -( q(t - d3) - C7 ) / C8 ) )        [3]

    V_i2(t)   = C9 * exp( -( ( q(t - d4) - C10 )^2 ) / (2 * C11^2) )     [4]

    V_GF(t)   = W_LC4 * V_LC4 + W_LPLC2 * V_LPLC2
                 + W_i1 * V_i1 + W_i2 * V_i2                              [5]

with the published coefficients and delays, all recorded in
:class:`AcheGFModelCoefficients` and :class:`AcheGFModelDelays`.

Two of these are worth a note, because both are easy to get subtly wrong:

  * [2] is a Gaussian in the LOGARITHM of angular size, not in angular size.
    It therefore peaks exactly at ``q = C3 = 42 deg`` and its width parameter
    ``C4 = 0.52`` is DIMENSIONLESS, a spread in natural-log units. A Gaussian
    in ``q`` would peak at the same place but would have a completely
    different shape: it would be far narrower at large ``q`` and would not be
    symmetric on a log axis. This is a log-normal-shaped component and the
    implementation says so.

  * [3] has ``C8 = -11 deg``, a NEGATIVE width. The published form keeps that
    sign inside the exponent, which makes the term INCREASE with ``q``: the
    component contributes increasing inhibition as the object grows. The sign
    is preserved as published rather than absorbed, so the stored coefficient
    and the evaluated expression agree literally.

UNITS
-----
    time                       seconds
    angle                      DEGREES
    angular velocity           degrees / second
    phenomenological output    millivolts

Degrees are NOT SI, and the published coefficients are written in degrees, so
degrees is the internal angle unit here and no silent radian conversion is
applied to any stimulus feature. The one and only angle conversion in this
module is inside the looming geometry, where ``math.atan2`` returns radians
and is converted to degrees explicitly by the named constant
``_RAD_TO_DEG``. A test asserts that passing a radians value where degrees are
expected produces a visibly different result, so a unit mix-up cannot pass
silently.

THE LOGARITHM AND INVALID STIMULUS
----------------------------------
[2] requires ``q > 0``. For a physically valid on-axis looming stimulus ``q``
is positive whenever the object is in front of the animal. When a defined
stimulus yields ``q <= 0`` this module RAISES
:class:`AngularSizeError`. It does not clamp, does not substitute epsilon, and
does not return a quiet zero: a non-positive angular size is a caller error or
a geometry error (an object behind the eye, or past collision), and silently
repairing it would hide the difference between a valid and an invalid stimulus.
The prehistory case is separate and is described next.

PREHISTORY CONVENTION, STATED EXPLICITLY
----------------------------------------
Each component evaluates its source feature at ``t - delay``. If ``t - delay``
is negative it precedes the available stimulus history, and 8H's convention is:

    THE STIMULUS IS ABSENT, AND EVERY COMPONENT IS EXACTLY ZERO.

This is a numerical boundary condition, not a claim about pre-stimulus neural
activity, and it is documented as such. It is preferable to zero-padding the
stimulus and evaluating the published formulas at ``q = 0``, because those
formulas do not all give zero there: [3] would evaluate to about +0.0585 mV
and [4] to about -0.0020 mV, both of which are artefacts of the functions'
asymptotes rather than anything the source states. Inventing that activity is
exactly what this checkpoint must not do. A caller who genuinely needs a
stimulus with history before ``t = 0`` supplies a stimulus object defined on
``t < 0``, and the published formulas are then applied there verbatim and
unchanged; :class:`CallableLoomingStimulus` exists for precisely that case.

THE RESULTING EDGE AT THE STIMULUS ONSET IS REAL AND DELIBERATE
--------------------------------------------------------------
Because the absent-stimulus value is zero while the published formulas have
non-zero limits at ``q -> 0``, the model is DISCONTINUOUS at the instant a
component's delay elapses. For component [3] the step is from exactly 0 mV to
``C5 + C6 / (1 + exp(-(0 - C7) / C8))``, which is about +0.0585 mV.

This is the honest consequence of the choice above, and it is pinned by a test
rather than smoothed over. Smoothing it would require either inventing
pre-stimulus activity or modifying a published coefficient, and 3.0D-8H does
neither. It is a boundary artefact of evaluating a stimulus that BEGINS at
``t = 0``; it does not arise for a stimulus with genuine earlier history, where
the published formula is applied smoothly throughout.

No particular value of ``r/v`` is hardcoded into the model. ``r/v`` is a
STIMULUS property, exposed as
:attr:`ConstantVelocityLoomingStimulus.radius_over_velocity_s`, and the
phenomenology does not consult it.

RELATION TO 3.0D-7Y, 7U, 8G AND THE LIVE GF
--------------------------------------------
7Y remains the provenance layer: it still holds no coefficient, and all
thirteen of its structurally-empty unavailable sensory quantities (the LC4 and
LPLC2 synaptic conductances, the membrane conductances, the channel densities,
the Hodgkin-Huxley kinetics, the release probabilities, the GF sensory
reversal potential, the sensory Q10 and the sensory receptor kinetics) remain
unavailable. 8H makes NONE of them available, because 8H supplies a
phenomenological function, not a synaptic mechanism. 7U is untouched, the 8G
PSI->DLMn chemical synapse is untouched, and ``gf_active``'s membrane
equations are untouched. This module is a sensory PHENOMENOLOGY layer that
lives beside the live GF, not inside it.
"""

import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

MODEL_NAME_GF_SENSORY_DRIVE_V0 = "gf_sensory_drive_v0"

#: The single, explicit radian->degree conversion in this module. It is used
#: only inside the looming geometry, where ``math.atan2`` returns radians. No
#: published coefficient is ever converted, because none of them is in radians.
_RAD_TO_DEG = 180.0 / math.pi


# --- sources -----------------------------------------------------------------

SOURCE_ACHE_2019 = (
    "Ache JM, Polsky J, Alghailani S, Parekh R, Breads P, Peek MY, Bock DD, "
    "von Reyn CR, Card GM (2019). Neural Basis for Looming Size and Velocity "
    "Encoding in the Drosophila Giant Fiber Escape Pathway. Curr Biol "
    "29(6):1073-1081.e4. https://pubmed.ncbi.nlm.nih.gov/30827912/ . "
    "PRIMARY SOURCE OF THE MODEL STRUCTURE AND COEFFICIENTS. The paper is NOT "
    "in PubMed Central (Europe PMC reports inPMC: N), so the project did not "
    "read its equations from the publisher of record."
)

# NOTE ON A CITATION CORRECTION, RECORDED RATHER THAN QUIETLY WORKED AROUND:
# https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ is frequently cited for
# this model, but that PMCID is Augustin H, Zylbertal A, Partridge L (2019),
# "A Computational Model of the Escape Response Latency in the Giant Fiber
# System of Drosophila melanogaster", eNeuro 6(2):ENEURO.0423-18.2019,
# PMID 31001574, ModelDB 245415. That is the THORACIC GAP-JUNCTION LATENCY
# model this project already uses at 3.0D-7V and 3.0D-8G. It contains the
# PSI->DLMn double-exponential synapse and NO looming phenomenology, NO LC4,
# NO LPLC2 and NO GF sensory drive. It is not a source for this module.
SOURCE_PMC6469880_IS_AUGUSTIN_2019 = (
    "CITATION CORRECTION, recorded because 3.0D-8H was pointed at this PMCID as "
    "a primary source for the Ache et al. 2019 sensory model. PMC6469880 is "
    "Augustin et al. 2019 eNeuro 6(2):ENEURO.0423-18.2019 (PMID 31001574, "
    "ModelDB 245415), the thoracic GFS latency model. It states the GF/TTMn, "
    "GF/PSI and PSI/DLMn parameters used at 3.0D-7V and 3.0D-8G and contains "
    "no LC4, no LPLC2, no GF looming response and none of the coefficients in "
    "this module. The coefficients here come from the source below, NOT from "
    "PMC6469880."
)

SOURCE_GABBIANI_2023_VERBATIM_REPRODUCTION = (
    "Gabbiani F, Preuss TM, Dewell RB (2023). Approaching object acceleration "
    "differentially affects the predictions of neuronal collision avoidance "
    "models. Biological Cybernetics 117:129-142. "
    "https://doi.org/10.1007/s00422-023-00961-0 . "
    "INDEPENDENT VERBATIM REPRODUCTION OF THE Ache et al. 2019 GF MODEL, and "
    "the source actually read for every coefficient in this module. Its "
    "'Giant Fiber model' section states: the model 'is formulated in terms of "
    "the full stimulus angle and angular speed (i.e., 2 theta and 2 thetadot "
    "in the notation used here) and relies on the weighted sum of two "
    "excitatory and two inhibitory inputs', gives 'vGF = wLC4 vLC4 + wLPLC2 "
    "vLPLC2 + wi1 vi1 + wi2 vi2, with weights wLC4 = 1.62, wLPLC2 = 1.45, wi1 "
    "= 2.27 and wi2 = 1', then 'vLC4 = c1 2 thetadot(t - delta1), with c1 = "
    "0.2567 . 10^-3 mV/(deg/s) and delta1 = 19 ms', 'vLPLC2 = c2 exp(-(log(2 "
    "theta(t - delta2)) - log(c3))^2 / (2 c4^2), with c2 = 1.7 mV, c3 = 42 "
    "deg, c4 = 0.52 (dimensionless) and the delay delta2 = 19 ms', 'vi1 = c5 + "
    "c6 / (1 + exp(-(2 theta(t - delta3) - c7)/c8)), with c5 = -0.53 mV, c6 = "
    "0.59 mV, c7 = 66 deg, c8 = -11 deg and delta3 = 37.5 ms', and 'vi2 = c9 "
    "exp(-(2 theta(t - delta4) - c10)^2 / (2 c11^2)), with c9 = -0.52 mV, c10 = "
    "26 deg, c11 = 7.8 deg and delta4 = 11 ms'. Its note on c1 written as "
    "'0.2567 . 10^-3' is the SAME NUMBER as 0.0002567, merely written with an "
    "explicit power of ten. Note also that this reproduction describes the two "
    "inhibitory inputs only as 'two inhibitory inputs' and does NOT identify "
    "their cellular source, so the attribution of component 1 to an "
    "LC4/LPLC2-independent tonic input and of component 2 to an LC4-dependent "
    "input rests on Ache et al. 2019 as reported, not on this reproduction."
)


# --- errors ------------------------------------------------------------------

class GFSensoryDriveError(Exception):
    """Base class for sensory->GF drive failures."""


class AngularSizeError(GFSensoryDriveError):
    """A defined stimulus reports a full angular size that cannot be used.

    Raised when ``q <= 0``, which makes ``ln q`` in component [2] undefined.
    The value is NEVER clamped: silently repairing a non-positive angular size
    would erase the difference between a valid and an invalid stimulus.
    """


class StimulusGeometryError(GFSensoryDriveError):
    """The looming geometry is not physically usable."""


class PhenomenologicalBoundaryError(GFSensoryDriveError):
    """Something tried to treat the phenomenological drive as a mechanism."""


# --- source-backed coefficients ----------------------------------------------

#: Published coefficients of the Ache et al. 2019 GF looming model, as
#: reproduced verbatim by Gabbiani et al. 2023. The published symbol is noted
#: beside each so that the mapping is auditable against the source text.
ACHE_C1 = 0.0002567      # mV per (deg/s)
ACHE_C2 = 1.7            # mV
ACHE_C3 = 42.0           # deg
ACHE_C4 = 0.52           # dimensionless (a spread in natural-log units)
ACHE_C5 = -0.53          # mV
ACHE_C6 = 0.59           # mV
ACHE_C7 = 66.0           # deg
ACHE_C8 = -11.0          # deg (negative, as published)
ACHE_C9 = -0.52          # mV
ACHE_C10 = 26.0          # deg
ACHE_C11 = 7.8           # deg

#: Published component weights. These are WEIGHTS OF A PHENOMENOLOGICAL SUM.
#: They are not synaptic strengths and not conductances.
ACHE_W_LC4 = 1.62
ACHE_W_LPLC2 = 1.45
ACHE_W_I1 = 2.27
ACHE_W_I2 = 1.0

#: Published sensory delays, in SECONDS.
ACHE_D1 = 0.019          # LC4
ACHE_D2 = 0.019          # LPLC2
ACHE_D3 = 0.0375         # inhibitory component 1
ACHE_D4 = 0.011          # inhibitory component 2


_NO_SYNAPTIC_MECHANISM = (
    "A PHENOMENOLOGICAL COMPONENT IS NOT A SYNAPSE. The published amplitudes are "
    "in millivolts because the published model is written in millivolts. They "
    "are NOT synaptic conductances, NOT currents, NOT reversal potentials, NOT "
    "receptor kinetics, NOT release probabilities and NOT vesicle dynamics. No "
    "retrieved source states an LC4->GF or LPLC2->GF synaptic conductance, a "
    "GF sensory reversal potential, a release probability, a receptor identity "
    "or a Q10, and none is created, estimated, borrowed or fitted here."
)

_NO_LIVE_GF_COUPLING = (
    "THERE IS NO DEFENSIBLE COUPLING FROM THIS DRIVE TO THE LIVE GF MEMBRANE. "
    "3.0D-8H therefore performs NO injection: it never calls inject_current, "
    "never calls ActiveAxonModel.step, never converts a millivolt of "
    "phenomenological drive into a current, and never introduces a synaptic "
    "conductance. There is no source-backed factor that would justify a "
    "conversion such as '1 mV of drive = X nA', so none is invented. Deciding "
    "how, or whether, this drive can reach the live GF membrane is left "
    "explicitly open for a later checkpoint."
)

_NOT_THE_LIVE_GF_STATE = (
    "THIS IS NOT THE LIVE GF MEMBRANE VOLTAGE. The live GF's voltage is a state "
    "vector held by GFActiveAxonModel and advanced by numerical integration of "
    "the membrane equations. This is a published PHENOMENOLOGICAL PREDICTION of "
    "the GF membrane-potential RESPONSE, evaluated analytically from stimulus "
    "coordinates. The two are different objects and are not interchangeable, "
    "and the values here must never be added to, compared against, or "
    "substituted for the live GF state."
)


@dataclass(frozen=True)
class AcheGFModelCoefficients:
    """The published coefficients of the Ache GF looming model.

    Frozen, source-backed, and unit-explicit. Every field is a PUBLISHED
    MODEL PARAMETER of a PHENOMENOLOGICAL function. The dataclass has no
    conductance, current, receptor or kinetic field, and the boundary flags are
    hard values that raise if cleared, so these numbers cannot be quietly
    promoted to a synaptic mechanism.
    """

    c1_mV_per_deg_per_s: float = ACHE_C1
    c2_mV: float = ACHE_C2
    c3_deg: float = ACHE_C3
    c4_log_width: float = ACHE_C4
    c5_mV: float = ACHE_C5
    c6_mV: float = ACHE_C6
    c7_deg: float = ACHE_C7
    c8_deg: float = ACHE_C8
    c9_mV: float = ACHE_C9
    c10_deg: float = ACHE_C10
    c11_deg: float = ACHE_C11
    w_lc4: float = ACHE_W_LC4
    w_lplc2: float = ACHE_W_LPLC2
    w_i1: float = ACHE_W_I1
    w_i2: float = ACHE_W_I2

    is_synaptic_conductance: bool = False
    is_membrane_current: bool = False
    has_receptor_kinetics: bool = False
    has_release_probability: bool = False
    has_receptor_identity: bool = False
    is_stochastic: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        for flag in (
            "is_synaptic_conductance",
            "is_membrane_current",
            "has_receptor_kinetics",
            "has_release_probability",
            "has_receptor_identity",
            "is_stochastic",
            "live_solver_eligible",
        ):
            if getattr(self, flag):
                raise PhenomenologicalBoundaryError(
                    f"Coefficient flag '{flag}' must be False. The Ache et al. "
                    f"2019 coefficients are published parameters of a "
                    f"PHENOMENOLOGICAL function. They are not a synaptic "
                    f"conductance, not a current, not receptor kinetics, not a "
                    f"release probability, not a receptor identity, not "
                    f"stochastic, and not eligible for the live solver."
                )
        numeric = (
            self.c1_mV_per_deg_per_s, self.c2_mV, self.c3_deg, self.c4_log_width,
            self.c5_mV, self.c6_mV, self.c7_deg, self.c8_deg, self.c9_mV,
            self.c10_deg, self.c11_deg,
            self.w_lc4, self.w_lplc2, self.w_i1, self.w_i2,
        )
        for value in numeric:
            if not math.isfinite(value):
                raise GFSensoryDriveError(
                    "A published Ache GF coefficient is not finite."
                )
        if self.c3_deg <= 0.0:
            raise GFSensoryDriveError(
                f"c3 must be a positive angular size because it appears inside "
                f"ln(c3), got {self.c3_deg}."
            )
        if self.c4_log_width == 0.0:
            raise GFSensoryDriveError(
                "c4 is a Gaussian width in log-angular-size units and must be "
                "non-zero, otherwise component [2] is a spike at q = c3."
            )
        if self.c8_deg == 0.0:
            raise GFSensoryDriveError(
                "c8 is the scale of the logistic in component [3] and must be "
                "non-zero."
            )
        if self.c11_deg == 0.0:
            raise GFSensoryDriveError(
                "c11 is a Gaussian width in component [4] and must be "
                "non-zero."
            )

    @property
    def coefficient_symbols(self) -> Tuple[Tuple[str, str], ...]:
        """Published symbol -> this dataclass field, for source auditability."""
        return (
            ("C1", "c1_mV_per_deg_per_s"),
            ("C2", "c2_mV"),
            ("C3", "c3_deg"),
            ("C4", "c4_log_width"),
            ("C5", "c5_mV"),
            ("C6", "c6_mV"),
            ("C7", "c7_deg"),
            ("C8", "c8_deg"),
            ("C9", "c9_mV"),
            ("C10", "c10_deg"),
            ("C11", "c11_deg"),
            ("W_LC4", "w_lc4"),
            ("W_LPLC2", "w_lplc2"),
            ("W_i1", "w_i1"),
            ("W_i2", "w_i2"),
        )

    def source_references(self) -> Tuple[str, ...]:
        return (
            SOURCE_ACHE_2019,
            SOURCE_GABBIANI_2023_VERBATIM_REPRODUCTION,
        )

    def limitations(self) -> str:
        return (
            "PUBLISHED PHENOMENOLOGICAL COEFFICIENTS. These are coefficients of "
            "a published stimulus-response function, not synaptic parameters. "
            f"{_NO_SYNAPTIC_MECHANISM} {_NO_LIVE_GF_COUPLING}"
        )


@dataclass(frozen=True)
class AcheGFModelDelays:
    """The four published sensory delays, in seconds.

    Each component evaluates its own source feature at ``t - delay``. These are
    SENSORY DELAYS in the published model. They are NOT synaptic delays in the
    transmission sense, NOT receptor rise constants, NOT decay constants and
    NOT axial conduction times, and they must not be read as any of those.
    """

    d1_s: float = ACHE_D1
    d2_s: float = ACHE_D2
    d3_s: float = ACHE_D3
    d4_s: float = ACHE_D4

    is_synaptic_delay: bool = False
    is_receptor_kinetic: bool = False
    changes_timestep_policy: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        for flag in (
            "is_synaptic_delay",
            "is_receptor_kinetic",
            "changes_timestep_policy",
            "live_solver_eligible",
        ):
            if getattr(self, flag):
                raise PhenomenologicalBoundaryError(
                    f"Delay flag '{flag}' must be False. These are SENSORY "
                    f"delays of a published phenomenological model, not "
                    f"synaptic delays, not receptor kinetics, and they do not "
                    f"change the project's timestep policy."
                )
        for name in ("d1_s", "d2_s", "d3_s", "d4_s"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0.0:
                raise GFSensoryDriveError(
                    f"Sensory delay '{name}' must be finite and non-negative, "
                    f"got {value}."
                )

    def as_ms(self) -> Tuple[float, float, float, float]:
        """The four delays in milliseconds, for reporting and tests."""
        return (
            self.d1_s * 1e3,
            self.d2_s * 1e3,
            self.d3_s * 1e3,
            self.d4_s * 1e3,
        )

    def source_references(self) -> Tuple[str, ...]:
        return (
            SOURCE_ACHE_2019,
            SOURCE_GABBIANI_2023_VERBATIM_REPRODUCTION,
        )

    def limitations(self) -> str:
        return (
            "PUBLISHED SENSORY DELAYS OF A PHENOMENOLOGICAL MODEL. They are not "
            "synaptic delays, not receptor rise or decay constants, not "
            "conduction times, and they do not change the numerical timestep "
            "policy."
        )


def published_ache_gf_coefficients() -> AcheGFModelCoefficients:
    """Return the published Ache et al. 2019 GF model coefficients."""
    return AcheGFModelCoefficients()


def published_ache_gf_delays() -> AcheGFModelDelays:
    """Return the published Ache et al. 2019 GF model sensory delays."""
    return AcheGFModelDelays()


# --- the stimulus ------------------------------------------------------------


class LoomingStimulus:
    """Interface for a looming stimulus expressed in FULL angular size.

    Implementations expose the stimulus in the SAME units the published model
    consumes, so that no conversion can be forgotten downstream:

        q_deg(t)      full angular size, DEGREES  ( == 2 * theta )
        q_dot_deg_per_s(t)  full angular velocity, DEGREES / SECOND

    ``theta`` is the HALF angular size and is provided only as a derived
    convenience, so that the factor-of-two relationship is explicit and testable
    rather than left to the caller's memory.
    """

    def q_deg(self, t_s: float) -> float:
        raise NotImplementedError

    def q_dot_deg_per_s(self, t_s: float) -> float:
        raise NotImplementedError

    def theta_deg(self, t_s: float) -> float:
        """HALF angular size. The published model uses ``q = 2 * theta``."""
        return self.q_deg(t_s) / 2.0

    def theta_dot_deg_per_s(self, t_s: float) -> float:
        """HALF angular velocity. The published model uses ``2 * theta_dot``."""
        return self.q_dot_deg_per_s(t_s) / 2.0

    def onset_time_s(self) -> float:
        """Earliest time at which this stimulus is defined.

        Times below this are PREHISTORY, and 3.0D-8H's documented convention
        there is that the stimulus is absent and every component is zero.
        """
        return 0.0

    def radius_over_velocity_s(self) -> Optional[float]:
        """``r/v`` if this stimulus has a constant radius and velocity."""
        return None


@dataclass(frozen=True)
class ConstantVelocityLoomingStimulus(LoomingStimulus):
    """The standard constant-radius, constant-velocity looming geometry.

    GEOMETRY, STATED EXACTLY
    -----------------------
    A sphere of constant radius ``r_m`` approaches the eye on the optic axis at
    constant speed ``v_m_per_s``, starting at axial distance ``d0_m`` at
    ``t = 0`` and reaching the eye at ``t_collision = d0 / v``. At time ``t``
    the axial distance is

        d(t) = d0 - v * t

    The object subtends a HALF angular size given by the small-angle-exact
    right-triangle relation

        theta(t) = arctan(r / d(t))

    and the published model uses the FULL angular size

        q(t) = 2 * theta(t) = 2 * arctan(r / d(t))          [degrees]

    Differentiating gives the FULL angular velocity

        q_dot(t) = 2 * r * v / (d(t)^2 + r^2)               [degrees/second]

    which is strictly positive for an approaching object, grows as the object
    gets close, and tends to zero as the object recedes. At collision
    ``d -> 0`` so ``theta -> 90 deg`` and ``q -> 180 deg``.

    The dimensionally important looming parameter is ``r / v``, a TIME, which
    is what sets the timescale on which ``q`` sweeps through its range. It is
    exposed as :attr:`radius_over_velocity_s` and is NEVER consulted by
    :class:`PhenomenologicalGFDrive`: no particular ``r/v``, and no behavioural
    threshold derived from it, is baked into the biology.

    Units are given in the field names. ``math.atan2`` is used rather than
    ``math.atan`` so that the expression is well defined for a negative
    denominator instead of silently returning a plausible-looking angle, and
    the single radian-to-degree conversion happens explicitly here.
    """

    r_m: float
    v_m_per_s: float
    d0_m: float

    def __post_init__(self) -> None:
        for name in ("r_m", "v_m_per_s", "d0_m"):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise StimulusGeometryError(
                    f"Looming geometry field '{name}' must be finite, got "
                    f"{value}."
                )
        if self.r_m <= 0.0:
            raise StimulusGeometryError(
                f"Object radius must be positive, got {self.r_m} m. A "
                f"zero-radius object subtends no angle and its r/v is "
                f"undefined."
            )
        if self.v_m_per_s <= 0.0:
            raise StimulusGeometryError(
                f"Approach velocity must be positive (an APPROACHING object), "
                f"got {self.v_m_per_s} m/s. A receding or static object is a "
                f"different stimulus and is not modelled here."
            )
        if self.d0_m <= 0.0:
            raise StimulusGeometryError(
                f"Initial distance must be positive, got {self.d0_m} m."
            )

    # -- derived geometry ---------------------------------------------------

    def distance_m(self, t_s: float) -> float:
        """Axial distance at time ``t``, in metres."""
        return self.d0_m - self.v_m_per_s * t_s

    def collision_time_s(self) -> float:
        """Time at which the object reaches the eye, ``d0 / v``."""
        return self.d0_m / self.v_m_per_s

    def radius_over_velocity_s(self) -> Optional[float]:
        """The looming timescale ``r/v``, in seconds."""
        return self.r_m / self.v_m_per_s

    def onset_time_s(self) -> float:
        return 0.0

    # -- the two stimulus features -----------------------------------------

    def q_deg(self, t_s: float) -> float:
        """FULL angular size ``2 * arctan(r / d)``, in DEGREES."""
        d = self.distance_m(t_s)
        if d <= 0.0:
            raise StimulusGeometryError(
                f"Object has reached or passed the eye at t = {t_s} s "
                f"(d = {d} m). The looming geometry is defined only while the "
                f"object is in front of the animal. Past collision the "
                f"angular size would exceed 180 degrees and the published "
                f"model is not applicable."
            )
        return 2.0 * math.atan2(self.r_m, d) * _RAD_TO_DEG

    def q_dot_deg_per_s(self, t_s: float) -> float:
        """FULL angular velocity ``2 r v / (d^2 + r^2)``, in DEGREES/SECOND.

        The closed form is derived from ``atan2``, which returns radians, so
        the derivative carries the SAME ``_RAD_TO_DEG`` factor as ``q_deg``
        itself. Omitting it here would make ``q_dot`` inconsistent with ``q``
        by exactly the factor 180/pi, which is a unit error rather than a
        modelling choice, so the conversion is applied explicitly and a test
        differentiates ``q_deg`` numerically to confirm the two agree.
        """
        d = self.distance_m(t_s)
        if d <= 0.0:
            raise StimulusGeometryError(
                f"Object has reached or passed the eye at t = {t_s} s "
                f"(d = {d} m); the angular velocity is not defined there."
            )
        return (
            2.0 * self.r_m * self.v_m_per_s
            / (d * d + self.r_m * self.r_m)
            * _RAD_TO_DEG
        )

    def geometry_note(self) -> str:
        return (
            f"Constant-radius / constant-velocity on-axis looming. "
            f"q(t) = 2 arctan(r / (d0 - v t)) in degrees, "
            f"q_dot(t) = 2 r v / (d(t)^2 + r^2) in degrees/second, with "
            f"r = {self.r_m} m, v = {self.v_m_per_s} m/s, d0 = {self.d0_m} m, "
            f"collision at t = {self.collision_time_s()} s, and a looming "
            f"timescale r/v = {self.radius_over_velocity_s()} s."
        )


@dataclass(frozen=True)
class CallableLoomingStimulus(LoomingStimulus):
    """A stimulus supplied by the caller as plain functions of time.

    This is the escape hatch for a stimulus whose history genuinely extends
    before ``t = 0``, or whose geometry is not the standard constant-velocity
    one. The published formulas are applied to whatever these functions return,
    verbatim and unchanged, including at negative times.
    """

    q_fn: Callable[[float], float]
    q_dot_fn: Callable[[float], float]
    onset_s: float = 0.0
    label: str = "callable_looming_stimulus"

    def q_deg(self, t_s: float) -> float:
        return float(self.q_fn(t_s))

    def q_dot_deg_per_s(self, t_s: float) -> float:
        return float(self.q_dot_fn(t_s))

    def onset_time_s(self) -> float:
        return self.onset_s

    def geometry_note(self) -> str:
        return f"Caller-supplied stimulus functions, labelled '{self.label}'."


# --- the result --------------------------------------------------------------


@dataclass(frozen=True)
class SensoryDriveSample:
    """The four published components and their weighted sum, at one instant.

    Every field is in the published units: MILLIVOLTS for the components and
    the sum, DEGREES for ``q_deg``, DEGREES/SECOND for ``q_dot_deg_per_s`` and
    SECONDS for ``t_s``.

    ``weighted_gf_drive_mV`` is a PHENOMENOLOGICAL PREDICTION of the GF
    membrane-potential RESPONSE. It is not a current, not a conductance, and
    not the voltage state of the live GFActiveAxonModel.
    """

    t_s: float
    q_deg: float
    q_dot_deg_per_s: float
    lc4_component_mV: float
    lplc2_component_mV: float
    inhibitory_component_1_mV: float
    inhibitory_component_2_mV: float
    weighted_lc4_mV: float
    weighted_lplc2_mV: float
    weighted_i1_mV: float
    weighted_i2_mV: float
    weighted_gf_drive_mV: float
    in_prehistory: bool

    def components_mV(self) -> Tuple[float, float, float, float]:
        """The four UNWEIGHTED components, in published order."""
        return (
            self.lc4_component_mV,
            self.lplc2_component_mV,
            self.inhibitory_component_1_mV,
            self.inhibitory_component_2_mV,
        )

    def weighted_components_mV(self) -> Tuple[float, float, float, float]:
        """The four WEIGHTED contributions, in published order."""
        return (
            self.weighted_lc4_mV,
            self.weighted_lplc2_mV,
            self.weighted_i1_mV,
            self.weighted_i2_mV,
        )

    def is_the_live_gf_membrane_voltage(self) -> bool:
        """Always False. See :data:`_NOT_THE_LIVE_GF_STATE`."""
        return False

    def limitations(self) -> str:
        return (
            f"{_NOT_THE_LIVE_GF_STATE} {_NO_SYNAPTIC_MECHANISM} "
            f"{_NO_LIVE_GF_COUPLING}"
        )


# --- the model ---------------------------------------------------------------


class PhenomenologicalGFDrive:
    """The published Ache et al. 2019 sensory->GF phenomenological model.

    Deterministic and pure: evaluation depends only on the published
    coefficients, the published delays, the evaluation time and the supplied
    stimulus. There is no random state, no accumulation, no hidden history, no
    timestep and no numerical integration. Calling ``evaluate`` twice with the
    same arguments gives bit-identical results, which is what makes the
    100-velocity sweep and the repeat-run assertions in the tests meaningful.

    The class deliberately exposes NO membrane, current or conductance
    interface. In particular it has no ``step``, no ``inject_current``, no
    ``voltages``, and it does not import any membrane solver, so it cannot be
    wired into the live GF even by accident.
    """

    def __init__(
        self,
        coefficients: Optional[AcheGFModelCoefficients] = None,
        delays: Optional[AcheGFModelDelays] = None,
    ) -> None:
        self._coefficients = (
            coefficients if coefficients is not None
            else published_ache_gf_coefficients()
        )
        self._delays = delays if delays is not None else published_ache_gf_delays()

    # -- published parameters ----------------------------------------------

    @property
    def coefficients(self) -> AcheGFModelCoefficients:
        return self._coefficients

    @property
    def delays(self) -> AcheGFModelDelays:
        return self._delays

    @property
    def model_name(self) -> str:
        return MODEL_NAME_GF_SENSORY_DRIVE_V0

    # -- the four published components, undelayed --------------------------
    #
    # These take the stimulus feature directly, so that the published algebra
    # can be checked against the source one term at a time, and so that the
    # delay bookkeeping lives in exactly one place (evaluate()).

    def lc4_component(self, q_dot_deg_per_s: float) -> float:
        """Component [1]: ``C1 * q_dot``, in mV.

        Takes the FULL angular velocity in degrees/second, which is what the
        published equation ``vLC4 = c1 * 2 * theta_dot`` evaluates to. Because
        ``q_dot = 2 * theta_dot``, passing the half-angle velocity here would
        halve the result, so the argument is named and documented for that
        reason.
        """
        c = self._coefficients
        return c.c1_mV_per_deg_per_s * q_dot_deg_per_s

    def lplc2_component(self, q_deg: float) -> float:
        """Component [2]: a Gaussian in ``ln q``, in mV.

        ``C2 * exp( -( (ln q - ln C3)^2 ) / (2 * C4^2) )``. The Gaussian is in
        the LOGARITHM of the full angular size, so it peaks exactly at
        ``q = C3`` and ``C4`` is dimensionless. ``q`` must be strictly
        positive; see :class:`AngularSizeError`.
        """
        c = self._coefficients
        self._require_positive_angular_size(q_deg)
        log_ratio = math.log(q_deg) - math.log(c.c3_deg)
        return c.c2_mV * math.exp(
            -(log_ratio * log_ratio) / (2.0 * c.c4_log_width * c.c4_log_width)
        )

    def inhibitory_component_1(self, q_deg: float) -> float:
        """Component [3]: a logistic in ``q``, in mV.

        ``C5 + C6 / (1 + exp( -(q - C7) / C8 ))``. ``C8`` is NEGATIVE as
        published, which is what makes the term increase with ``q`` and
        therefore contribute increasing inhibition as the object grows.
        """
        c = self._coefficients
        return c.c5_mV + c.c6_mV / (
            1.0 + math.exp(-(q_deg - c.c7_deg) / c.c8_deg)
        )

    def inhibitory_component_2(self, q_deg: float) -> float:
        """Component [4]: a Gaussian in ``q``, in mV.

        ``C9 * exp( -( (q - C10)^2 ) / (2 * C11^2) )``. Negative everywhere,
        with its most negative value exactly at ``q = C10``.
        """
        c = self._coefficients
        delta = q_deg - c.c10_deg
        return c.c9_mV * math.exp(
            -(delta * delta) / (2.0 * c.c11_deg * c.c11_deg)
        )

    # -- the published weighted combination --------------------------------

    def weighted_gf_drive(
        self,
        lc4_mV: float,
        lplc2_mV: float,
        inhibitory_1_mV: float,
        inhibitory_2_mV: float,
    ) -> float:
        """Equation [5]: the published weighted sum, in mV.

        ``W_LC4*V_LC4 + W_LPLC2*V_LPLC2 + W_i1*V_i1 + W_i2*V_i2``. The weights
        are weights of a phenomenological sum. They are NOT synaptic strengths
        and NOT conductances.
        """
        c = self._coefficients
        return (
            c.w_lc4 * lc4_mV
            + c.w_lplc2 * lplc2_mV
            + c.w_i1 * inhibitory_1_mV
            + c.w_i2 * inhibitory_2_mV
        )

    # -- delayed evaluation -------------------------------------------------

    def evaluate(self, t_s: float, stimulus: LoomingStimulus) -> SensoryDriveSample:
        """Evaluate all four delayed components and the weighted sum at ``t``.

        Each component reads its source feature at ``t - delay``. Where
        ``t - delay`` precedes the stimulus's onset, that component is exactly
        zero: the stimulus is ABSENT, and no pre-stimulus activity is invented.
        """
        if not math.isfinite(t_s):
            raise GFSensoryDriveError(
                f"Evaluation time must be finite, got {t_s}."
            )
        onset = stimulus.onset_time_s()
        c = self._coefficients
        d = self._delays

        t_lc4 = t_s - d.d1_s
        t_lplc2 = t_s - d.d2_s
        t_i1 = t_s - d.d3_s
        t_i2 = t_s - d.d4_s

        v_lc4 = (
            self.lc4_component(stimulus.q_dot_deg_per_s(t_lc4))
            if t_lc4 >= onset else 0.0
        )
        v_lplc2 = (
            self.lplc2_component(stimulus.q_deg(t_lplc2))
            if t_lplc2 >= onset else 0.0
        )
        v_i1 = (
            self.inhibitory_component_1(stimulus.q_deg(t_i1))
            if t_i1 >= onset else 0.0
        )
        v_i2 = (
            self.inhibitory_component_2(stimulus.q_deg(t_i2))
            if t_i2 >= onset else 0.0
        )

        drive = self.weighted_gf_drive(v_lc4, v_lplc2, v_i1, v_i2)

        # The reported stimulus features are those seen by the EARLIEST
        # delayed sample, which is the LC4/LPLC2 pair at d1 = d2.
        if t_s - min(d.d1_s, d.d2_s, d.d3_s, d.d4_s) >= onset:
            t_report = t_s - min(d.d1_s, d.d2_s, d.d3_s, d.d4_s)
        else:
            t_report = None

        return SensoryDriveSample(
            t_s=t_s,
            q_deg=(
                stimulus.q_deg(t_report) if t_report is not None else 0.0
            ),
            q_dot_deg_per_s=(
                stimulus.q_dot_deg_per_s(t_report) if t_report is not None else 0.0
            ),
            lc4_component_mV=v_lc4,
            lplc2_component_mV=v_lplc2,
            inhibitory_component_1_mV=v_i1,
            inhibitory_component_2_mV=v_i2,
            weighted_lc4_mV=c.w_lc4 * v_lc4,
            weighted_lplc2_mV=c.w_lplc2 * v_lplc2,
            weighted_i1_mV=c.w_i1 * v_i1,
            weighted_i2_mV=c.w_i2 * v_i2,
            weighted_gf_drive_mV=drive,
            in_prehistory=(
                t_s - max(d.d1_s, d.d2_s, d.d3_s, d.d4_s) < onset
            ),
        )

    def evaluate_series(
        self, times_s: Sequence[float], stimulus: LoomingStimulus
    ) -> Tuple[SensoryDriveSample, ...]:
        """Evaluate the model at each time in ``times_s``, in order."""
        return tuple(self.evaluate(t, stimulus) for t in times_s)

    # -- boundaries ---------------------------------------------------------

    @property
    def is_live_membrane_voltage(self) -> bool:
        """Always False. This is not the live GF membrane state."""
        return False

    @property
    def has_synaptic_conductance(self) -> bool:
        """Always False: no sensory synaptic conductance exists."""
        return False

    @property
    def has_receptor_kinetics(self) -> bool:
        """Always False: no receptor, subunit or kinetic constant exists."""
        return False

    @property
    def is_stochastic(self) -> bool:
        """Always False: the model is exactly deterministic."""
        return False

    @property
    def has_random_state(self) -> bool:
        """Always False: the model holds no mutable state at all."""
        return False

    @property
    def drives_the_live_gf_membrane(self) -> bool:
        """Always False: 8H performs no injection into the live GF."""
        return False

    def reject_unsupported_feature(self, feature: str) -> None:
        """Raise for anything that would turn this into a mechanism.

        Refused by name, with the reason, so that an attempt to attach a
        conductance, a receptor, a stochastic release, a calcium coupling or a
        direct GF injection fails loudly instead of silently.

        The vocabulary is deliberately broad, including the terms a caller
        would reach for when trying to turn this into a synaptic mechanism:
        peak conductances, reversal potentials, receptor kinetics, binding
        parameters, opening probabilities, and generic rise/decay time
        constants. Refusing "tau_rise" and "time_constant" matters even though
        those words are innocuous on their own, because the sensory delays
        below are NOT receptor rise or decay constants and must not be read as
        one, nor used to parameterise a synapse.
        """
        forbidden = (
            "conductance", "synaptic_conductance", "peak_conductance", "g_peak",
            "g_syn", "g_amp", "peak_amplitude", "reversal_potential",
            "receptor", "dalpha7", "d_alpha7", "alpha7", "release_probability",
            "vesicle", "receptor_density", "calcium", "q10",
            "short_term_plasticity", "desensitization", "injected_current",
            "inject_current", "live_gf_state", "membrane_current",
            "membrane_state", "membrane_voltage", "gf_membrane_voltage",
            "spike_threshold", "r2_over_v_threshold",
            # Synaptic-mechanism vocabulary that must not be attached here.
            "receptor_kinetic", "binding", "open_probability", "single_channel",
            "tau_rise", "tau_decay", "rise_time", "decay_time",
            "time_constant", "synaptic_delay", "unitary",
        )
        lowered = feature.lower()
        for name in forbidden:
            if name in lowered:
                raise PhenomenologicalBoundaryError(
                    f"'{feature}' is refused. {_NO_SYNAPTIC_MECHANISM} "
                    f"{_NO_LIVE_GF_COUPLING}"
                )

    def coupling_to_live_gf(self) -> None:
        """Always raises: there is no coupling strategy yet.

        This exists so that the absence of a coupling is a positive,
        discoverable fact rather than a missing method. A later checkpoint that
        researches a defensible coupling replaces it.
        """
        raise PhenomenologicalBoundaryError(
            f"NO COUPLING TO THE LIVE GF EXISTS. {_NO_LIVE_GF_COUPLING}"
        )

    def scope_note(self) -> str:
        return (
            f"{MODEL_NAME_GF_SENSORY_DRIVE_V0}: the published Ache et al. 2019 "
            f"four-component sensory->GF PHENOMENOLOGICAL model, implemented "
            f"quantitatively in degrees, degrees/second, seconds and "
            f"millivolts. {_NOT_THE_LIVE_GF_STATE} {_NO_SYNAPTIC_MECHANISM} "
            f"{_NO_LIVE_GF_COUPLING} 3.0D-7Y remains the provenance layer and "
            f"none of its thirteen unavailable sensory quantities becomes "
            f"available here. 3.0D-7U, 3.0D-8G and the live GF membrane "
            f"equations are untouched."
        )

    def source_references(self) -> Tuple[str, ...]:
        return (
            SOURCE_ACHE_2019,
            SOURCE_PMC6469880_IS_AUGUSTIN_2019,
            SOURCE_GABBIANI_2023_VERBATIM_REPRODUCTION,
        )

    # -- internal -----------------------------------------------------------

    @staticmethod
    def _require_positive_angular_size(q_deg: float) -> None:
        if not math.isfinite(q_deg):
            raise AngularSizeError(
                f"Full angular size must be finite, got {q_deg} deg."
            )
        if q_deg <= 0.0:
            raise AngularSizeError(
                f"Full angular size must be strictly positive because the "
                f"published LPLC2 component contains ln(q), got {q_deg} deg. "
                f"The value is NOT clamped: a non-positive angular size is a "
                f"caller error or a geometry error, and silently repairing it "
                f"would hide the difference between a valid and an invalid "
                f"stimulus. For a physically valid on-axis approaching object "
                f"q is always positive while the object is in front of the "
                f"animal."
            )


def gf_sensory_drive_scope_note() -> str:
    """Return the 3.0D-8H scope note."""
    return PhenomenologicalGFDrive().scope_note()
