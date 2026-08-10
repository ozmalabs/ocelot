"""jabberwock_cursive_read_run67.py -- RUN 67: DISCRIMINATIVE CURSIVE READING.

Run 66 TAUGHT the jabberwock to WRITE cursive (decisive WIN: generated-with-joins matches real
cursive whole-word DTW 0.244 vs 0.566 concat; joins better 140/140). READING floored at 18.6% char
/ 0.7% word because the reading COMPARISON was wrong, not the model:
  * whole-word arc-length DTW is ENVELOPE-dominated (shuffled-letter margin only +0.021);
  * the MEDOID allograph per letter DISCARDS the query writer's actual letter style;
  * per-letter geometric discrimination is real but WEAK (same-letter invariant DTW 0.205 vs
    different 0.235 -- a 15% margin).

RUN 67 localizes the fix to the DISCRIMINATIVE per-letter COMPARISON, reusing run 66's LEARNED
generative model (letters + joins, results/run66_checkpoints, READ-ONLY). THREE levers, each
ablated, so context does the heavy lifting on a real-but-weak per-letter signal:

  1. WRITER-ADAPTIVE ALLOGRAPHS -- per candidate letter, take the BEST-matching of that letter's
     learned allographs to the query span (not the generic medoid). Adapts to the writer's style.
  2. LETTER-WEIGHTED / DISCRIMINATIVE comparison -- reuse run-57 domains/discrimination.fisher_ratio
     to weight the ALIGNED canonical points that SEPARATE the 26 letters (between-class variance /
     within-class variance across the learned allographs), instead of the shared envelope. The
     per-letter distance is a native DtwTo over sqrt(Fisher)-scaled canonical polylines -- the
     DECISION stays a held Term; ONLY the per-dimension weights change (run-57's discipline).
  3. INCREMENTAL LEXICON-TRIE BEAM -- read left-to-right through a trie built from run-61's lexicon;
     at each position the trie + prefix narrow the next-letter candidates to a FEW, where the
     2.3x-chance per-letter signal CAN separate a handful. Run 61's lexicon-collapse, made
     incremental/generative. Beam over the trie -> collapse to the best lexicon word.

ARMS (per-letter comparison method; the trie-beam collapse is SHARED so it isolates levers 1+2):
  FLOOR   run 66 lexicon_a (medoid + whole-word DTW + lexicon)         [read from run66 ckpt]
  (A)     medoid       + UNIFORM-weight per-letter DtwTo + trie-beam   [baseline reproduction]
  (B)     writer-adapt + UNIFORM-weight per-letter DtwTo + trie-beam   [lever 1 alone]
  (C)     medoid       + FISHER-weight per-letter DtwTo + trie-beam    [lever 2 alone]
  (D)     writer-adapt + FISHER-weight per-letter DtwTo + trie-beam    [FULL: 1+2+3]
  (nc)    (D) per-letter argmax, NO lexicon                            [raw per-letter signal]

GIVEN char segmentation (test words carry char_segs) -- this ISOLATES the reading-comparison
question from segmentation (noted honestly; segmentation is a separate lever).

PRE-REGISTERED MILESTONE: WIN if (D) materially beats the 18.6% char / 0.7% word floor --
  bar: (D) char > 30% AND (D) word CI-separated above the run-66 floor word acc.
  Report which lever drives the lift (A->B writer-adaptive, A->C letter-weighted, A->D full).
NULL: if even (D) floors -> cursive per-letter content is too weak geometrically even context-
  narrowed; training-free cursive reading is fundamentally context-bound below usability. Localize.

DISCIPLINE: donkey=0 (no trained net; reuse run 66's learned model READ-ONLY; the geometric
comparison DECISION is a native DtwTo; the Fisher weights are run-57's sanctioned pure-statistics
reduction; the beam is host search over the trie, the same class as run-61 decode_lexicon).
SEED GUARD: OZMA_SEED_PERSIST_DISABLED=1; every stage asserts md5(seeds/stroke_shapes.json)
UNCHANGED before+after. run*_checkpoints READ-ONLY. NO git add/commit.

Run:
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_cursive_read_run67.py \\
    --stage <prep|read|summary>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

# run 66 curriculum: reuse its learned model loaders + geometry primitives READ-ONLY.
import scripts.jabberwock_cursive_curriculum_run66 as cc66
import scripts.jabberwock_wordread_run61 as r61
from domains import discrimination as disc
from domains import deepwriting_world as dww

SEP = "=" * 92
SYMBOLS = dww.CANON_SYMBOLS
LOWER_CLASSES = list(range(10, 36))              # 'a'..'z' canonical class ids.
CANON_N = cc66.CANON_N                            # 24 aligned points per letter.
STROKE_SHAPES_SEED = cc66.STROKE_SHAPES_SEED
RUN66_CKPT = cc66.CKPT_DIR                        # results/run66_checkpoints (READ-ONLY).
CKPT_DIR = os.path.join(ROOT, "results", "run67_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run67.log")
os.makedirs(CKPT_DIR, exist_ok=True)

# pre-registered constants (reader).
BEAM_WIDTH = 2000                                 # trie-beam width (>> #same-len words -> exact).
BIG = 1e6
PER_CALL_BUDGET_SECONDS = 480.0
# pre-registered milestone bar:
BAR_CHAR = 30.0                                   # (D) char accuracy must exceed this.


# ------------------------------------------------------------------------------------------- #
#  I/O + seed guard.
# ------------------------------------------------------------------------------------------- #
def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _save(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f)


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


# ============================================================================================= #
#  MODEL LOAD (run 66 learned letters, READ-ONLY) + FISHER discriminability weights.
# ============================================================================================= #
def _run66_codebook():
    """Load run 66's learned cursive letter codebook READ-ONLY. Returns {class: [form,...]} with
    each form's canonical aligned polyline as an (CANON_N, 2) float array."""
    lt = cc66._require("letters.json")["codebook"]           # reads results/run66_checkpoints.
    canons = {}
    for c in LOWER_CLASSES:
        forms = lt.get(str(c), []) or []
        canons[c] = [np.asarray(f["canon"], float) for f in forms
                     if np.asarray(f["canon"], float).shape == (CANON_N, 2)]
    return canons


