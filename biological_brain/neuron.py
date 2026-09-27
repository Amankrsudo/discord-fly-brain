"""Neuron model for Biological Brain 3.0 - Stage A: Leaky Integrate-and-Fire."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional
from .synapse import Synapse

if TYPE_CHECKING:
    from .dynamics.conductance import ConductanceNeuronState


@dataclass
class Neuron:
    """Stage A neuron: membrane integration + threshold -> spike.
    
    Implements discrete-time Leaky Integrate-and-Fire with:
    - Configurable resting potential (V_rest)
    - Configurable reset potential (V_reset) 
    - Exponential decay toward V_rest
    - Absolute refractory period
    - Hard threshold crossing
    
    The conductance_state field is optional and only used when the
    conductance_v0 dynamics model is selected. It defaults to None,
    preserving all existing LIF behavior.
    """
    neuron_id: str
    cell_type: str = "unknown"
    brain_region: str = "unknown"
    neurotransmitter: str = "unknown"
    membrane_potential: float = -70.0  # mV, will be set to resting_potential in __post_init__
    threshold: float = -55.0  # mV
    resting_potential: float = -70.0  # mV
    reset_potential: float = -75.0  # mV
    refractory_remaining: int = 0
    refractory_period: int = 2  # ticks
    tau_m: float = 20.0  # membrane time constant (ms)
    dt: float = 1.0  # simulation timestep (ms)
    incoming: List[Synapse] = field(default_factory=list)
    conductance_state: Optional[ConductanceNeuronState] = None
    dynamics_model: Optional[str] = None  # per-neuron dynamics backend; None = engine default

    def __post_init__(self):
        """Initialize membrane potential to resting potential."""
        self.membrane_potential = self.resting_potential

    def integrate(self, input_current: float = 0.0) -> bool:
        """Discrete-time LIF integration with exponential decay toward resting potential.
        
        Args:
            input_current: External current injected this tick (mV equivalent)
            
        Returns:
            True if spike emitted, False otherwise
        """
        if self.refractory_remaining > 0:
            self.refractory_remaining -= 1
            return False
        
        # Exponential decay toward resting potential: V += (V_rest - V) * (1 - exp(-dt/tau))
        # Equivalent to: V = V_rest + (V - V_rest) * exp(-dt/tau)
        decay_factor = 1.0 - pow(2.718281828, -self.dt / self.tau_m)
        self.membrane_potential += (self.resting_potential - self.membrane_potential) * decay_factor
        
        # Add input current (excitatory positive, inhibitory negative)
        self.membrane_potential += input_current
        
        # Threshold check
        if self.membrane_potential >= self.threshold:
            self.membrane_potential = self.reset_potential
            self.refractory_remaining = self.refractory_period
            return True
        return False

    def receive_spike(self, weight: float, sign: int = 1) -> None:
        """Receive a spike from a presynaptic neuron.
        
        Args:
            weight: Synaptic weight (mV equivalent)
            sign: +1 for excitatory, -1 for inhibitory
            
        Note: Input is blocked during refractory period.
        """
        if self.refractory_remaining > 0:
            return  # Block synaptic input during refractory
        
        self.membrane_potential += weight * sign

    def reset(self) -> None:
        """Reset neuron to initial state."""
        self.membrane_potential = self.resting_potential
        self.refractory_remaining = 0

    def is_refractory(self) -> bool:
        """Check if neuron is in refractory period."""
        return self.refractory_remaining > 0