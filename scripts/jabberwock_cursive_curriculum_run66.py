"""jabberwock_cursive_curriculum_run66.py -- RUN 66: TEACH THE JABBERWOCK TO READ AND WRITE
CURSIVE VIA A CURRICULUM (letters -> joins -> write -> read-by-AbS).

THE PRINCIPLE (creator): generation IS reading (AbS). Run 65 established the ligature is NOT
strippable -- it is distributed and geometrically entangled with the character. The fix is to
model it GENERATIVELY: LEARN TO WRITE cursive (a connected trajectory whose letters are joined by
real ligatures), then READ = invert that generator (propose letter-seq -> GENERATE connected
cursive -> compare to the query whole-word -> collapse with lexicon). A curriculum teaches this in
stages like a human: LETTERS -> JOINS -> WORDS.

WHY THIS SHOULD BEAT THE FLOOR (measured, not assumed -- see the run-66 bring-up probes):
  * StrokeQuantize -> StrokeRender is a FAITHFUL inverse on single-stroke cursive letters
    (invariant round-trip DTW ~0.05). Generation = the exact inverse of quantization, on REAL ink.
  * BUT the rotation+scale-INVARIANT per-letter representation is barely discriminative
    (same-letter invariant DTW ~0.205 vs different-letter ~0.235) -- THIS is run 64/65's 17.8%
    floor: isolated exemplars, normalized, collapse together. The discriminative signal lives in
    the CONNECTED placement (natural pose + joins + relative letter sizes), which whole-word
    connected-to-connected matching preserves and per-char invariant matching destroys.

THE CURRICULUM (each stage LEARNS via the jabberwock's OWN quantize/render machinery; donkey=0):
  STAGE 1 LETTERS  (learn_letters): learn a cursive letter-form codebook from DeepWriting single
      cursive chars (given seg, BACKGROUND writers). Multiple allographs per letter. Each form =
      a StrokeQuantize ShapeSignature (teach()'d to an ISOLATED seeds dir) + its natural writing
      pose (initial heading, arc-length) + a StrokeRender canonical polyline (the generator).
  STAGE 2 JOINS    (learn_joins): from adjacent single-stroke letter PAIRS within words, learn the
      JOIN = the connector displacement A.exit -> B.entry (in normalized letter units). The
      ligature-as-confound, LEARNED as a generative placement element.
  STAGE 3 WRITE    (write_validate): given a letter SEQUENCE, GENERATE the connected trajectory =
      compose learned letter-forms + learned joins (render each letter, place its entry at the
      previous exit + join). VALIDATE: does generated-WITH-joins match the REAL word's trajectory
      (whole-word DTW) materially better than concatenated-isolated-letters (no joins)?
  STAGE 4 READ     (read): the MILESTONE. per-char cost -> shortlist top-K same-length lexicon
      words (propose) -> GENERATE each as connected cursive -> whole-word DTW vs the query ->
      held Argmin -> lexicon collapse (verify). Arms: (a) isolated-exemplar per-char + lexicon
      (the run-64-style floor); (b) LEARNED-GENERATIVE AbS re-rank. Plus a CONTROLLED
      discrimination test (true word + N decoys) that isolates generation quality from the
      proposal bottleneck.

PRE-REGISTERED MILESTONE: LICENSED-TO-SCALE if the learned-generative AbS reader (b) MATERIALLY
beats the isolated-exemplar floor (a) -- bar: word acc CI-separated above (a), OR whole-word
generated-to-real match materially better because connected-to-connected works (the Stage-3
join lift + the controlled-discrim accuracy well above chance). NULL -> localize the next lever
(join model too weak? generation-match floored? cursive variability too high for the codebook?).

DISCIPLINE: donkey=0 (no trained net; all geometry DECISIONS via native StrokeQuantize/
StrokeRender/DtwTo/Argmin Terms; placement is mechanical host geometry, the same class as
abs_read._render_goal / _junction_blend). teach() redirected to results/run66_checkpoints/seeds/
(run-34c pattern). SEED GUARD: OZMA_SEED_PERSIST_DISABLED=1; every stage asserts
md5(seeds/stroke_shapes.json) UNCHANGED before+after. run*_checkpoints READ-ONLY. NO git add/commit.

Run:
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_cursive_curriculum_run66.py --stage <S>
  stages: prep -> learn_letters -> learn_joins -> write_validate -> read -> summary
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
from pathlib import Path

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run66_checkpoints")
RUN66_SEEDS_DIR = os.path.join(CKPT_DIR, "seeds")
os.makedirs(CKPT_DIR, exist_ok=True)
os.makedirs(RUN66_SEEDS_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run66.log")

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
SPLIT = "training"
WRITER_SPLIT_SEED = 20260706           # byte-identical to run 62/64.
N_BACKGROUND_FRAC = 0.5
WORD_MIN_LEN, WORD_MAX_LEN = 3, 8
LOWER_CLASSES = list(range(10, 36))    # canonical 62-class ids for 'a'..'z'.

K_ALLO = 4                             # allographs per letter (multiple cursive forms).
MEDOID_SUBSAMPLE = 60                  # exemplars sampled per class for medoid/FPS selection.
LEARN_SEED = 20260714

N_TEST = 140                           # test words (>= 100 pre-reg).
TEST_SELECT_SEED = 20260715
SHORTLIST_K = 20                       # top-K lexicon candidates the AbS reader re-ranks.
FULL_LEX_CAP = 4000                    # cap on same-length lexicon words the full-AbS reader scores.
N_DECOYS = 15                          # controlled-discrimination decoy count.
DISCRIM_SEED = 20260716

# geometry grains (StrokeQuantize/StrokeRender) -- abs_read's own single-stroke defaults.
SEG, TURN_BINS, LEN_BINS, GRID, SCALE_BINS = 12, 16, 8, 8, 8
CANON_N = 24                           # fixed per-letter canonical resample length.
WORD_N = 64                            # whole-word DTW resample length.
FREQ_PRIOR_ALPHA = 0.0                 # flat lexicon prior (primary arm).
PER_CALL_BUDGET_SECONDS = 480.0
INF = math.inf

# lazily imported deps (heavy).
import scripts.jabberwock_wordread_run61 as r61
import scripts.jabberwock_realwordread_run62 as r62
from domains import deepwriting_world as dww
from domains import stroke_codebook as sc
from domains.teach import teach as _real_teach

SYMBOLS = dww.CANON_SYMBOLS


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


def _require(name):
    p = _ckpt(name)
    if not os.path.exists(p):
        raise SystemExit(f"WALL: run the stage that produces {name} first.")
    return _load(p)


def _seed_guard(stage, before=None):
    cur = _md5(STROKE_SHAPES_SEED)
    if before is not None and cur != before:
        raise SystemExit(f"HARD STOP: seeds/stroke_shapes.json md5 changed during {stage} "
                         f"({before} -> {cur}).")
    return cur


def _wilson(k, n):
    return r61._wilson_ci(k, n)


# ============================================================================================= #
#  CURRICULUM GEOMETRY PRIMITIVES  (all DECISIONS via native Terms; placement = mechanical
#  host geometry -- the same admissible class as abs_read._render_goal / _junction_blend).
# ============================================================================================= #
def dtw(native, a, b) -> float:
    """ONE held DtwTo evaluate. a,b are point lists [[x,y],...]."""
    return float(native.evaluate(
        {"type": "DtwTo", "a": {"type": "Lit", "value": np.asarray(a, float).tolist()},
         "b": {"type": "Lit", "value": np.asarray(b, float).tolist()}}, {}) or 0.0)


def _quantize(native, points):
    return native.evaluate(
        {"type": "StrokeQuantize", "points": {"type": "Lit", "value": np.asarray(points, float).tolist()},
         "segments": SEG, "turn_bins": TURN_BINS, "len_bins": LEN_BINS, "grid": GRID,
         "scale_bins": SCALE_BINS, "canonical_pose": True}, {})


def _render(native, signature, n):
    return np.asarray(native.evaluate(
        {"type": "StrokeRender", "signature": {"type": "Lit", "value": signature},
         "n_points": int(max(8, n)), "apply_pose": False, "turn_bins": TURN_BINS,
         "len_bins": LEN_BINS, "grid": GRID, "scale_bins": SCALE_BINS, "field": "points"}, {}), float)


def invariant(points, n=CANON_N):
    """StrokeQuantize's own canonical normalization (translate-start, rotate-initial-heading,
    scale-arclen=1), kept CONTINUOUS -- reuses stroke_codebook._invariant_points."""
    return sc._invariant_points(np.asarray(points, float), n)


def _arclen(pts):
    pts = np.asarray(pts, float)
    if len(pts) < 2:
        return 1.0
    return float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1))) or 1.0


def _heading(pts):
    pts = np.asarray(pts, float)
    if len(pts) < 2:
        return 0.0
    v = pts[-1] - pts[0]
    # use the gross entry->exit direction for a stable natural orientation of the placed letter.
    if np.linalg.norm(v) < 1e-9:
        v = pts[1] - pts[0]
    return float(math.atan2(v[1], v[0]))


def learn_letter_form(native, points) -> dict:
    """LEARN one cursive letter allograph: quantize (StrokeQuantize ShapeSignature) + render the
    canonical generator polyline (StrokeRender, proving the inverse) + record the natural writing
    pose (initial heading, arc-length). Pure geometry, donkey=0."""
    pts = np.asarray(points, float)
    q = _quantize(native, pts)
    sig = q["signature"]
    r = _render(native, sig, max(CANON_N, q.get("n_points") or CANON_N))
    canon = invariant(r, CANON_N)                       # invariant frame: start origin, heading +x, arclen 1
    return {"signature": [list(x) for x in sig], "n_points": int(q.get("n_points") or len(pts)),
            "theta": _heading(pts), "arclen": _arclen(pts), "canon": canon}


def render_form_canonical(native, form) -> np.ndarray:
    """StrokeRender the learned form's signature back to a canonical polyline (the generator)."""
    return _render(native, [list(x) for x in form["signature"]], CANON_N)


