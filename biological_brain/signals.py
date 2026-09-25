"""Signal translation for Biological Brain 3.0."""

from typing import Dict
from .circuit import Circuit
from .neuron import Neuron


class SignalTranslator:
    """Map neural activity to high-level signals the 2.0 system understands."""

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self._output_neurons: Dict[str, Neuron] = {
            nid: circuit.neurons[nid] for nid in circuit.output_neurons if nid in circuit.neurons
        }
        self._all_neurons: Dict[str, Neuron] = dict(circuit.neurons)

    def _normalize_mv(self, neuron: Neuron, membrane_potential: float) -> float:
        """Normalize membrane potential to [0, 1] range.
        
        A neuron in refractory period (recently spiked) returns 1.0.
        resting_potential -> 0.0
        threshold -> 1.0
        Above threshold -> >1.0 (clamped to 1.0)
        Below resting -> <0.0 (clamped to 0.0)
        """
        if neuron.is_refractory():
            return 1.0
        v_range = neuron.threshold - neuron.resting_potential
        if v_range <= 0:
            return 0.0
        normalized = (membrane_potential - neuron.resting_potential) / v_range
        return max(0.0, min(1.0, normalized))

    def translate(self, neural_outputs: Dict[str, float]) -> Dict[str, float]:
        """Translate neural outputs to behavioral signals.
        
        Escape circuit signal mapping (bilateral max):
        - escape_signal: max(TTMn_L, TTMn_R) — tibia motor activation (jump)
        - flight_signal: max(DLMn_L, DLMn_R) — wing downstroke
        - threat_signal: max(GF_L, GF_R) — descending threat level
        
        Returns dict with signal names and normalized values [0, 1].
        """
        output_ids = set(self._output_neurons.keys())
        all_ids = set(self._all_neurons.keys())
        
        escape_neurons = {"TTMn_L", "TTMn_R"} & output_ids
        flight_neurons = {"DLMn_L", "DLMn_R"} & output_ids
        threat_neurons = {"GF_L", "GF_R"} & all_ids
        
        signals = {}
        
        if escape_neurons:
            max_val = max(
                self._normalize_mv(self._output_neurons[nid], neural_outputs.get(nid, 0.0))
                for nid in escape_neurons
            )
            signals["escape_signal"] = max_val
        
        if flight_neurons:
            max_val = max(
                self._normalize_mv(self._output_neurons[nid], neural_outputs.get(nid, 0.0))
                for nid in flight_neurons
            )
            signals["flight_signal"] = max_val
        
        if threat_neurons:
            max_val = max(
                self._normalize_mv(self._all_neurons[nid], neural_outputs.get(nid, 0.0))
                for nid in threat_neurons
            )
            signals["threat_signal"] = max_val
        
        for neuron_id, value in neural_outputs.items():
            neuron = self._output_neurons.get(neuron_id)
            if neuron is None:
                continue
            if neuron_id in escape_neurons or neuron_id in flight_neurons:
                continue
            if neuron_id in threat_neurons:
                continue
            normalized = self._normalize_mv(neuron, value)
            signal_name = neuron_id.lower().replace("_bio", "")
            signals[signal_name] = normalized
        
        return signals

    def translate_raw(self, neural_outputs: Dict[str, float]) -> Dict[str, float]:
        """Return raw membrane potentials without normalization."""
        return dict(neural_outputs)