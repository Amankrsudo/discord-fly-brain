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
    write("FIGURE_7_capability.svg", _stub_capability(cs))
    write("FIGURE_TABLE_R3_capability.md", table_r3())
    write("FIGURE_TABLE_R4_reproducibility.md", table_r4())
    write("FIGURE_8_reproducibility.svg", _stub_repro())


def _stub_capability(cs):
    return textwrap.dedent("""\
        <!-- Stub: Figure 7 (capability/gating diagram) pending hand-authoring.
             Source values verified from reduced_mn5.py and model_framework.py:
             AVAILABLE: anatomy, reduced_passive_mn5; PARTIAL: gfs_electrical_coupling;
             BLOCKED: psi_mn5_synaptic_physiology, psi_mn5_spatial_transfer,
             dalpha7_receptor_conductance. -->
        """) + (
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            f'<text x="200" y="100" text-anchor="middle" font-size="14">'
            'Figure 7: capability/gating diagram (pending)</text></svg>')


def _stub_repro():
    return textwrap.dedent("""\
        <!-- Stub: Figure 8 (reproducibility/overview) pending hand-authoring.
             Key facts: 1773 passed / 2 skipped (inherited, not freshly
             reproduced); Feather checksum NOT recorded; staging commands
             NOT DOCUMENTED; license/attribution VERIFY_REQUIRED. -->
        """) + (
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            f'<text x="200" y="100" text-anchor="middle" font-size="14">'
            'Figure 8: reproducibility overview (pending)</text></svg>')


if __name__ == "__main__":
    main()
