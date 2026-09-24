"""Signal translation for Biological Brain 3.0."""

from typing import Dict
from .circuit import Circuit


class SignalTranslator:
    """Map neural activity to high-level signals the 2.0 system understands."""

    def __init__(self, circuit: Circuit):
        self.circuit = circuit

    def translate(self, neural_outputs: Dict[str, float]) -> Dict[str, float]:
        """Translate neural outputs to behavioral signals.
        
        For startle circuit:
        - escape_signal: DN_STARTLE_BIO / DN_FLIGHT_BIO activity
        - threat_signal: THREAT_BIO activity
        
        Returns dict with signal names and normalized values [0, 1].
        """
        signals = {}
        
        # Startle/escape circuit outputs
        if "DN_STARTLE_BIO" in neural_outputs:
            val = neural_outputs["DN_STARTLE_BIO"]
            signals["escape_signal"] = min(1.0, max(0.0, val))
        
        if "DN_FLIGHT_BIO" in neural_outputs:
            val = neural_outputs["DN_FLIGHT_BIO"]
            signals["flight_signal"] = min(1.0, max(0.0, val))
        
        if "THREAT_BIO" in neural_outputs:
            val = neural_outputs["THREAT_BIO"]
            signals["threat_signal"] = min(1.0, max(0.0, val))
        
        # Generic: any output neuron can be exposed as signal
        for neuron_id, value in neural_outputs.items():
            if neuron_id not in ("DN_STARTLE_BIO", "DN_FLIGHT_BIO", "THREAT_BIO"):
                signal_name = neuron_id.lower().replace("_bio", "")
                signals[signal_name] = min(1.0, max(0.0, value))
        
        return signals

    def translate_raw(self, neural_outputs: Dict[str, float]) -> Dict[str, float]:
        """Return raw membrane potentials without normalization."""
        return dict(neural_outputs)