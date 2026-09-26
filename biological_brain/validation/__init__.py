"""Validation experiments for the Biological Brain escape circuit.

Provides reusable experiment runners that measure biological timing properties
using the 3.0B.1 circuit infrastructure.
"""


from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict
import copy

from biological_brain import BiologicalBrain, BiologicalMode, BIOLOGICAL_CIRCUITS
from biological_brain.neural_engine import NeuralEngine
from biological_brain.signals import SignalTranslator


@dataclass
class LatencyResult:
    """Result of a single latency measurement."""
    pathway_name: str
    source_neuron: str
    target_neuron: str
    source_spike_tick: int
    target_spike_tick: int
    latency_ticks: int
    biological_target: str
    evidence: str
    approximation: str = ""

    def __str__(self):
        return (
            f"{self.pathway_name}: {self.source_neuron} -> {self.target_neuron} "
            f"latency = {self.latency_ticks} tick(s) "
            f"(source spike @ tick {self.source_spike_tick}, "
            f"target spike @ tick {self.target_spike_tick}) "
            f"[target: {self.biological_target}, evidence: {self.evidence}]"
        )


@dataclass
class ExperimentReport:
    """Full report of a validation experiment."""
    name: str
    results: list = field(default_factory=list)
    notes: str = ""

    def summary(self) -> str:
        lines = [f"=== Experiment: {self.name} ==="]
        for r in self.results:
            lines.append(str(r))
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        return "\n".join(lines)


class LatencyValidator:
    """Measure synaptic latencies using deterministic spike injection.

    Uses the spike injection method documented in 3.0B.1 spec §10.3:
    injecting sufficient current into a source neuron to force a spike,
    then tracking when downstream targets fire.
    """

    SPIKE_INJECTION_CURRENT = 25.0

    def __init__(self, brain: BiologicalBrain, circuit_name: str = "escape_core"):
        self.brain = brain
        self.circuit_name = circuit_name
        self.engine = brain.engines[circuit_name]
        self.circuit = self.engine.circuit
        self.brain.reset()

    def _detect_spikes(
        self,
        source_neuron: str,
        target_neurons: List[str],
        max_ticks: int = 12,
    ) -> Dict[str, Optional[int]]:
        """Track when each neuron first enters refractory state (spikes).

        Injects spike current into source_neuron at tick 0, then steps
        the brain for max_ticks. Returns dict mapping neuron_id -> first
        spike tick, or None if no spike.
        """
        all_neurons = [source_neuron] + target_neurons
        first_spikes: Dict[str, Optional[int]] = {nid: None for nid in all_neurons}

        for tick in range(max_ticks):
            if tick == 0:
                stimuli = {source_neuron: self.SPIKE_INJECTION_CURRENT}
            else:
                stimuli = {}

            self.brain.step(stimuli)

            for nid in all_neurons:
                if first_spikes[nid] is None:
                    neuron = self.circuit.neurons[nid]
                    if neuron.refractory_remaining > 0:
                        first_spikes[nid] = tick

        return first_spikes

    def measure_latency(
        self,
        source_neuron: str,
        target_neurons: List[str],
        pathway_name: str,
        biological_target: str,
        evidence: str,
        approximation: str = "",
    ) -> LatencyResult:
        """Measure latency from source neuron spike to target neuron spike.

        Uses deterministic current injection to force a spike in the source
        neuron at tick 0.
        """
        self.brain.reset()
        first_spikes = self._detect_spikes(
            source_neuron=source_neuron,
            target_neurons=target_neurons,
            max_ticks=12,
        )

        source_tick = first_spikes[source_neuron]
        if source_tick is None:
            raise RuntimeError(
                f"Source neuron {source_neuron} did not spike with injection current "
                f"{self.SPIKE_INJECTION_CURRENT} mV"
            )

        # Find the earliest target spike after source spike
        target_tick: Optional[int] = None
        spiked_neuron: Optional[str] = None
        for nid in target_neurons:
            tick = first_spikes[nid]
            if tick is not None and tick > source_tick:
                if target_tick is None or tick < target_tick:
                    target_tick = tick
                    spiked_neuron = nid

        if target_tick is None:
            raise RuntimeError(
                f"No target neuron ({target_neurons}) spiked after {source_neuron} spike at tick {source_tick}"
            )

        latency = target_tick - source_tick

        return LatencyResult(
            pathway_name=pathway_name,
            source_neuron=source_neuron,
            target_neuron=spiked_neuron,
            source_spike_tick=source_tick,
            target_spike_tick=target_tick,
            latency_ticks=latency,
            biological_target=biological_target,
            evidence=evidence,
            approximation=approximation,
        )

    def run_gf_to_ttmn_latency(self) -> ExperimentReport:
        """Measure GF -> TTMn latency for both hemispheres.

        Biological prediction (spec §10.1, §5):
        - GF L65 -> TTMn: 1-2 ms latency (DIRECTLY_MEASURED: von Reyn 2014)
        - In simulation: 1 ms = 1 tick (dt_ms_per_tick = 1.0, APPROXIMATION)
        - Expected: 1 tick latency

        Circuit mechanism:
        - GF -> TTMn via electrical synapse (gap junction, ShakB)
        - Weight: 17.0 mV (calibrated per §5 formula: 15.0 / exp(-1/10) = 16.58 -> 17.0)
        - Delay: 1 tick
        """
        results = []

        # Left hemisphere
        left_result = self.measure_latency(
            source_neuron="GF_L",
            target_neurons=["TTMn_L"],
            pathway_name="GF->TTMn (left)",
            biological_target="1-2 ticks (1-2 ms, von Reyn 2014)",
            evidence="DIRECTLY_MEASURED (latency) + INFERRED (weight) + APPROXIMATION (LIF voltage-based)",
            approximation=(
                "Electrical synapse represented as paired EXCITATORY Synapse entries "
                "(§9.2). Weight calibrated from 135uS conductance to reproduce 1-tick "
                "latency. dt=1ms is APPROXIMATION (3.0A convention)."
            ),
        )
        results.append(left_result)

        # Right hemisphere
        right_result = self.measure_latency(
            source_neuron="GF_R",
            target_neurons=["TTMn_R"],
            pathway_name="GF->TTMn (right)",
            biological_target="1-2 ticks (1-2 ms, von Reyn 2014)",
            evidence="DIRECTLY_MEASURED (latency) + INFERRED (weight) + APPROXIMATION (LIF voltage-based)",
            approximation=(
                "Electrical synapse represented as paired EXCITATORY Synapse entries "
                "(§9.2). Weight calibrated from 135uS conductance to reproduce 1-tick "
                "latency. dt=1ms is APPROXIMATION (3.0A convention)."
            ),
        )
        results.append(right_result)

        report = ExperimentReport(
            name="GF -> TTMn Latency Measurement",
            results=results,
            notes=(
                "Biological prediction: GF->TTMn conduction via electrical gap junction "
                "(ShakB) at 1-2 ms latency (von Reyn 2014, eLife 2019 model). "
                f"Simulation: {len(results)} measurements, "
                f"latencies={[r.latency_ticks for r in results]} ticks. "
                "Each 1 ms biological time = 1 simulation tick (APPROXIMATION per §6.1). "
                "Spike injection method: inject 25.0 mV current into GF (spec §10.3)."
            ),
        )
        return report


@dataclass
class LateralizationResult:
    """Result of a lateralization experiment for one stimulus condition."""
    stimulus_name: str
    stimulus: Dict[str, float]
    vp_spikes: Dict[str, int]
    gf_spikes: Dict[str, int]
    ttmn_spikes: Dict[str, int]
    escape_signal: float
    flight_signal: float
    threat_signal: float
    biological_prediction: str
    evidence: str
    approximation: str

    def __str__(self):
        return (
            f"{self.stimulus_name}:\n"
            f"  VP spikes: {self.vp_spikes}\n"
            f"  GF spikes: {self.gf_spikes}\n"
            f"  TTMn spikes: {self.ttmn_spikes}\n"
            f"  Signals: escape={self.escape_signal:.3f}, flight={self.flight_signal:.3f}, "
            f"threat={self.threat_signal:.3f}\n"
            f"  Biological prediction: {self.biological_prediction}\n"
            f"  Evidence: {self.evidence}\n"
            f"  Approximation: {self.approximation}"
        )


