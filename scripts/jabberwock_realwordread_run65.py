"""jabberwock_realwordread_run65.py -- RUN 65: THE LIGATURE-AS-CONFOUND FALSIFIER (option b, step 1).

Creator's directive: "Model the ligature as a confound -- option b."

Run 64 established the floor: the FULL parse-marginal recognizer (run 16/17's 80.5% Omniglot
verdict) + WITHIN-corpus DeepWriting CONNECTED cursive chars = 17.8% char acc [14.3, 21.8], 26-way
(vs run 63's 33% ISOLATED ceiling, chance 3.85%). Run 64's own diagnosis: chars CUT from cursive
carry LIGATURE strokes (the pen-doesn't-lift connectors) that corrupt the exemplar match; the top
confusions are ligature-driven (a->o, e->i, e->l, e->r, h->u).

THE CONFOUND FRAME (native_collapse predict->residual): the character = the INTENT (content); the
ligature = the CONFOUND the physical realization adds (a smooth connecting stroke, near baseline,
low curvature, from the previous char's exit to the next char's entry). The PREDICT-RESIDUAL
decomposition: the ligature is the PREDICTABLE part (a smooth baseline connector); the character-
CORE is the RESIDUAL (the distinctive deviation). RUN 65 TESTS: does modeling / STRIPPING the
ligature confound recover character accuracy off the 17.8% floor toward the 33% isolated level?

DESIGN -- PURE MEASUREMENT, recognizer REUSED VERBATIM. This script does NOT modify abs_read /
recognition_graph. It reuses run 64's OWN bank + query set (loads run64_checkpoints/prep.json
READ-ONLY -- byte-identical bank exemplars + query chars, so f=0 MUST reproduce 17.8%) and run 64's
staging/verdict path (`stage_parse_char` + `parse_marginal_verdict`). The ONLY new thing is a
STRIP TRANSFORM applied to each char's stroke list BEFORE it is written to the Omniglot temp file
-- applied IDENTICALLY to bank exemplars and query chars (bank cores vs query cores, apples to
apples). f=0 / no-strip is the control (== run 64).

PRE-REGISTERED STRIPPING OPERATIONALIZATIONS (each strips the ligature, keeps the core):
  1. ENDPOINT-TRIM(f): strip a fraction f of the trajectory ARC-LENGTH at each temporal END of the
     char span (the entry/exit connectors); keep the middle CORE. Sweep f in {0, .1, .15, .2, .25}.
     f=0 == run 64's baseline (no strip).
  2. BASELINE-CONNECTOR STRIP: estimate the char's baseline (the writing line -- where the
     ligatures enter/leave, taken as the y of the entry+exit points); strip END-region points that
     are BOTH near-baseline (within a y-band) AND low-curvature (the ligature signature). Pre-reg:
     end fraction 0.30, band 0.20*y-range, low-curvature |turn| < 30 deg.
  3. PREDICT-RESIDUAL (the principled native_collapse form): fit a smooth low-curvature CONNECTOR
     (the straight segment entry->exit -- the pure-ligature prediction) and take the character-CORE
     as the span points with HIGH perpendicular RESIDUAL from that connector (the distinctive
     deviation). Keep residual >= thresh; drop the near-connector points. Sweep thresh in
     {0.10, 0.15} * bbox-diag. Confound-as-prediction, core-as-residual.

MEASURE per op: 26-way char accuracy vs the 17.8% floor (op f=0) and the 33% isolated ceiling; the
confusion-structure change (do the ligature-driven confusions a->o / e->i / e->l REDUCE when the
ligature is stripped? -- the direct mechanism check).

PRE-REGISTERED VERDICT: LICENSED (build the full joint reader) if a stripping op MATERIALLY lifts
char acc above 17.8% -- bar: point estimate > 25% AND its 95% CI lower bound clears run 64's 21.8%
upper bound (CI-separated lift) -- AND the ligature-driven confusions reduce. NULL if no op helps
(the ligature is not cleanly separable from the core at the trajectory level, or the given
segmentation already includes too much neighbor ink) -> report why + what a fuller joint model
needs. This is the CHEAP falsifier for option b; a lift licenses the big joint-reader build.

donkey=0: geometry only, no trained net. SEED GUARD: OZMA_SEED_PERSIST_DISABLED=1; every stage
asserts md5(seeds/stroke_shapes.json) UNCHANGED before+after. run64_checkpoints READ-ONLY (input);
all writes to run65_checkpoints. NO git add/commit.

Stages: recognize (loops the pre-registered ops, per-op resumable checkpoints) -> summary.
Run:
  OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_realwordread_run65.py --stage <S>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from collections import Counter, defaultdict

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import scripts.jabberwock_realwordread_run64 as r64
import scripts.jabberwock_wordread_run61 as r61

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run65_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
# RUN 64's prep -- READ ONLY. Byte-identical bank + query set (f=0 must reproduce run 64).
R64_PREP = os.path.join(ROOT, "results", "run64_checkpoints", "prep.json")

SYMBOLS = r64.SYMBOLS
LOWER_CLASSES = r64.LOWER_CLASSES
N_TEST_CHARS = r64.N_TEST_CHARS          # 400 -- same query prefix as run 64 (CI-comparable).

# Ligature-driven confusions to track (run 64's top confusions among lowercase pairs).
LIGATURE_CONFUSIONS = [("e", "i"), ("e", "l"), ("a", "o"), ("e", "r"), ("h", "u"), ("e", "x")]

# The run-64 floor + run-63 ceiling, for the report + the CI-separated LICENSED bar.
FLOOR_ACC = 0.178
FLOOR_CI_HI = 0.218          # run 64's Wilson upper bound -- a lift must clear this to be "material".
CEIL_ACC = 0.33
LICENSED_POINT_BAR = 0.25

PER_CALL_BUDGET_SECONDS = 470.0
INF = math.inf


# ------------------------------------------------------------------------------------------- #
#  I/O + seed guard (mirror run 64).
# ------------------------------------------------------------------------------------------- #
def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _save(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def _load(path):
    with open(path) as f:
        return json.load(f)


def _seed_guard(stage, before=None):
    cur = _md5(STROKE_SHAPES_SEED)
    if before is not None and cur != before:
        raise SystemExit(f"HARD STOP: seeds/stroke_shapes.json md5 changed during {stage} "
                         f"({before} -> {cur}).")
    return cur


def _wilson(k, n):
    return r61._wilson_ci(k, n)


# ------------------------------------------------------------------------------------------- #
#  STRIP TRANSFORMS -- operate on a list of (m,2) stroke arrays, return a list of stroke arrays.
#  Applied IDENTICALLY to bank exemplars and query chars. All guard: if < MIN_KEEP points would
#  remain, return the ORIGINAL strokes unchanged (an honest non-strip, never an empty char).
# ------------------------------------------------------------------------------------------- #
MIN_KEEP = 4


def _concat(strokes):
    """Concatenate stroke point-arrays in temporal order. Returns (P[N,2], sid[N])."""
    pts, sid = [], []
    for i, s in enumerate(strokes):
        a = np.asarray(s, float).reshape(-1, 2)
        if len(a) == 0:
            continue
        pts.append(a)
        sid.extend([i] * len(a))
    if not pts:
        return np.zeros((0, 2)), np.zeros((0,), int)
    return np.vstack(pts), np.asarray(sid, int)


def _arclen_cum(P, sid):
    """Cumulative arc length along the concatenated path; steps ACROSS a stroke boundary (pen-up
    jump) contribute 0 (the ligature is WITHIN a pen-down stroke, not the inter-stroke jump)."""
    d = np.zeros(len(P))
    for i in range(1, len(P)):
        if sid[i] == sid[i - 1]:
            d[i] = float(np.linalg.norm(P[i] - P[i - 1]))
    return np.cumsum(d)


def _regroup(P, sid, mask):
    """Rebuild a stroke list from the kept points, preserving original stroke membership + order."""
    out = []
    if not mask.any():
        return out
    order = np.arange(len(P))
    for s in sorted(set(sid[mask].tolist())):
        idx = order[(sid == s) & mask]
        if len(idx) >= 1:
            out.append(P[idx])
    return out


def _turn_angles(P):
    """Per-point absolute turning angle (radians) between the incoming and outgoing segment;
    endpoints get 0. Robust to zero-length segments."""
    ang = np.zeros(len(P))
    for i in range(1, len(P) - 1):
        v1 = P[i] - P[i - 1]
        v2 = P[i + 1] - P[i]
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 < 1e-9 or n2 < 1e-9:
            continue
        c = float(np.dot(v1, v2) / (n1 * n2))
        ang[i] = math.acos(max(-1.0, min(1.0, c)))
    return ang


def strip_none(strokes):
    """The f=0 control: identity (== run 64's staging)."""
    return [np.asarray(s, float).reshape(-1, 2) for s in strokes]


def strip_endpoint_trim(strokes, f):
    """OP 1: strip a fraction f of the arc-length at each temporal END; keep the middle core."""
    if f <= 0:
        return strip_none(strokes)
    P, sid = _concat(strokes)
    if len(P) < MIN_KEEP:
        return strip_none(strokes)
    cum = _arclen_cum(P, sid)
    L = float(cum[-1])
    if L <= 0:
        return strip_none(strokes)
    lo, hi = f * L, (1.0 - f) * L
    mask = (cum >= lo) & (cum <= hi)
    if int(mask.sum()) < MIN_KEEP:
        return strip_none(strokes)
    return _regroup(P, sid, mask)


def strip_baseline_connector(strokes, end_frac=0.30, band_frac=0.20, angle_deg=30.0):
    """OP 2: strip END-region points that are BOTH near the baseline (writing line, taken as the y
    of the entry+exit points) AND low-curvature -- the ligature signature. Interior + high-curvature
    ink is kept regardless."""
    P, sid = _concat(strokes)
    if len(P) < MIN_KEEP:
        return strip_none(strokes)
    cum = _arclen_cum(P, sid)
    L = float(cum[-1])
    if L <= 0:
        return strip_none(strokes)
    baseline_y = 0.5 * (float(P[0, 1]) + float(P[-1, 1]))   # writing line: where the ligatures sit.
    yr = float(P[:, 1].max() - P[:, 1].min())
    band = band_frac * yr if yr > 0 else 0.0
    ang = _turn_angles(P)
    thr = math.radians(angle_deg)
    in_end = (cum <= end_frac * L) | (cum >= (1.0 - end_frac) * L)
    near_base = np.abs(P[:, 1] - baseline_y) <= band
    low_curv = ang < thr
    strip = in_end & near_base & low_curv
    keep = ~strip
    if int(keep.sum()) < MIN_KEEP:
        return strip_none(strokes)
    return _regroup(P, sid, keep)


def strip_predict_residual(strokes, thresh_frac=0.15):
    """OP 3: the native_collapse form. Predict the confound as the smooth straight CONNECTOR
    (entry->exit -- the pure-ligature prediction); the character-CORE is the RESIDUAL: points with
    HIGH perpendicular distance from that connector. Keep residual >= thresh_frac * bbox-diag."""
    P, sid = _concat(strokes)
    if len(P) < MIN_KEEP:
        return strip_none(strokes)
    a, b = P[0], P[-1]
    ab = b - a
    Lab = float(np.linalg.norm(ab))
    if Lab < 1e-9:
        # degenerate connector (entry ~ exit, e.g. a closed loop): residual = distance from entry.
        resid = np.linalg.norm(P - a, axis=1)
    else:
        u = ab / Lab
        ap = P - a
        proj = ap @ u
        perp = ap - np.outer(proj, u)
        resid = np.linalg.norm(perp, axis=1)
    mn = P.min(axis=0)
    mx = P.max(axis=0)
    diag = float(np.linalg.norm(mx - mn))
    if diag <= 0:
        return strip_none(strokes)
    thr = thresh_frac * diag
    keep = resid >= thr
    if int(keep.sum()) < MIN_KEEP:
        return strip_none(strokes)
    return _regroup(P, sid, keep)


# ------------------------------------------------------------------------------------------- #
#  Pre-registered op table. Each op = (op_id, transform callable). f=0 first (the control).
# ------------------------------------------------------------------------------------------- #
def _op_table():
    ops = []
    for f in (0.0, 0.10, 0.15, 0.20, 0.25):
        ops.append((f"endpoint_trim_f{f:.2f}", (lambda ss, f=f: strip_endpoint_trim(ss, f))))
    ops.append(("baseline_connector", strip_baseline_connector))
    for t in (0.10, 0.15):
        ops.append((f"predict_residual_t{t:.2f}", (lambda ss, t=t: strip_predict_residual(ss, t))))
    return ops


# ------------------------------------------------------------------------------------------- #
#  Staging: bank + query strokes go through the SAME transform before write_omni_file.
# ------------------------------------------------------------------------------------------- #
def _stage_bank_stripped(scratch, bank, transform, tmpdir, ar):
    node2class = {}
    for c in LOWER_CLASSES:
        for j, strokes in enumerate(bank[c]):
            p = os.path.join(tmpdir, f"bank_{c}_{j}.txt")
            r64.write_omni_file(transform(strokes), p)
            node = ar.stage_parse_char(scratch, p, is_query=False, name=str(c))
            node2class[node] = c
    return node2class


def _run_op(op_id, transform, bank, units, ar, srs, md5_before, out_path, state, t0, deadline):
    """Recognize all query chars under one strip op. Resumable: records keyed by qid, checkpointed
    every 100 chars. Returns state (records may be partial if the wall-budget hit)."""
    done_ids = {r["qid"] for r in state["records"]}
    tmpdir = tempfile.mkdtemp(prefix=f"run65_{op_id}_")
    scratch = srs.Substrate()
    node2class = _stage_bank_stripped(scratch, bank, transform, tmpdir, ar)
    qp = os.path.join(tmpdir, "query.txt")
    n_new = 0
    for u in units:
        if u["qid"] in done_ids:
            continue
        r64.write_omni_file(transform(u["strokes"]), qp)
        qn = ar.stage_parse_char(scratch, qp, is_query=True)
        w = ar.parse_marginal_verdict(scratch, qn)
        pred = node2class.get(w, -1) if w is not None else -1
        state["records"].append({"qid": u["qid"], "true_class": u["true_class"],
                                  "pred_class": int(pred), "word": u["word"]})
        n_new += 1
        if n_new % 100 == 0:
            _save(state, out_path)
            _seed_guard("recognize", md5_before)
            k = sum(1 for r in state["records"] if r["pred_class"] == r["true_class"])
            print(f"      [{op_id}] {len(state['records'])}/{len(units)}  "
                  f"acc={100*k/len(state['records']):.1f}%  [{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                state["partial"] = True
                _save(state, out_path)
                return state
    state["done"] = True
    state.pop("partial", None)
    _save(state, out_path)
    return state


# ============================================================================================= #
#  STAGE: recognize -- loop the pre-registered ops. Per-op checkpoint file; resumable; drives one
#  op at a time and returns 2 (re-invoke) when the wall-budget is near, so the ops complete across
#  a few blocking calls.
# ============================================================================================= #
def stage_recognize():
    print(f"\n{SEP}\n  STAGE: recognize (ligature-strip ops x parse-marginal, connected cursive)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("recognize")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}")
    import substrate_rs as srs
    from domains import abs_read as ar

    if not os.path.exists(R64_PREP):
        raise SystemExit(f"WALL: run 64 prep missing at {R64_PREP} (needed as READ-ONLY input).")
    prep = _load(R64_PREP)
    print(f"  reusing run 64 prep (READ-ONLY): stroke_shapes_md5={prep['stroke_shapes_md5']} "
          f"(== live {md5_before}: {prep['stroke_shapes_md5']==md5_before})")
    bank = r64._select_bank(prep["bank_glyph_pool"])
    n_bank = sum(len(v) for v in bank.values())
    units = r64._query_units(prep["test_words"])[:N_TEST_CHARS]
    print(f"  bank: {n_bank} exemplars / {len(LOWER_CLASSES)} classes;  query chars: {len(units)} "
          f"(same as run 64)", flush=True)

    ops = _op_table()
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    for op_id, transform in ops:
        out_path = _ckpt(f"op_{op_id}.json")
        state = _load(out_path) if os.path.exists(out_path) else {"records": [], "done": False}
        if state.get("done"):
            continue
        print(f"  --- op {op_id} (resume from {len(state['records'])}) ---", flush=True)
        state = _run_op(op_id, transform, bank, units, ar, srs, md5_before, out_path, state,
                        t0, deadline)
        if not state.get("done"):
            print(f"  WALL-BUDGET during {op_id} ({len(state['records'])}/{len(units)}) -- "
                  f"re-invoke --stage recognize to resume.", flush=True)
            _seed_guard("recognize", md5_before)
            return 2
        k = sum(1 for r in state["records"] if r["pred_class"] == r["true_class"])
        n = len(state["records"])
        ci = _wilson(k, n)
        print(f"  == op {op_id} DONE: acc={100*k/n:.1f}% [{100*ci[0]:.1f},{100*ci[1]:.1f}] "
              f"n={n}  [{time.time()-t0:.1f}s]", flush=True)
    _seed_guard("recognize", md5_before)
    print(f"  ALL OPS DONE  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: summary -- the char-accuracy table + confusion-reduction check + LICENSED/NULL verdict.
# ============================================================================================= #
def _op_stats(state):
    recs = state["records"]
    n = len(recs)
    k = sum(1 for r in recs if r["pred_class"] == r["true_class"])
    conf = Counter()
    for r in recs:
        if r["pred_class"] != r["true_class"]:
            tp = SYMBOLS[r["true_class"]]
            pp = SYMBOLS[r["pred_class"]] if r["pred_class"] >= 0 else "?"
            conf[(tp, pp)] += 1
    return n, k, conf


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 65 LIGATURE-CONFOUND FALSIFIER SCOREBOARD\n{SEP}")
    md5_now = _seed_guard("summary")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}", flush=True)

    ops = _op_table()
    rows = []
    control_conf = None
    for op_id, _ in ops:
        p = _ckpt(f"op_{op_id}.json")
        if not os.path.exists(p):
            rows.append((op_id, None))
            continue
        st = _load(p)
        if not st.get("done"):
            rows.append((op_id, ("PARTIAL", len(st["records"]))))
            continue
        n, k, conf = _op_stats(st)
        ci = _wilson(k, n)
        rows.append((op_id, (n, k, ci, conf)))
        if op_id == "endpoint_trim_f0.00":
            control_conf = conf

    print(f"\n  === CHAR-ACCURACY TABLE (26-way, connected cursive, cross-writer, n={N_TEST_CHARS}) ===")
    print(f"  floor (run 64, f=0) = {100*FLOOR_ACC:.1f}% [.. {100*FLOOR_CI_HI:.1f}]   "
          f"ceiling (run 63 ISOLATED) = {100*CEIL_ACC:.0f}%   chance = 3.85%")
    hdr = f"  {'strip op':<26}{'n':>5}{'char_acc':>11}{'95% CI':>16}   vs floor"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    best = None
    for op_id, v in rows:
        if v is None:
            print(f"  {op_id:<26}{'--- not run ---':>32}")
            continue
        if v[0] == "PARTIAL":
            print(f"  {op_id:<26}{'PARTIAL n=%d' % v[1]:>32}")
            continue
        n, k, ci, conf = v
        acc = k / n
        lift = acc - FLOOR_ACC
        sep = "CI-SEP" if ci[0] > FLOOR_CI_HI else ("+" if lift > 0 else "")
        print(f"  {op_id:<26}{n:>5}{100*acc:>9.1f}%"
              f"{f'[{100*ci[0]:.1f},{100*ci[1]:.1f}]':>16}   {100*lift:+.1f}pp {sep}")
        if op_id != "endpoint_trim_f0.00" and (best is None or acc > best[1]):
            best = (op_id, acc, ci, conf)

    # --- ligature-confusion reduction (the direct mechanism check) ---
    print(f"\n  === LIGATURE-CONFUSION REDUCTION (control f=0 -> best strip op) ===")
    lic_reduced = False
    if control_conf is not None and best is not None:
        bconf = best[3]
        print(f"  best strip op = {best[0]} (acc {100*best[1]:.1f}%)")
        print(f"  {'confusion':<12}{'f=0':>7}{'stripped':>11}{'delta':>9}")
        tot0 = totb = 0
        for a, b in LIGATURE_CONFUSIONS:
            c0 = control_conf.get((a, b), 0)
            cb = bconf.get((a, b), 0)
            tot0 += c0
            totb += cb
            print(f"  {a+'->'+b:<12}{c0:>7}{cb:>11}{cb-c0:>+9}")
        print(f"  {'TOTAL':<12}{tot0:>7}{totb:>11}{totb-tot0:>+9}")
        lic_reduced = totb < tot0
        print(f"  ligature-driven confusions {'REDUCED' if lic_reduced else 'did NOT reduce'} "
              f"({tot0} -> {totb})")

    # --- verdict ---
    print(f"\n  === PRE-REGISTERED VERDICT ===")
    licensed = False
    if best is not None:
        op_id, acc, ci, _ = best
        material = acc > LICENSED_POINT_BAR and ci[0] > FLOOR_CI_HI
        licensed = material and lic_reduced
        print(f"  best strip: {op_id} = {100*acc:.1f}% [{100*ci[0]:.1f},{100*ci[1]:.1f}]")
        print(f"  material lift (>{100*LICENSED_POINT_BAR:.0f}% AND CI-lo > floor-hi "
              f"{100*FLOOR_CI_HI:.1f}%): {material}")
        print(f"  ligature-confusions reduced: {lic_reduced}")
    verdict = "LICENSED -- build the full joint reader (option b)" if licensed else \
              "NULL -- ligature not cleanly separable from the core at the trajectory level"
    print(f"  -> RUN 65 VERDICT: {verdict}")
    print(f"\n{SEP}\n  RUN 65 COMPLETE -- see final agent report.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["recognize", "summary"])
    args = p.parse_args()
    if args.stage == "recognize":
        return stage_recognize()
    if args.stage == "summary":
        return stage_summary()
    return 1


if __name__ == "__main__":
    sys.exit(main())
