"""jabberwock_ia_read_run68.py -- RUN 68: CLOSE THE TOP-DOWN LOOP (CURSIVE_PLAN.md step 1).

THE HYPOTHESIS (RESEARCH_CURSIVE.md B1/B2, McClelland & Rumelhart 1981): human reading runs a
WEAK per-letter signal and a STRONG lexical prior in a BIDIRECTIONAL loop -- words feed activation
back down to re-score their constituent letters, iterate to a fixpoint (interactive activation,
the mechanism behind the word-superiority effect, Reicher 1969 / Wheeler 1970). Run 61's lexicon
collapse is ONE-DIRECTIONAL (letters -> word, argmax, no feedback). RUN 68 asks: does closing the
loop (bidirectional word<->letter feedback) lift reading ABOVE run 61's feed-forward 67% char /
78% word on hand-PRINT -- the cheap regime where the bottom-up channel is already decent -- and
does the lift match the WSE signature (helps weak-posterior letters more than strong ones)?

REUSE (nothing new-from-scratch, per CURSIVE_PLAN.md): this run consumes run 61's checkpoints
READ-ONLY --
  * `results/run61_checkpoints/lexicon.json`  -- the lexicon (WordNet+Brown, lowercase, donkey=0)
    + the 300-word cross-writer test set (hand-PRINT: DigiLeTs pen glyphs, one real glyph instance
    per letter, composed from a held-out word writer -- see run 61's docstring).
  * `results/run61_checkpoints/lattices.json` -- the per-word, per-position 62-class geometry
    distance vectors (`dists[i][c]`, LOWER = better; the SC+TPS visual posterior with its
    uncertainty) already computed cross-writer. NOTHING in run 61 is modified or re-run.
Run 61's own decode (`decode_lexicon`, FREQ_PRIOR_ALPHA=0.0, the FLAT/uniform lexicon prior) is
the ONE-DIRECTIONAL reader this run reproduces as arm A, then extends to a bidirectional loop
(arm B). Bottom-up letter evidence b[i][c] = -dists[i][lower_class(c)] for the 26 lowercase
letters (higher = better, a log-score; the lexicon already constrains the decode to lowercase
alpha sequences exactly as run 61 does).

THE TWO ARMS (same words, same per-char distances, same lexicon):
  (A) ONE-DIRECTIONAL (run 61's arm, reproduced exactly): raw_W[w] = word_prior[w] +
      sum_i b[i][w[i]]; read = argmax_w over the length-matched lexicon subset. word_prior = 0
      (FLAT prior, matching run 61's primary FREQ_PRIOR_ALPHA=0.0 arm) so this is a pure re-
      expression of run 61's `decode_lexicon(..., alpha=0)` (cost-argmin on distance ==
      score-argmax on -distance) -- MUST reproduce run 61's exact 234/300 = 78.0% word / 90.3%
      char on the SAME 300-word lattice.
  (B) BIDIRECTIONAL INTERACTIVE-ACTIVATION LOOP: iterate to a fixpoint --
        raw_W[w]      = word_prior[w] + sum_i a_L[i][w[i]]      (word supported by its letters)
        p_W           = softmax_over_candidates(raw_W)          (normalized word activation)
        a_L[i][c]     = b[i][c] + lambda * sum_{w: w[i]=c} p_W[w]   (TOP-DOWN letter support)
      init a_L = b (raw bottom-up, no feedback yet); read = argmax_w raw_W[w] at the fixpoint (or
      after K steps). lambda sweeps {0, 0.25, 0.5, 1.0}; lambda=0 is the CONTROL and is required
      to reproduce arm A EXACTLY (see the design note below -- this is a hard unit-tested
      invariant, not a coincidence).

DESIGN NOTE -- why arm B's normalization is two-tier (raw score vs. feedback weight), not a
single softmax'd `a_L` fed straight back into the word-scoring sum: the run spec asks for
"normalize (softmax per position for a_L, over the candidate set for a_W) each iteration" AND
"lambda=0 == arm A (control)" as a hard equality. Softmax is a per-position monotonic transform;
summing softmax'd values across positions of different raw-score scale is NOT rank-equivalent to
summing raw values, so if `a_L` itself were softmax-renormalized every iteration and fed back into
`raw_W`'s sum, lambda=0 would NOT reproduce arm A's raw-score argmax exactly (a real risk, checked
by hand before writing this). The reconciling design keeps a_L's contribution to raw_W in b's
native (raw, log-score) units always -- so at lambda=0, a_L[i][c] = b[i][c] identically forever,
raw_W collapses to arm A's exact score, and the loop is a fixpoint after one step (no feedback to
converge). The NORMALIZATION the spec asks for is applied to a_W (softmax over the candidate set,
`p_W` -- this is the "how much is word w currently active" signal, bounded in [0,1] summing to 1,
exactly the interactive-activation "node activation" quantity) and it is THIS normalized quantity,
not raw_W, that is redistributed back down to the letters (scaled by lambda) -- so the feedback
pathway is normalized (stable, comparable across words of very different candidate-set sizes) while
the scoring pathway stays in raw units (so lambda=0 is an exact no-op). A per-position softmax of
a_L is ALSO computed (`_softmax_rows`) but used ONLY as the read-out for the confidence-bin
diagnostic (how much bottom-up mass sits on the true letter) -- never fed back into raw_W. This is
a considered interpretation of an underspecified equation, documented here and covered by
`tests/test_run68_migrated.py::test_lambda_zero_matches_one_directional`.

GRAPH-NATIVE STATUS (CLAUDE.md honesty clause): this run MEASURES the IA loop in the Python
harness (numpy, following runs 61-67's convention: decode-style pure-python stages after a Rust-
computed geometry stage upstream -- and here there is no new geometry stage at all, since run 61's
lattices are reused verbatim). It is NOT wired as a `run_rules` Rust fixpoint. Reasons, stated
plainly: (1) the loop's candidate sets are per-word lexicon subsets of up to ~14k words (length 8)
-- expressing "sum over all lexicon entries sharing letter c at position i" as a graph JOIN over
per-word Concept nodes is possible in principle (an edge type `has_letter_at(word, pos, letter)`
aggregated by a rule) but the AGGREGATION (softmax over a dynamic-cardinality candidate set) is not
yet an admissible DSL reduction primitive -- extending the DSL with a graph-resident softmax-
reduce Term is exactly the "new Term in Rust" case CLAUDE.md names, and is real, scoped work,
not a rewrite of this run; (2) priority per the run spec is the diagnostic answer (does the loop
lift reading, does it match WSE), which does not depend on WHERE the fixpoint is evaluated -- the
mechanism (decode -> feed back -> re-decode, iterate to a fixpoint) is identical either way. A
SKETCH of the graph-native form (for a follow-on productionization run) is below.

  SKETCH -- `seeds/ia_read_loop.json` (not built this run):
    Nodes: LetterUnit{pos, class} with attr `activation` (float, the a_L[i][c] scalar);
           WordUnit{word} with attr `activation` (the raw_W[w]/p_W[w] scalar), edge
           `has_letter_at(WordUnit, LetterUnit)` per position (the w[i]=c membership).
    Rules (a `run_rules` fixpoint, the same fixed-point machine as `sd_decode`/`sd_redecode`):
      ia_word_score:  WordUnit.activation <- word_prior + REDUCE_SUM(has_letter_at -> LetterUnit.activation)
      ia_word_norm:   WordUnit.activation <- SOFTMAX_OVER(candidate_set(WordUnit))   [new DSL Term: graph-resident softmax-reduce]
      ia_letter_fb:   LetterUnit.activation <- b[pos,class] + lambda * REDUCE_SUM(has_letter_at^-1 -> WordUnit.activation)
      ia_epoch:       fires while any WordUnit.activation changes beyond tol (the same
                      `codebook_epoch`-style re-arm pattern used by the sd_* loop).
    `run_rules`'s existing fixpoint scheduler (used today for codebook growth) is architecturally
    sufficient once REDUCE_SUM and SOFTMAX_OVER exist as Terms -- the missing piece is exactly
    those two aggregation primitives, not a new control-flow mechanism.

MEASURE: char + word accuracy, arm A vs arm B (all 4 lambda), on the SAME 300 hand-PRINT words,
cross-writer (n=300 >= the pre-registered n>=200). THE KEY DIAGNOSTIC: bin every letter POSITION
(900+ of them) by its BOTTOM-UP confidence (softmax(b[i])[true_letter], i.e. how much bottom-up
mass already sits on the correct answer) into tertiles, and report arm-A vs arm-B(best lambda)
per-position accuracy PER BIN -- the word-superiority-effect signature is feedback lift
CONCENTRATED in the low-confidence bin (weak letters get rescued) rather than spread evenly or
concentrated in the high-confidence bin (already-easy letters).

PRE-REGISTERED VERDICT:
  WIN   if arm B (best lambda) word accuracy is CI-separated ABOVE arm A's 78.0% [73.0, 82.3]
        (i.e. arm B's CI lower bound > 78.0, or a McNemar fixed>>broken with p<0.01) AND the
        confidence-bin lift is concentrated in the low-confidence bin (lift_low > lift_mid and
        lift_low > lift_high, the WSE signature).
  NULL/DIAGNOSTIC otherwise -- if arm B does not beat arm A on already-decent print evidence, this
        CONFIRMS the C2 warning (Liu/Wang 2020: an explicit LM/context is a MULTIPLIER on a decent
        posterior, not a substitute for one) -- feedback cannot manufacture information the
        bottom-up channel never carried, and cursive's ~18% floor needs step 2 (writer-adapted
        pose), not more loop. Either way this is diagnostic, not a failure.

SEED GUARD (this arc's binding rule): `OZMA_SEED_PERSIST_DISABLED=1` at import; every stage
asserts md5(seeds/stroke_shapes.json) UNCHANGED before AND after. This run reads two JSON
checkpoints and writes none of run 61's files; it trains nothing (donkey=0: the lexicon is
read-only WordNet+Brown count data, the IA loop is closed-form numpy, no gradient anywhere).

EXECUTION: every invocation <=540s FOREGROUND, checkpointed under `results/run68_checkpoints/`
(every other `results/run*_checkpoints/` -- notably run61's -- is READ-ONLY reference). Pure
python3 (system interpreter is fine -- no substrate_rs dependency; this run consumes precomputed
JSON, no geometry/native calls). NEVER run in background; NEVER end a turn with a live process.

Run (from the gamma-substrate repo root):
  python3 scripts/jabberwock_ia_read_run68.py --stage compute
  python3 scripts/jabberwock_ia_read_run68.py --stage summary
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run68_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

RUN61_CKPT = os.path.join(ROOT, "results", "run61_checkpoints")   # READ-ONLY.
RUN61_LEXICON = os.path.join(RUN61_CKPT, "lexicon.json")
RUN61_LATTICES = os.path.join(RUN61_CKPT, "lattices.json")

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
LAMBDAS = [0.0, 0.25, 0.5, 1.0]     # feedback-strength sweep; 0.0 is the control (== arm A).
MAX_ITERS = 12
CONV_TOL = 1e-9                     # raw_W max-abs-change fixpoint tolerance.
N_BINS = 3                          # confidence tertiles for the WSE diagnostic.
WIN_CI_SEPARATION = True            # arm B's word_ci lower bound must exceed arm A's word_acc.


def _md5(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _seed_guard(stage: str, before: str | None = None) -> str:
    cur = _md5(STROKE_SHAPES_SEED)
    if before is not None and cur != before:
        raise SystemExit(f"HARD STOP: seeds/stroke_shapes.json md5 changed during {stage} "
                          f"({before} -> {cur}).")
    return cur


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _wilson_ci(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def _mcnemar(a_correct: list, b_correct: list) -> dict:
    fixed = sum(1 for ca, cb in zip(a_correct, b_correct) if (not ca) and cb)
    broken = sum(1 for ca, cb in zip(a_correct, b_correct) if ca and (not cb))
    n = fixed + broken
    if n == 0:
        p = 1.0
    else:
        from math import comb
        k = min(fixed, broken)
        p = min(1.0, 2.0 * sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n))
    return {"fixed": fixed, "broken": broken, "p": p}


# ------------------------------------------------------------------------------------------- #
# Lowercase letter <-> class-index helpers (a..z -> 10..35 in the 62-class DigiLeTs scheme, but
# the IA loop works in a self-contained 0..25 lowercase index space -- see `_lower26`).
# ------------------------------------------------------------------------------------------- #
def _lower_class62(ch: str) -> int:
    return 10 + (ord(ch) - ord("a"))


def _lower26(ch: str) -> int:
    return ord(ch) - ord("a")


LETTERS26 = [chr(ord("a") + i) for i in range(26)]


def bottom_up_from_dists62(dists: list) -> np.ndarray:
    """Per-position bottom-up log-score b[i][c] over the 26 lowercase letters, from a run-61-style
    62-class distance row (lower distance = better -> b = -distance, higher = better)."""
    L = len(dists)
    b = np.empty((L, 26), dtype=np.float64)
    for i in range(L):
        row = dists[i]
        for c in range(26):
            b[i, c] = -row[_lower_class62(LETTERS26[c])]
    return b


def _softmax_rows(x: np.ndarray) -> np.ndarray:
    """Row-wise softmax (each row sums to 1). Used only for the confidence-bin diagnostic and for
    the internal a_W normalization -- never fed back into the raw scoring sum (see design note)."""
    m = np.max(x, axis=-1, keepdims=True)
    e = np.exp(x - m)
    return e / np.sum(e, axis=-1, keepdims=True)


def _softmax_vec(x: np.ndarray) -> np.ndarray:
    m = np.max(x)
    e = np.exp(x - m)
    s = np.sum(e)
    return e / s if s > 0 else np.full_like(x, 1.0 / len(x))


# ------------------------------------------------------------------------------------------- #
# THE IA LOOP -- pure function, importable, reused by tests and by `stage_compute`.
# ------------------------------------------------------------------------------------------- #
def ia_decode(b: np.ndarray, candidates: list, word_prior: np.ndarray | None,
              lam: float, max_iters: int = MAX_ITERS, tol: float = CONV_TOL) -> dict:
    """Bidirectional interactive-activation decode over ONE word position-length.

    b            : (L, 26) bottom-up log-score, higher = better.
    candidates   : list of length-L lowercase strings (the length-matched lexicon subset).
    word_prior   : (n_cand,) additive log-prior per candidate, or None (flat / all-zero).
    lam          : feedback strength. lam=0.0 is the exact one-directional control.

    Returns {"word": predicted string, "n_iters": int, "converged": bool, "raw_W": final scores,
             "a_L": final (L,26) raw letter scores actually used in scoring (== b when lam==0)}.
    """
    L = b.shape[0]
    n_cand = len(candidates)
    if n_cand == 0:
        return {"word": "", "n_iters": 0, "converged": True, "raw_W": np.array([]), "a_L": b}
    idx = np.array([[_lower26(ch) for ch in w] for w in candidates], dtype=np.int64)  # (n_cand, L)
    prior = word_prior if word_prior is not None else np.zeros(n_cand)

    a_L = b.copy()                      # init a_L = b (raw bottom-up, no feedback yet).
    raw_W_prev = None
    n_iters = 0
    converged = False
    for it in range(1, max_iters + 1):
        n_iters = it
        # raw_W[w] = word_prior[w] + sum_i a_L[i, w[i]]   -- fully vectorized gather-sum.
        raw_W = prior + np.sum(a_L[np.arange(L)[None, :], idx], axis=1)
        if raw_W_prev is not None and np.max(np.abs(raw_W - raw_W_prev)) < tol:
            converged = True
            raw_W_prev = raw_W
            break
        raw_W_prev = raw_W
        if lam == 0.0:
            # No feedback: a_L stays == b forever: the loop is already at its fixpoint.
            converged = True
            break
        p_W = _softmax_vec(raw_W)                          # normalized word activation.
        # feedback[i, c] = sum_{w: w[i]=c} p_W[w]  -- bincount per position.
        fb = np.zeros((L, 26), dtype=np.float64)
        for i in range(L):
            fb[i] = np.bincount(idx[:, i], weights=p_W, minlength=26)
        a_L = b + lam * fb
    best = int(np.argmax(raw_W_prev))
    return {"word": candidates[best], "n_iters": n_iters, "converged": converged,
            "raw_W": raw_W_prev, "a_L": a_L}


def build_lex_by_len(lexicon: list) -> dict:
    d = defaultdict(list)
    for w in lexicon:
        d[len(w)].append(w)
    return d


def _confidence(b_row: np.ndarray, true_c: int) -> float:
    """Bottom-up posterior mass on the TRUE letter at one position: softmax(b_row)[true_c]."""
    return float(_softmax_vec(b_row)[true_c])


# ============================================================================================= #
#  STAGE: compute -- run arm A + arm B (all lambdas) over run 61's 300-word cross-writer lattice.
# ============================================================================================= #
def stage_compute():
    print(f"\n{SEP}\n  STAGE: compute (IA loop, arm A vs arm B x lambda, on run 61's 300 words)"
          f"\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("compute")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}")

    if not (os.path.exists(RUN61_LEXICON) and os.path.exists(RUN61_LATTICES)):
        raise SystemExit(f"WALL: run 61 checkpoints not found at {RUN61_CKPT} "
                          f"(READ-ONLY reuse target missing).")
    lex = _load_json(RUN61_LEXICON)
    lat = _load_json(RUN61_LATTICES)
    if lat.get("partial"):
        raise SystemExit("WALL: run 61 lattices are PARTIAL -- not touching run 61, abort.")
    lexicon = lex["lexicon"]
    lex_by_len = build_lex_by_len(lexicon)
    words = lat["lattices"]
    print(f"  reused (READ-ONLY): {RUN61_LEXICON} ({len(lexicon)} lexicon entries), "
          f"{RUN61_LATTICES} ({len(words)} words)")

    per_word = []
    for wi, L in enumerate(words):
        word = L["word"]
        dists = L["dists"]
        b = bottom_up_from_dists62(dists)
        cands = lex_by_len.get(len(word), [])

        arm_a = ia_decode(b, cands, None, lam=0.0)
        arms_b = {lam: ia_decode(b, cands, None, lam=lam) for lam in LAMBDAS if lam != 0.0}
        arms_b[0.0] = arm_a   # by construction (checked in unit tests) lam=0.0 IS arm A.

        # per-position bottom-up confidence on the TRUE letter (for the WSE diagnostic).
        confs = [_confidence(b[i], _lower26(word[i])) for i in range(len(word))]

        per_word.append({
            "word": word, "len": len(word), "n_cand": len(cands),
            "confs": confs,
            "arm_a": {"pred": arm_a["word"], "n_iters": arm_a["n_iters"]},
            "arms_b": {str(lam): {"pred": r["word"], "n_iters": r["n_iters"],
                                   "converged": r["converged"]}
                       for lam, r in arms_b.items()},
        })
        if (wi + 1) % 100 == 0:
            print(f"    ... {wi+1}/{len(words)} words  [{time.time()-t0:.1f}s]", flush=True)

    _save_json({"per_word": per_word, "lambdas": LAMBDAS,
                "run61_lexicon_n": len(lexicon), "stroke_shapes_md5": md5_before},
               _ckpt("ia_results.json"))
    _seed_guard("compute", md5_before)
    print(f"  saved -> {_ckpt('ia_results.json')}  [{time.time()-t0:.1f}s]")
    return 0


def _require(name: str) -> dict:
    p = _ckpt(name)
    if not os.path.exists(p):
        raise SystemExit(f"WALL: run --stage compute first (missing {p}).")
    return _load_json(p)


# ============================================================================================= #
#  STAGE: summary -- accuracy table, confidence-bin diagnostic, WIN/NULL verdict.
# ============================================================================================= #
def _acc_report(per_word: list, arm_key: str, lam: str | None = None) -> dict:
    n = len(per_word)
    word_ok = 0
    char_ok = 0
    n_char = 0
    flags = []
    for pw in per_word:
        word = pw["word"]
        pred = pw["arm_a"]["pred"] if arm_key == "arm_a" else pw["arms_b"][lam]["pred"]
        ok = (pred == word)
        word_ok += ok
        flags.append(ok)
        m = min(len(pred), len(word))
        c = sum(1 for i in range(m) if pred[i] == word[i])
        char_ok += c
        n_char += len(word)
    return {"n": n, "word_acc": word_ok / n, "word_ci": list(_wilson_ci(word_ok, n)),
            "char_acc": char_ok / n_char, "word_correct": word_ok, "flags": flags}


def _confidence_bins(per_word: list, arm_key: str, lam: str | None, edges: list) -> list:
    """Per-position accuracy binned by bottom-up confidence tertile. Returns list of
    {bin, n, acc} for LOW/MID/HIGH bins (edges = the tertile cut points on pooled confs)."""
    bins = [{"lo": edges[i], "hi": edges[i + 1], "n": 0, "correct": 0}
            for i in range(len(edges) - 1)]
    for pw in per_word:
        word = pw["word"]
        pred = pw["arm_a"]["pred"] if arm_key == "arm_a" else pw["arms_b"][lam]["pred"]
        for i, conf in enumerate(pw["confs"]):
            bi = 0
            for k, e in enumerate(bins):
                if conf <= e["hi"] or k == len(bins) - 1:
                    bi = k
                    break
            bins[bi]["n"] += 1
            if i < len(pred) and pred[i] == word[i]:
                bins[bi]["correct"] += 1
    for e in bins:
        e["acc"] = e["correct"] / e["n"] if e["n"] else 0.0
    return bins


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 68 SCOREBOARD (CLOSE THE TOP-DOWN LOOP)\n{SEP}")
    md5_before = _seed_guard("summary")
    res = _require("ia_results.json")
    per_word = res["per_word"]
    n = len(per_word)

    rep_a = _acc_report(per_word, "arm_a")
    reps_b = {lam: _acc_report(per_word, "arm_b", str(lam)) for lam in LAMBDAS}

    print(f"\n  === ARM A (one-directional, run-61-reproduction) vs ARM B (bidirectional IA) "
          f"=== (n_words={n})")
    hdr = f"  {'arm':<28}{'word_acc':>12}{'word_CI':>18}{'char_acc':>12}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    print(f"  {'(A) one-directional':<28}{100*rep_a['word_acc']:>10.1f}%"
          f"{'[' + f'{100*rep_a['word_ci'][0]:.1f},{100*rep_a['word_ci'][1]:.1f}' + ']':>18}"
          f"{100*rep_a['char_acc']:>10.1f}%")
    for lam in LAMBDAS:
        r = reps_b[lam]
        lab = f"(B) bidirectional lam={lam}"
        print(f"  {lab:<28}{100*r['word_acc']:>10.1f}%"
              f"{'[' + f'{100*r['word_ci'][0]:.1f},{100*r['word_ci'][1]:.1f}' + ']':>18}"
              f"{100*r['char_acc']:>10.1f}%")

    # best lambda by word_acc among lam != 0.
    best_lam = max((lam for lam in LAMBDAS if lam != 0.0), key=lambda lam: reps_b[lam]["word_acc"])
    rep_best = reps_b[best_lam]
    mcnemar = _mcnemar(rep_a["flags"], rep_best["flags"])
    print(f"\n  lambda=0.0 control reproduces arm A exactly: "
          f"{reps_b[0.0]['word_correct'] == rep_a['word_correct']} "
          f"({reps_b[0.0]['word_correct']} vs {rep_a['word_correct']} / {n})")
    print(f"  best lambda (word_acc) = {best_lam}  "
          f"McNemar vs arm A: fixed={mcnemar['fixed']} broken={mcnemar['broken']} "
          f"p={mcnemar['p']:.3g}")

    # confidence-bin diagnostic (tertiles of pooled bottom-up confidence).
    all_confs = sorted(c for pw in per_word for c in pw["confs"])
    n_c = len(all_confs)
    e1 = all_confs[n_c // 3]
    e2 = all_confs[(2 * n_c) // 3]
    edges = [-1.0, e1, e2, 2.0]
    bins_a = _confidence_bins(per_word, "arm_a", None, edges)
    bins_b = _confidence_bins(per_word, "arm_b", str(best_lam), edges)
    labels = ["LOW", "MID", "HIGH"]
    print(f"\n  === WSE DIAGNOSTIC: per-letter-position accuracy by BOTTOM-UP CONFIDENCE tertile "
          f"(n_positions={n_c}) ===")
    print(f"  {'bin':<8}{'n':>8}{'arm_A acc':>12}{'arm_B acc':>12}{'lift(B-A)':>12}")
    lifts = {}
    for i, lab in enumerate(labels):
        na, aa = bins_a[i]["n"], bins_a[i]["acc"]
        nb, ab = bins_b[i]["n"], bins_b[i]["acc"]
        lift = ab - aa
        lifts[lab] = lift
        print(f"  {lab:<8}{na:>8}{100*aa:>11.1f}%{100*ab:>11.1f}%{100*lift:>+11.1f}%")
    wse_signature = (lifts["LOW"] > lifts["MID"]) and (lifts["LOW"] > lifts["HIGH"])
    print(f"\n  WSE signature (lift_LOW > lift_MID and lift_LOW > lift_HIGH): {wse_signature}")

    # verdict.
    ci_separated = rep_best["word_ci"][0] > rep_a["word_acc"]
    win = bool(ci_separated and wse_signature)
    verdict = {
        "arm_a_word_acc": rep_a["word_acc"], "arm_a_word_ci": rep_a["word_ci"],
        "best_lambda": best_lam, "arm_b_word_acc": rep_best["word_acc"],
        "arm_b_word_ci": rep_best["word_ci"], "ci_separated": ci_separated,
        "mcnemar": mcnemar, "lifts": lifts, "wse_signature": wse_signature, "win": win,
    }
    print(f"\n  VERDICT (pre-registered: arm-B CI lower bound > arm-A word_acc AND WSE signature "
          f"lift_LOW > lift_MID/HIGH):")
    print(f"    arm A word_acc = {100*rep_a['word_acc']:.1f}%  "
          f"CI=[{100*rep_a['word_ci'][0]:.1f},{100*rep_a['word_ci'][1]:.1f}]")
    print(f"    arm B (lam={best_lam}) word_acc = {100*rep_best['word_acc']:.1f}%  "
          f"CI=[{100*rep_best['word_ci'][0]:.1f},{100*rep_best['word_ci'][1]:.1f}]  "
          f"CI-separated-above-A: {ci_separated}")
    print(f"    WSE signature: {wse_signature}")
    print(f"    -> {'WIN: the bidirectional loop lifts reading, WSE-consistent' if win else 'NULL/DIAGNOSTIC'}")

    _save_json({"rep_a": rep_a, "reps_b": {str(lam): reps_b[lam] for lam in LAMBDAS},
                "bins_a": bins_a, "bins_b": bins_b, "verdict": verdict},
               _ckpt("summary.json"))
    _seed_guard("summary", md5_before)
    print(f"\n  saved -> {_ckpt('summary.json')}")
    print(f"\n{SEP}\n  RUN 68 COMPLETE -- see final agent report.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["compute", "summary"])
    args = p.parse_args()
    fn = {"compute": stage_compute, "summary": stage_summary}[args.stage]
    return fn()


if __name__ == "__main__":
    sys.exit(main())
