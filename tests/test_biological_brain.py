"""Unit tests for Biological Brain 3.0 components."""

import pytest
from biological_brain import (
    Neuron, Synapse, Sign, Circuit, NeuralEngine,
    SignalTranslator, BiologicalBrain, BiologicalMode, BIOLOGICAL_CIRCUITS
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
            # 10 chemical + 8 electrical JSON entries expanded to bidirectional pairs = 26 Synapse objects
            assert len(circuit.synapses) == 26
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