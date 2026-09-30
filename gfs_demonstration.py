"""3.0D GFS NUMERICAL DEMONSTRATION adapter (opt-in, explicitly labelled).

READ THIS BEFORE ENABLING IT
---------------------------
This module is NOT a sensory model and NOT a visual prediction. It is a
pass-through that runs the COMPLETED 3.0D GFS model from an EXPLICIT NUMERICAL
GF EVENT and republishes the 3.0D-8N consumer dictionary. Nothing here
predicts what a fly would do in response to a real predator.

WHAT IT DOES, AND ONLY THIS
---------------------------
    GFSNumericalDemonstrationConfig
        -> explicit GFSpikeEvent          (GFEventSource.DIRECT_NUMERICAL_STIMULUS)
        -> explicit GapJunctionConductance (via 3.0D-8C explicit_conductance)
        -> GFSCircuit
        -> run_live_circuit()
        -> escape_behavior_from_circuit() (3.0D-8K)
        -> gf_action_selection()          (3.0D-8N)
        -> to_consumer_dict()

There are NO biological equations in this file. It does not threshold a
voltage, does not convert a unit, does not choose a conductance for effect, and
does not synthesise a probability. It constructs things and returns them.

WHY A NUMERICAL EVENT RATHER THAN A LOOMING STIMULUS
-----------------------------------------------------
von Reyn et al. 2017 (PMID 28641115) establish that GF activity depends on the
INTEGRATION of looming features -- LC4 angular velocity and LPLC2 angular size
(Ache et al. 2019, PMID 30827912). A Discord command supplies none of those:
``/scare`` is a 2.0 weighted ``VIS_LC`` group injection that sets no stimulus
vector at all.

So the sensory route is genuinely unavailable, and 3.0D-8L is deliberately not
used. 3.0D-8I already designed ``GFSpikeEvent`` as the explicit substitute for
the missing sensory-to-live-GF coupling, and this adapter uses exactly that
substitute rather than inventing a coupling. Consequently:

* ``GFEventSource.DIRECT_NUMERICAL_STIMULUS`` is used, never
  ``FUTURE_SENSORY_COUPLING``, which would assert a bridge that does not exist.
* 3.0D-8L is never imported and ``LoomingStimulus`` is never constructed.
* ``couple_to_live_gf()`` remains unsupported and still raises.
* The provenance string on every event states that the trigger came from a
  product command and is NOT a visual stimulus or a measured biological event.

WHAT REMAINS UNRESOLVED, AND IS NOT RESOLVED HERE
-------------------------------------------------
* 3.0D-7U -- the gap-junction conductance is an unresolved factor-1000 unit
  conflict (paper 135/34.5 uS; literal ModelDB execution 135/34.5 nS) with NO
  PREFERRED SIDE. The value used here is a declared NUMERICAL FIXTURE whose
  provenance must say so. 3.0D-8C's ``from_unresolved_project_conductance()``
  still refuses to supply a project value, and ``GFSCircuit`` still requires a
  conductance with no default.
* 3.0D-8G -- the PSI->DLMn peak conductance remains an unresolved 80 uS vs
  0.08 uS conflict. This adapter never touches
  ``psi_dlmn_peak_conductance_source``, so 8G's own default stands.
* 3.0D-8I -- the sensory-to-live-GF coupling remains unsupported.
* Escape probability -- per Chai et al. 2025 (PMID 40425165) GF activity
  contributes to action selection while parallel non-GF escape pathways exist,
  so a GF action potential is NOT guaranteed escape. 8N reports
  ``escape_guaranteed=False``, ``overall_escape_probability=None`` and
  ``overall_escape_probability_status="unresolved"``, and this adapter passes
  those through unchanged.

PERFORMANCE NOTE
----------------
A live circuit run at the 8I defaults (``settle_ms=200``) takes roughly half a
minute, because the membrane is advanced to its numerical fixed point first.
This is a demonstration, not a real-time path.
"""

from biological_brain.configuration import (
    GFSNumericalDemonstrationConfig,
)
from biological_brain.dynamics.action_selection import gf_action_selection
from biological_brain.dynamics.electrical_coupling import explicit_conductance
from biological_brain.dynamics.escape_behavior import escape_behavior_from_circuit
from biological_brain.dynamics.gfs_circuit import (
    GFEventSource,
    GFSCircuit,
    GFSpikeEvent,
)

#: Provenance attached to every GF event this adapter builds. It states, in the
#: object itself, that the trigger is a numerical solver fixture originating
#: from a product command and NOT a visual or sensory stimulus.
GF_EVENT_FIXTURE_PROVENANCE = (
    "3.0D GFS NUMERICAL DEMONSTRATION FIXTURE. This GF action potential is a "
    "NUMERICAL SOLVER TRIGGER supplied explicitly by a Discord/product command. "
    "It is NOT a visual stimulus, NOT a looming stimulus, NOT a sensory drive, "
    "and NOT a measured biological event. The product command supplies no "
    "angular size, no angular velocity and no sensory coupling, so none is "
    "implied here. 3.0D-8L sensory phenomenology is deliberately NOT used and "
    "3.0D-8I couple_to_live_gf() remains unsupported."
)

