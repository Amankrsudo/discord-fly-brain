"""Provenance-safe model framework for the MN5 / PSI->MN5 / GFS system.

WHAT THIS IS
------------
The smallest clean layer that lets an honest computational model be built from
the frozen evidence base, and that makes it *impossible* for a blocked
biological quantity to quietly become a model constant.

It deliberately does NOT replace the existing architecture. The project's
8-category :class:`~biological_brain.provenance.ParameterProvenance` and its
``ProvenanceRecord`` remain the internal vocabulary; this module adds a single
auditable BRIDGE from that vocabulary to the five-class freeze taxonomy, plus
the safety machinery the freeze requires.

    existing ParameterProvenance (8 categories, internal)
        -> model_framework.bridge_provenance()  (explicit, refuses to guess)
        -> ModelProvenance (5 categories, the frozen evidence taxonomy)
        -> ParameterStatus  (SAFE | ASSUMPTION | BLOCKED)
        -> ParameterSet.require() -> value, or BlockedParameterError

THE ONE RULE
------------
A BLOCKED parameter has no value. It is not defaulted, not estimated, not
borrowed, and not rounded into something usable. Asking for one raises
:class:`BlockedParameterError` with the missing evidence named. There is no
constructor path that produces a blocked parameter carrying a number, so a
blocked quantity cannot become a biological constant by accident.

NO SYNTHETIC BIOLOGY
--------------------
This module contains no default biological values whatsoever -- no ``g_syn``,
no ``g_Da7``, no ``Ra``, no ``Rm``, no ``Cm``, no reversal potential, no
synaptic delay, no coupling conductance. Test fixtures live in the tests and
are constructed explicitly; nothing here can promote a fixture into a default.

GATES
-----
    PSI->MN5 spatial voltage transfer: NOT AUTHORIZED
    Dalpha7 conductance:                NOT AUTHORIZED

Both are enforced by :func:`require_spatial_transfer` and
:func:`require_dalpha7_gate`, which raise rather than degrade.
"""

from __future__ import annotations

import csv
import math
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .provenance import ParameterProvenance

__all__ = [
    "ModelProvenance", "ParameterStatus", "ModelParameter", "BlockedParameterError",
    "UnmappableProvenanceError", "GATE_TRANSFER", "GATE_DALPHA7",
    "bridge_provenance", "ParameterSet", "load_frozen_parameters",
    "MN5Anatomy", "ReducedPassiveMN5", "SynapticInterface", "GFSInterface",
    "Dalpha7Interface", "MN5Model", "Capability",
]


# --- the frozen five-class taxonomy ----------------------------------------

class ModelProvenance(Enum):
    """Exactly the five provenance classes of the frozen evidence base."""

    NATIVE_EXPERIMENTAL_MEASUREMENT = "native_experimental_measurement"
    ANATOMICAL_MEASUREMENT = "anatomical_measurement"
    LITERATURE_DERIVED_PASSIVE_PARAMETER = "literature_derived_passive_parameter"
    MODEL_ASSUMPTION = "model_assumption"
    MODEL_DERIVED_ESTIMATE = "model_derived_estimate"


class ParameterStatus(Enum):
    """Safety bucket. Mirrors research/model_input_freeze.csv."""

    SAFE = "SAFE"
    ASSUMPTION = "ASSUMPTION"
    BLOCKED = "BLOCKED"


