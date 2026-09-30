"""Looming / visual-input abstraction (3.0D-7Y).

3.0D-7W specified the CENTRAL synapses and the pathway validation targets.
3.0D-7X specified the OUTPUT END: the TTMn->TTM and DLMn->DLM glutamatergic
neuromuscular junctions, the fact that standard GFS muscle recordings are
end-to-end output measurements, and the experimental motor-neuron bypass. This
checkpoint specifies the INPUT END: the two looming-sensitive visual projection
neurons that drive the GF, the stimulus features they extract, and the published
phenomenological model of the GF looming response.

Why this layer exists
---------------------
The GF is the one neuron in this project that is known to receive DIRECT visual
input. Ache et al. 2019 established that two visual projection neurons (VPNs)
synapse directly onto the GF and that between them they supply the two features
the GF is known to integrate:

    angular velocity   ->  LC4   (lobula columnar, type 4)
    angular size       ->  LPLC2 (lobula plate/lobula columnar, type 2)

The project's escape circuit already names LC4 and LPLC2 neurons as input
neurons. What it does not have, and what this layer records as absent, is any
mechanism by which a moving object could become a current in either neuron.

Stimulus features are not membrane variables
--------------------------------------------
``angular_size`` and ``angular_velocity`` are properties of the STIMULUS. They
are dimensionless ratios of an object's subtended visual angle and its rate of
change. They are NOT voltages, NOT currents, NOT conductances, and NOT states
of any compartment. ``StimulusFeatureSpec`` records them as external stimulus
features with an explicit ``is_membrane_variable = False`` invariant, and
refuses at construction to be marked as one.

The published phenomenological model is a FUNCTION, not a mechanism
-------------------------------------------------------------------
Ache et al. 2019 report a model that sums a LINEAR function of angular velocity
(provided by LC4) with a GAUSSIAN function of angular size (provided by
LPLC2), and state that this model "replicates GF looming response dynamics and
predicts the peak response time". That is a statement about the SHAPE of a
stimulus-response curve. It is not a statement about ion channels, and it does
not license converting either term into a synaptic current.

The distinction is enforced structurally here. ``PhenomenologicalModelTerm``
records a term's functional FORM (a symbolic ``linear`` or ``gaussian`` label)
and carries no amplitude, no slope, no width, no offset and no time constant.
A term cannot be turned into a current, because there is nowhere in the record
to put a current, and because ``is_membrane_current`` is a hard False that
raises if set.

What the sources do NOT provide
-------------------------------
The three retrieved sources are a quantitative anatomy/physiology paper
(Klapoetke et al. 2017), a review (Kohn et al. 2018) and a recent study
(Jang et al. 2023). None of them states an LC4 or LPLC2 membrane conductance, a
channel density, Hodgkin-Huxley kinetics, an LC4->GF or LPLC2->GF synaptic
conductance, a release probability, a receptor kinetic constant, or a Q10. The
term "conductance" does not appear in Klapoetke et al. 2017 at all: the only
electrophysiology in that paper is whole-cell recording FROM THE GIANT FIBER
soma in response to optogenetic activation of LPLC2, which produced "a large
and rapid depolarization of the giant fiber" with no amplitude, no unitary
synapse and no conductance reported. All LPLC2 data in that paper are two-photon
GCaMP6 calcium imaging.

Ache et al. 2019 is the source of the MODEL STRUCTURE, not of its parameters.
The full text is behind a subscription (Europe PMC reports ``inPMC: N``), so
the project has the abstract's model sentence and not the equations. No
coefficient is guessed, and none is recorded. The unavailable-coefficient
quantities are tracked explicitly so that a later checkpoint with access to the
full text has a defined place to put them.

LPLC2 radial motion opponency is qualitative
---------------------------------------------
Klapoetke et al. 2017 establish that LPLC2 dendrites form an outward pattern
that encodes local outward motion, and that "each dendritic arm also receives
local inhibitory inputs directionally selective for inward motion opposing the
excitation". This is recorded as a QUALITATIVE functional property: outward
motion drives an excitatory component, inward motion drives an inhibitory one.
No inhibitory conductance, no excitatory conductance, no reversal potential, no
synaptic delay and no receptive-field membrane model is attached, because none
is stated by the source.

The GF sensory conductance does not exist here
----------------------------------------------
The project refuses to create a GF sensory conductance. Ache et al. 2019 show
by electron-microscopy reconstruction that LC4 and LPLC2 "synapse directly onto
the GF"; that establishes a CONNECTION, not a conductance. A direct connection
does not determine how much current it delivers, through what receptor, with
what reversal potential, at what rate. ``GFVisualInputRecord`` therefore names
the connection and holds ``gf_sensory_conductance = None`` as a structural
invariant.

Stimulus frame rates are not neural timesteps
---------------------------------------------
Klapoetke et al. 2017 present looming stimuli on a display running at 180 Hz,
and Jang et al. 2023 discuss the r/v ratio. Those are STIMULUS PRESENTATION
parameters. They are not neural integration times, and neither may be
reinterpreted as one. The project's numerical timestep policy is unchanged by
this checkpoint, and ``stimulus_presentation_rates`` is a prose record of the
display rate, not a timestep field.

Relationship to 3.0D-7W and 3.0D-7X
-----------------------------------
The intended future pathway is conceptual only:

    visual stimulus
        -> LC4 / LPLC2 feature extraction
        -> GF
        -> TTMn / PSI / DLMn
        -> NMJs
        -> muscle output

That is a STAGE DIAGRAM, not a simulator. ``PathwayStageDiagram`` names the
stages and records which earlier checkpoint owns the motor-output end, so the
7Y layer can reference TTMn/PSI/DLMn and the NMJs by name without duplicating a
single 7W validation number or 7X NMJ quantity. The GF stimulus-response curve
remains an OUTPUT of 3.0D-7W.

Hard boundaries
---------------
``live_solver_eligible`` is False on every record and on the layer itself, and
cannot be set otherwise. This module:

- does NOT implement LC4 membrane dynamics or Hodgkin-Huxley kinetics;
- does NOT implement LPLC2 membrane dynamics or Hodgkin-Huxley kinetics;
- does NOT implement photoreceptors, the phototransduction cascade, or any
  optic-lobe circuit;
- does NOT create an LC4->GF or LPLC2->GF synaptic conductance;
- does NOT create a GF sensory conductance or modify the GF morphology, the GF
  passive parameters, the GF active profile, ``CompartmentElectrical`` or
  ``PassiveNetwork``;
- does NOT convert a phenomenological term into a membrane current;
- does NOT invent a velocity-term slope, a Gaussian amplitude, width or offset,
  or any other coefficient of the Ache et al. 2019 model;
- does NOT import a photoreceptor or optic-lobe parameter from another species,
  another preparation, or another neuron class;
- does NOT reinterpret a stimulus frame rate, presentation rate or experimental
  sampling interval as a neural integration timestep;
- does NOT duplicate the 3.0D-7W validation targets or the 3.0D-7X NMJ
  quantities;
- does NOT import, modify or get imported by ``PassiveCableModel``,
  ``PassiveNetwork``, ``PassiveNetworkState``, ``CompartmentElectrical``,
  ``active_profiles`` or ``active_mechanism_registry``, and does not change
  the numerical timestep policy.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from .provenance import ParameterProvenance
from .synaptic_mechanism_registry import SynapticEvidenceStatus


# --- neuron classes ---------------------------------------------------------

NEURON_LC4 = "LC4"
NEURON_LPLC2 = "LPLC2"
NEURON_GF = "GF"

# --- feature labels ---------------------------------------------------------

FEATURE_ANGULAR_VELOCITY = "angular_velocity"
FEATURE_ANGULAR_SIZE = "angular_size"

# --- connection label -------------------------------------------------------

CONNECTION_DIRECT_VISUAL_INPUT = "direct_visual_input"

# --- functional-form labels -------------------------------------------------
#
# A functional FORM is a symbolic label for the shape of a published
# stimulus-response relationship. It is not an equation with coefficients and it
# is not a current.

FORM_LINEAR = "linear"
FORM_GAUSSIAN = "gaussian"
FORM_SUM = "sum_of_published_functions"

# --- stimulus-space rate labels ---------------------------------------------
#
# These name quantities in STIMULUS space. None of them is a neural integration
# time and none may be reinterpreted as one.

STIMULUS_DISPLAY_FRAME_RATE = "stimulus_display_frame_rate"
STIMULUS_RADIUS_OVER_VELOCITY_RATIO = "stimulus_radius_over_velocity_ratio"

# --- combined-input label ----------------------------------------------------
#
# The combined GF term takes BOTH looming features, so it carries this label
# rather than either single feature name.

_BOTH_FEATURES = f"{FEATURE_ANGULAR_VELOCITY} and {FEATURE_ANGULAR_SIZE}"

_STAGE_VISUAL_STIMULUS = "visual stimulus"
_STAGE_FEATURE_EXTRACTION = "LC4 / LPLC2 feature extraction"
_STAGE_GF = "GF"
_STAGE_DESCENDING_MOTOR = "TTMn / PSI / DLMn"
_STAGE_NMJ = "NMJs"
_STAGE_MUSCLE_OUTPUT = "muscle output"


# --- source references ------------------------------------------------------

SOURCE_ACHE_2019 = (
    "Ache JM, Polsky J, Alghailani S, Parekh R, Breads P, Peek MY, Bock DD, "
    "von Reyn CR, Card GM (2019). Neural Basis for Looming Size and Velocity "
    "Encoding in the Drosophila Giant Fiber Escape Pathway. Curr Biol "
    "29(6):1073-1081.e4. https://pubmed.ncbi.nlm.nih.gov/30827912/ . "
    "Establishes that LC4 and LPLC2 provide the entire velocity and size "
    "components of the GF looming response, that LPLC2 silencing eliminates the "
    "size component leaving only the velocity component, that LC4 and LPLC2 "
    "synapse directly onto the GF by EM reconstruction, and that 'A model "
    "summing a linear function of angular velocity (provided by LC4) and a "
    "Gaussian function of angular size (provided by LPLC2) replicates GF "
    "looming response dynamics and predicts the peak response time'. The full "
    "text is behind a subscription (Europe PMC reports inPMC: N), so the "
    "project holds this abstract-level model statement and NOT the equations. "
    "States NO coefficient of the model, and NO LC4 or LPLC2 conductance, "
    "channel density, Hodgkin-Huxley kinetics, synaptic conductance, release "
    "probability, receptor kinetics or Q10."
)

SOURCE_KLAPOETKE_2017 = (
    "Klapoetke NC, Nern A, Peek MY, Rogers EM, Breads P, Rubin GM, Reiser MB, "
    "Card GM (2017). Ultra-selective looming detection from radial motion "
    "opponency. Nature 551(7679):237-241. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7457385/ . Establishes LPLC2 as "
    "a population of ~80 visual projection neurons whose axons terminate near "
    "the lateral dendrite of the giant fiber, whose dendrites form an outward "
    "pattern encoding local outward motion, and where 'each dendritic arm also "
    "receives local inhibitory inputs directionally selective for inward motion "
    "opposing the excitation'. Reports that LPLC2 activation produced 'a large "
    "and rapid depolarization of the giant fiber... consistent with LPLC2s "
    "providing direct excitatory input to the giant fiber', and that T4 and T5 "
    "are directly upstream of LPLC2. The term conductance does not appear in "
    "this paper and NO LPLC2 membrane property is reported: all LPLC2 data are "
    "two-photon GCaMP6 calcium imaging."
)

SOURCE_KOHN_2018 = (
    "Kohn JR, Heath SL, Behnia R (2018). Eyes Matched to the Prize: The State "
    "of Matched Filters in Insect Visual Circuits. Front Neural Circuits 12:26. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC5893817/ . States that "
    "'Information about the angular velocity of looming objects is provided by "
    "the type 4 lobula columnar (LC4) cell, a second presynaptic partner of the "
    "GF interneuron', that LPLC2 'are strongly driven by motion outward from "
    "the center of their receptive field, and inhibited by inward motion', that "
    "'The output of LPLC2 cells provides the GF interneuron with information "
    "about the angular size of a looming object', and that GF activity works "
    "'By linearly integrating input from LC4 and LPLC2 pathways'. States NO "
    "numeric value for either neuron."
)

SOURCE_JANG_2023 = (
    "Jang H, Goodman DP, Ausborn J, von Reyn CR (2023). Azimuthal invariance "
    "to looming stimuli in the Drosophila giant fiber escape circuit. J Exp Biol "
    "226(8):jeb244790. "
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10263144/ . States that 'the VPNs "
    "LC4 and LPLC2 that provide ipsilateral visual input to the GF have small, "
    "ipsilaterally restricted receptive fields' and that 'LC4's angular "
    "velocity contribution to the GF response increases as r/v decreases (while "
    "LPLC2's angular size contribution remains constant)'. Reports NO numeric "
    "biophysical value and NO absolute GF looming-response latency."
)


# --- the project refuses these inferences -----------------------------------

_NOT_LIVE = (
    "3.0D-7Y IS A SPECIFICATION CHECKPOINT ONLY. This record is NOT eligible "
    "for the live solver: no visual-neuron membrane is modelled, no Hodgkin-"
    "Huxley kinetics exist for LC4 or LPLC2, no synaptic conductance is "
    "computed, no GF sensory conductance exists, no stimulus feature is a "
    "membrane variable, and the passive backend is unchanged."
)

_NO_SENSORY_MECHANISM = (
    "NO VISUAL-NEURON MECHANISM EXISTS IN ANY RETRIEVED SOURCE. Klapoetke et "
    "al. 2017, Kohn et al. 2018 and Jang et al. 2023 state NO LC4 or LPLC2 "
    "membrane conductance, NO channel density, NO Hodgkin-Huxley kinetics, NO "
    "LC4->GF or LPLC2->GF synaptic conductance, NO release probability, NO "
    "receptor kinetics and NO Q10. In Klapoetke et al. 2017 the only "
    "electrophysiology is whole-cell recording FROM THE GIANT FIBER soma "
    "during optogenetic activation of LPLC2, and every LPLC2 measurement in "
    "that paper is two-photon GCaMP6 calcium imaging. None of these quantities "
    "is created, estimated, borrowed or fitted here, and none may be filled "
    "with a generic Drosophila value, a value from another neuron class, or a "
    "value from another species."
)

_NO_PHENOMENOLOGICAL_CONVERSION = (
    "A PHENOMENOLOGICAL TERM IS A FUNCTION, NOT A MECHANISM. A linear function "
    "of angular velocity and a Gaussian function of angular size describe the "
    "SHAPE of a published stimulus-response curve. They are not membrane "
    "currents, not synaptic conductances and not channel descriptions. NO term "
    "is converted into a current, and no term may be multiplied by a "
    "conductance, added to a membrane state, or used to drive a compartment."
)

_NO_GF_SENSORY_CONDUCTANCE = (
    "NO GF SENSORY CONDUCTANCE IS CREATED. Ache et al. 2019 show by electron-"
    "microscopy reconstruction that LC4 and LPLC2 synapse directly onto the "
    "GF. A DIRECT CONNECTION IS NOT A CONDUCTANCE. It does not determine how "
    "much current the connection delivers, through which receptor, at which "
    "reversal potential, or at what rate. The GF morphology, the GF passive "
    "parameters, the GF active profile, CompartmentElectrical and PassiveNetwork "
    "are all unchanged by this checkpoint."
)

_NO_STIMULUS_TIMESTEP = (
    "NO SENSORY TIMESTEP IS INTRODUCED. The 180 Hz display frame rate of "
    "Klapoetke et al. 2017 and the r/v stimulus ratio discussed by Jang et al. "
    "2023 are STIMULUS PRESENTATION parameters. They are not neural integration "
    "times and neither may be reinterpreted as one. The project's numerical "
    "timestep policy is unchanged by 3.0D-7Y."
)

_NO_MODEL_COEFFICIENTS = (
    "NO COEFFICIENT OF THE PUBLISHED MODEL IS RECORDED. Ache et al. 2019 is "
    "behind a subscription, so the project holds the abstract's model sentence "
    "and not the equations. The velocity-term slope, the Gaussian amplitude, "
    "width and offset, and the relative weighting of the two terms are all "
    "UNKNOWN. None is guessed, back-calculated from a response curve, or "
    "borrowed from the locust LGMD model or any other loom-detection model."
)

_NO_MOTOR_OUTPUT_DUPLICATION = (
    "MOTOR-OUTPUT TARGETS ARE OWNED BY 3.0D-7W AND 3.0D-7X, NOT BY 3.0D-7Y. "
    "The stage diagram names TTMn, PSI, DLMn, the NMJs and the muscle output so "
    "the visual input has a stated destination, and names them only. No 7W "
    "validation number, no 7X NMJ quantity and no 7U gap-junction quantity is "
    "restated, copied or re-derived here."
)


# --- A/B: visual projection neuron specifications ---------------------------


@dataclass(frozen=True)
class VisualProjectionNeuronSpec:
    """One looming-sensitive visual projection neuron that drives the GF.

    This record type carries NO numeric field of any kind. It cannot be given a
    membrane conductance, a channel density, a Hodgkin-Huxley kinetic rate, a
    synaptic conductance, a release probability or a receptor parameter through
    this path, which is the point. It records WHICH FEATURE the neuron carries
    and WHERE it projects, both of which are experimentally supported.
    """

    neuron_class: str
    cell_class: str
    feature_extracted: str
    target_neuron: str
    connection_type: str
    anatomical_location: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    experimentally_supported: bool
    mechanistic_live_solver_ready: bool
    source_references: Tuple[str, ...]
    notes: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Visual projection neuron '{self.neuron_class}' cannot be "
                f"live-solver eligible. 3.0D-7Y specifies which stimulus "
                f"feature each neuron carries; it does not model the neuron."
            )
        if self.mechanistic_live_solver_ready:
            raise ValueError(
                f"Visual projection neuron '{self.neuron_class}' must not be "
                f"marked mechanistically live-solver ready. No retrieved "
                f"source states a conductance, a channel density, a kinetic "
                f"rate or a synaptic conductance for it."
            )
        if self.connection_type != CONNECTION_DIRECT_VISUAL_INPUT:
            raise ValueError(
                f"Visual projection neuron '{self.neuron_class}' must be "
                f"recorded as a '{CONNECTION_DIRECT_VISUAL_INPUT}', got "
                f"'{self.connection_type}'."
            )
        if self.target_neuron != NEURON_GF:
            raise ValueError(
                f"Visual projection neuron '{self.neuron_class}' must target "
                f"'{NEURON_GF}'. LC4 and LPLC2 provide direct input to the GF "
                f"and to no other target recorded here."
            )
        if self.feature_extracted not in (
            FEATURE_ANGULAR_VELOCITY, FEATURE_ANGULAR_SIZE
        ):
            raise ValueError(
                f"Visual projection neuron '{self.neuron_class}' must carry a "
                f"recorded stimulus feature, got "
                f"'{self.feature_extracted}'."
            )
        if not self.experimentally_supported:
            raise ValueError(
                f"Visual projection neuron '{self.neuron_class}' must state its "
                f"experimental support; this layer records experimentally "
                f"supported feature-to-GF assignments."
            )
        if self.evidence_status is not (
            SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED
        ):
            raise ValueError(
                f"Visual projection neuron '{self.neuron_class}' must carry "
                f"the status 'experimentally_constrained': the feature it "
                f"carries and its projection to the GF are direct experimental "
                f"observations."
            )
        if not self.source_references:
            raise ValueError(
                f"Visual projection neuron '{self.neuron_class}' must carry at "
                f"least one source reference."
            )
        if not self.anatomical_location:
            raise ValueError(
                f"Visual projection neuron '{self.neuron_class}' must state its "
                f"anatomical location, so it is not confused with the "
                f"central-brain descending neurons modelled at 3.0D-7A."
            )

    @property
    def is_visual_projection_neuron(self) -> bool:
        return True

    @property
    def is_optic_lobe_neuron(self) -> bool:
        """True: LC4 and LPLC2 are optic-lobe visual projection neurons."""
        return True

    @property
    def has_quantitative_parameter(self) -> bool:
        """Always False: the record type carries no number."""
        return False

    @property
    def drives_gf_directly(self) -> bool:
        return True

    def limitations(self) -> str:
        return (
            f"EXPERIMENTALLY SUPPORTED FEATURE-TO-GF ASSIGNMENT. {self.notes} "
            f"{_NO_SENSORY_MECHANISM} {_NO_GF_SENSORY_CONDUCTANCE} "
            f"{_NO_STIMULUS_TIMESTEP} {_NOT_LIVE}"
        )


# --- C: external stimulus features -------------------------------------------


@dataclass(frozen=True)
class StimulusFeatureSpec:
    """A feature of the stimulus, not a state of any membrane.

    ``angular_size`` and ``angular_velocity`` describe the retinal image of an
    approaching object. They are dimensionless stimulus coordinates. This
    record type carries no numeric field, and ``is_membrane_variable`` is a
    hard False that raises if set: these names must never become a compartment
    state, a voltage, a current or a conductance.
    """

    feature_id: str
    feature_name: str
    feature_kind: str
    described_as: str
    carried_by: str
    used_by: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    is_membrane_variable: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Stimulus feature '{self.feature_id}' cannot be live-solver "
                f"eligible. A stimulus feature is an external input "
                f"description, not a simulated state."
            )
        if self.is_membrane_variable:
            raise ValueError(
                f"Stimulus feature '{self.feature_id}' must NOT be a membrane "
                f"variable. {self.feature_name} is a property of the STIMULUS. "
                f"It is not a voltage, a current, a conductance, or a state of "
                f"any compartment, and it must not be added to a neuron state."
            )
        if self.feature_kind != "external_stimulus_feature":
            raise ValueError(
                f"Stimulus feature '{self.feature_id}' must be recorded as an "
                f"external stimulus feature, got '{self.feature_kind}'."
            )
        if self.feature_id not in (
            FEATURE_ANGULAR_VELOCITY, FEATURE_ANGULAR_SIZE
        ):
            raise ValueError(
                f"Stimulus feature '{self.feature_id}' is not one of the two "
                f"looming features recorded at 3.0D-7Y."
            )
        if not self.carried_by:
            raise ValueError(
                f"Stimulus feature '{self.feature_id}' must name the neuron "
                f"that carries it."
            )
        if not self.source_references:
            raise ValueError(
                f"Stimulus feature '{self.feature_id}' must carry at least one "
                f"source reference."
            )

    @property
    def is_external_stimulus(self) -> bool:
        return True

    @property
    def has_numeric_value(self) -> bool:
        """Always False: no stimulus amplitude, rate or range is recorded."""
        return False

    def limitations(self) -> str:
        return (
            f"EXTERNAL STIMULUS FEATURE, NOT A MEMBRANE VARIABLE. {self.notes} "
            f"{_NO_SENSORY_MECHANISM} {_NO_STIMULUS_TIMESTEP} {_NOT_LIVE}"
        )


# --- D: the published phenomenological model ---------------------------------


@dataclass(frozen=True)
class PhenomenologicalModelTerm:
    """One term of the published GF looming-response model.

    The record captures a FUNCTIONAL FORM: a symbolic label for the shape of a
    published relationship between a stimulus feature and the GF response. It
    carries NO amplitude, NO slope, NO width, NO offset, NO weight and NO time
    constant, and it has no field in which a membrane current could be placed.
    ``is_membrane_current`` is a hard False that raises if set.
    """

    term_id: str
    provided_by: str
    input_feature: str
    functional_form: str
    published_statement: str
    combines_into: str
    equation_available: bool
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    is_membrane_current: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Phenomenological term '{self.term_id}' cannot be "
                f"live-solver eligible. A phenomenological function is not a "
                f"mechanism and drives no compartment."
            )
        if self.is_membrane_current:
            raise ValueError(
                f"Phenomenological term '{self.term_id}' must NOT be a "
                f"membrane current. It is a published stimulus-response "
                f"FUNCTION and must not be converted into a current, a "
                f"conductance or a membrane state."
            )
        if self.functional_form not in (
            FORM_LINEAR, FORM_GAUSSIAN, FORM_SUM
        ):
            raise ValueError(
                f"Phenomenological term '{self.term_id}' must carry a recorded "
                f"functional form ('{FORM_LINEAR}', '{FORM_GAUSSIAN}' or "
                f"'{FORM_SUM}'), got '{self.functional_form}'."
            )
        if self.equation_available:
            raise ValueError(
                f"Phenomenological term '{self.term_id}' must not claim the "
                f"equation is available. Ache et al. 2019 is behind a "
                f"subscription and the project holds no equation."
            )
        if self.input_feature not in (
            FEATURE_ANGULAR_VELOCITY, FEATURE_ANGULAR_SIZE, _BOTH_FEATURES
        ):
            raise ValueError(
                f"Phenomenological term '{self.term_id}' must take a recorded "
                f"looming stimulus feature as its input, got "
                f"'{self.input_feature}'."
            )
        if not self.published_statement:
            raise ValueError(
                f"Phenomenological term '{self.term_id}' must carry the "
                f"published statement of its form."
            )
        if not self.source_references:
            raise ValueError(
                f"Phenomenological term '{self.term_id}' must carry at least "
                f"one source reference."
            )

    @property
    def carries_a_coefficient(self) -> bool:
        """Always False: no slope, amplitude, width, offset or weight."""
        return False

    @property
    def is_a_mechanism(self) -> bool:
        """Always False: this is a function, not a biophysical mechanism."""
        return False

    def limitations(self) -> str:
        return (
            f"PUBLISHED PHENOMENOLOGICAL FUNCTION, NOT A MECHANISM. "
            f"{self.published_statement} {self.notes} "
            f"{_NO_PHENOMENOLOGICAL_CONVERSION} {_NO_MODEL_COEFFICIENTS} "
            f"{_NO_SENSORY_MECHANISM} {_NOT_LIVE}"
        )


# --- E: LPLC2 radial motion opponency ----------------------------------------


@dataclass(frozen=True)
class RadialMotionOpponencyComponent:
    """One qualitative direction component of LPLC2 radial motion opponency.

    The record states a SIGN and a DIRECTION and nothing else. It has no
    conductance, no reversal potential, no delay and no amplitude, because
    Klapoetke et al. 2017 report none. ``is_qualitative`` is a hard True that
    raises if cleared.
    """

    component_id: str
    motion_direction: str
    functional_effect: str
    described_as: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    is_qualitative: bool = True
    has_conductance: bool = False
    has_reversal_potential: bool = False
    has_synaptic_delay: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Opponency component '{self.component_id}' cannot be "
                f"live-solver eligible. It is a qualitative functional "
                f"statement, not a synaptic model."
            )
        if not self.is_qualitative:
            raise ValueError(
                f"Opponency component '{self.component_id}' must remain "
                f"qualitative. The source states a direction and a sign and no "
                f"amplitude, so nothing quantitative may be attached to it."
            )
        if self.has_conductance or self.has_reversal_potential or (
            self.has_synaptic_delay
        ):
            raise ValueError(
                f"Opponency component '{self.component_id}' must not carry a "
                f"conductance, a reversal potential or a synaptic delay. No "
                f"source states any of them for LPLC2."
            )
        if self.functional_effect not in ("excitatory", "inhibitory"):
            raise ValueError(
                f"Opponency component '{self.component_id}' must be recorded as "
                f"'excitatory' or 'inhibitory', got "
                f"'{self.functional_effect}'."
            )
        if not self.source_references:
            raise ValueError(
                f"Opponency component '{self.component_id}' must carry at "
                f"least one source reference."
            )

    @property
    def is_excitatory(self) -> bool:
        return self.functional_effect == "excitatory"

    @property
    def is_inhibitory(self) -> bool:
        return self.functional_effect == "inhibitory"

    @property
    def has_quantitative_value(self) -> bool:
        """Always False."""
        return False

    def limitations(self) -> str:
        return (
            f"QUALITATIVE FUNCTIONAL EVIDENCE. {self.notes} "
            f"{_NO_SENSORY_MECHANISM} {_NO_STIMULUS_TIMESTEP} {_NOT_LIVE}"
        )


# --- F: GF visual input ------------------------------------------------------


@dataclass(frozen=True)
class GFVisualInputRecord:
    """The direct LC4 and LPLC2 input to the GF. NOT a conductance.

    Ache et al. 2019 establish the connection by electron-microscopy
    reconstruction. That establishes THAT the input exists, not how much
    current it delivers. ``gf_sensory_conductance`` is structurally None and
    cannot be set.
    """

    input_id: str
    target_neuron: str
    input_neurons: Tuple[str, ...]
    connection_basis: str
    reported_response: str
    attributable_gf_synaptic_conductance: bool
    modifies_gf_morphology: bool
    modifies_gf_passive_parameters: bool
    modifies_gf_active_profile: bool
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    gf_sensory_conductance: None = None
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"GF visual input '{self.input_id}' cannot be live-solver "
                f"eligible."
            )
        if self.gf_sensory_conductance is not None:
            raise ValueError(
                f"GF visual input '{self.input_id}' must not carry a GF "
                f"sensory conductance. No source states one, and a direct "
                f"connection does not determine a conductance."
            )
        if self.attributable_gf_synaptic_conductance:
            raise ValueError(
                f"GF visual input '{self.input_id}' must not be treated as a "
                f"GF synaptic conductance. The EM reconstruction establishes a "
                f"connection, not a current."
            )
        if (
            self.modifies_gf_morphology
            or self.modifies_gf_passive_parameters
            or self.modifies_gf_active_profile
        ):
            raise ValueError(
                f"GF visual input '{self.input_id}' must not modify the GF "
                f"morphology, the GF passive parameters or the GF active "
                f"profile. 3.0D-7Y specifies where the input comes from, not "
                f"how the GF membrane behaves."
            )
        if self.target_neuron != NEURON_GF:
            raise ValueError(
                f"GF visual input '{self.input_id}' must target '{NEURON_GF}'."
            )
        for required in (NEURON_LC4, NEURON_LPLC2):
            if required not in self.input_neurons:
                raise ValueError(
                    f"GF visual input '{self.input_id}' must name '{required}' "
                    f"as an input neuron."
                )
        if not self.source_references:
            raise ValueError(
                f"GF visual input '{self.input_id}' must carry at least one "
                f"source reference."
            )

    @property
    def is_direct(self) -> bool:
        return True

    @property
    def has_conductance(self) -> bool:
        """Always False: the GF sensory conductance does not exist here."""
        return False

    def limitations(self) -> str:
        return (
            f"DIRECT VISUAL INPUT TO THE GF, NOT A CONDUCTANCE. {self.notes} "
            f"{_NO_GF_SENSORY_CONDUCTANCE} {_NO_SENSORY_MECHANISM} "
            f"{_NO_STIMULUS_TIMESTEP} {_NOT_LIVE}"
        )


# --- G: experimental validation targets --------------------------------------


@dataclass(frozen=True)
class LoomingValidationTarget:
    """A qualitative or phenomenological target a future model would satisfy.

    None of these targets is a number. The GF stimulus-response curve, the
    latencies, the refractory periods and the following ratios belong to
    3.0D-7W; the NMJ and muscle-output quantities belong to 3.0D-7X. Ache et
    al. 2019's prediction of peak response time is recorded as a capability of
    their model, not as a latency value, because no absolute value is stated in
    any retrieved source. ``carries_a_value`` is always False.
    """

    target_id: str
    statement: str
    target_kind: str
    observable: str
    requires_component: str
    evidence_status: SynapticEvidenceStatus
    provenance_category: ParameterProvenance
    source_references: Tuple[str, ...]
    notes: str
    is_numeric_latency_target: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Looming validation target '{self.target_id}' cannot be "
                f"live-solver eligible. It is a target, not a model."
            )
        if self.is_numeric_latency_target:
            raise ValueError(
                f"Looming validation target '{self.target_id}' must not be a "
                f"numeric latency target. No retrieved source states an "
                f"absolute GF looming-response latency, and none may be "
                f"invented."
            )
        if self.target_kind not in (
            "qualitative_observation", "phenomenological_capability"
        ):
            raise ValueError(
                f"Looming validation target '{self.target_id}' must be "
                f"qualitative or phenomenological, got "
                f"'{self.target_kind}'."
            )
        if not self.statement:
            raise ValueError(
                f"Looming validation target '{self.target_id}' must state what "
                f"it asserts."
            )
        if not self.source_references:
            raise ValueError(
                f"Looming validation target '{self.target_id}' must carry at "
                f"least one source reference."
            )

    @property
    def carries_a_value(self) -> bool:
        """Always False: every target here is a statement, not a number."""
        return False

    def limitations(self) -> str:
        return (
            f"{self.notes} {_NO_MODEL_COEFFICIENTS} "
            f"{_NO_MOTOR_OUTPUT_DUPLICATION} {_NO_STIMULUS_TIMESTEP} {_NOT_LIVE}"
        )


# --- H: unsupported mechanistic quantities ------------------------------------


@dataclass(frozen=True)
class UnavailableSensoryQuantity:
    """A sensory quantity a mechanistic visual pathway would need, and lacks.

    ``value`` is structurally None and cannot be set. Where an equivalent
    exclusion already exists in 3.0D-7V, 3.0D-7W or 3.0D-7X, it is LINKED
    rather than duplicated.
    """

    quantity_id: str
    quantity_kind: str
    applies_to: str
    why_required: str
    why_unavailable: str
    linked_7v_excluded_name: Optional[str]
    linked_7w_requirement_id: Optional[str]
    linked_7x_quantity_id: Optional[str]
    must_not_be_inherited_from: Optional[str]
    value: None = None
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Unavailable sensory quantity '{self.quantity_id}' cannot be "
                f"live-solver eligible: it has no value to supply."
            )
        if self.value is not None:
            raise ValueError(
                f"Unavailable sensory quantity '{self.quantity_id}' must "
                f"remain unavailable. No retrieved source states it, so no "
                f"value may be populated."
            )
        if not self.why_required or not self.why_unavailable:
            raise ValueError(
                f"Unavailable sensory quantity '{self.quantity_id}' must "
                f"state both why a mechanistic pathway would need it and why "
                f"it is unavailable."
            )

    @property
    def value_is_populated(self) -> bool:
        """Always False."""
        return False

    def limitations(self) -> str:
        parts = [
            f"REQUIRED BY A MECHANISTIC VISUAL PATHWAY, CURRENTLY "
            f"UNAVAILABLE. {self.why_required} {self.why_unavailable} This "
            f"quantity stays empty. It is NOT filled with a generic "
            f"Drosophila value, with a value from another neuron class, with a "
            f"value from the locust LGMD loom model, or with a value "
            f"back-calculated from a response curve."
        ]
        if self.must_not_be_inherited_from:
            parts.append(
                f"It is specifically NOT inherited from "
                f"{self.must_not_be_inherited_from}."
            )
        parts.append(_NOT_LIVE)
        return " ".join(parts)


# --- J: 3.0D-8H quantitative update -----------------------------------------


@dataclass(frozen=True)
class PhenomenologicalCoefficientUpdate:
    """A record that a LATER checkpoint supplied the published coefficients.

    3.0D-7Y could not hold these numbers: the record types above deliberately
    refuse to carry a coefficient, and :class:`PhenomenologicalModelTerm`
    refuses to claim the equation is available. 3.0D-8H researched and
    verified the Ache et al. 2019 GF model coefficients, delays and weights, and
    implemented them quantitatively in ``biological_brain.dynamics.
    gf_sensory_drive``.

    This record exists so that the two layers do not appear to contradict each
    other: 7Y still holds NO coefficient, and 8H supplies them elsewhere. It is
    a POINTER, not a number. It carries no value, and it changes none of 7Y's
    thirteen unavailable sensory quantities, all of which remain structural
    ``None`` because 8H supplies a phenomenological FUNCTION and not a synaptic
    mechanism.

    It is also deliberately NOT a live-solver marker. A published
    stimulus-response function is not a mechanism, drives no compartment, and
    makes the GF sensory input no more mechanistic than it was in 7Y.
    """

    update_id: str
    supplies: Tuple[str, ...]
    implemented_in: str
    implemented_as: str
    source_references: Tuple[str, ...]
    notes: str
    resolves_an_unavailable_quantity_id: None = None
    creates_a_synaptic_conductance: bool = False
    is_live_solver_eligible: bool = False
    modifies_gf_membrane_equations: bool = False

    def __post_init__(self) -> None:
        if self.is_live_solver_eligible:
            raise ValueError(
                f"Phenomenological coefficient update '{self.update_id}' "
                f"cannot be live-solver eligible. Supplying published "
                f"coefficients for a stimulus-response function does not make "
                f"that function a mechanism."
            )
        if self.creates_a_synaptic_conductance:
            raise ValueError(
                f"Phenomenological coefficient update '{self.update_id}' must "
                f"not create a synaptic conductance. A coefficient of a "
                f"phenomenological function is not a synaptic conductance."
            )
        if self.modifies_gf_membrane_equations:
            raise ValueError(
                f"Phenomenological coefficient update '{self.update_id}' must "
                f"not modify the GF membrane equations."
            )
        if self.resolves_an_unavailable_quantity_id is not None:
            raise ValueError(
                f"Phenomenological coefficient update '{self.update_id}' must "
                f"not resolve an unavailable sensory quantity. 3.0D-8H supplies "
                f"phenomenological coefficients, delays and weights. It does "
                f"NOT supply an LC4 or LPLC2 synaptic conductance, a membrane "
                f"conductance, a channel density, Hodgkin-Huxley kinetics, a "
                f"release probability, a reversal potential, a receptor "
                f"identity, receptor kinetics or a Q10, and every one of those "
                f"stays unavailable."
            )
        if not self.supplies:
            raise ValueError(
                f"Phenomenological coefficient update '{self.update_id}' must "
                f"state what it supplies."
            )
        if not self.implemented_in or not self.implemented_as:
            raise ValueError(
                f"Phenomenological coefficient update '{self.update_id}' must "
                f"state where the implementation lives and what kind of object "
                f"it is."
            )
        if not self.source_references:
            raise ValueError(
                f"Phenomenological coefficient update '{self.update_id}' must "
                f"carry at least one source reference."
            )

    @property
    def supplies_a_coefficient(self) -> bool:
        """True: 8H supplies published coefficients, in the 8H module."""
        return True

    @property
    def seven_y_still_holds_a_coefficient(self) -> bool:
        """Always False: 7Y itself remains coefficient-free."""
        return False

    def limitations(self) -> str:
        return (
            f"POINTER TO A LATER CHECKPOINT, NOT A VALUE. 7Y holds no "
            f"coefficient and does not change. {self.notes} "
            f"{_NO_PHENOMENOLOGICAL_CONVERSION} {_NO_SENSORY_MECHANISM} "
            f"{_NOT_LIVE}"
        )


# --- stimulus-space rates (NOT timesteps) ------------------------------------


@dataclass(frozen=True)
class StimulusRateBoundary:
    """A published stimulus-presentation rate, recorded so it is not misused.

    The 180 Hz display frame rate of Klapoetke et al. 2017 and the r/v stimulus
    ratio discussed by Jang et al. 2023 describe how an object was SHOWN. They
    are not neural integration times. ``is_neural_timestep`` is a hard False
    that raises if set, and the project timestep policy is untouched.
    """

    rate_id: str
    rate_kind: str
    reported_description: str
    belongs_to: str
    source_references: Tuple[str, ...]
    notes: str
    is_neural_timestep: bool = False
    changes_timestep_policy: bool = False
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Stimulus rate '{self.rate_id}' cannot be live-solver "
                f"eligible."
            )
        if self.is_neural_timestep:
            raise ValueError(
                f"Stimulus rate '{self.rate_id}' must NOT be a neural "
                f"timestep. A display frame rate or a stimulus ratio is a "
                f"property of the STIMULUS, not of any neuron."
            )
        if self.changes_timestep_policy:
            raise ValueError(
                f"Stimulus rate '{self.rate_id}' must not change the "
                f"numerical timestep policy. 3.0D-7Y introduces no timestep."
            )
        if not self.source_references:
            raise ValueError(
                f"Stimulus rate '{self.rate_id}' must carry at least one "
                f"source reference."
            )

    def limitations(self) -> str:
        return f"{self.notes} {_NO_STIMULUS_TIMESTEP} {_NOT_LIVE}"


# --- I: the pathway stage diagram --------------------------------------------


@dataclass(frozen=True)
class PathwayStageDiagram:
    """The conceptual pathway, as stage NAMES. Not a simulator.

    The stages are strings. There is no weight, no delay, no per-stage
    contribution and no signal type between them, and the motor-output end of
    the diagram is OWNED by 3.0D-7W and 3.0D-7X and is named here only.
    """

    diagram_id: str
    description: str
    stages: Tuple[str, ...]
    motor_output_owned_by: Tuple[str, ...]
    source_references: Tuple[str, ...]
    notes: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Pathway diagram '{self.diagram_id}' cannot be live-solver "
                f"eligible. It names stages; it connects nothing."
            )
        required = (
            _STAGE_VISUAL_STIMULUS,
            _STAGE_FEATURE_EXTRACTION,
            _STAGE_GF,
            _STAGE_DESCENDING_MOTOR,
            _STAGE_NMJ,
            _STAGE_MUSCLE_OUTPUT,
        )
        for stage in required:
            if stage not in self.stages:
                raise ValueError(
                    f"Pathway diagram '{self.diagram_id}' must name the stage "
                    f"'{stage}'."
                )
        for stage in self.stages:
            if not isinstance(stage, str):
                raise ValueError(
                    f"Pathway diagram '{self.diagram_id}' stages must be stage "
                    f"NAMES, not simulated components."
                )
        if "3.0D-7W" not in self.motor_output_owned_by:
            raise ValueError(
                f"Pathway diagram '{self.diagram_id}' must record that the "
                f"motor-output validation targets are owned by 3.0D-7W."
            )
        if "3.0D-7X" not in self.motor_output_owned_by:
            raise ValueError(
                f"Pathway diagram '{self.diagram_id}' must record that the "
                f"NMJ quantities are owned by 3.0D-7X."
            )

    @property
    def stage_count(self) -> int:
        return len(self.stages)

    @property
    def has_weights(self) -> bool:
        """Always False: the diagram names stages and carries no numbers."""
        return False

    def limitations(self) -> str:
        return f"{self.notes} {_NO_MOTOR_OUTPUT_DUPLICATION} {_NOT_LIVE}"


# --- the layer ---------------------------------------------------------------


@dataclass(frozen=True)
class LoomingAbstraction:
    """The visual input end, specified. NOT modelled.

    Assigns nothing, populates nothing, connects nothing. No compartment, no
    ``CableParameters``, no ``CompartmentElectrical`` and no solver input is
    populated from this layer, and no solver module imports it.
    """

    name: str
    source: str
    model_id: str
    model_citation: str
    projection_neurons: Tuple[VisualProjectionNeuronSpec, ...]
    stimulus_features: Tuple[StimulusFeatureSpec, ...]
    phenomenological_terms: Tuple[PhenomenologicalModelTerm, ...]
    opponency_components: Tuple[RadialMotionOpponencyComponent, ...]
    gf_visual_inputs: Tuple[GFVisualInputRecord, ...]
    validation_targets: Tuple[LoomingValidationTarget, ...]
    unavailable_sensory_quantities: Tuple[UnavailableSensoryQuantity, ...]
    stimulus_rates: Tuple[StimulusRateBoundary, ...]
    pathway_diagrams: Tuple[PathwayStageDiagram, ...]
    scope_note: str
    live_solver_eligible: bool = False
    quantitative_updates: Tuple[PhenomenologicalCoefficientUpdate, ...] = ()

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                "The looming abstraction cannot be live-solver eligible. It is "
                "a specification of the visual input end, not a model of it."
            )
        if not self.projection_neurons:
            raise ValueError(
                "The looming abstraction must specify at least one visual "
                "projection neuron."
            )

    # -- lookup -------------------------------------------------------------

    def neuron(self, neuron_class: str) -> VisualProjectionNeuronSpec:
        for record in self.projection_neurons:
            if record.neuron_class == neuron_class:
                return record
        raise KeyError(
            f"Visual projection neuron '{neuron_class}' not in abstraction"
        )

    def neuron_classes(self) -> Tuple[str, ...]:
        return tuple(record.neuron_class for record in self.projection_neurons)

    def feature(self, feature_id: str) -> StimulusFeatureSpec:
        for record in self.stimulus_features:
            if record.feature_id == feature_id:
                return record
        raise KeyError(f"Stimulus feature '{feature_id}' not in abstraction")

    def feature_ids(self) -> Tuple[str, ...]:
        return tuple(record.feature_id for record in self.stimulus_features)

    def neuron_for_feature(self, feature_id: str) -> VisualProjectionNeuronSpec:
        for record in self.projection_neurons:
            if record.feature_extracted == feature_id:
                return record
        raise KeyError(
            f"No visual projection neuron recorded for feature '{feature_id}'"
        )

    def term(self, term_id: str) -> PhenomenologicalModelTerm:
        for record in self.phenomenological_terms:
            if record.term_id == term_id:
                return record
        raise KeyError(f"Phenomenological term '{term_id}' not in abstraction")

    def term_ids(self) -> Tuple[str, ...]:
        return tuple(record.term_id for record in self.phenomenological_terms)

    def opponency(self, component_id: str) -> RadialMotionOpponencyComponent:
        for record in self.opponency_components:
            if record.component_id == component_id:
                return record
        raise KeyError(
            f"Opponency component '{component_id}' not in abstraction"
        )

    def gf_input(self, input_id: str) -> GFVisualInputRecord:
        for record in self.gf_visual_inputs:
            if record.input_id == input_id:
                return record
        raise KeyError(f"GF visual input '{input_id}' not in abstraction")

    def target(self, target_id: str) -> LoomingValidationTarget:
        for record in self.validation_targets:
            if record.target_id == target_id:
                return record
        raise KeyError(f"Looming validation target '{target_id}' not in abstraction")

    def target_ids(self) -> Tuple[str, ...]:
        return tuple(record.target_id for record in self.validation_targets)

    def unavailable(self, quantity_id: str) -> UnavailableSensoryQuantity:
        for record in self.unavailable_sensory_quantities:
            if record.quantity_id == quantity_id:
                return record
        raise KeyError(
            f"Unavailable sensory quantity '{quantity_id}' not in abstraction"
        )

    def unavailable_ids(self) -> Tuple[str, ...]:
        return tuple(
            record.quantity_id for record in self.unavailable_sensory_quantities
        )

    def stimulus_rate(self, rate_id: str) -> StimulusRateBoundary:
        for record in self.stimulus_rates:
            if record.rate_id == rate_id:
                return record
        raise KeyError(f"Stimulus rate '{rate_id}' not in abstraction")

    def quantitative_update(
        self, update_id: str
    ) -> PhenomenologicalCoefficientUpdate:
        """Return the record for a later checkpoint's published coefficients.

        3.0D-8H adds exactly one of these. It is a pointer: it says the
        published Ache et al. 2019 coefficients exist and where they live, and
        it resolves NO unavailable quantity in this layer.
        """
        for record in self.quantitative_updates:
            if record.update_id == update_id:
                return record
        raise KeyError(
            f"Quantitative update '{update_id}' not in abstraction"
        )

    def quantitative_update_ids(self) -> Tuple[str, ...]:
        return tuple(record.update_id for record in self.quantitative_updates)

    def any_unavailable_quantity_resolved(self) -> bool:
        """Always False: 3.0D-8H resolved none of them.

        The published phenomenological coefficients are a different KIND of
        quantity from a synaptic conductance, a receptor kinetic or a release
        probability, and 8H supplies only the former.
        """
        return any(
            record.resolves_an_unavailable_quantity_id is not None
            for record in self.quantitative_updates
        )

    def seven_y_carries_a_model_coefficient(self) -> bool:
        """Always False: 7Y holds no coefficient even after 3.0D-8H.

        The coefficients live in ``biological_brain.dynamics.gf_sensory_drive``
        and are reached through :meth:`quantitative_update`, not stored here.
        """
        return False

    def diagram(self, diagram_id: str) -> PathwayStageDiagram:
        for record in self.pathway_diagrams:
            if record.diagram_id == diagram_id:
                return record
        raise KeyError(f"Pathway diagram '{diagram_id}' not in abstraction")

    # -- boundary -----------------------------------------------------------

    def any_live_solver_eligible(self) -> bool:
        """Always False in 3.0D-7Y."""
        return any(
            record.live_solver_eligible
            for record in (
                *self.projection_neurons,
                *self.stimulus_features,
                *self.phenomenological_terms,
                *self.opponency_components,
                *self.gf_visual_inputs,
                *self.validation_targets,
                *self.unavailable_sensory_quantities,
                *self.stimulus_rates,
                *self.pathway_diagrams,
            )
        )

    def any_mechanistically_ready(self) -> bool:
        """Always False: no visual neuron has a stated mechanism."""
        return any(
            record.mechanistic_live_solver_ready
            for record in self.projection_neurons
        )

    def any_membrane_conductance(self) -> bool:
        """Always False: no visual-neuron or GF sensory conductance exists."""
        return any(
            record.has_quantitative_parameter
            for record in self.projection_neurons
        ) or any(
            record.has_conductance for record in self.opponency_components
        ) or any(record.has_conductance for record in self.gf_visual_inputs)

    def any_hodgkin_huxley_kinetics(self) -> bool:
        """Always False: no HH kinetics exist for LC4 or LPLC2."""
        return any(
            record.mechanistic_live_solver_ready
            for record in self.projection_neurons
        )

    def any_synaptic_conductance(self) -> bool:
        """Always False: no LC4->GF or LPLC2->GF conductance exists."""
        return any(
            record.attributable_gf_synaptic_conductance
            for record in self.gf_visual_inputs
        )

    def any_membrane_variable(self) -> bool:
        """Always False: a stimulus feature is not a membrane variable."""
        return any(
            record.is_membrane_variable for record in self.stimulus_features
        )

    def any_membrane_current(self) -> bool:
        """Always False: a phenomenological term is not a current."""
        return any(
            record.is_membrane_current for record in self.phenomenological_terms
        )

    def any_model_coefficient(self) -> bool:
        """Always False: no coefficient of the published model is recorded."""
        return any(
            record.carries_a_coefficient
            for record in self.phenomenological_terms
        ) or any(record.equation_available for record in self.phenomenological_terms)

    def any_receptor_kinetics(self) -> bool:
        """Always False: no receptor kinetics exist for the LC4/LPLC2->GF
        input."""
        return any(
            record.value_is_populated
            for record in self.unavailable_sensory_quantities
            if "receptor" in record.quantity_id
        )

    def any_populated_sensory_quantity(self) -> bool:
        """Always False: every unavailable quantity stays empty."""
        return any(
            record.value_is_populated
            for record in self.unavailable_sensory_quantities
        )

    def any_visual_timestep(self) -> bool:
        """Always False: a stimulus rate is not a neural timestep."""
        return any(
            record.is_neural_timestep for record in self.stimulus_rates
        )

    def any_timestep_policy_change(self) -> bool:
        """Always False in 3.0D-7Y."""
        return any(
            record.changes_timestep_policy for record in self.stimulus_rates
        )

    def any_numeric_latency_target(self) -> bool:
        """Always False: no retrieved source states an absolute GF looming
        latency."""
        return any(
            record.is_numeric_latency_target for record in self.validation_targets
        )

    def any_target_value(self) -> bool:
        """Always False: every validation target is a statement, not a number."""
        return any(record.carries_a_value for record in self.validation_targets)

    def any_motor_output_quantity(self) -> bool:
        """Always False: 7Y names the motor-output stages and nothing else."""
        return any(
            record.has_weights for record in self.pathway_diagrams
        )

    def neurons_targeting(self, target_neuron: str) -> Tuple[str, ...]:
        return tuple(
            record.neuron_class
            for record in self.projection_neurons
            if record.target_neuron == target_neuron
        )

    def verifies_against_7w_and_7x(self) -> None:
        """Assert this layer names the earlier layers correctly.

        Every linked 7V exclusion, 7W requirement and 7X quantity must actually
        exist, and the motor-output stages must be recorded as owned by 7W and
        7X. This changes nothing; it fails loudly if the layers drift apart.
        """
        from .synaptic_mechanism_registry import (
            get_synaptic_mechanism_registry,
        )
        from .synaptic_abstraction import get_synaptic_abstraction
        from .motor_output_abstraction import get_motor_output_abstraction

        excluded = set(get_synaptic_mechanism_registry().excluded_names())
        requirements = set(
            get_synaptic_abstraction().requirement_ids()
        )
        nmj_quantities = set(
            get_motor_output_abstraction().unavailable_ids()
        )
        for record in self.unavailable_sensory_quantities:
            if record.linked_7v_excluded_name is not None:
                if record.linked_7v_excluded_name not in excluded:
                    raise ValueError(
                        f"Quantity '{record.quantity_id}' links to 7V "
                        f"exclusion '{record.linked_7v_excluded_name}', which "
                        f"does not exist."
                    )
            if record.linked_7w_requirement_id is not None:
                if record.linked_7w_requirement_id not in requirements:
                    raise ValueError(
                        f"Quantity '{record.quantity_id}' links to 7W "
                        f"requirement '{record.linked_7w_requirement_id}', "
                        f"which does not exist."
                    )
            if record.linked_7x_quantity_id is not None:
                if record.linked_7x_quantity_id not in nmj_quantities:
                    raise ValueError(
                        f"Quantity '{record.quantity_id}' links to 7X quantity "
                        f"'{record.linked_7x_quantity_id}', which does not "
                        f"exist."
                    )
        for record in self.pathway_diagrams:
            if "3.0D-7W" not in record.motor_output_owned_by:
                raise ValueError(
                    f"Diagram '{record.diagram_id}' does not record 3.0D-7W as "
                    f"the owner of the motor-output targets."
                )


# --- construction ------------------------------------------------------------


def _projection_neurons() -> Tuple[VisualProjectionNeuronSpec, ...]:
    return (
        VisualProjectionNeuronSpec(
            neuron_class=NEURON_LC4,
            cell_class="lobula columnar, type 4 visual projection neuron",
            feature_extracted=FEATURE_ANGULAR_VELOCITY,
            target_neuron=NEURON_GF,
            connection_type=CONNECTION_DIRECT_VISUAL_INPUT,
            anatomical_location=(
                "Optic lobe. LC4 is a visual projection neuron of the central "
                "complex, not one of the central-brain descending neurons whose "
                "morphology this project models at 3.0D-7A."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            experimentally_supported=True,
            mechanistic_live_solver_ready=False,
            source_references=(
                SOURCE_ACHE_2019, SOURCE_KOHN_2018, SOURCE_JANG_2023,
            ),
            notes=(
                "LC4 CARRIES THE ANGULAR-VELOCITY COMPONENT. Ache et al. 2019 "
                "state that 'We attributed velocity encoding to input from "
                "lobula columnar type 4 (LC4) visual projection neurons' and "
                "show by EM reconstruction that LC4 synapses directly onto the "
                "GF. Kohn et al. 2018 state that 'Information about the angular "
                "velocity of looming objects is provided by the type 4 lobula "
                "columnar (LC4) cell, a second presynaptic partner of the GF "
                "interneuron', that 'LC4 is tuned specifically to rapid "
                "expansion of a large object profile, and that it 'enhances GF "
                "responses as looms become more abrupt'. Jang et al. 2023 state "
                "that 'LC4 angular velocity contribution to the GF response "
                "increases as r/v decreases'. LPLC2 silencing leaves the "
                "velocity component intact, so the two features are separable. "
                "NO LC4 membrane conductance, channel density or Hodgkin-Huxley "
                "kinetic is stated by any retrieved source."
            ),
        ),
        VisualProjectionNeuronSpec(
            neuron_class=NEURON_LPLC2,
            cell_class="lobula plate/lobula columnar, type 2 visual projection "
                       "neuron",
            feature_extracted=FEATURE_ANGULAR_SIZE,
            target_neuron=NEURON_GF,
            connection_type=CONNECTION_DIRECT_VISUAL_INPUT,
            anatomical_location=(
                "Optic lobe. Klapoetke et al. 2017 report a population of ~80 "
                "LPLC2 visual projection neurons whose dendrites cover the "
                "lobula plate and whose axons terminate near the lateral "
                "dendrite of the giant fiber. LPLC2 is a visual projection "
                "neuron, not one of the central-brain descending neurons whose "
                "morphology this project models at 3.0D-7A."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            experimentally_supported=True,
            mechanistic_live_solver_ready=False,
            source_references=(
                SOURCE_ACHE_2019, SOURCE_KLAPOETKE_2017, SOURCE_KOHN_2018,
                SOURCE_JANG_2023,
            ),
            notes=(
                "LPLC2 CARRIES THE ENTIRE ANGULAR-SIZE COMPONENT. Ache et al. "
                "2019 state that 'lobula plate/lobula columnar, type 2 (LPLC2) "
                "visual projection neurons anatomically specialized to detect "
                "looming provide the entire GF size component', that 'LPLC2 "
                "silencing eliminates the size component of the GF looming "
                "response in patch-clamp recordings, leaving only the velocity "
                "component', and that LPLC2 and LC4 'synapse directly onto the "
                "GF via reconstruction in a fly brain electron microscopy (EM) "
                "volume'. Kohn et al. 2018 state that 'The output of LPLC2 cells "
                "provides the GF interneuron with information about the angular "
                "size of a looming object'. Jang et al. 2023 record that LPLC2's "
                "angular size contribution 'remains constant' as r/v varies. "
                "Klapoetke et al. 2017 establish the outward dendritic geometry "
                "and the radial motion opponency recorded separately in this "
                "layer. NO LPLC2 membrane conductance, channel density or "
                "Hodgkin-Huxley kinetic is stated by any retrieved source; all "
                "LPLC2 data in Klapoetke et al. 2017 are two-photon GCaMP6 "
                "calcium imaging."
            ),
        ),
    )


def _stimulus_features() -> Tuple[StimulusFeatureSpec, ...]:
    return (
        StimulusFeatureSpec(
            feature_id=FEATURE_ANGULAR_VELOCITY,
            feature_name="angular velocity (eta)",
            feature_kind="external_stimulus_feature",
            described_as=(
                "The rate of change of an approaching object's subtended "
                "angular size, as a stimulus coordinate. It is dimensionless and "
                "external to the animal."
            ),
            carried_by=NEURON_LC4,
            used_by=NEURON_GF,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019, SOURCE_KOHN_2018, SOURCE_JANG_2023,
            ),
            notes=(
                "ANGULAR VELOCITY IS A STIMULUS FEATURE, NOT A MEMBRANE "
                "VARIABLE. It is carried by LC4 and delivered to the GF. It is "
                "not a voltage, not a current, not a conductance and not a "
                "compartment state. Ache et al. 2019 refer to it as one of the "
                "two visual features whose summation determines GF spike "
                "timing; no velocity range or amplitude is stated in any "
                "retrieved source, and none is recorded here."
            ),
        ),
        StimulusFeatureSpec(
            feature_id=FEATURE_ANGULAR_SIZE,
            feature_name="angular size (rho)",
            feature_kind="external_stimulus_feature",
            described_as=(
                "The angular extent an approaching object subtends on the "
                "retina, as a stimulus coordinate. It is dimensionless and "
                "external to the animal."
            ),
            carried_by=NEURON_LPLC2,
            used_by=NEURON_GF,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019, SOURCE_KOHN_2018, SOURCE_JANG_2023,
            ),
            notes=(
                "ANGULAR SIZE IS A STIMULUS FEATURE, NOT A MEMBRANE VARIABLE. "
                "It is carried by LPLC2 and delivered to the GF. It is not a "
                "voltage, not a current, not a conductance and not a "
                "compartment state. Klapoetke et al. 2017 bound an individual "
                "LPLC2 receptive field at 60 degrees and used expansions from 5 "
                "to 20 and 5 to 60 degrees, but those are STIMULUS GEOMETRIES "
                "used in that experiment, not an encoding range, and they are "
                "not recorded here as a parameter."
            ),
        ),
    )


def _phenomenological_terms() -> Tuple[PhenomenologicalModelTerm, ...]:
    return (
        PhenomenologicalModelTerm(
            term_id="lc4_angular_velocity_term",
            provided_by=NEURON_LC4,
            input_feature=FEATURE_ANGULAR_VELOCITY,
            functional_form=FORM_LINEAR,
            published_statement=(
                "A linear function of angular velocity, provided by LC4."
            ),
            combines_into="gf_looming_response",
            equation_available=False,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_ACHE_2019, SOURCE_KOHN_2018),
            notes=(
                "Ache et al. 2019 state that 'A model summing a linear function "
                "of angular velocity (provided by LC4) and a Gaussian function "
                "of angular size (provided by LPLC2) replicates GF looming "
                "response dynamics and predicts the peak response time'. "
                "Kohn et al. 2018 independently describe the GF as working 'By "
                "linearly integrating input from LC4 and LPLC2 pathways'. The "
                "SLOPE OF THIS LINEAR TERM IS NOT AVAILABLE. The full text is "
                "behind a subscription, so no coefficient is recorded and none "
                "is guessed."
            ),
        ),
        PhenomenologicalModelTerm(
            term_id="lplc2_angular_size_term",
            provided_by=NEURON_LPLC2,
            input_feature=FEATURE_ANGULAR_SIZE,
            functional_form=FORM_GAUSSIAN,
            published_statement=(
                "A Gaussian function of angular size, provided by LPLC2."
            ),
            combines_into="gf_looming_response",
            equation_available=False,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_ACHE_2019, SOURCE_KOHN_2018),
            notes=(
                "Ache et al. 2019 state that the same model uses 'a Gaussian "
                "function of angular size (provided by LPLC2)'. The GAUSSIAN "
                "AMPLITUDE, WIDTH AND OFFSET ARE NOT AVAILABLE. The full text is "
                "behind a subscription, so no coefficient is recorded, none is "
                "fitted to a response curve, and none is borrowed from the "
                "locust LGMD loom-detection model of Gabbiani et al. 1999."
            ),
        ),
        PhenomenologicalModelTerm(
            term_id="gf_looming_response",
            provided_by=f"{NEURON_LC4} and {NEURON_LPLC2}",
            input_feature=_BOTH_FEATURES,
            functional_form=FORM_SUM,
            published_statement=(
                "GF response = combination of the LC4 angular-velocity "
                "contribution and the LPLC2 angular-size contribution."
            ),
            combines_into="giant fiber escape pathway",
            equation_available=False,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_ACHE_2019, SOURCE_KOHN_2018),
            notes=(
                "THE COMBINATION IS A SUM OF TWO PUBLISHED FUNCTIONS. Ache et "
                "al. 2019 state that a model 'summing a linear function of "
                "angular velocity... and a Gaussian function of angular size... "
                "replicates GF looming response dynamics and predicts the peak "
                "response time', and describe the circuit as one in which "
                "'information from looming feature-detecting neurons is combined "
                "by a common post-synaptic target to determine behavioral "
                "output'. The RELATIVE WEIGHTING OF THE TWO TERMS IS NOT "
                "AVAILABLE and is not recorded. The model is a phenomenological "
                "fit to a stimulus-response relationship; it is not a "
                "mechanism and drives no compartment."
            ),
        ),
    )


def _opponency_components() -> Tuple[RadialMotionOpponencyComponent, ...]:
    return (
        RadialMotionOpponencyComponent(
            component_id="lplc2_outward_motion_excitatory",
            motion_direction="outward radial motion from the receptive field "
                              "center",
            functional_effect="excitatory",
            described_as=(
                "Motion radiating outward from the center of the LPLC2 "
                "receptive field drives an excitatory component."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_KLAPOETKE_2017, SOURCE_KOHN_2018),
            notes=(
                "QUALITATIVE FUNCTIONAL EVIDENCE. Klapoetke et al. 2017 state "
                "that 'individual LPLC2 neurons respond strongly to outward "
                "motion emanating from the center of the neuron's receptive "
                "field' and that excitatory inputs from retinotopically "
                "arranged, directionally selective T4 and T5 neurons 'supply "
                "four outward-motion selective dendritic fields'. NO excitatory "
                "conductance, NO amplitude and NO reversal potential is stated "
                "for this component."
            ),
        ),
        RadialMotionOpponencyComponent(
            component_id="lplc2_inward_motion_inhibitory",
            motion_direction="inward radial motion toward the receptive field "
                              "center",
            functional_effect="inhibitory",
            described_as=(
                "Motion directed inward toward the receptive field center "
                "drives an inhibitory component that opposes the outward "
                "excitation."
            ),
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_KLAPOETKE_2017, SOURCE_KOHN_2018),
            notes=(
                "QUALITATIVE FUNCTIONAL EVIDENCE. Klapoetke et al. 2017 state "
                "that 'each dendritic arm also receives local inhibitory inputs "
                "directionally selective for inward motion opposing the "
                "excitation' and that the opponency 'generates a balance of "
                "excitation and inhibition that makes LPLC2 non-responsive to "
                "related patterns of motion such as contraction, wide-field "
                "translation, or luminance change'. Kohn et al. 2018 describe "
                "the same property as 'radial opponency'. NO inhibitory "
                "conductance, NO reversal potential, NO synaptic delay and NO "
                "receptive-field membrane model is stated for this component."
            ),
        ),
    )


def _gf_visual_inputs() -> Tuple[GFVisualInputRecord, ...]:
    return (
        GFVisualInputRecord(
            input_id="lc4_and_lplc2_to_gf",
            target_neuron=NEURON_GF,
            input_neurons=(NEURON_LC4, NEURON_LPLC2),
            connection_basis=(
                "Electron-microscopy reconstruction in a fly brain volume, plus "
                "optogenetic activation of LPLC2 producing a large and rapid "
                "depolarization of the GF."
            ),
            reported_response=(
                "A large and rapid depolarization of the giant fiber upon "
                "LPLC2 optogenetic activation; no amplitude, unitary synapse or "
                "conductance is reported."
            ),
            attributable_gf_synaptic_conductance=False,
            modifies_gf_morphology=False,
            modifies_gf_passive_parameters=False,
            modifies_gf_active_profile=False,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(
                SOURCE_ACHE_2019, SOURCE_KLAPOETKE_2017, SOURCE_JANG_2023,
            ),
            notes=(
                "LC4 AND LPLC2 PROVIDE DIRECT INPUT TO THE GF. Ache et al. "
                "2019 show that 'LPLC2 and LC4 synapse directly onto the GF via "
                "reconstruction in a fly brain electron microscopy (EM) "
                "volume'. Klapoetke et al. 2017 report that LPLC2 axons "
                "'terminate near the lateral dendrite of the giant fiber' and "
                "that LPLC2 activation gave 'a large and rapid depolarization "
                "of the giant fiber... consistent with LPLC2s providing direct "
                "excitatory input to the giant fiber'. Jang et al. 2023 state "
                "that 'the VPNs LC4 and LPLC2 that provide ipsilateral visual "
                "input to the GF have small, ipsilaterally restricted "
                "receptive fields'. THE CONNECTION IS EXPERIMENTALLY SUPPORTED "
                "AND THE CONDUCTANCE DOES NOT EXIST HERE."
            ),
        ),
    )


def _validation_targets() -> Tuple[LoomingValidationTarget, ...]:
    return (
        LoomingValidationTarget(
            target_id="gf_response_has_velocity_and_size_components",
            statement=(
                "The GF looming response contains both a velocity component and "
                "a size component, supplied by LC4 and LPLC2 respectively."
            ),
            target_kind="qualitative_observation",
            observable="GF spike timing under a looming stimulus",
            requires_component=f"{NEURON_LC4} and {NEURON_LPLC2}",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_ACHE_2019, SOURCE_KOHN_2018),
            notes=(
                "EXPERIMENTALLY SUPPORTED. Ache et al. 2019 establish the "
                "decomposition: the GF response sums a velocity and a size "
                "component, and Jang et al. 2023 vary the relative "
                "contributions of the two inputs independently. This target is "
                "a statement about decomposition, not a number."
            ),
        ),
        LoomingValidationTarget(
            target_id="lplc2_silencing_removes_size_component",
            statement=(
                "Silencing LPLC2 removes the size component of the GF looming "
                "response while leaving the velocity component."
            ),
            target_kind="qualitative_observation",
            observable=(
                "GF patch-clamp response under looming stimulation, with and "
                "without LPLC2 silencing"
            ),
            requires_component=NEURON_LPLC2,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_ACHE_2019,),
            notes=(
                "EXPERIMENTALLY SUPPORTED. Ache et al. 2019 state that 'LPLC2 "
                "silencing eliminates the size component of the GF looming "
                "response in patch-clamp recordings, leaving only the velocity "
                "component'. This is the causal separation of the two features, "
                "and it is a statement about which component survives, not a "
                "number."
            ),
        ),
        LoomingValidationTarget(
            target_id="lc4_contributes_angular_velocity_information",
            statement=(
                "LC4 contributes angular-velocity information to the GF, and "
                "its contribution grows as the loom becomes more abrupt."
            ),
            target_kind="qualitative_observation",
            observable="GF response as the r/v ratio of the stimulus varies",
            requires_component=NEURON_LC4,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_ACHE_2019, SOURCE_KOHN_2018, SOURCE_JANG_2023),
            notes=(
                "EXPERIMENTALLY SUPPORTED. Jang et al. 2023 state that 'LC4's "
                "angular velocity contribution to the GF response increases as "
                "r/v decreases', and Kohn et al. 2018 state that LC4 'enhances "
                "GF responses as looms become more abrupt'. No velocity range "
                "and no response amplitude is stated, and none is recorded."
            ),
        ),
        LoomingValidationTarget(
            target_id="lplc2_contributes_angular_size_information",
            statement=(
                "LPLC2 contributes angular-size information to the GF, and its "
                "contribution is approximately invariant across the tested "
                "r/v ratios."
            ),
            target_kind="qualitative_observation",
            observable="GF response as the r/v ratio of the stimulus varies",
            requires_component=NEURON_LPLC2,
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_ACHE_2019, SOURCE_KOHN_2018, SOURCE_JANG_2023),
            notes=(
                "EXPERIMENTALLY SUPPORTED. Jang et al. 2023 state that LPLC2's "
                "angular size contribution 'remains constant' while the LC4 "
                "velocity contribution varies, and Kohn et al. 2018 state that "
                "LPLC2 output 'provides the GF interneuron with information "
                "about the angular size of a looming object'. No size range is "
                "stated and none is recorded."
            ),
        ),
        LoomingValidationTarget(
            target_id="combined_feature_model_reproduces_response_timing",
            statement=(
                "A model combining a linear angular-velocity function with a "
                "Gaussian angular-size function can reproduce GF looming "
                "response dynamics and predict the peak response time."
            ),
            target_kind="phenomenological_capability",
            observable="GF looming-response time course",
            requires_component=f"{NEURON_LC4} and {NEURON_LPLC2}",
            evidence_status=SynapticEvidenceStatus.EXPERIMENTALLY_CONSTRAINED,
            provenance_category=(
                ParameterProvenance.EXPERIMENTALLY_CONSTRAINED
            ),
            source_references=(SOURCE_ACHE_2019,),
            notes=(
                "A PHENOMENOLOGICAL CAPABILITY, NOT A LATENCY TARGET. Ache et "
                "al. 2019 state that their model 'replicates GF looming "
                "response dynamics and predicts the peak response time'. NO "
                "ABSOLUTE PEAK TIME IS STATED in any retrieved source: Jang et "
                "al. 2023 compare peak latencies across loom locations and "
                "report no significant difference, giving no numeric value in "
                "text. A numeric GF looming latency is therefore NOT created "
                "here, and the GF stimulus-response curve remains owned by "
                "3.0D-7W."
            ),
        ),
    )


def _unavailable_sensory_quantities() -> Tuple[UnavailableSensoryQuantity, ...]:
    no_source = (
        "No retrieved source states it. Klapoetke et al. 2017, Kohn et al. "
        "2018 and Jang et al. 2023 state no LC4 or LPLC2 biophysical property "
        "at all, and the only electrophysiology among them is whole-cell "
        "recording FROM THE GIANT FIBER soma. "
    )
    return (
        UnavailableSensoryQuantity(
            quantity_id="lc4_membrane_conductance",
            quantity_kind="intrinsic_membrane_conductance",
            applies_to=NEURON_LC4,
            why_required=(
                "A mechanistic visual pathway needs the LC4 membrane "
                "conductance to convert an input into a voltage change."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            must_not_be_inherited_from=(
                "any GF passive resistance recorded at 3.0D-7E, which belongs "
                "to the giant fiber soma and not to an optic-lobe visual "
                "projection neuron"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="lc4_channel_densities",
            quantity_kind="channel_density",
            applies_to=NEURON_LC4,
            why_required=(
                "A conductance-based LC4 model needs per-channel densities to "
                "convert a maximum conductance into a current."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            must_not_be_inherited_from=(
                "the GF channel densities recorded at 3.0D-7S, which belong to "
                "the giant fiber and not to LC4"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="lc4_hodgkin_huxley_kinetics",
            quantity_kind="hodgkin_huxley_kinetic",
            applies_to=NEURON_LC4,
            why_required=(
                "A conductance-based LC4 model needs rate constants and voltage "
                "dependencies for its channels."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            must_not_be_inherited_from=(
                "the GF Hodgkin-Huxley kinetics recorded at 3.0D-7S, which "
                "belong to the giant fiber and not to LC4"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="lplc2_membrane_conductance",
            quantity_kind="intrinsic_membrane_conductance",
            applies_to=NEURON_LPLC2,
            why_required=(
                "A mechanistic visual pathway needs the LPLC2 membrane "
                "conductance to convert its T4/T5 input into a voltage change."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            must_not_be_inherited_from=(
                "any GF passive resistance recorded at 3.0D-7E, and any "
                "assumption that an axon terminal is electrically equivalent "
                "to a soma"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="lplc2_channel_densities",
            quantity_kind="channel_density",
            applies_to=NEURON_LPLC2,
            why_required=(
                "A conductance-based LPLC2 model needs per-channel densities to "
                "convert a maximum conductance into a current."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            must_not_be_inherited_from=(
                "the GF channel densities recorded at 3.0D-7S, and any "
                "calcium-imaging response amplitude, which is a calcium signal "
                "and not a conductance"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="lplc2_hodgkin_huxley_kinetics",
            quantity_kind="hodgkin_huxley_kinetic",
            applies_to=NEURON_LPLC2,
            why_required=(
                "A conductance-based LPLC2 model needs rate constants and "
                "voltage dependencies for its channels."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            must_not_be_inherited_from=(
                "the GF Hodgkin-Huxley kinetics recorded at 3.0D-7S, and any "
                "intrinsic-spike or adaptation rate measured in a different "
                "visual projection neuron"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="lc4_to_gf_synaptic_conductance",
            quantity_kind="synaptic_conductance",
            applies_to=f"{NEURON_LC4} -> {NEURON_GF}",
            why_required=(
                "A mechanistic pathway needs the LC4->GF synaptic conductance "
                "to turn LC4 activity into a current in the GF."
            ),
            why_unavailable=(
                "Ache et al. 2019 establish the connection by EM "
                "reconstruction but state no conductance for it. "
                + no_source
            ),
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            must_not_be_inherited_from=(
                "the CENTRAL GF-TTMn chemical peak conductance recorded in "
                "3.0D-7V, which belongs to a different synapse on a different "
                "cell and carries a documented 80 uS versus 134 uS discrepancy"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="lplc2_to_gf_synaptic_conductance",
            quantity_kind="synaptic_conductance",
            applies_to=f"{NEURON_LPLC2} -> {NEURON_GF}",
            why_required=(
                "A mechanistic pathway needs the LPLC2->GF synaptic "
                "conductance to turn LPLC2 activity into a current in the GF."
            ),
            why_unavailable=(
                "Ache et al. 2019 establish the connection by EM "
                "reconstruction, and Klapoetke et al. 2017 report only that "
                "LPLC2 activation produced 'a large and rapid depolarization of "
                "the giant fiber', with no amplitude and no conductance. "
                + no_source
            ),
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id=None,
            must_not_be_inherited_from=(
                "the CENTRAL GF-TTMn chemical peak conductance recorded in "
                "3.0D-7V, and the GF depolarization amplitude, which is a "
                "population optogenetic response and not a unitary conductance"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="lc4_release_probability",
            quantity_kind="presynaptic_release",
            applies_to=f"{NEURON_LC4} -> {NEURON_GF}",
            why_required=(
                "A mechanistic synapse needs a release probability at the "
                "LC4 terminal."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name="calcium_dependent_release",
            linked_7w_requirement_id="calcium_release_coupling",
            linked_7x_quantity_id="nmj_release_probability",
            must_not_be_inherited_from=(
                "the presynaptic weight recorded for the CENTRAL GF-TTMn "
                "connection at 3.0D-7V, which is a connectome weight and not a "
                "release probability at a visual terminal"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="lplc2_release_probability",
            quantity_kind="presynaptic_release",
            applies_to=f"{NEURON_LPLC2} -> {NEURON_GF}",
            why_required=(
                "A mechanistic synapse needs a release probability at the "
                "LPLC2 terminal."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name="calcium_dependent_release",
            linked_7w_requirement_id="calcium_release_coupling",
            linked_7x_quantity_id="nmj_release_probability",
            must_not_be_inherited_from=(
                "any release parameter of a central or neuromuscular synapse, "
                "and any value inferred from a calcium response"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="gf_sensory_reversal_potential",
            quantity_kind="synaptic_reversal",
            applies_to=f"{NEURON_GF} sensory input",
            why_required=(
                "A mechanistic sensory input needs a reversal potential to "
                "determine the sign of the current it drives into the GF."
            ),
            why_unavailable=no_source,
            linked_7v_excluded_name=None,
            linked_7w_requirement_id=None,
            linked_7x_quantity_id="nmj_reversal_potential",
            must_not_be_inherited_from=(
                "the 0 mV reversal recorded at 3.0D-7V, which is a STANDARD "
                "MODEL VALUE of the central phenomenological synapse and is "
                "neither a GF measurement nor a sensory receptor reversal"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="sensory_q10",
            quantity_kind="temperature_dependence",
            applies_to=f"{NEURON_LC4} and {NEURON_LPLC2} and their input to "
                       f"the {NEURON_GF}",
            why_required=(
                "A mechanistic visual pathway needs a temperature coefficient "
                "to state how its kinetics change with temperature."
            ),
            why_unavailable=(
                "No retrieved source states a Q10 for LC4, for LPLC2 or for "
                "the LC4/LPLC2 input to the GF. " + no_source
            ),
            linked_7v_excluded_name="q10_synaptic_scaling",
            linked_7w_requirement_id="q10_synaptic_scaling",
            linked_7x_quantity_id="nmj_q10_temperature_scaling",
            must_not_be_inherited_from=(
                "any Q10 borrowed from an insect muscle, a photoreceptor "
                "transduction cascade, or a central synapse"
            ),
        ),
        UnavailableSensoryQuantity(
            quantity_id="sensory_receptor_kinetics",
            quantity_kind="receptor_kinetics",
            applies_to=f"the {NEURON_GF} sensory input",
            why_required=(
                "A mechanistic sensory synapse needs receptor kinetics, a "
                "single-channel conductance and a receptor identity to model "
                "the LC4 and LPLC2 input."
            ),
            why_unavailable=(
                "No retrieved source names a receptor, a receptor subunit or a "
                "kinetic constant at the LC4->GF or LPLC2->GF synapse. "
                + no_source
            ),
            linked_7v_excluded_name="dalpha7_receptor_density",
            linked_7w_requirement_id="dalpha7_receptor_kinetics",
            linked_7x_quantity_id="nmj_receptor_kinetics",
            must_not_be_inherited_from=(
                "the Dalpha7 receptor of the CENTRAL cholinergic PSI->DLMn "
                "synapse, which is a different receptor at a different synapse, "
                "and any photoreceptor transduction rate"
            ),
        ),
    )


def _stimulus_rates() -> Tuple[StimulusRateBoundary, ...]:
    return (
        StimulusRateBoundary(
            rate_id=STIMULUS_DISPLAY_FRAME_RATE,
            rate_kind="stimulus_presentation_rate",
            reported_description=(
                "Looming stimuli were presented on a display running at 180 Hz "
                "in Klapoetke et al. 2017."
            ),
            belongs_to="the stimulus presentation apparatus",
            source_references=(SOURCE_KLAPOETKE_2017,),
            notes=(
                "A DISPLAY FRAME RATE IS NOT A NEURAL TIMESTEP. It describes "
                "how fast a monitor changed pixels. It is not an integration "
                "time in LC4, in LPLC2 or in the GF, and it must never be used "
                "as a simulation timestep or converted into one."
            ),
        ),
        StimulusRateBoundary(
            rate_id=STIMULUS_RADIUS_OVER_VELOCITY_RATIO,
            rate_kind="stimulus_geometry",
            reported_description=(
                "Jang et al. 2023 vary the r/v ratio of the looming stimulus "
                "and report that the LC4 velocity contribution grows as it "
                "decreases while the LPLC2 size contribution remains constant."
            ),
            belongs_to="the stimulus geometry",
            source_references=(SOURCE_JANG_2023,),
            notes=(
                "THE r/v RATIO IS A STIMULUS GEOMETRY, NOT A TIME CONSTANT. It "
                "is a ratio of an object's angular radius to its expansion "
                "speed. It is not a synaptic integration time, not a membrane "
                "time constant and not a simulation timestep, and no numeric "
                "value from it is recorded as a parameter here."
            ),
        ),
    )


def _quantitative_updates() -> Tuple[PhenomenologicalCoefficientUpdate, ...]:
    return (
        PhenomenologicalCoefficientUpdate(
            update_id="8h_ache_gf_phenomenological_coefficients",
            supplies=(
                "phenomenological model coefficients C1 through C11",
                "phenomenological sensory delays d1 through d4",
                "phenomenological component weights W_LC4, W_LPLC2, W_i1, W_i2",
            ),
            implemented_in=(
                "biological_brain.dynamics.gf_sensory_drive "
                "(PhenomenologicalGFDrive, AcheGFModelCoefficients, "
                "AcheGFModelDelays)"
            ),
            implemented_as=(
                "a deterministic, pure, phenomenological PREDICTION of the GF "
                "membrane-potential RESPONSE in millivolts. It is not a "
                "synaptic conductance, not a current, not receptor kinetics, "
                "and it drives no compartment: 3.0D-8H performs NO injection "
                "into the live GF and leaves the coupling to the live membrane "
                "explicitly open."
            ),
            source_references=(SOURCE_ACHE_2019,),
            notes=(
                "7Y REFUSED THESE NUMBERS BECAUSE IT HAD NOT ESTABLISHED THEM, "
                "AND 8H ESTABLISHED THEM. 7Y is unchanged and still holds no "
                "coefficient. The published equations, the eleven "
                "coefficients, the four delays and the four weights were "
                "verified against an independent verbatim reproduction of the "
                "Ache et al. 2019 GF model. A CITATION CORRECTION accompanies "
                "this: the PMCID previously cited as the primary source, "
                "PMC6469880, is Augustin et al. 2019, the thoracic GFS latency "
                "model used at 3.0D-7V and 3.0D-8G, and contains no looming "
                "phenomenology at all. NONE of the thirteen unavailable "
                "sensory quantities in this layer becomes available."
            ),
        ),
    )


def _pathway_diagrams() -> Tuple[PathwayStageDiagram, ...]:
    return (
        PathwayStageDiagram(
            diagram_id="looming_to_escape_pathway",
            description=(
                "The conceptual pathway from a looming stimulus to muscle "
                "output, recorded as stage NAMES only."
            ),
            stages=(
                _STAGE_VISUAL_STIMULUS,
                _STAGE_FEATURE_EXTRACTION,
                _STAGE_GF,
                _STAGE_DESCENDING_MOTOR,
                _STAGE_NMJ,
                _STAGE_MUSCLE_OUTPUT,
            ),
            motor_output_owned_by=("3.0D-7W", "3.0D-7X"),
            source_references=(SOURCE_ACHE_2019, SOURCE_KOHN_2018),
            notes=(
                "A SPECIFICATION DIAGRAM, NOT A NUMERICAL SIMULATOR. The "
                "stages are: visual stimulus -> LC4 / LPLC2 feature extraction "
                "-> GF -> TTMn / PSI / DLMn -> NMJs -> muscle output. There is "
                "no weight, no delay, no signal type and no per-stage "
                "contribution between them. The descending-motor, NMJ and "
                "muscle stages are named so the visual input has a stated "
                "destination; their validation targets and quantities are owned "
                "by 3.0D-7W and 3.0D-7X and are NOT restated here."
            ),
        ),
    )


def get_looming_abstraction() -> LoomingAbstraction:
    """Return the looming / visual-input abstraction specification.

    SPECIFICATION ONLY. Nothing here is implemented, connected, populated or
    activated: no LC4 or LPLC2 membrane, no Hodgkin-Huxley kinetics, no
    photoreceptor, no optic-lobe circuit, no LC4->GF or LPLC2->GF synaptic
    conductance, no GF sensory conductance, no membrane current derived from a
    phenomenological term, no sensory timestep, and no change to the passive
    backend, the timestep policy, 3.0D-7U, 3.0D-7V, 3.0D-7W or 3.0D-7X.
    """
    abstraction = LoomingAbstraction(
        name="looming_visual_input_specification",
        source=(
            "Specification of the INPUT END of the giant fiber pathway: LC4 as "
            "the angular-velocity and LPLC2 as the angular-size visual "
            "projection neuron, both projecting directly to the GF; the two "
            "looming stimulus features as external stimulus coordinates rather "
            "than membrane variables; the published phenomenological model as "
            "a sum of a linear velocity term and a Gaussian size term; LPLC2 "
            "radial motion opponency as qualitative functional evidence; the "
            "absence of any LC4, LPLC2, LC4->GF or LPLC2->GF biophysical "
            "quantity; and the explicit refusal to create a GF sensory "
            "conductance or a sensory timestep. SPECIFICATION ONLY: no "
            "visual-neuron simulator and no record eligible for the live "
            "solver."
        ),
        model_id="ModelDBRepository/245415",
        model_citation=SOURCE_ACHE_2019,
        projection_neurons=_projection_neurons(),
        stimulus_features=_stimulus_features(),
        phenomenological_terms=_phenomenological_terms(),
        opponency_components=_opponency_components(),
        gf_visual_inputs=_gf_visual_inputs(),
        validation_targets=_validation_targets(),
        unavailable_sensory_quantities=_unavailable_sensory_quantities(),
        stimulus_rates=_stimulus_rates(),
        pathway_diagrams=_pathway_diagrams(),
        quantitative_updates=_quantitative_updates(),
        scope_note=(
            "TWO VISUAL PROJECTION NEURONS DRIVE THE GF DIRECTLY. LC4 carries "
            "the ANGULAR-VELOCITY component and LPLC2 carries the ENTIRE "
            "ANGULAR-SIZE component, and both are EXPERIMENTALLY SUPPORTED "
            "optic-lobe visual projection neurons that synapse directly onto "
            "the GF. They are visual projection neurons, NOT part of the "
            "central-brain descending-neuron morphology modelled at 3.0D-7A, "
            "and this layer records no morphology or electrical parameter for "
            "either. THE TWO STIMULUS FEATURES ARE EXTERNAL, NOT MEMBRANE "
            "VARIABLES. angular_size and angular_velocity are stimulus "
            "coordinates carried by LPLC2 and LC4 respectively. They are not "
            "voltages, not currents, not conductances and not compartment "
            "states, and the stimulus-feature record type refuses to be marked "
            "as a membrane variable. THE PUBLISHED MODEL IS A FUNCTION, NOT A "
            "MECHANISM. Ache et al. 2019 report a model summing a LINEAR "
            "function of angular velocity (from LC4) with a GAUSSIAN function "
            "of angular size (from LPLC2), which 'replicates GF looming "
            "response dynamics and predicts the peak response time'. That is a "
            "statement about the SHAPE of a stimulus-response curve. "
            "NO COEFFICIENT IS RECORDED: the paper is behind a subscription, "
            "so the velocity-term slope, the Gaussian amplitude, width and "
            "offset, and the relative weighting of the two terms are all "
            "UNKNOWN, and none is guessed or fitted. A phenomenological term "
            "can never be converted into a membrane current. LPLC2 RADIAL "
            "MOTION OPPONENCY IS QUALITATIVE. Outward radial motion drives an "
            "excitatory component and inward radial motion drives an "
            "inhibitory one, per Klapoetke et al. 2017. No inhibitory "
            "conductance, no excitatory conductance, no reversal potential, no "
            "synaptic delay and no receptive-field membrane model is attached, "
            "because none is stated. NO GF SENSORY CONDUCTANCE IS CREATED. Ache "
            "et al. 2019 show by EM reconstruction that LC4 and LPLC2 synapse "
            "directly onto the GF, and that is a CONNECTION, not a "
            "conductance. The GF morphology, the GF passive parameters, the GF "
            "active profile, CompartmentElectrical and PassiveNetwork are "
            "unchanged. THIRTEEN SENSORY QUANTITIES ARE REQUIRED AND "
            "UNAVAILABLE: LC4 membrane conductance, channel densities and HH "
            "kinetics; LPLC2 membrane conductance, channel densities and HH "
            "kinetics; the LC4->GF and LPLC2->GF synaptic conductances; the "
            "LC4 and LPLC2 release probabilities; the GF sensory reversal "
            "potential; the sensory Q10; and the sensory receptor kinetics. "
            "Every one is structurally empty, and each is explicitly barred "
            "from being inherited from the GF parameters of 3.0D-7E and "
            "3.0D-7S or from the central synaptic values of 3.0D-7V. NO SENSORY "
            "TIMESTEP IS INTRODUCED. The 180 Hz display frame rate and the r/v "
            "stimulus ratio are stimulus-presentation parameters and are not "
            "neural integration times. VALIDATION TARGETS ARE QUALITATIVE. The "
            "GF response has velocity and size components; LPLC2 silencing "
            "removes the size component and leaves the velocity component; "
            "LC4 carries velocity and LPLC2 carries size; and the combined "
            "model reproduces response timing. No numeric GF looming latency is "
            "created, because no retrieved source states an absolute value, and "
            "the GF stimulus-response curve remains owned by 3.0D-7W. MOTOR-"
            "OUTPUT TARGETS ARE NOT DUPLICATED. The stage diagram names "
            "TTMn/PSI/DLMn, the NMJs and the muscle output so the visual input "
            "has a stated destination, and names them only. This checkpoint "
            "establishes NO visual-neuron model, NO optic-lobe circuit, NO "
            "synaptic conductance, NO GF sensory conductance and NO simulator "
            "input, and it does NOT modify 3.0D-7U, 3.0D-7V, 3.0D-7W or "
            "3.0D-7X."
        ),
    )
    abstraction.verifies_against_7w_and_7x()
    return abstraction
