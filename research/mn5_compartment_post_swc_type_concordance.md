# MN5 compartment_post vs SWC Type Concordance

## 1. Objective

Describe annotation concordance between the official MaleCNS v1.0
`compartment_post` labels and the numeric SWC Type code at the projected
postsynaptic node for the 43 verified PSI→MN5 contacts. This is not a biological
compartment validation.

## 2. Data and provenance

- Official annotation export: `research/artifacts/malecns_compartment_post_psi_mn5.csv`.
- Annotation layer: `gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed`; relationship: `body_post`.
- Contact coordinates are retained in the source's raw 8 nm coordinates and
  converted to nanometres only for geometric projection.
- Official SWCs: `em_801970.swc` and `em_801295.swc` from the MaleCNS v1.0
  `skeletons-malecns/skeletons-swc/` release.
- The composite `contact_id` preserves the source export's pair-specific
  `contact_index`; it is not represented as an independent official annotation
  UUID.

SWC Type is preserved as a numeric format/annotation code. Its biological semantics are undocumented by MaleCNS. The compartment_post string is preserved as a separate official dataset annotation. Concordance does not establish biological compartment semantics, biological localization, voltage transfer, or electrical properties.

## 3. Matching/projection method

Each contact is retained with its pre/post body IDs, exact official
`compartment_post` value, source contact index, and raw postsynaptic coordinate.
The coordinate is projected to the nearest SWC segment with the same point-to-
segment calculation used by `malecns_contact_path.project_contacts_to_swc`.
The projected point is associated with the nearer segment endpoint, matching
that method's node selection rule. All segments tied within
`1e-09 nm` are retained. A tie is flagged even when the endpoint
node is the same. No maximum-distance cutoff is imposed; geometric offsets are
reported rather than silently filtered.

## 4. PSI→MN5 concordance

| MN5 body | Contacts | Official label counts | Projected SWC Type-code counts | SWC nodes | SWC SHA-256 |
|---:|---:|---|---|---:|---|
| 801970 | 17 | {'axon': 17} | code 0: 17 | 8520 | `c4297590219f2d9bbb5038fd190c4c9d38d4a4ecb66dc35cf3f0d915b313f1d2` |
| 801295 | 26 | {'axon': 26} | code 0: 26 | 7991 | `b2c8e23c6b921f2548d239d83d6887be4e69fd919bd6e02ee41b00ad377d3e69` |

Overall contingency table (matched nodes only):

| `compartment_post` literal | SWC Type code | Contacts |
|---|---:|---:|
| axon | 0 | 43 |

## 5. Comparison contacts

No additional MN5 input contacts are included. The locally available official
annotation export contains only the 43 verified PSI→MN5 pairings. Although the
official layer supports a broader `body_post` relationship, the corresponding
per-contact records were not available in the local export for this analysis;
no alternative source was substituted.

## 6. Unmatched/ambiguous records

- Total PSI→MN5 contacts: 43.
- Matched to one projected node: 43.
- Unmatched: 0.
- Nearest-segment ties: 1.
- Candidate-node ambiguities: 0.
- Projection statuses: `{'MATCHED': 42, 'MATCHED_SEGMENT_TIE_SAME_NODE': 1}`.

Tie details:
- `802401->801970:12`: status `MATCHED_SEGMENT_TIE_SAME_NODE`, node `151`, candidate nodes `151`, candidate Type codes `0`, tied segments `150-151;151-152`.

Every contact is retained in the CSV, including flagged ties and any unmatched
case. The projection distance is the geometric distance to the reconstructed
centerline, not an electrical or physiological distance.

## 7. Interpretation

The table reports annotation concordance only: it places each literal
`compartment_post` annotation alongside the numeric SWC Type code selected by a
stated geometric projection rule. No biological interpretation is assigned to
either field.

## 8. Limitations

- SWC Type semantics are undocumented by MaleCNS.
- Concordance does not establish biological compartment semantics.
- Projection uncertainty remains; nearest-segment ties and geometric offsets
  are explicitly recorded.
- This does not establish voltage-transfer properties.
- This does not reopen the MN5 spatial-transfer gate.

## 9. Gate status

PSI→MN5 spatial voltage transfer: **NOT AUTHORIZED**

Dα7 biological conductance: **NOT AUTHORIZED**