class Capability(Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"


GATE_TRANSFER = "spatial voltage transfer"
GATE_DALPHA7 = "dalpha7"


# --- errors -----------------------------------------------------------------

class BlockedParameterError(Exception):
    """Raised when a BLOCKED quantity is requested for model construction."""


class UnmappableProvenanceError(Exception):
    """Raised when the internal provenance does not determine a freeze class."""


# --- bridge from the existing 8-category vocabulary -------------------------

#: Only categories whose freeze class is unambiguous are auto-bridged.
_UNAMBIGUOUS_BRIDGE: Dict[ParameterProvenance, ModelProvenance] = {
    ParameterProvenance.DIRECTLY_MEASURED:
        ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT,
    ParameterProvenance.EXPERIMENTALLY_CONSTRAINED:
        ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT,
    ParameterProvenance.CONNECTOME_DERIVED:
        ModelProvenance.ANATOMICAL_MEASUREMENT,
    ParameterProvenance.UNKNOWN:
        ModelProvenance.MODEL_ASSUMPTION,
}

#: Categories that MUST be declared explicitly, with the reason.
_REQUIRES_EXPLICIT_DECLARATION: Dict[ParameterProvenance, str] = {
    ParameterProvenance.PUBLISHED_MODEL_PARAMETER:
        "a value taken from a published computational model may be a "
        "literature-derived passive parameter OR a plain model assumption "
        "depending on what the source measured",
    ParameterProvenance.BORROWED_CROSS_CONTEXT:
        "a borrowed value may be a literature-derived passive parameter OR a "
        "model assumption depending on whether the donor organism is "
        "admissible for this quantity",
    ParameterProvenance.FITTED_CALIBRATED:
        "a calibrated value is fitted to reproduce an output, which is a model "
        "assumption rather than a measurement",
    ParameterProvenance.ESTIMATED:
        "an estimated value may be a literature-derived passive parameter OR a "
        "model assumption depending on whether a source actually estimated it",
}


def bridge_provenance(
        internal: ParameterProvenance,
        declared: Optional[ModelProvenance] = None,
        ) -> ModelProvenance:
    """Map the project's internal provenance onto the frozen five-class taxonomy.

    Unambiguous categories are mapped automatically. The remaining four are
    REFUSED without an explicit declaration, because guessing for them would
    silently move a value up or down the evidence hierarchy -- exactly the
    failure mode this framework exists to prevent.
    """
    if declared is not None:
        if not isinstance(declared, ModelProvenance):
            raise TypeError("declared must be a ModelProvenance")
        return declared
    if internal in _UNAMBIGUOUS_BRIDGE:
        return _UNAMBIGUOUS_BRIDGE[internal]
    reason = _REQUIRES_EXPLICIT_DECLARATION.get(internal)
    if reason is not None:
        raise UnmappableProvenanceError(
            f"{internal.value} does not determine a freeze provenance class: "
            f"{reason}. Pass declared=ModelProvenance.... explicitly.")
    raise UnmappableProvenanceError(
        f"{internal.value} has no bridge rule; refusing to guess.")


# --- the parameter record ---------------------------------------------------

@dataclass(frozen=True)
class ModelParameter:
    """One model input, carrying its provenance and its safety status."""

    name: str
    symbol: str
    value: Optional[float]
    unit: str
    provenance: ModelProvenance
    status: ParameterStatus
    source: str
    object: str
    gate: str = ""
    evidence_strength: str = ""
    notes: str = ""
    #: The unresolved-conflict identifier from the frozen inventory (e.g.
    #: "C-01"), or "" for an uncontested row. A conflicted parameter may be
    #: required, but only via an explicit acknowledgement, so a contested value
    #: can never be selected silently.
    conflict: str = ""
    #: True when ``value`` records what an ARTEFACT literally contains (for
    #: example the number a compiled model file executes) rather than a
    #: biological quantity. Such a row may be BLOCKED and still carry a value:
    #: the number is evidence about the artefact, not a usable biological
    #: constant, and :meth:`ParameterSet.require` refuses it regardless.
    recorded_value: bool = False

    def __post_init__(self) -> None:
        if (self.status is ParameterStatus.BLOCKED
                and self.value is not None
                and not self.recorded_value):
            raise BlockedParameterError(
                f"{self.name}: a BLOCKED parameter must not carry a biological "
                f"value (got {self.value!r}). Blocked quantities have no "
                f"biological value; this is what stops a blocked biological "
                f"quantity from becoming a model constant. Set "
                f"recorded_value=True only for a number that records what an "
                f"artefact literally contains.")

    @property
    def is_usable(self) -> bool:
        return self.status in (ParameterStatus.SAFE, ParameterStatus.ASSUMPTION)

    @property
    def conflict_id(self) -> str:
        """The leading conflict identifier, e.g. ``C-01``, or "" if none."""
        m = re.match(r"^\s*(C-\d+)", self.conflict or "")
        return m.group(1) if m else ""

    @property
    def is_assumption(self) -> bool:
        return self.status is ParameterStatus.ASSUMPTION

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name, "symbol": self.symbol, "value": self.value,
            "unit": self.unit, "provenance": self.provenance.value,
            "status": self.status.value, "source": self.source,
            "object": self.object, "gate": self.gate,
            "evidence_strength": self.evidence_strength, "notes": self.notes,
        }


