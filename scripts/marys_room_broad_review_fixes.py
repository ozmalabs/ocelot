"""Response-to-review analyses for the Mary's Room broad study (POST-HOC / ERRATA).

Run from the repo root:
    PYTHONPATH=. /home/matt/ozmadev/ocelot/.venv/bin/python -m scripts.marys_room_broad_review_fixes

Addresses the blocking issues in docs/experiments/marys-room-broad-review.md:
  B1  white/achromatic baseline for the P5 eyelid sign, plus the measures that
      do discriminate eyelid light from white light (dominant wavelength,
      eye (L-M)/(L+M), eye anchor label), incl. bare whites at the eyelid's
      matched at-retina td (replica eye, no eye run).
  B2  Arm A statistics at the theory-distinct-condition level (A1-4 accounting
      erratum) and eye statistics with intensity-condition clusters
      (cluster bootstrap) instead of per-row independence.
  B3  sha256 of the (unfrozen) Arm B / Arm C / Phase-5 scripts as they exist
      now, recorded for the record (cannot certify pre-run timing).
and cheap non-blocking items (P6 crossover N, truncated-locus dominant
wavelength, 5 nm quanta over-count, 10 vs 2 deg label changes).

Reads only frozen/recorded artefacts and the forward model.  Never imports
domains.photon_eye and never builds an eye; "replica" values use the documented
capture formula (sf.eye_capture_model), which equals the eye to 7e-16 on every
unadapted input (Arm B / audit).  Changes no frozen item, no decoder, anchor,
split, threshold, quanta anchor or OD parameter, and no verdict rule.
Writes results/marys_room_broad_review_fixes.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from domains import spectral_forward as sf
from scripts.marys_room_broad_theory import (binom_sf, binary, hue4, score, spd_from_recipe,
                                             wilson)

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
OUT = R / "marys_room_broad_review_fixes.json"
CORE = {"mono_sweep", "boundary_dense", "illuminant", "reflectance", "metamer", "eyelid"}
BINARY = ("reddish", "greenish")
HUE4 = ("red/purple", "yellow", "green", "blue")
SIGN_TO_BINARY = {"red": "reddish", "green": "greenish"}
SEED = 20261004
B = 10000
INTENSITY_KEYS = {"quanta", "scene_td"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ang(u, v):
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu == 0 or nv == 0:
        return float("nan")
    c = (u[0] * v[0] + u[1] * v[1]) / (nu * nv)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def nearest(rg, by, anchors):
    if rg == 0 and by == 0:
        return "undecided"
    return min(anchors, key=lambda k: (ang((rg, by), anchors[k]), k))


def sign_bin(rg):
    return "reddish" if rg > 0 else ("greenish" if rg < 0 else "undecided")


def strip_intensity(rec):
    if isinstance(rec, dict):
        return {k: strip_intensity(v) for k, v in rec.items() if k not in INTENSITY_KEYS}
    if isinstance(rec, list):
        return [strip_intensity(v) for v in rec]
    return rec


def recipe_of(e, idx):
    """(eye recipe, theory recipe or None if identical)."""
    ei = e["eye_input"]
    if "identical_to" in ei:
        eye = recipe_of(idx[ei["identical_to"]], idx)[0]
    else:
        eye = ei["recipe"]
    ti = e["theory_input"]
    th = ti["recipe"] if (not ti.get("same_as_eye_input", True) and "recipe" in ti) else None
    return eye, th, ti.get("observer")


def condition_key(e, idx):
    return json.dumps(strip_intensity(list(recipe_of(e, idx))), sort_keys=True)


def theory_key(row):
    lms = np.asarray(row["theory_primary"]["lms"], float)
    return (tuple(np.round(lms / max(lms.sum(), 1e-300), 12)),
            row["truth"]["binary"], row["truth"]["hue4"])


def rg_rel_act(L, M):
    return (L - M) / (L + M) if (L + M) > 0 else float("nan")


def rng_range(v):
    v = [x for x in v if not (isinstance(x, float) and math.isnan(x))]
    return [float(min(v)), float(max(v))] if v else None


# ------------------------------------------------------------------ B2
def distinct_theory(rows_a, sel_pred):
    """Collapse Arm A rows to theory-distinct conditions (Arm A's own key)."""
    sel = [r for r in rows_a if sel_pred(r) and r["hue_scored"]]
    groups = defaultdict(list)
    for r in sel:
        groups[theory_key(r)].append(r)
    truth_b, pred_b, truth_h, pred_h = [], [], [], []
    for k, g in groups.items():
        sb = {SIGN_TO_BINARY.get(r["theory_primary"]["sign_label"], "undecided") for r in g}
        mh = {r["theory_primary"]["multi_label"] for r in g}
        assert len(sb) == 1 and len(mh) == 1, f"non-identical predictions within a theory key {k}"
        truth_b.append(k[1]); pred_b.append(sb.pop())
        truth_h.append(k[2]); pred_h.append(mh.pop())
    out = {"n_rows": len(sel), "n_theory_distinct": len(groups),
           "sign_rule_binary": score(truth_b, pred_b, BINARY),
           "multi_anchor_hue4": score(truth_h, pred_h, HUE4)}
    for d in ("sign_rule_binary", "multi_anchor_hue4"):
        out[d].pop("confusion_truth_to_pred", None)
    return out


def intensity_collapsed_theory(rows_a, mstim, idx, sel_pred):
    """Reviewer's variant: collapse only rows sharing a recipe up to intensity."""
    sel = [r for r in rows_a if sel_pred(r) and r["hue_scored"]]
    groups = defaultdict(list)
    for r in sel:
        groups[condition_key(mstim[r["id"]], idx)].append(r)
    tb, pb, th, ph = [], [], [], []
    for g in groups.values():
        r = g[0]
        assert len({SIGN_TO_BINARY.get(x["theory_primary"]["sign_label"]) for x in g}) == 1
        assert len({x["theory_primary"]["multi_label"] for x in g}) == 1
        assert len({x["truth"]["hue4"] for x in g}) == 1
        tb.append(r["truth"]["binary"]); pb.append(SIGN_TO_BINARY.get(r["theory_primary"]["sign_label"], "undecided"))
        th.append(r["truth"]["hue4"]); ph.append(r["theory_primary"]["multi_label"])
    s1, s2 = score(tb, pb, BINARY), score(th, ph, HUE4)
    keep = ("n", "correct", "accuracy", "accuracy_wilson95", "chance_majority_rate", "p_binom_vs_majority",
            "p_binom_vs_0.5")
    return {"n_conditions": len(groups), "sign_rule_binary": {k: s1[k] for k in keep},
            "multi_anchor_hue4": {k: s2[k] for k in keep}}


def cluster_stats(clusters, majority_rate):
    """clusters: list of (n_correct, n_scored). Cluster bootstrap of pooled accuracy +
    per-cluster majority-vote binomial (ties = incorrect)."""
    c = np.array([x[0] for x in clusters], float)
    n = np.array([x[1] for x in clusters], float)
    keep = n > 0
    c, n = c[keep], n[keep]
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, len(c), size=(B, len(c)))
    acc_b = c[draws].sum(1) / n[draws].sum(1)
    k_vote = int(np.sum(c / n > 0.5))
    return {"n_clusters": int(len(c)), "n_rows": int(n.sum()), "accuracy": float(c.sum() / n.sum()),
            "cluster_boot95": [float(np.percentile(acc_b, 2.5)), float(np.percentile(acc_b, 97.5))],
            "row_level_majority_rate": majority_rate,
            "cluster_boot_p_acc_le_majority": float(np.mean(acc_b <= majority_rate)),
            "majority_vote_clusters_correct": k_vote,
            "majority_vote_binom_p_vs_majority": binom_sf(k_vote, int(len(c)), majority_rate)}


