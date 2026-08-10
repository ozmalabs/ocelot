"""jabberwock_realwordread_run62.py -- RUN 62: REAL-INK WORD READING (manifold-collapse reader on
REAL connected handwriting).

THE ADVANCE OVER RUN 61: run 61 proved the manifold-collapse principle on the GLYPH axis using
SYNTHETIC pre-segmented words (real cross-writer DigiLeTs glyphs concatenated). Run 62 adds the
SEGMENTATION AXIS on REAL connected cursive ink (DeepWriting / IAM-OnDB): where the character
boundaries fall WITHIN a word is itself ambiguous, held open, and collapsed JOINTLY with the glyph
identities by the lexicon. The creator's key: "he||o is a manifold held in suspension and collapses
in context" -- glyph + SEGMENTATION are ONE joint manifold; premature commitment DESTROYS it.

DATA: DeepWriting (Aksan et al. CHI'18), IAM-OnDB-derived, 294 authors, per-point stroke +
CHARACTER-level and WORD-level segmentation labels. Loaded by `domains.deepwriting_world` (mechanical
adapter). Words are REAL connected-ink, cross-writer, in-vocabulary (Brown+WordNet, len 3-8).

TWO PATHS on real ink:
  PATH 1 (char boundaries GIVEN -- the easier real-ink test, run 61 on REAL connected glyphs):
    per given char segment -> 62-class geometry candidates -> {no-context argmin} vs {lexicon-collapse}.
  PATH 2 (the JOINT MANIFOLD reader -- the real advance): HOLD SEGMENTATION OPEN. An arc-length KNOT
    lattice over the word ink; every span (knot_a,knot_b) -> 62-class geometry candidates. The
    lexicon collapses the (segmentation x glyph) lattice JOINTLY -- a TRIE-constrained Viterbi over
    boundaries chooses BOTH how many characters and which, simultaneously. The no-context contrast
    COMMITS the segmentation first (best free segmentation, then per-span argmax; also an oracle-count
    variant) -- segment-then-recognize, the thing the manifold-collapse principle forbids.

REUSE: run 61's decoders + homoglyph machinery (`decode_no_context`, `decode_lexicon`,
`_is_homoglyph_pair`, `_wilson_ci`, `_mcnemar`, `HOMOGLYPH_GROUPS`); run 47's per-stroke SC+TPS
geometry verdict (`ps.program_score`, `_stroke_point_sets_from_arrays`). NOTHING in run 47/61 modified.

donkey=0: WordNet+Brown counts, NO trained neural LM. The recognizer is one-shot geometry; the
lexicon is read-only count data; the joint decode is a mechanical held-Term Viterbi.

SEED GUARD: OZMA_SEED_PERSIST_DISABLED=1; every stage asserts md5(seeds/stroke_shapes.json) UNCHANGED.

Stages (dependency order):  prep -> bank -> recognize_path1 -> recognize_joint -> decode -> summary
  (prep/decode/summary pure-python; bank/recognize_* need substrate_rs via run 47 geometry.)
Run:
  PYTHONPATH=.:runners/dsl/python DEEPWRITING_DIR=/tmp/handwriting \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_realwordread_run62.py --stage <S>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

# Reuse run 61 (decoders + homoglyph + stats) and run 62's own loader.
import scripts.jabberwock_wordread_run61 as r61
from domains import deepwriting_world as dww

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run62_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
SYMBOLS = dww.CANON_SYMBOLS                      # == DIGILETS order; run61 decoders use this order.

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
SPLIT = "training"                 # the large split (34.5k samples, 207 writers with words).
WRITER_SPLIT_SEED = 20260706
N_BACKGROUND_FRAC = 0.5            # half the writers -> bank exemplars; other half -> test words.
BANK_M = 3                        # exemplars per class.
BANK_SEED = 20260711
N_TEST = 240                      # test words (>= 200 pre-reg).
WORD_SELECT_SEED = 20260712
WORD_MIN_LEN, WORD_MAX_LEN = 3, 8

# Joint-lattice params.
KNOT_DENSITY = 2.6                # boundary candidates per expected character (arc-length grid).
KMAX = 26                        # cap on total knots (boundaries) per word.
WMAX = 7                         # a character may span up to this many boundary gaps.
FREE_SEG_LAMBDA_MULT = 1.0       # free-segmentation per-char penalty = this * median bank char cost.

FREQ_PRIOR_ALPHA = 0.0            # PRIMARY lexicon arm: flat (uniform over valid words).
FREQ_PRIOR_ALPHA_WEIGHTED = 1.0  # secondary arm: + Brown unigram log-frequency prior.

# WIN thresholds (pre-registered): manifold-collapse MATERIALLY beats no-context on REAL ink.
WIN_WORD_ACC_RATIO = 2.0         # collapse word acc >= 2x no-context word acc (both paths).
WIN_HOMOGLYPH_RESOLVED = 0.50    # >= 50% of no-context homoglyph char-errors resolved (path 1).

INF = math.inf


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


# ------------------------------------------------------------------------------------------- #
#  Lexicon (donkey=0: Brown + WordNet count data).
# ------------------------------------------------------------------------------------------- #
def _build_lexicon():
    from nltk.corpus import brown, wordnet as wn
    brown_counts = Counter(w.lower() for w in brown.words() if w.isalpha())
    wn_lemmas = {l for l in wn.all_lemma_names() if l.isalpha() and l.islower()}
    lex = {w for w in (set(brown_counts) | wn_lemmas)
           if w.isalpha() and w.islower() and WORD_MIN_LEN <= len(w) <= WORD_MAX_LEN}
    total = sum(brown_counts.values())
    logfreq = {w: math.log((brown_counts.get(w, 0) + 1) / (total + len(lex))) for w in lex}
    return sorted(lex), logfreq, brown_counts


# ============================================================================================= #
#  STAGE: prep -- load DeepWriting, cross-writer split, select test words + bank glyph pool.
# ============================================================================================= #
def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (DeepWriting load + cross-writer split + word selection)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}")

    lex, logfreq, brown_counts = _build_lexicon()
    lexset = set(lex)
    print(f"  lexicon (Brown+WordNet, len {WORD_MIN_LEN}-{WORD_MAX_LEN}) = {len(lex)}  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    dw = dww.load_deepwriting(SPLIT)
    print(f"  DeepWriting '{SPLIT}': {dw['n']} samples  [{time.time()-t0:.1f}s]", flush=True)
    words = dww.extract_words(dw, min_len=WORD_MIN_LEN, max_len=WORD_MAX_LEN,
                              lowercase_only=True, complete_only=True, lexicon=lexset)
    glyphs = dww.extract_char_glyphs(dw)
    print(f"  complete in-lex words = {len(words)} (writers "
          f"{len({w['writer'] for w in words})});  char glyphs = {len(glyphs)}  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    # cross-writer split: background writers -> bank; held-out writers -> test words.
    bg_words, ho_words = dww.writer_split(words, n_background_frac=N_BACKGROUND_FRAC,
                                          seed=WRITER_SPLIT_SEED)
    bg_writers = {w["writer"] for w in bg_words}
    ho_writers = {w["writer"] for w in ho_words}
    # bank glyphs come from BACKGROUND writers ONLY (disjoint from test-word writers).
    bank_glyphs = [g for g in glyphs if g["writer"] in bg_writers]
    print(f"  bank writers={len(bg_writers)}  test-word writers={len(ho_writers)}  "
          f"disjoint={bg_writers.isdisjoint(ho_writers)}", flush=True)

    # select N_TEST test words from held-out writers (seeded shuffle; report length spread).
    rng = np.random.default_rng(WORD_SELECT_SEED)
    order = rng.permutation(len(ho_words))
    sel = [ho_words[int(i)] for i in order[:N_TEST]]
    print(f"  selected test words: {len(sel)}  len-dist="
          f"{sorted(Counter(len(w['word']) for w in sel).items())}", flush=True)
    print(f"  sample: {[w['word'] for w in sel[:24]]}")

    # Strip to a serialisable form (strokes as lists).
    def _ser_word(w):
        return {"writer": w["writer"], "word": w["word"], "sample": w["sample"],
                "strokes": [np.asarray(s, float).tolist() for s in w["strokes"]],
                "char_segs": [{"class": c["class"], "symbol": c["symbol"],
                               "strokes": [np.asarray(s, float).tolist() for s in c["strokes"]]}
                              for c in w["char_segs"]]}

    out = {"lexicon": lex, "logfreq": logfreq,
           "brown_unigram": {w: int(brown_counts[w]) for w in lex if w in brown_counts},
           "test_words": [_ser_word(w) for w in sel],
           "bank_glyph_pool": [{"writer": g["writer"], "class": g["class"],
                                "strokes": [np.asarray(s, float).tolist() for s in g["strokes"]]}
                               for g in bank_glyphs],
           "bank_writers": sorted(bg_writers), "test_writers": sorted(ho_writers),
           "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]")
    return 0


def _require(name):
    p = _ckpt(name)
    if not os.path.exists(p):
        raise SystemExit(f"WALL: run the stage that produces {name} first.")
    return _load(p)


# ============================================================================================= #
#  STAGE: bank -- M cross-writer exemplars per class + learned median char arc-length.
# ============================================================================================= #
def stage_bank():
    print(f"\n{SEP}\n  STAGE: bank ({BANK_M}/class from BACKGROUND writers + char-arc unit)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("bank")
    import scripts.jabberwock_omniglot_run47_pendata as run47
    prep = _require("prep.json")
    pool = prep["bank_glyph_pool"]
    by_class = defaultdict(list)
    for g in pool:
        by_class[g["class"]].append(g)
    rng = np.random.default_rng(BANK_SEED)
    bank = {}
    for c in range(62):
        insts = by_class.get(c, [])
        if not insts:
            bank[c] = []
            continue
        idx = rng.choice(len(insts), size=min(BANK_M, len(insts)), replace=False)
        bank[c] = [insts[int(i)]["strokes"] for i in idx]
    n_ent = sum(len(v) for v in bank.values())
    empty = [c for c in range(62) if not bank[c]]
    print(f"  bank entries: {n_ent} (target {62*BANK_M})  empty classes: "
          f"{[SYMBOLS[c] for c in empty]}", flush=True)

    # median per-char arc length (for the joint knot density) -- learned on the bank pool.
    def _arc(strokes):
        tot = 0.0
        for s in strokes:
            a = np.asarray(s, float)
            if len(a) >= 2:
                tot += float(np.sqrt((np.diff(a, axis=0) ** 2).sum(1)).sum())
        return tot
    arcs = [_arc(g["strokes"]) for g in pool if _arc(g["strokes"]) > 0]
    char_arc_unit = float(np.median(arcs)) if arcs else 1.0

    # median per-char geometry SELF-cost on the bank (for the free-seg penalty LAMBDA).
    #   score each bank exemplar against the OTHER exemplars of its class; take the median min.
    self_costs = []
    for c in range(62):
        ex = bank[c]
        if len(ex) < 2:
            continue
        ps = [run47._stroke_point_sets_from_arrays(e) for e in ex]
        for i in range(len(ps)):
            best = INF
            for j in range(len(ps)):
                if i == j:
                    continue
                sc = run47.ps.program_score(ps[i], ps[j])
                best = min(best, sc)
            if best != INF:
                self_costs.append(best)
    median_char_cost = float(np.median(self_costs)) if self_costs else 1.0
    print(f"  char_arc_unit(median)={char_arc_unit:.4f}  median_char_cost={median_char_cost:.4f}  "
          f"[{time.time()-t0:.1f}s]")

    out = {"bank": {str(c): bank[c] for c in range(62)}, "char_arc_unit": char_arc_unit,
           "median_char_cost": median_char_cost, "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("bank.json"))
    _seed_guard("bank", md5_before)
    print(f"  saved -> {_ckpt('bank.json')}  [bank {time.time()-t0:.1f}s]")
    return 0


def _bank_pointsets(bank, run47):
    return {c: [run47._stroke_point_sets_from_arrays(e) for e in bank[str(c)]] for c in range(62)}


def _char_dist_vector(q_ps, bank_ps, run47):
    """62-class distance vector: dist_c = min over class c's bank exemplars of program_score."""
    out = []
    for c in range(62):
        best = INF
        for ps in bank_ps[c]:
            if not ps:
                continue
            sc = run47.ps.program_score(q_ps, ps)
            if sc < best:
                best = sc
        out.append(float(best if best != INF else 1e6))
    return out


