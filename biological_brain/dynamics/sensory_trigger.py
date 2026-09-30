"""Sensory looming -> GF-escape trigger CANDIDATE (3.0D-8L).

THIS LAYER PRODUCES EVIDENCE, NOT A SPIKE, AND NOT A PROBABILITY
----------------------------------------------------------------
A looming stimulus is evaluated by the existing 3.0D-8H phenomenological model
-- LC4 for angular velocity, LPLC2 for angular size, plus the two published
inhibitory components -- and the result is packaged as a
:class:`GFTriggerCandidate`.

A candidate is a statement that SENSORALLY RELEVANT EVIDENCE was present. It is
not a detected action potential, not an injected current, not a voltage in a
neuron, and not a probability that the animal will escape. All four of those
are refused explicitly, and the object is built so that a consumer cannot
confuse it with a real spike even by mistake.

WHY THE CANDIDATE STOPS HERE
----------------------------
von Reyn et al. 2017 is the paper that establishes the feature integration
this project models, and it locates that integration INSIDE THE GF: "Motor
program selection and timing emerge from linear integration of these two
features within the GF." That is the whole problem. The linear combination is
not a function of the stimulus that can be read off a lookup table; it happens
in the GF cell, and the thing that turns it into a spike is GF membrane
dynamics -- exactly the part of the system 3.0D-8I declined to fabricate a
stand-in for.

So the correct place to convert a looming drive into a spike is inside the GF
neuron, and this project does not model the GF's conversion. Ache et al. 2019
supplies a fitted phenomenological GF response in millivolts, which 3.0D-8H
implements, but no source states a universal membrane-voltage threshold, a
rheobase, a synaptic conductance or a coupling that would let that millivolt
figure become a live GF current. Accordingly this module:

    introduces NO threshold and NO rheobase
    introduces NO probability, curve, or likelihood
    introduces NO voltage-to-current conversion
    introduces NO new numeric biological constant of any kind
    does NOT call ``GFActiveAxonModel`` and does NOT run a solver
    does NOT call ``gfs_circuit``'s coupling entry point

It consumes 3.0D-8H and produces a typed candidate. The boundary between the
candidate and a real GF action potential stays exactly where 3.0D-8I left it:
open, typed, and refusing.

THE PIPELINE, AND WHERE THE SEAM IS
-----------------------------------
    LoomingStimulus
        -> 3.0D-8H phenomenological sensory evidence
        -> 3.0D-8L GFTriggerCandidate                        (this module)
        -> [ UNRESOLVED BIOLOGICAL COUPLING ]                (3.0D-8I, open)
        -> actual detected GF action potential               (3.0D-8J)
        -> 3.0D-8K short-mode escape behavior

Only the third-to-last arrow is missing, and it is missing on purpose. The
absence is not a gap to be filled with a convenient number; it is the current
state of the science this project is tracking.

WHY A CANDIDATE IS THE RIGHT OBJECT RATHER THAN A PROBABILITY
--------------------------------------------------------------
von Reyn et al. 2017 is titled "Feature Integration Drives PROBABILISTIC
Behavior in the Drosophila Escape Response", and its abstract states that
linear integration "appropriately BIASES motor selection to rapid, GF-mediated
escapes during fast looms". So even a fully correct sensory model does not
determine whether the animal escapes: it biases the selection. A candidate is
therefore the honest output. Turning it into a probability would require a
probability model, a calibration against behavioural data, and the unresolved
coupling, and none of those exists here.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .gf_sensory_drive import (
    LoomingStimulus,
    PhenomenologicalGFDrive,
    SensoryDriveSample,
    published_ache_gf_coefficients,
)

MODEL_NAME_SENSORY_TRIGGER_V0 = "sensory_trigger_v0"


# --- sources -----------------------------------------------------------------

SOURCE_ACHE_2019 = (
    "Ache JM, Polsky J, Alghailani S, Parekh R, Breads P, Peek MY, Bock DD, "
    "von Reyn CR, Card GM (2019). Neural basis for looming size and velocity "
    "encoding in the Drosophila giant fiber escape pathway. Curr Biol "
    "29(6):1073-1081.e4. PMID 30827912. "
    "https://pubmed.ncbi.nlm.nih.gov/30827912/ . SOURCE of the LC4 angular-"
    "velocity and LPLC2 angular-size decomposition of the looming drive, and "
    "of the fitted phenomenological GF response that 3.0D-8H implements. "
    "Establishes that LC4 and LPLC2 are direct visual inputs to the GF whose "
    "contributions sum to reproduce the GF looming response. It supplies NO "
    "universal membrane-voltage threshold, NO rheobase, NO synaptic "
    "conductance, NO receptor kinetic and NO release probability for either "
    "pathway, and none is invented here."
)

SOURCE_VON_REYN_2017 = (
    "von Reyn CR, Nern A, Williamson WR, Breads P, Wu M, Namiki S, Card GM "
    "(2017). Feature integration drives probabilistic behavior in the "
    "Drosophila escape response. Neuron 94(6):1190-1204.e6. PMID 28641115. "
    "doi:10.1016/j.neuron.2017.05.036. "
    "https://pubmed.ncbi.nlm.nih.gov/28641115/ . THE KEY SOURCE FOR WHY THIS "
    "LAYER STOPS WHERE IT DOES. It identifies a visual projection neuron "
    "conveying predator-approach information to the GF, establishes that this "
    "input 'encodes angular expansion velocity, whereas other input cell "
    "type(s) encode angular size', and then states the decisive fact: 'Motor "
    "program selection and timing emerge from linear integration of these two "
    "features WITHIN THE GF.' The integration is a property of the GF CELL, so "
    "converting a looming drive into a spike requires GF membrane dynamics "
    "rather than a function of the stimulus. It also states that the outcome "
    "is PROBABILISTIC and that linear integration only 'appropriately BIASES "
    "motor selection to rapid, GF-mediated escapes during fast looms', which "
    "is why a CANDIDATE and not a probability is the honest output."
)

SOURCE_DEVINENI_SCAPLEN_2022 = (
    "Devineni AV, Scaplen KM (2022). Neural circuits underlying behavioral "
    "flexibility: insights from Drosophila. Front Behav Neurosci 15:821680. "
    "PMID 35069145. https://pmc.ncbi.nlm.nih.gov/articles/PMC8770416/ . "
    "CONTEXT. Records that responses to looming stimuli 'are modulated by "
    "behavioral state', that the giant fiber neurons 'mediate short but not "
    "long takeoffs', and that the two motor pathways are 'differentially "
    "sensitive to specific features of the looming stimulus, including looming "
    "size and velocity'. It is a REVIEW that cites von Reyn et al. 2014 and "
    "2017; it is not itself a primary report, and no number is taken from it."
)

SOURCE_AUGUSTIN_2019_SENSORY = (
    "Augustin H, Zylbertal A, Partridge L (2019). A computational model of the "
    "escape response latency in the giant fiber system of Drosophila "
    "melanogaster. eNeuro 6(2):ENEURO.0423-18.2019. PMID 31001574, ModelDB "
    "245415. https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ . CONTEXT for "
    "the biophysical target of this drive. It models the GF as an active "
    "neuron and measures 'the latency to the AP peak in the TTMn and DLMn'. "
    "It contains no LC4 or LPLC2 sensory drive and no sensory-to-GF coupling, "
    "so it contributes no quantity to this module; it is recorded because it "
    "is the model that a future coupling would have to reach."
)


# --- refusal statements ------------------------------------------------------

_NO_THRESHOLD = (
    "NO THRESHOLD, RHEOBASE, OR VOLTAGE CONVERSION EXISTS HERE. The only thing "
    "this module reports is what the published 3.0D-8H phenomenological model "
    "computed. No membrane-voltage threshold, no spike threshold, no rheobase, "
    "no transfer function, no conductance, no input resistance and no "
    "voltage-to-current factor is defined, calibrated, fitted or implied. The "
    "3.0D-7E GF input resistance of 75 Mohm is experimentally constrained "
    "CONTEXT and is deliberately not used. If a number is wanted here, it is "
    "missing science, not an oversight."
)

_NO_PROBABILITY = (
    "THIS IS NOT A PROBABILITY OF ESCAPE. von Reyn et al. 2017 is titled "
    "'Feature Integration Drives PROBABILISTIC Behavior', and its own abstract "
    "says the linear integration only 'appropriately BIASES motor selection to "
    "rapid, GF-mediated escapes during fast looms'. A correct sensory model "
    "therefore biases behaviour; it does not determine it. No probability, "
    "likelihood, confidence, odds, escape fraction or decision variable is "
    "computed or exposed, and the presence of a candidate must never be read "
    "as a forecast that the animal will escape."
)

_NOT_A_SPIKE = (
    "THIS IS NOT A DETECTED GF ACTION POTENTIAL. A candidate is SENSORY "
    "EVIDENCE: the output of a fitted phenomenological function of stimulus "
    "coordinates, evaluated in millivolts. An action potential is a state of a "
    "neuron membrane, detected by the existing 3.0D-8A waveform criterion "
    "inside the 3.0D-8J circuit. Those are different objects produced by "
    "different methods from different data. A millivolt value from 3.0D-8H is "
    "not a voltage in the GF, and no consumer may treat it as one."
)


class SensoryTriggerError(Exception):
    """Base class for sensory trigger-candidate failures."""


class SensoryTriggerStatus(Enum):
    """What, if anything, the sensory model found.

    ``EVIDENCE_PRESENT`` means the phenomenological model evaluated a defined
    stimulus. It does NOT mean the drive exceeded anything, because nothing was
    compared to anything.
    """

    EVIDENCE_PRESENT = "sensory_evidence_present"
    NO_STIMULUS_EVIDENCE = "no_stimulus_evidence"


# --- the candidate -----------------------------------------------------------


@dataclass(frozen=True)
class GFTriggerCandidate:
    """Sensory evidence that a looming stimulus engaged the GF drive model.

    The component and drive values are PEAKS over the evaluated window, taken
    verbatim from 3.0D-8H's own samples. Nothing is recomputed, rescaled,
    normalised, clipped or compared.

    The object deliberately does NOT carry any of the following, and their
    absence is tested rather than merely intended:

        ``ap_detected``          -- a real spike flag; this class has no such
                                    field, so ``candidate.ap_detected`` raises
        ``event_time_s``         -- a 3.0D-8I GFSpikeEvent field
        ``source``               -- a 3.0D-8I GFSpikeEvent field
        ``provenance``           -- a 3.0D-8I GFSpikeEvent field
        ``is_a_spike``           -- 3.0D-8J's spike-record flag

    Instead it exposes ``is_a_detected_gf_action_potential``, which is always
    False, and ``couple_to_live_gf()``, which always raises.
    """

    looming_stimulus_present: bool
    status: SensoryTriggerStatus
    peak_lc4_component_mV: float
    peak_lplc2_component_mV: float
    peak_inhibitory_component_1_mV: float
    peak_inhibitory_component_2_mV: float
    total_phenomenological_gf_drive_mV: float
    peak_time_s: float
    times_s: Tuple[float, ...]
    samples: Tuple[SensoryDriveSample, ...]
    stimulus_description: str
    has_evidence: bool = True
    is_a_detected_gf_action_potential: bool = False
    is_sensory_evidence_only: bool = True
    is_a_probability_of_escape: bool = False

    def __post_init__(self) -> None:
        if self.is_a_detected_gf_action_potential:
            raise SensoryTriggerError(
                "A sensory trigger candidate is NEVER a detected GF action "
                "potential. That flag is hard False and must stay False."
            )
        if not self.is_sensory_evidence_only:
            raise SensoryTriggerError(
                "A sensory trigger candidate is sensory evidence only."
            )
        if self.is_a_probability_of_escape:
            raise SensoryTriggerError(
                "A sensory trigger candidate is not a probability of escape. "
                + _NO_PROBABILITY
            )
        if not self.has_evidence:
            raise SensoryTriggerError(
                "A trigger candidate must carry evidence. Use the factory, "
                "which represents 'no stimulus' with a status rather than by "
                "emptying this object."
            )
        # Status and presence must agree, so the pair cannot be contradictory.
        if self.looming_stimulus_present != (
            self.status is SensoryTriggerStatus.EVIDENCE_PRESENT
        ):
            raise SensoryTriggerError(
                f"looming_stimulus_present={self.looming_stimulus_present} "
                f"contradicts status={self.status.value}."
            )
        if not self.samples:
            raise SensoryTriggerError(
                "A trigger candidate must carry the 3.0D-8H samples it was "
                "derived from, so the evidence is auditable."
            )
        if len(self.samples) != len(self.times_s):
            raise SensoryTriggerError(
                "times_s and samples must be the same length."
            )
        for name in (
            "peak_lc4_component_mV", "peak_lplc2_component_mV",
            "peak_inhibitory_component_1_mV",
            "peak_inhibitory_component_2_mV",
            "total_phenomenological_gf_drive_mV", "peak_time_s",
        ):
            if not math.isfinite(getattr(self, name)):
                raise SensoryTriggerError(f"{name} must be finite.")
        if self.peak_time_s < 0.0:
            raise SensoryTriggerError(
                f"peak_time_s must be non-negative, got {self.peak_time_s}."
            )
        if not self.stimulus_description:
            raise SensoryTriggerError(
                "A trigger candidate must describe the stimulus it evaluated."
            )
        # The peak time must be an actual sample time, not an interpolation.
        if self.peak_time_s not in self.times_s:
            raise SensoryTriggerError(
                f"peak_time_s={self.peak_time_s} is not one of the evaluated "
                f"sample times. The peak must be preserved from 3.0D-8H, not "
                f"interpolated."
            )
        # And the reported values must be the maxima of the carried samples,
        # so nothing was silently altered between 8H and here.
        if self.total_phenomenological_gf_drive_mV != max(
            sample.weighted_gf_drive_mV for sample in self.samples
        ):
            raise SensoryTriggerError(
                "total_phenomenological_gf_drive_mV is not the maximum of the "
                "carried 3.0D-8H samples."
            )

    # -- the boundary, stated as API -------------------------------------

    @property
    def is_a_spike(self) -> bool:
        """Always False.

        Named to match 3.0D-8J's spike-record flag so that a consumer testing
        the same attribute on either object gets the honest answer: a real
        spike is False for a candidate, because a candidate never is one.
        """
        return False

    def couple_to_live_gf(self) -> None:
        """ALWAYS RAISES. There is no source-backed sensory-to-GF coupling.

        Raises the same typed exception 3.0D-8I already raises for this
        boundary, so a caller handles one exception type for the whole seam
        rather than a different one per module. The 3.0D-8I import happens
        here, inside the refusal, so that the ordinary sensory path never
        pulls in the solver stack.
        """
        from .gfs_circuit import UnsupportedSensoryBiophysicalCoupling

        raise UnsupportedSensoryBiophysicalCoupling(
            f"{_NOT_A_SPIKE} {_NO_THRESHOLD} The peak phenomenological GF drive "
            f"for this stimulus was {self.total_phenomenological_gf_drive_mV:.6f} "
            f"mV at t = {self.peak_time_s:.6f} s, with LC4 "
            f"{self.peak_lc4_component_mV:.6f} mV and LPLC2 "
            f"{self.peak_lplc2_component_mV:.6f} mV. von Reyn et al. 2017 "
            f"locates the linear integration WITHIN THE GF cell, so the "
            f"conversion to a spike is a property of GF membrane dynamics, "
            f"which this project does not model. No threshold is applied here "
            f"to stand in for it."
        )

    def components_mV(self) -> dict:
        """The four published component peaks, by name."""
        return {
            "lc4": self.peak_lc4_component_mV,
            "lplc2": self.peak_lplc2_component_mV,
            "inhibitory_component_1": self.peak_inhibitory_component_1_mV,
            "inhibitory_component_2": self.peak_inhibitory_component_2_mV,
        }

    def to_consumer_dict(self) -> dict:
        """Plain data for a consumer that knows nothing about neurons.

        ``gf_ap_detected`` is present and explicitly ``None``. It is never
        ``True`` and never omitted, so a consumer reading the key can tell the
        difference between "not a spike" and "this object did not consider
        spikes".
        """
        return {
            "kind": "gf_trigger_candidate",
            "status": self.status.value,
            "looming_stimulus_present": self.looming_stimulus_present,
            "components_mV": self.components_mV(),
            "total_phenomenological_gf_drive_mV": (
                self.total_phenomenological_gf_drive_mV
            ),
            "peak_time_s": self.peak_time_s,
            "is_sensory_evidence_only": self.is_sensory_evidence_only,
            "is_a_detected_gf_action_potential": (
                self.is_a_detected_gf_action_potential
            ),
            "gf_ap_detected": None,
            "is_a_probability_of_escape": self.is_a_probability_of_escape,
            "unresolved_before_a_real_gf_ap": (
                "UNRESOLVED: the 3.0D-8I sensory-to-biophysical GF coupling. "
                "No action potential exists until that step is taken."
            ),
        }

    def summary(self) -> str:
        if not self.looming_stimulus_present:
            return (
                "SENSORY EVIDENCE: none. The 3.0D-8H phenomenological model "
                "evaluated no defined stimulus over this window, so there is no "
                "trigger candidate. No component, no drive, and NO GF action "
                "potential. " + _NOT_A_SPIKE
            )
        components = self.components_mV()
        return (
            "SENSORY EVIDENCE -> GF TRIGGER CANDIDATE (NOT A SPIKE).\n"
            f"  stimulus: {self.stimulus_description}\n"
            f"  peak LC4 (angular velocity) component : "
            f"{components['lc4']:.6f} mV\n"
            f"  peak LPLC2 (angular size) component   : "
            f"{components['lplc2']:.6f} mV\n"
            f"  peak inhibitory component 1          : "
            f"{components['inhibitory_component_1']:.6f} mV\n"
            f"  peak inhibitory component 2          : "
            f"{components['inhibitory_component_2']:.6f} mV\n"
            f"  total phenomenological GF drive       : "
            f"{self.total_phenomenological_gf_drive_mV:.6f} mV "
            f"(peak at t = {self.peak_time_s:.6f} s)\n"
            f"  {self.samples.__len__()} samples evaluated, all preserved.\n"
            f"  STATUS: {self.status.value}. This is sensory evidence that the "
            f"looming drive engaged the published GF model. It is NOT a "
            f"detected GF action potential, NOT a current, NOT a threshold "
            f"crossing, and NOT a probability of escape.\n"
            f"  REMAINING SEAM: 3.0D-8I sensory-to-biophysical GF coupling, "
            f"unresolved. couple_to_live_gf() raises."
        )

    def limitations(self) -> str:
        return f"{_NOT_A_SPIKE} {_NO_THRESHOLD} {_NO_PROBABILITY}"

    def source_references(self) -> Tuple[str, ...]:
        return (
            SOURCE_ACHE_2019,
            SOURCE_VON_REYN_2017,
            SOURCE_DEVINENI_SCAPLEN_2022,
            SOURCE_AUGUSTIN_2019_SENSORY,
        )


# --- the factory -------------------------------------------------------------


def gf_trigger_candidate_from_stimulus(
    stimulus: LoomingStimulus,
    duration_s: float = 2.0,
    samples: int = 2001,
) -> GFTriggerCandidate:
    """Evaluate a looming stimulus with 3.0D-8H and package the evidence.

    Consumes only 3.0D-8H. It does not import, construct or call the live GF
    solver, the 3.0D-8I circuit, the 3.0D-8J AP detector or the 3.0D-8K motor
    layer, and it applies no threshold of any kind.

    "Is a looming stimulus present" is answered WITHOUT a threshold: it is True
    when 3.0D-8H actually evaluated a defined stimulus feature at some sampled
    time, which 3.0D-8H reports through its own ``in_prehistory`` flag. A
    window entirely inside the 3.0D-8H prehistory has no defined stimulus, so
    the answer is False and every component is exactly zero.

    Note that a ``q <= 0`` stimulus is refused by 3.0D-8H itself, which raises
    ``AngularSizeError``: "no stimulus" is represented by the prehistory, not by
    a non-positive angular size.
    """
    if not isinstance(stimulus, LoomingStimulus):
        raise SensoryTriggerError(
            "gf_trigger_candidate_from_stimulus() requires a 3.0D-8H "
            "LoomingStimulus, such as ConstantVelocityLoomingStimulus or "
            "CallableLoomingStimulus. 8L defines no stimulus of its own."
        )
    if not math.isfinite(duration_s) or duration_s <= 0.0:
        raise SensoryTriggerError(
            f"duration_s must be positive and finite, got {duration_s}."
        )
    if not isinstance(samples, int) or samples < 2:
        raise SensoryTriggerError(
            f"samples must be an integer >= 2, got {samples!r}."
        )

    drive = PhenomenologicalGFDrive(
        coefficients=published_ache_gf_coefficients()
    )
    step = duration_s / (samples - 1)
    times = tuple(i * step for i in range(samples))
    evaluated = tuple(drive.evaluate_series(times, stimulus))

    # Threshold-free presence: did 8H evaluate a defined stimulus at all?
    present = any(not sample.in_prehistory for sample in evaluated)

    best = max(evaluated, key=lambda sample: sample.weighted_gf_drive_mV)
    description = (
        stimulus.geometry_note()
        if hasattr(stimulus, "geometry_note")
        else "caller-supplied stimulus functions"
    )
    return GFTriggerCandidate(
        looming_stimulus_present=present,
        status=(
            SensoryTriggerStatus.EVIDENCE_PRESENT
            if present else SensoryTriggerStatus.NO_STIMULUS_EVIDENCE
        ),
        peak_lc4_component_mV=max(
            sample.lc4_component_mV for sample in evaluated
        ),
        peak_lplc2_component_mV=max(
            sample.lplc2_component_mV for sample in evaluated
        ),
        peak_inhibitory_component_1_mV=max(
            sample.inhibitory_component_1_mV for sample in evaluated
        ),
        peak_inhibitory_component_2_mV=max(
            sample.inhibitory_component_2_mV for sample in evaluated
        ),
        total_phenomenological_gf_drive_mV=best.weighted_gf_drive_mV,
        peak_time_s=best.t_s,
        times_s=times,
        samples=evaluated,
        stimulus_description=description,
    )


def sensory_trigger_scope_note() -> str:
    """One statement of what 8L does and refuses to do."""
    return (
        f"{MODEL_NAME_SENSORY_TRIGGER_V0}: evaluates a looming stimulus with the "
        f"existing 3.0D-8H phenomenological model and packages the result as a "
        f"typed GFTriggerCandidate -- sensory evidence that the published GF "
        f"drive model engaged, with all four published components and the peak "
        f"time preserved verbatim. {_NOT_A_SPIKE} {_NO_THRESHOLD} "
        f"{_NO_PROBABILITY} It adds no solver, no spike detector, no threshold, "
        f"no probability and no new numeric biological constant, and it does "
        f"not import or call the live GF solver, the 3.0D-8I circuit, the "
        f"3.0D-8J AP detector or the 3.0D-8K motor layer. The seam between this "
        f"candidate and a real GF action potential is the 3.0D-8I "
        f"sensory-to-biophysical coupling, which stays unresolved and typed, "
        f"because von Reyn et al. 2017 locates the linear integration within "
        f"the GF cell."
    )