def _place_letter(form, cursor, unit):
    """Mechanical placement: rotate the canonical form to its natural heading, scale to its natural
    size (relative to the word unit), translate its entry to `cursor`. Returns (points, exit)."""
    P = np.asarray(form["canon"], float)
    th = float(form["theta"])
    scale = float(form["arclen"]) / unit
    c, s = math.cos(th), math.sin(th)
    R = np.array([[c, -s], [s, c]])
    nat = (P @ R.T) * scale                              # start still at origin (P[0]==origin)
    placed = np.asarray(cursor, float) + nat
    return placed, placed[-1]


def generate_word(native, forms, join_gap, joins=True):
    """GENERATE a connected cursive trajectory from a letter-form SEQUENCE. WITH joins: each
    letter's entry is placed at the previous letter's EXIT + the learned join gap (pen
    continuity). WITHOUT joins: letters are placed side-by-side at a fixed baseline pitch
    (isolated concatenation). Mechanical geometry (native unused here -- forms carry cached
    canonical renders); kept as a param for API symmetry with the quantize/render primitives."""
    if not forms:
        return np.zeros((2, 2))
    unit = float(np.mean([f["arclen"] for f in forms])) or 1.0
    jg = np.asarray(join_gap, float) * unit
    out = []
    cursor = np.zeros(2)
    for k, f in enumerate(forms):
        if joins:
            placed, exit_pt = _place_letter(f, cursor, unit)
            cursor = exit_pt + jg
        else:
            base = np.array([k * unit, 0.0])
            placed, _ = _place_letter(f, base, unit)
        out.append(placed)
    return np.concatenate(out, axis=0)


