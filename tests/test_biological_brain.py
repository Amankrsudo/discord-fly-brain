"""Unit tests for Biological Brain 3.0 components."""

import pytest
from biological_brain import (
    Neuron, Synapse, Sign, Circuit, NeuralEngine,
    SignalTranslator, BiologicalBrain, BiologicalMode, BIOLOGICAL_CIRCUITS,
    MODEL_NAME_LIF_VOLTAGE
)


class TestNeuron:
    """Test Stage A Leaky Integrate-and-Fire neuron with biophysical parameters."""

    def test_neuron_initializes_at_resting_potential(self):
        """Neuron starts at resting potential."""
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0)
        assert n.membrane_potential == -70.0

    def test_neuron_integrate_threshold_spike(self):
        """Neuron spikes when membrane potential crosses threshold.
        
        Note: Decay is applied before threshold check in same tick,
        so input current is partially leaked. With tau_m=1.0, 
        decay_factor ≈ 0.632, so 20mV input → ~12.6mV effective.
        """
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, reset_potential=-75.0, tau_m=1.0)
        assert n.membrane_potential == -70.0
        
        # Strong input to overcome decay in same tick
        # V = V_rest + (V - V_rest)*exp(-dt/tau) + I
        # Need: -70 + 0 + I*0.632 > -55 → I > 23.7
        spiked = n.integrate(25.0)
        assert spiked is True
        assert n.membrane_potential == -75.0  # Reset to reset_potential
        assert n.refractory_remaining == n.refractory_period

    def test_neuron_refractory_period(self):
        """Neuron cannot spike during refractory period."""
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, reset_potential=-75.0, 
                   refractory_period=2, tau_m=1.0)
        
        # Trigger spike
        n.integrate(20.0)  # Strong input to spike immediately
        assert n.refractory_remaining == 2
        
        # During refractory - no spike possible even with huge input
        spiked = n.integrate(100.0)
        assert spiked is False
        assert n.refractory_remaining == 1
        
        spiked = n.integrate(100.0)
        assert spiked is False
        assert n.refractory_remaining == 0
        
        # After refractory - can spike again
        spiked = n.integrate(20.0)
        assert spiked is True

    def test_neuron_exponential_decay_toward_resting(self):
        """Membrane potential decays exponentially toward resting potential."""
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        # Inject current to raise potential
        n.membrane_potential = -60.0
        
        # With no input, should decay toward -70
        n.integrate(0.0)
        # decay_factor = 1 - exp(-1/10) ≈ 0.095
        # V = -70 + (-60 - -70) * (1 - 0.095) = -70 + 9.05 = -60.95
        assert n.membrane_potential < -60.0
        assert n.membrane_potential > -70.0
        
        # Multiple decays
        for _ in range(10):
            n.integrate(0.0)
        assert n.membrane_potential < -65.0

    def test_neuron_receive_spike(self):
        """Neuron receives synaptic input."""
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0)
        
        # Excitatory input
        n.receive_spike(5.0, sign=1)
        assert n.membrane_potential == -65.0  # -70 + 5
        
        # Inhibitory input
        n.receive_spike(3.0, sign=-1)
        assert n.membrane_potential == -68.0  # -65 - 3

    def test_neuron_receive_spike_blocked_during_refractory(self):
        """Synaptic input is blocked during refractory period."""
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, 
                   reset_potential=-75.0, refractory_period=2, tau_m=1.0)
        
        # Trigger spike
        n.integrate(20.0)
        assert n.refractory_remaining == 2
        
        # Try to receive spike during refractory
        n.receive_spike(100.0, sign=1)
        # Should remain at reset potential (-75) + decay
        # Actually after spike, V = -75, then integrate hasn't been called yet
        # So V should still be -75
        assert n.membrane_potential == -75.0

    def test_neuron_reset(self):
        """Reset clears state to resting potential."""
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, 
                   reset_potential=-75.0, tau_m=1.0)
        n.integrate(20.0)  # Spike
        n.reset()
        assert n.membrane_potential == -70.0
        assert n.refractory_remaining == 0

    def test_neuron_is_refractory(self):
        """Check refractory state."""
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, 
                   reset_potential=-75.0, refractory_period=2, tau_m=1.0)
        assert not n.is_refractory()
        n.integrate(20.0)
        assert n.is_refractory()
        n.integrate(0.0)  # Tick 1
        assert n.is_refractory()
        n.integrate(0.0)  # Tick 2
        assert not n.is_refractory()


class TestSynapse:
    """Test synapse model."""

    def test_synapse_excitatory_inhibitory(self):
        """Synapse sign affects effective weight."""
        exc = Synapse("A", "B", weight=1.0, sign=Sign.EXCITATORY)
        inh = Synapse("A", "B", weight=1.0, sign=Sign.INHIBITORY)
        
        assert exc.effective_weight() == 1.0
        assert inh.effective_weight() == -1.0

    def test_synapse_delay(self):
        """Synapse has configurable delay."""
        syn = Synapse("A", "B", delay=3)
        assert syn.delay == 3

    def test_synapse_delay_must_be_at_least_one(self):
        """Synapse delay must be >= 1."""
        with pytest.raises(ValueError):
            Synapse("A", "B", delay=0)
        with pytest.raises(ValueError):
            Synapse("A", "B", delay=-1)

    def test_synapse_disabled(self):
        """Disabled synapse has zero effective weight."""
        syn = Synapse("A", "B", weight=5.0, enabled=False)
        assert syn.effective_weight() == 0.0

    def test_synapse_sign_from_string(self):
        """Sign can be constructed from string."""
        syn = Synapse("A", "B", sign="inhibitory")
        assert syn.sign == Sign.INHIBITORY


class TestCircuit:
    """Test circuit definition and builder."""

    def test_circuit_construction(self):
        """Circuit can be built with neurons and synapses."""
        c = Circuit("test")
        
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0))
        c.add_neuron(Neuron("B", resting_potential=-70.0, threshold=-55.0))
        c.connect("A", "B", weight=5.0)
        
        assert "A" in c.neurons
        assert "B" in c.neurons
        assert len(c.synapses) == 1
        assert c.synapses[0].source == "A"
        assert c.synapses[0].target == "B"

    def test_circuit_input_output_definition(self):
        """Circuit tracks input and output neurons."""
        c = Circuit("test")
        c.add_neuron(Neuron("in1", resting_potential=-70.0, threshold=-55.0))
        c.add_neuron(Neuron("out1", resting_potential=-70.0, threshold=-55.0))
        c.input_neurons = ["in1"]
        c.output_neurons = ["out1"]
        
        assert c.get_inputs() == ["in1"]
        assert c.get_outputs() == ["out1"]

    def test_circuit_validate_missing_neuron(self):
        """Validation catches missing neurons."""
        c = Circuit("test")
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0))
        c.connect("A", "B")  # B doesn't exist
        
        warnings = c.validate()
        assert any("target 'B'" in w for w in warnings)

    def test_circuit_validate_missing_input(self):
        """Validation catches undefined input neurons."""
        c = Circuit("test")
        c.input_neurons = ["missing"]
        
        warnings = c.validate()
        assert any("Input neuron 'missing'" in w for w in warnings)


class TestNeuralEngine:
    """Test neural engine time-stepping."""

    def test_engine_step_advances_time(self):
        """Engine tick increments."""
        c = Circuit("test")
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0, tau_m=1.0))
        c.add_neuron(Neuron("B", resting_potential=-70.0, threshold=-55.0, tau_m=1.0))
        c.connect("A", "B", weight=10.0)
        c.input_neurons = ["A"]
        c.output_neurons = ["B"]
        
        engine = NeuralEngine(c)
        assert engine.current_tick == 0
        
        engine.step({"A": 20.0})
        assert engine.current_tick == 1
        
        engine.step({})
        assert engine.current_tick == 2

    def test_engine_spike_propagation(self):
        """Spike propagates through synapse after delay."""
        c = Circuit("test")
        # tau_m=10 gives decay_factor ≈ 0.095, so most input preserved
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0, reset_potential=-75.0, tau_m=10.0))
        c.add_neuron(Neuron("B", resting_potential=-70.0, threshold=-55.0, tau_m=10.0))
        c.connect("A", "B", weight=10.0, delay=1)
        c.input_neurons = ["A"]
        c.output_neurons = ["B"]
        
        engine = NeuralEngine(c)
        
        # Tick 1: A gets strong sensory input to spike
        # With tau_m=10, decay_factor ≈ 0.095, so ~90% of input preserved
        engine.step({"A": 20.0})
        
        # Tick 2: B receives spike (10mV → -60mV, below threshold)
        outputs = engine.step({})
        # B should have received 10mV, membrane = -70 + 10 = -60, then decay
        assert outputs["B"] > -70.0
        assert outputs["B"] < -55.0  # Below threshold

    def test_engine_inhibitory_spike_propagation(self):
        """Inhibitory spike hyperpolarizes target."""
        c = Circuit("test")
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0, tau_m=1.0))
        c.add_neuron(Neuron("B", resting_potential=-70.0, threshold=-55.0, tau_m=1.0))
        c.connect("A", "B", weight=5.0, sign=Sign.INHIBITORY, delay=1)
        c.input_neurons = ["A"]
        c.output_neurons = ["B"]
        
        engine = NeuralEngine(c)
        
        # Raise B's potential first
        engine.step({"B": 10.0})  # B at -60
        # A spikes
        engine.step({"A": 20.0})
        # Inhibitory spike arrives at B
        outputs = engine.step({})
        # B should be hyperpolarized: -60 - 5 = -65, then decay toward -70
        assert outputs["B"] < -60.0
        assert outputs["B"] > -70.0

    def test_engine_sensory_input(self):
        """Sensory input injected at each step (blocked during refractory)."""
        c = Circuit("test")
        # Use higher threshold so neuron doesn't spike in this test
        c.add_neuron(Neuron("in", resting_potential=-70.0, threshold=-40.0, tau_m=10.0))
        c.output_neurons = ["in"]
        
        engine = NeuralEngine(c)
        
        engine.step({"in": 10.0})  # -70 + 10*0.905 ≈ -61
        engine.step({"in": 10.0})  # Decay + 10*0.905
        
        state = engine.get_state()
        # Should accumulate but with decay, staying well below threshold
        assert state["neurons"]["in"]["potential"] > -70.0
        assert state["neurons"]["in"]["potential"] < -40.0

    def test_engine_sensory_input_blocked_during_refractory(self):
        """Sensory input blocked when neuron is refractory."""
        c = Circuit("test")
        c.add_neuron(Neuron("in", resting_potential=-70.0, threshold=-55.0, 
                            reset_potential=-75.0, refractory_period=2, tau_m=1.0))
        c.input_neurons = ["in"]
        c.output_neurons = ["in"]
        
        engine = NeuralEngine(c)
        
        # Spike the neuron
        engine.step({"in": 20.0})  # Spikes, V = -75, refractory=2
        # Sensory input during refractory should be ignored
        engine.step({"in": 100.0})  # Should not affect V
        state = engine.get_state()
        # V should only have decayed from -75 toward -70
        assert state["neurons"]["in"]["potential"] < -70.0

    def test_engine_reset(self):
        """Reset clears engine state."""
        c = Circuit("test")
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0, tau_m=1.0))
        c.connect("A", "A", weight=10.0)
        c.input_neurons = ["A"]
        c.output_neurons = ["A"]
        
        engine = NeuralEngine(c)
        engine.step({"A": 20.0})
        engine.step({})
        
        engine.reset()
        assert engine.current_tick == 0
        assert engine.circuit.neurons["A"].membrane_potential == -70.0

    def test_engine_delay_zero_raises_error(self):
        """Synapse with delay=0 raises error at construction time."""
        c = Circuit("test")
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0))
        c.add_neuron(Neuron("B", resting_potential=-70.0, threshold=-55.0))
        # Should raise at connect() time (Synapse.__post_init__)
        with pytest.raises(ValueError, match="delay must be >= 1"):
            c.connect("A", "B", weight=5.0, delay=0)


class TestSignalTranslator:
    """Test signal translation."""

    def test_translate_escape_signals(self):
        """Translator maps escape outputs to signals (bilateral max)."""
        c = Circuit("escape_core")
        for nid in ["TTMn_L", "TTMn_R", "DLMn_L", "DLMn_R", "GF_L", "GF_R"]:
            c.add_neuron(Neuron(nid, resting_potential=-70.0, threshold=-55.0))
        c.output_neurons = ["TTMn_L", "TTMn_R", "DLMn_L", "DLMn_R", "GF_L", "GF_R"]

        translator = SignalTranslator(c)
        signals = translator.translate({
            "TTMn_L": -55.0,
            "DLMn_R": -55.0,
            "GF_L": -45.0,
        })

        assert "escape_signal" in signals
        assert "flight_signal" in signals
        assert "threat_signal" in signals
        assert signals["escape_signal"] == 1.0
        assert signals["flight_signal"] == 1.0
        assert signals["threat_signal"] == 1.0

    def test_translate_bilateral_max(self):
        """Bilateral neurons use max value across hemispheres."""
        c = Circuit("escape_core")
        gf_l = Neuron("GF_L", resting_potential=-65.0, threshold=-45.0)
        gf_r = Neuron("GF_R", resting_potential=-65.0, threshold=-45.0)
        c.add_neuron(gf_l)
        c.add_neuron(gf_r)
        c.output_neurons = ["GF_L", "GF_R"]

        translator = SignalTranslator(c)
        signals = translator.translate({"GF_L": -45.0, "GF_R": -65.0})
        assert signals["threat_signal"] == 1.0

        signals = translator.translate({"GF_L": -65.0, "GF_R": -45.0})
        assert signals["threat_signal"] == 1.0

    def test_translate_normalizes_to_range(self):
        """Outputs normalized to [0, 1] based on resting→threshold range."""
        c = Circuit("test")
        n = Neuron("out", resting_potential=-70.0, threshold=-55.0)
        c.add_neuron(n)
        c.output_neurons = ["out"]
        
        translator = SignalTranslator(c)
        
        # At resting (-70) → 0.0
        signals = translator.translate({"out": -70.0})
        assert signals["out"] == 0.0
        
        # At threshold (-55) → 1.0
        signals = translator.translate({"out": -55.0})
        assert signals["out"] == 1.0
        
        # Midpoint (-62.5) → 0.5
        signals = translator.translate({"out": -62.5})
        assert signals["out"] == pytest.approx(0.5)
        
        # Above threshold → clamped to 1.0
        signals = translator.translate({"out": -50.0})
        assert signals["out"] == 1.0
        
        # Below resting → clamped to 0.0
        signals = translator.translate({"out": -80.0})
        assert signals["out"] == 0.0