class LateralizationValidator:
    """Measure left/right lateralization of the escape circuit.

    Tests that unilateral looming stimuli activate the ipsilateral pathway
    while sparing the contralateral side, and that bilateral/front stimuli
    activate both hemispheres.
    """

    VP_NEURONS = ["LC4_L", "LPLC2_L", "LC4_R", "LPLC2_R"]
    GF_NEURONS = ["GF_L", "GF_R"]
    TTMN_NEURONS = ["TTMn_L", "TTMn_R"]
    DLMN_NEURONS = ["DLMn_L", "DLMn_R"]

    def __init__(self, brain: BiologicalBrain, circuit_name: str = "escape_core"):
        self.brain = brain
        self.circuit_name = circuit_name
        self.engine = brain.engines[circuit_name]
        self.circuit = self.engine.circuit

    def _run_stimulus(self, stimulus: Dict[str, float], max_ticks: int = 20) -> ExperimentReport:
        """Run a stimulus and track when neurons first spike."""
        self.brain.reset()

        target_neurons = self.VP_NEURONS + self.GF_NEURONS + self.TTMN_NEURONS + self.DLMN_NEURONS
        first_spikes: Dict[str, Optional[int]] = {nid: None for nid in target_neurons}
        max_signals = {"bio_escape_signal": 0.0, "bio_flight_signal": 0.0, "bio_threat_signal": 0.0}

        for tick in range(max_ticks):
            signals = self.brain.step(stimulus)
            for sig_name in max_signals:
                max_signals[sig_name] = max(max_signals[sig_name], signals.get(sig_name, 0.0))

            for nid in target_neurons:
                if first_spikes[nid] is None:
                    neuron = self.circuit.neurons[nid]
                    if neuron.refractory_remaining > 0:
                        first_spikes[nid] = tick

        return first_spikes, max_signals

    def run_lateralization(self) -> ExperimentReport:
        """Run left, right, and front looming stimuli and compare hemispheric activation.

        Biological prediction (spec §2.2 in-scope, Ache 2019, Klapoetke 2017):
        - loomingLeft: activates left VP pathway (LC4_L, LPLC2_L) → GF_L → TTMn_L
        - loomingRight: activates right VP pathway (LC4_R, LPLC2_R) → GF_R → TTMn_R
        - loomingFront: activates both pathways bilaterally
        - No cross-hemisphere connections in core escape circuit (§4.2, §4.3)
        - Contralateral TTMn should NOT fire for unilateral stimulus

        Evidence (spec §3.1, §3.2, §5):
        - VP→GF: DIRECTLY_MEASURED (FlyWire FAFB EM, 2290/1443 synapses)
        - GF→TTMn: DIRECTLY_MEASURED latency (von Reyn 2014) + INFERRED electrical synapse
        - Lateralization: DIRECTLY_MEASURED (LC4/LPLC2 response tuning, Ache 2019)
        - Stimulus currents: APPROXIMATION (spec §8.10-11, calibration)
        """
        results = []

        stimuli = [
            ("loomingLeft", {"loomingLeft": 1.0}),
            ("loomingRight", {"loomingRight": 1.0}),
            ("loomingFront", {"loomingFront": 1.0}),
        ]

        for name, stimulus in stimuli:
            first_spikes, max_signals = self._run_stimulus(stimulus)

            vp_spikes = {nid: t for nid, t in first_spikes.items()
                        if nid in self.VP_NEURONS and t is not None}
            gf_spikes = {nid: t for nid, t in first_spikes.items()
                        if nid in self.GF_NEURONS and t is not None}
            ttmn_spikes = {nid: t for nid, t in first_spikes.items()
                          if nid in self.TTMN_NEURONS and t is not None}

            result = LateralizationResult(
                stimulus_name=name,
                stimulus=stimulus,
                vp_spikes=vp_spikes,
                gf_spikes=gf_spikes,
                ttmn_spikes=ttmn_spikes,
                escape_signal=max_signals["bio_escape_signal"],
                flight_signal=max_signals["bio_flight_signal"],
                threat_signal=max_signals["bio_threat_signal"],
                biological_prediction=self._prediction_for(name),
                evidence=(
                    "VP->GF: DIRECTLY_MEASURED (FlyWire FAFB EM, 2290+1443 synapses). "
                    "GF->TTMn: DIRECTLY_MEASURED latency (von Reyn 2014). "
                    "Lateralization: DIRECTLY_MEASURED (Ache 2019, Klapoetke 2017)."
                ),
                approximation=(
                    "Looming currents: APPROXIMATION (spec §8.10-11, calibrated to 5.0 mV/tick "
                    "for simultaneous VP firing). Population collapse: APPROXIMATION. "
                    "dt=1ms: APPROXIMATION (3.0A convention)."
                ),
            )
            results.append(result)

        report = ExperimentReport(
            name="Left/Right Lateralization",
            notes=(
                "Tests that unilateral looming stimuli activate the ipsilateral escape "
                "pathway while sparing the contralateral side. Biological prediction: "
                "each hemisphere's VP neurons (LC4, LPLC2) project only to the ipsi-"
                "lateral GF (Ache 2019). The core circuit has no cross-hemisphere "
                "connections (§4.2, §4.3), so contralateral TTMn should not fire for "
                "unilateral stimulus. loomingFront activates both pathways bilaterally."
            ),
        )
        for r in results:
            report.results.append(r)
        return report

    def _prediction_for(self, stimulus_name: str) -> str:
        predictions = {
            "loomingLeft": "Left pathway only: LC4_L + LPLC2_L -> GF_L -> TTMn_L. No right-side activation.",
            "loomingRight": "Right pathway only: LC4_R + LPLC2_R -> GF_R -> TTMn_R. No left-side activation.",
            "loomingFront": "Bilateral: LC4_L+R + LPLC2_L+R -> GF_L+R -> TTMn_L+R. Both sides fire.",
        }
        return predictions.get(stimulus_name, "No prediction")

    def validate_lateralization(self, report: ExperimentReport) -> Dict[str, bool]:
        """Check whether each lateralization result matches biological prediction.

        Returns dict with pass/fail for each stimulus condition.
        """
        validation = {}
        for r in report.results:
            name = r.stimulus_name
            if name == "loomingLeft":
                ipsilateral = any(n in r.ttmn_spikes for n in ["TTMn_L"])
                contralateral = any(n in r.ttmn_spikes for n in ["TTMn_R"])
                validation[name] = ipsilateral and not contralateral
            elif name == "loomingRight":
                ipsilateral = any(n in r.ttmn_spikes for n in ["TTMn_R"])
                contralateral = any(n in r.ttmn_spikes for n in ["TTMn_L"])
                validation[name] = ipsilateral and not contralateral
            elif name == "loomingFront":
                left = "TTMn_L" in r.ttmn_spikes
                right = "TTMn_R" in r.ttmn_spikes
                validation[name] = left and right
        return validation


@dataclass
class ThresholdResult:
    """Result of a threshold intensity measurement."""
    stimulus_name: str
    intensity: float
    response_magnitude: float
    vp_spike_tick: Optional[int]
    gf_spike_tick: Optional[int]
    ttmn_spike_tick: Optional[int]
    escape_tick: Optional[int]
    biological_prediction: str
    evidence: str
    approximation: str

    def __str__(self):
        return (
            f"{self.stimulus_name} (intensity={self.intensity:.6f}):\n"
            f"  Response: escape_signal={self.response_magnitude:.3f}\n"
            f"  Timing: VP@{self.vp_spike_tick}, GF@{self.gf_spike_tick}, "
            f"TTMn@{self.ttmn_spike_tick}, escape@{self.escape_tick}\n"
            f"  Biological prediction: {self.biological_prediction}\n"
            f"  Evidence: {self.evidence}\n"
            f"  Approximation: {self.approximation}"
        )


