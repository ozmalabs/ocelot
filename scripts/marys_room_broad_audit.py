"""Phase 5 audit: independent re-verification of the freeze and of headline numbers.

Run from the repo root:
    PYTHONPATH=. /home/matt/ozmadev/ocelot/.venv/bin/python -m scripts.marys_room_broad_audit

Reads only frozen/recorded artefacts (manifest, Arm A, Arm B, Arm C results) plus
the forward model.  It never imports domains.photon_eye and never builds an eye.
Scoring, angle, Wilson, decoding and the eye capture formula are re-implemented
here from their written definitions (prereg A1/A2, mechanism table) rather than
imported from the stage scripts, so that agreement is an independent check.
Writes results/marys_room_broad_audit.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

from domains import spectral_forward as sf

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
OUT = R / "marys_room_broad_audit.json"
CORE = {"mono_sweep", "boundary_dense", "illuminant", "reflectance", "metamer", "eyelid"}
# documented eye receptors (mechanism table / prereg shared rules): centre, bw, half_sat, dark
RECEPT = {"l": (564.0, 42.0, 512.0, 0.0), "m": (534.0, 36.0, 512.0, 0.0),
          "s": (420.0, 28.0, 512.0, 0.0)}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wilson(k, n, z=1.959963984540054):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]


def angle(u, v):
    nu, nv = math.hypot(*u), math.hypot(*v)
    c = (u[0] * v[0] + u[1] * v[1]) / (nu * nv)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def nearest_anchor(rg, by, anchors):
    if rg == 0 and by == 0:
        return "undecided"
    best = min(anchors, key=lambda k: (angle((rg, by), anchors[k]), k))
    return best


def sign_label(rg):
    return "reddish" if rg > 0 else ("greenish" if rg < 0 else "undecided")


def eye_formula(packets):
    act = {}
    for r, (c, bw, half, dark) in RECEPT.items():
        caught = dark + sum(n * math.exp(-0.5 * ((w - c) / bw) ** 2) for w, n in packets)
        act[r] = caught / (caught + half)
    return act["l"] - act["m"], act["s"] - 0.5 * (act["l"] + act["m"])


def check(name, audit_val, reported_val, tol, out):
    ok = abs(audit_val - reported_val) <= tol
    out.append({"quantity": name, "audit": audit_val, "reported": reported_val,
                "abs_diff": abs(audit_val - reported_val), "tol": tol, "match": ok})


def main():
    freeze = json.loads((R / "marys_room_broad_freeze.json").read_text())
    # ---------------------------------------------------------- 1. freeze
    fz = {"files": {}, "prereg": {}}
    for rel, h in freeze["sha256"].items():
        p = ROOT / rel
        now = sha(p) if p.exists() else None
        fz["files"][rel] = {"frozen": h, "now": now, "match": now == h}
    pre = ROOT / "docs/experiments/marys-room-broad-prereg.md"
    a2 = freeze["amendment_A2"]
    b = pre.read_bytes()
    fz["prereg"] = {
        "full_sha256_now": hashlib.sha256(b).hexdigest(),
        "bytes_now": len(b),
        "matches_A2_lock": hashlib.sha256(b).hexdigest() == a2["sha256"],
        "a1_prefix_matches_A1_freeze":
            hashlib.sha256(b[: a2["a1_prefix_bytes"]]).hexdigest()
            == freeze["sha256"]["docs/experiments/marys-room-broad-prereg.md"],
    }
    non_prereg = [v["match"] for k, v in fz["files"].items() if not k.endswith("prereg.md")]
    fz["all_non_prereg_files_match"] = all(non_prereg)
    fz["n_files"] = len(fz["files"])
    rd = json.loads((R / "marys_room_rate_distortion.json").read_text())
    armb_sha_now = sha(R / "marys_room_broad.json")
    fz["armB_result_sha_now"] = armb_sha_now
    fz["armB_result_matches_hash_recorded_by_armC"] = armb_sha_now == rd["inputs"]["eye_result"]["sha256"]
    try:
        fz["git_head_now"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception as e:  # pragma: no cover
        fz["git_head_now"] = f"unavailable: {e}"
    fz["git_head_matches_freeze"] = fz["git_head_now"] == freeze["git_head"]

    # ---------------------------------------------------------- 2. headline numbers
    man = json.loads((R / "marys_room_broad_stimuli.json").read_text())
    arma = json.loads((R / "marys_room_broad_armA.json").read_text())
    armb = json.loads((R / "marys_room_broad.json").read_text())
    anchors = {k: tuple(v["unit_direction"]) for k, v in arma["anchors"].items()}
    mstim = {e["id"]: e for e in man["stimuli"]}
    rows = armb["per_stimulus"]
    checks = []

    core = [r for r in rows if r["split"] == "heldout" and r["family"] in CORE and r["duplicate_of"] is None]
    scored = []
    for r in core:
        t = mstim[r["id"]]["truth"]          # truth from the frozen manifest, not Arm B
        if t["excitation_purity"] < 0.05:
            continue
        scored.append((r, t))
    n = len(scored)
    eye_anchor = sum(nearest_anchor(r["eye"]["red_green"], r["eye"]["blue_yellow"], anchors) == t["hue4"]
                     for r, t in scored)
    eye_sign = sum(sign_label(r["eye"]["red_green"]) == t["binary"] for r, t in scored)

    # theory recomputed from the recipe via the forward model (not read from Arm A)
    th = {}
    for r in core:
        e = mstim[r["id"]]
        from scripts.marys_room_broad_theory import spd_from_recipe  # recipe interpreter only
        rec = e["theory_input"].get("recipe") or e["eye_input"]["recipe"]
        lms = sf.lms_from_spd(spd_from_recipe(rec), observer=e["theory_input"]["observer"])
        th[r["id"]] = (float(lms[0] - lms[1]), float(lms[2] - 0.5 * (lms[0] + lms[1])))
    th_sign = sum(sign_label(th[r["id"]][0]) == t["binary"] for r, t in scored)
    th_anchor = sum(nearest_anchor(*th[r["id"]], anchors) == t["hue4"] for r, t in scored)
    angles = [angle(th[r["id"]], (r["eye"]["red_green"], r["eye"]["blue_yellow"])) for r in core]
    p = armb["pools"]["HELDOUT_core"]
    check("HO_core n hue-scored", n, p["eye_multi_anchor_hue4"]["n"], 0, checks)
    check("HO_core eye anchor accuracy", eye_anchor / n, p["eye_multi_anchor_hue4"]["accuracy"], 1e-12, checks)
    wl = wilson(eye_anchor, n)
    check("HO_core eye anchor Wilson lo", wl[0], p["eye_multi_anchor_hue4"]["accuracy_wilson95"][0], 1e-9, checks)
    check("HO_core eye sign accuracy", eye_sign / n, p["eye_sign_rule_binary"]["accuracy"], 1e-12, checks)
    check("HO_core theory sign accuracy", th_sign / n, p["theory_sign_accuracy"], 1e-12, checks)
    check("HO_core theory anchor accuracy", th_anchor / n, p["theory_multi_accuracy"], 1e-12, checks)
    check("HO_core median angle (deg)", float(np.median(angles)), p["angular_error"]["median_deg"], 1e-9, checks)
    check("HO_core mean angle (deg)", float(np.mean(angles)), p["angular_error"]["mean_deg"], 1e-9, checks)

    # eye outputs vs the documented capture formula from the stored packets (unadapted)
    worst = 0.0
    n_rep = 0
    for r in rows:
        e = mstim[r["id"]]
        if r["family"] == "adaptation" or "packets" not in e["eye_input"]:
            continue
        rg, by = eye_formula(e["eye_input"]["packets"])
        worst = max(worst, abs(rg - r["eye"]["red_green"]), abs(by - r["eye"]["blue_yellow"]))
        n_rep += 1
    check("max |eye - documented formula| over unadapted inputs", worst, 0.0, 1e-12, checks)

    # eyelid sign
    lid = [r for r in rows if r["family"] == "eyelid"]
    check("eyelid n with eye red_green > 0", sum(r["eye"]["red_green"] > 0 for r in lid), 27, 0, checks)
    check("eyelid min eye red_green", min(r["eye"]["red_green"] for r in lid),
          armb["eyelid"]["summary"]["rg_min"], 1e-15, checks)

    # metamers: eye gap per pair, recomputed from per-stimulus eye outputs
    met_rows = {}
    for r in rows:
        if r["family"] == "metamer":
            prm = mstim[r["id"]]["params"]
            met_rows.setdefault(prm["pair_id"], {})[prm["member"][0]] = r
    n_broken = 0
    gaps = []
    for pid, m in met_rows.items():
        a, bb = m["a"], m["b"]
        g = math.hypot(a["eye"]["red_green"] - bb["eye"]["red_green"], a["eye"]["blue_yellow"] - bb["eye"]["blue_yellow"])
        gaps.append(g)
        n_broken += g > 1e-6
    check("metamer pairs broken (eye gap > 1e-6)", n_broken, armb["verdicts"]["P3"]["n_measurable"], 0, checks)
    rep_gaps = [x["eye_gap"] for x in armb["metamers"]]
    check("metamer max eye gap", max(gaps), max(rep_gaps), 1e-12, checks)

    # Gaussian L=M crossing (analytic), vs reported eye zero-crossing at 1000 q
    lam = np.linspace(530, 560, 300001)
    Lg = np.exp(-0.5 * ((lam - 564) / 42) ** 2)
    Mg = np.exp(-0.5 * ((lam - 534) / 36) ** 2)
    z = float(lam[np.argmin(abs(Lg - Mg))])
    rep_val = [x for x in armb["eye_zero_crossings"]["q1000"]["eye_red_green_zero_nm"] if 530 < x < 560][0]
    check("eye RG zero (nm), Gaussian analytic vs reported q1000", z, rep_val, 0.02, checks)

    # ---------------------------------------------------------- Arm C: raw LMS USQ b=6 from scratch
    tr = [r for r in rows if r["split"] == "train"]
    Xtr = np.array([[r["eye"]["receptors"][c]["activation"] for c in "lms"] for r in tr])
    lo, hi = Xtr.min(0), Xtr.max(0)
    Xho = np.array([[r["eye"]["receptors"][c]["activation"] for c in "lms"] for r in core])
    bits = 6
    idx = np.clip(np.floor((Xho - lo) / (hi - lo) * 2 ** bits), 0, 2 ** bits - 1)
    rec = lo + (idx + 0.5) * (hi - lo) / 2 ** bits
    truth_core = {r["id"]: mstim[r["id"]]["truth"] for r in core}
    corr = tot = 0
    for r, v in zip(core, rec):
        t = truth_core[r["id"]]
        if t["excitation_purity"] < 0.05:
            continue
        tot += 1
        corr += nearest_anchor(v[0] - v[1], v[2] - 0.5 * (v[0] + v[1]), anchors) == t["hue4"]
    op = rd["operating_points"]["HO_core"]
    check("Arm C A0 (HO_core eye anchor acc)", eye_anchor / n, op["A0"], 1e-12, checks)
    check("Arm C raw LMS b=6 accuracy", corr / tot,
          op["per_representation"]["a_raw_LMS"]["acc_op_with_model_cost"]["task_accuracy"], 1e-12, checks)
    check("Arm C raw LMS b=6 total rate", 3 * bits + 192 / len(core),
          op["per_representation"]["a_raw_LMS"]["acc_op_with_model_cost"]["rate_total"], 1e-12, checks)
    check("Arm C VQ k=64 total rate", math.log2(64) + 64 * 2 * 32 / len(core),
          op["per_representation"]["d1_VQ_opp"]["acc_op_with_model_cost"]["rate_total"], 1e-12, checks)
    # R* raw recomputed from rd_rows: smallest rate with acc >= 0.95*A0
    tgt = 0.95 * op["A0"]
    raw_rows = [x for x in rd["rd_rows"] if x["pool"] == "HO_core" and x["representation"] == "a_raw_LMS"
                and x["task_accuracy"] >= tgt]
    check("Arm C R*(raw) from rd_rows", min(x["rate_total"] for x in raw_rows),
          rd["verdicts"]["P6_primary"]["baseline_R"], 1e-12, checks)

    out = {
        "experiment": "marys_room_broad_audit",
        "provenance_note": "no eye built; engine provenance of audited eye data: " + armb["provenance"],
        "freeze": fz,
        "checks": checks,
        "n_checks": len(checks),
        "n_mismatch": sum(not c["match"] for c in checks),
        "n_unadapted_inputs_replicated": n_rep,
    }
    assert "domains.photon_eye" not in sys.modules
    OUT.write_text(json.dumps(out, indent=1))
    for c in checks:
        print(("OK   " if c["match"] else "MISS ") + f"{c['quantity']}: audit={c['audit']!r} reported={c['reported']!r}")
    print("freeze non-prereg files match:", fz["all_non_prereg_files_match"], "| prereg:", fz["prereg"],
          "| armB sha matches ArmC record:", fz["armB_result_matches_hash_recorded_by_armC"],
          "| git head ok:", fz["git_head_matches_freeze"])


if __name__ == "__main__":
    main()
