**Table R-3.** Model capability surface and authorization gates. Capabilities are enforced by `model_framework.py` and `reduced_mn5.py` [C-602, C-401, C-501].

| Capability | Status | Enforced by | Gate |
|---|---|---|---|
| Anatomy (17/26 contacts, compartment labels, mesh geometry) | AVAILABLE | `malecns_ingest.py` | — |
| Reduced single-compartment MN5 (3 native inputs, no leak) | PARTIAL | `reduced_mn5.py:ReducedMN5Simulator` | — |
| PSI→MN5 synaptic physiology | BLOCKED | `SynapticInterface` (raises) | B |
| PSI→MN5 spatial voltage transfer | BLOCKED | `require_spatial_transfer` / `require_biological_transfer_authorization` | **Gate A** |
| Dα7 receptor conductance | BLOCKED | `Dalpha7Interface.conductance` / `require_dalpha7_gate` | **Gate B** |
| GFS electrical coupling | PARTIAL | `GFSInterface` (no native conductance inserted) | — |

**Frozen parameter inventory (`model_input_freeze.csv`, 108 parameters)** [C-301]:

| Bucket | Count |
|---|---|
| SAFE to use now | 40 |
| Assumption-only (usable as explicit assumptions) | 31 |
| Blocked (never used) | 37 |
| Unresolved conflicts preserved | 15 |

**Blocked quantities never inserted** (examples): MN5 Ra (no Drosophila measurement), MN5 Rm, PSI→MN5 synaptic conductance, native Dα7 conductance, contact→soma electrotonic distance [C-201, C-303, C-401, C-501].