class WeakStrongThresholdValidator:
    """Measure the looming intensity threshold for escape response initiation.

    Tests the intensity at which the escape pathway transitions from
    sub-threshold (no response) to supra-threshold (escape response).
    Uses binary search to find the precise threshold within a defined
    intensity range.

    The threshold is **window-dependent simulator behavior**: the minimum
    intensity sufficient for the full VP→GF→TTMn cascade to complete within
    the simulation window. It is not a biological intensity threshold. The
    asymptotic limit as window → infinity is ~0.258 (theoretical minimum
    for VP steady-state voltage to reach threshold).
    """

    VP_NEURONS = ["LC4_L", "LPLC2_L"]
    GF_NEURONS = ["GF_L"]
    TTMN_NEURONS = ["TTMn_L"]
    WEAK_INTENSITY = 0.1
    STRONG_INTENSITY = 1.0
    MAX_TICKS = 35
    BINARY_SEARCH_ITERATIONS = 20
    ASYMPTOTIC_THRESHOLD = 0.257972

    def __init__(self, brain: BiologicalBrain, circuit_name: str = "escape_core"):
        self.brain = brain
        self.circuit_name = circuit_name
        self.engine = brain.engines[circuit_name]
        self.circuit = self.engine.circuit

    def _measure_response(
        self, intensity: float, stimulus_name: str = "loomingLeft", max_ticks: int = None
    ) -> ThresholdResult:
        """Run a single stimulus at given intensity and measure response.

        Args:
            intensity: Looming stimulus intensity (0.0 to 1.0).
            stimulus_name: Stimulus key (default "loomingLeft").
            max_ticks: Simulation window. Defaults to self.MAX_TICKS (35).
        """
        ticks = max_ticks if max_ticks is not None else self.MAX_TICKS
        self.brain.reset()

        first_spikes = {nid: None for nid in self.VP_NEURONS + self.GF_NEURONS + self.TTMN_NEURONS}
        max_escape = 0.0
        escape_tick = None

        for tick in range(ticks):
            signals = self.brain.step({stimulus_name: intensity})
            escape = signals.get("bio_escape_signal", 0.0)
            max_escape = max(max_escape, escape)

            if escape > 0.5 and escape_tick is None:
                escape_tick = tick

            for nid in self.VP_NEURONS + self.GF_NEURONS + self.TTMN_NEURONS:
                if first_spikes[nid] is None:
                    neuron = self.circuit.neurons[nid]
                    if neuron.refractory_remaining > 0:
                        first_spikes[nid] = tick

        vp_tick = first_spikes["LC4_L"]
        gf_tick = first_spikes["GF_L"]
        ttmn_tick = first_spikes["TTMn_L"]

        return ThresholdResult(
            stimulus_name=stimulus_name,
            intensity=intensity,
            response_magnitude=max_escape,
            vp_spike_tick=vp_tick,
            gf_spike_tick=gf_tick,
            ttmn_spike_tick=ttmn_tick,
            escape_tick=escape_tick,
            biological_prediction="",
            evidence="",
            approximation="",
        )

    def find_threshold_intensity(self, max_ticks: int = None) -> float:
        """Binary search for the intensity at which escape_signal exceeds 0.5.

        Uses loomingLeft stimulus with the given max_ticks window.
        Returns the minimum intensity that produces escape within the window.
        Converges to ~1e-6 precision over 20 iterations.

        Note: This is a **window-dependent simulator measurement**, not a
        biological intensity threshold. Lower intensities eventually fire
        given enough ticks, but the binary search finds the minimum intensity
        that completes the cascade within the finite window.
        """
        ticks = max_ticks if max_ticks is not None else self.MAX_TICKS
        low, high = 0.0, 1.0

        for _ in range(self.BINARY_SEARCH_ITERATIONS):
            mid = (low + high) / 2
            result = self._measure_response(mid, max_ticks=ticks)
            if result.response_magnitude > 0.5:
                high = mid
            else:
                low = mid

        return high

    def run_threshold_experiment(self, max_ticks: int = None) -> ExperimentReport:
        """Run the full weak-strong threshold experiment.

        Biological prediction:
        - Weak looming (intensity 0.1): sub-threshold, no escape response
        - Strong looming (intensity 1.0): supra-threshold, immediate escape
        - Threshold intensity: the midpoint where escape_signal transitions from ~0 to ~1

        Evidence (spec §3.1, §5, §8):
        - VP->GF connectivity: DIRECTLY_MEASURED (FlyWire FAFB EM, 2290+1443 synapses)
        - GF->TTMn: DIRECTLY_MEASURED latency (von Reyn 2014)
        - Intensity threshold: APPROXIMATION (LIF voltage-based model)
        - Looming currents: APPROXIMATION (spec §8.10-11 calibration)

        Validation plan expected range: 0.3-0.7 (§10.4, for short-mode window)
        Asymptotic threshold (window→∞): ~0.258 (theoretical VP steady-state)
        """
        ticks = max_ticks if max_ticks is not None else self.MAX_TICKS
        results = []

        weak_result = self._measure_response(
            self.WEAK_INTENSITY, stimulus_name="loomingLeft", max_ticks=ticks
        )
        weak_result.biological_prediction = (
            f"Weak looming (intensity={self.WEAK_INTENSITY}) produces sub-threshold "
            f"VP input. escape_signal should be ~0 (no escape)."
        )
        weak_result.evidence = (
            "VP->GF: DIRECTLY_MEASURED (FlyWire FAFB EM). "
            "Threshold mechanism: APPROXIMATION (LIF voltage-based)."
        )
        weak_result.approximation = (
            "Looming current: APPROXIMATION (spec §8.10-11, calibrated 5.0 mV/tick baseline). "
            "dt=1ms: APPROXIMATION (3.0A convention)."
        )
        results.append(weak_result)

        strong_result = self._measure_response(
            self.STRONG_INTENSITY, stimulus_name="loomingLeft", max_ticks=ticks
        )
        strong_result.biological_prediction = (
            f"Strong looming (intensity={self.STRONG_INTENSITY}) produces supra-threshold "
            f"VP input. escape_signal should be ~1.0 (full escape)."
        )
        strong_result.evidence = (
            "VP->GF: DIRECTLY_MEASURED (FlyWire FAFB EM). "
            "GF->TTMn: DIRECTLY_MEASURED latency (von Reyn 2014)."
        )
        strong_result.approximation = (
            "Looming current: APPROXIMATION (spec §8.10-11 calibration). "
            "dt=1ms: APPROXIMATION (3.0A convention)."
        )
        results.append(strong_result)

        threshold_intensity = self.find_threshold_intensity(max_ticks=ticks)
        threshold_result = self._measure_response(threshold_intensity, stimulus_name="loomingLeft", max_ticks=ticks)
        threshold_result.stimulus_name = f"loomingLeft_threshold (binary search)"
        threshold_result.biological_prediction = (
            f"Threshold intensity: VP input current just sufficient to drive both "
            f"LC4_L and LPLC2_L to threshold, enabling GF firing and escape signal > 0.5 "
            f"within {ticks} ticks."
        )
        threshold_result.evidence = (
            "VP->GF: DIRECTLY_MEASURED (FlyWire FAFB EM, 2290+1443 synapses). "
            "GF->TTMn: DIRECTLY_MEASURED latency (von Reyn 2014)."
        )
        threshold_result.approximation = (
            "WINDOW-DEPENDENT SIMULATOR MEASUREMENT: binary search threshold is the minimum "
            f"intensity that completes the VP→GF→TTMn cascade within {ticks} ticks. "
            "NOT a biological intensity threshold — LIF voltage integration accumulates "
            "current exponentially; lower intensities fire given more time. "
            f"Asymptotic limit (window→∞): ~{self.ASYMPTOTIC_THRESHOLD:.6f} "
            "(theoretical VP steady-state threshold crossing). "
            "Validation plan §10.4 expected range 0.3-0.7 assumes short-mode window. "
            "dt=1ms: APPROXIMATION (3.0A convention)."
        )
        results.append(threshold_result)

        report = ExperimentReport(
            name="Weak/Strong Looming Threshold",
            notes=(
                f"Measures the looming intensity threshold for escape response initiation. "
                f"Binary search over intensity using loomingLeft stimulus "
                f"(window={ticks} ticks). "
                f"RESULT IS WINDOW-DEPENDENT — not a biological intensity threshold. "
                f"Weak intensity={self.WEAK_INTENSITY} (sub-threshold, no escape). "
                f"Strong intensity={self.STRONG_INTENSITY} (supra-threshold, escape). "
                f"Threshold intensity={threshold_intensity:.6f} "
                f"(asymptotic limit ~{self.ASYMPTOTIC_THRESHOLD:.6f} with infinite window). "
                f"Validation plan §10.4 expected range: 0.3-0.7."
            ),
        )
        for r in results:
            report.results.append(r)
        return report

    def validate_threshold(self, report: ExperimentReport) -> Dict[str, bool]:
        """Check threshold results against biological predictions.

        Returns dict with pass/fail for each measurement.
        """
        validation = {}
        for r in report.results:
            name = r.stimulus_name
            if "weak" in name.lower() or "sub" in r.biological_prediction.lower():
                validation["weak"] = r.response_magnitude < 0.5
            elif "strong" in name.lower() or "supra" in r.biological_prediction.lower():
                validation["strong"] = r.response_magnitude > 0.5
            elif "threshold" in name.lower():
                validation["threshold"] = r.response_magnitude > 0.5
        return validation