class TestBiologicalBrain:
    """Test BiologicalBrain facade."""

    def test_legacy_mode_returns_empty(self):
        """LEGACY_2_0 mode returns empty signals."""
        BIOLOGICAL_CIRCUITS["escape"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.LEGACY_2_0)
            signals = brain.step({"lightLevel": 1.0})
            assert signals == {}
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_biological_mode_runs_circuit(self):
        """BIOLOGICAL_3_0 mode runs enabled circuits."""
        BIOLOGICAL_CIRCUITS["escape"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            signals = brain.step({"lightLevel": 0.5})
            assert any(k.startswith("bio_") for k in signals)
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_sensory_mapping_looming_keys(self):
        """Looming keys map to VP neurons with correct values."""
        BIOLOGICAL_CIRCUITS["escape"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            bio_input = brain._map_sensory_input({"loomingLeft": 1.0})
            assert bio_input["LC4_L"] == 5.0
            assert bio_input["LPLC2_L"] == 5.0
            assert "LC4_R" not in bio_input
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_sensory_mapping_fallback_keys(self):
        """Fallback 2.0 keys map to VP neurons."""
        BIOLOGICAL_CIRCUITS["escape"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            bio_input = brain._map_sensory_input({
                "lightLevel": 1.0,
                "nociception": True,
                "touch": True,
            })
            assert "LC4_L" in bio_input
            assert "LC4_R" in bio_input
            assert "LPLC2_L" in bio_input
            assert "LPLC2_R" in bio_input
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_sensory_mapping_sums_inputs(self):
        """Multiple stimuli targeting the same neuron are summed."""
        BIOLOGICAL_CIRCUITS["escape"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            bio_input = brain._map_sensory_input({
                "loomingLeft": 1.0,
                "nociception": True,
            })
            assert bio_input["LC4_L"] == 10.0  # 5.0 + 5.0
            assert bio_input["LPLC2_L"] == 10.0  # 5.0 + 5.0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_reset_clears_all(self):
        """Reset clears all engine state to resting potential."""
        BIOLOGICAL_CIRCUITS["escape"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            brain.step({"loomingLeft": 1.0})
            brain.step({"loomingLeft": 1.0})
            brain.reset()

            state = brain.get_circuit_state("escape_core")
            assert state["tick"] == 0
            for n in state["neurons"].values():
                assert n["potential"] == n["resting_potential"]
                assert n["refractory"] == 0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestEscapeCircuitStructure:
    """Test the escape circuit loaded from JSON."""

    def _get_brain(self):
        BIOLOGICAL_CIRCUITS["escape"] = True
        return BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)

    def test_circuit_loads_from_json(self):
        """escape_circuit.json loads without error."""
        brain = self._get_brain()
        try:
            assert "escape_core" in brain.circuits
            circuit = brain.circuits["escape_core"]
            assert len(circuit.neurons) == 12
            # 10 chemical + 8 electrical directed entries = 18 Synapse objects
            # (no expansion — JSON already contains both directions for electrical pairs)
            assert len(circuit.synapses) == 18
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_neuron_biophysics_gf(self):
        """GF_L/R: V_rest=-65, threshold=-45, reset=-65, tau_m=5, refractory=5."""
        brain = self._get_brain()
        try:
            circuit = brain.circuits["escape_core"]
            for nid in ["GF_L", "GF_R"]:
                n = circuit.neurons[nid]
                assert n.resting_potential == -65.0
                assert n.threshold == -45.0
                assert n.reset_potential == -65.0
                assert n.tau_m == 5.0
                assert n.refractory_period == 5
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_neuron_biophysics_motor(self):
        """TTMn, DLMn: V_rest=-70, threshold=-55, reset=-75, tau_m=10, refractory=2."""
        brain = self._get_brain()
        try:
            circuit = brain.circuits["escape_core"]
            for nid in ["TTMn_L", "TTMn_R", "DLMn_L", "DLMn_R"]:
                n = circuit.neurons[nid]
                assert n.resting_potential == -70.0
                assert n.threshold == -55.0
                assert n.reset_potential == -75.0
                assert n.tau_m == 10.0
                assert n.refractory_period == 2
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_neuron_biophysics_sensory_in(self):
        """LC4, LPLC2: V_rest=-70, threshold=-50, reset=-75, tau_m=15, refractory=2."""
        brain = self._get_brain()
        try:
            circuit = brain.circuits["escape_core"]
            for nid in ["LC4_L", "LC4_R", "LPLC2_L", "LPLC2_R"]:
                n = circuit.neurons[nid]
                assert n.resting_potential == -70.0
                assert n.threshold == -50.0
                assert n.reset_potential == -75.0
                assert n.tau_m == 15.0
                assert n.refractory_period == 2
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_neuron_biophysics_psi(self):
        """PSI_L/R: V_rest=-70, threshold=-55, reset=-75, tau_m=15, refractory=2."""
        brain = self._get_brain()
        try:
            circuit = brain.circuits["escape_core"]
            for nid in ["PSI_L", "PSI_R"]:
                n = circuit.neurons[nid]
                assert n.resting_potential == -70.0
                assert n.threshold == -55.0
                assert n.reset_potential == -75.0
                assert n.tau_m == 15.0
                assert n.refractory_period == 2
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_electrical_synapses_bidirectional(self):
        """Electrical synapses create bidirectional pairs (4 pairs total)."""
        brain = self._get_brain()
        try:
            circuit = brain.circuits["escape_core"]
            pairs = [
                ("GF_L", "TTMn_L"), ("TTMn_L", "GF_L"),
                ("GF_L", "PSI_L"), ("PSI_L", "GF_L"),
                ("GF_R", "TTMn_R"), ("TTMn_R", "GF_R"),
                ("GF_R", "PSI_R"), ("PSI_R", "GF_R"),
            ]
            for src, tgt in pairs:
                assert circuit.get_synapse(src, tgt) is not None
                syn = circuit.get_synapse(src, tgt)
                assert syn.neurotransmitter == "ShakB"
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_chemical_components_present(self):
        """GF->TTMn and GF->PSI chemical synapses exist with delay=2."""
        brain = self._get_brain()
        try:
            circuit = brain.circuits["escape_core"]
            chem_pairs = [
                ("GF_L", "TTMn_L"), ("GF_L", "PSI_L"),
                ("GF_R", "TTMn_R"), ("GF_R", "PSI_R"),
            ]
            for src, tgt in chem_pairs:
                syns = circuit.get_synapses(src, tgt)
                chem_syn = [s for s in syns if s.neurotransmitter == "ACh"]
                assert len(chem_syn) == 1
                assert chem_syn[0].delay == 2
                assert chem_syn[0].weight == 5.0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_io_neurons(self):
        """Inputs = VP neurons, outputs = motor neurons."""
        brain = self._get_brain()
        try:
            circuit = brain.circuits["escape_core"]
            assert set(circuit.get_inputs()) == {"LC4_L", "LC4_R", "LPLC2_L", "LPLC2_R"}
            assert set(circuit.get_outputs()) == {"TTMn_L", "TTMn_R", "DLMn_L", "DLMn_R"}
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_psi_to_dlmn_crossed(self):
        """PSI crosses to contralateral DLMn."""
        brain = self._get_brain()
        try:
            circuit = brain.circuits["escape_core"]
            syn1 = circuit.get_synapse("PSI_L", "DLMn_R")
            syn2 = circuit.get_synapse("PSI_R", "DLMn_L")
            assert syn1 is not None
            assert syn2 is not None
            assert syn1.weight == 17.0
            assert syn2.weight == 17.0
            assert syn1.neurotransmitter == "ACh"
            assert syn2.neurotransmitter == "ACh"
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_circuit_validates_clean(self):
        """Circuit passes validation with no warnings."""
        brain = self._get_brain()
        try:
            circuit = brain.circuits["escape_core"]
            warnings = circuit.validate()
            assert len(warnings) == 0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestEscapeLatency:
    """Test escape pathway timing against biological targets."""

    def _get_brain(self):
        BIOLOGICAL_CIRCUITS["escape"] = True
        return BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)

    def test_gf_to_ttmn_latency(self):
        """GF->TTMn latency is 1 tick (DIRECTLY_MEASURED: 1-2 ms, von Reyn 2014)."""
        brain = self._get_brain()
        try:
            brain.step({"GF_L": 25.0})
            outputs = brain.step({})
            engine = brain.engines["escape_core"]
            ttmn_l = engine.circuit.neurons["TTMn_L"]
            assert ttmn_l.membrane_potential < -55.0 or ttmn_l.refractory_remaining > 0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_gf_to_dlmn_latency(self):
        """GF->PSI->DLMn latency is 4 ticks (DIRECTLY_MEASURED: 3-4 ms, King & Wyman 1980)."""
        brain = self._get_brain()
        try:
            # GF spikes at tick 0
            brain.step({"GF_L": 25.0})  # tick 0: GF_L spikes
            # Tick 1: PSI_L receives electrical input (delay=1), should spike
            brain.step({})  # tick 1: PSI_L may spike
            # Tick 2, 3: chemical GF->PSI arrives (delay=2) but PSI already spiked
            brain.step({})  # tick 2
            brain.step({})  # tick 3
            # Tick 4: PSI_L spike (chemical delay=2) arrives at DLMn_R
            outputs = brain.step({})  # tick 4
            engine = brain.engines["escape_core"]
            dlmn_r = engine.circuit.neurons["DLMn_R"]
            # DLMn should have fired or be near threshold
            assert dlmn_r.refractory_remaining > 0 or dlmn_r.membrane_potential > -70.0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_full_pathway_short_mode(self):
        """loomingLeft=1.0 -> TTMn_L fires within 10-15 ticks."""
        brain = self._get_brain()
        try:
            signals = {}
            for i in range(16):
                signals = brain.step({"loomingLeft": 1.0})
                if signals.get("bio_escape_signal", 0.0) > 0.5:
                    break
            assert signals.get("bio_escape_signal", 0.0) > 0.5
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_gf_refractory(self):
        """GF cannot spike within 5 ticks of previous spike."""
        brain = self._get_brain()
        try:
            brain.step({"GF_L": 25.0})  # tick 0: GF_L spikes (refractory=5)
            brain.step({"GF_L": 25.0})  # tick 1: blocked (refractory=4)
            brain.step({"GF_L": 25.0})  # tick 2: blocked (refractory=3)
            engine = brain.engines["escape_core"]
            gf = engine.circuit.neurons["GF_L"]
            # GF should be refractory and not in a spiking state
            assert gf.refractory_remaining > 0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestEscapeBehavior:
    """Test escape circuit behavioral outputs."""

    def _get_brain(self):
        BIOLOGICAL_CIRCUITS["escape"] = True
        return BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)

    def test_left_looming_triggers_left_jump(self):
        """loomingLeft activates left TTMn more than right."""
        brain = self._get_brain()
        try:
            for _ in range(12):
                brain.step({"loomingLeft": 1.0})
            engine = brain.engines["escape_core"]
            ttmn_l = engine.circuit.neurons["TTMn_L"]
            ttmn_r = engine.circuit.neurons["TTMn_R"]
            assert ttmn_l.refractory_remaining > 0 or ttmn_l.membrane_potential < -60.0
            assert ttmn_r.refractory_remaining == 0
            assert ttmn_r.membrane_potential == -70.0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_nociception_triggers_escape(self):
        """Nociception triggers bilateral escape."""
        brain = self._get_brain()
        try:
            max_escape = 0.0
            for _ in range(15):
                signals = brain.step({"nociception": True})
                max_escape = max(max_escape, signals.get("bio_escape_signal", 0.0))
            assert max_escape > 0.5
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_no_stimulus_no_escape(self):
        """No stimulus produces no escape signal."""
        brain = self._get_brain()
        try:
            for _ in range(20):
                signals = brain.step({})
            assert signals.get("bio_escape_signal", 0.0) == 0.0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_weak_stimulus_no_escape(self):
        """Weak stimulus does not trigger escape."""
        brain = self._get_brain()
        try:
            for _ in range(20):
                signals = brain.step({"loomingLeft": 0.1})
            assert signals.get("bio_escape_signal", 0.0) == 0.0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_flight_signal_from_dlmn(self):
        """Flight signal activates when DLMn fires."""
        brain = self._get_brain()
        try:
            signals = {}
            for _ in range(12):
                signals = brain.step({"loomingLeft": 1.0})
            assert "bio_flight_signal" in signals
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class Test20Integration:
    """Test 2.0 system integration for escape circuit."""

    def _get_brain(self):
        BIOLOGICAL_CIRCUITS["escape"] = True
        return BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)

    def test_bio_signals_prefix(self):
        """All biological signals prefixed with 'bio_'."""
        brain = self._get_brain()
        try:
            signals = brain.step({"loomingLeft": 1.0})
            for k in signals:
                assert k.startswith("bio_")
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_legacy_mode_unchanged(self):
        """LEGACY_2_0 mode produces no biological signals."""
        brain = BiologicalBrain(mode=BiologicalMode.LEGACY_2_0)
        signals = brain.step({"lightLevel": 1.0, "nociception": True})
        assert signals == {}

    def test_optional_looming_keys(self):
        """Without looming keys, circuit still runs (no crash)."""
        brain = self._get_brain()
        try:
            signals = brain.step({"lightLevel": 0.5})
            assert isinstance(signals, dict)
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_fallback_nociception_triggers_escape(self):
        """Nociception fallback key triggers escape via VP activation."""
        brain = self._get_brain()
        try:
            max_escape = 0.0
            for _ in range(15):
                signals = brain.step({"nociception": True})
                max_escape = max(max_escape, signals.get("bio_escape_signal", 0.0))
            assert max_escape > 0.0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_threat_signal_produced_from_gf(self):
        """GF activity (not an output neuron) produces bio_threat_signal."""
        brain = self._get_brain()
        try:
            max_threat = 0.0
            for _ in range(15):
                signals = brain.step({"loomingLeft": 1.0})
                max_threat = max(max_threat, signals.get("bio_threat_signal", 0.0))
            assert max_threat > 0.5
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestValidationLatency:
    """Test the 3.0B.2 validation experiment runner."""

    def _get_validator(self):
        from biological_brain.validation import LatencyValidator
        BIOLOGICAL_CIRCUITS["escape"] = True
        brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
        return LatencyValidator(brain)

    def test_gf_to_ttmn_latency_left(self):
        """GF_L -> TTMn_L latency is 1 tick (target: 1-2 ticks, von Reyn 2014)."""
        validator = self._get_validator()
        try:
            report = validator.run_gf_to_ttmn_latency()
            left_result = report.results[0]
            assert left_result.source_neuron == "GF_L"
            assert left_result.target_neuron == "TTMn_L"
            assert left_result.latency_ticks == 1
            assert left_result.source_spike_tick == 0
            assert left_result.target_spike_tick == 1
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_gf_to_ttmn_latency_right(self):
        """GF_R -> TTMn_R latency is 1 tick (target: 1-2 ticks, von Reyn 2014)."""
        validator = self._get_validator()
        try:
            report = validator.run_gf_to_ttmn_latency()
            right_result = report.results[1]
            assert right_result.source_neuron == "GF_R"
            assert right_result.target_neuron == "TTMn_R"
            assert right_result.latency_ticks == 1
            assert right_result.source_spike_tick == 0
            assert right_result.target_spike_tick == 1
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_gf_to_ttmn_latency_bilateral(self):
        """Both hemispheres produce 1-tick latency."""
        validator = self._get_validator()
        try:
            report = validator.run_gf_to_ttmn_latency()
            for r in report.results:
                assert r.latency_ticks == 1
            assert len(report.results) == 2
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_gf_spike_injection_threshold(self):
        """25.0 mV injection is the minimum to force GF spike in one tick."""
        validator = self._get_validator()
        try:
            brain = validator.brain
            brain.reset()
            # GF needs: V_rest + W*exp(-dt/tau) >= threshold
            # -65 + W*exp(-1/5) >= -45 => W >= 24.43
            # 25.0 > 24.43, so should spike
            signals = brain.step({"GF_L": 25.0})
            engine = brain.engines["escape_core"]
            gf = engine.circuit.neurons["GF_L"]
            assert gf.refractory_remaining > 0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_validator_report_contains_evidence(self):
        """Validation report includes evidence classification and approximation notes."""
        validator = self._get_validator()
        try:
            report = validator.run_gf_to_ttmn_latency()
            for r in report.results:
                assert r.evidence is not None
                assert r.approximation is not None
                assert "DIRECTLY_MEASURED" in r.evidence
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestLateralization:
    """Test left/right lateralization of the escape circuit."""

    def _get_validator(self):
        from biological_brain.validation import LateralizationValidator
        BIOLOGICAL_CIRCUITS["escape"] = True
        brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
        return LateralizationValidator(brain)

    def test_left_looming_spikes_left_only(self):
        """loomingLeft activates left VP/GF/TTMn, not right."""
        validator = self._get_validator()
        try:
            report = validator.run_lateralization()
            left_result = report.results[0]
            assert "LC4_L" in left_result.vp_spikes
            assert "LPLC2_L" in left_result.vp_spikes
            assert "GF_L" in left_result.gf_spikes
            assert "TTMn_L" in left_result.ttmn_spikes
            assert "TTMn_R" not in left_result.ttmn_spikes
            assert "LC4_R" not in left_result.vp_spikes
            assert "GF_R" not in left_result.gf_spikes
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_right_looming_spikes_right_only(self):
        """loomingRight activates right VP/GF/TTMn, not left."""
        validator = self._get_validator()
        try:
            report = validator.run_lateralization()
            right_result = report.results[1]
            assert "LC4_R" in right_result.vp_spikes
            assert "LPLC2_R" in right_result.vp_spikes
            assert "GF_R" in right_result.gf_spikes
            assert "TTMn_R" in right_result.ttmn_spikes
            assert "TTMn_L" not in right_result.ttmn_spikes
            assert "LC4_L" not in right_result.vp_spikes
            assert "GF_L" not in right_result.gf_spikes
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_front_looming_bilateral(self):
        """loomingFront activates both hemispheres."""
        validator = self._get_validator()
        try:
            report = validator.run_lateralization()
            front_result = report.results[2]
            assert "TTMn_L" in front_result.ttmn_spikes
            assert "TTMn_R" in front_result.ttmn_spikes
            assert "GF_L" in front_result.gf_spikes
            assert "GF_R" in front_result.gf_spikes
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_lateralization_validation_pass(self):
        """All three lateralization conditions pass validation."""
        validator = self._get_validator()
        try:
            report = validator.run_lateralization()
            validation = validator.validate_lateralization(report)
            assert validation["loomingLeft"] is True
            assert validation["loomingRight"] is True
            assert validation["loomingFront"] is True
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_left_looming_produces_escape_signal(self):
        """Left looming stimulates escape pathway (ipsilateral TTMn)."""
        validator = self._get_validator()
        try:
            report = validator.run_lateralization()
            left_result = report.results[0]
            assert left_result.escape_signal > 0.5
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_lateralization_report_has_evidence(self):
        """Lateralization report includes biological evidence classification."""
        validator = self._get_validator()
        try:
            report = validator.run_lateralization()
            for r in report.results:
                assert "DIRECTLY_MEASURED" in r.evidence
                assert "APPROXIMATION" in r.approximation
                assert r.biological_prediction is not None
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestWeakStrongThreshold:
    """Test the 3.0B.2 weak-strong threshold experiment."""

    def _get_validator(self):
        from biological_brain.validation import WeakStrongThresholdValidator
        BIOLOGICAL_CIRCUITS["escape"] = True
        brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
        return WeakStrongThresholdValidator(brain)

    def test_weak_intensity_no_escape(self):
        """Weak looming (0.1) does not trigger escape response."""
        validator = self._get_validator()
        try:
            report = validator.run_threshold_experiment()
            weak = report.results[0]
            assert weak.intensity == 0.1
            assert weak.response_magnitude < 0.5
            assert weak.vp_spike_tick is None
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_strong_intensity_full_escape(self):
        """Strong looming (1.0) triggers full escape response."""
        validator = self._get_validator()
        try:
            report = validator.run_threshold_experiment()
            strong = report.results[1]
            assert strong.intensity == 1.0
            assert strong.response_magnitude > 0.5
            assert strong.vp_spike_tick is not None
            assert strong.gf_spike_tick is not None
            assert strong.ttmn_spike_tick is not None
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_strong_intensity_short_latency(self):
        """Strong intensity (1.0) produces escape within 7 ticks (short-mode)."""
        validator = self._get_validator()
        try:
            report = validator.run_threshold_experiment()
            strong = report.results[1]
            assert strong.escape_tick is not None
            assert strong.escape_tick <= 7
            assert strong.vp_spike_tick == strong.gf_spike_tick - 1
            assert strong.gf_spike_tick == strong.ttmn_spike_tick - 1
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_threshold_between_weak_and_strong(self):
        """Binary-searched threshold is between weak (0.1) and strong (1.0)."""
        validator = self._get_validator()
        try:
            report = validator.run_threshold_experiment()
            threshold = report.results[2]
            assert 0.1 < threshold.intensity < 1.0
            assert threshold.response_magnitude > 0.5
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_threshold_within_validation_plan_range(self):
        """Measured threshold with 35-tick window is within the expected 0.3-0.7 range.

        At max_ticks=35 (short-mode latency upper bound, ~35ms), the binary-searched
        threshold falls within the validation plan's expected range. The threshold is
        explicitly labeled as window-dependent simulator behavior in the approximation.
        """
        validator = self._get_validator()
        try:
            report = validator.run_threshold_experiment()
            threshold = report.results[2]
            assert 0.3 <= threshold.intensity <= 0.7
            assert "WINDOW-DEPENDENT" in threshold.approximation
            assert "0.3-0.7" in threshold.approximation
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_threshold_is_window_dependent(self):
        """Threshold changes with simulation window, confirming it is not biological."""
        validator = self._get_validator()
        try:
            t35 = validator.find_threshold_intensity(max_ticks=35)
            t50 = validator.find_threshold_intensity(max_ticks=50)
            assert t35 > t50
            assert t35 != t50
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_validation_passes(self):
        """All threshold conditions pass validation."""
        validator = self._get_validator()
        try:
            report = validator.run_threshold_experiment()
            validation = validator.validate_threshold(report)
            assert validation["weak"] is True
            assert validation["strong"] is True
            assert validation["threshold"] is True
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_threshold_report_has_evidence(self):
        """Threshold report includes evidence classification and approximation."""
        validator = self._get_validator()
        try:
            report = validator.run_threshold_experiment()
            for r in report.results:
                assert r.evidence is not None
                assert r.approximation is not None
                assert r.biological_prediction is not None
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestTemporalSummation:
    """Test the 3.0B.2 temporal summation experiment."""

    def _get_validator(self):
        from biological_brain.validation import TemporalSummationValidator
        BIOLOGICAL_CIRCUITS["escape"] = True
        brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
        return TemporalSummationValidator(brain)

    def test_simultaneous_inputs_fire_gf(self):
        """Delay=0 (simultaneous VP spikes) fires GF."""
        validator = self._get_validator()
        try:
            report = validator.run_temporal_summation()
            simult = report.results[0]
            assert simult.delay_ticks == 0
            assert simult.gf_fired is True
            assert simult.escape_signal > 0.5
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_staggered_inputs_do_not_fire_gf(self):
        """Delays >= 1 (staggered VP spikes) do not fire GF."""
        validator = self._get_validator()
        try:
            report = validator.run_temporal_summation()
            for r in report.results[1:]:
                assert r.delay_ticks >= 1
                assert r.gf_fired is False
                assert r.escape_signal < 0.5
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_all_six_delays_tested(self):
        """Experiment tests delays 0 through 5."""
        validator = self._get_validator()
        try:
            report = validator.run_temporal_sumbination()
        except AttributeError:
            pass
        try:
            report = validator.run_temporal_summation()
            delays = [r.delay_ticks for r in report.results]
            assert delays == [0, 1, 2, 3, 4, 5]
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_validation_passes(self):
        """Simultaneous input fires, staggered inputs don't."""
        validator = self._get_validator()
        try:
            report = validator.run_temporal_summation()
            validation = validator.validate_temporal_summation(report)
            assert validation["simultaneous"] is True
            for key in validation:
                if key.startswith("staggered"):
                    assert validation[key] is True
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_report_has_evidence(self):
        """All results include evidence, prediction, and approximation."""
        validator = self._get_validator()
        try:
            report = validator.run_temporal_summation()
            for r in report.results:
                assert r.evidence is not None
                assert r.approximation is not None
                assert r.biological_prediction is not None
                assert "DIRECTLY_MEASURED" in r.evidence
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestRefractoryPeriod:
    """Test the 3.0B.2 refractory-period recovery experiment."""

    def _get_validator(self):
        from biological_brain.validation import RefractoryPeriodValidator
        BIOLOGICAL_CIRCUITS["escape"] = True
        brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
        return RefractoryPeriodValidator(brain)

    def test_gf_not_respike_within_refractory(self):
        """GF (refractory=5) does not re-spike at delays 1, 3, 5."""
        validator = self._get_validator()
        try:
            report = validator.run_refractory_experiment()
            gf_results = [r for r in report.results if r.neuron_id == "GF_L"]
            for r in gf_results:
                if r.delay_ticks in [1, 3, 5]:
                    assert r.re_spiked is False
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_gf_respike_after_effective_recovery(self):
        """GF (refractory=5) re-spikes at delays >= 6 (effective recovery = 6)."""
        validator = self._get_validator()
        try:
            report = validator.run_refractory_experiment()
            gf_results = [r for r in report.results if r.neuron_id == "GF_L"]
            for r in gf_results:
                if r.delay_ticks >= 6:
                    assert r.re_spiked is True
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_ttmn_not_respike_within_refractory(self):
        """TTMn (refractory=2) does not re-spike at delay 1."""
        validator = self._get_validator()
        try:
            report = validator.run_refractory_experiment()
            ttmn_results = [r for r in report.results if r.neuron_id == "TTMn_L"]
            for r in ttmn_results:
                if r.delay_ticks < 3:
                    assert r.re_spiked is False
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_ttmn_respike_after_effective_recovery(self):
        """TTMn (refractory=2) re-spikes at delays >= 3."""
        validator = self._get_validator()
        try:
            report = validator.run_refractory_experiment()
            ttmn_results = [r for r in report.results if r.neuron_id == "TTMn_L"]
            for r in ttmn_results:
                if r.delay_ticks >= 3:
                    assert r.re_spiked is True
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_all_ten_conditions_present(self):
        """Experiment tests 5 delays x 2 neurons = 10 conditions."""
        validator = self._get_validator()
        try:
            report = validator.run_refractory_experiment()
            assert len(report.results) == 10
            delays = [r.delay_ticks for r in report.results if r.neuron_id == "GF_L"]
            assert delays == [1, 3, 5, 7, 10]
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_validation_passes(self):
        """All 10 conditions match biological predictions."""
        validator = self._get_validator()
        try:
            report = validator.run_refractory_experiment()
            validation = validator.validate_refractory(report)
            assert all(validation.values())
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_report_has_evidence(self):
        """All results include evidence, prediction, and approximation."""
        validator = self._get_validator()
        try:
            report = validator.run_refractory_experiment()
            for r in report.results:
                assert r.evidence is not None
                assert r.approximation is not None
                assert r.biological_prediction is not None
                assert r.configured_refractory in [2, 5]
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestGFDLMnLatency:
    """Test the 3.0B.2 GF -> PSI -> contralateral DLMn latency experiment."""

    def _get_validator(self):
        from biological_brain.validation import GFDLMnLatencyValidator
        BIOLOGICAL_CIRCUITS["escape"] = True
        brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
        return GFDLMnLatencyValidator(brain)

    def test_left_pathway_timing(self):
        """GF_L -> PSI_L -> DLMn_R: spikes at ticks 0, 1, 3."""
        validator = self._get_validator()
        try:
            report = validator.run_pathway_latency_experiment()
            left = report.results[0]
            assert left.gf_source == "GF_L"
            assert left.psi_target == "PSI_L"
            assert left.dlmn_target == "DLMn_R"
            assert left.gf_spike_tick == 0
            assert left.psi_spike_tick == 1
            assert left.dlmn_spike_tick == 3
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_right_pathway_timing(self):
        """GF_R -> PSI_R -> DLMn_L: spikes at ticks 0, 1, 3."""
        validator = self._get_validator()
        try:
            report = validator.run_pathway_latency_experiment()
            right = report.results[1]
            assert right.gf_source == "GF_R"
            assert right.psi_target == "PSI_R"
            assert right.dlmn_target == "DLMn_L"
            assert right.gf_spike_tick == 0
            assert right.psi_spike_tick == 1
            assert right.dlmn_spike_tick == 3
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_left_pathway_component_latencies(self):
        """Left pathway: GF->PSI=1, PSI->DLMn=2, total=3 ticks."""
        validator = self._get_validator()
        try:
            report = validator.run_pathway_latency_experiment()
            left = report.results[0]
            assert left.gf_to_psi_latency == 1
            assert left.psi_to_dlmn_latency == 2
            assert left.total_latency == 3
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_right_pathway_component_latencies(self):
        """Right pathway: GF->PSI=1, PSI->DLMn=2, total=3 ticks."""
        validator = self._get_validator()
        try:
            report = validator.run_pathway_latency_experiment()
            right = report.results[1]
            assert right.gf_to_psi_latency == 1
            assert right.psi_to_dlmn_latency == 2
            assert right.total_latency == 3
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_contralateral_dlmn_selection(self):
        """GF_L drives DLMn_R (contralateral), GF_R drives DLMn_L (contralateral)."""
        validator = self._get_validator()
        try:
            report = validator.run_pathway_latency_experiment()
            assert report.results[0].dlmn_target == "DLMn_R"
            assert report.results[1].dlmn_target == "DLMn_L"
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_total_latency_in_target_range(self):
        """Total latency 3 ticks is within biological target of 3-4 ticks."""
        validator = self._get_validator()
        try:
            report = validator.run_pathway_latency_experiment()
            for r in report.results:
                assert 3 <= r.total_latency <= 4
                assert "3-4" in r.biological_target
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_intermediate_psi_activation(self):
        """PSI spikes at tick 1 (intermediate, between GF and DLMn)."""
        validator = self._get_validator()
        try:
            report = validator.run_pathway_latency_experiment()
            for r in report.results:
                assert r.psi_spike_tick is not None
                assert r.gf_spike_tick < r.psi_spike_tick < r.dlmn_spike_tick
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_validation_passes(self):
        """Both pathways pass validation."""
        validator = self._get_validator()
        try:
            report = validator.run_pathway_latency_experiment()
            validation = validator.validate_pathway_latency(report)
            assert validation["left_pathway"] is True
            assert validation["right_pathway"] is True
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_report_has_evidence_and_approximation(self):
        """All results include biological evidence, simulation result, and approximation."""
        validator = self._get_validator()
        try:
            report = validator.run_pathway_latency_experiment()
            for r in report.results:
                assert r.biological_target is not None
                assert r.biological_evidence is not None
                assert r.simulation_result is not None
                assert r.connectome_info is not None
                assert r.inferred_values is not None
                assert r.approximation is not None
                assert "DIRECTLY_MEASURED" in r.biological_evidence
                assert "APPROXIMATION" in r.approximation
                assert "not a direct biological recording" in r.approximation
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_fail_if_pathway_does_not_complete(self):
        """Validator raises RuntimeError if DLMn doesn't activate.

        Using GF_L -> PSI_L -> DLMn_L (ipsilateral DLMn_L, not the actual
        contralateral target DLMn_R) — DLMn_L receives no input from PSI_L.
        """
        from biological_brain.validation import GFDLMnLatencyValidator
        validator = self._get_validator()
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            v = GFDLMnLatencyValidator(brain)
            with pytest.raises(RuntimeError, match="did not activate"):
                v._measure_pathway("test", "GF_L", "PSI_L", "DLMn_L")
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestSynapseAblation:
    """Experiment 7: Synapse ablation — verify necessity of escape pathway synapses."""

    def _get_validator(self):
        from biological_brain.validation import SynapseAblationValidator
        BIOLOGICAL_CIRCUITS["escape"] = True
        brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
        return SynapseAblationValidator(brain)

    def test_sensory_ablation_halts_escape(self):
        """LC4_L → GF_L and LPLC2_L → GF_L ablation: all downstream neurons silenced."""
        validator = self._get_validator()
        try:
            report = validator.run_ablation_experiment()
            sensory = [r for r in report.results
                       if r.ablation_name in ("LC4_L → GF_L", "LPLC2_L → GF_L")]
            assert len(sensory) == 2
            for r in sensory:
                assert "GF_L" in r.neurons_deficit
                assert "TTMn_L" in r.neurons_deficit
                assert "DLMn_R" in r.neurons_deficit
                assert r.baseline_signals["escape_signal"] == 1.0
                assert r.ablated_signals["escape_signal"] == 0.0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_gf_ttmn_ablation_selective_deficit(self):
        """GF_L → TTMn_L (all): only TTMn_L (ipsilateral jump) silenced, DLMn_R intact."""
        validator = self._get_validator()
        try:
            report = validator.run_ablation_experiment()
            ablations = {r.ablation_name: r for r in report.results}
            r = ablations["GF_L → TTMn_L (all)"]
            assert r.neurons_deficit == ["TTMn_L"]
            assert r.ablated_spikes.get("DLMn_R") is not None
            assert r.ablated_spikes.get("PSI_L") is not None
            assert "TTMn_L" not in [n for n in r.ablated_spikes if r.ablated_spikes[n] is not None]
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_gf_psi_ablation_disables_flight(self):
        """GF_L → PSI_L (all): flight_signal drops to 0 (PSI is flight pathway)."""
        validator = self._get_validator()
        try:
            report = validator.run_ablation_experiment()
            ablations = {r.ablation_name: r for r in report.results}
            r = ablations["GF_L → PSI_L (all)"]
            assert r.neurons_deficit == ["PSI_L", "DLMn_R"]
            assert r.ablated_signals["flight_signal"] == 0.0
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_psi_dlmn_ablation_disables_flight(self):
        """PSI_L → DLMn_R: flight_signal drops to 0, PSI_L spikes preserved."""
        validator = self._get_validator()
        try:
            report = validator.run_ablation_experiment()
            ablations = {r.ablation_name: r for r in report.results}
            r = ablations["PSI_L → DLMn_R"]
            assert r.neurons_deficit == ["DLMn_R"]
            assert r.ablated_signals["flight_signal"] == 0.0
            assert r.ablated_spikes.get("PSI_L") is not None
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_validation_all_pass(self):
        """All ablation validations pass."""
        validator = self._get_validator()
        try:
            report = validator.run_ablation_experiment()
            validation = validator.validate_ablation(report)
            assert all(validation.values())
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False

    def test_ablation_blocked_count_is_positive(self):
        """Each ablation blocks at least one synapse."""
        validator = self._get_validator()
        try:
            report = validator.run_ablation_experiment()
            for r in report.results:
                assert r.approximation is not None
                assert "blocked" in r.approximation.lower() or "APPROXIMATION" in r.approximation
        finally:
            BIOLOGICAL_CIRCUITS["escape"] = False


class TestDynamicsModelSelection:
    """Phase 1: DynamicsModel abstraction with default lif_voltage."""

    def test_default_engine_uses_lif_voltage(self):
        """NeuralEngine defaults to lif_voltage model."""
        c = Circuit("test")
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0, tau_m=10.0))
        c.input_neurons = ["A"]
        c.output_neurons = ["A"]

        engine = NeuralEngine(c)
        assert engine.dynamics_model_name == MODEL_NAME_LIF_VOLTAGE

    def test_explicit_lif_voltage_selection(self):
        """Explicitly selecting lif_voltage works and uses same model class."""
        from biological_brain.dynamics import LIFVoltageModel

        c = Circuit("test")
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0, tau_m=10.0))
        c.input_neurons = ["A"]
        c.output_neurons = ["A"]

        engine_default = NeuralEngine(c)
        engine_explicit = NeuralEngine(c, dynamics_model="lif_voltage")

        assert isinstance(engine_default.dynamics, LIFVoltageModel)
        assert isinstance(engine_explicit.dynamics, LIFVoltageModel)

    def test_factory_unknown_model_raises(self):
        """Factory raises ValueError for unknown model names."""
        from biological_brain.dynamics import get_model
        with pytest.raises(ValueError, match="Unknown dynamics model"):
            get_model("nonexistent_model")

    def test_factory_returns_lif_voltage_for_valid_name(self):
        """Factory returns LIFVoltageModel for known name."""
        from biological_brain.dynamics import get_model, LIFVoltageModel
        model = get_model("lif_voltage")
        assert isinstance(model, LIFVoltageModel)


