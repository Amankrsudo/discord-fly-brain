"""Pluggable neural dynamics models for Biological Brain 3.0.

This module provides an abstraction layer that separates neural dynamics
computation (integration, spike generation, reset) from the rest of the
NeuralEngine. The default ``lif_voltage`` model reproduces the exact
behavior of the original 3.0B Stage A LIF neuron.

No new biological parameters are introduced. Each model is an
APPROXIMATION of real neural dynamics.
"""

from .base import DynamicsModel, DynamicsModelFactory, NumericalResolution
from .lif_voltage import LIFVoltageModel
from .conductance import ConductanceDynamicsModel, ConductanceParams, ConductanceNeuronState, attach_conductance_state
from .passive_cable import (
    PassiveCableModel, PassiveNetwork, PassiveNetworkState, PassiveNumericalPolicy,
    CompartmentElectrical, AxialConnection, leak_current_A,
    AppliedParameter, PassiveParameterApplication,
    PassiveBackendError, PassiveGeometryError, PassiveAuthorizationError,
    PassiveNumericalResolutionError, PassiveNumericalMethodError,
    PassiveUnsupportedError,
    PassiveNumericalMethod, PassiveNumericalMethodRecord, BackwardEulerOperator,
    assemble_backward_euler_matrix,
    PASSIVE_CABLE_NUMERICAL_POLICY, PASSIVE_CABLE_REQUIRED_PARAMETERS,
    PASSIVE_PARAMETER_CANONICAL_UNITS, CANONICAL_AXIAL_RESISTIVITY_UNIT,
    FORBIDDEN_AXIAL_RESISTIVITY_UNITS,
    MODEL_NAME_PASSIVE_CABLE_V0,
)
from ..passive_profiles import PROFILE_AUGUSTIN_2019_GFS_PASSIVE
from functools import partial

__all__ = [
    "DynamicsModel",
    "DynamicsModelFactory",
    "NumericalResolution",
    "LIFVoltageModel",
    "ConductanceDynamicsModel",
    "ConductanceParams",
    "ConductanceNeuronState",
    "attach_conductance_state",
    "PassiveCableModel",
    "PassiveNetwork",
    "PassiveNetworkState",
    "PassiveNumericalPolicy",
    "CompartmentElectrical",
    "AxialConnection",
    "leak_current_A",
    "PassiveBackendError",
    "PassiveGeometryError",
    "PassiveAuthorizationError",
    "PassiveNumericalResolutionError",
    "PassiveNumericalMethodError",
    "PassiveUnsupportedError",
    "PassiveNumericalMethod",
    "PassiveNumericalMethodRecord",
    "BackwardEulerOperator",
    "assemble_backward_euler_matrix",
    "PASSIVE_CABLE_NUMERICAL_POLICY",
    "PASSIVE_CABLE_REQUIRED_PARAMETERS",
    "MODEL_NAME_LIF_VOLTAGE",
    "MODEL_NAME_CONDUCTANCE_V0",
    "MODEL_NAME_PASSIVE_CABLE_V0",
]

MODEL_NAME_LIF_VOLTAGE = "lif_voltage"
MODEL_NAME_CONDUCTANCE_V0 = "conductance_v0"
MODEL_NAME_PASSIVE_CABLE_V0 = "passive_cable_v0"

# Registry of available models (extendable by 3.0C phases).
# LIF voltage is the default and must remain numerically unchanged.
# Conductance is opt-in, architecture-only stub.
# Passive cable is opt-in, requires an explicit authorized profile, and
# declares its own (finer) numerical resolution policy.
#
# PassiveCableModel requires profile_name positionally, so its registry
# entry names the profile explicitly here rather than relying on a hidden
# default inside the class. The CompartmentModel must still declare the
# same profile before it can be solved.
MODELS = {
    MODEL_NAME_LIF_VOLTAGE: LIFVoltageModel,
    MODEL_NAME_CONDUCTANCE_V0: ConductanceDynamicsModel,
    MODEL_NAME_PASSIVE_CABLE_V0: partial(
        PassiveCableModel, profile_name=PROFILE_AUGUSTIN_2019_GFS_PASSIVE
    ),
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