def fisher_weights(canons) -> np.ndarray:
    """LETTER-WEIGHTED discriminability (run-57 faculty). Over the ALIGNED canonical letter frame
    (each letter's own StrokeQuantize normalization: start at origin, initial-heading +x, arc-len
    1), compute a per-dimension Fisher ratio (between-class variance / within-class variance)
    across the 26 letter classes, using the learned allographs as each class's samples. High weight
    = an aligned (point, coord) that SEPARATES letters; low weight = shared cursive envelope. Pure
    statistics over already-collected features -- disc.fisher_ratio, NOT a decision.

    Returns a (CANON_N, 2) weight array normalized to mean 1 (so uniform weights == all-ones and
    the Fisher arm differs from the uniform arm ONLY in the VALUES -- run-57's discipline)."""
    D = CANON_N * 2
    # groups[dim] = list over classes; each entry = that class's allograph values at that dim.
    per_class = {}
    for c in LOWER_CLASSES:
        forms = canons.get(c, [])
        if len(forms) >= 1:
            per_class[c] = np.asarray([f.reshape(-1) for f in forms], float)   # (n_allo, D)
    w = np.zeros(D, float)
    for d in range(D):
        groups = [per_class[c][:, d] for c in per_class]
        w[d] = disc.fisher_ratio(groups)
    if not np.isfinite(w).all() or w.sum() <= 0:
        w = np.ones(D, float)
    w = w / (w.mean() or 1.0)                                 # mean 1: comparable scale to uniform.
    return w.reshape(CANON_N, 2)


def load_model():
    """The run-67 reader model: run 66's learned canonical letter allographs (READ-ONLY) + the
    per-dimension Fisher discriminability weights + sqrt scalings for the two weightings."""
    canons = _run66_codebook()
    fw = fisher_weights(canons)
    return {
        "canons": canons,                                    # {class: [(24,2) arrays]}
        "fisher_w": fw,                                       # (24,2)
        "sqrt_uniform": np.ones((CANON_N, 2), float),
        "sqrt_fisher": np.sqrt(np.maximum(fw, 0.0)),
    }


# ============================================================================================= #
#  PER-LETTER DISCRIMINATIVE COMPARISON  (native DtwTo -- the held-Term DECISION).
# ============================================================================================= #
def weighted_dtw(native, a, b, sqrt_w) -> float:
    """A held DtwTo between two aligned canonical polylines, with per-(point,coord) weighting
    applied by pre-scaling both inputs by sqrt(weight) -- so the DtwTo's squared distances become
    the Fisher-weighted squared distances (near-diagonal alignment on arc-length-resampled
    canonical forms). sqrt_w == ones -> plain invariant-DTW (== run 66's per-letter channel)."""
    a2 = (np.asarray(a, float) * sqrt_w)
    b2 = (np.asarray(b, float) * sqrt_w)
    return cc66.dtw(native, a2.tolist(), b2.tolist())


