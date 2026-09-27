"""Base protocol for neural dynamics models.

A DynamicsModel defines how a single neuron integrates inputs,
detects spikes, and resets after a spike. The protocol is designed
to be minimal so that future models (e.g. conductance-based) can
implement these operations without modifying NeuralEngine.

NUMERICAL RESOLUTION POLICY (3.0D-3)

The engine runs at a fixed dt (currently 1 ms). This is documented
as a model/integration concern, NOT a biological parameter. The
distinction matters:

- Biological timescale: the intrinsic speed of a physiological process
  (e.g. Na activation tau ~ 0.1 ms, chemical synapse rise tau ~ 0.1 ms).
- Simulator timestep: the dt the engine iterates at (currently 1 ms).
- Numerical resolution: whether dt adequately samples the model's
  dynamics (e.g. Forward Euler is conditionally stable; rapid voltage
  transients require smaller dt).
- Model approximation: the degree to which a model simplifies biology
  (e.g. conductance_v0 uses a threshold-crossing spike-event adapter
  instead of active HH channels).

Rules:
1. The current reduced models (lif_voltage, conductance_v0) are
   validated at dt = 1 ms. This is adequate for LIF (no fast kinetics)
   and for conductance_v0 as a passive Forward-Euler approximation.
2. Active channel models (e.g. Hodgkin-Huxley) require sub-ms timesteps
   (~0.01 ms) to resolve voltage-gated Na/K kinetics. 1 ms must NOT
   be treated as sufficient for HH kinetics.
3. A future HH model must declare its own numerical-resolution
   requirements via the NumericalResolution contract on DynamicsModel.
   It may request a smaller timestep or alternative integration method.
4. No future timestep may be chosen as a biological fact.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from ..neuron import Neuron


@dataclass
class NumericalResolution:
    """Documents the numerical resolution contract for a dynamics model.

    This is META-INFORMATION about simulation numerics, NOT a biological
    parameter. It records the timestep for which the model's behavior has
    been validated or is appropriate, and any resolution constraints.

    See the NUMERICAL RESOLUTION POLICY in this module's docstring for
    the distinction between biological timescales, simulator timestep,
    numerical resolution, and model approximation.
    """

    timestep_ms: float
    resolution_note: str


@runtime_checkable
class DynamicsModel(Protocol):
    """Interface for neural dynamics computation.

    Implementations are responsible for:
    - Integrating a neuron's membrane potential (exponential decay + input)
    - Determining whether the neuron spikes
    - Resetting the neuron after a spike (potential, refractory)
    - Receiving synaptic input (respecting refractory state)

    This is an APPROXIMATION of biological neural dynamics. No model
    is claimed to be biologically accurate; each represents a
    computational approximation for simulation purposes.

    Implementations must provide a ``numerical_resolution`` attribute
    (NumericalResolution) documenting the timestep(s) for which the
    model has been validated and any numerical constraints. See the
    NUMERICAL RESOLUTION POLICY in the module docstring.
    """

    numerical_resolution: NumericalResolution

    @property
    def name(self) -> str:
        """Identifier for this dynamics model."""
        ...

    def inject_sensory_current(self, neuron: Neuron, current: float) -> None:
        """Inject external current into a neuron's membrane potential.

        This is called by NeuralEngine BEFORE integrate_neuron.
        The current is added to the membrane potential.

        Args:
            neuron: The neuron to inject current into
            current: Voltage-equivalent current to add (mV)
        """
        ...

    def receive_synaptic_spike(self, neuron: Neuron, weight: float, sign: int) -> None:
        """Deliver a synaptic spike to a neuron.

        Args:
            neuron: The postsynaptic neuron
            weight: Synaptic weight (mV equivalent)
            sign: +1 for excitatory, -1 for inhibitory
        """
        ...

    def receive_electrical_current(self, neuron: Neuron, current: float) -> None:
        """Accumulate electrical (gap-junction) current for one timestep.

        Args:
            neuron: The postsynaptic neuron
            current: Gap-junction current to accumulate
        """
        ...

    def decay_conductances(self, neuron: Neuron) -> None:
        """Apply per-tick conductance decay to a neuron's synaptic state.

        Implementations that do not use conductance-based state perform
        a no-op. The conductance model applies exponential decay to
        g_syn: g_syn *= exp(-dt / tau_decay).
        """
        ...

    def integrate(self, neuron: Neuron, input_current: float = 0.0) -> bool:
        """Integrate a neuron's membrane potential for one timestep.

        Args:
            neuron: The neuron to integrate
            input_current: Additional voltage-equivalent current (mV)

        Returns:
            True if the neuron emitted a spike this step
        """
        ...

    def reset(self, neuron: Neuron) -> None:
        """Reset a neuron to its initial state.

        Restores membrane potential to resting potential and
        clears the refractory counter.
        """
        ...


class DynamicsModelFactory:
    """Factory for creating dynamics model instances.

    This allows the engine to select models without importing
    concrete implementations directly.
    """

    @staticmethod
    def create(name: str) -> DynamicsModel:
        """Create a dynamics model instance by name.

        Args:
            name: Model identifier (e.g. "lif_voltage", "conductance_v0")

        Returns:
            A DynamicsModel instance

        Raises:
            ValueError: If the model name is unknown
        """
        from .lif_voltage import LIFVoltageModel
        from .conductance import ConductanceDynamicsModel

        registry = {
            "lif_voltage": LIFVoltageModel,
            "conductance_v0": ConductanceDynamicsModel,
        }

        if name not in registry:
            raise ValueError(
                f"Unknown dynamics model '{name}'. "
                f"Available: {list(registry.keys())}"
            )

        return registry[name]()

    @staticmethod
    def available_models() -> list:
        """Return list of available model names."""
        from .lif_voltage import LIFVoltageModel
        from .conductance import ConductanceDynamicsModel

        return list({
            "lif_voltage": LIFVoltageModel,
            "conductance_v0": ConductanceDynamicsModel,
        }.keys())
