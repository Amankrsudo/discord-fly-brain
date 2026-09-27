"""Structured provenance classification for biological parameters.

Provides a typed enum-based taxonomy for tracking the provenance of
every biological parameter in the model. This is a metadata-only
facility — it does not alter any numerical or behavioral computation.

The taxonomy follows the 3.0D roadmap classification:

    DIRECTLY_MEASURED          — Electrophysiology + EM reconstruction in same specimen
    EXPERIMENTALLY_CONSTRAINED — Constrained by experimental fit or recording
    CONNECTOME_DERIVED         — Synapse counts from EM connectome
    PUBLISHED_MODEL_PARAMETER  — Value from a published computational model
    BORROWED_CROSS_CONTEXT     — Borrowed from a different neuron/cell type or species
    FITTED_CALIBRATED          — Manually adjusted or calibrated for simulator behavior
    ESTIMATED                  — Estimated in the source, not measured
    UNKNOWN                    — No source or evidence available
"""

from dataclasses import dataclass
from enum import Enum


class ParameterProvenance(Enum):
    """Typed provenance classification for a biological parameter value."""

    DIRECTLY_MEASURED = "DIRECTLY_MEASURED"
    EXPERIMENTALLY_CONSTRAINED = "EXPERIMENTALLY_CONSTRAINED"
    CONNECTOME_DERIVED = "CONNECTOME_DERIVED"
    PUBLISHED_MODEL_PARAMETER = "PUBLISHED_MODEL_PARAMETER"
    BORROWED_CROSS_CONTEXT = "BORROWED_CROSS_CONTEXT"
    FITTED_CALIBRATED = "FITTED_CALIBRATED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ProvenanceRecord:
    """Records the provenance of a single parameter value.

    A category alone is insufficient; the ``source`` field preserves
    the bibliographic or method-level origin of the value so it can be
    audited and re-checked.
    """

    category: ParameterProvenance
    source: str = ""


_JSON_EVIDENCE_TO_PROVENANCE = {
    "DIRECTLY_MEASURED": ParameterProvenance.DIRECTLY_MEASURED,
    "EXPERIMENTALLY_CONSTRAINED": ParameterProvenance.EXPERIMENTALLY_CONSTRAINED,
    "CONNECTOME_DERIVED": ParameterProvenance.CONNECTOME_DERIVED,
    "ESTIMATED": ParameterProvenance.ESTIMATED,
    "INFERRED": ParameterProvenance.UNKNOWN,
    "APPROXIMATION": ParameterProvenance.UNKNOWN,
}


def evidence_to_provenance(evidence_strings):
    """Convert a list of JSON evidence strings to ParameterProvenance enums.

    Strings not in the mapping default to UNKNOWN. This preserves the
    original evidence while providing structured classification.
    """
    return [
        _JSON_EVIDENCE_TO_PROVENANCE.get(s, ParameterProvenance.UNKNOWN)
        for s in evidence_strings
    ]
