"""Neural engine for Biological Brain 3.0 - time-stepping simulation."""

from collections import defaultdict
from typing import Dict, List, Optional
from .circuit import Circuit
from .neuron import Neuron
from .synapse import Synapse
from .dynamics import get_model, DynamicsModel, MODEL_NAME_LIF_VOLTAGE


class NeuralEngine:
    """Discrete-time neural simulation engine.

    Stage A: integration, threshold, spike propagation with delays.
    Uses a pluggable DynamicsModel for neural dynamics computation.
    Default model is 'lif_voltage' which reproduces the original 3.0B
    Stage A LIF behavior exactly.
    """

    def __init__(self, circuit: Circuit, dynamics_model: str = MODEL_NAME_LIF_VOLTAGE):
        self.circuit = circuit
        self.spike_queue: Dict[int, List[tuple]] = defaultdict(list)
        self.current_tick = 0
        self.dynamics_model_name = dynamics_model
        self.dynamics: DynamicsModel = get_model(dynamics_model)
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
        model = self.dynamics

        # 0. Decay conductance state (tick-level exponential decay)
        for neuron in self.circuit.neurons.values():
            model.decay_conductances(neuron)

        # 1. Inject sensory current into input neurons (blocked during refractory)
        for neuron_id, current in sensory_input.items():
            neuron = self.circuit.neurons.get(neuron_id)
            if neuron and not neuron.is_refractory():
                model.inject_sensory_current(neuron, current)

        # 2. Process scheduled spikes from previous ticks
        due_spikes = self.spike_queue.pop(self.current_tick, [])
        for target_id, weight, sign in due_spikes:
            neuron = self.circuit.neurons.get(target_id)
            if neuron:
                model.receive_synaptic_spike(neuron, weight, sign)

        # 3. Compute electrical (gap-junction) currents for conductance model
        self._compute_electrical_currents()

        # 4. Integrate & threshold all neurons
        spiked_neurons = []
        for neuron in self.circuit.neurons.values():
            if model.integrate(neuron, 0.0):
                spiked_neurons.append(neuron.neuron_id)

        # 5. Clear electrical current accumulators (consumed during integrate step 4)
        # This prevents stale current from leaking into the next timestep.
        for neuron in self.circuit.neurons.values():
            if neuron.conductance_state is not None:
                neuron.conductance_state.I_elec_accumulator = 0.0

        # 6. Schedule synaptic propagation for spiked neurons
        for source_id in spiked_neurons:
            self._schedule_propagation(source_id)

        # 7. Read outputs
        outputs = {}
        for out_id in self.circuit.output_neurons:
            neuron = self.circuit.neurons.get(out_id)
            if neuron:
                outputs[out_id] = neuron.membrane_potential

        self.current_tick += 1
        return outputs

    def _schedule_propagation(self, source_id: str) -> None:
        """Schedule spike propagation to target neurons.

        For the conductance_v0 model, electrical synapses are excluded
        from the delay queue — they are handled by
        _compute_electrical_currents() using the gap-junction formula
        I_elec = g_gap * (V_pre - V_post). Only chemical synapses
        contribute to the delay queue in conductance mode.
        """
        for syn in self._synapses_by_source.get(source_id, []):
            if not syn.enabled:
                continue
            if syn.delay < 1:
                raise ValueError(f"Synapse delay must be >= 1, got {syn.delay}")
            if self.dynamics_model_name == "conductance_v0" and syn.synapse_type == "electrical":
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
        model = self.dynamics
        for neuron in self.circuit.neurons.values():
            model.reset(neuron)

    def _compute_electrical_currents(self) -> None:
        """Compute gap-junction currents for electrical (gap-junction) synapses.

        For each directional electrical Synapse, calculates the
        gap-junction current from the presynaptic voltage to the
        postsynaptic neuron, using the formula:

            I_elec = g_gap * (V_pre - V_post)

        where g_gap is the gap-junction conductance in µS (from the
        circuit definition, derived from PMC6469880 Table 1, labeled
        "INFERRED" / "APPROXIMATION" — 135 µS for young flies, explicitly
        estimated, not directly measured).

        The resulting current is accumulated into each postsynaptic
        neuron's conductance state via the dynamics model's
        receive_electrical_current() method.

        IMPORTANT: This is CURRENT CALCULATION ONLY. The computed
        current is NOT yet used to update membrane potential. The
        conductance_v0 integrate() method still raises
        NotImplementedError. This step merely populates the
        I_elec_accumulator in conductance state for future use.

        UNITS: If V is in mV and g_gap is in µS, I_elec is in nA.
        No scaling or conversion is applied — this is an explicit
        approximation due to dt=1ms.

        Each directional electrical Synapse is processed exactly once.
        No conductance doubling, no bidirectional collapsing.
        """
        for syn in self.circuit.synapses:
            if not syn.enabled:
                continue
            if syn.synapse_type != "electrical":
                continue

            source_neuron = self.circuit.neurons.get(syn.source)
            target_neuron = self.circuit.neurons.get(syn.target)
            if source_neuron is None or target_neuron is None:
                continue

            V_pre = source_neuron.membrane_potential
            V_post = target_neuron.membrane_potential
            I_elec = syn.conductance * (V_pre - V_post)

            if target_neuron.conductance_state is not None:
                self.dynamics.receive_electrical_current(target_neuron, I_elec)

    def get_state(self) -> Dict:
        """Get current engine state for inspection."""
        return {
            "tick": self.current_tick,
            "neurons": {
                nid: {
                    "potential": n.membrane_potential,
                    "refractory": n.refractory_remaining,
                    "threshold": n.threshold,
                    "resting_potential": n.resting_potential,
                    "reset_potential": n.reset_potential,
                }
                for nid, n in self.circuit.neurons.items()
            },
            "pending_spikes": sum(len(v) for v in self.spike_queue.values()),
        }