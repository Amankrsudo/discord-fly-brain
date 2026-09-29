"""3.0D-8F: the LIVE DLMn ACTIVE NEURON.

WHAT THIS CHECKPOINT IS
-----------------------
3.0D-8A made the GF axon live, 3.0D-8D the TTMn axon, 3.0D-8E the PSI axon.
3.0D-8F makes the DLMn axon live, completing the fourth cell of the published
Augustin et al. 2019 giant fiber system model. It uses the SAME mechanism engine
and the SAME equations: there is exactly ONE implementation of the nat/nap/k
mechanism in this project, in ``biological_brain/dynamics/gf_active.py``, and
this module is a CONFIGURATION of that engine, not a fourth copy of it.

DLMn STRUCTURE
--------------
::

    DLMn_dendrite (PASSIVE) --.  >-- DLMn_axon (ACTIVE, TAPERING)

Only ``DLMn_axon`` carries the active density channels. ``DLMn_dendrite`` is
carried in the same network and participates in the passive cable solve, but it
receives NONE of the active conductances, so it is genuinely passive rather than
merely labelled passive. The dendrite-to-axon connection is the existing 3.0D-7P
computational topology (``DLMn_pas.connect(DLMn, 0, 0)``, gfpn.py line 121), read
from the model, never rebuilt here.

THE TAPER IS REAL GEOMETRY, AND 3.0D-8F IS THE FIRST LIVE NEURON TO EXERCISE IT
-----------------------------------------------------------------------------
GF, TTMn and PSI all have uniform-diameter axons. The DLMn axon is the first
section in this project that is a genuinely LINEARLY TAPERED circular cable, and
making it live therefore exercises the 3.0D-7J/7K taper machinery in the ACTIVE
solver rather than only in the passive backend.

The taper is NOT approximated, averaged or replaced by a single equivalent
diameter. It is represented exactly as the existing implementation defines it:

- membrane area per segment is the true lateral area of a conical FRUSTUM,
  ``pi * (r1 + r2) * sqrt(L^2 + (r2 - r1)^2)``, which accounts for the slant
  length rather than treating the taper as a cylinder;
- axial resistance per segment is the tapered-cable form
  ``R = Ra * L / (pi * r1 * r2)``, not the uniform-cylinder ``Ra * L / (pi r^2)``;
- segment diameters are the source linear taper evaluated at each segment's two
  endpoints, by the existing ``derive_segments`` interpolation.

Both of those are the existing 3.0D-7J/7K formulations. 3.0D-8F defines no new
taper equation, no new membrane-area formula and no new resistance formula, and
it does not alter the subdivision policy: ``segment_count`` remains the explicit
numerical configuration 7K defines, defaulting to 1.

Subdivision CONSERVES the taper. The sum of the per-segment frustum areas is
identical to the un-subdivided section area (471.333136395 um2) at every
subdivision, and the sum of the per-segment tapered axial resistances equals the
whole-section tapered resistance (2817042.492727 ohm) at every subdivision. 8F
asserts both, so a regression that quietly degraded the taper would be caught
here rather than silently changing the DLMn's electrical behaviour.

ONE TOPOLOGICAL CONSEQUENCE WORTH RECORDING
------------------------------------------
Because the DLMn soma's geometry is insufficient for electrical representation
(3.0D-7I), ``DLMn_axon`` is an electrical ROOT in the 7Q computational
abstraction. Its first derived segment therefore has no proximal neighbour and
records ``axial_resistance_ohm`` as None: there is no proximal axial connection
to carry a resistance. This is a property of the existing topology, not a
missing value, and 8F does not invent a parent connection to fill it. The
conservation statement is therefore made over each segment's OWN tapered
resistance, which is what the frustum formulation defines, and the sum of the
N-1 recorded internal interfaces equals the whole-section value minus the root
segment's own resistance.

SOURCE BASIS, AND WHAT IS NOT A MEASUREMENT
-------------------------------------------
The geometry is the published Augustin et al. 2019 (eLife, PMC6469880) model
morphology already recorded at 3.0D-7B: DLMn dendrite 100 um x 2 um, DLMn axon
50 um tapering from 2 um proximally to 4 um distally. All five values are
``PUBLISHED_MODEL_PARAMETER``: unlike the PSI dendrite length, NOTHING about the
DLMn geometry is classified ESTIMATED, and 8F does not reclassify anything. The
passive parameters are the 3.0D-7F authorized profile (Cm 1 uF/cm2, Ra 35.4
ohm*cm, leak density 0.03 mS/cm2, E_leak -85 mV). The active parameters are the
3.0D-7S authorized Augustin profile (g_Nat 300 mS/cm2, g_Nap 0.11 mS/cm2, g_K 10
mS/cm2, E_Na +65 mV, E_K -74 mV), consumed unchanged. The rate equations are the
vendored ``nat.mod``, ``nap.mod`` and ``k.mod``.

ALL active and passive parameters here are PUBLISHED COMPUTATIONAL-MODEL
PARAMETERS. None of them is a direct experimental measurement of a DLMn, and
this checkpoint never presents one as one. The equal conductance density across
active sections is the published model's assumption, which 3.0D-8F reproduces
rather than re-derives. Note in particular that the published DLMn active
sections are based on a Drosophila motoneuron model with parameters manually
adjusted, as 3.0D-7S already records.

The PSI input placement at 12.5 um from the proximal end of the DLMn axon is
preserved exactly as 7B recorded it, because it is a source-backed anatomical
placement. 3.0D-8F does NOT act on it: it places no synapse, opens no channel
and drives no synaptic conductance at that location. The placement is anatomy,
not a connection.

WHAT IS EXPLICITLY NOT IMPLEMENTED HERE
---------------------------------------
3.0D-8F is INTRINSIC DLMn DYNAMICS ONLY. The biologically real PSI->DLMn
transmission is NOT implemented. In particular there is NO Dalpha7 kinetics: the
available literature implicates Dalpha7 in PSI->DLMn transmission, but it does
not supply sufficient quantitative kinetics to build a defensible live receptor
model, so none is invented. There is no Exp2Syn, no chemical synapse, no
neurotransmitter release, no receptor kinetics, no gap junction, no ShakB, no
calcium, DmCa1D, Slowpoke, Shaker or Para channel, no Q10, no sensory input, no
motor output, no NMJ, no muscle and no behaviour.

The existence of the PSI->DLMn connection is already represented qualitatively in
the 3.0D-7W abstraction layer. 3.0D-8F does not turn it into a quantitative live
synapse and does not connect the circuit: 8F is the DLMn neuron alone. The
unresolved 3.0D-7U gap-junction unit conflict is neither touched nor resolved.

THE DIRECT-STIMULUS FIXTURE
---------------------------
Augustin et al. 2019 reports no direct-stimulation amplitude or duration for the
DLMn, so 3.0D-8F cannot reproduce any such experiment and does not claim to. The
paper's approximately 0.3 ms direct-stimulation timing was described for the TTMn
specifically, and the paper does not supply the parameters needed to treat it as
a DLMn calibration target; 3.0D-8F therefore does NOT treat it as one and does
not fabricate a DLMn experimental latency. The paper's published 120 nA / 0.03 ms
value belongs to the paper's GF circuit simulation and is explicitly NOT a DLMn
stimulus; it is not borrowed.

Instead this module declares its OWN numerical fixture, chosen by 3.0D-8F to be
comfortably supra-threshold for the vendored mechanism on this thin tapered axon
and numerically convergent. It is a NUMERICAL SOLVER FIXTURE for exercising the
solver. It is NOT a DLMn rheobase, NOT a DLMn spike threshold, NOT a
physiological or sensory input, and NOT a measurement. The emergent peak latency
and amplitude under this fixture are numerical results of this implementation
and reproduce no experimental DLMn timing.

The fixture amplitude is SMALLER than the 50 nA used for GF, TTMn and PSI, and
that difference is a discretisation fact rather than a biological one. The DLMn
axon is a 2-4 um taper whose proximal segment has roughly twenty times less
membrane area than the corresponding GF segment, so the same current would move
the membrane twenty times further in a single step. The 50 nA value drives the
linearised implicit step about 1.67 V in one 0.01 ms step, which overshoots E_Na
and destroys timestep convergence. 3.0D-8F therefore sizes the fixture to THIS
geometry, on numerical grounds only, and makes NO claim that a DLMn needs less
current to fire than any other neuron.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from ..morphology import CompartmentModel
from ..passive_profiles import PROFILE_AUGUSTIN_2019_GFS_PASSIVE
from ..active_profiles import PROFILE_AUGUSTIN_2019_ACTIVE_MODEL
from .gf_active import ActiveAxonModel, GFActiveNetwork

MODEL_NAME_DLMN_ACTIVE_V0 = "dlmn_active_v0"

#: The neuron this checkpoint activates.
NEURON_DLMN = "DLMn"

#: The ONE section that carries the active density channels. The published model
#: makes the DLMn axon active; the dendrite is passive. This section TAPERS.
DLMN_ACTIVE_SECTION_ID = "DLMn_axon"

#: The passive section, carried in the same network with no active channel.
DLMN_PASSIVE_SECTION_IDS: Tuple[str, ...] = ("DLMn_dendrite",)

# -- the direct-stimulation numerical fixture ----------------------------------
#
# WHY THIS AMPLITUDE IS SMALLER THAN THE GF / TTMn / PSI FIXTURES
# --------------------------------------------------------------
# The other three neurons use 50 nA. That value is NOT portable to the DLMn,
# and reusing it here would have been a numerical error dressed up as
# consistency. All four axons share the same g_Nat density, so they share the
# same membrane time constant Cm/g_Nat of about 3.3 us, but they do NOT share a
# membrane AREA: at segment_count=11 the DLMn axon's proximal segment is
# 29.86 um2 (0.299 pF), roughly twenty times smaller than the corresponding GF
# segment, because the DLMn axon is a thin 2-4 um taper rather than an 8 um
# cylinder. A fixed current into a twenty-fold smaller capacitance produces a
# twenty-fold larger single-step voltage excursion, and the linearised implicit
# step cannot represent that.
#
# Measured consequence: 50 nA into the DLMn axon moves the membrane 1.67 V in
# ONE 0.01 ms step. The solution overshoots E_Na to about +179 mV, the peak
# lands on the very first sample, and the timestep-refinement spread blows out to
# 5.5 mV. That is a discretisation artefact of an over-driven thin compartment,
# not a property of a DLMn.
#
# This amplitude is therefore chosen for THIS geometry: it is comfortably
# supra-threshold for the vendored mechanism while keeping the per-step
# excursion inside what the linearised solve represents. It was selected on
# NUMERICAL grounds alone (peak below E_Na, refinement spread well inside the
# existing 0.5 mV convergence label, a resolved rather than first-sample peak,
# and a genuine repolarisation) and on no biological criterion whatsoever.
#
# It is emphatically NOT a claim that a DLMn needs less current to fire than a
# GF, a TTMn or a PSI. A rheobase comparison between neurons would require
# matching stimulation geometry and a defensible per-neuron input resistance,
# neither of which exists here, and no such comparison is made or implied.
DLMN_DIRECT_STIMULUS_AMPLITUDE_A = 20.0e-9
DLMN_DIRECT_STIMULUS_DURATION_MS = 0.03
DLMN_DIRECT_STIMULUS_LOCATION = "DLMn_axon#seg0"

DLMN_DIRECT_STIMULUS_PROVENANCE = (
    "NUMERICAL SOLVER FIXTURE, CHOSEN BY 3.0D-8F. THIS IS NOT A BIOLOGICAL DLMn "
    "STIMULUS. Augustin et al. 2019 reports no direct-stimulation amplitude or "
    "duration for the DLMn, so no such experiment is reproduced here. The "
    "paper's approximately 0.3 ms direct-stimulation timing was described for "
    "the TTMn specifically, and the paper does not supply the parameters needed "
    "to treat it as a DLMn calibration target, so 3.0D-8F does NOT treat it as "
    "one and fabricates no DLMn experimental latency. The published 120 nA / "
    "0.03 ms value belongs to the paper's GF circuit simulation and is "
    "explicitly NOT a DLMn stimulus; it is not borrowed. This amplitude was "
    "selected by 3.0D-8F as comfortably supra-threshold for the vendored "
    "mechanism on this thin tapered axon and numerically convergent across "
    "segment counts and timesteps. It is a solver fixture. It is NOT a DLMn "
    "rheobase, NOT a DLMn spike threshold, NOT a physiological or sensory "
    "input, and NOT a measurement of anything. The amplitude is SMALLER than "
    "the GF, TTMn and PSI fixtures because the DLMn axon segment is roughly "
    "twenty times smaller in membrane area, and a fixed current into a "
    "twenty-fold smaller capacitance produces a twenty-fold larger single-step "
    "excursion that the linearised implicit solve cannot represent. That is a "
    "DISCRETISATION CONSTRAINT of this geometry, and it is NOT a claim that a "
    "DLMn needs less current to fire than a GF, a TTMn or a PSI."
)


@dataclass(frozen=True)
class DLMNSectionRole:
    """Which DLMn sections are active and which are passive, and why.

    This is a REPORT of what was built, read back off the prepared network, not
    a declaration written in advance. ``DLMn_axon`` is the only active section.
    """

    active_section_ids: Tuple[str, ...]
    passive_section_ids: Tuple[str, ...]
    basis: str

    def is_active_section(self, section_id: str) -> bool:
        return section_id in self.active_section_ids


class DLMNActiveAxonModel(ActiveAxonModel):
    """3.0D-8F configuration of the shared active-axon mechanism engine.

    This class defines NO mechanism. It pins the shared engine to the DLMn
    neuron and the DLMn axon, declares the dendrite passive, names its own
    stimulation fixture, and adds only DLMn-shaped reporting on top. Every
    equation, the exact ``cnexp`` gate solution and the implicit membrane solve
    are inherited unchanged from :class:`ActiveAxonModel`, the same object 3.0D-8A
    built and 3.0D-8D and 3.0D-8E reused.

    The runs are NOT redefined here. ``equilibrium_report()``,
    ``stimulus_response()``, ``voltages_mV()``, ``axon_diagnostic()``,
    ``passive_are_inert()`` and ``with_active_conductances_removed()`` are the
    GENERIC implementations 3.0D-8E lifted onto the shared engine. 3.0D-8F is the
    second neuron to use them without a per-neuron copy, which is the whole point
    of that refactor: the four published GFS cells are now four CONFIGURATIONS of
    one engine, and adding the fourth required no new numerical code at all.

    What makes DLMn different from GF, TTMn and PSI is its TAPERED axon, and that
    difference is handled entirely by the existing 3.0D-7J/7K geometry, which
    this adapter does not touch. No taper equation, no area formula and no
    subdivision behaviour is defined or modified here.
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
            neuron_id=NEURON_DLMN,
            active_section_id=DLMN_ACTIVE_SECTION_ID,
        )

    @property
    def name(self) -> str:
        return MODEL_NAME_DLMN_ACTIVE_V0

    @property
    def passive_section_ids(self) -> Tuple[str, ...]:
        """The DLMn sections that stay passive, with no active channel."""
        return DLMN_PASSIVE_SECTION_IDS

    @property
    def stimulus_fixture_amplitude_A(self) -> float:
        """3.0D-8F's OWN numerical fixture. NOT a biological DLMn stimulus."""
        return DLMN_DIRECT_STIMULUS_AMPLITUDE_A

    @property
    def stimulus_fixture_duration_ms(self) -> float:
        """3.0D-8F's OWN numerical fixture duration. Not a biological value."""
        return DLMN_DIRECT_STIMULUS_DURATION_MS

    # -- structure ----------------------------------------------------------

    def prepare_dlmn(
        self, model: CompartmentModel, segment_count: int = 1
    ) -> GFActiveNetwork:
        """Prepare the DLMn network: active tapering axon plus passive dendrite.

        ``segment_count`` subdivides the ACTIVE AXON only, and each derived
        segment of the taper receives its own interpolated proximal/distal
        diameters, its own frustum membrane area and its own tapered axial
        resistance from the existing 3.0D-7J/7K implementation. The dendrite is
        carried at its un-subdivided default.
        """
        return self.prepare_active_axon(model, segment_count=segment_count)

    def section_roles(self, network: GFActiveNetwork) -> DLMNSectionRole:
        """Read back which prepared sections are active and which are passive."""
        active = {
            c.source_section_id
            for c in network.network.compartments
            if network.is_active(c.compartment_id)
        }
        passive = {
            c.source_section_id
            for c in network.network.compartments
            if not network.is_active(c.compartment_id)
        }
        return DLMNSectionRole(
            active_section_ids=tuple(sorted(active)),
            passive_section_ids=tuple(sorted(passive)),
            basis=(
                f"The active density channels are applied ONLY to compartments "
                f"derived from {sorted(active)}. Compartments derived from "
                f"{sorted(passive)} receive no active conductance and are "
                f"passive. This is read back off the prepared network, not "
                f"asserted. The single active section follows the published "
                f"model, which distributes each conductance type with equal "
                f"density across ACTIVE sections only."
            ),
        )


