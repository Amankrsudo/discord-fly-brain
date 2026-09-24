"""Neural engine for Biological Brain 3.0 - time-stepping simulation."""

from collections import defaultdict
from typing import Dict, List
from .circuit import Circuit
from .neuron import Neuron
from .synapse import Synapse


class NeuralEngine:
    """Discrete-time neural simulation engine.
    
    Stage A: integration, threshold, spike propagation with delays.
    """

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.spike_queue: Dict[int, List[tuple]] = defaultdict(list)
        self.current_tick = 0
        self._build_neuron_index()

    def _build_neuron_index(self) -> None:
        """Build fast lookup for synapses by source."""
        self._synapses_by_source: Dict[str, List[Synapse]] = defaultdict(list)
        for syn in self.circuit.synapses:
            self._synapses_by_source[syn.source].append(syn)

    def step(self, sensory_input: Dict[str, float]) -> Dict[str, float]:
        """Advance simulation by one tick.
        
        Args:
            sensory_input: Mapping of input neuron ID -> injected current
            
        Returns:
            Mapping of output neuron ID -> membrane potential
        """
        # 1. Inject sensory current into input neurons
        for neuron_id, current in sensory_input.items():
            neuron = self.circuit.neurons.get(neuron_id)
            if neuron:
                neuron.membrane_potential += current

        # 2. Process scheduled spikes from previous ticks
        due_spikes = self.spike_queue.pop(self.current_tick, [])
        for target_id, weight, sign in due_spikes:
            neuron = self.circuit.neurons.get(target_id)
            if neuron:
                neuron.receive_spike(weight, sign)

        # 3. Integrate & threshold all neurons
        spiked_neurons = []
        for neuron in self.circuit.neurons.values():
            if neuron.integrate(0.0):
                spiked_neurons.append(neuron.neuron_id)

        # 4. Schedule synaptic propagation for spiked neurons
        for source_id in spiked_neurons:
            self._schedule_propagation(source_id)

        # 5. Read outputs
        outputs = {}
        for out_id in self.circuit.output_neurons:
            neuron = self.circuit.neurons.get(out_id)
            if neuron:
                outputs[out_id] = neuron.membrane_potential

        self.current_tick += 1
        return outputs

    def _schedule_propagation(self, source_id: str) -> None:
        """Schedule spike propagation to target neurons."""
        for syn in self._synapses_by_source.get(source_id, []):
            if not syn.enabled:
                continue
            target_tick = self.current_tick + syn.delay
            effective_weight = syn.effective_weight()
            self.spike_queue[target_tick].append((
                syn.target, effective_weight, syn.sign.value
            ))

    def reset(self) -> None:
        """Reset engine and all neurons to initial state."""
        self.spike_queue.clear()
        self.current_tick = 0
        for neuron in self.circuit.neurons.values():
            neuron.reset()

    def get_state(self) -> Dict:
        """Get current engine state for inspection."""
        return {
            "tick": self.current_tick,
            "neurons": {
                nid: {
                    "potential": n.membrane_potential,
                    "refractory": n.refractory_remaining,
                    "threshold": n.threshold,
                }
                for nid, n in self.circuit.neurons.items()
            },
            "pending_spikes": sum(len(v) for v in self.spike_queue.values()),
        }