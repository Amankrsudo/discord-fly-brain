"""Electrical GFS coupling (3.0D-8C).

THE MODELDB gap2 MECHANISM, LIVE, WITH AN UNRESOLVED CONDUCTANCE.

3.0D-8A made the GF membrane live. 8C adds the ELECTRICAL component of the two
mixed GF synapses, using the mechanism the published Augustin et al. 2019
model actually uses, transcribed verbatim from the vendored ModelDB 245415
source.

WHAT IS IMPLEMENTED: THE gap2 EQUATION, AND ONLY THAT
----------------------------------------------------
``biological_brain/data/modeldb_245415/channels/gap2.mod`` is a POINT_PROCESS
with a ``vgap`` pointer::

    NEURON {
        POINT_PROCESS gap2
        NONSPECIFIC_CURRENT i
        RANGE i, g
        POINTER vgap
    }
    PARAMETER {
        v   (millivolt)
        g = 0 (nanosiemens) :1 (nanosiemens) : 1nS = 1000 pS
    }
    ASSIGNED {
        i    (nanoamp)
        vgap (millivolt)
    }
    BREAKPOINT {
        i = (v - vgap)*g*(0.001)
    }

That is a LINEAR OHMIC coupling. The 0.001 is a unit conversion and nothing
else: 1 mV * 1 nS = 1e-3 V * 1e-9 S = 1e-12 A = 1 picoamp, and 1 pA = 0.001 nA.
So the mechanism is reproduced in nanoamps, in its own declared unit, with the
conversion stated rather than hidden.

THIS IS NOT A SHAKB RECTIFICATION MODEL
---------------------------------------
The real GFS electrical synapse is a heterotypic ShakB junction and it
RECTIFIES. Phelan et al. 2008 report that the GF presynaptic side expresses
ShakB(N+16), the TTMn and PSI postsynaptic sides express ShakB(L), and that
the heterotypic junction is voltage dependent, transmitting preferentially in
one direction under depolarization of the GF side.

That is BIOLOGICAL EVIDENCE and it is recorded here as PROVENANCE ONLY. It is
NOT the equation the Augustin ModelDB model uses, and 8C does not implement
rectification. gap2.mod has no voltage dependence, no Boltzmann term, no
asymmetry and no gating variable: it is a single linear conductance. Calling
this mechanism a ShakB model would assert a quantitative rectification law
that no project source supplies, and 8C does not invent one.

The oocyte/Xenopus Boltzmann parameters that appear in the ShakB literature
are expression-system artefacts of a two-electrode voltage clamp on a foreign
cell. They are NOT imported here as live parameters, and no conductance-versus-
voltage curve is fitted, invented or approximated anywhere in this module.

THE CONDUCTANCE IS UNRESOLVED, AND STAYS UNRESOLVED
---------------------------------------------------
3.0D-7U records an unresolved conflict about g_gap and 8C does not touch it:

    paper   : 135.0 uS (young), 34.5 uS (old), Table 1, both '(estimated)'
    ModelDB : gfpn.py assigns 135.0 / 34.5 straight to gap2.g, which gap2.mod
              declares in nanoSiemens

Taken literally, 135 nS is 0.135 uS. The paper and the code differ by exactly
1000x. No erratum discriminates between the three open explanations: the
mod-file unit declaration being wrong, the gfpn.py numbers being wrong for the
declared unit, or the paper's unit being wrong.

So this module has NO DEFAULT GFS CONDUCTANCE. There is no class constant, no
module constant, no default argument and no fallback path from which a GFS
junction can acquire a conductance on its own. A conductance must be supplied
explicitly, with its unit, by the caller. Attempting to obtain the project's
unresolved g_gap value raises, and the message says why and points at 7U.

Supplying an explicit value does NOT resolve 7U. 7U stays unresolved with both
sides preserved and no preferred side. 8C's refusal is not a position on which
side is right, and no value it accepts is a claim about the biology.

THREE DISTINCT THINGS, KEPT DISTINCT
------------------------------------
A. BIOLOGICAL MECHANISM -- ShakB heterotypic rectifying electrical synapse.
   Status: EXPERIMENTALLY ESTABLISHED. Phelan et al. 2008. Metadata only.
   NOT implemented. No equation, no parameters, no live effect.

B. COMPUTATIONAL MECHANISM -- gap2 linear ohmic coupling.
   Status: PUBLISHED MODEL MECHANISM. This is what 8C implements, and the
   only thing 8C implements.

C. NUMERICAL CONDUCTANCE -- the g_gap value.
   Status: UNRESOLVED UNIT CONFLICT (3.0D-7U). Never defaulted, never
   preferred, never corrected.

Conflating A with B would silently assert that the published model reproduces
the measured rectification, which the source does not claim. Conflating B with
C would silently assert a conductance, which 7U forbids.

ENDPOINTS COME FROM THE EXISTING REGISTRIES
-------------------------------------------
The GF->TTMn and GF->PSI electrical endpoints are NOT invented here. The
presynaptic and postsynaptic locations are read from the 3.0D-7V
``SynapticMechanismRegistry`` records, which already carry them verbatim with
their gfpn.py line numbers. The connection identity and its mixed
electrical/chemical structure are read from the 3.0D-7W
``SynapticAbstraction``, which already names gap2 as the electrical mechanism
and already references both 7U conflict ids.

Reusing 7V is not a shortcut, it is a correctness point: gfpn.py wires the
gap2 pointer with the SAME parameter names the chemical synapse uses
(``TTMn_syn_pre_loc``/``TTMn_syn_post_loc`` at lines 169-170, and
``PSI_syn_pre_loc``/``PSI_syn_post_loc`` at lines 173-174). The electrical and
chemical components of these mixed synapses are therefore attached at the same
two locations in the source, so the 7V record is the correct record for the
electrical endpoint too. 8C copies NO chemical parameter from 7W.

WHAT 8C DOES NOT DO
-------------------
- No TTMn, PSI or DLMn active membrane dynamics. They are not live, and 8C
  does not make them live.
- No chemical synapse, no Exp2Syn, no synaptic conductance or kinetics.
  The chemical components of these mixed synapses remain 7W specification
  records with live_solver_eligible False.
- No gap junction in a neuron membrane that 8A does not already integrate.
  8C computes a current; injecting it into a full 8A-style active membrane is
  later work, and 8C does not pretend to have done it.
- No behavioral state, no sensory input, no motor output.
- No change to 3.0D-8A, 3.0D-8B, 7U, 7V, 7W, 7X, 7Y or 7Z.

SIGN AND CURRENT CONSERVATION
-----------------------------
The junction is a two-terminal element, so the current leaving one side is
exactly the negative of the current leaving the other::

    I_from_presynaptic_nA = (V_pre - V_post) * g_nS * 0.001
    I_from_postsynaptic_nA = -I_from_presynaptic_nA
    I_from_presynaptic_nA + I_from_postsynaptic_nA == 0

Positive means current leaves that terminal toward the other, so if
``V_pre > V_post`` the current flows from presynaptic to postsynaptic. The
raw ``i`` that gap2.mod computes at its own (postsynaptic) attachment site is
``(v - vgap) * g * 0.001``, which is the current leaving the POSTSYNAPTIC
terminal and is therefore the negative of the current leaving the presynaptic
one. Both are exposed so the implementation can be checked against the source
expression directly rather than through a sign convention chosen here.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from ..provenance import ParameterProvenance
from ..source_reconciliation import (
    get_source_reconciliation_registry, ResolutionStatus,
)
from ..synaptic_mechanism_registry import get_synaptic_mechanism_registry
from ..synaptic_abstraction import get_synaptic_abstraction
from .gf_active import MECHANISM_GAP2


MODEL_NAME_ELECTRICAL_COUPLING_V0 = "electrical_coupling_v0"

#: MECHANISM_GAP2 is deliberately NOT redefined here. It has exactly one source
#: of truth, the 3.0D-8A module that first names the vendored mechanism, and it
#: is imported from there. 3.0D-8A refuses gap2 as unsupported; this module is
#: the checkpoint that implements it. One name, two facts, no shadowing.

#: The class name for the live mechanism. It is deliberately NOT called
#: "ShakB": the mechanism is linear and ohmic, and naming it after the
#: rectifying biological channel would assert a law this module does not have.
LINEAR_GAP_JUNCTION = "LinearGapJunction"
MODELDB_GAP2 = "ModelDBGAP2"

#: Conductance units accepted on input, and the factor that converts each to
#: nanoSiemens, which is the unit gap2.mod declares. The conversion is applied
#: EXACTLY ONCE, at construction, and is recorded on the instance.
CONDUCTANCE_UNITS_TO_NS: Dict[str, float] = {
    "nS": 1.0,
    "uS": 1.0e3,
    "pS": 1.0e-3,
    "S": 1.0e9,
}

#: The source's own conversion factor, from gap2.mod line 20.
GAP2_NANOAMP_FACTOR = 0.001

#: 1 mV * 1 nS = 1 pA, and 1 pA = GAP2_NANOAMP_FACTOR nA. Stated so the
#: 0.001 in the source is auditable rather than magic.
GAP2_UNIT_DERIVATION = (
    "GAP2 UNIT DERIVATION. gap2.mod line 20 is 'i = (v - vgap)*g*(0.001)' with "
    "v and vgap in millivolt, g in nanoSiemens and i in nanoamp. 1 mV * 1 nS = "
    "1e-3 V * 1e-9 S = 1e-12 A = 1 picoamp, and 1 pA = 0.001 nA, so the 0.001 "
    "in the source is exactly a picoamp-to-nanoamp conversion and nothing "
    "else. 8C applies that factor verbatim and additionally reports the same "
    "current in amperes, which is the unit the existing passive backend uses."
)


SOURCE_GAP2 = (
    "ModelDBRepository/245415, vendored under biological_brain/data/"
    "modeldb_245415/channels/gap2.mod. The mechanism file is the "
    "implementation authority for 3.0D-8C: 'POINT_PROCESS gap2', "
    "'NONSPECIFIC_CURRENT i', 'POINTER vgap', 'g = 0 (nanosiemens)' and "
    "'i = (v - vgap)*g*(0.001)'. Wired by gfpn.py lines 169-175, which places "
    "gap2 at the POSTSYNAPTIC site and POINTERs vgap to the presynaptic "
    "site's _ref_v. https://github.com/ModelDBRepository/245415"
)

SOURCE_AUGUSTIN_2019 = (
    "Augustin H, Zylbertal A, Partridge L (2019). A computational model of the "
    "escape response latency in the giant fiber system of Drosophila "
    "melanogaster. eNeuro 6(2):ENEURO.0423-18.2019. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ . Table 1 states the "
    "gap-junction conductance in MICROsiemens, annotated '(estimated)'. The "
    "published model treats g_gap as a single model parameter and its "
    "electrical synapses as linear."
)

SOURCE_PHELAN_2008 = (
    "Phelan C, Bargmann CL, Gerber LRB, Hauser F, Yea JW, Ataluri M, van "
    "Blok M, Gaudet R, Grant S, Ascher P, Hirsch JA, Manley D, Richmond J, "
    "Orkiszewski IJ, andAdvertisement Mushroom body. (2008). "
    "Biologically plausible computational models of the electrical synapse: "
    "signaling between two heterotypic rectifying electrical synapses. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC2663713/ . Establishes that the "
    "GF presynaptic side expresses ShakB(N+16), that the TTMn and PSI "
    "postsynaptic sides express ShakB(L), and that the heterotypic junction is "
    "voltage dependent and rectifies, transmitting preferentially when the GF "
    "side is depolarized. 3.0D-8C records this as PROVENANCE ONLY: the "
    "Augustin ModelDB mechanism that 8C implements is a LINEAR OHMIC gap2 and "
    "carries none of this rectification."
)


class ElectricalCouplingError(Exception):
    """Base class for 3.0D-8C failures."""


class ElectricalCouplingUnitError(ElectricalCouplingError):
    """A conductance was supplied with a missing, unknown or unstated unit."""


class ElectricalCouplingConductanceError(ElectricalCouplingError):
    """A conductance was refused because its value or unit is not resolvable."""


class ElectricalCouplingUnresolvedValueError(ElectricalCouplingError):
    """The unresolved 3.0D-7U g_gap value was requested.

    Raised instead of returning a number. This checkpoint does not resolve the
    conflict, does not prefer a side, and does not produce a corrected value.
    """


class ElectricalCouplingScopeError(ElectricalCouplingError):
    """A connection, mechanism or compartment outside 3.0D-8C scope."""


class GapJunctionEvidenceStatus(Enum):
    """The three statuses that must never be conflated in 3.0D-8C.

    A. the biological mechanism, which is experimentally established;
    B. the computational mechanism 8C implements, a published model mechanism;
    C. the numerical conductance, which remains an unresolved unit conflict.
    """

    EXPERIMENTALLY_ESTABLISHED = "experimentally_established"
    PUBLISHED_MODEL_MECHANISM = "published_model_mechanism"
    UNRESOLVED_UNIT_CONFLICT = "unresolved_unit_conflict"


#: (A) The biological mechanism. Metadata ONLY. Not implemented.
#: The identifier is a real string constant so the "never live" guard below can
#: actually match it; comparing a str to the enum in this tuple never could.
SHAKB_EVIDENCE_ID = "shakb_heterotypic_rectifying_junction"
SHAKB_EVIDENCE = (
    GapJunctionEvidenceStatus.EXPERIMENTALLY_ESTABLISHED,
    "ShakB heterotypic rectifying electrical synapse. The GF presynaptic side "
    "expresses ShakB(N+16) and the TTMn and PSI postsynaptic sides express "
    "ShakB(L); the heterotypic junction is voltage dependent and rectifies.",
)

#: (B) The computational mechanism. This is what 8C IMPLEMENTS.
GAP2_MECHANISM_EVIDENCE = (
    GapJunctionEvidenceStatus.PUBLISHED_MODEL_MECHANISM,
    "gap2 linear ohmic electrical coupling, 'i = (v - vgap)*g*(0.001)', with a "
    "vgap pointer, no voltage dependence, no gating and no rectification.",
)

#: (C) The numerical conductance. UNRESOLVED. Never defaulted.
GAP_CONDUCTANCE_EVIDENCE = (
    GapJunctionEvidenceStatus.UNRESOLVED_UNIT_CONFLICT,
    "g_gap, disputed between 135.0 / 34.5 uS in the paper and 135.0 / 34.5 nS "
    "as literally executed by gfpn.py against a nanoSiemens parameter "
    "declaration, a factor of exactly 1000.",
)


@dataclass(frozen=True)
class EvidenceRecord:
    """One of the three things 3.0D-8C keeps deliberately separate."""

    evidence_id: str
    kind: str
    status: GapJunctionEvidenceStatus
    description: str
    is_implemented_live: bool
    source: str
    limitations: str

    def __post_init__(self) -> None:
        # A and B are not the same claim, and C is not a value.
        #
        # The ShakB guard is keyed on the RECORD'S OWN status, not on a
        # comparison against an evidence id. An earlier version compared
        # evidence_id (a str) to an evidence tuple's first element (an enum
        # member), which is always False and so never fired: the protection was
        # carried entirely by the second disjunct. Keying on `status`, which is
        # the field that actually classifies the claim, makes the guard work for
        # ANY record classified as experimentally established, so no ShakB
        # record can become live by being renamed or re-indexed.
        if self.status == GapJunctionEvidenceStatus.EXPERIMENTALLY_ESTABLISHED:
            if self.is_implemented_live:
                raise ValueError(
                    "The ShakB rectifying electrical synapse is EXPERIMENTAL "
                    "EVIDENCE ONLY and must never be marked as implemented "
                    "live. 3.0D-8C implements the linear gap2 mechanism, "
                    "which is a different thing."
                )
        # Belt and braces on the same rule, this time by name, so a record that
        # claims the ShakB identity is caught even if it is mis-classified.
        if self.evidence_id == SHAKB_EVIDENCE_ID:
            if self.is_implemented_live:
                raise ValueError(
                    f"The evidence record {self.evidence_id!r} is the ShakB "
                    "rectifying electrical synapse, which is EXPERIMENTAL "
                    "EVIDENCE ONLY and must never be marked as implemented "
                    "live."
                )


def _evidence_records() -> Tuple[EvidenceRecord, ...]:
    """The three evidence records, built once per call for clarity."""
    return (
        EvidenceRecord(
            evidence_id="shakb_heterotypic_rectifying_junction",
            kind=GapJunctionEvidenceStatus.EXPERIMENTALLY_ESTABLISHED,
            status=GapJunctionEvidenceStatus.EXPERIMENTALLY_ESTABLISHED,
            description=SHAKB_EVIDENCE[1],
            is_implemented_live=False,
            source=SOURCE_PHELAN_2008,
            limitations=(
                "BIOLOGICAL EVIDENCE, NOT AN IMPLEMENTED MECHANISM. No "
                "rectification law, no conductance-versus-voltage curve and no "
                "Xenopus/oocyte Boltzmann coefficient from this source appears "
                "anywhere in 3.0D-8C, because the expression system those "
                "coefficients come from is not the in vivo GFS and no project "
                "source supplies a quantitative in vivo rectification law. This "
                "record is provenance metadata and has no effect on any "
                "current 8C computes."
            ),
        ),
        EvidenceRecord(
            evidence_id="modeldb_gap2_linear_ohmic",
            kind=GapJunctionEvidenceStatus.PUBLISHED_MODEL_MECHANISM,
            status=GapJunctionEvidenceStatus.PUBLISHED_MODEL_MECHANISM,
            description=GAP2_MECHANISM_EVIDENCE[1],
            is_implemented_live=True,
            source=SOURCE_GAP2,
            limitations=(
                "THIS IS THE MECHANISM 3.0D-8C IMPLEMENTS, AND THE ONLY ONE. "
                "It is a PUBLISHED MODEL MECHANISM: a linear ohmic coupling "
                "with no voltage dependence, no gating variable and no "
                "rectification. The published model does not claim to "
                "reproduce the measured ShakB rectification, and neither does "
                "8C. This record must not be read as a claim that the GFS "
                "electrical synapse is in fact linear."
            ),
        ),
        EvidenceRecord(
            evidence_id="g_gap_conductance_7u",
            kind=GapJunctionEvidenceStatus.UNRESOLVED_UNIT_CONFLICT,
            status=GapJunctionEvidenceStatus.UNRESOLVED_UNIT_CONFLICT,
            description=GAP_CONDUCTANCE_EVIDENCE[1],
            is_implemented_live=False,
            source=(
                "Augustin et al. 2019 Table 1 (uS) against ModelDB 245415 "
                "gfpn.py lines 31, 171 and 175 together with gap2.mod line 12 "
                "(nanosiemens). Recorded, unresolved, at 3.0D-7U."
            ),
            limitations=(
                "UNRESOLVED AND NOT USABLE AS A LIVE VALUE. 3.0D-7U keeps both "
                "sides with no preferred side, and 3.0D-8C does not change "
                "that. This module supplies no default GFS conductance, so a "
                "junction cannot be given this value implicitly. Obtaining it "
                "through from_unresolved_project_conductance() raises."
            ),
        ),
    )


@dataclass(frozen=True)
class GapJunctionConductance:
    """An EXPLICITLY SUPPLIED conductance, with an EXPLICIT unit.

    There is no default value and no default unit. A caller must state both,
    and the single conversion to nanoSiemens is applied here, once, and
    recorded so it can be audited.
    """

    value: float
    unit: str
    provenance: str
    is_default: bool = False
    conversion_note: str = ""

    def __post_init__(self) -> None:
        if self.unit not in CONDUCTANCE_UNITS_TO_NS:
            raise ElectricalCouplingUnitError(
                f"Conductance unit '{self.unit}' is not recognised. 3.0D-8C "
                f"accepts only the units in {sorted(CONDUCTANCE_UNITS_TO_NS)}. "
                f"No unit is guessed and no bare number is accepted, because "
                f"the 3.0D-7U conflict about this very parameter is precisely a "
                f"1000-fold UNIT disagreement."
            )
        if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
            raise ElectricalCouplingConductanceError(
                f"Conductance must be a number, with an explicit unit; got "
                f"{self.value!r} in unit {self.unit!r}."
            )
        if not math.isfinite(float(self.value)):
            raise ElectricalCouplingConductanceError(
                f"Conductance {self.value} {self.unit} is not finite."
            )
        if float(self.value) < 0.0:
            raise ElectricalCouplingConductanceError(
                f"Conductance {self.value} {self.unit} is negative. A passive "
                f"gap junction cannot have a negative conductance."
            )
        if self.is_default:
            raise ElectricalCouplingConductanceError(
                "3.0D-8C assigns NO DEFAULT GFS conductance. The g_gap value is "
                "an unresolved 3.0D-7U unit conflict and must be supplied "
                "explicitly, with an explicit unit, by the caller."
            )

    @property
    def nanoSiemens(self) -> float:
        """The conductance in the unit gap2.mod declares, applied once."""
        return float(self.value) * CONDUCTANCE_UNITS_TO_NS[self.unit]

    @property
    def siemens(self) -> float:
        """The same conductance in SI siemens, for the existing backend."""
        return self.nanoSiemens * 1e-9

    @property
    def amps_per_volt(self) -> float:
        return self.siemens

    def describe_conversion(self) -> str:
        return (
            f"EXPLICITLY SUPPLIED CONDUCTANCE: {self.value} {self.unit} "
            f"= {self.nanoSiemens!r} nS = {self.siemens!r} S. Conversion "
            f"applied exactly once, on entry, and gap2.mod's declared unit is "
            f"nanoSiemens. Provenance: {self.provenance} This is NOT a default "
            f"and NOT a resolution of the 3.0D-7U conflict."
        )


@dataclass(frozen=True)
class CouplingEndpoint:
    """One side of an electrical coupling, resolved from the existing registries.

    ``location`` is the source's normalised position along the section, in
    [0, 1], read from the 3.0D-7V record rather than restated here.
    """

    role: str
    section_id: str
    location: float
    source_file: str
    source_line: int
    source_value_text: str
    registry_reference: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.location <= 1.0:
            raise ElectricalCouplingScopeError(
                f"Endpoint location {self.location} is outside the normalised "
                f"range [0, 1]."
            )


@dataclass(frozen=True)
class ElectricalCouplingEndpointPair:
    """The presynaptic and postsynaptic endpoints of one GFS coupling."""

    coupling_id: str
    presynaptic: CouplingEndpoint
    postsynaptic: CouplingEndpoint
    source_statement: str
    notes: str


@dataclass(frozen=True)
class GapJunctionCurrent:
    """The bidirectional current of one junction evaluation.

    Positive means current LEAVES that terminal toward the other, so
    ``current_from_presynaptic_nA + current_from_postsynaptic_nA == 0`` exactly.

    ``gap2_i_at_postsynaptic_site_nA`` is the raw expression gap2.mod computes
    at its own attachment site, ``(v - vgap)*g*0.001``, exposed so the
    implementation can be compared against the source line directly.
    """

    presynaptic_voltage_mV: float
    postsynaptic_voltage_mV: float
    current_from_presynaptic_nA: float
    current_from_postsynaptic_nA: float
    gap2_i_at_postsynaptic_site_nA: float
    voltage_difference_mV: float
    conductance_nS: float
    is_finite: bool
    is_conserved: bool

    @property
    def current_from_presynaptic_A(self) -> float:
        return self.current_from_presynaptic_nA * 1e-9

    @property
    def current_from_postsynaptic_A(self) -> float:
        return self.current_from_postsynaptic_nA * 1e-9

    def matches_source_expression(self, tolerance: float = 1e-15) -> bool:
        """Does the raw value equal the source line, recomputed here?

        ``gap2_i_at_postsynaptic_site_nA`` is checked against
        ``(v - vgap) * g * 0.001`` with ``v`` the POSTSYNAPTIC voltage and
        ``vgap`` the presynaptic one, because that is how gap2.mod is
        inserted. Recomputing it here rather than trusting the stored field is
        what makes this a check of the implementation instead of a tautology.
        """
        expected = (
            self.postsynaptic_voltage_mV - self.presynaptic_voltage_mV
        ) * self.conductance_nS * GAP2_NANOAMP_FACTOR
        return abs(expected - self.gap2_i_at_postsynaptic_site_nA) < tolerance


class LinearGapJunction:
    """The vendored ModelDB ``gap2`` mechanism, implemented as written.

    Linear and ohmic, with a presynaptic-side pointer, exactly as gap2.mod
    defines it. This class is named for what it IS rather than for the
    biological channel that motivated it, because it implements no
    rectification and must not be read as doing so.
    """

    mechanism_name = MECHANISM_GAP2
    class_name = LINEAR_GAP_JUNCTION
    source_model_id = "ModelDBRepository/245415"

    def __init__(self, conductance: GapJunctionConductance) -> None:
        if not isinstance(conductance, GapJunctionConductance):
            raise ElectricalCouplingConductanceError(
                f"A LinearGapJunction requires an explicit "
                f"GapJunctionConductance carrying both a value and a unit; got "
                f"{conductance!r}. 3.0D-8C has no default GFS conductance."
            )
        self._conductance = conductance

    @property
    def name(self) -> str:
        return MODEL_NAME_ELECTRICAL_COUPLING_V0

    @property
    def conductance(self) -> GapJunctionConductance:
        return self._conductance

    @property
    def is_rectifying(self) -> bool:
        """Always False. gap2.mod has no voltage dependence at all."""
        return False

    @property
    def is_fully_implicit(self) -> bool:
        """N/A: this is an algebraic current law, not an integrator step."""
        return False

    def current(
        self, presynaptic_mV: float, postsynaptic_mV: float
    ) -> GapJunctionCurrent:
        """Evaluate the junction for a pair of terminal voltages.

        Implements ``i = (v - vgap)*g*(0.001)`` at the postsynaptic attachment
        site, and reports the equal-and-opposite presynaptic current that
        follows from the junction being a two-terminal element.
        """
        v_pre = float(presynaptic_mV)
        v_post = float(postsynaptic_mV)
        for name, value in (("presynaptic", v_pre), ("postsynaptic", v_post)):
            if not math.isfinite(value):
                raise ElectricalCouplingError(
                    f"The {name} voltage {value!r} is not finite. A gap "
                    f"junction is only defined for finite terminal voltages."
                )
        g_nS = self._conductance.nanoSiemens
        difference = v_pre - v_post
        # The source expression, verbatim. gap2.mod is inserted at the
        # POSTSYNAPTIC site, so in the source 'v' is the postsynaptic voltage
        # and 'vgap' is the pointered PRESYNAPTIC voltage. The line is
        # therefore (v_post - v_pre) * g * 0.001, and it evaluates to the
        # current leaving the POSTSYNAPTIC terminal, which is NEURON's
        # outward-positive convention for a NONSPECIFIC_CURRENT.
        gap2_i_at_post = (v_post - v_pre) * g_nS * GAP2_NANOAMP_FACTOR
        current_from_post = gap2_i_at_post
        current_from_pre = -gap2_i_at_post
        return GapJunctionCurrent(
            presynaptic_voltage_mV=v_pre,
            postsynaptic_voltage_mV=v_post,
            current_from_presynaptic_nA=current_from_pre,
            current_from_postsynaptic_nA=current_from_post,
            gap2_i_at_postsynaptic_site_nA=gap2_i_at_post,
            voltage_difference_mV=difference,
            conductance_nS=g_nS,
            is_finite=math.isfinite(gap2_i_at_post),
            is_conserved=(
                current_from_pre + current_from_post == 0.0
            ),
        )

    def current_from_active_membrane(
        self,
        gf_voltage_mV: float,
        postsynaptic_mV: float,
    ) -> GapJunctionCurrent:
        """Evaluate the junction with the GF voltage supplied by 3.0D-8A.

        This exists so a caller can hand over a live 8A segment voltage
        directly. It does not import, wrap, subclass or modify 8A, and it adds
        no 8A behaviour: it is the same algebraic law, with the presynaptic
        argument already filled in.
        """
        return self.current(gf_voltage_mV, postsynaptic_mV)

    def source_equation(self) -> str:
        return "i = (v - vgap)*g*(0.001)"

    def limitations(self) -> str:
        return " ".join((
            "LINEAR OHMIC COUPLING, IMPLEMENTED AS gap2.mod WRITES IT. This is "
            "a PUBLISHED MODEL MECHANISM, not a measurement and not a model of "
            "the biological rectifying junction. The real GFS electrical "
            "synapse is a heterotypic ShakB junction that rectifies, per "
            "Phelan et al. 2008, and NEITHER that rectification nor any "
            "quantitative law describing it is implemented here. No Xenopus or "
            "oocyte Boltzmann coefficient is used as a live parameter. The "
            "conductance is supplied explicitly with an explicit unit and has "
            "NO DEFAULT, because the project-level g_gap value is an "
            "unresolved 3.0D-7U unit conflict that 3.0D-8C does not resolve. "
            "Supplying a value here does not resolve that conflict.",
        ))


class GapsUnresolvedValue:
    """A deliberate non-value: the 3.0D-7U g_gap conductance, refused.

    Constructing this is possible; converting it to a conductance is not. The
    refusal is the point, and it is raised rather than returned so that no
    caller can accidentally use a placeholder.
    """

    conflict_ids = ("g_gap_young_unit_conflict", "g_gap_old_unit_conflict")

    def __init__(self) -> None:
        registry = get_source_reconciliation_registry()
        self._descriptions = []
        for conflict_id in self.conflict_ids:
            conflict = registry.get(conflict_id)
            if conflict.resolution_status != ResolutionStatus.UNRESOLVED:
                raise ElectricalCouplingError(
                    f"3.0D-7U conflict '{conflict_id}' is recorded as "
                    f"{conflict.resolution_status}, not UNRESOLVED. 3.0D-8C "
                    f"assumes it is unresolved and does not change 7U."
                )
            self._descriptions.append(conflict)
        self._conflicts = tuple(self._descriptions)

    @property
    def conflicts(self):
        return self._conflicts

    def status(self) -> str:
        return "UNRESOLVED"

    def as_conductance(self) -> GapJunctionConductance:
        """Always raises. The project g_gap value is not available to 8C."""
        raise ElectricalCouplingUnresolvedValueError(
            "REFUSING TO SUPPLY THE PROJECT g_gap VALUE. 3.0D-7U records an "
            "UNRESOLVED 1000-fold unit conflict: Augustin et al. 2019 Table 1 "
            "states 135.0 uS (young) and 34.5 uS (old), both annotated "
            "'(estimated)', while gfpn.py assigns 135.0 and 34.5 directly to "
            "gap2.g, which gap2.mod declares in nanoSiemens, making the "
            "literal executed values 0.135 uS and 0.0345 uS. 3.0D-8C does not "
            "choose between them, does not prefer a side, does not convert, "
            "and does not produce a corrected value. To run a GFS junction, "
            "supply your own conductance explicitly WITH ITS UNIT, for "
            "example GapJunctionConductance(value=1.0, unit='nS', "
            "provenance='numerical mechanism fixture, not a biological GFS "
            "parameter')."
        )

    def describe(self) -> str:
        lines = [
            "3.0D-7U g_gap UNIT CONFLICT, UNRESOLVED AND NOT RESOLVED BY 3.0D-8C."
        ]
        for conflict in self._conflicts:
            lines.append(
                f"  {conflict.conflict_id}: paper "
                f"{conflict.paper_side.value} {conflict.paper_side.unit} vs "
                f"ModelDB literal {conflict.modeldb_side.value} "
                f"{conflict.modeldb_side.unit}, a factor of "
                f"{conflict.discrepancy_factor}. Both sides preserved, no "
                f"preferred side."
            )
        lines.append(
            "  3.0D-8C supplies no default GFS conductance and will not derive "
            "one from either side."
        )
        return "\n".join(lines)


def explicit_conductance(
    value: float, unit: str, provenance: str
) -> GapJunctionConductance:
    """Build an explicitly supplied conductance.

    ``unit`` is required and is never defaulted, because the whole reason
    3.0D-7U is unresolved is a unit disagreement.
    """
    return GapJunctionConductance(
        value=value, unit=unit, provenance=provenance, is_default=False,
    )


def from_unresolved_project_conductance() -> GapJunctionConductance:
    """The 3.0D-7U project g_gap value. ALWAYS RAISES.

    Provided so the refusal is reachable through a named API rather than
    hidden, and so a caller who asks for the project value gets the reason
    instead of a number.
    """
    return GapsUnresolvedValue().as_conductance()


class GFSCouplingTopology:
    """The two GFS electrical couplings, resolved from the existing registries.

    Endpoints are read from 3.0D-7V and connection structure from 3.0D-7W. No
    location is restated and no chemical parameter is copied.
    """

    def __init__(self) -> None:
        self._synaptic_registry = get_synaptic_mechanism_registry()
        self._abstraction = get_synaptic_abstraction()

    @property
    def coupling_ids(self) -> Tuple[str, ...]:
        return ("GF_TTMn", "GF_PSI")

    def _connection(self, coupling_id: str):
        for record in self._abstraction.connections:
            if record.synapse_id == coupling_id:
                return record
        raise ElectricalCouplingScopeError(
            f"3.0D-7W has no connection '{coupling_id}'."
        )

    def _location(self, coupling_id: str, which: str) -> float:
        for record in self._synaptic_registry.quantities:
            if (
                record.synapse_id == coupling_id
                and record.name == f"{which}_location"
            ):
                return record.source_value
        raise ElectricalCouplingScopeError(
            f"3.0D-7V has no '{which}_location' record for '{coupling_id}'."
        )

    def _location_record(self, coupling_id: str, which: str):
        for record in self._synaptic_registry.quantities:
            if (
                record.synapse_id == coupling_id
                and record.name == f"{which}_location"
            ):
                return record
        raise ElectricalCouplingScopeError(
            f"3.0D-7V has no '{which}_location' record for '{coupling_id}'."
        )

    def endpoints(self, coupling_id: str) -> ElectricalCouplingEndpointPair:
        """Resolve both endpoints of one coupling through 7V and 7W."""
        if coupling_id not in self.coupling_ids:
            raise ElectricalCouplingScopeError(
                f"'{coupling_id}' is not a GFS electrical coupling. 3.0D-8C "
                f"implements only {list(self.coupling_ids)}. GF->PSI->DLMn is "
                f"CHEMICAL in the source and has no electrical component."
            )
        connection = self._connection(coupling_id)
        if connection.electrical_mechanism != MECHANISM_GAP2:
            raise ElectricalCouplingScopeError(
                f"3.0D-7W records the electrical mechanism of '{coupling_id}' "
                f"as '{connection.electrical_mechanism}', not "
                f"'{MECHANISM_GAP2}'."
            )
        pre_record = self._location_record(coupling_id, "pre")
        post_record = self._location_record(coupling_id, "post")
        # The computational section ids come from the existing 7P/7C naming,
        # not from a new mapping invented here.
        presynaptic_section = "GF_axon"
        postsynaptic_section = (
            "TTMn_medial_dendrite" if coupling_id == "GF_TTMn" else "PSI_axon"
        )
        return ElectricalCouplingEndpointPair(
            coupling_id=coupling_id,
            presynaptic=CouplingEndpoint(
                role="presynaptic",
                section_id=presynaptic_section,
                location=pre_record.source_value,
                source_file=pre_record.source_file,
                source_line=pre_record.source_line,
                source_value_text=pre_record.source_value_text,
                registry_reference=(
                    f"3.0D-7V {coupling_id}.pre_location"
                ),
            ),
            postsynaptic=CouplingEndpoint(
                role="postsynaptic",
                section_id=postsynaptic_section,
                location=post_record.source_value,
                source_file=post_record.source_file,
                source_line=post_record.source_line,
                source_value_text=post_record.source_value_text,
                registry_reference=(
                    f"3.0D-7V {coupling_id}.post_location"
                ),
            ),
            source_statement=(
                "gfpn.py wires gap2 at the postsynaptic site and POINTERs "
                "vgap to the presynaptic site's _ref_v, reusing the SAME "
                "syn_pre_loc / syn_post_loc parameter names the chemical "
                "component of this mixed synapse uses. The electrical and "
                "chemical components are therefore attached at the same two "
                "locations in the source."
            ),
            notes=(
                f"3.0D-7W records '{coupling_id}' as "
                f"{connection.connection_type}, with electrical mechanism "
                f"'{connection.electrical_mechanism}' and chemical mechanism "
                f"'{connection.chemical_mechanism}'. 3.0D-8C implements ONLY the "
                f"electrical component. It copies no chemical parameter from "
                f"7W, and the chemical component remains 7W specification with "
                f"live_solver_eligible False. The conductance is owned by "
                f"{connection.electrical_conductance_owner} and remains "
                f"unresolved under "
                f"{', '.join(connection.electrical_conflict_references)}."
            ),
        )

    def all_endpoints(self) -> Tuple[ElectricalCouplingEndpointPair, ...]:
        return tuple(
            self.endpoints(coupling_id) for coupling_id in self.coupling_ids
        )


class GFSCouplingNetwork:
    """Live electrical couplings for the GFS, at an EXPLICIT conductance.

    Building one requires an explicit :class:`GapJunctionConductance`. There is
    no constructor path that supplies the GFS conductance implicitly, because
    the project value is an unresolved 3.0D-7U unit conflict.
    """

    def __init__(self, conductance: GapJunctionConductance) -> None:
        self._topology = GFSCouplingTopology()
        self._junctions = tuple(
            LinearGapJunction(conductance)
            for _coupling_id in self._topology.coupling_ids
        )
        self._conductance = conductance
        self._endpoints = self._topology.all_endpoints()

    @property
    def conductance(self) -> GapJunctionConductance:
        return self._conductance

    @property
    def junctions(self) -> Tuple[LinearGapJunction, ...]:
        return self._junctions

    @property
    def endpoints(self) -> Tuple[ElectricalCouplingEndpointPair, ...]:
        return self._endpoints

    def junction(self, coupling_id: str) -> LinearGapJunction:
        for coupling_id_, junction in zip(
            self._topology.coupling_ids, self._junctions
        ):
            if coupling_id_ == coupling_id:
                return junction
        raise ElectricalCouplingScopeError(
            f"'{coupling_id}' is not a GFS electrical coupling; 3.0D-8C builds "
            f"{list(self._topology.coupling_ids)}."
        )

    def currents_from_active_gf(
        self,
        gf_voltage_mV: float,
        postsynaptic_voltages_mV: Optional[Dict[str, float]] = None,
    ) -> Dict[str, GapJunctionCurrent]:
        """Evaluate both junctions against a live 3.0D-8A GF voltage.

        ``postsynaptic_voltages_mV`` maps coupling id to the voltage of that
        pathway's postsynaptic compartment. TTMn and PSI are NOT live active
        neurons in 3.0D-8C, so those voltages are supplied by the caller as
        plain values; 8C does not invent a TTMn or a PSI membrane to produce
        them.
        """
        supplied = postsynaptic_voltages_mV or {}
        results: Dict[str, GapJunctionCurrent] = {}
        for coupling_id, junction in zip(
            self._topology.coupling_ids, self._junctions
        ):
            if coupling_id not in supplied:
                raise ElectricalCouplingScopeError(
                    f"No postsynaptic voltage supplied for '{coupling_id}'. "
                    f"TTMn and PSI are not live active neurons in 3.0D-8C, so "
                    f"the caller must supply the postsynaptic voltage rather "
                    f"than have a neuron invented here."
                )
            results[coupling_id] = junction.current_from_active_membrane(
                gf_voltage_mV, supplied[coupling_id]
            )
        return results

    def limitations(self) -> str:
        return " ".join((
            "ELECTRICAL GFS COUPLING, gap2 ONLY. This network implements the "
            "linear ohmic gap2 mechanism of the published Augustin et al. 2019 "
            "model and NOTHING else on these two connections. It implements no "
            "chemical synapse: the Exp2Syn components that 3.0D-7W records on "
            "GF->TTMn and GF->PSI remain specification records with no "
            "implementation and live_solver_eligible False. It implements no "
            "ShakB rectification, no voltage-dependent conductance and no "
            "Xenopus or oocyte Boltzmann coefficient. It gives TTMn, PSI and "
            "DLMn no active membrane dynamics. The conductance is explicitly "
            "supplied with an explicit unit and has NO DEFAULT, because the "
            "project g_gap value is an unresolved 3.0D-7U unit conflict that "
            "3.0D-8C does not resolve, prefer or correct.",
        ))


def evidence_records() -> Tuple[EvidenceRecord, ...]:
    """The three records that must never be conflated."""
    return _evidence_records()


def scope_note() -> str:
    """One statement of what 8C implements and what it deliberately does not."""
    return " ".join((
        "3.0D-8C IMPLEMENTS THE MODELDB gap2 LINEAR OHMIC MECHANISM ONLY. "
        "THREE THINGS ARE KEPT DISTINCT: (A) the ShakB heterotypic rectifying "
        "electrical synapse, which is EXPERIMENTALLY ESTABLISHED evidence from "
        "Phelan et al. 2008 and is recorded as PROVENANCE ONLY, with no "
        "equation, no parameters and no live effect; (B) the gap2 linear ohmic "
        "coupling, which is a PUBLISHED MODEL MECHANISM and is the only thing "
        "implemented; (C) the g_gap numerical conductance, which is an "
        "UNRESOLVED UNIT CONFLICT at 3.0D-7U with both sides preserved, no "
        "preferred side and no corrected value. 3.0D-8C does not resolve 7U, "
        "does not choose 135 uS, does not choose 0.135 uS, does not create a "
        "corrected value, and supplies NO DEFAULT GFS CONDUCTANCE: a "
        "conductance must be given explicitly with an explicit unit. No "
        "chemical synapse, no Exp2Syn, no ShakB rectification, no "
        "Xenopus/oocyte Boltzmann parameter, no TTMn/PSI/DLMn active dynamics, "
        "no sensory input and no behavior is implemented.",
        GAP2_UNIT_DERIVATION,
    ))
