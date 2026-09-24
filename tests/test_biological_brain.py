"""Unit tests for Biological Brain 3.0 components."""

import pytest
from biological_brain import (
    Neuron, Synapse, Sign, Circuit, NeuralEngine,
    SignalTranslator, BiologicalBrain, BiologicalMode, BIOLOGICAL_CIRCUITS
)


class TestNeuron:
    """Test Stage A Leaky Integrate-and-Fire neuron."""

    def test_neuron_integrate_threshold_spike(self):
        """Neuron spikes when membrane potential crosses threshold."""
        n = Neuron("test", threshold=1.0)
        assert n.membrane_potential == 0.0
        
        # Below threshold - no spike
        spiked = n.integrate(0.5)
        assert spiked is False
        assert n.membrane_potential == 0.4  # 0.5 - 0.1 leak
        
        # Cross threshold - spike
        spiked = n.integrate(0.7)
        assert spiked is True
        assert n.membrane_potential == 0.0  # Reset after spike
        assert n.refractory_remaining == n.refractory_period

    def test_neuron_refractory_period(self):
        """Neuron cannot spike during refractory period."""
        n = Neuron("test", threshold=1.0, refractory_period=2)
        
        # Trigger spike
        n.integrate(2.0)
        assert n.refractory_remaining == 2
        
        # During refractory - no spike possible
        spiked = n.integrate(10.0)
        assert spiked is False
        assert n.refractory_remaining == 1
        
        spiked = n.integrate(10.0)
        assert spiked is False
        assert n.refractory_remaining == 0
        
        # After refractory - can spike again
        spiked = n.integrate(2.0)
        assert spiked is True

    def test_neuron_leak(self):
        """Membrane potential leaks toward zero."""
        n = Neuron("test", threshold=10.0, leak=0.5)
        n.integrate(3.0)
        assert n.membrane_potential == 2.5  # 3.0 - 0.5
        
        n.integrate(0.0)
        assert n.membrane_potential == 2.0  # 2.5 - 0.5

    def test_neuron_receive_spike(self):
        """Neuron receives synaptic input."""
        n = Neuron("test", threshold=1.0)
        
        # Excitatory input
        n.receive_spike(0.6, sign=1)
        assert n.membrane_potential == 0.6
        
        # Inhibitory input
        n.receive_spike(0.3, sign=-1)
        assert n.membrane_potential == 0.3  # 0.6 - 0.3

    def test_neuron_inhibitory_cannot_go_negative(self):
        """Membrane potential floors at zero."""
        n = Neuron("test", threshold=1.0)
        n.receive_spike(0.5, sign=1)
        n.receive_spike(1.0, sign=-1)
        assert n.membrane_potential == 0.0

    def test_neuron_reset(self):
        """Reset clears state."""
        n = Neuron("test", threshold=1.0)
        n.integrate(2.0)  # Spike
        n.reset()
        assert n.membrane_potential == 0.0
        assert n.refractory_remaining == 0


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
        
        c.add_neuron(Neuron("A"))
        c.add_neuron(Neuron("B"))
        c.connect("A", "B", weight=1.0)
        
        assert "A" in c.neurons
        assert "B" in c.neurons
        assert len(c.synapses) == 1
        assert c.synapses[0].source == "A"
        assert c.synapses[0].target == "B"

    def test_circuit_input_output_definition(self):
        """Circuit tracks input and output neurons."""
        c = Circuit("test")
        c.add_neuron(Neuron("in1"))
        c.add_neuron(Neuron("out1"))
        c.input_neurons = ["in1"]
        c.output_neurons = ["out1"]
        
        assert c.get_inputs() == ["in1"]
        assert c.get_outputs() == ["out1"]

    def test_circuit_validate_missing_neuron(self):
        """Validation catches missing neurons."""
        c = Circuit("test")
        c.add_neuron(Neuron("A"))
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
        c.add_neuron(Neuron("A", threshold=1.0))
        c.add_neuron(Neuron("B", threshold=1.0))
        c.connect("A", "B", weight=1.0)
        c.input_neurons = ["A"]
        c.output_neurons = ["B"]
        
        engine = NeuralEngine(c)
        assert engine.current_tick == 0
        
        engine.step({"A": 2.0})
        assert engine.current_tick == 1
        
        engine.step({})
        assert engine.current_tick == 2

    def test_engine_spike_propagation(self):
        """Spike propagates through synapse after delay."""
        c = Circuit("test")
        c.add_neuron(Neuron("A", threshold=1.0))
        c.add_neuron(Neuron("B", threshold=1.0))
        c.connect("A", "B", weight=1.0, delay=1)
        c.input_neurons = ["A"]
        c.output_neurons = ["B"]
        
        engine = NeuralEngine(c)
        
        # Tick 1: A spikes
        engine.step({"A": 2.0})
        
        # Tick 2: B receives spike
        outputs = engine.step({})
        # B should have received 1.0 input, membrane = 0.9 (with leak)
        assert outputs["B"] > 0.0

    def test_engine_sensory_input(self):
        """Sensory input injected at each step."""
        c = Circuit("test")
        c.add_neuron(Neuron("in", threshold=10.0))
        c.output_neurons = ["in"]
        
        engine = NeuralEngine(c)
        
        engine.step({"in": 1.0})
        engine.step({"in": 1.0})
        
        state = engine.get_state()
        # Accumulating with leak: 1.0 -> 0.9, then +1.0 -> 1.9 -> 1.8
        assert state["neurons"]["in"]["potential"] > 0.0

    def test_engine_reset(self):
        """Reset clears engine state."""
        c = Circuit("test")
        c.add_neuron(Neuron("A", threshold=1.0))
        c.connect("A", "A", weight=1.0)  # Self-connection
        c.input_neurons = ["A"]
        c.output_neurons = ["A"]
        
        engine = NeuralEngine(c)
        engine.step({"A": 2.0})
        engine.step({})
        
        engine.reset()
        assert engine.current_tick == 0
        assert engine.circuit.neurons["A"].membrane_potential == 0.0