# ============================================================================================= #
#  STAGE: recognize_path1 -- per GIVEN char segment, 62-class geometry distances.
# ============================================================================================= #
def stage_recognize_path1():
    print(f"\n{SEP}\n  STAGE: recognize_path1 (per given-char 62-class geometry distances)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("recognize_path1")
    import scripts.jabberwock_omniglot_run47_pendata as run47
    prep = _require("prep.json")
    bankd = _require("bank.json")
    bank_ps = _bank_pointsets(bankd["bank"], run47)

    out = []
    for wi, w in enumerate(prep["test_words"]):
        char_dists = []
        for cs in w["char_segs"]:
            q = run47._stroke_point_sets_from_arrays(cs["strokes"])
            char_dists.append(_char_dist_vector(q, bank_ps, run47))
        out.append({"word": w["word"], "writer": w["writer"],
                    "true_classes": [c["class"] for c in w["char_segs"]], "dists": char_dists})
        if (wi + 1) % 40 == 0:
            print(f"    ... {wi+1}/{len(prep['test_words'])}  [{time.time()-t0:.1f}s]", flush=True)
            _seed_guard("recognize_path1", md5_before)
    _save({"path1": out, "bank_md5": bankd["stroke_shapes_md5"]}, _ckpt("recog_path1.json"))
    _seed_guard("recognize_path1", md5_before)
    print(f"  recognized {len(out)} words  [{time.time()-t0:.1f}s]  saved -> "
          f"{_ckpt('recog_path1.json')}")
    return 0


# ------------------------------------------------------------------------------------------- #
#  Joint lattice geometry (pure, testable): build knots + span distance tensor.
# ------------------------------------------------------------------------------------------- #
def build_knots(strokes, char_arc_unit, density=KNOT_DENSITY, kmax=KMAX):
    """Arc-length knot boundaries over a word's connected ink. Returns (pts (T,2), sid (T,),
    boundaries [point-indices, sorted, incl 0 and T-1]). Knots = uniform arc-length grid (density
    per expected char) UNION pen-lift points. Segmentation-blind to the true char count."""
    pts = []
    sid = []
    for k, s in enumerate(strokes):
        a = np.asarray(s, float)
        for p in a:
            pts.append([float(p[0]), float(p[1])])
            sid.append(k)
    pts = np.asarray(pts, float)
    T = len(pts)
    if T < 2:
        return pts, np.asarray(sid), [0, max(0, T - 1)]
    d = np.sqrt((np.diff(pts, axis=0) ** 2).sum(1))
    cum = np.concatenate([[0.0], np.cumsum(d)])
    total = cum[-1] if cum[-1] > 0 else 1.0
    n_interior = int(round(density * total / max(char_arc_unit, 1e-6)))
    n_interior = max(1, min(kmax - 2, n_interior))
    grid = np.linspace(0.0, total, n_interior + 2)[1:-1]
    bset = {0, T - 1}
    for g in grid:
        bset.add(int(np.argmin(np.abs(cum - g))))
    # pen-lift points: last index of each stroke except the final one.
    sid_arr = np.asarray(sid)
    for k in range(len(strokes) - 1):
        idxs = np.flatnonzero(sid_arr == k)
        if len(idxs):
            bset.add(int(idxs[-1]))
    boundaries = sorted(b for b in bset if 0 <= b <= T - 1)
    if len(boundaries) > kmax:                      # keep first, last, and an even subsample.
        keep = np.linspace(0, len(boundaries) - 1, kmax).round().astype(int)
        boundaries = sorted({boundaries[i] for i in keep})
    return pts, sid_arr, boundaries


def _span_pointset(pts, sid, i0, i1, run47):
    """Point-set for the ink between point-indices i0..i1, regrouped into its original strokes."""
    sub = pts[i0:i1 + 1]
    ss = sid[i0:i1 + 1]
    strokes = []
    if len(sub) == 0:
        return []
    cur = [sub[0]]
    for k in range(1, len(sub)):
        if ss[k] != ss[k - 1]:
            strokes.append(np.asarray(cur, float))
            cur = []
        cur.append(sub[k])
    strokes.append(np.asarray(cur, float))
    return run47._stroke_point_sets_from_arrays(strokes)


def span_distance_tensor(strokes, char_arc_unit, bank_ps, run47):
    """For every feasible span (a<b, b-a<=WMAX in BOUNDARY-index units), the 62-class geometry
    distance vector. Returns (boundaries, spans={ (a,b): [62 dists] }). THE expensive geometry."""
    pts, sid, boundaries = build_knots(strokes, char_arc_unit)
    K = len(boundaries)
    spans = {}
    for a in range(K):
        for b in range(a + 1, min(K, a + WMAX + 1)):
            i0, i1 = boundaries[a], boundaries[b]
            if i1 - i0 < 2:
                continue
            q = _span_pointset(pts, sid, i0, i1, run47)
            if not q:
                continue
            spans[(a, b)] = _char_dist_vector(q, bank_ps, run47)
    return boundaries, spans, K


# ============================================================================================= #
#  STAGE: recognize_joint -- span-lattice geometry per word (resumable, checkpointed).
# ============================================================================================= #
def stage_recognize_joint():
    print(f"\n{SEP}\n  STAGE: recognize_joint (arc-length span-lattice 62-class geometry)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("recognize_joint")
    import scripts.jabberwock_omniglot_run47_pendata as run47
    prep = _require("prep.json")
    bankd = _require("bank.json")
    bank_ps = _bank_pointsets(bankd["bank"], run47)
    char_arc_unit = bankd["char_arc_unit"]

    lat_path = _ckpt("recog_joint.json")
    done = {}
    if os.path.exists(lat_path):
        prev = _load(lat_path)
        if prev.get("bank_md5") == bankd["stroke_shapes_md5"]:
            done = {d["idx"]: d for d in prev.get("joint", [])}
            print(f"  resuming: {len(done)} words already done", flush=True)

    joint = []
    n_new = 0
    words = prep["test_words"]
    for wi, w in enumerate(words):
        if wi in done:
            joint.append(done[wi])
            continue
        boundaries, spans, K = span_distance_tensor(w["strokes"], char_arc_unit, bank_ps, run47)
        # true char boundary alignment (for eval only) -- nearest boundary to each true char end.
        rec = {"idx": wi, "word": w["word"], "writer": w["writer"], "K": K,
               "spans": [[a, b, d] for (a, b), d in spans.items()]}
        joint.append(rec)
        n_new += 1
        if n_new % 12 == 0:
            print(f"    ... joint {wi+1}/{len(words)} ({n_new} new)  [{time.time()-t0:.1f}s]",
                  flush=True)
            _save({"bank_md5": bankd["stroke_shapes_md5"], "joint": joint, "partial": True},
                  lat_path)
            _seed_guard("recognize_joint", md5_before)
    _save({"bank_md5": bankd["stroke_shapes_md5"], "joint": joint, "partial": False}, lat_path)
    _seed_guard("recognize_joint", md5_before)
    print(f"  joint lattices: {len(joint)} ({n_new} new)  [{time.time()-t0:.1f}s]  saved -> "
          f"{lat_path}")
    return 0


# ------------------------------------------------------------------------------------------- #
#  Joint decoders (pure, testable).
# ------------------------------------------------------------------------------------------- #
def _spans_to_SD(spans, K):
    """(a,b,dists) list -> dict[(a,b)] = np.array(62). """
    SD = {}
    for a, b, d in spans:
        SD[(int(a), int(b))] = np.asarray(d, float)
    return SD


def _build_trie(lexicon):
    """Trie over lexicon words by canonical lowercase class. Returns (children, end_word).
    children[node] = {class: child_node}; end_word[node] = word or None."""
    children = [dict()]
    end_word = [None]

    def _new():
        children.append(dict())
        end_word.append(None)
        return len(children) - 1
    root = 0
    for w in lexicon:
        node = root
        for ch in w:
            c = r61._lower_class(ch)
            nxt = children[node].get(c)
            if nxt is None:
                nxt = _new()
                children[node][c] = nxt
            node = nxt
        end_word[node] = w
    return children, end_word, root


def joint_lexicon_decode(SD, K, trie, logfreq, alpha, wmax=WMAX):
    """THE MANIFOLD COLLAPSE: trie-constrained Viterbi over the (segmentation x glyph) lattice.
    Segmentation held OPEN -- the lexicon selects BOTH how many characters and which, jointly.
    Returns the best lexicon word (or "" if none reachable)."""
    children, end_word, root = trie
    # cost[t] = {node: (cost, backptr)} ; backptr = (prev_t, prev_node, class)
    cost = [dict() for _ in range(K)]
    cost[0][root] = (0.0, None)
    for t in range(K):
        layer = cost[t]
        if not layer:
            continue
        for node, (cst, _) in list(layer.items()):
            ch = children[node]
            if not ch:
                continue
            for tp in range(t + 1, min(K, t + wmax + 1)):
                sd = SD.get((t, tp))
                if sd is None:
                    continue
                for c, child in ch.items():
                    nc = cst + float(sd[c])
                    cur = cost[tp].get(child)
                    if cur is None or nc < cur[0]:
                        cost[tp][child] = (nc, (t, node, c))
    best_w, best_cost = "", INF
    floor = math.log(1.0 / (len(logfreq) + 1)) if logfreq else 0.0
    for node, (cst, _) in cost[K - 1].items():
        w = end_word[node]
        if w is None:
            continue
        total = cst - alpha * logfreq.get(w, floor)
        if total < best_cost:
            best_cost, best_w = total, w
    return best_w


def joint_free_decode(SD, K, symbols, lam, wmax=WMAX):
    """NO-CONTEXT contrast: COMMIT the best FREE segmentation (per-span argmin class + per-char
    penalty `lam`), THEN read off argmax per span. Segment-then-recognize -- the forbidden order."""
    dp = [INF] * K
    back = [None] * K
    dp[0] = 0.0
    for t in range(K):
        if dp[t] == INF:
            continue
        for tp in range(t + 1, min(K, t + wmax + 1)):
            sd = SD.get((t, tp))
            if sd is None:
                continue
            c = int(np.argmin(sd))
            nc = dp[t] + float(sd[c]) + lam
            if nc < dp[tp]:
                dp[tp] = nc
                back[tp] = (t, c)
    if dp[K - 1] == INF:
        return ""
    seq = []
    t = K - 1
    while t != 0 and back[t] is not None:
        pt, c = back[t]
        seq.append(symbols[c])
        t = pt
    seq.reverse()
    return "".join(seq)


def joint_oracle_count_decode(SD, K, symbols, m, wmax=WMAX):
    """NO-CONTEXT (conservative): ORACLE character count m; best m-span segmentation + per-span
    argmax. Isolates exactly the lexicon's contribution (both readers know m; only the collapse
    reader uses the lexicon constraint)."""
    dp = np.full((m + 1, K), INF)
    back = [[None] * K for _ in range(m + 1)]
    dp[0][0] = 0.0
    for j in range(1, m + 1):
        for t in range(1, K):
            best = INF
            bs = None
            lo = max(0, t - wmax)
            for s in range(lo, t):
                if dp[j - 1][s] == INF:
                    continue
                sd = SD.get((s, t))
                if sd is None:
                    continue
                c = int(np.argmin(sd))
                nc = dp[j - 1][s] + float(sd[c])
                if nc < best:
                    best, bs = nc, (s, c)
            dp[j][t] = best
            back[j][t] = bs
    if dp[m][K - 1] == INF:
        return ""
    seq = []
    t = K - 1
    j = m
    while j > 0 and back[j][t] is not None:
        s, c = back[j][t]
        seq.append(symbols[c])
        t, j = s, j - 1
    seq.reverse()
    return "".join(seq)


# ============================================================================================= #
#  STAGE: decode -- both paths, the accuracy table + resolution accounting.
# ============================================================================================= #
def _char_acc(pred, true):
    n = min(len(pred), len(true))
    return sum(1 for i in range(n) if pred[i] == true[i]), len(true)


def stage_decode():
    print(f"\n{SEP}\n  STAGE: decode (PATH 1 given-seg + PATH 2 joint manifold)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("decode")
    prep = _require("prep.json")
    bankd = _require("bank.json")
    p1 = _require("recog_path1.json")["path1"]
    pj = _require("recog_joint.json")["joint"]
    lexicon = prep["lexicon"]
    logfreq = prep["logfreq"]
    lex_by_len = r61._lex_by_len(lexicon)
    trie = _build_trie(lexicon)
    lam = FREE_SEG_LAMBDA_MULT * bankd["median_char_cost"]

    # ---- PATH 1: given char segmentation ------------------------------------------------- #
    nc1_ok = lx1_ok = 0
    nc1_char = lx1_char = nch = 0
    homo_errs = homo_res = 0
    nc1_flags, lx1_flags = [], []
    for L in p1:
        word = L["word"]
        dists = L["dists"]
        nc = r61.decode_no_context(dists, SYMBOLS)
        lx = r61.decode_lexicon(dists, len(word), lex_by_len, logfreq, FREQ_PRIOR_ALPHA)
        nc1_ok += (nc == word)
        lx1_ok += (lx == word)
        nc1_flags.append(nc == word)
        lx1_flags.append(lx == word)
        a, tot = _char_acc(nc, word)
        b, _ = _char_acc(lx, word)
        nc1_char += a
        lx1_char += b
        nch += tot
        for i, ch in enumerate(word):
            if i < len(nc) and nc[i] != ch and r61._is_homoglyph_pair(ch, nc[i]):
                homo_errs += 1
                if i < len(lx) and lx[i] == ch:
                    homo_res += 1

    # ---- PATH 2: joint manifold vs committed segmentation -------------------------------- #
    ncj_ok = ocj_ok = jc_ok = 0
    ncj_char = ocj_char = jc_char = jch = 0
    ncj_flags, jc_flags = [], []
    seg_amb_fixed = 0        # cases oracle-count no-ctx mis-segments (wrong len OR wrong) & joint right
    per_word_joint = []
    pj_sorted = sorted(pj, key=lambda d: d["idx"])
    word_by_idx = {i: w for i, w in enumerate(prep["test_words"])}
    for L in pj_sorted:
        word = word_by_idx[L["idx"]]["word"]
        K = L["K"]
        SD = _spans_to_SD(L["spans"], K)
        free = joint_free_decode(SD, K, SYMBOLS, lam)
        oracle = joint_oracle_count_decode(SD, K, SYMBOLS, len(word))
        collapse = joint_lexicon_decode(SD, K, trie, logfreq, FREQ_PRIOR_ALPHA)
        ncj_ok += (free == word)
        ocj_ok += (oracle == word)
        jc_ok += (collapse == word)
        ncj_flags.append(free == word)
        jc_flags.append(collapse == word)
        a, tot = _char_acc(free, word)
        b, _ = _char_acc(oracle, word)
        c, _ = _char_acc(collapse, word)
        ncj_char += a
        ocj_char += b
        jc_char += c
        jch += tot
        if oracle != word and collapse == word:
            seg_amb_fixed += 1
        per_word_joint.append({"word": word, "free": free, "oracle": oracle, "collapse": collapse})

    n1 = len(p1)
    nj = len(pj_sorted)

    def acc(k, tot):
        return k / tot if tot else 0.0

    rep = {
        "n_path1": n1, "n_joint": nj, "n_chars_p1": nch, "n_chars_joint": jch,
        "lambda_free": lam,
        "path1": {
            "no_context": {"word_acc": acc(nc1_ok, n1), "ci": list(r61._wilson_ci(nc1_ok, n1)),
                           "char_acc": acc(nc1_char, nch), "n_correct": nc1_ok},
            "lexicon_collapse": {"word_acc": acc(lx1_ok, n1), "ci": list(r61._wilson_ci(lx1_ok, n1)),
                                 "char_acc": acc(lx1_char, nch), "n_correct": lx1_ok},
            "homoglyph": {"nc_homoglyph_char_errors": homo_errs, "resolved_by_lexicon": homo_res,
                          "frac_resolved": (homo_res / homo_errs) if homo_errs else 0.0},
            "mcnemar": r61._mcnemar(nc1_flags, lx1_flags),
        },
        "joint": {
            "no_context_free": {"word_acc": acc(ncj_ok, nj), "ci": list(r61._wilson_ci(ncj_ok, nj)),
                                "char_acc": acc(ncj_char, jch), "n_correct": ncj_ok},
            "no_context_oracle_count": {"word_acc": acc(ocj_ok, nj),
                                        "ci": list(r61._wilson_ci(ocj_ok, nj)),
                                        "char_acc": acc(ocj_char, jch), "n_correct": ocj_ok},
            "manifold_collapse": {"word_acc": acc(jc_ok, nj), "ci": list(r61._wilson_ci(jc_ok, nj)),
                                  "char_acc": acc(jc_char, jch), "n_correct": jc_ok},
            "seg_ambiguity_fixed_vs_oracle": seg_amb_fixed,
            "mcnemar_collapse_vs_free": r61._mcnemar(ncj_flags, jc_flags),
        },
    }
    # WIN verdict (pre-registered).
    p1nc = rep["path1"]["no_context"]["word_acc"]
    p1lx = rep["path1"]["lexicon_collapse"]["word_acc"]
    jnc = rep["joint"]["no_context_free"]["word_acc"]
    joc = rep["joint"]["no_context_oracle_count"]["word_acc"]
    jc = rep["joint"]["manifold_collapse"]["word_acc"]
    r1 = (p1lx / p1nc) if p1nc > 0 else INF
    rj = (jc / jnc) if jnc > 0 else INF
    frac = rep["path1"]["homoglyph"]["frac_resolved"]
    path1_win = (r1 >= WIN_WORD_ACC_RATIO and frac >= WIN_HOMOGLYPH_RESOLVED)
    joint_win = (rj >= WIN_WORD_ACC_RATIO) and (jc > joc)      # beats the free AND the oracle-count.
    if path1_win and joint_win:
        verdict = "WIN"
    elif path1_win and not joint_win:
        verdict = "PARTIAL-SEG-BOTTLENECK"
    elif not path1_win:
        verdict = "NULL"
    else:
        verdict = "MIXED"
    rep["verdict"] = {"path1_ratio": r1, "path1_homoglyph": frac, "path1_win": path1_win,
                      "joint_ratio": rj, "joint_beats_oracle": bool(jc > joc), "joint_win": joint_win,
                      "overall": verdict}
    _save({"report": rep, "per_word_joint": per_word_joint}, _ckpt("decode.json"))
    _seed_guard("decode", md5_before)
    _print_report(rep)
    print(f"  saved -> {_ckpt('decode.json')}  [decode {time.time()-t0:.1f}s]")
    return 0


def _print_report(rep):
    p1, jt = rep["path1"], rep["joint"]
    print(f"\n  === REAL-INK WORD READING (path1 n={rep['n_path1']}, joint n={rep['n_joint']}) ===")
    hdr = f"  {'reader':<40}{'word_acc':>11}{'word_CI':>16}{'char_acc':>11}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    def row(lab, r):
        ci = f"[{100*r['ci'][0]:.1f},{100*r['ci'][1]:.1f}]"
        print(f"  {lab:<40}{100*r['word_acc']:>9.1f}%{ci:>16}{100*r['char_acc']:>9.1f}%")
    print("  PATH 1 -- char boundaries GIVEN (run 61 on REAL connected glyphs):")
    row("(a) no-context (per-char argmin)", p1["no_context"])
    row("(b) LEXICON-COLLAPSE", p1["lexicon_collapse"])
    print("  PATH 2 -- segmentation HELD OPEN (the joint manifold):")
    row("(c) no-context free-seg (commit+argmax)", jt["no_context_free"])
    row("(c') no-context oracle-count seg+argmax", jt["no_context_oracle_count"])
    row("(d) JOINT MANIFOLD-COLLAPSE", jt["manifold_collapse"])
    h = p1["homoglyph"]
    print(f"\n  PATH1 HOMOGLYPH: of {h['nc_homoglyph_char_errors']} no-context homoglyph char-errors, "
          f"lexicon resolves {h['resolved_by_lexicon']} ({100*h['frac_resolved']:.1f}%)")
    print(f"  PATH1 McNemar (lexicon vs no-context): fixed={p1['mcnemar']['fixed']} "
          f"broken={p1['mcnemar']['broken']} p={p1['mcnemar']['p']:.3g}")
    print(f"  JOINT seg-ambiguity fixed vs oracle-count no-ctx: "
          f"{jt['seg_ambiguity_fixed_vs_oracle']}")
    print(f"  JOINT McNemar (collapse vs free): fixed={jt['mcnemar_collapse_vs_free']['fixed']} "
          f"broken={jt['mcnemar_collapse_vs_free']['broken']} "
          f"p={jt['mcnemar_collapse_vs_free']['p']:.3g}")
    v = rep["verdict"]
    print(f"\n  VERDICT: path1 ratio={v['path1_ratio']:.2f}x (homoglyph {100*v['path1_homoglyph']:.0f}%) "
          f"win={v['path1_win']};  joint ratio={v['joint_ratio']:.2f}x "
          f"beats-oracle={v['joint_beats_oracle']} win={v['joint_win']}")
    print(f"  -> OVERALL: {v['overall']}")


# ============================================================================================= #
#  STAGE: summary
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 62 SCOREBOARD (REAL-INK WORD READING)\n{SEP}")
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    dec = _require("decode.json")
    print(f"\n  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: {md5_now == prep['stroke_shapes_md5']})")
    _print_report(dec["report"])
    print(f"\n  ILLUSTRATIVE JOINT RESCUES (free/oracle -> collapse):")
    shown = 0
    for pw in dec["per_word_joint"]:
        if pw["collapse"] == pw["word"] and (pw["oracle"] != pw["word"] or pw["free"] != pw["word"]):
            print(f"    {pw['word']:<10}  free='{pw['free']}'  oracle='{pw['oracle']}'  "
                  f"-> collapse='{pw['collapse']}'")
            shown += 1
            if shown >= 14:
                break
    print(f"\n{SEP}\n  RUN 62 COMPLETE -- see final agent report.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                   choices=["prep", "bank", "recognize_path1", "recognize_joint", "decode",
                            "summary"])
    args = p.parse_args()
    fn = {"prep": stage_prep, "bank": stage_bank, "recognize_path1": stage_recognize_path1,
          "recognize_joint": stage_recognize_joint, "decode": stage_decode,
          "summary": stage_summary}[args.stage]
    return fn()


if __name__ == "__main__":
    sys.exit(main())