def letter_cost_vectors(native, qcanon, model):
    """For ONE query letter span (its aligned canonical polyline), return the four 26-length cost
    vectors (lower = better), one per arm's per-letter method:
        medoid_uniform, adaptive_uniform, medoid_fisher, adaptive_fisher.
    WRITER-ADAPTIVE = min over the letter's allographs (best-matching to THIS writer's span);
    MEDOID = allograph 0 only. UNIFORM vs FISHER = the sqrt-weight scaling."""
    canons = model["canons"]
    su, sf = model["sqrt_uniform"], model["sqrt_fisher"]
    mu = [BIG] * 26
    au = [BIG] * 26
    mf = [BIG] * 26
    af = [BIG] * 26
    for c in LOWER_CLASSES:
        li = c - 10
        forms = canons.get(c, [])
        if not forms:
            continue
        du = [weighted_dtw(native, qcanon, f, su) for f in forms]
        df = [weighted_dtw(native, qcanon, f, sf) for f in forms]
        mu[li] = du[0]
        au[li] = min(du)
        mf[li] = df[0]
        af[li] = min(df)
    return {"medoid_uniform": mu, "adaptive_uniform": au,
            "medoid_fisher": mf, "adaptive_fisher": af}


# ============================================================================================= #
#  INCREMENTAL LEXICON-TRIE BEAM  (lever 3 -- run 61's lexicon collapse, made incremental).
# ============================================================================================= #
def build_trie(words):
    """A prefix trie over lowercase lexicon words. Node = dict of {char: child}; a complete word is
    marked with the sentinel key '$'."""
    root = {}
    for w in words:
        node = root
        ok = True
        for ch in w:
            if not ("a" <= ch <= "z"):
                ok = False
                break
            node = node.setdefault(ch, {})
        if ok:
            node["$"] = True
    return root


def trie_beam(root, C, L, beam=BEAM_WIDTH):
    """Read LEFT-TO-RIGHT through the trie. At each position the trie + prefix NARROW the allowed
    next letters (only children present in the trie); score each by the per-letter cost C[i][li]
    (li = letter index 0..25); keep the top-`beam` partial paths. Collapse to the min-cost COMPLETE
    lexicon word of length L. Returns (predicted_word, narrowing_trace) where narrowing_trace[i] =
    the set of distinct letters the beam considered at position i (evidence the trie narrows)."""
    beams = [(0.0, root, "")]
    trace = []
    for i in range(L):
        nxt = []
        considered = set()
        for cost, node, path in beams:
            for ch, child in node.items():
                if ch == "$":
                    continue
                li = ord(ch) - ord("a")
                considered.add(ch)
                nxt.append((cost + C[i][li], child, path + ch))
        trace.append(considered)
        if not nxt:
            break
        nxt.sort(key=lambda t: t[0])
        beams = nxt[:beam]
    finals = [(cost, path) for cost, node, path in beams if "$" in node and len(path) == L]
    if not finals:                                            # no complete word survived the beam.
        finals = [(cost, path) for cost, node, path in beams if len(path) == L]
    if not finals:
        return "", trace
    finals.sort(key=lambda t: t[0])
    return finals[0][1], trace


def per_letter_argmax(C, L):
    """Raw per-letter reading (NO lexicon): argmin over the 26 letters at each position."""
    out = []
    for i in range(L):
        li = int(np.argmin(C[i]))
        out.append(chr(ord("a") + li))
    return "".join(out)


def brute_lexicon(C, L, lex_by_len):
    """Exact lexicon collapse (run-61 decode_lexicon): min summed per-letter cost over ALL
    same-length lexicon words. Cross-checks that the trie-beam is not the bottleneck (search vs
    signal): beam == brute -> the beam loses nothing, the floor is the SIGNAL not the search."""
    cands = lex_by_len.get(L, [])
    best_w, best_c = "", math.inf
    for w in cands:
        cost = 0.0
        for i, ch in enumerate(w):
            cost += C[i][ord(ch) - ord("a")]
        if cost < best_c:
            best_c, best_w = cost, w
    return best_w