_STATUS_FROM_FREEZE = {
    "yes_safe": ParameterStatus.SAFE,
}


def _status_from_freeze(safe: str, assumption: str, blocked: str
                        ) -> ParameterStatus:
    if blocked == "yes":
        return ParameterStatus.BLOCKED
    if assumption == "yes":
        return ParameterStatus.ASSUMPTION
    if safe == "yes":
        return ParameterStatus.SAFE
    raise ValueError(
        "a frozen row must be exactly one of safe/assumption/blocked")


# --- the parameter set ------------------------------------------------------

class ParameterSet:
    """A collection of parameters that refuses to yield a blocked value."""

    def __init__(self, parameters: Iterable[ModelParameter] = ()) -> None:
        self._by_name: Dict[str, ModelParameter] = {}
        for p in parameters:
            if p.name in self._by_name:
                raise ValueError(f"duplicate parameter {p.name!r}")
            self._by_name[p.name] = p

    def __len__(self) -> int:
        return len(self._by_name)

    def __contains__(self, name: str) -> bool:
        return name in self._by_name

    def get(self, name: str) -> ModelParameter:
        if name not in self._by_name:
            raise KeyError(
                f"{name!r} is not in this parameter set "
                f"({len(self._by_name)} parameters present)")
        return self._by_name[name]

    def require(self, name: str) -> float:
        """Return the value, or raise. Never invents one."""
        p = self.get(name)
        if p.status is ParameterStatus.BLOCKED:
            raise BlockedParameterError(_blocked_message(p))
        if p.value is None:
            raise BlockedParameterError(
                f"{p.name}: status {p.status.value} but no value is present. "
                f"Absence is reported, never filled in.")
        return p.value

    def require_uncontested(self, name: str) -> float:
        """Return the value only if the frozen inventory records NO conflict.

        A conflicted parameter (for example the two whole-cell capacitance
        values behind C-01) can still be obtained through :meth:`require`, but
        only by naming the exact variant, which forces an explicit choice.
        This method removes even that: it refuses to yield a contested value,
        so no model can quietly settle a disagreement.
        """
        p = self.get(name)
        value = self.require(name)
        if p.conflict:
            raise BlockedParameterError(
                f"BlockedParameterError:\n"
                f"  Parameter: {p.name} ({p.symbol}) is CONTESTED "
                f"(conflict {p.conflict}).\n"
                f"  The frozen inventory records an unresolved disagreement "
                f"about this value, and no winner has been chosen.\n"
                f"  Notes: {p.notes}\n"
                f"  A contested value may only be used by explicitly naming "
                f"the variant you assume; this method refuses to do that for "
                f"you.")
        return value

    def conflicted_parameters(self) -> Dict[str, List[str]]:
        """Contested parameter names grouped by conflict id."""
        out: Dict[str, List[str]] = {}
        for p in self._by_name.values():
            cid = p.conflict_id
            if cid:
                out.setdefault(cid, []).append(p.name)
        return {k: sorted(v) for k, v in sorted(out.items())}

    def add(self, p: ModelParameter) -> None:
        if p.name in self._by_name:
            raise ValueError(f"duplicate parameter {p.name!r}")
        self._by_name[p.name] = p

    def extend(self, ps: Iterable[ModelParameter]) -> None:
        for p in ps:
            self.add(p)

    # -- reporting -----------------------------------------------------------

    def provenance_summary(self) -> Dict[str, object]:
        by_prov: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for p in self._by_name.values():
            by_prov[p.provenance.value] = by_prov.get(p.provenance.value, 0) + 1
            by_status[p.status.value] = by_status.get(p.status.value, 0) + 1
        return {
            "total": len(self._by_name),
            "by_provenance": dict(sorted(by_prov.items())),
            "by_status": dict(sorted(by_status.items())),
            "experimental": by_prov.get(
                ModelProvenance.NATIVE_EXPERIMENTAL_MEASUREMENT.value, 0),
            "anatomical": by_prov.get(
                ModelProvenance.ANATOMICAL_MEASUREMENT.value, 0),
            "literature_derived": by_prov.get(
                ModelProvenance.LITERATURE_DERIVED_PASSIVE_PARAMETER.value, 0),
            "assumptions": by_prov.get(
                ModelProvenance.MODEL_ASSUMPTION.value, 0),
            "model_derived": by_prov.get(
                ModelProvenance.MODEL_DERIVED_ESTIMATE.value, 0),
            "blocked": by_status.get(ParameterStatus.BLOCKED.value, 0),
            "assumptions_used": by_status.get(
                ParameterStatus.ASSUMPTION.value, 0),
            "safe": by_status.get(ParameterStatus.SAFE.value, 0),
            "assumption_names": sorted(
                p.name for p in self._by_name.values() if p.is_assumption),
        }

    def assumptions_used(self) -> List[str]:
        return sorted(p.name for p in self._by_name.values() if p.is_assumption)


