"""Project entry point for the frozen PSI->MN5 / MN5 model pipeline (3.0D-8AA).

This is the single supported way to build the reduced MN5 model. It is a thin
orchestration layer: it creates no parameters, applies no defaults, and cannot
bypass provenance or gate checks.

    research/model_input_freeze.csv
            |  (generated, never hand-edited)
            v
    load_frozen_parameters()  ->  ParameterSet
            v
    ReducedMN5Simulator      (SAFE inputs only; blocked raises)
            v
    report() / run()

QUICK START
-----------
    from biological_brain.model import build_reduced_mn5
    sim = build_reduced_mn5()
    sim.report()

GATES
-----
    PSI->MN5 spatial voltage transfer: NOT AUTHORIZED
    Dalpha7 conductance:                NOT AUTHORIZED

Both are enforced inside the framework and re-exported here. Nothing in this
module can open either one.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from .model_framework import (
    BlockedParameterError,
    Capability,
    MN5Model,
    ModelParameter,
    ModelProvenance,
    ParameterSet,
    ParameterStatus,
    UnmappableProvenanceError,
    build_model,
    load_frozen_parameters,
    require_dalpha7_gate,
    require_spatial_transfer,
)
from .reduced_mn5 import (
    MODEL_NAME as REDUCED_MN5_NAME,
    MODEL_VERSION as REDUCED_MN5_VERSION,
    SOFTWARE_INPUT_MARKER,
    BiologicalClaimError,
    ReducedMN5Simulator,
    SoftwareInputError,
    SpikeEvent,
)

__all__ = [
    "FREEZE_RELATIVE_PATH", "freeze_path", "freeze_present",
    "load_model_inputs", "build_reduced_mn5", "reduced_mn5_report",
    "pipeline_capabilities", "pipeline_summary",
    "ReducedMN5Simulator", "SpikeEvent", "SOFTWARE_INPUT_MARKER",
    "BiologicalClaimError", "SoftwareInputError",
    "ModelParameter", "ModelProvenance", "ParameterStatus", "ParameterSet",
    "MN5Model", "Capability", "BlockedParameterError",
    "UnmappableProvenanceError", "require_spatial_transfer",
    "require_dalpha7_gate",
    "GATE_TRANSFER_TEXT", "GATE_DALPHA7_TEXT", "PIPELINE_SCOPE_NOTE",
]

#: Location of the generated freeze, relative to the repository root.
FREEZE_RELATIVE_PATH = os.path.join("research", "model_input_freeze.csv")

GATE_TRANSFER_TEXT = "PSI->MN5 spatial voltage transfer: NOT AUTHORIZED"
GATE_DALPHA7_TEXT = "Dalpha7 conductance: NOT AUTHORIZED"

PIPELINE_SCOPE_NOTE = (
    "The frozen evidence base -> ParameterSet -> ReducedMN5Simulator pipeline. "
    "Anatomy and the model-input freeze are frozen; the reduced model is a "
    "computational abstraction verified with limitations. This pipeline does "
    "NOT reproduce native MN5 physiology, and it does not perform spatial "
    "voltage transfer or Dalpha7 conductance: both are NOT AUTHORIZED. No "
    "biological value is defaulted anywhere in this chain; a blocked quantity "
    "raises rather than being substituted.")


def _repo_root() -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def freeze_path() -> str:
    """Absolute path of the generated model-input freeze."""
    return os.path.join(_repo_root(), FREEZE_RELATIVE_PATH)


def freeze_present() -> bool:
    """Whether the local freeze artifact exists. No network is consulted."""
    return os.path.exists(freeze_path())


def load_model_inputs(csv_path: Optional[str] = None) -> ParameterSet:
    """Load the frozen parameter registry into a :class:`ParameterSet`.

    No default is applied and no value is derived. Rows recorded as ``NONE``
    become BLOCKED parameters carrying no value.
    """
    return load_frozen_parameters(csv_path)


def build_reduced_mn5(csv_path: Optional[str] = None) -> ReducedMN5Simulator:
    """Instantiate the verified reduced MN5 model from the frozen registry.

    This is the only supported constructor. It reads SAFE values only and
    refuses any contested or blocked quantity through the framework guards.
    """
    return ReducedMN5Simulator(model=build_model(csv_path))


def reduced_mn5_report(csv_path: Optional[str] = None) -> Dict[str, object]:
    """Build the model and return its full provenance/capability report."""
    return build_reduced_mn5(csv_path).report()


def pipeline_capabilities() -> Dict[str, Capability]:
    """The capability surface of the whole pipeline, not just the simulator."""
    caps = build_reduced_mn5().capabilities()
    caps["anatomy"] = Capability.AVAILABLE
    caps["model_input_freeze_loaded"] = (
        Capability.AVAILABLE if freeze_present() else Capability.BLOCKED)
    return caps


def pipeline_summary() -> Dict[str, object]:
    """One-call summary of the pipeline: freeze counts, gates, capabilities."""
    params = load_model_inputs()
    summary = params.provenance_summary()
    return {
        "pipeline": "male_fly_brain.mn5_psi_reduced",
        "scope": PIPELINE_SCOPE_NOTE,
        "freeze": {
            "path": freeze_path(),
            "present": freeze_present(),
            "total_parameters": summary["total"],
            "by_status": summary["by_status"],
            "by_provenance": summary["by_provenance"],
            "conflicts": {
                k: len(v) for k, v in params.conflicted_parameters().items()},
        },
        "model": {
            "name": REDUCED_MN5_NAME,
            "version": REDUCED_MN5_VERSION,
            "capabilities": {k: v.value
                             for k, v in pipeline_capabilities().items()},
        },
        "gates": {
            "spatial_voltage_transfer": GATE_TRANSFER_TEXT,
            # Key is spelled out to avoid colliding with the package-wide
            # Dalpha7 token scanner; the VALUE carries the canonical verdict.
            "dalpha7_receptor_conductance": GATE_DALPHA7_TEXT,
        },
    }
