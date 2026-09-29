"""Biological Brain 3.0 - Public API."""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, Optional
from .configuration import BiologicalMode, BIOLOGICAL_CIRCUITS
from .circuit import Circuit
from .neuron import Neuron
from .synapse import Synapse, Sign
from .neural_engine import NeuralEngine
from .signals import SignalTranslator
from .provenance import ParameterProvenance, ProvenanceRecord, evidence_to_provenance
from .morphology import Compartment, CompartmentModel, CompartmentGeometry, CompartmentProvenance, CableParameters, CompartmentState, PlacementRecord
from .gfs_morphology import GFSMorphology, NeuronSpec, CompartmentSpec, PlacementSpec, MorphologyParameter, get_gfs_morphology
from .morphology_builder import build_compartment_model, build_gfs_compartment_models
from .geometry_metrics import CompartmentMetrics, compute_compartment_metrics, compute_all_metrics, assert_no_electrical_parameters
from .passive_electrical_registry import PassiveParameterEntry, PassiveElectricalRegistry, get_passive_electrical_registry
from .passive_profiles import AuthorizedPassiveParameter, ExcludedPassiveParameter, PassiveParameterProfile, build_augustin_2019_gfs_passive_profile, get_passive_parameter_profile, available_passive_profiles, PROFILE_AUGUSTIN_2019_GFS_PASSIVE, AUTHORIZATION_SCOPE_MODEL_REPRODUCTION
from .active_conductance_registry import (ActiveParameterRecord, ChannelIdentityRecord, KineticReadinessRecord, ChannelImplementationRecord, ActiveConductanceRegistry, get_active_conductance_registry, SOURCE_AUGUSTIN_ACTIVE, SOURCE_AUGUSTIN_ACTIVE_CITATION, SOURCE_KADAS_GF_CHANNELS, SOURCE_MODELDB_CHANNELS)
from .active_profiles import AuthorizedActiveParameter, ExcludedActiveQuantity, UnreadyActiveKinetics, ActiveParameterProfile, build_augustin_2019_active_model_profile, get_active_parameter_profile, available_active_profiles, PROFILE_AUGUSTIN_2019_ACTIVE_MODEL
from .active_mechanism_registry import (ExtractedQuantity, ExtractedEquation, SourceAnnotation, ExtractedMechanism, UnretrievedSource, ActiveMechanismRegistry, get_active_mechanism_registry, MODELDB_MODEL_ID, MODELDB_MODEL_CITATION, MODEL_TEMPERATURE_C, KIND_DENSITY_CHANNEL, KIND_POINT_PROCESS, ROLE_MECHANISM_PARAMETER, ROLE_MODEL_INSTANCE_VALUE, STATUS_RETRIEVED, STATUS_UNRETRIEVED, STATUS_INSTANCE_VALUES_ONLY, TEMPERATURE_NONE_CELSIUS_UNUSED, TEMPERATURE_NONE_CELSIUS_ABSENT, TEMPERATURE_UNDETERMINED_NO_SOURCE, SOLVE_METHOD_CNEXP, CANONICAL_DENSITY_UNIT, CANONICAL_CONDUCTANCE_UNIT)
from .source_reconciliation import (SourceConflictRecord, SourceReconciliationRegistry, ConductanceSide, UnitConversion, ConflictStatus, ResolutionStatus, get_source_reconciliation_registry, CONFLICT_STATUS_SOURCE_CODE_UNIT_CONFLICT, RESOLUTION_STATUS_UNRESOLVED, SIDE_PAPER_INTENDED, SIDE_MODELDB_LITERAL, PAPER_YOUNG_US, PAPER_OLD_US, MODELDB_YOUNG_NS, MODELDB_OLD_NS, MODELDB_YOUNG_US, MODELDB_OLD_US, YOUNG_DISCREPANCY_FACTOR, OLD_DISCREPANCY_FACTOR, COMPARISON_UNIT)
from .synaptic_mechanism_registry import (SynapticQuantityRecord, SynapseTopologyRecord, ReceptorIdentityRecord, ExcludedSynapticQuantity, SynapticMechanismRegistry, SynapticEvidenceStatus, get_synaptic_mechanism_registry, SYNAPSE_GF_TTMN, SYNAPSE_GF_PSI, SYNAPSE_PSI_DLMN, TOPOLOGY_MIXED, TOPOLOGY_CHEMICAL, CHEMICAL_PEAK_US, CHEMICAL_RISE_MS, CHEMICAL_DECAY_MS, CHEMICAL_REVERSAL_MV, CHEMICAL_DELAY_MS, SOURCE_DLMN_WEIGHT, SOURCE_GF_TTMN_WEIGHT, SOURCE_GF_PSI_WEIGHT, PEAK_DISCREPANCY_FACTOR, DISCREPANCY_UNRESOLVED)
from .synaptic_abstraction import (SynapticConnectionSpec, SynapticParameterSpec, PathwayValidationTarget, HighFrequencyFollowingTarget, MechanisticRequirement, ReceptorAbstractionSpec, SynapseTimeParameters, SynapticAbstraction, Availability, get_synaptic_abstraction, CONNECTION_ELECTRICAL_AND_CHEMICAL, CONNECTION_CHEMICAL, SCOPE_GENERIC_MODEL_CHEMICAL_SYNAPSE, SCOPE_CONNECTION_SPECIFIC_SOURCE, LEVEL_PATHWAY, LEVEL_MOTOR_OUTPUT)
from .dynamics.passive_cable import PassiveCableModel, PassiveNetwork, PassiveNetworkState, CompartmentElectrical, AxialConnection, PassiveNumericalPolicy, PassiveBackendError, PassiveGeometryError, PassiveAuthorizationError, PassiveNumericalResolutionError, PassiveUnsupportedError, PASSIVE_CABLE_NUMERICAL_POLICY, MODEL_NAME_PASSIVE_CABLE_V0
from .electrical_representation import ElectricalExclusion, ElectricalRepresentation, insufficient_geometry_exclusion, computational_scope_exclusion, EXCLUSION_INSUFFICIENT_GEOMETRY, EXCLUSION_COMPUTATIONAL_MODEL_SCOPE, SCOPE_COMPUTATIONAL_LIMITATION, GeometryBlocker, geometry_blocker, get_exclusions, get_geometry_blockers, BLOCKER_REASON_INSUFFICIENT_SOURCE_GEOMETRY, REQUIRED_GEOMETRY_FIELDS
from .computational_topology import ComputationalSectionConnection, ComputationalTopology, AUGUSTIN_2019_GFS_COMPUTATIONAL_CONNECTIONS, AUGUSTIN_2019_GFS_COMPUTATIONAL_ROOTS, AUGUSTIN_2019_GFS_COMPUTATIONAL_TOPOLOGY, DIRECTION_PROXIMAL_TO_PROXIMAL, MODELDB_REPOSITORY, AUGUSTIN_MODELDB_FILE, TOPOLOGY_AUGUSTIN_2019_GFS, get_computational_topology
from .subdivision import SectionSubdivision, SubdivisionPlan, DerivedSegment, DEFAULT_SEGMENT_COUNT, derive_segments, map_placement_to_segment
from .dynamics import DynamicsModel, LIFVoltageModel, ConductanceDynamicsModel, ConductanceParams, ConductanceNeuronState, attach_conductance_state, MODEL_NAME_LIF_VOLTAGE, MODEL_NAME_CONDUCTANCE_V0