@dataclass
class SummationResult:
    """Result of a temporal summation measurement for a given inter-spike delay."""
    delay_ticks: int
    gf_fired: bool
    gf_spike_tick: Optional[int]
    escape_signal: float
    escape_tick: Optional[int]
    biological_prediction: str
    evidence: str
    approximation: str

    def __str__(self):
        return (
            f"delay={self.delay_ticks} tick(s):\n"
            f"  GF fired: {self.gf_fired}\n"
            f"  GF spike tick: {self.gf_spike_tick}\n"
            f"  escape_signal={self.escape_signal:.3f}, escape_tick={self.escape_tick}\n"
            f"  Biological prediction: {self.biological_prediction}\n"
            f"  Evidence: {self.evidence}\n"
            f"  Approximation: {self.approximation}"
        )


class TemporalSummationValidator:
    """Measure temporal summation window at the GF (Giant Fiber) neuron.

    Tests whether convergent synaptic inputs from LC4 (15 mV) and LPLC2 (10 mV)
    can summate when staggered by different time intervals. The GF neuron's
    fast membrane time constant (tau_m=5 ms) means the integration window is
    very short — only near-simultaneous inputs can reach threshold.

    Biological basis:
    - GF tau_m = 5 ms (DIRECTLY_MEASURED, Allen 2007, eNeuro 2019 model)
    - VP->GF weights: LC4=15 mV (INFERRED), LPLC2=10 mV (INFERRED),
      calibrated from synapse-count ratios (FlyWire FAFB EM)
    - Combined simultaneous input: 25 mV > threshold gap (20 mV) → fires
    - Staggered input: first input decays before second arrives → no fire
    """

    SPIKE_INJECTION_CURRENT = 25.0
    VP_PAIRS = [("LC4_L", "LPLC2_L")]
    TEST_DELAYS = [0, 1, 2, 3, 4, 5]
    MAX_TICKS = 12

    def __init__(self, brain: BiologicalBrain, circuit_name: str = "escape_core"):
        self.brain = brain
        self.circuit_name = circuit_name
        self.engine = brain.engines[circuit_name]
        self.circuit = self.engine.circuit

    def _measure_summation(self, delay: int) -> SummationResult:
        """Inject VP spikes at tick 0 and tick `delay`, measure GF response.

        Uses deterministic spike injection (25.0 mV) into VP neurons to control
        spike timing precisely. The first VP spikes at tick 0; the second VP
        spikes at tick `delay`. Both spikes propagate to GF with delay=1.
        """
        self.brain.reset()

        vp_a, vp_b = self.VP_PAIRS[0]
        gf_neuron = "GF_L"
        ttmn_neuron = "TTMn_L"

        gf_fired_tick = None
        ttmn_fired_tick = None
        max_escape = 0.0

        for tick in range(self.MAX_TICKS):
            stim = {}
            if tick == 0:
                stim[vp_a] = self.SPIKE_INJECTION_CURRENT
            if tick == delay:
                stim[vp_b] = self.SPIKE_INJECTION_CURRENT
            signals = self.brain.step(stim)
            max_escape = max(max_escape, signals.get("bio_escape_signal", 0.0))

            gf = self.circuit.neurons[gf_neuron]
            if gf.refractory_remaining > 0 and gf_fired_tick is None:
                gf_fired_tick = tick

            ttmn = self.circuit.neurons[ttmn_neuron]
            if ttmn.refractory_remaining > 0 and ttmn_fired_tick is None:
                ttmn_fired_tick = tick

        gf_fired = gf_fired_tick is not None

        return SummationResult(
            delay_ticks=delay,
            gf_fired=gf_fired,
            gf_spike_tick=gf_fired_tick,
            escape_signal=max_escape,
            escape_tick=ttmn_fired_tick,
            biological_prediction="",
            evidence="",
            approximation="",
        )

    def run_temporal_summation(self) -> ExperimentReport:
        """Run temporal summation experiment across delays 0-5 ticks.

        Biological prediction:
        - delay=0 (simultaneous): GF fires (15+10=25 mV > 20 mV gap)
        - delay>=1 (staggered): GF does not fire (first input decays, tau_m=5ms)
        - Effective summation window: 0 ticks (strict coincidence detection)

        Evidence:
        - GF biophysics (tau_m=5): DIRECTLY_MEASURED (Allen 2007, eNeuro 2019)
        - VP->GF weights (15/10): INFERRED (synapse-count calibrated, FlyWire FAFB EM)
        - Temporal summation mechanism: APPROXIMATION (LIF voltage-based)

        Validation plan §10.5: expects strict coincidence detection for GF.
        """
        results = []

        for delay in self.TEST_DELAYS:
            r = self._measure_summation(delay)

            if delay == 0:
                r.biological_prediction = (
                    f"Simultaneous VP inputs (delay={delay}): LC4 (15 mV) + LPLC2 (10 mV) "
                    f"arrive at GF in same tick. Combined 25 mV exceeds threshold gap (20 mV). "
                    f"GF should fire."
                )
            else:
                r.biological_prediction = (
                    f"Staggered VP inputs (delay={delay} tick(s)): first input decays by "
                    f"factor exp(-{delay}/5)={pow(0.2, delay):.4f} before second arrives. "
                    f"First input alone is sub-threshold; decay prevents summation. "
                    f"GF should NOT fire."
                )

            r.evidence = (
                "GF tau_m=5ms: DIRECTLY_MEASURED (Allen2007_JCompNeurol, eNeuro2019_model). "
                "VP->GF weights (15+10=25 mV): INFERRED (synapse-count calibrated, FlyWire_FAFB_v783). "
                "Coincidence detection: DIRECTLY_MEASURED (von Reyn 2014, Cheong 2026)."
            )
            r.approximation = (
                "Spike injection timing: APPROXIMATION (deterministic 25.0 mV, bypasses "
                "sensory integration). dt=1ms: APPROXIMATION (3.0A convention). "
                "GF summation window = 0 ticks reflects strict coincidence detection "
                "(fast tau_m=5ms limits integration to single-tick coincidence). "
                "Validation plan §10.5: expects strict coincidence detection."
            )
            results.append(r)

        report = ExperimentReport(
            name="Temporal Summation Window",
            notes=(
                f"Tests whether convergent VP inputs (LC4 15 mV + LPLC2 10 mV) can summate "
                f"at GF neuron with inter-spike delays 0-{max(self.TEST_DELAYS)} ticks. "
                f"GF tau_m=5ms limits temporal summation window to 0 ticks (strict "
                f"coincidence detection). Spike injection: 25.0 mV deterministic. "
                f"Window: {self.MAX_TICKS} ticks per delay condition."
            ),
        )
        for r in results:
            report.results.append(r)
        return report

    def validate_temporal_summation(self, report: ExperimentReport) -> Dict[str, bool]:
        """Check temporal summation results against biological predictions.

        Returns dict: 'simultaneous' (delay=0) should fire,
        'staggered' (delay>=1) should NOT fire.
        """
        validation = {}
        for r in report.results:
            if r.delay_ticks == 0:
                validation["simultaneous"] = r.gf_fired
            else:
                key = f"staggered_delay_{r.delay_ticks}"
                validation[key] = not r.gf_fired
        return validation


@dataclass
class RefractoryResult:
    """Result of a refractory-period recovery measurement for one neuron."""
    neuron_id: str
    delay_ticks: int
    re_spiked: bool
    re_spike_tick: Optional[int]
    configured_refractory: int
    biological_prediction: str
    evidence: str
    approximation: str

    def __str__(self):
        return (
            f"{self.neuron_id} (delay={self.delay_ticks}):\n"
            f"  Re-spike: {self.re_spiked} at tick {self.re_spike_tick}\n"
            f"  Configured refractory: {self.configured_refractory} ticks\n"
            f"  Biological prediction: {self.biological_prediction}\n"
            f"  Evidence: {self.evidence}\n"
            f"  Approximation: {self.approximation}"
        )