#: Key under which the consumer dictionary is published on the snapshot. It is
#: a SIBLING of the existing ``bio_*`` signals and is never merged into them:
#: merging would let a 3.0D number overwrite a 2.0 number and blur which model
#: produced what.
GFS_DEMONSTRATION_SNAPSHOT_KEY = "gfs_3d"


class GFSNumericalDemonstrationError(Exception):
    """Raised when the GFS numerical demonstration cannot run as configured."""


def build_gap_conductance(config: GFSNumericalDemonstrationConfig):
    """Build the EXPLICIT gap-junction conductance from configuration.

    Delegates entirely to 3.0D-8C's ``explicit_conductance``, which requires
    a unit, refuses unrecognised units, and never guesses. No unit conversion
    is performed here, and no value is chosen for effect.

    The result always has ``is_default=False``: this is a caller-stated
    fixture, never a library default and never a resolution of 3.0D-7U.
    """
    if not isinstance(config, GFSNumericalDemonstrationConfig):
        raise GFSNumericalDemonstrationError(
            "build_gap_conductance() requires a "
            "GFSNumericalDemonstrationConfig."
        )
    if not config.enabled:
        raise GFSNumericalDemonstrationError(
            "The GFS numerical demonstration is disabled. No "
            "GapJunctionConductance is constructed when it is disabled, "
            "because 3.0D-7U is unresolved and a disabled feature must not "
            "materialise a conductance."
        )
    conductance = explicit_conductance(
        config.gap_conductance_value,
        config.gap_conductance_unit,
        config.gap_conductance_provenance,
    )
    # Belt and braces: 8C already sets this False, and the demonstration must
    # never present a default.
    assert conductance.is_default is False
    return conductance


def build_gf_event(config: GFSNumericalDemonstrationConfig) -> GFSpikeEvent:
    """Build the EXPLICIT numerical GF event from configuration.

    Uses ``GFEventSource.DIRECT_NUMERICAL_STIMULUS``. It does NOT use
    ``FUTURE_SENSORY_COUPLING``, because that member would assert a sensory
    bridge which does not exist. The provenance states in the object itself
    that this is a numerical solver trigger from a product command.
    """
    if not isinstance(config, GFSNumericalDemonstrationConfig):
        raise GFSNumericalDemonstrationError(
            "build_gf_event() requires a GFSNumericalDemonstrationConfig."
        )
    if not config.enabled:
        raise GFSNumericalDemonstrationError(
            "The GFS numerical demonstration is disabled. No GFSpikeEvent is "
            "constructed when it is disabled."
        )
    return GFSpikeEvent(
        event_time_s=config.gf_event_time_s,
        source=GFEventSource.DIRECT_NUMERICAL_STIMULUS,
        provenance=GF_EVENT_FIXTURE_PROVENANCE,
    )


def run_gfs_numerical_demonstration(
    config: GFSNumericalDemonstrationConfig,
) -> dict:
    """Run the demonstration and return the 3.0D-8N consumer dictionary.

    Returns ``{}`` when the demonstration is disabled, so a caller can write
    the result unconditionally and leave the snapshot unchanged.
    """
    if not isinstance(config, GFSNumericalDemonstrationConfig):
        raise GFSNumericalDemonstrationError(
            "run_gfs_numerical_demonstration() requires a "
            "GFSNumericalDemonstrationConfig."
        )
    if not config.enabled:
        # No GFSCircuit is constructed and no conductance is built.
        return {}

    conductance = build_gap_conductance(config)
    gf_event = build_gf_event(config)

    # 8I's constructor signature is untouched: gap_conductance stays required,
    # and psi_dlmn_peak_conductance_source keeps 8G's own default.
    circuit = GFSCircuit(gap_conductance=conductance)
    result = circuit.run_live_circuit(
        gf_event,
        duration_ms=config.duration_ms,
        settle_ms=config.settle_ms,
    )
    behaviour = escape_behavior_from_circuit(result)
    selection = gf_action_selection(result, behaviour)
    return selection.to_consumer_dict()


def gfs_demonstration_scope_note() -> str:
    """One statement of what this adapter is and is not."""
    return (
        "3.0D GFS NUMERICAL DEMONSTRATION ADAPTER, opt-in and explicitly "
        "labelled. It runs the completed 3.0D GFS model from an EXPLICIT "
        "NUMERICAL GF EVENT (GFEventSource.DIRECT_NUMERICAL_STIMULUS) and "
        "republishes the 3.0D-8N consumer dictionary. It is NOT a sensory or "
        "visual prediction, NOT a looming model, and NOT a claim about what a "
        "real fly would do. It contains no biological equations, performs no "
        "voltage thresholding, performs no unit conversion, and synthesises no "
        "probability. 3.0D-8L is never imported and couple_to_live_gf() "
        "remains unsupported. 3.0D-7U remains an unresolved factor-1000 "
        "unit conflict and the conductance used here is a declared NUMERICAL "
        "FIXTURE, not a biological value. 3.0D-8G's 80 uS vs 0.08 uS conflict is "
        "untouched. Escape probability remains None/unresolved, because per "
        "Chai et al. 2025 parallel non-GF escape pathways exist and GF "
        "activation does not imply guaranteed escape."
    )
