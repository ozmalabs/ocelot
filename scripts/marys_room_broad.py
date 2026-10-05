"""Mary's Room broad study -- Arm B (photon eye) + scoring against Arm A.

    python -m scripts.marys_room_broad

Order of operations (binding):
  1. Recompute every sha256 in results/marys_room_broad_freeze.json; abort on
     any mismatch (printing which file).  Only then engine_preamble().
  2. Verify every manifest entry's packets_sha256 / spd_sha256 (integrity).
  3. Pilot regression (GraphEye(n_az=2), 610 nm col 0 / 530 nm col 1).
  4. Batched-vs-fresh equivalence check on >= 10 stimuli (byte-identical
     red_green / blue_yellow and receptor state).
  5. Batched single-epoch runs (fresh eye per batch, one column per stimulus
     instance) for every manifest entry that has packets, except adaptation
     and pilot entries.  Supplementary eyelid reference stimuli (declared
     below, BEFORE any Arm B eye run) are run in their own fresh batch.
  6. Adaptation: one dedicated fresh n_az=1 eye per adaptation entry,
     20 adapting epochs + 1 test epoch (each epoch waited to completion,
     because submit_photons reads the receptor adaptation at submit time).
  7. Score per prereg "Primary metrics" + Amendment A1-4.

Nothing here feeds back into a stimulus, decoder, anchor, threshold, split or
metric of the frozen preregistration.  The extra analysis choices made by this
stage (ARM_B_DECLARATIONS below) were written before any Arm B eye output was
seen; they are reported as Arm B stage declarations, not as A1 content.

The eye is only read: percepts via eye.latest(), receptor state via
eye.substrate.node(eye._receptors[(col, cls)])['attrs'].  Nothing is written.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "results" / "marys_room_broad_freeze.json"
OUT_JSON = ROOT / "results" / "marys_room_broad.json"
OUT_CSV = ROOT / "results" / "marys_room_broad_per_stimulus.csv"
EXPECTED_ENGINE = "b6a41e3bbba6"

# ------------------------------------------------------------------ Arm B stage declarations
# Written before any Arm B eye run.  Analysis-only; none of these touches a
# frozen stimulus / decoder / anchor / split.
ARM_B_DECLARATIONS = {
    "execution": {
        "batch_size_columns": 100,
        "eye_construct": 'GraphEye(n_az=<batch size>, context={"worker_capacity": 1})',
        "fresh_eye_per_batch": True,
        "wait": "poll processed_count() every 2 ms; deadline = 60 s + 0.5 s x columns per epoch; "
                "timeout raises (no partial data)",
        "adaptation": "one fresh GraphEye(n_az=1) per adaptation entry; 20 adapting epochs then 1 test "
                      "epoch, each epoch waited until processed_count() == epoch before the next submit",
        "equivalence_check_min_stimuli": 10,
    },
    "angular_error": "angle (deg) between theory (RG,BY) and eye (red_green, blue_yellow) as 2-vectors; "
                     "undefined (reported, excluded) if either vector is exactly zero",
    "angular_error_ci": "percentile bootstrap of mean and median, B=10000, numpy default_rng(20261004) "
                        "(Arm B stage declaration; A1-4 declares no CI for angular error); descriptive only",
    "rg_rel_bins": [0.0, 0.01, 0.03, 0.1, 0.3, 1.0000001],
    "eye_abs_rg_bins": [0.0, 0.01, 0.03, 0.1, 0.3, 1.0000001],
    "dist_bins_nm": [[0, 5], [5, 10], [10, 20], [20, 50], [50, 100], [100, 200]],
    "metamer_measurable_gap": 1e-6,
    "clear_chromatic_sign_margin_rel": 0.10,
    "clear_chromatic_multi_margin_deg": 10.0,
    "clear_agreement_threshold": 0.90,
    "near_boundary_window_nm": 20.0,
    "quantisation_leg_negligible_fraction": 0.10,
    "replica_exact_tolerance": 1e-12,
    "calibration": "per intensity: Pearson & Spearman of theory rg_rel=(L-M)/(L+M) vs eye red_green "
                   "(and by_rel vs blue_yellow) on mono_sweep+boundary_dense; through-origin slope per "
                   "intensity; residual vs a through-origin slope fitted on TRAIN mono 1000 q only, "
                   "binned by td over HELDOUT_core distinct items. Descriptive; feeds no decoder.",
    "decomposition": "theory(CIE) -> Gaussian-linear on expected quanta (sensitivity mismatch) -> "
                     "Gaussian-linear on submitted integer packets, read from eye caught_quanta "
                     "(quantisation) -> eye activations (Naka-Rushton). Linear opponent = "
                     "(cL-cM, cS-0.5(cL+cM)). Angles per leg.",
    "eyelid_reference": "for each eyelid stimulus, monochromatic 610 nm and 640 nm references at the "
                        "eyelid stimulus's at-retina td (quanta = 1000 x td / td(1000 q)), plus 640 nm at "
                        "the eyelid stimulus's packets_total quanta; cumulative rounding (single bin).",
    "verdict_rules": {
        "P1": "Arm A only: sign/anchor decoders beat chance = one-sided exact p vs majority < 0.05 on "
              "HELDOUT mono_sweep and on reflectance; graceful = sign accuracy non-decreasing over the "
              "distance bins (1000 q). supported if all hold for at least one decoder, else mixed/not.",
        "P2": "(a) theory-eye label agreement >= 0.90 on clear-chromatic items (TRAIN + HELDOUT_core "
              "distinct; sign margin >= 0.10 / anchor margin >= 10 deg) for both decoders; (b) agreement "
              "within +-20 nm of 554.08 nm (mono+boundary) lower than (a) for both decoders; (c) the "
              "documented sources account for the eye: replica == eye within 1e-12 on every unadapted "
              "stimulus and near-boundary median quantisation leg < 0.10 x median total error. "
              "supported = a,b,c; not supported = none; else mixed.",
        "P3": "supported if >= 1 metamer pair has eye opponent gap > 1e-6 (activation units).",
        "P4": "per condition (wrong_optics vs its unfiltered D65 bases; wrong_observer 10deg vs 2deg on the "
              "same bases): degrade = median theory-eye angular error higher AND neither decoder's "
              "theory accuracy higher. supported = both degrade; mixed = one; not supported = neither.",
        "P5": "supported if eye red_green > 0 for all 27 eyelid stimuli; not supported if any <= 0 "
              "(per-OD_long breakdown reported).",
    },
}
BOOT_SEED = 20261004
BOOT_B = 10000
EQUIV_IDS = ["mono_400nm_q100", "mono_555nm_q1000", "mono_700nm_q10000", "bnd_551nm_q100",
             "illum_A_1000td", "refl_01_D65", "refl_15_A", "refl_19_E", "met_pair03_red_D65_b",
             "wopt_lens_05_D65", "wopt_macular_12_D65", "lid_D65_od1.3_100td", "lid_A_od1.6_10000td",
             "pois_mono554_t3", "abl5_refl_10_D65"]
REF_WL = (610, 640)


# ------------------------------------------------------------------ 1. freeze check

def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_freeze() -> dict:
    fz = json.loads(FREEZE_PATH.read_text())
    bad = []
    for rel, h in fz["sha256"].items():
        p = ROOT / rel
        cur = sha256_file(p) if p.exists() else "MISSING"
        if cur != h:
            bad.append((rel, h, cur))
    if bad:
        for rel, h, cur in bad:
            print(f"FREEZE MISMATCH: {rel}\n  frozen {h}\n  now    {cur}", file=sys.stderr)
        raise SystemExit("ABORT: frozen preregistration files changed; Arm B not run.")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"freeze_file": str(FREEZE_PATH.relative_to(ROOT)), "freeze_file_sha256": sha256_file(FREEZE_PATH),
            "freeze_utc": fz["utc_timestamp"], "n_files_checked": len(fz["sha256"]), "all_match": True,
            "git_head_at_freeze": fz["git_head"], "git_head_now": head,
            "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


# ------------------------------------------------------------------ small numerics

def vangle(u, v):
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu == 0 or nv == 0:
        return None, None
    c = (u[0] * v[0] + u[1] * v[1]) / (nu * nv)
    c = max(-1.0, min(1.0, c))
    return math.degrees(math.acos(c)), c


def rankdata(x):
    import numpy as np
    x = np.asarray(x, float)
    order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x))
    r[order] = np.arange(1, len(x) + 1)
    _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
    return np.bincount(inv, weights=r)[inv] / cnt[inv]


def corr(x, y):
    import numpy as np
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return {"n": int(len(x)), "pearson": None, "spearman": None}
    return {"n": int(len(x)), "pearson": float(np.corrcoef(x, y)[0, 1]),
            "spearman": float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])}


def ang_summary(vals):
    import numpy as np
    defined = [v for v in vals if v is not None]
    out = {"n": len(vals), "n_undefined": len(vals) - len(defined)}
    if not defined:
        return out
    a = np.asarray(defined, float)
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(a), size=(BOOT_B, len(a)))
    bs = a[idx]
    out.update({"mean_deg": float(a.mean()), "median_deg": float(np.median(a)),
                "p90_deg": float(np.percentile(a, 90)), "max_deg": float(a.max()), "min_deg": float(a.min()),
                "mean_boot95": [float(np.percentile(bs.mean(1), 2.5)), float(np.percentile(bs.mean(1), 97.5))],
                "median_boot95": [float(np.percentile(np.median(bs, 1), 2.5)),
                                  float(np.percentile(np.median(bs, 1), 97.5))],
                "mean_cosine": float(np.mean(np.cos(np.radians(a))))})
    return out


def agree(rows, key_a, key_b):
    from scripts.marys_room_broad_theory import wilson
    n = len(rows)
    k = sum(1 for r in rows if r[key_a] == r[key_b])
    return {"n": n, "agree": k, "rate": (k / n) if n else None, "wilson95": wilson(k, n)}


# ------------------------------------------------------------------ eye I/O

def wait_epochs(eye, n_expected: int, n_cols: int):
    deadline = time.monotonic() + 60.0 + 0.5 * n_cols
    while eye.processed_count() < n_expected:
        if time.monotonic() > deadline:
            raise RuntimeError(f"TIMEOUT: eye processed {eye.processed_count()} epochs, expected "
                               f"{n_expected} ({n_cols} columns); aborting, no partial data")
        time.sleep(0.002)
    if eye.processed_count() != n_expected:
        raise RuntimeError(f"processed {eye.processed_count()} != {n_expected}")
    snap = eye.latest()
    if snap is None or int(snap["sensor_epoch"]) != n_expected:
        raise RuntimeError(f"snapshot epoch {snap and snap['sensor_epoch']} != {n_expected}")
    if len(snap["percepts"]) != n_cols:
        raise RuntimeError(f"{len(snap['percepts'])} percepts for {n_cols} columns")
    return snap


RCLS = ("l", "m", "s", "rod")


def read_receptors(eye, col):
    out = {}
    for c in RCLS:
        a = eye.substrate.node(eye._receptors[(col, c)])["attrs"]
        out[c] = {"caught_quanta": float(a["caught_quanta"]), "activation": float(a["activation"]),
                  "adaptation_after_epoch": float(a["adaptation"]),
                  "input_epoch": int(a.get("input_epoch", -1))}
    return out


def read_col(eye, snap, col):
    p = snap["percepts"][col]
    return {"red_green": float(p["red_green"]), "blue_yellow": float(p["blue_yellow"]),
            "intensity": float(p["intensity"]), "receptors": read_receptors(eye, col)}


def run_batch(GraphEye, items, tag):
    """items: list of (key, [packet dicts with column already = position])."""
    n = len(items)
    eye = GraphEye(n_az=n, context={"worker_capacity": 1}).build()
    try:
        pk = []
        for col, (key, packets) in enumerate(items):
            assert all(p["column"] == col for p in packets), key
            pk.extend(packets)
        t0 = time.monotonic()
        eye.submit_photons(pk)
        snap = wait_epochs(eye, 1, n)
        dt = time.monotonic() - t0
        out = {}
        for col, (key, _) in enumerate(items):
            r = read_col(eye, snap, col)
            r["eye_run"] = {"run": tag, "column": col, "n_az": n, "epochs": 1}
            out[key] = r
        return out, dt
    finally:
        eye.stop()


def run_adaptation(GraphEye, entry, eye_packets):
    from scripts.marys_room_broad_theory import packets_sha
    prot = entry["protocol"]
    af = prot["adapting_field"]
    assert packets_sha(af["packets"]) == af["packets_sha256"], entry["id"]
    adapt = [{"column": 0, "wavelength_nm": float(w), "count": int(c)} for w, c in af["packets"]]
    test = eye_packets(entry, 0)
    eye = GraphEye(n_az=1, context={"worker_capacity": 1}).build()
    try:
        trace = []
        for k in range(1, prot["adapt_epochs"] + 1):
            eye.submit_photons(adapt)
            snap = wait_epochs(eye, k, 1)
            p = snap["percepts"][0]
            trace.append([float(p["red_green"]), float(p["blue_yellow"])])
        pre = read_receptors(eye, 0)
        eye.submit_photons(test)
        snap = wait_epochs(eye, prot["adapt_epochs"] + prot["test_epochs"], 1)
        r = read_col(eye, snap, 0)
        r["adaptation_before_test"] = {c: pre[c]["adaptation_after_epoch"] for c in RCLS}
        r["adapting_field_percept_trace"] = trace
        r["eye_run"] = {"run": f"adapt:{entry['id']}", "column": 0, "n_az": 1,
                        "epochs": prot["adapt_epochs"] + prot["test_epochs"]}
        return r
    finally:
        eye.stop()


# ------------------------------------------------------------------ main

def main():
    T0 = time.monotonic()
    freeze = verify_freeze()
    print("freeze OK:", freeze["n_files_checked"], "files")

    from domains.engine_provenance import engine_preamble, provenance_line
    engine_preamble()
    prov = provenance_line()
    if EXPECTED_ENGINE not in prov:
        raise SystemExit(f"ABORT: engine provenance {prov!r} lacks expected {EXPECTED_ENGINE}")
    import numpy as np
    from domains import spectral_forward as sf
    import scripts.marys_room_broad_theory as th
    from domains.photon_eye import GraphEye  # noqa: E402  (after engine_preamble)

    manifest = th.load_manifest()
    arma = json.loads(th.ARMA_PATH.read_text())
    anchors = arma["anchors"]
    S = manifest["stimuli"]
    idx = {e["id"]: e for e in S}
    arow = {r["id"]: r for r in arma["per_stimulus"]}

    # ---- 2. manifest integrity
    spd_cache = {}
    n_chk = 0
    for e in S:
        ei = e["eye_input"]
        if "packets" not in ei:
            continue
        if th.packets_sha(ei["packets"]) != ei["packets_sha256"]:
            raise SystemExit(f"ABORT: packets sha mismatch {e['id']}")
        spd = th.spd_from_recipe(ei["recipe"])
        if th.spd_sha(spd) != ei["spd_sha256"]:
            raise SystemExit(f"ABORT: spd sha mismatch {e['id']}")
        spd_cache[e["id"]] = spd
        n_chk += 1
    integrity = {"entries_with_packets_checked": n_chk, "packets_sha256_and_spd_sha256_all_match": True}
    print("manifest integrity OK:", n_chk)

    # ---- 3. pilot regression
    pil = [e for e in S if e["family"] == "pilot_regression"]
    eye = GraphEye(n_az=2, context={"worker_capacity": 1}).build()
    try:
        pk = []
        for e in pil:
            pk += th.eye_packets(e, e["params"]["column"])
        eye.submit_photons(pk)
        snap = wait_epochs(eye, 1, 2)
        pilot_out = {}
        for e in pil:
            col = e["params"]["column"]
            r = read_col(eye, snap, col)
            r["eye_run"] = {"run": "pilot", "column": col, "n_az": 2, "epochs": 1}
            pilot_out[e["id"]] = r
    finally:
        eye.stop()
    pilot = []
    for e in pil:
        r = pilot_out[e["id"]]
        exp = e["expected_eye"]
        pilot.append({"id": e["id"], "expected": [exp["red_green"], exp["blue_yellow"]],
                      "observed": [r["red_green"], r["blue_yellow"]],
                      "exact": r["red_green"] == exp["red_green"] and r["blue_yellow"] == exp["blue_yellow"]})
    pilot_ok = all(p["exact"] for p in pilot)
    print("pilot regression exact:", pilot_ok, pilot)

    # ---- supplementary eyelid references (declared above, before any run)
    refs = {}
    for e in S:
        if e["family"] != "eyelid":
            continue
        td = e["eye_input"]["td"]
        for wl in REF_WL:
            q = 1000.0 * td / sf.retinal_illuminance_td(sf.monochromatic_spd(wl, 1000.0))
            spd = sf.monochromatic_spd(wl, q)
            refs[f"ref_{e['id']}_{wl}nm_tdmatch"] = {"base": e["id"], "wavelength_nm": wl, "match": "td",
                                                      "quanta_expected": q, "td": sf.retinal_illuminance_td(spd),
                                                      "packets": th.packets_compact(spd), "spd": spd}
        q = float(e["eye_input"]["packets_total"])
        spd = sf.monochromatic_spd(640, q)
        refs[f"ref_{e['id']}_640nm_quantamatch"] = {"base": e["id"], "wavelength_nm": 640, "match": "packets_total",
                                                     "quanta_expected": q, "td": sf.retinal_illuminance_td(spd),
                                                     "packets": th.packets_compact(spd), "spd": spd}

    # ---- 5. batched runs
    to_run = [e for e in S if "packets" in e["eye_input"] and e["family"] not in ("adaptation", "pilot_regression")]
    bs = ARM_B_DECLARATIONS["execution"]["batch_size_columns"]
    eye_out, batch_log = {}, []
    for b in range(0, len(to_run), bs):
        chunk = to_run[b:b + bs]
        items = [(e["id"], th.eye_packets(e, i)) for i, e in enumerate(chunk)]
        out, dt = run_batch(GraphEye, items, f"batch{b // bs:02d}")
        eye_out.update(out)
        batch_log.append({"run": f"batch{b // bs:02d}", "n_columns": len(chunk), "seconds": dt,
                          "first": chunk[0]["id"], "last": chunk[-1]["id"]})
    ref_items = []
    for i, (k, v) in enumerate(refs.items()):
        ref_items.append((k, [{"column": i, "wavelength_nm": float(w), "count": int(c)} for w, c in v["packets"]]))
    ref_out, dt = run_batch(GraphEye, ref_items, "batch_eyelid_refs")
    batch_log.append({"run": "batch_eyelid_refs", "n_columns": len(ref_items), "seconds": dt})
    print("batched runs done:", len(eye_out), "+", len(ref_out), "refs")

    # ---- 4. equivalence check: batched vs fresh single-column eye
    equiv = []
    for sid in EQUIV_IDS:
        e = idx[sid]
        single, _ = run_batch(GraphEye, [(sid, th.eye_packets(e, 0))], f"fresh:{sid}")
        a, s = eye_out[sid], single[sid]
        same = (a["red_green"] == s["red_green"] and a["blue_yellow"] == s["blue_yellow"]
                and a["intensity"] == s["intensity"]
                and all(a["receptors"][c][k] == s["receptors"][c][k] for c in RCLS
                        for k in ("caught_quanta", "activation", "adaptation_after_epoch")))
        equiv.append({"id": sid, "batched": [a["red_green"], a["blue_yellow"]],
                      "batched_run": a["eye_run"], "fresh_single": [s["red_green"], s["blue_yellow"]],
                      "byte_identical_rg_by": a["red_green"] == s["red_green"] and a["blue_yellow"] == s["blue_yellow"],
                      "byte_identical_all_recorded_state": same})
    equiv_ok = all(x["byte_identical_all_recorded_state"] for x in equiv)
    print("batched==fresh on", len(equiv), "stimuli:", equiv_ok)
    if not equiv_ok:
        print("WARNING: batched/fresh equivalence FAILED; batched results reported as measured", file=sys.stderr)

    # ---- 6. adaptation
    for e in S:
        if e["family"] == "adaptation":
            eye_out[e["id"]] = run_adaptation(GraphEye, e, th.eye_packets)
    eye_out.update(pilot_out)
    print("adaptation runs done")
    eye_runtime = time.monotonic() - T0

    # ================================================================== scoring
    SIGN_TO_BINARY = th.SIGN_TO_BINARY

    def lin_opp(rec):
        L, M, Sx = (rec[c]["caught_quanta"] for c in ("l", "m", "s"))
        return (L - M, Sx - 0.5 * (L + M))

    rows = []
    replica_max = {"caught": 0.0, "activation": 0.0, "rg_by": 0.0, "n": 0}
    for e in S:
        a = arow[e["id"]]
        tp = a["theory_primary"]
        ei = e["eye_input"]
        if "identical_to" in ei:
            src = ei["identical_to"]
            ev = eye_out[src]
            eye_source = f"identical_to:{src}"
            spd = spd_cache[src]
            packets = idx[src]["eye_input"]["packets"]
        else:
            ev = eye_out[e["id"]]
            eye_source = "own"
            spd = spd_cache[e["id"]]
            packets = ei["packets"]
        erg, eby = ev["red_green"], ev["blue_yellow"]
        d = th.decode(erg, eby, anchors)
        ang, cos = vangle((tp["rg"], tp["by"]), (erg, eby))
        # decomposition legs
        exp_rep = sf.eye_capture_expected(spd)
        lin_exp = (exp_rep["l"]["caught"] - exp_rep["m"]["caught"],
                   exp_rep["s"]["caught"] - 0.5 * (exp_rep["l"]["caught"] + exp_rep["m"]["caught"]))
        lin_q = lin_opp(ev["receptors"])
        legs = {"mismatch_theory_to_gausslin_expected_deg": vangle((tp["rg"], tp["by"]), lin_exp)[0],
                "quantisation_gausslin_expected_to_quantised_deg": vangle(lin_exp, lin_q)[0],
                "nonlinearity_gausslin_quantised_to_eye_deg": vangle(lin_q, (erg, eby))[0]}
        if e["family"] != "adaptation":
            rep = sf.eye_capture_model([{"wavelength_nm": w, "count": c} for w, c in packets])
            for c in ("l", "m", "s", "rod"):
                replica_max["caught"] = max(replica_max["caught"], abs(rep[c]["caught"] - ev["receptors"][c]["caught_quanta"]))
                replica_max["activation"] = max(replica_max["activation"],
                                                abs(rep[c]["activation"] - ev["receptors"][c]["activation"]))
            replica_max["rg_by"] = max(replica_max["rg_by"], abs(rep["red_green"] - erg), abs(rep["blue_yellow"] - eby))
            replica_max["n"] += 1
        lms = tp["lms"]
        scored = a["hue_scored"]
        tr = a["truth"]
        row = {
            "id": e["id"], "family": e["family"], "split": e["split"], "adversarial": e.get("adversarial", False),
            "duplicate_of": ei.get("duplicate_of"), "eye_source": eye_source, "eye_run": ev["eye_run"],
            "wavelength_nm": e["params"].get("wavelength_nm"), "quanta": e["params"].get("quanta"),
            "dist_from_rg_zero_nm": a.get("dist_from_rg_zero_nm"),
            "td": idx[eye_source.split(":", 1)[1]]["eye_input"]["td"] if "identical_to" in ei else ei["td"],
            "packets_total": (idx[eye_source.split(":", 1)[1]]["eye_input"] if "identical_to" in ei else ei)["packets_total"],
            "packets_sha256": (idx[eye_source.split(":", 1)[1]]["eye_input"] if "identical_to" in ei else ei)["packets_sha256"],
            "truth": tr, "hue_scored": scored,
            "theory": {"observer": tp["observer"], "lms": lms, "rg": tp["rg"], "by": tp["by"], "rg_rel": tp["rg_rel"],
                       "by_rel": tp["by"] / (lms[0] + lms[1]) if (lms[0] + lms[1]) > 0 else float("nan"),
                       "sign": tp["sign_label"], "sign_margin_rel": tp["sign_margin_rel"],
                       "multi": tp["multi_label"], "multi_margin_deg": tp["multi_margin_deg"]},
            "theory_2deg": {"rg": a["theory_2deg"]["rg"], "by": a["theory_2deg"]["by"],
                            "sign": a["theory_2deg"]["sign_label"], "multi": a["theory_2deg"]["multi_label"]},
            "eye": {"red_green": erg, "blue_yellow": eby, "intensity": ev["intensity"], "receptors": ev["receptors"],
                    "sign": d["sign"], "multi": d["multi"], "multi_margin_deg": d["multi_margin_deg"],
                    "opponent_angle_deg": math.degrees(math.atan2(eby, erg)) if (erg or eby) else None},
            "theory_sign_correct": a["sign_correct"], "theory_multi_correct": a["multi_correct"],
            "eye_sign_correct": (SIGN_TO_BINARY.get(d["sign"]) == tr["binary"]) if scored else None,
            "eye_multi_correct": (d["multi"] == tr["hue4"]) if scored else None,
            "angle_err_deg": ang, "cosine": cos, "legs": legs,
            "gausslin_expected": list(lin_exp), "gausslin_quantised": list(lin_q),
        }
        if "adaptation_before_test" in ev:
            row["eye"]["adaptation_before_test"] = ev["adaptation_before_test"]
            row["eye"]["adapting_field_percept_trace"] = ev["adapting_field_percept_trace"]
        row["agree_sign"] = row["theory"]["sign"] == row["eye"]["sign"]
        row["agree_multi"] = row["theory"]["multi"] == row["eye"]["multi"]
        rows.append(row)
    R = {r["id"]: r for r in rows}

    # ---- deterministic duplicates
    dups = []
    for r in rows:
        if r["duplicate_of"]:
            o = R[r["duplicate_of"]]
            dups.append({"id": r["id"], "duplicate_of": r["duplicate_of"],
                         "identical": (r["eye"]["red_green"], r["eye"]["blue_yellow"]) == (o["eye"]["red_green"], o["eye"]["blue_yellow"]),
                         "different_column_or_batch": r["eye_run"] != o["eye_run"]})

    # ---- pools (same definitions as Arm A)
    core_fams = {"mono_sweep", "boundary_dense", "illuminant", "reflectance", "metamer", "eyelid"}

    def pool(pred):
        sel_all = [r for r in rows if pred(r)]
        sel = [r for r in sel_all if r["hue_scored"]]
        out = {"n_entries": len(sel_all), "n_achromatic_excluded": len(sel_all) - len(sel)}
        out["eye_sign_rule_binary"] = th.score([r["truth"]["binary"] for r in sel],
                                               [SIGN_TO_BINARY.get(r["eye"]["sign"], "undecided") for r in sel], th.BINARY)
        out["eye_multi_anchor_hue4"] = th.score([r["truth"]["hue4"] for r in sel], [r["eye"]["multi"] for r in sel], th.HUE4)
        out["theory_sign_accuracy"] = (sum(r["theory_sign_correct"] for r in sel) / len(sel)) if sel else None
        out["theory_multi_accuracy"] = (sum(r["theory_multi_correct"] for r in sel) / len(sel)) if sel else None
        out["agreement_theory_eye_sign_all"] = agree([{"a": r["theory"]["sign"], "b": r["eye"]["sign"]} for r in sel_all], "a", "b")
        out["agreement_theory_eye_multi_all"] = agree([{"a": r["theory"]["multi"], "b": r["eye"]["multi"]} for r in sel_all], "a", "b")
        out["angular_error"] = ang_summary([r["angle_err_deg"] for r in sel_all])
        return out

    pools = {
        "TRAIN": pool(lambda r: r["split"] == "train"),
        "HELDOUT_core": pool(lambda r: r["split"] == "heldout" and r["family"] in core_fams and r["duplicate_of"] is None),
        "HELDOUT_core_incl_duplicates": pool(lambda r: r["split"] == "heldout" and r["family"] in core_fams),
        "ADVERSARIAL_wrong_optics": pool(lambda r: r["family"] == "wrong_optics"),
        "ADVERSARIAL_wrong_observer_10deg": pool(lambda r: r["family"] == "wrong_observer"),
        "ADAPTATION": pool(lambda r: r["family"] == "adaptation"),
        "POISSON": pool(lambda r: r["family"] == "poisson"),
        "ABLATION_grid5": pool(lambda r: r["family"] == "ablation_grid5"),
    }
    per_family = {}
    for fam in sorted({r["family"] for r in rows}):
        for sp in sorted({r["split"] for r in rows if r["family"] == fam}):
            per_family[f"{fam}/{sp}"] = pool(lambda r, f=fam, s=sp: r["family"] == f and r["split"] == s)
    for ill in th.ILLUMS:
        per_family[f"reflectance/heldout/{ill}"] = pool(lambda r, i=ill: r["family"] == "reflectance" and r["id"].endswith("_" + i))
    for q in th.INTENSITIES_Q:
        per_family[f"mono+boundary/q{q}"] = pool(lambda r, q=q: r["family"] in ("mono_sweep", "boundary_dense") and r["quanta"] == q)

    # ---- error vs distance from RG zero and vs |RG|
    mb = [r for r in rows if r["family"] in ("mono_sweep", "boundary_dense")]

    def bin_block(sel):
        sc = [r for r in sel if r["hue_scored"]]
        mean = lambda xs: (float(np.mean(xs)) if xs else None)  # noqa: E731
        return {"n": len(sel), "n_scored": len(sc),
                "theory_sign_acc": mean([r["theory_sign_correct"] for r in sc]),
                "eye_sign_acc": mean([r["eye_sign_correct"] for r in sc]),
                "theory_multi_acc": mean([r["theory_multi_correct"] for r in sc]),
                "eye_multi_acc": mean([r["eye_multi_correct"] for r in sc]),
                "agree_sign": mean([r["agree_sign"] for r in sel]), "agree_multi": mean([r["agree_multi"] for r in sel]),
                "angle_median_deg": (float(np.median([r["angle_err_deg"] for r in sel if r["angle_err_deg"] is not None]))
                                     if any(r["angle_err_deg"] is not None for r in sel) else None),
                "angle_mean_deg": mean([r["angle_err_deg"] for r in sel if r["angle_err_deg"] is not None])}

    vs_dist = {}
    for q in list(th.INTENSITIES_Q) + ["pooled"]:
        tab = []
        for lo, hi in ARM_B_DECLARATIONS["dist_bins_nm"]:
            sel = [r for r in mb if (q == "pooled" or r["quanta"] == q) and lo <= abs(r["dist_from_rg_zero_nm"]) < hi]
            if sel:
                tab.append({"abs_dist_nm": [lo, hi], **bin_block(sel)})
        vs_dist[str(q)] = tab

    def binned(sel, key, edges):
        tab = []
        for lo, hi in zip(edges[:-1], edges[1:]):
            s = [r for r in sel if r[key] is not None and lo <= r[key] < hi]
            if s:
                tab.append({"bin": [lo, hi], **bin_block(s)})
        return tab

    for r in rows:
        r["_abs_rg_rel"] = abs(r["theory"]["rg_rel"]) if r["theory"]["rg_rel"] == r["theory"]["rg_rel"] else None
        r["_abs_eye_rg"] = abs(r["eye"]["red_green"])
    core_distinct = [r for r in rows if ((r["split"] == "heldout" and r["family"] in core_fams) or r["split"] == "train")
                     and r["duplicate_of"] is None]
    vs_rg = {"mono+boundary_by_theory_abs_rg_rel": binned(mb, "_abs_rg_rel", ARM_B_DECLARATIONS["rg_rel_bins"]),
             "core_distinct_by_theory_abs_rg_rel": binned(core_distinct, "_abs_rg_rel", ARM_B_DECLARATIONS["rg_rel_bins"]),
             "mono+boundary_by_eye_abs_rg": binned(mb, "_abs_eye_rg", ARM_B_DECLARATIONS["eye_abs_rg_bins"])}

    # 1-nm boundary table (window) and eye zero crossings
    window = sorted([r for r in mb if abs(r["dist_from_rg_zero_nm"]) <= 20.0], key=lambda r: (r["quanta"], r["wavelength_nm"]))
    boundary_table = [{"wavelength_nm": r["wavelength_nm"], "quanta": r["quanta"], "theory_rg_rel": r["theory"]["rg_rel"],
                       "eye_rg": r["eye"]["red_green"], "eye_by": r["eye"]["blue_yellow"],
                       "theory_sign": r["theory"]["sign"], "eye_sign": r["eye"]["sign"],
                       "theory_multi": r["theory"]["multi"], "eye_multi": r["eye"]["multi"],
                       "truth_binary": r["truth"]["binary"], "truth_hue4": r["truth"]["hue4"],
                       "angle_err_deg": r["angle_err_deg"]} for r in window]
    zc = {}
    for q in th.INTENSITIES_Q:
        s = sorted([r for r in mb if r["quanta"] == q], key=lambda r: r["wavelength_nm"])
        wl = np.array([r["wavelength_nm"] for r in s], float)
        zc[f"q{q}"] = {"eye_red_green_zero_nm": sf.zero_crossings(np.array([r["eye"]["red_green"] for r in s]), wl),
                       "eye_blue_yellow_zero_nm": sf.zero_crossings(np.array([r["eye"]["blue_yellow"] for r in s]), wl),
                       "theory_rg_zero_nm_cie2deg": th.RG_ZERO_NM}

    # ---- calibration
    calib = {"per_intensity": {}}
    for q in th.INTENSITIES_Q:
        s = [r for r in mb if r["quanta"] == q]
        x = np.array([r["theory"]["rg_rel"] for r in s])
        y = np.array([r["eye"]["red_green"] for r in s])
        xb = np.array([r["theory"]["by_rel"] for r in s])
        yb = np.array([r["eye"]["blue_yellow"] for r in s])
        calib["per_intensity"][f"q{q}"] = {
            "rg": {**corr(x, y), "through_origin_slope": float(np.sum(x * y) / np.sum(x * x))},
            "by": {**corr(xb, yb), "through_origin_slope": float(np.sum(xb * yb) / np.sum(xb * xb))},
            "eye_opponent_norm_median": float(np.median(np.hypot(y, yb))),
            "td_median": float(np.median([r["td"] for r in s]))}
    tr1000 = [r for r in rows if r["family"] == "mono_sweep" and r["split"] == "train" and r["quanta"] == 1000]
    x = np.array([r["theory"]["rg_rel"] for r in tr1000]); y = np.array([r["eye"]["red_green"] for r in tr1000])
    a_rg = float(np.sum(x * y) / np.sum(x * x))
    calib["train_1000q_through_origin_slope_rg"] = a_rg
    td_edges = [0, 1, 10, 50, 100, 200, 500, 2000, 1e9]
    hc = [r for r in rows if r["split"] == "heldout" and r["family"] in core_fams and r["duplicate_of"] is None]
    res_tab = []
    for lo, hi in zip(td_edges[:-1], td_edges[1:]):
        s = [r for r in hc if lo <= r["td"] < hi and r["theory"]["rg_rel"] == r["theory"]["rg_rel"]]
        if s:
            res = np.array([r["eye"]["red_green"] - a_rg * r["theory"]["rg_rel"] for r in s])
            ratio = [abs(r["eye"]["red_green"]) / abs(a_rg * r["theory"]["rg_rel"]) for r in s if r["theory"]["rg_rel"] != 0]
            res_tab.append({"td_bin": [lo, hi], "n": len(s), "residual_mean": float(res.mean()),
                            "residual_rms": float(np.sqrt(np.mean(res ** 2))),
                            "median_abs_ratio_eye_over_predicted": float(np.median(ratio)) if ratio else None,
                            "families": sorted({r["family"] for r in s})})
    calib["heldout_core_residual_vs_td"] = res_tab
    calib["note"] = ("theory rg_rel is a scale-free cone contrast; the eye red_green is an activation difference. "
                     "A linear (no Naka-Rushton) eye would show equal slopes at all intensities; slope changes "
                     "with intensity are the nonlinearity signature. Descriptive only.")

    # ---- decomposition summary
    def legs_summary(sel):
        out = {}
        for k in ("mismatch_theory_to_gausslin_expected_deg", "quantisation_gausslin_expected_to_quantised_deg",
                  "nonlinearity_gausslin_quantised_to_eye_deg"):
            v = [r["legs"][k] for r in sel if r["legs"][k] is not None]
            out[k] = {"median": float(np.median(v)) if v else None, "mean": float(np.mean(v)) if v else None,
                      "max": float(np.max(v)) if v else None}
        v = [r["angle_err_deg"] for r in sel if r["angle_err_deg"] is not None]
        out["total_theory_to_eye_deg"] = {"median": float(np.median(v)) if v else None,
                                          "mean": float(np.mean(v)) if v else None}
        out["n"] = len(sel)
        return out
    near = [r for r in mb if abs(r["dist_from_rg_zero_nm"]) <= ARM_B_DECLARATIONS["near_boundary_window_nm"]]
    far = [r for r in mb if abs(r["dist_from_rg_zero_nm"]) > ARM_B_DECLARATIONS["near_boundary_window_nm"]]
    decomposition = {"near_boundary_mono": legs_summary(near), "far_mono": legs_summary(far),
                     "heldout_core_distinct": legs_summary(hc),
                     "per_intensity_near": {f"q{q}": legs_summary([r for r in near if r["quanta"] == q]) for q in th.INTENSITIES_Q},
                     "replica_vs_eye_max_abs_diff_unadapted": replica_max}

    # ---- metamers
    met = []
    for e in S:
        if e["family"] == "metamer" and e["id"].endswith("_b"):
            ra, rb = R[e["id"][:-1] + "a"], R[e["id"]]
            ga = math.hypot(ra["eye"]["red_green"] - rb["eye"]["red_green"], ra["eye"]["blue_yellow"] - rb["eye"]["blue_yellow"])
            na = math.hypot(ra["eye"]["red_green"], ra["eye"]["blue_yellow"])
            ea, eb = sf.eye_capture_expected(spd_cache[ra["id"]]), sf.eye_capture_expected(spd_cache[rb["id"]])
            gexp = math.hypot(ea["red_green"] - eb["red_green"], ea["blue_yellow"] - eb["blue_yellow"])
            mt = next(m for m in arma["metamer_theory"] if m["pair_id"] == e["pair_id"])
            met.append({"pair_id": e["pair_id"], "cie2_theory_gap_rel": mt["theory_gap_rel"],
                        "cie10_theory_gap_rel": mt["theory_10deg_gap_rel"],
                        "eye_a": [ra["eye"]["red_green"], ra["eye"]["blue_yellow"]],
                        "eye_b": [rb["eye"]["red_green"], rb["eye"]["blue_yellow"]],
                        "eye_gap": ga, "eye_gap_rel_to_norm_a": ga / na if na else None,
                        "eye_gap_angle_deg": vangle((ra["eye"]["red_green"], ra["eye"]["blue_yellow"]),
                                                    (rb["eye"]["red_green"], rb["eye"]["blue_yellow"]))[0],
                        "replica_expected_continuous_gap": gexp,
                        "eye_labels_a_b": [[ra["eye"]["sign"], ra["eye"]["multi"]], [rb["eye"]["sign"], rb["eye"]["multi"]]],
                        "eye_label_flip_sign": ra["eye"]["sign"] != rb["eye"]["sign"],
                        "eye_label_flip_multi": ra["eye"]["multi"] != rb["eye"]["multi"],
                        "truth_a_b": [ra["truth"]["hue4"], rb["truth"]["hue4"]],
                        "measurable": ga > ARM_B_DECLARATIONS["metamer_measurable_gap"]})

    # ---- wrong observer
    wob = [r for r in rows if r["family"] == "wrong_observer"]
    wob_pairs = []
    for r in wob:
        base = R[idx[r["id"]]["params"]["base_id"]]
        wob_pairs.append({"id": r["id"], "base": base["id"], "angle_10deg": r["angle_err_deg"], "angle_2deg": base["angle_err_deg"],
                          "scored": r["hue_scored"], "sign10_correct": r["theory_sign_correct"], "sign2_correct": base["theory_sign_correct"],
                          "multi10_correct": r["theory_multi_correct"], "multi2_correct": base["theory_multi_correct"],
                          "agree_sign10_eye": r["agree_sign"], "agree_sign2_eye": base["agree_sign"],
                          "agree_multi10_eye": r["agree_multi"], "agree_multi2_eye": base["agree_multi"]})

    def cond_block(pairs, ka, kb, labels):
        sc = [p for p in pairs if p["scored"]]
        mean = lambda xs: (float(np.mean(xs)) if xs else None)  # noqa: E731
        a1 = [p[ka] for p in pairs if p[ka] is not None]; a0 = [p[kb] for p in pairs if p[kb] is not None]
        return {"n": len(pairs), "n_scored": len(sc),
                f"angle_median_{labels[0]}": float(np.median(a1)), f"angle_median_{labels[1]}": float(np.median(a0)),
                f"angle_mean_{labels[0]}": float(np.mean(a1)), f"angle_mean_{labels[1]}": float(np.mean(a0)),
                "paired_frac_worse": mean([p[ka] > p[kb] for p in pairs if p[ka] is not None and p[kb] is not None])}

    wob_summary = cond_block(wob_pairs, "angle_10deg", "angle_2deg", ("theory10", "theory2"))
    sc = [p for p in wob_pairs if p["scored"]]
    wob_summary.update({"theory_sign_acc_10deg": float(np.mean([p["sign10_correct"] for p in sc])),
                        "theory_sign_acc_2deg": float(np.mean([p["sign2_correct"] for p in sc])),
                        "theory_multi_acc_10deg": float(np.mean([p["multi10_correct"] for p in sc])),
                        "theory_multi_acc_2deg": float(np.mean([p["multi2_correct"] for p in sc])),
                        "agree_sign_eye_10deg": float(np.mean([p["agree_sign10_eye"] for p in wob_pairs])),
                        "agree_sign_eye_2deg": float(np.mean([p["agree_sign2_eye"] for p in wob_pairs])),
                        "agree_multi_eye_10deg": float(np.mean([p["agree_multi10_eye"] for p in wob_pairs])),
                        "agree_multi_eye_2deg": float(np.mean([p["agree_multi2_eye"] for p in wob_pairs]))})

    # ---- wrong optics
    wopt = {}
    for filt in ("lens", "macular"):
        pairs = []
        for r in rows:
            if r["family"] == "wrong_optics" and f"_{filt}_" in r["id"]:
                p = idx[r["id"]]["params"]["patch"]
                base = R[f"refl_{p:02d}_D65"]
                pairs.append({"id": r["id"], "base": base["id"], "angle_filtered": r["angle_err_deg"],
                              "angle_base": base["angle_err_deg"], "scored": r["hue_scored"] and base["hue_scored"],
                              "theory_sign_correct_f": r["theory_sign_correct"], "theory_sign_correct_b": base["theory_sign_correct"],
                              "theory_multi_correct_f": r["theory_multi_correct"], "theory_multi_correct_b": base["theory_multi_correct"],
                              "eye_sign_correct_f": r["eye_sign_correct"], "eye_multi_correct_f": r["eye_multi_correct"],
                              "eye_shift_deg_filtered_vs_unfiltered": vangle((r["eye"]["red_green"], r["eye"]["blue_yellow"]),
                                                                             (base["eye"]["red_green"], base["eye"]["blue_yellow"]))[0]})
        b = cond_block(pairs, "angle_filtered", "angle_base", ("filtered", "base"))
        s2 = [p for p in pairs if p["scored"]]
        b.update({"theory_sign_acc_filtered_truth": float(np.mean([p["theory_sign_correct_f"] for p in s2])),
                  "theory_sign_acc_base": float(np.mean([p["theory_sign_correct_b"] for p in s2])),
                  "theory_multi_acc_filtered_truth": float(np.mean([p["theory_multi_correct_f"] for p in s2])),
                  "theory_multi_acc_base": float(np.mean([p["theory_multi_correct_b"] for p in s2])),
                  "eye_sign_acc_filtered": float(np.mean([p["eye_sign_correct_f"] for p in s2])),
                  "eye_multi_acc_filtered": float(np.mean([p["eye_multi_correct_f"] for p in s2])),
                  "eye_shift_median_deg": float(np.median([p["eye_shift_deg_filtered_vs_unfiltered"] for p in pairs
                                                           if p["eye_shift_deg_filtered_vs_unfiltered"] is not None])),
                  "pairs": pairs})
        wopt[filt] = b

    # ---- adaptation
    def ctrl_id(test):
        if test == "whiteE":
            return "illum_E_100td"
        wl = int(test[4:])
        return f"mono_{wl}nm_q1000" if wl % 5 == 0 else f"bnd_{wl}nm_q1000"
    adapt = []
    for r in rows:
        if r["family"] != "adaptation":
            continue
        p = idx[r["id"]]["params"]
        c = R[ctrl_id(p["test"])]
        assert c["packets_sha256"] == r["packets_sha256"], (r["id"], c["id"])
        adapt.append({"id": r["id"], "field": p["adapting_field"], "test": p["test"], "control": c["id"],
                      "eye_unadapted": [c["eye"]["red_green"], c["eye"]["blue_yellow"]],
                      "eye_adapted": [r["eye"]["red_green"], r["eye"]["blue_yellow"]],
                      "shift_deg": vangle((c["eye"]["red_green"], c["eye"]["blue_yellow"]),
                                          (r["eye"]["red_green"], r["eye"]["blue_yellow"]))[0],
                      "rg_sign_flip": (c["eye"]["red_green"] > 0) != (r["eye"]["red_green"] > 0),
                      "eye_sign_unadapted": c["eye"]["sign"], "eye_sign_adapted": r["eye"]["sign"],
                      "eye_multi_unadapted": c["eye"]["multi"], "eye_multi_adapted": r["eye"]["multi"],
                      "theory_sign": r["theory"]["sign"], "theory_multi": r["theory"]["multi"],
                      "truth_binary": r["truth"]["binary"], "truth_hue4": r["truth"]["hue4"],
                      "angle_theory_adapted": r["angle_err_deg"], "angle_theory_unadapted": c["angle_err_deg"],
                      "adaptation_before_test": r["eye"]["adaptation_before_test"]})
    asc = [a for a in adapt if a["truth_binary"] != "achromatic"]
    adapt_summary = {"n": len(adapt), "n_scored": len(asc),
                     "eye_sign_acc_adapted": float(np.mean([SIGN_TO_BINARY.get(a["eye_sign_adapted"]) == a["truth_binary"] for a in asc])),
                     "eye_sign_acc_unadapted": float(np.mean([SIGN_TO_BINARY.get(a["eye_sign_unadapted"]) == a["truth_binary"] for a in asc])),
                     "eye_multi_acc_adapted": float(np.mean([a["eye_multi_adapted"] == a["truth_hue4"] for a in asc])),
                     "eye_multi_acc_unadapted": float(np.mean([a["eye_multi_unadapted"] == a["truth_hue4"] for a in asc])),
                     "angle_median_theory_adapted": float(np.median([a["angle_theory_adapted"] for a in adapt if a["angle_theory_adapted"] is not None])),
                     "angle_median_theory_unadapted": float(np.median([a["angle_theory_unadapted"] for a in adapt if a["angle_theory_unadapted"] is not None])),
                     "n_rg_sign_flips": sum(a["rg_sign_flip"] for a in adapt),
                     "per_field": {}}
    for f in ("adapt610", "adapt530", "adaptE"):
        s = [a for a in adapt if a["field"] == f]
        adapt_summary["per_field"][f] = {"median_shift_deg": float(np.median([a["shift_deg"] for a in s if a["shift_deg"] is not None])),
                                         "n_rg_sign_flips": sum(a["rg_sign_flip"] for a in s),
                                         "agree_sign_theory_adapted": float(np.mean([a["theory_sign"] == a["eye_sign_adapted"] for a in s]))}

    # ---- poisson
    def det_id(sub):
        if sub == "whiteE100":
            return "illum_E_100td"
        if sub.startswith("lidD65od1.3_"):
            return f"lid_D65_od1.3_{sub.split('_')[1]}"
        wl = int(sub[4:])
        return f"mono_{wl}nm_q1000" if wl % 5 == 0 else f"bnd_{wl}nm_q1000"
    pois = []
    subs = sorted({idx[r["id"]]["params"]["subset"] for r in rows if r["family"] == "poisson"},
                  key=lambda s: next(idx[r["id"]]["params"]["subset_index"] for r in rows if r["family"] == "poisson" and idx[r["id"]]["params"]["subset"] == s))
    for sub in subs:
        s = [r for r in rows if r["family"] == "poisson" and idx[r["id"]]["params"]["subset"] == sub]
        dr = R[det_id(sub)]
        rg = np.array([r["eye"]["red_green"] for r in s]); by = np.array([r["eye"]["blue_yellow"] for r in s])
        dv = (dr["eye"]["red_green"], dr["eye"]["blue_yellow"])
        angs = [vangle(dv, (a, b))[0] for a, b in zip(rg, by)]
        pois.append({"subset": sub, "n_trials": len(s), "independent_trials": True,
                     "seeds": [idx[r["id"]]["params"]["seed"] for r in s],
                     "deterministic_counterpart": dr["id"], "eye_det": list(dv),
                     "packets_total": [r["packets_total"] for r in s],
                     "rg_mean": float(rg.mean()), "rg_sd": float(rg.std(ddof=1)),
                     "by_mean": float(by.mean()), "by_sd": float(by.std(ddof=1)),
                     "rg_det_z": float((dv[0] - rg.mean()) / rg.std(ddof=1)) if rg.std(ddof=1) > 0 else None,
                     "angle_to_det_median_deg": float(np.median([a for a in angs if a is not None])) if any(a is not None for a in angs) else None,
                     "angle_to_det_max_deg": float(np.max([a for a in angs if a is not None])) if any(a is not None for a in angs) else None,
                     "eye_sign_counts": {k: sum(r["eye"]["sign"] == k for r in s) for k in ("red", "green", "undecided")},
                     "eye_multi_counts": {k: sum(r["eye"]["multi"] == k for r in s) for k in sorted({r["eye"]["multi"] for r in s})},
                     "truth": [s[0]["truth"]["binary"], s[0]["truth"]["hue4"]],
                     "theory": [s[0]["theory"]["sign"], s[0]["theory"]["multi"]],
                     "eye_det_labels": [dr["eye"]["sign"], dr["eye"]["multi"]],
                     "angle_theory_eye_median_deg": float(np.median([r["angle_err_deg"] for r in s if r["angle_err_deg"] is not None]))})

    # ---- EYELID named result
    pilot_red = R["mono_610nm_q1000"]["eye"]["red_green"]
    lid = []
    for r in rows:
        if r["family"] != "eyelid":
            continue
        p = idx[r["id"]]["params"]
        rec = r["eye"]["receptors"]
        ent = {"id": r["id"], "illuminant": p["illuminant"], "od_long": p["od_long"], "ambient_td": p["ambient_td"],
               "td_at_retina": r["td"], "packets_total": r["packets_total"],
               "eye_red_green": r["eye"]["red_green"], "eye_blue_yellow": r["eye"]["blue_yellow"],
               "eye_sign": r["eye"]["sign"], "eye_multi": r["eye"]["multi"],
               "L_act": rec["l"]["activation"], "M_act": rec["m"]["activation"], "S_act": rec["s"]["activation"],
               "L_caught": rec["l"]["caught_quanta"], "M_caught": rec["m"]["caught_quanta"],
               "eye_rg_contrast": (rec["l"]["activation"] - rec["m"]["activation"]) / (rec["l"]["activation"] + rec["m"]["activation"])
               if (rec["l"]["activation"] + rec["m"]["activation"]) > 0 else None,
               "theory_rg_rel": r["theory"]["rg_rel"], "theory_sign": r["theory"]["sign"], "theory_multi": r["theory"]["multi"],
               "truth_dominant_nm": r["truth"]["dominant_wavelength_nm"], "truth_hue4": r["truth"]["hue4"],
               "angle_err_deg": r["angle_err_deg"], "rg_over_pilot_610nm_1000q": r["eye"]["red_green"] / pilot_red,
               "refs": {}}
        for k, v in refs.items():
            if v["base"] == r["id"]:
                o = ref_out[k]
                rr = o["receptors"]
                lm = rr["l"]["activation"] + rr["m"]["activation"]
                ent["refs"][f"{v['wavelength_nm']}nm_{v['match']}"] = {
                    "td": v["td"], "quanta_expected": v["quanta_expected"], "packets": v["packets"],
                    "eye_red_green": o["red_green"], "eye_blue_yellow": o["blue_yellow"],
                    "eye_rg_contrast": (rr["l"]["activation"] - rr["m"]["activation"]) / lm if lm > 0 else None,
                    "eyelid_rg_over_ref_rg": (r["eye"]["red_green"] / o["red_green"]) if o["red_green"] != 0 else None}
        lid.append(ent)
    lid_summary = {"n": len(lid), "n_rg_positive": sum(e["eye_red_green"] > 0 for e in lid),
                   "per_od_long": {str(od): {"n": sum(e["od_long"] == od for e in lid),
                                             "n_rg_positive": sum(e["eye_red_green"] > 0 for e in lid if e["od_long"] == od)}
                                   for od in th.EYELID_OD_LONGS},
                   "rg_min": min(e["eye_red_green"] for e in lid), "rg_max": max(e["eye_red_green"] for e in lid),
                   "eye_multi_counts": {k: sum(e["eye_multi"] == k for e in lid) for k in sorted({e["eye_multi"] for e in lid})},
                   "pilot_610nm_1000q_red_green": pilot_red}

    # ---- verdicts
    verdicts = {}
    pf = arma["per_family"]
    s_mono, s_refl = pf["mono_sweep/heldout"], pf["reflectance/heldout"]
    beats = {dec: {"mono": s_mono[dec]["p_binom_vs_majority"] < 0.05, "reflectance": s_refl[dec]["p_binom_vs_majority"] < 0.05,
                   "mono_acc": s_mono[dec]["accuracy"], "mono_majority": s_mono[dec]["chance_majority_rate"],
                   "refl_acc": s_refl[dec]["accuracy"], "refl_majority": s_refl[dec]["chance_majority_rate"],
                   "p_mono": s_mono[dec]["p_binom_vs_majority"], "p_refl": s_refl[dec]["p_binom_vs_majority"]}
             for dec in ("sign_rule_binary", "multi_anchor_hue4")}
    dacc = [b["sign_accuracy"] for b in arma["accuracy_vs_distance_from_rg_zero_1000q"]]
    graceful = all(dacc[i] <= dacc[i + 1] + 1e-12 for i in range(len(dacc) - 1))
    ok_any = any(b["mono"] and b["reflectance"] for b in beats.values())
    ok_all = all(b["mono"] and b["reflectance"] for b in beats.values())
    verdicts["P1"] = {"prediction": "Arm A beats chance on HELD-OUT monochromatic and reflected stimuli; accuracy degrades "
                                    "gracefully approaching the RG zero-crossing.",
                      "beats_chance": beats, "sign_accuracy_by_distance_bin_1000q": dacc, "graceful_monotone": graceful,
                      "verdict": "supported" if (ok_all and graceful) else ("mixed" if (ok_any or graceful) else "not supported")}

    D = ARM_B_DECLARATIONS
    clear_s = [r for r in core_distinct if r["theory"]["sign_margin_rel"] >= D["clear_chromatic_sign_margin_rel"]]
    clear_m = [r for r in core_distinct if r["theory"]["multi_margin_deg"] >= D["clear_chromatic_multi_margin_deg"]]
    near_d = [r for r in near if r["duplicate_of"] is None]
    a_cs = agree([{"a": r["theory"]["sign"], "b": r["eye"]["sign"]} for r in clear_s], "a", "b")
    a_cm = agree([{"a": r["theory"]["multi"], "b": r["eye"]["multi"]} for r in clear_m], "a", "b")
    a_ns = agree([{"a": r["theory"]["sign"], "b": r["eye"]["sign"]} for r in near_d], "a", "b")
    a_nm = agree([{"a": r["theory"]["multi"], "b": r["eye"]["multi"]} for r in near_d], "a", "b")
    ca = a_cs["rate"] >= D["clear_agreement_threshold"] and a_cm["rate"] >= D["clear_agreement_threshold"]
    cb = a_ns["rate"] < a_cs["rate"] and a_nm["rate"] < a_cm["rate"]
    dn = decomposition["near_boundary_mono"]
    cc = (replica_max["rg_by"] <= D["replica_exact_tolerance"]
          and dn["quantisation_gausslin_expected_to_quantised_deg"]["median"]
          < D["quantisation_leg_negligible_fraction"] * dn["total_theory_to_eye_deg"]["median"])
    nparts = sum([ca, cb, cc])
    verdicts["P2"] = {"prediction": "Arm B labels agree with Arm A on the clearly-chromatic stimuli; agreement drops near the "
                                    "boundary and the angular error there is dominated by the Naka-Rushton nonlinearity + "
                                    "Gaussian-vs-CIE mismatch.",
                      "clear_sign_agreement": a_cs, "clear_multi_agreement": a_cm,
                      "near_boundary_sign_agreement": a_ns, "near_boundary_multi_agreement": a_nm,
                      "near_boundary_decomposition": dn, "replica_max_abs_diff_rg_by": replica_max["rg_by"],
                      "part_a_clear_agreement": ca, "part_b_drops_near_boundary": cb, "part_c_attribution": cc,
                      "verdict": "supported" if nparts == 3 else ("not supported" if nparts == 0 else "mixed")}
    nmeas = sum(m["measurable"] for m in met)
    verdicts["P3"] = {"prediction": "The eye breaks at least some CIE metamers by a measurable opponent gap.",
                      "n_pairs": len(met), "n_measurable": nmeas,
                      "verdict": "supported" if nmeas >= 1 else "not supported"}
    wob_deg = (wob_summary["angle_median_theory10"] > wob_summary["angle_median_theory2"]
               and wob_summary["theory_sign_acc_10deg"] <= wob_summary["theory_sign_acc_2deg"]
               and wob_summary["theory_multi_acc_10deg"] <= wob_summary["theory_multi_acc_2deg"])
    wopt_deg = {}
    for f, b in wopt.items():
        wopt_deg[f] = (b["angle_median_filtered"] > b["angle_median_base"]
                       and b["theory_sign_acc_filtered_truth"] <= b["theory_sign_acc_base"]
                       and b["theory_multi_acc_filtered_truth"] <= b["theory_multi_acc_base"])
    wopt_all = all(wopt_deg.values())
    n4 = int(wob_deg) + int(wopt_all)
    verdicts["P4"] = {"prediction": "Theory predictions degrade under wrong-observer/wrong-optics conditions.",
                      "wrong_observer_degrades": wob_deg, "wrong_optics_degrades_per_filter": wopt_deg,
                      "verdict": "supported" if n4 == 2 else ("not supported" if (n4 == 0 and not any(wopt_deg.values())) else "mixed")}
    verdicts["P5"] = {"prediction": "The closed-eyelid stimulus drives the eye to positive red_green at every tested ambient "
                                    "intensity and across the OD_long ablation.",
                      "n": lid_summary["n"], "n_positive": lid_summary["n_rg_positive"], "per_od_long": lid_summary["per_od_long"],
                      "verdict": "supported" if lid_summary["n_rg_positive"] == lid_summary["n"] else "not supported"}

    total_runtime = time.monotonic() - T0
    for r in rows:
        r.pop("_abs_rg_rel", None); r.pop("_abs_eye_rg", None)
    result = {
        "experiment": "marys_room_broad_armB",
        "arm": "B (photon eye, post-exposure) + scoring vs Arm A",
        "provenance": prov,
        "freeze_verification": freeze,
        "manifest_integrity": integrity,
        "manifest_schema": manifest["schema"],
        "arm_b_declarations": ARM_B_DECLARATIONS,
        "pilot_regression": {"exact": pilot_ok, "rows": pilot},
        "batched_vs_fresh_equivalence": {"n": len(equiv), "all_byte_identical": equiv_ok, "rows": equiv,
                                         "note": "deterministic-repeat check (same packets, different eye/column count), "
                                                 "not independent trials"},
        "runs": batch_log, "runtime_seconds": {"eye_phase": eye_runtime, "total": total_runtime},
        "repeat_structure": {
            "deterministic_duplicates": {"n": len(dups), "all_identical": all(d["identical"] for d in dups), "rows": dups},
            "wrong_observer": "eye values reused from the base stimulus (identical_to); not new eye inputs",
            "intensity_variants": "distinct eye inputs (different packets); not repeats",
            "poisson": "genuine independent trials (distinct seeded packet draws); the only source of variance",
            "everything_else": "single deterministic evaluation; no variance is claimed"},
        "pools": pools, "per_family": per_family,
        "error_vs_distance_from_rg_zero": vs_dist, "error_vs_abs_rg": vs_rg,
        "boundary_window_1nm": boundary_table, "eye_zero_crossings": zc,
        "calibration": calib, "decomposition": decomposition,
        "metamers": met, "wrong_observer": {"summary": wob_summary, "pairs": wob_pairs}, "wrong_optics": wopt,
        "adaptation": {"summary": adapt_summary, "rows": adapt},
        "poisson": pois,
        "eyelid": {"summary": lid_summary, "rows": lid},
        "verdicts": verdicts,
        "per_stimulus": rows,
        "supplementary_eyelid_refs": {k: {kk: vv for kk, vv in v.items() if kk != "spd"} | {"eye": ref_out[k]} for k, v in refs.items()},
    }
    OUT_JSON.write_text(json.dumps(result, indent=1, allow_nan=True) + "\n")

    cols = ["id", "family", "split", "adversarial", "duplicate_of", "eye_source", "eye_run", "eye_column", "wavelength_nm", "quanta",
            "td", "packets_total", "truth_binary", "truth_hue4", "truth_dominant_nm", "truth_purity",
            "theory_observer", "theory_rg", "theory_by", "theory_rg_rel", "theory_sign", "theory_multi",
            "eye_red_green", "eye_blue_yellow", "eye_intensity", "eye_sign", "eye_multi",
            "theory_sign_correct", "theory_multi_correct", "eye_sign_correct", "eye_multi_correct",
            "agree_sign", "agree_multi", "angle_err_deg", "cosine"]
    cols += [f"{c}_{k}" for c in RCLS for k in ("caught", "act", "adapt")]
    with OUT_CSV.open("w", newline="") as fh:
        fh.write(f"# provenance: {prov}\n")
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            rec = r["eye"]["receptors"]
            w.writerow([r["id"], r["family"], r["split"], r["adversarial"], r["duplicate_of"] or "", r["eye_source"],
                        r["eye_run"]["run"], r["eye_run"]["column"], r["wavelength_nm"] if r["wavelength_nm"] is not None else "",
                        r["quanta"] if r["quanta"] is not None else "", repr(r["td"]), r["packets_total"],
                        r["truth"]["binary"], r["truth"]["hue4"], repr(r["truth"]["dominant_wavelength_nm"]),
                        repr(r["truth"]["excitation_purity"]), r["theory"]["observer"], repr(r["theory"]["rg"]),
                        repr(r["theory"]["by"]), repr(r["theory"]["rg_rel"]), r["theory"]["sign"], r["theory"]["multi"],
                        repr(r["eye"]["red_green"]), repr(r["eye"]["blue_yellow"]), repr(r["eye"]["intensity"]),
                        r["eye"]["sign"], r["eye"]["multi"], r["theory_sign_correct"], r["theory_multi_correct"],
                        r["eye_sign_correct"], r["eye_multi_correct"], r["agree_sign"], r["agree_multi"],
                        "" if r["angle_err_deg"] is None else repr(r["angle_err_deg"]),
                        "" if r["cosine"] is None else repr(r["cosine"])]
                       + [repr(rec[c][k]) for c in RCLS for k in ("caught_quanta", "activation", "adaptation_after_epoch")])
    # post-run freeze re-check (Arm B must not have touched frozen files)
    post = verify_freeze()
    result["freeze_verification_after_run"] = post
    OUT_JSON.write_text(json.dumps(result, indent=1, allow_nan=True) + "\n")
    print(json.dumps({"verdicts": {k: v["verdict"] for k, v in verdicts.items()},
                      "pilot_exact": pilot_ok, "equiv": equiv_ok, "runtime_s": total_runtime}, indent=1))
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