def cluster_angle_ci(vals_by_cluster):
    groups = [np.array(v, float) for v in vals_by_cluster if len(v)]
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, len(groups), size=(B, len(groups)))
    med, mean = np.zeros(B), np.zeros(B)
    for b in range(B):
        x = np.concatenate([groups[i] for i in draws[b]])
        med[b], mean[b] = np.median(x), x.mean()
    allv = np.concatenate(groups)
    return {"n_clusters": len(groups), "n_rows": int(len(allv)),
            "median_deg": float(np.median(allv)), "mean_deg": float(allv.mean()),
            "median_cluster_boot95": [float(np.percentile(med, 2.5)), float(np.percentile(med, 97.5))],
            "mean_cluster_boot95": [float(np.percentile(mean, 2.5)), float(np.percentile(mean, 97.5))]}


# ------------------------------------------------------------------ item 7
def dominant_wavelength_truncated(spd, white):
    """Same construction as sf.dominant_wavelength but the spectrum locus is
    truncated at its long-wavelength extreme (max x) and the purple line joins
    390 nm to that point.  POST-HOC check only."""
    spd = np.asarray(spd, float)
    step = sf.step_for(spd)
    w = np.array(sf.chromaticity(sf._as_spectrum(white, step, "illuminant")))
    p = np.array(sf.chromaticity(spd))
    d = p - w
    if np.hypot(*d) < 1e-12:
        return (float("nan"), 0.0), None
    cmf = sf.load_xyz(1)
    loc_full = cmf[:, :2] / cmf.sum(axis=1, keepdims=True)
    wl_full = sf.grid(1)
    imax = int(np.argmax(loc_full[:, 0]))
    loc, wl = loc_full[: imax + 1], wl_full[: imax + 1]

    def hit(direction):
        best = None
        for i in range(len(loc) - 1):
            a, b = loc[i], loc[i + 1]
            e = b - a
            den = direction[0] * (-e[1]) + direction[1] * e[0]
            if abs(den) < 1e-15:
                continue
            r = a - w
            t = (r[0] * (-e[1]) + r[1] * e[0]) / den
            u = (direction[0] * r[1] - direction[1] * r[0]) / den
            if t > 0 and -1e-12 <= u <= 1 + 1e-12 and (best is None or t < best[0]):
                best = (t, wl[i] + u * (wl[i + 1] - wl[i]))
        return best

    h = hit(d)
    if h is not None:
        return (float(h[1]), float(1.0 / h[0])), float(wl_full[imax])
    h = hit(-d)
    if h is None:
        return (float("nan"), float("nan")), float(wl_full[imax])
    a, b = loc[0], loc[-1]
    e = b - a
    den = d[0] * (-e[1]) + d[1] * e[0]
    r = a - w
    t = (r[0] * (-e[1]) + r[1] * e[0]) / den
    return (-float(h[1]), float(1.0 / t) if t > 0 else float("nan")), float(wl_full[imax])