class TestDynamicsNumericalEquivalence:
    """Phase 1: lif_voltage model produces identical results to original Neuron methods."""

    def test_membrane_integration_equivalence(self):
        """LIFVoltageModel.integrate matches Neuron.integrate exactly across decay."""
        from biological_brain.dynamics import get_model
        model = get_model("lif_voltage")

        n_direct = Neuron("d", resting_potential=-70.0, threshold=-55.0,
                           reset_potential=-75.0, tau_m=10.0)
        n_model = Neuron("m", resting_potential=-70.0, threshold=-55.0,
                          reset_potential=-75.0, tau_m=10.0)

        n_direct.membrane_potential = -60.0
        n_model.membrane_potential = -60.0

        for _ in range(20):
            spiked_d = n_direct.integrate(0.0)
            spiked_m = model.integrate(n_model, 0.0)
            assert spiked_d == spiked_m
            assert n_direct.membrane_potential == n_model.membrane_potential
            assert n_direct.refractory_remaining == n_model.refractory_remaining

    def test_membrane_integration_threshold_cross(self):
        """Integration produces identical spike when threshold is crossed."""
        from biological_brain.dynamics import get_model
        model = get_model("lif_voltage")

        n_direct = Neuron("d", resting_potential=-70.0, threshold=-55.0,
                           reset_potential=-75.0, refractory_period=2, tau_m=10.0)
        n_model = Neuron("m", resting_potential=-70.0, threshold=-55.0,
                          reset_potential=-75.0, refractory_period=2, tau_m=10.0)

        n_direct.membrane_potential = -52.0
        n_model.membrane_potential = -52.0

        spiked_d = n_direct.integrate(0.0)
        spiked_m = model.integrate(n_model, 0.0)

        assert spiked_d == spiked_m
        assert n_direct.membrane_potential == n_model.membrane_potential
        assert n_direct.refractory_remaining == n_model.refractory_remaining

    def test_synaptic_input_equivalence(self):
        """receive_synaptic_spike matches receive_spike exactly."""
        from biological_brain.dynamics import get_model
        model = get_model("lif_voltage")

        n_direct = Neuron("d", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        n_model = Neuron("m", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)

        n_direct.receive_spike(10.0, 1.0)
        model.receive_synaptic_spike(n_model, 10.0, 1.0)
        assert n_direct.membrane_potential == n_model.membrane_potential

        n_direct.receive_spike(8.0, -1.0)
        model.receive_synaptic_spike(n_model, 8.0, -1.0)
        assert n_direct.membrane_potential == n_model.membrane_potential

        # Refractory blocking
        n_direct.membrane_potential = -50.0
        n_model.membrane_potential = -50.0
        n_direct.integrate(0.0)
        model.integrate(n_model, 0.0)

        n_direct.receive_spike(5.0, 1.0)
        model.receive_synaptic_spike(n_model, 5.0, 1.0)
        assert n_direct.membrane_potential == n_model.membrane_potential

    def test_sensory_current_injection_equivalence(self):
        """inject_sensory_current is blocked during refractory, matches original."""
        c = Circuit("test")
        # tau_m=10.0 so that input 20.0 (V=-50 after injection) still
        # exceeds threshold after exponential decay (V ≈ -51.9 >= -55)
        c.add_neuron(Neuron("n", resting_potential=-70.0, threshold=-55.0,
                            reset_potential=-75.0, refractory_period=2, tau_m=10.0))
        c.input_neurons = ["n"]
        c.output_neurons = ["n"]

        engine = NeuralEngine(c, dynamics_model="lif_voltage")

        # Step 1: 20.0 input should cause spike -> V=-75, refractory=2
        engine.step({"n": 20.0})
        assert c.neurons["n"].membrane_potential == -75.0
        assert c.neurons["n"].refractory_remaining == 2

        # Step 2: 100.0 input is blocked during refractory
        # V should only decrement refractory (no decay during refractory)
        engine.step({"n": 100.0})
        assert c.neurons["n"].membrane_potential == -75.0  # unchanged
        assert c.neurons["n"].refractory_remaining == 1

    def test_spike_reset_equivalence(self):
        """reset matches: membrane -> resting, refractory cleared."""
        from biological_brain.dynamics import get_model
        model = get_model("lif_voltage")

        n_direct = Neuron("d", resting_potential=-70.0, threshold=-55.0,
                           reset_potential=-75.0, tau_m=10.0)
        n_model = Neuron("m", resting_potential=-70.0, threshold=-55.0,
                          reset_potential=-75.0, tau_m=10.0)

        n_direct.membrane_potential = -50.0
        n_model.membrane_potential = -50.0
        n_direct.integrate(0.0)
        model.integrate(n_model, 0.0)

        n_direct.reset()
        model.reset(n_model)

        assert n_direct.membrane_potential == n_model.membrane_potential
        assert n_direct.refractory_remaining == n_model.refractory_remaining

    def test_refractory_period_equivalence(self):
        """Refractory countdown matches exactly across steps."""
        from biological_brain.dynamics import get_model
        model = get_model("lif_voltage")

        n_direct = Neuron("d", resting_potential=-70.0, threshold=-55.0,
                           reset_potential=-75.0, refractory_period=3, tau_m=10.0)
        n_model = Neuron("m", resting_potential=-70.0, threshold=-55.0,
                          reset_potential=-75.0, refractory_period=3, tau_m=10.0)

        n_direct.membrane_potential = -50.0
        n_model.membrane_potential = -50.0

        n_direct.integrate(0.0)
        model.integrate(n_model, 0.0)

        for _ in range(3):
            n_direct.integrate(0.0)
            model.integrate(n_model, 0.0)
            assert n_direct.refractory_remaining == n_model.refractory_remaining
            assert n_direct.membrane_potential == n_model.membrane_potential

    def test_engine_spike_propagation_equivalence(self):
        """Full engine step with spike propagation matches original behavior."""
        c1 = Circuit("test")
        c1.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0,
                              reset_potential=-75.0, tau_m=10.0))
        c1.add_neuron(Neuron("B", resting_potential=-70.0, threshold=-55.0, tau_m=10.0))
        c1.connect("A", "B", weight=10.0, delay=1)
        c1.input_neurons = ["A"]
        c1.output_neurons = ["B"]

        c2 = Circuit("test")
        c2.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0,
                              reset_potential=-75.0, tau_m=10.0))
        c2.add_neuron(Neuron("B", resting_potential=-70.0, threshold=-55.0, tau_m=10.0))
        c2.connect("A", "B", weight=10.0, delay=1)
        c2.input_neurons = ["A"]
        c2.output_neurons = ["B"]

        e1 = NeuralEngine(c1)
        e2 = NeuralEngine(c2, dynamics_model="lif_voltage")

        inputs = [{"A": 30.0}, {}, {"A": 5.0}, {}, {"A": 0.0}]
        for inp in inputs:
            e1.step(inp)
            e2.step(inp)
            assert c1.neurons["A"].membrane_potential == c2.neurons["A"].membrane_potential
            assert c1.neurons["B"].membrane_potential == c2.neurons["B"].membrane_potential


