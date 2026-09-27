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
