"""3.0D-8D: the LIVE TTMn ACTIVE NEURON.

WHAT THIS CHECKPOINT IS
-----------------------
3.0D-8A made the GF axon live. 3.0D-8D makes the TTMn axon live, using the
SAME mechanism engine and the SAME equations. There is exactly ONE
implementation of the nat/nap/k mechanism in this project, in
``biological_brain/dynamics/gf_active.py``; this module is a CONFIGURATION of
that engine, not a second copy of it. TTMn is not a special-case GF: it is the
same :class:`ActiveAxonModel` with a different ``neuron_id`` and a different
``active_section_id``.

TTMn STRUCTURE
--------------
::

    TTMn_medial_dendrite (PASSIVE)  --.
                                        >-- TTMn_axon (ACTIVE)
    TTMn_lateral_dendrite (PASSIVE) -'

Only ``TTMn_axon`` carries the active density channels. Both dendrites are
carried in the same network and participate in the passive cable solve, but
they receive NONE of the active conductances, so they are genuinely passive
rather than merely labelled passive. The dendrite-to-axon connections are the
existing 3.0D-7X computational topology, read from the model, never rebuilt.

SOURCE BASIS, AND WHAT IS NOT A MEASUREMENT
-------------------------------------------
The geometry is the published Augustin et al. 2019 (eLife, PMC6469880) model
morphology, already recorded at 3.0D-7B: TTMn axon 50 um x 6 um, medial
dendrite 60 um x 6 um, lateral dendrite 30 um x 6 um. The passive parameters
are the 3.0D-7F authorized profile (Cm 1 uF/cm2, Ra 35.4 ohm*cm, leak density
0.03 mS/cm2, E_leak -85 mV). The active parameters are the 3.0D-7S authorized
Augustin profile (g_Nat 300 mS/cm2, g_Nap 0.11 mS/cm2, g_K 10 mS/cm2, E_Na +65
mV, E_K -74 mV), whose recorded neuron scope explicitly names the TTMn. The
rate equations are the vendored ``nat.mod``, ``nap.mod`` and ``k.mod``.

ALL of these are PUBLISHED COMPUTATIONAL-MODEL PARAMETERS. None of them is a
direct experimental measurement of a TTMn, and this checkpoint never presents
them as one. The equal conductance density across active sections is the
published model's assumption, which 3.0D-8D reproduces rather than re-derives.

WHAT IS EXPLICITLY NOT IMPLEMENTED HERE
---------------------------------------
No chemical GF->TTMn synapse (that stays a 3.0D-7W specification record), no
gap junction (3.0D-8C owns the electrical primitive; the 3.0D-7U unit conflict
is untouched and unresolved), no ShakB rectification, no PSI, no DLMn, no DLM,
no calcium or Slowpoke or Shaker or Para channel, no sensory input, no NMJ, no
muscle, and no behaviour. Nothing here connects the circuit; 3.0D-8D is the
TTMn neuron alone.

THE DIRECT-STIMULUS FIXTURE
---------------------------
Augustin et al. 2019 used direct TTMn stimulation to estimate roughly 0.3 ms
from stimulus onset to the TTMn action-potential peak. That paper does not
state the direct-stimulation amplitude or duration it used, so 3.0D-8D cannot
reproduce that experiment and does not claim to. The paper's CIRCUIT
simulation uses a 120 nA / 0.03 ms stimulus applied to the GF, and that value
is explicitly NOT a TTMn stimulus; 3.0D-8D does not borrow it.

Instead this module declares its OWN numerical fixture, chosen by 3.0D-8D to be
comfortably supra-threshold for the vendored mechanism and numerically
convergent. It is a MODEL-REPRODUCTION FIXTURE for exercising the solver, and
it is NOT a TTMn rheobase, NOT a TTMn spike threshold, and NOT a measurement.
The emergent peak time under this fixture is a numerical result of this
implementation and is not a reproduction of the paper's timing measurement.

WHAT 3.0D-8E CHANGED HERE (AND WHAT IT DID NOT)
----------------------------------------------
3.0D-8E added the PSI neuron and, in doing so, corrected an abstraction defect
8D had left behind: ``equilibrium_report()`` and ``stimulus_response()`` were
defined on THIS adapter rather than on the shared engine, so they were written
for one neuron and would have had to be copied for every neuron after it.

3.0D-8E therefore LIFTED those two runs, plus ``voltages_mV()``,
``axon_diagnostic()``, ``passive_are_inert()`` and
``with_active_conductances_removed()``, onto
:class:`ActiveAxonModel` in ``gf_active.py``, and deleted the TTMn copies. What
remains in this module is CONFIGURATION ONLY: the neuron and section ids, the
passive-section declaration, this neuron's own stimulation fixture, the
``prepare_ttmn`` name kept for API compatibility, and the TTMn role report.

NO NUMERICAL EQUATION CHANGED. NO PARAMETER CHANGED. The timestep policy is
untouched. 3.0D-8E verifies that the TTMn numbers 8D validated are reproduced
exactly through the generic path, so this refactor is behaviour-preserving by
construction and by test. ``TTMAxonDiagnostic`` and ``TTMnEquilibriumReport``
are retained as ALIASES of the lifted generic types so the 8D public API does
not break.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from ..morphology import CompartmentModel
from ..passive_profiles import PROFILE_AUGUSTIN_2019_GFS_PASSIVE
from ..active_profiles import PROFILE_AUGUSTIN_2019_ACTIVE_MODEL
from .gf_active import (
    ActiveAxonModel,
    ActiveAxonEquilibriumReport,
    ActiveSegmentDiagnostic,
    GFActiveNetwork,
)

MODEL_NAME_TTMN_ACTIVE_V0 = "ttmn_active_v0"

#: The neuron this checkpoint activates.
NEURON_TTMN = "TTMn"

#: The ONE section that carries the active density channels. The published
#: model makes the TTMn axon active; the dendrites are passive.
TTMN_ACTIVE_SECTION_ID = "TTMn_axon"

#: The two passive sections, carried in the same network with no active
#: channel. Order is fixed so every result is deterministic.
TTMN_PASSIVE_SECTION_IDS: Tuple[str, ...] = (
    "TTMn_medial_dendrite",
    "TTMn_lateral_dendrite",
)

# -- the direct-stimulation numerical fixture --------------------------------

TTMN_DIRECT_STIMULUS_AMPLITUDE_A = 50.0e-9
TTMN_DIRECT_STIMULUS_DURATION_MS = 0.03
TTMN_DIRECT_STIMULUS_LOCATION = "TTMn_axon#seg0"

TTMN_DIRECT_STIMULUS_PROVENANCE = (
    "NUMERICAL MODEL-REPRODUCTION FIXTURE, CHOSEN BY 3.0D-8D. THIS IS NOT A "
    "BIOLOGICAL TTMn STIMULUS. Augustin et al. 2019 used direct TTMn "
    "stimulation to estimate roughly 0.3 ms from onset to the TTMn action "
    "potential peak, but the paper does not state the amplitude or duration it "
    "used, so that experiment is NOT reproduced here. The published 120 nA / "
    "0.03 ms value belongs to the paper's GF circuit simulation and is "
    "explicitly NOT a TTMn stimulus; it is not borrowed. This amplitude was "
    "selected by 3.0D-8D as comfortably supra-threshold for the vendored "
    "mechanism and numerically convergent across segment counts and timesteps. "
    "It is a solver fixture. It is NOT a TTMn rheobase, NOT a TTMn spike "
    "threshold, and NOT a measurement of anything."
)


@dataclass(frozen=True)
class TTMSectionRole:
    """Which TTMn sections are active and which are passive, and why.

    This is a REPORT of what was built, read back off the prepared network, not
    a declaration written in advance. ``axon`` is the only active section.
    """

    active_section_ids: Tuple[str, ...]
    passive_section_ids: Tuple[str, ...]
    basis: str

    def is_active_section(self, section_id: str) -> bool:
        return section_id in self.active_section_ids


#: 3.0D-8E BACKWARDS-COMPATIBLE ALIASES. 3.0D-8D declared these two dataclasses
#: in this module; 3.0D-8E lifted them onto the shared engine as
#: :class:`ActiveSegmentDiagnostic` and :class:`ActiveAxonEquilibriumReport`, so
#: that GF, TTMn, PSI and DLMn report through ONE definition rather than a copy
#: per neuron. The fields are unchanged, so the 3.0D-8D public API still holds.
TTMAxonDiagnostic = ActiveSegmentDiagnostic
TTMnEquilibriumReport = ActiveAxonEquilibriumReport


class TTMActiveAxonModel(ActiveAxonModel):
    """3.0D-8D configuration of the shared active-axon mechanism engine.

    This class defines NO mechanism. It pins the shared engine to the TTMn
    neuron and the TTMn axon, declares the two dendrites passive, names its own
    stimulation fixture, and adds only TTMn-shaped reporting on top. Every
    equation, the exact ``cnexp`` gate solution and the implicit membrane solve
    are inherited unchanged from :class:`ActiveAxonModel`, which is the same
    object 3.0D-8A uses.

    3.0D-8E note: ``equilibrium_report()``, ``stimulus_response()``,
    ``voltages_mV()``, ``axon_diagnostic()``, ``passive_are_inert()`` and
    ``with_active_conductances_removed()`` are NO LONGER defined here. They live
    on the shared engine and 8D's validated numbers are reproduced by calling
    them, not by a TTMn-specific copy. What remains here is configuration and
    the TTMn role report.
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
            neuron_id=NEURON_TTMN,
            active_section_id=TTMN_ACTIVE_SECTION_ID,
        )

    @property
    def name(self) -> str:
        return MODEL_NAME_TTMN_ACTIVE_V0

    @property
    def passive_section_ids(self) -> Tuple[str, ...]:
        """The TTMn sections that stay passive, with no active channel."""
        return TTMN_PASSIVE_SECTION_IDS

    @property
    def stimulus_fixture_amplitude_A(self) -> float:
        """3.0D-8D's OWN numerical fixture. NOT a biological TTMn stimulus."""
        return TTMN_DIRECT_STIMULUS_AMPLITUDE_A

    @property
    def stimulus_fixture_duration_ms(self) -> float:
        """3.0D-8D's OWN numerical fixture duration. Not a biological value."""
        return TTMN_DIRECT_STIMULUS_DURATION_MS

    # -- structure ----------------------------------------------------------

    def prepare_ttmn(
        self, model: CompartmentModel, segment_count: int = 1
    ) -> GFActiveNetwork:
        """Prepare the TTMn network: active axon plus passive dendrites.

        The 3.0D-8D name for :meth:`ActiveAxonModel.prepare_active_axon`, kept so
        the validated 8D API is unchanged. It resolves to exactly the same
        network, because it performs exactly the same call.
        """
        return self.prepare_active_axon(model, segment_count=segment_count)

    def section_roles(self, network: GFActiveNetwork) -> TTMSectionRole:
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
        return TTMSectionRole(
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


def ttmn_scope_note() -> str:
    """The scope statement 3.0D-8D reports alongside any of its results."""
    return (
        "3.0D-8D MAKES THE TTMn AXON LIVE AND NOTHING ELSE. The active axon is "
        "TTMn_axon; TTMn_medial_dendrite and TTMn_lateral_dendrite are carried "
        "in the same network and remain PASSIVE, receiving none of the active "
        "conductances. The mechanism is the SAME shared engine and the SAME "
        "vendored nat.mod, nap.mod and k.mod equations 3.0D-8A validated; there "
        "is exactly ONE implementation of them and TTMn does not have a copy. "
        "All parameters are published computational-model parameters from the "
        "3.0D-7B morphology, the 3.0D-7F passive profile and the 3.0D-7S "
        "Augustin active profile, and none of them is a direct experimental "
        "TTMn measurement. NO chemical GF->TTMn synapse is implemented (3.0D-7W "
        "keeps it a specification record), NO gap junction is implemented "
        "(3.0D-8C owns the electrical primitive and the 3.0D-7U unit conflict "
        "remains UNRESOLVED and untouched), no ShakB rectification, no calcium, "
        "Slowpoke, Shaker or Para channel, no PSI, no DLMn, no DLM, no sensory "
        "input, no NMJ, no muscle and no behavior. The direct-stimulation "
        "amplitude used by the fixture is a NUMERICAL MODEL-REPRODUCTION "
        "FIXTURE chosen by 3.0D-8D, NOT a biological TTMn stimulus, NOT a "
        "rheobase and NOT a threshold; the 120 nA / 0.03 ms value belongs to "
        "the paper's GF circuit simulation and is deliberately not borrowed."
    )