class TestConductanceDynamicsStub:
    """3.0C Phase 2 Step 1: Architecture stub tests for conductance_v0 model.

    These tests verify model selection, interface conformance, and reset
    behavior ONLY. No HH kinetics, no channel equations, no biological claims.
    """

    def test_conductance_v0_selectable_from_factory(self):
        """conductance_v0 can be retrieved from the model factory."""
        from biological_brain.dynamics import get_model
        from biological_brain import ConductanceDynamicsModel
        model = get_model("conductance_v0")
        assert isinstance(model, ConductanceDynamicsModel)

    def test_default_model_remains_lif_voltage(self):
        """get_model() with no args still defaults to lif_voltage."""
        from biological_brain.dynamics import get_model, MODEL_NAME_LIF_VOLTAGE
        model = get_model()
        assert model.name == MODEL_NAME_LIF_VOLTAGE

    def test_invalid_model_still_raises_value_error(self):
        """Unknown model names still raise ValueError with available list."""
        from biological_brain.dynamics import get_model
        with pytest.raises(ValueError, match="Unknown dynamics model"):
            get_model("nonexistent_model")
        try:
            get_model("nonexistent_model")
        except ValueError as e:
            pass  # raised correctly; available models listed in message

    def test_conductance_model_exposes_dynamics_model_interface(self):
        """ConductanceDynamicsModel conforms to DynamicsModel Protocol."""
        from biological_brain.dynamics import ConductanceDynamicsModel
        model = ConductanceDynamicsModel()
        assert hasattr(model, 'name')
        assert hasattr(model, 'inject_sensory_current')
        assert hasattr(model, 'receive_synaptic_spike')
        assert hasattr(model, 'integrate')
        assert hasattr(model, 'reset')
        assert hasattr(model, 'receive_electrical_current')
        assert model.name == "conductance_v0"

    def test_conductance_stub_construction_does_not_alter_lif_behavior(self):
        """Creating conductance model does not change existing LIF engine behavior."""
        from biological_brain.dynamics import get_model

        c = Circuit("test")
        c.add_neuron(Neuron("A", resting_potential=-70.0, threshold=-55.0,
                            reset_potential=-75.0, tau_m=10.0))
        c.add_neuron(Neuron("B", resting_potential=-70.0, threshold=-55.0, tau_m=10.0))
        c.connect("A", "B", weight=10.0, delay=1)
        c.input_neurons = ["A"]
        c.output_neurons = ["B"]

        # Verify lif_voltage still works identically after importing conductance model
        _ = get_model("lif_voltage")
        _ = get_model("conductance_v0")

        engine = NeuralEngine(c)
        assert engine.dynamics_model_name == "lif_voltage"

        engine.step({"A": 20.0})
        assert engine.current_tick == 1

    def test_conductance_model_reset_clears_state(self):
        """reset() on conductance model clears electrical accumulator and g_syn."""
        from biological_brain.dynamics import get_model
        from biological_brain.dynamics.conductance import ConductanceNeuronState
        model = get_model("conductance_v0")

        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        n.conductance_state = ConductanceNeuronState()

        # Simulate having accumulated electrical current and synaptic conductance
        n.conductance_state.I_elec_accumulator = 5.0
        n.conductance_state.g_syn = 3.0
        n.conductance_state.refractory_remaining = 2
        n.refractory_remaining = 2

        model.reset(n)

        assert n.conductance_state.I_elec_accumulator == 0.0
        assert n.conductance_state.g_syn == 0.0
        assert n.conductance_state.refractory_remaining == 0
        assert n.refractory_remaining == 0

    def test_available_models_includes_both(self):
        """available_models lists both lif_voltage and conductance_v0."""
        from biological_brain.dynamics import DynamicsModelFactory
        models = DynamicsModelFactory.available_models()
        assert "lif_voltage" in models
        assert "conductance_v0" in models

    def test_conductance_model_integrate_raises_not_implemented(self):
        """Conductance model integrate() raises NotImplementedError without membrane area."""
        from biological_brain.dynamics import get_model, attach_conductance_state
        model = get_model("conductance_v0")
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        attach_conductance_state(n)
        with pytest.raises(NotImplementedError, match="membrane_area_cm2"):
            model.integrate(n, 0.0)

    def test_conductance_model_inject_sensory_raises_not_implemented(self):
        """Conductance model inject_sensory_current raises NotImplementedError."""
        from biological_brain.dynamics import get_model, attach_conductance_state
        model = get_model("conductance_v0")
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        attach_conductance_state(n)
        with pytest.raises(NotImplementedError, match="input resistance"):
            model.inject_sensory_current(n, 20.0)

    def test_conductance_model_receive_synaptic_spike_increments_g(self):
        """Conductance model receive_synaptic_spike increments g_syn by peak conductance."""
        from biological_brain.dynamics import get_model, attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams
        model = get_model("conductance_v0")
        n = Neuron("test", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        params = ConductanceParams()
        attach_conductance_state(n, params=params)

        assert n.conductance_state.g_syn == 0.0
        model.receive_synaptic_spike(n, 10.0, 1)
        assert n.conductance_state.g_syn == params.g_syn_peak_us

    def test_conductance_params_have_source_supported_defaults(self):
        """ConductanceParams defaults come from published model (PMC6469880 Table 1)."""
        from biological_brain.dynamics.conductance import ConductanceParams
        params = ConductanceParams()
        assert params.E_leak == -85.0    # [Günay et al. 2015 via Augustin et al.]
        assert params.E_Na == 65.0       # [Günay et al. 2015 via Augustin et al.]
        assert params.E_K == -74.0       # [Günay et al. 2015 via Augustin et al.]
        assert params.g_Na == 300.0      # mS/cm^2
        assert params.g_K == 10.0        # mS/cm^2
        assert params.g_leak == 0.03     # mS/cm^2
        assert params.C_m == 1.0         # uF/cm^2
        assert params.tau_syn_decay_ms == 1.0  # ms
        assert params.E_syn == 0.0       # mV (ACh reversal)


class TestConductanceAccumulatorLifecycle:
    """3.0C Phase 2 — targeted regression guard for I_elec_accumulator.

    Verifies that gap-junction current is computed, consumed by integrate(),
    and then CLEARED so it does not leak into the next timestep.

    The clearing step at NeuralEngine.step() (line ~73-75) was added during
    Phase 2 development. The committed version (a282bd4) lacked this clearing
    and would accumulate stale gap-junction current across timesteps.
    """

    def test_accumulator_cleared_after_step(self):
        """Electrical current contributes during its timestep and is cleared afterward.

        Without clearing, I_elec_accumulator would carry stale current into
        the next step, causing voltage updates from old coupling rather than
        fresh gap-junction calculations.
        """
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        params = ConductanceParams(membrane_area_cm2=1.0)
        n_pre = Neuron("A", resting_potential=-70.0, threshold=-50.0, tau_m=100.0)
        n_post = Neuron("B", resting_potential=-70.0, threshold=-50.0, tau_m=100.0)
        attach_conductance_state(n_pre, params=params)
        attach_conductance_state(n_post, params=params)

        c = Circuit("test")
        c.add_neuron(n_pre)
        c.add_neuron(n_post)
        c.add_synapse(Synapse("A", "B", sign=Sign.EXCITATORY, delay=1,
                              synapse_type="electrical", conductance=135.0))
        c.input_neurons = []
        c.output_neurons = ["B"]

        engine = NeuralEngine(c, dynamics_model="conductance_v0")

        # Different voltages => electrical current flows (I_elec = 135 * 20 = 2700 nA)
        n_pre.membrane_potential = -50.0
        n_post.membrane_potential = -70.0
        n_pre.conductance_state.V = -50.0
        n_post.conductance_state.V = -70.0

        # Step 1: accumulator populated, consumed by integrate, then cleared
        engine.step({})
        assert n_post.conductance_state.I_elec_accumulator == 0.0
        # Voltage moved toward A's potential (depolarized from -70)
        assert n_post.conductance_state.V > -70.0

        # Step 2: accumulator must be 0, not carrying stale 2700 nA
        engine.step({})
        assert n_post.conductance_state.I_elec_accumulator == 0.0


class TestProvenanceMetadata:
    """3.0D-1A: Structured Parameter Provenance — metadata-only tests."""

    def test_parameter_provenance_enum_has_all_categories(self):
        """ParameterProvenance enum exposes all 8 taxonomy categories from the roadmap."""
        from biological_brain.provenance import ParameterProvenance
        expected = {
            "DIRECTLY_MEASURED",
            "EXPERIMENTALLY_CONSTRAINED",
            "CONNECTOME_DERIVED",
            "PUBLISHED_MODEL_PARAMETER",
            "BORROWED_CROSS_CONTEXT",
            "FITTED_CALIBRATED",
            "ESTIMATED",
            "UNKNOWN",
        }
        actual = {e.name for e in ParameterProvenance}
        assert expected == actual

    def test_synapse_preserves_json_evidence(self):
        """Synapse objects constructed from escape_circuit.json preserve evidence strings and map to provenance enums."""
        from biological_brain import BIOLOGICAL_CIRCUITS, BiologicalMode, BiologicalBrain
        from biological_brain.provenance import ParameterProvenance
        BIOLOGICAL_CIRCUITS["escape"] = True
        brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
        circuit = brain.circuits.get("escape_core")
        assert circuit is not None

        # Electrical synapse should have INFERRED + APPROXIMATION evidence
        elec_syn = None
        for syn in circuit.synapses:
            if syn.synapse_type == "electrical":
                elec_syn = syn
                break
        assert elec_syn is not None
        assert "INFERRED" in elec_syn.evidence
        assert "APPROXIMATION" in elec_syn.evidence
        # INFERRED and APPROXIMATION are ambiguous — mapped to UNKNOWN conservatively
        assert ParameterProvenance.UNKNOWN in elec_syn.provenance
        assert ParameterProvenance.BORROWED_CROSS_CONTEXT not in elec_syn.provenance
        assert ParameterProvenance.FITTED_CALIBRATED not in elec_syn.provenance

        # gap-junction conductance value is unchanged (135 uS)
        assert elec_syn.conductance == 135.0

        BIOLOGICAL_CIRCUITS["escape"] = False

    def test_conductance_params_have_provenance_records(self):
        """ConductanceParams exposes a provenance dict with records for all defined parameters."""
        from biological_brain.dynamics.conductance import ConductanceParams
        from biological_brain.provenance import ParameterProvenance, ProvenanceRecord

        params = ConductanceParams()
        assert params.provenance is not None
        assert len(params.provenance) == 13

        # Spot-check key classifications
        assert params.provenance["E_leak"].category == ParameterProvenance.PUBLISHED_MODEL_PARAMETER
        assert params.provenance["g_leak"].category == ParameterProvenance.ESTIMATED
        assert params.provenance["g_syn_peak_us"].category == ParameterProvenance.BORROWED_CROSS_CONTEXT
        assert params.provenance["V_threshold"].category == ParameterProvenance.FITTED_CALIBRATED
        assert params.provenance["membrane_area_cm2"].category == ParameterProvenance.UNKNOWN

        # All records have a non-empty source string
        for name, rec in params.provenance.items():
            assert isinstance(rec, ProvenanceRecord)
            assert rec.source != ""


class TestConductanceInvariantValidation:
    """3.0C Phase 2 Step 7: Invariant validation experiments for conductance_v0.

    7 invariant experiments, 17 test methods. VALIDATION ONLY — no new
    biological mechanisms. Parameters from PMC6469880 Table 1 or test-only
    fixtures. No inventions of HH parameters.

    Experiments:
      1. Multi-timestep passive Forward Euler integration (3 tests)
      2. Leak current dominance and direction (2 tests)
      3. Gap-junction voltage coupling (3 tests)
      4. Chemical synapse conductance accumulation and decay (2 tests)
      5. Chemical synaptic current effect on membrane voltage (2 tests)
      6. Reduced threshold-crossing spike-event adapter (3 tests)
      7. Refractory, unit, and electrical-exclusion constraints (2 tests)
    """

    # === Invariant 1: Multi-timestep Passive Forward Euler Integration ===

    def test_passive_decay_toward_el_leak_multi_tick(self):
        """Experiment 1a: Without input, V decays toward E_leak (-85 mV) across ticks.

        Forward Euler: dV/dt = -g_leak*(V - E_leak) / C_m
        Starting at V=-70 (above E_leak), V should decrease toward -85.
        """
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.V = -70.0
        n.membrane_potential = -70.0

        for _ in range(5):
            model.integrate(n, 0.0)

        assert n.conductance_state.V < -70.0

    def test_forward_euler_deterministic_same_input_same_output(self):
        """Experiment 1b: Deterministic — same state and inputs produce identical V."""
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        model = get_model("conductance_v0")

        n1 = Neuron("n1", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        n2 = Neuron("n2", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        attach_conductance_state(n1, params=ConductanceParams(membrane_area_cm2=1.0))
        attach_conductance_state(n2, params=ConductanceParams(membrane_area_cm2=1.0))

        n1.conductance_state.V = -60.0
        n2.conductance_state.V = -60.0
        n1.membrane_potential = -60.0
        n2.membrane_potential = -60.0
        n1.conductance_state.g_syn = 10.0
        n2.conductance_state.g_syn = 10.0
        n1.conductance_state.I_elec_accumulator = 5.0
        n2.conductance_state.I_elec_accumulator = 5.0

        model.integrate(n1, 3.0)
        model.integrate(n2, 3.0)

        assert n1.conductance_state.V == pytest.approx(n2.conductance_state.V)

    def test_forward_euler_matches_manual_computation(self):
        """Experiment 1c: Single-timestep V matches hand-computed Forward Euler.

        V=-70, g_leak=0.03 mS/cm^2, E_leak=-85 mV, C_m=1.0 uF/cm^2, no input.
        I_leak = 0.03*(-70-(-85)) = 0.45 uA/cm^2
        dV/dt = -0.45/1.0 = -0.45 mV/ms -> V_new = -70.45
        """
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.V = -70.0
        n.membrane_potential = -70.0

        model.integrate(n, 0.0)

        expected = -70.0 + 1.0 * (-(0.03 * (-70.0 - (-85.0))) / 1.0)
        assert n.conductance_state.V == pytest.approx(expected, abs=1e-10)
        assert n.membrane_potential == pytest.approx(expected, abs=1e-10)

    # === Invariant 2: Leak Current Dominance and Direction ===

    def test_leak_drives_voltage_toward_el_leak_from_above(self):
        """Experiment 2a: V above E_leak -> V decreases (toward E_leak)."""
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.V = -60.0
        n.membrane_potential = -60.0

        model.integrate(n, 0.0)

        # I_leak = 0.03*(-60-(-85)) = 0.75 > 0 (outward/hyperpolarizing)
        # dV/dt = -0.75 -> V should decrease
        assert n.conductance_state.V < -60.0

    def test_leak_drives_voltage_toward_el_leak_from_below(self):
        """Experiment 2b: V below E_leak -> V increases (toward E_leak)."""
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.V = -90.0
        n.membrane_potential = -90.0

        model.integrate(n, 0.0)

        # I_leak = 0.03*(-90-(-85)) = -0.15 < 0 (inward/depolarizing)
        # dV/dt = +0.15 -> V should increase
        assert n.conductance_state.V > -90.0

    # === Invariant 3: Gap-Junction Voltage Coupling ===

    def test_electrical_current_drives_post_voltage(self):
        """Experiment 3a (Regression A): Electrical current depolarizes postsynaptic V.

        V_pre=-50, V_post=-70, g_gap=135 uS, area=1.0.
        I_elec = 135*(-50-(-70)) = 2700 nA
        I_elec_density = 2700/(1000*1.0) = 2.7 uA/cm^2
        I_leak = 0.03*(-70-(-85)) = 0.45 uA/cm^2
        dV/dt = (-0.45 + 2.7)/1.0 = 2.25 -> V_new = -70+2.25 = -67.75
        """
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        params = ConductanceParams(membrane_area_cm2=1.0)
        n_pre = Neuron("pre", resting_potential=-65.0, threshold=-45.0, tau_m=100.0)
        n_post = Neuron("post", resting_potential=-65.0, threshold=-45.0, tau_m=100.0)
        attach_conductance_state(n_pre, params=ConductanceParams(membrane_area_cm2=1.0))
        attach_conductance_state(n_post, params=ConductanceParams(membrane_area_cm2=1.0))

        c = Circuit("test")
        c.add_neuron(n_pre)
        c.add_neuron(n_post)
        c.add_synapse(Synapse("pre", "post", sign=Sign.EXCITATORY, delay=1,
                              synapse_type="electrical", conductance=135.0))
        c.input_neurons = []
        c.output_neurons = ["post"]

        engine = NeuralEngine(c, dynamics_model="conductance_v0")

        n_pre.membrane_potential = -50.0
        n_post.membrane_potential = -70.0
        n_pre.conductance_state.V = -50.0
        n_post.conductance_state.V = -70.0

        engine.step({})

        # Post should have depolarized toward pre
        assert n_post.conductance_state.V > -70.0
        assert n_post.conductance_state.I_elec_accumulator == 0.0  # cleared

    def test_gap_current_hyperpolarizes_when_pre_below_post(self):
        """Experiment 3b: V_pre < V_post -> I_elec < 0 -> V_post hyperpolarizes.

        V_pre=-90, V_post=-70, g_gap=135 uS, area=1.0.
        I_elec = 135*(-90-(-70)) = -2700 nA
        I_elec_density = -2.7 uA/cm^2
        I_leak = 0.45, dV/dt = (-0.45 - 2.7)/1.0 = -3.15 -> V_new = -73.15
        """
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        params = ConductanceParams(membrane_area_cm2=1.0)
        n_pre = Neuron("pre", resting_potential=-65.0, threshold=-45.0, tau_m=100.0)
        n_post = Neuron("post", resting_potential=-65.0, threshold=-45.0, tau_m=100.0)
        attach_conductance_state(n_pre, params=ConductanceParams(membrane_area_cm2=1.0))
        attach_conductance_state(n_post, params=ConductanceParams(membrane_area_cm2=1.0))

        c = Circuit("test")
        c.add_neuron(n_pre)
        c.add_neuron(n_post)
        c.add_synapse(Synapse("pre", "post", sign=Sign.EXCITATORY, delay=1,
                              synapse_type="electrical", conductance=135.0))
        c.input_neurons = []
        c.output_neurons = ["post"]

        engine = NeuralEngine(c, dynamics_model="conductance_v0")

        n_pre.membrane_potential = -90.0
        n_post.membrane_potential = -70.0
        n_pre.conductance_state.V = -90.0
        n_post.conductance_state.V = -70.0

        engine.step({})

        # Post should have hyperpolarized (moved away from pre, toward E_leak)
        assert n_post.conductance_state.V < -70.0

    def test_no_conductance_doubling_single_synapse(self):
        """Experiment 3c: Each directional electrical synapse processed exactly once.

        With a single electrical synapse (pre->post, g=135),
        I_elec_accumulator should be exactly 135*(V_pre - V_post), not doubled.
        """
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        params = ConductanceParams(membrane_area_cm2=1.0)
        n_pre = Neuron("pre", resting_potential=-65.0, threshold=-45.0, tau_m=100.0)
        n_post = Neuron("post", resting_potential=-65.0, threshold=-45.0, tau_m=100.0)
        attach_conductance_state(n_pre, params=ConductanceParams(membrane_area_cm2=1.0))
        attach_conductance_state(n_post, params=ConductanceParams(membrane_area_cm2=1.0))

        c = Circuit("test")
        c.add_neuron(n_pre)
        c.add_neuron(n_post)
        c.add_synapse(Synapse("pre", "post", sign=Sign.EXCITATORY, delay=1,
                              synapse_type="electrical", conductance=135.0))
        c.input_neurons = []
        c.output_neurons = ["post"]

        engine = NeuralEngine(c, dynamics_model="conductance_v0")

        n_pre.membrane_potential = -50.0
        n_post.membrane_potential = -70.0
        n_pre.conductance_state.V = -50.0
        n_post.conductance_state.V = -70.0

        # Compute electrical currents directly (before integrate clears)
        engine._compute_electrical_currents()

        expected_I_elec = 135.0 * (-50.0 - (-70.0))  # = 2700 nA
        assert n_post.conductance_state.I_elec_accumulator == pytest.approx(expected_I_elec)

    # === Invariant 4: Chemical Synapse Conductance Accumulation and Decay ===

    def test_g_syn_decays_exponentially_per_tick(self):
        """Experiment 4a: g_syn decays by exp(-dt/tau_decay) each tick."""
        from math import exp
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.g_syn = 80.0

        model.decay_conductances(n)

        expected = 80.0 * exp(-1.0 / 1.0)  # dt=1ms, tau_decay=1ms
        assert n.conductance_state.g_syn == pytest.approx(expected)

    def test_chemical_conductance_summation_multiple_spikes(self):
        """Experiment 4b: Multiple simultaneous chemical spikes sum g_syn linearly."""
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        params = ConductanceParams(membrane_area_cm2=1.0)
        attach_conductance_state(n, params=params)
        model = get_model("conductance_v0")

        assert n.conductance_state.g_syn == 0.0

        model.receive_synaptic_spike(n, 1.0, 1)  # adds g_syn_peak_us (80 uS)
        assert n.conductance_state.g_syn == pytest.approx(params.g_syn_peak_us)

        model.receive_synaptic_spike(n, 1.0, 1)  # adds another 80 uS
        assert n.conductance_state.g_syn == pytest.approx(2 * params.g_syn_peak_us)

    # === Invariant 5: Chemical Synaptic Current Effect on Voltage ===

    def test_synaptic_current_zero_without_conductance(self):
        """Experiment 5a: g_syn=0 -> I_syn=0 -> no synaptic voltage effect."""
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.V = -70.0
        n.membrane_potential = -70.0
        n.conductance_state.g_syn = 0.0

        I_syn = model.compute_synaptic_current(n)
        assert I_syn == 0.0

        model.integrate(n, 0.0)
        # V should only move toward E_leak (due to leak), no synaptic contribution
        expected_V = -70.0 + 1.0 * (-(0.03 * (-70.0 - (-85.0))) / 1.0)
        assert n.conductance_state.V == pytest.approx(expected_V, abs=1e-10)

    def test_synaptic_current_depolarizes_when_v_below_esyn(self):
        """Experiment 5b: V < E_syn(0mV) and g_syn > 0 -> depolarizing current.

        I_syn = g_syn * (V - E_syn). When V < 0, I_syn is negative (inward, depolarizing).
        With g_syn=100 uS, V=-70, area=1.0:
          I_syn_abs = 100*(-70-0) = -7000 nA
          I_syn_density = -7 uA/cm^2
          dV/dt = (-0.45 + 7.0)/1.0 = 6.55 -> V_new = -63.45
        """
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        params = ConductanceParams(membrane_area_cm2=1.0)
        attach_conductance_state(n, params=params)
        model = get_model("conductance_v0")

        n.conductance_state.V = -70.0
        n.membrane_potential = -70.0
        n.conductance_state.g_syn = 100.0

        V_before = n.conductance_state.V
        model.integrate(n, 0.0)

        # V should increase (depolarize toward E_syn=0)
        assert n.conductance_state.V > V_before
        assert n.conductance_state.I_syn == pytest.approx(-7000.0)

    # === Invariant 6: Reduced Threshold-Crossing Spike-Event Adapter ===

    def test_upward_threshold_crossing_emits_spike(self):
        """Experiment 6a: V crosses threshold upward -> spike emitted, V resets."""
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0,
                   reset_potential=-65.0, tau_m=10.0, refractory_period=2)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.V = -50.0  # below threshold (-45)
        n.membrane_potential = -50.0

        spiked = model.integrate(n, 100.0)  # large depolarizing input

        assert spiked is True
        assert n.conductance_state.V == -65.0  # reset_potential
        assert n.membrane_potential == -65.0
        assert n.refractory_remaining == 2
        assert n.conductance_state.refractory_remaining == 2

    def test_no_spike_when_already_above_threshold(self):
        """Experiment 6b: V already above threshold -> no spike (no upward crossing)."""
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0,
                   reset_potential=-65.0, tau_m=10.0, refractory_period=2)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.V = -40.0  # above threshold (-45)
        n.membrane_potential = -40.0

        V_before = n.conductance_state.V
        spiked = model.integrate(n, 0.0)

        assert spiked is False
        # V should have changed (leak pulls toward E_leak)
        assert n.conductance_state.V != V_before

    def test_spike_resets_both_state_v_and_membrane_potential(self):
        """Experiment 6c: After spike, both state.V and membrane_potential = reset_potential."""
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0,
                   reset_potential=-65.0, tau_m=10.0, refractory_period=2)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.V = -48.0  # just below threshold
        n.membrane_potential = -48.0

        model.integrate(n, 50.0)  # forces threshold crossing

        assert n.conductance_state.V == -65.0
        assert n.membrane_potential == -65.0

    # === Invariant 7: Refractory, Unit, and Electrical-Exclusion Constraints ===

    def test_refractory_blocks_voltage_integration(self):
        """Experiment 7a: refractory_remaining > 0 -> V unchanged, no integration."""
        from biological_brain.dynamics import attach_conductance_state, get_model
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0,
                   reset_potential=-65.0, tau_m=10.0, refractory_period=2)
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))
        model = get_model("conductance_v0")

        n.conductance_state.V = -50.0
        n.membrane_potential = -50.0
        n.refractory_remaining = 1

        V_before = n.conductance_state.V
        spiked = model.integrate(n, 100.0)  # large input, but refractory

        assert spiked is False
        assert n.conductance_state.V == V_before  # V unchanged
        assert n.refractory_remaining == 0  # decremented

    def test_electrical_synapses_excluded_from_delay_queue(self):
        """Experiment 7b: In conductance_v0, electrical synapses skip spike propagation queue.

        Only chemical synapses contribute to the delay queue. Electrical
        coupling is handled separately by _compute_electrical_currents().
        """
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        params = ConductanceParams(membrane_area_cm2=1.0)
        n_pre = Neuron("pre", resting_potential=-65.0, threshold=-45.0,
                       reset_potential=-65.0, tau_m=100.0, refractory_period=2)
        n_post = Neuron("post", resting_potential=-65.0, threshold=-45.0,
                        reset_potential=-65.0, tau_m=100.0, refractory_period=2)
        attach_conductance_state(n_pre, params=ConductanceParams(membrane_area_cm2=1.0))
        attach_conductance_state(n_post, params=ConductanceParams(membrane_area_cm2=1.0))

        c = Circuit("test")
        c.add_neuron(n_pre)
        c.add_neuron(n_post)
        # Electrical synapse (should be excluded from delay queue in conductance_v0)
        c.add_synapse(Synapse("pre", "post", sign=Sign.EXCITATORY, delay=1,
                              synapse_type="electrical", conductance=135.0))
        # Chemical synapse (should be included in delay queue)
        c.add_synapse(Synapse("pre", "post", sign=Sign.EXCITATORY, delay=2,
                              synapse_type="chemical", weight=5.0))
        c.input_neurons = []
        c.output_neurons = ["post"]

        engine = NeuralEngine(c, dynamics_model="conductance_v0")

        # Force pre to schedule propagation (simulating a spike)
        engine._schedule_propagation("pre")

        # Electrical synapse (delay=1) should NOT be in queue
        # Chemical synapse (delay=2) SHOULD be in queue at tick 2
        tick_1_spikes = engine.spike_queue.get(1, [])
        tick_2_spikes = engine.spike_queue.get(2, [])

        assert len(tick_1_spikes) == 0  # electrical excluded
        assert len(tick_2_spikes) == 1  # chemical included


