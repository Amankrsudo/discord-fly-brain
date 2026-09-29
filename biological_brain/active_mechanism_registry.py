"""Verbatim active mechanism source registry (3.0D-7T).

The 3.0D-7S layer established WHAT the sources support: five published active
model parameters plus qualitative GF channel identities. It deliberately did
not record the compiled NEURON mechanism source that actually implements the
conductances. 3.0D-7T records that source, verbatim.

What this registry holds
------------------------
For each retrieved mechanism of ModelDB 245415 (Augustin et al. 2019, eLife
8:e40240, PMC6469880), the record carries:

- the exact source file, line number and URL of every extracted statement;
- the VERBATIM source line, character for character, including the NEURON tab
  indentation and the source's own inline comments;
- the source's own unit, kept exactly as written (``S/cm2``, ``mV``, ``nS``),
  together with a separate canonical converted value in the project's canonical
  unit (``mS/cm2``, ``mV``, ``uS``);
- the mechanism's STATE block, activation and inactivation variables, its
  ``SOLVE`` method, and whether it declares ``celsius``;
- the source annotations that travel with the value (for example the
  ``: 0.12 mho/cm2`` comment on ``gbar``, which does NOT match the assigned
  value of 0);
- which computational sections of ``gfpn.py`` instantiate the mechanism, and
  where;
- a linkage field naming the 3.0D-7S or 3.0D-7E evidence record that already
  holds the numeric value, so nothing is defined twice.

Mechanisms are recorded at BOTH levels, and the two are never merged:

    MECHANISM_PARAMETER   the ``PARAMETER`` default compiled into the .mod file
    MODEL_INSTANCE_VALUE  the value ``gfpn.py`` assigns on the constructed cell

They are different statements about different things. ``nat.mod`` declares
``gbar = 0``; ``gfpn.py`` assigns ``gbar_nat = 300e-3`` at run time. Recording
only one of the two would be a fabrication of the other.

Retrieved mechanisms
--------------------
    nat.mod    transient sodium, density channel, states m and h
    nap.mod    persistent sodium, density channel, state m
    k.mod      potassium, density channel, state m
    gap2.mod   gap junction, point process, no state variables

``pas`` is recorded separately as INSTANCE VALUES ONLY. It is a built-in
NEURON mechanism and ModelDB 245415 contains no ``channels/pas.mod``, so there
is no mechanism text to extract. What gfpn.py does state is the value it
assigns to ``g_pas`` and ``e_pas``, and those are recorded so that ``gleak`` and
``Eleak`` can be LINKED to the 3.0D-7E passive evidence records. No leak
equation, no leak default and no gate is transcribed from outside this model.

Not retrieved, and why
----------------------
``Exp2Syn`` is a BUILT-IN NEURON point process for the model's chemical
synapses. There is no source text in this model to extract, and it is outside
the scope of active-channel extraction. It is recorded as an unretrieved source
rather than silently omitted.

The channels that 3.0D-7S recorded qualitatively (``Para``, ``Shaker``,
``DmCa1D``, ``Slowpoke``) have NO source mechanism in this model at all. Their
names appear nowhere in the ``channels`` directory. This is recorded explicitly:
the GFS model implements conductance with three generic Hodgkin-Huxley-style
mechanisms, not with the four named Drosophila channels. That is a finding about
the source, not a licence to import generic channel kinetics for any named
channel.

Source conflicts recorded, not resolved
----------------------------------------
Three conflicts in the source are recorded verbatim on both sides and are NOT
reconciled here:

1. ``gbar = 0`` carries the annotation ``: 0.12 mho/cm2`` in all three of
   ``nat.mod``, ``nap.mod`` and ``k.mod``. The annotation does not describe the
   assigned value.
2. The ``DERIVATIVE states`` header comment says it computes ``m, h, and n`` in
   all three files, but ``nap.mod`` and ``k.mod`` declare only ``m``. The header
   is a copy-paste artefact. The STATE block is authoritative.
3. ``gfpn.py`` declares ``g_gap = 135.0`` and assigns it to ``gap2.g``, whose
   unit is NANOSIEMENS, so the statement is 0.135 uS. The 3.0D-7E record
   ``gap_junction_conductance_young`` holds 135.0 uS. The two differ by a factor
   of 1000. This registry records both, links them, and decides nothing.


Hard boundaries
---------------
This module is DATA ONLY. It:

- does NOT implement Hodgkin-Huxley equations or translate the .mod files into
  Python;
- does NOT populate ``CompartmentElectrical``, ``CableParameters`` or any
  compartment;
- does NOT create gating variables or a channel current;
- does NOT connect to the passive backend, to ``PassiveCableModel`` or to any
  DynamicsModel;
- does NOT invent a Q10, a temperature coefficient or any temperature-dependent
  rate. All four retrieved .mod files DECLARE ``celsius`` and NONE OF THEM USE
  IT. No temperature scaling exists in this source and none is created here;
- does NOT derive a solver policy from the source ``METHOD cnexp`` statement.
  The engine timestep policy of 3.0D-3 is untouched by the fact that a NEURON
  source file says ``cnexp``;
- does NOT change, reconcile or override the 3.0D-7S evidence records it links
  to. A linkage is a NAME plus a note, never a second numeric definition and
  never a correction.

``live_solver_eligible`` is False for every record and the registry refuses to
carry a record that says otherwise.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .provenance import ParameterProvenance, ProvenanceRecord


MODELDB_MODEL_ID = "ModelDBRepository/245415"
MODELDB_MODEL_CITATION = (
    "Augustin et al. 2019. Drosophila integrative nerve circuit for escape "
    "behavior. eLife 8:e40240. https://pmc.ncbi.nlm.nih.gov/articles/PMC6469880/ . "
    "ModelDB accession 245415: https://github.com/ModelDBRepository/245415"
)
MODELDB_RAW_BASE = (
    "https://raw.githubusercontent.com/ModelDBRepository/245415/master"
)
MODELDB_TREE_BASE = (
    "https://github.com/ModelDBRepository/245415/tree/master"
)

# The published model runs at exactly this temperature.
MODEL_TEMPERATURE_C = 25.0

# gfpn.py line 146: `neuron.h.celsius = params['temp']`, with
# gfpn.py line 30: `'temp': 25.0,`.
MODEL_TEMPERATURE_SOURCE_LINE = 146
MODEL_TEMPERATURE_DECLARATION_LINE = 30
MODEL_TEMPERATURE_STATEMENT = "neuron.h.celsius = params['temp']"
MODEL_TEMPERATURE_DECLARATION = "'temp': 25.0,"

# Retrieved source text is vendored so provenance is checkable offline.
_VENDORED_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "modeldb_245415",
)


# --- kind labels -----------------------------------------------------------

KIND_DENSITY_CHANNEL = "density_channel"
KIND_POINT_PROCESS = "point_process"

# --- quantity role labels --------------------------------------------------

ROLE_MECHANISM_PARAMETER = "mechanism_parameter_default"
ROLE_MODEL_INSTANCE_VALUE = "model_instance_value"

# --- temperature labels ----------------------------------------------------

TEMPERATURE_NONE_CELSIUS_UNUSED = "none_celsius_declared_but_unused"
TEMPERATURE_NONE_CELSIUS_ABSENT = "none_celsius_absent_from_source"
TEMPERATURE_UNDETERMINED_NO_SOURCE = "undetermined_no_mechanism_source_in_model"

_NO_TEMPERATURE_DECLARED = (
    "NO TEMPERATURE DEPENDENCE EXISTS IN THIS SOURCE. The .mod file DECLARES "
    "celsius but never references it, and no Q10 or rate scaling is present. "
    "No temperature coefficient is invented here."
)

_NO_TEMPERATURE_ABSENT = (
    "NO TEMPERATURE DEPENDENCE EXISTS IN THIS SOURCE. The .mod file does not "
    "even declare celsius, and no Q10 or rate scaling is present. No "
    "temperature coefficient is invented here."
)

_TEMPERATURE_UNDETERMINED = (
    "TEMPERATURE BEHAVIOUR CANNOT BE DETERMINED FROM THIS MODEL. This "
    "mechanism has NO source file in ModelDB 245415, so whether it declares "
    "or uses celsius is not knowable from this source. NEURON's built-in "
    "implementation is deliberately NOT consulted or transcribed: doing so "
    "would import text from outside the project source. No temperature "
    "coefficient and no Q10 is invented here."
)

# --- solver method labels --------------------------------------------------

SOLVE_METHOD_CNEXP = "cnexp"
SOLVE_METHOD_NONE = "none_no_state_variables"

# --- computational status labels -------------------------------------------

STATUS_RETRIEVED = "retrieved_verbatim_not_activated"
STATUS_UNRETRIEVED = "not_retrieved_no_source_in_this_model"
STATUS_INSTANCE_VALUES_ONLY = (
    "model_instance_values_only_builtin_mechanism_source_absent"
)

# Canonical unit of a conductance density in this project.
CANONICAL_DENSITY_UNIT = "mS/cm2"
# Canonical unit of a whole-cell conductance.
CANONICAL_CONDUCTANCE_UNIT = "uS"


_NOT_LIVE = (
    "3.0D-7T IS AN EXTRACTION AND PROVENANCE CHECKPOINT ONLY. This record is "
    "NOT eligible for the live solver: no Hodgkin-Huxley mechanism is "
    "implemented in Python, no compartment is populated with it, no gating "
    "variable exists, no channel current is calculated and the passive backend "
    "is unchanged. Live use requires a separate implementation and "
    "numerical-validation checkpoint."
)

_NO_TEMPERATURE = (
    "NO TEMPERATURE DEPENDENCE EXISTS IN THIS SOURCE. The .mod file DECLARES "
    "celsius but never references it, and no Q10 or rate scaling is present. "
    "No temperature coefficient is invented here."
)

_SOLVER_UNCHANGED = (
    "The source statement 'SOLVE states METHOD cnexp' is a property of the "
    "NEURON source file. It does NOT set, relax or override the project engine "
    "timestep policy, which remains the 3.0D-3 policy of 1 ms. No solver "
    "behaviour is changed by this registry."
)

_COMMENT_MISMATCH = (
    "SOURCE COMMENT CONFLICT, RECORDED NOT RESOLVED. The source assigns "
    "gbar = 0 and annotates it ': 0.12 mho/cm2'. The annotation does not "
    "describe the assigned value, and it is present identically in nat.mod, "
    "nap.mod and k.mod. The verbatim assignment is recorded as the value; the "
    "verbatim annotation is recorded as an annotation. Neither is corrected, "
    "and no gbar default is adopted as a biological value."
)

_DERIVATIVE_COMMENT_MISMATCH = (
    "SOURCE COMMENT CONFLICT, RECORDED NOT RESOLVED. The DERIVATIVE block "
    "header comment reads 'Computes state variables m, h, and n', but the "
    "actual STATE block for this mechanism contains only the variables "
    "recorded in `states`. The header comment is a copy-paste artefact shared "
    "by nat.mod, nap.mod and k.mod. The STATE block is authoritative for the "
    "variable list; the comment is retained verbatim and is not treated as a "
    "declaration of additional state variables."
)

_NO_INACTIVATION = (
    "This mechanism declares NO inactivation variable. "
)

_CONSTANT_TAU = (
    "The activation time constant is the source constant 'mtau = 1' in ms, "
    "independent of voltage. It is NOT a voltage-dependent fit."
)

_STEADY_STATE_NA_P_K = (
    "nap and k have no inactivation gate and a voltage-INDEPENDENT activation "
    "time constant of exactly 1 ms. They are steady-state conductance models in "
    "the source, which reproduces the simplification of the published model and "
    "is not a full transient description of these currents."
)


@dataclass(frozen=True)
class SourceAnnotation:
    """A verbatim source annotation attached to a statement.

    The annotation is the source's own text, kept exactly as written. It is
    never merged into the value and never corrected.
    """

    text: str
    source_file: str
    source_line: int

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError(
                "A source annotation must carry the source's own text."
            )


@dataclass(frozen=True)
class ExtractedQuantity:
    """One quantity extracted verbatim from a mechanism or model file.

    ``source_value_text`` is the COMPLETE verbatim source line, tab indentation
    and inline comment included, so the record can be checked character for
    character against the retrieved file.

    ``value`` and ``source_unit`` are the source's own number and the source's
    own unit string. ``canonical_value`` and ``canonical_unit`` are a separate
    converted pair stored alongside; they never overwrite the source pair.

    ``linked_evidence_record`` names the record of 3.0D-7S or 3.0D-7E that
    already holds this quantity. It is a NAME. This registry never stores a
    second competing numeric definition of a linked quantity.
    """

    name: str
    role: str
    value: float
    source_unit: str
    source_value_text: str
    source_file: str
    source_line: int
    source_url: str
    provenance_category: ParameterProvenance
    annotations: Tuple[SourceAnnotation, ...] = ()
    canonical_value: Optional[float] = None
    canonical_unit: Optional[str] = None
    linked_evidence_registry: Optional[str] = None
    linked_evidence_record: Optional[str] = None
    linkage_note: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if self.role not in (ROLE_MECHANISM_PARAMETER, ROLE_MODEL_INSTANCE_VALUE):
            raise ValueError(
                f"Quantity '{self.name}' has unknown role '{self.role}'"
            )
        if not self.source_value_text:
            raise ValueError(
                f"Quantity '{self.name}' must carry its verbatim source line."
            )
        if (self.canonical_value is None) != (self.canonical_unit is None):
            raise ValueError(
                f"Quantity '{self.name}' must carry both a canonical value and "
                f"a canonical unit, or neither."
            )
        if (
            self.linked_evidence_registry is None
        ) != (self.linked_evidence_record is None):
            raise ValueError(
                f"Quantity '{self.name}' must name both an evidence registry "
                f"and an evidence record, or neither."
            )

    @property
    def provenance(self) -> ProvenanceRecord:
        return ProvenanceRecord(self.provenance_category, self.source_url)

    @property
    def is_linked(self) -> bool:
        return self.linked_evidence_record is not None

    @property
    def source_reference(self) -> str:
        return (
            f"{self.source_file} line {self.source_line} "
            f"({MODELDB_MODEL_ID}): {self.source_value_text}"
        )

    def annotation_texts(self) -> Tuple[str, ...]:
        return tuple(annotation.text for annotation in self.annotations)


@dataclass(frozen=True)
class ExtractedEquation:
    """One source statement recorded verbatim, without interpretation.

    ``expression`` is the verbatim source line. The project does not evaluate
    it here: recording the source equation is not the same as implementing it.
    """

    name: str
    kind: str
    expression: str
    source_file: str
    source_line: int
    source_url: str
    description: str
    note: str = ""

    def __post_init__(self) -> None:
        if not self.expression:
            raise ValueError(
                f"Equation '{self.name}' must carry its verbatim source line."
            )

    @property
    def source_reference(self) -> str:
        return (
            f"{self.source_file} line {self.source_line} "
            f"({MODELDB_MODEL_ID}): {self.expression}"
        )


@dataclass(frozen=True)
class ExtractedMechanism:
    """One retrieved NEURON mechanism of ModelDB 245415, recorded verbatim.

    Every record is observational. ``live_solver_eligible`` exists so that the
    ineligibility is a machine-checkable property of the record rather than a
    sentence in a docstring, and it cannot be set to True.
    """

    name: str
    kind: str
    source_file: str
    source_url: str
    header_comment: Tuple[str, ...]
    states: Tuple[str, ...]
    activation_variables: Tuple[str, ...]
    inactivation_variables: Tuple[str, ...]
    quantities: Tuple[ExtractedQuantity, ...]
    equations: Tuple[ExtractedEquation, ...]
    solve_method: str
    declares_celsius: bool
    temperature_dependence: str
    instantiated_in: Tuple[str, ...]
    instantiation_source_lines: Tuple[int, ...]
    instantiation_statement: str
    computational_status: str
    live_solver_eligible: bool
    limitations: str

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Mechanism '{self.name}' cannot be live-solver eligible in "
                f"3.0D-7T. Extracting a source mechanism does not authorize "
                f"implementing, integrating or activating it."
            )
        if self.kind not in (KIND_DENSITY_CHANNEL, KIND_POINT_PROCESS):
            raise ValueError(
                f"Mechanism '{self.name}' has unknown kind '{self.kind}'"
            )
        if self.computational_status not in (
            STATUS_RETRIEVED, STATUS_INSTANCE_VALUES_ONLY
        ):
            raise ValueError(
                f"Mechanism '{self.name}' has unknown computational status "
                f"'{self.computational_status}'"
            )
        if self.temperature_dependence not in (
            TEMPERATURE_NONE_CELSIUS_UNUSED,
            TEMPERATURE_NONE_CELSIUS_ABSENT,
            TEMPERATURE_UNDETERMINED_NO_SOURCE,
        ):
            raise ValueError(
                f"Mechanism '{self.name}' claims a temperature dependence. No "
                f"temperature-dependent rate exists in this source and none may "
                f"be invented."
            )
        expected_declaration = {
            TEMPERATURE_NONE_CELSIUS_UNUSED: True,
            TEMPERATURE_NONE_CELSIUS_ABSENT: False,
            TEMPERATURE_UNDETERMINED_NO_SOURCE: False,
        }[self.temperature_dependence]
        if self.declares_celsius is not expected_declaration:
            raise ValueError(
                f"Mechanism '{self.name}' declares_celsius="
                f"{self.declares_celsius} contradicts its temperature "
                f"dependence '{self.temperature_dependence}'. The verbatim "
                f"declaration status of celsius must be recorded as the source "
                f"has it."
            )
        for variable in self.activation_variables + self.inactivation_variables:
            if variable not in self.states:
                raise ValueError(
                    f"Mechanism '{self.name}' names gating variable '{variable}' "
                    f"that is not in its STATE block {self.states}."
                )
        # A mechanism with no .mod file may record only model instance values.
        if self.computational_status == STATUS_INSTANCE_VALUES_ONLY:
            if self.mechanism_parameters():
                raise ValueError(
                    f"Mechanism '{self.name}' has no .mod source file, so it "
                    f"cannot carry mechanism PARAMETER defaults."
                )
            if self.equations:
                raise ValueError(
                    f"Mechanism '{self.name}' has no .mod source file, so it "
                    f"cannot carry mechanism equations."
                )
            if not self.model_instance_values():
                raise ValueError(
                    f"Mechanism '{self.name}' has no source text at all and "
                    f"must be recorded as unretrieved instead."
                )

    @property
    def is_instantiated(self) -> bool:
        return bool(self.instantiated_in)

    @property
    def has_inactivation(self) -> bool:
        return bool(self.inactivation_variables)

    @property
    def has_mechanism_source(self) -> bool:
        """True when a .mod file for this mechanism exists in the model."""
        return self.computational_status == STATUS_RETRIEVED

    def quantity(self, name: str) -> ExtractedQuantity:
        for quantity in self.quantities:
            if quantity.name == name:
                return quantity
        raise KeyError(
            f"Quantity '{name}' not in mechanism '{self.name}'"
        )

    def equation(self, name: str) -> ExtractedEquation:
        for equation in self.equations:
            if equation.name == name:
                return equation
        raise KeyError(
            f"Equation '{name}' not in mechanism '{self.name}'"
        )

    def model_instance_values(self) -> Tuple[ExtractedQuantity, ...]:
        return tuple(
            q for q in self.quantities if q.role == ROLE_MODEL_INSTANCE_VALUE
        )

    def mechanism_parameters(self) -> Tuple[ExtractedQuantity, ...]:
        return tuple(
            q for q in self.quantities if q.role == ROLE_MECHANISM_PARAMETER
        )


@dataclass(frozen=True)
class UnretrievedSource:
    """A mechanism the model uses or a source names, with no text to extract.

    Recorded so that absence is explicit. A mechanism that is silently missing
    from the registry cannot be distinguished from one that was overlooked.
    """

    name: str
    kind: str
    computational_status: str
    reason: str
    scope_note: str
    live_solver_eligible: bool = False

    def __post_init__(self) -> None:
        if self.live_solver_eligible:
            raise ValueError(
                f"Unretrieved source '{self.name}' cannot be live-solver "
                f"eligible; nothing was retrieved from it."
            )
        if self.computational_status != STATUS_UNRETRIEVED:
            raise ValueError(
                f"Unretrieved source '{self.name}' must have status "
                f"'{STATUS_UNRETRIEVED}'"
            )
        if not self.reason:
            raise ValueError(
                f"Unretrieved source '{self.name}' must state why it was not "
                f"retrieved."
            )


@dataclass(frozen=True)
class ActiveMechanismRegistry:
    """Verbatim active mechanism source records. NOT an activation mechanism.

    Assigns nothing. No compartment, no ``CableParameters``, no
    ``CompartmentElectrical``, no gating state and no solver input is populated
    from this registry, and the passive backend does not import it.
    """

    name: str
    source: str
    model_id: str
    model_citation: str
    model_temperature_c: float
    mechanisms: Tuple[ExtractedMechanism, ...]
    unretrieved: Tuple[UnretrievedSource, ...]
    scope_note: str

    def get(self, name: str) -> ExtractedMechanism:
        for mechanism in self.mechanisms:
            if mechanism.name == name:
                return mechanism
        raise KeyError(f"Active mechanism '{name}' not in registry")

    def names(self) -> Tuple[str, ...]:
        return tuple(mechanism.name for mechanism in self.mechanisms)

    def density_channels(self) -> Tuple[str, ...]:
        return tuple(
            m.name for m in self.mechanisms if m.kind == KIND_DENSITY_CHANNEL
        )

    def point_processes(self) -> Tuple[str, ...]:
        return tuple(
            m.name for m in self.mechanisms if m.kind == KIND_POINT_PROCESS
        )

    def instantiated(self) -> Tuple[str, ...]:
        return tuple(m.name for m in self.mechanisms if m.is_instantiated)

    def not_instantiated(self) -> Tuple[str, ...]:
        return tuple(m.name for m in self.mechanisms if not m.is_instantiated)

    def unretrieved_names(self) -> Tuple[str, ...]:
        return tuple(record.name for record in self.unretrieved)

    def quantity(self, mechanism_name: str, quantity_name: str) -> ExtractedQuantity:
        return self.get(mechanism_name).quantity(quantity_name)

    def model_temperature_celsius_statement(self) -> str:
        return (
            f"{MODELDB_MODEL_ID} gfpn.py line "
            f"{MODEL_TEMPERATURE_SOURCE_LINE}: "
            f"{MODEL_TEMPERATURE_STATEMENT}"
        )

    def linkages(self) -> Tuple[Tuple[str, str, str, str], ...]:
        """Every evidence linkage, as (mechanism, quantity, registry, record)."""
        return tuple(
            (mechanism.name, quantity.name,
             quantity.linked_evidence_registry or "",
             quantity.linked_evidence_record or "")
            for mechanism in self.mechanisms
            for quantity in mechanism.quantities
            if quantity.is_linked
        )

    def linked_evidence_records(self) -> Tuple[str, ...]:
        seen: Dict[str, None] = {}
        for _, _, _, record in self.linkages():
            seen.setdefault(record, None)
        return tuple(seen)

    def quantities_for_evidence_record(self, record_name: str) -> Tuple[str, ...]:
        return tuple(
            f"{mechanism.name}.{quantity.name}"
            for mechanism in self.mechanisms
            for quantity in mechanism.quantities
            if quantity.linked_evidence_record == record_name
        )

    def any_live_solver_eligible(self) -> bool:
        """Always False in 3.0D-7T: extraction authorizes nothing."""
        return any(m.live_solver_eligible for m in self.mechanisms) or any(
            u.live_solver_eligible for u in self.unretrieved
        )

    def unretrieved_by_name(self, name: str) -> UnretrievedSource:
        for record in self.unretrieved:
            if record.name == name:
                return record
        raise KeyError(f"Unretrieved source '{name}' not in registry")

    def verify_verbatim_source(self) -> None:
        """Assert every recorded line matches the retrieved file character for
        character.

        The retrieved mechanism sources and ``gfpn.py`` are vendored under
        ``biological_brain/data/modeldb_245415/`` so that provenance is
        checkable offline without a network fetch. Each statement is checked
        against ITS OWN source file, not against the mechanism's primary file,
        because a mechanism's model-instance values come from ``gfpn.py``. The
        test suite calls this so a transcription error cannot pass unnoticed.
        """
        cache: Dict[str, Tuple[str, ...]] = {}
        for mechanism in self.mechanisms:
            for quantity in mechanism.quantities:
                lines = cache.get(quantity.source_file)
                if lines is None:
                    lines = _source_lines(quantity.source_file)
                    cache[quantity.source_file] = lines
                _assert_verbatim(
                    mechanism, quantity.source_file, quantity.source_line,
                    quantity.source_value_text, lines,
                )
                for annotation in quantity.annotations:
                    if annotation.text not in quantity.source_value_text:
                        raise AssertionError(
                            f"{mechanism.name} {quantity.name}: annotation "
                            f"{annotation.text!r} is not present in its own "
                            f"source line"
                        )
            for equation in mechanism.equations:
                lines = cache.get(equation.source_file)
                if lines is None:
                    lines = _source_lines(equation.source_file)
                    cache[equation.source_file] = lines
                _assert_verbatim(
                    mechanism, equation.source_file, equation.source_line,
                    equation.expression, lines,
                )


def _source_lines(source_file: str) -> Tuple[str, ...]:
    path = os.path.join(_VENDORED_ROOT, source_file)
    with open(path, encoding="utf-8") as handle:
        return tuple(handle.read().split("\n"))


def _assert_verbatim(
    mechanism: ExtractedMechanism,
    source_file: str,
    line_number: int,
    text: str,
    lines: Tuple[str, ...],
) -> None:
    if not 1 <= line_number <= len(lines):
        raise AssertionError(
            f"{mechanism.name}: line {line_number} is outside {source_file}"
        )
    actual = lines[line_number - 1]
    if actual != text:
        raise AssertionError(
            f"{mechanism.name} {source_file} line {line_number}: "
            f"recorded text is not verbatim.\n  recorded: {text!r}\n"
            f"  file:     {actual!r}"
        )


def _url(path: str) -> str:
    return f"{MODELDB_RAW_BASE}/{path}"


def _mod_quantity(
    mechanism: str,
    source_file: str,
    line: int,
    name: str,
    value: float,
    unit: str,
    text: str,
    annotation: Optional[str] = None,
    canonical_value: Optional[float] = None,
    canonical_unit: Optional[str] = None,
    provenance_category: ParameterProvenance = ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
    note: str = "",
) -> ExtractedQuantity:
    annotations: Tuple[SourceAnnotation, ...] = ()
    if annotation is not None:
        annotations = (
            SourceAnnotation(
                text=annotation, source_file=source_file, source_line=line
            ),
        )
    return ExtractedQuantity(
        name=name,
        role=ROLE_MECHANISM_PARAMETER,
        value=value,
        source_unit=unit,
        source_value_text=text,
        source_file=source_file,
        source_line=line,
        source_url=_url(source_file),
        provenance_category=provenance_category,
        annotations=annotations,
        canonical_value=canonical_value,
        canonical_unit=canonical_unit,
        note=note,
    )


def _instance_quantity(
    mechanism: str,
    source_file: str,
    line: int,
    name: str,
    value: float,
    unit: str,
    text: str,
    canonical_value: Optional[float] = None,
    canonical_unit: Optional[str] = None,
    linked_registry: Optional[str] = None,
    linked_record: Optional[str] = None,
    linkage_note: str = "",
    note: str = "",
) -> ExtractedQuantity:
    return ExtractedQuantity(
        name=name,
        role=ROLE_MODEL_INSTANCE_VALUE,
        value=value,
        source_unit=unit,
        source_value_text=text,
        source_file=source_file,
        source_line=line,
        source_url=_url(source_file),
        provenance_category=ParameterProvenance.PUBLISHED_MODEL_PARAMETER,
        canonical_value=canonical_value,
        canonical_unit=canonical_unit,
        linked_evidence_registry=linked_registry,
        linked_evidence_record=linked_record,
        linkage_note=linkage_note,
        note=note,
    )


def _mod_equation(
    source_file: str,
    line: int,
    name: str,
    kind: str,
    expression: str,
    description: str,
    note: str = "",
) -> ExtractedEquation:
    return ExtractedEquation(
        name=name,
        kind=kind,
        expression=expression,
        source_file=source_file,
        source_line=line,
        source_url=_url(source_file),
        description=description,
        note=note,
    )


_NAT_FILE = "channels/nat.mod"
_NAP_FILE = "channels/nap.mod"
_K_FILE = "channels/k.mod"
_GAP2_FILE = "channels/gap2.mod"
_GFPN_FILE = "gfpn.py"


def _nat() -> ExtractedMechanism:
    gbar_text = "\tgbar = 0   \t(S/cm2)\t: 0.12 mho/cm2"
    return ExtractedMechanism(
        name="nat",
        kind=KIND_DENSITY_CHANNEL,
        source_file=_NAT_FILE,
        source_url=_url(_NAT_FILE),
        header_comment=(
            "COMMENT",
            "",
            "nat.mod",
            "",
            "Transient sodium channel, Hodgkin-Huxley style kinetics.  ",
            "Adapted from Gunay et al., 2015",
        ),
        states=("m", "h"),
        activation_variables=("m",),
        inactivation_variables=("h",),
        quantities=(
            _mod_quantity(
                "nat", _NAT_FILE, 22, "gbar", 0.0, "S/cm2", gbar_text,
                annotation="0.12 mho/cm2",
                note=_COMMENT_MISMATCH,
            ),
            _mod_quantity(
                "nat", _NAT_FILE, 24, "v1_2m", -29.13, "mV",
                "\tv1_2m  = -29.13\t(mV)\t\t: v 1/2 for act\t\t",
                annotation="v 1/2 for act",
                note=(
                    "Source comment says 'v 1/2 for act'. VERBATIM."
                ),
            ),
            _mod_quantity(
                "nat", _NAT_FILE, 25, "km", -8.92, "mV",
                "\tkm   = -8.92\t(mV)\t\t\t: act slope\t\t",
                annotation="act slope",
            ),
            _mod_quantity(
                "nat", _NAT_FILE, 28, "v1_2h", -47.0, "mV",
                "\tv1_2h  = -47\t(mV)\t\t: v 1/2 for inact \t",
                annotation="v 1/2 for inact ",
            ),
            _mod_quantity(
                "nat", _NAT_FILE, 29, "kh", 5.0, "mV",
                "\tkh   = 5\t(mV)\t\t\t: act slope\t\t",
                annotation="act slope",
                note=(
                    "The source annotates the INACTIVATION slope as "
                    "'act slope'. VERBATIM; the annotation is not corrected."
                ),
            ),
            _mod_quantity(
                "nat", _NAT_FILE, 34, "vmin", -120.0, "mV",
                "\tvmin = -120\t(mV)",
            ),
            _mod_quantity(
                "nat", _NAT_FILE, 35, "vmax", 1000.0, "mV",
                "\tvmax = 1000\t(mV)",
            ),
            _instance_quantity(
                "nat", _GFPN_FILE, 53, "gnatbar", 300.0, "S/cm2",
                "                 'gnatbar': 300e-3,",
                canonical_value=300.0,
                canonical_unit=CANONICAL_DENSITY_UNIT,
                linked_registry="active_conductance_registry",
                linked_record="g_Na",
                linkage_note=(
                    "300e-3 S/cm2 is 300 mS/cm2, the value already held by the "
                    "3.0D-7S record 'g_Na'. This registry links to that record "
                    "and does not define a second numeric value for it."
                ),
            ),
            _instance_quantity(
                "nat", _GFPN_FILE, 58, "ena", 65.0, "mV", "                 'ena': 65,",
                linked_registry="active_conductance_registry",
                linked_record="E_Na",
                linkage_note=(
                    "65 mV is the value already held by the 3.0D-7S record "
                    "'E_Na'. This registry links to that record and does not "
                    "define a second numeric value for it. gfpn.py assigns it "
                    "as cell.ena on line 140; the mechanisms READ ena through "
                    "'USEION na READ ena' and do not own it."
                ),
            ),
        ),
        equations=(
            _mod_equation(
                _NAT_FILE, 14, "useion", "ion_use",
                "\tUSEION na READ ena WRITE ina",
                "Reads the sodium reversal potential and writes the sodium "
                "current. The mechanism does not own the reversal potential.",
            ),
            _mod_equation(
                _NAT_FILE, 57, "state_block", "state",
                "STATE { m h }",
                "Two state variables: an activation gate m and an "
                "inactivation gate h.",
            ),
            _mod_equation(
                _NAT_FILE, 67, "solve_statement", "solve",
                "\tSOLVE states METHOD cnexp",
                "The source solves its states with NEURON's cnexp method.",
                note=_SOLVER_UNCHANGED,
            ),
            _mod_equation(
                _NAT_FILE, 68, "conductance", "conductance_expression",
                "\tgna = gbar*m*m*m*h",
                "Conductance density is gbar times the third power of m times h.",
            ),
            _mod_equation(
                _NAT_FILE, 69, "current", "current_expression",
                "\tina = gna * (v - ena)",
                "Ohm's law on the sodium reversal potential.",
            ),
            _mod_equation(
                _NAT_FILE, 75, "m_derivative", "state_derivative",
                "        m' =  (minf-m)/(mtau)",
                "Activation gate approaches its steady state with time "
                "constant mtau.",
            ),
            _mod_equation(
                _NAT_FILE, 76, "h_derivative", "state_derivative",
                "        h' =  (hinf-h)/(htau)",
                "Inactivation gate approaches its steady state with time "
                "constant htau.",
            ),
            _mod_equation(
                _NAT_FILE, 96, "minf", "rate",
                "\tminf = 1/(1+exp((vm-v1_2m)/km))",
                "Steady-state activation, Boltzmann form.",
            ),
            _mod_equation(
                _NAT_FILE, 97, "mtau", "rate",
                "\tmtau = 0.13 + 3.43/(1+exp((vm+45.35)/5.98))",
                "Activation time constant, voltage dependent, in ms.",
            ),
            _mod_equation(
                _NAT_FILE, 100, "hinf", "rate",
                "\thinf = 1/(1+exp((vm-v1_2h)/kh))",
                "Steady-state inactivation, Boltzmann form.",
            ),
            _mod_equation(
                _NAT_FILE, 101, "htau", "rate",
                "\thtau = 0.36 + exp((vm+20.65)/-10.47)",
                "Inactivation time constant, voltage dependent, in ms.",
            ),
            _mod_equation(
                _GFPN_FILE, 134, "instantiation", "insertion",
                "            cell.insert('nat')",
                "nat is inserted into each computational section of the "
                "active list.",
            ),
            _mod_equation(
                _GFPN_FILE, 142, "gbar_assignment", "assignment",
                "            cell.gbar_nat = params['gnatbar']",
                "The model instance value overrides the .mod gbar default of 0.",
            ),
        ),
        solve_method=SOLVE_METHOD_CNEXP,
        declares_celsius=True,
        temperature_dependence=TEMPERATURE_NONE_CELSIUS_UNUSED,
        instantiated_in=("GF", "PSI", "DLMn", "TTMn"),
        instantiation_source_lines=(134, 142),
        instantiation_statement="            cell.insert('nat')",
        computational_status=STATUS_RETRIEVED,
        live_solver_eligible=False,
        limitations=(
            "Transient sodium mechanism of the published model, recorded "
            "verbatim. " + _NOT_LIVE + " " + _NO_TEMPERATURE + " "
            + _SOLVER_UNCHANGED + " " + _DERIVATIVE_COMMENT_MISMATCH
        ),
    )


def _nap() -> ExtractedMechanism:
    gbar_text = "\tgbar = 0   \t(S/cm2)\t: 0.12 mho/cm2"
    return ExtractedMechanism(
        name="nap",
        kind=KIND_DENSITY_CHANNEL,
        source_file=_NAP_FILE,
        source_url=_url(_NAP_FILE),
        header_comment=(
            "COMMENT",
            "",
            "nap.mod",
            "",
            "Persistent sodium channel, Hodgkin-Huxley style kinetics.  ",
            "Adapted from Gunay et al., 2015",
        ),
        states=("m",),
        activation_variables=("m",),
        inactivation_variables=(),
        quantities=(
            _mod_quantity(
                "nap", _NAP_FILE, 22, "gbar", 0.0, "S/cm2", gbar_text,
                annotation="0.12 mho/cm2",
                note=_COMMENT_MISMATCH,
            ),
            _mod_quantity(
                "nap", _NAP_FILE, 24, "v1_2m", -48.77, "mV",
                "\tv1_2m  = -48.77\t(mV)\t\t: v 1/2 for act\t\t",
                annotation="v 1/2 for act",
            ),
            _mod_quantity(
                "nap", _NAP_FILE, 25, "km", -3.68, "mV",
                "\tkm   = -3.68\t(mV)\t\t\t: act slope\t\t",
                annotation="act slope",
            ),
            _mod_quantity(
                "nap", _NAP_FILE, 32, "vmin", -120.0, "mV",
                "\tvmin = -120\t(mV)",
            ),
            _mod_quantity(
                "nap", _NAP_FILE, 33, "vmax", 1000.0, "mV",
                "\tvmax = 1000\t(mV)",
            ),
            _instance_quantity(
                "nap", _GFPN_FILE, 54, "gnapbar", 110e-6, "S/cm2",
                "                 'gnapbar': 110e-6,",
                canonical_value=0.11,
                canonical_unit=CANONICAL_DENSITY_UNIT,
                linked_registry="active_conductance_registry",
                linked_record="g_Nap",
                linkage_note=(
                    "110e-6 S/cm2 is 0.11 mS/cm2, the value already held by the "
                    "3.0D-7S record 'g_Nap'. This registry links to that record "
                    "and does not define a second numeric value for it."
                ),
            ),
        ),
        equations=(
            _mod_equation(
                _NAP_FILE, 14, "useion", "ion_use",
                "\tUSEION na READ ena WRITE ina",
                "Reads the sodium reversal potential and writes the sodium "
                "current. Shares ena with nat.",
            ),
            _mod_equation(
                _NAP_FILE, 55, "state_block", "state",
                "STATE {m}",
                "One state variable m. There is no inactivation gate.",
                note=_NO_INACTIVATION,
            ),
            _mod_equation(
                _NAP_FILE, 64, "solve_statement", "solve",
                "\tSOLVE states METHOD cnexp",
                "The source solves its states with NEURON's cnexp method.",
                note=_SOLVER_UNCHANGED,
            ),
            _mod_equation(
                _NAP_FILE, 65, "conductance", "conductance_expression",
                "\tgna = gbar*m",
                "Conductance density is gbar times m to the first power. NOTE "
                "the symbol is gna, the same name nat uses, but the exponent "
                "differs. VERBATIM.",
            ),
            _mod_equation(
                _NAP_FILE, 66, "current", "current_expression",
                "\tina = gna * (v - ena)",
                "Ohm's law on the sodium reversal potential, identical in form "
                "to nat's current equation.",
            ),
            _mod_equation(
                _NAP_FILE, 73, "m_derivative", "state_derivative",
                "        m' =  (minf-m)/(mtau)",
                "Single activation gate.",
            ),
            _mod_equation(
                _NAP_FILE, 93, "minf", "rate",
                "\tminf = 1/(1+exp((vm-v1_2m)/km))",
                "Steady-state activation, Boltzmann form.",
            ),
            _mod_equation(
                _NAP_FILE, 94, "mtau", "rate",
                "\tmtau = 1",
                "Activation time constant is the constant 1 ms, independent of "
                "voltage.",
                note=_CONSTANT_TAU,
            ),
            _mod_equation(
                _GFPN_FILE, 135, "instantiation", "insertion",
                "            cell.insert('nap')",
                "nap is inserted into each computational section of the "
                "active list.",
            ),
            _mod_equation(
                _GFPN_FILE, 143, "gbar_assignment", "assignment",
                "            cell.gbar_nap = params['gnapbar']",
                "The model instance value overrides the .mod gbar default of 0.",
            ),
        ),
        solve_method=SOLVE_METHOD_CNEXP,
        declares_celsius=True,
        temperature_dependence=TEMPERATURE_NONE_CELSIUS_UNUSED,
        instantiated_in=("GF", "PSI", "DLMn", "TTMn"),
        instantiation_source_lines=(135, 143),
        instantiation_statement="            cell.insert('nap')",
        computational_status=STATUS_RETRIEVED,
        live_solver_eligible=False,
        limitations=(
            "Persistent sodium mechanism of the published model, recorded "
            "verbatim. " + _NO_INACTIVATION + _CONSTANT_TAU + " " + _NOT_LIVE
            + " " + _NO_TEMPERATURE + " " + _SOLVER_UNCHANGED + " "
            + _STEADY_STATE_NA_P_K + " " + _DERIVATIVE_COMMENT_MISMATCH
        ),
    )


def _k() -> ExtractedMechanism:
    gbar_text = "\tgbar = 0   \t(S/cm2)\t: 0.12 mho/cm2"
    return ExtractedMechanism(
        name="k",
        kind=KIND_DENSITY_CHANNEL,
        source_file=_K_FILE,
        source_url=_url(_K_FILE),
        header_comment=(
            "COMMENT",
            "",
            "k.mod",
            "",
            "Potassium channel, Hodgkin-Huxley style kinetics.  ",
            "Adapted from Gunay et al., 2015",
        ),
        states=("m",),
        activation_variables=("m",),
        inactivation_variables=(),
        quantities=(
            _mod_quantity(
                "k", _K_FILE, 22, "gbar", 0.0, "S/cm2", gbar_text,
                annotation="0.12 mho/cm2",
                note=_COMMENT_MISMATCH,
            ),
            _mod_quantity(
                "k", _K_FILE, 24, "v1_2m", -12.85, "mV",
                "\tv1_2m  = -12.85\t(mV)\t\t: v 1/2 for act\t\t",
                annotation="v 1/2 for act",
            ),
            _mod_quantity(
                "k", _K_FILE, 25, "km", -19.91, "mV",
                "\tkm   = -19.91\t(mV)\t\t\t: act slope\t\t",
                annotation="act slope",
            ),
            _mod_quantity(
                "k", _K_FILE, 32, "vmin", -120.0, "mV",
                "\tvmin = -120\t(mV)",
            ),
            _mod_quantity(
                "k", _K_FILE, 33, "vmax", 1000.0, "mV",
                "\tvmax = 1000\t(mV)",
            ),
            _instance_quantity(
                "k", _GFPN_FILE, 55, "gkbar", 10e-3, "S/cm2",
                "                 'gkbar': 10e-3,",
                canonical_value=10.0,
                canonical_unit=CANONICAL_DENSITY_UNIT,
                linked_registry="active_conductance_registry",
                linked_record="g_K",
                linkage_note=(
                    "10e-3 S/cm2 is 10 mS/cm2, the value already held by the "
                    "3.0D-7S record 'g_K'. This registry links to that record "
                    "and does not define a second numeric value for it."
                ),
            ),
            _instance_quantity(
                "k", _GFPN_FILE, 59, "ek", -74.0, "mV", "                 'ek': -74,",
                linked_registry="active_conductance_registry",
                linked_record="E_K",
                linkage_note=(
                    "-74 mV is the value already held by the 3.0D-7S record "
                    "'E_K'. This registry links to that record and does not "
                    "define a second numeric value for it. gfpn.py assigns it "
                    "as cell.ek on line 141; the mechanism READS ek through "
                    "'USEION k READ ek' and does not own it."
                ),
            ),
        ),
        equations=(
            _mod_equation(
                _K_FILE, 14, "useion", "ion_use",
                "\tUSEION k READ ek WRITE ik",
                "Reads the potassium reversal potential and writes the "
                "potassium current.",
            ),
            _mod_equation(
                _K_FILE, 55, "state_block", "state",
                "STATE {m}",
                "One state variable m. There is no inactivation gate, so the "
                "mechanism as written cannot express a delayed rectifier's "
                "deactivation kinetics.",
                note=_NO_INACTIVATION,
            ),
            _mod_equation(
                _K_FILE, 64, "solve_statement", "solve",
                "\tSOLVE states METHOD cnexp",
                "The source solves its states with NEURON's cnexp method.",
                note=_SOLVER_UNCHANGED,
            ),
            _mod_equation(
                _K_FILE, 65, "conductance", "conductance_expression",
                "\tgk = gbar*m",
                "Conductance density is gbar times m.",
            ),
            _mod_equation(
                _K_FILE, 66, "current", "current_expression",
                "\tik = gk * (v - ek)",
                "Ohm's law on the potassium reversal potential.",
            ),
            _mod_equation(
                _K_FILE, 73, "m_derivative", "state_derivative",
                "        m' =  (minf-m)/(mtau)",
                "Single activation gate.",
            ),
            _mod_equation(
                _K_FILE, 93, "minf", "rate",
                "\tminf = 1/(1+exp((vm-v1_2m)/km))",
                "Steady-state activation, Boltzmann form.",
            ),
            _mod_equation(
                _K_FILE, 94, "mtau", "rate",
                "\tmtau = 1",
                "Activation time constant is the constant 1 ms, independent of "
                "voltage.",
                note=_CONSTANT_TAU,
            ),
            _mod_equation(
                _GFPN_FILE, 136, "instantiation", "insertion",
                "            cell.insert('k')",
                "k is inserted into each computational section of the active "
                "list.",
            ),
            _mod_equation(
                _GFPN_FILE, 144, "gbar_assignment", "assignment",
                "            cell.gbar_k = params['gkbar']",
                "The model instance value overrides the .mod gbar default of 0.",
            ),
        ),
        solve_method=SOLVE_METHOD_CNEXP,
        declares_celsius=True,
        temperature_dependence=TEMPERATURE_NONE_CELSIUS_UNUSED,
        instantiated_in=("GF", "PSI", "DLMn", "TTMn"),
        instantiation_source_lines=(136, 144),
        instantiation_statement="            cell.insert('k')",
        computational_status=STATUS_RETRIEVED,
        live_solver_eligible=False,
        limitations=(
            "Potassium mechanism of the published model, recorded verbatim. "
            + _NO_INACTIVATION + _CONSTANT_TAU + " " + _NOT_LIVE + " "
            + _NO_TEMPERATURE + " " + _SOLVER_UNCHANGED + " "
            + _STEADY_STATE_NA_P_K + " " + _DERIVATIVE_COMMENT_MISMATCH
        ),
    )


def _gap2() -> ExtractedMechanism:
    return ExtractedMechanism(
        name="gap2",
        kind=KIND_POINT_PROCESS,
        source_file=_GAP2_FILE,
        source_url=_url(_GAP2_FILE),
        header_comment=(),
        states=(),
        activation_variables=(),
        inactivation_variables=(),
        quantities=(
            _mod_quantity(
                "gap2", _GAP2_FILE, 12, "g", 0.0, "nanosiemens",
                "\tg = 0 (nanosiemens) :1 (nanosiemens) : 1nS = 1000 pS",
                annotation="1nS = 1000 pS",
                note=(
                    "The source default g is 0, with the annotation "
                    "':1 (nanosiemens) : 1nS = 1000 pS'. The annotation is "
                    "the source's own unit gloss and a suggested value, not "
                    "the assigned default. VERBATIM."
                ),
            ),
            _instance_quantity(
                "gap2", _GFPN_FILE, 31, "g_gap", 135.0, "nS",
                "                 'g_gap': 135.0,",
                canonical_value=0.135,
                canonical_unit=CANONICAL_CONDUCTANCE_UNIT,
                linked_registry="passive_electrical_registry",
                linked_record="gap_junction_conductance_young",
                linkage_note=(
                    "UNITS CONFLICT BETWEEN SOURCES, RECORDED NOT RESOLVED. "
                    "gfpn.py declares g_gap = 135.0 and assigns it to "
                    "gap2.g on line 171. gap2.g is a whole-cell conductance in "
                    "nANOSIEMENS, so 135.0 is 0.135 uS. The 3.0D-7E record "
                    "'gap_junction_conductance_young' holds 135.0 uS, a factor "
                    "of 1000 apart. The canonical pair above is a MECHANICAL "
                    "UNIT CONVERSION of the source statement only (135 nS = "
                    "0.135 uS) and is NOT a claim about which of the two "
                    "records is correct. This registry records both statements "
                    "verbatim, links them, and does NOT decide between them, "
                    "does NOT convert one into the other, and does NOT change "
                    "either record."
                ),
            ),
            _instance_quantity(
                "gap2", _GFPN_FILE, 171, "g_gap_at_assignment_site", 135.0, "nS",
                "        self.GF_TTMn_gap.g = params['g_gap']",
                note=(
                    "The assignment SITE of the declared g_gap. It states the "
                    "same nS quantity as the declaration, so it is a second "
                    "verbatim statement of one value, not a second value. The "
                    "units conflict with the 3.0D-7E record is recorded on the "
                    "declaration and is NOT resolved here."
                ),
            ),
            _instance_quantity(
                "gap2", _GFPN_FILE, 175, "g_gap_at_second_site", 135.0, "nS",
                "        self.GF_PSI_gap.g = params['g_gap']",
                note=(
                    "The second gap junction uses the same declared g_gap. "
                    "Same units conflict, recorded not resolved."
                ),
            ),
        ),
        equations=(
            _mod_equation(
                _GAP2_FILE, 3, "point_process_declaration", "declaration",
                "\tPOINT_PROCESS gap2",
                "gap2 is a point process, not a density channel. It is "
                "instantiated at a location, not distributed over a section.",
            ),
            _mod_equation(
                _GAP2_FILE, 4, "nonspecific_current", "declaration",
                "\tNONSPECIFIC_CURRENT i",
                "The current is nonspecific, not ionic: it has no reversal "
                "potential and no USEION.",
            ),
            _mod_equation(
                _GAP2_FILE, 6, "pointer", "declaration",
                "\tPOINTER vgap\t",
                "vgap is a POINTER: the coupled partner's voltage is supplied "
                "from outside by setpointer().",
            ),
            _mod_equation(
                _GAP2_FILE, 20, "current", "current_expression",
                "\ti = (v - vgap)*g*(0.001)",
                "Ohm's law against the pointer voltage, with the literal "
                "factor 0.001 the source needs to express mV x nS in nA. The "
                "factor is recorded verbatim and is not reinterpreted.",
            ),
            _mod_equation(
                _GFPN_FILE, 169, "instantiation", "instantiation",
                "        self.GF_TTMn_gap = neuron.h.gap2(self.TTMn_med(params['TTMn_syn_post_loc']))",
                "The GF->TTMn gap junction is created in wire_cells(), NOT in "
                "__init__(). It exists only after that method is called.",
            ),
            _mod_equation(
                _GFPN_FILE, 170, "pointer_binding", "pointer",
                "        neuron.h.setpointer(self.GF(params['TTMn_syn_pre_loc'])._ref_v, 'vgap', self.GF_TTMn_gap)",
                "The GF axon voltage is bound to the gap junction's vgap.",
            ),
            _mod_equation(
                _GFPN_FILE, 171, "g_assignment", "assignment",
                "        self.GF_TTMn_gap.g = params['g_gap']",
                "The declared g_gap is assigned in NANOSIEMENS to the GF->TTMn "
                "gap junction.",
            ),
            _mod_equation(
                _GFPN_FILE, 175, "g_assignment_second_gap", "assignment",
                "        self.GF_PSI_gap.g = params['g_gap']",
                "The same declared g_gap is assigned to the GF->PSI gap "
                "junction.",
            ),
        ),
        solve_method=SOLVE_METHOD_NONE,
        declares_celsius=False,
        temperature_dependence=TEMPERATURE_NONE_CELSIUS_ABSENT,
        instantiated_in=("TTMn_med", "PSI"),
        instantiation_source_lines=(169, 173),
        instantiation_statement=(
            "        self.GF_TTMn_gap = "
            "neuron.h.gap2(self.TTMn_med(params['TTMn_syn_post_loc']))"
        ),
        computational_status=STATUS_RETRIEVED,
        live_solver_eligible=False,
        limitations=(
            "Gap junction point process of the published model, recorded "
            "verbatim. It is a POINT PROCESS with no state variables and no "
            "gating, and it is NOT a membrane conductance density: it is "
            "instantiated in wire_cells() rather than __init__(), and it "
            "carries a units conflict with the 3.0D-7E gap-junction record "
            "that is recorded and NOT resolved here. " + _NOT_LIVE + " "
            + _NO_TEMPERATURE_ABSENT
        ),
    )


def _pas() -> ExtractedMechanism:
    """The model's use of the built-in 'pas' mechanism.

    There is no channels/pas.mod in ModelDB 245415, so there is no .mod text to
    extract and no leak equation, gate or default to record. What the model
    source DOES state is the set of instances and the two values it assigns to
    them, and those link to the 3.0D-7E passive evidence records rather than
    defining new numbers.
    """
    return ExtractedMechanism(
        name="pas",
        kind=KIND_DENSITY_CHANNEL,
        source_file=_GFPN_FILE,
        source_url=_url(_GFPN_FILE),
        header_comment=(),
        states=(),
        activation_variables=(),
        inactivation_variables=(),
        quantities=(
            _instance_quantity(
                "pas", _GFPN_FILE, 56, "gleak", 30e-6, "S/cm2",
                "                 'gleak': 30e-6,",
                canonical_value=0.03,
                canonical_unit=CANONICAL_DENSITY_UNIT,
                linked_registry="passive_electrical_registry",
                linked_record="leak_conductance_density",
                linkage_note=(
                    "30e-6 S/cm2 is 0.03 mS/cm2, the value already held by the "
                    "3.0D-7E record 'leak_conductance_density'. This registry "
                    "links to that record and does not define a second numeric "
                    "value for it."
                ),
                note=(
                    "Declared in gfpn.py and assigned as cell.g_pas on lines "
                    "131 and 139. It is a PASSIVE quantity; the active layer "
                    "does not use it."
                ),
            ),
            _instance_quantity(
                "pas", _GFPN_FILE, 57, "Eleak", -85.0, "mV",
                "                 'Eleak': -85.0,",
                linked_registry="passive_electrical_registry",
                linked_record="leak_reversal_potential",
                linkage_note=(
                    "Already held by the 3.0D-7E record "
                    "'leak_reversal_potential'. This registry links to that "
                    "record and does not define a second numeric value for it."
                ),
                note=(
                    "Declared in gfpn.py and assigned as cell.e_pas on lines "
                    "130 and 138. It is a PASSIVE quantity; the active layer "
                    "does not use it."
                ),
            ),
        ),
        equations=(),
        solve_method=SOLVE_METHOD_NONE,
        declares_celsius=False,
        temperature_dependence=TEMPERATURE_UNDETERMINED_NO_SOURCE,
        instantiated_in=(
            "DLMn", "DLMn_pas", "GF", "PSI", "PSI_pas", "TTMn",
            "TTMn_lat", "TTMn_med",
        ),
        instantiation_source_lines=(129, 137),
        instantiation_statement="            cell.insert('pas')",
        computational_status=STATUS_INSTANCE_VALUES_ONLY,
        live_solver_eligible=False,
        limitations=(
            "'pas' is a BUILT-IN NEURON mechanism. ModelDB 245415 contains NO "
            "channels/pas.mod, so this record carries ONLY the model instance "
            "values stated in gfpn.py. No leak equation, no leak conductance "
            "default, no gate and no mechanism source line is transcribed, "
            "because none exists in this model. It is a PASSIVE mechanism and "
            "is outside the scope of active-channel extraction; its two values "
            "are recorded solely to LINK them to the 3.0D-7E passive evidence "
            "records that already hold them. " + _TEMPERATURE_UNDETERMINED
            + " " + _NOT_LIVE
        ),
    )


def _unretrieved() -> Tuple[UnretrievedSource, ...]:
    return (
        UnretrievedSource(
            name="Exp2Syn",
            kind="point_process",
            computational_status=STATUS_UNRETRIEVED,
            reason=(
                "ModelDB 245415 contains NO Exp2Syn.mod. 'Exp2Syn' is a "
                "BUILT-IN NEURON point process used for the model's chemical "
                "synapses, so there is no source text in this model to "
                "extract."
            ),
            scope_note=(
                "Instantiated at gfpn.py lines 84, 100 and 117. It is a "
                "CHEMICAL SYNAPSE mechanism, not an active membrane channel, "
                "and it is outside the scope of active-channel extraction. "
                "No synaptic equation, no tau1/tau2 dynamics and no reversal "
                "potential is invented or transcribed here."
            ),
        ),
        UnretrievedSource(
            name="Para",
            kind="named_channel_without_source_mechanism",
            computational_status=STATUS_UNRETRIEVED,
            reason=(
                "No mechanism named 'Para' exists in the ModelDB 245415 "
                "channels directory. The model implements its sodium "
                "conductance with the generic mechanisms 'nat' and 'nap'."
            ),
            scope_note=(
                "3.0D-7S records 'Para' as a QUALITATIVE GF channel identity "
                "from Kadas et al. 2019, with no number. The absence of a "
                "source mechanism is recorded so that the identity evidence is "
                "NOT silently replaced by the kinetics of 'nat'. No Para "
                "kinetic parameter is created here."
            ),
        ),
        UnretrievedSource(
            name="Shaker",
            kind="named_channel_without_source_mechanism",
            computational_status=STATUS_UNRETRIEVED,
            reason=(
                "No mechanism named 'Shaker' exists in the ModelDB 245415 "
                "channels directory. The model implements its potassium "
                "conductance with the generic mechanism 'k'."
            ),
            scope_note=(
                "3.0D-7S records 'Shaker' as a QUALITATIVE GF channel identity "
                "from Kadas et al. 2019, with no number. Its absence here is "
                "recorded so that the identity evidence is NOT silently "
                "replaced by the kinetics of 'k'. No Shaker kinetic parameter "
                "is created here."
            ),
        ),
        UnretrievedSource(
            name="DmCa1D",
            kind="named_channel_without_source_mechanism",
            computational_status=STATUS_UNRETRIEVED,
            reason=(
                "No mechanism named 'DmCa1D' exists in the ModelDB 245415 "
                "channels directory, and no calcium mechanism of any name "
                "exists there."
            ),
            scope_note=(
                "3.0D-7S records 'DmCa1D' as a QUALITATIVE GF channel identity "
                "from Kadas et al. 2019, with no number. The model contains NO "
                "calcium current at all. No calcium conductance density, no "
                "calcium reversal potential and no calcium-dependent kinetics "
                "is created here."
            ),
        ),
        UnretrievedSource(
            name="Slowpoke",
            kind="named_channel_without_source_mechanism",
            computational_status=STATUS_UNRETRIEVED,
            reason=(
                "No mechanism named 'Slowpoke' exists in the ModelDB 245415 "
                "channels directory, and no calcium-activated mechanism of any "
                "name exists there."
            ),
            scope_note=(
                "3.0D-7S records 'Slowpoke' as a QUALITATIVE GF channel "
                "identity from Kadas et al. 2019, with no number. The model "
                "contains no calcium signal for such a channel to read, so no "
                "BK conductance, no BK reversal potential and no calcium "
                "coupling is created here."
            ),
        ),
    )


def get_active_mechanism_registry() -> ActiveMechanismRegistry:
    """Return the verbatim active mechanism source registry.

    DATA ONLY. Every mechanism is observational: nothing is implemented,
    nothing is connected, no gating variable exists, no compartment is
    populated, the passive backend is unchanged and no record is eligible for
    the live solver.
    """
    return ActiveMechanismRegistry(
        name="modeldb_245415_active_mechanism_sources",
        source=(
            "Verbatim source records of the active mechanisms of ModelDB "
            "245415 (Augustin et al. 2019). Source text, line numbers, source "
            "units and inline annotations are preserved exactly as retrieved "
            "from the compiled NEURON mechanism files and from gfpn.py. ALL "
            "records are observational: NONE is eligible for the live solver "
            "and nothing is activated, implemented or translated."
        ),
        model_id=MODELDB_MODEL_ID,
        model_citation=MODELDB_MODEL_CITATION,
        model_temperature_c=MODEL_TEMPERATURE_C,
        mechanisms=(_nat(), _nap(), _k(), _gap2(), _pas()),
        unretrieved=_unretrieved(),
        scope_note=(
            "The published GFS model implements its active conductance with "
            "THREE generic Hodgkin-Huxley-style mechanisms (nat, nap, k) and "
            "ONE nonspecific gap-junction point process (gap2). It contains NO "
            "mechanism named Para, Shaker, DmCa1D or Slowpoke, and NO calcium "
            "current of any kind. The qualitative GF channel identities of "
            "3.0D-7S are therefore NOT implemented by these mechanisms, and "
            "this checkpoint does not treat them as if they were. nap and k "
            "have no inactivation gate and a constant 1 ms activation time "
            "constant, so they are steady-state conductance models in the "
            "source and NOT full transient descriptions. The three retrieved "
            "density mechanisms nat, nap and k each DECLARE celsius and none "
            "of them uses it, gap2 does not declare celsius at all, and pas has "
            "no source file in this model, so NO temperature dependence and NO "
            "Q10 exists in this source. Three verbatim source conflicts "
            "are RECORDED AND NOT RESOLVED: the 'gbar = 0' annotation "
            "'0.12 mho/cm2' that does not describe the assigned value; the "
            "DERIVATIVE header comment 'm, h, and n' that does not match the "
            "STATE blocks; and the factor-1000 units conflict between "
            "gfpn.py's g_gap in nS and the 3.0D-7E gap-junction record in uS. "
            "This checkpoint extracts source text. It establishes NO "
            "Hodgkin-Huxley implementation, NO validated Na/K or Ca kinetics, "
            "NO complete channel distribution, NO action-potential "
            "reproduction and NO live-solver eligibility."
        ),
    )
