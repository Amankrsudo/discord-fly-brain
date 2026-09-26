"""Pluggable neural dynamics models for Biological Brain 3.0.

This module provides an abstraction layer that separates neural dynamics
computation (integration, spike generation, reset) from the rest of the
NeuralEngine. The default ``lif_voltage`` model reproduces the exact
behavior of the original 3.0B Stage A LIF neuron.

No new biological parameters are introduced. Each model is an
APPROXIMATION of real neural dynamics.
"""

from .base import DynamicsModel, DynamicsModelFactory
from .lif_voltage import LIFVoltageModel
from .conductance import ConductanceDynamicsModel, ConductanceParams, ConductanceNeuronState, attach_conductance_state

__all__ = [
    "DynamicsModel",
    "DynamicsModelFactory",
    "LIFVoltageModel",
    "ConductanceDynamicsModel",
    "ConductanceParams",
    "ConductanceNeuronState",
    "attach_conductance_state",
    "MODEL_NAME_LIF_VOLTAGE",
    "MODEL_NAME_CONDUCTANCE_V0",
]

MODEL_NAME_LIF_VOLTAGE = "lif_voltage"
MODEL_NAME_CONDUCTANCE_V0 = "conductance_v0"

# Registry of available models (extendable by 3.0C phases).
# LIF voltage is the default and must remain numerically unchanged.
# Conductance is opt-in, architecture-only stub.
MODELS = {
    MODEL_NAME_LIF_VOLTAGE: LIFVoltageModel,
    MODEL_NAME_CONDUCTANCE_V0: ConductanceDynamicsModel,
}


def get_model(name: str = MODEL_NAME_LIF_VOLTAGE) -> DynamicsModel:
    """Retrieve a dynamics model instance by name.

    Defaults to ``lif_voltage`` which reproduces the original 3.0B behavior.
    """
    if name in MODELS:
        return MODELS[name]()
    raise ValueError(
        f"Unknown dynamics model '{name}'. Available: {list(MODELS.keys())}"
    )