def _blocked_message(p: ModelParameter) -> str:
    gate_line = ""
    if p.gate:
        pretty = (GATE_TRANSFER if p.gate in (GATE_TRANSFER, "transfer")
                  else GATE_DALPHA7)
        gate_line = f"\n  Scientific gate: {pretty} = NOT AUTHORIZED."
    return (
        f"BlockedParameterError:\n"
        f"  Parameter: {p.name} ({p.symbol})\n"
        f"  Object:    {p.object}\n"
        f"  Status:    BLOCKED -- no qualifying measurement exists.\n"
        f"  Source:    {p.source}{gate_line}\n"
        f"  Notes:     {p.notes}\n"
        f"  No biological fallback value is permitted. This parameter has no "
        f"value and the framework will not supply one.")


# --- loading the frozen inventory ------------------------------------------

def _default_freeze_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.normpath(os.path.join(here, ".."))
    return os.path.join(repo, "research", "model_input_freeze.csv")


def load_frozen_parameters(csv_path: Optional[str] = None,
                           ) -> ParameterSet:
    """Load research/model_input_freeze.csv into a :class:`ParameterSet`.

    Rows whose freeze value is ``NONE`` become BLOCKED parameters carrying no
    value, which is the whole point: absence is represented, never filled.
    """
    path = csv_path or _default_freeze_path()
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"frozen parameter inventory not found at {path}; regenerate with "
            f"python research/scripts/build_model_input_freeze.py")
    out: List[ModelParameter] = []
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            status = _status_from_freeze(
                row["safe_now"], row["assumption_only"], row["blocked"])
            raw = (row["value"] or "").strip()
            value = _parse_number(raw)
            # A row sourced from model CODE records what that artefact
            # literally executes, which is evidence about the artefact even
            # when the quantity is blocked. Nothing else may do this.
            recorded = (row.get("source_type", "").strip() == "model code")
            out.append(ModelParameter(
                name=row["parameter"],
                symbol=row["symbol"],
                value=value,
                unit=row["unit"],
                provenance=ModelProvenance(row["provenance"]),
                status=status,
                source=row["source"],
                object=row["object"],
                gate=row["gate"],
                evidence_strength=row["evidence_strength"],
                notes=row["notes"],
                conflict=(row.get("conflict", "").strip()
                          if row.get("conflict", "").strip() != "none" else ""),
                recorded_value=recorded))
    return ParameterSet(out)


