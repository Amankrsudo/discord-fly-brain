"""Configuration for Biological Brain 3.0."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional


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


# --- 3.0D GFS numerical demonstration (opt-in, explicitly labelled) ---------
#
# WHAT THIS IS
# ------------
# An explicitly-labelled, opt-in wiring of the COMPLETED 3.0D GFS model to the
# product surface. It runs the live circuit from an EXPLICIT numerical GF event
# and publishes the 3.0D-8N consumer dictionary.
#
# WHAT THIS IS NOT
# ----------------
# It is NOT a sensory or visual prediction, and NOT a looming model. The
# 3.0D-8L sensory phenomenology is NOT used and the 3.0D-8I sensory-to-live-GF
# coupling remains unsupported: couple_to_live_gf() still raises. A Discord
# command must never be silently represented as a biologically generated
# looming stimulus, because von Reyn et al. 2017 (PMID 28641115) establish
# that GF activity depends on the INTEGRATION of looming features, and this
# configuration supplies none.
#
# THE CONDUCTANCE IS A FIXTURE, NOT A FINDING
# ------------------------------------------
# The three gap_conductance_* fields have NO DEFAULTS and are REQUIRED whenever
# enabled is True. That is deliberate. 3.0D-7U is an UNRESOLVED factor-1000
# unit conflict with no preferred side, so any default would be a covert
# resolution. 3.0D-8I enforces the same rule on GFSCircuit.__init__, which is
# left untouched by this checkpoint.
#
# WHAT IT DOES NOT DO
# --------------------
# It does not resolve 3.0D-7U; does not resolve 3.0D-8G's 80 uS vs 0.08 uS
# conflict; does not modify psi_dlmn_peak_conductance_source; does not
# synthesise an escape probability; and does not claim that GF activation
# implies escape. Per Chai et al. 2025 (PMID 40425165) GF activity contributes
# to action selection while parallel non-GF escape pathways exist, so a GF
# action potential is NOT guaranteed escape.

#: Provenance the 3.0D GFS numerical demonstration REQUIRES. It is checked at
#: construction, not merely documented, so a demonstration cannot be configured
#: while claiming a biological gap-junction conductance.
#:
#: The 1.0 nS value is the SAME numerical fixture the 3.0D-8I/8K/8N tests use.
#: It is declared in nS because that is the unit gap2.mod itself uses, and it
#: is a SOLVER FIXTURE chosen so the live circuit runs at all. It is NOT the
#: real GFS gap-junction conductance, and 3.0D-7U remains an UNRESOLVED
#: factor-1000 unit conflict with NO PREFERRED SIDE. Nothing here chooses
#: between 135 uS, 135 nS, 34.5 uS and 34.5 nS.
GFS_DEMONSTRATION_FIXTURE_PROVENANCE = (
    "3.0D-8I NUMERICAL MECHANISM FIXTURE, NOT A BIOLOGICAL g_gap VALUE. "
    "Chosen so the live circuit runs at all, and declared in nS to match the "
    "unit gap2.mod itself uses. The real GFS gap-junction conductance is the "
    "UNRESOLVED 3.0D-7U value, factor 1000, no preferred side, and 8I does "
    "not choose between 135 uS, 135 nS, 34.5 uS and 34.5 nS."
)

#: Substring every GFS demonstration conductance provenance must contain. Kept
#: as a separate constant so tests and callers assert against one value.
GFS_DEMONSTRATION_PROVENANCE_REQUIRED_FRAGMENT = (
    "NOT A BIOLOGICAL g_gap VALUE"
)


class GFSNumericalDemonstrationConfigError(Exception):
    """Raised when the GFS numerical demonstration is misconfigured."""


@dataclass(frozen=True)
class GFSNumericalDemonstrationConfig:
    """Opt-in configuration for the 3.0D GFS numerical demonstration."""

    gap_conductance_value: Optional[float]
    gap_conductance_unit: Optional[str]
    gap_conductance_provenance: Optional[str]
    enabled: bool = False
    gf_event_time_s: float = 0.0
    duration_ms: float = 5.0
    settle_ms: float = 200.0

    def __post_init__(self) -> None:
        if not self.enabled:
            # Disabled: the conductance fields are unused. They are still
            # REQUIRED arguments, so a caller must always state a position,
            # but nothing is validated because nothing will be built.
            return

        if self.gap_conductance_value is None:
            raise GFSNumericalDemonstrationConfigError(
                "gap_conductance_value is REQUIRED when the GFS numerical "
                "demonstration is enabled. 3.0D-7U is an unresolved "
                "factor-1000 unit conflict with no preferred side, so there is "
                "no value this project may default to."
            )
        if not self.gap_conductance_unit:
            raise GFSNumericalDemonstrationConfigError(
                "gap_conductance_unit is REQUIRED when the GFS numerical "
                "demonstration is enabled. The unit must be stated explicitly "
                "because the 3.0D-7U conflict is precisely a unit "
                "disagreement, and 3.0D-8C never guesses a unit or accepts a "
                "bare number."
            )
        if not self.gap_conductance_provenance or (
            GFS_DEMONSTRATION_PROVENANCE_REQUIRED_FRAGMENT
            not in self.gap_conductance_provenance
        ):
            raise GFSNumericalDemonstrationConfigError(
                "gap_conductance_provenance is REQUIRED when the GFS numerical "
                "demonstration is enabled, and must contain "
                f"{GFS_DEMONSTRATION_PROVENANCE_REQUIRED_FRAGMENT!r} so the "
                "conductance is never presented as a biological GFS value."
            )
        for name, value in (
            ("gf_event_time_s", self.gf_event_time_s),
            ("duration_ms", self.duration_ms),
            ("settle_ms", self.settle_ms),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise GFSNumericalDemonstrationConfigError(
                    f"{name} must be a number, got {value!r}."
                )
        if self.gf_event_time_s < 0.0:
            raise GFSNumericalDemonstrationConfigError(
                f"gf_event_time_s must be non-negative, got "
                f"{self.gf_event_time_s}."
            )
        if self.duration_ms <= 0.0:
            raise GFSNumericalDemonstrationConfigError(
                f"duration_ms must be positive, got {self.duration_ms}."
            )
        if self.settle_ms < 0.0:
            raise GFSNumericalDemonstrationConfigError(
                f"settle_ms must be non-negative, got {self.settle_ms}."
            )

    @classmethod
    def from_mapping(
        cls, mapping: Optional[Mapping[str, Any]]
    ) -> "GFSNumericalDemonstrationConfig":
        """Build a config from a mapping, raising on any missing REQUIRED field.

        This is the boundary an operator or a config file actually uses. A
        missing key is an error, never a default, because the three
        gap-conductance fields have no defensible default while 3.0D-7U is
        unresolved.
        """
        if mapping is None:
            raise GFSNumericalDemonstrationConfigError(
                "A GFS numerical demonstration requires an explicit mapping. "
                "Construct "
                "GFSNumericalDemonstrationConfig(gap_conductance_value=None, "
                "gap_conductance_unit=None, gap_conductance_provenance=None) "
                "for an explicitly DISABLED configuration."
            )
        if not isinstance(mapping, Mapping):
            raise GFSNumericalDemonstrationConfigError(
                f"Expected a mapping, got {type(mapping).__name__}."
            )
        required = (
            "gap_conductance_value",
            "gap_conductance_unit",
            "gap_conductance_provenance",
        )
        missing = [key for key in required if mapping.get(key) is None]
        if missing:
            raise GFSNumericalDemonstrationConfigError(
                f"GFS numerical demonstration configuration is missing "
                f"required field(s): {missing}. These have NO defaults while "
                f"3.0D-7U is unresolved, and omitting one would silently pick a "
                f"side of a factor-1000 unit conflict."
            )
        return cls(
            gap_conductance_value=mapping.get("gap_conductance_value"),
            gap_conductance_unit=mapping.get("gap_conductance_unit"),
            gap_conductance_provenance=mapping.get("gap_conductance_provenance"),
            enabled=bool(mapping.get("enabled", False)),
            gf_event_time_s=mapping.get("gf_event_time_s", 0.0),
            duration_ms=mapping.get("duration_ms", 5.0),
            settle_ms=mapping.get("settle_ms", 200.0),
        )