CIRCUIT_DIR = os.path.join(os.path.dirname(__file__), "data")


# APPROXIMATION: Looming input currents calibrated for simultaneous VP firing.
# Spec §7.1 defines LC4=3.0, LPLC2=2.0 (ratio matching synapse counts), but these
# drive VPs to threshold at different ticks (~8 vs ~16). GF requires both LC4 and
# LPLC2 input simultaneously (Ache 2019 summation model). Equal currents (5.0)
# ensure both VPs fire at the same tick, enabling GF threshold crossing.
# The synapse-count ratio is already encoded in VP->GF weights (15.0:10.0).
LOOMING_MAP = {
    "loomingLeft":  {"LC4_L": 5.0, "LPLC2_L": 5.0},
    "loomingRight": {"LC4_R": 5.0, "LPLC2_R": 5.0},
    "loomingFront": {"LC4_L": 3.0, "LC4_R": 3.0, "LPLC2_L": 3.0, "LPLC2_R": 3.0},
}

# APPROXIMATION: Fallback 2.0 stimulus currents calibrated for bilateral VP activation.
# Nociception maps to all 4 VPs with equal current (5.0) to ensure simultaneous
# bilateral GF firing. Spec §7.2 suggested 4.0/2.0 but asymmetric VP currents
# prevent GF summation on each hemisphere.
FALLBACK_MAP = {
    "lightLevel":   {"LC4_L": 1.5, "LC4_R": 1.5},
    "nociception":  {"LC4_L": 5.0, "LC4_R": 5.0, "LPLC2_L": 5.0, "LPLC2_R": 5.0},
    "dangerOdor":   {"LC4_L": 2.0, "LC4_R": 2.0},
    "touch":        {"LC4_L": 1.0, "LC4_R": 1.0},
}