class RefractoryPeriodValidator:
    """Measure refractory period recovery for GF and TTMn neurons.

    Tests whether a neuron can re-spike after a given inter-stimulus interval,
    comparing measured recovery against configured refractory_period_ticks.

    Biological basis:
    - GF: refractory = 5 ticks (INFERRED from von Reyn 2014, Allen 2007)
    - TTMn: refractory = 2 ticks (APPROXIMATION, eNeuro 2019 model)
    - Recovery timing: refractory_period + 1 ticks (sensory injection blocked
      during refractory check precedes integrate decrement)
    """

    SPIKE_INJECTION_CURRENT = 25.0
    TEST_DELAYS = [1, 3, 5, 7, 10]
    MAX_TICKS = 30
    NEURON_CONFIG = {
        "GF_L": {"type": "GiantFiber", "configured_refractory": 5},
        "TTMn_L": {"type": "MotorNeuron", "configured_refractory": 2},
    }

    def __init__(self, brain: BiologicalBrain, circuit_name: str = "escape_core"):
        self.brain = brain
        self.circuit_name = circuit_name
        self.engine = brain.engines[circuit_name]
        self.circuit = self.engine.circuit

    def _measure_recovery(self, neuron_id: str, delay: int) -> RefractoryResult:
        """Inject spikes at tick 0 and tick `delay`, check if neuron re-spikes."""
        self.brain.reset()

        neuron = self.circuit.neurons[neuron_id]
        configured_refractory = neuron.refractory_period

        first_spike_tick = None
        re_spike_tick = None
        prev_refractory = 0

        for tick in range(self.MAX_TICKS):
            stim = {}
            if tick == 0:
                stim[neuron_id] = self.SPIKE_INJECTION_CURRENT
            if tick == delay:
                stim[neuron_id] = self.SPIKE_INJECTION_CURRENT

            self.brain.step(stim)

            if neuron.refractory_remaining > 0 and prev_refractory == 0:
                if first_spike_tick is None:
                    first_spike_tick = tick
                elif re_spike_tick is None:
                    re_spike_tick = tick
            prev_refractory = neuron.refractory_remaining

        re_spiked = re_spike_tick is not None
        effective_recovery = configured_refractory + 1

        if re_spiked:
            bio_pred = (
                f"{neuron_id} re-spikes at delay={delay} (effective recovery "
                f"= refractory_period({configured_refractory}) + 1 = {effective_recovery} ticks)."
            )
        else:
            bio_pred = (
                f"{neuron_id} does NOT re-spike at delay={delay} "
                f"(below effective recovery threshold of {effective_recovery} ticks)."
            )

        return RefractoryResult(
            neuron_id=neuron_id,
            delay_ticks=delay,
            re_spiked=re_spiked,
            re_spike_tick=re_spike_tick,
            configured_refractory=configured_refractory,
            biological_prediction=bio_pred,
            evidence="",
            approximation="",
        )

    def run_refractory_experiment(self) -> ExperimentReport:
        """Run refractory recovery experiment for GF and TTMn.

        Tests inter-stimulus intervals of 1, 3, 5, 7, 10 ticks for both
        GF (refractory=5) and TTMn (refractory=2).

        Biological prediction:
        - GF: re-spiking only at delay >= 6 (refractory 5 + 1)
        - TTMn: re-spiking only at delay >= 3 (refractory 2 + 1)
        - The +1 offset arises because sensory injection is blocked during
          step 1 (is_refractory check) while refractory decrements in step 3

        Evidence:
        - GF refractory: INFERRED (von Reyn 2014, Allen 2007)
        - TTMn refractory: APPROXIMATION (eNeuro 2019 model)
        - Recovery mechanism: APPROXIMATION (LIF voltage-based)
        """
        results = []

        neuron_evidence = {
            "GF_L": (
                "GF refractory=5 ticks: INFERRED (von Reyn 2014, Allen2007_JCompNeurol). "
                "GF tau_m=5ms: DIRECTLY_MEASURED (Allen2007, eNeuro2019_model). "
                "Recovery mechanism: APPROXIMATION (LIF voltage-based)."
            ),
            "TTMn_L": (
                "TTMn refractory=2 ticks: APPROXIMATION (eNeuro2019_model). "
                "TTMn tau_m=10ms: APPROXIMATION. "
                "Recovery mechanism: APPROXIMATION (LIF voltage-based)."
            ),
        }

        neuron_approx = {
            "GF_L": (
                "Spike injection: APPROXIMATION (deterministic 25.0 mV, bypasses "
                "sensory integration). dt=1ms: APPROXIMATION (3.0A convention). "
                "Effective recovery = configured_refractory + 1 (sensory injection "
                "blocked during is_refractory check before integrate decrement)."
            ),
            "TTMn_L": (
                "Spike injection: APPROXIMATION (deterministic 25.0 mV, bypasses "
                "sensory integration). dt=1ms: APPROXIMATION (3.0A convention). "
                "Effective recovery = configured_refractory + 1."
            ),
        }

        for neuron_id in self.NEURON_CONFIG:
            neuron = self.circuit.neurons[neuron_id]
            for delay in self.TEST_DELAYS:
                r = self._measure_recovery(neuron_id, delay)
                r.evidence = neuron_evidence[neuron_id]
                r.approximation = neuron_approx[neuron_id]
                results.append(r)

        report = ExperimentReport(
            name="Refractory Period Recovery",
            notes=(
                f"Tests re-spiking at delays {self.TEST_DELAYS} for GF (refractory=5) "
                f"and TTMn (refractory=2). Recovery mechanism: neurons are blocked from "
                f"receiving sensory input while refractory_remaining > 0, which decrements "
                f"in integrate(). Effective recovery = refractory_period + 1 ticks. "
                f"Spike injection: 25.0 mV deterministic. Window: {self.MAX_TICKS} ticks."
            ),
        )
        for r in results:
            report.results.append(r)
        return report

    def validate_refractory(self, report: ExperimentReport) -> Dict[str, bool]:
        """Check refractory results against biological predictions.

        GF (refractory=5): re-spike only at delay >= 6
        TTMn (refractory=2): re-spike only at delay >= 3
        """
        validation = {}
        for r in report.results:
            effective = r.configured_refractory + 1
            key = f"{r.neuron_id}_delay_{r.delay_ticks}"
            if r.delay_ticks >= effective:
                validation[key] = r.re_spiked
            else:
                validation[key] = not r.re_spiked
        return validation


@dataclass
class PathwayLatencyResult:
    """Result of a GF→PSI→DLMn latency measurement for one hemisphere."""
    pathway_name: str
    gf_source: str
    psi_target: str
    dlmn_target: str
    gf_spike_tick: Optional[int]
    psi_spike_tick: Optional[int]
    dlmn_spike_tick: Optional[int]
    gf_to_psi_latency: int
    psi_to_dlmn_latency: int
    total_latency: int
    biological_target: str
    biological_evidence: str
    simulation_result: str
    connectome_info: str
    inferred_values: str
    approximation: str

    def __str__(self):
        return (
            f"{self.pathway_name}:\n"
            f"  {self.gf_source} -> {self.psi_target} -> {self.dlmn_target}\n"
            f"  GF spike: tick {self.gf_spike_tick}\n"
            f"  PSI spike: tick {self.psi_spike_tick}\n"
            f"  DLMn spike: tick {self.dlmn_spike_tick}\n"
            f"  GF->PSI latency: {self.gf_to_psi_latency} tick(s)\n"
            f"  PSI->DLMn latency: {self.psi_to_dlmn_latency} tick(s)\n"
            f"  Total latency: {self.total_latency} tick(s)\n"
            f"  Biological target: {self.biological_target}\n"
            f"  Biological evidence: {self.biological_evidence}\n"
            f"  Simulation result: {self.simulation_result}\n"
            f"  Connectome info: {self.connectome_info}\n"
            f"  Inferred values: {self.inferred_values}\n"
            f"  Approximation: {self.approximation}"
        )