def _parse_number(text: str) -> Optional[float]:
    """Extract the LEADING numeric quantity from a freeze value field.

    Freeze values carry their uncertainty inline, e.g. ``-67.8 +/- 5.5 SD
    (n=13)`` or ``43 +/- 2 (n=22)``, so only the first number is the value.
    Non-numeric fields (categorical labels, ``NONE``, ``NOT REPORTED``,
    ``CHANNEL ABSENT``) return None, which the caller treats as absence.
    """
    if not text:
        return None
    cleaned = text.split("(")[0].strip().replace("~", "")
    cleaned = cleaned.replace("+/-", " ").replace("±", " ")
    m = re.match(r"^[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", cleaned)
    return float(m.group(0)) if m else None


# --- gate entry points ------------------------------------------------------

def require_spatial_transfer() -> None:
    """Always raises. Spatial transfer is NOT AUTHORIZED."""
    raise BlockedParameterError(
        "BlockedParameterError:\n"
        "  PSI->MN5 spatial voltage transfer is NOT AUTHORIZED.\n"
        "  Required evidence: a measured contact->soma voltage transfer, or a "
        "validated electrical model built on measured parameters.\n"
        "  Currently missing: a Drosophila-specific axial resistance, a "
        "specific membrane resistance, an adjudicated whole-cell capacitance, "
        "a path to a labelled soma, and any direct transfer measurement.\n"
        "  No biological fallback value is permitted.")


def require_dalpha7_gate() -> None:
    """Always raises. Dalpha7 conductance is NOT AUTHORIZED."""
    raise BlockedParameterError(
        "BlockedParameterError:\n"
        "  Dalpha7 biological conductance is NOT AUTHORIZED.\n"
        "  Required evidence: a native PSI->MN5 Dalpha7 conductance or "
        "single-channel measurement.\n"
        "  Currently missing: every native Dalpha7 conductance, open "
        "probability, reversal potential, kinetic and Ca-permeability value; "
        "any Dalpha7 density at this synapse; and any Dalpha7 imaging at PSI "
        "terminals or MN5 axons. Drosophila additionally has no Kir7.1/"
        "KCNJ13 orthologue, so the vertebrate alpha7->Kir mechanism cannot be "
        "modelled.\n"
        "  No biological fallback value is permitted.")


# --- safe model core --------------------------------------------------------

@dataclass(frozen=True)
class MN5Anatomy:
    """Official MaleCNS anatomy. Pure metadata; carries no electrical value."""

    mn5_left: int
    mn5_right: int
    psi_left: int
    psi_right: int
    contacts_left: int
    contacts_right: int
    compartment_post_by_body: Mapping[int, Mapping[str, int]]
    coordinate_unit_nm: float
    source_layer: str

    def contact_summary(self) -> Dict[str, object]:
        total = self.contacts_left + self.contacts_right
        return {
            "total_contacts": total,
            "by_pairing": {
                f"{self.psi_left}->{self.mn5_left}": self.contacts_left,
                f"{self.psi_right}->{self.mn5_right}": self.contacts_right,
            },
            "compartment_post": {
                str(b): dict(c) for b, c in
                sorted(self.compartment_post_by_body.items())},
            "coordinate_unit_nm": self.coordinate_unit_nm,
            "provenance": "anatomical_measurement",
            "note": ("Official MaleCNS v1.0 metadata. The compartment label is "
                     "a DATASET ANNOTATION: not a distance, not a voltage, and "
                     "not a conductance."),
        }


class ReducedPassiveMN5:
    """A reduced MN5 representation built ONLY from SAFE parameters.

    This is explicitly NOT a cable model. ``Ra`` and ``Rm`` are blocked and
    ``Cm`` is conflicted, so no compartment model can be constructed. What is
    available is a single-compartment / reduced description whose inputs are
    all traceable to a native measurement.
    """

    def __init__(self, params: ParameterSet) -> None:
        self._params = params
        self._inputs: Dict[str, float] = {}
        for name in ("MN5 resting potential", "MN5 spike threshold",
                     "MN5 action potential amplitude"):
            # require_uncontested, not require: a contested value must never
            # enter a model silently.
            self._inputs[name] = params.require_uncontested(name)

    @property
    def inputs(self) -> Dict[str, float]:
        return dict(self._inputs)

    def summary(self) -> Dict[str, object]:
        return {
            "kind": "reduced single-compartment MN5 description",
            "is_cable_model": False,
            "why_not_cable": (
                "Ra and Rm are BLOCKED (no Drosophila-specific measurement) "
                "and whole-cell Cm is unresolved (C-01, 43 vs 127 pF)."),
            "inputs": dict(self._inputs),
            "assumptions_used": self._params.assumptions_used(),
            "provenance": (self._params.provenance_summary()["by_provenance"]),
        }


