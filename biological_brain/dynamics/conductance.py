"""Conductance-based neural dynamics model for 3.0C Phase 2.

This model implements a reduced single-compartment conductance-based
architecture with source-supported parameters from the Augustin et al.
2019 (eNeuro) Drosophila GFS model (PMC6469880).

CURRENT STATUS (Phase 2 Steps 1-6):
  - Electrical (gap-junction) current calculation: IMPLEMENTED (Step 3)
  - Chemical synaptic conductance accumulation/decay: IMPLEMENTED (Step 4)
  - Membrane current-balance scaffold: IMPLEMENTED (Step 5)
  - Passive membrane voltage integration (Forward Euler): IMPLEMENTED (Step 6)
  - Reduced threshold-crossing spike-event adapter: IMPLEMENTED (Step 8)

SCIENTIFIC LIMITATIONS:
  The published GFS conductance model (PMC6469880) is a MULTI-COMPARTMENT
  NEURON cable model with 51 isopotential segments per section and anatomical
  geometry. Our implementation is a reduced single-compartment approximation
  and does NOT claim to reproduce the published cable model.

  This is a reduced single-compartment approximation. It is not the
  Augustin et al. multi-compartment GFS model and does not reproduce its
  active channel kinetics.

   Voltage integration is implemented as a passive Forward Euler update
   (Step 6). Active voltage-gated Na/K kinetics (HH gating) are NOT
   implemented. Action-potential generation is outside this model.

  Our dt=1 ms timestep CANNOT resolve sub-millisecond HH channel kinetics
  (Na activation tau ~ 0.1 ms) or the 0.1 ms chemical synapse rise time.

  Chemical synaptic rise τ=0.1 ms is below the simulator's 1 ms temporal
  resolution and is represented as an instantaneous conductance increment.

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

UNIT HANDLING:
  g_leak is a conductance DENSITY (mS/cm²). Synaptic and gap-junction
  conductances are ABSOLUTE (µS). These CANNOT be combined without an
  explicit membrane area (cm²). Voltage integration requires this area
  to be set via ConductanceParams.membrane_area_cm2.

ARCHITECTURAL NOTE:
  The conductance_state field on Neuron is optional and defaults to None.
  Only neurons that explicitly have ConductanceNeuronState attached can
  use this model. LC4/LPLC2 and PSI neurons are expected to remain on
  lif_voltage until source-supported parameters are found. This does NOT
  implement per-neuron mixed LIF/HH execution.
"""

from dataclasses import dataclass, field
from math import exp
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
    g_syn_peak_us: float = 80.0   # µS, chemical synapse peak conductance [Augustin et al. 2019, estimated]
    membrane_area_cm2: Optional[float] = None  # cm², required for passive integration; APPROXIMATION (test-only reference)


@dataclass
class ConductanceNeuronState:
    """Per-neuron state for conductance-based model.

    The published GFS conductance model (PMC6469880) is a multi-compartment
    NEURON cable model. This implementation is a reduced single-compartment
    architecture and does NOT claim to reproduce the published cable model.

    Voltage integration is implemented as passive Forward Euler (Step 6).
    Active voltage-gated Na/K kinetics are NOT implemented.
    """
    V: float = -70.0           # membrane potential (mV)
    I_elec_accumulator: float = 0.0  # accumulated gap-junction current (nA)
    g_syn: float = 0.0         # instantaneous synaptic conductance (µS)
    I_syn: float = 0.0         # computed chemical synaptic current (nA)
    I_applied_accumulator: float = 0.0  # accumulated applied/sensory current (µA, future use)
    I_total: float = 0.0       # total membrane current (dimensionally mixed — see integrate)
    refractory_remaining: int = 0    # integer ticks (approximate)
    params: Optional['ConductanceParams'] = None  # provenance-tagged parameters for this neuron