class TestSignalTranslator:
    """Test signal translation."""

    def test_translate_startle_signals(self):
        """Translator maps startle outputs to signals."""
        c = Circuit("startle")
        c.add_neuron(Neuron("DN_STARTLE_BIO", threshold=1.0))
        c.add_neuron(Neuron("THREAT_BIO", threshold=1.0))
        c.output_neurons = ["DN_STARTLE_BIO", "THREAT_BIO"]
        
        translator = SignalTranslator(c)
        signals = translator.translate({
            "DN_STARTLE_BIO": 2.5,
            "THREAT_BIO": 1.5,
        })
        
        assert "escape_signal" in signals
        assert "threat_signal" in signals
        assert signals["escape_signal"] == 1.0  # Clamped
        assert signals["threat_signal"] == 1.0

    def test_translate_normalizes(self):
        """Outputs normalized to [0, 1]."""
        c = Circuit("test")
        c.add_neuron(Neuron("out"))
        c.output_neurons = ["out"]
        
        translator = SignalTranslator(c)
        signals = translator.translate({"out": 5.0})
        assert signals["out"] == 1.0
        
        signals = translator.translate({"out": -2.0})
        assert signals["out"] == 0.0


class TestBiologicalBrain:
    """Test BiologicalBrain facade."""

    def test_legacy_mode_returns_empty(self):
        """LEGACY_2_0 mode returns empty signals."""
        # Temporarily enable startle circuit for test
        BIOLOGICAL_CIRCUITS["startle"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.LEGACY_2_0)
            signals = brain.step({"lightLevel": 1.0})
            assert signals == {}
        finally:
            BIOLOGICAL_CIRCUITS["startle"] = False

    def test_biological_mode_runs_circuit(self):
        """BIOLOGICAL_3_0 mode runs enabled circuits."""
        BIOLOGICAL_CIRCUITS["startle"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            signals = brain.step({"lightLevel": 0.5})
            # Should have bio_* signals
            assert any(k.startswith("bio_") for k in signals)
        finally:
            BIOLOGICAL_CIRCUITS["startle"] = False

    def test_sensory_mapping(self):
        """2.0 stimulate maps to biological inputs."""
        BIOLOGICAL_CIRCUITS["startle"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            bio_input = brain._map_sensory_input({
                "lightLevel": 0.5,
                "nociception": True,
                "dangerOdor": True,
                "touch": True,
            })
            assert "VIS_LC_BIO" in bio_input
            assert "NOCI_BIO" in bio_input
            assert bio_input["VIS_LC_BIO"] == 1.0  # 0.5 * 2.0
            assert bio_input["NOCI_BIO"] == 3.0  # nociception
        finally:
            BIOLOGICAL_CIRCUITS["startle"] = False

    def test_reset_clears_all(self):
        """Reset clears all engine state."""
        BIOLOGICAL_CIRCUITS["startle"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            brain.step({"lightLevel": 1.0})
            brain.step({"lightLevel": 1.0})
            brain.reset()
            
            state = brain.get_circuit_state("startle")
            assert state["tick"] == 0
            for n in state["neurons"].values():
                assert n["potential"] == 0.0
                assert n["refractory"] == 0
        finally:
            BIOLOGICAL_CIRCUITS["startle"] = False


class TestStartleCircuit:
    """Test the startle circuit scaffold."""

    def test_startle_circuit_structure(self):
        """Startle circuit has expected neurons and connections."""
        BIOLOGICAL_CIRCUITS["startle"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            circuit = brain.circuits["startle"]
            
            # Check neurons
            assert "VIS_LC_BIO" in circuit.neurons
            assert "NOCI_BIO" in circuit.neurons
            assert "THREAT_BIO" in circuit.neurons
            assert "DN_STARTLE_BIO" in circuit.neurons
            assert "DN_FLIGHT_BIO" in circuit.neurons
            
            # Check I/O
            assert circuit.get_inputs() == ["VIS_LC_BIO", "NOCI_BIO"]
            assert set(circuit.get_outputs()) == {"DN_STARTLE_BIO", "DN_FLIGHT_BIO", "THREAT_BIO"}
            
            # Check connections
            assert len(circuit.synapses) == 5
            
            # Validate
            warnings = circuit.validate()
            assert len(warnings) == 0
        finally:
            BIOLOGICAL_CIRCUITS["startle"] = False

    def test_startle_circuit_responds_to_light(self):
        """Light input activates VIS_LC_BIO -> DN_STARTLE_BIO path."""
        BIOLOGICAL_CIRCUITS["startle"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            
            # Strong light for several ticks
            for _ in range(5):
                signals = brain.step({"lightLevel": 1.0})
            
            # Should produce escape/threat signals
            assert "bio_escape_signal" in signals or "bio_threat_signal" in signals
        finally:
            BIOLOGICAL_CIRCUITS["startle"] = False

    def test_startle_circuit_responds_to_nociception(self):
        """Nociception activates NOCI_BIO -> DN_STARTLE_BIO path."""
        BIOLOGICAL_CIRCUITS["startle"] = True
        try:
            brain = BiologicalBrain(mode=BiologicalMode.BIOLOGICAL_3_0)
            
            # Nociception pulse
            signals = brain.step({"nociception": True})
            
            # Should produce signals
            assert len(signals) > 0
        finally:
            BIOLOGICAL_CIRCUITS["startle"] = False