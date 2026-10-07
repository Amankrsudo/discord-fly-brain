"""Presentation-only summary of verified Fly Brain 3.0 research outputs.

This is the single source of truth for the Fly Brain 3.0 biological-model
research summary. It is rendered verbatim as a static panel on the
dashboard image whenever the 3.0B layer is enabled; it is never a live
simulation output and never an experimental measurement.
"""

FLY_BRAIN_3_STATUS = """BIOLOGICAL CIRCUIT
GF → PSI → MN5/DLMn → MOTOR OUTPUT
ANATOMY VERIFIED
PSI→MN5 contacts: 43 (left 17, right 26)
Contact→node mapping: 43/43 verified
LITERATURE
MN5 resting: -67.8 mV · Somatic EPSP: 4.71 mV
MODEL-DERIVED
Sensitivity rows: 15,528 · g_PSI C-01 A: 4.49 nS · C-01 B: 10.16 nS
UNRESOLVED / ASSUMPTION
C-01 capacitance: 43 vs ~127 pF · Contact→soma path: unresolved
Native Dα7 conductance: model-derived · Erev: model assumption
MODEL OUTPUTS ≠ EXPERIMENTAL MEASUREMENTS"""
