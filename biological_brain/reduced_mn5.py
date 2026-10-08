"""Reduced MN5 computational abstraction (3.0D-8Y).

WHAT THIS IS
------------
The first executable MN5 model that the frozen evidence actually permits. It is
a **reduced computational abstraction** built from exactly three SAFE native
measurements of adult Drosophila MN5, all somatic whole-cell recordings:

    resting potential   -67.8 mV   (n=13, Ryglewski, Kilo & Duch 2014)
    spike threshold     -24.1 mV   (n=11, Ryglewski, Kilo & Duch 2014)
    action potential    +45.5 mV   (n=13, Ryglewski, Kilo & Duch 2014)

That is the whole biological basis. Nothing else is supplied.

WHY THERE IS NO LEAK TERM
-------------------------
The obvious implementation is a leaky integrator, and the project already has
one: :class:`biological_brain.dynamics.lif_voltage.LIFVoltageModel`. It is NOT
used here, because it requires a membrane time constant:

    tau_m : BLOCKED -- no qualifying measurement exists for MN5.

The same reasoning excludes Ra (no Drosophila-specific value; the only one ever
applied is Manduca-derived), Rm (no measurement), Cm (unresolved conflict C-01),
and any leak conductance. A leaky model would therefore require inventing a
value, so this model has **no decay term at all**: voltage moves only when an
explicitly software input moves it, and returns to rest only on a spike.

CONSEQUENCE, STATED PLAINLY
---------------------------
Because ``tau_m`` is blocked, voltage here does NOT decay toward rest between
inputs. That is not a simplification of a leak; it is the absence of a leak,
because the parameter that defines it does not exist. A reader expecting
passive leak must not assume it is here.

WHAT THIS IS NOT
----------------
Not a cable model. Not a spatial-transfer model. Not a PSI->MN5 synaptic
physiology model. Not a Dalpha7 model. Not a fitted model. It contains no
compartment, no synapse, no axon and no dendrite, and it holds no hidden
parameter of any kind. The 43 official PSI->MN5 contacts are metadata only and
play no role in its arithmetic.

**This model is a reduced computational abstraction. Its outputs are
model-derived and are not measurements of MN5 physiology.**

GATES
-----
    PSI->MN5 spatial voltage transfer: NOT AUTHORIZED
    Dalpha7 conductance:                NOT AUTHORIZED
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .model_framework import (
    BlockedParameterError,
    Capability,
    ModelParameter,
    ModelProvenance,
    MN5Model,
    ParameterSet,
    ParameterStatus,
    build_model,
    require_dalpha7_gate,
    require_spatial_transfer,
)

MODEL_NAME = "reduced_mn5"
MODEL_VERSION = "1.0.0"

#: Marker that must accompany any value the caller supplies.
SOFTWARE_INPUT_MARKER = "SOFTWARE INPUT -- NOT A BIOLOGICAL MEASUREMENT"

#: The three SAFE native MN5 measurements this model may use.
PERMITTED_BIOLOGICAL_INPUTS = (
    "MN5 resting potential",
    "MN5 spike threshold",
    "MN5 action potential amplitude",
)

#: Names a caller may NOT supply as though they were native evidence.
#: Names only -- no values, no defaults, and no way to fill them in.
#:
#: Matching is on the NORMALISED WHOLE NAME, never on a substring. An earlier
#: substring matcher was both unsound and unsound in the other direction: it
#: refused innocent names ("fixture_param" contains "ra") while ACCEPTING
#: "axial_resistance_us", which is a straight bypass of this guard. Normalised
#: whole-name equality plus the frozen inventory's own blocked rows closes both.
REFUSED_SUPPLY_NAMES = (
    "Ra", "Rm", "Cm", "g_pas", "tau_m",
    "psi_mn5_gsyn", "psi_mn5_reversal", "spatial_transfer_ratio",
    "Dalpha7 conductance", "gap_junction_conductance",
)

#: Canonical aliases for the same blocked quantities, normalised.
_BLOCKED_ALIASES = frozenset({
    "ra", "rm", "cm", "g_pas", "tau_m",
    "axial_resistance", "axial_resistivity",
    "specific_membrane_resistance", "specific_membrane_capacitance",
    "capacitance", "leak_conductance", "membrane_time_constant",
    "psi_mn5_gsyn", "psi_mn5_reversal", "synaptic_conductance",
    "peak_conductance", "reversal_potential",
    "spatial_transfer_ratio", "spatial_transfer", "transfer_ratio",
    "electrotonic_distance", "length_constant", "space_constant",
    "attenuation", "transfer_resistance", "input_resistance",
    "dalpha7 conductance", "dalpha7 receptor conductance",
    "dalpha7_receptor_conductance", "dalpha7 conductance",
    "gap_junction_conductance", "gap_junction_conductance_us",
    "gj_conductance", "gap_junction_weight",
})


def _normalise_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


def _tokens(name: str) -> List[str]:
    n = _normalise_name(name)
    return n.split("_") if n else []


def _matches_blocked_alias(name: str) -> Optional[str]:
    """Return the alias this name matches, or None.

    Matching is by whole-token CONTIGUOUS SUBSEQUENCE, not raw substring.
    Substring matching could not see through a unit or qualifier suffix, so
    "axial_resistance_us" and "Cm_specific" both slipped past a plain
    containment check, while innocent names such as "fixture_param" were
    falsely refused. Token matching closes both directions.
    """
    toks = _tokens(name)
    if not toks:
        return None
    for alias in sorted(_BLOCKED_ALIASES) + [
            _normalise_name(n) for n in REFUSED_SUPPLY_NAMES]:
        want = alias.split("_")
        if not want:
            continue
        n = len(want)
        for i in range(len(toks) - n + 1):
            if toks[i:i + n] == want:
                return alias
    return None


class BiologicalClaimError(Exception):
    """Raised when blocked biology is offered as if it were native evidence."""


class SoftwareInputError(Exception):
    """Raised when a software input is malformed, non-numeric or non-finite."""


@dataclass(frozen=True)
class SpikeEvent:
    """One emitted spike. A MODEL OUTPUT, not a recorded event.

    Field semantics, which matter and were the subject of this audit:

    ``from_mv`` / ``peak_mv`` / ``voltage_excursion_mv``
        What the MODEL did. ``voltage_excursion_mv`` is ``peak_mv - from_mv``:
        the actual modelled voltage rise at the crossing step. It is a MODEL
        OUTPUT and is NOT the biological action-potential amplitude.

    ``reference_ap_amplitude_mv``
        The measured MN5 action-potential amplitude, echoed from the frozen
        registry so a reader can compare the two. It is an INPUT, not an
        output, and it is deliberately NOT used to shape the event.

    An earlier version reported the measured amplitude under the name
    ``amplitude_mv`` next to an unrelated ``peak_mv``, so a reader could
    mistake a 45.5 mV biological figure for the size of a spike the model had
    actually produced at, say, 932 mV. The two are now named apart.
    """

    step_index: int
    peak_mv: float
    voltage_excursion_mv: float
    from_mv: float
    reference_ap_amplitude_mv: float
    source: str = MODEL_NAME

    def is_measurement(self) -> bool:
        """Always False. A simulated spike is not an observed one."""
        return False

    def spike_shape_modelled(self) -> bool:
        """Always False. No integration means no spike shape is produced."""
        return False

    def excursion_matches_reference(self) -> bool:
        """Whether the modelled excursion equals the measured AP amplitude."""
        return abs(self.voltage_excursion_mv
                   - self.reference_ap_amplitude_mv) < 1e-9

    def as_dict(self) -> Dict[str, object]:
        return {
            "kind": "model_output",
            "is_measurement": False,
            "spike_shape_modelled": False,
            "step_index": self.step_index,
            "peak_mv": self.peak_mv,
            "from_mv": self.from_mv,
            "voltage_excursion_mv": self.voltage_excursion_mv,
            "reference_ap_amplitude_mv": self.reference_ap_amplitude_mv,
            "excursion_matches_reference": self.excursion_matches_reference(),
            "source": self.source,
            "note": ("MODEL-DERIVED OUTPUT of a reduced abstraction. NOT a "
                     "native MN5 measurement and not an electrophysiological "
                     "record. No spike shape or integration is modelled: "
                     "voltage_excursion_mv is whatever the software inputs "
                     "produced at the crossing step, and it need not equal the "
                     "measured reference amplitude."),
        }


class ReducedMN5Simulator:
    """Threshold-only MN5 abstraction. No leak, no compartment, no synapse."""

    def __init__(self, model: Optional[MN5Model] = None) -> None:
        self._model = model if model is not None else build_model()
        params = self._model.params
        self._v_rest = params.require_uncontested("MN5 resting potential")
        self._threshold = params.require_uncontested("MN5 spike threshold")
        self._ap_amplitude = params.require_uncontested(
            "MN5 action potential amplitude")
        self._inputs: Dict[str, ModelParameter] = {}
        for name in PERMITTED_BIOLOGICAL_INPUTS:
            p = params.get(name)
            if p.status is not ParameterStatus.SAFE:
                raise BlockedParameterError(
                    f"{name} is {p.status.value}, not SAFE; the reduced MN5 "
                    f"model admits only SAFE inputs.")
        self._v = self._v_rest
        self._v_prev = self._v_rest
        self._steps = 0
        self._spikes: List[SpikeEvent] = []

    # -- capability surface --------------------------------------------------

    @property
    def is_cable_model(self) -> bool:
        return False

    @property
    def spatial_transfer_available(self) -> bool:
        return False

    @property
    def psi_mn5_synaptic_physiology_available(self) -> bool:
        return False

    @property
    def dalpha7_available(self) -> bool:
        return False

    def capabilities(self) -> Dict[str, Capability]:
        return {
            "resting_state_representation": Capability.AVAILABLE,
            "threshold_representation": Capability.AVAILABLE,
            "spike_output_abstraction": Capability.AVAILABLE,
            "passive_leak_or_decay": Capability.BLOCKED,
            "cable_behaviour": Capability.BLOCKED,
            "psi_mn5_synaptic_physiology": Capability.BLOCKED,
            "psi_mn5_spatial_transfer": Capability.BLOCKED,
            "dalpha7_receptor_conductance": Capability.BLOCKED,
        }

    # -- state ---------------------------------------------------------------

    @property
    def voltage_mv(self) -> float:
        return self._v

    @property
    def resting_potential_mv(self) -> float:
        return self._v_rest

    @property
    def threshold_mv(self) -> float:
        return self._threshold

    @property
    def spike_amplitude_mv(self) -> float:
        """Amplitude of an emitted spike. A MODEL-DERIVED abstraction."""
        return self._ap_amplitude

    @property
    def spikes(self) -> List[SpikeEvent]:
        return list(self._spikes)

    def reset(self) -> None:
        self._v = self._v_rest
        self._steps = 0
        self._spikes = []

    # -- input ---------------------------------------------------------------

    def apply_software_input(self, delta_mv: float, marker: str) -> float:
        """Apply an explicitly SOFTWARE input, in millivolts.

        The caller must supply ``marker`` proving this is not a biological
        measurement. There is no synaptic input path, because the synaptic
        conductance is blocked: this is the only way to move the voltage, and
        it carries no biological weight.
        """
        if not marker or SOFTWARE_INPUT_MARKER not in marker:
            raise BiologicalClaimError(
                "apply_software_input requires marker="
                f"{SOFTWARE_INPUT_MARKER!r}. Without it there is no way to tell "
                f"a software fixture from a claimed biological measurement, so "
                f"the input is refused.")
        try:
            delta = float(delta_mv)
        except (TypeError, ValueError) as exc:
            raise SoftwareInputError(
                f"software input must be a finite number of millivolts; got "
                f"{delta_mv!r} ({type(delta_mv).__name__}).") from exc
        if not math.isfinite(delta):
            # NaN silently fails every comparison and would corrupt the state
            # without ever spiking; inf would emit a spike with peak inf. Both
            # are refused rather than absorbed.
            raise SoftwareInputError(
                f"software input must be finite; got {delta!r}. NaN would "
                f"silently suppress threshold crossing and corrupt the model "
                f"state, and an infinite input is not a voltage.")
        self._v_prev = self._v
        self._v += delta
        return self._v

    def supply_biological_parameter(self, name: str, value: float,
                                    provenance: ModelProvenance,
                                    status: ParameterStatus,
                                    source: str) -> ModelParameter:
        """Offer a biological parameter, routed through the frozen guards.

        A blocked quantity offered as native evidence raises. A quantity offered
        as a labelled assumption is accepted, recorded, and reported as an
        assumption. There is no path here that turns a blocked quantity into a
        usable value.
        """
        alias_hit = _matches_blocked_alias(name)
        # Also refuse anything the frozen inventory already marks BLOCKED, so a
        # caller cannot reach a blocked quantity by renaming it.
        try:
            existing = self._model.params.get(name)
        except KeyError:
            existing = None
        blocked_inventory = (existing is not None
                             and existing.status is ParameterStatus.BLOCKED)
        if alias_hit or blocked_inventory:
            raise BiologicalClaimError(
                f"{name} is not admissible to this model"
                + (f" (matches blocked quantity {alias_hit!r})"
                   if alias_hit else "")
                + ". " + self._refusal_reason(name))
        p = ModelParameter(
            name=name, symbol=name, value=value, unit="unspecified",
            provenance=provenance, status=status, source=source,
            object="Drosophila MN5", notes="supplied by caller")
        self._model.params.add(p)
        self._inputs[name] = p
        return p

    @staticmethod
    def _refusal_reason(name: str) -> str:
        lowered = name.lower()
        if lowered in ("ra", "rm", "tau_m", "g_pas"):
            return ("It is BLOCKED in the frozen inventory: no qualifying "
                    "Drosophila MN5 measurement exists.")
        if lowered == "cm":
            return ("Whole-cell capacitance is CONTESTED (C-01, 43 +/- 2 pF "
                    "versus 127 +/- 16 pF). This model must not resolve the "
                    "conflict by choosing one.")
        if lowered == "spatial_transfer_ratio":
            return ("Spatial voltage transfer is NOT AUTHORIZED and has never "
                    "been measured.")
        if "dalpha7" in lowered:
            return ("Dalpha7 conductance is NOT AUTHORIZED, and Drosophila "
                    "has no Kir7.1/KCNJ13 orthologue.")
        if lowered in ("psi_mn5_gsyn", "psi_mn5_reversal"):
            return ("No PSI->MN5 synaptic conductance or reversal potential has "
                    "ever been measured in any source.")
        if lowered == "gap_junction_conductance":
            return ("No native GFS junctional conductance exists, and the "
                    "published value carries an unresolved 1000x unit "
                    "conflict (C-02).")
        return "It is not part of the permitted evidence set."

    def model_synapse_conductance_refused(self) -> bool:
        """True when the synaptic-conductance path refuses, as it must.

        There is no synaptic input path on this model. The 43 official
        PSI->MN5 contacts are metadata; none of them carries a weight, because
        no PSI->MN5 synaptic conductance exists to weight it with.
        """
        try:
            self._model.params.require("PSI->MN5 synaptic conductance")
        except BlockedParameterError:
            return True
        return False

    def require_leak(self) -> float:
        """Always raises: a membrane time constant does not exist for MN5."""
        raise BlockedParameterError(
            "BlockedParameterError:\n"
            "  Parameter: tau_m (membrane time constant)\n"
            "  Object:    Drosophila MN5\n"
            "  Status:    BLOCKED -- no qualifying measurement exists.\n"
            "  Consequence: this reduced model therefore has NO decay term. "
            "Voltage does not relax toward rest between inputs. Adding a leak "
            "would require inventing a time constant.")

    # -- execution -----------------------------------------------------------

    def step(self) -> Optional[SpikeEvent]:
        """One model step: threshold test, spike-and-reset if crossed.

        No integration occurs. There is no differential equation to solve,
        because every parameter such an equation would need is blocked.
        """
        self._steps += 1
        if self._v >= self._threshold:
            peak = self._v
            event = SpikeEvent(
                step_index=self._steps, peak_mv=peak, from_mv=self._v_prev,
                voltage_excursion_mv=peak - self._v_prev,
                reference_ap_amplitude_mv=self._ap_amplitude)
            self._spikes.append(event)
            self._v = self._v_rest
            return event
        return None

    def run(self, inputs: Sequence[float],
            marker: str = SOFTWARE_INPUT_MARKER) -> List[SpikeEvent]:
        """Apply a sequence of software inputs, stepping after each."""
        for delta in inputs:
            self.apply_software_input(delta, marker)
            self.step()
        return self.spikes

    # -- reporting -----------------------------------------------------------

    def biological_inputs(self) -> List[Dict[str, object]]:
        out = []
        for name in PERMITTED_BIOLOGICAL_INPUTS:
            p = self._model.params.get(name)
            out.append({
                "parameter": p.name, "symbol": p.symbol, "unit": p.unit,
                "value": self._model.params.require_uncontested(p.name),
                "provenance": p.provenance.value,
                "status": p.status.value, "source": p.source,
                "object": p.object, "evidence_strength": p.evidence_strength,
            })
        return out

    def report(self) -> Dict[str, object]:
        ps = self._model.params.provenance_summary()
        return {
            "model": MODEL_NAME,
            "version": MODEL_VERSION,
            "kind": "reduced computational abstraction",
            "result_kind": "model_derived_output",
            "is_measurement": False,
            "statement": ("This model is a reduced computational abstraction. "
                          "Its outputs are model-derived and are not "
                          "measurements of MN5 physiology."),
            "is_cable_model": self.is_cable_model,
            "spatial_transfer_available": self.spatial_transfer_available,
            "psi_mn5_synaptic_physiology_available":
                self.psi_mn5_synaptic_physiology_available,
            "dalpha7_available": self.dalpha7_available,
            "resting_potential_mv": self._v_rest,
            "threshold_mv": self._threshold,
            "spike_amplitude_mv": self._ap_amplitude,
            "biological_inputs": self.biological_inputs(),
            "provenance_summary": ps,
            "assumptions_used": sorted(ps["assumption_names"]),
            "supplied_by_caller": sorted(self._inputs),
            "blocked_capabilities": [
                k for k, v in self.capabilities().items()
                if v is Capability.BLOCKED],
            "capabilities": {k: v.value for k, v in self.capabilities().items()},
            "absent_by_design": [
                "membrane time constant (tau_m BLOCKED) so there is NO decay",
                "axial resistance (Ra BLOCKED)",
                "specific membrane resistance (Rm BLOCKED)",
                "whole-cell capacitance (Cm CONTESTED, C-01)",
                "leak conductance (g_pas BLOCKED)",
                "any compartment, synapse, axon or dendrite",
            ],
            "does_not_claim": [
                "PSI->MN5 EPSP amplitude reproduced",
                "PSI->MN5 EPSP kinetics reproduced",
                "native MN5 EPSP reproduced",
                "distal-to-soma voltage attenuation calculated",
                "spatial transfer calculated",
                "MN5 cable behaviour reproduced",
                "Dalpha7 current calculated",
                "native GFS electrical coupling reproduced",
                "measured MN5 response",
            ],
            "gates": {
                "spatial_voltage_transfer":
                    "PSI->MN5 spatial voltage transfer: NOT AUTHORIZED",
                "dalpha7_receptor_conductance":
                    "Dalpha7 conductance: NOT AUTHORIZED",
            },
            "anatomy_metadata": self._model.anatomy.contact_summary(),
        }

    def assert_no_biological_claim(self, claim: str) -> None:
        """Refuse a forbidden biological claim in this model's own output."""
        lowered = claim.lower()
        for banned in (
                "epsp reproduced", "spatial transfer calculated",
                "dalpha7 current calculated", "cable model",
                "measured mn5 response", "native epsp"):
            if banned in lowered:
                raise BiologicalClaimError(
                    f"claim {claim!r} is not available: {banned!r} is "
                    f"forbidden while the relevant gate is closed.")
