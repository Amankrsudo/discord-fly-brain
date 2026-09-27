"""LIF voltage-based dynamics model.

This model reproduces the exact numerical behavior of the original
3.0B Stage A Leaky Integrate-and-Fire neuron implementation.

It is an APPROXIMATION of biological neural dynamics. The model uses:
- Exponential membrane decay toward V_rest
- Hard threshold crossing for spike generation
- Instantaneous reset to V_reset
- Absolute refractory period (integer ticks)
- Voltage-step synaptic input
- Voltage-step sensory current injection

These are the same dynamics as the original 3.0B implementation
(neuron.py integrate, receive_spike, reset). No changes to numerical
behavior are introduced.
"""

from ..neuron import Neuron
from .base import DynamicsModel, NumericalResolution


class LIFVoltageModel(DynamicsModel):
    """Stage A LIF dynamics: voltage-based integration.

    This is the default model, reproducing the 3.0B behavior exactly.
    """

    numerical_resolution = NumericalResolution(
        timestep_ms=1.0,
        resolution_note=(
            "LIF model has no fast kinetics. dt=1ms is adequate for "
            "exponential decay + threshold crossing. This model does "
            "NOT involve active voltage-gated channels and therefore "
            "does not require sub-ms resolution."
        ),
    )

    @property
    def name(self) -> str:
        return "lif_voltage"

    def inject_sensory_current(self, neuron: Neuron, current: float) -> None:
        """Inject external current into a neuron.

        Matches the original NeuralEngine.step() sensory injection:
        - Blocked if the neuron is refractory (is_refractory check)
        - Adds current to membrane potential
        - Called BEFORE integrate()

        Note: The refractory check is performed by the caller (NeuralEngine)
        or by the neuron's is_refractory() method. This method assumes
        the caller has already verified the neuron is not refractory
        for sensory input.
        """
        neuron.membrane_potential += current

    def receive_synaptic_spike(self, neuron: Neuron, weight: float, sign: int) -> None:
        """Deliver a synaptic spike.

        Matches the original Neuron.receive_spike():
        - Blocked if the neuron is in refractory period
        - Adds weight * sign to membrane potential
        """
        if neuron.refractory_remaining > 0:
            return
        neuron.membrane_potential += weight * sign

    def receive_electrical_current(self, neuron: Neuron, current: float) -> None:
        """No-op for LIF model (electrical coupling handled via spike queue)."""
        pass

    def decay_conductances(self, neuron: Neuron) -> None:
        """No-op for LIF model (no conductance-based state)."""
        pass

    def integrate(self, neuron: Neuron, input_current: float = 0.0) -> bool:
        """Integrate one timestep of membrane potential.

        Matches the original Neuron.integrate() exactly:
        1. If refractory: decrement refractory_remaining, return False
        2. Exponential decay toward V_rest:
           decay_factor = 1.0 - exp(-dt / tau_m)
           V += (V_rest - V) * decay_factor
        3. Add input current: V += input_current
        4. Threshold check: if V >= threshold, reset and return True
        5. Otherwise return False
        """
        if neuron.refractory_remaining > 0:
            neuron.refractory_remaining -= 1
            return False

        decay_factor = 1.0 - pow(2.718281828, -neuron.dt / neuron.tau_m)
        neuron.membrane_potential += (
            neuron.resting_potential - neuron.membrane_potential
        ) * decay_factor

        neuron.membrane_potential += input_current

        if neuron.membrane_potential >= neuron.threshold:
            neuron.membrane_potential = neuron.reset_potential
            neuron.refractory_remaining = neuron.refractory_period
            return True
        return False

    def reset(self, neuron: Neuron) -> None:
        """Reset a neuron to initial state.

        Matches the original Neuron.reset():
        - membrane_potential = resting_potential
        - refractory_remaining = 0
        """
        neuron.membrane_potential = neuron.resting_potential
        neuron.refractory_remaining = 0