class ConductanceDynamicsModel(DynamicsModel):
    """Conductance-based dynamics model for 3.0C Phase 2.

    Implements:
    - Electrical (gap-junction) current calculation: I_elec = g_gap * (V_pre - V_post)
    - Chemical synaptic conductance accumulation and exponential decay
    - Passive membrane voltage integration via Forward Euler (Step 6)
      C_m * dV/dt = I_applied - I_leak - I_syn - I_ion + I_elec
    - Reduced threshold-crossing spike-event adapter (Step 8):
      detects upward threshold crossing, emits spike, resets V

    This is a reduced single-compartment approximation. It is NOT the
    Augustin et al. multi-compartment GFS model and does NOT reproduce
    active channel kinetics.

    Key constraints:
    - dt=1ms cannot resolve HH channel kinetics (tau ~ 0.1ms) → APPROXIMATION
    - LC4/LPLC2/PSI lack source-supported HH parameters → must stay LIF
    - Sensory input is in mV-equivalent, not physical current → no conversion
    - 135 uS gap junction = ESTIMATED (PMC6469880 Table 1), not DIRECTLY_MEASURED
    - 80 uS chemical peak = ESTIMATED (PMC6469880 Table 1), not DIRECTLY_MEASURED
    - Voltage integration: IMPLEMENTED as passive Forward Euler with spike-event adapter (Steps 6-8)

    The conductance_state field on Neuron is optional and defaults to None.
    Only neurons that explicitly have ConductanceNeuronState attached can
    use this model. LC4/LPLC2 and PSI neurons are expected to remain on
    lif_voltage until source-supported parameters are found. This does NOT
    implement per-neuron mixed LIF/HH execution.
    """

    def _ensure_conductance_state(self, neuron: Neuron) -> ConductanceNeuronState:
        """Verify neuron has conductance state, raise if missing."""
        if neuron.conductance_state is None:
            raise RuntimeError(
                f"conductance_v0: Neuron '{neuron.neuron_id}' lacks conductance_state. "
                f"This model requires explicit ConductanceNeuronState with source-supported "
                f"parameters (e.g., from PMC6469880 Table 1). "
                f"LC4, LPLC2, and PSI currently have no source-supported intrinsic HH "
                f"parameters and must remain on lif_voltage. "
                f"Use attach_conductance_state() to initialize."
            )
        return neuron.conductance_state

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
        self._ensure_conductance_state(neuron)
        raise NotImplementedError(
            "conductance_v0: sensory current injection not yet implemented. "
            "Requires input resistance and membrane area (not source-supported)."
        )

    def receive_synaptic_spike(self, neuron: Neuron, weight: float, sign: int) -> None:
        """Increment chemical synaptic conductance on spike arrival.

        Called by NeuralEngine when a delayed chemical spike is delivered.

        Chemical synaptic rise τ=0.1 ms is below the simulator's 1 ms
        temporal resolution and is represented as an instantaneous
        conductance increment (APPROXIMATION).

        The conductance increment uses the model parameter g_syn_peak_us
        (80 µS, published computational-model parameter from Augustin et
        al. 2019 via PMC6469880, labeled "estimated").

        IMPORTANT: weight_mV is NOT converted to conductance. The LIF
        weight_mV values are voltage-calibrated for the 3.0B LIF model
        and lack biophysical validation as conductance values.

        Multiple spikes arriving at the same tick each contribute their
        full conductance increment; conductances sum linearly.
        """
        self._ensure_conductance_state(neuron)
        params = neuron.conductance_state.params or ConductanceParams()
        neuron.conductance_state.g_syn += params.g_syn_peak_us

    def receive_electrical_current(self, neuron: Neuron, current: float) -> None:
        """Accumulate gap-junction current from electrical synapses.

        This is called by NeuralEngine before integrate() to sum
        all electrical currents: I_elec = g_gap * (V_pre - V_post).
        """
        self._ensure_conductance_state(neuron)
        neuron.conductance_state.I_elec_accumulator += current

    def decay_conductances(self, neuron: Neuron) -> None:
        """Decay chemical synaptic conductance for one timestep.

        Implements exponential decay:
            g_syn(t + dt) = g_syn(t) * exp(-dt / tau_decay)

        With dt=1 ms and tau_decay=1 ms (published standard modeling
        parameter from Augustin et al. 2019 via PMC6469880), each tick
        decays g_syn by a factor of exp(-1).

        Chemical synaptic rise τ=0.1 ms is below 1 ms resolution and
        is represented as instantaneous increment (see receive_synaptic_spike).

        Does NOT compute I_syn = g_syn * (V - E_syn). That belongs to
        the membrane-dynamics step (not yet implemented).
        """
        if neuron.conductance_state is None:
            return
        params = neuron.conductance_state.params or ConductanceParams()
        decay_factor = exp(-neuron.dt / params.tau_syn_decay_ms)
        neuron.conductance_state.g_syn *= decay_factor

    def compute_leak_current(self, neuron: Neuron) -> float:
        """I_leak = g_leak * (V - E_leak).

        Returns leak current density in µA/cm² because g_leak is a
        conductance DENSITY (mS/cm²):
            g_leak (mS/cm²) * (V - E_leak) (mV) = µA/cm²

         This CANNOT be directly summed with I_syn or I_elec (which are
         in absolute nA) without membrane area conversion.
        """
        state = self._ensure_conductance_state(neuron)
        p = ConductanceParams()
        return p.g_leak * (state.V - p.E_leak)

    def compute_synaptic_current(self, neuron: Neuron) -> float:
        """I_syn = g_syn * (V - E_syn).

        Returns absolute chemical synaptic current in nA because g_syn
        is an absolute conductance (µS):
            g_syn (µS) * (V - E_syn) (mV) = nA

        E_syn = 0 mV (published standard modeling parameter, ACh reversal,
        Augustin et al. 2019 via PMC6469880).
        """
        state = self._ensure_conductance_state(neuron)
        p = ConductanceParams()
        return state.g_syn * (state.V - p.E_syn)

    def compute_electrical_current(self, neuron: Neuron) -> float:
        """I_elec = accumulated gap-junction current.

        Returns the accumulated electrical current in nA (from
        _compute_electrical_currents: g_gap (µS) * ΔV (mV) = nA).
        """
        state = self._ensure_conductance_state(neuron)
        return state.I_elec_accumulator

    def compute_ionic_current(self, neuron: Neuron) -> float:
        """I_ion — placeholder for future voltage-gated Na/K currents.

        Returns 0.0. HH gating kinetics (m, h, n) are NOT implemented.
        Na activation tau ~ 0.1 ms is below this simulator's 1 ms
        resolution (dt=1 ms).
        """
        self._ensure_conductance_state(neuron)
        return 0.0

    def integrate(self, neuron: Neuron, input_current: float = 0.0) -> bool:
        """Integrate membrane potential and detect spike events (Steps 6–8).

        Implements:
        1. Refractory check — reuses existing neuron.refractory_remaining
           (simulator state, NOT a new biological parameter).
        2. Passive Forward Euler voltage update:
           C_m * dV/dt = I_applied - I_leak - I_syn - I_ion + I_elec
        3. Reduced threshold-crossing spike-event adapter:
           Detects upward crossing of neuron.threshold and emits a spike
           event, resets V to neuron.reset_potential, and sets refractory.

        This is a REDUCED THRESHOLD-CROSSING SPIKE-EVENT APPROXIMATION.
        It is NOT a biological action-potential model and NOT HH.
        The real GFS uses active voltage-gated ion channels, which are
        outside this model due to dt=1ms limitations and parameter gaps.

        UNIT HANDLING:
        - g_leak is a conductance DENSITY (mS/cm²): I_leak = g_leak*(V-E_leak) → µA/cm²
        - g_syn is ABSOLUTE conductance (µS): I_syn = g_syn*(V-E_syn) → nA
        - g_gap currents are ABSOLUTE (nA): I_elec from accumulator
        - All absolute currents are converted to density (µA/cm²) using
          the explicit membrane_area_cm2 before combining.
        - input_current is treated as a density current (µA/cm²).

        Raises NotImplementedError when membrane_area_cm2 is None, because
        density and absolute currents cannot be combined without it.

        Args:
            neuron: The neuron to integrate
            input_current: Density current (µA/cm²)

        Returns:
            True if a spike event was emitted, False otherwise
        """
        # --- Refractory check: reuse existing Neuron refractory state ---
        # This is simulator behavior inherited from the existing architecture.
        # neuron.refractory_remaining is decremented by 1 each tick.
        if neuron.refractory_remaining > 0:
            neuron.refractory_remaining -= 1
            state = self._ensure_conductance_state(neuron)
            state.refractory_remaining = neuron.refractory_remaining
            return False

        state = self._ensure_conductance_state(neuron)
        params = state.params or ConductanceParams()

        if params.membrane_area_cm2 is None:
            raise NotImplementedError(
                "conductance_v0: voltage integration requires explicit "
                "membrane_area_cm2 in ConductanceParams to resolve unit "
                "incompatibility between g_leak (mS/cm² density) and "
                "g_syn/g_gap (absolute µS). Without area, the membrane "
                "current sum is dimensionally inconsistent. "
                "Set via attach_conductance_state(neuron, params=ConductanceParams(membrane_area_cm2=...))."
            )

        area = params.membrane_area_cm2
        dt = neuron.dt  # 1 ms from simulator configuration

        I_applied_density = input_current + state.I_applied_accumulator  # µA/cm²

        I_leak_density = params.g_leak * (state.V - params.E_leak)  # µA/cm²

        I_syn_abs = state.g_syn * (state.V - params.E_syn)  # nA (absolute)
        I_syn_density = I_syn_abs / (1000.0 * area)  # nA → µA/cm²

        I_elec_density = state.I_elec_accumulator / (1000.0 * area)  # nA → µA/cm²

        I_ion_density = 0.0  # no HH gating

        # Forward Euler: C_m * dV/dt = I_applied - I_leak - I_syn - I_ion + I_elec
        # Units: dt(ms) * (µA/cm²) / (µF/cm²) = ms * (µA/µF) = mV
        V_before = state.V
        dV_dt = (
            I_applied_density - I_leak_density - I_syn_density
            - I_ion_density + I_elec_density
        ) / params.C_m

        state.V += dt * dV_dt
        neuron.membrane_potential = state.V

        state.I_syn = I_syn_abs
        state.I_total = (
            I_applied_density - I_leak_density - I_syn_density
            + I_elec_density
        )

        # --- Spike-event adapter (Step 8) ---
        # Uses existing neuron.threshold (an existing simulator threshold,
        # NOT a directly measured Drosophila action-potential threshold).
        # Detects upward crossing: V_before < threshold AND V >= threshold.
        # This prevents repeated spikes while V stays above threshold.
        if V_before < neuron.threshold and state.V >= neuron.threshold:
            state.V = neuron.reset_potential
            neuron.membrane_potential = neuron.reset_potential
            neuron.refractory_remaining = neuron.refractory_period
            state.refractory_remaining = neuron.refractory_period
            return True

        return False

    def reset(self, neuron: Neuron) -> None:
        """Reset conductance-model state for a neuron.

        Clears all current bookkeeping and resets voltage to resting potential.
        The membrane potential (state.V and neuron.membrane_potential) is
        restored to neuron.resting_potential. This override only resets
        conductance-specific state, preserving all existing LIF reset
        behavior for neurons that use the LIF model.
        """
        if neuron.conductance_state is not None:
            neuron.conductance_state.V = neuron.resting_potential
            neuron.membrane_potential = neuron.resting_potential
            neuron.conductance_state.I_elec_accumulator = 0.0
            neuron.conductance_state.g_syn = 0.0
            neuron.conductance_state.I_syn = 0.0
            neuron.conductance_state.I_applied_accumulator = 0.0
            neuron.conductance_state.I_total = 0.0
            neuron.conductance_state.refractory_remaining = 0
            neuron.refractory_remaining = 0


def attach_conductance_state(neuron: Neuron, params: Optional[ConductanceParams] = None) -> None:
    """Explicitly initialize conductance state on a Neuron.

    Call this helper to enable conductance_v0 for a neuron that has
    source-supported parameters. This is an EXPLICIT operation — the
    helper does NOT automatically assign parameters to any neuron.

    Args:
        neuron: The neuron to attach state to
        params: Optional ConductanceParams. If None, uses default params
                from PMC6469880 Table 1 (Günay et al. 2015 motoneuron model).

    Note:
        LC4, LPLC2, and PSI neurons lack source-supported intrinsic HH
        parameters and must NOT have conductance state attached.
        Only use this for neurons where full parameter provenance exists.
    """
    if params is None:
        params = ConductanceParams()
    neuron.conductance_state = ConductanceNeuronState(
        V=neuron.membrane_potential,
        params=params
    )