def wordnorm(points, n=WORD_N):
    """Whole-word normalization for DTW: translate to start, scale by arc-length to 1, resample to
    n -- NO rotation (keeps relative letter placement + orientation, the connected signal)."""
    pts = np.asarray(points, float)
    if pts.ndim != 2 or len(pts) < 2:
        return [[0.0, 0.0]] * max(2, n)
    from domains import glyph_motor_world as gmw
    rs = np.asarray(gmw._resample_arclen(pts, max(2, n)), float)
    rs = rs - rs[0]
    al = float(np.sum(np.linalg.norm(np.diff(rs, axis=0), axis=1))) or 1.0
    return (rs / al).tolist()


def word_points(word_rec):
    """Whole-word connected ink of a test-word record: concat its char_segs' strokes in order."""
    out = []
    for cs in word_rec["char_segs"]:
        for s in cs["strokes"]:
            out.append(np.asarray(s, float)[:, :2])
    if not out:
        return np.zeros((2, 2))
    return np.concatenate(out, axis=0)


def extract_join(A_points, B_points):
    """The JOIN = connector displacement A.exit -> B.entry, in normalized letter units (mean of
    the two letters' arc-lengths). A 2-vector."""
    A = np.asarray(A_points, float)
    B = np.asarray(B_points, float)
    unit = (_arclen(A) + _arclen(B)) / 2.0 or 1.0
    return ((B[0] - A[-1]) / unit).tolist()


def teach_letter_form(agent, symbol, allo, form, seeds_dir=None):
    """teach() the learned cursive letter-form as a ShapeSignature, REDIRECTED to the isolated
    seeds dir (never the real boot seed). 'Learn the letters', persisted."""
    sd = Path(seeds_dir) if seeds_dir is not None else Path(RUN66_SEEDS_DIR)
    tagent = agent if hasattr(agent, "s") else type("_TA", (), {"s": agent})()
    attrs = {
        "name": f"cursive_{symbol}_{allo}", "kind": "cursive_letter", "symbol": symbol,
        "allograph": int(allo),
        "signature": json.dumps([list(x) for x in form["signature"]]),
        "theta": float(form["theta"]), "arclen": float(form["arclen"]),
        "n_points": int(form["n_points"]),
    }
    return _real_teach(tagent, "ShapeSignature", attrs, category="cursive_letters", seeds_dir=sd)