def dlmn_scope_note() -> str:
    """The scope statement 3.0D-8F reports alongside any of its results."""
    return (
        "3.0D-8F MAKES THE DLMn AXON LIVE AND NOTHING ELSE. The active axon is "
        "DLMn_axon, which TAPERS from 2 um proximally to 4 um distally over "
        "50 um; that taper is real geometry, represented with the existing "
        "3.0D-7J/7K frustum membrane area and tapered axial resistance "
        "formulas, and it is never replaced by an averaged diameter. "
        "DLMn_dendrite is carried in the same network and remains PASSIVE, "
        "receiving none of the active conductances while still participating in "
        "the cable solve. The mechanism is the SAME shared engine and the SAME "
        "vendored nat.mod, nap.mod and k.mod equations 3.0D-8A validated, "
        "3.0D-8D reused for TTMn and 3.0D-8E reused for PSI; there is exactly "
        "ONE implementation of them and DLMn does not have a copy. All active "
        "and passive parameters are published computational-model parameters "
        "from the 3.0D-7B morphology, the 3.0D-7F passive profile and the "
        "3.0D-7S Augustin active profile, and none of them is a direct "
        "experimental DLMn measurement. The PSI input placement at 12.5 um on "
        "the DLMn axon is preserved as source-backed ANATOMY but is NOT acted "
        "on: no synapse is placed and no synaptic conductance is applied there. "
        "NO PSI->DLMn synapse is implemented and NO Dalpha7 kinetics are "
        "implemented: Dalpha7 is biologically implicated in PSI->DLMn "
        "transmission but the available sources do not provide sufficient "
        "quantitative kinetics for a defensible live receptor model, so none is "
        "invented. No Exp2Syn, no neurotransmitter release, no gap junction, no "
        "ShakB, no calcium, DmCa1D, Slowpoke, Shaker or Para channel, no Q10, "
        "no sensory input, no NMJ, no muscle and no behavior. The "
        "direct-stimulation amplitude used by the fixture is a NUMERICAL SOLVER "
        "FIXTURE chosen by 3.0D-8F, NOT a biological DLMn stimulus, NOT a "
        "rheobase and NOT a threshold. It is SMALLER than the GF, TTMn and PSI "
        "fixtures because the DLMn axon segment is roughly twenty times smaller "
        "in membrane area, so a fixed current would produce a twenty-fold larger "
        "single-step excursion that the linearised solve cannot represent; that "
        "is a discretisation constraint and is NOT a claim about DLMn excitation "
        "threshold. The 120 nA / 0.03 ms value belongs to the paper's GF circuit "
        "simulation and is deliberately not borrowed, and the paper's "
        "approximately 0.3 ms direct-stimulation timing was described for the "
        "TTMn and is NOT treated as a DLMn calibration target."
    )
