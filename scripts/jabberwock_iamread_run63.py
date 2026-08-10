"""jabberwock_iamread_run63.py -- RUN 63: READING IAM-OnDB (the authoritative online-handwriting
benchmark).

THE ADVANCE OVER RUN 62: run 61 proved language-context word reading on SYNTHETIC pre-segmented
words; run 62 added the joint segmentation manifold on REAL connected ink but from the DeepWriting
release. Run 63 moves to IAM-OnDB itself -- the authoritative online-HWR benchmark -- and reads
REAL whiteboard word ink with the SAME training-free manifold-collapse reader: SC+TPS geometry
(the earned-quanta proposal layer) + a LEXICON language prior (the continuous-decides verdict).
The question: how far does training-free manifold-collapse get on REAL IAM handwriting, and does
run 61's reading-with-context WIN hold on the authoritative benchmark?

HONEST FRAME: donkey=0 -- NO trained neural net (commercial/SOTA IAM-OnDB systems are deep
BLSTM/CTC nets at ~5-10% WER; we do NOT compete with those). The geometry recognizer is one-shot
exemplar matching against a cross-CORPUS DeepWriting bank; the lexicon is read-only count data
(Brown + WordNet + IAM CSR counts). We report the numbers and position them honestly against
published IAM-OnDB WER/CER.

WHAT COMES FROM WHERE:
  * TEST ink  : IAM-OnDB lineStrokes (real whiteboard lines), segmented into WORDS. domains/iam_world.
  * BANK      : DeepWriting char glyphs (a different IAM-OnDB-derived release) -> the 62-class
                geometry codebook. Cross-corpus => bank<->test writer-independence is structural.
  * LEXICON   : Brown + WordNet (len 3-8) UNION IAM CSR vocabulary; freq prior = Brown unigram +
                IAM CSR counts. Corpus-general, donkey=0.

SEGMENTATION: the READING axis is isolated the run-62 way. Word segmentation uses ORACLE word
COUNT (split each punctuation-free line at its largest inter-stroke gaps) so the geometry reader is
tested on real, correctly-bounded word ink; adaptive-threshold word-count recovery is reported
SEPARATELY as a segmentation diagnostic. WITHIN a word, char segmentation is HELD OPEN and
collapsed jointly by the lexicon (the manifold-collapse key) -- NO commit-then-decode.

STAGES (dependency order): prep -> bank -> recognize -> decode -> line_poc -> summary
Run (from repo root):
  PYTHONPATH=.:runners/dsl/python IAM_STROKES_DIR=... IAM_ASCII_DIR=... DEEPWRITING_DIR=... \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_iamread_run63.py --stage <S>
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
os.environ.setdefault("IAM_STROKES_DIR", "/tmp/handwriting/iam_onbd/lineStrokes")
os.environ.setdefault("IAM_ASCII_DIR", "/tmp/handwriting/iam_ascii/ascii")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import scripts.jabberwock_wordread_run61 as r61
import scripts.jabberwock_realwordread_run62 as r62
from domains import iam_world as iw

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run63_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
SYMBOLS = iw.CANON_SYMBOLS

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
WORD_MIN_LEN, WORD_MAX_LEN = 3, 8
N_TEST = 260                       # target test words (>= 200 pre-reg); real-ink yield permitting.
TEST_SPLIT_SEED = 20260706         # held-out-FORM split.
TEST_FRAC = 0.5
WORD_SELECT_SEED = 20260714
MAX_TEST_FORMS = 900               # cap forms scanned for test-word yield (keeps prep fast).

BANK_M = 3
BANK_SEED = 20260711
DW_SPLIT = "training"

GAP_FRAC_SWEEP = [0.25, 0.35, 0.45, 0.55, 0.7, 0.9]   # adaptive word-seg diagnostic sweep.

FREQ_PRIOR_ALPHA = 0.0             # PRIMARY lexicon arm: flat (uniform over valid words).
FREQ_PRIOR_ALPHA_WEIGHTED = 1.0    # secondary arm: + (Brown+IAM) unigram log-frequency prior.
TOPK = 5                           # per-word lexicon candidates carried for the line-level LM.
BIGRAM_BETA = 1.0                  # word-bigram weight in the line POC.

# WIN thresholds (pre-registered): reading-with-context holds on REAL IAM.
WIN_WORD_ACC_RATIO = 2.0           # collapse word acc >= 2x no-context word acc.
WIN_CER_DROP = 0.30                # collapse CER <= 0.70 * no-context CER (>=30% relative drop).

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


def _require(name):
    p = _ckpt(name)
    if not os.path.exists(p):
        raise SystemExit(f"WALL: run the stage that produces {name} first.")
    return _load(p)


def _levenshtein(a, b):
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[lb]


# ------------------------------------------------------------------------------------------- #
#  Lexicon (donkey=0: Brown + WordNet + IAM CSR counts).
# ------------------------------------------------------------------------------------------- #
def _build_lexicon(iam_word_counts):
    from nltk.corpus import brown, wordnet as wn
    brown_counts = Counter(w.lower() for w in brown.words() if w.isalpha())
    wn_lemmas = {l for l in wn.all_lemma_names() if l.isalpha() and l.islower()}
    iam_vocab = {w for w in iam_word_counts if w.isalpha() and w.islower()}
    lex = {w for w in (set(brown_counts) | wn_lemmas | iam_vocab)
           if w.isalpha() and w.islower() and WORD_MIN_LEN <= len(w) <= WORD_MAX_LEN}
    # blended unigram: Brown + IAM CSR counts.
    blended = Counter(brown_counts)
    for w, c in iam_word_counts.items():
        blended[w] += c
    total = sum(blended.values())
    logfreq = {w: math.log((blended.get(w, 0) + 1) / (total + len(lex))) for w in lex}
    return sorted(lex), logfreq, blended


# ============================================================================================= #
#  STAGE: prep -- load IAM, held-out split, select test words (oracle-count seg), seg diagnostic.
# ============================================================================================= #
def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (IAM load + held-out-form split + oracle-count word selection)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}")

    lines = iw.load_lines(max_forms=MAX_TEST_FORMS)
    print(f"  IAM lines loaded (<= {MAX_TEST_FORMS} forms): {len(lines)}  "
          f"forms={len({l['form'] for l in lines})}  writers(prefix)={len({l['writer'] for l in lines})}"
          f"  [{time.time()-t0:.1f}s]", flush=True)

    # IAM CSR word counts (all loaded lines) -> in-domain vocab + freq prior.
    iam_counts = Counter(w.lower() for l in lines for w in l["words"])
    lex, logfreq, blended = _build_lexicon(iam_counts)
    lexset = set(lex)
    print(f"  lexicon (Brown+WordNet+IAM CSR, len {WORD_MIN_LEN}-{WORD_MAX_LEN}) = {len(lex)}  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    # held-out-FORM split (writer proxy = form prefix); test words come from the HELD-OUT side.
    bg, test_lines = iw.writer_form_split(lines, n_test_frac=TEST_FRAC, seed=TEST_SPLIT_SEED)
    bg_w = {l["writer"] for l in bg}
    te_w = {l["writer"] for l in test_lines}
    print(f"  split: bg forms-prefix={len(bg_w)} test={len(te_w)} disjoint={bg_w.isdisjoint(te_w)}"
          f"  test lines={len(test_lines)}", flush=True)

    # PUNCTUATION-FREE lines only -> ink-unit count == word-token count (clean oracle alignment).
    def _punct_free(l):
        return len(l["words"]) >= 2 and all(t.isalpha() for t in l["text"].split())
    pf_lines = [l for l in test_lines if _punct_free(l)]
    print(f"  punctuation-free test lines: {len(pf_lines)}", flush=True)

    # segmentation diagnostic: adaptive word-count recovery over gap_frac sweep (on pf lines).
    seg_diag = []
    for gf in GAP_FRAC_SWEEP:
        errs = []
        for l in pf_lines:
            nw = len(l["words"])
            errs.append(len(iw.segment_words(l["strokes"], gap_frac=gf)) - nw)
        exact = sum(1 for d in errs if d == 0) / max(1, len(errs))
        within1 = sum(1 for d in errs if abs(d) <= 1) / max(1, len(errs))
        seg_diag.append({"gap_frac": gf, "exact_count": exact, "within1": within1,
                         "mean_err": float(np.mean(errs))})
    best = max(seg_diag, key=lambda d: d["exact_count"])
    print(f"  adaptive word-count recovery sweep (pf lines, n={len(pf_lines)}):")
    for d in seg_diag:
        print(f"    gap_frac={d['gap_frac']:.2f}  exact={100*d['exact_count']:.1f}%  "
              f"within1={100*d['within1']:.1f}%  mean_err={d['mean_err']:+.2f}")
    print(f"  -> best adaptive: gap_frac={best['gap_frac']} exact={100*best['exact_count']:.1f}%",
          flush=True)

    # SELECT test words: oracle-count segment each pf line; align group[i] <-> words[i]; keep
    # positions that are lowercase alpha, len 3-8, in lexicon. Carry line_id + position.
    rng = np.random.default_rng(WORD_SELECT_SEED)
    order = rng.permutation(len(pf_lines))
    test_words = []
    for oi in order:
        l = pf_lines[int(oi)]
        groups = iw.segment_words(l["strokes"], n_words=len(l["words"]))
        if len(groups) != len(l["words"]):
            continue
        for pos, (grp, tok) in enumerate(zip(groups, l["words"])):
            w = tok.lower()
            if not (w.isalpha() and w.islower() and WORD_MIN_LEN <= len(w) <= WORD_MAX_LEN):
                continue
            if w not in lexset:
                continue
            ink = [np.asarray(s, float)[:, :2].tolist() for s in grp]
            npts = sum(len(s) for s in ink)
            if npts < 6:
                continue
            test_words.append({"word": w, "line_id": l["line_id"], "writer": l["writer"],
                               "pos": pos, "strokes": ink})
        if len(test_words) >= N_TEST:
            break
    test_words = test_words[:N_TEST]
    print(f"  selected test words: {len(test_words)}  "
          f"len-dist={sorted(Counter(len(w['word']) for w in test_words).items())}", flush=True)
    print(f"  from {len({w['line_id'] for w in test_words})} lines / "
          f"{len({w['writer'] for w in test_words})} form-prefixes", flush=True)
    print(f"  sample: {[w['word'] for w in test_words[:26]]}")

    out = {"lexicon": lex, "logfreq": logfreq,
           "iam_unigram": {w: int(blended[w]) for w in lex if blended.get(w, 0) > 0},
           "test_words": test_words, "seg_diag": seg_diag, "best_gap_frac": best["gap_frac"],
           "n_pf_lines": len(pf_lines), "n_test_lines_total": len(test_lines),
           "bg_writers": sorted(bg_w), "test_writers": sorted(te_w),
           "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]")
    return 0


# ============================================================================================= #
#  STAGE: bank -- M cross-writer DeepWriting exemplars per class + char-arc unit + median cost.
# ============================================================================================= #
def stage_bank():
    print(f"\n{SEP}\n  STAGE: bank (DeepWriting {BANK_M}/class + char-arc unit)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("bank")
    import scripts.jabberwock_omniglot_run47_pendata as run47
    from domains import deepwriting_world as dww
    dw = dww.load_deepwriting(DW_SPLIT)
    glyphs = dww.extract_char_glyphs(dw)
    print(f"  DeepWriting '{DW_SPLIT}' char glyphs: {len(glyphs)}  [{time.time()-t0:.1f}s]",
          flush=True)
    by_class = defaultdict(list)
    for g in glyphs:
        by_class[g["class"]].append(g)
    rng = np.random.default_rng(BANK_SEED)
    bank = {}
    for c in range(62):
        insts = by_class.get(c, [])
        if not insts:
            bank[c] = []
            continue
        idx = rng.choice(len(insts), size=min(BANK_M, len(insts)), replace=False)
        bank[c] = [[np.asarray(s, float).tolist() for s in insts[int(i)]["strokes"]] for i in idx]
    n_ent = sum(len(v) for v in bank.values())
    empty = [SYMBOLS[c] for c in range(62) if not bank[c]]
    print(f"  bank entries: {n_ent} (target {62*BANK_M})  empty classes: {empty}", flush=True)

    def _arc(strokes):
        tot = 0.0
        for s in strokes:
            a = np.asarray(s, float)
            if len(a) >= 2:
                tot += float(np.sqrt((np.diff(a, axis=0) ** 2).sum(1)).sum())
        return tot
    arcs = [_arc(g["strokes"]) for g in glyphs if _arc(g["strokes"]) > 0]
    char_arc_unit = float(np.median(arcs)) if arcs else 1.0

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


# ============================================================================================= #
#  STAGE: recognize -- span-lattice geometry per test word (resumable, checkpointed).
# ============================================================================================= #
def stage_recognize():
    print(f"\n{SEP}\n  STAGE: recognize (arc-length span-lattice 62-class geometry on IAM words)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("recognize")
    import scripts.jabberwock_omniglot_run47_pendata as run47
    prep = _require("prep.json")
    bankd = _require("bank.json")
    bank_ps = r62._bank_pointsets(bankd["bank"], run47)
    char_arc_unit = bankd["char_arc_unit"]

    lat_path = _ckpt("recog.json")
    done = {}
    if os.path.exists(lat_path):
        prev = _load(lat_path)
        if prev.get("bank_md5") == bankd["stroke_shapes_md5"]:
            done = {d["idx"]: d for d in prev.get("recog", [])}
            print(f"  resuming: {len(done)} words already done", flush=True)

    recog = []
    n_new = 0
    words = prep["test_words"]
    for wi, w in enumerate(words):
        if wi in done:
            recog.append(done[wi])
            continue
        strokes = [np.asarray(s, float) for s in w["strokes"]]
        boundaries, spans, K = r62.span_distance_tensor(strokes, char_arc_unit, bank_ps, run47)
        recog.append({"idx": wi, "word": w["word"], "line_id": w["line_id"], "pos": w["pos"],
                      "writer": w["writer"], "K": K,
                      "spans": [[a, b, d] for (a, b), d in spans.items()]})
        n_new += 1
        if n_new % 5 == 0:
            print(f"    ... {wi+1}/{len(words)} ({n_new} new)  [{time.time()-t0:.1f}s]", flush=True)
            _save({"bank_md5": bankd["stroke_shapes_md5"], "recog": recog, "partial": True}, lat_path)
            _seed_guard("recognize", md5_before)
            if time.time() - t0 > 450:      # clean wall-budget: exit between checkpoints, resume.
                remaining = len(words) - len(recog)
                print(f"  WALL-BUDGET: checkpointed {len(recog)} done, {remaining} remain "
                      f"-- re-invoke --stage recognize to resume.", flush=True)
                _seed_guard("recognize", md5_before)
                return 2
    _save({"bank_md5": bankd["stroke_shapes_md5"], "recog": recog, "partial": False}, lat_path)
    _seed_guard("recognize", md5_before)
    print(f"  span-lattices: {len(recog)} ({n_new} new)  [{time.time()-t0:.1f}s]  saved -> {lat_path}")
    return 0


# ============================================================================================= #
#  RAW-POINT WHOLE-FIGURE recognizer (the connected-cursive-capable verdict -- run 16's 73.5%
#  SC+TPS+SmoothDeform on RAW POINTS, NOT run 47's per-stroke program_score which run 62 proved
#  floors at ~15-20% char on cursive even with true segmentation). Whole span/glyph resampled to
#  ONE point cloud; scored by SmoothDeformDist + SC_W*ShapeContextDist (recognition_graph's own
#  fusion), evaluated directly on point-set literals -- no graph staging.
# ============================================================================================= #
RAW_N = 48                 # whole-figure resample length.
RAW_SC_W = 1.6             # shapecontext weight (recognition_graph.predict_smooth_render_sc_term).
_S_NATIVE = None


def _native():
    global _S_NATIVE
    if _S_NATIVE is None:
        import substrate_rs as srs
        _S_NATIVE = srs._NativeSubstrate()
    return _S_NATIVE


def whole_fig_points(strokes, N=RAW_N):
    """Concatenate a figure's strokes into ONE arc-length-resampled point cloud, whole-figure
    normalized (translation+scale). Returns list[[x,y]] or None if degenerate."""
    arrs = [np.asarray(s, float)[:, :2] for s in strokes if len(s)]
    arrs = [a for a in arrs if len(a) >= 1]
    if not arrs:
        return None
    allp = np.concatenate(arrs, 0)
    if len(allp) < 3:
        return None
    mn = allp.mean(0)
    scale = np.abs(allp - mn).max() + 1e-9
    pts = np.concatenate([(a - mn) / scale for a in arrs], 0)
    d = np.sqrt((np.diff(pts, axis=0) ** 2).sum(1))
    cum = np.concatenate([[0.0], np.cumsum(d)])
    if cum[-1] == 0:
        return None
    u = np.linspace(0.0, cum[-1], N)
    return np.stack([np.interp(u, cum, pts[:, 0]), np.interp(u, cum, pts[:, 1])], 1).tolist()


def _raw_score(q, e):
    S = _native()
    L = lambda v: {"type": "Lit", "value": v}
    sd = float(S.evaluate({"type": "SmoothDeformDist", "a": L(q), "b": L(e)}, {}))
    sc = float(S.evaluate({"type": "ShapeContextDist", "a": L(q), "b": L(e)}, {}))
    return sd + RAW_SC_W * sc


def _raw_char_dist_vector(q_wf, bank_wf):
    out = []
    for c in range(62):
        best = INF
        for e in bank_wf[c]:
            if e is None:
                continue
            s = _raw_score(q_wf, e)
            if s < best:
                best = s
        out.append(float(best if best != INF else 1e6))
    return out


def _span_whole_fig(pts, sid, i0, i1):
    """Whole-figure point cloud for the ink between point-indices i0..i1 (regroup its strokes)."""
    sub = pts[i0:i1 + 1]
    ss = sid[i0:i1 + 1]
    if len(sub) < 3:
        return None
    strokes = []
    cur = [sub[0]]
    for k in range(1, len(sub)):
        if ss[k] != ss[k - 1]:
            strokes.append(np.asarray(cur, float))
            cur = []
        cur.append(sub[k])
    strokes.append(np.asarray(cur, float))
    return whole_fig_points(strokes)


RAW_KMAX = 18              # knot cap for the raw arm (IAM words are long; 18 knots ~ enough
                           # boundary resolution for <=8 chars while cutting the O(K*WMAX) span count).


def raw_span_distance_tensor(strokes, char_arc_unit, bank_wf):
    """Same arc-length knot lattice as run 62 (build_knots), but each span scored WHOLE-FIGURE by
    the raw-point recognizer. Returns (boundaries, spans={(a,b):[62 dists]}, K)."""
    pts, sid, boundaries = r62.build_knots(strokes, char_arc_unit, kmax=RAW_KMAX)
    K = len(boundaries)
    spans = {}
    for a in range(K):
        for b in range(a + 1, min(K, a + r62.WMAX + 1)):
            i0, i1 = boundaries[a], boundaries[b]
            if i1 - i0 < 2:
                continue
            q = _span_whole_fig(pts, sid, i0, i1)
            if q is None:
                continue
            spans[(a, b)] = _raw_char_dist_vector(q, bank_wf)
    return boundaries, spans, K


def stage_recognize_raw():
    print(f"\n{SEP}\n  STAGE: recognize_raw (WHOLE-FIGURE raw-point SC+TPS+SmoothDeform -- the "
          f"cursive-capable verdict)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("recognize_raw")
    prep = _require("prep.json")
    bankd = _require("bank.json")
    char_arc_unit = bankd["char_arc_unit"]
    # bank whole-figure exemplars.
    bank_wf = {}
    for c in range(62):
        bank_wf[c] = [whole_fig_points([np.asarray(s, float) for s in e])
                      for e in bankd["bank"][str(c)]]
    lat_path = _ckpt("recog_raw.json")
    done = {}
    if os.path.exists(lat_path):
        prev = _load(lat_path)
        if prev.get("bank_md5") == bankd["stroke_shapes_md5"]:
            done = {d["idx"]: d for d in prev.get("recog", [])}
            print(f"  resuming: {len(done)} words already done", flush=True)
    recog = []
    n_new = 0
    words = prep["test_words"]
    for wi, w in enumerate(words):
        if wi in done:
            recog.append(done[wi])
            continue
        strokes = [np.asarray(s, float) for s in w["strokes"]]
        boundaries, spans, K = raw_span_distance_tensor(strokes, char_arc_unit, bank_wf)
        recog.append({"idx": wi, "word": w["word"], "line_id": w["line_id"], "pos": w["pos"],
                      "writer": w["writer"], "K": K,
                      "spans": [[a, b, d] for (a, b), d in spans.items()]})
        n_new += 1
        if n_new % 5 == 0:
            print(f"    ... {wi+1}/{len(words)} ({n_new} new)  [{time.time()-t0:.1f}s]", flush=True)
            _save({"bank_md5": bankd["stroke_shapes_md5"], "recog": recog, "partial": True}, lat_path)
            _seed_guard("recognize_raw", md5_before)
            if time.time() - t0 > 450:
                remaining = len(words) - len(recog)
                print(f"  WALL-BUDGET: checkpointed {len(recog)} done, {remaining} remain "
                      f"-- re-invoke --stage recognize_raw to resume.", flush=True)
                _seed_guard("recognize_raw", md5_before)
                return 2
    _save({"bank_md5": bankd["stroke_shapes_md5"], "recog": recog, "partial": False}, lat_path)
    _seed_guard("recognize_raw", md5_before)
    print(f"  raw span-lattices: {len(recog)} ({n_new} new)  [{time.time()-t0:.1f}s]  saved -> "
          f"{lat_path}")
    return 0


# ------------------------------------------------------------------------------------------- #
#  top-K joint lexicon decode (for the line-level LM) -- pure.
# ------------------------------------------------------------------------------------------- #
def joint_lexicon_all(SD, K, trie, wmax=r62.WMAX):
    """ONE trie-constrained Viterbi over the (segmentation x glyph) lattice. Returns dict
    {word: min summed span cost} over ALL reachable lexicon words -- collapse (alpha=0),
    frequency-weighted collapse, and top-K are all derived from this single pass."""
    children, end_word, root = trie
    cost = [dict() for _ in range(K)]
    cost[0][root] = 0.0
    for t in range(K):
        layer = cost[t]
        if not layer:
            continue
        for node, cst in list(layer.items()):
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
                    if cur is None or nc < cur:
                        cost[tp][child] = nc
    words = {}
    for node, cst in cost[K - 1].items():
        w = end_word[node]
        if w is not None and (w not in words or cst < words[w]):
            words[w] = cst
    return words


def _collapse_from_all(words, logfreq, alpha):
    if not words:
        return ""
    floor = math.log(1.0 / (len(logfreq) + 1)) if logfreq else 0.0
    return min(words.items(), key=lambda kv: kv[1] - alpha * logfreq.get(kv[0], floor))[0]


# ============================================================================================= #
#  STAGE: decode -- no-context vs lexicon-collapse; word acc + CER; carry top-K for line POC.
# ============================================================================================= #
def _decode_recog(rec, trie, logfreq, lam, cache_path=None, t0=None, budget=430):
    """Decode every word (free / oracle / collapse / collapse_freq + top-K). Resumable: per-word
    results cached to `cache_path`; a wall budget returns (None, partial, False) to be resumed."""
    per_word = []
    done = {}
    if cache_path and os.path.exists(cache_path):
        prev = _load(cache_path)
        done = {d["idx"]: d for d in prev.get("per_word", [])}
    for wi, L in enumerate(rec):
        if L["idx"] in done:
            per_word.append(done[L["idx"]])
            continue
        word = L["word"]
        K = L["K"]
        SD = r62._spans_to_SD(L["spans"], K)
        free = r62.joint_free_decode(SD, K, SYMBOLS, lam)
        oracle = r62.joint_oracle_count_decode(SD, K, SYMBOLS, len(word))
        allw = joint_lexicon_all(SD, K, trie)                 # ONE trie Viterbi pass.
        collapse = _collapse_from_all(allw, logfreq, FREQ_PRIOR_ALPHA)
        collapse_f = _collapse_from_all(allw, logfreq, FREQ_PRIOR_ALPHA_WEIGHTED)
        topk = [(c, w) for w, c in sorted(allw.items(), key=lambda kv: kv[1])[:TOPK]]
        per_word.append({"idx": L["idx"], "word": word, "line_id": L["line_id"], "pos": L["pos"],
                         "free": free, "oracle": oracle, "collapse": collapse,
                         "collapse_freq": collapse_f, "topk": [[c, w] for c, w in topk]})
        if cache_path and len(per_word) % 10 == 0:
            _save({"per_word": per_word, "partial": True}, cache_path)
            if t0 is not None and time.time() - t0 > budget:
                print(f"    decode WALL-BUDGET: {len(per_word)}/{len(rec)} done -- resume.",
                      flush=True)
                return None, per_word, False

    if cache_path:
        _save({"per_word": per_word, "partial": False}, cache_path)

    acc = {"free": 0, "oracle": 0, "collapse": 0, "collapse_freq": 0}
    ed = {"free": 0, "oracle": 0, "collapse": 0, "collapse_freq": 0}
    cer_word = {"free": [], "oracle": [], "collapse": [], "collapse_freq": []}
    n_ref_chars = 0
    flags = {"free": [], "oracle": [], "collapse": []}
    for pw in per_word:
        word = pw["word"]
        preds = {k: pw[k] for k in ("free", "oracle", "collapse", "collapse_freq")}
        for k, p in preds.items():
            acc[k] += (p == word)
            e = _levenshtein(p, word)
            ed[k] += e
            cer_word[k].append(e / max(1, len(word)))
        n_ref_chars += len(word)
        flags["free"].append(pw["free"] == word)
        flags["oracle"].append(pw["oracle"] == word)
        flags["collapse"].append(pw["collapse"] == word)

    n = len(per_word)

    def _blk(k):
        wok = acc[k]
        return {"word_acc": wok / n if n else 0.0, "word_ci": list(r61._wilson_ci(wok, n)),
                "n_correct": wok, "cer_micro": ed[k] / max(1, n_ref_chars),
                "cer_macro": float(np.mean(cer_word[k])) if cer_word[k] else 0.0}
    rep = {"n_words": n, "n_ref_chars": n_ref_chars, "lambda_free": lam,
           "no_context_free": _blk("free"), "no_context_oracle_count": _blk("oracle"),
           "manifold_collapse": _blk("collapse"), "manifold_collapse_freq": _blk("collapse_freq"),
           "mcnemar_collapse_vs_free": r61._mcnemar(flags["free"], flags["collapse"]),
           "mcnemar_collapse_vs_oracle": r61._mcnemar(flags["oracle"], flags["collapse"])}
    # WIN verdict.
    ncf = rep["no_context_free"]["word_acc"]
    nco = rep["no_context_oracle_count"]["word_acc"]
    col = rep["manifold_collapse"]["word_acc"]
    ratio = (col / ncf) if ncf > 0 else INF
    cer_drop = 1.0 - (rep["manifold_collapse"]["cer_micro"] /
                      max(1e-9, rep["no_context_free"]["cer_micro"]))
    rep["verdict"] = {"word_acc_ratio_vs_free": ratio, "cer_relative_drop": cer_drop,
                      "beats_oracle_count": bool(col > nco),
                      "win": bool(ratio >= WIN_WORD_ACC_RATIO and cer_drop >= WIN_CER_DROP)}
    return rep, per_word, True


def stage_decode():
    print(f"\n{SEP}\n  STAGE: decode (no-context free/oracle-count vs LEXICON-COLLAPSE)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("decode")
    prep = _require("prep.json")
    bankd = _require("bank.json")
    trie = r62._build_trie(prep["lexicon"])
    logfreq = prep["logfreq"]
    lam = r62.FREE_SEG_LAMBDA_MULT * bankd["median_char_cost"]

    arms = [("raw", "recog_raw.json", "WHOLE-FIGURE raw-point SC+TPS+SmoothDeform (cursive-capable)"),
            ("program_score", "recog.json", "per-stroke program_score (run-47; cursive FLOOR)")]
    out = {"arms": {}}
    per_word_by_arm = {}
    for tag, fname, label in arms:
        p = _ckpt(fname)
        if not os.path.exists(p):
            continue
        rec = _load(p)["recog"]
        cache = _ckpt(f"decode_{tag}.json")
        rep, per_word, complete = _decode_recog(rec, trie, logfreq, lam, cache_path=cache,
                                                 t0=t0, budget=430)
        if not complete:
            _seed_guard("decode", md5_before)
            print(f"  decode incomplete for arm '{tag}' ({len(per_word)}/{len(rec)}) -- "
                  f"re-invoke --stage decode to resume.", flush=True)
            return 2
        rep["label"] = label
        out["arms"][tag] = rep
        per_word_by_arm[tag] = per_word
        print(f"\n  >>> ARM: {label}  (recog={fname})")
        _print_decode(rep)

    # matched-subset contrast (raw vs program_score on shared word indices).
    if "raw" in per_word_by_arm and "program_score" in per_word_by_arm:
        raw_by = {d["idx"]: d for d in per_word_by_arm["raw"]}
        ps_by = {d["idx"]: d for d in per_word_by_arm["program_score"]}
        shared = sorted(set(raw_by) & set(ps_by))
        if shared:
            raw_ok = [raw_by[i]["collapse"] == raw_by[i]["word"] for i in shared]
            ps_ok = [ps_by[i]["collapse"] == ps_by[i]["word"] for i in shared]
            print(f"\n  === MATCHED-SUBSET (n={len(shared)}) collapse word_acc: "
                  f"raw={100*sum(raw_ok)/len(shared):.1f}%  "
                  f"program_score={100*sum(ps_ok)/len(shared):.1f}%  "
                  f"McNemar(raw vs ps)={r61._mcnemar(ps_ok, raw_ok)}")
            out["matched_subset"] = {"n": len(shared),
                                     "raw_collapse_acc": sum(raw_ok) / len(shared),
                                     "ps_collapse_acc": sum(ps_ok) / len(shared)}
    # primary per_word = the raw arm if present (for the line POC), else program_score.
    out["per_word"] = per_word_by_arm.get("raw", per_word_by_arm.get("program_score", []))
    _save(out, _ckpt("decode.json"))
    _seed_guard("decode", md5_before)
    print(f"  saved -> {_ckpt('decode.json')}  [decode {time.time()-t0:.1f}s]")
    return 0


def _print_decode(rep):
    print(f"\n  === IAM-OnDB WORD READING (n_words={rep['n_words']}, "
          f"n_ref_chars={rep['n_ref_chars']}) ===")
    hdr = f"  {'reader':<42}{'word_acc':>11}{'word_CI':>16}{'CER':>10}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    def row(lab, r):
        ci = f"[{100*r['word_ci'][0]:.1f},{100*r['word_ci'][1]:.1f}]"
        print(f"  {lab:<42}{100*r['word_acc']:>9.1f}%{ci:>16}{100*r['cer_micro']:>9.1f}%")
    row("(a) no-context free-seg (commit+argmax)", rep["no_context_free"])
    row("(b) no-context oracle-char-count+argmax", rep["no_context_oracle_count"])
    row("(c) LEXICON-COLLAPSE (flat)", rep["manifold_collapse"])
    row("(c') LEXICON-COLLAPSE (+freq)", rep["manifold_collapse_freq"])
    mf, mo = rep["mcnemar_collapse_vs_free"], rep["mcnemar_collapse_vs_oracle"]
    print(f"\n  McNemar collapse vs free:   fixed={mf['fixed']} broken={mf['broken']} p={mf['p']:.3g}")
    print(f"  McNemar collapse vs oracle: fixed={mo['fixed']} broken={mo['broken']} p={mo['p']:.3g}")
    v = rep["verdict"]
    print(f"\n  VERDICT (pre-reg: word_acc ratio >= {WIN_WORD_ACC_RATIO}x free AND CER drop "
          f">= {100*WIN_CER_DROP:.0f}%):")
    print(f"    word_acc ratio (collapse/free) = {v['word_acc_ratio_vs_free']:.2f}x;  "
          f"CER relative drop = {100*v['cer_relative_drop']:.1f}%;  "
          f"beats-oracle-count = {v['beats_oracle_count']}")
    print(f"    -> {'WIN: reading-with-context holds on real IAM' if v['win'] else 'PARTIAL/NULL'}")


# ============================================================================================= #
#  STAGE: line_poc -- STAGE 3: line-level word-bigram LM over the per-word candidate lists.
# ============================================================================================= #
def _word_bigram_logprob(brown_bi, brown_uni, a, b, V):
    num = brown_bi.get(f"{a}|{b}", 0) + 1
    den = brown_uni.get(a, 0) + V
    return math.log(num / den)


def stage_line_poc():
    print(f"\n{SEP}\n  STAGE: line_poc (STAGE 3 -- line-level word-bigram LM, proof-of-concept)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("line_poc")
    prep = _require("prep.json")
    dec = _require("decode.json")
    per_word = dec["per_word"]

    # word-bigram from Brown (donkey=0).
    from nltk.corpus import brown
    bi = Counter()
    uni = Counter()
    toks = [w.lower() for w in brown.words() if w.isalpha()]
    prev = "<s>"
    for w in toks:
        bi[f"{prev}|{w}"] += 1
        uni[prev] += 1
        prev = w
    V = len(uni) + 1

    # group test words by line, ordered by position.
    by_line = defaultdict(list)
    for pw in per_word:
        by_line[pw["line_id"]].append(pw)
    lines = [sorted(v, key=lambda d: d["pos"]) for v in by_line.values() if len(v) >= 2]
    print(f"  lines with >=2 in-vocab test words: {len(lines)}  "
          f"(total test words in them: {sum(len(l) for l in lines)})", flush=True)

    # per-word best (collapse alpha=0 == topk[0]) vs line word-bigram Viterbi over candidate lists.
    base_ok = ctx_ok = tot = 0
    base_ed = ctx_ed = ref_chars = 0
    for line in lines:
        cand_lists = []
        truth = []
        for pw in line:
            cands = pw["topk"] if pw["topk"] else [[0.0, pw["collapse"]]]
            cand_lists.append(cands)
            truth.append(pw["word"])
        # baseline: independent argmin geometry (candidate 0).
        base = [cl[0][1] for cl in cand_lists]
        # Viterbi with word-bigram transitions; emission = -geom_cost.
        n = len(cand_lists)
        dp = []
        bp = []
        first = cand_lists[0]
        dp.append([-c + BIGRAM_BETA * _word_bigram_logprob(bi, uni, "<s>", w, V)
                   for c, w in first])
        bp.append([-1] * len(first))
        for i in range(1, n):
            cur = cand_lists[i]
            row = []
            brow = []
            for c, w in cur:
                best_s, best_p = -INF, 0
                for pj, (pc, pw_) in enumerate(cand_lists[i - 1]):
                    s = dp[i - 1][pj] + BIGRAM_BETA * _word_bigram_logprob(bi, uni, pw_, w, V)
                    if s > best_s:
                        best_s, best_p = s, pj
                row.append(best_s + (-c))
                brow.append(best_p)
            dp.append(row)
            bp.append(brow)
        # backtrace.
        last = int(np.argmax(dp[-1]))
        seq_idx = [last]
        for i in range(n - 1, 0, -1):
            last = bp[i][last]
            seq_idx.append(last)
        seq_idx.reverse()
        ctx = [cand_lists[i][seq_idx[i]][1] for i in range(n)]
        for i in range(n):
            base_ok += (base[i] == truth[i])
            ctx_ok += (ctx[i] == truth[i])
            base_ed += _levenshtein(base[i], truth[i])
            ctx_ed += _levenshtein(ctx[i], truth[i])
            ref_chars += len(truth[i])
            tot += 1

    def _rate(k, t):
        return k / t if t else 0.0
    rep = {"n_lines": len(lines), "n_words": tot,
           "per_word_lexicon": {"word_acc": _rate(base_ok, tot), "wer": 1 - _rate(base_ok, tot),
                                 "cer": base_ed / max(1, ref_chars)},
           "line_word_bigram": {"word_acc": _rate(ctx_ok, tot), "wer": 1 - _rate(ctx_ok, tot),
                                "cer": ctx_ed / max(1, ref_chars)}}
    _save(rep, _ckpt("line_poc.json"))
    _seed_guard("line_poc", md5_before)
    print(f"\n  === STAGE 3 LINE-LEVEL POC (n_lines={rep['n_lines']}, n_words={rep['n_words']}) ===")
    for key, lab in (("per_word_lexicon", "per-word lexicon (no line ctx)"),
                     ("line_word_bigram", "+ line word-bigram LM")):
        r = rep[key]
        print(f"    {lab:<34} word_acc={100*r['word_acc']:5.1f}%  "
              f"WER={100*r['wer']:5.1f}%  CER={100*r['cer']:5.1f}%")
    print(f"  saved -> {_ckpt('line_poc.json')}  [line_poc {time.time()-t0:.1f}s]")
    return 0


# ============================================================================================= #
#  STAGE: summary
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 63 SCOREBOARD (READING IAM-OnDB)\n{SEP}")
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    dec = _require("decode.json")
    print(f"\n  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: {md5_now == prep['stroke_shapes_md5']})")
    print(f"  best adaptive word-seg (diagnostic): gap_frac={prep['best_gap_frac']} "
          f"(exact word-count "
          f"{100*max(d['exact_count'] for d in prep['seg_diag']):.1f}%) -- "
          f"reading uses ORACLE word-count segmentation.")
    for tag, rep in dec.get("arms", {}).items():
        print(f"\n  >>> ARM: {rep.get('label', tag)}")
        _print_decode(rep)
    if "matched_subset" in dec:
        m = dec["matched_subset"]
        print(f"\n  MATCHED-SUBSET (n={m['n']}) collapse word_acc: raw={100*m['raw_collapse_acc']:.1f}% "
              f"vs program_score={100*m['ps_collapse_acc']:.1f}%")
    lp = _ckpt("line_poc.json")
    if os.path.exists(lp):
        r = _load(lp)
        print(f"\n  STAGE 3 LINE POC (n_lines={r['n_lines']}, n_words={r['n_words']}):")
        print(f"    per-word lexicon      WER={100*r['per_word_lexicon']['wer']:.1f}%  "
              f"CER={100*r['per_word_lexicon']['cer']:.1f}%")
        print(f"    + line word-bigram    WER={100*r['line_word_bigram']['wer']:.1f}%  "
              f"CER={100*r['line_word_bigram']['cer']:.1f}%")
    print(f"\n  ILLUSTRATIVE RESCUES (free/oracle -> collapse):")
    shown = 0
    for pw in dec["per_word"]:
        if pw["collapse"] == pw["word"] and (pw["free"] != pw["word"] or pw["oracle"] != pw["word"]):
            print(f"    {pw['word']:<10} free='{pw['free']}' oracle='{pw['oracle']}' "
                  f"-> collapse='{pw['collapse']}'")
            shown += 1
            if shown >= 14:
                break
    print(f"\n{SEP}\n  RUN 63 COMPLETE -- see final agent report.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                   choices=["prep", "bank", "recognize", "recognize_raw", "decode", "line_poc",
                            "summary"])
    args = p.parse_args()
    fn = {"prep": stage_prep, "bank": stage_bank, "recognize": stage_recognize,
          "recognize_raw": stage_recognize_raw, "decode": stage_decode,
          "line_poc": stage_line_poc, "summary": stage_summary}[args.stage]
    return fn()


if __name__ == "__main__":
    sys.exit(main())
