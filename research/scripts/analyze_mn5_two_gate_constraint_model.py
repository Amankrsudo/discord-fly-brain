"""Run the MN5 contact-local and abstract cable sensitivity analyses.

The contact-local analysis uses the audited MaleCNS contact-to-SWC-node
projection. The abstract transfer analysis uses the Augustin et al. GFS
geometry as a model bridge; it does not assign an anatomical soma path to any
MaleCNS contact.

Run:
    python research/scripts/analyze_mn5_two_gate_constraint_model.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import math
import os
import statistics
import sys
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from biological_brain.exploratory_mn5 import (  # noqa: E402
    ExploratoryMN5Model,
    ExploratorySimulationResult,
)
from biological_brain.malecns_ingest import (  # noqa: E402
    SkeletonGeometry,
)

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONTACT_MAP = os.path.join(
    ROOT, "research", "mn5_compartment_post_swc_type_concordance.csv")
OUTPUT_CSV = os.path.join(
    ROOT, "research", "mn5_psi_mn5_final_constraint_model_sensitivity.csv")
EXPECTED_CONTACTS = {801970: 17, 801295: 26}
EXPECTED_PRE = {801970: 802401, 801295: 903327}
EXPECTED_SWC_SHA256 = {
    801970: "c4297590219f2d9bbb5038fd190c4c9d38d4a4ecb66dc35cf3f0d915b313f1d2",
    801295: "b2c8e23c6b921f2548d239d83d6887be4e69fd919bd6e02ee41b00ad377d3e69",
}

# The modeled MN5-equivalent path is an explicit abstraction: the published
# DLMn dendrite (100 um) plus 12.5 um from the proximal end of its axon to the
# PSI input. It is not a path mapped onto a MaleCNS SWC.
GFS_BRIDGE_LENGTH_UM = 100.0 + 12.5
GFS_BRIDGE_DIAMETER_UM = 2.0

PASSIVE_GRID = {
    "axial resistivity": (30.0, 35.4, 90.0, 200.0, 400.0),
    "specific membrane capacitance": (0.6, 1.0, 1.15, 2.6),
    "specific membrane resistance": (6.0, 10.0, 20.0, 26.0),
}
E_SYN_GRID = (-15.0, 0.0, 10.0)
G_PSI_GRID_NS = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)
G_DALPHA7_GRID_NS = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)
E_DALPHA7_GRID_MV = (-15.0, 0.0, 10.0)
LOCAL_CM_GRID = (0.6, 1.15, 2.6)
LOCAL_RM_GRID = (6.0, 10.0, 20.0, 26.0)
DT_MS = 0.01
DURATION_MS = 15.0
TAU_RISE_MS = 0.1
TAU_DECAY_MS = 1.0

CSV_FIELDS = (
    "analysis_id", "contact_id", "contact_index", "pre_body", "post_body",
    "compartment_post", "swc_node_index", "swc_type_code",
    "projection_status", "projection_distance_nm", "node_radius_um",
    "mean_adjacent_segment_um", "capacitance_variant",
    "Ra_ohm_cm", "Cm_spec_uF_cm2", "Rm_kohm_cm2", "E_syn_mV",
    "g_PSI_nS", "E_Dalpha7_mV", "g_Dalpha7_effective_nS",
    "local_peak_mV", "somatic_peak_mV", "local_to_somatic_peak_ratio",
    "somatic_time_to_peak_ms", "delta_local_vs_no_Dalpha7_mV",
    "delta_somatic_vs_no_Dalpha7_mV", "threshold_crossing",
    "classification", "output_provenance", "interpretation",
)


@dataclass(frozen=True)
class ContactGeometry:
    contact_id: str
    contact_index: int
    pre_body: int
    post_body: int
    compartment_post: str
    node_index: int
    swc_type_code: int
    projection_status: str
    projection_distance_nm: float
    node_radius_um: float
    mean_adjacent_segment_um: float


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_contact_geometry(
        contact_map_path: str = CONTACT_MAP,
        swc_paths: Mapping[int, str] | None = None,
        ) -> List[ContactGeometry]:
    """Load audited contact mappings and attach geometry without Type semantics."""
    if swc_paths is None:
        swc_paths = {
            body: os.path.join(tempfile.gettempdir(), f"em_{body}.swc")
            for body in EXPECTED_CONTACTS
        }
    if set(swc_paths) != set(EXPECTED_CONTACTS):
        raise ValueError(
            f"expected SWCs for {sorted(EXPECTED_CONTACTS)}, "
            f"got {sorted(swc_paths)}")
    skeletons: Dict[int, SkeletonGeometry] = {}
    for body, path in swc_paths.items():
        if not os.path.isfile(path):
            raise FileNotFoundError(f"required cached SWC not found: {path}")
        if _sha256(path) != EXPECTED_SWC_SHA256[body]:
            raise ValueError(f"unexpected SWC content for MN5 body {body}")
        skeletons[body] = SkeletonGeometry.from_swc(path, body_id=body)

    with open(contact_map_path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    counts: Dict[int, int] = {}
    seen = set()
    output = []
    for row in rows:
        pre, post = int(row["pre_body"]), int(row["post_body"])
        index = int(row["contact_index"])
        if post not in EXPECTED_CONTACTS or EXPECTED_PRE[post] != pre:
            raise ValueError(f"unexpected contact pairing {pre}->{post}")
        key = (pre, post, index)
        contact_id = f"{pre}->{post}:{index}"
        if key in seen or row["contact_id"] != contact_id:
            raise ValueError(f"duplicate or mismatched contact identity: {key}")
        seen.add(key)
        counts[post] = counts.get(post, 0) + 1
        status = row["projection_status"]
        if status not in ("MATCHED", "MATCHED_SEGMENT_TIE_SAME_NODE"):
            raise ValueError(f"unresolved audited node projection: {contact_id}")
        node_index = int(row["swc_node_index"])
        skeleton = skeletons[post]
        table = skeleton.by_index()
        node = table.get(node_index)
        if node is None:
            raise ValueError(f"{contact_id}: projected node {node_index} missing")
        adjacent = []
        for start, end in skeleton.segments():
            if start.index == node_index:
                adjacent.append(skeleton.to_um(skeleton.distance(start, end)))
            elif end.index == node_index:
                adjacent.append(skeleton.to_um(skeleton.distance(start, end)))
        if not adjacent:
            raise ValueError(f"{contact_id}: projected node has no SWC edge")
        output.append(ContactGeometry(
            contact_id=contact_id,
            contact_index=index,
            pre_body=pre,
            post_body=post,
            compartment_post=row["compartment_post"],
            node_index=node_index,
            swc_type_code=int(row["swc_type_code"]),
            projection_status=status,
            projection_distance_nm=float(row["projection_distance_nm"]),
            node_radius_um=skeleton.to_um(node.radius),
            mean_adjacent_segment_um=statistics.fmean(adjacent),
        ))
    if counts != EXPECTED_CONTACTS or len(seen) != 43:
        raise ValueError(
            f"expected 17/26 unique contact records; got {counts}")
    return output


def contact_local_peak(
        contact: ContactGeometry,
        g_psi_ns: float,
        e_syn_mv: float,
        cm_spec_uf_cm2: float,
        rm_kohm_cm2: float,
        v_rest_mv: float = -67.8,
        dt_ms: float = DT_MS,
        duration_ms: float = DURATION_MS,
        tau_rise_ms: float = TAU_RISE_MS,
        tau_decay_ms: float = TAU_DECAY_MS,
        ) -> Tuple[float, float]:
    """Single local patch response; no axial or soma path is represented."""
    if min(g_psi_ns, cm_spec_uf_cm2, rm_kohm_cm2, dt_ms,
           duration_ms, tau_rise_ms, tau_decay_ms) <= 0:
        raise ValueError("conductance, passive values, and times must be positive")
    if tau_rise_ms >= tau_decay_ms:
        raise ValueError("rise time must be shorter than decay time")
    area_cm2 = (
        2.0 * math.pi * contact.node_radius_um
        * contact.mean_adjacent_segment_um * 1e-8)
    capacitance_pf = area_cm2 * cm_spec_uf_cm2 * 1e6
    leak_ns = area_cm2 * 1e6 / rm_kohm_cm2
    n_steps = int(round(duration_ms / dt_ms))
    g_course = ExploratoryMN5Model._double_exponential_course(
        n_steps, dt_ms, g_psi_ns, tau_rise_ms, tau_decay_ms)
    t_peak = 0.0
    peak = 0.0
    voltage = v_rest_mv
    for i, g_syn in enumerate(g_course):
        total = leak_ns + g_syn
        steady = (leak_ns * v_rest_mv + g_syn * e_syn_mv) / total
        decay = math.exp(-total * dt_ms / capacitance_pf)
        voltage = steady + (voltage - steady) * decay
        depolarization = voltage - v_rest_mv
        if depolarization > peak:
            peak = depolarization
            t_peak = (i + 1) * dt_ms
    return peak, t_peak


def _bridge_overrides(ra: float, cm: float, rm: float,
                      e_syn: float, g_psi: float) -> Dict[str, float]:
    return {
        "process length (soma to PSI-contact region)": GFS_BRIDGE_LENGTH_UM,
        "process diameter": GFS_BRIDGE_DIAMETER_UM,
        "axial resistivity": ra,
        "specific membrane capacitance": cm,
        "specific membrane resistance": rm,
        "cholinergic reversal potential (exploratory)": e_syn,
        "PSI synaptic peak conductance": g_psi,
        "PSI synaptic rise time constant": TAU_RISE_MS,
        "PSI synaptic decay time constant": TAU_DECAY_MS,
    }


def simulate_abstract_transfer(
        capacitance_variant: str,
        ra: float = 90.0,
        cm: float = 1.15,
        rm: float = 6.0,
        e_syn: float = 0.0,
        g_psi: float = 1.0,
        dalpha7_enabled: bool = False,
        e_dalpha7: float = 0.0,
        g_dalpha7_effective: float = 0.0,
        ) -> ExploratorySimulationResult:
    """Run the existing two-compartment model with explicit GFS bridge geometry."""
    model = ExploratoryMN5Model(
        capacitance_variant=capacitance_variant,
        dalpha7_enabled=dalpha7_enabled,
    )
    overrides = _bridge_overrides(ra, cm, rm, e_syn, g_psi)
    overrides["Dα7 reversal potential (exploratory)"] = e_dalpha7
    overrides["Dα7 maximal conductance"] = g_dalpha7_effective
    return model.simulate(overrides=overrides, dt_ms=DT_MS,
                          duration_ms=DURATION_MS)


def fit_g_psi_to_target(
        capacitance_variant: str,
        ra: float,
        cm: float,
        rm: float,
        e_syn: float,
        target_mv: float = 4.71,
        ) -> Tuple[float | None, str]:
    """Fit only within the existing 0.01--1000 nS exploratory g_PSI range."""
    lower, upper = 0.01, 1000.0
    low_peak = simulate_abstract_transfer(
        capacitance_variant, ra, cm, rm, e_syn, lower
    ).somatic_peak_depolarization_mv
    high_peak = simulate_abstract_transfer(
        capacitance_variant, ra, cm, rm, e_syn, upper
    ).somatic_peak_depolarization_mv
    if low_peak > target_mv:
        return None, "OUTSIDE CURRENT EXPLORATORY RANGE (below minimum)"
    if high_peak < target_mv:
        return None, "OUTSIDE CURRENT EXPLORATORY RANGE (above maximum)"

    low_log, high_log = math.log10(lower), math.log10(upper)
    for _ in range(24):
        middle_log = (low_log + high_log) / 2.0
        peak = simulate_abstract_transfer(
            capacitance_variant, ra, cm, rm, e_syn,
            10.0 ** middle_log,
        ).somatic_peak_depolarization_mv
        if peak < target_mv:
            low_log = middle_log
        else:
            high_log = middle_log
    fitted = 10.0 ** ((low_log + high_log) / 2.0)
    central_low = lower * (upper / lower) ** (1.0 / 3.0)
    central_high = lower * (upper / lower) ** (2.0 / 3.0)
    if central_low <= fitted <= central_high:
        return fitted, "CENTRAL"
    return fitted, "EDGE"


def _base_row(analysis_id: str, interpretation: str) -> Dict[str, object]:
    row = {field: "" for field in CSV_FIELDS}
    row["analysis_id"] = analysis_id
    row["output_provenance"] = "model_derived_estimate"
    row["interpretation"] = interpretation
    return row


def run_analysis(contact_map_path: str = CONTACT_MAP,
                 swc_paths: Mapping[int, str] | None = None,
                 ) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    contacts = load_contact_geometry(contact_map_path, swc_paths)
    rows: List[Dict[str, object]] = []

    local_results = []
    for contact in contacts:
        for cm, rm, e_syn, g_psi in itertools.product(
                LOCAL_CM_GRID, LOCAL_RM_GRID, E_SYN_GRID, G_PSI_GRID_NS):
            peak, peak_time = contact_local_peak(
                contact, g_psi, e_syn, cm, rm)
            row = _base_row(
                "CONTACT_LOCAL",
                "Per-contact one-patch response from SWC radius and "
                "mean adjacent edge length; no axial or soma path. SWC "
                "Type is preserved literally and not biologically interpreted.")
            row.update({
                "contact_id": contact.contact_id,
                "contact_index": contact.contact_index,
                "pre_body": contact.pre_body,
                "post_body": contact.post_body,
                "compartment_post": contact.compartment_post,
                "swc_node_index": contact.node_index,
                "swc_type_code": contact.swc_type_code,
                "projection_status": contact.projection_status,
                "projection_distance_nm": contact.projection_distance_nm,
                "node_radius_um": contact.node_radius_um,
                "mean_adjacent_segment_um":
                    contact.mean_adjacent_segment_um,
                "Cm_spec_uF_cm2": cm,
                "Rm_kohm_cm2": rm,
                "E_syn_mV": e_syn,
                "g_PSI_nS": g_psi,
                "local_peak_mV": peak,
                "somatic_time_to_peak_ms": peak_time,
            })
            rows.append(row)
            local_results.append((contact, cm, rm, e_syn, g_psi, peak))

    abstract_results = []
    for variant in ("A", "B"):
        for ra, cm, rm, e_syn, g_psi in itertools.product(
                PASSIVE_GRID["axial resistivity"],
                PASSIVE_GRID["specific membrane capacitance"],
                PASSIVE_GRID["specific membrane resistance"],
                E_SYN_GRID, G_PSI_GRID_NS):
            result = simulate_abstract_transfer(
                variant, ra=ra, cm=cm, rm=rm, e_syn=e_syn, g_psi=g_psi)
            row = _base_row(
                "ABSTRACT_SOMATIC_TRANSFER",
                "Uniform-cable abstraction of published GFS DLMn geometry; "
                "not a path mapped from any MaleCNS contact. SWC Type codes "
                "are not used to assign biological compartments.")
            row.update({
                "capacitance_variant": variant,
                "Ra_ohm_cm": ra,
                "Cm_spec_uF_cm2": cm,
                "Rm_kohm_cm2": rm,
                "E_syn_mV": e_syn,
                "g_PSI_nS": g_psi,
                "local_peak_mV":
                    result.local_synaptic_peak_depolarization_mv,
                "somatic_peak_mV":
                    result.somatic_peak_depolarization_mv,
                "local_to_somatic_peak_ratio":
                    result.spatial_attenuation_ratio,
                "somatic_time_to_peak_ms": result.time_to_peak_ms,
                "threshold_crossing": result.threshold_crossing,
            })
            rows.append(row)
            abstract_results.append((variant, ra, cm, rm, e_syn, g_psi,
                                     result))

    dalpha7_results = []
    for variant in ("A", "B"):
        for ra, cm, rm, e_da7, g_da7 in itertools.product(
                PASSIVE_GRID["axial resistivity"],
                PASSIVE_GRID["specific membrane capacitance"],
                PASSIVE_GRID["specific membrane resistance"],
                E_DALPHA7_GRID_MV,
                G_DALPHA7_GRID_NS):
            baseline = simulate_abstract_transfer(
                variant, ra=ra, cm=cm, rm=rm, e_syn=0.0, g_psi=1.0)
            enabled = simulate_abstract_transfer(
                variant, ra=ra, cm=cm, rm=rm, e_syn=0.0, g_psi=1.0,
                dalpha7_enabled=True, e_dalpha7=e_da7,
                g_dalpha7_effective=g_da7)
            row = _base_row(
                "DALPHA7_EFFECTIVE_CONDUCTANCE_SWEEP",
                "g_Dalpha7_effective is a model free parameter; recombinant "
                "channel currents are not converted to native conductance.")
            row.update({
                "capacitance_variant": variant,
                "Ra_ohm_cm": ra,
                "Cm_spec_uF_cm2": cm,
                "Rm_kohm_cm2": rm,
                "E_syn_mV": 0.0,
                "g_PSI_nS": 1.0,
                "E_Dalpha7_mV": e_da7,
                "g_Dalpha7_effective_nS": g_da7,
                "local_peak_mV":
                    enabled.local_synaptic_peak_depolarization_mv,
                "somatic_peak_mV":
                    enabled.somatic_peak_depolarization_mv,
                "local_to_somatic_peak_ratio":
                    enabled.spatial_attenuation_ratio,
                "somatic_time_to_peak_ms": enabled.time_to_peak_ms,
                "delta_local_vs_no_Dalpha7_mV":
                    (enabled.local_synaptic_peak_depolarization_mv
                     - baseline.local_synaptic_peak_depolarization_mv),
                "delta_somatic_vs_no_Dalpha7_mV":
                    (enabled.somatic_peak_depolarization_mv
                     - baseline.somatic_peak_depolarization_mv),
                "threshold_crossing": enabled.threshold_crossing,
            })
            rows.append(row)
            dalpha7_results.append((variant, ra, cm, rm, e_da7, g_da7,
                                    baseline, enabled))

    calibration_results = []
    for variant in ("A", "B"):
        for ra, cm, rm, e_syn in itertools.product(
                PASSIVE_GRID["axial resistivity"],
                PASSIVE_GRID["specific membrane capacitance"],
                PASSIVE_GRID["specific membrane resistance"],
                E_SYN_GRID):
            fitted, classification = fit_g_psi_to_target(
                variant, ra, cm, rm, e_syn)
            row = _base_row(
                "EPSP_TARGET_MODEL_CALIBRATION",
                "Model fit to the 4.71 mV GF-stimulated somatic comparison "
                "target; not model validation or native g_PSI.")
            row.update({
                "capacitance_variant": variant,
                "Ra_ohm_cm": ra,
                "Cm_spec_uF_cm2": cm,
                "Rm_kohm_cm2": rm,
                "E_syn_mV": e_syn,
                "g_PSI_nS": "" if fitted is None else fitted,
                "somatic_peak_mV": (
                    "" if fitted is None else simulate_abstract_transfer(
                        variant, ra, cm, rm, e_syn, fitted
                    ).somatic_peak_depolarization_mv),
                "classification": classification,
            })
            rows.append(row)
            calibration_results.append(
                (variant, ra, cm, rm, e_syn, fitted, classification))

    def limits(values: Sequence[float]) -> Dict[str, float]:
        return {
            "min": min(values),
            "median": statistics.median(values),
            "max": max(values),
        }

    nominal_calibration = {
        variant: {
            "g_PSI_nS": g,
            "classification": classification,
            "provenance": "model_derived_estimate",
            "target": "4.71 mV MN5 somatic EPSP under GF stimulation",
        }
        for variant, ra, cm, rm, e_syn, g, classification
        in calibration_results
        if (ra, cm, rm, e_syn) == (35.4, 1.0, 6.0, 0.0)
    }

    local_nominal = [
        peak for _, cm, rm, e_syn, g_psi, peak in local_results
        if cm == 1.15 and rm == 6.0 and e_syn == 0.0 and g_psi == 1.0
    ]
    local_nominal_by_body = {
        str(body): limits([
            peak for contact, cm, rm, e_syn, g_psi, peak in local_results
            if contact.post_body == body and cm == 1.15 and rm == 6.0
            and e_syn == 0.0 and g_psi == 1.0
        ])
        for body in EXPECTED_CONTACTS
    }
    abstract_peaks = [item[6].somatic_peak_depolarization_mv
                      for item in abstract_results]
    abstract_local = [item[6].local_synaptic_peak_depolarization_mv
                      for item in abstract_results]
    transfer = [item[6].spatial_attenuation_ratio
                for item in abstract_results]
    delta_local = [item[7].local_synaptic_peak_depolarization_mv
                   - item[6].local_synaptic_peak_depolarization_mv
                   for item in dalpha7_results]
    delta_somatic = [item[7].somatic_peak_depolarization_mv
                     - item[6].somatic_peak_depolarization_mv
                     for item in dalpha7_results]
    paired_abstract = {
        (variant, ra, cm, rm): result
        for variant, ra, cm, rm, e_syn, g_psi, result in abstract_results
        if e_syn == 0.0 and g_psi == 1.0
    }
    c01_ratios = {}
    for output_key in (
            "local_synaptic_peak_depolarization_mv",
            "somatic_peak_depolarization_mv",
            "spatial_attenuation_ratio"):
        c01_ratios[output_key] = limits([
            getattr(paired_abstract[("B", ra, cm, rm)], output_key)
            / getattr(paired_abstract[("A", ra, cm, rm)], output_key)
            for ra, cm, rm in itertools.product(
                PASSIVE_GRID["axial resistivity"],
                PASSIVE_GRID["specific membrane capacitance"],
                PASSIVE_GRID["specific membrane resistance"])
        ])
    delta_by_conductance = {}
    for g in G_DALPHA7_GRID_NS:
        subset = [item for item in dalpha7_results if item[5] == g]
        delta_by_conductance[str(g)] = {
            "local_mV": limits([
                item[7].local_synaptic_peak_depolarization_mv
                - item[6].local_synaptic_peak_depolarization_mv
                for item in subset]),
            "somatic_mV": limits([
                item[7].somatic_peak_depolarization_mv
                - item[6].somatic_peak_depolarization_mv
                for item in subset]),
            "threshold_crossings": sum(
                item[7].threshold_crossing for item in subset),
        }
    summary: Dict[str, object] = {
        "contact_count": len(contacts),
        "contacts_by_post_body": dict(EXPECTED_CONTACTS),
        "unresolved_anatomical_contact_to_soma_paths": len(contacts),
        "contact_local_nominal_peak_mV": limits(local_nominal),
        "contact_local_nominal_by_body_mV": local_nominal_by_body,
        "abstract_run_count": len(abstract_results),
        "abstract_somatic_peak_mV": limits(abstract_peaks),
        "abstract_local_peak_mV": limits(abstract_local),
        "abstract_local_to_somatic_peak_ratio": limits(transfer),
        "C01_B_over_A_at_g_PSI_1_nS": c01_ratios,
        "abstract_threshold_crossings": sum(
            item[6].threshold_crossing for item in abstract_results),
        "calibration_regions": {
            classification: sum(
                item[6] == classification for item in calibration_results)
            for classification in (
                "CENTRAL", "EDGE",
                "OUTSIDE CURRENT EXPLORATORY RANGE (above maximum)",
                "OUTSIDE CURRENT EXPLORATORY RANGE (below minimum)",
            )
        },
        "calibrated_g_PSI_at_nominal_passives": nominal_calibration,
        "calibrated_g_PSI_range_inside_exploratory_range": limits([
            item[5] for item in calibration_results if item[5] is not None]),
        "calibration_configuration_count": len(calibration_results),
        "dalpha7_run_count": len(dalpha7_results),
        "dalpha7_delta_local_mV": limits(delta_local),
        "dalpha7_delta_somatic_mV": limits(delta_somatic),
        "dalpha7_delta_by_effective_conductance": delta_by_conductance,
        "dalpha7_baseline_threshold_crossings": sum(
            item[6].threshold_crossing for item in dalpha7_results),
        "dalpha7_threshold_crossings": sum(
            item[7].threshold_crossing for item in dalpha7_results),
        "all_outputs_finite": all(
            math.isfinite(value)
            for row in rows
            for key, value in row.items()
            if key in ("local_peak_mV", "somatic_peak_mV",
                       "local_to_somatic_peak_ratio",
                       "somatic_time_to_peak_ms",
                       "delta_local_vs_no_Dalpha7_mV",
                       "delta_somatic_vs_no_Dalpha7_mV")
            and value != ""
        ),
        "model_authorization": {
            "gate_a": "MODEL-AUTHORIZED / ANATOMY + LITERATURE CONSTRAINED",
            "gate_b": (
                "MODEL-AUTHORIZED / CHANNEL-CONSTRAINED / "
                "NATIVE VALUE MODEL-DERIVED"),
            "biological_measurement_gates": "NOT AUTHORIZED",
        },
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=OUTPUT_CSV)
    args = parser.parse_args()
    rows, summary = run_analysis()
    with open(args.output, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} sensitivity rows to {args.output}")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
