"""Biological Brain 3.0 - Public API."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from .configuration import BiologicalMode, BIOLOGICAL_CIRCUITS
from .circuit import Circuit
from .neuron import Neuron
from .synapse import Synapse, Sign
from .neural_engine import NeuralEngine
from .signals import SignalTranslator


@dataclass
class BiologicalBrain:
    """Biological neural layer facade.
    
    Exposes step(sensory_input) -> signals interface for 2.0 integration.
    """
    mode: BiologicalMode = BiologicalMode.LEGACY_2_0
    circuits: Dict[str, Circuit] = field(default_factory=dict)
    engines: Dict[str, NeuralEngine] = field(default_factory=dict)
    translators: Dict[str, SignalTranslator] = field(default_factory=dict)

    def __post_init__(self):
        self._build_circuits()

    def _build_circuits(self) -> None:
        """Construct circuits enabled in BIOLOGICAL_CIRCUITS."""
        if BIOLOGICAL_CIRCUITS.get("startle"):
            circuit = self._build_startle_circuit()
            self.circuits["startle"] = circuit
            self.engines["startle"] = NeuralEngine(circuit)
            self.translators["startle"] = SignalTranslator(circuit)

    def _build_startle_circuit(self) -> Circuit:
        """Minimal startle circuit scaffold for 3.0A.
        
        ~10 neurons, fully inspectable, maps to 2.0 threat/escape pathways.
        """
        c = Circuit(name="startle")
        
        # Sensory entry points (map to 2.0 stimulate keys)
        c.add_neuron(Neuron(
            "VIS_LC_BIO", cell_type="LC", brain_region="VIS",
            neurotransmitter="acetylcholine", threshold=1.0
        ))
        c.add_neuron(Neuron(
            "NOCI_BIO", cell_type="nociceptor", brain_region="SEZ",
            neurotransmitter="glutamate", threshold=1.0
        ))
        
        # Interneurons
        c.add_neuron(Neuron(
            "THREAT_BIO", cell_type="interneuron", brain_region="MB",
            neurotransmitter="dopamine", threshold=1.5
        ))
        
        # Descending neurons (outputs)
        c.add_neuron(Neuron(
            "DN_STARTLE_BIO", cell_type="DN", brain_region="GNG",
            neurotransmitter="glutamate", threshold=2.0
        ))
        c.add_neuron(Neuron(
            "DN_FLIGHT_BIO", cell_type="DN", brain_region="GNG",
            neurotransmitter="glutamate", threshold=2.5
        ))
        
        # Define I/O
        c.input_neurons = ["VIS_LC_BIO", "NOCI_BIO"]
        c.output_neurons = ["DN_STARTLE_BIO", "DN_FLIGHT_BIO", "THREAT_BIO"]
        
        # Connections (weights inspired by group_weights.json, scaled for bio dynamics)
        # VIS_LC -> DN_STARTLE (strong, fast)
        c.connect("VIS_LC_BIO", "DN_STARTLE_BIO", weight=1.2, sign=Sign.EXCITATORY, delay=1)
        # VIS_LC -> THREAT (moderate)
        c.connect("VIS_LC_BIO", "THREAT_BIO", weight=0.8, sign=Sign.EXCITATORY, delay=1)
        # NOCI -> DN_STARTLE (very strong)
        c.connect("NOCI_BIO", "DN_STARTLE_BIO", weight=1.5, sign=Sign.EXCITATORY, delay=1)
        # NOCI -> THREAT (strong)
        c.connect("NOCI_BIO", "THREAT_BIO", weight=1.0, sign=Sign.EXCITATORY, delay=1)
        # THREAT -> DN_FLIGHT (moderate, delayed)
        c.connect("THREAT_BIO", "DN_FLIGHT_BIO", weight=0.9, sign=Sign.EXCITATORY, delay=2)
        
        return c

    def step(self, sensory_input: Dict[str, float]) -> Dict[str, float]:
        """Public interface per framework §9.
        
        Args:
            sensory_input: 2.0 stimulate dict keys (lightLevel, nociception, etc.)
            
        Returns:
            Unified signal dict for 2.0 consumption (prefixed with 'bio_')
        """
        if self.mode == BiologicalMode.LEGACY_2_0:
            return {}

        all_signals = {}
        bio_input = self._map_sensory_input(sensory_input)

        for name, engine in self.engines.items():
            neural_out = engine.step(bio_input)
            signals = self.translators[name].translate(neural_out)
            # Prefix to avoid collision with 2.0 signals
            all_signals.update({f"bio_{k}": v for k, v in signals.items()})

        return all_signals

    def _map_sensory_input(self, stimulate: Dict) -> Dict[str, float]:
        """Translate 2.0 stimulate dict to biological input neuron currents.
        
        Multiple stimuli targeting the same neuron are combined by taking the maximum.
        """
        mapping = {
            "lightLevel": {"VIS_LC_BIO": stimulate.get("lightLevel", 0.0) * 2.0},
            "nociception": {"NOCI_BIO": 3.0 if stimulate.get("nociception") else 0.0},
            "dangerOdor": {"NOCI_BIO": 2.0 if stimulate.get("dangerOdor") else 0.0},
            "touch": {"NOCI_BIO": 1.5 if stimulate.get("touch") else 0.0},
            "temperature": {},  # Handled separately if needed
        }
        merged = {}
        for v in mapping.values():
            for neuron_id, current in v.items():
                if current > 0:
                    merged[neuron_id] = max(merged.get(neuron_id, 0.0), current)
        return merged

    def reset(self) -> None:
        """Reset all circuits to initial state."""
        for engine in self.engines.values():
            engine.reset()

    def get_circuit_state(self, circuit_name: str) -> Optional[Dict]:
        """Get internal state of a circuit for debugging."""
        engine = self.engines.get(circuit_name)
        if engine:
            return engine.get_state()
        return None


# Re-export key types
__all__ = [
    "BiologicalBrain",
    "BiologicalMode",
    "BIOLOGICAL_CIRCUITS",
    "Circuit",
    "Neuron",
    "Synapse",
    "Sign",
    "NeuralEngine",
    "SignalTranslator",
]