# ============================================================================================= #
#  STAGE: prep -- load DeepWriting, cross-writer split, lexicon, test words.
# ============================================================================================= #
def _ser_word(w):
    return {"writer": w["writer"], "word": w["word"], "sample": w["sample"],
            "char_segs": [{"class": c["class"], "symbol": c["symbol"],
                           "strokes": [np.asarray(s, float)[:, :2].tolist() for s in c["strokes"]]}
                          for c in w["char_segs"]]}


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (DeepWriting load + cross-writer split + lexicon + test words)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    lex, logfreq, brown = r62._build_lexicon()
    lexset = set(lex)
    print(f"  lexicon (Brown+WordNet, len {WORD_MIN_LEN}-{WORD_MAX_LEN}) = {len(lex)}  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    dw = dww.load_deepwriting(SPLIT)
    print(f"  DeepWriting '{SPLIT}': {dw['n']} samples  [{time.time()-t0:.1f}s]", flush=True)
    words = dww.extract_words(dw, min_len=WORD_MIN_LEN, max_len=WORD_MAX_LEN,
                              lowercase_only=True, complete_only=True, lexicon=lexset)
    print(f"  complete in-lex words = {len(words)}  writers={len({w['writer'] for w in words})}  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    bg_words, ho_words = dww.writer_split(words, n_background_frac=N_BACKGROUND_FRAC,
                                          seed=WRITER_SPLIT_SEED)
    bg_writers = {w["writer"] for w in bg_words}
    ho_writers = {w["writer"] for w in ho_words}
    print(f"  background(learn) writers={len(bg_writers)}  held-out(test) writers={len(ho_writers)}  "
          f"disjoint={bg_writers.isdisjoint(ho_writers)}", flush=True)

    # test words: held-out writers, restricted to words whose every char has a single-stroke form
    # somewhere in the BACKGROUND pool (so the learned codebook can generate them). Multi-stroke
    # letters (i/t/x/j dots+crosses) are dropped from the test set -- reported honestly.
    rng = np.random.default_rng(TEST_SELECT_SEED)
    usable = [w for w in ho_words
              if all(len(cs["strokes"]) == 1 and len(cs["strokes"][0]) >= 5 for cs in w["char_segs"])]
    order = rng.permutation(len(usable))
    sel = [usable[int(i)] for i in order[:N_TEST]]
    print(f"  usable held-out words (all single-stroke chars) = {len(usable)}; selected test = {len(sel)}",
          flush=True)
    print(f"  test len-dist = {sorted(Counter(len(w['word']) for w in sel).items())}", flush=True)
    print(f"  sample test words: {[w['word'] for w in sel[:20]]}", flush=True)

    out = {"lexicon": lex, "logfreq": logfreq,
           "background_words": [_ser_word(w) for w in bg_words],
           "test_words": [_ser_word(w) for w in sel],
           "bg_writers": sorted(bg_writers), "ho_writers": sorted(ho_writers),
           "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE 1: learn_letters -- the cursive letter-form codebook (allographs), teach()'d isolated.
# ============================================================================================= #
def _bg_single_stroke_by_class(bg_words):
    by_class = defaultdict(list)
    for w in bg_words:
        for cs in w["char_segs"]:
            if cs["class"] in set(LOWER_CLASSES) and len(cs["strokes"]) == 1 \
                    and len(cs["strokes"][0]) >= 6:
                by_class[cs["class"]].append(np.asarray(cs["strokes"][0], float))
    return by_class


def _select_allographs(native, exemplars, k, rng):
    """Greedy farthest-point-sampling of k allographs (invariant-DTW diverse) around the medoid.
    The medoid (min total invariant-DTW to a subsample) is allograph 0; the rest maximize
    diversity. All DISTANCES are held DtwTo evaluates."""
    if len(exemplars) <= k:
        return list(range(len(exemplars)))
    idx = rng.permutation(len(exemplars))[:MEDOID_SUBSAMPLE]
    invs = {i: invariant(exemplars[i], CANON_N) for i in idx}
    ids = list(invs)
    # pairwise invariant-DTW (subsample) -> medoid.
    D = {}
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            d = dtw(native, invs[ids[a]], invs[ids[b]])
            D[(ids[a], ids[b])] = d
            D[(ids[b], ids[a])] = d
    tot = {i: sum(D.get((i, j), 0.0) for j in ids) for i in ids}
    medoid = min(ids, key=lambda i: tot[i])
    chosen = [medoid]
    while len(chosen) < k:
        # pick the exemplar maximizing its min distance to the already-chosen set (FPS).
        best_i, best_d = None, -1.0
        for i in ids:
            if i in chosen:
                continue
            md = min(D.get((i, c), 0.0) for c in chosen)
            if md > best_d:
                best_d, best_i = md, i
        if best_i is None:
            break
        chosen.append(best_i)
    return chosen


def stage_learn_letters():
    print(f"\n{SEP}\n  STAGE 1: learn_letters (cursive letter-form codebook; allographs; teach() "
          f"isolated)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("learn_letters")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    ag = srs.Substrate()
    prep = _require("prep.json")

    by_class = _bg_single_stroke_by_class(prep["background_words"])
    print(f"  background single-stroke lowercase exemplars: "
          f"{sum(len(v) for v in by_class.values())} over {len(by_class)} classes", flush=True)
    rng = np.random.default_rng(LEARN_SEED)
    codebook = {}
    n_taught = 0
    for c in LOWER_CLASSES:
        ex = by_class.get(c, [])
        if not ex:
            codebook[str(c)] = []
            continue
        picks = _select_allographs(native, ex, K_ALLO, rng)
        forms = []
        for a, pi in enumerate(picks):
            form = learn_letter_form(native, ex[pi])
            teach_letter_form(ag, SYMBOLS[c], a, form, seeds_dir=RUN66_SEEDS_DIR)
            n_taught += 1
            forms.append(form)
        codebook[str(c)] = forms
        print(f"    {SYMBOLS[c]}: {len(ex)} exemplars -> {len(forms)} allographs  "
              f"[{time.time()-t0:.1f}s]", flush=True)
    _save({"codebook": codebook, "k_allo": K_ALLO}, _ckpt("letters.json"))
    _seed_guard("learn_letters", md5_before)
    # verify isolated teach wrote to the run dir, real seed untouched.
    iso = list(Path(RUN66_SEEDS_DIR).glob("*.json"))
    print(f"  taught {n_taught} letter-forms -> isolated seeds {[p.name for p in iso]}", flush=True)
    print(f"  REAL seeds/stroke_shapes.json md5 unchanged: {_md5(STROKE_SHAPES_SEED)==md5_before}",
          flush=True)
    # quick fidelity report: mean invariant round-trip DTW over the medoid forms.
    ds = []
    for c in LOWER_CLASSES:
        for form in codebook[str(c)][:1]:
            r = render_form_canonical(native, form)
            ds.append(dtw(native, invariant(r, CANON_N), np.asarray(form["canon"]).tolist()))
    if ds:
        print(f"  generator self-consistency (render vs stored canon) DTW mean={np.mean(ds):.4f}",
              flush=True)
    print(f"  saved -> {_ckpt('letters.json')}  [learn_letters {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE 2: learn_joins -- the connector model from adjacent letter pairs.
# ============================================================================================= #
def stage_learn_joins():
    print(f"\n{SEP}\n  STAGE 2: learn_joins (connector A.exit -> B.entry from adjacent letter "
          f"pairs)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("learn_joins")
    prep = _require("prep.json")

    joins = []
    per_first = defaultdict(list)
    for w in prep["background_words"]:
        segs = w["char_segs"]
        for k in range(len(segs) - 1):
            a, b = segs[k], segs[k + 1]
            if len(a["strokes"]) != 1 or len(b["strokes"]) != 1:
                continue
            A = np.asarray(a["strokes"][0], float)
            B = np.asarray(b["strokes"][0], float)
            if len(A) < 4 or len(B) < 4:
                continue
            j = extract_join(A, B)
            joins.append(j)
            per_first[a["class"]].append(j)
    J = np.asarray(joins, float)
    glob = J.mean(axis=0).tolist() if len(J) else [0.0, 0.0]
    glob_std = J.std(axis=0).tolist() if len(J) else [0.0, 0.0]
    per_first_mean = {str(c): np.asarray(v, float).mean(axis=0).tolist()
                      for c, v in per_first.items() if len(v) >= 20}
    print(f"  learned joins from {len(joins)} adjacent single-stroke pairs", flush=True)
    print(f"  GLOBAL join gap (norm units): mean={[round(x,3) for x in glob]}  "
          f"std={[round(x,3) for x in glob_std]}", flush=True)
    print(f"  per-first-letter joins learned: {len(per_first_mean)} classes", flush=True)
    _save({"global": glob, "global_std": glob_std, "per_first": per_first_mean, "n": len(joins)},
          _ckpt("joins.json"))
    _seed_guard("learn_joins", md5_before)
    print(f"  saved -> {_ckpt('joins.json')}  [learn_joins {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  helpers shared by write_validate + read.
# ============================================================================================= #
def _load_codebook():
    lt = _require("letters.json")["codebook"]
    return {int(c): forms for c, forms in lt.items()}


def _medoid_form(codebook, cls):
    forms = codebook.get(cls, [])
    return forms[0] if forms else None


def _gen_from_word(native, word, codebook, join_gap, joins=True):
    """Generate a candidate word string as connected cursive using each letter's medoid allograph.
    Returns None if any letter has no learned form."""
    forms = []
    for ch in word:
        cls = dww.canon_class(ch)
        f = _medoid_form(codebook, cls) if cls is not None else None
        if f is None:
            return None
        forms.append(f)
    return generate_word(native, forms, join_gap, joins=joins)


# ============================================================================================= #
#  STAGE 3: write_validate -- does generated-WITH-joins match real better than no-joins?
# ============================================================================================= #
def stage_write_validate():
    print(f"\n{SEP}\n  STAGE 3: write_validate (generated cursive vs real; joins vs no-joins)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("write_validate")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    codebook = _load_codebook()
    joins = _require("joins.json")
    jg = np.asarray(joins["global"], float)

    words = prep["test_words"]
    d_join, d_nojoin, d_shuffle = [], [], []
    n_ok = 0
    rng = np.random.default_rng(99)
    for w in words:
        q = wordnorm(word_points(w))
        gj = _gen_from_word(native, w["word"], codebook, jg, joins=True)
        gn = _gen_from_word(native, w["word"], codebook, jg, joins=False)
        if gj is None or gn is None:
            continue
        n_ok += 1
        d_join.append(dtw(native, q, wordnorm(gj)))
        d_nojoin.append(dtw(native, q, wordnorm(gn)))
        # control: a SHUFFLED-letters word of the same length (generation of the wrong content).
        letters = list(w["word"])
        rng.shuffle(letters)
        gs = _gen_from_word(native, "".join(letters), codebook, jg, joins=True)
        if gs is not None:
            d_shuffle.append(dtw(native, q, wordnorm(gs)))
    dj, dn, dss = np.asarray(d_join), np.asarray(d_nojoin), np.asarray(d_shuffle)
    joins_better = int(np.sum(dj < dn))
    print(f"\n  === STAGE 3: WRITING VALIDATION (n={n_ok} words) ===")
    print(f"  whole-word DTW  generated-vs-real:")
    print(f"    WITH joins       mean={dj.mean():.4f}  median={np.median(dj):.4f}")
    print(f"    NO joins (concat)mean={dn.mean():.4f}  median={np.median(dn):.4f}")
    print(f"    SHUFFLED letters mean={dss.mean():.4f}  (content control; should be WORSE)")
    print(f"  joins better than no-joins: {joins_better}/{n_ok} = {100*joins_better/max(1,n_ok):.1f}%")
    lift = (dn.mean() - dj.mean())
    print(f"  join lift (no-join mean - join mean) = {lift:+.4f}  "
          f"({'JOINS HELP' if lift > 0 else 'joins do NOT help'})")
    print(f"  discrimination margin (shuffle mean - join mean) = {dss.mean()-dj.mean():+.4f}")
    _save({"n": n_ok, "with_joins": dj.tolist(), "no_joins": dn.tolist(),
           "shuffle": dss.tolist(), "joins_better": joins_better}, _ckpt("write_validate.json"))
    _seed_guard("write_validate", md5_before)
    print(f"  [write_validate {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE 4: read -- THE MILESTONE. (a) isolated-exemplar+lexicon floor vs (b) generative AbS.
# ============================================================================================= #
def _char_cost_vector(native, char_pts, codebook):
    """62-length cost vector (lower=better): entry[c] = min invariant-DTW over class c's allograph
    canonical forms. The isolated-exemplar per-char channel (the run-64-style floor matcher)."""
    qi = invariant(char_pts, CANON_N)
    vec = [1e6] * 62
    for c in LOWER_CLASSES:
        best = INF
        for form in codebook.get(c, []):
            d = dtw(native, qi, np.asarray(form["canon"]).tolist())
            if d < best:
                best = d
        vec[c] = float(best if best != INF else 1e6)
    return vec


def _argmin_native(native, pairs):
    """Held Argmin over (cost, id) pairs -> the winning id (the reading DECISION, not a Python
    min()). Mirrors abs_read._argmin_pairs_term. NB the Argmin Term returns the WHOLE winning
    element (the [cost, id] pair, per stroke_codebook.continuous_mint_or_note's own `winner[1]`
    idiom); this returns element[1] = the id."""
    win = native.evaluate(
        {"type": "Argmin", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
         "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                   "index": {"type": "Lit", "value": 0}}, "default": None}, {})
    if win is None:
        return ""
    return win[1] if isinstance(win, (list, tuple)) and len(win) > 1 else ""


def _shortlist(dists, true_len, lex_by_len, k):
    """Top-k same-length lexicon words by summed per-char cost (the cheap proposal)."""
    cands = lex_by_len.get(true_len, [])
    if not cands:
        return []
    D = np.asarray(dists)
    scored = []
    for w in cands:
        cls = [r61._lower_class(ch) for ch in w]
        cost = float(sum(D[i, cls[i]] for i in range(true_len)))
        scored.append((cost, w))
    scored.sort(key=lambda t: t[0])
    return [w for _, w in scored[:k]]


def stage_read():
    print(f"\n{SEP}\n  STAGE 4: read -- MILESTONE (isolated-exemplar floor vs generative AbS)\n{SEP}")
    t0 = time.time()
    md5_before = _seed_guard("read")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    codebook = _load_codebook()
    joins = _require("joins.json")
    jg = np.asarray(joins["global"], float)
    lexicon = prep["lexicon"]
    logfreq = prep["logfreq"]
    lex_by_len = r61._lex_by_len(lexicon)

    out_path = _ckpt("read.json")
    state = _load(out_path) if os.path.exists(out_path) else {"records": [], "done": False}
    if state.get("done"):
        print(f"  read already COMPLETE (n={len(state['records'])}).")
        _report_read(state)
        return 0
    done = {r["wi"] for r in state["records"]}

    words = prep["test_words"]
    drng = np.random.default_rng(DISCRIM_SEED)
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    # cache generated candidate trajectories (wordnorm) across queries -- content-keyed.
    gen_cache = {}

    def gen_norm(word):
        key = (word, True)
        if key not in gen_cache:
            g = _gen_from_word(native, word, codebook, jg, joins=True)
            gen_cache[key] = None if g is None else wordnorm(g)
        return gen_cache[key]

    for wi, w in enumerate(words):
        if wi in done:
            continue
        true = w["word"]
        L = len(true)
        # per-char cost vectors (isolated-exemplar channel).
        dists = [_char_cost_vector(native, np.asarray(cs["strokes"][0], float), codebook)
                 for cs in w["char_segs"]]
        # (a) baseline: no-context argmin + lexicon-collapse top-1.
        nc = r61.decode_no_context(dists, SYMBOLS)
        lx = r61.decode_lexicon(dists, L, lex_by_len, logfreq, FREQ_PRIOR_ALPHA)
        # proposal shortlist (shared).
        shortlist = _shortlist(dists, L, lex_by_len, SHORTLIST_K)
        cover = true in shortlist
        # (b) generative AbS re-rank of the shortlist (whole-word connected DTW).
        q = wordnorm(word_points(w))
        pairs = []
        for cand in shortlist:
            gn = gen_norm(cand)
            if gn is None:
                continue
            pairs.append([dtw(native, q, gn), cand])
        pred_b = _argmin_native(native, pairs) if pairs else ""
        # (b-full) generative AbS as the PRIMARY reader: score EVERY same-length lexicon word by
        # generation DTW, argmin -- the fair open-vocab-within-lexicon reading number, NOT gated
        # by the weak per-char proposal. Capped (seeded) for tractability; `cover_full` records
        # whether the true word was in the scored set (never injected -- an honest open-vocab test).
        same_len = lex_by_len.get(L, [])
        if len(same_len) > FULL_LEX_CAP:
            fidx = np.random.default_rng(1000 + L).permutation(len(same_len))[:FULL_LEX_CAP]
            fcands = [same_len[int(i)] for i in fidx]
        else:
            fcands = list(same_len)
        cover_full = true in fcands
        fpairs = []
        for cand in fcands:
            gn = gen_norm(cand)
            if gn is not None:
                fpairs.append([dtw(native, q, gn), cand])
        pred_bf = _argmin_native(native, fpairs) if fpairs else ""
        # controlled discrimination: true + N decoys (same length), generation-quality isolated.
        decoys = [x for x in lex_by_len.get(L, []) if x != true]
        drng.shuffle(decoys)
        cset = [true] + decoys[:N_DECOYS]
        dpairs = []
        for cand in cset:
            gn = gen_norm(cand)
            if gn is None:
                continue
            dpairs.append([dtw(native, q, gn), cand])
        pred_d = _argmin_native(native, dpairs) if dpairs else ""

        state["records"].append({
            "wi": wi, "word": true, "no_context": nc, "lexicon_a": lx,
            "gen_abs_b": pred_b, "gen_full": pred_bf, "discrim": pred_d, "cover_k": bool(cover),
            "cover_full": bool(cover_full), "n_full": len(fcands),
            "shortlist_n": len(shortlist), "cset_n": len(cset)})
        n_new += 1
        if n_new % 10 == 0:
            _save(state, out_path)
            _seed_guard("read", md5_before)
            ka = sum(1 for r in state["records"] if r["lexicon_a"] == r["word"])
            kb = sum(1 for r in state["records"] if r["gen_abs_b"] == r["word"])
            print(f"    ... {len(state['records'])}/{len(words)}  lexA={100*ka/len(state['records']):.1f}%"
                  f"  genB={100*kb/len(state['records']):.1f}%  [{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                print(f"  WALL-BUDGET: {len(state['records'])}/{len(words)} done -- re-invoke.",
                      flush=True)
                _seed_guard("read", md5_before)
                return 2
    state["done"] = True
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  read {len(state['records'])} words  [{time.time()-t0:.1f}s]", flush=True)
    _report_read(state)
    return 0


def _char_acc(pred, true):
    n = min(len(pred), len(true))
    return sum(1 for i in range(n) if pred[i] == true[i]), len(true)


def _report_read(state):
    recs = state["records"]
    n = len(recs)
    if not n:
        print("  (no records)")
        return
    def wacc(key):
        return sum(1 for r in recs if r[key] == r["word"])
    def cacc(key):
        kc = tot = 0
        for r in recs:
            a, t = _char_acc(r[key], r["word"])
            kc += a
            tot += t
        return kc, tot
    cover = sum(1 for r in recs if r["cover_k"])
    print(f"\n  === STAGE 4: READING (connected cursive, cross-writer, n={n}) ===")
    print(f"  coverage@{SHORTLIST_K} (true word in proposal shortlist): "
          f"{cover}/{n} = {100*cover/n:.1f}%  (bounds the AbS re-rank ceiling)")
    hdr = f"  {'reader':<40}{'word_acc':>11}{'word_CI':>16}{'char_acc':>11}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    def row(lab, key):
        kw = wacc(key)
        kc, tot = cacc(key)
        ci = _wilson(kw, n)
        print(f"  {lab:<40}{100*kw/n:>9.1f}%{f'[{100*ci[0]:.1f},{100*ci[1]:.1f}]':>16}"
              f"{100*kc/tot if tot else 0:>9.1f}%")
    row("(a) isolated per-char argmin (no-context)", "no_context")
    row("(a) isolated per-char + LEXICON  [FLOOR]", "lexicon_a")
    row("(b) LEARNED-GENERATIVE AbS re-rank(propose)", "gen_abs_b")
    cf = sum(1 for r in recs if r.get("cover_full"))
    mean_full = np.mean([r.get("n_full", 0) for r in recs])
    row(f"(b-full) GENERATIVE AbS over lexicon", "gen_full")
    print(f"       (full-AbS scores mean {mean_full:.0f} same-len words/query; true in scored "
          f"set {cf}/{n}={100*cf/n:.0f}%; chance ~{100.0/max(1,mean_full):.2f}%)")
    row("    controlled discrim (true+decoys)", "discrim")
    # McNemar b vs a.
    fa = [r["lexicon_a"] == r["word"] for r in recs]
    fb = [r["gen_abs_b"] == r["word"] for r in recs]
    mc = r61._mcnemar(fa, fb)
    print(f"  McNemar (generative-b vs lexicon-a): b_fixed={mc['broken']}? "
          f"fixed={mc['fixed']} broken={mc['broken']} p={mc['p']:.3g}")
    # discrim chance line.
    mean_cset = np.mean([r["cset_n"] for r in recs])
    print(f"  controlled-discrim chance ~= {100.0/mean_cset:.1f}% (mean candidate set {mean_cset:.1f})")


# ============================================================================================= #
#  STAGE: summary
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 66 SCOREBOARD (CURSIVE CURRICULUM)\n{SEP}")
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"\n  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: {md5_now == prep['stroke_shapes_md5']})")
    lt = _ckpt("letters.json")
    if os.path.exists(lt):
        cb = _load(lt)["codebook"]
        n_forms = sum(len(v) for v in cb.values())
        print(f"  STAGE 1: learned {n_forms} letter-forms over "
              f"{sum(1 for v in cb.values() if v)} letters (K_allo={K_ALLO})")
    jp = _ckpt("joins.json")
    if os.path.exists(jp):
        j = _load(jp)
        print(f"  STAGE 2: learned join model from {j['n']} pairs; global gap={[round(x,3) for x in j['global']]}")
    wp = _ckpt("write_validate.json")
    if os.path.exists(wp):
        wv = _load(wp)
        dj, dn = np.mean(wv["with_joins"]), np.mean(wv["no_joins"])
        print(f"  STAGE 3: generated-vs-real DTW  with-joins={dj:.4f}  no-joins={dn:.4f}  "
              f"lift={dn-dj:+.4f}  joins-better={wv['joins_better']}/{wv['n']}")
    rp = _ckpt("read.json")
    if os.path.exists(rp):
        st = _load(rp)
        _report_read(st)
    print(f"\n{SEP}\n  RUN 66 COMPLETE -- see final agent report.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                   choices=["prep", "learn_letters", "learn_joins", "write_validate", "read",
                            "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "learn_letters": stage_learn_letters,
            "learn_joins": stage_learn_joins, "write_validate": stage_write_validate,
            "read": stage_read, "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
