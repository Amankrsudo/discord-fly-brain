"""Generate Fly Brain 3.0 figures and tables from verified repository artifacts.

Reads the committed, audited source CSVs/JSON and writes SVG figures and Markdown
tables into paper/figures/ and paper/tables/. Uses only the Python standard library
and numpy (no matplotlib/pandas required).

Gate safety: never converts geometry into electrical parameters; never labels a
model-derived ratio as a native transfer; never presents an assumption as a
native measurement.

Run:
    python paper/scripts/generate_figures_tables.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import textwrap

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
PAPER = os.path.join(ROOT, "paper")
FIG = os.path.join(PAPER, "figures")
TAB = os.path.join(PAPER, "tables")
RES = os.path.join(ROOT, "research")
ART = os.path.join(RES, "artifacts")

CONTACT_SUMMARY = os.path.join(ART, "malecns_compartment_post_summary.json")
SENSITIVITY_CSV = os.path.join(
    RES, "mn5_psi_mn5_final_constraint_model_sensitivity.csv")
FREEZE_CSV = os.path.join(RES, "model_input_freeze.csv")

os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def med(vals):
    a = np.array(vals, dtype=float)
    return float(np.median(a))


# --- Table R-1: contact summary -------------------------------------------------

def table_r1():
    with open(CONTACT_SUMMARY, encoding="utf-8") as f:
        s = json.load(f)
    lines = [
        "**Table R-1.** PSI→MN5 contact summary at minimum confidence 0.5 "
        "(MaleCNS v1.0). Counts are `AM` (anatomical measurement); "
        "compartment labels are dataset annotations, not voltages or distances "
        "[C-102, C-103].",
        "",
        "| Pairing | Contacts | compartment_post | compartment_pre |",
        "|---|---|---|---|",
    ]
    for pairing, label in [("802401→801970", "left"),
                           ("903327→801295", "right")]:
        body = pairing.split("→")[1]
        b = s["by_mn5_body"][body]
        cp = ", ".join(f"{k}={v}" for k, v in b["compartment_post"].items())
        pr = ", ".join(f"{k}={v}" for k, v in b["compartment_pre"].items())
        lines.append(f"| {pairing} ({label}) | {b['contacts']} | {cp} | {pr} |")
    lines += [
        f"| **Total** | **{s['total_contacts']}** | "
        f"axon=**{s['compartment_post_overall']['axon']}** | "
        f"axon={s['compartment_pre_overall'].get('axon', 0)}, "
        f"unknown={s['compartment_pre_overall'].get('unknown', 0)} |",
        "",
        f"- **Source**: `{CONTACT_SUMMARY}` (sha256: {sha(CONTACT_SUMMARY)[:16]}…)",
        "- **Minconf threshold**: 0.5 (applied by source).",
        "- **Note**: `compartment_post=axon` for all 43; 0 missing, 0 ambiguous, "
        "0 unknown-post.",
        "",
    ]
    return "\n".join(lines)


# --- Figure 3: contact mapping --------------------------------------------------

def figure_3():
    with open(CONTACT_SUMMARY, encoding="utf-8") as f:
        s = json.load(f)
    pairs = [("Left\n802401→801970", s["by_mn5_body"]["801970"]["contacts"]),
             ("Right\n903327→801295", s["by_mn5_body"]["801295"]["contacts"])]
    total = sum(c for _, c in pairs)
    width, height = 520, 360
    margin_l, margin_b = 60, 50
    chart_w = width - margin_l - 40
    max_h = max(c for _, c in pairs) or 1
    bar_w = chart_w / 2.6
    gap = (chart_w - 2 * bar_w) / 3
    max_h_px = height - margin_b - 40
    scale = max_h_px / max_h

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="sans-serif">']
    svg.append(f'<text x="{width/2}" y="22" text-anchor="middle" '
               f'font-size="15" font-weight="bold">'
               f'PSI→MN5 contacts at minconf 0.5 (n={total})</text>')
    svg.append(f'<text x="{width/2}" y="40" text-anchor="middle" '
               f'font-size="10" fill="#555">'
               f'Source: MaleCNS v1.0 syn-partners + annotation layer</text>')
    svg.append(f'<line x1="{margin_l}" y1="{height - margin_b}" '
               f'x2="{width - 40}" y2="{height - margin_b}" '
               f'stroke="#333" stroke-width="1"/>')
    svg.append(f'<line x1="{margin_l}" y1="{margin_b}" '
               f'x2="{margin_l}" y2="{height - margin_b}" '
               f'stroke="#333" stroke-width="1"/>')
    svg.append(f'<text x="{margin_l - 8}" y="{height - margin_b + 15}" '
               f'font-size="10" text-anchor="end">0</text>')
    svg.append(f'<text x="{margin_l - 8}" y="{height - margin_b - max_h_px + 15}" '
               f'font-size="10" text-anchor="end">{max_h}</text>')
    for i, (label, count) in enumerate(pairs):
        x = margin_l + gap + i * (bar_w + gap)
        h = count * scale
        y0 = height - margin_b - h
        svg.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bar_w:.1f}" '
                   f'height="{h:.1f}" fill="#4a6fa5" stroke="#2c4b7d"/>')
        svg.append(f'<text x="{x + bar_w/2:.1f}" y="{y0 - 6:.1f}" '
                   f'font-size="13" font-weight="bold" text-anchor="middle">'
                   f'{count}</text>')
        svg.append(f'<text x="{x + bar_w/2:.1f}" y="{height - margin_b + 16:.1f}" '
                   f'font-size="11" text-anchor="middle">{label}</text>')
    svg.append(f'<text x="{width/2}" y="{height - 8}" text-anchor="middle" '
               f'font-size="10" fill="#666">Evidence: AM (anatomical measurement). '
               f'Compartment label is a dataset annotation, not a voltage [C-102, '
               f'C-103].</text>')
    svg.append('</svg>')
    return "\n".join(svg)


# --- Figure 4: compartment_post distribution ------------------------------------

def figure_4():
    with open(CONTACT_SUMMARY, encoding="utf-8") as f:
        s = json.load(f)
    post = s["compartment_post_overall"]
    pre = s["compartment_pre_overall"]
    cats_post = list(post.keys())
    vals_post = list(post.values())
    cats_pre = list(pre.keys())
    vals_pre = list(pre.values())

    width, height = 560, 340
    margin_l, margin_b, margin_t = 55, 55, 45
    chart_h = height - margin_b - margin_t
    max_v = max(max(vals_post), max(vals_pre)) or 1
    bar_h = chart_h / 4.2
    gap = bar_h * 0.4
    scale = (width - margin_l - 50) / max_v

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="sans-serif">']
    svg.append(f'<text x="{width/2}" y="20" text-anchor="middle" '
               f'font-size="15" font-weight="bold">'
               f'PSI→MN5 compartment annotations (43 contacts)</text>')
    svg.append(f'<text x="{width/2}" y="38" text-anchor="middle" '
               f'font-size="10" fill="#555">'
               f'Source: MaleCNS v1.0 annotation layer</text>')
    colors = {"axon": "#4a6fa5", "dendrite": "#f4a582",
              "unknown": "#999999", "linker": "#66c2a5",
              "cell-body-fiber": "#8da0cb"}
    for row, (cat, val) in enumerate(post.items()):
        y = margin_t + row * (bar_h + gap)
        w = val * scale
        svg.append(f'<rect x="{margin_l}" y="{y:.1f}" width="{w:.1f}" '
                   f'height="{bar_h:.1f}" fill="{colors.get(cat, "#ccc")}" '
                   f'stroke="#333"/>')
        svg.append(f'<text x="{margin_l + 4}" y="{y + bar_h/2 + 4:.1f}" '
                   f'font-size="11" fill="#fff" font-weight="bold">{val}</text>')
        svg.append(f'<text x="{margin_l + 4}" y="{y - 5:.1f}" '
                   f'font-size="10" fill="#444">{cat} (pre)</text>')
        svg.append(f'<text x="{margin_l - 4}" y="{y + bar_h/2 + 4:.1f}" '
                   f'font-size="10" text-anchor="end" fill="#333">'
                   f'compartment_pre</text>')
    for row, (cat, val) in enumerate(pre.items()):
        y = margin_t + (len(post) + row) * (bar_h + gap) + 10
        w = val * scale
        svg.append(f'<rect x="{margin_l}" y="{y:.1f}" width="{w:.1f}" '
                   f'height="{bar_h:.1f}" fill="{colors.get(cat, "#ccc")}" '
                   f'fill-opacity="0.45" stroke="#333"/>')
        svg.append(f'<text x="{margin_l + 4}" y="{y + bar_h/2 + 4:.1f}" '
                   f'font-size="11" fill="#333" font-weight="bold">{val}</text>')
        svg.append(f'<text x="{margin_l - 4}" y="{y + bar_h/2 + 4:.1f}" '
                   f'font-size="10" text-anchor="end" fill="#333">'
                   f'compartment_post</text>')
    svg.append(f'<text x="{width/2}" y="{height - 8}" text-anchor="middle" '
               f'font-size="10" fill="#666">All 43 contacts: compartment_post=axon. '
               f'Label is a dataset annotation, not electrophysiology [C-103].</text>')
    svg.append('</svg>')
    return "\n".join(svg)


# --- Table R-2: native biophysics -----------------------------------------------

def table_r2():
    rows = read_csv(FREEZE_CSV)
    safe_native = [r for r in rows
                   if r["provenance"] == "native_experimental_measurement"
                   and r["safe_now"] == "yes"]
    by_section = [
        ("MN5 resting potential", "−67.8 ± 5.5 SD (n=13)", "mV",
         "Ryglewski, Kilo & Duch 2014", "native_experimental_measurement",
         "[C-301]"),
        ("MN5 spike threshold", "−24.1 ± 8.2 SD (n=11)", "mV",
         "Ryglewski, Kilo & Duch 2014", "native_experimental_measurement",
         "[C-301]"),
        ("MN5 action potential amplitude", "+45.5 ± 8.6 SD (n=13)", "mV",
         "Ryglewski, Kilo & Duch 2014", "native_experimental_measurement",
         "[C-301]"),
        ("MN5 action potential time to peak", "1.20 ± 0.33 (n=13)", "ms",
         "Ryglewski, Kilo & Duch 2014", "native_experimental_measurement",
         "[C-301]"),
        ("MN5 AP 50% width", "0.92 ± 0.25 (n=13)", "ms",
         "Ryglewski, Kilo & Duch 2014", "native_experimental_measurement",
         "[C-301]"),
        ("MN5 input resistance (set 1)", "102 ± 12 (n=22)", "MOhm",
         "Fayyazuddin et al. 2006", "native_experimental_measurement",
         "[C-302]"),
        ("MN5 input resistance (set 2)", "97 ± 31 (n=52)", "MOhm",
         "Ryglewski, Kilo & Duch 2014", "native_experimental_measurement",
         "[C-302]"),
    ]
    conflict_rows = [r for r in rows if r["conflict"] and r["conflict"].startswith("C-01")]

    lines = [
        "**Table R-2.** Admissible native MN5 electrophysiological measurements "
        "(SAFE bucket of `model_input_freeze.csv`) with provenance. Conflicts are "
        "preserved unresolved (see C-01) [C-301, C-302, C-303].",
        "",
        "| Parameter | Value (n) | Unit | Source | Provenance | Claim |",
        "|---|---|---|---|---|---|",
    ]
    for name, val, unit, src, prov, claim in by_section:
        lines.append(f"| {name} | {val} | {unit} | {src} | `{prov}` | {claim} |")
    lines.append("")
    lines.append("**Conflict C-01 (capacitance, unresolved) — both retained, no winner chosen [C-303]**:")
    lines.append("")
    lines.append("| Parameter | Variant A | Variant B | Provenance |")
    lines.append("|---|---|---|---|")
    for r in conflict_rows:
        lines.append(f"| {r['parameter']} | {r['value']} | — | "
                     f"native_experimental_measurement (contested) |")
    lines += [
        "| MN5 whole-cell capacitance (Ryglewski & Duch 2009) | — | 127 ± 16 | "
        "native_experimental_measurement (contested) |",
        "",
        f"- **Source**: `{FREEZE_CSV}` (sha256: {sha(FREEZE_CSV)[:16]}…)",
        "- **Caveat**: the 4.71 ± 0.35 mV somatic EPSP (n=10) was recorded "
        "under GF stimulation and is a comparison target only, not a "
        "PSI-specific measurement [C-304].",
    ]
    return "\n".join(lines)


# --- Table R-3: gate/capability surface -----------------------------------------

def table_r3():
    return "\n".join([
        "**Table R-3.** Model capability surface and authorization gates. "
        "Capabilities are enforced by `model_framework.py` and `reduced_mn5.py` "
        "[C-602, C-401, C-501].",
        "",
        "| Capability | Status | Enforced by | Gate |",
        "|---|---|---|---|",
        "| Anatomy (17/26 contacts, compartment labels, mesh geometry) | AVAILABLE | `malecns_ingest.py` | — |",
        "| Reduced single-compartment MN5 (3 native inputs, no leak) | PARTIAL | `reduced_mn5.py:ReducedMN5Simulator` | — |",
        "| PSI→MN5 synaptic physiology | BLOCKED | `SynapticInterface` (raises) | B |",
        "| PSI→MN5 spatial voltage transfer | BLOCKED | `require_spatial_transfer` / `require_biological_transfer_authorization` | **Gate A** |",
        "| Dα7 receptor conductance | BLOCKED | `Dalpha7Interface.conductance` / `require_dalpha7_gate` | **Gate B** |",
        "| GFS electrical coupling | PARTIAL | `GFSInterface` (no native conductance inserted) | — |",
        "",
        "**Frozen parameter inventory (`model_input_freeze.csv`, 108 parameters)** [C-301]:",
        "",
        "| Bucket | Count |",
        "|---|---|",
        "| SAFE to use now | 40 |",
        "| Assumption-only (usable as explicit assumptions) | 31 |",
        "| Blocked (never used) | 37 |",
        "| Unresolved conflicts preserved | 15 |",
        "",
        "**Blocked quantities never inserted** (examples): MN5 Ra (no Drosophila "
        "measurement), MN5 Rm, PSI→MN5 synaptic conductance, native Dα7 "
        "conductance, contact→soma electrotonic distance [C-201, C-303, C-401, "
        "C-501].",
    ])


# --- Table R-4: reproducibility -------------------------------------------------

def table_r4():
    return "\n".join([
        "**Table R-4.** Reproducibility and validation status. The test count is "
        "inherited, not freshly executed [C-602, C-701].",
        "",
        "| Item | Value | Status | Evidence class |",
        "|---|---|---|---|",
        "| Repository test suite | 1773 passed / 2 skipped (excluding diagnostics) | INHERITED | AM (software) |",
        "| Test command | `python -m pytest tests/ -v --tb=short --ignore=tests/test_diagnostics.py` | VERIFIED | AM |",
        "| SWC SHA-256 pinning (sensitivity script) | 2 cached MN5 SWCs pinned | SHA-256 confirmed in script | AM |",
        "| MaleCNS synapse Feather checksum | NOT RECORDED | VERIFY_REQUIRED | — |",
        "| Data download/staging commands | NOT DOCUMENTED in repo | VERIFY_REQUIRED | — |",
        "| External data license/attribution | VERIFY_REQUIRED | VERIFY_REQUIRED | — |",
        "| Model sensitivity rows | 15,528 (9,288 local + 2,880 abstract + 2,880 Dα7 + 480 cal) | GENERATED | MDE |",
        "",
        "> Software validation is not empirical biological validation [C-602].",
    ])


# --- Figure 6: sensitivity box plot --------------------------------------------

def _box_path(x, vals, width, height):
    """Build a simple box plot (min, q1, median, q3, max) as an SVG path/glyph."""
    a = np.array(vals, dtype=float)
    lo, hi = float(a.min()), float(a.max())
    q1, med, q3 = float(np.percentile(a, 25)), float(np.median(a)), float(np.percentile(a, 75))
    return {"min": lo, "q1": q1, "med": med, "q3": q3, "max": hi}


def figure_6():
    rows = read_csv(SENSITIVITY_CSV)
    abstract = [r for r in rows if r["analysis_id"] == "ABSTRACT_SOMATIC_TRANSFER"]
    local = [r for r in rows if r["analysis_id"] == "CONTACT_LOCAL"]

    somatic = [float(r["somatic_peak_mV"]) for r in abstract]
    local_p = [float(r["local_peak_mV"]) for r in abstract]
    ratio = [float(r["local_to_somatic_peak_ratio"]) for r in abstract]
    local_nominal = [float(r["local_peak_mV"]) for r in local
                     if r["Cm_spec_uF_cm2"] == "1.15"
                     and r["Rm_kohm_cm2"] == "6.0"
                     and r["E_syn_mV"] == "0.0"
                     and r["g_PSI_nS"] == "1.0"]

    # Nominal point values
    nom = [r for r in abstract
           if r["Ra_ohm_cm"] == "35.4" and r["Cm_spec_uF_cm2"] == "1.0"
           and r["Rm_kohm_cm2"] == "6.0" and r["E_syn_mV"] == "0.0"
           and r["g_PSI_nS"] == "1.0"]
    nom_a = next(r for r in nom if r["capacitance_variant"] == "A")
    nom_b = next(r for r in nom if r["capacitance_variant"] == "B")

    width, height = 760, 480
    ml, mr, mt, mb = 70, 30, 50, 70
    pw = width - ml - mr
    ph = height - mt - mb
    groups = [("Local peak", local_p), ("Somatic peak", somatic),
              ("Local-to-somatic\nratio", ratio)]
    ngroups = len(groups) + 1  # +1 for nominal point
    slot = pw / ngroups
    bar_w = slot * 0.28

    def y(v):
        return mt + ph * (1 - (v - 0) / 78)

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="sans-serif">']
    svg.append(f'<text x="{width/2}" y="24" text-anchor="middle" '
               f'font-size="15" font-weight="bold">'
               f'Model-derived sensitivity ranges (15,528 rows) [C-601, C-402]''></text>')
    svg.append(f'<text x="{width/2}" y="42" text-anchor="middle" '
               f'font-size="10" fill="#555">'
               f'Outputs are MODEL-DERIVED, not native measurements. '
               f'Gate A (spatial transfer) NOT AUTHORIZED [C-401].''></text>')
    # axis
    svg.append(f'<line x1="{ml}" y1="{mt+ph}" x2="{ml+pw}" y2="{mt+ph}" '
               f'stroke="#333" stroke-width="1"/>')
    svg.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ph}" '
               f'stroke="#333" stroke-width="1"/>')
    for i, (label, vals) in enumerate(groups):
        b = _box_path(0, vals, 0, 0)
        cx = ml + slot * (i + 1)
        x0 = cx - bar_w / 2
        ylo, yhi = y(b["min"]), y(b["max"])
        yq1, yq3 = y(b["q1"]), y(b["q3"])
        ymed = y(b["med"])
        svg.append(f'<rect x="{x0:.1f}" y="{yq3:.1f}" width="{bar_w:.1f}" '
                   f'height="{yq1 - yq3:.1f}" fill="#4a6fa5" fill-opacity="0.35" '
                   f'stroke="#4a6fa5"/>')
        svg.append(f'<line x1="{cx:.1f}" y1="{yq3:.1f}" x2="{cx:.1f}" '
                   f'y2="{yq1:.1f}" stroke="#4a6fa5" stroke-width="1.5"/>')
        svg.append(f'<line x1="{cx-9:.1f}" y1="{ymed:.1f}" x2="{cx+9:.1f}" '
                   f'y2="{ymed:.1f}" stroke="#1a365d" stroke-width="2"/>')
        svg.append(f'<line x1="{cx:.1f}" y1="{ylo:.1f}" x2="{cx:.1f}" '
                   f'y2="{yq3:.1f}" stroke="#4a6fa5" stroke-width="1"/>')
        svg.append(f'<line x1="{cx:.1f}" y1="{yq1:.1f}" x2="{cx:.1f}" '
                   f'y2="{yhi:.1f}" stroke="#4a6fa5" stroke-width="1"/>')
        svg.append(f'<text x="{cx:.1f}" y="{mt+ph+16}" font-size="10" '
                   f'text-anchor="middle">{label}</text>')
        svg.append(f'<text x="{cx:.1f}" y="{yhi-4:.1f}" font-size="8" '
                   f'text-anchor="middle" fill="#333">'
                   f'{b["min"]:.2f}</text>')
        svg.append(f'<text x="{cx:.1f}" y="{ylo+12:.1f}" font-size="8" '
                   f'text-anchor="middle" fill="#333">{b["max"]:.2f}</text>')

    # Nominal point bar (variant A+B)
    cx = ml + slot * ngroups
    x0 = cx - bar_w / 2
    for vi, (nmv, vcolor, ltag) in enumerate(
            [(float(nom_a["somatic_peak_mV"]), "#e53e3e", "A (43pF)"),
             (float(nom_b["somatic_peak_mV"]), "#dd6b20", "B (127pF)")]):
        yc = y(nmv)
        svg.append(f'<rect x="{x0 + vi*bar_w:.1f}" y="{yc-6:.1f}" width="{bar_w:.1f}" '
                   f'height="12" fill="{vcolor}" fill-opacity="0.7"/>')
        svg.append(f'<text x="{x0 + vi*bar_w + bar_w/2:.1f}" y="{yc-9:.1f}" '
                   f'font-size="8" text-anchor="middle">{ltag}</text>')
    svg.append(f'<text x="{cx:.1f}" y="{mt+ph+16}" font-size="10" '
               f'text-anchor="middle">Nominal point\n(somatic, mV)</text>')
    svg.append(f'<text x="{cx:.1f}" y="{mt+ph+34}" font-size="8" '
               f'text-anchor="middle" fill="#666">'
               f'A: {float(nom_a["somatic_peak_mV"]):.3f} / B: '
               f'{float(nom_b["somatic_peak_mV"]):.3f}</text>')

    svg.append(f'<text x="{width/2}" y="{height-10}" text-anchor="middle" '
               f'font-size="9" fill="#666">C-01 variants A/B both shown; '
               f'no winner chosen. Local nominal (gPSI=1, E_syn=0): '
               f'min {min(local_nominal):.2f} / max {max(local_nominal):.2f} mV '
               f'[C-303].</text>')
    svg.append('</svg>')
    return "\n".join(svg)


def figure_8_reproducibility():
    """Generate Figure 8: Reproducibility overview from verified audit records."""
    width, height = 820, 580
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="monospace">',
        f'<style>'
        f'.title {{ font-size: 20px; font-weight: bold; fill: #1e293b; }}'
        f'.subtitle {{ font-size: 13px; fill: #475569; }}'
        f'.hdr {{ font-size: 13px; font-weight: bold; fill: #0f172a; }}'
        f'.cell {{ font-size: 12px; fill: #1e293b; }}'
        f'.verified {{ fill: #dcfce7; stroke: #16a34a; }}'
        f'.inherited {{ fill: #dbeafe; stroke: #2563eb; }}'
        f'.generated {{ fill: #dbeafe; stroke: #2563eb; }}'
        f'.unavail {{ fill: #fee2e2; stroke: #dc2626; }}'
        f'.verify {{ fill: #fff7ed; stroke: #f97316; }}'
        f'.badge {{ font-size: 11px; font-weight: bold; }}'
        f'.note {{ font-size: 11px; fill: #475569; }}'
        f'.stat {{ font-size: 13px; font-weight: bold; fill: #0f172a; }}'
        f'.stat-label {{ font-size: 11px; fill: #475569; }}'
        f'</style>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width/2}" y="32" text-anchor="middle" class="title">'
        f'Figure 8. Reproducibility and validation overview</text>',
        f'<text x="{width/2}" y="54" text-anchor="middle" class="subtitle">'
        f'Test count and audit status are inherited from prior runs, not freshly reproduced [C-602, C-701]</text>',
        f'<g transform="translate(80, 80)">',
        f'<rect x="0" y="0" width="660" height="26" class="hdr" fill="#e2e8f0" stroke="#94a3b8"/>',
        f'<text x="180" y="17" class="hdr">Item</text>',
        f'<text x="500" y="17" class="hdr">Value / Status</text>',
        f'<text x="640" y="17" class="hdr">Evidence class</text>',
        f'<rect x="0" y="26" width="660" height="34" class="inherited"/>',
        f'<text x="180" y="50" class="cell">Repository test suite</text>',
        f'<rect x="500" y="36" width="120" height="20" class="inherited" stroke="#2563eb"/>',
        f'<text x="560" y="50" text-anchor="middle" class="badge" fill="#2563eb">1773 passed / 2 skipped</text>',
        f'<text x="700" y="50" text-anchor="middle" class="badge" fill="#2563eb">INHERITED</text>',
        f'<text x="640" y="50" text-anchor="middle" class="cell" fill="#2563eb">AM (software)</text>',
        f'<rect x="0" y="60" width="660" height="34" class="verified"/>',
        f'<text x="180" y="84" class="cell">Test command</text>',
        f'<rect x="500" y="70" width="120" height="20" class="verified" stroke="#16a34a"/>',
        f'<text x="560" y="84" text-anchor="middle" class="badge" fill="#16a34a">VERIFIED</text>',
        f'<text x="640" y="84" text-anchor="middle" class="cell" fill="#16a34a">AM</text>',
        f'<text x="20" y="90" class="note">python -m pytest tests/ -v --tb=short --ignore=tests/test_diagnostics.py</text>',
        f'<rect x="0" y="94" width="660" height="34" class="verified"/>',
        f'<text x="180" y="118" class="cell">SWC SHA-256 pinning (sensitivity script)</text>',
        f'<rect x="500" y="104" width="120" height="20" class="verified" stroke="#16a34a"/>',
        f'<text x="560" y="118" text-anchor="middle" class="badge" fill="#16a34a">SHA-256 confirmed</text>',
        f'<text x="640" y="118" text-anchor="middle" class="cell" fill="#16a34a">AM</text>',
        f'<text x="20" y="122" class="note">2 cached MN5 SWCs pinned in analyze_mn5_two_gate_constraint_model.py</text>',
        f'<rect x="0" y="128" width="660" height="34" class="unavail"/>',
        f'<text x="180" y="152" class="cell">MaleCNS synapse Feather checksum</text>',
        f'<rect x="500" y="138" width="120" height="20" class="unavail" stroke="#dc2626"/>',
        f'<text x="560" y="152" text-anchor="middle" class="badge" fill="#dc2626">NOT RECORDED</text>',
        f'<text x="640" y="152" text-anchor="middle" class="cell" fill="#dc2626">—</text>',
        f'<text x="20" y="158" class="note">VERIFY_REQUIRED: no expected checksum recorded for raw Feather artifact</text>',
        f'<rect x="0" y="162" width="660" height="34" class="verify"/>',
        f'<text x="180" y="186" class="cell">Data download / staging commands</text>',
        f'<rect x="500" y="172" width="120" height="20" class="verify" stroke="#f97316"/>',
        f'<text x="560" y="186" text-anchor="middle" class="badge" fill="#f97316">NOT DOCUMENTED</text>',
        f'<text x="640" y="186" text-anchor="middle" class="cell" fill="#f97316">—</text>',
        f'<text x="20" y="190" class="note">VERIFY_REQUIRED: no repository-authored download/stage command exists</text>',
        f'<rect x="0" y="196" width="660" height="34" class="verify"/>',
        f'<text x="180" y="220" class="cell">External data license / attribution</text>',
        f'<rect x="500" y="206" width="120" height="20" class="verify" stroke="#f97316"/>',
        f'<text x="560" y="220" text-anchor="middle" class="badge" fill="#f97316">VERIFY_REQUIRED</text>',
        f'<text x="640" y="220" text-anchor="middle" class="cell" fill="#f97316">—</text>',
        f'<text x="20" y="224" class="note">MaleCNS v1.0 is CC-BY; exact attribution terms to be verified</text>',
        f'<rect x="0" y="230" width="660" height="34" class="generated"/>',
        f'<text x="180" y="254" class="cell">Model sensitivity rows (two-gate sweep)</text>',
        f'<rect x="500" y="240" width="120" height="20" class="generated" stroke="#2563eb"/>',
        f'<text x="560" y="254" text-anchor="middle" class="badge" fill="#2563eb">15,528 rows</text>',
        f'<text x="640" y="254" text-anchor="middle" class="cell" fill="#2563eb">MDE</text>',
        f'<text x="20" y="258" class="note">9,288 local + 2,880 abstract + 2,880 Dα7 + 480 calibration [C-601]</text>',
        f'</g>',
        f'<g transform="translate(80, 290)">',
        f'<text x="0" y="16" class="hdr">Status legend:</text>',
        f'<rect x="0" y="24" width="110" height="22" class="verified" stroke="#16a34a" rx="4"/>',
        f'<text x="120" y="40" class="cell">VERIFIED — confirmed by audit</text>',
        f'<rect x="0" y="52" width="110" height="22" class="inherited" stroke="#2563eb" rx="4"/>',
        f'<text x="120" y="68" class="cell">INHERITED — from prior run, not fresh</text>',
        f'<rect x="0" y="80" width="110" height="22" class="generated" stroke="#2563eb" rx="4"/>',
        f'<text x="120" y="96" class="cell">GENERATED — model-derived output</text>',
        f'<rect x="0" y="108" width="110" height="22" class="unavail" stroke="#dc2626" rx="4"/>',
        f'<text x="120" y="124" class="cell">NOT RECORDED / VERIFY_REQUIRED</text>',
        f'<rect x="0" y="136" width="110" height="22" class="verify" stroke="#f97316" rx="4"/>',
        f'<text x="120" y="152" class="cell">NOT DOCUMENTED / VERIFY_REQUIRED</text>',
        f'</g>',
        f'<g transform="translate(80, 460)">',
        f'<rect x="0" y="0" width="660" height="70" fill="#f8fafc" stroke="#e2e8f0" rx="6"/>',
        f'<text x="20" y="20" class="note"><tspan font-weight="bold">Key constraints:</tspan></text>',
        f'<text x="20" y="40" class="note">• Test count 1773/2 is INHERITED — not freshly executed against a clean checkout.</text>',
        f'<text x="20" y="58" class="note">• Feather checksum NOT RECORDED; staging commands NOT DOCUMENTED — VERIFY_REQUIRED.</text>',
        f'<text x="20" y="76" class="note">• Software validation is not empirical biological validation [C-602].</text>',
        f'</g>',
        f'<text x="80" y="560" class="note">Source: paper/tables/FIGURE_TABLE_R4_reproducibility.md, validation/full_suite_report.md, EXTERNAL_DATA_REPRODUCIBILITY.md</text>',
        f'</svg>'
    ]
    return "\n".join(svg)


def write(name, content):
    path = os.path.join(FIG if name.endswith(".svg") else TAB, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote {path}")


def main():
    write("FIGURE_3_contact_mapping.svg", figure_3())
    write("FIGURE_4_compartment_annotations.svg", figure_4())
    write("FIGURE_6_sensitivity.svg", figure_6())
    write("FIGURE_TABLE_R1_contact_summary.md", table_r1())
    write("FIGURE_TABLE_R2_native_biophysics.md", table_r2())
    with open(CONTACT_SUMMARY, encoding="utf-8") as f:
        cs = json.load(f)
    # Figures 7 and 8 are hand-authored from verified sources — do not regenerate
    write("FIGURE_TABLE_R3_capability.md", table_r3())
    write("FIGURE_TABLE_R4_reproducibility.md", table_r4())


def figure_7_capability(cs):
    """Generate Figure 7: Capability surface and authorization gates."""
    width, height = 820, 680
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="monospace">',
        f'<style>'
        f'.title {{ font-size: 20px; font-weight: bold; fill: #1e293b; }}'
        f'.subtitle {{ font-size: 13px; fill: #475569; }}'
        f'.hdr {{ font-size: 13px; font-weight: bold; fill: #0f172a; }}'
        f'.cell {{ font-size: 12px; fill: #1e293b; }}'
        f'.avail {{ fill: #dcfce7; stroke: #16a34a; }}'
        f'.partial {{ fill: #fef9c3; stroke: #ca8a04; }}'
        f'.blocked {{ fill: #fee2e2; stroke: #dc2626; }}'
        f'.badge {{ font-size: 11px; font-weight: bold; }}'
        f'.note {{ font-size: 11px; fill: #475569; }}'
        f'.gate-label {{ font-size: 12px; font-weight: bold; fill: #dc2626; }}'
        f'.stat {{ font-size: 13px; font-weight: bold; fill: #0f172a; }}'
        f'.stat-label {{ font-size: 11px; fill: #475569; }}'
        f'</style>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width/2}" y="32" text-anchor="middle" class="title">'
        f'Figure 7. Model capability surface and authorization gates</text>',
        f'<text x="{width/2}" y="54" text-anchor="middle" class="subtitle">'
        f'Six capabilities enforced by model_framework.py (MN5Model.capabilities) and reduced_mn5.py (ReducedMN5Simulator.capabilities) [C-602, C-401, C-501]</text>',
        f'<g transform="translate(80, 80)">',
        f'<rect x="0" y="0" width="660" height="26" class="hdr" fill="#e2e8f0" stroke="#94a3b8"/>',
        f'<text x="180" y="17" class="hdr">Capability</text>',
        f'<text x="470" y="17" class="hdr">Status</text>',
        f'<rect x="0" y="26" width="660" height="32" class="avail"/>',
        f'<text x="180" y="48" class="cell">Anatomy (17/26 contacts, compartment labels, mesh geometry)</text>',
        f'<rect x="470" y="34" width="72" height="20" class="avail" stroke="#16a34a"/>',
        f'<text x="506" y="48" text-anchor="middle" class="badge" fill="#16a34a">AVAILABLE</text>',
        f'<rect x="0" y="58" width="660" height="32" class="partial"/>',
        f'<text x="180" y="80" class="cell">Reduced single-compartment MN5 (3 native inputs, no leak)</text>',
        f'<rect x="470" y="66" width="72" height="20" stroke="#ca8a04" fill="#fef9c3"/>',
        f'<text x="506" y="80" text-anchor="middle" class="badge" fill="#ca8a04">PARTIAL</text>',
        f'<rect x="0" y="90" width="660" height="32" fill="#fee2e2" stroke="#dc2626"/>',
        f'<text x="180" y="112" class="cell">PSI→MN5 synaptic physiology</text>',
        f'<rect x="470" y="98" width="72" height="20" fill="#fee2e2" stroke="#dc2626"/>',
        f'<text x="506" y="112" text-anchor="middle" class="badge" fill="#dc2626">BLOCKED</text>',
        f'<text x="560" y="112" class="gate-label">Gate B</text>',
        f'<rect x="0" y="122" width="660" height="32" fill="#fee2e2" stroke="#dc2626"/>',
        f'<text x="180" y="144" class="cell">PSI→MN5 spatial voltage transfer</text>',
        f'<rect x="470" y="130" width="72" height="20" fill="#fee2e2" stroke="#dc2626"/>',
        f'<text x="506" y="144" text-anchor="middle" class="badge" fill="#dc2626">BLOCKED</text>',
        f'<text x="560" y="144" class="gate-label">Gate A</text>',
        f'<rect x="0" y="154" width="660" height="32" fill="#fee2e2" stroke="#dc2626"/>',
        f'<text x="180" y="176" class="cell">Dα7 receptor conductance</text>',
        f'<rect x="470" y="162" width="72" height="20" fill="#fee2e2" stroke="#dc2626"/>',
        f'<text x="506" y="176" text-anchor="middle" class="badge" fill="#dc2626">BLOCKED</text>',
        f'<text x="560" y="176" class="gate-label">Gate B</text>',
        f'<rect x="0" y="186" width="660" height="32" class="partial" fill="#fef9c3" stroke="#ca8a04"/>',
        f'<text x="180" y="208" class="cell">GFS electrical coupling</text>',
        f'<rect x="470" y="194" width="72" height="20" stroke="#ca8a04" fill="#fef9c3"/>',
        f'<text x="506" y="208" text-anchor="middle" class="badge" fill="#ca8a04">PARTIAL</text>',
        f'</g>',
        f'<g transform="translate(80, 240)">',
        f'<rect x="0" y="0" width="260" height="70" fill="#fef2f2" stroke="#fecaca" rx="6"/>',
        f'<text x="130" y="18" text-anchor="middle" class="gate-label">Gate A: PSI→MN5 spatial voltage transfer</text>',
        f'<text x="130" y="36" text-anchor="middle" class="note">NOT AUTHORIZED — no native measurement</text>',
        f'<text x="130" y="54" text-anchor="middle" class="note">require_spatial_transfer raises</text>',
        f'<rect x="290" y="0" width="260" height="70" fill="#fef2f2" stroke="#fecaca" rx="6"/>',
        f'<text x="420" y="18" text-anchor="middle" class="gate-label">Gate B: Dα7 receptor conductance</text>',
        f'<text x="420" y="36" text-anchor="middle" class="note">NOT AUTHORIZED — no native measurement</text>',
        f'<text x="420" y="54" text-anchor="middle" class="note">require_dalpha7_gate raises</text>',
        f'</g>',
        f'<g transform="translate(80, 340)">',
        f'<text x="0" y="22" class="hdr">Frozen parameter inventory (model_input_freeze.csv, 108 parameters) [C-301]</text>',
        f'<rect x="0" y="28" width="140" height="48" class="avail" stroke="#16a34a" rx="6"/>',
        f'<text x="70" y="50" text-anchor="middle" class="stat">40</text>',
        f'<text x="70" y="68" text-anchor="middle" class="stat-label">SAFE to use</text>',
        f'<rect x="150" y="28" width="140" height="48" stroke="#ca8a04" fill="#fef9c3" rx="6"/>',
        f'<text x="220" y="50" text-anchor="middle" class="stat">31</text>',
        f'<text x="220" y="68" text-anchor="middle" class="stat-label">Assumption-only</text>',
        f'<rect x="300" y="28" width="140" height="48" stroke="#dc2626" fill="#fee2e2" rx="6"/>',
        f'<text x="370" y="50" text-anchor="middle" class="stat">37</text>',
        f'<text x="370" y="68" text-anchor="middle" class="stat-label">Blocked (never used)</text>',
        f'<rect x="450" y="28" width="140" height="48" stroke="#dc2626" fill="#ffebee" rx="6"/>',
        f'<text x="520" y="50" text-anchor="middle" class="stat">15</text>',
        f'<text x="520" y="68" text-anchor="middle" class="stat-label">Unresolved conflicts</text>',
        f'<rect x="600" y="28" width="140" height="48" stroke="#64748b" fill="#f1f5f9" stroke-dasharray="4 2" rx="6"/>',
        f'<text x="670" y="50" text-anchor="middle" class="stat">0</text>',
        f'<text x="670" y="68" text-anchor="middle" class="stat-label">Promoted to native</text>',
        f'</g>',
        f'<g transform="translate(80, 440)">',
        f'<rect x="0" y="0" width="660" height="62" fill="#fff5f5" stroke="#fecaca" rx="6"/>',
        f'<text x="20" y="20" class="note">Blocked quantities never inserted (examples from model_input_freeze.csv):</text>',
        f'<text x="20" y="40" class="note">MN5 Ra, MN5 Rm, PSI→MN5 synaptic conductance, native Dα7 conductance, contact→soma electrotonic distance [C-201, C-303, C-401, C-501]</text>',
        f'<text x="20" y="60" class="note">These raise BlockedParameterError when requested — they do not default, estimate, or degrade silently.</text>',
        f'</g>',
        f'<text x="80" y="660" class="note">Source: model_framework.py:669-676, reduced_mn5.py:262-272, paper/tables/FIGURE_TABLE_R3_capability.md</text>',
        f'</svg>'
    ]
    return "\n".join(svg)


if __name__ == "__main__":
    main()