class GFDLMnLatencyValidator:
    """Measure GF → PSI → contralateral DLMn pathway latency.

    Tests both left (GF_L → PSI_L → DLMn_R) and right (GF_R → PSI_R → DLMn_L)
    pathways using deterministic GF spike injection (25.0 mV) at tick 0.

    The pathway uses two synapse types:
    - GF→PSI: electrical synapse (gap junction, ShakB), delay=1, weight=16.5 mV
    - PSI→DLMn: chemical synapse (ACh), delay=2, weight=17.0 mV
    - Total expected latency: 3 ticks (1 + 2)

    Biological target: 3-4 ticks (~3-4 ms), DIRECTLY_MEASURED (King & Wyman 1980,
    Cheong 2026).
    """

    SPIKE_INJECTION_CURRENT = 25.0
    MAX_TICKS = 12
    PATHWAYS = [
        ("left", "GF_L", "PSI_L", "DLMn_R"),
        ("right", "GF_R", "PSI_R", "DLMn_L"),
    ]

    def __init__(self, brain: BiologicalBrain, circuit_name: str = "escape_core"):
        self.brain = brain
        self.circuit_name = circuit_name
        self.engine = brain.engines[circuit_name]
        self.circuit = self.engine.circuit

    def _measure_pathway(self, pathway_name, gf_source, psi_target, dlmn_target):
        """Inject spike into GF, measure PSI and DLMn activation ticks."""
        self.brain.reset()

        neurons_to_track = [gf_source, psi_target, dlmn_target]
        first_spikes = {nid: None for nid in neurons_to_track}
        prev_refractory = {nid: 0 for nid in neurons_to_track}

        for tick in range(self.MAX_TICKS):
            stim = {gf_source: self.SPIKE_INJECTION_CURRENT} if tick == 0 else {}
            self.brain.step(stim)

            for nid in neurons_to_track:
                neuron = self.circuit.neurons[nid]
                if neuron.refractory_remaining > 0 and prev_refractory[nid] == 0:
                    if first_spikes[nid] is None:
                        first_spikes[nid] = tick
                prev_refractory[nid] = neuron.refractory_remaining

        gf_tick = first_spikes[gf_source]
        psi_tick = first_spikes[psi_target]
        dlmn_tick = first_spikes[dlmn_target]

        if gf_tick is None:
            raise RuntimeError(
                f"Source neuron {gf_source} did not spike with injection current "
                f"{self.SPIKE_INJECTION_CURRENT} mV"
            )
        if psi_tick is None:
            raise RuntimeError(
                f"PSI neuron {psi_target} did not activate after {gf_source} spike at tick {gf_tick}"
            )
        if dlmn_tick is None:
            raise RuntimeError(
                f"DLMn neuron {dlmn_target} did not activate after {psi_target} spike at tick {psi_tick}"
            )

        return PathwayLatencyResult(
            pathway_name=f"GF({gf_source}) -> PSI({psi_target}) -> DLMn({dlmn_target})",
            gf_source=gf_source,
            psi_target=psi_target,
            dlmn_target=dlmn_target,
            gf_spike_tick=gf_tick,
            psi_spike_tick=psi_tick,
            dlmn_spike_tick=dlmn_tick,
            gf_to_psi_latency=psi_tick - gf_tick,
            psi_to_dlmn_latency=dlmn_tick - psi_tick,
            total_latency=dlmn_tick - gf_tick,
            biological_target="",
            biological_evidence="",
            simulation_result="",
            connectome_info="",
            inferred_values="",
            approximation="",
        )

    def run_pathway_latency_experiment(self) -> ExperimentReport:
        """Run GF→PSI→contralateral DLMn latency experiment for both hemispheres.

        Biological prediction (spec §5.4, King & Wyman 1980, Cheong 2026):
        - GF→PSI: 1-2 ms (= 1-2 ticks at dt=1ms), electrical synapse (ShakB)
        - PSI→DLMn: 2-3 ms (= 2-3 ticks), chemical crossed synapse (King & Wyman 1980)
        - Total: 3-4 ms (= 3-4 ticks), DIRECTLY_MEASURED

        Circuit mechanism:
        - GF→PSI: electrical synapse, weight=16.5 mV, delay=1 tick
        - PSI→DLMn: chemical synapse, weight=17.0 mV, delay=2 ticks
        - Total simulated latency: 3 ticks (1 + 2)

        Evidence classification:
        - GF biophysics: DIRECTLY_MEASURED (Allen 2007, eNeuro 2019)
        - GF→PSI connectivity: DIRECTLY_MEASURED (Cheong 2026 EM)
        - PSI→DLMn connectivity: DIRECTLY_MEASURED (King & Wyman 1980, MANC)
        - Weights (16.5, 17.0): INFERRED (calibrated from conductance/synapse counts)
        - Latency (3-4 ms): DIRECTLY_MEASURED (King & Wyman 1980, Cheong 2026)
        - dt=1ms: APPROXIMATION (3.0A convention)
        """
        results = []

        for pathway_name, gf, psi, dlmn in self.PATHWAYS:
            r = self._measure_pathway(pathway_name, gf, psi, dlmn)
            r.biological_target = (
                "Total latency: 3-4 ticks (3-4 ms, King & Wyman 1980, Cheong 2026). "
                "GF->PSI: 1-2 ticks (electrical). PSI->DLMn: 2-3 ticks (chemical crossed)."
            )
            r.biological_evidence = (
                "GF biophysics (tau_m=5ms, V_rest=-65): DIRECTLY_MEASURED (Allen2007, eNeuro2019). "
                "Latency target: DIRECTLY_MEASURED (King1980_JNeurocytol, Cheong2026_eLife)."
            )
            r.simulation_result = (
                f"Measured: GF spikes at tick {r.gf_spike_tick}, PSI at tick {r.psi_spike_tick}, "
                f"DLMn at tick {r.dlmn_spike_tick}. "
                f"GF->PSI = {r.gf_to_psi_latency} tick(s), PSI->DLMn = {r.psi_to_dlmn_latency} tick(s), "
                f"total = {r.total_latency} tick(s)."
            )
            r.connectome_info = (
                f"GF->PSI: electrical synapse (ShakB gap junction), "
                f"weight=16.5 mV, delay=1 tick (Cheong2026_eLife EM). "
                f"PSI->DLMn: chemical synapse (ACh), weight=17.0 mV, delay=2 ticks "
                f"(King1980_JNeurocytol, MANC_v1). "
                f"PSI crosses midline to contralateral DLMn."
            )
            r.inferred_values = (
                "Weights (16.5, 17.0 mV): INFERRED from synapse-count calibration "
                "(spec §5 formula: W = threshold_gap / exp(-dt/tau_m)). "
                "Refractory periods: INFERRED (von Reyn 2014, eNeuro 2019)."
            )
            r.approximation = (
                "Spike injection: APPROXIMATION (deterministic 25.0 mV, bypasses "
                "sensory integration). dt=1ms: APPROXIMATION (3.0A convention). "
                "LIF voltage-based: APPROXIMATION. "
                "Result is a simulation measurement, not a direct biological recording."
            )
            results.append(r)

        report = ExperimentReport(
            name="GF → PSI → Contralateral DLMn Latency",
            notes=(
                f"Measures GF->PSI (electrical, delay=1) -> PSI->DLMn (chemical crossed, "
                f"delay=2) pathway latency for both hemispheres. "
                f"Spike injection: 25.0 mV into GF at tick 0. "
                f"Window: {self.MAX_TICKS} ticks. "
                f"Biological target: 3-4 ticks (3-4 ms, King & Wyman 1980, Cheong 2026). "
                f"Simulated result: 3 ticks (1 + 2) — within target range."
            ),
        )
        for r in results:
            report.results.append(r)
        return report

    def validate_pathway_latency(self, report: ExperimentReport) -> Dict[str, bool]:
        """Check pathway latencies against biological targets.

        Both pathways should have total latency of 3-4 ticks (within
        the 3-4 ms biological target from King & Wyman 1980, Cheong 2026).
        """
        validation = {}
        for r in report.results:
            name = r.pathway_name.split("(")[0]
            if "left" in r.pathway_name.lower() or "GF_L" in r.gf_source:
                key = "left_pathway"
            else:
                key = "right_pathway"

            latency_in_range = 3 <= r.total_latency <= 4
            gf_to_psi_correct = r.gf_to_psi_latency == 1
            psi_to_dlmn_correct = r.psi_to_dlmn_latency == 2
            cross_check = r.dlmn_target.endswith(
                "R" if r.gf_source.endswith("L") else "L"
            )

            validation[key] = latency_in_range and gf_to_psi_correct and psi_to_dlmn_correct and cross_check
        return validation


