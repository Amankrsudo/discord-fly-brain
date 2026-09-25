"""Configuration for Biological Brain 3.0."""

from enum import Enum


class BiologicalMode(Enum):
    """Operating mode for the biological layer."""
    LEGACY_2_0 = "legacy_2_0"
    BIOLOGICAL_3_0 = "biological_3_0"
    HYBRID = "hybrid"


BIOLOGICAL_CIRCUITS = {
    "escape": False,
    "feeding": False,
    "phototaxis": False,
}