class SynapticInterface:
    """PSI->MN5 synaptic mechanism INTERFACE.

    Declares the mechanism surface without supplying a conductance. There is no
    default ``g_syn``: constructing a synaptic conductance requires an
    explicitly marked experimental parameter, and the frozen inventory has none.
    """

    REQUIRED = ("peak_conductance",)

    def __init__(self, params: ParameterSet) -> None:
        self._params = params

    def has_biological_conductance(self) -> bool:
        try:
            self._params.require("PSI->MN5 synaptic conductance")
        except BlockedParameterError:
            return False
        return True

    def conductance(self) -> float:
        """Raises. No biological PSI->MN5 conductance exists."""
        return self._params.require("PSI->MN5 synaptic conductance")

    def interface_report(self) -> Dict[str, object]:
        return {
            "interface": "PSI->MN5 chemical synapse",
            "required_inputs": list(self.REQUIRED),
            "biological_conductance_available": self.has_biological_conductance(),
            "contact_count": "available as anatomy (43, minconf 0.5)",
            "provenance": "anatomical_measurement for the metadata only",
            "note": ("No conductance, reversal potential, kinetics, quantal "
                     "analysis, active-zone count or receptor density is "
                     "available. None is defaulted."),
        }


class GFSInterface:
    """GFS electrical-coupling INTERFACE. No native conductance is inserted."""

    def __init__(self, params: ParameterSet) -> None:
        self._params = params

    def native_conductance_available(self) -> bool:
        for name in ("GF->PSI native junctional conductance",
                     "GF->TTMn native junctional conductance"):
            try:
                self._params.require(name)
            except BlockedParameterError:
                return False
        return True

    def coupling_coefficient(self) -> float:
        """Raises. No MN1->MN5 coupling coefficient has been reported."""
        return self._params.require("MN1->MN5 coupling coefficient")

    def interface_report(self) -> Dict[str, object]:
        return {
            "interface": "GFS electrical coupling",
            "native_conductance_available": self.native_conductance_available(),
            "mn1_mn5_coupling_coefficient_available": False,
            "usable_measurements": [
                "GF->TTMn pathway latency (measured)",
                "GF->PSI pathway latency (measured)",
                "GF->TTMn ShakB plaque fraction (measured)",
                "MN1-MN2 / MN3-MN4 coupling coefficient (measured, other "
                "neurons)",
            ],
            "note": ("The ModelDB gap-junction value carries an unresolved "
                     "1000x unit conflict (C-02) and the chemical synapse "
                     "another (C-03). Neither is a measurement and neither is "
                     "inserted."),
        }


class Dalpha7Interface:
    """Dalpha7 SCHEMA ONLY.

    Defines the mechanism surface. It deliberately cannot produce a
    conductance: :meth:`conductance` always raises, and no property of this
    class returns a number that could be mistaken for one.
    """

    REQUIRED = ("single_channel_conductance", "open_probability",
                "reversal_potential", "activation_kinetics",
                "desensitisation_kinetics", "density_at_synapse")

    def __init__(self, params: ParameterSet) -> None:
        self._params = params

    def conductance(self) -> float:
        require_dalpha7_gate()

    def schema(self) -> Dict[str, object]:
        return {
            "interface": "Dalpha7 nicotinic acetylcholine receptor",
            "required_inputs": list(self.REQUIRED),
            "available": False,
            "implemented": False,
            "provenance": "none",
            "blockers": [
                "no native Dalpha7 single-channel conductance",
                "no native open probability",
                "no native reversal potential (a 0 mV value is not measured)",
                "no native activation or desensitisation kinetics",
                "no Dalpha7 density at PSI->MN5",
                "no Dalpha7 imaging at PSI terminals or MN5 axons",
                "no Kir7.1/KCNJ13 orthologue in Drosophila",
            ],
            "note": ("This class is a SCHEMA. It exists so a future measurement "
                     "can be inserted without redesigning the architecture. It "
                     "does not implement Dalpha7 and cannot be coaxed into "
                     "producing a value."),
        }