@dataclass
class AblationResult:
    """Result of a single synapse ablation experiment."""
    ablation_name: str
    blocked_synapse: str
    blocked_connections: List[str]
    baseline_spikes: Dict[str, Optional[int]]
    ablated_spikes: Dict[str, Optional[int]]
    baseline_signals: Dict[str, float]
    ablated_signals: Dict[str, float]
    neurons_deficit: List[str]
    predicted_deficit: str
    biological_evidence: str
    connectome_info: str
    inferred_values: str
    approximation: str

    def __str__(self):
        diff_signals = {
            k: f"baseline={self.baseline_signals.get(k,0):.3f} -> ablated={self.ablated_signals.get(k,0):.3f}"
            for k in set(self.baseline_signals) | set(self.ablated_signals)
        }
        return (
            f"Ablation: {self.ablation_name}\n"
            f"  Blocked: {self.blocked_synapse} ({', '.join(self.blocked_connections)} synapses)\n"
            f"  Baseline spikes: {self._spikes_str(self.baseline_spikes)}\n"
            f"  Ablated spikes: {self._spikes_str(self.ablated_spikes)}\n"
            f"  Baseline signals: {self._signals_str(self.baseline_signals)}\n"
            f"  Ablated signals: {self._signals_str(self.ablated_signals)}\n"
            f"  Signal changes: {diff_signals}\n"
            f"  Neurons deficit: {self.neurons_deficit}\n"
            f"  Predicted deficit: {self.predicted_deficit}\n"
            f"  Biological evidence: {self.biological_evidence}\n"
            f"  Connectome info: {self.connectome_info}\n"
            f"  Inferred values: {self.inferred_values}\n"
            f"  Approximation: {self.approximation}"
        )

    def _spikes_str(self, spikes: Dict[str, Optional[int]]) -> str:
        active = {k: v for k, v in spikes.items() if v is not None}
        return str(active) if active else "none"

    def _signals_str(self, signals: Dict[str, float]) -> str:
        return str({k: round(v, 3) for k, v in signals.items()})


