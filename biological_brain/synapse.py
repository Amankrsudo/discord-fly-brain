"""Synapse model for Biological Brain 3.0."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List
from .provenance import ParameterProvenance, evidence_to_provenance


class Sign(Enum):
    """Synaptic sign: excitatory or inhibitory."""
    EXCITATORY = 1
    INHIBITORY = -1


@dataclass
class Synapse:
    """Biological connection between neurons.

    Provenance metadata (evidence, provenance) is optional and defaults
    to empty lists, preserving backward compatibility.
    """
    source: str
    target: str
    weight: float = 1.0
    sign: Sign = Sign.EXCITATORY
    delay: int = 1
    neurotransmitter: str = "unknown"
    enabled: bool = True
    synapse_type: str = "chemical"  # "chemical" or "electrical" (gap junction)
    conductance: float = 0.0  # gap junction conductance in µS (electrical only)
    evidence: List[str] = field(default_factory=list)  # raw JSON evidence strings, preserved verbatim
    provenance: List[ParameterProvenance] = field(default_factory=list)  # structured provenance derived from evidence

    def effective_weight(self) -> float:
        """Get the signed weight for propagation."""
        if not self.enabled:
            return 0.0
        return self.weight * self.sign.value

    def __post_init__(self):
        if isinstance(self.sign, str):
            self.sign = Sign[self.sign.upper()]
        if self.delay < 1:
            raise ValueError(f"Synapse delay must be >= 1, got {self.delay}")