class MN5Model:
    """The assembled model. Reports its own capability surface."""

    def __init__(self, params: ParameterSet, anatomy: MN5Anatomy) -> None:
        self.params = params
        self.anatomy = anatomy
        self.passive = ReducedPassiveMN5(params)
        self.synapse = SynapticInterface(params)
        self.coupling = GFSInterface(params)
        self.dalpha7 = Dalpha7Interface(params)

    def capabilities(self) -> Dict[str, object]:
        return {
            "anatomy": Capability.AVAILABLE,
            "reduced_passive_mn5": Capability.PARTIAL,
            "psi_mn5_synaptic_physiology": Capability.BLOCKED,
            "psi_mn5_spatial_transfer": Capability.BLOCKED,
            "dalpha7_receptor_conductance": Capability.BLOCKED,
            "gfs_electrical_coupling": Capability.PARTIAL,
        }

    def capability_notes(self) -> Dict[str, str]:
        return {
            "anatomy": "Official MaleCNS identities, 43 contacts, compartment "
                       "labels, geometry and paths. All SAFE.",
            "reduced_passive_mn5": "Restricted to SAFE native measurements. "
                                   "Not a cable model: Ra and Rm are blocked "
                                   "and Cm is conflicted.",
            "psi_mn5_synaptic_physiology": "No synaptic conductance exists in "
                                            "any source. Blocked.",
            "psi_mn5_spatial_transfer": "NOT AUTHORIZED. Never measured for "
                                        "Drosophila MN5.",
            "dalpha7_receptor_conductance": "NOT AUTHORIZED, and Drosophila has no "
                                   "Kir7.1 orthologue.",
            "gfs_electrical_coupling": "No native junctional conductance; the "
                                       "published value has an unresolved "
                                       "1000x conflict; MN1->MN5 CC "
                                       "unreported. Not a gate.",
        }

    def report(self) -> Dict[str, object]:
        return {
            "anatomy": self.anatomy.contact_summary(),
            "passive": self.passive.summary(),
            "synapse": self.synapse.interface_report(),
            "coupling": self.coupling.interface_report(),
            "dalpha7": self.dalpha7.schema(),
            "capabilities": {k: v.value for k, v in self.capabilities().items()},
            "capability_notes": self.capability_notes(),
            "provenance_summary": self.params.provenance_summary(),
            "gates": {
                "spatial_voltage_transfer": "NOT AUTHORIZED",
                "dalpha7_receptor_conductance": "NOT AUTHORIZED",
            },
            "non_inference": (
                "The framework does not infer biological parameters from "
                "desired model outputs."),
        }


# --- the frozen anatomy, as official metadata -------------------------------

FROZEN_MN5_ANATOMY = MN5Anatomy(
    mn5_left=801970, mn5_right=801295,
    psi_left=802401, psi_right=903327,
    contacts_left=17, contacts_right=26,
    compartment_post_by_body={
        801970: {"axon": 17},
        801295: {"axon": 26},
    },
    coordinate_unit_nm=1.0,
    source_layer=("gs://flyem-male-cns/v1.0/"
                  "male-cns-v1.0-synapses-precomputed"),
)


def build_model(csv_path: Optional[str] = None) -> MN5Model:
    """Assemble the model from the frozen inventory. No substitution occurs."""
    return MN5Model(load_frozen_parameters(csv_path), FROZEN_MN5_ANATOMY)