def narrowing_along(trie, word):
    """Per-position trie branching factor along `word`'s prefixes: how many next-letters the trie
    ALLOWS given the preceding letters (26 -> few). Returns the mean over positions 1..L."""
    node = trie
    facs = []
    for i, ch in enumerate(word):
        if i > 0:
            facs.append(sum(1 for k in node if k != "$"))
        if ch not in node:
            break
        node = node[ch]
    return float(np.mean(facs)) if facs else float("nan")


# ============================================================================================= #
#  STAGE: prep -- build + cache the run-67 reader model (Fisher weights) + the length-keyed trie.
# ============================================================================================= #
def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (run-67 reader model: run66 letters READ-ONLY + Fisher weights "
          f"+ lexicon trie)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)
    r66_letters_md5 = _md5(os.path.join(RUN66_CKPT, "letters.json"))
    r66_prep_md5 = _md5(os.path.join(RUN66_CKPT, "prep.json"))

    model = load_model()
    n_forms = sum(len(v) for v in model["canons"].values())
    n_letters = sum(1 for v in model["canons"].values() if v)
    fw = model["fisher_w"].reshape(-1)
    print(f"  reused run 66 codebook (READ-ONLY): {n_forms} allographs over {n_letters}/26 letters",
          flush=True)
    print(f"  Fisher discriminability weights: min={fw.min():.3f} mean={fw.mean():.3f} "
          f"max={fw.max():.3f}  (mean-normalized; >1 = separating dim, <1 = shared envelope)",
          flush=True)
    # top discriminative aligned dims (point, coord).
    order = np.argsort(-fw)[:6]
    tops = [(int(d // 2), "x" if d % 2 == 0 else "y", round(float(fw[d]), 2)) for d in order]
    print(f"  most-discriminative aligned dims (pt, coord, weight): {tops}", flush=True)

    prep = cc66._require("prep.json")                         # reads run66 ckpt (READ-ONLY).
    lexicon = prep["lexicon"]
    test_words = prep["test_words"]
    trie = build_trie(lexicon)
    print(f"  lexicon = {len(lexicon)} words; trie built; test words = {len(test_words)}", flush=True)
    print(f"  test len-dist = {sorted(__import__('collections').Counter(len(w['word']) for w in test_words).items())}",
          flush=True)

    out = {
        "fisher_w": model["fisher_w"].tolist(),
        "n_forms": n_forms, "n_letters": n_letters,
        "r66_letters_md5": r66_letters_md5, "r66_prep_md5": r66_prep_md5,
        "stroke_shapes_md5": md5_before,
    }
    _save(out, _ckpt("model.json"))
    # verify run66 checkpoints untouched (READ-ONLY discipline).
    assert _md5(os.path.join(RUN66_CKPT, "letters.json")) == r66_letters_md5
    assert _md5(os.path.join(RUN66_CKPT, "prep.json")) == r66_prep_md5
    _seed_guard("prep", md5_before)
    print(f"  run66 checkpoints md5 UNCHANGED (read-only OK); saved -> {_ckpt('model.json')}  "
          f"[prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read -- THE MILESTONE. per-word costs -> trie-beam per arm. per-word checkpoint.
# ============================================================================================= #
def _char_canon(char_seg):
    """The aligned canonical polyline of a GIVEN char span (single stroke)."""
    pts = np.asarray(char_seg["strokes"][0], float)
    return cc66.invariant(pts, CANON_N)


def stage_read():
    print(f"\n{SEP}\n  STAGE: read -- MILESTONE (discriminative + writer-adaptive + trie-beam)\n{SEP}",
          flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    model = load_model()
    prep = cc66._require("prep.json")                         # READ-ONLY.
    lexicon = prep["lexicon"]
    trie = build_trie(lexicon)
    lex_by_len = r61._lex_by_len(lexicon)
    words = prep["test_words"]

    out_path = _ckpt("read.json")
    state = _load(out_path) if os.path.exists(out_path) else {"records": [], "done": False}
    if state.get("done"):
        print(f"  read already COMPLETE (n={len(state['records'])}).", flush=True)
        _report(state)
        return 0
    done = {r["wi"] for r in state["records"]}
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0

    ARMS = [("A_medoid_uniform", "medoid_uniform"),
            ("B_adaptive_uniform", "adaptive_uniform"),
            ("C_medoid_fisher", "medoid_fisher"),
            ("D_full", "adaptive_fisher")]

    for wi, w in enumerate(words):
        if wi in done:
            continue
        true = w["word"]
        L = len(true)
        # per-letter cost vectors for every arm (26-length each), per position.
        per_pos = [letter_cost_vectors(native, _char_canon(cs), model) for cs in w["char_segs"]]
        rec = {"wi": wi, "word": true}
        for arm_name, key in ARMS:
            C = [per_pos[i][key] for i in range(L)]
            pred, trace = trie_beam(trie, C, L)
            rec[arm_name] = pred
            if arm_name == "D_full":
                rec["nc_full"] = per_letter_argmax(C, L)
                # search-exactness cross-check: trie-beam vs brute-force lexicon collapse.
                rec["D_brute"] = brute_lexicon(C, L, lex_by_len)
                rec["beam_exact"] = (pred == rec["D_brute"])
                # genuine narrowing along the TRUE word's prefixes (trie 26 -> few).
                rec["narrow_true"] = narrowing_along(trie, true)
                rec["n_samelen"] = len(lex_by_len.get(L, []))
        state["records"].append(rec)
        n_new += 1
        if n_new % 10 == 0:
            _save(state, out_path)
            _seed_guard("read", md5_before)
            n = len(state["records"])
            dw = sum(1 for r in state["records"] if r["D_full"] == r["word"])
            aw = sum(1 for r in state["records"] if r["A_medoid_uniform"] == r["word"])
            print(f"    ... {n}/{len(words)}  A_word={100*aw/n:.1f}%  D_word={100*dw/n:.1f}%  "
                  f"[{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                _seed_guard("read", md5_before)
                print(f"  WALL-BUDGET: {len(state['records'])}/{len(words)} done -- re-invoke.",
                      flush=True)
                return 2
    state["done"] = True
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  read {len(state['records'])} words  [{time.time()-t0:.1f}s]", flush=True)
    _report(state)
    return 0


# ============================================================================================= #
#  REPORTING + MILESTONE VERDICT.
# ============================================================================================= #
def _char_acc(pred, true):
    n = min(len(pred), len(true))
    return sum(1 for i in range(n) if pred[i] == true[i]), len(true)


def _accs(recs, key):
    n = len(recs)
    kw = sum(1 for r in recs if r.get(key) == r["word"])
    kc = tot = 0
    for r in recs:
        a, t = _char_acc(r.get(key, ""), r["word"])
        kc += a
        tot += t
    return kw, n, (100 * kc / tot if tot else 0.0)


def _run66_floor():
    """The run 66 reading floor, read from run66 checkpoint (READ-ONLY)."""
    p = os.path.join(RUN66_CKPT, "read.json")
    if not os.path.exists(p):
        return None
    recs = _load(p)["records"]
    n = len(recs)
    out = {}
    for key in ("lexicon_a", "gen_abs_b"):
        kw = sum(1 for r in recs if r.get(key) == r["word"])
        kc = tot = 0
        for r in recs:
            a, t = _char_acc(r.get(key, ""), r["word"])
            kc += a
            tot += t
        out[key] = (100 * kw / n, _wilson(kw, n), 100 * kc / tot)
    return out


def _report(state):
    recs = state["records"]
    n = len(recs)
    if not n:
        print("  (no records)")
        return
    print(f"\n  === RUN 67: DISCRIMINATIVE CURSIVE READING (cross-writer, GIVEN seg, n={n}) ===")
    floor = _run66_floor()
    hdr = f"  {'reader':<44}{'word_acc':>10}{'word_CI':>15}{'char_acc':>10}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    def row(lab, key, recs_=None, precomp=None):
        if precomp is not None:
            wpct, ci, cpct = precomp
            kw = round(wpct * n / 100)
        else:
            kw, _, cpct = _accs(recs_ or recs, key)
            wpct = 100 * kw / n
            ci = _wilson(kw, n)
        print(f"  {lab:<44}{wpct:>8.1f}%{f'[{100*ci[0]:.1f},{100*ci[1]:.1f}]':>15}{cpct:>8.1f}%")

    if floor:
        row("FLOOR run66 lexicon_a (medoid+wordDTW+lex)", None, precomp=floor["lexicon_a"])
        row("FLOOR run66 gen_abs_b (medoid genAbS)", None, precomp=floor["gen_abs_b"])
    row("(nc) full per-letter argmax  [NO lexicon]", "nc_full")
    row("(A) medoid + uniform + trie-beam", "A_medoid_uniform")
    row("(B) +writer-adaptive (lever 1)", "B_adaptive_uniform")
    row("(C) +letter-weighted Fisher (lever 2)", "C_medoid_fisher")
    row("(D) FULL adaptive+Fisher+trie-beam", "D_full")

    # ablation attribution.
    kwA, _, _ = _accs(recs, "A_medoid_uniform")
    kwB, _, _ = _accs(recs, "B_adaptive_uniform")
    kwC, _, _ = _accs(recs, "C_medoid_fisher")
    kwD, _, _ = _accs(recs, "D_full")
    _, _, caA = _accs(recs, "A_medoid_uniform")
    _, _, caD = _accs(recs, "D_full")
    print(f"\n  ABLATION (word acc): A={100*kwA/n:.1f}%  "
          f"B(+writer-adapt)={100*kwB/n:.1f}% ({100*(kwB-kwA)/n:+.1f})  "
          f"C(+letter-weight)={100*kwC/n:.1f}% ({100*(kwC-kwA)/n:+.1f})  "
          f"D(full)={100*kwD/n:.1f}% ({100*(kwD-kwA)/n:+.1f})")
    nt = [r["narrow_true"] for r in recs if r.get("narrow_true") == r.get("narrow_true")]  # drop NaN
    nsl = np.mean([r.get("n_samelen", 0) for r in recs])
    print(f"  narrowing (lever 3): trie branching along true prefix = {np.mean(nt):.1f} letters/pos "
          f"(26 -> few); same-length lexicon words scored = {nsl:.0f}")
    beam_exact = sum(1 for r in recs if r.get("beam_exact"))
    print(f"  search-exactness: trie-beam == brute-force lexicon collapse on {beam_exact}/{n} "
          f"(the floor is the SIGNAL, not the search)" if beam_exact == n else
          f"  search-exactness: beam==brute on {beam_exact}/{n} (beam width may be pruning)")

    # McNemar D vs A.
    fa = [r["A_medoid_uniform"] == r["word"] for r in recs]
    fd = [r["D_full"] == r["word"] for r in recs]
    mc = r61._mcnemar(fa, fd)
    print(f"  McNemar (D vs A): fixed={mc['fixed']} broken={mc['broken']} p={mc['p']:.3g}")

    # MILESTONE verdict.
    ciD = _wilson(kwD, n)
    floor_word = floor["lexicon_a"][0] if floor else 0.7
    floor_word_ci_hi = None
    if floor:
        # run66 floor word CI upper bound.
        fkw = round(floor["lexicon_a"][0] * n / 100)
        floor_word_ci_hi = _wilson(fkw, n)[1] * 100
    sep = (100 * ciD[0]) > (floor_word_ci_hi if floor_word_ci_hi is not None else floor_word)
    win = (caD > BAR_CHAR) and sep
    print(f"\n  MILESTONE (bar: D char > {BAR_CHAR:.0f}% AND D word CI-separated above run66 floor):")
    print(f"    D char = {caD:.1f}%  (> {BAR_CHAR:.0f}%? {caD > BAR_CHAR})")
    print(f"    D word = {100*kwD/n:.1f}% CI[{100*ciD[0]:.1f},{100*ciD[1]:.1f}]  vs floor word "
          f"{floor_word:.1f}% (CI-hi {floor_word_ci_hi:.1f}% ; separated? {sep})"
          if floor_word_ci_hi is not None else "")
    print(f"    VERDICT: {'WIN -- discriminative cursive reading beats the floor; scale to real IAM' if win else 'NULL -- training-free cursive reading is fundamentally context-bound below usability'}")
    return win


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 67 SCOREBOARD (DISCRIMINATIVE CURSIVE READING)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    model_ckpt = _ckpt("model.json")
    if os.path.exists(model_ckpt):
        m = _load(model_ckpt)
        print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
              f"(== prep capture {m['stroke_shapes_md5']}: {md5_now == m['stroke_shapes_md5']})")
        print(f"  run66 model reused READ-ONLY: {m['n_forms']} allographs / {m['n_letters']} letters")
    rp = _ckpt("read.json")
    if os.path.exists(rp):
        _report(_load(rp))
    print(f"\n{SEP}\n  RUN 67 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["prep", "read", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "read": stage_read, "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