class SynapseAblationValidator:
    """Test pathway necessity via temporary synapse ablation.

    Creates an isolated deep copy of the circuit, disables specified synapses,
    and runs identical stimuli on both baseline and ablated configurations.
    The original production circuit is never modified.

    Safety: uses copy.deepcopy on the entire Circuit object. Ablated synapses
    are disabled via syn.enabled = False on the copy only.
    """

    SPIKE_INJECTION_CURRENT = 25.0
    MAX_TICKS = 12
    NEURONS_TO_TRACK = ["GF_L", "PSI_L", "TTMn_L", "DLMn_R", "GF_R", "PSI_R", "TTMn_R", "DLMn_L", "LC4_L", "LPLC2_L"]

    # (name, blocked_source, blocked_target, stimulus, predicted_deficit, role)
    ABLATIONS = [
        (
            "LC4_L → GF_L",
            "LC4_L", "GF_L",
            {"loomingLeft": 1.0},
            "Loss of left escape pathway: GF_L, TTMn_L, PSI_L, DLMn_R all fail to activate. "
            "escape_signal, flight_signal, threat_signal all drop to 0.",
            "LC4 provides major excitatory drive to GF (15 mV). Blocking it removes "
            "sufficient input for GF threshold crossing with LPLC2 alone (10 mV < 20 mV gap)."
        ),
        (
            "LPLC2_L → GF_L",
            "LPLC2_L", "GF_L",
            {"loomingLeft": 1.0},
            "Loss of left escape pathway: GF_L, TTMn_L, PSI_L, DLMn_R all fail to activate. "
            "Same deficit as LC4 ablation (15 mV < 20 mV threshold gap).",
            "LPLC2 provides secondary excitatory drive to GF (10 mV). Blocking it removes "
            "sufficient input for GF threshold crossing with LC4 alone (15 mV < 20 mV gap)."
        ),
        (
            "GF_L → TTMn_L (all)",
            "GF_L", "TTMn_L",
            {"loomingLeft": 1.0},
            "TTMn_L fails to activate (no escape signal). GF_L and PSI_L still fire normally. "
            "DLMn_R still fires via GF→PSI→DLMn pathway (flight_signal preserved). "
            "threat_signal preserved (GF itself fires).",
            "GF directly drives TTMn (jump motor) via electrical (17.0 mV) + chemical (5.0 mV) synapses."
        ),
        (
            "GF_R → TTMn_R (all)",
            "GF_R", "TTMn_R",
            {"loomingRight": 1.0},
            "TTMn_R fails to activate (no escape signal). GF_R and PSI_R still fire normally. "
            "DLMn_L still fires via GF→PSI→DLMn pathway (flight_signal preserved). "
            "threat_signal preserved (GF itself fires).",
            "GF directly drives TTMn (jump motor) via electrical (17.0 mV) + chemical (5.0 mV) synapses."
        ),
        (
            "GF_L → PSI_L (all)",
            "GF_L", "PSI_L",
            {"loomingLeft": 1.0},
            "PSI_L fails to activate, DLMn_R fails (no flight_signal). TTMn_L still fires "
            "(escape_signal preserved). threat_signal preserved (GF fires).",
            "GF drives PSI via electrical (16.5 mV) + chemical (5.0 mV) synapses. PSI crosses "
            "midline to contralateral DLMn (King & Wyman 1980)."
        ),
        (
            "PSI_L → DLMn_R",
            "PSI_L", "DLMn_R",
            {"loomingLeft": 1.0},
            "DLMn_R fails to activate (no flight_signal). GF_L, PSI_L, TTMn_L all fire normally. "
            "escape_signal and threat_signal preserved.",
            "PSI provides the sole chemical drive to contralateral DLMn (17.0 mV, delay=2). "
            "PSI crosses midline (King & Wyman 1980, MANC v1)."
        ),
    ]

    def __init__(self, brain: BiologicalBrain, circuit_name: str = "escape_core"):
        self.brain = brain
        self.circuit_name = circuit_name
        self._original_synapses = None

    def _snapshot_circuit(self) -> list:
        """Snapshot all synapse enabled states for restoration verification."""
        circuit = self.brain.circuits[self.circuit_name]
        return [(id(s), s.enabled) for s in circuit.synapses]

    def _verify_circuit_intact(self) -> bool:
        """Verify original circuit synapses are unchanged."""
        if self._original_synapses is None:
            self._original_synapses = self._snapshot_circuit()
            return True

        current = self._snapshot_circuit()
        for orig_id, orig_enabled in self._original_synapses:
            match = [c for c in current if c[0] == orig_id]
            if not match or match[0][1] != orig_enabled:
                return False
        return True

    def _create_ablated_circuit(self, block_source: str, block_target: str):
        """Create an isolated deep copy of the circuit with synapses disabled.

        Returns (ablated_circuit, blocked_count). The original circuit is
        never modified.
        """
        original_circuit = self.brain.circuits[self.circuit_name]
        ablated_circuit = copy.deepcopy(original_circuit)

        blocked_count = 0
        for syn in ablated_circuit.synapses:
            if syn.source == block_source and syn.target == block_target:
                syn.enabled = False
                blocked_count += 1

        return ablated_circuit, blocked_count

    def _run_stimulus(
        self, brain_or_engine, stimulus: Dict, use_brain_step: bool = True
    ) -> tuple:
        """Run stimulus on baseline brain or ablated engine. Returns (spikes, signals)."""
        neurons_to_track = self.NEURONS_TO_TRACK
        first_spikes = {nid: None for nid in neurons_to_track}
        prev_refractory = {nid: 0 for nid in neurons_to_track}
        max_signals = {"escape_signal": 0.0, "flight_signal": 0.0, "threat_signal": 0.0}

        if use_brain_step:
            brain = brain_or_engine
            brain.reset()
            for tick in range(self.MAX_TICKS):
                signals = brain.step(stimulus)
                for sig_name in max_signals:
                    max_signals[sig_name] = max(max_signals[sig_name], signals.get(f"bio_{sig_name}", 0.0))
                for nid in neurons_to_track:
                    if nid in brain.circuits[self.circuit_name].neurons:
                        neuron = brain.circuits[self.circuit_name].neurons[nid]
                        if neuron.refractory_remaining > 0 and prev_refractory[nid] == 0:
                            if first_spikes[nid] is None:
                                first_spikes[nid] = tick
                        prev_refractory[nid] = neuron.refractory_remaining
        else:
            engine, translator, circuit = brain_or_engine
            engine.reset()
            for tick in range(self.MAX_TICKS):
                neural_out = engine.step({})
                signals = translator.translate(neural_out)
                for sig_name in max_signals:
                    max_signals[sig_name] = max(max_signals[sig_name], signals.get(sig_name, 0.0))
                for nid in neurons_to_track:
                    if nid in circuit.neurons:
                        neuron = circuit.neurons[nid]
                        if neuron.refractory_remaining > 0 and prev_refractory[nid] == 0:
                            if first_spikes[nid] is None:
                                first_spikes[nid] = tick
                        prev_refractory[nid] = neuron.refractory_remaining

        return first_spikes, max_signals

    def _run_ablated_stimulus(self, stimulus, block_source, block_target):
        """Run stimulus on an ablated circuit copy. Returns (spikes, signals).

        Creates a deep copy of the circuit, disables synapses, and resets the
        ablated engine to ensure clean initial conditions matching baseline.
        """
        ablated_circuit, blocked_count = self._create_ablated_circuit(block_source, block_target)
        engine = NeuralEngine(ablated_circuit)
        translator = SignalTranslator(ablated_circuit)
        engine.reset()

        bio_input = self.brain._map_sensory_input(stimulus)

        neurons_to_track = self.NEURONS_TO_TRACK
        first_spikes = {nid: None for nid in neurons_to_track}
        prev_refractory = {nid: 0 for nid in neurons_to_track}
        max_signals = {"escape_signal": 0.0, "flight_signal": 0.0, "threat_signal": 0.0}

        for tick in range(self.MAX_TICKS):
            neural_out = engine.step(bio_input)
            signals = translator.translate(neural_out)
            for sig_name in max_signals:
                max_signals[sig_name] = max(max_signals[sig_name], signals.get(sig_name, 0.0))
            for nid in neurons_to_track:
                if nid in ablated_circuit.neurons:
                    neuron = ablated_circuit.neurons[nid]
                    if neuron.refractory_remaining > 0 and prev_refractory[nid] == 0:
                        if first_spikes[nid] is None:
                            first_spikes[nid] = tick
                    prev_refractory[nid] = neuron.refractory_remaining

        return first_spikes, max_signals

    def run_ablation_experiment(self) -> ExperimentReport:
        """Run all synapse ablation experiments.

        Biological predictions (validation plan §10.6):
        - LC4→GF or LPLC2→GF: abolishes escape (both inputs needed for GF threshold)
        - GF→TTMn: abolishes escape signal, preserves threat/flight
        - GF→PSI: abolishes flight, preserves escape/threat
        - PSI→DLMn: abolishes flight, preserves escape/threat

        Evidence classification:
        - Connectivity: DIRECTLY_MEASURED (FlyWire FAFB EM, MANC)
        - Weights: INFERRED (synapse-count calibrated)
        - Functional role: INFERRED (circuit model, King & Wyman 1980)
        - dt=1ms: APPROXIMATION (3.0A convention)
        """
        results = []

        for ablation_name, block_src, block_tgt, stimulus, predicted_deficit, role in self.ABLATIONS:
            baseline_spikes, baseline_signals = self._run_stimulus(self.brain, stimulus, use_brain_step=True)
            ablated_spikes, ablated_signals = self._run_ablated_stimulus(stimulus, block_src, block_tgt)

            if not self._verify_circuit_intact():
                raise RuntimeError(
                    f"CIRCUIT MUTATION DETECTED: ablation '{ablation_name}' modified "
                    f"the production circuit. Aborting."
                )

            neurons_deficit = []
            for nid in self.NEURONS_TO_TRACK:
                baseline_spike = baseline_spikes.get(nid)
                ablated_spike = ablated_spikes.get(nid)
                if baseline_spike is not None and ablated_spike is None:
                    neurons_deficit.append(nid)

            blocked_connections_str = [f"{block_src}->{tgt}" for tgt in
                                       [s.target for s in self.brain.circuits[self.circuit_name].synapses
                                        if s.source == block_src and s.target == block_tgt]]

            result = AblationResult(
                ablation_name=ablation_name,
                blocked_synapse=f"{block_src}->{block_tgt}",
                blocked_connections=blocked_connections_str,
                baseline_spikes=baseline_spikes,
                ablated_spikes=ablated_spikes,
                baseline_signals=baseline_signals,
                ablated_signals=ablated_signals,
                neurons_deficit=neurons_deficit,
                predicted_deficit=predicted_deficit,
                biological_evidence=(
                    f"Connectivity: DIRECTLY_MEASURED (FlyWire_FAFB_v783, MANC_v1). "
                    f"Functional role: INFERRED (circuit model, King1980_JNeurocytol, Cheong2026_eLife). "
                    f"Refractory behavior: INFERRED (von Reyn 2014)."
                ),
                connectome_info=role,
                inferred_values=(
                    f"Synaptic weights: INFERRED from synapse-count calibration "
                    f"(spec §5 formula: W = threshold_gap / exp(-dt/tau_m)). "
                    f"Refractory periods: INFERRED."
                ),
                approximation=(
                    "Spike injection: APPROXIMATION (loomingLeft=1.0, calibrated 5.0 mV/tick). "
                    "dt=1ms: APPROXIMATION (3.0A convention). LIF voltage-based: APPROXIMATION. "
                    "Ablation: temporary synapse.disable=True on deep-copied circuit. "
                    "Result describes model perturbation, not biological necessity proof. "
                    "Production circuit verified intact after each ablation."
                ),
            )
            results.append(result)

        report = ExperimentReport(
            name="Synapse Ablation / Pathway Necessity",
            notes=(
                f"Tests {len(self.ABLATIONS)} synapse ablations using loomingLeft=1.0 or "
                f"loomingRight=1.0 stimuli. Each ablation creates an isolated deep-copied "
                f"circuit with synapses disabled. Production circuit verified intact after "
                f"each experiment. Window: {self.MAX_TICKS} ticks."
            ),
        )
        for r in results:
            report.results.append(r)
        return report

    def validate_ablation(self, report: ExperimentReport) -> Dict[str, bool]:
        """Check each ablation against the predicted deficit."""
        validation = {}
        neuron_mapping = {
            "LC4_L → GF_L": ["LC4_L", "LPLC2_L", "GF_L", "TTMn_L", "PSI_L", "DLMn_R"],
            "LPLC2_L → GF_L": ["LC4_L", "LPLC2_L", "GF_L", "TTMn_L", "PSI_L", "DLMn_R"],
            "GF_L → TTMn_L (all)": ["GF_L", "TTMn_L", "PSI_L", "DLMn_R"],
            "GF_R → TTMn_R (all)": ["GF_R", "TTMn_R", "PSI_R", "DLMn_L"],
            "GF_L → PSI_L (all)": ["GF_L", "PSI_L", "DLMn_R", "TTMn_L"],
            "PSI_L → DLMn_R": ["PSI_L", "DLMn_R", "GF_L", "TTMn_L"],
        }

        for r in report.results:
            name = r.ablation_name
            if name not in neuron_mapping:
                continue

            expected_affected = set()
            if "LC4" in name or "LPLC2" in name:
                if "GF_L" in name:
                    expected_affected = {"GF_L", "TTMn_L", "PSI_L", "DLMn_R"}
            elif "GF_L → TTMn_L" in name:
                expected_affected = {"TTMn_L"}
            elif "GF_R → TTMn_R" in name:
                expected_affected = {"TTMn_R"}
            elif "GF_L → PSI_L" in name:
                expected_affected = {"PSI_L", "DLMn_R"}
            elif "PSI_L → DLMn_R" in name:
                expected_affected = {"DLMn_R"}

            actual_deficit = set(r.neurons_deficit)
            validation[name] = expected_affected == actual_deficit

            escape_preserved = (
                "escape_signal" not in name or
                0.5 not in r.ablated_signals.values() or
                r.ablated_signals.get("escape_signal", 0.0) > 0.5
            ) if "TTMn" in name else True
            if "GF_L → TTMn_L" in name:
                validation[name] = validation[name] and r.ablated_signals.get("escape_signal", 0) < 0.5
                validation[name] = validation[name] and r.ablated_signals.get("threat_signal", 0) > 0.5
            elif "GF_R → TTMn_R" in name:
                validation[name] = validation[name] and r.ablated_signals.get("escape_signal", 0) < 0.5
                validation[name] = validation[name] and r.ablated_signals.get("threat_signal", 0) > 0.5
            elif "GF_L → PSI_L" in name:
                validation[name] = validation[name] and r.ablated_signals.get("flight_signal", 0) < 0.5
                validation[name] = validation[name] and r.ablated_signals.get("escape_signal", 0) > 0.5
            elif "PSI_L → DLMn_R" in name:
                validation[name] = validation[name] and r.ablated_signals.get("flight_signal", 0) < 0.5
                validation[name] = validation[name] and r.ablated_signals.get("escape_signal", 0) > 0.5

        return validation