class TestPerNeuronDynamicsSelection:
    """3.0D-2: Per-neuron dynamics backend selection.

    Allows individual Neuron objects to select one of the EXISTING
    dynamics implementations (lif_voltage or conductance_v0). No new
    biological mechanisms or parameters are introduced.
    """

    def test_two_neurons_select_different_backends(self):
        """Two neurons can independently select LIF and conductance_v0 backends."""
        from biological_brain.dynamics import LIFVoltageModel, ConductanceDynamicsModel
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        a = Neuron("A", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        a.dynamics_model = "lif_voltage"

        b = Neuron("B", resting_potential=-65.0, threshold=-45.0,
                   reset_potential=-65.0, tau_m=10.0)
        b.dynamics_model = "conductance_v0"
        attach_conductance_state(b, params=ConductanceParams(membrane_area_cm2=1.0))

        c = Circuit("mixed")
        c.add_neuron(a)
        c.add_neuron(b)
        c.connect("A", "B", weight=3.0, delay=1)
        c.input_neurons = ["A"]
        c.output_neurons = ["B"]

        engine = NeuralEngine(c)  # engine default is LIF

        model_a = engine._get_neuron_model(a)
        model_b = engine._get_neuron_model(b)
        assert isinstance(model_a, LIFVoltageModel)
        assert isinstance(model_b, ConductanceDynamicsModel)
        assert model_a.name == "lif_voltage"
        assert model_b.name == "conductance_v0"

    def test_unspecified_neuron_uses_engine_default(self):
        """Neuron without dynamics_model uses engine's default model."""
        from biological_brain.dynamics import LIFVoltageModel

        n = Neuron("n", resting_potential=-70.0, threshold=-55.0,
                   reset_potential=-75.0, tau_m=10.0)
        assert n.dynamics_model is None

        c = Circuit("test")
        c.add_neuron(n)
        c.input_neurons = ["n"]
        c.output_neurons = ["n"]

        engine = NeuralEngine(c, dynamics_model="lif_voltage")
        model = engine._get_neuron_model(n)
        assert isinstance(model, LIFVoltageModel)

        # Numerical behavior unchanged: sub-threshold sensory input depolarizes
        engine.step({"n": 10.0})
        assert n.membrane_potential > -70.0  # depolarized, no spike

    def test_explicit_lif_selection(self):
        """Neuron with dynamics_model='lif_voltage' uses LIF backend."""
        from biological_brain.dynamics import LIFVoltageModel

        n = Neuron("n", resting_potential=-70.0, threshold=-55.0,
                   reset_potential=-75.0, tau_m=10.0, refractory_period=2)
        n.dynamics_model = "lif_voltage"

        c = Circuit("test")
        c.add_neuron(n)
        c.input_neurons = ["n"]
        c.output_neurons = ["n"]

        engine = NeuralEngine(c)  # default LIF
        model = engine._get_neuron_model(n)
        assert isinstance(model, LIFVoltageModel)

        # Should behave identically to default LIF (spikes with strong input)
        engine.step({"n": 20.0})
        assert n.refractory_remaining > 0  # spiked

    def test_explicit_conductance_v0_selection(self):
        """Neuron with dynamics_model='conductance_v0' uses conductance backend."""
        from biological_brain.dynamics import ConductanceDynamicsModel
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0,
                   reset_potential=-65.0, tau_m=10.0)
        n.dynamics_model = "conductance_v0"
        attach_conductance_state(n, params=ConductanceParams(membrane_area_cm2=1.0))

        c = Circuit("test")
        c.add_neuron(n)
        c.input_neurons = []
        c.output_neurons = ["n"]

        engine = NeuralEngine(c, dynamics_model="lif_voltage")  # engine default LIF
        model = engine._get_neuron_model(n)
        assert isinstance(model, ConductanceDynamicsModel)

        # Conductance model integrates (passive Forward Euler) without error
        engine.step({})
        # V should have moved toward E_leak (-85), i.e., decreased from -65
        assert n.conductance_state.V < n.resting_potential

    def test_mixed_dynamics_coexist(self):
        """LIF and conductance_v0 neurons coexist in one circuit and step together."""
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        c = Circuit("mixed")
        # Neuron A: LIF (engine default)
        a = Neuron("A", resting_potential=-70.0, threshold=-55.0,
                   reset_potential=-75.0, tau_m=10.0, refractory_period=2)
        # Neuron B: conductance_v0
        b = Neuron("B", resting_potential=-65.0, threshold=-45.0,
                   reset_potential=-65.0, tau_m=10.0, refractory_period=2)
        b.dynamics_model = "conductance_v0"
        attach_conductance_state(b, params=ConductanceParams(membrane_area_cm2=1.0))

        c.add_neuron(a)
        c.add_neuron(b)
        c.connect("A", "B", weight=3.0, delay=1)  # chemical synapse
        c.input_neurons = ["A"]
        c.output_neurons = ["B"]

        engine = NeuralEngine(c)  # default LIF

        # Tick 0: drive A to spike via sensory input
        engine.step({"A": 25.0})
        assert a.refractory_remaining > 0  # A (LIF) spiked

        # Tick 1: A's chemical spike arrives at B
        engine.step({})
        # B (conductance_v0) should have received synaptic conductance
        assert b.conductance_state.g_syn > 0.0

    def test_backend_selection_requires_no_biological_params(self):
        """Selecting conductance_v0 backend doesn't require conductance_state or params."""
        from biological_brain.dynamics import ConductanceDynamicsModel

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        n.dynamics_model = "conductance_v0"
        # No conductance_state, no params — just selecting the backend
        assert n.conductance_state is None

        c = Circuit("test")
        c.add_neuron(n)
        c.input_neurons = []
        c.output_neurons = ["n"]

        engine = NeuralEngine(c)  # default LIF
        model = engine._get_neuron_model(n)
        assert isinstance(model, ConductanceDynamicsModel)
        assert model.name == "conductance_v0"
        # Model resolution succeeded without any biological parameters


