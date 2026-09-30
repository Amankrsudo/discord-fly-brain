"""End-to-end GFS circuit integration (3.0D-8I).

TWO LAYERS, JOINED BY AN INTERFACE, NOT BY A GUESS
--------------------------------------------------
This module is the orchestration layer that finally lets the Drosophila Giant
Fiber System run as ONE deterministic circuit. It reuses, and never rewrites:

    the GF, TTMn, PSI and DLMn active neurons   3.0D-8A / 8D / 8E / 8F
    the GF->TTMn and GF->PSI electrical paths   3.0D-8C
    the PSI->DLMn chemical synapse              3.0D-8G
    the LC4/LPLC2 phenomenological GF drive     3.0D-8H

and it wires them together in the published order:

    LoomingStimulus --> PhenomenologicalGFDrive        (8H, sensory)
                              :
                              :   <-- THE UNRESOLVED BOUNDARY
                              v
    GF event --> GF --> {TTMn, PSI} --> DLMn         (8A-8G, live)

THE BOUNDARY IS THE POINT OF THIS CHECKPOINT
---------------------------------------------
The colon above is real and is not crossed. The Ache et al. 2019 model is a FIT
to a stimulus-response relationship, expressed in millivolts. The Augustin et
al. 2019 model is a BIOPHYSICAL NEURON with membrane capacitance, leak, three
sodium/potassium channel families, cable geometry and active propagation. No
retrieved source states a quantitative mapping from the fitted GF voltage
response to a synaptic conductance, a synaptic reversal potential, a synaptic
current, a receptor kinetic, a release probability or a unit conductance.

That means the following equation is FORBIDDEN, and this module never forms it:

    I = V_drive / 75 Mohm          # 7E's GF input resistance is CONTEXT
    I = k * V_drive                # with an invented k

The 7E GF input resistance of 75 Mohm is EXPERIMENTALLY CONSTRAINED CONTEXT.
It is not an authorized live-solver conversion, and using it here would convert
a documented non-claim into a silent live current. The same applies to a
voltage clamp, to treating the phenomenological drive as a GF dendritic
voltage, and to deriving a spike threshold from the phenomenological model's
maximum.

Instead the two layers are joined by an EXPLICIT EVENT INTERFACE. The circuit
is driven by a :class:`GFSpikeEvent` that a caller supplies with declared
provenance, and the sensory layer is a separate, independently runnable mode.
:class:`SensoryBiophysicalGFBoundary` holds the two results side by side,
reports ``coupling_status = "unresolved"``, lists the assumptions that are
prohibited, and its ``couple_to_live_gf()`` ALWAYS RAISES. A third entry point,
``run_looming_through_live_circuit()``, also always raises. The missing science
is therefore impossible to overlook and impossible to accidentally fill in.

WHY THE CIRCUIT NEEDS A CONDUCTANCE, AND WHERE IT COMES FROM
-------------------------------------------------------------
The two GF output pathways are electrical, so running the live circuit
requires a gap-junction conductance. 3.0D-7U records that value as UNRESOLVED:
the paper says 135 uS (young) / 34.5 uS (old) while gap2.mod declares its
parameter in nanoSiemens, a factor of exactly 1000, with no erratum to
discriminate between the open explanations. 8I does not resolve 7U.

Rather than pick a side silently, ``GFSCircuit`` REQUIRES the caller to pass a
``GapJunctionConductance`` built through 3.0D-8C's own
``explicit_conductance(value, unit, provenance)`` factory. There is no default
and no fallback, because a default would be exactly the covert resolution 7U
forbids. 8C's ``from_unresolved_project_conductance()`` still always raises, and
that refusal is still reachable. Whatever a caller supplies is used verbatim and
echoed back in the result, together with the unresolved-provenance warning.

EXPERIMENTAL LATENCIES ARE CONTEXT, NOT TARGETS
----------------------------------------------
Augustin, Allen and Partridge 2011 (PMC3182647) report that brain
stimulation gives latencies of 0.7-1.2 ms for the GF-TTM pathway and
1.3-1.7 ms for the GF-DLM pathway. Those numbers are recorded here as
validation context and are NOT fitted, tuned toward, or inserted as delays.

There is a second reason they cannot be matched even in principle by this
module. That paper defines response latency as "the time between stimulation
of the brain and depolarization of the MUSCLE", so both ranges INCLUDE a
neuromuscular junction. 8I models neurons only: there is no NMJ, no muscle and
no motor output, and adding one belongs to 8J/8K. The reported ranges are
therefore not the quantity this circuit computes, and the circuit reports its
own simulated timings for comparison without claiming agreement or
disagreement.

The same source also reports that sensory (light-off) activation yields
responses longer than 3 ms, against under 1.7 ms for direct brain stimulation,
which is direct experimental support for the distinction this module enforces:
a numerical GF event is NOT a visual stimulus.

WHAT IS DELIBERATELY ABSENT
---------------------------
No behaviour: no escape decision, no short/long takeoff classification, no
probability of escape, no behavioural threshold and no behavioural state
machine. No motor output, no NMJ, no muscle. No GF->TTMn or GF->PSI CHEMICAL
component, which remains 3.0D-7W provenance only and is not made live here.
No new conductance, no new synaptic equation, no duplicated neuron solver, no
random state, and no threshold of any kind.
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from .chemical_synapse import PSI_DLMnChemicalSynapse
from .dlmn_active import DLMNActiveAxonModel
from .electrical_coupling import GFSCouplingNetwork, GapJunctionConductance
from .gf_active import GFActiveAxonModel
from .gf_sensory_drive import (
    LoomingStimulus,
    PhenomenologicalGFDrive,
    SensoryDriveSample,
    published_ache_gf_coefficients,
)
from .psi_active import PSIActiveAxonModel
from .ttmn_active import TTMActiveAxonModel

MODEL_NAME_GFS_CIRCUIT_V0 = "gfs_circuit_v0"

#: Coupling ids owned by 3.0D-8C. 8I consumes them and does not invent any.
COUPLING_GF_TTMN = "GF_TTMn"
COUPLING_GF_PSI = "GF_PSI"

#: 3.0D-8G owns this synapse. 8I consumes it and changes nothing about it.
SYNAPSE_PSI_DLMN = "PSI_DLMn"


# --- sources -----------------------------------------------------------------

SOURCE_ACHE_2019 = (
    "Ache JM, Polsky J, Alghailani S, Parekh R, Breads P, Peek MY, Bock DD, "
    "von Reyn CR, Card GM (2019). Neural Basis for Looming Size and Velocity "
    "Encoding in the Drosophila Giant Fiber Escape Pathway. Curr Biol "
    "29(6):1073-1081.e4. PMID 30827912. "
    "https://www.sciencedirect.com/science/article/pii/S0960982219301381 . "
    "SOURCE OF THE SENSORY PHENOMENOLOGY, implemented at 3.0D-8H. LC4 carries "
    "angular velocity and LPLC2 carries angular size; both are direct visual "
    "inputs to the GF and their contributions sum to reproduce the GF looming "
    "response. The paper presents a PHENOMENOLOGICAL GF model in those visual "
    "variables. It does NOT supply a synaptic conductance, a synaptic "
    "reversal potential, a synaptic current, a receptor kinetic or a release "
    "probability for either LC4->GF or LPLC2->GF, which is why this circuit "
    "cannot drive the live GF from it."
)

SOURCE_AUGUSTIN_2019 = (
    "Augustin H, Zylbertal A, Partridge L (2019). A Computational Model of the "
    "Escape Response Latency in the Giant Fiber System of Drosophila "
    "melanogaster. eNeuro 6(2):ENEURO.0423-18.2019. PMID 31001574, "
    "ModelDB 245415. https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ . "
    "SOURCE OF THE LIVE BIOPHYSICAL CIRCUIT, implemented at 3.0D-7V through "
    "8G: the GF/TTMn, GF/PSI and PSI/DLMn parameters, the gap2 electrical "
    "mechanism and the Exp2Syn chemical mechanism. NOTE that this PMCID was "
    "long cited in this project as the source of the Ache et al. 2019 "
    "sensory model; that was wrong, and 3.0D-8H recorded the correction. It is "
    "the thoracic latency model and contains no looming phenomenology."
)

SOURCE_AUGUSTIN_2011_LATENCY = (
    "Augustin H, Allen MJ, Partridge L (2011). Electrophysiological Recordings "
    "from the Giant Fiber Pathway of D. melanogaster. J Vis Exp (47):2412. "
    "doi:10.3791/2412. PMID 21304452. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC3182647/ . "
    "EXPERIMENTAL VALIDATION CONTEXT ONLY, NEVER A TUNING TARGET. The paper "
    "states: 'Latencies between 0.7 and 1.2 ms for the GF-TTM pathway and "
    "between 1.3 and 1.7 ms for the GF-DLM pathway indicate a healthy "
    "preparation and proper recording technique.' CRUCIALLY, that paper "
    "defines response latency as 'the time between stimulation of the brain "
    "and depolarization of the muscle', so BOTH ranges INCLUDE a "
    "neuromuscular junction. 8I models neurons only and has no NMJ, so these "
    "ranges are not the quantity this circuit computes and cannot be matched "
    "even in principle. The same paper also reports that sensory ('light-off') "
    "activation gives responses longer than 3 ms against under 1.7 ms for "
    "direct brain stimulation, which is direct experimental support for "
    "keeping a numerical GF event distinct from a visual stimulus."
)

SOURCE_MODELDB_2017_FEATURE_INTEGRATION = (
    "von Reyn CR, Ache JM, Card GM (2017). Neural contrasts for detecting "
    "looming motion and angular size differ within a single interneuron. "
    "Curr Biol. PMID 28641115. ModelDB 230400. "
    "CONTEXT ONLY. The 2017 ModelDB implementation treats the GF visual "
    "response as a linear feature-integration model over the two visual "
    "variables, which is the same structure 3.0D-8H implements from the 2019 "
    "coefficients. It is recorded here to show the two are consistent; 8I "
    "does not import it, does not duplicate it, and takes no parameter from "
    "it."
)


# --- errors ------------------------------------------------------------------

class GFSCircuitError(Exception):
    """Base class for 3.0D-8I circuit failures."""


class UnsupportedSensoryBiophysicalCoupling(GFSCircuitError):
    """Raised whenever something tries to join the two layers numerically.

    This is the deliberate centre of the checkpoint. The Ache phenomenology and
    the Augustin biophysics cannot be joined by any source-backed conversion,
    so every attempt raises this instead of returning a number. The message
    says what is missing and what would not be acceptable.
    """


_NO_COUPLING_REASON = (
    "NO SOURCE-BACKED SENSORY-TO-BIOPHYSICAL GF COUPLING EXISTS. The Ache et "
    "al. 2019 model is a FITTED PHENOMENOLOGICAL RESPONSE in millivolts, and "
    "the Augustin et al. 2019 GF is a BIOPHYSICAL NEURON. No retrieved source "
    "gives a mapping from the fitted drive to a synaptic conductance, a "
    "synaptic reversal potential, a synaptic current, a receptor kinetic, a "
    "release probability or a receptor density for either LC4->GF or "
    "LPLC2->GF. The Ache model's vGF is a model PREDICTION of a "
    "stimulus-response curve and is NOT the live GF membrane voltage; the two "
    "are different objects produced by different methods."
)

_PROHIBITED_ASSUMPTIONS = (
    "I = V_drive / 75 Mohm. The 3.0D-7E GF input resistance of 75 Mohm is "
    "EXPERIMENTALLY CONSTRAINED CONTEXT, not an authorized live-solver "
    "conversion, and dividing by it would manufacture a synaptic conductance "
    "from nothing.",
    "I = k * V_drive for any invented k, including any value fitted to make a "
    "downstream neuron fire.",
    "Any hardcoded conversion such as '1 mV of sensory drive = X nA'.",
    "Treating the phenomenological vGF as the live GF membrane voltage, or as a "
    "GF dendritic voltage.",
    "Applying a voltage clamp to the live GF, or overriding its membrane state "
    "from the phenomenological model.",
    "Deriving a GF spike threshold from the maximum of the phenomenological "
    "response.",
    "Any new or adjusted synaptic conductance, gap-junction conductance, "
    "reversal potential, receptor kinetic, release probability or Q10.",
    "Any delay inserted to make the simulated timing match a literature "
    "latency.",
    "Converting the 2,442 LC4->GF and 1,366 LPLC2->GF EM synapse counts into "
    "conductances. Those counts are ANATOMICAL CONTEXT, not synaptic weights.",
)


# --- enums -------------------------------------------------------------------

class GFEventSource(Enum):
    """Where an explicit GF event came from.

    There is deliberately NO member meaning "this came from the 8H sensory
    model". Such a member would imply the sensory phenomenology is connected to
    the live GF, which is exactly what is unresolved. ``FUTURE_SENSORY_COUPLING``
    names a coupling that does not exist yet; using it today asserts a bridge
    that has not been researched, so it records an intent, never a fact.
    """

    DIRECT_NUMERICAL_STIMULUS = "direct_numerical_stimulus"
    EXTERNAL_EXPERIMENTAL_EVENT = "external_experimental_event"
    FUTURE_SENSORY_COUPLING = "future_sensory_coupling"

    @property
    def is_visual_stimulus(self) -> bool:
        """Always False. A numerical event is not a visual stimulus.

        PMC3182647 reports sensory 'light-off' responses longer than 3 ms
        against under 1.7 ms for direct brain stimulation, so the two are
        experimentally distinguishable and must not be conflated here.
        """
        return False

    @property
    def is_connected_to_the_sensory_phenomenology(self) -> bool:
        """Always False, for every member including FUTURE_SENSORY_COUPLING."""
        return False


class CouplingStatus(Enum):
    """The only value 8I can report for the sensory/biophysical boundary."""

    UNRESOLVED = "unresolved"


# --- inputs ------------------------------------------------------------------

@dataclass(frozen=True)
class GFSpikeEvent:
    """An EXPLICIT, EXTERNALLY SUPPLIED event that is delivered to the live GF.

    This is the input that replaces the missing sensory coupling, and it is
    deliberately explicit: the event carries its own time and its own declared
    provenance, so no reader can mistake a numerical trigger for a simulated
    visual response.

    It does NOT carry an amplitude. The current used to drive the GF is the
    existing, validated 3.0D-8A direct-stimulation fixture, which is a
    NUMERICAL SOLVER FIXTURE and not a biological threshold or rheobase. A
    caller wanting a different amplitude supplies a different event class in a
    later checkpoint rather than smuggling one in here.
    """

    event_time_s: float
    source: GFEventSource
    provenance: str

    def __post_init__(self) -> None:
        if not isinstance(self.source, GFEventSource):
            raise GFSCircuitError(
                f"GF event source must be a GFEventSource, got "
                f"{self.source!r}. Declared sources are: "
                f"{[s.value for s in GFEventSource]}. There is deliberately no "
                f"'sensory_drive' source, because the sensory phenomenology is "
                f"NOT connected to the live GF."
            )
        if not isinstance(self.event_time_s, (int, float)) or not math.isfinite(
            float(self.event_time_s)
        ):
            raise GFSCircuitError(
                f"GF event time must be finite, got {self.event_time_s!r}."
            )
        if float(self.event_time_s) < 0.0:
            raise GFSCircuitError(
                f"GF event time must be non-negative, got {self.event_time_s}."
            )
        if not isinstance(self.provenance, str) or not self.provenance.strip():
            raise GFSCircuitError(
                "A GF event must carry a non-empty provenance string. An "
                "event with no declared origin is exactly the kind of "
                "unlabelled trigger this interface exists to prevent."
            )

    @property
    def is_visual_stimulus(self) -> bool:
        """Always False. See :attr:`GFEventSource.is_visual_stimulus`."""
        return False

    @property
    def is_sensory_phenomenology_output(self) -> bool:
        """Always False, even for FUTURE_SENSORY_COUPLING."""
        return False

    def note(self) -> str:
        return (
            f"EXPLICIT GF EVENT at t = {self.event_time_s} s, source "
            f"'{self.source.value}'. {self.provenance} This event is NOT a "
            f"visual stimulus, NOT an LC4 or LPLC2 synaptic event, and NOT a "
            f"biological threshold or rheobase."
        )


# --- results -----------------------------------------------------------------

@dataclass(frozen=True)
class PhenomenologicalGFDriveTrace:
    """3.0D-8I MODE 1: looming stimulus -> phenomenological GF response.

    A pure re-publication of 3.0D-8H's deterministic evaluation over a time
    series. Nothing here touches a membrane, and nothing here is in
    millivolts-of-a-real-cell.
    """

    times_s: Tuple[float, ...]
    samples: Tuple[SensoryDriveSample, ...]
    stimulus_description: str
    drive: PhenomenologicalGFDrive

    def peak_weighted_drive_mV(self) -> float:
        return max(sample.weighted_gf_drive_mV for sample in self.samples)

    def peak_time_s(self) -> float:
        best = max(self.samples, key=lambda s: s.weighted_gf_drive_mV)
        return best.t_s

    def component_peaks_mV(self) -> Dict[str, float]:
        return {
            "lc4": max(s.lc4_component_mV for s in self.samples),
            "lplc2": max(s.lplc2_component_mV for s in self.samples),
            "inhibitory_component_1": max(
                s.inhibitory_component_1_mV for s in self.samples
            ),
            "inhibitory_component_2": max(
                s.inhibitory_component_2_mV for s in self.samples
            ),
        }

    def is_live_membrane_voltage(self) -> bool:
        """Always False. This is the 8H phenomenology, not a live voltage."""
        return False

    def limitations(self) -> str:
        return (
            "PHENOMENOLOGICAL GF RESPONSE, 3.0D-8H. A fitted model prediction "
            f"in millivolts. {_NO_COUPLING_REASON} It is NOT the voltage "
            f"state of the live GF and is never used as one."
        )


@dataclass(frozen=True)
class GFSpikeRecord:
    """A detected response in one neuron, with the criterion that found it.

    ``observation_floor_mV`` is a TEST OBSERVATION LEVEL, not a spike
    threshold. It is measured against ``reference_voltage_mV``, which is the
    neuron's OWN settled numerical fixed point for this run, not its declared
    ``E_leak`` initial value and not a hardcoded voltage. 8I defines no
    rheobase, no threshold voltage and no spike-initiation mechanism.

    The floor defaults to 1.0 mV because at a numerical fixed point the
    membrane is stationary only to within solver roundoff, of order 1e-12 mV,
    and a zero floor would be crossed by that roundoff on the first timestep.
    It is a declared numerical level, not a biological quantity, and not a
    value taken from any source.
    """

    neuron_id: str
    segment_id: str
    time_s: float
    voltage_mV: float
    observation_floor_mV: float
    reference_voltage_mV: float
    criterion: str

    @property
    def is_a_biological_threshold(self) -> bool:
        """Always False."""
        return False

    @property
    def is_a_spike(self) -> bool:
        """Always False: this is a floor crossing, not a detected action potential.

        A floor crossing can occur while the neuron is merely depolarised, so
        ``time_s`` is a subthreshold onset and not a spike time. Reading these
        as spike latencies would overstate how fast the pathway responds.
        """
        return False


@dataclass(frozen=True)
class SynapticEventRecord:
    """One 3.0D-8G chemical-synapse event delivered during a live circuit run."""

    synapse_id: str
    source_neuron: str
    target_neuron: str
    event_time_s: float
    trigger_segment_id: str
    trigger_time_s: float
    note: str

    @property
    def is_synthetic(self) -> bool:
        """Always False. The event is triggered by the live PSI voltage."""
        return False


@dataclass(frozen=True)
class ExperimentalLatencyContext:
    """Published GFS latencies, recorded as CONTEXT and never fitted.

    The ranges are the experimental brain-stimulation-to-MUSCLE latencies of
    Augustin et al. 2011. They include a neuromuscular junction, which 8I does
    not model, so they are not the quantity this circuit computes. See
    :data:`SOURCE_AUGUSTIN_2011_LATENCY`.
    """

    gf_to_ttm_ms_range: Tuple[float, float] = (0.7, 1.2)
    gf_to_dlm_ms_range: Tuple[float, float] = (1.3, 1.7)
    source: str = SOURCE_AUGUSTIN_2011_LATENCY
    measured_quantity: str = (
        "brain stimulation to MUSCLE depolarization, INCLUDING a "
        "neuromuscular junction"
    )
    not_modelled_by_8i: str = (
        "3.0D-8I models NEURONS ONLY. It has no neuromuscular junction, no "
        "muscle and no motor output, so these ranges cannot be matched even in "
        "principle and are not solver requirements."
    )
    is_a_tuning_target: bool = False

    def __post_init__(self) -> None:
        if self.is_a_tuning_target:
            raise GFSCircuitError(
                "Experimental latency context must never be a tuning target."
            )

    def compare(
        self, name: str, simulated_ms: Optional[float]
    ) -> str:
        """Compare a simulated value with the context, without judging it."""
        if simulated_ms is None:
            return (
                f"{name}: no simulated value available, so no comparison is "
                f"made. {self.not_modelled_by_8i}"
            )
        return (
            f"{name}: simulated {simulated_ms:.3f} ms. The experimental "
            f"context is {self.measured_quantity} ({self.source.split('.')[0]}"
            f".), which is not the same quantity. No agreement or "
            f"disagreement is claimed, and no parameter was adjusted to move "
            f"this number."
        )


@dataclass(frozen=True)
class LiveCircuitResult:
    """3.0D-8I MODE 2: an explicit GF event through the live GFS circuit.

    Everything recorded here came from the existing 3.0D-8A-8G mechanisms. No
    voltage, current or spike time in this object was manufactured: the
    ``voltages`` traces are the four live models' own outputs, the gap currents
    are 3.0D-8C's own ``gap2`` law, and the synaptic current that reaches the
    DLMn is 3.0D-8G's own double exponential evaluated at the live DLMn
    voltage.
    """

    gf_event: GFSpikeEvent
    duration_ms: float
    timestep_ms: float
    segment_count: int
    voltages_mV: Dict[str, Tuple[Dict[str, float], ...]]
    final_voltages_mV: Dict[str, Dict[str, float]]
    spikes: Dict[str, GFSpikeRecord]
    synaptic_events: Tuple[SynapticEventRecord, ...]
    event_timestamps_s: Dict[str, float]
    gap_currents_nA: Dict[str, Tuple[float, ...]]
    peak_gap_current_nA: Dict[str, float]
    settled_voltages_mV: Dict[str, float]
    declared_rest_voltages_mV: Dict[str, float]
    settle_ms: float
    gap_conductance: GapJunctionConductance
    psi_dlmn_peak_conductance_uS: float
    psi_dlmn_peak_conductance_source: str
    latency_context: ExperimentalLatencyContext
    all_finite: bool
    notes: str

    def latency_ms(self, source: str, target: str) -> Optional[float]:
        """Simulated onset latency from one neuron to another, in ms.

        Measured between the two neurons' detected response onsets, NOT
        manufactured and NOT adjusted. ``None`` when either neuron did not
        respond within the run.
        """
        first = self.spikes.get(source)
        second = self.spikes.get(target)
        if first is None or second is None:
            return None
        return (second.time_s - first.time_s) * 1e3

    def timing_report(self) -> str:
        lines = [
            f"Simulated GFS circuit timing, timestep {self.timestep_ms} ms, "
            f"run length {self.duration_ms} ms, {self.segment_count} "
            f"subdivisions per axon.",
            "",
            "READ THE RESPONSE ONSETS WITH THIS CAVEAT: an onset here is the "
            "first crossing of a 1.0 mV OBSERVATION FLOOR above each neuron's "
            "settled voltage, not a spike. Under a strong gap conductance a "
            "postsynaptic neuron can cross that floor while merely being "
            "depolarised, well before it fires, so these are FLOOR-CROSSING "
            "LATENCIES and they shrink as the coupling grows. They are not "
            "conduction times and not spike latencies.",
            "",
            self.latency_context.compare(
                "GF -> TTMn", self.latency_ms("GF", "TTMn")
            ),
            self.latency_context.compare(
                "GF -> PSI", self.latency_ms("GF", "PSI")
            ),
            self.latency_context.compare(
                "GF -> DLMn (via PSI)", self.latency_ms("GF", "DLMn")
            ),
        ]
        for name, record in sorted(self.spikes.items()):
            lines.append(
                f"  {name} response at {record.time_s:.3f} ms on "
                f"{record.segment_id}, {record.voltage_mV:.2f} mV against an "
                f"observation floor of {record.observation_floor_mV} mV (a "
                f"test observation level, NOT a biological threshold)."
            )
        if not self.synaptic_events:
            lines.append(
                "  No PSI->DLMn chemical event was delivered: the PSI axon did "
                "not reach its response observation level within the run. That "
                "is a reported outcome, not a suppressed failure."
            )
        return "\n".join(lines)

    def limitations(self) -> str:
        return (
            f"MODEL-REPRODUCTION CIRCUIT RESULT, NOT A MEASUREMENT. Every "
            f"parameter is a published model parameter of the Augustin et al. "
            f"2019 computational GFS model or an explicitly declared numerical "
            f"fixture, and none is an experimental measurement of these "
            f"neurons. The gap-junction conductance is supplied by the caller "
            f"and 3.0D-7U is UNRESOLVED. {_NO_COUPLING_REASON} No behaviour, "
            f"motor output, neuromuscular junction or muscle is modelled."
        )


@dataclass(frozen=True)
class SensoryBiophysicalGFBoundary:
    """The explicit, typed record of the UNRESOLVED sensory/biophysical join.

    It holds the two results side by side so a reader can see exactly what
    exists and exactly what is missing, and its ``couple_to_live_gf()`` always
    raises. The point is architectural: the missing science cannot be
    overlooked, and it cannot be filled in by accident.
    """

    phenomenological_drive: PhenomenologicalGFDriveTrace
    live_gf: LiveCircuitResult
    coupling_status: CouplingStatus = CouplingStatus.UNRESOLVED
    reason: str = _NO_COUPLING_REASON
    prohibited_assumptions: Tuple[str, ...] = _PROHIBITED_ASSUMPTIONS

    def couple_to_live_gf(self) -> None:
        """ALWAYS RAISES. There is no source-backed coupling to apply.

        Returning a number here is the single most damaging thing this module
        could do, because it would silently convert a fitted phenomenological
        response into a synaptic current and make every downstream result
        unfalsifiable. It raises instead, and says why.
        """
        raise UnsupportedSensoryBiophysicalCoupling(
            f"{_NO_COUPLING_REASON} The sensory drive is a phenomenological "
            f"prediction of {self.phenomenological_drive.peak_weighted_drive_mV():.4f} "
            f"mV and the live GF is a biophysical neuron whose axon reached "
            f"{self.live_gf.final_voltages_mV.get('GF', {}).get('GF_axon#seg0', float('nan')):.2f} "
            f"mV. These are DIFFERENT OBJECTS from DIFFERENT METHODS and no "
            f"source converts one into the other. These are the assumptions "
            f"that are prohibited here: "
            + " | ".join(self.prohibited_assumptions)
        )

    def is_coupled(self) -> bool:
        """Always False."""
        return False

    def describe(self) -> str:
        return (
            f"SENSORY/BIOPHYSICAL GF BOUNDARY: coupling_status = "
            f"{self.coupling_status.value}. {self.reason} "
            f"{len(self.prohibited_assumptions)} assumptions are prohibited. "
            f"couple_to_live_gf() raises "
            f"UnsupportedSensoryBiophysicalCoupling."
        )


# --- helpers -----------------------------------------------------------------

def _resolve_segment(
    network, section_id: str, location: float, morphology_model
) -> str:
    """Resolve a normalized source location to a REAL segment id in ``network``.

    The segment count actually used for each source section is read back off
    the prepared network rather than assumed, because the axons are subdivided
    while the dendrites are carried whole. Guessing would produce a segment id
    that does not exist, and 8I must not invent geometry or re-implement the
    3.0D-7K mapping.
    """
    counts = defaultdict(int)
    ids = {}
    for compartment in network.network.compartments:
        counts[compartment.source_section_id] = max(
            counts[compartment.source_section_id],
            compartment.segment_index + 1,
        )
        ids[(compartment.source_section_id, compartment.segment_index)] = (
            compartment.compartment_id
        )
    if section_id not in counts:
        raise GFSCircuitError(
            f"Section '{section_id}' is not present in the prepared network "
            f"for this neuron. Available source sections: "
            f"{sorted(counts)}. 8I invents no geometry and will not attach a "
            f"synapse to a compartment that does not exist."
        )
    from ..subdivision import map_placement_to_segment

    length = morphology_model.compartments[section_id].geometry.length_um
    index = map_placement_to_segment(location * length, length, counts[section_id])
    segment_id = ids[(section_id, index)]
    if segment_id not in set(network.segment_ids):
        raise GFSCircuitError(
            f"Resolved segment '{segment_id}' for '{section_id}' is not in the "
            f"prepared network. Available: {list(network.segment_ids)}"
        )
    return segment_id


# --- the circuit -------------------------------------------------------------

class GFSCircuit:
    """The end-to-end GFS circuit: four live neurons plus the 8H phenomenology.

    The circuit OWNS no mechanism. It holds the four existing active-neuron
    adapters, builds one prepared network and one state per neuron per run, and
    asks the existing 8C and 8G objects to do the coupling and the synapse. A
    per-run network and state are created through each model's own
    ``initial_state``, which is how determinism is obtained without keeping a
    second, parallel state representation: a second run starts from the same
    declared rest state as the first, so the same event gives the same answer.

    There is no global or class-level mutable state, and no random state.

    THE OBSERVATION FLOOR IS NUMERICAL, AND SAYS SO
    ------------------------------------------------
    ``observation_floor_mV`` defaults to 1.0 mV and is a NUMERICAL OBSERVATION
    LEVEL, not a biological quantity. A run is measured from each neuron's own
    numerical fixed point, and at that fixed point the membrane is stationary
    only to within solver roundoff, of order 1e-12 mV. A floor of zero would
    therefore be crossed by roundoff on the very first timestep and every
    neuron would appear to respond immediately, making every latency
    meaningless. 1.0 mV is a declared numerical floor that comfortably exceeds
    that roundoff.

    It is NOT a spike threshold, NOT a rheobase, NOT a spike-initiation
    mechanism, NOT a behavioural threshold, and it is NOT taken from any
    source. It exists only so that "a response occurred" is a statement about
    the trace rather than about floating-point noise.
    """

    def __init__(
        self,
        gap_conductance: GapJunctionConductance,
        segment_count: int = 11,
        observation_floor_mV: float = 1.0,
        psi_dlmn_peak_conductance_source: str = "paper",
    ) -> None:
        if not isinstance(gap_conductance, GapJunctionConductance):
            raise GFSCircuitError(
                "A GFSCircuit requires an explicit GapJunctionConductance built "
                "through 3.0D-8C's explicit_conductance(value, unit, "
                "provenance). There is deliberately NO default: 3.0D-7U is an "
                "unresolved 1000x unit conflict, and a default would silently "
                "choose a side. Build the conductance yourself and pass it in, "
                "so the choice is visible."
            )
        if not isinstance(segment_count, int) or segment_count < 1:
            raise GFSCircuitError(
                f"segment_count must be an integer >= 1, got {segment_count!r}. "
                f"It is a NUMERICAL discretisation, not a biological claim."
            )
        if not math.isfinite(observation_floor_mV):
            raise GFSCircuitError(
                "observation_floor_mV must be finite."
            )

        self._gap_conductance = gap_conductance
        self._segment_count = segment_count
        self._observation_floor_mV = observation_floor_mV
        self._psi_dlmn_peak_conductance_source = (
            psi_dlmn_peak_conductance_source
        )

        # The four EXISTING adapters, reused rather than reimplemented.
        self._gf = GFActiveAxonModel()
        self._ttmn = TTMActiveAxonModel()
        self._psi = PSIActiveAxonModel()
        self._dlmn = DLMNActiveAxonModel()

        # The 3.0D-8C electrical network, used verbatim.
        self._junction = GFSCouplingNetwork(gap_conductance)

    # -- accessors ---------------------------------------------------------

    @property
    def gap_conductance(self) -> GapJunctionConductance:
        return self._gap_conductance

    @property
    def segment_count(self) -> int:
        return self._segment_count

    @property
    def observation_floor_mV(self) -> float:
        return self._observation_floor_mV

    @property
    def name(self) -> str:
        return MODEL_NAME_GFS_CIRCUIT_V0

    def neuron_models(self) -> Dict[str, object]:
        """The four existing adapters, by id, for inspection."""
        return {
            "GF": self._gf,
            "TTMn": self._ttmn,
            "PSI": self._psi,
            "DLMn": self._dlmn,
        }

    def is_connected_to_the_sensory_phenomenology(self) -> bool:
        """Always False. The boundary is unresolved and stays that way."""
        return False

    def has_random_state(self) -> bool:
        """Always False."""
        return False

    def topology(self) -> Dict[str, Dict[str, str]]:
        """The live circuit topology, resolved against the real networks.

        Every entry is a segment id that actually exists in the prepared
        network, resolved through 3.0D-7K's own placement mapping.
        """
        morphology = self._morphology()
        networks = self._networks(morphology)
        out = {}
        for coupling_id in (COUPLING_GF_TTMN, COUPLING_GF_PSI):
            pair = _gfs_coupling_topology().endpoints(coupling_id)
            pre_key = pair.presynaptic.section_id.split("_")[0]
            post_key = pair.postsynaptic.section_id.split("_")[0]
            out[coupling_id] = {
                "presynaptic_segment": _resolve_segment(
                    networks[pre_key],
                    pair.presynaptic.section_id,
                    pair.presynaptic.location,
                    morphology[pre_key],
                ),
                "postsynaptic_segment": _resolve_segment(
                    networks[post_key],
                    pair.postsynaptic.section_id,
                    pair.postsynaptic.location,
                    morphology[post_key],
                ),
            }
        connection = self._new_psi_dlmn_connection()
        target = connection.postsynaptic_segment_id(
            morphology["DLMn"], self._segment_count
        )
        out[SYNAPSE_PSI_DLMN] = {
            "presynaptic_segment": connection.source_section_id,
            "postsynaptic_segment": target,
        }
        return out

    # -- MODE 1: sensory phenomenology --------------------------------------

    def run_sensory_phenomenology(
        self,
        stimulus: LoomingStimulus,
        duration_s: float = 2.0,
        samples: int = 2001,
    ) -> PhenomenologicalGFDriveTrace:
        """MODE 1: a looming stimulus drives the 8H phenomenological GF model.

        Entirely independent of the live circuit. Nothing in this method
        touches a membrane, and it cannot be used to start the live run.
        """
        if not isinstance(stimulus, LoomingStimulus):
            raise GFSCircuitError(
                "run_sensory_phenomenology requires a 3.0D-8H LoomingStimulus. "
                "Pass a ConstantVelocityLoomingStimulus or a "
                "CallableLoomingStimulus; 8I does not define its own stimulus."
            )
        if not math.isfinite(duration_s) or duration_s <= 0.0:
            raise GFSCircuitError(
                f"Sensory run duration must be positive and finite, got "
                f"{duration_s}."
            )
        if not isinstance(samples, int) or samples < 2:
            raise GFSCircuitError(
                f"Sensory run needs at least 2 samples, got {samples!r}."
            )
        drive = PhenomenologicalGFDrive(
            coefficients=published_ache_gf_coefficients()
        )
        step = duration_s / (samples - 1)
        times = tuple(i * step for i in range(samples))
        evaluated = drive.evaluate_series(times, stimulus)
        description = (
            stimulus.geometry_note()
            if hasattr(stimulus, "geometry_note")
            else "caller-supplied stimulus functions"
        )
        return PhenomenologicalGFDriveTrace(
            times_s=times,
            samples=tuple(evaluated),
            stimulus_description=description,
            drive=drive,
        )

    # -- MODE 3: refused ---------------------------------------------------

    def run_looming_through_live_circuit(
        self,
        stimulus: LoomingStimulus,
        duration_s: float = 2.0,
        samples: int = 2001,
    ) -> None:
        """ALWAYS RAISES. Looming -> live GF is not implemented, deliberately.

        It exists so that the missing coupling has a named, discoverable entry
        point that refuses, rather than an absence a caller might route around.
        """
        raise UnsupportedSensoryBiophysicalCoupling(
            f"LOOMING -> LIVE GF IS NOT IMPLEMENTED, BY DESIGN. "
            f"{_NO_COUPLING_REASON} To run the two layers, run "
            f"run_sensory_phenomenology(stimulus) for the 8H phenomenology and "
            f"run_live_circuit(GFSpikeEvent(...)) for the live GFS circuit, and "
            f"inspect SensoryBiophysicalGFBoundary to see the unresolved join. "
            f"Prohibited here: "
            + " | ".join(_PROHIBITED_ASSUMPTIONS)
        )

    # -- the boundary ------------------------------------------------------

    def boundary(
        self,
        drive_trace: PhenomenologicalGFDriveTrace,
        live_result: LiveCircuitResult,
    ) -> SensoryBiophysicalGFBoundary:
        """Join the two results into the explicit unresolved boundary record."""
        if not isinstance(drive_trace, PhenomenologicalGFDriveTrace):
            raise GFSCircuitError(
                "boundary() requires a PhenomenologicalGFDriveTrace from "
                "run_sensory_phenomenology()."
            )
        if not isinstance(live_result, LiveCircuitResult):
            raise GFSCircuitError(
                "boundary() requires a LiveCircuitResult from "
                "run_live_circuit()."
            )
        return SensoryBiophysicalGFBoundary(
            phenomenological_drive=drive_trace, live_gf=live_result
        )

    # -- MODE 2: the live circuit ------------------------------------------

    def run_live_circuit(
        self,
        gf_event: GFSpikeEvent,
        duration_ms: float = 5.0,
        settle_ms: float = 200.0,
    ) -> LiveCircuitResult:
        """MODE 2: an explicit GF event propagates through the live circuit.

        Order of operations, which IS the method and is the published
        GFS order:

        1. The GF advances with the existing 3.0D-8A direct-stimulation
           numerical fixture, for the fixture's own duration, at the fixture's
           own site. This is a SOLVER FIXTURE, not a visual stimulus.
        2. The GF voltage at each 8C presynaptic site is read off the live GF
           state, and the existing 3.0D-8C ``gap2`` law produces a current for
           that pathway with its own presynaptic voltage.
        3. That current is injected into the live TTMn and the live PSI at
           their own 8C postsynaptic sites, and both are stepped.
        4. A PSI axon response is looked for. The FIRST time it is seen, the
           existing 3.0D-8G double-exponential mechanism is given the event and
           its current is injected into the live DLMn at the 8G postsynaptic
           site, at the live DLMn voltage.
        5. Every step is recorded.

        No voltage, current, spike time or latency here is manufactured, and no
        delay is inserted anywhere.
        """
        if not isinstance(gf_event, GFSpikeEvent):
            raise GFSCircuitError(
                "run_live_circuit requires an explicit GFSpikeEvent. 8I will "
                "not synthesise a GF event from the sensory phenomenology, "
                "because that coupling is unresolved."
            )
        if not math.isfinite(duration_ms) or duration_ms <= 0.0:
            raise GFSCircuitError(
                f"Live run duration must be positive and finite, got "
                f"{duration_ms}."
            )
        if not math.isfinite(settle_ms) or settle_ms < 0.0:
            raise GFSCircuitError(
                f"Live run settle time must be non-negative and finite, got "
                f"{settle_ms}. The settling phase advances the membrane to its "
                f"NUMERICAL fixed point before the event, so that the "
                f"relaxation from the declared E_leak initial value is not "
                f"mistaken for a response. It is a numerical step, not a "
                f"biological claim."
            )

        morphology = self._morphology()
        networks = self._networks(morphology)
        adapters = self.neuron_models()
        states = {
            neuron_id: adapters[neuron_id].initial_state(networks[neuron_id])
            for neuron_id in ("GF", "TTMn", "PSI", "DLMn")
        }
        timestep = adapters["GF"].timestep_ms
        steps = int(round(duration_ms / timestep))
        if steps < 1:
            raise GFSCircuitError(
                f"duration_ms {duration_ms} is shorter than one timestep "
                f"{timestep} ms; the live circuit cannot take a step."
            )

        # The 8A validated numerical fixture, used as a solver trigger only.
        gf_amplitude_A = adapters["GF"].stimulus_fixture_amplitude_A
        gf_duration_ms = adapters["GF"].stimulus_fixture_duration_ms
        gf_stimulus_site = networks["GF"].active_compartment_ids[0]

        # 8C endpoint sites, resolved against the real networks.
        ttmn_pair = _gfs_coupling_topology().endpoints(COUPLING_GF_TTMN)
        psi_pair = _gfs_coupling_topology().endpoints(COUPLING_GF_PSI)
        gf_ttmn_site = _resolve_segment(
            networks["GF"],
            ttmn_pair.presynaptic.section_id,
            ttmn_pair.presynaptic.location,
            morphology["GF"],
        )
        gf_psi_site = _resolve_segment(
            networks["GF"],
            psi_pair.presynaptic.section_id,
            psi_pair.presynaptic.location,
            morphology["GF"],
        )
        ttmn_site = _resolve_segment(
            networks["TTMn"],
            ttmn_pair.postsynaptic.section_id,
            ttmn_pair.postsynaptic.location,
            morphology["TTMn"],
        )
        psi_site = _resolve_segment(
            networks["PSI"],
            psi_pair.postsynaptic.section_id,
            psi_pair.postsynaptic.location,
            morphology["PSI"],
        )

        # The 8G synapse, built fresh so repeated runs are identical.
        connection = self._new_psi_dlmn_connection()
        mechanism = connection.mechanism
        dlmn_site = connection.postsynaptic_segment_id(
            morphology["DLMn"], self._segment_count
        )
        psi_axon_site = networks["PSI"].active_compartment_ids[0]

        ttmn_junction = self._junction.junction(COUPLING_GF_TTMN)
        psi_junction = self._junction.junction(COUPLING_GF_PSI)

        declared_rest_mV = {
            neuron_id: adapters[neuron_id].rest_voltage_mV
            for neuron_id in ("GF", "TTMn", "PSI", "DLMn")
        }
        criterion = (
            "First timestep at which the tracked axon's voltage rises strictly "
            "above the neuron's OWN settled (numerical fixed point) voltage plus "
            "the observation floor. The floor is a TEST OBSERVATION LEVEL. It is "
            "NOT a spike threshold, NOT a rheobase and NOT a spike-initiation "
            "mechanism, and 8I defines none. Anchoring to the settled voltage "
            "rather than to an absolute level is what keeps the initial "
            "relaxation from E_leak out of the measurement."
        )

        traces: Dict[str, list] = {
            neuron_id: [] for neuron_id in ("GF", "TTMn", "PSI", "DLMn")
        }
        gap_history = {COUPLING_GF_TTMN: [], COUPLING_GF_PSI: []}
        spikes: Dict[str, GFSpikeRecord] = {}
        synaptic_events = []
        event_times: Dict[str, float] = {
            "gf_event_s": gf_event.event_time_s
        }
        all_finite = True
        event_fired = False

        # -- a silent settling phase, so the event is measured from rest ----
        #
        # ``initial_state`` starts every compartment at E_leak = -85 mV, while
        # the numerical fixed point of these channels is about -74.67 mV. If
        # the event were applied immediately, every neuron would appear to
        # "respond" within one timestep purely because it was relaxing from
        # its initial value, and every latency would be meaningless.
        #
        # So the circuit first advances all four neurons silently to their
        # numerical fixed point, using the same timestep and the same models,
        # and each neuron's response is then measured against ITS OWN settled
        # voltage. This is a numerical settling phase, not a biological claim:
        # no parameter is changed and no state is invented.
        settle_steps = int(round(settle_ms / timestep))
        for _ in range(settle_steps):
            for neuron_id in ("GF", "TTMn", "PSI", "DLMn"):
                net_current = adapters[neuron_id].step(
                    networks[neuron_id], states[neuron_id], {}, timestep
                )
                for value in net_current.values():
                    if not math.isfinite(value):
                        all_finite = False
        settled = {
            neuron_id: adapters[neuron_id].voltages_mV(
                networks[neuron_id], states[neuron_id]
            )
            for neuron_id in ("GF", "TTMn", "PSI", "DLMn")
        }
        reference = {
            neuron_id: settled[neuron_id][
                networks[neuron_id].active_compartment_ids[0]
            ]
            for neuron_id in ("GF", "TTMn", "PSI", "DLMn")
        }

        for index in range(steps):
            t_s = index * timestep * 1e-3

            # 1. GF, with the numerical fixture for its own declared duration.
            gf_current = {}
            if (
                gf_event.event_time_s <= t_s
                < gf_event.event_time_s + gf_duration_ms * 1e-3
            ):
                gf_current = {gf_stimulus_site: gf_amplitude_A}
                event_fired = True
            adapters["GF"].step(
                networks["GF"], states["GF"], gf_current, timestep
            )
            gf_voltages = adapters["GF"].voltages_mV(
                networks["GF"], states["GF"]
            )
            all_finite = self._record(traces, "GF", gf_voltages) and all_finite

            # 2. 8C gap currents, each from its OWN presynaptic GF site and
            #    the live postsynaptic voltage of that pathway's own neuron.
            ttmn_result = ttmn_junction.current_from_active_membrane(
                gf_voltages[gf_ttmn_site],
                ttmn_voltages[ttmn_site] if traces["TTMn"]
                else reference["TTMn"],
            )
            psi_result = psi_junction.current_from_active_membrane(
                gf_voltages[gf_psi_site],
                psi_voltages[psi_site] if traces["PSI"]
                else reference["PSI"],
            )
            gap_history[COUPLING_GF_TTMN].append(
                ttmn_result.current_from_presynaptic_nA
            )
            gap_history[COUPLING_GF_PSI].append(
                psi_result.current_from_presynaptic_nA
            )
            if not (ttmn_result.is_finite and psi_result.is_finite):
                all_finite = False

            # 3. Inject into the live TTMn and the live PSI and step them.
            adapters["TTMn"].step(
                networks["TTMn"], states["TTMn"],
                {ttmn_site: ttmn_result.current_from_presynaptic_nA * 1e-9},
                timestep,
            )
            ttmn_voltages = adapters["TTMn"].voltages_mV(
                networks["TTMn"], states["TTMn"]
            )
            all_finite = self._record(traces, "TTMn", ttmn_voltages) and all_finite
            adapters["PSI"].step(
                networks["PSI"], states["PSI"],
                {psi_site: psi_result.current_from_presynaptic_nA * 1e-9},
                timestep,
            )
            psi_voltages = adapters["PSI"].voltages_mV(
                networks["PSI"], states["PSI"]
            )
            all_finite = self._record(traces, "PSI", psi_voltages) and all_finite

            # 4. The PSI axon response is looked for as the run proceeds, and
            #    the FIRST one triggers the 8G synapse. Detection uses the
            #    settle-aware reference and the declared numerical floor.
            psi_has_responded = any(
                v > reference["PSI"] + self._observation_floor_mV
                for v in (
                    frame[psi_axon_site] for frame in traces["PSI"]
                )
                if math.isfinite(v)
            )
            if psi_has_responded and not synaptic_events:
                psi_response_time_s = next(
                    index * timestep * 1e-3
                    for index, frame in enumerate(traces["PSI"])
                    if math.isfinite(frame[psi_axon_site])
                    and frame[psi_axon_site]
                    > reference["PSI"] + self._observation_floor_mV
                )
                mechanism.deliver_event(psi_response_time_s)
                synaptic_events.append(
                    SynapticEventRecord(
                        synapse_id=connection.synapse_id,
                        source_neuron=connection.source_neuron,
                        target_neuron=connection.target_neuron,
                        event_time_s=psi_response_time_s,
                        trigger_segment_id=psi_axon_site,
                        trigger_time_s=psi_response_time_s,
                        note=(
                            "The 3.0D-8G double-exponential PSI->DLMn "
                            "mechanism was given this event because the LIVE "
                            "PSI axon voltage rose above the observation level "
                            "at this time. The synaptic current it produces is "
                            "evaluated at the LIVE DLMn voltage each step. The "
                            "synapse is consumed as 8G implemented it, "
                            "including 8G's own unresolved 1000x peak "
                            "conductance conflict, which 8I does not resolve."
                        ),
                    )
                )
                event_times["psi_to_dlmn_synapse_event_s"] = psi_response_time_s

            # 5. DLMn, driven by the 8G current evaluated at the LIVE DLMn
            #    voltage, not at a fixed one.
            dlmn_voltage = (
                traces["DLMn"][-1][dlmn_site]
                if traces["DLMn"] else reference["DLMn"]
            )
            synaptic_current_A = mechanism.injected_current_A(
                t_s, dlmn_voltage * 1e-3
            )
            adapters["DLMn"].step(
                networks["DLMn"], states["DLMn"],
                {dlmn_site: synaptic_current_A} if synaptic_current_A else {},
                timestep,
            )
            dlmn_voltages = adapters["DLMn"].voltages_mV(
                networks["DLMn"], states["DLMn"]
            )
            all_finite = self._record(traces, "DLMn", dlmn_voltages) and all_finite

        # -- post-hoc response detection, over the recorded live traces -----
        #
        # Detecting after the run, rather than inside it, keeps the criterion
        # in one place and means the 8G trigger and the reported response
        # times come from the same rule applied to the same traces.
        tracked = {
            "GF": gf_stimulus_site,
            "TTMn": networks["TTMn"].active_compartment_ids[0],
            "PSI": psi_axon_site,
            "DLMn": networks["DLMn"].active_compartment_ids[0],
        }
        for neuron_id, segment_id in tracked.items():
            rise_index = next(
                (
                    index
                    for index, frame in enumerate(traces[neuron_id])
                    if math.isfinite(frame[segment_id])
                    and frame[segment_id]
                    > reference[neuron_id] + self._observation_floor_mV
                ),
                None,
            )
            if rise_index is None:
                continue
            frame = traces[neuron_id][rise_index]
            spikes[neuron_id] = GFSpikeRecord(
                neuron_id=neuron_id,
                segment_id=segment_id,
                time_s=rise_index * timestep * 1e-3,
                voltage_mV=frame[segment_id],
                observation_floor_mV=self._observation_floor_mV,
                reference_voltage_mV=reference[neuron_id],
                criterion=criterion,
            )

        for neuron_id, record in sorted(spikes.items()):
            event_times[f"{neuron_id}_response_s"] = record.time_s

        return LiveCircuitResult(
            gf_event=gf_event,
            duration_ms=steps * timestep,
            timestep_ms=timestep,
            segment_count=self._segment_count,
            voltages_mV={
                neuron_id: tuple(values) for neuron_id, values in traces.items()
            },
            final_voltages_mV={
                neuron_id: values[-1] for neuron_id, values in traces.items()
            },
            spikes=spikes,
            synaptic_events=tuple(synaptic_events),
            event_timestamps_s=event_times,
            gap_currents_nA={
                key: tuple(values) for key, values in gap_history.items()
            },
            peak_gap_current_nA={
                key: max(values) for key, values in gap_history.items() if values
            },
            gap_conductance=self._gap_conductance,
            settled_voltages_mV=reference,
            declared_rest_voltages_mV=declared_rest_mV,
            settle_ms=settle_steps * timestep,
            psi_dlmn_peak_conductance_uS=mechanism.peak_conductance_uS,
            psi_dlmn_peak_conductance_source=connection.peak_conductance_source,
            latency_context=ExperimentalLatencyContext(),
            all_finite=all_finite,
            notes=(
                f"{gf_event.note()} The GF was driven by the existing 3.0D-8A "
                f"direct-stimulation numerical fixture "
                f"({gf_amplitude_A} A for {gf_duration_ms} ms at "
                f"{gf_stimulus_site}), which is a SOLVER FIXTURE and not a "
                f"visual stimulus and not a biological threshold. The gap "
                f"conductance was supplied by the caller and 3.0D-7U is "
                f"UNRESOLVED: {self._gap_conductance.describe_conversion() if hasattr(self._gap_conductance, 'describe_conversion') else ''} "
                f"The 3.0D-8G peak conductance is consumed unchanged at "
                f"{mechanism.peak_conductance_uS} uS from source "
                f"'{connection.peak_conductance_source}', and 8G's own 1000x "
                f"conflict is not resolved here. The GF event fired: "
                f"{event_fired}."
            ),
        )

    # -- internals ---------------------------------------------------------

    def _morphology(self):
        from ..morphology_builder import build_gfs_compartment_models
        from ..passive_profiles import PROFILE_AUGUSTIN_2019_GFS_PASSIVE

        models = build_gfs_compartment_models()
        for model in models.values():
            model.passive_profile_name = PROFILE_AUGUSTIN_2019_GFS_PASSIVE
        return models

    def _networks(self, morphology):
        return {
            "GF": self._gf.prepare(
                morphology["GF"], segment_count=self._segment_count
            ),
            "TTMn": self._ttmn.prepare_ttmn(
                morphology["TTMn"], segment_count=self._segment_count
            ),
            "PSI": self._psi.prepare_psi(
                morphology["PSI"], segment_count=self._segment_count
            ),
            "DLMn": self._dlmn.prepare_dlmn(
                morphology["DLMn"], segment_count=self._segment_count
            ),
        }

    def _new_psi_dlmn_connection(self) -> PSI_DLMnChemicalSynapse:
        """A fresh 3.0D-8G connection, with 8G's own defaults untouched.

        A new object per call is what makes repeated runs identical: the 8G
        mechanism accumulates delivered events, so reusing one instance across
        runs would make the second run differ from the first. The CONFIGURATION
        is 8G's, unmodified.

        ``psi_dlmn_peak_conductance_source`` is handed straight to 8G's own
        factory. 8G records an UNRESOLVED factor-1000 conflict between the
        paper's 80 uS and the ModelDB source weight of 0.08, and 8I does not
        resolve it. Passing this argument lets a caller run either branch of
        8G's own conflict and see the consequence, which is how the divergence
        documented in 8G becomes visible end to end here. 8I introduces no
        value of its own and neither branch is preferred by this module; the
        default is 8G's own default.
        """
        return PSI_DLMnChemicalSynapse(
            peak_conductance_source=self._psi_dlmn_peak_conductance_source
        )

    @staticmethod
    def _record(traces, neuron_id, voltages) -> bool:
        """Append one timestep of live voltages. Returns whether all were finite.

        The finiteness flag is RETURNED rather than mutated, because passing a
        bool by value into a helper cannot propagate a change back to the
        caller. Getting that wrong would silently report ``all_finite = True``
        for a diverged run, which is precisely the failure this checkpoint
        must not have.
        """
        finite = True
        for value in voltages.values():
            if not math.isfinite(value):
                finite = False
        traces[neuron_id].append(dict(voltages))
        return finite

    def scope_note(self) -> str:
        return GFS_CIRCUIT_SCOPE_NOTE

    def source_references(self) -> Tuple[str, ...]:
        return (
            SOURCE_ACHE_2019,
            SOURCE_AUGUSTIN_2019,
            SOURCE_AUGUSTIN_2011_LATENCY,
            SOURCE_MODELDB_2017_FEATURE_INTEGRATION,
        )


def _gfs_coupling_topology():
    from .electrical_coupling import GFSCouplingTopology

    return GFSCouplingTopology()


#: The single 3.0D-8I scope statement, available without constructing a circuit
#: (which requires a caller-supplied gap conductance).
GFS_CIRCUIT_SCOPE_NOTE = (
    f"{MODEL_NAME_GFS_CIRCUIT_V0}: end-to-end GFS circuit integration. Reuses "
    f"the 3.0D-8A/8D/8E/8F live neurons, the 3.0D-8C gap2 electrical pathways "
    f"and the 3.0D-8G PSI->DLMn chemical synapse without duplicating or "
    f"modifying any of them, and integrates the 3.0D-8H LC4/LPLC2 "
    f"phenomenology as a SEPARATE, independently runnable mode. "
    f"{_NO_COUPLING_REASON} The sensory/biophysical boundary is explicit, "
    f"typed and always refuses to couple. 3.0D-7U is unresolved and the gap "
    f"conductance is required from the caller, never defaulted. 3.0D-8G's "
    f"1000x peak-conductance conflict is consumed unchanged and not "
    f"resolved. Experimental GFS latencies are recorded as validation context "
    f"only and were never fitted. No behaviour, motor output, neuromuscular "
    f"junction or muscle is modelled, and no GF->TTMn or GF->PSI chemical "
    f"component is made live."
)


def gfs_circuit_scope_note() -> str:
    """One statement of what 3.0D-8I integrates and what it refuses to do."""
    return GFS_CIRCUIT_SCOPE_NOTE
