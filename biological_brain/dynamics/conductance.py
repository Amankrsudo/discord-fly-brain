"""Conductance-based neural dynamics model stub for 3.0C Phase 2, Step 1.

This model provides the architecture/state container for a future
conductance-based dynamics implementation that will use source-supported
parameters from the Augustin et al. 2019 (eNeuro) Drosophila GFS model.

IMPORTANT: This is an architecture stub only. No HH equations, channel
kinetics, or biological parameter inference is implemented. The model
raises NotImplementedError for actual integration.

Scientific context:
  The published Augustin et al. 2019 model uses a multi-compartment NEURON
  model with 51 isopotential segments per section and anatomical geometry.
  Our future conductance_v0 will be a reduced experimental approximation,
  NOT a reproduction of that NEURON model.

  Our dt=1 ms timestep CANNOT resolve sub-millisecond HH channel kinetics
  (Na activation tau ~ 0.1 ms) or the 0.1 ms chemical synapse rise time.
  Any implementation at dt=1 ms is therefore an explicit approximation.

Source-supported parameters (from PMC6469880 Table 1):
  - E_leak = -85 mV       [Günay et al. 2015 via Augustin et al. 2019]
  - E_Na = +65 mV         [Günay et al. 2015 via Augustin et al. 2019]
  - E_K = -74 mV          [Günay et al. 2015 via Augustin et al. 2019]
  - g_Na = 300 mS/cm^2    [Günay et al. 2015 via Augustin et al. 2019]
  - g_Nap = 0.11 mS/cm^2  [Günay et al. 2015 via Augustin et al. 2019]
  - g_K = 10 mS/cm^2      [Augustin et al. 2019, labeled "estimated"]
  - g_leak = 0.03 mS/cm^2 [Augustin et al. 2019, labeled "estimated"]
  - g_gap = 135 uS (young) [Augustin et al. 2019, labeled "estimated"]
  - g_gap = 34.5 uS (old)  [Augustin et al. 2019, labeled "estimated"]
  - Chemical synapse: rise_tau=0.1ms, decay_tau=1ms, E_syn=0mV,
    peak_conductance=80 uS, delay=0.15ms [Augustin et al. 2019, labeled
    "standard value" or "estimated"]

None of these are DIRECTLY_MEASURED for our specific neurons.

ARCHITECTURAL LIMITATION (future work, NOT solved here):
  LC4/LPLC2 and PSI lack source-supported intrinsic HH parameters.
  Future conductance_v0 may require per-neuron dynamics selection or a
  hybrid model strategy where some neurons use conductance dynamics and
  others remain LIF-compatible. This step does NOT implement that.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from ..neuron import Neuron
from .base import DynamicsModel


@dataclass
class ConductanceParams:
    """Container for source-supported conductance parameters.

    All defaults come from Augustin et al. 2019 (eNeuro) Table 1,
    which derived active conductances from Günay et al. 2015 Drosophila
    motoneuron model. These are model parameters, not direct measurements.

    None of these should be labeled DIRECTLY_MEASURED.
    """
    E_leak: float = -85.0      # mV, reversal potential [Günay et al. 2015]
    E_Na: float = 65.0         # mV, sodium reversal [Günay et al. 2015]
    E_K: float = -74.0         # mV, potassium reversal [Günay et al. 2015]
    g_Na: float = 300.0        # mS/cm^2, max transient Na [Günay et al. 2015]
    g_Nap: float = 0.11        # mS/cm^2, persistent Na [Günay et al. 2015]
    g_K: float = 10.0          # mS/cm^2, max K [Augustin et al. 2019, "estimated"]
    g_leak: float = 0.03       # mS/cm^2 [Augustin et al. 2019, "estimated"]
    C_m: float = 1.0           # uF/cm^2 [Augustin et al. 2019, "estimated"]
    V_threshold: float = -50.0  # mV, approximate threshold for spike detection
    tau_syn_decay_ms: float = 1.0   # ms chemical synapse decay tau
    E_syn: float = 0.0         # mV, chemical synapse reversal (ACh)


@dataclass
class ConductanceNeuronState:
    """Per-neuron state for conductance-based model.

    Stores dynamic variables that the future HH implementation will use.
    Currently empty placeholders — no gating variables implemented.
    """
    V: float = -70.0           # membrane potential (mV)
    I_elec_accumulator: float = 0.0  # accumulated gap-junction current this tick
    g_syn: float = 0.0         # instantaneous synaptic conductance
    refractory_remaining: int = 0    # integer ticks (approximate)


class ConductanceDynamicsModel(DynamicsModel):
    """Architecture stub for conductance-based dynamics (3.0C Phase 2 Step 1).

    This is NOT a working conductance model. It provides the state
    containers and interface conformity needed for future implementation.

    Key constraints from the scientific audit:
    - dt=1ms cannot resolve HH channel kinetics (tau ~ 0.1ms) → APPROXIMATION
    - LC4/LPLC2/PSI lack source-supported HH parameters → must stay LIF
    - Sensory input is in mV-equivalent, not physical current → no conversion
    - 135 uS gap junction = ESTIMATED (PMC6469880 Table 1), not DIRECTLY_MEASURED
    - 80 uS chemical peak = ESTIMATED (PMC6469880 Table 1), not DIRECTLY_MEASURED
    """

    @property
    def name(self) -> str:
        return "conductance_v0"

    def inject_sensory_current(self, neuron: Neuron, current: float) -> None:
        """Inject external current into a neuron's membrane potential.

        STUB: Not implemented yet.
        Sensory input conversion from mV-equivalent to physical current
        requires input resistance and membrane area, which are not
        available from cited sources.
        """
        raise NotImplementedError(
            "conductance_v0: sensory current injection not yet implemented. "
            "Requires input resistance and membrane area (not source-supported)."
        )

    def receive_synaptic_spike(self, neuron: Neuron, weight: float, sign: int) -> None:
        """Deliver a synaptic spike to a neuron.

        STUB: Not implemented yet.
        In the conductance model, this would increment g_syn by a
        conductance amount derived from the chemical synapse peak
        conductance (80 uS, ESTIMATED per PMC6469880 Table 1).
        """
        raise NotImplementedError(
            "conductance_v0: synaptic conductance increment not yet implemented."
        )

    def receive_electrical_current(self, neuron: Neuron, current: float) -> None:
        """Accumulate gap-junction current from electrical synapses.

        This is called by NeuralEngine before integrate() to sum
        all electrical currents: I_elec = g_gap * (V_pre - V_post).

        STUB: Accumulates into state if present, otherwise no-op.
        """
        state = getattr(neuron, '_conductance_state', None)
        if state is not None:
            state.I_elec_accumulator += current

    def integrate(self, neuron: Neuron, input_current: float = 0.0) -> bool:
        """Integrate membrane dynamics for one timestep.

        STUB: Not implemented yet.
        Future implementation will solve the membrane equation:

            C_m * dV/dt = I_inj + I_elec - I_leak - I_Na - I_K - I_Nap - I_syn

        where each current is conductance-based:
            I_leak = g_leak * (V - E_leak)
            I_Na    = g_Na * m^3 * h * (V - E_Na)   [HH gating]
            I_K     = g_K * n^4 * (V - E_K)         [HH gating]
            I_syn   = g_syn * (V - E_syn)

        WARNING: dt=1ms cannot resolve Na activation kinetics (tau ~0.1ms).
        Any numerical implementation is an explicit APPROXIMATION.
        """
        raise NotImplementedError(
            "conductance_v0: HH integration not yet implemented. "
            "Blocked by dt=1ms timestep vs sub-ms channel kinetics."
        )

    def reset(self, neuron: Neuron) -> None:
        """Reset conductance-model state for a neuron.

        Clears the accumulated electrical current and synaptic conductance.
        Does NOT reset membrane potential to V_rest automatically — the
        neuron's own reset() handles that.
        """
        state = getattr(neuron, '_conductance_state', None)
        if state is not None:
            state.I_elec_accumulator = 0.0
            state.g_syn = 0.0
            state.refractory_remaining = 0