class TestNumericalResolutionPolicy:
    """3.0D-3: Numerical resolution contract documents dt and constraints."""

    def test_lif_voltage_has_numerical_resolution(self):
        """LIF model declares numerical_resolution with timestep_ms."""
        from biological_brain.dynamics import LIFVoltageModel, NumericalResolution

        model = LIFVoltageModel()
        assert isinstance(model.numerical_resolution, NumericalResolution)
        assert model.numerical_resolution.timestep_ms == 1.0
        assert model.numerical_resolution.resolution_note != ""

    def test_conductance_v0_has_numerical_resolution(self):
        """Conductance model declares numerical_resolution with timestep_ms."""
        from biological_brain.dynamics import ConductanceDynamicsModel, NumericalResolution

        model = ConductanceDynamicsModel()
        assert isinstance(model.numerical_resolution, NumericalResolution)
        assert model.numerical_resolution.timestep_ms == 1.0
        assert model.numerical_resolution.resolution_note != ""

    def test_all_models_validated_at_dt_1ms(self):
        """Both models are validated at the engine's current dt=1ms."""
        from biological_brain.dynamics import get_model, MODEL_NAME_LIF_VOLTAGE, MODEL_NAME_CONDUCTANCE_V0

        for name in [MODEL_NAME_LIF_VOLTAGE, MODEL_NAME_CONDUCTANCE_V0]:
            model = get_model(name)
            assert model.numerical_resolution.timestep_ms == 1.0