def main():
    man = json.loads((R / "marys_room_broad_stimuli.json").read_text())
    arma = json.loads((R / "marys_room_broad_armA.json").read_text())
    armb = json.loads((R / "marys_room_broad.json").read_text())
    rd = json.loads((R / "marys_room_rate_distortion.json").read_text())
    anchors = {k: tuple(v["unit_direction"]) for k, v in arma["anchors"].items()}
    idx = {e["id"]: e for e in man["stimuli"]}
    rows_a = arma["per_stimulus"]
    rows_b = {r["id"]: r for r in armb["per_stimulus"]}
    out = {"experiment": "marys_room_broad_review_fixes",
           "status": "POST-HOC response to review; changes no frozen item and no verdict",
           "provenance_note": "no eye built; engine provenance of the eye data analysed: " + armb["provenance"],
           "inputs_sha256": {p: sha(R / p) for p in ("marys_room_broad_stimuli.json", "marys_room_broad_armA.json",
                                                      "marys_room_broad.json", "marys_room_rate_distortion.json")}}

    # ============================================================ B1 white baseline
    core_b = [r for r in armb["per_stimulus"] if r["split"] == "heldout" and r["family"] in CORE
              and r["duplicate_of"] is None]
    achrom = [r for r in core_b if not r["hue_scored"]]

    def eye_summary(r):
        L = r["eye"]["receptors"]["l"]["activation"]
        M = r["eye"]["receptors"]["m"]["activation"]
        return {"id": r["id"], "family": r["family"], "eye_red_green": r["eye"]["red_green"],
                "eye_blue_yellow": r["eye"]["blue_yellow"], "eye_rg_rel": rg_rel_act(L, M),
                "eye_sign": sign_bin(r["eye"]["red_green"]),
                "eye_anchor": nearest(r["eye"]["red_green"], r["eye"]["blue_yellow"], anchors),
                "theory_rg": r["theory"]["rg"], "theory_rg_rel": r["theory"]["rg_rel"],
                "packets_total": r.get("packets_total"), "td": r.get("td")}

    ach = [eye_summary(r) for r in achrom]
    illum = [eye_summary(rows_b[e["id"]]) for e in man["stimuli"] if e["family"] == "illuminant"]
    lid_rows = armb["eyelid"]["rows"]
    lid = []
    for x in lid_rows:
        e = idx[x["id"]]
        spd = spd_from_recipe(e["eye_input"]["recipe"])
        ex = sf.eye_capture_expected(spd)
        lid.append({"id": x["id"], "illuminant": x["illuminant"], "od_long": x["od_long"],
                    "ambient_td": x["ambient_td"], "td_at_retina": x["td_at_retina"],
                    "packets_total": x["packets_total"], "eye_red_green": x["eye_red_green"],
                    "eye_rg_rel": rg_rel_act(x["L_act"], x["M_act"]), "eye_anchor": x["eye_multi"],
                    "truth_dominant_nm": x["truth_dominant_nm"], "truth_purity": e["truth"]["excitation_purity"],
                    "replica_expected_value_rg": ex["red_green"],
                    "replica_expected_value_rg_rel": rg_rel_act(ex["l"]["activation"], ex["m"]["activation"]),
                    "replica_expected_value_anchor": nearest(ex["red_green"], ex["blue_yellow"], anchors)})

    # bare whites, replica eye: (i) at the eyelid ambient levels, (ii) at each eyelid row's at-retina td
    bare_amb = []
    for ill in ("E", "D65", "A"):
        for td in (100.0, 1000.0, 10000.0):
            spd = sf.scale_to_td(sf.illuminant(ill, 1), td)
            m = sf.eye_capture_model(sf.quantize(spd))
            ex = sf.eye_capture_expected(spd)
            bare_amb.append({"illuminant": ill, "td": td, "replica_rg": m["red_green"],
                             "replica_rg_rel": rg_rel_act(m["l"]["activation"], m["m"]["activation"]),
                             "replica_anchor": nearest(m["red_green"], m["blue_yellow"], anchors),
                             "expected_rg_rel": rg_rel_act(ex["l"]["activation"], ex["m"]["activation"])})
    matched = []
    for x in lid:
        spd = sf.scale_to_td(sf.illuminant(x["illuminant"], 1), x["td_at_retina"])
        pk = sf.quantize(spd)
        m = sf.eye_capture_model(pk)
        ex = sf.eye_capture_expected(spd)
        matched.append({"eyelid_id": x["id"], "illuminant": x["illuminant"], "td": x["td_at_retina"],
                        "packets_total": sf.packets_total(pk), "replica_rg": m["red_green"],
                        "replica_rg_rel": rg_rel_act(m["l"]["activation"], m["m"]["activation"]),
                        "replica_anchor": nearest(m["red_green"], m["blue_yellow"], anchors),
                        "expected_rg": ex["red_green"],
                        "expected_rg_rel": rg_rel_act(ex["l"]["activation"], ex["m"]["activation"]),
                        "expected_anchor": nearest(ex["red_green"], ex["blue_yellow"], anchors),
                        "eyelid_eye_rg": x["eye_red_green"], "eyelid_eye_rg_rel": x["eye_rg_rel"],
                        "eyelid_expected_rg_rel": x["replica_expected_value_rg_rel"]})

    by_amb = {}
    for a in (100.0, 1000.0, 10000.0):
        g = [x for x in lid if x["ambient_td"] == a]
        by_amb[str(int(a))] = {"n": len(g), "eye_rg": rng_range([x["eye_red_green"] for x in g]),
                               "eye_rg_rel": rng_range([x["eye_rg_rel"] for x in g]),
                               "expected_value_rg_rel": rng_range([x["replica_expected_value_rg_rel"] for x in g]),
                               "eye_anchor_red_purple": sum(x["eye_anchor"] == "red/purple" for x in g),
                               "expected_value_anchor_red_purple": sum(x["replica_expected_value_anchor"] == "red/purple"
                                                                       for x in g),
                               "packets_total": rng_range([float(x["packets_total"]) for x in g])}
    white_rel = ([x["eye_rg_rel"] for x in ach] + [x["replica_rg_rel"] for x in bare_amb]
                 + [x["replica_rg_rel"] for x in matched])
    white_rel_ex = [x["expected_rg_rel"] for x in bare_amb] + [x["expected_rg_rel"] for x in matched]
    out["B1_eyelid_white_baseline"] = {
        "achromatic_HO_core": {
            "n": len(ach), "n_eye_rg_positive": sum(x["eye_red_green"] > 0 for x in ach),
            "n_theory_rg_positive": sum(x["theory_rg"] > 0 for x in ach),
            "eye_rg": rng_range([x["eye_red_green"] for x in ach]),
            "eye_rg_rel": rng_range([x["eye_rg_rel"] for x in ach]),
            "eye_anchor_counts": {k: sum(x["eye_anchor"] == k for x in ach) for k in set(x["eye_anchor"] for x in ach)},
            "rows": ach},
        "bare_illuminants_eye": illum,
        "bare_whites_replica_at_ambient": bare_amb,
        "bare_whites_replica_at_matched_retinal_td": matched,
        "eyelid": {"by_ambient_td": by_amb,
                   "truth_dominant_nm": rng_range([x["truth_dominant_nm"] for x in lid]),
                   "truth_purity": rng_range([x["truth_purity"] for x in lid]),
                   "eye_anchor_red_purple": sum(x["eye_anchor"] == "red/purple" for x in lid),
                   "rows": lid},
        "separation": {
            "max_white_rg_rel_quantised_all": float(max(white_rel)),
            "max_white_rg_rel_expected_value": float(max(white_rel_ex)),
            "min_eyelid_eye_rg_rel": float(min(x["eye_rg_rel"] for x in lid)),
            "min_eyelid_expected_rg_rel": float(min(x["replica_expected_value_rg_rel"] for x in lid)),
            "n_matched_white_rg_positive": sum(x["replica_rg"] > 0 for x in matched),
            "n_matched_white_rg_zero": sum(x["replica_rg"] == 0 for x in matched),
            "n_eyelid_rg_rel_gt_every_white": sum(x["eye_rg_rel"] > max(white_rel) for x in lid),
            "n_eyelid_rg_rel_gt_matched_white": sum(x["eyelid_eye_rg_rel"] > x["replica_rg_rel"]
                                                    for x in matched
                                                    if not math.isnan(x["replica_rg_rel"])),
            "n_matched_white_defined": sum(not math.isnan(x["replica_rg_rel"]) for x in matched),
            "n_eyelid_rg_gt_matched_white_rg": sum(x["eyelid_eye_rg"] > x["replica_rg"] for x in matched),
            "n_eyelid_expected_rg_rel_gt_matched_white_expected": sum(x["eyelid_expected_rg_rel"] > x["expected_rg_rel"]
                                                                      for x in matched),
            "min_ratio_eyelid_over_matched_white_expected_rg_rel": float(min(
                x["eyelid_expected_rg_rel"] / x["expected_rg_rel"] for x in matched)),
            "n_bare_white_anchor_red_purple_eye_or_replica": (
                sum(x["eye_anchor"] == "red/purple" for x in ach)
                + sum(x["replica_anchor"] == "red/purple" for x in bare_amb)
                + sum(x["expected_anchor"] == "red/purple" for x in matched)),
            "n_bare_white_cases_counted": len(ach) + len(bare_amb) + len(matched),
            "n_matched_white_quantised_anchor_red_purple": sum(x["replica_anchor"] == "red/purple" for x in matched),
            "eyelid_expected_value_anchor_counts": {k: sum(x["replica_expected_value_anchor"] == k for x in lid)
                                                    for k in sorted({x["replica_expected_value_anchor"] for x in lid})},
            "max_white_rg_rel_expected_by_illuminant": {
                ill: float(max([x["expected_rg_rel"] for x in bare_amb + matched if x["illuminant"] == ill]
                               + [x["eye_rg_rel"] for x in illum if x["id"].split("_")[1] == ill]))
                for ill in ("E", "D65", "A")},
            "min_eyelid_expected_rg_rel_by_illuminant": {
                ill: float(min(x["replica_expected_value_rg_rel"] for x in lid if x["illuminant"] == ill))
                for ill in ("E", "D65", "A")}}}

    # ============================================================ B2 distinct conditions
    is_core = lambda r: r["split"] == "heldout" and r["family"] in CORE and r["duplicate_of"] is None
    pools = {
        "TRAIN": lambda r: r["split"] == "train",
        "HELDOUT_core": is_core,
        "mono_sweep/heldout": lambda r: r["family"] == "mono_sweep" and r["split"] == "heldout",
        "boundary_dense/heldout": lambda r: r["family"] == "boundary_dense",
        "reflectance/heldout": lambda r: r["family"] == "reflectance",
        "reflectance/heldout/E": lambda r: r["family"] == "reflectance" and r["id"].endswith("_E"),
        "reflectance/heldout/D65": lambda r: r["family"] == "reflectance" and r["id"].endswith("_D65"),
        "reflectance/heldout/A": lambda r: r["family"] == "reflectance" and r["id"].endswith("_A"),
        "metamer/heldout": lambda r: r["family"] == "metamer",
        "eyelid/heldout": lambda r: r["family"] == "eyelid",
        "ADVERSARIAL_wrong_observer_10deg": lambda r: r["family"] == "wrong_observer",
        "ADVERSARIAL_wrong_optics": lambda r: r["family"] == "wrong_optics",
    }
    b2 = {}
    for name, pred in pools.items():
        d = distinct_theory(rows_a, pred)
        d["reported_row_level"] = {
            k: {kk: (arma["pools"].get(name) or arma["per_family"].get(name))[k][kk]
                for kk in ("n", "accuracy", "accuracy_wilson95", "p_binom_vs_majority", "chance_majority_rate")}
            for k in ("sign_rule_binary", "multi_anchor_hue4")} if (name in arma["pools"] or name in arma["per_family"]) else None
        d["intensity_collapsed_variant"] = intensity_collapsed_theory(rows_a, idx, idx, pred)
        b2[name] = d
    # check: Arm A's own n_theory_distinct_scored reproduced
    assert b2["HELDOUT_core"]["n_theory_distinct"] == arma["pools"]["HELDOUT_core"]["n_theory_distinct_scored"]

    # eye: cluster = recipe up to intensity, HO core
    clus = defaultdict(list)
    for r in core_b:
        clus[condition_key(idx[r["id"]], idx)].append(r)
    hp = armb["pools"]["HELDOUT_core"]
    eye_anchor_cl, eye_sign_cl, th_sign_cl, th_anchor_cl, ang_cl = [], [], [], [], []
    for g in clus.values():
        sc = [r for r in g if r["hue_scored"]]
        eye_anchor_cl.append((sum(nearest(r["eye"]["red_green"], r["eye"]["blue_yellow"], anchors)
                                  == r["truth"]["hue4"] for r in sc), len(sc)))
        eye_sign_cl.append((sum(sign_bin(r["eye"]["red_green"]) == r["truth"]["binary"] for r in sc), len(sc)))
        th_sign_cl.append((sum(SIGN_TO_BINARY.get(r["theory"]["sign"]) == r["truth"]["binary"] for r in sc), len(sc)))
        th_anchor_cl.append((sum(r["theory"]["multi"] == r["truth"]["hue4"] for r in sc), len(sc)))
        ang_cl.append([ang((r["theory"]["rg"], r["theory"]["by"]), (r["eye"]["red_green"], r["eye"]["blue_yellow"]))
                       for r in g])
    eye_cl = {"cluster_definition": "manifest recipe with intensity fields (quanta, scene_td) removed; "
                                    "HO core distinct eye inputs",
              "eye_anchor": cluster_stats(eye_anchor_cl, hp["eye_multi_anchor_hue4"]["chance_majority_rate"]),
              "eye_sign": cluster_stats(eye_sign_cl, hp["eye_sign_rule_binary"]["chance_majority_rate"]),
              "theory_sign_same_clusters": cluster_stats(th_sign_cl, hp["eye_sign_rule_binary"]["chance_majority_rate"]),
              "theory_anchor_same_clusters": cluster_stats(th_anchor_cl, hp["eye_multi_anchor_hue4"]["chance_majority_rate"]),
              "angle": cluster_angle_ci(ang_cl),
              "angle_reported_row_bootstrap": {k: hp["angular_error"][k] for k in
                                               ("median_deg", "mean_deg", "median_boot95", "mean_boot95")},
              "reported_row_level": {
                  "eye_anchor": {k: hp["eye_multi_anchor_hue4"][k] for k in ("n", "accuracy", "accuracy_wilson95",
                                                                              "p_binom_vs_majority")},
                  "eye_sign": {k: hp["eye_sign_rule_binary"][k] for k in ("n", "accuracy", "accuracy_wilson95",
                                                                           "p_binom_vs_majority")}}}
    # cluster sizes
    sizes = [len([r for r in g if r["hue_scored"]]) for g in clus.values()]
    eye_cl["cluster_size_counts"] = {str(s): sizes.count(s) for s in sorted(set(sizes))}
    out["B2_distinct_condition_statistics"] = {
        "status": "ACCOUNTING ERRATUM per prereg A1-4 (theory-distinct counts must accompany row-level "
                  "statistics); row-level numbers retained for reference",
        "theory_distinct_key": "Arm A's own key: theory LMS normalised to sum 1 (rounded 1e-12) + truth labels",
        "arm_A": b2, "arm_B_eye_cluster": eye_cl}

    # ============================================================ B3 script hashes
    out["B3_unfrozen_script_hashes_now"] = {
        "note": "Recorded at review-response time. These do NOT certify that ARM_B_DECLARATIONS existed "
                "before the eye run; Arm B's result does not record its script hash.",
        "sha256": {p: sha(ROOT / p) for p in ("scripts/marys_room_broad.py", "scripts/marys_room_rate_distortion.py",
                                               "scripts/marys_room_broad_audit.py",
                                               "scripts/marys_room_broad_boundary.py",
                                               "scripts/marys_room_broad_review_fixes.py")},
        "arm_C_script_hash_recorded_in_arm_C_result": rd.get("inputs", {}).get("script_sha256"),
    }
    b3 = out["B3_unfrozen_script_hashes_now"]
    b3["arm_C_script_unchanged_since_run"] = (b3["arm_C_script_hash_recorded_in_arm_C_result"]
                                              == b3["sha256"]["scripts/marys_room_rate_distortion.py"])
    b3["arm_B_script_hash_recorded_in_arm_B_result"] = None

    # ============================================================ item 4: P6 crossover
    ps = rd.get("pool_sizes", {})
    out["N4_P6_crossover"] = {
        "raw_LMS_b6_total_bits": "18 + 192/N", "VQ_k64_total_bits": "6 + 4096/N",
        "crossover_N": 3904 / 12, "pool_sizes": ps,
        "HO_core": {"raw": 18 + 192 / 302, "vq": 6 + 4096 / 302},
        "VQ_vs_fixed_opponent_HO_core": {"vq_k64": rd["verdicts"]["secondary"]["VQ_opp_vs_opponent"]["learned_R"],
                                         "opponent_b6": rd["verdicts"]["secondary"]["VQ_opp_vs_opponent"]["baseline_R"],
                                         "without_model_cost": {"vq_k64": 6.0, "opponent_b6": 12.0}},
        "VQ_opponent_vs_opponent_crossover_N": "6 + 4096/N < 12 + 128/N  <=>  N > 3968/6 = %.1f" % (3968 / 6)}

    # ============================================================ item 7: truncated locus
    changes, max_diff, n_checked, worst_repl = [], 0.0, 0, 0.0
    long_end = None
    for e in man["stimuli"]:
        ei = e["eye_input"]
        if "identical_to" in ei or "recipe" not in ei:
            continue
        tr = e["truth"]
        spd = spd_from_recipe(ei["recipe"])
        if sf.step_for(spd) != 1:
            continue
        dw0, pur0 = sf.dominant_wavelength(spd, white=tr["white"])
        worst_repl = max(worst_repl, 0.0 if (math.isnan(dw0) and math.isnan(tr["dominant_wavelength_nm"]))
                         else abs(dw0 - tr["dominant_wavelength_nm"]))
        (dw1, pur1), long_end = dominant_wavelength_truncated(spd, tr["white"])
        n_checked += 1
        if math.isnan(dw0) or math.isnan(dw1):
            continue
        diff = abs(dw1 - dw0)
        max_diff = max(max_diff, diff)
        h1, b1 = hue4(dw1, pur1), binary(dw1, pur1)
        if diff > 0.5 or h1 != tr["hue4"] or b1 != tr["binary"]:
            changes.append({"id": e["id"], "family": e["family"], "dw_frozen": dw0, "dw_truncated": dw1,
                            "hue4_frozen": tr["hue4"], "hue4_truncated": h1,
                            "binary_frozen": tr["binary"], "binary_truncated": b1})
    out["N7_dominant_wavelength_truncated_locus"] = {
        "status": "POST-HOC check; frozen truth unchanged",
        "locus_truncated_at_nm": long_end, "n_checked_1nm_recipes": n_checked,
        "max_abs_frozen_vs_recomputed_dw": worst_repl,
        "n_dw_change_gt_0.5nm": sum(abs(c["dw_truncated"] - c["dw_frozen"]) > 0.5 for c in changes),
        "n_hue4_label_changes": sum(c["hue4_frozen"] != c["hue4_truncated"] for c in changes),
        "n_binary_label_changes": sum(c["binary_frozen"] != c["binary_truncated"] for c in changes),
        "families_affected": sorted({c["family"] for c in changes}),
        "changes": changes}

    # ============================================================ item 8: 5 nm over-count
    o8 = {}
    for ill in ("E", "A", "D65"):
        q1 = float(sf.expected_quanta(sf.scale_to_td(sf.illuminant(ill, 1), 100.0)).sum())
        s5 = sf.scale_to_td(sf.illuminant(ill, 5), 100.0)
        q5 = sf.expected_quanta(s5)
        wt = np.ones(len(q5)); wt[0] = wt[-1] = 0.5
        o8[ill] = {"quanta_1nm": q1, "quanta_5nm_rectangle": float(q5.sum()),
                   "quanta_5nm_trapezoid_endweights": float((q5 * wt).sum()),
                   "rel_overcount_rectangle": float(q5.sum() / q1 - 1)}
    out["N8_grid5_quanta"] = {"status": "documented convention (frozen forward model unchanged)",
                              "at_100_td": o8}

    # ============================================================ item 14: 10 vs 2 deg
    wo = [r for r in rows_a if r["family"] == "wrong_observer" and r["hue_scored"]]
    out["N14_wrong_observer_label_changes"] = {
        "n": len(wo),
        "n_anchor_label_differs_2_vs_10": sum(r["theory_2deg"]["multi_label"] != r["theory_10deg"]["multi_label"]
                                              for r in wo),
        "n_sign_label_differs_2_vs_10": sum(r["theory_2deg"]["sign_label"] != r["theory_10deg"]["sign_label"]
                                            for r in wo),
        "anchor_correct_2deg": sum(r["theory_2deg"]["multi_label"] == r["truth"]["hue4"] for r in wo),
        "anchor_correct_10deg": sum(r["theory_10deg"]["multi_label"] == r["truth"]["hue4"] for r in wo),
        "sign_correct_2deg": sum(SIGN_TO_BINARY.get(r["theory_2deg"]["sign_label"]) == r["truth"]["binary"] for r in wo),
        "sign_correct_10deg": sum(SIGN_TO_BINARY.get(r["theory_10deg"]["sign_label"]) == r["truth"]["binary"]
                                  for r in wo)}

    assert "domains.photon_eye" not in sys.modules
    OUT.write_text(json.dumps(out, indent=1, default=float))
    # ------------------------------------------------------------ console summary
    b1 = out["B1_eyelid_white_baseline"]
    print("B1 achromatic HO-core:", {k: b1["achromatic_HO_core"][k] for k in
                                     ("n", "n_eye_rg_positive", "n_theory_rg_positive", "eye_rg", "eye_rg_rel",
                                      "eye_anchor_counts")})
    for x in illum:
        print("   bare", x["id"], "rg=%.4g rel=%.4f anchor=%s" % (x["eye_red_green"], x["eye_rg_rel"], x["eye_anchor"]))
    for x in bare_amb:
        print("   replica bare", x["illuminant"], x["td"], "rg=%.4g rel=%.4f exp_rel=%.4f %s" % (
            x["replica_rg"], x["replica_rg_rel"], x["expected_rg_rel"], x["replica_anchor"]))
    print("   eyelid by ambient:", json.dumps(b1["eyelid"]["by_ambient_td"]))
    print("   eyelid truth dw:", b1["eyelid"]["truth_dominant_nm"], "purity", b1["eyelid"]["truth_purity"])
    print("   separation:", json.dumps(b1["separation"]))
    print("   eyelid expected anchors:", [(x["id"], x["replica_expected_value_anchor"]) for x in lid])
    for x in matched[:27]:
        print("   matched", x["eyelid_id"], "td=%.3f q=%d rg=%.3g rel=%s | lid rg=%.3g rel=%.3f exp_rel=%.3f" % (
            x["td"], x["packets_total"], x["replica_rg"], "%.3f" % x["replica_rg_rel"], x["eyelid_eye_rg"],
            x["eyelid_eye_rg_rel"], x["expected_rg_rel"]))
    print("B2:")
    for k, d in b2.items():
        s, m = d["sign_rule_binary"], d["multi_anchor_hue4"]
        ic = d["intensity_collapsed_variant"]
        print("  %-34s rows=%d distinct=%d | sign %d/%d=%.3f p=%.3g maj=%.3f | anchor %d/%d=%.3f p=%.3g maj=%.3f"
              " || icol n=%d sign %.3f p=%.3g anchor %.3f p=%.3g" % (
                  k, d["n_rows"], d["n_theory_distinct"], s["correct"], s["n"], s["accuracy"],
                  s["p_binom_vs_majority"], s["chance_majority_rate"], m["correct"], m["n"], m["accuracy"],
                  m["p_binom_vs_majority"], m["chance_majority_rate"], ic["n_conditions"],
                  ic["sign_rule_binary"]["accuracy"], ic["sign_rule_binary"]["p_binom_vs_majority"],
                  ic["multi_anchor_hue4"]["accuracy"], ic["multi_anchor_hue4"]["p_binom_vs_majority"]))
        print("      wilson sign", s["accuracy_wilson95"], "anchor", m["accuracy_wilson95"])
    print("  eye clusters:", json.dumps({k: v for k, v in eye_cl.items() if k not in ("cluster_definition",)}, default=float))
    print("N4:", json.dumps(out["N4_P6_crossover"]))
    n7 = out["N7_dominant_wavelength_truncated_locus"]
    print("N7:", {k: v for k, v in n7.items() if k != "changes"})
    print("N8:", json.dumps(o8))
    print("N14:", out["N14_wrong_observer_label_changes"])


if __name__ == "__main__":
    main()
