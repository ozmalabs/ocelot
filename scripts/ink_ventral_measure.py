"""INK × VENTRAL — does the ventral machinery retroactively improve the handwriting arc?

THE RUNNER for `VISION_INK_VENTRAL_PREREG.md` (committed BEFORE this ran, §3). Reuses the RUN 16
harness verbatim (`scripts/jabberwock_omniglot_run16_reconcile.py`'s own LEARN + block structure,
which itself reuses `scripts/jabberwock_omniglot_dynamic_quantization.py`) so that A0/A1 are
BYTE-IDENTICAL control arms and their reproduction is a real check, not a restatement.

GATE 0 (§1 — calibrate the measure before the agent; NO confirmatory seed consumed):
  G0a  exact synthetic positive/negative control of the `EnclosedCount` Term, 6 cases.
  G0b  writer-invariance on real ink: modal-agreement rate over 10 alphabets x 20 chars x all
       drawers, against a CLASS-SHUFFLED null (seed 54001) — the honest chance level GIVEN the
       marginal hole-count distribution.
  G0c  informativeness: the per-class modal hole-count distribution, its entropy, and f0 (the
       fraction of classes whose modal hole count is 0). PRE-DECLARED: f0 > 0.90 records H1 as
       REFUTED AT THE PREMISE, independently of any accuracy delta.

CONFIRMATORY (seed 54000, n = 400 fixed in advance):
  A0  ADOPTED            earned quanta (delta=0 + appearance)          -- CONTROL
  A1  SC+TPS FULL DWELL  the borrowed continuous verdict, all 20       -- CONTROL
  A2  TOPOLOGY ALONE     held Argmin over (|holes_q - holes_c|, ci)    -- FLOOR
  A3  SC+TPS + TOPOLOGY GATE   A1 restricted to hole-count-equal candidates (H1)
  A4  D4-UNTANGLED SC+TPS      min over g in D4 of SC+TPS(g.query, cand) (H3)

H2 is measured off the SAME records with no extra compute: A0's accuracy RESTRICTED to A1's error
episodes, with a Wilson CI, against the 5% chance floor, plus the oracle-union ceiling.

donkey=0: every decision on the path is a HELD TERM evaluate — `EnclosedCount` (the new Rust
primitive), `Eq` (A3's per-candidate admission), `Argmin` over (score, id) pairs (A2/A3/A4's
winners, `ar._argmin_pairs_term`), and `abs_rerank_targeted`/`sctps_rerank`'s own internal held
verdicts (A0/A1, unchanged). Python here iterates real files, applies MECHANICAL coordinate
transforms (the D4 group elements — geometry, not a decision), and aggregates already-decided
results. No Python min/max/sort/argmin on any decision path. No torch.

A3 REUSES A1's OWN COMPUTED SCORES (the restricted candidate set is a SUBSET of the full dwell,
so the per-candidate distances are identical by construction) — so A3 costs nothing and cannot
differ from A1 for any reason other than the gate.

Run:
  PYTHONPATH=.:runners/dsl/python python scripts/ink_ventral_measure.py
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np

from domains import engine_provenance

# PROTOCOL §10 rule 3 / 1b -- PIN, do not merely REPORT. This import was
# BELOW `scripts.jabberwock_omniglot_dynamic_quantization`, which LOADS the
# engine, so the prescribed "one-line fix" placed here-as-found would have
# been a NO-OP ON RESOLUTION: an extension module is bound at first import and
# a later `sys.path` insert cannot rebind it. The import is hoisted and the
# pin runs before anything can load the engine.
engine_provenance.engine_preamble()

import scripts.jabberwock_omniglot_dynamic_quantization as gate  # noqa: E402
import scripts.jabberwock_omniglot_run16_reconcile as run16  # noqa: E402
from domains import abs_read as ar  # noqa: E402
from domains import omniglot_world as ow  # noqa: E402

SEP = "=" * 92

# --------------------------------------------------------------------------------------------
# SEEDS — the pre-registered 54000 block. Recorded here so the results file cannot drift from
# what the pre-registration claimed.
# --------------------------------------------------------------------------------------------
SEED_POWERED = 54000
SEED_G0B_NULL = 54001
SEED_SHUFFLE_LABELS = 54002

WAY = gate.WAY
EPISODES_PER_ALPHABET = WAY
R_TARGET = 2                       # n = 10 alphabets x R=2 x 20 = 400, FIXED IN ADVANCE (§3.3)
POWER_ALPHABETS = run16.POWER_ALPHABETS
LEARN_STROKE_CAP = run16.LEARN_STROKE_CAP

# The standing numbers the controls must reproduce (CI-overlap, not equality).
RUN15_ADOPTED = {"acc": 0.268, "ci": (0.226, 0.313), "n": 400}
RUN16_ADOPTED = {"acc": 0.220, "ci": (0.168, 0.282), "n": 200}
RUN16_SCTPS_FULL = {"acc": 0.735, "ci": (0.670, 0.791), "n": 200}

OUT_JSON = os.path.join(ROOT, "results", "ink_ventral_measure.json")


# --------------------------------------------------------------------------------------------
# HELD-TERM WRAPPERS — every one of these is ONE `native.evaluate` of a Term, never a Python
# decision. `EnclosedCount` is the new Rust primitive; the rest are pre-existing standard Terms.
# --------------------------------------------------------------------------------------------
def enclosed_count_term(strokes: list) -> dict:
    return {"type": "EnclosedCount", "arg": {"type": "Lit", "value": strokes}}


def holes_of(native, stroke_points: list):
    """ONE held `EnclosedCount` evaluate over the figure's own pen polylines. Returns
    `(holes, clamped)`; `(None, False)` for degenerate ink (an honest miss, never a
    fabricated count). NOTE the documented gotcha: `native.evaluate()` returns TUPLES, and a
    `Dict` comes back as a plain dict here — both are read explicitly, never via isinstance."""
    polys = []
    for item in stroke_points:
        arr = np.asarray(item[0], dtype=float).reshape(-1, 2)
        if arr.shape[0] >= 1:
            polys.append(arr.tolist())
    if not polys:
        return None, False
    d = native.evaluate(enclosed_count_term(polys), {})
    if d is None:
        return None, False
    holes = d["holes"] if "holes" in d else None
    clamped = bool(d.get("clamped", 0.0)) if hasattr(d, "get") else False
    if holes is None:
        return None, clamped
    return int(round(float(holes))), clamped


def eq_decides_admissible(native, hq: int, hc: int) -> bool:
    """A3's ADMISSION DECISION — ONE held `Eq` evaluate, exactly the `widen_decision` precedent.
    Python does not compare the two integers; the graph does."""
    return bool(native.evaluate(
        {"type": "Eq", "a": {"type": "Lit", "value": float(hq)},
         "b": {"type": "Lit", "value": float(hc)}}, {}))


# --------------------------------------------------------------------------------------------
# THE D4 GROUP — the group the wall crossing ACTUALLY EARNED (`shape_decode.rs`'s own
# `rotation90` + `reflection_r`/`reflection_c` generators). Applying it to an already
# centre+abs-max-normalized point set is EXACTLY measure-preserving (rot90 swaps axes, so the
# abs-max is unchanged; reflection negates one axis, likewise) — so no re-normalization is
# needed and the transform cannot smuggle in a scale change.
# These are MECHANICAL coordinate maps, not decisions.
# --------------------------------------------------------------------------------------------
def d4_orbit(ps: list) -> list:
    if ps is None:
        return []
    a = np.asarray(ps, dtype=float)
    out = []
    for refl in (False, True):
        b = a.copy()
        if refl:
            b[:, 1] = -b[:, 1]
        for _k in range(4):
            out.append(b.tolist())
            b = np.stack([-b[:, 1], b[:, 0]], 1)
    return out


def _acc_ci(preds, trues):
    k = sum(1 for p, t in zip(preds, trues) if p == t)
    acc = k / max(1, len(trues))
    lo, hi = gate.wilson_ci(k, len(trues))
    return acc, (lo, hi), k


def _sep(ci_a, ci_b) -> bool:
    return gate._ci_separated(ci_a, ci_b)


def _verdict(name_a, a, ci_a, name_b, b, ci_b) -> str:
    if not _sep(ci_a, ci_b):
        return f"NULL (CIs overlap; delta {100*(a-b):+.1f}pp)"
    return ("CROSSES" if a > b else "HARM") + f" (CI-separated; delta {100*(a-b):+.1f}pp)"


# --------------------------------------------------------------------------------------------
# GATE 0a — exact synthetic control of the instrument.
# --------------------------------------------------------------------------------------------
def _circle(cx, cy, r, n, frac=1.0):
    return [[cx + r * math.cos(frac * 2 * math.pi * i / n),
             cy + r * math.sin(frac * 2 * math.pi * i / n)] for i in range(n + 1)]


def _figure_eight(r, n):
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        pts.append([r * math.sin(2 * t), r * math.sin(t)])
    return pts


def gate0a(native) -> dict:
    cases = [
        ("closed circle", [_circle(0, 0, 10, 120)], 1),
        ("open 270 arc", [_circle(0, 0, 10, 120, 0.75)], 0),
        ("figure of eight", [_figure_eight(10, 200)], 2),
        ("two nested circles", [_circle(0, 0, 10, 120), _circle(0, 0, 4, 60)], 2),
        ("straight line", [[[0, 0], [10, 0], [20, 0]]], 0),
        ("three scattered points", [[[0, 0], [1, 0]], [[9, 4], [10, 4]], [[3, 9], [4, 9]]], 0),
    ]
    rows = []
    for name, strokes, want in cases:
        d = native.evaluate(enclosed_count_term(strokes), {})
        got = int(round(float(d["holes"])))
        rows.append({"case": name, "want": want, "got": got, "ok": got == want,
                     "grid": [int(d["grid_w"]), int(d["grid_h"])], "cell": float(d["cell"])})
    return {"rows": rows, "pass": all(r["ok"] for r in rows)}


# --------------------------------------------------------------------------------------------
# GATE 0b / 0c — real-ink writer-invariance and informativeness.
# --------------------------------------------------------------------------------------------
def gate0bc(s, native, dk, alphabets) -> dict:
    per_class = []          # list of lists of hole counts, one list per class
    clamp_hits = 0
    n_drawings = 0
    # DIAGNOSTIC-ONLY accumulators (they enter NO verdict; see the module's own note and
    # `ink_topology.rs`'s: a bare hole count cannot tell a perceptual counter from a one-cell
    # pen-jitter micro-loop, and a null has to be DIAGNOSED, not shrugged at).
    tot_holes = 0
    tot_one_cell = 0
    hole_frac_area = []
    t0 = time.time()
    for alph in alphabets:
        chars = sorted(ow.characters(alph, "evaluation"))[:WAY]
        for cd in chars:
            counts = []
            for path in ow.drawings(cd):
                try:
                    strokes = ow.load_strokes(path, drop_degenerate=True)
                except Exception:
                    continue
                polys = [np.asarray(x, dtype=float).reshape(-1, 2).tolist() for x in strokes
                         if np.asarray(x).reshape(-1, 2).shape[0] >= 1]
                if not polys:
                    continue
                d = native.evaluate(enclosed_count_term(polys), {})
                if d is None:
                    continue
                nh = int(round(float(d["holes"])))
                counts.append(nh)
                clamp_hits += 1 if float(d.get("clamped", 0.0)) else 0
                n_drawings += 1
                tot_holes += nh
                tot_one_cell += int(round(float(d.get("holes_one_cell", 0.0))))
                gc = float(d.get("grid_cells", 0.0))
                if nh > 0 and gc > 0:
                    hole_frac_area.append(float(d.get("hole_cells_max", 0.0)) / gc)
            if counts:
                per_class.append(counts)

    def modal_agreement(groups):
        rates = []
        for g in groups:
            vals, cnts = np.unique(np.asarray(g), return_counts=True)
            rates.append(float(cnts.max()) / float(len(g)))
        return float(np.mean(rates)) if rates else 0.0, rates

    obs_rate, obs_rates = modal_agreement(per_class)

    # NULL: reshuffle every drawing across classes, preserving the group sizes. This is the
    # honest chance level GIVEN the marginal hole-count distribution -- exactly the count-matched
    # null discipline this arc already standardized.
    flat = [v for g in per_class for v in g]
    rng = np.random.default_rng(SEED_G0B_NULL)
    perm = list(flat)
    rng.shuffle(perm)
    shuffled_groups, i = [], 0
    for g in per_class:
        shuffled_groups.append(perm[i:i + len(g)])
        i += len(g)
    null_rate, null_rates = modal_agreement(shuffled_groups)

    # Per-class agreement is a mean of per-class rates; report a normal-approx 95% CI on that
    # mean (the unit of analysis is the CLASS, §4 -- never the drawing).
    def mean_ci(xs):
        a = np.asarray(xs, dtype=float)
        if a.size < 2:
            return (0.0, 0.0)
        se = float(a.std(ddof=1) / math.sqrt(a.size))
        m = float(a.mean())
        return (max(0.0, m - 1.959963984540054 * se), min(1.0, m + 1.959963984540054 * se))

    obs_ci, null_ci = mean_ci(obs_rates), mean_ci(null_rates)

    modes = []
    for g in per_class:
        vals, cnts = np.unique(np.asarray(g), return_counts=True)
        modes.append(int(vals[int(np.argmax(cnts))]))
    modes_arr = np.asarray(modes)
    vals, cnts = np.unique(modes_arr, return_counts=True)
    p = cnts / cnts.sum()
    entropy = float(-(p * np.log2(p)).sum())
    f0 = float((modes_arr == 0).mean())

    return {
        "n_classes": len(per_class), "n_drawings": n_drawings, "clamp_hits": clamp_hits,
        "clamp_rate": clamp_hits / max(1, n_drawings),
        "modal_agreement": obs_rate, "modal_agreement_ci": obs_ci,
        "null_modal_agreement": null_rate, "null_modal_agreement_ci": null_ci,
        "g0b_pass": bool(obs_ci[0] > null_ci[1]),
        "mode_hist": {int(v): int(c) for v, c in zip(vals, cnts)},
        "mode_entropy_bits": entropy, "f0": f0,
        "g0c_refutes_at_premise": bool(f0 > 0.90),
        "mean_holes_per_drawing": tot_holes / max(1, n_drawings),
        "diag_total_holes": tot_holes, "diag_one_cell_holes": tot_one_cell,
        "diag_one_cell_fraction": tot_one_cell / max(1, tot_holes),
        "diag_largest_hole_area_fraction_mean":
            float(np.mean(hole_frac_area)) if hole_frac_area else 0.0,
        "diag_largest_hole_area_fraction_median":
            float(np.median(hole_frac_area)) if hole_frac_area else 0.0,
        "elapsed": time.time() - t0,
    }


# --------------------------------------------------------------------------------------------
# THE CONFIRMATORY BLOCK.
# --------------------------------------------------------------------------------------------
def _episode(s, native, dk, qd, true_idx, ex_composed, ex_stroke_points, ex_ps, ex_holes):
    t0 = time.time()
    adopted = ar.abs_rerank_targeted(
        s, qd["composed_sig"], qd["stroke_points"], ex_composed, ex_stroke_points,
        delta=0.0, use_widen=False, use_appearance=True, turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
        segments=dk["segments"])
    t_a0 = time.time() - t0
    w_a0 = adopted["winner"] if adopted["winner"] is not None else -1
    shortlist = adopted["shortlist0"]

    q_ps = ar.whole_figure_point_set(qd["stroke_points"])

    # ---- A1: SC+TPS FULL DWELL. Its per-candidate scores are captured and REUSED by A3. ----
    t0 = time.time()
    full = ar.sctps_rerank(native, q_ps, ex_ps, list(range(len(ex_ps))))
    t_a1 = time.time() - t0
    w_a1 = full["winner"] if full["winner"] is not None else -1
    full_pairs = list(full["scores"])          # [(score, ci), ...] over every scored candidate

    # ---- topology of the query (ONE held EnclosedCount) ----
    hq, q_clamped = holes_of(native, qd["stroke_points"])

    # ---- A2: TOPOLOGY ALONE -- held Argmin over (|dh|, ci). Ties resolve to the lowest ci. ----
    w_a2 = -1
    n_topo_ties = 0
    if hq is not None:
        pairs_t = [(float(abs(hq - hc)), ci) for ci, hc in enumerate(ex_holes) if hc is not None]
        if pairs_t:
            best = min(sc for sc, _ in pairs_t)
            n_topo_ties = sum(1 for sc, _ in pairs_t if sc == best)
            wt = native.evaluate(ar._argmin_pairs_term(pairs_t), {})
            if wt is not None:
                w_a2 = int(wt[1])

    # ---- A3: SC+TPS + TOPOLOGY GATE. Admission is ONE held `Eq` per candidate; the winner is
    #      the SAME held Argmin over the SAME A1 scores, restricted. Zero free parameters. ----
    w_a3 = w_a1
    a3_fell_back = 0
    a3_admitted = len(full_pairs)
    if hq is not None and full_pairs:
        admitted = [(sc, ci) for sc, ci in full_pairs
                    if ex_holes[ci] is not None and eq_decides_admissible(native, hq, ex_holes[ci])]
        a3_admitted = len(admitted)
        if admitted:
            w3 = native.evaluate(ar._argmin_pairs_term(admitted), {})
            if w3 is not None:
                w_a3 = int(w3[1])
        else:
            a3_fell_back = 1

    # ---- A4: D4-UNTANGLED SC+TPS -- min over the earned group, then held Argmin. ----
    t0 = time.time()
    w_a4 = -1
    n_a4_compares = 0
    if q_ps is not None:
        # Every (group element, candidate) pair enters ONE held Argmin. `min over g, then argmin
        # over ci` and `argmin over (g, ci) jointly` are the SAME winner by construction -- so
        # the generator-invariant residual is decided by the graph, with no Python min anywhere.
        pairs4: list = []
        for gq in d4_orbit(q_ps):
            r = ar.sctps_rerank(native, gq, ex_ps, list(range(len(ex_ps))))
            n_a4_compares += r["n_compared"]
            pairs4.extend(r["scores"])
        if pairs4:
            w4 = native.evaluate(ar._argmin_pairs_term(pairs4), {})
            if w4 is not None:
                w_a4 = int(w4[1])
    t_a4 = time.time() - t0

    return dict(true=true_idx, w_a0=w_a0, w_a1=w_a1, w_a2=w_a2, w_a3=w_a3, w_a4=w_a4,
                hq=(hq if hq is not None else -1), q_clamped=int(q_clamped),
                a3_admitted=a3_admitted, a3_fell_back=a3_fell_back, n_topo_ties=n_topo_ties,
                in_shortlist=1 if true_idx in shortlist else 0, shortlist_size=len(shortlist),
                n_a1_compared=full["n_compared"], n_a4_compares=n_a4_compares,
                t_a0=t_a0, t_a1=t_a1, t_a4=t_a4)


def _run_block(s, native, dk, cache, alph, rng):
    t0 = time.time()
    chars = sorted(ow.characters(alph, "evaluation"))[:WAY]
    drawer_files = [ow.drawings(cd) for cd in chars]
    n_drawers = min(len(fl) for fl in drawer_files)

    ex_drawer = int(rng.integers(n_drawers))
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, dk)
                 for ci in range(WAY)]
    ex_composed = [e["composed_sig"] for e in exemplars]
    ex_stroke_points = [e["stroke_points"] for e in exemplars]
    ex_ps = [ar.whole_figure_point_set(e["stroke_points"]) for e in exemplars]
    ex_holes = []
    for e in exemplars:
        h, _c = holes_of(native, e["stroke_points"])
        ex_holes.append(h)

    records = []
    for qi in range(min(EPISODES_PER_ALPHABET, WAY)):
        q_drawer = int(rng.integers(n_drawers))
        while q_drawer == ex_drawer:
            q_drawer = int(rng.integers(n_drawers))
        qd = gate.decode_char_signature(s, drawer_files[qi][q_drawer], cache, dk)
        records.append(_episode(s, native, dk, qd, qi, ex_composed, ex_stroke_points,
                                ex_ps, ex_holes))
    return {"records": records, "elapsed": time.time() - t0,
            "ex_holes": [h if h is not None else -1 for h in ex_holes]}


def main() -> int:
    t_start = time.time()
    print(SEP)
    print("  INK x VENTRAL -- does the ventral machinery retroactively improve the")
    print("  handwriting arc? (VISION_INK_VENTRAL_PREREG.md, seeds 54000-54999)")
    print(SEP)
    prov = engine_provenance.provenance_line()
    print(f"\n  {prov}")

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    s, ag, native = gate.boot()

    # ---------------------------------------------------------------------------------------
    print(f"\n{SEP}\n  GATE 0a -- EXACT SYNTHETIC CONTROL OF `EnclosedCount` (§1)\n{SEP}")
    g0a = gate0a(native)
    for r in g0a["rows"]:
        print(f"    {r['case']:<26s} want={r['want']}  got={r['got']}  "
              f"{'OK' if r['ok'] else 'MISS'}   grid={r['grid']}  cell={r['cell']:.4f}")
    print(f"  G0a VERDICT: {'PASS' if g0a['pass'] else 'FAIL -- the instrument does not measure enclosure; the rung STOPS here'}")
    if not g0a["pass"]:
        json.dump({"g0a": g0a, "provenance": prov}, open(OUT_JSON, "w"), indent=1)
        return 1

    # ---------------------------------------------------------------------------------------
    print(f"\n{SEP}\n  PHASE 1: LEARN (RUN 16's caps verbatim)\n{SEP}")
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    lr = gate.run_learn(s, ag, native, learn_alphabets, gate.LEARN_DRAWERS, LEARN_STROKE_CAP,
                        gate.DK, gate.GROWTH_WINDOW)
    growth = lr["growth"]
    first = float(np.mean([g["new_quanta"] for g in growth[:1]])) if growth else 0.0
    last = float(np.mean([g["new_quanta"] for g in growth[-2:]])) if len(growth) >= 2 else 0.0
    sat_pass = bool(last <= max(3.0, 0.3 * first)) if first > 0 else True
    import domains.stroke_codebook as sc
    final_codebook = len(sc._existing_names(s, "stroke"))
    print(f"  processed {lr['n_strokes']} pen-down strokes "
          f"({lr['n_degenerate_skipped']} degenerate skipped) in {lr['elapsed']:.1f}s.")
    print(f"  saturation: first-window new={first:.1f} -> last-2-windows mean new={last:.1f}  "
          f"VERDICT: {'PASS' if sat_pass else 'FAIL'}")
    print(f"  final LEARN codebook size: {final_codebook} stroke quanta (RUN 15/16 produced 7).")

    # ---------------------------------------------------------------------------------------
    print(f"\n{SEP}\n  GATE 0b / 0c -- WRITER-INVARIANCE AND INFORMATIVENESS ON REAL INK (§1)\n{SEP}")
    g0 = gate0bc(s, native, gate.DK, POWER_ALPHABETS)
    print(f"  {g0['n_classes']} classes, {g0['n_drawings']} drawings, "
          f"clamp rate {100*g0['clamp_rate']:.2f}% ({g0['clamp_hits']} figures)")
    print(f"  G0b modal-agreement  observed = {100*g0['modal_agreement']:.1f}% "
          f"95% CI [{100*g0['modal_agreement_ci'][0]:.1f}, {100*g0['modal_agreement_ci'][1]:.1f}]")
    print(f"      class-shuffled null   = {100*g0['null_modal_agreement']:.1f}% "
          f"95% CI [{100*g0['null_modal_agreement_ci'][0]:.1f}, {100*g0['null_modal_agreement_ci'][1]:.1f}]")
    print(f"  G0b VERDICT: {'PASS -- topology IS writer-invariant above the marginal null' if g0['g0b_pass'] else 'FAIL -- not separated from the marginal null'}")
    print(f"  G0c per-class modal hole-count histogram: {g0['mode_hist']}")
    print(f"      entropy = {g0['mode_entropy_bits']:.4f} bits over {g0['n_classes']} classes;  f0 = {100*g0['f0']:.1f}%")
    print(f"  DIAGNOSTIC (enters NO verdict): {g0['diag_total_holes']} holes over "
          f"{g0['n_drawings']} drawings ({g0['mean_holes_per_drawing']:.2f}/drawing); "
          f"{100*g0['diag_one_cell_fraction']:.1f}% are ONE-CELL micro-loops; "
          f"largest hole covers {100*g0['diag_largest_hole_area_fraction_median']:.2f}% of the "
          f"raster (median)")
    print(f"  G0c VERDICT: {'REFUTED AT THE PREMISE (f0 > 90%: the feature is near-constant on this corpus)' if g0['g0c_refutes_at_premise'] else 'informative enough to proceed'}")

    # ---------------------------------------------------------------------------------------
    print(f"\n{SEP}\n  PHASE 2: CONFIRMATORY POWERED RUN -- n = {len(POWER_ALPHABETS)} x R={R_TARGET} x {EPISODES_PER_ALPHABET} = {len(POWER_ALPHABETS)*R_TARGET*EPISODES_PER_ALPHABET}, seed {SEED_POWERED}\n{SEP}")
    cache: dict = {}
    rng = np.random.default_rng(SEED_POWERED)
    all_records = []
    for alph in POWER_ALPHABETS:
        for r in range(R_TARGET):
            blk = _run_block(s, native, gate.DK, cache, alph, rng)
            all_records.extend(blk["records"])
            print(f"    {alph:<24s} r={r}  {len(blk['records'])} episodes in {blk['elapsed']:.1f}s"
                  f"   exemplar holes={blk['ex_holes']}")

    n = len(all_records)
    trues = [r["true"] for r in all_records]
    arms = {"a0": "A0 ADOPTED (earned quanta)", "a1": "A1 SC+TPS FULL DWELL",
            "a2": "A2 TOPOLOGY ALONE", "a3": "A3 SC+TPS + TOPOLOGY GATE",
            "a4": "A4 D4-UNTANGLED SC+TPS"}
    shuf = list(trues)
    np.random.default_rng(SEED_SHUFFLE_LABELS).shuffle(shuf)

    res = {}
    print(f"\n  {n} total episodes scored.\n")
    for key, label in arms.items():
        preds = [r[f"w_{key}"] for r in all_records]
        a, ci, k = _acc_ci(preds, trues)
        a_s, _ci_s, _k_s = _acc_ci(preds, shuf)
        res[key] = {"acc": a, "ci": ci, "k": k, "n": n, "acc_shuffled": a_s}
        print(f"  {label:<32s} n={n:4d}  k={k:4d}  acc={100*a:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]   shuffled={100*a_s:4.1f}%")

    # ---- H2: complementarity, off the SAME records ----
    a1_wrong = [r for r in all_records if r["w_a1"] != r["true"]]
    k_h2 = sum(1 for r in a1_wrong if r["w_a0"] == r["true"])
    h2_acc = k_h2 / max(1, len(a1_wrong))
    h2_ci = gate.wilson_ci(k_h2, len(a1_wrong))
    oracle_k = sum(1 for r in all_records if r["w_a0"] == r["true"] or r["w_a1"] == r["true"])
    oracle_acc = oracle_k / max(1, n)
    oracle_ci = gate.wilson_ci(oracle_k, n)
    both_k = sum(1 for r in all_records if r["w_a0"] == r["true"] and r["w_a1"] == r["true"])

    # ---- diagnostics ----
    a3_gate_changed = sum(1 for r in all_records if r["w_a3"] != r["w_a1"])
    a3_fellback = sum(r["a3_fell_back"] for r in all_records)
    mean_admitted = float(np.mean([r["a3_admitted"] for r in all_records]))
    mean_ties = float(np.mean([r["n_topo_ties"] for r in all_records]))
    q_clamped = sum(r["q_clamped"] for r in all_records)
    coverage_shortlist = float(np.mean([r["in_shortlist"] for r in all_records]))
    mean_shortlist = float(np.mean([r["shortlist_size"] for r in all_records]))
    t_a0 = sum(r["t_a0"] for r in all_records)
    t_a1 = sum(r["t_a1"] for r in all_records)
    t_a4 = sum(r["t_a4"] for r in all_records)
    n_a4 = sum(r["n_a4_compares"] for r in all_records)

    print(f"\n  DIAGNOSTICS")
    print(f"    A3 topology gate changed the A1 winner on {a3_gate_changed}/{n} episodes "
          f"({100*a3_gate_changed/max(1,n):.1f}%); mean admitted candidates {mean_admitted:.2f}/20; "
          f"empty-gate fallbacks {a3_fellback}")
    print(f"    A2 mean tied candidates at the winning |dh|: {mean_ties:.2f}/20 "
          f"(the tie is why the floor arm is what it is)")
    print(f"    query clamp hits: {q_clamped}/{n} (a non-zero value invalidates the §13 "
          f"resolution derivation for those figures)")
    print(f"    coverage@shortlist {100*coverage_shortlist:.1f}%  mean shortlist {mean_shortlist:.2f}")
    print(f"    cost: A0 {t_a0:.1f}s  A1 {t_a1:.1f}s ({1000*t_a1/max(1,n*20):.2f}ms/compare)  "
          f"A4 {t_a4:.1f}s over {n_a4} compares ({1000*t_a4/max(1,n_a4):.2f}ms/compare)")

    # ---------------------------------------------------------------------------------------
    print(f"\n{SEP}\n  VERDICTS (decision rules FIXED in the pre-registration, §5)\n{SEP}")
    ctrl0_ok = not _sep(res["a0"]["ci"], RUN15_ADOPTED["ci"])
    ctrl1_ok = not _sep(res["a1"]["ci"], RUN16_SCTPS_FULL["ci"])
    print(f"  CONTROL A0 vs RUN 15's 26.8% [22.6, 31.3]: {100*res['a0']['acc']:.1f}% "
          f"[{100*res['a0']['ci'][0]:.1f}, {100*res['a0']['ci'][1]:.1f}] -- "
          f"{'CI-OVERLAP (reproduced)' if ctrl0_ok else 'CI-SEPARATED (control DID NOT reproduce)'}")
    print(f"  CONTROL A1 vs RUN 16's 73.5% [67.0, 79.1]: {100*res['a1']['acc']:.1f}% "
          f"[{100*res['a1']['ci'][0]:.1f}, {100*res['a1']['ci'][1]:.1f}] -- "
          f"{'CI-OVERLAP (reproduced)' if ctrl1_ok else 'CI-SEPARATED (control DID NOT reproduce)'}")

    h1 = _verdict("A3", res["a3"]["acc"], res["a3"]["ci"], "A1", res["a1"]["acc"], res["a1"]["ci"])
    h3 = _verdict("A4", res["a4"]["acc"], res["a4"]["ci"], "A1", res["a1"]["acc"], res["a1"]["ci"])
    h2_verdict = "COMPLEMENTARY" if h2_ci[0] > 0.05 else "NULL"
    print(f"\n  H1 (topology gate)      A3 {100*res['a3']['acc']:.1f}% vs A1 {100*res['a1']['acc']:.1f}%  --> {h1}")
    if g0["g0c_refutes_at_premise"]:
        print(f"       ... and G0c ALREADY REFUTED H1 AT THE PREMISE (f0 = {100*g0['f0']:.1f}% > 90%). "
              f"The A3 delta CONFIRMS that diagnosis; it is not the verdict's basis.")
    print(f"  H2 (contour x ductus)   A0 on A1's {len(a1_wrong)} errors = {100*h2_acc:.1f}% "
          f"95% CI [{100*h2_ci[0]:.1f}, {100*h2_ci[1]:.1f}] vs 5.0% chance --> {h2_verdict}")
    print(f"       oracle-union (A0 or A1 correct) = {100*oracle_acc:.1f}% "
          f"[{100*oracle_ci[0]:.1f}, {100*oracle_ci[1]:.1f}];  both correct on {both_k}/{n}")
    print(f"  H3 (D4 untangling)      A4 {100*res['a4']['acc']:.1f}% vs A1 {100*res['a1']['acc']:.1f}%  --> {h3}")

    crossing = ("CROSSES" in h1) or ("CROSSES" in h3)
    print(f"\n  OVERALL: {'CROSSING' if crossing else 'DIAGNOSED NEGATIVE'} "
          f"(a crossing requires H1 or H3 to be CI-separated ABOVE A1)")

    donkey = "torch" not in sys.modules
    print(f"  donkey=0 (no torch in sys.modules): {'PASS' if donkey else 'FAIL'}")
    print(f"  total runtime: {time.time()-t_start:.1f}s")

    out = {
        "provenance": prov, "seeds": {"powered": SEED_POWERED, "g0b_null": SEED_G0B_NULL,
                                       "shuffled_labels": SEED_SHUFFLE_LABELS},
        "protocol": {"way": WAY, "alphabets": POWER_ALPHABETS, "r": R_TARGET,
                      "episodes_per_alphabet": EPISODES_PER_ALPHABET, "n": n,
                      "split": "evaluation", "learn_stroke_cap": LEARN_STROKE_CAP,
                      "learn_alphabets": learn_alphabets, "dk": gate.DK},
        "learn": {"n_strokes": lr["n_strokes"], "codebook": final_codebook,
                   "saturation_pass": sat_pass, "first_window_new": first, "last_windows_new": last},
        "g0a": g0a, "g0bc": g0,
        "arms": res,
        "h1_verdict": h1, "h2_verdict": h2_verdict, "h3_verdict": h3,
        "h2": {"n_a1_errors": len(a1_wrong), "k": k_h2, "acc": h2_acc, "ci": h2_ci,
                "oracle_union_acc": oracle_acc, "oracle_union_ci": oracle_ci, "both_correct": both_k},
        "controls_reproduced": {"a0_vs_run15": ctrl0_ok, "a1_vs_run16": ctrl1_ok},
        "diagnostics": {"a3_gate_changed": a3_gate_changed, "a3_fellback": a3_fellback,
                         "a3_mean_admitted": mean_admitted, "a2_mean_ties": mean_ties,
                         "query_clamp_hits": q_clamped,
                         "coverage_shortlist": coverage_shortlist,
                         "mean_shortlist": mean_shortlist,
                         "t_a0": t_a0, "t_a1": t_a1, "t_a4": t_a4, "n_a4_compares": n_a4},
        "overall": "CROSSING" if crossing else "DIAGNOSED NEGATIVE",
        "donkey_zero": donkey,
        "elapsed": time.time() - t_start,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(out, open(OUT_JSON, "w"), indent=1, default=float)
    print(f"  saved -> {OUT_JSON}")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
