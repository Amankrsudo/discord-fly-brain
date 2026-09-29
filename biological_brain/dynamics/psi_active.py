"""3.0D-8E: the LIVE PSI ACTIVE NEURON.

WHAT THIS CHECKPOINT IS
-----------------------
3.0D-8A made the GF axon live. 3.0D-8D made the TTMn axon live. 3.0D-8E makes
the PSI axon live, using the SAME mechanism engine and the SAME equations.
There is exactly ONE implementation of the nat/nap/k mechanism in this project,
in ``biological_brain/dynamics/gf_active.py``; this module is a CONFIGURATION of
that engine, not a third copy of it. PSI is not a special-case GF and not a
renamed TTMn: it is the same :class:`ActiveAxonModel` with a different
``neuron_id``, a different ``active_section_id`` and one passive section.

PSI STRUCTURE
-------------
::

    PSI_dendrite (PASSIVE) --.  >-- PSI_axon (ACTIVE)

Only ``PSI_axon`` carries the active density channels. ``PSI_dendrite`` is
carried in the same network and participates in the passive cable solve, but it
receives NONE of the active conductances, so it is genuinely passive rather than
merely labelled passive. The dendrite-to-axon connection is the existing
3.0D-7P computational topology (``PSI_pas.connect(PSI, 0, 0)``, gfpn.py line
105), read from the model, never rebuilt here.

SOURCE BASIS, AND WHAT IS NOT A MEASUREMENT
-------------------------------------------
The geometry is the published Augustin et al. 2019 (eLife, PMC6469880) model
morphology already recorded at 3.0D-7B: PSI axon 90 um x 4.5 um, PSI dendrite
170 um x 4.5 um. The passive parameters are the 3.0D-7F authorized profile
(Cm 1 uF/cm2, Ra 35.4 ohm*cm, leak density 0.03 mS/cm2, E_leak -85 mV). The
active parameters are the 3.0D-7S authorized Augustin profile (g_Nat 300
mS/cm2, g_Nap 0.11 mS/cm2, g_K 10 mS/cm2, E_Na +65 mV, E_K -74 mV). The rate
equations are the vendored ``nat.mod``, ``nap.mod`` and ``k.mod``, which the
published model bases on the Guenay et al. motoneuron kinetics.

THE 170 um DENDRITE LENGTH IS ESTIMATED, NOT MEASURED
-----------------------------------------------------
This is the single most important provenance fact in this module. The paper
states the PSI dendrite length was ESTIMATED, and 3.0D-7B records it as
``ParameterProvenance.ESTIMATED`` while every other PSI geometry value is
``PUBLISHED_MODEL_PARAMETER``. 3.0D-8E does NOT upgrade that classification, and
it does not create a second morphology system that could quietly disagree: it
consumes the existing builder, so the ESTIMATED marker is whatever 7B says it
is. A test asserts this explicitly, because silently promoting an estimated
length to a measured one is exactly the kind of provenance drift this project
exists to prevent.

ALL active and passive parameters here are PUBLISHED COMPUTATIONAL-MODEL
PARAMETERS. None of them is a direct experimental measurement of a PSI, and
this checkpoint never presents one as one. The equal conductance density
across active sections is the published model's assumption, which 3.0D-8E
reproduces rather than re-derives.

WHAT IS EXPLICITLY NOT IMPLEMENTED HERE
---------------------------------------
The biologically real GF->PSI connection is NOT implemented, in either form.
There is NO gap junction between GF and PSI (3.0D-8C owns the electrical
primitive; the 3.0D-7U unit conflict is untouched and unresolved) and NO chemical
GF->PSI synapse. There is NO PSI->DLMn synapse, and in particular NO Dalpha7
kinetics: Dalpha7 is biologically implicated in PSI->DLMn transmission, but the
available sources (including Dickson et al. 2000, PMC3667824) do not provide
sufficient quantitative kinetics to build a defensible live receptor model, so
none is invented. There is no ShakB rectification, no calcium, Slowpoke, Shaker
or Para channel, no sensory input, no NMJ, no muscle, no DLM, and no behaviour.

The existence of these connections is already represented qualitatively in the
3.0D-7W / 3.0D-8C abstraction layers. 3.0D-8E does not turn any of them into a
quantitative live synapse, and it does not connect the circuit: 3.0D-8E is the
PSI neuron alone.

THE DIRECT-STIMULUS FIXTURE
---------------------------
Augustin et al. 2019 does not report a direct-stimulation amplitude or duration
for PSI, so 3.0D-8E cannot reproduce any such experiment and does not claim to.
The paper's published 120 nA / 0.03 ms value belongs to the paper's GF circuit
simulation and is explicitly NOT a PSI stimulus; 3.0D-8E does not borrow it,
for the same reason 3.0D-8D did not.

Instead this module declares its OWN numerical fixture, chosen by 3.0D-8E to be
comfortably supra-threshold for the vendored mechanism and numerically
convergent. It is a NUMERICAL SOLVER FIXTURE for exercising the solver. It is
NOT a PSI rheobase, NOT a PSI spike threshold, NOT a physiological input, and
NOT a measurement. The emergent peak latency and amplitude under this fixture
are numerical results of this implementation and reproduce no experimental PSI
timing.

A NOTE ON THE FIXTURE VALUE, SO IT IS NOT MISREAD
------------------------------------------------
The amplitude below happens to equal the value 3.0D-8D independently chose for
its own TTMn fixture. That is a NUMERICAL COINCIDENCE between two separately
declared solver fixtures that both had to be comfortably supra-threshold for
this vendored mechanism on this geometry, and nothing more. It is NOT a shared
biological quantity, NOT evidence of a common PSI/TTMn input, and NOT a claim
that the two neurons share a rheobase. Each constant is declared, named and
provenance-labelled by its own checkpoint, and neither is derived from the
other. The only value that is genuinely NOT reused across neurons is the
published 120 nA / 0.03 ms GF circuit stimulus, which belongs to the paper's GF
simulation and is a model input rather than a solver fixture at all.
"""

