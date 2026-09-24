"""Neuron model for Biological Brain 3.0 - Stage A: Leaky Integrate-and-Fire."""

from dataclasses import dataclass, field
from typing import List, Optional
from .synapse import Synapse


@dataclass
class Neuron:
    """Stage A neuron: membrane integration + threshold -> spike."""
    neuron_id: str
    cell_type: str = "unknown"
    brain_region: str = "unknown"
    neurotransmitter: str = "unknown"
    membrane_potential: float = 0.0
    threshold: float = 1.0
    refractory_remaining: int = 0
    refractory_period: int = 2
    leak: float = 0.1
    incoming: List[Synapse] = field(default_factory=list)

    def integrate(self, input_current: float = 0.0) -> bool:
        """Stage A: membrane integration + threshold -> spike.
        
        Args:
            input_current: External current injected this tick
            
        Returns:
            True if spike emitted, False otherwise
        """
        if self.refractory_remaining > 0:
            self.refractory_remaining -= 1
            return False
        
        self.membrane_potential += input_current
        self.membrane_potential -= self.leak
        self.membrane_potential = max(0.0, self.membrane_potential)
        
        if self.membrane_potential >= self.threshold:
            self.membrane_potential = 0.0
            self.refractory_remaining = self.refractory_period
            return True
        return False

    def receive_spike(self, weight: float, sign: int = 1) -> None:
        """Receive a spike from a presynaptic neuron.
        
        Args:
            weight: Synaptic weight
            sign: +1 for excitatory, -1 for inhibitory
        """
        if self.refractory_remaining == 0:
            self.membrane_potential += weight * sign
            self.membrane_potential = max(0.0, self.membrane_potential)

    def reset(self) -> None:
        """Reset neuron to initial state."""
        self.membrane_potential = 0.0
        self.refractory_remaining = 0

    def is_refractory(self) -> bool:
        """Check if neuron is in refractory period."""
        return self.refractory_remaining > 0