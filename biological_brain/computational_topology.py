"""Source-backed computational section connectivity (3.0D-7P).

The Augustin et al. 2019 ModelDB implementation constructs each modelled
neuron as one to three unbranched cylindrical computational sections, each
divided into 51 isopotential segments, and wires those sections together with
NEURON's ``child.connect(parent, 0, 0)`` statement. The relevant source lines
in ``gfpn.py`` of ModelDBRepository/245415 are:

    TTMn_med.connect(TTMn, 0, 0)      line 86
    TTMn_lat.connect(TTMn, 0, 0)      line 91
    PSI_pas.connect(PSI, 0, 0)        line 105
    DLMn_pas.connect(DLMn, 0, 0)      line 121

Those four statements are the computational section topology reproduced here.

Why this layer exists
---------------------
The source-backed ANATOMICAL topology puts every section behind a soma, and
all four somata are excluded from the electrical representation because the
published simplified model gives no computational soma geometry (3.0D-7I,
3.0D-7L). Deriving the electrical parent purely from the anatomical parent
therefore turns every GFS section into an electrically disconnected root,
which is NOT what the published computational abstraction does.

This module keeps the two concerns apart:

- the ANATOMICAL topology (``Compartment.parent_id``, ``neighbor_ids``) is
  untouched source-backed morphology and is never rewritten;
- the COMPUTATIONAL topology declared here determines which represented
  sections are electrically chained, using the published proximal-to-proximal
  section connection convention.

An excluded soma is therefore neither given geometry nor used as an axial
path: sections that the published abstraction directly connects are chained
directly, and no connection is invented across a soma.

Connection endpoints (3.0D-7Q)
-------------------------------
The source statement is ``child.connect(parent, 0, 0)``: the child's proximal
end (x=0) joins the parent's proximal end (x=0). Under numerical subdivision
this is preserved exactly: the section connection attaches at CHILD SEGMENT 0
and PARENT SEGMENT 0, and is never relocated to the child's distal end. The
internal chain of an N-segment section runs segment 0 -> 1 -> ... -> N-1.

Scope
-----
An axial connection between two computational sections is the ordinary axial
cable connection of the selected computational abstraction. It is NOT a
biological gap junction and NOT a chemical synapse. Circuit-level mechanisms
(GF->TTMn, GF->PSI, PSI->DLMn) are explicitly out of scope for 3.0D-7P.

This module is DATA ONLY. It assigns no biological parameter, computes no
resistance, modifies no geometry, and alters no anatomical topology.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .provenance import ParameterProvenance, ProvenanceRecord


MODELDB_REPOSITORY = "ModelDBRepository/245415"
AUGUSTIN_MODELDB_FILE = "gfpn.py"

# NEURON's child.connect(parent, 0, 0): the child's proximal end (0) joins the
# parent's proximal end (0). The electrical chain runs parent -> child.
DIRECTION_PROXIMAL_TO_PROXIMAL = "child_proximal_end_to_parent_proximal_end"

# 3.0D-7Q: the exact endpoints the source specifies. Under subdivision the
# section connection attaches at CHILD SEGMENT 0 and PARENT SEGMENT 0; it is
# never relocated to the child's distal end.
CHILD_ENDPOINT_X = 0.0
PARENT_ENDPOINT_X = 0.0
CHILD_ENDPOINT_SEGMENT_INDEX = 0
PARENT_ENDPOINT_SEGMENT_INDEX = 0

TOPOLOGY_AUGUSTIN_2019_GFS = "augustin_2019_gfs_computational_sections"

_SCOPE_NOTE = (
    "Computational section connectivity reproduced from the Augustin et al. "
    "2019 ModelDB abstraction. This is a COMPUTATIONAL TOPOLOGY record, not a "
    "biological claim: it is NOT DIRECTLY_MEASURED, NOT "
    "EXPERIMENTALLY_CONSTRAINED, and NOT ESTIMATED biological morphology. It "
    "does NOT assert anything about soma geometry, does not create a "
    "gap junction, and does not create a chemical synapse."
)

_COMPUTATIONAL_SOURCE = (
    "Augustin et al. 2019 (eLife, PMC6469880) ModelDB implementation, "
    f"{MODELDB_REPOSITORY}, {AUGUSTIN_MODELDB_FILE}. " + _SCOPE_NOTE
)


@dataclass(frozen=True)
class ComputationalSectionConnection:
    """One source-backed intra-neuron computational section connection.

    Records which sections the published computational abstraction joins, the
    source statement it came from, and the connection direction. It supplies
    no value: the axial resistance is derived later from the child's geometry
    and the authorized profile.
    """

    child_section_id: str
    parent_section_id: str
    source_model_id: str
    source_file: str
    source_line: int
    source_statement: str
    direction: str
    derivation: str
    provenance: ProvenanceRecord

    def __post_init__(self) -> None:
        if self.child_section_id == self.parent_section_id:
            raise ValueError(
                f"Computational section connection cannot be a self "
                f"connection on '{self.child_section_id}'"
            )

    def source_text(self) -> str:
        return (
            f"{self.source_model_id} {self.source_file} line "
            f"{self.source_line}: {self.source_statement}"
        )


@dataclass(frozen=True)
class ComputationalTopology:
    """A declared, source-backed computational section topology.

    ``connections`` is ordered deterministically by (parent, child). The
    topology is authoritative only for the sections it names; a model that
    declares none falls back to its anatomical parentage, so models without a
    declared computational abstraction are unaffected.
    """

    name: str
    source: str
    connections: Tuple[ComputationalSectionConnection, ...]
    computational_roots: Tuple[str, ...]
    scope_note: str

    def parent_of(self, section_id: str) -> Optional[str]:
        for connection in self.connections:
            if connection.child_section_id == section_id:
                return connection.parent_section_id
        return None

    def connection_for_child(
        self, section_id: str
    ) -> Optional[ComputationalSectionConnection]:
        for connection in self.connections:
            if connection.child_section_id == section_id:
                return connection
        return None

    def children_of(self, section_id: str) -> Tuple[str, ...]:
        return tuple(
            c.child_section_id
            for c in self.connections
            if c.parent_section_id == section_id
        )

    def connected_section_ids(self) -> Tuple[str, ...]:
        ids = {c.child_section_id for c in self.connections}
        ids.update(c.parent_section_id for c in self.connections)
        return tuple(sorted(ids))

    def connections_within(
        self, section_ids
    ) -> Tuple[ComputationalSectionConnection, ...]:
        """Connections whose BOTH endpoints exist in the given section set.

        A GFS model holds one neuron's sections, so the full table is filtered
        down to that neuron's own connections. Deterministic order preserved.
        """
        available = set(section_ids)
        return tuple(
            c for c in self.connections
            if c.child_section_id in available and c.parent_section_id in available
        )


def _augustin_connection(
    child: str, parent: str, line: int, statement: str
) -> ComputationalSectionConnection:
    return ComputationalSectionConnection(
        child_section_id=child,
        parent_section_id=parent,
        source_model_id=MODELDB_REPOSITORY,
        source_file=AUGUSTIN_MODELDB_FILE,
        source_line=line,
        source_statement=statement,
        direction=DIRECTION_PROXIMAL_TO_PROXIMAL,
        derivation=(
            f"The published Augustin 2019 ModelDB computational abstraction "
            f"wires '{child}' to '{parent}' with NEURON's "
            f"'{statement}', connecting the child's proximal end "
            f"(x={CHILD_ENDPOINT_X:.0f}) to the parent's proximal end "
            f"(x={PARENT_ENDPOINT_X:.0f}). The electrical chain therefore runs "
            f"'{parent}' -> '{child}'. Computational section connectivity is "
            f"preserved under numerical subdivision: with N segments per "
            f"section the connection attaches at CHILD SEGMENT "
            f"{CHILD_ENDPOINT_SEGMENT_INDEX} and PARENT SEGMENT "
            f"{PARENT_ENDPOINT_SEGMENT_INDEX}, exactly as the source states, "
            f"and is never relocated to the child's distal end. This reproduces "
            f"the computational section topology of the published abstraction "
            f"and asserts nothing about the geometry of the intervening soma, "
            f"which remains excluded from the electrical representation."
        ),
        provenance=ProvenanceRecord(ParameterProvenance.UNKNOWN, _COMPUTATIONAL_SOURCE),
    )


# The four, and only four, intra-neuron computational section connections
# reproduced from the published source. Deterministic order: by parent, then
# child, matching the source statement order.
AUGUSTIN_2019_GFS_COMPUTATIONAL_CONNECTIONS = (
    _augustin_connection(
        "TTMn_medial_dendrite", "TTMn_axon", 86, "TTMn_med.connect(TTMn, 0, 0)"
    ),
    _augustin_connection(
        "TTMn_lateral_dendrite", "TTMn_axon", 91, "TTMn_lat.connect(TTMn, 0, 0)"
    ),
    _augustin_connection("PSI_dendrite", "PSI_axon", 105, "PSI_pas.connect(PSI, 0, 0)"),
    _augustin_connection("DLMn_dendrite", "DLMn_axon", 121, "DLMn_pas.connect(DLMn, 0, 0)"),
)

# GF_axon is the only GF section in the published abstraction, so it is the
# only GF computational root. GF_medial_dendrite is excluded from the selected
# computational representation (3.0D-7N) and GF_soma is excluded for
# insufficient geometry (3.0D-7I); neither is a computational section here.
AUGUSTIN_2019_GFS_COMPUTATIONAL_ROOTS = ("GF_axon",)

AUGUSTIN_2019_GFS_COMPUTATIONAL_TOPOLOGY = ComputationalTopology(
    name=TOPOLOGY_AUGUSTIN_2019_GFS,
    source=_COMPUTATIONAL_SOURCE,
    connections=AUGUSTIN_2019_GFS_COMPUTATIONAL_CONNECTIONS,
    computational_roots=AUGUSTIN_2019_GFS_COMPUTATIONAL_ROOTS,
    scope_note=_SCOPE_NOTE,
)


def get_computational_topology(model) -> Optional[ComputationalTopology]:
    """Return the computational topology a model declares, if any.

    Absence (None) means no computational abstraction has been declared, and
    electrical parentage falls back to the anatomical parentage. The topology
    is never inferred.
    """
    return getattr(model, "computational_topology", None)