from dataclasses import dataclass
from typing import Tuple

from ..morphology import CompartmentModel
from ..passive_profiles import PROFILE_AUGUSTIN_2019_GFS_PASSIVE
from ..active_profiles import PROFILE_AUGUSTIN_2019_ACTIVE_MODEL
from .gf_active import ActiveAxonModel, GFActiveNetwork

MODEL_NAME_PSI_ACTIVE_V0 = "psi_active_v0"

#: The neuron this checkpoint activates.
NEURON_PSI = "PSI"

#: The ONE section that carries the active density channels. The published model
#: makes the PSI axon active; the dendrite is passive.
PSI_ACTIVE_SECTION_ID = "PSI_axon"

#: The passive section, carried in the same network with no active channel.
PSI_PASSIVE_SECTION_IDS: Tuple[str, ...] = ("PSI_dendrite",)

# -- the direct-stimulation numerical fixture ----------------------------------

PSI_DIRECT_STIMULUS_AMPLITUDE_A = 50.0e-9
PSI_DIRECT_STIMULUS_DURATION_MS = 0.03
PSI_DIRECT_STIMULUS_LOCATION = "PSI_axon#seg0"

PSI_DIRECT_STIMULUS_PROVENANCE = (
    "NUMERICAL SOLVER FIXTURE, CHOSEN BY 3.0D-8E. THIS IS NOT A BIOLOGICAL PSI "
    "STIMULUS. Augustin et al. 2019 reports no direct-stimulation amplitude or "
    "duration for PSI, so no such experiment is reproduced here. The published "
    "120 nA / 0.03 ms value belongs to the paper's GF circuit simulation and is "
    "explicitly NOT a PSI stimulus; it is not borrowed. This amplitude was "
    "selected by 3.0D-8E as comfortably supra-threshold for the vendored "
    "mechanism and numerically convergent across segment counts and "
    "timesteps. It is a solver fixture. It is NOT a PSI rheobase, NOT a PSI "
    "spike threshold, NOT a physiological or sensory input, and NOT a "
    "measurement of anything."
)


@dataclass(frozen=True)
class PSISectionRole:
    """Which PSI sections are active and which are passive, and why.

    This is a REPORT of what was built, read back off the prepared network, not
    a declaration written in advance. ``PSI_axon`` is the only active section.
    """

    active_section_ids: Tuple[str, ...]
    passive_section_ids: Tuple[str, ...]
    basis: str

    def is_active_section(self, section_id: str) -> bool:
        return section_id in self.active_section_ids


