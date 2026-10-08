"""Best-effort exploratory MN5 / PSI / Dalpha7 mechanistic model (3.0D-8E).

WHAT THIS IS
------------
A transparent, best-effort EXPLORATORY model that runs across explicit
plausible parameter ranges. Its purpose is to move the project from
"cannot model because some biological parameters are unknown" to "can
run a transparent best-effort model across explicit plausible parameter
ranges" -- WITHOUT claiming that any unknown biology has become known.

This is an EXPLORATORY MODEL LAYER, separate from the evidence-safe
reduced model in ``reduced_mn5.py``. It does not replace it, it does
not read from or write to the frozen evidence registry
(``research/model_input_freeze.csv``). It is authorized for conditional
model-derived analyses only; it does not authorize native biological
measurement claims.

PARAMETER TIERS (never collapsed)
---------------------------------
TIER A  native MN5 measurements -- the frozen project values, carried
        with provenance NATIVE_EXPERIMENTAL_MEASUREMENT. The whole-cell
        capacitance conflict (C-01, 43 +/- 2 pF versus 127 +/- 16 pF)
        is carried as TWO explicit variants and is never adjudicated.
TIER B  literature-constrained ranges -- provenance
        LITERATURE_DERIVED_PASSIVE_PARAMETER. Ra, specific Cm, specific
        Rm and the generic cholinergic reversal range are NOT native
        MN5 measurements and are never labelled as such.
TIER C  free exploratory parameters -- provenance MODEL_ASSUMPTION.
        g_PSI, g_Dalpha7, Dalpha7 density/kinetics, PSI synaptic
        kinetics, the exploratory Dalpha7 reversal range and the
        effective spatial transfer ratio are not known sufficiently
        and carry no biological value.

MODEL
-----
A two-compartment (soma + PSI-contact-bearing process) cable-style
abstraction, integrated with Forward Euler:

    PSI synaptic conductance input (double-exponential, kinetics are
    MODEL_ASSUMPTION)
      -> local process depolarization
      -> spatial attenuation across the axial resistance
      -> somatic voltage response
      -> threshold comparison against the measured MN5 threshold

An optional Dalpha7 receptor component (g_Dalpha7, E_Dalpha7,
tau_activation, tau_desensitization, optional Ca-permeability factor)
can be enabled; it is exploratory and assumption-dependent, and it is
never used to retroactively justify the existence or magnitude of the
PSI conductance.

SPATIAL TRANSFER
----------------
Two modes, kept apart:

    "cable"    attenuation is DERIVED from Ra/Rm/Cm and the assumed
               geometry -> MODEL_DERIVED_ESTIMATE. The experimental
               spatial-transfer gate remains closed.
    "explicit" the caller supplies transfer_ratio directly ->
               MODEL_ASSUMPTION. It is never a measurement.

CALIBRATION
-----------
The model may be calibrated against the published MN5 somatic EPSP
(4.71 +/- 0.35 mV) as a COMPARISON TARGET ONLY. The procedure is
labelled MODEL_CALIBRATION and the fitted conductance is preserved as a
MODEL-DERIVED ESTIMATE. It is not a measurement of the PSI->MN5
synaptic conductance, which remains BLOCKED. Calibration always runs
with the Dalpha7 component disabled.

MODEL AUTHORIZATION (not native measurement authorization)
-----------------------------------------------------------
    PSI->MN5 postsynaptic spatial voltage transfer:
        MODEL-AUTHORIZED / ANATOMY + LITERATURE CONSTRAINED
    Dalpha7 biological conductance:
        MODEL-AUTHORIZED / CHANNEL-CONSTRAINED /
        NATIVE VALUE MODEL-DERIVED

The spatial-transfer model uses a separate abstract cable bridge:
no anatomically reconstructed contact-to-soma path exists. Its transfer
is MODEL-DERIVED and is not an experimental voltage-transfer measurement.
Recombinant Dalpha7 electrophysiology constrains channel-level behavior,
but native MN5 receptor number, density and open probability are not
directly measured; effective native conductance remains MODEL-DERIVED.
No simulation output is a native biological measurement.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .model_framework import (
    ModelParameter,
    ModelProvenance,
    ParameterSet,
    ParameterStatus,
)

__all__ = [
    "MODEL_NAME", "MODEL_VERSION",
    "GATE_STATEMENT_TRANSFER", "GATE_STATEMENT_DALPHA7",
    "CALIBRATION_METHOD", "EXPLORATORY_STATEMENT",
    "DALPHA7_STATEMENT", "ROBUST", "PARAMETER_DEPENDENT",
    "UNCONSTRAINED", "RobustnessClass",
    "TIER_A", "TIER_B", "TIER_C", "TIER_GEOMETRY",
    "DEFAULT_SWEEP_GRID", "FREE_PARAMETERS",
    "ExploratoryParameter", "ExploratorySimulationResult",
    "CalibrationRecord", "SensitivityResult",
    "ExploratoryMN5Model",
]

MODEL_NAME = "exploratory_mn5"
MODEL_VERSION = "0.1.0"

GATE_STATEMENT_TRANSFER = (
    "PSI→MN5 postsynaptic spatial voltage transfer: "
    "MODEL-AUTHORIZED / ANATOMY + LITERATURE CONSTRAINED")
GATE_STATEMENT_DALPHA7 = (
    "Dα7 biological conductance: MODEL-AUTHORIZED / CHANNEL-CONSTRAINED / "
    "NATIVE VALUE MODEL-DERIVED")

#: Label for the fitting procedure itself (the fitted VALUE is preserved
#: as a MODEL-DERIVED ESTIMATE, never as a measurement).
CALIBRATION_METHOD = "MODEL_CALIBRATION"

EXPLORATORY_STATEMENT = (
    "This model is not a measurement of MN5 spatial voltage transfer "
    "or Dα7 conductance.")

DALPHA7_STATEMENT = (
    "Dα7 component is exploratory and assumption-dependent.")

TIER_A = "TIER_A_NATIVE_MEASUREMENT"
TIER_B = "TIER_B_LITERATURE_DERIVED_RANGE"
TIER_C = "TIER_C_FREE_EXPLORATORY_PARAMETER"
TIER_GEOMETRY = "TIER_GEOMETRY_MODEL_ASSUMPTION"


class RobustnessClass(Enum):
    """How a conclusion behaves across plausible parameter sets."""

    ROBUST = "ROBUST"
    PARAMETER_DEPENDENT = "PARAMETER-DEPENDENT"
    UNCONSTRAINED = "UNCONSTRAINED"


ROBUST = RobustnessClass.ROBUST
PARAMETER_DEPENDENT = RobustnessClass.PARAMETER_DEPENDENT
UNCONSTRAINED = RobustnessClass.UNCONSTRAINED

#: Broad logarithmic exploratory ranges for the two free conductances.
#: Neither range is biologically measured.
DEFAULT_SWEEP_GRID: Dict[str, Tuple[float, ...]] = {
    "axial_resistivity_ohm_cm": (30.0, 90.0, 200.0, 400.0),
    "specific_membrane_capacitance_uf_cm2": (0.6, 1.15, 2.6),
    "specific_membrane_resistance_kohm_cm2": (6.0, 10.0, 20.0, 26.0),
    "cholinergic_reversal_mv": (-15.0, 0.0, 10.0),
    "g_psi_ns": (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
    "g_dalpha7_ns": (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0),
}

#: Tier C parameters whose plausible range current evidence cannot
#: bound. Names are the parameter-table names.
FREE_PARAMETERS = frozenset({
    "PSI synaptic peak conductance",
    "Dα7 reversal potential (exploratory)",
    "Dα7 maximal conductance",
    "Dα7 receptor density (relative)",
    "Dα7 activation time constant",
    "Dα7 desensitization time constant",
    "Dα7 steady-state desensitization fraction",
    "PSI synaptic rise time constant",
    "PSI synaptic decay time constant",
    "effective spatial transfer ratio",
    "process length (soma to PSI-contact region)",
    "process diameter",
    "synapse location along the assumed process",
})

#: Maps the sweep-grid keys used by the sensitivity plan to the
#: parameter-table names.
SWEEP_PARAMETER_NAMES: Dict[str, str] = {
    "axial_resistivity_ohm_cm": "axial resistivity",
    "specific_membrane_capacitance_uf_cm2":
        "specific membrane capacitance",
    "specific_membrane_resistance_kohm_cm2":
        "specific membrane resistance",
    "cholinergic_reversal_mv":
        "cholinergic reversal potential (exploratory)",
    "g_psi_ns": "PSI synaptic peak conductance",
    "g_dalpha7_ns": "Dα7 maximal conductance",
}


# --- parameter construction ----------------------------------------------


def _param(name: str, symbol: str, value: Optional[float], unit: str,
           provenance: ModelProvenance, status: ParameterStatus,
           source: str, tier: str, plausible_range: Optional[Tuple[
               float, float]] = None,
           range_scale: str = "linear", conflict: str = "",
           gate: str = "", notes: str = "") -> ModelParameter:
    return ModelParameter(
        name=name, symbol=symbol, value=value, unit=unit,
        provenance=provenance, status=status, source=source,
        object="Drosophila MN5", gate=gate,
        evidence_strength=tier, notes=notes, conflict=conflict)


def _tier_a(name: str, symbol: str, value: float, unit: str, source: str,
            plausible_range: Optional[Tuple[float, float]] = None,
            conflict: str = "", notes: str = "",
            status: ParameterStatus = ParameterStatus.SAFE
            ) -> ModelParameter:
    return _param(name, symbol, value, unit,
                  ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT,
                  status, source, TIER_A, plausible_range,
                  conflict=conflict, notes=notes)


def _tier_b(name: str, symbol: str, value: float, unit: str, source: str,
            plausible_range: Tuple[float, float],
            range_scale: str = "linear", notes: str = ""
            ) -> ModelParameter:
    return _param(name, symbol, value, unit,
                  ModelProvenance.LITERATURE_DERIVED_PASSIVE_PARAMETER,
                  ParameterStatus.ASSUMPTION, source, TIER_B,
                  plausible_range, range_scale, notes=notes)


def _tier_c(name: str, symbol: str, value: Optional[float], unit: str,
            source: str,
            plausible_range: Optional[Tuple[float, float]] = None,
            range_scale: str = "linear", notes: str = ""
            ) -> ModelParameter:
    return _param(name, symbol, value, unit,
                  ModelProvenance.MODEL_ASSUMPTION,
                  ParameterStatus.ASSUMPTION, source, TIER_C,
                  plausible_range, range_scale, notes=notes)


def _geometry(name: str, symbol: str, value: float, unit: str,
              source: str, plausible_range: Tuple[float, float],
              notes: str = "") -> ModelParameter:
    return _param(name, symbol, value, unit,
                  ModelProvenance.MODEL_ASSUMPTION,
                  ParameterStatus.ASSUMPTION, source, TIER_GEOMETRY,
                  plausible_range, notes=notes)


# --- the exploratory parameter set ---------------------------------------


def _build_exploratory_parameters() -> List[ModelParameter]:
    """The complete exploratory parameter table.

    Tier A values are echoed from the frozen registry so the two can be
    cross-checked; nothing here is written back to the registry.
    """
    out: List[ModelParameter] = []

    # TIER A -- native MN5 measurements (frozen project values).
    out.append(_tier_a(
        "MN5 resting potential", "V_rest", -67.8, "mV",
        "project freeze; Ryglewski, Kilo & Duch 2014 Eur J Neurosci "
        "39:151 (n=13, -67.8 +/- 5.5 SD)",
        plausible_range=(-73.3, -62.3),
        notes="Somatic whole-cell, zero holding current after break-in. "
              "Strongest MN5 record."))
    out.append(_tier_a(
        "MN5 spike threshold", "V_th", -24.1, "mV",
        "project freeze; Ryglewski, Kilo & Duch 2014 Eur J Neurosci "
        "39:151 (n=11, -24.1 +/- 8.2 SD)",
        plausible_range=(-32.3, -15.9),
        notes="Steepest slope at AP onset."))
    out.append(_tier_a(
        "MN5 action potential amplitude", "AP_amp", 45.5, "mV",
        "project freeze; Ryglewski, Kilo & Duch 2014 Eur J Neurosci "
        "39:151 (n=13, 45.5 +/- 8.6 SD)",
        plausible_range=(36.9, 54.1),
        notes="Used only as a reference figure; no AP shape is modelled."))
    out.append(_tier_a(
        "MN5 input resistance (set 1)", "Rin", 102.0, "MΩ",
        "project freeze; Fayyazuddin+ 2006 PLoS Biol 4(3):e63 "
        "(n=22, 102 +/- 12 MΩ)",
        plausible_range=(97.0, 102.0),
        notes="Genuine native measurement. Used as the soma leak "
              "conductance g_leak_s = 1/Rin; that USE is a model "
              "construction, the measurement itself is native. Set 2 "
              "(Herrera-Valdez+ 2013, 97 +/- 31 MΩ, n=52) is the "
              "independent second set; both are carried in the table."))
    out.append(_tier_a(
        "MN5 input resistance (set 2)", "Rin", 97.0, "MΩ",
        "project freeze; Herrera-Valdez+ 2013 J Comput Neurosci "
        "34:211 (n=52, 97 +/- 31 MΩ)",
        plausible_range=(97.0, 102.0),
        notes="Second independent set, broader n, consistent with set 1. "
              "The model runs on set 1 by default; the plausible band "
              "97-102 MΩ spans both sets."))
    # The capacitance conflict is carried as TWO explicit variants and is
    # never adjudicated. The freeze records both variants as ASSUMPTION
    # because they are contested; the provenance stays native.
    out.append(_tier_a(
        "MN5 whole-cell capacitance (variant A)", "Cm", 43.0, "pF",
        "project freeze; Fayyazuddin+ 2006 PLoS Biol 4(3):e63 "
        "(n=22, 43 +/- 2 pF)",
        plausible_range=(41.0, 45.0),
        conflict="C-01 unresolved (~2.95x)",
        status=ParameterStatus.ASSUMPTION,
        notes="CONTESTED. Contradicted by variant B; using either "
              "requires explicitly naming the variant. NOT "
              "compartment-specific."))
    out.append(_tier_a(
        "MN5 whole-cell capacitance (variant B)", "Cm", 127.0, "pF",
        "project freeze; Ryglewski & Duch 2009 J Neurophysiol "
        "102:3673 (127 +/- 16 SD)",
        plausible_range=(111.0, 143.0),
        conflict="C-01 unresolved (~2.95x)",
        status=ParameterStatus.ASSUMPTION,
        notes="CONTESTED. Authors flag dendritic space-clamp as a Cm "
              "error source; the same mean and SD are re-reported by "
              "Herrera-Valdez+ 2013 and count as ONE measurement."))

    # TIER B -- literature-constrained passive ranges. NOT native MN5
    # measurements.
    out.append(_tier_b(
        "axial resistivity", "Ra", 90.0, "Ω·cm",
        "Drosophila modeling literature plus MN5 model precedent "
        "(Ryglewski & Duch 2009, via Meseke et al. 2009 generic "
        "insect defaults)",
        (30.0, 400.0),
        notes="NOT a native MN5 measurement. The only value ever "
              "applied to MN5 is a generic insect default adopted "
              "because it was 'consistent with' measured Rin/Cm; an "
              "internal-consistency failure of that claim is flagged in "
              "the project audit."))
    out.append(_tier_b(
        "specific membrane capacitance", "Cm_spec", 1.15, "µF/cm²",
        "Drosophila modeling literature (Ryglewski & Duch 2009, via "
        "Meseke et al. 2009 generic insect defaults)",
        (0.6, 2.6),
        notes="NOT a native MN5 measurement. Distinct from the "
              "contested whole-cell capacitance (C-01), which is a "
              "TIER A native measurement."))
    out.append(_tier_b(
        "specific membrane resistance", "Rm", 6.0, "kΩ·cm²",
        "derived from literature/model g_pas ranges (g_pas = "
        "1.667e-4 S/cm² -> Rm = 6 kΩ·cm², Ryglewski & Duch 2009)",
        (6.0, 26.0),
        notes="The nominal 6 kΩ·cm² is the historical MN5-model value "
              "and is CROSS-CONTEXT/MODEL-DERIVED, not a native MN5 "
              "measurement. No Drosophila-specific Rm has ever been "
              "measured."))
    out.append(_tier_c(
        "cholinergic reversal potential (exploratory)", "E_syn", 0.0,
        "mV",
        "no direct PSI→MN5 reversal-potential measurement; exploratory "
        "model assumption",
        (-15.0, 10.0),
        notes="MODEL-ASSUMED exploratory range; not a biological "
              "constraint and not a PSI→MN5 measurement. The 0 mV value is a "
              "computational-model precedent, not a measurement."))
    out.append(_tier_c(
        "Dα7 reversal potential (exploratory)", "E_Da7", 0.0, "mV",
        "no direct Dα7 reversal-potential source; exploratory model "
        "assumption",
        (-15.0, 10.0),
        notes="MODEL-ASSUMED exploratory range, not a native Dα7 or "
              "PSI→MN5 measurement. Carried separately from E_syn so "
              "the two can be swept independently."))

    # TIER C -- free exploratory parameters. MODEL_ASSUMPTION.
    out.append(_tier_c(
        "PSI synaptic peak conductance", "g_PSI", 1.0, "nS",
        "no source; free exploratory parameter",
        (0.01, 1000.0), range_scale="log",
        notes="FREE. No PSI→MN5 synaptic conductance has ever been "
              "measured in any source. The nominal 1 nS is a round "
              "exploratory midpoint, not an estimate. Swept on a broad "
              "logarithmic range; the range is NOT biologically "
              "measured."))
    out.append(_tier_c(
        "Dα7 maximal conductance", "g_Dα7", 1.0, "nS",
        "no source; free exploratory parameter",
        (0.01, 1000.0), range_scale="log",
        notes="FREE. No native Dα7 conductance exists. The nominal 1 nS "
              "is a round exploratory midpoint, not an estimate. Never "
              "used to retroactively justify the PSI conductance."))
    out.append(_tier_c(
        "Dα7 receptor density (relative)", "Dα7_density", 1.0,
        "relative",
        "no source; free exploratory parameter",
        (0.01, 100.0), range_scale="log",
        notes="FREE. No Dα7 density at PSI→MN5 exists. Relative units "
              "only; no absolute density is implied."))
    out.append(_tier_c(
        "Dα7 activation time constant", "tau_act_Da7", 1.0, "ms",
        "no source; millisecond-scale exploratory kinetics",
        (0.1, 10.0),
        notes="FREE. Millisecond-scale exploratory kinetics only; NOT "
              "MN5/PSI-native."))
    out.append(_tier_c(
        "Dα7 desensitization time constant", "tau_des_Da7", 5.0, "ms",
        "no source; millisecond-scale exploratory kinetics",
        (1.0, 50.0),
        notes="FREE. Millisecond-scale exploratory kinetics only; NOT "
              "MN5/PSI-native."))
    out.append(_tier_c(
        "Dα7 steady-state desensitization fraction", "D_inf", 0.5,
        "fraction",
        "no source; free exploratory parameter",
        (0.0, 0.95),
        notes="FREE. Fraction of the peak conductance lost to "
              "desensitization at steady state."))
    out.append(_tier_c(
        "PSI synaptic rise time constant", "tau_rise", 0.5, "ms",
        "no source; millisecond-scale exploratory kinetics",
        (0.1, 2.0),
        notes="FREE. Millisecond-scale exploratory kinetics only; NOT "
              "MN5/PSI-native."))
    out.append(_tier_c(
        "PSI synaptic decay time constant", "tau_decay", 2.0, "ms",
        "no source; millisecond-scale exploratory kinetics",
        (0.5, 10.0),
        notes="FREE. Millisecond-scale exploratory kinetics only; NOT "
              "MN5/PSI-native."))
    out.append(_tier_c(
        "effective spatial transfer ratio", "transfer_ratio", None,
        "fraction",
        "no source; free exploratory parameter, used only in "
        "explicit-transfer mode",
        (0.0, 1.0),
        notes="FREE. Never measured for MN5. Used ONLY when "
              "transfer_mode='explicit'; the caller must supply it and "
              "it remains a MODEL_ASSUMPTION. In cable mode it is not "
              "used at all."))

    # GEOMETRY -- unsupported by measurement, hence MODEL_ASSUMPTION.
    out.append(_geometry(
        "process length (soma to PSI-contact region)", "L_proc", 50.0,
        "µm",
        "assumption anchored on the documented PSI contact span "
        "(Fayyazuddin+ 2006: contacts 'span 50 um' of the PDMN)",
        (50.0, 500.0),
        notes="The documented 50 µm is the contact SPAN in the "
              "peripheral nerve, not a measured process length. The "
              "soma-to-contact path length is unmeasured; 50 µm is a "
              "lower-anchored assumption."))
    out.append(_geometry(
        "process diameter", "d_proc", 0.5, "µm",
        "no source; MN5 process diameter is unmeasured",
        (0.2, 2.0),
        notes="FREE. MN5 process diameter has never been measured."))
    out.append(_geometry(
        "synapse location along the assumed process", "syn_loc", 50.0,
        "µm",
        "assumption: the PSI contacts sit within the documented 50 µm "
        "contact span",
        (0.0, 50.0),
        notes="Descriptive in the two-compartment reduction: the whole "
              "process is one compartment, so the synaptic input is "
              "placed on the process compartment. The location is "
              "reported metadata for the geometry assumptions, not an "
              "additional electrical degree of freedom."))
    return out


# --- result records -------------------------------------------------------


@dataclass(frozen=True)
class ExploratoryParameter:
    """One row of the exploratory parameter table, with its tier."""

    parameter: ModelParameter
    tier: str
    plausible_range: Optional[Tuple[float, float]]
    range_scale: str

    def as_dict(self) -> Dict[str, object]:
        p = self.parameter
        return {
            "parameter": p.name, "symbol": p.symbol, "tier": self.tier,
            "value": p.value, "unit": p.unit,
            "plausible_range": self.plausible_range,
            "range_scale": self.range_scale,
            "provenance": p.provenance.value, "status": p.status.value,
            "source": p.source, "object": p.object, "conflict": p.conflict,
            "gate": p.gate, "notes": p.notes,
        }


@dataclass(frozen=True)
class ExploratorySimulationResult:
    """One exploratory simulation. Every output is a MODEL-DERIVED
    ESTIMATE unless it is directly a supplied native measurement."""

    model_name: str
    model_version: str
    capacitance_variant: str
    dalpha7_enabled: bool
    transfer_mode: str
    parameters: Tuple[Dict[str, object], ...]
    local_synaptic_peak_depolarization_mv: float
    somatic_peak_depolarization_mv: float
    spatial_attenuation_ratio: float
    spatial_attenuation_provenance: str
    peak_depolarization_mv: float
    threshold_excursion_required_mv: float
    threshold_crossing: bool
    spike_model_output: str
    time_to_peak_ms: float
    output_provenance: str
    is_measurement: bool
    dalpha7_statement: str
    gates: Dict[str, str]
    statement: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "model": self.model_name, "version": self.model_version,
            "kind": "best-effort exploratory mechanistic model",
            "capacitance_variant": self.capacitance_variant,
            "dalpha7_enabled": self.dalpha7_enabled,
            "transfer_mode": self.transfer_mode,
            "parameters": list(self.parameters),
            "local_synaptic_peak_depolarization_mv":
                self.local_synaptic_peak_depolarization_mv,
            "somatic_peak_depolarization_mv":
                self.somatic_peak_depolarization_mv,
            "spatial_attenuation_ratio": self.spatial_attenuation_ratio,
            "spatial_attenuation_provenance":
                self.spatial_attenuation_provenance,
            "peak_depolarization_mv": self.peak_depolarization_mv,
            "threshold_excursion_required_mv":
                self.threshold_excursion_required_mv,
            "threshold_crossing": self.threshold_crossing,
            "spike_model_output": self.spike_model_output,
            "time_to_peak_ms": self.time_to_peak_ms,
            "output_provenance": self.output_provenance,
            "is_measurement": self.is_measurement,
            "dalpha7_statement": self.dalpha7_statement,
            "gates": dict(self.gates),
            "statement": self.statement,
        }


@dataclass(frozen=True)
class CalibrationRecord:
    """A calibration against the published somatic EPSP.

    The target is a NATIVE measurement used as a COMPARISON TARGET
    ONLY. The procedure is MODEL_CALIBRATION; the fitted conductance is
    a MODEL-DERIVED ESTIMATE and is NOT a measurement of the PSI→MN5
    synaptic conductance, which remains BLOCKED.
    """

    method: str
    target_mv: float
    target_uncertainty_mv: float
    target_provenance: str
    target_source: str
    fitted_g_psi_ns: float
    fitted_provenance: str
    resulting_somatic_peak_depolarization_mv: float
    capacitance_variant: str
    dalpha7_enabled: bool
    statement: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "method": self.method,
            "target_mv": self.target_mv,
            "target_uncertainty_mv": self.target_uncertainty_mv,
            "target_provenance": self.target_provenance,
            "target_source": self.target_source,
            "fitted_g_psi_ns": self.fitted_g_psi_ns,
            "fitted_provenance": self.fitted_provenance,
            "resulting_somatic_peak_depolarization_mv":
                self.resulting_somatic_peak_depolarization_mv,
            "capacitance_variant": self.capacitance_variant,
            "dalpha7_enabled": self.dalpha7_enabled,
            "statement": self.statement,
        }


@dataclass(frozen=True)
class SensitivityResult:
    """Sweep results and robustness classifications."""

    design: Dict[str, object]
    total_runs: int
    ofat: Dict[str, Dict[str, object]]
    designs: Dict[str, Dict[str, object]]
    conclusions: Dict[str, str]
    classification_rules: Dict[str, str]
    statement: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "design": self.design,
            "total_runs": self.total_runs,
            "ofat": self.ofat,
            "designs": self.designs,
            "conclusions": dict(self.conclusions),
            "classification_rules": dict(self.classification_rules),
            "statement": self.statement,
        }


# --- the model ------------------------------------------------------------


class ExploratoryMN5Model:
    """Best-effort exploratory two-compartment MN5 model.

    The model owns a PRIVATE :class:`ParameterSet`. It never touches
    the frozen evidence registry: no value is read from
    ``model_input_freeze.csv`` at run time and no value is ever
    written back, so no synthetic measurement can enter the registry.
    """

    def __init__(self, capacitance_variant: str,
                 dalpha7_enabled: bool = False,
                 transfer_mode: str = "cable",
                 transfer_ratio: Optional[float] = None) -> None:
        if capacitance_variant not in ("A", "B"):
            raise ValueError(
                "capacitance_variant must be explicitly 'A' (43 +/- 2 pF, "
                "Fayyazuddin 2006) or 'B' (127 +/- 16 pF, Ryglewski & "
                "Duch 2009). The C-01 conflict must never be resolved "
                "silently; there is no default.")
        if transfer_mode not in ("cable", "explicit"):
            raise ValueError(
                "transfer_mode must be 'cable' (attenuation DERIVED from "
                "Ra/Rm/Cm and assumed geometry -> MODEL_DERIVED_ESTIMATE) "
                "or 'explicit' (caller-supplied transfer_ratio -> "
                "MODEL_ASSUMPTION).")
        if transfer_mode == "explicit" and transfer_ratio is None:
            raise ValueError(
                "explicit transfer mode requires a caller-supplied "
                "transfer_ratio; it is a MODEL_ASSUMPTION and is never "
                "defaulted or measured.")
        if transfer_ratio is not None and not 0.0 <= transfer_ratio <= 1.0:
            raise ValueError(
                "transfer_ratio must lie in [0, 1]; it is an assumed "
                "fraction, not a measured quantity.")
        self._capacitance_variant = capacitance_variant
        self._dalpha7_enabled = dalpha7_enabled
        self._transfer_mode = transfer_mode
        self._explicit_transfer_ratio = transfer_ratio

        self._parameters = _build_exploratory_parameters()
        self._set = ParameterSet(self._parameters)
        self._tiers: Dict[str, str] = {}
        for p in self._parameters:
            self._tiers[p.name] = p.evidence_strength
        # Ranges are carried alongside (ModelParameter has no range
        # field); they are reported, never used to fill a value.
        self._ranges = {
            "MN5 resting potential": (-73.3, -62.3),
            "MN5 spike threshold": (-32.3, -15.9),
            "MN5 action potential amplitude": (36.9, 54.1),
            "MN5 input resistance (set 1)": (97.0, 102.0),
            "MN5 input resistance (set 2)": (97.0, 102.0),
            "MN5 whole-cell capacitance (variant A)": (41.0, 45.0),
            "MN5 whole-cell capacitance (variant B)": (111.0, 143.0),
            "axial resistivity": (30.0, 400.0),
            "specific membrane capacitance": (0.6, 2.6),
            "specific membrane resistance": (6.0, 26.0),
            "cholinergic reversal potential (exploratory)": (-15.0, 10.0),
            "Dα7 reversal potential (exploratory)": (-15.0, 10.0),
            "PSI synaptic peak conductance": (0.01, 1000.0),
            "Dα7 maximal conductance": (0.01, 1000.0),
            "Dα7 receptor density (relative)": (0.01, 100.0),
            "Dα7 activation time constant": (0.1, 10.0),
            "Dα7 desensitization time constant": (1.0, 50.0),
            "Dα7 steady-state desensitization fraction": (0.0, 0.95),
            "PSI synaptic rise time constant": (0.1, 2.0),
            "PSI synaptic decay time constant": (0.5, 10.0),
            "effective spatial transfer ratio": (0.0, 1.0),
            "process length (soma to PSI-contact region)": (50.0, 500.0),
            "process diameter": (0.2, 2.0),
            "synapse location along the assumed process": (0.0, 50.0),
        }
        self._range_scales = {
            "PSI synaptic peak conductance": "log",
            "Dα7 maximal conductance": "log",
            "Dα7 receptor density (relative)": "log",
        }

    # -- parameter surface --------------------------------------------------

    @property
    def capacitance_variant(self) -> str:
        return self._capacitance_variant

    @property
    def dalpha7_enabled(self) -> bool:
        return self._dalpha7_enabled

    @property
    def transfer_mode(self) -> str:
        return self._transfer_mode

    @property
    def parameters(self) -> ParameterSet:
        """The model's PRIVATE parameter set (not the evidence registry)."""
        return self._set

    def parameter_table(self) -> List[Dict[str, object]]:
        out = []
        for p in self._parameters:
            out.append(ExploratoryParameter(
                parameter=p, tier=self._tiers[p.name],
                plausible_range=self._ranges.get(p.name),
                range_scale=self._range_scales.get(p.name, "linear")
            ).as_dict())
        return out

    def _value(self, name: str,
               overrides: Optional[Mapping[str, float]] = None) -> float:
        if overrides and name in overrides:
            return float(overrides[name])
        return float(self._set.require(name))

    # -- simulation ---------------------------------------------------------

    def simulate(self,
                 overrides: Optional[Mapping[str, float]] = None,
                 dt_ms: float = 0.01,
                 duration_ms: float = 15.0
                 ) -> ExploratorySimulationResult:
        """Run one exploratory simulation.

        ``overrides`` supplies alternative values for ANY parameter by
        name (the sensitivity analysis uses this). Overrides are applied
        to a local copy: the model's own parameter set is never
        modified, so a sweep can never overwrite a source parameter.
        """
        if dt_ms <= 0 or duration_ms <= 0:
            raise ValueError("dt_ms and duration_ms must be positive.")
        overrides = dict(overrides or {})
        unknown = [k for k in overrides if k not in self._set]
        if unknown:
            raise KeyError(
                f"unknown exploratory parameter(s): {sorted(unknown)}")

        # -- resolved parameter values (local copy; no mutation) --
        v_rest = self._value("MN5 resting potential", overrides)
        v_th = self._value("MN5 spike threshold", overrides)
        rin_mohm = self._value(
            "MN5 input resistance (set 1)", overrides)
        cm_pf = self._value(
            f"MN5 whole-cell capacitance (variant "
            f"{self._capacitance_variant})", overrides)
        ra_ohm_cm = self._value("axial resistivity", overrides)
        cm_spec_uf_cm2 = self._value(
            "specific membrane capacitance", overrides)
        rm_kohm_cm2 = self._value(
            "specific membrane resistance", overrides)
        e_syn = self._value(
            "cholinergic reversal potential (exploratory)", overrides)
        e_da7 = self._value("Dα7 reversal potential (exploratory)",
                            overrides)
        g_psi = self._value("PSI synaptic peak conductance", overrides)
        tau_rise = self._value("PSI synaptic rise time constant", overrides)
        tau_decay = self._value("PSI synaptic decay time constant",
                                overrides)
        l_proc_um = self._value(
            "process length (soma to PSI-contact region)", overrides)
        d_proc_um = self._value("process diameter", overrides)

        # -- derived constants (units: mV, nS, pF, ms, MΩ) --
        g_leak_s_ns = 1000.0 / rin_mohm
        # cylindrical process membrane area, ends neglected
        area_proc_cm2 = math.pi * d_proc_um * l_proc_um * 1e-8
        g_leak_p_ns = area_proc_cm2 * 1e6 / rm_kohm_cm2
        c_proc_pf = area_proc_cm2 * cm_spec_uf_cm2 * 1e6
        r_axial_mohm = (ra_ohm_cm * (l_proc_um * 1e-4)
                        / (math.pi * (d_proc_um / 2.0 * 1e-4) ** 2)) / 1e6
        g_axial_ns = 1000.0 / r_axial_mohm

        # -- prescribed conductance time courses --
        n_steps = int(round(duration_ms / dt_ms))
        g_syn = self._double_exponential_course(
            n_steps, dt_ms, g_psi, tau_rise, tau_decay)
        g_da7: List[float] = []
        if self._dalpha7_enabled:
            g_da7_max = self._value("Dα7 maximal conductance", overrides)
            tau_act = self._value("Dα7 activation time constant", overrides)
            tau_des = self._value(
                "Dα7 desensitization time constant", overrides)
            d_inf = self._value(
                "Dα7 steady-state desensitization fraction", overrides)
            g_da7 = self._dalpha7_course(
                n_steps, dt_ms, g_da7_max, tau_act, tau_des, d_inf)

        # -- Forward Euler integration of the two-compartment model --
        # The synaptic and Dα7 conductances are prescribed (not
        # voltage-dependent), so the system is linear with a
        # time-varying input. Explicit Euler is stable only when
        # dt < 2*C/g_total for each compartment; at the large
        # conductances of the exploratory sweep the nominal step
        # would overshoot and diverge, so each step is subdivided
        # until the stability criterion holds (safety factor 0.5).
        # The subdivision is a numerical-stability measure only:
        # it changes no parameter, no provenance and no conclusion.
        v_s = v_rest
        v_p = v_rest
        local_peak = 0.0
        somatic_peak = 0.0
        time_to_peak = 0.0
        for i in range(n_steps):
            g_syn_i = g_syn[i]
            g_da7_i = g_da7[i] if g_da7 else 0.0
            g_s_total = g_leak_s_ns + g_axial_ns
            g_p_total = (g_leak_p_ns + g_axial_ns + g_syn_i
                         + g_da7_i)
            tau_s_ms = cm_pf / g_s_total
            tau_p_ms = c_proc_pf / g_p_total
            n_sub = max(1, int(math.ceil(
                dt_ms / (0.5 * min(tau_s_ms, tau_p_ms)))))
            h = dt_ms / n_sub
            for _ in range(n_sub):
                i_syn_p = (g_syn_i * (e_syn - v_p)
                           + g_da7_i * (e_da7 - v_p))
                i_axial_sp = (v_s - v_p) / r_axial_mohm  # nA
                i_axial_ps = (v_p - v_s) / r_axial_mohm  # nA
                # currents in pA: nS*mV = pA; nA = 1000 pA
                dv_s = ((-g_leak_s_ns * (v_s - v_rest)
                         - 1000.0 * i_axial_sp) / cm_pf)
                dv_p = ((-g_leak_p_ns * (v_p - v_rest)
                         - 1000.0 * i_axial_ps + i_syn_p)
                        / c_proc_pf)
                v_s += dv_s * h
                v_p += dv_p * h
            if v_p - v_rest > local_peak:
                local_peak = v_p - v_rest
            if v_s - v_rest > somatic_peak:
                somatic_peak = v_s - v_rest
                time_to_peak = i * dt_ms

        # -- spatial transfer --
        if local_peak > 0.0:
            cable_attenuation = somatic_peak / local_peak
        else:
            cable_attenuation = 0.0
        if self._transfer_mode == "explicit":
            attenuation = float(self._explicit_transfer_ratio)
            attenuation_provenance = "model_assumption"
            somatic_peak = attenuation * local_peak
            threshold_crossing = (
                v_rest + somatic_peak) >= v_th
        else:
            attenuation = cable_attenuation
            attenuation_provenance = "model_derived_estimate"
            threshold_crossing = (v_rest + somatic_peak) >= v_th

        if threshold_crossing:
            spike_output = "MODEL_SPIKE_THRESHOLD_CROSSED"
        else:
            spike_output = "NO_MODEL_SPIKE_THRESHOLD_CROSSING"

        parameters = tuple(
            self._parameter_row(p, overrides) for p in self._parameters)
        return ExploratorySimulationResult(
            model_name=MODEL_NAME, model_version=MODEL_VERSION,
            capacitance_variant=self._capacitance_variant,
            dalpha7_enabled=self._dalpha7_enabled,
            transfer_mode=self._transfer_mode,
            parameters=parameters,
            local_synaptic_peak_depolarization_mv=local_peak,
            somatic_peak_depolarization_mv=somatic_peak,
            spatial_attenuation_ratio=attenuation,
            spatial_attenuation_provenance=attenuation_provenance,
            peak_depolarization_mv=somatic_peak,
            threshold_excursion_required_mv=v_th - v_rest,
            threshold_crossing=threshold_crossing,
            spike_model_output=spike_output,
            time_to_peak_ms=time_to_peak,
            output_provenance="model_derived_estimate",
            is_measurement=False,
            dalpha7_statement=(DALPHA7_STATEMENT
                               if self._dalpha7_enabled else ""),
            gates={
                "spatial_voltage_transfer": GATE_STATEMENT_TRANSFER,
                "dalpha7_receptor_conductance": GATE_STATEMENT_DALPHA7,
            },
            statement=EXPLORATORY_STATEMENT)

    def _parameter_row(self, p: ModelParameter,
                       overrides: Mapping[str, float]
                       ) -> Dict[str, object]:
        value = (float(overrides[p.name])
                 if p.name in overrides else p.value)
        return {
            "parameter": p.name, "symbol": p.symbol,
            "tier": self._tiers[p.name], "value": value, "unit": p.unit,
            "plausible_range": self._ranges.get(p.name),
            "range_scale": self._range_scales.get(p.name, "linear"),
            "provenance": p.provenance.value, "status": p.status.value,
            "source": p.source, "conflict": p.conflict,
            "overridden": p.name in overrides,
        }

    @staticmethod
    def _double_exponential_course(n_steps: int, dt_ms: float,
                                   g_max: float, tau_rise: float,
                                   tau_decay: float) -> List[float]:
        if tau_rise <= 0 or tau_decay <= 0:
            raise ValueError("synaptic time constants must be positive.")
        if tau_rise >= tau_decay:
            raise ValueError(
                "tau_rise must be shorter than tau_decay for a "
                "double-exponential conductance.")
        t_peak = (tau_rise * tau_decay / (tau_decay - tau_rise)) * math.log(
            tau_decay / tau_rise)
        norm = (math.exp(-t_peak / tau_decay)
                - math.exp(-t_peak / tau_rise))
        course = []
        for i in range(n_steps):
            t = i * dt_ms
            course.append(g_max * (math.exp(-t / tau_decay)
                                   - math.exp(-t / tau_rise)) / norm)
        return course

    @staticmethod
    def _dalpha7_course(n_steps: int, dt_ms: float, g_max: float,
                        tau_act: float, tau_des: float,
                        d_inf: float) -> List[float]:
        if tau_act <= 0 or tau_des <= 0:
            raise ValueError("Dα7 time constants must be positive.")
        course = []
        for i in range(n_steps):
            t = i * dt_ms
            activation = 1.0 - math.exp(-t / tau_act)
            desensitization = d_inf * (1.0 - math.exp(-t / tau_des))
            course.append(g_max * activation * (1.0 - desensitization))
        return course

    # -- calibration --------------------------------------------------------

    def calibrate_to_somatic_epsp(
            self, target_mv: float = 4.71,
            target_uncertainty_mv: float = 0.35,
            dt_ms: float = 0.01, duration_ms: float = 15.0
    ) -> CalibrationRecord:
        """Fit g_PSI so the peak somatic depolarization matches the
        published MN5 somatic EPSP.

        The published EPSP (4.71 +/- 0.35 mV, Fayyazuddin+ 2006) is a
        NATIVE measurement used as a COMPARISON TARGET ONLY. The
        procedure is MODEL_CALIBRATION and the fitted conductance is
        preserved as a MODEL-DERIVED ESTIMATE. It is NOT a measurement
        of the PSI→MN5 synaptic conductance, which remains BLOCKED.

        Calibration ALWAYS runs with the Dα7 component disabled: Dα7
        must never retroactively justify the existence or magnitude of
        the PSI conductance.
        """
        if self._dalpha7_enabled:
            raise ValueError(
                "calibration must run with the Dα7 component disabled: "
                "Dα7 must never retroactively justify the existence or "
                "magnitude of the PSI conductance.")
        if not math.isfinite(target_mv) or target_mv <= 0:
            raise ValueError("target_mv must be a positive finite number.")

        def somatic_peak_for(log10_g: float) -> float:
            result = self.simulate(
                overrides={"PSI synaptic peak conductance":
                           10.0 ** log10_g},
                dt_ms=dt_ms, duration_ms=duration_ms)
            return result.somatic_peak_depolarization_mv

        lo, hi = -4.0, 5.0
        if somatic_peak_for(lo) > target_mv or somatic_peak_for(hi) < target_mv:
            raise ValueError(
                "the target somatic depolarization is not reachable "
                "within the exploratory g_PSI range 1e-4..1e5 nS; the "
                "target is a comparison figure, not a fitting "
                "guarantee.")
        for _ in range(48):
            mid = 0.5 * (lo + hi)
            if somatic_peak_for(mid) < target_mv:
                lo = mid
            else:
                hi = mid
        fitted_g = 10.0 ** (0.5 * (lo + hi))
        check = self.simulate(
            overrides={"PSI synaptic peak conductance": fitted_g},
            dt_ms=dt_ms, duration_ms=duration_ms)
        return CalibrationRecord(
            method=CALIBRATION_METHOD,
            target_mv=target_mv, target_uncertainty_mv=target_uncertainty_mv,
            target_provenance="native_experimental_measurement "
                              "(comparison target only)",
            target_source="Fayyazuddin+ 2006 PLoS Biol 4(3):e63 "
                          "(4.71 +/- 0.35 mV, n=10, GF stimulated, "
                          "somatic whole-cell; PSI never directly "
                          "stimulated and the distal amplitude is "
                          "unreported)",
            fitted_g_psi_ns=fitted_g,
            fitted_provenance="model_derived_estimate",
            resulting_somatic_peak_depolarization_mv=(
                check.somatic_peak_depolarization_mv),
            capacitance_variant=self._capacitance_variant,
            dalpha7_enabled=False,
            statement=(
                "The fitted g_PSI is a MODEL-DERIVED ESTIMATE produced "
                "by MODEL_CALIBRATION against a comparison target. It is "
                "NOT a measurement of the PSI→MN5 synaptic conductance, "
                "which remains BLOCKED, and it must not be read back as "
                "a biological value. The published EPSP was recorded "
                "under GF stimulation (PSI never directly activated), so "
                "the comparison is against a pathway-filtered somatic "
                "voltage, not an isolated PSI→MN5 event."))

    # -- sensitivity analysis -------------------------------------------------

    def sensitivity_analysis(
            self,
            grid: Optional[Mapping[str, Sequence[float]]] = None,
            dt_ms: float = 0.01, duration_ms: float = 15.0
    ) -> SensitivityResult:
        """Parameter sweep framework with robustness classification.

        Design (main effects plus the key interaction; the full
        six-way cross product is not required to classify conclusions):

        1. OFAT: every grid parameter varied alone at nominal values.
        2. Passive TIER-B factors (Ra, Cm_spec, Rm) crossed with assumed
           TIER-C E_syn, at BOTH contested capacitance variants (C-01
           stays explicit).
        3. g_PSI main effect: the passive/E_syn grid x the logarithmic
           g_PSI range, Dα7 disabled.
        4. g_Dα7 main effect: the passive/E_syn grid x the logarithmic
           g_Dα7 range, Dα7 enabled, g_PSI at nominal.
        5. g_PSI x g_Dα7 interaction: the two logarithmic ranges
           crossed, nominal passive TIER-B values and nominal TIER-C
           E_syn assumption.

        Overrides are applied to local copies; the model's source
        parameters are never modified by the sweep.
        """
        grid = dict(grid or DEFAULT_SWEEP_GRID)
        for key in grid:
            if key not in SWEEP_PARAMETER_NAMES:
                raise KeyError(
                    f"unknown sweep parameter {key!r}; the sweep "
                    f"grid is keyed by {sorted(SWEEP_PARAMETER_NAMES)}")

        nominal: Dict[str, float] = {}
        for key in grid:
            nominal[key] = float(
                self._set.require(SWEEP_PARAMETER_NAMES[key]))

        def run(overrides: Mapping[str, float],
                variant: str = self._capacitance_variant,
                dalpha7: bool = self._dalpha7_enabled
                ) -> ExploratorySimulationResult:
            model = self if (variant == self._capacitance_variant
                             and dalpha7 == self._dalpha7_enabled) \
                else ExploratoryMN5Model(
                    capacitance_variant=variant, dalpha7_enabled=dalpha7,
                    transfer_mode=self._transfer_mode,
                    transfer_ratio=self._explicit_transfer_ratio)
            return model.simulate(overrides=overrides, dt_ms=dt_ms,
                                  duration_ms=duration_ms)

        def summarize(results: Sequence[ExploratorySimulationResult]
                      ) -> Dict[str, object]:
            if not results:
                return {
                    "runs": 0,
                    "note": "design not run: the parameter is "
                            "absent from the sweep grid",
                }
            local = [r.local_synaptic_peak_depolarization_mv
                     for r in results]
            somatic = [r.somatic_peak_depolarization_mv for r in results]
            atten = [r.spatial_attenuation_ratio for r in results]
            crossings = [r.threshold_crossing for r in results]
            return {
                "runs": len(results),
                "local_peak_mv": {"min": min(local), "max": max(local)},
                "somatic_peak_mv": {"min": min(somatic),
                                    "max": max(somatic)},
                "attenuation": {"min": min(atten), "max": max(atten)},
                "threshold_crossings": sum(crossings),
                "threshold_crossing_fraction": (
                    sum(crossings) / len(results) if results else 0.0),
            }

        # 1. OFAT -- per-parameter sensitivity at nominal values.
        ofat: Dict[str, Dict[str, object]] = {}
        for key, values in grid.items():
            param = SWEEP_PARAMETER_NAMES[key]
            # The g_Dalpha7 OFAT only means something with the
            # component enabled; otherwise g_Dalpha7 is inert and
            # the sweep is degenerate (identical values).
            da7 = self._dalpha7_enabled or (key == "g_dalpha7_ns")
            results = [run({param: float(v)}, dalpha7=da7)
                       for v in values]
            ofat[key] = summarize(results)
            ofat[key]["parameter"] = param
            ofat[key]["values"] = list(values)
            ofat[key]["dalpha7_enabled"] = da7
            ofat[key]["somatic_peak_mv_by_value"] = [
                r.somatic_peak_depolarization_mv for r in results]
            ofat[key]["threshold_crossing_by_value"] = [
                r.threshold_crossing for r in results]

        passive_and_esyn_keys = [
            "axial_resistivity_ohm_cm",
            "specific_membrane_capacitance_uf_cm2",
            "specific_membrane_resistance_kohm_cm2",
            "cholinergic_reversal_mv",
        ]
        passive_and_esyn_grid = {
            k: grid[k] for k in passive_and_esyn_keys if k in grid}

        def passive_and_esyn_overrides(
                combo: Sequence[float]) -> Dict[str, float]:
            return {SWEEP_PARAMETER_NAMES[k]: float(v)
                    for k, v in zip(passive_and_esyn_grid, combo)}

        # 2. Passive TIER-B factors plus the TIER-C E_syn assumption.
        design2: List[ExploratorySimulationResult] = []
        if passive_and_esyn_grid:
            keys = list(passive_and_esyn_grid)
            for combo in itertools.product(
                    *(passive_and_esyn_grid[k] for k in keys)):
                overrides = passive_and_esyn_overrides(combo)
                for variant in ("A", "B"):
                    design2.append(run(overrides, variant=variant))
        else:
            for variant in ("A", "B"):
                design2.append(run({}, variant=variant))

        # 3. g_PSI main effect across the passive/E_syn grid.
        design3: List[ExploratorySimulationResult] = []
        if "g_psi_ns" in grid and passive_and_esyn_grid:
            keys = list(passive_and_esyn_grid)
            for combo in itertools.product(
                    *(passive_and_esyn_grid[k] for k in keys)):
                overrides = passive_and_esyn_overrides(combo)
                for g in grid["g_psi_ns"]:
                    o = dict(overrides)
                    o["PSI synaptic peak conductance"] = float(g)
                    design3.append(run(o))
        elif "g_psi_ns" in grid:
            for g in grid["g_psi_ns"]:
                design3.append(
                    run({"PSI synaptic peak conductance": float(g)}))

        # 4. g_Dα7 main effect across the passive/E_syn grid (Dα7 on).
        design4: List[ExploratorySimulationResult] = []
        if "g_dalpha7_ns" in grid and passive_and_esyn_grid:
            keys = list(passive_and_esyn_grid)
            for combo in itertools.product(
                    *(passive_and_esyn_grid[k] for k in keys)):
                overrides = passive_and_esyn_overrides(combo)
                for g in grid["g_dalpha7_ns"]:
                    o = dict(overrides)
                    o["Dα7 maximal conductance"] = float(g)
                    design4.append(run(o, dalpha7=True))
        elif "g_dalpha7_ns" in grid:
            for g in grid["g_dalpha7_ns"]:
                design4.append(run(
                    {"Dα7 maximal conductance": float(g)}, dalpha7=True))

        # 5. g_PSI x g_Dα7 interaction at nominal passive/E_syn values.
        design5: List[ExploratorySimulationResult] = []
        if "g_psi_ns" in grid and "g_dalpha7_ns" in grid:
            for g_psi in grid["g_psi_ns"]:
                for g_da7 in grid["g_dalpha7_ns"]:
                    design5.append(run(
                        {"PSI synaptic peak conductance": float(g_psi),
                         "Dα7 maximal conductance": float(g_da7)},
                        dalpha7=True))

        all_runs = [design2, design3, design4, design5]
        total_runs = sum(len(d) for d in all_runs) + sum(
            len(grid[key]) for key in grid)

        # -- robustness classification --
        rules = {
            "ROBUST": "same qualitative conclusion across most plausible "
                      "parameter sets",
            "PARAMETER-DEPENDENT": "changes across plausible parameter "
                                   "sets whose ranges current evidence "
                                   "bounds (TIER B)",
            "UNCONSTRAINED": "cannot be meaningfully bounded by current "
                             "evidence (varies across a TIER C free "
                             "parameter range)",
        }

        def classify(outcome_values: Sequence[bool],
                     parameter_name: str) -> str:
            # A TIER C free parameter has no evidence-bounded
            # plausible range, so ANY conclusion that depends on
            # it cannot be meaningfully bounded by current
            # evidence -- whether or not the outcome happens to
            # be constant across the assumed sweep range.
            if parameter_name in FREE_PARAMETERS:
                return RobustnessClass.UNCONSTRAINED.value
            if len(set(outcome_values)) <= 1:
                return RobustnessClass.ROBUST.value
            return RobustnessClass.PARAMETER_DEPENDENT.value

        conclusions: Dict[str, str] = {}

        # Conclusion 1: a PSI input produces a local depolarization.
        local_positive = all(
            r.local_synaptic_peak_depolarization_mv > 0.0
            for d in all_runs for r in d)
        conclusions["a PSI synaptic input produces a local "
                    "depolarization at the synaptic site"] = (
            RobustnessClass.ROBUST.value if local_positive
            else RobustnessClass.PARAMETER_DEPENDENT.value)

        # Conclusion 2: the somatic response is attenuated relative
        # to the local response (cable mode only).
        cable_runs = [r for d in all_runs for r in d
                      if r.transfer_mode == "cable"]
        attenuated = all(
            r.spatial_attenuation_ratio < 1.0 for r in cable_runs)
        conclusions["the somatic response is attenuated relative "
                    "to the local synaptic response"] = (
            RobustnessClass.ROBUST.value if attenuated
            else RobustnessClass.PARAMETER_DEPENDENT.value)

        # Conclusion 3a: threshold crossing across the
        # literature-bounded (TIER B) parameter space, g_PSI at
        # nominal. The outcome is invariant across all TIER B
        # combinations (no crossing), so the negative statement
        # is ROBUST.
        tier_b_crossings = [r.threshold_crossing for r in design2]
        if all(tier_b_crossings):
            conclusion_3a = (
                "the somatic response crosses the MN5 spike "
                "threshold across the literature-bounded (TIER B) "
                "parameter space")
        elif not any(tier_b_crossings):
            conclusion_3a = (
                "the somatic response does NOT cross the MN5 spike "
                "threshold anywhere in the literature-bounded "
                "(TIER B) parameter space (at the nominal g_PSI)")
        else:
            conclusion_3a = (
                "whether the somatic response crosses the MN5 spike "
                "threshold across the literature-bounded (TIER B) "
                "parameter space")
        conclusions[conclusion_3a] = classify(
            tier_b_crossings, "axial resistivity")

        # Conclusion 3b: whether threshold crossing can be reached
        # by varying the free g_PSI. g_PSI is a TIER C free
        # parameter whose plausible range current evidence cannot
        # bound, so this question is UNCONSTRAINED.
        conclusions["whether the somatic response can cross the "
                    "MN5 spike threshold by varying the free "
                    "g_PSI"] = classify(
            ofat["g_psi_ns"]["threshold_crossing_by_value"]
            if "g_psi_ns" in ofat else [],
            "PSI synaptic peak conductance")

        # Conclusion 4: the Dα7 component's effect on the somatic
        # response. g_Dα7 is a free parameter, so the size of the
        # effect cannot be bounded by current evidence.
        conclusions["the Dα7 component's effect on the somatic "
                    "response"] = classify(
            [r.threshold_crossing for r in design4],
            "Dα7 maximal conductance")

        # Conclusion 5: the C-01 capacitance conflict changes the
        # peak. The two variants are both native measurements in
        # unresolved disagreement, so the peak is
        # PARAMETER-DEPENDENT on which variant is assumed.
        variant_a = [r for r in design2
                     if r.capacitance_variant == "A"]
        variant_b = [r for r in design2
                     if r.capacitance_variant == "B"]
        if variant_a and variant_b:
            peaks_a = [r.somatic_peak_depolarization_mv
                       for r in variant_a]
            peaks_b = [r.somatic_peak_depolarization_mv
                       for r in variant_b]
            conflict_matters = not math.isclose(
                min(peaks_a), min(peaks_b), rel_tol=1e-9) or not \
                math.isclose(max(peaks_a), max(peaks_b),
                               rel_tol=1e-9)
        else:
            conflict_matters = True
        conclusions["the contested whole-cell capacitance (C-01) "
                    "changes the peak somatic response"] = (
            RobustnessClass.PARAMETER_DEPENDENT.value
            if conflict_matters else RobustnessClass.ROBUST.value)

        # Keep the established summary keys stable. Designs 2–4 include the
        # TIER-C E_syn assumption alongside the TIER-B passive grid.
        design_summary = {
            "1_ofat": {name: ofat[name] for name in grid},
            "2_tier_b_factorial_both_capacitance_variants":
                summarize(design2),
            "3_g_psi_main_effect_across_tier_b": summarize(design3),
            "4_g_dalpha7_main_effect_across_tier_b": summarize(design4),
            "5_g_psi_x_g_dalpha7_interaction": summarize(design5),
        }

        return SensitivityResult(
            design={
                "grid": {k: list(v) for k, v in grid.items()},
                "nominal_values": nominal,
                "dt_ms": dt_ms, "duration_ms": duration_ms,
                "capacitance_variants": ["A", "B"],
                "dalpha7_enabled_for_designs_4_and_5": True,
                "note": "main-effects design plus the g_PSI x g_Dα7 "
                        "interaction; the full six-way cross product is "
                        "not required to classify the conclusions",
            },
            total_runs=total_runs,
            ofat=ofat,
            designs=design_summary,
            conclusions=conclusions,
            classification_rules=rules,
            statement=EXPLORATORY_STATEMENT)

    # -- reporting -----------------------------------------------------------

    def report(self,
               sensitivity_result: Optional[SensitivityResult] = None
               ) -> Dict[str, object]:
        """The five required report sections, never collapsed."""
        nominal = self.simulate()
        return {
            "model": MODEL_NAME,
            "version": MODEL_VERSION,
            "kind": "best-effort exploratory mechanistic model",
            "is_measurement": False,
            "statement": EXPLORATORY_STATEMENT,
            "measured_inputs": [
                row for row in self.parameter_table()
                if row["tier"] == TIER_A],
            "literature_derived_ranges": [
                row for row in self.parameter_table()
                if row["tier"] == TIER_B],
            "model_assumptions": [
                row for row in self.parameter_table()
                if row["tier"] in (TIER_C, TIER_GEOMETRY)],
            "model_derived_outputs": nominal.as_dict(),
            "sensitivity_robustness": (
                sensitivity_result.as_dict()
                if sensitivity_result is not None
                else {"note": "run sensitivity_analysis() to populate; "
                              "the design is described in "
                              "research/exploratory_sensitivity_plan.md"}),
            "evidence_safe_boundary": {
                "reads_frozen_registry": False,
                "writes_frozen_registry": False,
                "replaces_reduced_mn5": False,
                "opens_gates": False,
                "adjudicates_c01": False,
            },
            "gates": {
                "spatial_voltage_transfer": GATE_STATEMENT_TRANSFER,
                "dalpha7_receptor_conductance": GATE_STATEMENT_DALPHA7,
            },
        }
