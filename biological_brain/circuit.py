"""Circuit definition for Biological Brain 3.0."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .neuron import Neuron
from .synapse import Synapse, Sign


@dataclass
class Circuit:
    """Validated biological circuit definition."""
    name: str
    neurons: Dict[str, Neuron] = field(default_factory=dict)
    synapses: List[Synapse] = field(default_factory=list)
    input_neurons: List[str] = field(default_factory=list)
    output_neurons: List[str] = field(default_factory=list)

    def add_neuron(self, neuron: Neuron) -> 'Circuit':
        """Add a neuron to the circuit."""
        self.neurons[neuron.neuron_id] = neuron
        return self

    def add_synapse(self, synapse: Synapse) -> 'Circuit':
        """Add a synapse to the circuit."""
        self.synapses.append(synapse)
        return self

    def connect(self, source_id: str, target_id: str, weight: float = 1.0,
                sign: Sign = Sign.EXCITATORY, delay: int = 1,
                neurotransmitter: str = "unknown") -> 'Circuit':
        """Convenience method to add a connection."""
        synapse = Synapse(
            source=source_id,
            target=target_id,
            weight=weight,
            sign=sign,
            delay=delay,
            neurotransmitter=neurotransmitter
        )
        return self.add_synapse(synapse)

    def get_neuron(self, neuron_id: str) -> Optional[Neuron]:
        """Get a neuron by ID."""
        return self.neurons.get(neuron_id)

    def get_synapse(self, source_id: str, target_id: str) -> Optional[Synapse]:
        """Get a synapse by source and target ID (returns first match)."""
        for syn in self.synapses:
            if syn.source == source_id and syn.target == target_id:
                return syn
        return None

    def get_synapses(self, source_id: str, target_id: str) -> List[Synapse]:
        """Get all synapses between source and target."""
        return [syn for syn in self.synapses if syn.source == source_id and syn.target == target_id]

    def get_inputs(self) -> List[str]:
        """Get input neuron IDs."""
        return self.input_neurons.copy()

    def get_outputs(self) -> List[str]:
        """Get output neuron IDs."""
        return self.output_neurons.copy()

    def validate(self) -> List[str]:
        """Validate circuit structure, return list of warnings."""
        warnings = []
        neuron_ids = set(self.neurons.keys())
        
        for syn in self.synapses:
            if syn.source not in neuron_ids:
                warnings.append(f"Synapse source '{syn.source}' not in circuit")
            if syn.target not in neuron_ids:
                warnings.append(f"Synapse target '{syn.target}' not in circuit")
        
        for inp in self.input_neurons:
            if inp not in neuron_ids:
                warnings.append(f"Input neuron '{inp}' not in circuit")
        
        for out in self.output_neurons:
            if out not in neuron_ids:
                warnings.append(f"Output neuron '{out}' not in circuit")
        
        return warnings