class PSIActiveAxonModel(ActiveAxonModel):
    """3.0D-8E configuration of the shared active-axon mechanism engine.

    This class defines NO mechanism. It pins the shared engine to the PSI neuron
    and the PSI axon, declares the dendrite passive, names its own stimulation
    fixture, and adds only PSI-shaped reporting on top. Every equation, the
    exact ``cnexp`` gate solution and the implicit membrane solve are inherited
    unchanged from :class:`ActiveAxonModel`, the same object 3.0D-8A built and
    3.0D-8D reused.

    The runs are NOT redefined here. ``equilibrium_report()``,
    ``stimulus_response()``, ``voltages_mV()``, ``axon_diagnostic()``,
    ``passive_are_inert()`` and ``with_active_conductances_removed()`` are the
    GENERIC implementations 3.0D-8E lifted onto the shared engine, so PSI is the
    second neuron to use them and the first to be added without a per-neuron
    copy being written. What this adapter contributes is configuration only.
    """

    def __init__(
        self,
        profile_name: str = PROFILE_AUGUSTIN_2019_ACTIVE_MODEL,
        passive_profile_name: str = PROFILE_AUGUSTIN_2019_GFS_PASSIVE,
        timestep_ms=None,
    ) -> None:
        super().__init__(
            profile_name=profile_name,
            passive_profile_name=passive_profile_name,
            timestep_ms=timestep_ms,
            neuron_id=NEURON_PSI,
            active_section_id=PSI_ACTIVE_SECTION_ID,
        )

    @property
    def name(self) -> str:
        return MODEL_NAME_PSI_ACTIVE_V0

    @property
    def passive_section_ids(self) -> Tuple[str, ...]:
        """The PSI sections that stay passive, with no active channel."""
        return PSI_PASSIVE_SECTION_IDS

    @property
    def stimulus_fixture_amplitude_A(self) -> float:
        """3.0D-8E's OWN numerical fixture. NOT a biological PSI stimulus."""
        return PSI_DIRECT_STIMULUS_AMPLITUDE_A

    @property
    def stimulus_fixture_duration_ms(self) -> float:
        """3.0D-8E's OWN numerical fixture duration. Not a biological value."""
        return PSI_DIRECT_STIMULUS_DURATION_MS

    # -- structure ----------------------------------------------------------

    def prepare_psi(
        self, model: CompartmentModel, segment_count: int = 1
    ) -> GFActiveNetwork:
        """Prepare the PSI network: active axon plus the passive dendrite.

        ``segment_count`` subdivides the ACTIVE AXON only. The dendrite is
        carried at its un-subdivided default, which is the existing 3.0D-7K
        behaviour for a section that is not being resolved.
        """
        return self.prepare_active_axon(model, segment_count=segment_count)

    def section_roles(self, network: GFActiveNetwork) -> PSISectionRole:
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
        return PSISectionRole(
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


def psi_scope_note() -> str:
    """The scope statement 3.0D-8E reports alongside any of its results."""
    return (
        "3.0D-8E MAKES THE PSI AXON LIVE AND NOTHING ELSE. The active axon is "
        "PSI_axon; PSI_dendrite is carried in the same network and remains "
        "PASSIVE, receiving none of the active conductances while still "
        "participating in the cable solve. The mechanism is the SAME shared "
        "engine and the SAME vendored nat.mod, nap.mod and k.mod equations "
        "3.0D-8A validated and 3.0D-8D reused; there is exactly ONE "
        "implementation of them and PSI does not have a copy. All active and "
        "passive parameters are published computational-model parameters from "
        "the 3.0D-7B morphology, the 3.0D-7F passive profile and the 3.0D-7S "
        "Augustin active profile, and none of them is a direct experimental PSI "
        "measurement. The 170 um dendrite length is additionally ESTIMATED in "
        "the source, and that classification is preserved rather than promoted. "
        "NO GF->PSI gap junction is implemented (3.0D-8C owns the electrical "
        "primitive and the 3.0D-7U unit conflict remains UNRESOLVED and "
        "untouched), NO GF->PSI chemical synapse is implemented, NO PSI->DLMn "
        "synapse is implemented, and NO Dalpha7 kinetics are implemented: "
        "Dalpha7 is biologically implicated in PSI->DLMn transmission but the "
        "available sources do not provide sufficient quantitative kinetics for a "
        "defensible live receptor model, so none is invented. No ShakB "
        "rectification, no calcium, Slowpoke, Shaker or Para channel, no DLMn, "
        "no DLM, no sensory input, no NMJ, no muscle and no behavior. The "
        "direct-stimulation amplitude used by the fixture is a NUMERICAL SOLVER "
        "FIXTURE chosen by 3.0D-8E, NOT a biological PSI stimulus, NOT a "
        "rheobase and NOT a threshold; the 120 nA / 0.03 ms value belongs to the "
        "paper's GF circuit simulation and is deliberately not borrowed."
    )