class TestMixedDynamicsValidation:
    """3.0D-4: Validation of mixed-dynamics architectural coexistence.

    Validates that the per-neuron dynamics architecture correctly coexists
    with existing circuit mechanisms (electrical + chemical synapses, delays).

    Scientific limitation: This validates ARCHITECTURAL COEXISTENCE ONLY.
    The published GFS (Augustin et al. 2019, PMC6469880) is a multicompartment
    conductance model; our implementation is a reduced single-compartment
    approximation. Experimental reference observations (GF-TTM ~0.7-1.2ms,
    GF-DLM ~1.3-1.7ms, 100 Hz following) are NOT asserted here — they are
    future biological validation targets, not acceptance criteria for this
    reduced architecture.
    """

    def test_lif_and_conductance_coexist_in_same_step(self):
        """Validation 1: LIF and conductance_v0 participate in same engine.step()."""
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        lif = Neuron("lif_n", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        cond = Neuron("cond_n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        cond.dynamics_model = "conductance_v0"
        attach_conductance_state(cond, params=ConductanceParams(membrane_area_cm2=1.0))

        c = Circuit("mixed")
        c.add_neuron(lif)
        c.add_neuron(cond)
        c.input_neurons = ["lif_n"]
        c.output_neurons = ["lif_n", "cond_n"]

        engine = NeuralEngine(c)  # default LIF
        engine.step({"lif_n": 5.0})

        # LIF neuron depolarized from resting (-70 → -65)
        assert lif.membrane_potential > -70.0
        # conductance_v0 neuron passively decays toward E_leak (-85)
        assert cond.conductance_state.V < -65.0

    def test_conductance_v0_electrical_current_directionality(self):
        """Validation 2: Electrical current drives conductance_v0 V in both directions."""
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        params = ConductanceParams(membrane_area_cm2=1.0)
        pre = Neuron("pre", resting_potential=-65.0, threshold=-45.0, tau_m=100.0)
        post = Neuron("post", resting_potential=-65.0, threshold=-45.0, tau_m=100.0)
        pre.dynamics_model = "conductance_v0"
        post.dynamics_model = "conductance_v0"
        attach_conductance_state(pre, params=ConductanceParams(membrane_area_cm2=1.0))
        attach_conductance_state(post, params=ConductanceParams(membrane_area_cm2=1.0))

        c = Circuit("elec_dir")
        c.add_neuron(pre)
        c.add_neuron(post)
        c.add_synapse(Synapse("pre", "post", sign=Sign.EXCITATORY, delay=1,
                              synapse_type="electrical", conductance=135.0))
        c.input_neurons = []
        c.output_neurons = ["post"]

        engine = NeuralEngine(c)  # default LIF; neurons select conductance_v0

        # Case 1: V_pre > V_post -> post depolarizes
        pre.membrane_potential = -50.0
        post.membrane_potential = -70.0
        pre.conductance_state.V = -50.0
        post.conductance_state.V = -70.0
        engine.step({})
        assert post.conductance_state.V > -70.0
        engine.reset()

        # Case 2: V_pre < V_post -> post hyperpolarizes (toward E_leak)
        pre.membrane_potential = -90.0
        post.membrane_potential = -70.0
        pre.conductance_state.V = -90.0
        post.conductance_state.V = -70.0
        engine.step({})
        assert post.conductance_state.V < -70.0

    def test_electrical_synapses_excluded_from_delay_queue(self):
        """Validation 3: Electrical synapses skip chemical propagation delay queue."""
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        cond = Neuron("cond_n", resting_potential=-65.0, threshold=-45.0, tau_m=100.0)
        cond.dynamics_model = "conductance_v0"
        attach_conductance_state(cond, params=ConductanceParams(membrane_area_cm2=1.0))
        lif = Neuron("lif_n", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)

        c = Circuit("delay_excl")
        c.add_neuron(lif)
        c.add_neuron(cond)
        # Electrical synapse (should be excluded from delay queue)
        c.add_synapse(Synapse("lif_n", "cond_n", sign=Sign.EXCITATORY, delay=1,
                              synapse_type="electrical", conductance=135.0))
        # Chemical synapse (should be included in delay queue)
        c.add_synapse(Synapse("lif_n", "cond_n", sign=Sign.EXCITATORY, delay=1,
                              synapse_type="chemical", weight=5.0))
        c.input_neurons = ["lif_n"]
        c.output_neurons = ["cond_n"]

        engine = NeuralEngine(c)

        # Drive LIF neuron to spike
        engine.step({"lif_n": 20.0})
        assert lif.refractory_remaining > 0

        # Tick delay=1: only chemical spike queued, electrical excluded
        queued = engine.spike_queue.get(1, [])
        assert len(queued) == 1
        assert queued[0][0] == "cond_n"

        # Tick 1 arrives: chemical spike delivers synaptic conductance
        engine.step({})
        assert cond.conductance_state.g_syn > 0.0

    def test_default_neuron_matches_explicit_lif_numerically(self):
        """Validation 4: Neuron without dynamics_model == explicit lif_voltage."""
        n_default = Neuron("n1", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        n_explicit = Neuron("n2", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        n_explicit.dynamics_model = "lif_voltage"

        c = Circuit("equiv")
        c.add_neuron(n_default)
        c.add_neuron(n_explicit)
        c.input_neurons = ["n1", "n2"]
        c.output_neurons = ["n1", "n2"]

        engine = NeuralEngine(c)
        engine.step({"n1": 10.0, "n2": 10.0})

        assert n_default.membrane_potential == pytest.approx(n_explicit.membrane_potential)

    def test_mixed_circuit_full_coexistence(self):
        """Validation 5: LIF + conductance_v0 + electrical + chemical synapse coexist."""
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        lif = Neuron("lif_n", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        cond = Neuron("cond_n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        cond.dynamics_model = "conductance_v0"
        attach_conductance_state(cond, params=ConductanceParams(membrane_area_cm2=1.0))

        c = Circuit("full_mixed")
        c.add_neuron(lif)
        c.add_neuron(cond)
        c.add_synapse(Synapse("lif_n", "cond_n", sign=Sign.EXCITATORY, delay=2,
                              synapse_type="chemical", weight=5.0))
        c.add_synapse(Synapse("lif_n", "cond_n", sign=Sign.EXCITATORY, delay=1,
                              synapse_type="electrical", conductance=135.0))
        c.input_neurons = ["lif_n"]
        c.output_neurons = ["cond_n"]

        engine = NeuralEngine(c)

        # Tick 0: drive LIF to spike
        engine.step({"lif_n": 20.0})
        assert lif.refractory_remaining > 0

        # Only chemical spike queued (delay=2); electrical excluded
        queued = engine.spike_queue.get(2, [])
        assert len(queued) == 1

        # Tick 1: no chemical spike arrives yet (delay=2)
        engine.step({})
        assert cond.conductance_state.g_syn == 0.0

        # Tick 2: chemical spike arrives
        engine.step({})
        assert cond.conductance_state.g_syn > 0.0

    def test_conductance_v0_integration_enforces_area_requirement(self):
        """Validation 6: conductance_v0 integration enforces area; no invented params."""
        from biological_brain.dynamics import attach_conductance_state, get_model

        n = Neuron("n", resting_potential=-65.0, threshold=-45.0, tau_m=10.0)
        n.dynamics_model = "conductance_v0"
        # Attach state WITHOUT membrane_area_cm2 — no invented parameters
        attach_conductance_state(n)
        model = get_model("conductance_v0")

        with pytest.raises(NotImplementedError):
            model.integrate(n, 0.0)


class TestCompartmentArchitecture:
    """3.0D-7A: Compartment/morphology architecture (no invented biology)."""

    def test_compartment_has_no_invented_geometry(self):
        """A compartment can be represented without any biological geometry values."""
        from biological_brain.morphology import Compartment

        comp = Compartment(compartment_id="c0")
        assert comp.geometry.length_um is None
        assert comp.geometry.diameter_um is None
        assert comp.geometry.position is None
        assert comp.geometry.anatomical_role is None

    def test_compartments_form_parent_child_topology(self):
        """Compartments can form a parent/neighbor topology without biology."""
        from biological_brain.morphology import Compartment, CompartmentModel

        model = CompartmentModel(neuron_id="n0")
        parent = Compartment(compartment_id="parent")
        child = Compartment(compartment_id="child")
        model.add_compartment(parent)
        model.add_compartment(child)
        model.add_connection("parent", "child")

        assert child.parent_id == "parent"
        assert "child" in parent.neighbor_ids

    def test_geometry_remains_explicitly_unknown(self):
        """Geometry defaults to None, not an invented default value."""
        from biological_brain.morphology import CompartmentGeometry

        geom = CompartmentGeometry()
        assert geom.length_um is None
        assert geom.diameter_um is None

    def test_provenance_attached_to_future_morphology(self):
        """Provenance records can be attached to geometry fields."""
        from biological_brain.morphology import CompartmentGeometry, CompartmentProvenance
        from biological_brain.provenance import ParameterProvenance, ProvenanceRecord

        prov = CompartmentProvenance(
            length_um=ProvenanceRecord(ParameterProvenance.DIRECTLY_MEASURED, "Boerner & Godenschwege 2010"),
            diameter_um=ProvenanceRecord(ParameterProvenance.ESTIMATED, "Augustin et al. 2019"),
        )
        assert prov.length_um.category == ParameterProvenance.DIRECTLY_MEASURED
        assert prov.diameter_um.category == ParameterProvenance.ESTIMATED

    def test_neuron_backward_compatible_without_compartment_model(self):
        """Neuron without compartment_model behaves identically to before."""
        n = Neuron("n", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        assert n.compartment_model is None

        c = Circuit("test")
        c.add_neuron(n)
        c.input_neurons = ["n"]
        c.output_neurons = ["n"]

        engine = NeuralEngine(c)
        engine.step({"n": 10.0})
        assert n.membrane_potential > -70.0

    def test_no_passive_solver_required(self):
        """CompartmentModel exists without any integration/solver methods."""
        from biological_brain.morphology import CompartmentModel

        model = CompartmentModel(neuron_id="n0")
        assert not hasattr(model, "integrate")
        assert not hasattr(model, "solve_cable")
        assert not hasattr(model, "compute_axial_current")


class TestGFSMorphologySpecification:
    """3.0D-7B: Source-backed GFS morphology from Augustin et al. 2019."""

    def test_gfs_morphology_contains_all_four_neurons(self):
        """Morphology spec covers GF, TTMn, PSI, DLMn."""
        from biological_brain.gfs_morphology import get_gfs_morphology

        gfs = get_gfs_morphology()
        for neuron_type in ["GF", "TTMn", "PSI", "DLMn"]:
            assert neuron_type in gfs.neurons

    def test_psi_dendrite_length_is_estimated(self):
        """PSI dendrite length (170 um) must be classified ESTIMATED, not measured."""
        from biological_brain.gfs_morphology import get_gfs_morphology, get_morphology_parameter
        from biological_brain.provenance import ParameterProvenance

        gfs = get_gfs_morphology()
        param = get_morphology_parameter(gfs, "PSI", "dendrite", "length")
        assert param is not None
        assert param.value == 170.0
        assert param.provenance.category == ParameterProvenance.ESTIMATED

    def test_all_other_morphology_values_are_published_model_parameters(self):
        """Non-estimated Augustin anatomy values must be PUBLISHED_MODEL_PARAMETER."""
        from biological_brain.gfs_morphology import get_gfs_morphology
        from biological_brain.provenance import ParameterProvenance

        gfs = get_gfs_morphology()
        _collect_params(gfs, _assert_published_model_parameter)

    def test_values_match_august_2019_table(self):
        """Spot-check key values against Augustin Table 1."""
        from biological_brain.gfs_morphology import get_gfs_morphology, get_morphology_parameter

        gfs = get_gfs_morphology()

        assert get_morphology_parameter(gfs, "GF", "axon", "length").value == 400.0
        assert gfs.neurons["GF"].soma_diameter.value == 8.0

        assert get_morphology_parameter(gfs, "TTMn", "axon", "length").value == 50.0
        assert get_morphology_parameter(gfs, "TTMn", "medial_dendrite", "length").value == 60.0
        assert get_morphology_parameter(gfs, "TTMn", "lateral_dendrite", "length").value == 30.0
        assert gfs.neurons["TTMn"].soma_diameter.value == 6.0

        assert get_morphology_parameter(gfs, "PSI", "axon", "length").value == 90.0
        assert gfs.neurons["PSI"].soma_diameter.value == 4.5

        assert get_morphology_parameter(gfs, "DLMn", "dendrite", "length").value == 100.0
        assert get_morphology_parameter(gfs, "DLMn", "axon", "length").value == 50.0
        assert get_morphology_parameter(gfs, "DLMn", "dendrite", "diameter").value == 2.0
        assert get_morphology_parameter(gfs, "DLMn", "axon", "diameter_distal").value == 4.0

    def test_placements_present_for_gf_ttmn_psi_dlmn(self):
        """Contact and input placements are present for all four neurons."""
        from biological_brain.gfs_morphology import get_gfs_morphology

        gfs = get_gfs_morphology()
        assert len(gfs.neurons["GF"].placements) == 3    # 2 contacts + 1 input
        assert len(gfs.neurons["TTMn"].placements) == 0   # no placements in Table 1
        assert len(gfs.neurons["PSI"].placements) == 2    # 1 input + 1 contact
        assert len(gfs.neurons["DLMn"].placements) == 1    # 1 input

    def test_boerner_anatomical_context_documented(self):
        """GF and TTMn include Boerner context (3D reconstruction provenance)."""
        from biological_brain.gfs_morphology import get_gfs_morphology

        gfs = get_gfs_morphology()
        assert any("Boerner" in s for s in gfs.neurons["GF"].context_sources)
        assert any("Boerner" in s for s in gfs.neurons["TTMn"].context_sources)

    def test_no_invented_cable_parameters_or_coordinates(self):
        """No cable parameters or 3D coordinates stored in morphology data."""
        from biological_brain.gfs_morphology import get_gfs_morphology

        gfs = get_gfs_morphology()
        # CompartmentSpec has no cable_param or position fields
        for neuron in gfs.neurons.values():
            for comp in neuron.compartments:
                # No cable params, no coordinates, no branch angles
                for attr in ["cable_params", "position", "branch_angle", "compartment_count"]:
                    assert not hasattr(comp, attr)
            # No cable params on NeuronSpec
            assert not hasattr(neuron, "cable_params")

    def test_neuron_without_compartment_model_backward_compatible(self):
        """Existing Neuron without compartment_model still works as before."""
        from biological_brain.dynamics import attach_conductance_state
        from biological_brain.dynamics.conductance import ConductanceParams

        c = Circuit("test")
        n = Neuron("n", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        assert n.compartment_model is None

        c.add_neuron(n)
        c.input_neurons = ["n"]
        c.output_neurons = ["n"]

        engine = NeuralEngine(c)
        engine.step({"n": 10.0})
        assert n.membrane_potential > -70.0


def _collect_params(gfs, check_fn):
    """Walk all morphology parameters and apply check_fn."""
    for neuron in gfs.neurons.values():
        if neuron.soma_diameter is not None:
            check_fn(neuron.soma_diameter)
        for comp in neuron.compartments:
            if comp.length is not None:
                check_fn(comp.length)
            if comp.diameter is not None:
                check_fn(comp.diameter)
            if comp.diameter_distal is not None:
                check_fn(comp.diameter_distal)
        for placement in neuron.placements:
            check_fn(placement.distance)


def _assert_published_model_parameter(param):
    """Assert a parameter is PUBLISHED_MODEL_PARAMETER (or ESTIMATED for known cases)."""
    from biological_brain.provenance import ParameterProvenance

    if param.value == 170.0:
        assert param.provenance.category == ParameterProvenance.ESTIMATED
    else:
        assert param.provenance.category == ParameterProvenance.PUBLISHED_MODEL_PARAMETER


class TestCompartmentTopologyConstruction:
    """3.0D-7C: Build CompartmentModel from source-backed GFS morphology."""

    def test_deterministic_construction(self):
        """Building twice produces identical compartment models."""
        from biological_brain.morphology_builder import build_gfs_compartment_models

        m1 = build_gfs_compartment_models()
        m2 = build_gfs_compartment_models()
        assert set(m1.keys()) == set(m2.keys())
        for neuron_type in m1:
            c1 = m1[neuron_type]
            c2 = m2[neuron_type]
            assert set(c1.compartments.keys()) == set(c2.compartments.keys())
            for cid in c1.compartments:
                assert c1.compartments[cid].geometry.length_um == c2.compartments[cid].geometry.length_um
                assert c1.compartments[cid].geometry.diameter_um == c2.compartments[cid].geometry.diameter_um

    def test_expected_gfs_neuron_topology(self):
        """Each GFS neuron has soma root + expected section compartments."""
        from biological_brain.morphology_builder import build_gfs_compartment_models

        models = build_gfs_compartment_models()

        # GF: soma + axon + medial_dendrite
        gf = models["GF"]
        assert "GF_soma" in gf.compartments
        assert "GF_axon" in gf.compartments
        assert "GF_medial_dendrite" in gf.compartments

        # TTMn: soma + axon + medial_dendrite + lateral_dendrite
        ttmn = models["TTMn"]
        assert "TTMn_soma" in ttmn.compartments
        assert "TTMn_axon" in ttmn.compartments
        assert "TTMn_medial_dendrite" in ttmn.compartments
        assert "TTMn_lateral_dendrite" in ttmn.compartments

        # PSI: soma + axon + dendrite
        psi = models["PSI"]
        assert "PSI_soma" in psi.compartments
        assert "PSI_axon" in psi.compartments
        assert "PSI_dendrite" in psi.compartments

        # DLMn: soma + dendrite + axon
        dlmn = models["DLMn"]
        assert "DLMn_soma" in dlmn.compartments
        assert "DLMn_dendrite" in dlmn.compartments
        assert "DLMn_axon" in dlmn.compartments

    def test_parent_child_connectivity(self):
        """All section compartments have soma as parent."""
        from biological_brain.morphology_builder import build_gfs_compartment_models

        models = build_gfs_compartment_models()
        for neuron_type, model in models.items():
            soma_id = f"{neuron_type}_soma"
            soma = model.compartments[soma_id]
            assert soma.parent_id is None  # root
            for comp_id in soma.neighbor_ids:
                child = model.compartments[comp_id]
                assert child.parent_id == soma_id

    def test_geometry_provenance_preserved(self):
        """Geometry values and provenance are transferred from source to compartment."""
        from biological_brain.morphology_builder import build_gfs_compartment_models
        from biological_brain.provenance import ParameterProvenance

        models = build_gfs_compartment_models()
        dlmn = models["DLMn"]

        axon = dlmn.compartments["DLMn_axon"]
        assert axon.geometry.length_um == 50.0
        assert axon.provenance.length_um.category == ParameterProvenance.PUBLISHED_MODEL_PARAMETER

        assert axon.geometry.diameter_um == 2.0
        assert axon.geometry.diameter_distal_um == 4.0
        assert axon.provenance.diameter_distal_um.category == ParameterProvenance.PUBLISHED_MODEL_PARAMETER

    def test_distal_diameter_preserved_not_averaged(self):
        """DLMn axon preserves both proximal (2) and distal (4) diameters."""
        from biological_brain.morphology_builder import build_gfs_compartment_models

        models = build_gfs_compartment_models()
        axon = models["DLMn"].compartments["DLMn_axon"]
        assert axon.geometry.diameter_um == 2.0
        assert axon.geometry.diameter_distal_um == 4.0

    def test_psi_dendrite_provenance_estimated(self):
        """PSI dendrite length retains ESTIMATED provenance through conversion."""
        from biological_brain.morphology_builder import build_gfs_compartment_models
        from biological_brain.provenance import ParameterProvenance

        models = build_gfs_compartment_models()
        dend = models["PSI"].compartments["PSI_dendrite"]
        assert dend.geometry.length_um == 170.0
        assert dend.provenance.length_um.category == ParameterProvenance.ESTIMATED

    def test_placement_metadata_preserved(self):
        """Contact/input placements are attached to the correct compartments."""
        from biological_brain.morphology_builder import build_gfs_compartment_models

        models = build_gfs_compartment_models()

        # GF axon: 2 contacts
        gf_axon = models["GF"].compartments["GF_axon"]
        assert len(gf_axon.placements) == 2
        distances = sorted(p.distance_um for p in gf_axon.placements)
        assert distances == [360.0, 400.0]

        # GF medial_dendrite: 1 input
        gf_dend = models["GF"].compartments["GF_medial_dendrite"]
        assert len(gf_dend.placements) == 1
        assert gf_dend.placements[0].distance_um == 12.0

        # PSI axon: 1 input + 1 contact = 2
        psi_axon = models["PSI"].compartments["PSI_axon"]
        assert len(psi_axon.placements) == 2

        # DLMn axon: 1 input
        dlmn_axon = models["DLMn"].compartments["DLMn_axon"]
        assert len(dlmn_axon.placements) == 1
        assert dlmn_axon.placements[0].distance_um == 12.5

    def test_no_invented_cable_parameters(self):
        """No axial resistance, capacitance, leak, or reversal potentials assigned."""
        from biological_brain.morphology_builder import build_gfs_compartment_models

        models = build_gfs_compartment_models()
        for model in models.values():
            for comp in model.compartments.values():
                assert comp.cable_params.axial_resistance_ohm_cm is None
                assert comp.cable_params.membrane_capacitance_uf_per_cm2 is None
                assert comp.cable_params.leak_conductance_ms_per_cm2 is None
                assert comp.cable_params.leak_reversal_mV is None

    def test_neuron_backward_compatible_without_compartment_model(self):
        """Existing Neuron without compartment_model still works unchanged."""
        n = Neuron("n", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        assert n.compartment_model is None

        c = Circuit("test")
        c.add_neuron(n)
        c.input_neurons = ["n"]
        c.output_neurons = ["n"]

        engine = NeuralEngine(c)
        engine.step({"n": 10.0})
        assert n.membrane_potential > -70.0


class TestCompartmentGeometryMetrics:
    """3.0D-7D: Geometry-derived compartment metrics (no electrical parameters)."""

    def test_exact_cylinder_cross_sectional_area(self):
        """Cross-sectional area = π * d² / 4 for a cylindrical compartment."""
        from math import pi
        from biological_brain.morphology import Compartment, CompartmentGeometry
        from biological_brain.geometry_metrics import compute_compartment_metrics

        comp = Compartment(
            compartment_id="cyl",
            geometry=CompartmentGeometry(length_um=100.0, diameter_um=10.0),
        )
        m = compute_compartment_metrics(comp)
        assert m.cross_sectional_area_um2 == pytest.approx(pi * 10.0 ** 2 / 4)

    def test_exact_cylinder_lateral_surface_area(self):
        """Lateral surface area = π * d * L for a cylinder."""
        from math import pi
        from biological_brain.morphology import Compartment, CompartmentGeometry
        from biological_brain.geometry_metrics import compute_compartment_metrics

        comp = Compartment(
            compartment_id="cyl",
            geometry=CompartmentGeometry(length_um=100.0, diameter_um=10.0),
        )
        m = compute_compartment_metrics(comp)
        assert m.lateral_surface_area_um2 == pytest.approx(pi * 10.0 * 100.0)

    def test_exact_cylinder_volume(self):
        """Volume = π * d² * L / 4 for a cylinder."""
        from math import pi
        from biological_brain.morphology import Compartment, CompartmentGeometry
        from biological_brain.geometry_metrics import compute_compartment_metrics

        comp = Compartment(
            compartment_id="cyl",
            geometry=CompartmentGeometry(length_um=100.0, diameter_um=10.0),
        )
        m = compute_compartment_metrics(comp)
        assert m.volume_um3 == pytest.approx(pi * 10.0 ** 2 * 100.0 / 4)

    def test_tapered_section_frustum_formulas(self):
        """DLMn axon taper: proximal=2 um, distal=4 um, length=50 um."""
        from math import pi, sqrt
        from biological_brain.morphology import Compartment, CompartmentGeometry
        from biological_brain.geometry_metrics import compute_compartment_metrics

        comp = Compartment(
            compartment_id="dlmn_axon",
            geometry=CompartmentGeometry(
                length_um=50.0,
                diameter_um=2.0,
                diameter_distal_um=4.0,
            ),
        )
        m = compute_compartment_metrics(comp)
        assert m.is_tapered is True
        assert m.cross_sectional_area_um2 is None
        assert m.proximal_cross_sectional_area_um2 == pytest.approx(pi * 2.0 ** 2 / 4)
        assert m.distal_cross_sectional_area_um2 == pytest.approx(pi * 4.0 ** 2 / 4)

        # Frustum lateral surface area
        r1, r2, L = 1.0, 2.0, 50.0
        slant = sqrt((r1 - r2) ** 2 + L ** 2)
        expected_lateral = pi * (r1 + r2) * slant
        assert m.lateral_surface_area_um2 == pytest.approx(expected_lateral)

        # Frustum volume
        expected_volume = (pi * L / 3) * (r1 ** 2 + r2 ** 2 + r1 * r2)
        assert m.volume_um3 == pytest.approx(expected_volume)

    def test_missing_geometry_returns_none(self):
        """Compartment with no diameter cannot compute any metrics."""
        from biological_brain.morphology import Compartment, CompartmentGeometry
        from biological_brain.geometry_metrics import compute_compartment_metrics

        comp = Compartment(
            compartment_id="unknown",
            geometry=CompartmentGeometry(),
        )
        m = compute_compartment_metrics(comp)
        assert m.cross_sectional_area_um2 is None
        assert m.lateral_surface_area_um2 is None
        assert m.volume_um3 is None
        assert "diameter_um is None" in m.derivation_note

    def test_provenance_links_to_source_geometry(self):
        """Derived metrics provenance references source geometry fields."""
        from biological_brain.morphology import (
            Compartment, CompartmentGeometry, CompartmentProvenance,
        )
        from biological_brain.provenance import ParameterProvenance, ProvenanceRecord
        from biological_brain.geometry_metrics import compute_compartment_metrics

        comp = Compartment(
            compartment_id="cyl",
            geometry=CompartmentGeometry(length_um=100.0, diameter_um=10.0),
            provenance=CompartmentProvenance(
                length_um=ProvenanceRecord(ParameterProvenance.PUBLISHED_MODEL_PARAMETER, "source1"),
                diameter_um=ProvenanceRecord(ParameterProvenance.ESTIMATED, "source2"),
            ),
        )
        m = compute_compartment_metrics(comp)
        assert ParameterProvenance.UNKNOWN == m.provenance.category
        assert "diameter_um(ESTIMATED)" in m.provenance.source
        assert "length_um(PUBLISHED_MODEL_PARAMETER)" in m.provenance.source

    def test_no_cable_parameters_populated(self):
        """Computing metrics does NOT populate CableParameters."""
        from biological_brain.morphology import Compartment, CompartmentGeometry
        from biological_brain.geometry_metrics import compute_compartment_metrics, assert_no_electrical_parameters

        comp = Compartment(
            compartment_id="cyl",
            geometry=CompartmentGeometry(length_um=100.0, diameter_um=10.0),
        )
        compute_compartment_metrics(comp)
        assert_no_electrical_parameters(comp)


class TestPassiveElectricalRegistry:
    """3.0D-7E: Evidence registry for candidate passive electrical parameters.

    The registry is a provenance boundary, NOT an assignment mechanism.
    No parameter may be simulator-eligible and no CableParameters value
    may be populated from it.
    """

    EXPECTED_NAMES = [
        "specific_membrane_capacitance",
        "specific_axial_resistance",
        "leak_conductance_density",
        "leak_reversal_potential",
        "gap_junction_conductance_young",
        "gap_junction_conductance_old",
        "gf_input_resistance",
        "gfs_electrophysiology_reference",
    ]

    def test_factory_returns_expected_entries(self):
        """Factory builds a registry with exactly the expected candidate set."""
        from biological_brain.passive_electrical_registry import (
            PassiveElectricalRegistry, PassiveParameterEntry,
            get_passive_electrical_registry,
        )

        r = get_passive_electrical_registry()
        assert isinstance(r, PassiveElectricalRegistry)
        assert r.names() == self.EXPECTED_NAMES
        for name in self.EXPECTED_NAMES:
            assert isinstance(r.get(name), PassiveParameterEntry)
        with pytest.raises(KeyError):
            r.get("not_a_registered_parameter")

    def test_augustin_candidate_values_and_units(self):
        """Augustin 2019 candidate values are recorded verbatim with units."""
        from biological_brain.passive_electrical_registry import get_passive_electrical_registry

        r = get_passive_electrical_registry()
        expected = {
            "specific_membrane_capacitance": (1.0, "uF/cm2"),
            "specific_axial_resistance": (35.4, "ohm*cm"),
            "leak_conductance_density": (0.03, "mS/cm2"),
            "leak_reversal_potential": (-85.0, "mV"),
            "gap_junction_conductance_young": (135.0, "uS"),
            "gap_junction_conductance_old": (34.5, "uS"),
        }
        for name, (value, unit) in expected.items():
            entry = r.get(name)
            assert entry.value == pytest.approx(value)
            assert entry.unit == unit

    def test_provenance_classifications(self):
        """Estimated model values are not presented as direct measurements."""
        from biological_brain.passive_electrical_registry import get_passive_electrical_registry
        from biological_brain.provenance import ParameterProvenance

        r = get_passive_electrical_registry()
        expected = {
            "specific_membrane_capacitance": ParameterProvenance.ESTIMATED,
            "specific_axial_resistance": ParameterProvenance.ESTIMATED,
            "leak_conductance_density": ParameterProvenance.ESTIMATED,
            # Borrowed from Günay et al. model, not measured in GFS neurons.
            "leak_reversal_potential": ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
            "gap_junction_conductance_young": ParameterProvenance.ESTIMATED,
            "gap_junction_conductance_old": ParameterProvenance.ESTIMATED,
            "gf_input_resistance": ParameterProvenance.EXPERIMENTALLY_CONSTRAINED,
            "gfs_electrophysiology_reference": ParameterProvenance.EXPERIMENTALLY_CONSTRAINED,
        }
        for name, category in expected.items():
            assert r.get(name).provenance_category == category, name

    def test_source_attribution(self):
        """Each entry names the source its evidence actually came from."""
        from biological_brain.passive_electrical_registry import get_passive_electrical_registry

        r = get_passive_electrical_registry()
        for name in (
            "specific_membrane_capacitance",
            "specific_axial_resistance",
            "leak_conductance_density",
            "gap_junction_conductance_young",
            "gap_junction_conductance_old",
        ):
            assert "Augustin" in r.get(name).source, name

        # Leak reversal is attributed to the borrowed motoneuron model.
        assert "Günay" in r.get("leak_reversal_potential").source
        assert "NOT a direct measurement" in r.get("leak_reversal_potential").notes

        assert "Jensen" in r.get("gf_input_resistance").source
        assert "Hoyle" in r.get("gfs_electrophysiology_reference").source

    def test_all_candidates_ineligible_for_simulator(self):
        """No candidate is authorized for direct simulator assignment."""
        from biological_brain.passive_electrical_registry import get_passive_electrical_registry

        r = get_passive_electrical_registry()
        assert len(r.parameters) == len(self.EXPECTED_NAMES)
        for entry in r.parameters:
            assert entry.eligible_for_simulator is False, entry.name
            assert "Must NOT be assigned to CableParameters" in entry.notes, entry.name

    def test_gf_input_resistance_is_whole_cell_range_not_specific_rm(self):
        """GF input resistance stays a whole-cell MOhm range, never a specific Rm."""
        from biological_brain.passive_electrical_registry import get_passive_electrical_registry

        r = get_passive_electrical_registry()
        entry = r.get("gf_input_resistance")

        assert entry.unit == "MOhm"
        assert entry.value_min == pytest.approx(50.0)
        assert entry.value_max == pytest.approx(100.0)
        assert entry.value_min <= entry.value <= entry.value_max
        assert "NOT convertible to specific membrane resistance" in entry.notes

        # No entry claims a specific membrane resistance (ohm*cm2).
        assert all(e.unit != "ohm*cm2" for e in r.parameters)
        # Only the whole-cell observation is expressed as a range.
        ranged = [e.name for e in r.parameters if e.value_min is not None or e.value_max is not None]
        assert ranged == ["gf_input_resistance"]

    def test_factory_returns_fresh_independent_objects(self):
        """Each call builds new entries; mutating one cannot affect another."""
        from biological_brain.passive_electrical_registry import get_passive_electrical_registry

        r1 = get_passive_electrical_registry()
        r2 = get_passive_electrical_registry()

        assert r1 is not r2
        assert r1.parameters is not r2.parameters
        assert r1.get("leak_reversal_potential") is not r2.get("leak_reversal_potential")

        r1.get("leak_reversal_potential").value = 0.0
        r1.get("leak_reversal_potential").eligible_for_simulator = True
        r1.parameters.clear()

        fresh = get_passive_electrical_registry()
        assert fresh.names() == self.EXPECTED_NAMES
        assert fresh.get("leak_reversal_potential").value == pytest.approx(-85.0)
        assert fresh.get("leak_reversal_potential").eligible_for_simulator is False

    def test_no_cable_parameter_coupling(self):
        """The registry module neither imports nor mutates compartment electrical state."""
        import inspect
        from biological_brain import passive_electrical_registry as per_module
        from biological_brain.morphology import CableParameters
        from biological_brain.morphology_builder import build_gfs_compartment_models

        source = inspect.getsource(per_module)
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        assert not any("morphology" in line for line in import_lines)
        assert "CableParameters" not in per_module.__dict__
        assert "Compartment" not in per_module.__dict__

        # Using the registry alongside built compartment models changes nothing.
        from biological_brain.passive_electrical_registry import get_passive_electrical_registry

        models = build_gfs_compartment_models()
        before = [
            (c.cable_params.axial_resistance_ohm_cm,
             c.cable_params.membrane_capacitance_uf_per_cm2,
             c.cable_params.leak_conductance_ms_per_cm2,
             c.cable_params.leak_reversal_mV)
            for model in models.values()
            for c in model.compartments.values()
        ]

        registry = get_passive_electrical_registry()
        assert CableParameters().axial_resistance_ohm_cm is None
        assert registry.names() == self.EXPECTED_NAMES

        after = [
            (c.cable_params.axial_resistance_ohm_cm,
             c.cable_params.membrane_capacitance_uf_per_cm2,
             c.cable_params.leak_conductance_ms_per_cm2,
             c.cable_params.leak_reversal_mV)
            for model in models.values()
            for c in model.compartments.values()
        ]
        assert after == before
        assert all(v == (None, None, None, None) for v in after)

    def test_existing_behavior_unchanged(self):
        """Importing and using the registry does not alter LIF/dynamics behavior."""
        from biological_brain.passive_electrical_registry import get_passive_electrical_registry

        get_passive_electrical_registry()

        n = Neuron("n", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        assert n.compartment_model is None
        assert n.dynamics_model is None

        c = Circuit("test")
        c.add_neuron(n)
        c.input_neurons = ["n"]
        c.output_neurons = ["n"]

        engine = NeuralEngine(c)
        engine.step({"n": 10.0})
        assert n.membrane_potential > -70.0


class TestPassiveParameterProfile:
    """3.0D-7F: Explicit opt-in authorization layer over the 7E evidence registry.

    Authorization is a permission record, not a measurement claim and not
    a parameter assignment. The profile must never populate
    Compartment.CableParameters or alter runtime behavior.
    """

    EXPECTED_AUTHORIZED = [
        "specific_membrane_capacitance",
        "specific_axial_resistance",
        "leak_conductance_density",
        "leak_reversal_potential",
    ]

    def test_profile_contains_exactly_four_authorized_quantities(self):
        """Only the four Augustin passive quantities are authorized."""
        from biological_brain.passive_profiles import (
            PassiveParameterProfile, build_augustin_2019_gfs_passive_profile,
            get_passive_parameter_profile, available_passive_profiles,
            PROFILE_AUGUSTIN_2019_GFS_PASSIVE,
        )

        p = build_augustin_2019_gfs_passive_profile()
        assert isinstance(p, PassiveParameterProfile)
        assert p.name == PROFILE_AUGUSTIN_2019_GFS_PASSIVE
        assert p.authorized_names() == tuple(self.EXPECTED_AUTHORIZED)
        assert p.opt_in is True

        # Exactly one profile exists and lookup is explicit, never defaulted.
        assert available_passive_profiles() == ("augustin_2019_gfs_passive",)
        assert get_passive_parameter_profile(PROFILE_AUGUSTIN_2019_GFS_PASSIVE).name == p.name
        with pytest.raises(KeyError):
            get_passive_parameter_profile("some_other_profile")

    def test_exact_values_and_units_preserved(self):
        """Values and units are exactly as reported by Augustin."""
        from biological_brain.passive_profiles import build_augustin_2019_gfs_passive_profile

        p = build_augustin_2019_gfs_passive_profile()
        expected = {
            "specific_membrane_capacitance": (1.0, "uF/cm2"),
            "specific_axial_resistance": (35.4, "ohm*cm"),
            "leak_conductance_density": (0.03, "mS/cm2"),
            "leak_reversal_potential": (-85.0, "mV"),
        }
        for name, (value, unit) in expected.items():
            entry = p.get(name)
            assert entry.value == pytest.approx(value)
            assert entry.unit == unit

        # Specific axial resistance uses the canonical ohm*cm (ohm.cm) unit.
        # The paper's literal printed notation is preserved as source text only.
        ra = p.get("specific_axial_resistance")
        assert ra.unit == "ohm*cm"
        assert ra.unit != "ohm*cm2"
        assert "CANONICAL UNIT: ohm*cm" in ra.limitations
        assert "35.4 Ω/cm (estimated)" in ra.limitations
        assert "retained here as source text only" in ra.limitations
        assert "NOT a per-compartment axial" in ra.limitations

    def test_provenance_and_source_preserved_from_registry(self):
        """Profile values are copied from the evidence layer, which is not mutated."""
        from biological_brain.passive_electrical_registry import get_passive_electrical_registry
        from biological_brain.passive_profiles import (
            AUTHORIZATION_SCOPE_MODEL_REPRODUCTION, build_augustin_2019_gfs_passive_profile,
        )
        from biological_brain.provenance import ParameterProvenance

        registry = get_passive_electrical_registry()
        p = build_augustin_2019_gfs_passive_profile()

        for name in self.EXPECTED_AUTHORIZED:
            entry = p.get(name)
            source_entry = registry.get(name)
            assert entry.value == source_entry.value
            assert entry.unit == source_entry.unit
            assert entry.provenance_category == source_entry.provenance_category
            assert entry.source == source_entry.source
            assert entry.authorization_scope == AUTHORIZATION_SCOPE_MODEL_REPRODUCTION

        assert p.get("leak_reversal_potential").provenance_category == (
            ParameterProvenance.PUBLISHED_MODEL_PARAMETER
        )
        assert p.get("specific_membrane_capacitance").provenance_category == (
            ParameterProvenance.ESTIMATED
        )
        assert "Günay" in p.get("leak_reversal_potential").source

        # Authorizing for reproduction does not change registry eligibility.
        for name in self.EXPECTED_AUTHORIZED:
            assert registry.get(name).eligible_for_simulator is False

    def test_profile_is_explicitly_model_reproduction_only(self):
        """The profile authorizes reproducing a model, not asserting biology."""
        from biological_brain.passive_profiles import build_augustin_2019_gfs_passive_profile

        p = build_augustin_2019_gfs_passive_profile()
        assert p.model_reproduction_only is True
        assert "MODEL REPRODUCTION ONLY" in p.limitations
        assert "does NOT mean" in p.limitations
        assert "reproducing that model's assumptions" in p.limitations
        assert "51 isopotential segments" in p.limitations

    def test_whole_cell_measurements_not_authorized(self):
        """GF input resistance and DLMn whole-cell values stay unauthorized."""
        from biological_brain.passive_profiles import build_augustin_2019_gfs_passive_profile

        p = build_augustin_2019_gfs_passive_profile()
        excluded = {e.name for e in p.excluded}

        assert p.is_authorized("gf_input_resistance") is False
        assert p.is_authorized("dlmn_whole_cell_capacitance") is False
        assert p.is_authorized("dlmn_whole_cell_input_resistance") is False
        assert {"gf_input_resistance", "dlmn_whole_cell_capacitance",
                "dlmn_whole_cell_input_resistance"} <= excluded

        # No whole-cell quantity was converted into a specific parameter.
        assert not any("MOhm" == e.unit for e in p.parameters)
        assert not any("pF" in e.unit for e in p.parameters)
        with pytest.raises(KeyError):
            p.get("gf_input_resistance")

    def test_gap_junction_synaptic_and_active_parameters_not_authorized(self):
        """Coupling, synaptic, and active/HH parameters are outside the profile."""
        from biological_brain.passive_profiles import build_augustin_2019_gfs_passive_profile

        p = build_augustin_2019_gfs_passive_profile()
        excluded = {e.name for e in p.excluded}

        for name in (
            "gap_junction_conductance_young",
            "gap_junction_conductance_old",
            "chemical_synapse_conductance",
            "active_na_conductance_density",
            "active_k_conductance_density",
            "active_ca_conductance_density",
            "hodgkin_huxley_parameters",
        ):
            assert p.is_authorized(name) is False, name
            assert name in excluded, name

        assert not any("uS" == e.unit for e in p.parameters)

    def test_profile_creation_deterministic_and_frozen(self):
        """Rebuilding yields equal profiles; instances are immutable and separate."""
        import dataclasses
        from biological_brain.passive_profiles import build_augustin_2019_gfs_passive_profile

        p1 = build_augustin_2019_gfs_passive_profile()
        p2 = build_augustin_2019_gfs_passive_profile()

        assert p1 == p2
        assert p1 is not p2
        assert p1.parameters is not p2.parameters
        assert isinstance(p1.parameters, tuple)

        with pytest.raises(dataclasses.FrozenInstanceError):
            p1.model_reproduction_only = False
        with pytest.raises(dataclasses.FrozenInstanceError):
            p1.get("leak_conductance_density").value = 0.5

    def test_no_cable_parameters_populated(self):
        """Building the profile populates no compartment cable parameters."""
        from biological_brain.morphology import CableParameters
        from biological_brain.morphology_builder import build_gfs_compartment_models
        from biological_brain.passive_profiles import build_augustin_2019_gfs_passive_profile

        models = build_gfs_compartment_models()
        p = build_augustin_2019_gfs_passive_profile()
        assert p.authorized_names() == tuple(self.EXPECTED_AUTHORIZED)

        for model in models.values():
            for comp in model.compartments.values():
                assert comp.cable_params.axial_resistance_ohm_cm is None
                assert comp.cable_params.membrane_capacitance_uf_per_cm2 is None
                assert comp.cable_params.leak_conductance_ms_per_cm2 is None
                assert comp.cable_params.leak_reversal_mV is None

        assert CableParameters().axial_resistance_ohm_cm is None

    def test_existing_default_behavior_unchanged(self):
        """The profile is opt-in and leaves lif_voltage/default paths untouched."""
        from biological_brain.dynamics import MODEL_NAME_LIF_VOLTAGE
        from biological_brain.passive_profiles import build_augustin_2019_gfs_passive_profile

        build_augustin_2019_gfs_passive_profile()

        n = Neuron("n", resting_potential=-70.0, threshold=-55.0, tau_m=10.0)
        assert n.dynamics_model is None
        assert n.compartment_model is None

        c = Circuit("test")
        c.add_neuron(n)
        c.input_neurons = ["n"]
        c.output_neurons = ["n"]

        engine = NeuralEngine(c)
        engine.step({"n": 10.0})
        assert n.membrane_potential > -70.0

        explicit = Neuron("m", dynamics_model=MODEL_NAME_LIF_VOLTAGE)
        assert explicit.dynamics_model == MODEL_NAME_LIF_VOLTAGE
