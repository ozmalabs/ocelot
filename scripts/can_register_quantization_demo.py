"""Live demonstration harness for seeds/can_register_quantization.json.

Per docs/research/engine_substrate/CAN_REGISTER_QUANTIZATION_PREREG.md Sec6.
Pure world-adapter/harness code (CLAUDE.md's own architecture rule): this
script MECHANICALLY builds graph nodes/edges from a synthetic population,
calls `run_rules()`, and reads back the RESULT the engine's own Rule
already decided. It contains no register decision -- the label choice is
entirely the engine's `can_register_decode_band` rule (Argmin over the
RegisterLabelAnchor codebook), not a Python `if`/`else`.

`_draw_resolution_bins` below is a REUSE of the identical formula
`/home/matt/ozmadev/bigville/worlds/bigville_town100_world.py:142-151`
already uses (same constants, same shape, same clamp) -- ported here
because that file lives only in the sibling bigville repo and cannot be
imported cross-repo (PREREG Sec3). It is pure arithmetic (drawing a
population trait), not a graph decision, so it stays Python, exactly like
the original file's own `_draw_resolution_bins` does.

Run: python3 scripts/can_register_quantization_demo.py
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

import substrate_rs as sr  # noqa: E402
from substrate.seed_loader import engine_rules_only  # noqa: E402

SEED_PATH = "seeds/can_register_quantization.json"
BANDS = list(range(6))  # 0..5, per PREREG Sec1 point 4's registered scoping

# ---------------------------------------------------------------------
# _draw_resolution_bins -- REUSE of bigville_town100_world.py's own
# constants (_RES_FLOOR_MEAN/_RES_FLOOR_SD/_RES_CEIL_MEAN/_RES_CEIL_SD/
# _RES_CEIL_WEIGHT/_RES_LO/_RES_HI), ported verbatim (PREREG Sec3).
# ---------------------------------------------------------------------
_RES_FLOOR_MEAN, _RES_FLOOR_SD = 3.0, 1.0
_RES_CEIL_MEAN, _RES_CEIL_SD = 7.5, 2.0
_RES_CEIL_WEIGHT = 0.35
_RES_LO, _RES_HI = 2, 12


def _draw_resolution_bins(rng):
    if rng.random() < _RES_CEIL_WEIGHT:
        z = rng.normal(_RES_CEIL_MEAN, _RES_CEIL_SD)
    else:
        z = rng.normal(_RES_FLOOR_MEAN, _RES_FLOOR_SD)
    return int(min(_RES_HI, max(_RES_LO, round(z))))


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    filtered = engine_rules_only(d)
    inner.load_seed_manifest(filtered)
    return s


def _band_anchors(inner):
    return {inner.node(n)["attrs"]["band_code"]: n for n in inner.nodes("BandAffinityAnchor")}


def build_profile(inner, anchors, name, resolution_bins, resolution_level):
    prof = inner.add_node("RegisterProfile", {
        "name": name, "resolution_bins": resolution_bins,
        "resolution_level": resolution_level,
    })
    obs_ids = {}
    for band in BANDS:
        ta = inner.node(anchors[band])["attrs"]["true_affinity"]
        obs = inner.add_node("RegisterObservation", {
            "band_code": band, "true_affinity": ta, "status": "pending",
        })
        inner.add_edge(prof, "observed_band", obs, {})
        obs_ids[band] = obs
    return prof, obs_ids


def read_results(inner, obs_ids):
    out = {}
    for band, obs in obs_ids.items():
        at = inner.node(obs)["attrs"]
        out[band] = {
            "true_affinity": at["true_affinity"],
            "effective_bins": at["effective_bins"],
            "level_index": at["register_level_index"],
            "quantized_value": at["quantized_value"],
            "label": at["register_label"],
        }
    return out


def mean_abs_error(results):
    return statistics.fmean(
        abs(r["true_affinity"] - r["quantized_value"]) for r in results.values()
    )


def distinct_labels(results):
    return len({r["label"] for r in results.values()})


def main():
    rng = np.random.default_rng(20260816)
    population = [("resident_%03d" % i, _draw_resolution_bins(rng)) for i in range(100)]

    # Mechanical, non-cherry-picked selection -- PREREG Sec6.1, mirroring
    # BIGVILLE_CAN_INTEGRATION_RESULTS.md Sec5's own selection rule exactly.
    lo_idx = min(range(100), key=lambda i: (population[i][1], i))
    hi_idx = max(range(100), key=lambda i: (population[i][1], -i))
    lo_name, lo_bins = population[lo_idx]
    hi_name, hi_bins = population[hi_idx]

    print("=" * 70)
    print("PRIMARY COMPARISON (PREREG Sec6.2)")
    print("=" * 70)
    print("population size:", len(population))
    print("coarse resident: %s (idx %d) resolution_bins=%d" % (lo_name, lo_idx, lo_bins))
    print("fine   resident: %s (idx %d) resolution_bins=%d" % (hi_name, hi_idx, hi_bins))

    s = _loaded_substrate()
    inner = s._inner
    anchors = _band_anchors(inner)

    prof_c, obs_c = build_profile(inner, anchors, lo_name, lo_bins, 1.0)
    prof_f, obs_f = build_profile(inner, anchors, hi_name, hi_bins, 1.0)
    steps = inner.run_rules(200)
    print("run_rules steps:", steps)

    res_c = read_results(inner, obs_c)
    res_f = read_results(inner, obs_f)

    print()
    print("%-4s %-9s %-6s %-4s %-9s %-8s   ||  %-6s %-4s %-9s %-8s" % (
        "band", "true", "eb_c", "idx_c", "qv_c", "label_c",
        "eb_f", "idx_f", "qv_f", "label_f"))
    for b in BANDS:
        c, f = res_c[b], res_f[b]
        print("%-4d %-9.4f %-6.0f %-4.0f %-9.4f %-8s   ||  %-6.0f %-4.0f %-9.4f %-8s" % (
            b, c["true_affinity"], c["effective_bins"], c["level_index"],
            c["quantized_value"], c["label"],
            f["effective_bins"], f["level_index"], f["quantized_value"], f["label"]))

    err_c = mean_abs_error(res_c)
    err_f = mean_abs_error(res_f)
    dl_c = distinct_labels(res_c)
    dl_f = distinct_labels(res_f)
    labels_c = sorted({r["label"] for r in res_c.values()})
    labels_f = sorted({r["label"] for r in res_f.values()})

    print()
    print("Prediction 1 (manipulation check) -- mean |true - quantized|:")
    print("  coarse: %.4f   fine: %.4f   ratio: %.2fx" % (err_c, err_f, err_c / err_f if err_f else float("inf")))
    print("Prediction 2 (structural certainty) -- coarse never 'neutral':")
    print("  coarse labels used: %s   ('neutral' present: %s)" % (labels_c, "neutral" in labels_c))
    print("Prediction 3 (primary) -- distinct label count, fine > coarse:")
    print("  coarse distinct labels: %d %s   fine distinct labels: %d %s" % (dl_c, labels_c, dl_f, labels_f))
    print("  PASS" if dl_f > dl_c else "  NULL (dl_f <= dl_c)")

    # -------------------------------------------------------------
    # Supplementary 1: population-wide correlation (PREREG Sec6.3)
    # -------------------------------------------------------------
    print()
    print("=" * 70)
    print("SUPPLEMENTARY 1: population-wide correlation (exploratory)")
    print("=" * 70)
    s2 = _loaded_substrate()
    inner2 = s2._inner
    anchors2 = _band_anchors(inner2)
    eb_list, err_list, dl_list, bins_list = [], [], [], []
    for name, bins in population:
        prof, obs = build_profile(inner2, anchors2, name, bins, 1.0)
        inner2.run_rules(200)
        res = read_results(inner2, obs)
        eb_list.append(res[0]["effective_bins"])
        err_list.append(mean_abs_error(res))
        dl_list.append(distinct_labels(res))
        bins_list.append(bins)

    def corr(a, b):
        a = np.array(a, dtype=float)
        b = np.array(b, dtype=float)
        if a.std() == 0 or b.std() == 0:
            return float("nan")
        return float(np.corrcoef(a, b)[0, 1])

    print("corr(effective_bins, mean_abs_error) =", round(corr(eb_list, err_list), 4))
    print("corr(effective_bins, distinct_label_count) =", round(corr(eb_list, dl_list), 4))
    from collections import Counter
    print("distinct_label_count distribution:", dict(sorted(Counter(dl_list).items())))
    print("resolution_bins distribution:", dict(sorted(Counter(bins_list).items())))

    # -------------------------------------------------------------
    # Supplementary 2: resolution_level sanity sweep (PREREG Sec6.3)
    # -------------------------------------------------------------
    print()
    print("=" * 70)
    print("SUPPLEMENTARY 2: resolution_level sanity sweep, one resident")
    print("=" * 70)
    s3 = _loaded_substrate()
    inner3 = s3._inner
    anchors3 = _band_anchors(inner3)
    for level in (0.3, 0.6, 1.0):
        prof, obs = build_profile(inner3, anchors3, "sweep_%.1f" % level, 8, level)
        inner3.run_rules(200)
        res = read_results(inner3, obs)
        eb = res[0]["effective_bins"]
        dl = distinct_labels(res)
        print("resolution_level=%.1f -> effective_bins=%.0f distinct_labels=%d labels=%s" % (
            level, eb, dl, sorted({r['label'] for r in res.values()})))

    return {
        "lo_name": lo_name, "lo_bins": lo_bins, "hi_name": hi_name, "hi_bins": hi_bins,
        "err_c": err_c, "err_f": err_f, "dl_c": dl_c, "dl_f": dl_f,
        "labels_c": labels_c, "labels_f": labels_f,
        "corr_eb_err": corr(eb_list, err_list), "corr_eb_dl": corr(eb_list, dl_list),
    }


if __name__ == "__main__":
    main()