@dataclass
class BiologicalBrain:
    """Biological neural layer facade.
    
    Exposes step(sensory_input) -> signals interface for 2.0 integration.
    """
    mode: BiologicalMode = BiologicalMode.LEGACY_2_0
    circuits: Dict[str, Circuit] = field(default_factory=dict)
    engines: Dict[str, NeuralEngine] = field(default_factory=dict)
    translators: Dict[str, SignalTranslator] = field(default_factory=dict)

    def __post_init__(self):
        self._build_circuits()

    def _build_circuits(self) -> None:
        """Construct circuits enabled in BIOLOGICAL_CIRCUITS."""
        if BIOLOGICAL_CIRCUITS.get("escape"):
            circuit = self._build_escape_circuit()
            self.circuits["escape_core"] = circuit
            self.engines["escape_core"] = NeuralEngine(circuit)
            self.translators["escape_core"] = SignalTranslator(circuit)

    def _build_escape_circuit(self) -> Circuit:
        """Load escape circuit from JSON data file.
        
        Implements the core visual-to-motor escape pathway:
        LC4/LPLC2 -> GF -> TTMn/PSI -> DLMn
        """
        filepath = os.path.join(CIRCUIT_DIR, "escape_circuit.json")
        with open(filepath) as f:
            data = json.load(f)
        
        circuit_def = data["circuit"]
        c = Circuit(name=circuit_def["name"])
        
        for nd in circuit_def["neurons"]:
            bp = nd["biophysics"]
            neuron = Neuron(
                neuron_id=nd["id"],
                cell_type=nd.get("cell_type", "unknown"),
                brain_region=nd.get("brain_region", "unknown"),
                neurotransmitter=nd.get("neurotransmitter", "unknown"),
                resting_potential=bp["V_rest"],
                threshold=bp["V_threshold"],
                reset_potential=bp["V_reset"],
                tau_m=bp["tau_m"],
                refractory_period=bp["refractory_period_ticks"],
            )
            c.add_neuron(neuron)
        
        for sd in circuit_def["synapses"]:
            src = sd["pre"]
            tgt = sd["post"]
            bio_sig = sd["sign"]
            sign = Sign.EXCITATORY if bio_sig == "excitatory" else Sign.INHIBITORY

            evidence = sd.get("evidence", [])
            provenance = evidence_to_provenance(evidence)

            c.add_synapse(Synapse(
                source=src, target=tgt,
                weight=sd["weight_mV"], sign=sign,
                delay=sd["delay_ticks"],
                neurotransmitter=sd.get("neurotransmitter", "unknown"),
                synapse_type=sd.get("type", "chemical"),
                conductance=sd.get("gap_junction_conductance_us", 0.0),
                evidence=evidence,
                provenance=provenance,
            ))
        
        io = circuit_def["circuit_io"]
        c.input_neurons = io["inputs"]
        c.output_neurons = io["outputs"]
        
        return c

    def step(self, sensory_input: Dict[str, float]) -> Dict[str, float]:
        """Public interface per framework §9.
        
        Args:
            sensory_input: 2.0 stimulate dict keys (lightLevel, nociception, etc.)
            
        Returns:
            Unified signal dict for 2.0 consumption (prefixed with 'bio_')
        """
        if self.mode == BiologicalMode.LEGACY_2_0:
            return {}

        all_signals = {}
        bio_input = self._map_sensory_input(sensory_input)

        for name, engine in self.engines.items():
            neural_out = engine.step(bio_input)
            signals = self.translators[name].translate(neural_out)
            # Prefix to avoid collision with 2.0 signals
            all_signals.update({f"bio_{k}": v for k, v in signals.items()})

        return all_signals

    def _map_sensory_input(self, stimulate: Dict) -> Dict[str, float]:
        """Translate 2.0 stimulate dict to biological input neuron currents.
        
        Three tiers:
        1. Biological-specific looming keys (loomingLeft/Right/Front) - direct VP drive
        2. Fallback to existing 2.0 stimulus keys mapped to VP activation
        3. 2.0 keys (lightLevel, nociception, dangerOdor, touch) as additional proxy triggers
        
        Multiple stimuli targeting the same neuron are summed.
        """
        merged = {}
        
        for key, targets in LOOMING_MAP.items():
            if key in stimulate and stimulate[key]:
                current = stimulate[key] if isinstance(stimulate[key], (int, float)) else 1.0
                for neuron_id, base_current in targets.items():
                    effective = base_current * current
                    if effective > 0:
                        merged[neuron_id] = merged.get(neuron_id, 0.0) + effective
        
        for key, targets in FALLBACK_MAP.items():
            if key in stimulate and stimulate[key]:
                for neuron_id, base_current in targets.items():
                    effective = base_current * (stimulate[key] if isinstance(stimulate[key], (int, float)) else 1.0)
                    if effective > 0:
                        merged[neuron_id] = merged.get(neuron_id, 0.0) + effective
        
        for key, value in stimulate.items():
            if key not in LOOMING_MAP and key not in FALLBACK_MAP and isinstance(value, (int, float)) and value > 0:
                for engine in self.engines.values():
                    if key in engine.circuit.neurons:
                        merged[key] = merged.get(key, 0.0) + value
                        break
        
        return merged

    def reset(self) -> None:
        """Reset all circuits to initial state."""
        for engine in self.engines.values():
            engine.reset()

    def get_circuit_state(self, circuit_name: str) -> Optional[Dict]:
        """Get internal state of a circuit for debugging."""
        engine = self.engines.get(circuit_name)
        if engine:
            return engine.get_state()
        return None


# Re-export key types
__all__ = [
    "BiologicalBrain",
    "BiologicalMode",
    "BIOLOGICAL_CIRCUITS",
    "Circuit",
    "Neuron",
    "Synapse",
    "Sign",
    "NeuralEngine",
    "SignalTranslator",
    "DynamicsModel",
    "LIFVoltageModel",
    "ConductanceDynamicsModel",
    "ConductanceParams",
    "ConductanceNeuronState",
    "attach_conductance_state",
    "MODEL_NAME_LIF_VOLTAGE",
    "MODEL_NAME_CONDUCTANCE_V0",
    "ParameterProvenance",
    "ProvenanceRecord",
    "Compartment",
    "CompartmentModel",
    "CompartmentGeometry",
    "CompartmentProvenance",
    "CableParameters",
    "CompartmentState",
    "PlacementRecord",
    "GFSMorphology",
    "NeuronSpec",
    "CompartmentSpec",
    "PlacementSpec",
    "MorphologyParameter",
    "get_gfs_morphology",
    "build_compartment_model",
    "build_gfs_compartment_models",
    "CompartmentMetrics",
    "compute_compartment_metrics",
    "compute_all_metrics",
    "assert_no_electrical_parameters",
]